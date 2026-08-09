"""MPI-backed pool with a native rich progress bar, driven by mpi4py.

Workers block in a recv loop; only the master process (rank 0) renders the
progress bar and returns results. Run scripts using this pool via
``mpiexec -n N python script.py``.
"""

import atexit
import sys
import traceback
from collections.abc import Callable, Iterable
from typing import Any

from rich.console import Console

from richpool._progress import make_progress, resolve_total
from richpool.pool import BasePool

__all__ = ["MPIPool"]

# Imported lazily (only when an MPIPool is actually constructed or `enabled()` is
# probed) because `import mpi4py.MPI` calls MPI_Init() as a side effect. That
# initializes MPI process-wide, which is incompatible with later spawning a
# fresh, unrelated `mpiexec` job from this same process. Importing it
# unconditionally at module load time would break MultiPool/JoblibPool users
# who never touch MPIPool, and would break any code that itself shells out to
# mpiexec after merely importing richpool.
MPI = None


def _import_mpi(quiet: bool = False):
    global MPI
    try:
        from mpi4py import MPI as _MPI  # ty: ignore[unresolved-import]

        MPI = _MPI
    except ImportError as e:
        if not quiet:
            raise ImportError("Please install mpi4py to use MPIPool") from e
    return MPI


def _dummy_callback(_: Any) -> None:
    pass


def _print_progress_line(console: Console, progress) -> None:
    r"""Render the current progress state as one newline-terminated line and flush it.

    mpiexec/mpirun forward each rank's output line-by-line rather than byte-by-byte,
    so a normal rich ``Live`` display (which redraws in place via ``\\r``, only ever
    emitting a real newline once the bar completes) sits fully buffered until the
    whole run finishes. Printing one complete, flushed line per update sidesteps that:
    it trades in-place redraw for a scrolling log of styled lines, but it's the
    only way to get live feedback under mpiexec.
    """
    with console.capture() as capture:
        console.print(progress)
    console.file.write(capture.get().rstrip("\n") + "\n")
    console.file.flush()


class MPIPool(BasePool):
    """A processing pool that distributes tasks using MPI, with a rich progress bar on the master.

    MPI messages are serialized with ``dill`` rather than the standard library's
    ``pickle`` (via ``MPI.pickle.__init__``, process-wide), since mpi4py's default
    pickling can't send lambdas, closures, or locally-defined functions as the
    worker function. ``dill`` can, matching what `MultiPool`/`JoblibPool` already
    support via pathos/joblib.

    Parameters
    ----------
    comm : mpi4py.MPI.Comm, optional
        An MPI communicator to distribute tasks with. Defaults to ``MPI.COMM_WORLD``.
    processes : int, optional
        Not used by `MPIPool`. The number of workers is fixed by how many MPI
        ranks the script was launched with (``mpiexec -n N``). Accepted so
        `choose_pool()` can construct any pool backend with the same call.
    initializer : callable, optional
        Not used by `MPIPool`. Accepted for the same reason.
    initargs : tuple, optional
        Not used by `MPIPool`. Accepted for the same reason.
    disable : bool, optional
        Default for ``map()``'s ``disable`` argument; suppresses the progress
        bar on every call unless a call overrides it explicitly.
    """

    def __init__(
        self,
        comm: Any = None,
        processes: int | None = None,
        initializer: Callable | None = None,
        initargs: tuple | None = None,
        disable: bool = False,
        **_: Any,
    ):
        super().__init__(disable=disable)
        self._mpi = _import_mpi()

        import dill

        self._mpi.pickle.__init__(dill.dumps, dill.loads)

        if comm is None:
            comm = self._mpi.COMM_WORLD
        self.comm = comm

        self.master = 0
        self.rank = self.comm.Get_rank()

        atexit.register(lambda: MPIPool.close(self))

        if not self.is_master():
            try:
                self.wait()
            except Exception:
                traceback.print_exc()
                sys.stdout.flush()
                sys.stderr.flush()
                self._mpi.COMM_WORLD.Abort()
            finally:
                sys.exit(0)

        self.workers = set(range(self.comm.size))
        self.workers.discard(self.master)
        self.size = self.comm.Get_size() - 1

        if self.size == 0:
            msg = (
                "Tried to create an MPI pool, but there was only one MPI process "
                "available. Need at least two (run with `mpiexec -n 2` or more)."
            )
            raise ValueError(msg)

    @staticmethod
    def enabled() -> bool:
        """Return whether mpi4py is installed and more than one MPI rank is running."""
        mpi = MPI
        if mpi is None:
            mpi = _import_mpi(quiet=True)
        return mpi is not None and mpi.COMM_WORLD.size > 1

    def wait(self, callback: Callable | None = None) -> None:
        """Workers block here, waiting for tasks from the master. Called automatically by ``map``."""
        if self.is_master():
            return

        mpi = self._mpi
        status = mpi.Status()
        while True:
            task = self.comm.recv(source=self.master, tag=mpi.ANY_TAG, status=status)

            if task is None:
                break

            func, arg = task
            result = func(arg)
            self.comm.ssend(result, self.master, status.tag)

        if callback is not None:
            callback()

    def map(
        self,
        func: Callable,
        iterable: Iterable,
        callback: Callable | None = None,
        **kwargs,
    ) -> list[Any] | None:  # ty:ignore[invalid-method-override]
        """Dispatch `func` over `iterable` to MPI worker ranks; only the master returns results.

        Parameters
        ----------
        func : callable
            Function to apply to each item.
        iterable : iterable
            Items to process.
        callback : callable, optional
            Called on the master with each result as it completes.
        **kwargs
            ``desc``, ``total``, and ``disable`` control the progress bar.

        Returns
        -------
        list or None
            Results in the same order as `iterable` on the master process;
            `None` on worker processes.
        """
        desc: str = kwargs.pop("desc", "")
        total: int | None = kwargs.pop("total", None)
        disable: bool = kwargs.pop("disable", self.disable)
        if not self.is_master():
            self.wait()
            return None

        items = list(iterable)
        total = resolve_total(total, items)
        user_callback = callback if callback is not None else _dummy_callback

        mpi = self._mpi
        workerset = self.workers.copy()
        tasklist = [(tid, (func, arg)) for tid, arg in enumerate(items)]
        resultlist: list = [None] * len(tasklist)
        pending = len(tasklist)

        # A normal `with make_progress(...) as progress:` live display doesn't work
        # here, see `_print_progress_line`'s docstring. Instead, build the Progress
        # renderer without starting its Live display, and print one flushed line per
        # update. Printing on every single completed item would flood the output for
        # large item counts, so updates are throttled to roughly one print per worker
        # (`self.size`), a bounded number of lines regardless of how many items
        # there are, always including the final, 100% line.
        console = Console(file=sys.stderr, force_terminal=True)
        progress = make_progress(disable=disable, console=console)
        task_id = progress.add_task(desc, total=total)
        print_every = max(1, -(-len(items) // self.size))
        completed = 0

        while pending:
            if workerset and tasklist:
                worker = workerset.pop()
                taskid, task = tasklist.pop()
                self.comm.send(task, dest=worker, tag=taskid)

            if tasklist:
                flag = self.comm.Iprobe(source=mpi.ANY_SOURCE, tag=mpi.ANY_TAG)
                if not flag:
                    continue
            else:
                self.comm.Probe(source=mpi.ANY_SOURCE, tag=mpi.ANY_TAG)

            status = mpi.Status()
            result = self.comm.recv(source=mpi.ANY_SOURCE, tag=mpi.ANY_TAG, status=status)
            worker = status.source
            taskid = status.tag

            user_callback(result)
            progress.advance(task_id)

            workerset.add(worker)
            resultlist[taskid] = result
            pending -= 1
            completed += 1

            if not disable and (completed % print_every == 0 or pending == 0):
                _print_progress_line(console, progress)

        return resultlist

    def close(self) -> None:
        """Tell all workers to quit."""
        if self.is_worker():
            return

        for worker in self.workers:
            self.comm.send(None, worker, 0)

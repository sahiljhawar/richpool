"""pathos-backed multiprocessing pool with a native rich progress bar."""

import functools
import signal
from collections.abc import Callable, Iterable
from typing import Any

from pathos.helpers import mp
from pathos.multiprocessing import ProcessPool

from richpool._progress import make_progress, resolve_total
from richpool.pool import BasePool

__all__ = ["MultiPool"]


def _initializer_wrapper(actual_initializer, *rest):
    """Ignore SIGINT in workers; the parent is responsible for killing them on ^C."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    if actual_initializer is not None:
        actual_initializer(*rest)


class _CallbackWrapper:
    """Turns amap's per-chunk callback into per-item ticks on the progress bar."""

    def __init__(self, progress, task_id, callback: Callable | None):
        self.progress = progress
        self.task_id = task_id
        self.callback = callback

    def __call__(self, chunk_results: Iterable[Any]) -> None:
        for result in chunk_results:
            if self.callback is not None:
                self.callback(result)
            self.progress.advance(self.task_id)


class MultiPool(BasePool):
    """A multiprocessing pool (via ``pathos.multiprocessing.ProcessPool``) with a rich progress bar.

    Parameters
    ----------
    processes : int, optional
        The number of worker processes to use; defaults to the number of CPUs.
    initializer : callable, optional
        Invoked by each worker process when it starts.
    initargs : iterable, optional
        Arguments for ``initializer``.
    comm : mpi4py.MPI.Comm, optional
        Not used by `MultiPool`. Accepted so `choose_pool()` can construct any
        pool backend with the same call, regardless of which one gets picked.
    disable : bool, optional
        Default for ``map()``'s ``disable`` argument; suppresses the progress
        bar on every call unless a call overrides it explicitly. Useful when
        another library (e.g. emcee) calls ``map()`` many times internally
        and you'd rather track overall progress yourself.
    """

    wait_timeout = 3600

    def __init__(
        self,
        processes: int | None = None,
        initializer: Callable | None = None,
        initargs: tuple = (),
        comm: Any = None,
        disable: bool = False,
        **kwargs: Any,
    ):
        super().__init__(disable=disable)
        new_initializer = functools.partial(_initializer_wrapper, initializer)
        if processes is not None:
            kwargs["ncpus"] = processes
        self._pool = ProcessPool(initializer=new_initializer, initargs=initargs, **kwargs)
        self.size: int | None = self._pool.nodes

    @staticmethod
    def enabled() -> bool:
        """Return True; the multiprocessing pool is always available."""
        return True

    def map(
        self,
        func: Callable,
        iterable: Iterable,
        callback: Callable | None = None,
        chunksize: int | None = None,
        **kwargs,
    ) -> list:
        """Apply `func` to `iterable` across the pool's worker processes.

        Parameters
        ----------
        func : callable
            Function to apply to each item.
        iterable : iterable
            Items to process.
        callback : callable, optional
            Called with each result as it completes.
        chunksize : int, optional
            Number of items dispatched to a worker at a time.
        **kwargs
            ``desc``, ``total``, and ``disable`` control the progress bar.

        Returns
        -------
        list
            Results in the same order as `iterable`.
        """
        desc: str = kwargs.pop("desc", "")
        total: int | None = kwargs.pop("total", None)
        disable: bool = kwargs.pop("disable", self.disable)
        items = list(iterable)
        total = resolve_total(total, items)

        with make_progress(disable=disable) as progress:
            task_id = progress.add_task(desc, total=total)
            tick = _CallbackWrapper(progress, task_id, callback)

            async_result = self._pool.amap(func, items, chunksize=chunksize, callback=tick)

            while True:
                try:
                    return async_result.get(self.wait_timeout)
                except mp.TimeoutError:  # ty: ignore[unresolved-attribute]
                    continue
                except KeyboardInterrupt:
                    self._pool.terminate()
                    self._pool.join()
                    raise

    def close(self) -> None:
        """Close the underlying process pool and release its workers."""
        self._pool.close()
        self._pool.join()
        self._pool.clear()

    def terminate(self) -> None:
        """Terminate the underlying process pool immediately."""
        self._pool.terminate()

    def join(self) -> None:
        """Wait for the underlying process pool's worker processes to exit."""
        self._pool.join()

"""Sequential pool with a native rich progress bar."""

from collections.abc import Callable, Iterable
from typing import Any

from rich.progress import Progress

from richpool._progress import make_progress, resolve_total
from richpool.pool import BasePool

__all__ = ["SerialPool"]


class SerialPool(BasePool):
    """A serial pool that wraps the built-in ``map`` function with a rich progress bar.

    Parameters
    ----------
    processes : int, optional
        Not used by `SerialPool`. Accepted so `choose_pool()` can construct any
        pool backend with the same call, regardless of which one gets picked.
    initializer : callable, optional
        Not used by `SerialPool`. Accepted for the same reason.
    initargs : tuple, optional
        Not used by `SerialPool`. Accepted for the same reason.
    comm : mpi4py.MPI.Comm, optional
        Not used by `SerialPool`. Accepted for the same reason.
    disable : bool, optional
        Default for ``map()``'s ``disable`` argument; suppresses the progress
        bar on every call unless a call overrides it explicitly.
    """

    def __init__(
        self,
        processes: int | None = None,
        initializer: Callable | None = None,
        initargs: tuple | None = None,
        comm: Any = None,
        disable: bool = False,
        **_: Any,
    ):
        super().__init__(disable=disable)

    @staticmethod
    def enabled() -> bool:
        """Return True; the serial pool has no external dependencies."""
        return True

    def map(
        self,
        func: Callable,
        iterable: Iterable,
        callback: Callable | None = None,
        **kwargs,
    ) -> list:
        """Apply `func` to `iterable` sequentially, one item at a time.

        Parameters
        ----------
        func : callable
            Function to apply to each item.
        iterable : iterable
            Items to process.
        callback : callable, optional
            Called with each result as it completes.
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

        results = []
        progress: Progress
        with make_progress(disable=disable) as progress:
            task_id = progress.add_task(desc, total=total)
            for item in map(func, items):
                if callback is not None:
                    callback(item)
                results.append(item)
                progress.advance(task_id)

        return results

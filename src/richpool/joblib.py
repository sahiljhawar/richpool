"""joblib-backed pool with a native rich progress bar."""

from collections.abc import Callable, Iterable
from typing import Any

from joblib import Parallel, delayed

from richpool._progress import make_progress, resolve_total
from richpool.pool import BasePool

__all__ = ["JoblibPool"]


class JoblibPool(BasePool):
    """A processing pool that distributes tasks using ``joblib.Parallel``, with a rich progress bar.

    All constructor arguments and keyword arguments are passed directly to
    ``joblib.Parallel.__init__`` (e.g. ``n_jobs``, ``backend``, ``prefer``).
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__()
        self.args = args
        self.kwargs = kwargs
        self.size = 0
        self.rank = 0

    @staticmethod
    def enabled() -> bool:
        """Return whether joblib is installed."""
        return Parallel is not None

    def map(
        self,
        func: Callable,
        iterable: Iterable,
        callback: Callable | None = None,
        **kwargs,
    ) -> list:
        """Apply `func` to `iterable` via `joblib.Parallel`, ticking the bar as results arrive.

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
        disable: bool = kwargs.pop("disable", False)
        items = list(iterable)
        total = resolve_total(total, items)

        kwargs = dict(self.kwargs)
        kwargs["return_as"] = "generator"
        parallel = Parallel(*self.args, **kwargs)

        results = []
        with make_progress(disable=disable) as progress:
            task_id = progress.add_task(desc, total=total)
            for result in parallel(delayed(func)(item) for item in items):
                if callback is not None:
                    callback(result)
                results.append(result)
                progress.advance(task_id)

        return results

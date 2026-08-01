"""Sequential pool with a native rich progress bar."""

from collections.abc import Callable, Iterable
from typing import Any

from rich.progress import Progress

from richpool._progress import make_progress, resolve_total
from richpool.pool import BasePool

__all__ = ["SerialPool"]


class SerialPool(BasePool):
    """A serial pool that wraps the built-in ``map`` function with a rich progress bar."""

    def __init__(self, **_: Any):
        super().__init__()
        self.size = 0
        self.rank = 0

    @staticmethod
    def enabled() -> bool:
        return True

    def map(
        self,
        func: Callable,
        iterable: Iterable,
        callback: Callable | None = None,
        **kwargs,
    ) -> list:
        desc: str = kwargs.pop("desc", "")
        total: int | None = kwargs.pop("total", None)
        disable: bool = kwargs.pop("disable", False)
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

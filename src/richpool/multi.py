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
    """

    wait_timeout = 3600

    def __init__(
        self,
        processes: int | None = None,
        initializer: Callable | None = None,
        initargs: tuple = (),
        **kwargs: Any,
    ):
        super().__init__()
        new_initializer = functools.partial(_initializer_wrapper, initializer)
        self._pool = ProcessPool(
            processes, initializer=new_initializer, initargs=initargs, **kwargs
        )
        self.size = self._pool.nodes

    @staticmethod
    def enabled() -> bool:
        return True

    def map(
        self,
        func: Callable,
        iterable: Iterable,
        callback: Callable | None = None,
        chunksize: int | None = None,
        **kwargs,
    ) -> list:
        desc: str = kwargs.pop("desc", "")
        total: int | None = kwargs.pop("total", None)
        disable: bool = kwargs.pop("disable", False)
        items = list(iterable)
        total = resolve_total(total, items)

        with make_progress(disable=disable) as progress:
            task_id = progress.add_task(desc, total=total)
            tick = _CallbackWrapper(progress, task_id, callback)

            async_result = self._pool.amap(
                func, items, chunksize=chunksize, callback=tick
            )

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
        self._pool.close()
        self._pool.join()
        self._pool.clear()

    def terminate(self) -> None:
        self._pool.terminate()

    def join(self) -> None:
        self._pool.join()

"""Base pool interface, shared by all richpool pool classes."""

import abc
from collections.abc import Callable, Iterable
from typing import Any


class BasePool(metaclass=abc.ABCMeta):
    """A base class for pools exposing a uniform ``map`` interface with a rich progress bar."""

    def __init__(self, **_: Any):
        self.rank = 0
        self.size = 0

    @staticmethod
    def enabled() -> bool:
        return False

    def is_master(self) -> bool:
        return self.rank == 0

    def is_worker(self) -> bool:
        return self.rank != 0

    def wait(self) -> None:
        return

    @abc.abstractmethod
    def map(
        self,
        func: Callable,
        iterable: Iterable,
        callback: Callable | None = None,
        **progress_kwargs: Any,
    ) -> list:
        """Apply ``func`` to every item of ``iterable``, showing a rich progress bar."""
        raise NotImplementedError

    def close(self) -> None:  # noqa: B027 (intentional no-op default, not abstract)
        """Release any resources held by the pool. No-op by default; override if needed."""

    def __enter__(self) -> "BasePool":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

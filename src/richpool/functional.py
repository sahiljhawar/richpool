"""p_tqdm-style free functions: no Pool object required from the caller.

p_map:   Performs a parallel ordered map.
p_imap:  Returns an iterator for a parallel ordered map.
p_umap:  Performs a parallel unordered map.
p_uimap: Returns an iterator for a parallel unordered map.
t_map:   Performs a sequential map.
t_imap:  Returns an iterator for a sequential map.
"""

import signal
from collections.abc import Callable, Generator, Iterable, Sized
from typing import Any

from pathos.helpers import cpu_count
from pathos.multiprocessing import ProcessPool

from richpool._progress import make_progress

__all__ = ["p_map", "p_imap", "p_umap", "p_uimap", "t_map", "t_imap"]


def _ignore_sigint() -> None:
    """Worker initializer: SIGINT is handled by the parent process, not workers."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def _num_processes(num_cpus: Any | None) -> int:
    cpu_total = cpu_count()
    if num_cpus is None:
        return cpu_total
    if isinstance(num_cpus, float):
        return max(1, int(round(num_cpus * cpu_total)))
    return num_cpus


def _length(iterables: Iterable, total: int | None) -> int | None:
    if total is not None:
        return total
    lengths = [len(it) for it in iterables if isinstance(it, Sized)]
    return min(lengths) if lengths else None


def _parallel(
    ordered: bool,
    function: Callable,
    *iterables: Iterable,
    **kwargs: Any,
) -> Generator:
    num_cpus = _num_processes(kwargs.pop("num_cpus", None))
    total = _length(iterables, kwargs.pop("total", None))
    desc = kwargs.pop("desc", "")
    disable = kwargs.pop("disable", False)
    chunksize = kwargs.pop("chunksize", None)

    # Materialize each iterable so pathos can zip them and so a generator
    # doesn't get consumed twice (once for length, once for mapping).
    materialized = [list(it) for it in iterables]

    pool = ProcessPool(num_cpus, initializer=_ignore_sigint)
    try:
        with make_progress(disable=disable) as progress:
            task_id = progress.add_task(desc, total=total)
            map_func = pool.imap if ordered else pool.uimap
            map_kwargs = {} if chunksize is None else {"chunksize": chunksize}
            for result in map_func(function, *materialized, **map_kwargs):
                progress.advance(task_id)
                yield result
    finally:
        pool.close()
        pool.join()
        pool.clear()


def p_map(function: Callable, *iterables: Iterable, **kwargs: Any) -> list[Any]:
    """Performs a parallel ordered map with a rich progress bar."""
    return list(_parallel(True, function, *iterables, **kwargs))


def p_imap(function: Callable, *iterables: Iterable, **kwargs: Any) -> Generator:
    """Returns a generator for a parallel ordered map with a rich progress bar."""
    return _parallel(True, function, *iterables, **kwargs)


def p_umap(function: Callable, *iterables: Iterable, **kwargs: Any) -> list[Any]:
    """Performs a parallel unordered map with a rich progress bar."""
    return list(_parallel(False, function, *iterables, **kwargs))


def p_uimap(function: Callable, *iterables: Iterable, **kwargs: Any) -> Generator:
    """Returns a generator for a parallel unordered map with a rich progress bar."""
    return _parallel(False, function, *iterables, **kwargs)


def _sequential(function: Callable, *iterables: Iterable, **kwargs: Any) -> Generator:
    total = _length(iterables, kwargs.pop("total", None))
    desc = kwargs.pop("desc", "")
    disable = kwargs.pop("disable", False)

    with make_progress(disable=disable) as progress:
        task_id = progress.add_task(desc, total=total)
        for item in map(function, *iterables):
            progress.advance(task_id)
            yield item


def t_map(function: Callable, *iterables: Iterable, **kwargs: Any) -> list[Any]:
    """Performs a sequential map with a rich progress bar."""
    return list(_sequential(function, *iterables, **kwargs))


def t_imap(function: Callable, *iterables: Iterable, **kwargs: Any) -> Generator:
    """Returns a generator for a sequential map with a rich progress bar."""
    return _sequential(function, *iterables, **kwargs)

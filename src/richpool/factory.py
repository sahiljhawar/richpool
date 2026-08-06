"""Pool selection, mirroring schwimmbad's ``choose_pool``."""

from typing import Any

from richpool.mpi import MPIPool
from richpool.multi import MultiPool
from richpool.serial import SerialPool

__all__ = ["choose_pool"]


def choose_pool(
    mpi: bool = False, processes: int = 1, **kwargs: Any
) -> MPIPool | MultiPool | SerialPool:  # noqa: F821
    """Choose between :class:`SerialPool`, :class:`MultiPool`, and :class:`MPIPool`.

    Parameters
    ----------
    mpi : bool, optional
        Use :class:`MPIPool`. By default ``False``.
    processes : int, optional
        Number of worker processes. ``processes=1`` (the default) selects
        :class:`SerialPool`; any other value selects :class:`MultiPool`.
    **kwargs
        Additional keyword arguments passed through to the selected pool's constructor.
    """

    if mpi:
        from richpool.mpi import MPIPool

        if not MPIPool.enabled():
            raise SystemError(
                "Tried to run with MPI but MPIPool is not enabled."
            )

        return MPIPool(**kwargs)

    if processes != 1 and MultiPool.enabled():
        return MultiPool(processes=processes, **kwargs)

    return SerialPool(**kwargs)

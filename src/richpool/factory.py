"""Pool selection, mirroring schwimmbad's ``choose_pool``."""

from typing import Any

from richpool.joblib import JoblibPool
from richpool.mpi import MPIPool
from richpool.multi import MultiPool
from richpool.serial import SerialPool

__all__ = ["choose_pool"]


def choose_pool(
    mpi: bool = False, processes: int = 1, pool: str | None = None, **kwargs: Any
) -> MPIPool | MultiPool | SerialPool | JoblibPool:  # noqa: F821
    """Choose between :class:`SerialPool`, :class:`MultiPool`, :class:`MPIPool`, and :class:`JoblibPool`.

    Parameters
    ----------
    mpi : bool, optional
        Use :class:`MPIPool`. By default ``False``.
    processes : int, optional
        Number of worker processes. ``processes=1`` (the default) selects
        :class:`SerialPool`; any other value selects :class:`MultiPool`
        (or :class:`JoblibPool`, if ``pool="joblib"``).
    pool : str, optional
        Backend to use for the non-MPI, multi-process case. ``None`` (the
        default) preserves the schwimmbad-compatible behavior and selects
        :class:`MultiPool`. Pass ``"joblib"`` to select :class:`JoblibPool`
        instead. Ignored when ``mpi=True`` or ``processes=1``.
    **kwargs
        Additional keyword arguments passed through to the selected pool's
        constructor. ``backend`` is a ``joblib.Parallel`` kwarg: it's only
        forwarded when ``pool="joblib"`` and dropped otherwise, so passing it
        doesn't break :class:`MultiPool`/:class:`SerialPool`/:class:`MPIPool`.
    """
    if mpi:
        from richpool.mpi import MPIPool

        kwargs.pop("backend", None)

        if not MPIPool.enabled():
            raise SystemError(
                "Tried to run with MPI but MPIPool is not enabled. "
                "Try running by appending mpiexec/mpirun, e.g. `mpiexec -n 4 python script.py`."
            )

        return MPIPool(**kwargs)

    if processes != 1:
        if pool == "joblib":
            return JoblibPool(processes=processes, **kwargs)

        if pool not in (None, "multi"):
            raise ValueError(f"Unknown pool {pool!r}; expected None, 'multi', or 'joblib'.")

        kwargs.pop("backend", None)

        if MultiPool.enabled():
            return MultiPool(processes=processes, **kwargs)

    kwargs.pop("backend", None)
    return SerialPool(**kwargs)

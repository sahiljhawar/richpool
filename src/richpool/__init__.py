"""richpool: parallel processing pools and p_tqdm-style maps with native rich progress bars."""

from richpool.factory import choose_pool
from richpool.functional import p_imap, p_map, p_uimap, p_umap, t_imap, t_map
from richpool.joblib import JoblibPool
from richpool.mpi import MPIPool
from richpool.multi import MultiPool
from richpool.pool import BasePool
from richpool.serial import SerialPool

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "BasePool",
    "SerialPool",
    "MultiPool",
    "JoblibPool",
    "MPIPool",
    "choose_pool",
    "p_map",
    "p_imap",
    "p_umap",
    "p_uimap",
    "t_map",
    "t_imap",
]

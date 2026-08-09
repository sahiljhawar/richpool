# richpool

|          |                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Versions | [![PyPI](https://badge.fury.io/py/richpool.svg)](https://pypi.org/project/richpool/) [![Python version](https://img.shields.io/pypi/pyversions/richpool.svg)](https://pypi.org/project/richpool/)                                                                                                                                                                                                                                                                           |
| Status   | [![Tests](https://github.com/sahiljhawar/richpool/actions/workflows/tests.yml/badge.svg)](https://github.com/sahiljhawar/richpool/actions/workflows/tests.yml) [![Coverage Status](https://coveralls.io/repos/github/sahiljhawar/richpool/badge.svg)](https://coveralls.io/github/sahiljhawar/richpool) [![Docs](https://app.readthedocs.org/projects/richpool/badge/?version=latest)](https://richpool.readthedocs.io/en/latest/)                                          |
| Tools    | [![Pre-Commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![ty](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ty/main/assets/badge/v0.json)](https://github.com/astral-sh/ty) |
| License  | [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)                                                                                                                                                                                                                                                                                                                                                                   |

`richpool` is a kind of fork that mixes both [`p_tqdm`](https://github.com/swansonk14/p_tqdm) and [`schwimmbad`](https://github.com/adrn/schwimmbad) into one standalone library, with progress bars rendered natively by [`rich`](https://github.com/Textualize/rich) instead of `tqdm`. It has no dependency on `tqdm`, `p_tqdm`, or `schwimmbad`.

Since, both `p_tqdm` and `schwimmbad` are effectively unmaintained, `richpool` reimplements what both projects offer, aiming to be the successor to both, with the added functionality of a native `rich` progress bar.

It gives you two ways to run parallel work, both with a rich progress bar by default:

1. **A `schwimmbad`-style pool interface**: `SerialPool`, `MultiPool`, `JoblibPool`, `MPIPool`, selected via `choose_pool()`, each with a uniform `.map()` method. This mirrors all four pool types in [schwimmbad](https://github.com/adrn/schwimmbad).
2. **A `p_tqdm`-style functional interface**: `p_map`, `p_imap`, `p_umap`, `p_uimap`, `t_map`, `t_imap`. No pool object to create or manage.

## Installation

`uv pip install richpool`

`MPIPool` needs `mpi4py` (also needs a system MPI, e.g. OpenMPI/MPICH) installed too. Everything else (`SerialPool`, `MultiPool`, `JoblibPool`, the functional API) works out of the box:

```
uv pip install "richpool[mpi]"
```

## Pool interface (schwimmbad)

```python
from richpool import choose_pool

def square(x):
    return x * x

with choose_pool(processes=4) as pool:
    results = pool.map(square, range(20), desc="squaring")
# results == [0, 1, 4, ..., 361]
```

`choose_pool(mpi=False, processes=1, **kwargs)` picks a pool:

- `mpi=True` picks `MPIPool`
- `processes != 1` picks `MultiPool` (backed by `pathos.multiprocessing.ProcessPool`)
- otherwise picks `SerialPool`

All four pool classes share the same `.map()` interface:

```python
pool.map(func, iterable, callback=None, desc="", total=None, disable=False)
```

- `callback`: optional, called on the master process with each individual result as it completes (same contract as schwimmbad's `callback`).
- `desc`: progress bar description.
- `total`: override the progress bar total (inferred from `len(iterable)` when omitted).
- `disable`: suppress the progress bar.

You can also instantiate pools directly:

```python
from richpool import SerialPool, MultiPool, JoblibPool, MPIPool

SerialPool()
MultiPool(processes=8)
JoblibPool(processes=8, backend="loky")  # any joblib.Parallel kwargs
MPIPool()  # run script with: mpiexec -n 4 python script.py
```

### MPIPool notes

`MPIPool` distributes tasks across MPI ranks using `mpi4py`. Only the master process (rank 0) returns from `map()` with results and renders the progress bar; other ranks block in a worker loop and `map()` returns `None` for them. Launch scripts with `mpiexec`/`mpirun`:

```python
from richpool import choose_pool


def square(x):
    return x * x


with choose_pool(mpi=True) as pool:
    if pool.is_master():
        results = pool.map(square, range(20), desc="squaring")
        print(results)
```

```
mpiexec -n 4 python script.py
```

Needs at least 2 MPI ranks (1 master + >=1 worker).

## Functional interface (p_tqdm)

No pool to create, just call the function:

```python
from richpool import p_map, p_umap, t_map


def add(a, b):
    return a + b


p_map(add, [1, 2, 3], [10, 20, 30])  # parallel, ordered:   [11, 22, 33]
p_umap(add, [1, 2, 3], [10, 20, 30])  # parallel, unordered: e.g. [22, 11, 33]
t_map(add, [1, 2, 3], [10, 20, 30])  # sequential, ordered: [11, 22, 33]
```

- `p_map` / `p_imap`: parallel ordered map / iterator.
- `p_umap` / `p_uimap`: parallel unordered map / iterator (results as they complete).
- `t_map` / `t_imap`: sequential map / iterator.

All accept `num_cpus` (int, or float as a proportion of available CPUs), `total`, `desc`, `disable`, and `chunksize` keyword arguments.

```python
from functools import partial
from richpool import p_map


def add(a, b, c=0):
    return a + b + c


p_map(partial(add, c=1), [1, 2, 3], [10, 20, 30], num_cpus=0.5, desc="adding")
```

## Examples

Every pool and every functional map has a minimal, runnable example under [`examples/`](examples):

```
python examples/serial_pool_example.py
python examples/multi_pool_example.py
python examples/joblib_pool_example.py
mpiexec -n 4 python examples/mpi_pool_example.py

python examples/functional_pmap_example.py
python examples/functional_pimap_example.py
python examples/functional_pumap_example.py
python examples/functional_puimap_example.py
python examples/functional_tmap_example.py
python examples/functional_timap_example.py
```

See them run with their real output, progress bar included, on the [examples page](https://richpool.readthedocs.io/en/latest/examples.html) of the docs.

## Credits

Parts of `richpool`'s code and docs are adapted directly from [`schwimmbad`](https://github.com/adrn/schwimmbad) (Copyright (c) 2016 Adrian Price-Whelan) and [`p_tqdm`](https://github.com/swansonk14/p_tqdm) (Copyright (c) 2024 Kyle Swanson), both MIT licensed. See [THIRD_PARTY_NOTICES.md](https://github.com/sahiljhawar/richpool/blob/main/THIRD_PARTY_NOTICES.md) for their original license text.

## License

MIT, see [LICENSE](https://github.com/sahiljhawar/richpool/blob/main/LICENSE).

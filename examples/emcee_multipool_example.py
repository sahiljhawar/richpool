"""Using MultiPool with emcee for parallel MCMC sampling.

Adapted from schwimmbad's "Using MultiPool with emcee" example:
https://schwimmbad.readthedocs.io/en/latest/examples/index.html#using-multipool-with-emcee

emcee's EnsembleSampler accepts any pool object exposing a .map() method, so
richpool's MultiPool can be passed directly to parallelize likelihood
evaluations across worker processes. log_probability sleeps briefly to stand
in for a realistic, non-trivial likelihood (e.g. one involving a simulation
or numerical integration); without that, each evaluation is a handful of
floating-point ops that finishes in microseconds.

emcee calls pool.map() several times per MCMC step internally (its default
move splits the ensemble in half and updates each half in turn), so letting
MultiPool render its usual per-call progress bar produces a handful of tiny,
near-instant, low-information bars, not real progress bars. Passing disable=True to
MultiPool's constructor turns off those per-call bars (the default for every
map() call unless a call overrides it), and a single rich progress bar below
tracks real progress across the n_steps MCMC steps instead, while the
likelihood evaluations for each step still run in parallel underneath it.

Needs the extra emcee, numpy, and matplotlib dependencies:
pip install emcee numpy matplotlib.
"""

import time

import matplotlib.pyplot as plt  # ty: ignore[unresolved-import]
import numpy as np  # ty: ignore[unresolved-import]
from emcee import EnsembleSampler  # ty: ignore[unresolved-import]
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from richpool import MultiPool

LIKELIHOOD_SLEEP = 0.01


def log_probability(p, mean, var):
    time.sleep(LIKELIHOOD_SLEEP)
    x = p[0]
    return -0.5 * (x - mean) ** 2 / var


def main():
    n_walkers = 20
    n_dim = 1
    n_steps = 50
    processes = 4
    p0 = np.random.uniform(0, 10, (n_walkers, n_dim))
    serial_estimate = n_steps * n_walkers * LIKELIHOOD_SLEEP

    start = time.perf_counter()
    with MultiPool(processes, disable=True) as pool:
        sampler = EnsembleSampler(n_walkers, n_dim, log_probability, args=(5, 1.2), pool=pool)

        columns = (
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        )
        with Progress(*columns) as progress:
            task_id = progress.add_task("sampling", total=n_steps)
            for _ in sampler.sample(p0, iterations=n_steps):
                progress.advance(task_id)
    elapsed = time.perf_counter() - start

    print(f"mean of flatchain: {sampler.flatchain.mean():.3f}")
    print(f"parallel: {elapsed:.2f}s (serial would take ~{serial_estimate:.2f}s)")

    plt.figure()
    plt.hist(sampler.flatchain, bins=30)
    plt.xlabel("x")
    plt.ylabel("count")
    plt.title("emcee samples drawn via richpool's MultiPool")


if __name__ == "__main__":
    main()

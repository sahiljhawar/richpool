"""Minimal working example of MPIPool.

Run with: mpiexec -n 4 python mpi_example.py
Only the master rank (rank 0) prints output and shows the progress bar.
"""

import time

from richpool import MPIPool

SLEEP_TIME = 1


def square_slowly(x):
    time.sleep(SLEEP_TIME)
    return x * x


if __name__ == "__main__":
    n = 20
    serial_estimate = n * SLEEP_TIME

    with MPIPool() as pool:
        if pool.is_master():
            start = time.perf_counter()
            results = pool.map(square_slowly, range(n), desc="squaring")
            elapsed = time.perf_counter() - start

            print(results)
            print(f"parallel: {elapsed:.2f}s (serial would take ~{serial_estimate:.2f}s)")

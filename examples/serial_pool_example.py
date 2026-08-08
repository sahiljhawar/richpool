"""Minimal working example of SerialPool."""

import time

from richpool import SerialPool

SLEEP_TIME = 1


def square_slowly(x):
    time.sleep(SLEEP_TIME)
    return x * x


if __name__ == "__main__":
    n = 20

    start = time.perf_counter()
    with SerialPool() as pool:
        results = pool.map(square_slowly, range(n), desc="squaring")
    elapsed = time.perf_counter() - start

    print(results)
    print(f"serial: {elapsed:.2f}s (no speedup, SerialPool runs one item at a time)")

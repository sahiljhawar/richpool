"""Minimal working example of richpool's t_map: a sequential map with a progress bar.

No parallelism, t_map just wraps the builtin map() with a rich progress bar.
"""

import time

from richpool import t_map

SLEEP_TIME = 1


def square_slowly(x):
    time.sleep(SLEEP_TIME)
    return x * x


if __name__ == "__main__":
    n = 10

    start = time.perf_counter()
    results = t_map(square_slowly, range(n), desc="squaring")
    elapsed = time.perf_counter() - start

    print(results)
    print(f"sequential: {elapsed:.2f}s (no speedup, t_map runs one item at a time)")

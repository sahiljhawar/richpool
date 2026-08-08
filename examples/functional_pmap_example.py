"""Minimal working example of richpool's p_map: a parallel ordered map."""

import time

from richpool import p_map

SLEEP_TIME = 1


def square_slowly(x):
    time.sleep(SLEEP_TIME)
    return x * x


if __name__ == "__main__":
    n = 20
    serial_estimate = n * SLEEP_TIME

    start = time.perf_counter()
    results = p_map(square_slowly, range(n), desc="squaring")
    elapsed = time.perf_counter() - start

    print(results)
    print(f"parallel: {elapsed:.2f}s (serial would take ~{serial_estimate:.2f}s)")

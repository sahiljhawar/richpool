"""Minimal working example of richpool's p_imap: a parallel ordered iterator.

Unlike p_map, p_imap doesn't wait for the whole batch, it yields each result
as soon as it's ready, in the same order as the input.
"""

import time

from richpool import p_imap

SLEEP_TIME = 1


def square_slowly(x):
    time.sleep(SLEEP_TIME)
    return x * x


if __name__ == "__main__":
    n = 10
    serial_estimate = n * SLEEP_TIME

    start = time.perf_counter()
    for result in p_imap(square_slowly, range(n), desc="squaring"):
        print("got:", result)
    elapsed = time.perf_counter() - start

    print(f"parallel: {elapsed:.2f}s (serial would take ~{serial_estimate:.2f}s)")

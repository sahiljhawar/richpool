"""Minimal working example of richpool's t_imap: a sequential iterator.

Same as t_map, but yields each result immediately instead of waiting to
return a full list.
"""

import time

from richpool import t_imap

SLEEP_TIME = 1


def square_slowly(x):
    time.sleep(SLEEP_TIME)
    return x * x


if __name__ == "__main__":
    for result in t_imap(square_slowly, range(5), desc="squaring"):
        print("got:", result)

"""Minimal working example of richpool's p_uimap: a parallel unordered iterator.

Combines p_imap's lazy, as-ready yielding with p_umap's unordered delivery.
Earlier items sleep longer than later ones, so results arrive out of order.
"""

import time

from richpool import p_uimap


def square_reverse_delay(x):
    time.sleep((9 - x) * 0.3)
    return x * x


if __name__ == "__main__":
    for result in p_uimap(square_reverse_delay, range(10), desc="squaring"):
        print("got:", result)

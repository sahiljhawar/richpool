"""Minimal working example of richpool's p_umap: a parallel unordered map.

Unlike p_map, results come back in completion order, not input order. To make
that visible, earlier items are made to sleep longer than later ones, so later
items finish first.
"""

import time

from richpool import p_umap


def square_reverse_delay(x):
    time.sleep((9 - x) * 0.3)
    return x * x


if __name__ == "__main__":
    results = p_umap(square_reverse_delay, range(10), desc="squaring")
    print("input order: ", list(range(10)))
    print("result order:", results)

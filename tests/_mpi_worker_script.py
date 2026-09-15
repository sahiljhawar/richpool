"""Run under mpiexec by test_mpi_pool.py. Prints RESULT:<list> on the master rank.

`disable` is controlled via the RICHPOOL_TEST_DISABLE env var (default "1", i.e.
disabled) so test_mpi_pool.py can also verify the progress bar itself, rendered
to stderr, without needing a separate worker script.
"""

import os

from richpool import choose_pool


def square(x):
    return x * x


def main():
    disable = os.environ.get("RICHPOOL_TEST_DISABLE", "1") != "0"
    with choose_pool(mpi=True) as pool:
        if pool.is_master():
            result = pool.map(square, range(10), desc="probing", disable=disable)
            print(f"RESULT:{result}")


if __name__ == "__main__":
    main()

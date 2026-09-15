"""MPI pool tests, run in a subprocess launch of mpiexec.

richpool.mpi imports mpi4py lazily (only when MPIPool is actually constructed),
since `import mpi4py.MPI` initializes MPI as a side effect, which would otherwise
conflict with this file's own nested `mpiexec` subprocess launches.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("mpi4py")

MPIEXEC = shutil.which("mpiexec") or shutil.which("mpirun")

WORKER_SCRIPT = Path(__file__).parent / "_mpi_worker_script.py"

CURSOR_UP_AND_CLEAR = "\x1b[1A\x1b[2K"

pytestmark = pytest.mark.skipif(MPIEXEC is None, reason="no mpiexec/mpirun found on PATH")


def _run_proc(nprocs, disable=True, mode="lines"):
    assert MPIEXEC is not None
    cmd = [MPIEXEC, "-n", str(nprocs), "--oversubscribe"]
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        cmd.append("--allow-run-as-root")
    cmd += [sys.executable, str(WORKER_SCRIPT)]
    print("Running command:", " ".join(cmd))
    env = os.environ.copy()
    env["RICHPOOL_TEST_DISABLE"] = "1" if disable else "0"
    env["RICHPOOL_MPI_PROGRESS"] = mode
    env["COLUMNS"] = "100"
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=env)
    assert proc.returncode == 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    return proc


def _run(nprocs, disable=True, mode="lines"):
    proc = _run_proc(nprocs, disable=disable, mode=mode)
    for line in proc.stdout.splitlines():
        if line.startswith("RESULT:"):
            return eval(line[len("RESULT:") :])

    pytest.fail(f"no RESULT line in output:\n{proc.stdout}\n{proc.stderr}")


@pytest.mark.parametrize("nprocs", [2, 4])
def test_map(nprocs):
    result = _run(nprocs)
    assert result == [x * x for x in range(10)]


def test_progress_bar_shown_by_default():
    proc = _run_proc(2, disable=False)
    assert "probing" in proc.stderr
    assert "100%" in proc.stderr


def test_progress_bar_hidden_by_disable():
    proc = _run_proc(2, disable=True)
    assert proc.stderr == ""


@pytest.mark.parametrize("mode", ["inplace", "lines"])
def test_progress_bar_hidden_by_disable_in_either_mode(mode):
    assert _run_proc(2, disable=True, mode=mode).stderr == ""


def test_inplace_mode_redraws_a_single_bar():
    """Every bar line after the first erases the one before it, so only one is ever visible."""
    proc = _run_proc(4, disable=False, mode="inplace")
    lines = proc.stderr.splitlines()

    assert len(lines) > 1, f"expected several redraws, got {proc.stderr!r}"
    assert not lines[0].startswith(CURSOR_UP_AND_CLEAR)
    assert all(line.startswith(CURSOR_UP_AND_CLEAR) for line in lines[1:])
    # One cursor-up per line beyond the first: the net growth of the display is zero rows.
    assert proc.stderr.count(CURSOR_UP_AND_CLEAR) == len(lines) - 1
    assert "100%" in lines[-1]


def test_lines_mode_scrolls_without_cursor_escapes():
    """The log-friendly fallback: plain lines, bounded in number, no cursor movement."""
    nprocs = 4
    proc = _run_proc(nprocs, disable=False, mode="lines")
    lines = proc.stderr.splitlines()

    assert CURSOR_UP_AND_CLEAR not in proc.stderr
    assert all(not line.startswith("\x1b[1A") for line in lines)
    # Throttled to ~one print per worker, whatever the item count. The +1 covers
    # the unconditional final line landing on its own.
    assert 1 <= len(lines) <= (nprocs - 1) + 1, f"unbounded output: {len(lines)} lines"
    assert "100%" in lines[-1]


def test_both_modes_return_the_same_results():
    assert _run(4, disable=False, mode="inplace") == _run(4, disable=False, mode="lines")

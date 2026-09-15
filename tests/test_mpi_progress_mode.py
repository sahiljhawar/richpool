"""Unit tests for MPIPool's progress rendering-mode selection.

These need neither mpi4py nor mpiexec: richpool.mpi imports mpi4py lazily, and
`_progress_mode` is a pure function of the console's stream and the environment.
"""

import io

import pytest
from rich.console import Console

from richpool.mpi import _CURSOR_UP_AND_CLEAR, _isatty, _print_progress_line, _progress_mode


class _Stream(io.StringIO):
    def __init__(self, tty):
        super().__init__()
        self._tty = tty

    def isatty(self):
        return self._tty


def _console(tty=False):
    return Console(file=_Stream(tty), force_terminal=True, width=80)


@pytest.mark.parametrize("mode", ["inplace", "lines"])
def test_env_var_forces_mode(monkeypatch, mode):
    monkeypatch.setenv("RICHPOOL_MPI_PROGRESS", mode)
    # Set TERM the opposite way the autodetect would read it, to prove the override wins.
    monkeypatch.setenv("TERM", "dumb" if mode == "inplace" else "xterm-256color")
    assert _progress_mode(_console(tty=False)) == mode


def test_env_var_is_case_and_space_insensitive(monkeypatch):
    monkeypatch.setenv("RICHPOOL_MPI_PROGRESS", "  InPlace  ")
    monkeypatch.setenv("TERM", "dumb")
    assert _progress_mode(_console(tty=False)) == "inplace"


def test_unrecognized_env_var_falls_back_to_autodetect(monkeypatch):
    monkeypatch.setenv("RICHPOOL_MPI_PROGRESS", "nonsense")
    monkeypatch.setenv("TERM", "dumb")
    assert _progress_mode(_console(tty=False)) == "lines"


def test_real_tty_is_inplace(monkeypatch):
    monkeypatch.delenv("RICHPOOL_MPI_PROGRESS", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    assert _progress_mode(_console(tty=True)) == "inplace"


@pytest.mark.parametrize(
    ("term", "expected"),
    [("xterm-256color", "inplace"), ("screen", "inplace"), ("dumb", "lines"), ("", "lines")],
)
def test_term_decides_when_stream_is_a_pipe(monkeypatch, term, expected):
    """Under mpiexec the rank's stderr is a pipe, so TERM is what's left to go on."""
    monkeypatch.delenv("RICHPOOL_MPI_PROGRESS", raising=False)
    monkeypatch.setenv("TERM", term)
    assert _progress_mode(_console(tty=False)) == expected


def test_unset_term_on_a_pipe_is_lines(monkeypatch):
    monkeypatch.delenv("RICHPOOL_MPI_PROGRESS", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    assert _progress_mode(_console(tty=False)) == "lines"


def test_isatty_tolerates_streams_without_isatty():
    class NoIsatty:
        pass

    class Closed:
        def isatty(self):
            raise ValueError("I/O operation on closed file")

    assert _isatty(NoIsatty()) is False
    assert _isatty(Closed()) is False
    assert _isatty(_Stream(True)) is True


def test_print_progress_line_emits_one_terminated_line():
    from richpool._progress import make_progress

    console = _console()
    progress = make_progress(console=console)
    progress.add_task("work", total=4)

    _print_progress_line(console, progress)
    out = console.file.getvalue()
    assert out.endswith("\n")
    assert out.count("\n") == 1
    assert not out.startswith(_CURSOR_UP_AND_CLEAR)

    _print_progress_line(console, progress, _CURSOR_UP_AND_CLEAR)
    second = console.file.getvalue()[len(out) :]
    assert second.startswith(_CURSOR_UP_AND_CLEAR)
    assert second.endswith("\n")
    assert second.count("\n") == 1

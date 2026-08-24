"""Shared rich progress bar construction for richpool."""

from collections.abc import Sequence
from math import ceil

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    Task,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.text import Text

__all__ = ["AdaptiveTimeRemainingColumn", "make_progress", "resolve_total"]


def _average_remaining(task: Task) -> float | None:
    """Seconds left at the task's average rate over the whole run, or None if unknowable."""
    elapsed = task.elapsed
    if not elapsed or not task.completed or task.total is None:
        return None
    remaining = task.total - task.completed
    if remaining <= 0:
        return None
    return ceil(remaining * elapsed / task.completed)


class AdaptiveTimeRemainingColumn(TimeRemainingColumn):
    """Time-remaining column that falls back to the whole-run average.

    ``rich`` derives its ETA from a rate measured over a sliding window, and reports
    nothing at all until that window holds two samples separated by a non-zero
    interval. A worker pool hands results back in bursts, so the window can sit
    on a single timestamp for a long time and the column renders ``-:--:--``
    exactly when an estimate is most useful: at the start of a run, and after a
    slow chunk.

    When rich has no estimate this falls back to ``elapsed / completed`` over the
    whole run so far.
    """

    def render(self, task: Task) -> Text:
        """Render rich's estimate, or a whole-run average when it has none."""
        if task.total is not None and not task.finished and task.time_remaining is None:
            remaining = _average_remaining(task)
            if remaining is not None:
                return Text(self._format(remaining), style="progress.remaining")
        return super().render(task)

    def _format(self, seconds: float) -> str:
        """Match ``TimeRemainingColumn``'s own H:MM:SS / MM:SS formatting."""
        minutes, secs = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if self.compact and not hours:
            return f"{minutes:02d}:{secs:02d}"
        return f"{hours:d}:{minutes:02d}:{secs:02d}"


def make_progress(disable: bool = False, console: Console | None = None) -> Progress:
    """Build a rich Progress instance with p_tqdm-like columns.

    Parameters
    ----------
    disable : bool, optional
        Suppress the progress display entirely.
    console : rich.console.Console, optional
        Console to render to. Defaults to rich's global console.
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        AdaptiveTimeRemainingColumn(),
        disable=disable,
        console=console,
    )


def resolve_total(total: int | None, iterable: Sequence) -> int | None:
    if total is not None:
        return total
    return len(iterable)

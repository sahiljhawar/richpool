"""Shared rich progress bar construction for richpool."""


from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


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
        TimeRemainingColumn(),
        disable=disable,
        console=console,
    )


def resolve_total(total: int | None, iterable) -> int | None:
    if total is not None:
        return total
    try:
        return len(iterable)
    except TypeError:
        return None

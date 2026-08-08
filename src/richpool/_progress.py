"""Shared rich progress bar construction for richpool."""


from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


def make_progress(disable: bool = False) -> Progress:
    """Build a rich Progress instance with p_tqdm-like columns."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        disable=disable,
    )


def resolve_total(total: int | None, iterable) -> int | None:
    if total is not None:
        return total
    try:
        return len(iterable)
    except TypeError:
        return None

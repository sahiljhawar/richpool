"""Tests for the ETA column and for MultiPool driving the bar during the run."""

import time

from rich.progress import TimeRemainingColumn

from richpool._progress import AdaptiveTimeRemainingColumn, make_progress

BLANK = "-:--:--"


def _task(total, ticks, now):
    """Build a task whose progress samples land at the given (time, count) ticks."""
    clock = {"t": 0.0}
    progress = make_progress(disable=True)
    progress.get_time = lambda: clock["t"]
    task_id = progress.add_task("t", total=total)
    for at, count in ticks:
        clock["t"] = at
        progress.advance(task_id, count)
    clock["t"] = now
    return progress.tasks[task_id]


def test_stock_column_is_blank_for_a_single_burst():
    task = _task(40, [(4.0, 8)], now=6.0)
    assert task.time_remaining is None
    assert TimeRemainingColumn().render(task).plain.strip() == BLANK


def test_adaptive_column_fills_in_a_single_burst():
    task = _task(40, [(4.0, 8)], now=6.0)
    # 8 of 40 done in 6s -> 32 left at 8/6 per second -> 24s
    assert AdaptiveTimeRemainingColumn().render(task).plain.strip() == "0:00:24"


def test_adaptive_column_defers_to_rich_when_rich_has_an_estimate():
    task = _task(40, [(4.0, 8), (8.0, 8)], now=8.0)
    assert task.time_remaining is not None
    assert (
        AdaptiveTimeRemainingColumn().render(task).plain == TimeRemainingColumn().render(task).plain
    )


def test_adaptive_column_stays_blank_before_anything_completes():
    task = _task(40, [], now=5.0)
    assert AdaptiveTimeRemainingColumn().render(task).plain.strip() == BLANK


def test_adaptive_column_blank_when_total_is_unknown():
    task = _task(None, [(1.0, 3)], now=4.0)
    assert AdaptiveTimeRemainingColumn().render(task).plain.strip() == ""


def test_adaptive_column_compact_formatting():
    task = _task(40, [(4.0, 8)], now=6.0)
    assert AdaptiveTimeRemainingColumn(compact=True).render(task).plain.strip() == "00:24"


def _slow(i):
    time.sleep(0.02)
    return i

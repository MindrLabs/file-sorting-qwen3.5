"""How the tables print a number: shares with Wilson intervals, means and differences with folder-bootstrap ones."""
from __future__ import annotations

import statistics
from typing import Dict, Iterable, List, Optional, Sequence

from stats import FolderInterval, cells_of, cluster_bootstrap, judge_difference, wilson

NOT_RUN = "—"


def share(passed: int, n: int) -> str:
    """`19/20 = 95% [76, 99]`: a share of folders with its Wilson 95% interval."""
    interval = wilson(passed, n)
    if interval is None:
        return NOT_RUN
    return f"{passed}/{n} = {100 * interval.value:.0f}% [{100 * interval.low:.0f}, {100 * interval.high:.0f}]"


def spread(interval: Optional[FolderInterval], digits: int = 2, percent: bool = False) -> str:
    """A mean over folders and its folder-bootstrap 95% interval."""
    if interval is None:
        return NOT_RUN
    scale, unit = (100.0, "%") if percent else (1.0, "")
    value = f"{scale * interval.value:.{digits}f}{unit}"
    if interval.low is None or interval.high is None:
        return f"{value} (too few folders for an interval)"
    return f"{value} [{scale * interval.low:.{digits}f}, {scale * interval.high:.{digits}f}]"


def folder_mean(found: Dict[str, float], digits: int = 2, percent: bool = False) -> str:
    return spread(cluster_bootstrap(cells_of(found)), digits, percent) if found else NOT_RUN


def difference(interval: Optional[FolderInterval]) -> str:
    """`+0.003 [-0.020, +0.030] equivalent`: second minus first, same folders, with the registered verdict."""
    if interval is None or interval.low is None or interval.high is None:
        return NOT_RUN
    return (f"{interval.value:+.3f} [{interval.low:+.3f}, {interval.high:+.3f}] {judge_difference(interval)}"
            f" ({interval.folders} folders)")


def gigabytes(value: Optional[float]) -> str:
    return f"{value:.1f}GB" if value is not None else NOT_RUN


def duration(seconds: float) -> str:
    if seconds < 90:
        return f"{seconds:.0f}s"
    minutes, rest = divmod(round(seconds), 60)
    return f"{minutes}m {rest:02d}s"


def median_time(found: List[float]) -> str:
    """Median with the fastest and slowest folder."""
    if not found:
        return NOT_RUN
    return f"{duration(statistics.median(found))} ({duration(min(found))}–{duration(max(found))})"


def p_value(p: float) -> str:
    return f"{p:.4f}" if p >= 0.0001 else f"{p:.1e}"


def markdown(title: str, header: Sequence[str], rows: Iterable[Sequence[str]], notes: Sequence[str] = ()) -> str:
    lines = [f"### {title}", "", "| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines + ([""] + [f"- {note}" for note in notes] if notes else []))


__all__ = ["NOT_RUN", "difference", "duration", "folder_mean", "gigabytes", "markdown", "median_time", "p_value",
           "share", "spread"]

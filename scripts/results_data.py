"""Read results/*.csv: one file per README line, one row per folder (or one aggregate row per real-folder run)."""
from __future__ import annotations

import csv
import statistics
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

RESULTS = Path(__file__).resolve().parents[1] / "results"
TEXT_COLUMNS = ("line", "folder", "first_plan_sha256")
BREAKDOWN = "first-plan-breakdown"
Row = Dict[str, Optional[float]]


def number(text: str) -> Optional[float]:
    return float(text) if text != "" else None


@lru_cache(maxsize=None)
def table(name: str) -> Tuple[Dict[str, str], ...]:
    """Rows of results/<name>.csv as text; empty when the file is not there."""
    path = RESULTS / f"{name}.csv"
    if not path.is_file():
        return ()
    with path.open(encoding="utf-8", newline="") as handle:
        return tuple(csv.DictReader(handle))


def numbers(row: Dict[str, str]) -> Row:
    return {key: number(value) for key, value in row.items() if key not in TEXT_COLUMNS}


def line(name: str) -> Dict[str, Row]:
    """folder -> numbers of one line."""
    return {row["folder"]: numbers(row) for row in table(name)}


def counts(name: str) -> Dict[str, Row]:
    """folder -> first-plan counts of one line (first-plan-breakdown.csv)."""
    return {row["folder"]: numbers(row) for row in table(BREAKDOWN) if row["line"] == name}


def values(rows: Dict[str, Row], key: str, missing: Optional[float] = None) -> Dict[str, float]:
    """folder -> one number; a folder without it is left out, or gets `missing`."""
    found: Dict[str, float] = {}
    for folder, row in rows.items():
        value = row.get(key)
        value = missing if value is None else value
        if value is not None:
            found[folder] = value
    return found


def passes(name: str, key: str = "usable") -> Dict[str, bool]:
    return {folder: value >= 1 for folder, value in values(line(name), key, 0.0).items()}


def passed(name: str, key: str = "usable") -> Tuple[int, int]:
    """(folders that passed, folders run)."""
    found = passes(name, key)
    return sum(found.values()), len(found)


def mean(rows: Dict[str, Row], key: str) -> Optional[float]:
    found = list(values(rows, key).values())
    return statistics.mean(found) if found else None


def total(rows: Dict[str, Row], key: str) -> float:
    return sum(values(rows, key).values())


def seconds(name: str) -> List[float]:
    return sorted(values(line(name), "gen_sec").values())


def peak_gb(name: str) -> Optional[float]:
    """The largest peak over the line's folders, 1GB = 1024MB."""
    found = values(line(name), "peak_mb").values()
    return max(found) / 1024 if found else None


def first_plans(name: str) -> Dict[str, str]:
    return {row["folder"]: row["first_plan_sha256"] for row in table(name) if row.get("first_plan_sha256")}


def provenance(name: str) -> Dict[str, str]:
    return next((row for row in table("provenance") if row["line"] == name), {})


def failed_runs(name: str) -> Dict[str, str]:
    """folder -> why its run did not complete (provenance.csv `failed_runs`, `folder: status (error kind)`)."""
    found = [entry.split(": ", 1) for entry in provenance(name).get("failed_runs", "").split(";") if ": " in entry]
    return {folder: reason for folder, reason in found}


__all__ = ["RESULTS", "Row", "counts", "failed_runs", "first_plans", "line", "mean", "passed", "passes", "peak_gb", "provenance",
           "seconds", "table", "total", "values"]

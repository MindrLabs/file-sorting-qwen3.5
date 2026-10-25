"""The results table: one row per line and folder. After `line,folder` come the published quality keys in
the order the results store them, then time, memory and the hash of the first plan the person saw."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable, List

QUALITY_KEYS = (
    "step1_tool", "step2_format", "step3_by_name", "step4_by_content", "step5_leaves_alone", "step7_stops",
    "approved_as_is", "edited_lines", "calls_after_done", "step6_feedback", "rounds_to_fix",
    "wrong_merge_pairs", "pair_recall", "coverage", "pair_precision", "pair_f1", "wrong_share",
    "usable_10", "usable", "usable_30", "approvals", "empty_plans", "ari", "ami",
    "final_pair_f1", "final_coverage", "session_wrong_share",
)
COLUMNS = ("line", "folder", *QUALITY_KEYS, "gen_sec", "peak_mb", "first_plan_sha256")


def first_plan_sha256(bundle: Dict[str, Any]) -> str:
    """The plan shown at the first approval stop, as UTF-8; empty when the run never stopped."""
    stops = bundle.get("stops") or []
    return hashlib.sha256(stops[0]["plan"].encode("utf-8")).hexdigest() if stops else ""


def cell(value: Any) -> str:
    """A blank for a value nobody knows; numbers as the results file writes them."""
    return "" if value is None else str(value)


def table_row(line: str, folder: str, quality: Dict[str, Any], runtime: Dict[str, Any],
              bundle: Dict[str, Any]) -> Dict[str, str]:
    values = {"line": line, "folder": folder, **{key: quality.get(key) for key in QUALITY_KEYS},
              "gen_sec": runtime.get("gen_sec"), "peak_mb": runtime.get("peak_mb"),
              "first_plan_sha256": first_plan_sha256(bundle)}
    return {column: cell(values[column]) for column in COLUMNS}


def write_table(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def read_table(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


__all__ = ["COLUMNS", "QUALITY_KEYS", "first_plan_sha256", "read_table", "table_row", "write_table"]

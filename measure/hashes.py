"""First-plan hashes, one `<sha256>  <folder>` line per folder with `#` lines for notes, and the check of a
results table against them: the same hash means the model showed the same plan, byte for byte."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from .table import read_table

Row = Dict[str, str]


def write_hashes(path: Path, rows: List[Row], notes: List[str]) -> None:
    """A run that never reached the approval stop has no first plan: it becomes a note, not a hash."""
    ordered = sorted(rows, key=lambda row: row["folder"])
    unplanned = [f"{row['folder']}: the recorded run never reached the approval stop"
                 for row in ordered if not row["first_plan_sha256"]]
    hashes = [f"{row['first_plan_sha256']}  {row['folder']}" for row in ordered if row["first_plan_sha256"]]
    path.write_text("\n".join([f"# {note}" for note in notes + unplanned] + hashes) + "\n", encoding="utf-8")


def read_hashes(path: Path) -> Dict[str, str]:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if not line.startswith("#")]
    pairs = [line.split(None, 1) for line in lines]
    return {pair[1].strip(): pair[0] for pair in pairs if len(pair) == 2}


def rows_for(rows: List[Row], line: str) -> List[Row]:
    """The table's rows for this line; a table that holds a single line is taken whatever it is called."""
    named = [row for row in rows if row["line"] == line]
    if named or len({row["line"] for row in rows}) != 1:
        return named
    return rows


def verdict(row: Row, expected: Dict[str, str]) -> Tuple[str, bool]:
    recorded, found = expected.get(row["folder"]), row["first_plan_sha256"]
    if recorded is None:
        return f"{row['folder']}  no recorded first plan", False
    if found == recorded:
        return f"{row['folder']}  same", True
    return f"{row['folder']}  differs: {found[:12] or 'no plan'} vs recorded {recorded[:12]}", False


def check(table: Path, hashes: Path) -> Tuple[List[str], bool]:
    """A line per compared row and a summary; true when every row matched and at least one was compared."""
    line, expected = hashes.stem, read_hashes(hashes)
    rows = rows_for(read_table(table), line)
    if not rows:
        return [f"{table} has no rows for {line}"], False
    results = [verdict(row, expected) for row in rows]
    matched = sum(1 for _, same in results if same)
    missing = sorted(set(expected) - {row["folder"] for row in rows})
    summary = f"{line}: {matched} of {len(rows)} first plans match byte for byte"
    summary += f" ({len(missing)} recorded folders not in the table)" if missing else ""
    return [text for text, _ in results] + [summary], matched == len(rows)


__all__ = ["check", "read_hashes", "write_hashes"]

"""`check` compares a table's first-plan hashes with first-plans/<line>.sha256, folder by folder."""
from fixtures import run_tests, scratch_root

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from measure.__main__ import main  # noqa: E402
from measure.hashes import check, read_hashes, write_hashes  # noqa: E402
from measure.table import COLUMNS, write_table  # noqa: E402

FIRST_PLANS = Path(__file__).resolve().parents[1] / "measure" / "first-plans"
LINE = "dev-9b-q4km-names-about-vote-8k"
A, B, C = "a" * 64, "b" * 64, "c" * 64
DEV = [f"dev-{number:02d}" for number in range(1, 13)]


def row(line: str, folder: str, digest: str) -> Dict[str, str]:
    return {**{column: "" for column in COLUMNS}, "line": line, "folder": folder, "first_plan_sha256": digest}


def files(rows: List[Dict[str, str]], recorded: Dict[str, str]) -> Tuple[Path, Path]:
    folder = scratch_root({})
    table, hashes = folder / "results.csv", folder / f"{LINE}.sha256"
    write_table(table, rows)
    write_hashes(hashes, [row("any", name, digest) for name, digest in recorded.items()], ["a note"])
    return table, hashes


def test_the_shipped_lines_hold_a_hash_per_recorded_folder():
    lines = {path.stem: read_hashes(path) for path in FIRST_PLANS.glob("*.sha256")}
    assert len(lines) == 12 and all(re.fullmatch(r"(mac-)?dev-\db-q4km-names-about(-vote)?(-8k)?", name) for name in lines)
    assert all(sorted(hashes) == DEV for name, hashes in lines.items() if not name.startswith("mac-"))
    assert all(re.fullmatch(r"[0-9a-f]{64}", digest) for hashes in lines.values() for digest in hashes.values())


def test_the_hash_file_keeps_notes_and_unplanned_runs_out_of_the_hashes():
    _, hashes = files([], {"dev-02": B, "dev-01": A, "dev-03": ""})
    assert hashes.read_text(encoding="utf-8").splitlines() == [
        "# a note", "# dev-03: the recorded run never reached the approval stop", f"{A}  dev-01", f"{B}  dev-02"]
    assert read_hashes(hashes) == {"dev-01": A, "dev-02": B}


def test_the_same_first_plans_pass_and_folders_not_run_are_counted():
    lines, same = check(*files([row(LINE, "dev-01", A)], {"dev-01": A, "dev-02": B}))
    assert same and lines == ["dev-01  same",
                              f"{LINE}: 1 of 1 first plans match byte for byte (1 recorded folders not in the table)"]


def test_a_different_or_missing_first_plan_fails():
    lines, same = check(*files([row(LINE, "dev-01", C), row(LINE, "dev-02", "")], {"dev-01": A, "dev-02": B}))
    assert not same and lines[0] == f"dev-01  differs: {C[:12]} vs recorded {A[:12]}"
    assert lines[1] == f"dev-02  differs: no plan vs recorded {B[:12]}"


def test_a_table_of_one_line_is_compared_whatever_it_is_called():
    assert check(*files([row("organize", "dev-01", A)], {"dev-01": A}))[1]


def test_a_table_of_other_lines_only_is_refused():
    lines, same = check(*files([row("organize", "dev-01", A), row("organize-quick", "dev-01", A)], {"dev-01": A}))
    assert not same and lines == [lines[0]] and f"no rows for {LINE}" in lines[0]


def test_the_command_exits_with_the_verdict():
    table, hashes = files([row(LINE, "dev-01", A)], {"dev-01": A})
    assert main(["check", str(table), str(hashes)]) == 0
    write_table(table, [row(LINE, "dev-01", C)])
    assert main(["check", str(table), str(hashes)]) == 1


run_tests(globals())

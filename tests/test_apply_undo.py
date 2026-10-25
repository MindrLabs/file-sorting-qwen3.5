from fixtures import run_tests, scratch_root, tree

import json
import os
import subprocess
import sys
from pathlib import Path

from journal import RunJournal, undo_last
import moving
from moving import apply_plan
from plan import parse_plan
from preview import preview_plan
from workspace_lock import workspace_lock

ORGANIZER = Path(__file__).resolve().parents[1] / "tools" / "organizer.py"
FILES = {"notes/kickoff.md": "rhythm game kickoff", "budget.csv": "gpu,4090", "photo.jpg": "x"}


def test_an_approved_plan_moves_files_and_undo_puts_them_back():
    root = scratch_root(FILES)
    report = apply_plan(root, parse_plan("photo.jpg => rhythm-game  # cover art\nbudget.csv => infra"))
    assert tree(root) == {"notes/kickoff.md": "rhythm game kickoff", "infra/budget.csv": "gpu,4090", "rhythm-game/photo.jpg": "x"}
    assert "2 moved, 0 skipped" in report
    undo_last(root)
    assert tree(root) == FILES
    assert not (root / "rhythm-game").exists() and not (root / "infra").exists()


def test_undo_goes_back_one_run_at_a_time():
    root = scratch_root(FILES)
    apply_plan(root, parse_plan("budget.csv => infra"))
    apply_plan(root, parse_plan("photo.jpg => infra"))
    undo_last(root)
    assert set(tree(root)) == {"notes/kickoff.md", "infra/budget.csv", "photo.jpg"}
    undo_last(root)
    assert tree(root) == FILES
    assert undo_last(root) == "Nothing to undo."


def test_undo_never_overwrites_a_file_that_came_back():
    root = scratch_root(FILES)
    apply_plan(root, parse_plan("budget.csv => infra"))
    (root / "budget.csv").write_text("newer", encoding="utf-8")
    assert "is taken again" in undo_last(root)
    assert tree(root)["budget.csv"] == "newer" and tree(root)["infra/budget.csv"] == "gpu,4090"


def test_files_the_person_cut_from_the_plan_are_named_in_the_report():
    root = scratch_root(FILES)
    shown = preview_plan(root, parse_plan("./budget.csv => infra\nphoto.jpg => infra\nmissing.txt => infra"))
    report = apply_plan(root, parse_plan("budget.csv => infra"), parse_plan(shown))
    assert "Left where they are: photo.jpg." in report and report.endswith("The undo tab puts them back.")
    nothing = apply_plan(root, parse_plan("# nothing to move"))
    assert nothing == "0 moved, 0 skipped."


def test_a_rejection_moves_nothing_and_returns_the_feedback():
    root = scratch_root(FILES)
    report = apply_plan(root, parse_plan("REJECT: keep photos where they are\nand group by year"))
    assert tree(root) == FILES
    assert "Feedback: keep photos where they are\nand group by year" in report


def test_unreadable_lines_are_reported_not_guessed():
    root = scratch_root(FILES)
    report = apply_plan(root, parse_plan("# grouping by project\nbudget.csv -> infra\nbudget.csv => infra"))
    assert "budget.csv -> infra: not in `path => project` form" in report
    assert "1 moved, 1 skipped" in report


def test_the_cli_reports_errors_where_the_workflow_reads_them():
    root = scratch_root(FILES)
    run = subprocess.run([sys.executable, str(ORGANIZER), "scan", str(root / "missing")], capture_output=True, text=True)
    assert run.returncode == 1 and "error: not a folder" in run.stdout
    run = subprocess.run([sys.executable, str(ORGANIZER), "apply", str(root), "budget.csv => infra"], capture_output=True, text=True)
    assert run.returncode == 0 and "1 moved" in run.stdout


def test_an_apply_waits_while_another_one_holds_the_folder():
    root = scratch_root(FILES)
    with workspace_lock(root):
        waiting = subprocess.Popen([sys.executable, str(ORGANIZER), "apply", str(root), "budget.csv => infra"],
                                   stdout=subprocess.PIPE, text=True)
        try:
            waiting.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        assert waiting.poll() is None and (root / "budget.csv").exists()
    assert waiting.wait(timeout=10) == 0 and (root / "infra" / "budget.csv").exists()


def test_only_plain_top_level_files_move_whoever_wrote_the_line():
    root = scratch_root({**FILES, ".env": "secret"})
    lines = "notes/kickoff.md => rhythm-game\n.env => infra\nbudget.csv => infra"
    report = apply_plan(root, parse_plan(lines))
    assert "notes/kickoff.md: only top-level files are sorted" in report
    assert ".env: hidden files are left alone" in report and "1 moved, 2 skipped" in report
    assert set(tree(root)) == {"notes/kickoff.md", ".env", "infra/budget.csv", "photo.jpg"}
    assert preview_plan(root, parse_plan("notes/kickoff.md => x")).startswith("# skip:")


LOCKED = []  # folders made read-only by a test, made writable again at the end so the scratch can be removed


def locked(folder: Path) -> None:
    folder.chmod(0o555)
    LOCKED.append(folder)


def test_a_failing_move_is_skipped_and_the_rest_of_the_plan_still_runs():
    root = scratch_root({**FILES, "locked/.keep": ""})
    locked(root / "locked")
    report = apply_plan(root, parse_plan("budget.csv => locked\nphoto.jpg => pictures"))
    assert "budget.csv: Permission denied" in report and "1 moved, 1 skipped" in report
    assert (root / "budget.csv").exists() and (root / "pictures" / "photo.jpg").exists()
    undo_last(root)
    assert (root / "photo.jpg").exists() and not (root / "pictures").exists()


def test_undo_skips_a_file_it_cannot_put_back_and_the_run_before_stays_reachable():
    root = scratch_root(FILES)
    apply_plan(root, parse_plan("photo.jpg => pictures"))
    apply_plan(root, parse_plan("budget.csv => infra"))
    locked(root / "infra")
    assert "skipped infra/budget.csv: Permission denied" in undo_last(root)
    assert "restored photo.jpg" in undo_last(root)


def test_the_journal_holds_a_move_before_it_happens_and_drops_it_when_it_fails():
    root = scratch_root(FILES)
    journal = RunJournal(root)
    journal.begin("budget.csv", "infra/budget.csv", "infra")
    record = json.loads(journal.path.read_text(encoding="utf-8"))
    assert record == {"moves": [{"from": "budget.csv", "to": "infra/budget.csv"}], "created_dirs": ["infra"]}
    path = journal.path
    journal.cancel()
    assert not path.exists() and undo_last(root) == "Nothing to undo."



def test_a_broken_symlink_at_the_target_is_a_taken_name():
    root = scratch_root(FILES)
    (root / "infra").mkdir()
    os.symlink("/nonexistent", root / "infra" / "budget.csv")
    report = apply_plan(root, parse_plan("budget.csv => infra"))
    assert "already exists" in report and (root / "budget.csv").exists()
    assert os.path.islink(root / "infra" / "budget.csv")


def test_a_run_killed_after_its_record_but_before_the_move_undoes_cleanly():
    root = scratch_root(FILES)
    RunJournal(root).begin("budget.csv", "infra/budget.csv", "infra")
    (root / "infra").mkdir()  # the kill came after mkdir, before the file moved
    report = undo_last(root)
    assert "skipped infra/budget.csv: no longer there" in report and "removed empty folder infra/" in report
    assert tree(root) == FILES


def test_a_move_that_fails_into_a_new_folder_leaves_neither_folder_nor_record():
    root = scratch_root(FILES)
    real_place = moving.place

    def refuse_budget(source, target):
        if source.name == "budget.csv":
            raise PermissionError(13, "Permission denied")
        real_place(source, target)

    moving.place = refuse_budget
    try:
        report = apply_plan(root, parse_plan("photo.jpg => pictures\nbudget.csv => infra"))
    finally:
        moving.place = real_place
    assert "budget.csv: Permission denied" in report and not (root / "infra").exists()
    assert undo_last(root) == "restored photo.jpg\nremoved empty folder pictures/"


def test_a_damaged_record_is_set_aside_and_the_run_before_is_undone():
    root = scratch_root(FILES)
    apply_plan(root, parse_plan("budget.csv => infra"))
    runs = root / ".organizer" / "runs"
    (runs / "99999999-999999-999999.json").write_text('{"moves": [{"from": "a', encoding="utf-8")
    report = undo_last(root)
    assert "skipped a damaged undo record" in report and "restored budget.csv" in report
    assert tree(root) == FILES and list(runs.glob("*.broken"))


try:
    run_tests(globals())
finally:
    for folder in LOCKED:
        folder.chmod(0o755)

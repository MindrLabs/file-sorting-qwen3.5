from fixtures import run_tests, scratch_root, tree

import os

from moving import apply_plan
from plan import parse_plan
from reading import peek, top_level
from safe_paths import OutsideRoot, inside


def raises_outside(action) -> bool:
    try:
        action()
    except OutsideRoot:
        return True
    return False


def test_paths_that_climb_out_of_root_are_refused():
    root = scratch_root({"a.md": "a"})
    assert raises_outside(lambda: inside(root, "../secret"))
    assert raises_outside(lambda: inside(root, "/etc/passwd"))
    assert raises_outside(lambda: peek(root, "../../etc/hosts"))


def test_symlinks_and_the_journal_are_off_limits():
    root = scratch_root({"a.md": "a", ".organizer/runs/x.json": "{}"})
    os.symlink("/etc", root / "link")
    assert raises_outside(lambda: inside(root, "link"))
    assert raises_outside(lambda: inside(root, ".organizer/runs/x.json"))
    files, folders = top_level(root)
    assert "link" not in files + folders and ".organizer" not in folders


def test_a_plan_cannot_move_outside_or_nest_projects():
    root = scratch_root({"a.md": "a"})
    report = apply_plan(root, parse_plan("a.md => ../escape\na.md => x/y\na.md => .hidden\n../b => p"))
    assert tree(root) == {"a.md": "a"}
    assert "0 moved, 4 skipped" in report


def test_a_move_never_overwrites():
    root = scratch_root({"a.md": "new", "docs/a.md": "old"})
    report = apply_plan(root, parse_plan("a.md => docs"))
    assert tree(root) == {"a.md": "new", "docs/a.md": "old"}
    assert "docs/a.md already exists" in report


def test_peek_reads_only_the_head_of_text_files():
    root = scratch_root({"long.txt": "x" * 5000, "photo.jpg": "binary"})
    assert len(peek(root, "long.txt")) == 2048
    assert "not a text file" in peek(root, "photo.jpg")


run_tests(globals())

from fixtures import run_tests, scratch_root, tree

from moving import apply_plan
from plan import parse_plan
from preview import preview_plan

FILES = {"a.md": "a", "b.md": "b", "docs/b.md": "old"}


def test_preview_moves_nothing_and_comments_out_what_would_be_skipped():
    root = scratch_root(FILES)
    shown = preview_plan(root, parse_plan("a.md => notes/  # meeting notes\nb.md => docs\nc.md => notes\nbroken line"))
    assert tree(root) == FILES
    assert shown.splitlines() == [
        "a.md => notes  # meeting notes",
        "# skip: b.md => docs  (docs/b.md already exists)",
        "# skip: c.md => notes  (not a file)",
        "# unreadable, not `path => project`: broken line",
    ]


def test_an_approved_preview_runs_exactly_its_uncommented_lines():
    root = scratch_root(FILES)
    report = apply_plan(root, parse_plan(preview_plan(root, parse_plan("a.md => notes\nb.md => docs"))))
    assert "1 moved, 0 skipped" in report
    assert tree(root) == {"notes/a.md": "a", "b.md": "b", "docs/b.md": "old"}


run_tests(globals())

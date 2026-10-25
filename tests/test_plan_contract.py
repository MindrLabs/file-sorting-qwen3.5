"""The scorer reads a plan with its own parser, apart from the harness. On every line the harness shows or
the person types in the box, both must see the same moves, or the scores describe another plan."""
from fixtures import run_tests, scratch_root

import sys
from pathlib import Path

from harness_steps import assemble
from plan import parse_plan
from preview import preview_plan
from shown_plan import normalized

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from measure.reviewer import plan_moves  # noqa: E402

FILES = {"a.md": "x", "notes (2).md": "x", "guest list final.csv": "x", "docs": "a file, not a folder"}


def harness_moves(root, text):
    return sorted((normalized(root, move.source), move.project) for move in parse_plan(text).moves)


def scorer_moves(text):
    return sorted((move.source, move.project) for move in plan_moves(text))


def test_the_assembled_plan_reads_the_same_to_the_scorer():
    picks = {"a.md": "notes", "notes (2).md": "notes", "guest list final.csv": "wedding", "b.md": None}
    text = assemble({"picks": picks})
    assert harness_moves(scratch_root(FILES), text) == scorer_moves(text)


def test_the_previewed_plan_with_reasons_and_skips_reads_the_same_to_the_scorer():
    root = scratch_root(FILES)
    text = preview_plan(root, parse_plan("a.md => notes/  # meeting notes\nguest list final.csv => docs\nbroken"))
    assert text.splitlines()[1].startswith("# skip:")
    assert harness_moves(root, text) == scorer_moves(text) == [("a.md", "notes")]


def test_lines_the_person_types_read_the_same_to_the_scorer():
    root = scratch_root(FILES)
    text = "./a.md => notes/  # mine\n# a.md => elsewhere\nnotes (2).md =>   notes\n\nno arrow here"
    assert harness_moves(root, text) == scorer_moves(text) == [("a.md", "notes"), ("notes (2).md", "notes")]


run_tests(globals())

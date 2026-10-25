"""The stand-in reviewer answers the approval stop as a careful person would."""
from fixtures import run_tests

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from measure.reviewer import answer, judge, with_ignored  # noqa: E402

ANSWERS = {"a.md": "game", "b.md": "game", "c.csv": "tax", "d.csv": "tax", "e.txt": None}
KEEP = {"game/README.md"}


def test_a_plan_with_its_own_folder_names_and_nothing_wrong_is_approved():
    assert answer("a.md => rhythm\nb.md => rhythm\nc.csv => taxes", "edit", 0, ANSWERS, KEEP) is None


def test_a_timid_but_right_plan_is_still_approved():
    assert answer("a.md => g", "reject", 0, ANSWERS, KEEP) is None


def test_edit_moves_a_stray_file_to_its_project_folder_and_drops_what_should_stay():
    plan = "a.md => g\nb.md => g\nc.csv => t\nd.csv => g  # wrong\ne.txt => g\ngame/README.md => misc"
    verdict = judge(plan, ANSWERS, KEEP)
    assert verdict.edited_lines == 3
    assert verdict.fixed_plan.splitlines() == ["a.md => g", "b.md => g", "c.csv => t", "d.csv => t"]


def test_a_file_listed_twice_is_moved_once_in_the_edited_plan():
    verdict = judge("a.md => g\nb.md => g\nc.csv => g\nc.csv => t\nd.csv => t", ANSWERS, KEEP)
    assert verdict.fixed_plan.splitlines() == ["a.md => g", "b.md => g", "c.csv => t", "d.csv => t"]


def test_two_projects_never_end_up_sharing_a_folder_name():
    verdict = judge("a.md => stuff\nb.md => stuff\nc.csv => stuff\nd.csv => stuff", ANSWERS, KEEP)
    assert verdict.fixed_plan.splitlines() == ["a.md => stuff", "b.md => stuff", "c.csv => tax", "d.csv => tax"]


def test_skip_comments_move_nothing_and_are_never_wrong():
    assert answer("# skip: e.txt cannot move\na.md => g\nb.md => g", "edit", 0, ANSWERS, KEEP) is None


def test_reject_names_the_files_without_giving_the_answer_key_away():
    text = answer("a.md => g\nc.csv => g\ne.txt => g", "reject", 0, ANSWERS, KEEP)
    assert text is not None and text.startswith("REJECT:")
    assert "c.csv does not belong in g; it goes with d.csv" in text and "leave e.txt where it is" in text
    assert "tax" not in text


def test_reject_gives_up_after_three_times_and_approves():
    assert answer("c.csv => g\na.md => g", "reject", 3, ANSWERS, KEEP) is None


def test_edit_never_sends_an_empty_answer_that_would_mean_approve():
    assert answer("e.txt => g", "edit", 0, ANSWERS, KEEP) == "# nothing to move"


def test_a_file_left_out_of_scoring_is_never_wrong_and_never_edited():
    answers = with_ignored(ANSWERS, ["c.csv"])
    verdict = judge("a.md => g\nb.md => g\nc.csv => g\nd.csv => t", answers, KEEP)
    assert verdict.wrong == [] and "c.csv => g" in verdict.fixed_plan


run_tests(globals())

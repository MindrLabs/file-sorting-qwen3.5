"""The ported scorer gives the published numbers: two recorded runs scored again, a run file re-read, and a
run without a tool-call log, which leaves the keys that read the log blank."""
from fixtures import run_tests, scratch_root

import hashlib
import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from measure.final import score_run  # noqa: E402
from measure.folders import labels  # noqa: E402
from measure.hashes import read_hashes  # noqa: E402
from measure.rescore import rescore  # noqa: E402
from measure.reviewer import answer, with_ignored  # noqa: E402
from measure.table import QUALITY_KEYS  # noqa: E402

FIRST_PLANS = Path(__file__).resolve().parents[1] / "measure" / "first-plans"
# Two recorded first plans (RTX 4090, four asks per file, 8K context), byte for byte as the person saw them.
PLAN_9B_DEV01 = "\n".join([
    "SP-214_survivor_pension_application_scan.pdf => survivor-pension", "bank-closures-letter-template.docx => bank-closures",
    "bank_closures_notes.txt => bank-closures", "bank_closures_tracker.xlsx => bank-closures", "call_log.txt => bank-closures",
    "draft_v2.md => maple-street-sale", "ideas.txt => solo-cooking", "maple-street-staging-photos.zip => maple-street-sale",
    "maple_street_appraisal_2026-09.pdf => maple-street-sale", "maple_street_front_IMG_4412.heic => maple-street-sale",
    "maple_street_repairs_quote_final (2).docx => maple-street-sale", "notes_oct.txt => survivor-pension",
    "scratch.txt => survivor-pension", "solo-cooking-grocery-list.txt => solo-cooking",
    "solo_cooking_freezer_inventory.csv => solo-cooking", "solo_cooking_meal_plan_week3.md => solo-cooking",
    "survivor_pension_award_letter_scan.pdf => survivor-pension", "survivor_pension_checklist.md => survivor-pension",
    "todo.txt => solo-cooking", "untitled.md => maple-street-sale"])
PLAN_2B_DEV04 = "\n".join([
    "README.md => job-applications", "UI_claim_determination_letter_scan.pdf => unemployment-claims",
    "brew_kettle_manual_SS_20gal.pdf => garage-homebrew", "cover_letter_larkspur_analytics_v2.docx => job-applications",
    "document (3).docx => unemployment-claims", "draft.txt => job-applications", "followup.txt => job-applications",
    "garage_brew_shelf_IMG_4412.heic => garage-homebrew", "hefeweizen_recipe_batch1.md => garage-homebrew",
    "homebrew_corner_shopping_list.txt => garage-homebrew", "interview_prep_larkspur.md => job-applications",
    "job_applications_tracker.xlsx => job-applications", "notes.txt => garage-homebrew",
    "portfolio-hero-screenshot@2x.png => portfolio-refresh", "scratch.txt => garage-homebrew", "todo.md => portfolio-refresh",
    "unemployment_work_search_record.xlsx => unemployment-claims", "weekly_certification_log_oct.csv => unemployment-claims"])
# What the stand-in reviewer sent back for the 2B plan in that run: one line fixed, one removed.
ANSWER_2B_DEV04 = PLAN_2B_DEV04.replace("README.md => job-applications", "README.md => portfolio-refresh").replace(
    "document (3).docx => unemployment-claims\n", "")
RECORDED_9B_DEV01 = {
    "step1_tool": 1, "step2_format": 1, "step3_by_name": 1, "step4_by_content": 0, "step5_leaves_alone": 1, "step7_stops": 1,
    "approved_as_is": 1, "edited_lines": 0, "calls_after_done": 1, "step6_feedback": None, "rounds_to_fix": None,
    "wrong_merge_pairs": 0, "pair_recall": 0.569, "coverage": 0.769, "pair_precision": 1.0, "pair_f1": 0.726,
    "wrong_share": 0.0, "usable_10": 1, "usable": 1, "usable_30": 1, "approvals": 1, "empty_plans": 0, "ari": 0.706,
    "ami": 0.771, "final_pair_f1": 0.726, "final_coverage": 0.769, "session_wrong_share": 0.0}
RECORDED_2B_DEV04 = {
    "step1_tool": 1, "step2_format": 1, "step3_by_name": 1, "step4_by_content": 0, "step5_leaves_alone": 0, "step7_stops": 1,
    "approved_as_is": 0, "edited_lines": 2, "calls_after_done": 1, "step6_feedback": None, "rounds_to_fix": None,
    "wrong_merge_pairs": 5, "pair_recall": 0.296, "coverage": 0.567, "pair_precision": 0.784, "pair_f1": 0.43,
    "wrong_share": 0.111, "usable_10": 0, "usable": 0, "usable_30": 0, "approvals": 1, "empty_plans": 0, "ari": 0.397,
    "ami": 0.473, "final_pair_f1": 0.481, "final_coverage": 0.567, "session_wrong_share": 0.111}
# Keys that read the tool-call log, and the usable bars that hinge on step 7 once everything else passes.
BLANK_WITHOUT_LOG = ("step1_tool", "step7_stops", "calls_after_done", "empty_plans", "usable_10", "usable", "usable_30")


def recorded_bundle(plan: str, reply: Optional[str]) -> dict:
    """The run as recorded: its stop, the journal of the plan it applied, and the tool log cut to what the
    ladder reads (a tool ran, the apply moved files, one call came after)."""
    pairs = [line.split(" => ") for line in (reply or plan).splitlines()]
    moves = [{"from": source, "to": f"{project}/{source}"} for source, project in pairs]
    log = [{"command": "scan"}, {"command": "preview"},
           {"command": "apply", "output": f"{len(moves)} moved, 0 skipped."}, {"command": "rework"}]
    return {"stops": [{"plan": plan, "answer": reply}], "journals": [{"moves": moves}], "events": log}


def test_the_embedded_plans_are_the_recorded_ones():
    for line, folder, plan in (("dev-9b-q4km-names-about-vote-8k", "dev-01", PLAN_9B_DEV01),
                               ("dev-2b-q4km-names-about-vote-8k", "dev-04", PLAN_2B_DEV04)):
        assert read_hashes(FIRST_PLANS / f"{line}.sha256")[folder] == hashlib.sha256(plan.encode("utf-8")).hexdigest()


def test_the_reviewer_answers_as_it_did_in_the_recorded_runs():
    for folder, plan, reply in (("dev-01", PLAN_9B_DEV01, None), ("dev-04", PLAN_2B_DEV04, ANSWER_2B_DEV04)):
        expect = labels(folder)
        keep = set(expect["keep_in_place"])
        assert answer(plan, "edit", 0, with_ignored(expect["answers"], expect["ignore"]), keep) == reply


def test_two_recorded_runs_score_as_published_in_the_table_order():
    scored = score_run(recorded_bundle(PLAN_9B_DEV01, None), labels("dev-01"))
    assert scored == RECORDED_9B_DEV01 and list(scored) == list(QUALITY_KEYS)
    assert score_run(recorded_bundle(PLAN_2B_DEV04, ANSWER_2B_DEV04), labels("dev-04")) == RECORDED_2B_DEV04


def test_without_a_tool_log_the_keys_that_read_it_are_blank():
    scored = score_run({**recorded_bundle(PLAN_9B_DEV01, None), "events": None}, labels("dev-01"))
    assert scored == {key: None if key in BLANK_WITHOUT_LOG else value for key, value in RECORDED_9B_DEV01.items()}
    short = score_run({**recorded_bundle(PLAN_2B_DEV04, ANSWER_2B_DEV04), "events": None}, labels("dev-04"))
    assert short is not None and short["usable"] == 0 and short["step1_tool"] is None  # too little moved: 0 either way


def test_a_run_file_is_scored_again_and_compared_key_by_key():
    folder = scratch_root({})
    (folder / "runs").mkdir()
    (folder / "runs" / "dev-04.json").write_text(json.dumps(recorded_bundle(PLAN_2B_DEV04, ANSWER_2B_DEV04)))
    job = {"input_id": "dev-04-edit", "expect": {"fixture": "dev-04/files", **labels("dev-04")},
           "runtime": {"gen_sec": 14.022, "peak_mb": 2300.0}, "artifact": {"path": "runs/dev-04.json"}}
    run_file = folder / "run.json"
    run_file.write_text(json.dumps({"jobs": [{**job, "quality": RECORDED_2B_DEV04}]}))
    result = rescore(run_file, "dev-2b-q4km-names-about-vote-8k")
    assert (result.matched, result.jobs) == (1, 1) and result.rows[0]["folder"] == "dev-04"
    assert result.rows[0]["gen_sec"] == "14.022" and result.rows[0]["step6_feedback"] == ""
    run_file.write_text(json.dumps({"jobs": [{**job, "quality": {**RECORDED_2B_DEV04, "pair_f1": 0.5}}]}))
    assert rescore(run_file).matched == 0 and "pair_f1 0.5 -> 0.43" in rescore(run_file).notes[0]


run_tests(globals())

"""The published ladder: one 0/1 per step a run climbed, judged against the labelled answer.

Steps 1-5 read the first plan, the one the model made before any person said anything. Step 6 reads the
plans after a rejection that named the wrong files. Step 7 reads what came after the last plan that moved
files (tool_calls.py). A step that cannot apply to this run is None, and so is a value nobody recorded.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Dict, List, Optional, Set

from .agreement import agreement
from .reviewer import ANY, Answers, Verdict, folder_names, judge, plan_moves, with_ignored
from .tool_calls import Events, empty_plans, log_steps

COVERAGE_BAR = 0.6   # share of a file group the plan must move to count as doing the step
USABLE_WRONG_SHARE = 0.2  # a person fixes at most one line in five of a usable first plan
# The registered bar and two others, so a reader can see how much the verdict leans on 20%.
USABLE_SHARES = {"usable_10": 0.1, "usable": USABLE_WRONG_SHARE, "usable_30": 0.3}
UNREADABLE = "# unreadable"


@dataclass(frozen=True)
class FirstPlan:
    """One run as the ladder reads it: the labels once `ignore` is applied, every plan the person saw,
    the tool-call log (None when none was kept), and where the first plan put each scored file."""
    answers: Answers
    known_by: Dict[str, str]
    keep: Set[str]
    stops: List[Dict[str, Any]]
    events: Events
    plan: str
    where: Dict[str, str]


def placed(plan: str) -> Dict[str, str]:
    return {move.source: move.project for move in plan_moves(plan)}


def read_run(bundle: Dict[str, Any], expect: Dict[str, Any]) -> Optional[FirstPlan]:
    answers = expect.get("answers")
    if not isinstance(answers, dict):
        return None
    answers = with_ignored(answers, list(expect.get("ignore") or []))
    stops = bundle.get("stops", [])
    plan = stops[0]["plan"] if stops else ""
    where = {name: folder for name, folder in placed(plan).items() if answers.get(name) != ANY}
    return FirstPlan(answers, expect.get("known_by") or {}, set(expect.get("keep_in_place") or []),
                     stops, bundle.get("events", []), plan, where)


def group_right(files: List[str], where: Dict[str, str], names: Dict[str, str],
                answers: Answers) -> Optional[int]:
    """Every file of the group that moved went to the folder the reviewer would accept, and enough moved."""
    if not files:
        return None
    moved = [name for name in files if name in where]
    wrong = [name for name in moved if where[name] != names.get(str(answers[name]))]
    return int(not wrong and len(moved) / len(files) >= COVERAGE_BAR)


def leaves_alone(where: Dict[str, str], answers: Answers, keep: Set[str]) -> int:
    return int(not any(name in keep or not answers.get(name) for name in where))


def known_by(run: FirstPlan, kind: str) -> List[str]:
    return [name for name, project in run.answers.items()
            if project and project != ANY and run.known_by.get(name) == kind]


def pair_scores(where: Dict[str, str], answers: Answers) -> Dict[str, Any]:
    labelled = sorted(name for name, project in answers.items() if project and project != ANY)
    together = [(a, b) for a, b in combinations(labelled, 2) if answers[a] == answers[b]]
    kept = [(a, b) for a, b in together if a in where and b in where and where[a] == where[b]]
    moved = [name for name in labelled if name in where]
    wrong = [(a, b) for a, b in combinations(sorted(moved), 2)
             if where[a] == where[b] and answers[a] != answers[b]]
    recall = len(kept) / len(together) if together else None
    coverage = round(len(moved) / len(labelled), 3) if labelled else None
    return {"wrong_merge_pairs": len(wrong), "pair_recall": rounded(recall), "coverage": coverage,
            **pair_precision_f1(where, answers, recall)}


def pair_precision_f1(where: Dict[str, str], answers: Answers, recall: Optional[float]) -> Dict[str, Any]:
    """Every pair the plan put in one folder, unknown and organized files included: a pair is right only
    when both files carry the same label."""
    shared = [(a, b) for a, b in combinations(sorted(where), 2) if where[a] == where[b]]
    right = [(a, b) for a, b in shared if answers.get(a) and answers.get(a) == answers.get(b)]
    precision = len(right) / len(shared) if shared else None
    f1 = 2 * precision * recall / (precision + recall) if precision and recall else 0.0
    return {"pair_precision": rounded(precision), "pair_f1": round(f1, 3) if recall is not None else None}


def moved_lines(plan: str, answers: Answers) -> int:
    return len([move for move in plan_moves(plan) if answers.get(move.source) != ANY])


def rounded(value: Optional[float]) -> Optional[float]:
    return round(value, 3) if value is not None else None


def plan_steps(run: FirstPlan) -> Dict[str, Any]:
    """Steps 2-5 on the first plan; a run that never stopped climbed none of them."""
    if not run.stops:
        return {"step2_format": 0, "step3_by_name": 0, "step4_by_content": 0, "step5_leaves_alone": 0}
    names = folder_names(plan_moves(run.plan), run.answers)
    readable = not any(line.strip().startswith(UNREADABLE) for line in run.plan.splitlines())
    return {"step2_format": int(readable),
            "step3_by_name": group_right(known_by(run, "name"), run.where, names, run.answers),
            "step4_by_content": group_right(known_by(run, "content"), run.where, names, run.answers),
            "step5_leaves_alone": leaves_alone(run.where, run.answers, run.keep)}


def step_scores(run: FirstPlan, verdict: Verdict, coverage: Optional[float], mode: Any) -> Dict[str, Any]:
    has_plan, log = bool(run.stops), log_steps(run.events)
    return {"step1_tool": log["step1_tool"], **plan_steps(run), "step7_stops": log["step7_stops"],
            "approved_as_is": int(has_plan and not verdict.wrong and (coverage or 0) >= COVERAGE_BAR),
            "edited_lines": verdict.edited_lines if mode == "edit" and has_plan else None,
            "calls_after_done": log["calls_after_done"]}


def usable_flag(share: Optional[float], bar: float, rest: bool, stops: Optional[int]) -> Optional[int]:
    """1 when the first plan passes every test, 0 when it fails one, None when only step 7 is unknown."""
    if share is None or share > bar or not rest:
        return 0
    return None if stops is None else int(stops == 1)


def human_cost(lines: int, wrong_lines: int, scores: Dict[str, Any],
               coverage: Optional[float]) -> Dict[str, Any]:
    """What the person pays for the first plan: the share of lines to fix, and whether the run could be left
    to the agent (few fixes, enough moved, organized folders untouched, stopped when done)."""
    share = wrong_lines / lines if lines else None
    rest = (coverage or 0) >= COVERAGE_BAR and not scores["moved_kept"]
    usable = {key: usable_flag(share, bar, rest, scores["step7_stops"]) for key, bar in USABLE_SHARES.items()}
    return {"wrong_share": rounded(share), **usable}


def feedback_steps(stops: List[Dict[str, Any]], expect: Dict[str, Any], answers: Answers,
                   keep: Set[str]) -> Dict[str, Any]:
    """reject mode only: how many named rejections until a plan had nothing wrong (None if never needed)."""
    if expect.get("mode") != "reject" or not stops or not judge(stops[0]["plan"], answers, keep).wrong:
        return {"step6_feedback": None, "rounds_to_fix": None}
    for rounds, stop in enumerate(stops[1:], start=1):
        if not judge(stop["plan"], answers, keep).wrong:
            return {"step6_feedback": 1, "rounds_to_fix": rounds}
    return {"step6_feedback": 0, "rounds_to_fix": None}


def ladder(bundle: Dict[str, Any], expect: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Every ladder key for one run, in the order the published results store them; None without labels."""
    run = read_run(bundle, expect)
    if run is None:
        return None
    verdict, pairs = judge(run.plan, run.answers, run.keep), pair_scores(run.where, run.answers)
    scores = step_scores(run, verdict, pairs["coverage"], expect.get("mode"))
    kept_moved = {**scores, "moved_kept": bool(run.keep & set(run.where))}
    cost = human_cost(moved_lines(run.plan, run.answers), verdict.edited_lines, kept_moved, pairs["coverage"])
    counts = {"approvals": len(run.stops), "empty_plans": empty_plans(run.events)}
    return {**scores, **feedback_steps(run.stops, expect, run.answers, run.keep), **pairs, **cost,
            **counts, **agreement(run.answers, run.where)}


__all__ = ["ladder", "moved_lines", "pair_scores", "rounded"]

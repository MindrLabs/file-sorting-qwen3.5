"""The state after every approval, next to the ladder that judges the first plan:
- final_pair_f1 and final_coverage: where the files ended up, from the applied undo journals. In edit mode
  the person's fixes are in it, so it mostly shows how much got moved.
- session_wrong_share (edit mode): the lines the person fixed over every plan, out of every line.
"""
from __future__ import annotations

import posixpath
from typing import Any, Dict, List, Optional, Set

from .ladder import ladder, moved_lines, pair_scores, rounded
from .reviewer import ANY, Answers, judge, with_ignored


def final_places(journals: List[Dict[str, Any]]) -> Dict[str, str]:
    """Each moved file's starting path and the folder it sits in after the last applied plan."""
    origin_of: Dict[str, str] = {}
    for journal in journals:
        for move in journal.get("moves", []):
            origin_of[move["to"]] = origin_of.pop(move["from"], move["from"])
    return {origin: posixpath.dirname(now) for now, origin in origin_of.items()
            if now != origin and posixpath.dirname(now)}


def session_wrong_share(stops: List[Dict[str, Any]], answers: Answers, keep: Set[str],
                        mode: Any) -> Optional[float]:
    if mode != "edit":
        return None
    lines = sum(moved_lines(stop["plan"], answers) for stop in stops)
    wrong = sum(judge(stop["plan"], answers, keep).edited_lines for stop in stops)
    return rounded(wrong / lines) if lines else None


def final_state(bundle: Dict[str, Any], answers: Answers, keep: Set[str], mode: Any) -> Dict[str, Any]:
    places = final_places(bundle.get("journals") or [])
    scored = {name: folder for name, folder in places.items() if answers.get(name) != ANY}
    pairs = pair_scores(scored, answers)
    return {"final_pair_f1": pairs["pair_f1"], "final_coverage": pairs["coverage"],
            "session_wrong_share": session_wrong_share(bundle.get("stops") or [], answers, keep, mode)}


def score_run(bundle: Dict[str, Any], expect: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Every published key for one recorded run; None when the run carries no labels."""
    scores = ladder(bundle, expect)
    if scores is None:
        return None
    answers = with_ignored(expect["answers"], list(expect.get("ignore") or []))
    keep = set(expect.get("keep_in_place") or [])
    return {**scores, **final_state(bundle, answers, keep, expect.get("mode"))}


__all__ = ["final_places", "score_run"]

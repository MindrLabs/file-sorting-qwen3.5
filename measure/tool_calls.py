"""What the tool-call log says about a run: whether a tool ran, when the run was done, what came after,
and how many applied plans moved nothing. A run recorded without a log (`events: null`) leaves these blank."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

CALLS_AFTER_DONE = 2  # tool calls tolerated after the last plan that moved files (previews not counted)
# The closing line of the apply step's report.
MOVED = re.compile(r"^(\d+) moved, \d+ skipped\.", re.MULTILINE)
APPLIES = {"apply", "submit-apply"}
# Not a call the model made: half of an apply, the steps inside one placing call, and the half of a
# submit that runs after the person answered.
NOT_MODEL_CALLS = {"preview", "place-record", "place-decide", "submit-apply"}
Events = Optional[List[Dict[str, Any]]]


def moved_count(event: Dict[str, Any]) -> Optional[int]:
    """How many files an apply moved, read from its report; None for a rejection or an old record."""
    found = MOVED.search(str(event.get("output") or ""))
    return int(found.group(1)) if found else None


def done_at(events: List[Dict[str, Any]]) -> Optional[int]:
    """The last apply that moved something; with no move at all, the first apply."""
    applies = [index for index, event in enumerate(events) if event.get("command") in APPLIES]
    moving = [index for index in applies if (moved_count(events[index]) or 0) > 0]
    if moving:
        return moving[-1]
    return applies[0] if applies else None


def calls_after_done(events: List[Dict[str, Any]]) -> Optional[int]:
    """Tool calls the model made after the run was done."""
    done = done_at(events)
    if done is None:
        return None
    return sum(1 for event in events[done + 1:] if event.get("command") not in NOT_MODEL_CALLS)


def log_steps(events: Events) -> Dict[str, Any]:
    """step1_tool (a tool ran), step7_stops (stopped once done) and the calls that came after."""
    if events is None:
        return {"step1_tool": None, "step7_stops": None, "calls_after_done": None}
    after = calls_after_done(events)
    stopped = after is not None and after <= CALLS_AFTER_DONE
    return {"step1_tool": int(bool(events)), "step7_stops": int(stopped), "calls_after_done": after}


def empty_plans(events: Events) -> Optional[int]:
    """Applied plans that moved nothing."""
    if events is None:
        return None
    return len([event for event in events if event.get("command") in APPLIES and moved_count(event) == 0])


__all__ = ["Events", "empty_plans", "log_steps"]

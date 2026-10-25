"""The plan as plain `path => project` lines; a first line starting with REJECT is feedback."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

ARROW = "=>"
REJECT = "REJECT"
COMMENT = "#"
REJECTED = "The person rejected the plan. Feedback:"
MATCHED = "\0"


@dataclass(frozen=True)
class Move:
    source: str
    project: str
    reason: str = ""


@dataclass(frozen=True)
class Plan:
    moves: Tuple[Move, ...]
    unreadable: Tuple[str, ...]
    rejection: Optional[str]


NO_PLAN = Plan((), (), None)


def parse_plan(text: str) -> Plan:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines and lines[0].upper().startswith(REJECT):
        return Plan((), (), feedback(lines))
    moves = []
    unreadable = []
    for line in lines:
        if line.startswith(COMMENT):
            continue
        move = parse_line(line)
        if move:
            moves.append(move)
        else:
            unreadable.append(line)
    return Plan(tuple(moves), tuple(unreadable), None)


def parse_line(line: str) -> Optional[Move]:
    """`a/b.md => project  # reason`. The reason is for the person reviewing; moving ignores it."""
    source, arrow, rest = line.partition(ARROW)
    target, _, reason = rest.partition(COMMENT)
    # Models write folders as `project/`; only that trailing slash is forgiven, nesting is still refused.
    project = target.strip().rstrip("/")
    if not arrow or not source.strip() or not project:
        return None
    return Move(source.strip(), project, reason.strip())


def feedback(lines: List[str]) -> str:
    first = lines[0][len(REJECT):].lstrip(" :")
    text = "\n".join([first, *lines[1:]]).strip()
    return text or "(no reason given)"


def rejection_note(reason: str) -> str:
    """What applying a rejected plan reports; feedback_in reads the reason back out of it."""
    return f"{REJECTED} {reason}"


def feedback_in(outcome: str) -> str:
    if REJECTED not in outcome:
        return ""
    return outcome.split(REJECTED, 1)[1].strip()


def names_in(text: str, names: List[str]) -> List[str]:
    """The names the text mentions whole: `data.md` does not name `a.md`, nor `guest list final.csv`
    `final.csv`. Longer names are matched first and cut out, so a shorter one cannot match inside them."""
    found = set()
    for name in sorted(names, key=len, reverse=True):
        whole = re.compile(rf"(?<![\w.-]){re.escape(name)}(?!\.?[\w-])")
        text, count = whole.subn(MATCHED, text)
        if count:
            found.add(name)
    return [name for name in names if name in found]

"""The stand-in person at the approval stop: reads the plan against the labelled answer and answers as a
careful person would. A plan with no wrong line is approved as is, even when it leaves files out.

- `edit` sends back the plan with wrong lines fixed or removed, as a person typing in the box would.
- `reject` names what is wrong and sends it back to the model, up to MAX_REJECTIONS times.

The model names its own folders, so "right" means right company: each labelled project gets the
folder name the model used most for it, and a file is wrong when it lands anywhere else.
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

MAX_REJECTIONS = 3
ANY = "*"  # a file a second reader could place in two projects: wherever it goes, it is not wrong
MODES = ("edit", "reject")
Answers = Dict[str, Optional[str]]


class Move(NamedTuple):
    source: str
    project: str
    line: str


class Verdict(NamedTuple):
    wrong: List[Move]       # lines a person would not let through
    fixed_plan: str         # the plan with those lines fixed or removed
    edited_lines: int


def plan_moves(text: str) -> List[Move]:
    """`path => project  # reason` lines; comments (skips included) move nothing."""
    moves = []
    for line in (raw.strip() for raw in text.splitlines()):
        if not line or line.startswith("#") or "=>" not in line:
            continue
        source, target = line.split("=>", 1)
        project = target.split("#", 1)[0].strip().strip("/")
        moves.append(Move(source.strip().removeprefix("./"), project, line))
    return moves


def with_ignored(answers: Answers, ignore: List[str]) -> Answers:
    return {**answers, **{name: ANY for name in ignore}}


def folder_names(moves: List[Move], answers: Answers) -> Dict[str, str]:
    """Labelled project -> the model's folder for it, biggest project first; two projects never share one."""
    votes: Dict[str, Counter] = {}
    for move in moves:
        label = answers.get(move.source)
        if label and label != ANY:
            votes.setdefault(label, Counter())[move.project] += 1
    names: Dict[str, str] = {}
    for label in sorted(votes, key=lambda key: -sum(votes[key].values())):
        taken = set(names.values())
        free = [name for name, _ in votes[label].most_common() if name not in taken]
        names[label] = free[0] if free else label
    return names


def is_wrong(move: Move, answers: Answers, keep: Set[str], names: Dict[str, str]) -> bool:
    label = answers.get(move.source)
    if label == ANY:
        return False
    if move.source in keep or not label:
        return True
    return move.project != names.get(label, label)


def judge(plan: str, answers: Answers, keep: Set[str]) -> Verdict:
    moves = plan_moves(plan)
    names = folder_names(moves, answers)
    wrong = [move for move in moves if is_wrong(move, answers, keep, names)]
    fixed = [(move.source, fixed_line(move, answers, keep, names)) for move in moves]
    return Verdict(wrong, "\n".join(once_per_file(fixed)), len(wrong))


def once_per_file(lines: List[Tuple[str, str]]) -> List[str]:
    """A file the model listed twice ends up on one line: fixing both would move it twice."""
    seen: Set[str] = set()
    kept = []
    for source, line in lines:
        if line and source not in seen:
            seen.add(source)
            kept.append(line)
    return kept


def fixed_line(move: Move, answers: Answers, keep: Set[str], names: Dict[str, str]) -> str:
    if not is_wrong(move, answers, keep, names):
        return move.line
    label = answers.get(move.source)
    if move.source in keep or not label:
        return ""
    return f"{move.source} => {names.get(label, label)}"


def feedback(verdict: Verdict, answers: Answers, keep: Set[str]) -> str:
    """What a person would type: which file is wrong and what it belongs with, no answer key."""
    notes = []
    for move in verdict.wrong:
        label = answers.get(move.source)
        if move.source in keep or not label:
            notes.append(f"leave {move.source} where it is")
            continue
        peers = sorted(name for name, project in answers.items() if project == label and name != move.source)
        company = f"; it goes with {peers[0]}" if peers else ""
        notes.append(f"{move.source} does not belong in {move.project}{company}")
    return "REJECT: " + "; ".join(notes) + "."


def answer(plan: str, mode: str, rejections_so_far: int, answers: Answers, keep: Set[str]) -> Optional[str]:
    """None approves as is; text replaces the plan (edit) or sends it back (a REJECT line)."""
    verdict = judge(plan, answers, keep)
    if not verdict.wrong:
        return None
    if mode == "edit":
        # An empty answer means "approve as is" to the server; a plan with every line removed is a comment.
        return verdict.fixed_plan or "# nothing to move"
    return feedback(verdict, answers, keep) if rejections_so_far < MAX_REJECTIONS else None


__all__ = ["ANY", "MODES", "Answers", "Verdict", "answer", "folder_names", "judge", "plan_moves",
           "with_ignored"]

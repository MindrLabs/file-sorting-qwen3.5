"""Each file asked in up to ASKS menu rotations; it moves only when one project wins WIN votes.

Ids follow the position (P1 is always the first line) and none is always last, so a model that
favours a position spreads its votes instead of piling them on one project.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

from harness_state import RunState
from project_menu import answered, menu_text
from reading import card
from vote_log import write_votes

ASKS = 4
WIN = 3
REPLY_CHARS = 80  # the question allows 16 tokens; more than this is the model not answering


class VoteItem(TypedDict):
    name: str
    rotation: str
    menu: str
    card: str
    hint: str


class Started(TypedDict):
    items: List[VoteItem]
    state: RunState


class Recorded(TypedDict):
    state: RunState


class Decided(TypedDict):
    summary: str
    state: RunState


def rotations(count: int) -> List[int]:
    """Up to ASKS evenly spaced starting lines; a shorter menu has one rotation per line."""
    return sorted({round(step * count / ASKS) % count for step in range(ASKS)}) if count else [0]


def start_votes(root: Path, state: RunState) -> Started:
    """A fresh tally, and one ask per file and rotation."""
    starts = rotations(len(state["projects"]))
    cards = {name: card(root, name) for name in state["files"]}
    items = [vote_item(state["projects"], name, cards[name], start) for name in state["files"] for start in starts]
    return {"items": items, "state": {**state, "votes": {}, "replies": {}}}


def vote_item(projects: List[Dict[str, str]], name: str, text: str, start: int) -> VoteItem:
    return {"name": name, "rotation": str(start), "menu": menu_text(projects, start), "card": text, "hint": ""}


def record_vote(state: RunState, name: str, rotation: int, reply: str = "") -> Recorded:
    """The vote it counts as, and the reply as the model wrote it, cut, for the log."""
    votes, replies = dict(state.get("votes", {})), dict(state.get("replies", {}))
    votes[name] = {**votes.get(name, {}), str(rotation): answered(state["projects"], rotation, reply)}
    replies[name] = {**replies.get(name, {}), str(rotation): reply.strip()[:REPLY_CHARS]}
    return {"state": {**state, "votes": votes, "replies": replies}}


def winner(votes: Dict[str, Optional[str]]) -> Optional[str]:
    """WIN of ASKS; a menu with fewer rotations needs the same share of the asks it had (2 of 2, 3 of 3)."""
    needed = -(-WIN * len(votes) // ASKS)
    top = Counter(vote for vote in votes.values() if vote and vote != "none").most_common(1)
    return top[0][0] if top and top[0][1] >= needed else None


def decide_votes(root: Path, state: RunState) -> Decided:
    """The picks from the tally, which is also logged under the journal for the person to look into."""
    votes = state.get("votes", {})
    picks = {name: winner(votes.get(name, {})) for name in state["files"]}
    write_votes(root, votes, state.get("replies", {}), picks)
    moved = sum(1 for project in picks.values() if project)
    summary = f"{moved} of {len(state['files'])} files have a project with {WIN} of {ASKS} votes"
    return {"summary": summary, "state": {**state, "picks": picks}}


__all__ = ["ASKS", "WIN", "decide_votes", "record_vote", "rotations", "start_votes"]

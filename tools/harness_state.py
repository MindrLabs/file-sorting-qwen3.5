"""What one run carries between the harness steps. Each step gets it as JSON text and hands back a new
one, so the compose shows every value a step reads; nothing is kept on disk between steps."""
from __future__ import annotations

import json
from typing import Dict, List, Optional, TypedDict


class RunState(TypedDict, total=False):
    files: List[str]
    folders: List[str]
    given: List[Dict[str, str]]
    projects: List[Dict[str, str]]
    picks: Dict[str, Optional[str]]
    round: int
    votes: Dict[str, Dict[str, Optional[str]]]
    replies: Dict[str, Dict[str, str]]


def decode(text: str) -> RunState:
    state: RunState = json.loads(text) if text.strip() else {}
    return state


def encode(state: RunState) -> str:
    return json.dumps(state, ensure_ascii=False)


__all__ = ["RunState", "decode", "encode"]

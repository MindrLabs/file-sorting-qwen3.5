"""What the person cut from the plan they were shown: those files stay where they are and are named in
the report. The shown plan arrives with the approved one, so nothing is kept between the two steps."""
from __future__ import annotations

from pathlib import Path
from typing import List

from plan import Plan
from safe_paths import OutsideRoot, inside, relative


def left_by_person(root: Path, shown: Plan, approved: Plan) -> List[str]:
    kept = {normalized(root, move.source) for move in approved.moves}
    offered = sorted({normalized(root, move.source) for move in shown.moves})
    return [source for source in offered if source not in kept]


def normalized(root: Path, source: str) -> str:
    """`./a.md` and `a.md` are the same file whether the model or the person wrote the line."""
    try:
        return relative(root, inside(root, source))
    except OutsideRoot:
        return source


__all__ = ["left_by_person", "normalized"]

"""Dry run of a plan: lines that would be skipped come back as comments with the reason, so the text
still parses as the plan that would run."""
from __future__ import annotations

from pathlib import Path

from moving import blocked_reason
from plan import COMMENT, Move, Plan
from safe_paths import OutsideRoot, inside, project_dir


def preview_plan(root: Path, plan: Plan) -> str:
    lines = [preview_move(root, move) for move in plan.moves]
    lines += [f"{COMMENT} unreadable, not `path => project`: {line}" for line in plan.unreadable]
    return "\n".join(lines) or f"{COMMENT} empty plan"


def preview_move(root: Path, move: Move) -> str:
    line = f"{move.source} => {move.project}" + (f"  {COMMENT} {move.reason}" if move.reason else "")
    try:
        source = inside(root, move.source)
        target = project_dir(root, move.project) / source.name
    except OutsideRoot as error:
        return f"{COMMENT} skip: {line}  ({error})"
    reason = blocked_reason(root, source, target)
    return f"{COMMENT} skip: {line}  ({reason})" if reason else line

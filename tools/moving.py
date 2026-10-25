"""Carries out an approved plan. Never deletes or overwrites; a failing move is skipped and reported."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from journal import RunJournal
from plan import NO_PLAN, Move, Plan, rejection_note
from safe_paths import OutsideRoot, inside, place, project_dir, relative
from shown_plan import left_by_person


@dataclass
class Report:
    moved: List[Tuple[str, str]] = field(default_factory=list)
    created: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    left: List[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"moved {source} -> {target}" for source, target in self.moved]
        lines += [f"skipped {reason}" for reason in self.skipped]
        if self.left:
            lines.append(f"Left where they are: {', '.join(self.left)}.")
        undo = " The undo tab puts them back." if self.moved else ""
        lines.append(f"{len(self.moved)} moved, {len(self.skipped)} skipped.{undo}")
        return "\n".join(lines)


def apply_plan(root: Path, plan: Plan, shown: Plan = NO_PLAN) -> str:
    """`plan` is what the person approved or edited; `shown` is what they were shown, to name the cuts."""
    if plan.rejection is not None:
        return rejection_note(plan.rejection)
    return carry_out(root, plan, left_by_person(root, shown, plan)).render()


def carry_out(root: Path, plan: Plan, left: List[str]) -> Report:
    """The moves of a plan the person did not reject, journalled for undo, as counts and lines."""
    report = Report(skipped=[f"{line}: not in `path => project` form" for line in plan.unreadable], left=left)
    journal = RunJournal(root)
    for move in plan.moves:
        apply_move(root, move, report, journal)
    return report


def apply_move(root: Path, move: Move, report: Report, journal: RunJournal) -> None:
    try:
        source = inside(root, move.source)
        folder = project_dir(root, move.project)
    except OutsideRoot as error:
        report.skipped.append(f"{move.source}: {error}")
        return
    target = folder / source.name
    reason = blocked_reason(root, source, target)
    if reason:
        report.skipped.append(f"{move.source}: {reason}")
        return
    new_dir = None if folder.exists() else relative(root, folder)
    journal.begin(relative(root, source), relative(root, target), new_dir)
    try:
        move_file(source, folder, target, new_dir)
    except OSError as error:  # a failing move is skipped and reported; the rest of the plan still runs
        journal.cancel()
        report.skipped.append(f"{move.source}: {error.strerror or error}")
        return
    report.created += [new_dir] if new_dir else []
    report.moved.append((relative(root, source), relative(root, target)))


def move_file(source: Path, folder: Path, target: Path, new_dir: Optional[str]) -> None:
    if new_dir:
        folder.mkdir()
    try:
        place(source, target)
    except OSError:
        if new_dir and not any(folder.iterdir()):
            folder.rmdir()
        raise


def blocked_reason(root: Path, source: Path, target: Path) -> str:
    """Only plain top-level files move, whoever wrote the line: the person can edit the plan before approving."""
    if source == target:
        return "already in that project"
    if source.parent != root:
        return "only top-level files are sorted"
    if source.name.startswith("."):
        return "hidden files are left alone"
    if not source.is_file():
        return "not a file"
    if os.path.lexists(target):  # a broken symlink is a taken name too
        return f"{target.parent.name}/{target.name} already exists"
    return ""

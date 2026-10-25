"""One record per approved run, so the person can undo it at once. Only the person calls undo."""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from safe_paths import JOURNAL_DIR, OutsideRoot, inside, place, relative

RUNS = "runs"
UNDONE_SUFFIX = ".undone"
BROKEN_SUFFIX = ".broken"


class RunJournal:
    """One run's record, rewritten before each move: a run killed mid-plan (a shell timeout sends SIGKILL)
    still leaves undo every move it began. A move that then fails is taken back out."""

    def __init__(self, root: Path):
        self.root, self.path = root, None
        self.moves: List[Tuple[str, str, Optional[str]]] = []

    def begin(self, source: str, target: str, new_dir: Optional[str]) -> None:
        self.moves.append((source, target, new_dir))
        self.save()

    def cancel(self) -> None:
        self.moves.pop()
        if self.moves:
            self.save()
        elif self.path is not None:
            self.path.unlink()
            self.path = None

    def save(self) -> None:
        if self.path is None:
            folder = self.root / JOURNAL_DIR / RUNS
            folder.mkdir(parents=True, exist_ok=True)
            self.path = folder / f"{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.json"
        record = {"moves": [{"from": source, "to": target} for source, target, _ in self.moves],
                  "created_dirs": [new_dir for _, _, new_dir in self.moves if new_dir]}
        draft = self.path.with_suffix(".tmp")  # written aside and swapped in: a kill never leaves half a record
        draft.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(draft, self.path)


def last_run(root: Path) -> Optional[Path]:
    runs = sorted((root / JOURNAL_DIR / RUNS).glob("*.json"))
    return runs[-1] if runs else None


def undo_last(root: Path) -> str:
    """The latest run put back; a record that cannot be read is set aside so the runs before it stay reachable."""
    notes: List[str] = []
    while (record_path := last_run(root)) is not None:
        record = read_record(record_path)
        if record is None:
            record_path.rename(record_path.with_suffix(BROKEN_SUFFIX))
            notes.append(f"skipped a damaged undo record: {record_path.name}")
            continue
        lines = [undo_move(root, move["from"], move["to"]) for move in reversed(record["moves"])]
        lines += remove_if_empty(root, record["created_dirs"])
        record_path.rename(record_path.with_suffix(UNDONE_SUFFIX))
        return "\n".join(notes + lines)
    return "\n".join(notes + ["Nothing to undo."])


def read_record(path: Path) -> Optional[dict]:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    ok = isinstance(record, dict) and isinstance(record.get("moves"), list) and isinstance(record.get("created_dirs"), list)
    return record if ok else None


def undo_move(root: Path, source: str, target: str) -> str:
    """Never overwrites: a file put back where something new now sits is left for the person."""
    try:
        moved_to = inside(root, target)
        original = inside(root, source)
    except OutsideRoot as error:
        return f"skipped {target}: {error}"
    if not moved_to.is_file():
        return f"skipped {target}: no longer there"
    if os.path.lexists(original):
        return f"skipped {target}: {source} is taken again"
    try:
        original.parent.mkdir(parents=True, exist_ok=True)
        place(moved_to, original)
    except OSError as error:  # one stuck file must not keep every earlier run from being undone
        return f"skipped {target}: {error.strerror or error}"
    return f"restored {relative(root, original)}"


def remove_if_empty(root: Path, created: List[str]) -> List[str]:
    removed = []
    for name in created:
        folder = root / name
        if folder.is_dir() and not folder.is_symlink() and not any(folder.iterdir()):
            folder.rmdir()
            removed.append(f"removed empty folder {name}/")
    return removed

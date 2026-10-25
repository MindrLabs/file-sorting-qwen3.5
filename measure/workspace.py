"""The folder the server organizes (its ORGANIZE_ROOT): staged fresh before each run and read after it.
Staging empties the folder, so it only touches a folder that is empty or that this tool staged before."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .folders import build_folder, differing, hash_tree

JOURNAL_DIR = ".organizer"  # the tools' undo journal, left out of every comparison
MARKER = ".measure-workspace"  # hidden from the organizer; says the next run may empty this folder


class NotStageable(ValueError):
    """The folder holds files this tool did not put there."""


def check_stageable(root: Path) -> None:
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise NotStageable(f"{root} is not a plain folder")
    if not root.exists() or (root / MARKER).is_file() or not any(root.iterdir()):
        return
    raise NotStageable(f"{root} holds files this tool did not stage, and staging empties it. "
                       "Start the server on an empty folder and pass that folder as --root.")


def stage(root: Path, folder: str) -> None:
    """The dev folder's files in root, checked against their recorded hashes."""
    check_stageable(root)
    build_folder(folder, root)
    (root / MARKER).write_text("Staged by python3 -m measure, which empties this folder before every run.\n",
                               encoding="utf-8")
    wrong = differing(folder, tree(root))
    if wrong:
        raise ValueError(f"{folder} staged {len(wrong)} files unlike the recorded ones, first {wrong[0]}")


def tree(root: Path) -> Dict[str, str]:
    """Every file but the journal and the marker, by content hash: what undo has to give back."""
    return hash_tree(root, (JOURNAL_DIR, MARKER))


def journals(root: Path) -> List[Dict[str, Any]]:
    """Applied runs in order; undone ones are renamed and no longer match."""
    paths = sorted((root / JOURNAL_DIR / "runs").glob("*.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def events(root: Path) -> Optional[List[Dict[str, Any]]]:
    """The tools' call log if they keep one, else None: the keys that read it then stay blank."""
    log = root / JOURNAL_DIR / "events.jsonl"
    if not log.is_file():
        return None
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


__all__ = ["MARKER", "NotStageable", "events", "journals", "stage", "tree"]

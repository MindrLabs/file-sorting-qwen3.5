"""Keeps every path the model names inside the folder the person chose. The only gate to the disk."""
from __future__ import annotations

import errno
import os
from pathlib import Path

JOURNAL_DIR = ".organizer"


class OutsideRoot(ValueError):
    """A path left the chosen folder, went through a symlink or reached the journal."""


def open_root(root: str) -> Path:
    path = Path(root).expanduser().resolve()
    if not path.is_dir():
        raise OutsideRoot(f"not a folder: {root}")
    return path


def inside(root: Path, name: str) -> Path:
    """`name` relative to root. Symlinks are refused rather than followed: they may point anywhere."""
    candidate = root / name
    if candidate.is_symlink():
        raise OutsideRoot(f"symlinks are not handled: {name}")
    path = candidate.resolve()
    if path != root and root not in path.parents:
        raise OutsideRoot(f"outside the chosen folder: {name}")
    if JOURNAL_DIR in path.relative_to(root).parts:
        raise OutsideRoot(f"the undo journal is off limits: {name}")
    return path


def project_dir(root: Path, project: str) -> Path:
    """A project is one folder directly under root, so a name cannot nest or climb."""
    if not is_plain_name(project):
        raise OutsideRoot(f"project must be a plain folder name: {project!r}")
    folder = root / project
    if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
        raise OutsideRoot(f"project name is taken by a file or symlink: {project}")
    return folder


def is_plain_name(name: str) -> bool:
    return bool(name) and not name.startswith(".") and "/" not in name and "\\" not in name


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def place(source: Path, target: Path) -> None:
    """Moves a file without ever replacing what sits at target, even one that appears after the last check:
    a hard link fails on a taken name. A filesystem without hard links falls back to check-then-rename."""
    try:
        os.link(source, target, follow_symlinks=False)
    except FileExistsError:
        raise
    except OSError:
        if os.path.lexists(target):
            raise FileExistsError(errno.EEXIST, "already exists", str(target))
        source.rename(target)
        return
    source.unlink()

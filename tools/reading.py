"""What the harness reads of a file: never writes and never leaves root."""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from safe_paths import JOURNAL_DIR, inside

TEXT_SUFFIXES = frozenset({
    ".md", ".txt", ".rst", ".tex", ".csv", ".tsv", ".json", ".yml", ".yaml", ".toml", ".ini", ".log",
    ".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".sql", ".html", ".css", ".xml",
})
# A small model's context is the budget: 2 KB is roughly 500-700 tokens per file read.
PEEK_BYTES = 2048
CARD_CHARS = 300


def peek(root: Path, name: str) -> str:
    path = inside(root, name)
    if not path.is_file():
        raise IsADirectoryError(f"not a file: {name}")
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return f"{name}: not a text file ({path.stat().st_size} bytes). Judge it by its name."
    with path.open("rb") as handle:
        head = handle.read(PEEK_BYTES)
    return head.decode("utf-8", errors="replace")


def card(root: Path, name: str) -> str:
    """A file's name and its first characters on one line: what a model reads before opening it."""
    text = " ".join(peek(root, name).split())
    return f"{name}\n{text[:CARD_CHARS]}"


def top_level(root: Path) -> Tuple[List[str], List[str]]:
    entries = [entry for entry in sorted(root.iterdir()) if is_visible(entry)]
    files = [entry.name for entry in entries if entry.is_file()]
    folders = [entry.name for entry in entries if entry.is_dir() and entry.name != JOURNAL_DIR]
    return files, folders


def is_visible(entry: Path) -> bool:
    return not entry.name.startswith(".") and not entry.is_symlink()

"""Commands that change the folder run one at a time."""
from __future__ import annotations

import fcntl
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from safe_paths import JOURNAL_DIR

LOCK = "lock"


@contextmanager
def workspace_lock(root: Path) -> Iterator[None]:
    folder = root / JOURNAL_DIR
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / LOCK).open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)

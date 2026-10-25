"""Each vote run's tally, one line per file, so a person can see why a file moved or stayed. Written once
the votes are decided and never read back: the run itself still goes on in its state."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from safe_paths import JOURNAL_DIR

VOTES = "votes"
Tally = Dict[str, Dict[str, Optional[str]]]


def write_votes(root: Path, votes: Tally, replies: Dict[str, Dict[str, str]],
                picks: Dict[str, Optional[str]]) -> Path:
    """`votes` by rotation: a project, "none", or None for an answer that named nothing on the menu;
    `replies` what the model wrote for each, so a None can be read."""
    folder = root / JOURNAL_DIR / VOTES
    folder.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps({"file": name, "votes": votes.get(name, {}), "replies": replies.get(name, {}),
                         "picked": picked}, ensure_ascii=False) for name, picked in picks.items()]
    path = folder / f"{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.jsonl"
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    return path


__all__ = ["write_votes"]

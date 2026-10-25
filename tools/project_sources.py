"""The person's project list as typed in the web UI: one project per line, `name: about`."""
from __future__ import annotations

import re
from typing import Dict, List

BULLET = re.compile(r"^[-*•]\s+")


def parse_listing(text: str) -> List[Dict[str, str]]:
    """Bullets and blank lines are ignored; the about is optional and may hold more colons."""
    lines = [BULLET.sub("", line.strip()) for line in text.splitlines()]
    pairs = [line.partition(":") for line in lines if line]
    return [{"name": name.strip(), "about": about.strip()} for name, _, about in pairs if name.strip()]


__all__ = ["parse_listing"]

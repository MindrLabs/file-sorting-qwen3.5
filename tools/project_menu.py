"""The menu the model picks from: the project list as folder names, its P1.. lines, the answers."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from plan import ARROW, COMMENT
from safe_paths import is_plain_name

MAX_PROJECTS = 8
MIN_NEW_PROJECTS = 2
EXISTING_ABOUT = "existing folder"
NONE_LINE = "none: not sure, or it fits no project"
PICK = re.compile(r"\b(P\d+|none)\b", re.IGNORECASE)


def folder_name(raw: str) -> Optional[str]:
    name = re.sub(r"[^0-9a-z가-힣]+", "-", raw.strip().lower()).strip("-")[:40]
    return name if name and is_plain_name(name) else None


def parse_project_list(reply: str) -> List[Dict[str, str]]:
    """Every complete item of the JSON array, even when it was cut off at the token limit."""
    start, items, decoder = reply.find("["), [], json.JSONDecoder()
    index = start + 1 if start >= 0 else len(reply)
    while index < len(reply):
        while index < len(reply) and reply[index] in " \n\r\t,":
            index += 1
        try:
            item, index = decoder.raw_decode(reply, index)
        except json.JSONDecodeError:
            break
        items.append(item)
    kept = [item for item in items if isinstance(item, (dict, str))]
    rows = [item if isinstance(item, dict) else {"name": str(item)} for item in kept]
    return [{"name": str(row.get("name", "")), "about": str(row.get("about", ""))[:120]} for row in rows]


def existing_rows(folders: List[str], proposals: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Existing folders while there is room; past that, only the ones the model named."""
    named = {folder_name(row["name"]) for row in proposals}
    room = len(folders) <= MAX_PROJECTS - MIN_NEW_PROJECTS
    usable = [folder for folder in folders if COMMENT not in folder and ARROW not in folder]
    kept = [folder for folder in usable if room or folder_name(folder) in named]
    return [{"name": folder, "about": EXISTING_ABOUT} for folder in kept]


def project_name(raw: str, folders: List[str]) -> Optional[str]:
    """An existing folder keeps its own name, also when the model wrote it another way."""
    by_slug = {folder_name(folder): folder for folder in reversed(folders)}
    return raw if raw in folders else by_slug.get(folder_name(raw), folder_name(raw))


def menu_rows(proposals: List[Dict[str, str]], files: List[str], folders: List[str],
              limit: Optional[int] = MAX_PROJECTS) -> List[Dict[str, str]]:
    """Existing folders first, then the projects, at most eight; `limit` None keeps every row."""
    file_names = {folder_name(name) for name in files} | {folder_name(Path(name).stem) for name in files}
    kept: List[Dict[str, str]] = []
    for row in existing_rows(folders, proposals) + proposals:
        name = project_name(row["name"], folders)
        fresh = name not in folders
        if name and name not in [project["name"] for project in kept] and not (fresh and name in file_names):
            kept.append({"name": name, "about": row["about"]})
    return kept if limit is None else kept[:limit]


def new_count(rows: List[Dict[str, str]], folders: List[str]) -> int:
    return len([row for row in rows if row["name"] not in folders])


def rotated(rows: List[Dict[str, str]], start: int) -> List[Dict[str, str]]:
    return rows[start:] + rows[:start]


def menu_text(rows: List[Dict[str, str]], start: int = 0) -> str:
    """The menu the model picks from: ids by position from P1, none always last."""
    shown = rotated(rows, start)
    lines = [f"P{place}: {row['name']} - {row['about']}" for place, row in enumerate(shown, start=1)]
    return "\n".join(lines + [NONE_LINE])


def answered(rows: List[Dict[str, str]], start: int, reply: str) -> Optional[str]:
    """The project the reply names on this menu, "none", or None when it names nothing on it."""
    names = {f"p{place}": row["name"] for place, row in enumerate(rotated(rows, start), start=1)}
    found = (match.lower() for match in PICK.findall(reply))
    answer = next((match for match in found if match in names or match == "none"), None)
    if answer is None or answer == "none":
        return answer
    return names[answer]


__all__ = ["EXISTING_ABOUT", "MAX_PROJECTS", "MIN_NEW_PROJECTS", "answered", "folder_name", "menu_rows",
           "menu_text", "new_count", "parse_project_list", "project_name"]

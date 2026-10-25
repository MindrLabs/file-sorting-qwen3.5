"""Code steps between the model's two questions: which projects, and which one each file belongs to.
Every step takes the run's state and returns the next one; the compose carries it from step to step."""
from __future__ import annotations

from pathlib import Path
from typing import List, TypedDict

from harness_state import RunState
from plan import feedback_in, names_in
from project_menu import EXISTING_ABOUT, MAX_PROJECTS, MIN_NEW_PROJECTS
from project_menu import answered, menu_rows, menu_text, new_count, parse_project_list
from project_sources import parse_listing
from reading import card, top_level

NO_DRAFT = "No projects to suggest. Write your own lines: `name: what the work is`."
TOO_FEW = ("Your list had fewer than two projects, or used file names as project names. A project groups "
           "several files about one piece of work. Name 2 to 8 such projects.")
MAX_ROUNDS = 3


class FileItem(TypedDict):
    name: str
    card: str
    hint: str


class Scanned(TypedDict):
    listing: str
    folders: str
    files: List[FileItem]
    state: RunState
    has_list: str  # "1" when the person gave the list: the workflow then skips asking the model for one


class Accepted(TypedDict):
    ok: bool
    error: str
    state: RunState


class NextRound(TypedDict):
    done: bool
    files: List[FileItem]
    outcome: str
    state: RunState


def scan(root: Path, listed: str = "") -> Scanned:
    """`listed` is the person's `name: about` lines; empty, the model names the projects."""
    files, folders = top_level(root)
    cards = [card(root, name) for name in files]
    listing = "\n".join("- " + text.replace("\n", ": ", 1)[:160] for text in cards)
    items: List[FileItem] = [{"name": name, "card": text, "hint": ""} for name, text in zip(files, cards)]
    state: RunState = {"files": files, "folders": folders, "given": parse_listing(listed),
                       "projects": [], "picks": {}, "round": 0}
    return {"listing": listing, "folders": ", ".join(folders) or "(none)", "files": items, "state": state,
            "has_list": "1" if state["given"] else "0"}


def accept_projects(state: RunState, reply: str = "", last_try: bool = False) -> Accepted:
    """The person's list if given, else the model's; file names are dropped. Fewer than two new
    projects in the model's list: the reason goes back to it once."""
    given, folders = state["given"], state["folders"]
    proposals = given or parse_project_list(reply)
    kept = menu_rows(proposals, state["files"], folders, limit=None if given else MAX_PROJECTS)
    if not given and new_count(kept, folders) < MIN_NEW_PROJECTS and not last_try:
        return {"ok": False, "error": TOO_FEW, "state": state}
    return {"ok": True, "error": "", "state": {**state, "projects": kept}}


def menu(state: RunState) -> str:
    return menu_text(state["projects"])


def draft(state: RunState) -> str:
    """The menu as `name: about` lines for the projects box; an existing folder's line is left to fill."""
    rows = state.get("projects", [])
    abouts = ["" if row["about"] == EXISTING_ABOUT else row["about"] for row in rows]
    lines = [f"{row['name']}: {about}".rstrip() for row, about in zip(rows, abouts)]
    return "\n".join(lines) or NO_DRAFT


def accept_pick(state: RunState, name: str, reply: str = "", last_try: bool = False) -> Accepted:
    rows = state["projects"]
    answer = answered(rows, 0, reply)
    if answer is None and not last_try:
        valid = ", ".join(f"P{place}" for place in range(1, len(rows) + 1))
        error = (f"Your answer {reply.strip()[:40]!r} is not one of: {valid}, none. "
                 "Answer with one of them only.")
        return {"ok": False, "error": error, "state": state}
    picked = None if answer in (None, "none") else answer
    return {"ok": True, "error": "", "state": {**state, "picks": {**state["picks"], name: picked}}}


def assemble(state: RunState) -> str:
    lines = [f"{name} => {project}" for name, project in sorted(state["picks"].items()) if project]
    return "\n".join(lines) or "# nothing to move"


def next_round(root: Path, state: RunState, outcome: str = "") -> NextRound:
    """Approved, edited or out of rounds: done. Rejected: the files the feedback names, with it as a hint."""
    feedback = feedback_in(outcome)
    named = names_in(feedback, state["files"])
    rounds = state["round"] + 1
    done = not feedback or not named or rounds > MAX_ROUNDS
    picks = {name: project for name, project in state["picks"].items() if done or name not in named}
    hint = f"\n\nThe person said: {feedback}"
    files: List[FileItem] = [] if done else [{"name": name, "card": card(root, name), "hint": hint}
                                             for name in named]
    return {"done": done, "files": files, "outcome": outcome[:2000],
            "state": {**state, "round": rounds, "picks": picks}}


__all__ = ["MAX_ROUNDS", "accept_pick", "accept_projects", "assemble", "draft", "menu", "next_round", "scan"]

"""The compose's shell steps call this with argv, never a shell. Here argv text becomes typed values, by
parameter name, and a step's result becomes text: its state goes back as JSON text, the form a shell
argument can carry to the next step."""
from __future__ import annotations

import inspect
import json
import sys
from contextlib import nullcontext
from pathlib import Path
from typing import Callable, ContextManager, Dict, List, Mapping, Tuple

import harness_steps
import harness_votes
from harness_state import decode, encode
from journal import undo_last
from moving import apply_plan
from plan import parse_plan
from preview import preview_plan
from safe_paths import open_root
from workspace_lock import workspace_lock

USAGE = "usage: organizer.py <command> <root> [args...]\ncommands: "
CONVERT: Dict[str, Callable[[str], object]] = {
    "state": decode, "plan": parse_plan, "shown": parse_plan, "rotation": int,
    "last_try": lambda text: text == "1",
}


def approve(text: str = "") -> str:
    """The person's answer replaces this step's input in the compose; the plan goes on as it then is."""
    return text


COMMANDS: Dict[str, Callable[..., object]] = {
    "preview": preview_plan,
    "approve": approve,
    "apply": apply_plan,
    "undo": undo_last,
    "scan": harness_steps.scan,
    "accept-projects": harness_steps.accept_projects,
    "menu": harness_steps.menu,
    "draft": harness_steps.draft,
    "accept-pick": harness_steps.accept_pick,
    "assemble": harness_steps.assemble,
    "next-round": harness_steps.next_round,
    "start-votes": harness_votes.start_votes,
    "record-vote": harness_votes.record_vote,
    "decide-votes": harness_votes.decide_votes,
}
MOVES_FILES = {"apply", "undo"}


def main(argv: List[str]) -> int:
    if len(argv) < 2 or argv[0] not in COMMANDS:
        print(USAGE + ", ".join(COMMANDS), file=sys.stderr)
        return 2
    try:
        root: Path = open_root(argv[1])
    except (ValueError, OSError) as error:
        print(f"error: {error}")
        return 1
    with lock_for(root, argv[0]):
        output, ok = run_command(root, argv[0], argv[2:])
    # stdout, not stderr: the shell component hands the workflow stdout only.
    print(output)
    return 0 if ok else 1


def lock_for(root: Path, command: str) -> ContextManager[None]:
    return workspace_lock(root) if command in MOVES_FILES else nullcontext()


def run_command(root: Path, command: str, args: List[str]) -> Tuple[str, bool]:
    try:
        return render(call(COMMANDS[command], root, args)), True
    except (ValueError, OSError, TypeError) as error:  # OutsideRoot is a ValueError
        return f"error: {error}", False


def call(step: Callable[..., object], root: Path, args: List[str]) -> object:
    """Steps that read the folder take `root` first; every other argument is converted by its name."""
    names = list(inspect.signature(step).parameters)
    takes_root = names[:1] == ["root"]
    names = names[1:] if takes_root else names
    if len(args) > len(names):
        raise TypeError(f"{len(args)} arguments for {len(names)}: {', '.join(names)}")
    values = [CONVERT.get(name, str)(text) for name, text in zip(names, args)]
    return step(root, *values) if takes_root else step(*values)


def render(result: object) -> str:
    """Text as it is; a step's fields as JSON, its state as JSON text inside them."""
    if isinstance(result, str):
        return result
    if not isinstance(result, Mapping):
        raise TypeError(f"a step returned {type(result).__name__}")
    fields = {key: encode(value) if key == "state" else value for key, value in result.items()}
    return json.dumps(fields, ensure_ascii=False)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

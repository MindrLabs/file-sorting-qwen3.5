"""The draft tab in the compose: the step-by-step list step, its menu as text, and nothing moved."""
from fixtures import run_tests

from pathlib import Path

import organizer

COMPOSE = (Path(__file__).resolve().parents[1] / "model-compose.yml").read_text(encoding="utf-8")


def block(block_id: str) -> str:
    found = [part for part in COMPOSE.split("\n  - id: ") if part.startswith(f"{block_id}\n")]
    assert found, block_id
    return found[0]


def test_the_draft_tab_sits_next_to_the_first_tab():
    workflows = COMPOSE.split("\ncomponents:")[0].split("\n  - id: ")[1:]
    assert [part.split("\n", 1)[0] for part in workflows[:2]] == ["organize", "draft-projects"]


def test_the_draft_uses_the_same_list_step_and_moves_nothing():
    draft = block("draft-projects")
    assert "action: ask-projects\n" in draft and "action: draft\n" in draft
    assert "apply" not in draft and "interrupt" not in draft and "approve" not in draft


def test_the_draft_step_is_a_shell_command_the_organizer_knows():
    assert "tools/organizer.py, draft," in block("organizer-cli") and "draft" in organizer.COMMANDS


run_tests(globals())

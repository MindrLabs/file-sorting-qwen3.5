"""Both model questions take presence_penalty and min_p from the environment (.env.sample sets the
Qwen3.5 card's values); the defaults are llama-cpp-python's own."""
from fixtures import run_tests

import re
from pathlib import Path

COMPOSE = (Path(__file__).resolve().parents[1] / "model-compose.yml").read_text(encoding="utf-8")
SAMPLING = ("          presence_penalty: ${env.LLM_PRESENCE_PENALTY | 0.0}\n"
            "          min_p: ${env.LLM_MIN_P | 0.05}\n")


def action_block(action: str) -> str:
    found = re.search(rf"^      - id: {action}\n((?:        .*\n|      #.*\n|\n)*?)(?=^      - id: |^  \S)", COMPOSE, re.MULTILINE)
    assert found, f"no action {action}"
    return found.group(1)


def test_the_project_question_takes_both_settings():
    assert SAMPLING in action_block("choose-projects")


def test_the_per_file_question_shares_the_project_question_params():
    assert "        params: *choose_params\n" in action_block("choose-file")


run_tests(globals())

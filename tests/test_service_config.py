"""The sample settings are the measured light setting, and the web UI opens on the flow that takes the person's list."""
from fixtures import run_tests

import re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
COMPOSE = (HERE / "model-compose.yml").read_text(encoding="utf-8")
MEASURED = {"LLM_REPO": "unsloth/Qwen3.5-9B-GGUF", "LLM_GGUF": "Qwen3.5-9B-Q4_K_M.gguf", "LLM_N_CTX": "8192",
            "LLM_PRESENCE_PENALTY": "1.5", "LLM_MIN_P": "0",
            "LLM_REVISION": "3885219b6810b007914f3a7950a8d1b469d598a5"}


def sample_env():
    lines = (HERE / ".env.sample").read_text(encoding="utf-8").splitlines()
    return dict(line.split("=", 1) for line in lines if line and not line.startswith("#"))


def workflow(workflow_id):
    blocks = [block for block in COMPOSE.split("\n  - id: ") if block.startswith(f"{workflow_id}\n")]
    assert blocks, f"{workflow_id} not found"
    return blocks[0]


def test_the_sample_env_is_the_measured_light_setting():
    assert {name: value for name, value in sample_env().items() if name.startswith("LLM_")} == MEASURED


def test_every_sample_setting_is_read_by_the_compose():
    for name in sample_env():
        assert "${env." + name + " |" in COMPOSE, name


def test_no_model_question_calls_tools():
    assert "tool_call_parser" not in COMPOSE and "LLM_TOOL_FORMAT" not in COMPOSE
    assert COMPOSE.count("        tools: []\n") == len(re.findall(r"^      - id: choose-", COMPOSE, re.MULTILINE)) == 2


def test_the_web_ui_opens_on_the_vote_flow():
    """The gradio UI opens on the first workflow in the file; `default` is what the API runs."""
    defaults = re.findall(r"^  - id: (\S+)\n    default: true$", COMPOSE, re.MULTILINE)
    assert defaults == ["organize"]
    assert re.findall(r"^  - id: (\S+)$", COMPOSE, re.MULTILINE)[0] == "organize"


def test_both_flows_take_the_persons_list():
    for flow in ("organize", "organize-quick"):
        assert "action: scan\n" in workflow(flow)
        assert '"${input.projects as text @(description' in workflow(flow)
    assert '"${input.projects | }" ]' in COMPOSE


run_tests(globals())

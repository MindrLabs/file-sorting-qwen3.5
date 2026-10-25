"""The vote flow in the compose: organize-quick with only the picks changed, the same choose-file question."""
from fixtures import run_tests

import inspect
import re
from pathlib import Path

import organizer

COMPOSE = (Path(__file__).resolve().parents[1] / "model-compose.yml").read_text(encoding="utf-8")


def block(kind_indent: str, block_id: str) -> str:
    found = [part for part in COMPOSE.split(f"\n{kind_indent}- id: ") if part.startswith(f"{block_id}\n")]
    assert found, block_id
    return found[0]


def job_texts(workflow: str) -> dict:
    parts = block("  ", workflow).split("\n    output:")[0].split("\n      - id: ")[1:]
    return {part.split("\n", 1)[0]: part for part in parts}


def jobs(workflow: str) -> list:
    return list(job_texts(workflow))


def test_the_vote_flow_keeps_the_harness_steps_around_its_picks():
    assert jobs("organize-quick") == ["scan", "projects", "assign", "rounds"]
    assert jobs("organize") == ["scan", "projects", "votes", "assign", "decide", "rounds"]
    quick, vote = job_texts("organize-quick"), job_texts("organize")
    assert quick["scan"] == vote["scan"] and quick["projects"] == vote["projects"]


def test_each_vote_asks_the_same_choose_file_question_and_records_it():
    one = block("  ", "ask-file-vote")
    assert "action: choose-file\n" in one and "action: record-vote\n" in one
    assert "workflow: ask-file-vote\n" in block("  ", "subflow")


def test_every_shell_action_is_the_organizer_command_of_the_same_name_and_back():
    shell = block("  ", "organizer-cli")
    pairs = re.findall(r"- id: (\S+)\n\s+command: \[ python3, tools/organizer.py, (\S+),", shell)
    assert all(action == command for action, command in pairs)
    assert sorted(command for _, command in pairs) == sorted(organizer.COMMANDS)


def test_each_shell_action_passes_its_steps_arguments_in_order():
    """organizer.py converts argv by parameter name, so the compose must pass them in the step's order."""
    renamed = {"projects": "listed", "": "text"}  # the projects box, and approve's whole input
    actions = re.findall(r"tools/organizer.py, (\S+), \"[^\"]+\"((?:, \"[^\"]+\")*) \]", block("  ", "organizer-cli"))
    for action, args in actions:
        passed = [renamed.get(name, name) for name in re.findall(r"\$\{input\.?(\w*)", args)]
        params = [name for name in inspect.signature(organizer.COMMANDS[action]).parameters if name != "root"]
        assert passed == params, (action, passed, params)


def test_every_job_that_runs_a_state_step_hands_it_the_state():
    takes_state = {name for name, step in organizer.COMMANDS.items() if "state" in inspect.signature(step).parameters}
    for job in re.split(r"\n\s+- id: ", COMPOSE.split("\ncomponents:")[0]):
        action = re.search(r"component: organizer-cli\n\s+action: (\S+)", job)
        if action and action.group(1) in takes_state:
            assert "state: ${" in job, job[:80]


def test_each_subflow_action_is_named_after_its_workflow():
    pairs = re.findall(r"- id: (\S+)\n(?:\s+default: true\n)?\s+workflow: (\S+)\n", block("  ", "subflow"))
    assert len(pairs) == 7 and all(action == workflow for action, workflow in pairs)


def test_the_web_ui_opens_on_the_vote_flow():
    assert COMPOSE.split("\n  - id: ", 1)[1].startswith("organize\n")



def test_each_question_is_asked_at_most_twice_and_the_second_try_is_always_kept():
    """A loop past max_iteration_count fails the run, so the second try must be the last_try that passes."""
    for ask in ("ask-projects", "ask-file"):
        loop = block("  ", ask)
        assert "type: loop\n" in loop and "max_iteration_count: 2\n" in loop and 'last_try: "0"\n' in loop
        once = block("  ", f"{ask}-once")
        assert "last_try: ${input.last_try}\n" in once and once.rstrip().endswith('last_try: "1"')


def test_the_rounds_loop_stops_one_past_the_last_rejection_round():
    from harness_steps import MAX_ROUNDS
    for flow in ("organize", "organize-quick"):
        assert f"max_iteration_count: {MAX_ROUNDS + 1}\n" in block("  ", flow)



def test_a_list_from_the_person_skips_asking_the_model_for_one():
    flow = block("  ", "ask-projects")
    assert "type: if\n" in flow and "input: ${input.has_list}\n" in flow and "if_true: given\n" in flow
    assert "output: ${jobs.given.output | ${jobs.ask.output}}" in flow
    for workflow in ("organize", "organize-quick", "draft-projects"):
        assert "has_list: ${jobs.scan.output.has_list}" in job_texts(workflow)["projects"], workflow


run_tests(globals())

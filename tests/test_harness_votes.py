"""Picks by vote: the menu asked in rotations, ids by position, a file moves only on WIN of ASKS votes."""
from fixtures import run_tests, scratch_root

import json

from harness_steps import accept_projects, menu, scan
from harness_votes import ASKS, REPLY_CHARS, WIN, decide_votes, record_vote, rotations, start_votes

FILES = {"kitchen_quote.pdf": "x", "memo.txt": "cabinet sizes", "trip.md": "osaka hotels", "notes.txt": "misc"}
MENU = "kitchen: quotes\nosaka: hotels\nseeds: garden\nbudget: money\ncar: repairs"


def started(listed=MENU):
    root = scratch_root(FILES)
    return root, accept_projects(scan(root, listed)["state"])["state"]


def answer_all(root, state, reply_for):
    started_votes = start_votes(root, state)
    state = started_votes["state"]
    for item in started_votes["items"]:
        state = record_vote(state, item["name"], int(item["rotation"]), reply_for(item))["state"]
    return decide_votes(root, state)


def place_of(item, project):
    """The id this rotation shows for a project, as a model that knows the answer would reply."""
    line = next(line for line in item["menu"].splitlines() if f": {project} - " in line)
    return line.split(":", 1)[0]


def test_each_file_is_asked_in_rotations_with_ids_by_position_and_none_last():
    root, state = started()
    items = start_votes(root, state)["items"]
    assert rotations(5) == [0, 1, 2, 4] and len(items) == len(FILES) * ASKS
    first = [item for item in items if item["name"] == "memo.txt"]
    assert [item["menu"].splitlines()[0].split(" - ")[0] for item in first] == ["P1: kitchen", "P1: osaka", "P1: seeds", "P1: car"]
    assert all(item["menu"].splitlines()[-1].startswith("none:") for item in items)
    assert all(isinstance(value, str) for item in items for value in item.values())  # shell arguments are text


def test_a_project_with_three_of_four_votes_moves_and_two_of_four_stays():
    root, state = started()
    def reply(item):
        if item["name"] == "trip.md":
            return place_of(item, "osaka") if item["rotation"] != "4" else "none"
        if item["name"] == "memo.txt":
            return place_of(item, "kitchen") if item["rotation"] in ("0", "1") else place_of(item, "budget")
        return "none"
    decided = answer_all(root, state, reply)
    assert decided["summary"] == f"1 of 4 files have a project with {WIN} of {ASKS} votes"
    assert decided["state"]["picks"] == {"kitchen_quote.pdf": None, "memo.txt": None, "notes.txt": None, "trip.md": "osaka"}


def test_a_bad_answer_abstains_and_counts_against_moving():
    root, state = started()
    decided = answer_all(root, state, lambda item: "P9" if item["rotation"] in ("0", "1") else place_of(item, "car"))
    assert set(decided["state"]["picks"].values()) == {None}


def test_a_short_menu_needs_the_same_share_of_its_asks():
    root, state = started("kitchen: quotes\nosaka: hotels")
    assert rotations(2) == [0, 1] and len(start_votes(root, state)["items"]) == len(FILES) * 2
    decided = answer_all(root, state, lambda item: place_of(item, "osaka"))
    assert set(decided["state"]["picks"].values()) == {"osaka"}


def test_the_first_rotation_asks_the_same_menu_as_the_one_ask_flow():
    root, state = started()
    first = start_votes(root, state)["items"][0]
    assert first["rotation"] == "0" and first["menu"] == menu(state)


def test_the_votes_live_in_the_state_and_start_fresh_each_run():
    root, state = started()
    decided = answer_all(root, state, lambda item: "none")
    assert len(decided["state"]["votes"]["memo.txt"]) == ASKS
    assert start_votes(root, decided["state"])["state"]["votes"] == {}


def test_asking_keeps_nothing_on_disk_and_deciding_logs_the_tally_once():
    root, state = started()
    started_votes = start_votes(root, state)
    state = started_votes["state"]
    for item in started_votes["items"]:
        reply = place_of(item, "osaka") if item["name"] == "trip.md" else "P9" if item["rotation"] == "0" else "none"
        state = record_vote(state, item["name"], int(item["rotation"]), reply)["state"]
    assert not (root / ".organizer").exists()
    decide_votes(root, state)
    logs = list((root / ".organizer" / "votes").glob("*.jsonl"))
    lines = [json.loads(line) for line in logs[0].read_text(encoding="utf-8").splitlines()]
    assert len(logs) == 1 and [line["file"] for line in lines] == sorted(FILES)
    trip = next(line for line in lines if line["file"] == "trip.md")
    assert trip == {"file": "trip.md", "votes": {"0": "osaka", "1": "osaka", "2": "osaka", "4": "osaka"},
                    "replies": {"0": "P2", "1": "P1", "2": "P5", "4": "P3"}, "picked": "osaka"}
    memo = next(line for line in lines if line["file"] == "memo.txt")
    assert memo["votes"] == {"0": None, "1": "none", "2": "none", "4": "none"} and memo["picked"] is None
    assert memo["replies"]["0"] == "P9"


def test_a_long_reply_is_kept_cut_and_the_replies_start_fresh_each_run():
    root, state = started()
    state = start_votes(root, state)["state"]
    state = record_vote(state, "memo.txt", 0, "x" * 500)["state"]
    assert state["replies"]["memo.txt"]["0"] == "x" * REPLY_CHARS
    assert start_votes(root, state)["state"]["replies"] == {}


run_tests(globals())

"""The harness's code steps: the model only picks ids, and everything it names is checked here. Each step
takes the run's state and returns the next one, so a test reads the whole run from return values."""
from fixtures import run_tests, scratch_root

import json

from harness_steps import NO_DRAFT, accept_pick, accept_projects, assemble, draft, menu, next_round, scan
from moving import apply_plan
from plan import parse_plan, rejection_note
from project_sources import parse_listing

FILES = {"kitchen_quote.pdf": "x", "memo.txt": "cabinet sizes for the kitchen", "trip.md": "osaka hotels",
         "japan-trip/flights.pdf": "x"}
MODEL_LIST = '[{"name": "Kitchen Renovation", "about": "the remodel"}, "japan trip", "osaka", {"x": 1}]'


def started():
    root = scratch_root(FILES)
    return root, accept_projects(scan(root)["state"], MODEL_LIST)["state"]


def scanned(files=FILES, listed=""):
    return scan(scratch_root(files), listed)["state"]


def test_scan_lists_top_level_files_with_cards_and_keeps_folders_apart():
    found = scan(scratch_root(FILES))
    assert [item["name"] for item in found["files"]] == ["kitchen_quote.pdf", "memo.txt", "trip.md"]
    assert found["folders"] == "japan-trip" and found["state"]["folders"] == ["japan-trip"]
    assert found["files"][1]["card"] == "memo.txt\ncabinet sizes for the kitchen"
    assert "not a text file" in found["files"][0]["card"]
    assert found["has_list"] == "0" and scan(scratch_root(FILES), "kitchen: cabinets")["has_list"] == "1"


def test_projects_put_existing_folders_first_and_drop_duplicates_file_names_and_junk():
    reply = 'Sure! [{"name": "Kitchen Renovation", "about": "the remodel"}, "japan trip", "memo.txt", "osaka", {"x": 1}]'
    accepted = accept_projects(scanned(), reply)
    assert accepted["ok"] is True
    assert menu(accepted["state"]).splitlines() == ["P1: japan-trip - existing folder", "P2: kitchen-renovation - the remodel",
                                                    "P3: osaka - ", "none: not sure, or it fits no project"]


def test_a_list_cut_off_at_the_token_limit_keeps_its_complete_items():
    reply = '[{"name": "Kitchen Renovation", "about": "quotes"}, {"name": "Osaka Trip", "about": "hotels"}, {"name": "Car Rep'
    state = accept_projects(scanned(), reply)["state"]
    assert menu(state).splitlines()[1:3] == ["P2: kitchen-renovation - quotes", "P3: osaka-trip - hotels"]


def test_too_few_projects_are_sent_back_once_then_kept():
    state = scanned()
    first = accept_projects(state, '["memo", "trip.md", "kitchen"]')
    assert first["ok"] is False and "file names" in first["error"] and first["state"] == state
    last = accept_projects(state, "no json here", last_try=True)
    assert last["ok"] is True and menu(last["state"]).splitlines()[0] == "P1: japan-trip - existing folder"


def many_folders_state():
    folders = {f"Folder {index}/x.txt": "x" for index in range(9)}
    return scanned({**FILES, **folders, "My Photos/a.jpg": "x"})


def test_with_too_many_existing_folders_only_the_named_ones_join_the_new_projects():
    accepted = accept_projects(many_folders_state(), '["my photos", "Kitchen", "Osaka", "Taxes"]')
    assert accepted["ok"] is True
    assert [line.split(" - ")[0] for line in menu(accepted["state"]).splitlines()] == [
        "P1: My Photos", "P2: kitchen", "P3: osaka", "P4: taxes", "none: not sure, or it fits no project"]


def test_too_few_counts_only_new_projects_not_the_existing_folders_kept():
    assert accept_projects(many_folders_state(), '["My Photos", "Folder 1", "Kitchen"]')["ok"] is False


def test_a_bad_pick_is_retried_once_then_left_in_place():
    _, state = started()
    state = accept_pick(state, "memo.txt", "I think P2 fits")["state"]
    retry = accept_pick(state, "trip.md", "the trip folder")
    assert retry["ok"] is False and "P1, P2, P3, none" in retry["error"] and retry["state"] == state
    state = accept_pick(state, "trip.md", "still unsure", last_try=True)["state"]
    state = accept_pick(state, "kitchen_quote.pdf", "P9 or P2")["state"]
    assert assemble(state).splitlines() == ["kitchen_quote.pdf => kitchen-renovation", "memo.txt => kitchen-renovation"]


def test_next_round_sends_back_only_the_files_the_feedback_names_and_stops_after_three_rounds():
    root, state = started()
    state = accept_pick(state, "memo.txt", "P2")["state"]
    rejected = rejection_note("memo.txt does not belong in kitchen-renovation.")
    again = next_round(root, state, rejected)
    assert again["done"] is False and [item["name"] for item in again["files"]] == ["memo.txt"]
    assert again["files"][0]["hint"] == "\n\nThe person said: memo.txt does not belong in kitchen-renovation."
    assert "memo.txt" not in again["state"]["picks"] and next_round(root, state, "1 moved, 0 skipped.")["done"]
    for _ in range(3):
        again = next_round(root, again["state"], rejected)
    assert again["done"] is True and again["state"]["round"] == 4


def test_next_round_reads_the_feedback_from_what_apply_reports():
    root, state = started()
    state = accept_pick(state, "memo.txt", "P2")["state"]
    outcome = apply_plan(root, parse_plan("REJECT: memo.txt is a shopping list\nnot the kitchen"))
    again = next_round(root, state, outcome)
    assert [item["name"] for item in again["files"]] == ["memo.txt"]
    assert again["files"][0]["hint"] == "\n\nThe person said: memo.txt is a shopping list\nnot the kitchen"


def test_next_round_sends_back_a_file_only_when_the_feedback_names_it_whole():
    files = {"a.md": "x", "data.md": "x", "final.csv": "x", "guest list final.csv": "x", "memo.txt": "x"}
    root = scratch_root(files)
    state = accept_projects(scan(root)["state"], MODEL_LIST)["state"]
    rejected = rejection_note("data.md does not belong in osaka; guest list final.csv goes with ./memo.txt.")
    again = next_round(root, state, rejected)
    assert [item["name"] for item in again["files"]] == ["data.md", "guest list final.csv", "memo.txt"]


def test_a_list_the_person_wrote_keeps_every_project_past_the_menu_limit():
    listed = scanned(listed="\n".join(f"work-{n}: part {n}" for n in range(1, 13)))
    assert len(menu(accept_projects(listed)["state"]).splitlines()) == 1 + 12 + 1  # the folder here, the list, none
    model = accept_projects(scanned(), json.dumps([f"work-{n}" for n in range(1, 13)]))["state"]
    assert len(menu(model).splitlines()) == 8 + 1


def test_the_draft_is_the_models_menu_in_the_boxs_own_format():
    _, state = started()
    rows = parse_listing(draft(state))
    assert rows[:2] == [{"name": "japan-trip", "about": ""}, {"name": "kitchen-renovation", "about": "the remodel"}]
    again = accept_projects(scanned(listed=draft(state)))["state"]
    assert menu(again) == menu(state)  # pasted back as is, the same menu


def test_no_menu_gives_a_line_on_writing_one_instead():
    assert draft(scanned()) == NO_DRAFT


def test_steps_keep_nothing_on_disk():
    root, state = started()
    accept_pick(state, "memo.txt", "P2")
    assert not (root / ".organizer").exists()


run_tests(globals())

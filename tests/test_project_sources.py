"""The person's project list: an empty box keeps the measured flow, a filled one replaces the model's list."""
from fixtures import run_tests, scratch_root

from harness_steps import accept_projects, menu, scan
from project_sources import parse_listing

FILES = {"kitchen_quote.pdf": "x", "memo.txt": "cabinet sizes for the kitchen", "trip.md": "osaka hotels",
         "japan-trip/flights.pdf": "x"}
REPLY = '[{"name": "Kitchen Renovation", "about": "the remodel"}, "osaka"]'
# What the web UI sends with the box left empty: the compose default renders one space.
EMPTY_BOX = " "


def run_once(*scan_args):
    found = scan(scratch_root(FILES), *scan_args)
    accepted = accept_projects(found["state"], REPLY)
    return found, menu(accepted["state"]), accepted


def test_an_empty_box_runs_exactly_like_no_input_on_the_models_list():
    assert run_once(EMPTY_BOX) == run_once() == run_once("")


def test_the_persons_list_replaces_the_models():
    state = scan(scratch_root(FILES), "Japan trip: flights and hotels\nTax 2026: receipts")["state"]
    accepted = accept_projects(state, "[]")
    assert accepted["ok"] is True
    # An existing folder keeps "existing folder" as its about.
    assert menu(accepted["state"]).splitlines() == ["P1: japan-trip - existing folder", "P2: tax-2026 - receipts",
                                                    "none: not sure, or it fits no project"]


def test_each_run_starts_from_its_own_box_and_an_empty_one_gives_no_list():
    root = scratch_root(FILES)
    assert scan(root, "Tax 2026: receipts\nOsaka: hotels")["state"]["given"]
    state = scan(root, EMPTY_BOX)["state"]
    assert state["given"] == [] and accept_projects(state, "[]")["ok"] is False


def test_lines_are_name_colon_about_with_bullets_blanks_and_extra_colons():
    text = "- Job hunt: cover letters, interview prep\n\n* Taxes\n  Trip: Osaka: hotels \n: no name\n"
    assert parse_listing(text) == [{"name": "Job hunt", "about": "cover letters, interview prep"},
                                   {"name": "Taxes", "about": ""}, {"name": "Trip", "about": "Osaka: hotels"}]


run_tests(globals())

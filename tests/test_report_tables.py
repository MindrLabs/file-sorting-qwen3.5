from fixtures import run_tests

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from comparisons import QUANT_STEP, f1_difference, primary  # noqa: E402
from report_tables import render  # noqa: E402
from results_data import RESULTS, counts, line, mean, passed, total  # noqa: E402
from tables_real import person_fixes, real_counts, undo_totals  # noqa: E402

FOLDER = re.compile(r"^(v2-(0[1-9]|1\d|20)|dev-(0[1-9]|1[0-2])|downloads|desktop)$")
OTHER_FILES = {"provenance.csv", "first-plan-breakdown.csv", "undo-check.csv"}


def line_files() -> list:
    return sorted(path for path in RESULTS.glob("*.csv") if path.name not in OTHER_FILES)


def test_every_line_file_keeps_the_shared_column_format():
    for path in line_files():
        with path.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle))
        assert header[:2] == ["line", "folder"] and header[-3:] == ["gen_sec", "peak_mb", "first_plan_sha256"], path.name


def test_folders_appear_only_as_labels():
    for path in line_files() + [RESULTS / "first-plan-breakdown.csv"]:
        with path.open(encoding="utf-8", newline="") as handle:
            assert all(FOLDER.match(row["folder"]) for row in csv.DictReader(handle)), path.name


def test_every_line_has_provenance_and_an_index_entry():
    with (RESULTS / "provenance.csv").open(encoding="utf-8", newline="") as handle:
        described = {row["line"] for row in csv.DictReader(handle)}
    index = (RESULTS / "README.md").read_text(encoding="utf-8")
    for path in line_files():
        assert path.stem in described and path.name in index, path.name


def test_sealed_usable_counts_match_the_readme():
    expected = {"sealed-9b-q4km-names-about": 19, "sealed-9b-q4km-names-about-vote": 19, "sealed-9b-q8-names-about": 18,
                "sealed-2b-q8-names-about": 11, "sealed-2b-q4km-names-about": 9, "sealed-2b-q8-names": 3,
                "sealed-9b-q8-model-list": 6, "sealed-2b-q8-model-list": 1, "sealed-4b-q8-model-list": 1,
                "sealed-tfidf-names-about": 16, "sealed-tfidf-names": 10, "sealed-embed-names": 9, "sealed-embed-names-about": 6}
    for name, usable in expected.items():
        assert passed(name) == (usable, 20), name


def test_four_asks_numbers_match_table_5():
    one, four = line("sealed-9b-q4km-names-about"), line("sealed-9b-q4km-names-about-vote")
    assert round(100 * (mean(one, "wrong_share") or 0), 1) == 8.3 and round(100 * (mean(four, "wrong_share") or 0), 1) == 4.3
    moved = {size: [total(counts(f"dev-{size}-q4km-names-about{kind}-8k"), "stay_moved") for kind in ("", "-vote")]
             for size in ("9b", "4b", "2b")}
    assert moved == {"9b": [11, 7], "4b": [90, 47], "2b": [41, 3]}
    assert passed("dev-4b-q4km-names-about-8k") == (2, 12) and passed("dev-4b-q4km-names-about-vote-8k") == (7, 12)


def test_real_downloads_counts_match_table_7():
    expected = {"downloads-9b-q4km-careful-vote-8k": (50, 6, 7), "downloads-9b-q4km-careful-8k": (42, 21, 0),
                "downloads-9b-q4km-casual-8k": (29, 27, 7), "downloads-2b-q4km-careful-8k": (31, 27, 5),
                "downloads-2b-q4km-casual-8k": (22, 34, 7)}
    for name, found in expected.items():
        row = real_counts(name)
        assert (row["right_folder"], row["wrong_folder"], row["not_moved"]) == found, name
    assert [person_fixes(real_counts(f"downloads-9b-q4km-careful{kind}-8k")) for kind in ("", "-vote")] == [25, 16]


def test_quantization_verdicts_match_table_9():
    verdicts = [f1_difference(comparison) for comparison in QUANT_STEP]
    assert [round(found.value, 3) for found in verdicts if found] == [0.003, 0.006, -0.030, -0.054]


def test_primary_family_is_holm_corrected():
    tested = {item.comparison.second: item for item in primary()}
    nine = tested["sealed-9b-q8-names-about"]
    assert (nine.test.only_first, nine.test.only_second) == (0, 12) and nine.holm_p == 8 * 0.00048828125
    assert tested["sealed-9b-q4km-names-about-vote"].test.p == 1.0


def test_no_run_lost_a_file():
    found = undo_totals()
    assert found["runs"] >= 4979 and found["undo_clean"] == found["runs"]


def test_the_report_prints_the_headline_with_its_interval():
    text = render([])
    assert "19/20 = 95% [76, 99]" in text and "6/20 = 30% [15, 52]" in text and "16/20 = 80% [58, 92]" in text


run_tests(globals())

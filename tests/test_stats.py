from fixtures import run_tests

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from stats import (FolderInterval, cells_of, cluster_bootstrap, holm, judge_difference, mcnemar_exact,  # noqa: E402
                   mcnemar_paired, paired_difference, wilson)


def close(value: float, expected: float, tolerance: float = 0.0005) -> bool:
    return abs(value - expected) <= tolerance


def test_wilson_gives_the_published_bounds_for_19_of_20():
    interval = wilson(19, 20)
    assert interval is not None
    assert close(interval.low, 0.764) and close(interval.high, 0.991)


def test_fifteen_of_twenty_is_the_fewest_folders_whose_lower_bound_reaches_one_half():
    fifteen, fourteen = wilson(15, 20), wilson(14, 20)
    assert fifteen is not None and fourteen is not None
    assert fifteen.low >= 0.5 > fourteen.low


def test_wilson_stays_inside_zero_and_one():
    none, every = wilson(0, 20), wilson(20, 20)
    assert none is not None and every is not None
    assert none.low == 0.0 and every.high == 1.0
    assert wilson(0, 0) is None


def test_exact_mcnemar_on_known_tables():
    assert mcnemar_exact(0, 5).p == 0.0625  # 2 * 0.5**5
    assert mcnemar_exact(1, 9).p == 22 / 1024  # 2 * (1 + 10) / 2**10
    assert mcnemar_exact(2, 12).p == 212 / 16384  # 2 * (1 + 14 + 91) / 2**14
    assert mcnemar_exact(3, 3).p == 1.0 and mcnemar_exact(0, 0).p == 1.0


def test_mcnemar_reads_only_the_folders_both_lines_ran():
    first = {"a": True, "b": False, "c": True, "d": False}
    second = {"a": True, "b": True, "c": False, "e": True}
    test = mcnemar_paired(first, second)
    assert (test.only_first, test.only_second, test.p) == (1, 1, 1.0)


def test_holm_on_known_p_values():
    assert [round(p, 9) for p in holm([0.01, 0.04, 0.03, 0.005])] == [0.03, 0.06, 0.06, 0.02]
    assert [round(p, 9) for p in holm([0.01, 0.02, 0.5])] == [0.03, 0.04, 0.5]
    assert holm([0.5, 0.9]) == [1.0, 1.0]


def irregular(shift: bool) -> dict:
    return {f"f{i:02d}": (i * 37 % 17) / 17 + (((i * 13 % 7) - 3) / 50 if shift else 0.0) for i in range(12)}


def test_the_bootstrap_is_the_registered_one():
    """Values printed by bench/harness/cluster_stats.py (seed 20261022) for the same input."""
    difference = paired_difference(cells_of(irregular(False)), cells_of(irregular(True)))
    mean = cluster_bootstrap(cells_of(irregular(False)))
    assert difference is not None and mean is not None
    assert (difference.low, difference.high) == (-0.018333333333333333, 0.028333333333333335)
    assert (mean.low, mean.high) == (0.29901960784313725, 0.6421568627450981)
    assert judge_difference(difference) == "equivalent"


def test_too_few_folders_give_no_interval_and_no_verdict():
    found = cluster_bootstrap(cells_of({"a": 1.0, "b": 0.0}))
    assert found is not None and found.low is None
    assert judge_difference(found) is None


def test_equivalent_needs_the_whole_interval_inside_the_margin():
    assert judge_difference(FolderInterval(0.0, -0.04, 0.04, 20)) == "equivalent"
    assert judge_difference(FolderInterval(0.0, -0.06, 0.04, 20)) == "undecided"
    assert judge_difference(FolderInterval(0.1, 0.01, 0.2, 20)) == "different"


run_tests(globals())

"""The comparisons the README rests on, defined once.

- Primary family: the claims made on the 20 sealed folders. Usable (pass/fail per folder) is compared with an
  exact McNemar test and the family is Holm-corrected together.
- Pair F1 differences: folder bootstrap, same folders for both lines, with the registered verdict
  (different / equivalent within ±0.05 / undecided).
"""
from __future__ import annotations

from typing import List, NamedTuple, Optional, Tuple

from results_data import line, passed, passes, values
from stats import Cells, FolderInterval, McNemar, cells_of, holm, mcnemar_paired, paired_difference

LABELS = {"0.8b-q8": "0.8B", "2b-q8": "2B", "4b-q8": "4B", "9b-q8": "9B", "2b-q4km": "2B Q4_K_M",
          "4b-q4km": "4B Q4_K_M", "4b-q2kxl": "4B UD-Q2_K_XL", "9b-q4km": "9B Q4_K_M"}


class Comparison(NamedTuple):
    name: str
    first: str   # results line before the change
    second: str  # results line after it


class Tested(NamedTuple):
    comparison: Comparison
    first: Tuple[int, int]   # (usable folders, folders)
    second: Tuple[int, int]
    test: McNemar
    holm_p: float
    f1: Optional[FolderInterval]


def menu_change(model: str) -> Comparison:
    return Comparison(f"{LABELS[model]}: model list -> names + about", f"sealed-{model}-model-list",
                      f"sealed-{model}-names-about")


PRIMARY: Tuple[Comparison, ...] = (
    *(menu_change(model) for model in ("0.8b-q8", "2b-q8", "4b-q8", "9b-q8", "2b-q4km", "4b-q4km")),
    Comparison("9B Q4_K_M, names + about: TF-IDF -> model", "sealed-tfidf-names-about", "sealed-9b-q4km-names-about"),
    Comparison("9B Q4_K_M, names + about: one ask -> four asks", "sealed-9b-q4km-names-about",
               "sealed-9b-q4km-names-about-vote"),
)
MENU = tuple(menu_change(model) for model in ("0.8b-q8", "2b-q8", "4b-q8", "9b-q8", "2b-q4km", "4b-q4km", "4b-q2kxl"))
NAMES_ONLY = tuple(Comparison(f"{LABELS[model]}: names -> names + about", f"sealed-{model}-names",
                              f"sealed-{model}-names-about") for model in ("2b-q8", "4b-q8"))
FLOW = tuple(Comparison(f"{LABELS[model]}: tool agent -> step (both make the list)", f"sealed-{model}-tool-agent",
                        f"sealed-{model}-model-list") for model in ("2b-q8", "4b-q8", "9b-q8"))
QUANT_STEP = tuple(Comparison(f"step, names + about: {LABELS[low]} -> {LABELS[high]}", f"sealed-{low}-names-about",
                              f"sealed-{high}-names-about")
                   for low, high in (("9b-q8", "9b-q4km"), ("4b-q8", "4b-q4km"), ("2b-q8", "2b-q4km"), ("4b-q8", "4b-q2kxl")))
QUANT_AGENT = tuple(Comparison(f"tool agent: {LABELS[low]} -> {LABELS[high]}", f"sealed-{low}-tool-agent",
                               f"sealed-{high}-tool-agent")
                    for low, high in (("4b-q8", "4b-q4km"), ("2b-q8", "2b-q4km"), ("4b-q8", "4b-q2kxl")))
BASELINES = (
    *(Comparison(f"names + about: TF-IDF -> {LABELS[model]}", "sealed-tfidf-names-about", f"sealed-{model}-names-about")
      for model in ("2b-q8", "4b-q8", "9b-q8", "9b-q4km")),
    Comparison("names + about: 0.6B embedding -> 9B Q4_K_M", "sealed-embed-names-about", "sealed-9b-q4km-names-about"),
)
AGENT_RULES = tuple(Comparison(f"{LABELS[model]}, dev folders: tool agent v3 -> v4 list rules", f"dev-{model}-tool-agent-v3",
                               f"dev-{model}-tool-agent-v4") for model in ("9b-q8", "4b-q8"))
VOTE_SYNTHETIC = (
    Comparison("sealed, 9B Q4_K_M (65K)", "sealed-9b-q4km-names-about", "sealed-9b-q4km-names-about-vote"),
    *(Comparison(f"dev, {size.upper()} Q4_K_M (8K)", f"dev-{size}-q4km-names-about-8k", f"dev-{size}-q4km-names-about-vote-8k")
      for size in ("9b", "4b", "2b")),
)


def pair_f1(name: str) -> Cells:
    return cells_of(values(line(name), "pair_f1", 0.0))


def f1_difference(comparison: Comparison) -> Optional[FolderInterval]:
    """Second minus first on pair F1; a run without a pair F1 counts 0, as the registered tables did."""
    return paired_difference(pair_f1(comparison.first), pair_f1(comparison.second))


def usable_test(comparison: Comparison) -> McNemar:
    return mcnemar_paired(passes(comparison.first), passes(comparison.second))


def primary() -> List[Tested]:
    tests = [usable_test(comparison) for comparison in PRIMARY]
    adjusted = holm([test.p for test in tests])
    return [Tested(comparison, passed(comparison.first), passed(comparison.second), test, holm_p, f1_difference(comparison))
            for comparison, test, holm_p in zip(PRIMARY, tests, adjusted)]


__all__ = ["AGENT_RULES", "BASELINES", "FLOW", "LABELS", "MENU", "NAMES_ONLY", "PRIMARY", "QUANT_AGENT", "QUANT_STEP", "VOTE_SYNTHETIC",
           "Comparison", "Tested", "f1_difference", "primary", "usable_test"]

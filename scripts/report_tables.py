"""Every README table and summary number, recomputed from results/*.csv with 95% intervals and paired tests.

    python3 scripts/report_tables.py            # all sections, Markdown
    python3 scripts/report_tables.py primary 4  # chosen sections: summary, primary, folders, 1-9, sections,
                                                # desktop, sensitivity, undo

Shares of folders carry Wilson intervals; means and differences resample folders (seed 20261022); usable on the
same 20 sealed folders is compared with an exact McNemar test, Holm-corrected over the primary family.
"""
from __future__ import annotations

import sys
from typing import Callable, Dict, List

import sensitivity
import summary
from comparisons import PRIMARY, primary
from report_format import difference, markdown, p_value, share
from results_data import RESULTS, table
from tables_device import table_1, table_2, table_3
from tables_features import folders, sections_3_1_and_3_6, table_4, table_5, table_6, table_9
from tables_real import desktop, table_7, table_8, undo_check

ALPHA = 0.05


def primary_table() -> str:
    rows = [[tested.comparison.name, share(*tested.first), share(*tested.second),
             f"{tested.test.only_first} / {tested.test.only_second}", p_value(tested.test.p), p_value(tested.holm_p),
             "yes" if tested.holm_p < ALPHA else "no", difference(tested.f1)] for tested in primary()]
    header = ["Comparison (first -> second)", "First usable", "Second usable", "Folders only first / only second pass",
              "Exact McNemar p", "Holm p", "Holm p < 0.05", "Pair F1 difference [95%]"]
    notes = [f"The family is fixed in scripts/comparisons.py (PRIMARY, {len(PRIMARY)} comparisons); Holm keeps the "
             "chance of any false claim in the family at 5%.",
             "McNemar uses only the folders where the two lines disagree, so 19 vs 19 usable can still differ by folder."]
    return markdown("Primary comparisons on the 20 sealed folders", header, rows, notes)


SECTIONS: Dict[str, Callable[[], str]] = {
    "summary": summary.render, "primary": primary_table, "folders": folders,
    "1": table_1, "2": table_2, "3": table_3, "4": table_4, "5": table_5, "6": table_6, "7": table_7, "8": table_8,
    "9": table_9, "sections": sections_3_1_and_3_6, "desktop": desktop, "sensitivity": sensitivity.render,
    "undo": undo_check,
}


def missing_lines() -> List[str]:
    """Lines a table asks for that results/ does not have (a baseline that was not exported, say)."""
    wanted = [f"downloads-embed-{style}" for style in ("names", "careful", "casual")]
    return [name for name in wanted if not table(name)]


def render(names: List[str]) -> str:
    unknown = [name for name in names if name not in SECTIONS]
    if unknown:
        raise SystemExit(f"unknown section {unknown}; choose from {', '.join(SECTIONS)}")
    parts = [SECTIONS[name]() for name in names or list(SECTIONS)]
    absent = missing_lines()
    if absent and not names:
        parts.append("Not in results/ (recorded in the text only, not recomputable here): " + ", ".join(absent))
    return "\n\n".join(parts)


def main(argv: List[str]) -> None:
    if not (RESULTS / "provenance.csv").is_file():
        raise SystemExit(f"no results in {RESULTS}")
    print(render(argv))


if __name__ == "__main__":
    main(sys.argv[1:])

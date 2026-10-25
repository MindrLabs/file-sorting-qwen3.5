"""Tables 7-8, the desktop copy and the undo check: the real folders, one aggregate row per run."""
from __future__ import annotations

from typing import Dict, List, Optional

from report_format import NOT_RUN, markdown
from results_data import Row, counts, line, table
from stats import wilson

REAL_RUNS = (("9B Q4_K_M, careful about, four asks", "downloads-9b-q4km-careful-vote-8k"),
             ("9B Q4_K_M, careful about", "downloads-9b-q4km-careful-8k"),
             ("9B Q4_K_M, casual about", "downloads-9b-q4km-casual-8k"),
             ("2B Q4_K_M, careful about", "downloads-2b-q4km-careful-8k"),
             ("2B Q4_K_M, casual about", "downloads-2b-q4km-casual-8k"))
GRID = (("9B Q4_K_M, four asks", {"careful": "downloads-9b-q4km-careful-vote-8k"}),
        ("9B Q4_K_M, one ask", {"names": "downloads-9b-q4km-names-8k", "careful": "downloads-9b-q4km-careful-8k",
                                "casual": "downloads-9b-q4km-casual-8k"}),
        ("2B, one ask", {"names": "downloads-2b-q8-names", "careful": "downloads-2b-q4km-careful-8k",
                         "casual": "downloads-2b-q4km-casual-8k"}),
        ("0.6B embedding", {style: f"downloads-embed-{style}" for style in ("names", "careful", "casual")}),
        ("TF-IDF", {style: f"downloads-tfidf-{style}" for style in ("names", "careful", "casual")}))
DESKTOP = (("9B Q4_K_M (8K)", "desktop-9b-q4km-model-list-8k"), ("2B", "desktop-2b-q8-model-list"),
           ("4B Q4_K_M", "desktop-4b-q4km-model-list"))


def real_row(name: str, folder: str = "downloads") -> Row:
    return line(name).get(folder) or {}


def real_counts(name: str, folder: str = "downloads") -> Row:
    return counts(name).get(folder) or {}


def whole(value: Optional[float]) -> str:
    return f"{value:.0f}" if value is not None else NOT_RUN


def person_fixes(found: Row) -> float:
    """Files a person still fixes or moves: wrong folder, stay-files moved, labelled files left where they were."""
    return sum(found.get(key) or 0.0 for key in ("wrong_folder", "stay_moved", "not_moved"))


def table_7_row(label: str, name: str) -> List[str]:
    found, row = real_counts(name), real_row(name)
    stay_left = (found.get("stay_total") or 0) - (found.get("stay_moved") or 0)
    return [label, whole(found.get("right_folder")), whole(found.get("wrong_folder")), whole(found.get("not_moved")),
            f"{stay_left:.0f}/{found.get('stay_total') or 0:.0f}", f"{row.get('pair_f1') or 0:.2f}",
            f"{100 * (row.get('wrong_share') or 0):.1f}%", "yes" if (row.get("usable") or 0) >= 1 else "no",
            whole(person_fixes(found))]


def wrong_share(label: str, name: str) -> str:
    found = real_counts(name)
    wrong, labelled = found.get("wrong_folder") or 0, found.get("labelled") or 0
    return f"{label} {wrong:.0f}/{labelled:.0f} = {100 * wrong / labelled:.0f}%" if labelled else f"{label} {NOT_RUN}"


def table_7() -> str:
    header = ["Setting", "Right folder", "Wrong folder", "Not moved", "Stay-files left alone", "Pair F1",
              "Lines to fix", "Usable", "Files a person fixes or moves"]
    notes = ["63 labelled files and 7 stay-files; Mac, 8K context. One folder, one run each: no interval is claimed.",
             "Right folder = the folder named exactly as the file's project. Lines to fix leaves out the 6 ambiguous files.",
             "Wrong folder of the 63 labelled files: " + ", ".join(wrong_share(label, name) for label, name in REAL_RUNS[1:4:2])]
    return markdown("Table 7: real downloads copy, first plan", header, [table_7_row(*run) for run in REAL_RUNS], notes)


def grid_cell(name: Optional[str]) -> str:
    if name is None:
        return "not measured"
    if not table(name):
        return "not in results/"
    return f"{real_row(name).get('pair_f1') or 0:.2f}"


def table_8() -> str:
    rows = [[label, *(grid_cell(cells.get(style)) for style in ("names", "careful", "casual"))] for label, cells in GRID]
    notes = ["2B with names only is 8-bit at 65K context; every other model cell is 4-bit at 8K.",
             "Baselines got the same list as the model and the dev-folder threshold. " + baseline_fix_range()]
    return markdown("Table 8: real downloads copy, pair F1 against the no-AI baselines",
                    ["", "Names only", "Careful about", "Casual about"], rows, notes)


def baseline_fix_range() -> str:
    names = [name for _, cells in GRID[3:] for name in cells.values() if table(name)]
    shares = [real_row(name).get("wrong_share") or 0.0 for name in names]
    usable = sum(1 for name in names if (real_row(name).get("usable") or 0) >= 1)
    if not shares:
        return ""
    return f"Usable baseline cells: {usable} of {len(names)}; lines to fix {100 * min(shares):.0f}-{100 * max(shares):.0f}%."


def desktop() -> str:
    rows = []
    for label, name in DESKTOP:
        found = real_counts(name, "desktop")
        rows.append([label, f"{found.get('stay_moved') or 0:.0f}/{found.get('stay_total') or 0:.0f}"])
    return markdown("Desktop copy: every file should stay (model writes the list)", ["Model", "Files the first plan moved"], rows)


def undo_totals() -> Dict[str, int]:
    rows = table("undo-check")
    return {key: sum(int(row[key]) for row in rows) for key in ("runs", "undo_clean", "failed_runs")}


def undo_check() -> str:
    found = undo_totals()
    lost = found["runs"] - found["undo_clean"]
    bound = wilson(lost, found["runs"])
    upper = f"{100 * bound.high:.2f}%" if bound else NOT_RUN
    return (f"Undo check: {found['undo_clean']} of {found['runs']} measured runs left every file as it was after undo "
            f"({lost} not), over {len(table('undo-check'))} results files; 95% upper bound on the share of runs that "
            f"lose a file: {upper} (Wilson). {found['failed_runs']} runs failed before an undo check.")


__all__ = ["desktop", "person_fixes", "real_counts", "real_row", "table_7", "table_8", "undo_check", "undo_totals"]

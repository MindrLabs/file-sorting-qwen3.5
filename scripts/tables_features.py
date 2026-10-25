"""Tables 4-6 and 9 and the pair-F1 comparisons of sections 3.1, 3.5 and 3.6 (the 20 sealed folders)."""
from __future__ import annotations

from typing import List, Sequence

from comparisons import (AGENT_RULES, BASELINES, FLOW, LABELS, MENU, NAMES_ONLY, QUANT_AGENT, QUANT_STEP, VOTE_SYNTHETIC,
                         Comparison, f1_difference, usable_test)
from report_format import NOT_RUN, difference, folder_mean, markdown, p_value, share
from results_data import counts, line, mean, passed, table, total, values
from stats import wilson

MENUS = (("model list", "model-list"), ("names", "names"), ("names + about", "names-about"))
PASS_LOW = 0.5  # pass: the Wilson lower bound of the usable share is at least one half (15 of 20 folders)


def sealed_cell(name: str) -> str:
    if not table(name):
        return NOT_RUN
    found = passed(name)
    interval = wilson(*found)
    return share(*found) + (" pass" if interval and interval.low >= PASS_LOW else "")


def table_4() -> str:
    rows = [[label, *(sealed_cell(f"sealed-{model}-{menu}") for _, menu in MENUS)] for model, label in LABELS.items()]
    rows += [[name, "n/a", sealed_cell(f"sealed-{method}-names"), sealed_cell(f"sealed-{method}-names-about")]
             for method, name in (("tfidf", "TF-IDF (no AI)"), ("embed", "0.6B embedding"))]
    header = ["Model", *(menu for menu, _ in MENUS)]
    notes = ["Usable folders of 20 sealed folders, step flow, 65K context, with Wilson 95% intervals. "
             "Pass = lower bound at least 50%, i.e. 15 of 20 or more."]
    return markdown("Table 4: sealed folders usable, by who writes the project list", header, rows, notes)


def arrow(first: str, second: str) -> str:
    return f"{first} -> {second}"


def vote_row(comparison: Comparison) -> List[str]:
    one, four = line(comparison.first), line(comparison.second)
    fix = [f"{100 * (mean(rows, 'wrong_share') or 0):.1f}%" for rows in (one, four)]
    stay = [f"{total(counts(name), 'stay_moved'):.0f}" for name in (comparison.first, comparison.second)]
    f1 = [f"{mean(rows, 'pair_f1') or 0:.2f}" for rows in (one, four)]
    return [comparison.name, arrow(share(*passed(comparison.first)), share(*passed(comparison.second))),
            p_value(usable_test(comparison).p), arrow(*fix), arrow(*stay), arrow(*f1), difference(f1_difference(comparison))]


def real_vote_row() -> List[str]:
    names = ("downloads-9b-q4km-careful-8k", "downloads-9b-q4km-careful-vote-8k")
    rows = [line(name).get("downloads") or {} for name in names]
    usable = ["yes" if (row.get("usable") or 0) >= 1 else "no" for row in rows]
    fix = [f"{100 * (row.get('wrong_share') or 0):.1f}%" for row in rows]
    stay = [f"{total(counts(name), 'stay_moved'):.0f}" for name in names]
    f1 = [f"{row.get('pair_f1') or 0:.2f}" for row in rows]
    return ["real downloads, 9B Q4_K_M (8K, one run)", arrow(*usable), "n/a", arrow(*fix), arrow(*stay), arrow(*f1), "n/a"]


def sealed_vote_note() -> str:
    sealed = [line(name) for name in (VOTE_SYNTHETIC[0].first, VOTE_SYNTHETIC[0].second)]
    precision = arrow(*(f"{mean(rows, 'pair_precision') or 0:.2f}" for rows in sealed))
    moved = arrow(*(f"{mean(rows, 'coverage') or 0:.2f}" for rows in sealed))
    return f"Sealed 9B Q4_K_M: pair precision {precision}, share of labelled files moved {moved}."


def table_5() -> str:
    rows = [vote_row(comparison) for comparison in VOTE_SYNTHETIC] + [real_vote_row()]
    header = ["Folders, model", "Usable", "McNemar p", "Lines to fix (mean)", "Stay-files moved", "Pair F1 (mean)",
              "Pair F1 difference [95%]"]
    notes = [sealed_vote_note(), "Dev folders tuned the four-ask rule, so their p-values are descriptive, not a test."]
    return markdown("Table 5: one ask -> four asks (4-bit, names + about)", header, rows, notes)


def table_6() -> str:
    rows = []
    for model in ("0.8b-q8", "2b-q8", "4b-q8", "9b-q8", "2b-q4km", "9b-q4km"):
        found = counts(f"sealed-{model}-names-about")
        rows.append([LABELS[model], folder_mean(values(found, "pick"), 0, percent=True),
                     folder_mean(values(found, "abstain"), 0, percent=True)])
    header = ["Model", "Moved files sent to their project's folder", "Unrelated files left alone"]
    notes = ["Mean over the 20 sealed folders, folder-bootstrap 95% interval; the registered bar for picking is a lower bound of 80%."]
    return markdown("Table 6: picking and leaving alone (names + about)", header, rows, notes)


def differences(title: str, comparisons: Sequence[Comparison], notes: Sequence[str] = ()) -> str:
    rows = [[comparison.name, difference(f1_difference(comparison))] for comparison in comparisons]
    return markdown(title, ["Comparison (second minus first)", "Pair F1 difference [95%], verdict"], rows, notes)


def table_9() -> str:
    return differences("Table 9: pair F1 against 8-bit (same sealed folders)", QUANT_STEP + QUANT_AGENT,
                       ["Folder bootstrap, seed 20261022; equivalent = interval inside ±0.05."])


def folders() -> str:
    """How big the test folders are, from the first-plan counts (labelled files plus files that should stay)."""
    sealed, dev = counts("sealed-9b-q4km-names-about"), counts("dev-9b-q4km-names-about-8k")
    sizes = [(row.get("labelled") or 0) + (row.get("stay_total") or 0) for row in sealed.values()]
    stay = total(dev, "stay_total")
    files = stay + total(dev, "labelled")
    return (f"Test folders: {len(sealed)} sealed folders of {min(sizes):.0f}-{max(sizes):.0f} files each; in the "
            f"{len(dev)} dev folders {stay:.0f} of {files:.0f} files ({100 * stay / files:.0f}%) belong to no project.")


def tool_agent_usable() -> str:
    rows = [[LABELS[model], sealed_cell(f"sealed-{model}-tool-agent"), sealed_cell(f"sealed-{model}-model-list")]
            for model in ("2b-q8", "4b-q8", "9b-q8", "2b-q4km", "4b-q4km", "4b-q2kxl")]
    notes = ["4B Q4_K_M tool agent: v2-03 timed out after 1,800s and is not counted (19 folders)."]
    return markdown("Section 3.6: usable when the model writes the list, by flow", ["Model", "Tool agent", "Step flow"],
                    rows, notes)


def sections_3_1_and_3_6() -> str:
    return "\n\n".join([differences("Section 3.1: giving the list (pair F1)", MENU + NAMES_ONLY), tool_agent_usable(),
                        differences("Section 3.6 and FAQ: flow, baselines, agent list rules (pair F1)",
                                    FLOW + BASELINES + AGENT_RULES)])


__all__ = ["folders", "sections_3_1_and_3_6", "table_4", "table_5", "table_6", "table_9"]

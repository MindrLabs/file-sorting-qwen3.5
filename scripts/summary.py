"""The README summary, item by item, with the interval or test behind each number."""
from __future__ import annotations

from typing import List

from comparisons import NAMES_ONLY, QUANT_STEP, Comparison, f1_difference, primary, usable_test
from report_format import difference, duration, folder_mean, gigabytes, median_time, p_value, share
from results_data import counts, line, mean, passed, peak_gb, seconds, values
from sensitivity import same_plans
from tables_device import swap_range, time_ratio
from tables_real import person_fixes, real_counts, real_row, undo_totals


def arrow_share(comparison: Comparison) -> str:
    test = usable_test(comparison)
    return (f"{share(*passed(comparison.first))} -> {share(*passed(comparison.second))} "
            f"(exact McNemar p = {p_value(test.p)})")


def list_items() -> List[str]:
    best = "sealed-9b-q4km-names-about"
    model_list = ", ".join(f"{label} {share(*passed(f'sealed-{model}-model-list'))}"
                           for model, label in (("9b-q8", "9B"), ("2b-q8", "2B"), ("4b-q8", "4B")))
    names = NAMES_ONLY[0]
    careful, casual = real_counts("downloads-9b-q4km-careful-8k"), real_counts("downloads-9b-q4km-casual-8k")
    return [f"1. Names + about, 9B Q4_K_M: {share(*passed(best))} usable (pass = 15/20). Model writes the list: {model_list}.",
            f"2. 2B names only -> names + about: {arrow_share(names)}. Real downloads, 9B right folder: careful "
            f"{careful.get('right_folder') or 0:.0f}/63 vs casual {casual.get('right_folder') or 0:.0f}/63; pair F1 casual "
            f"{real_row('downloads-9b-q4km-casual-8k').get('pair_f1') or 0:.2f} vs names only "
            f"{real_row('downloads-9b-q4km-names-8k').get('pair_f1') or 0:.2f}."]


def vote_item() -> str:
    one, four = real_counts("downloads-9b-q4km-careful-8k"), real_counts("downloads-9b-q4km-careful-vote-8k")
    tested = next(item for item in primary() if item.comparison.second == "sealed-9b-q4km-names-about-vote")
    fix = [100 * (mean(line(name), "wrong_share") or 0) for name in (tested.comparison.first, tested.comparison.second)]
    ratios = ", ".join(time_ratio(f"dev-{size}-q4km-names-about-8k", f"dev-{size}-q4km-names-about-vote-8k") for size in ("9b", "2b"))
    return (f"3. Four asks, real downloads: wrong folder {one.get('wrong_folder') or 0:.0f} -> {four.get('wrong_folder') or 0:.0f}, "
            f"not moved {one.get('not_moved') or 0:.0f} -> {four.get('not_moved') or 0:.0f}, files a person handles "
            f"{person_fixes(one):.0f} -> {person_fixes(four):.0f} (one folder, one run). Sealed: lines to fix "
            f"{fix[0]:.1f}% -> {fix[1]:.1f}%, usable {share(*tested.first)} -> {share(*tested.second)} (Holm p = "
            f"{p_value(tested.holm_p)}). Time, total four/one asks (dev 9B, 2B): {ratios}.")


def device_item() -> str:
    mac, real = "mac-dev-9b-q4km-names-about-8k", ("downloads-9b-q4km-careful-vote-8k", "downloads-9b-q4km-careful-8k")
    vote, once = (duration(real_row(name).get("gen_sec") or 0.0) for name in real)
    return (f"4. 9B Q4_K_M on a 16GB Mac: peak {gigabytes(peak_gb(mac))}, one ask {median_time(seconds(mac))} per dev "
            f"folder ({swap_range(mac)}). Real downloads, 70 files: four asks {vote} ({swap_range(real[0])}), "
            f"one ask {once} ({swap_range(real[1])}).")


def quant_item() -> str:
    found = "; ".join(f"{comparison.name.split(': ')[1]} {difference(f1_difference(comparison))}" for comparison in QUANT_STEP)
    plans = ", ".join("{}/{}".format(*same_plans(f"dev-{size}-q4km-names-about", f"dev-{size}-q4km-names-about-8k"))
                      for size in ("2b", "4b", "9b"))
    return f"5. Pair F1 against 8-bit, sealed: {found}. 8K vs 65K identical first plans (2B, 4B, 9B Q4_K_M): {plans}."


def stay_item() -> str:
    desk = ", ".join(f"{label} {real_counts(name, 'desktop').get('stay_moved') or 0:.0f}/30"
                     for label, name in (("9B Q4_K_M", "desktop-9b-q4km-model-list-8k"), ("2B", "desktop-2b-q8-model-list"),
                                         ("4B Q4_K_M", "desktop-4b-q4km-model-list")))
    alone = ", ".join(f"{label} {folder_mean(values(counts(f'sealed-{model}-names-about'), 'abstain'), 0, True)}"
                      for model, label in (("9b-q8", "9B"), ("4b-q8", "4B")))
    return f"6. Desktop copy, files moved by the first plan: {desk}. Sealed, unrelated files left alone: {alone}."


def real_f1(name: str) -> str:
    value = real_row(name).get("pair_f1")
    return f"{value:.2f}" if value is not None else "not in results/"


def baseline_item() -> str:
    menus = ("names", "careful", "casual")
    model = dict(zip(menus, ("downloads-9b-q4km-names-8k", "downloads-9b-q4km-careful-8k", "downloads-9b-q4km-casual-8k")))
    shown = "; ".join(f"{menu}: 9B one ask {real_f1(model[menu])}, TF-IDF {real_f1(f'downloads-tfidf-{menu}')}, "
                      f"embedding {real_f1(f'downloads-embed-{menu}')}" for menu in menus)
    return f"7. TF-IDF, names + about, sealed: {share(*passed('sealed-tfidf-names-about'))}. Real downloads pair F1, {shown}."


def undo_item() -> str:
    found = undo_totals()
    return f"8. Undo restored every file in {found['undo_clean']} of {found['runs']} runs (see the undo check)."


def render() -> str:
    items = list_items() + [vote_item(), device_item(), quant_item(), stay_item(), baseline_item(), undo_item()]
    return "### Summary numbers\n\n" + "\n".join(items)


__all__ = ["render"]

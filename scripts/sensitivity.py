"""Does a result move when only the machine or the context length changes? First plans compared by sha256."""
from __future__ import annotations

from typing import List, Tuple

from report_format import NOT_RUN, gigabytes, markdown
from results_data import Row, failed_runs, first_plans, line, peak_gb

DEVICE_PAIRS = (  # label, RTX 4090 line, Mac line: same setting, same dev-01..04 folders, 8K context
    ("9B Q4_K_M, four asks", "dev-9b-q4km-names-about-vote-8k", "mac-dev-9b-q4km-names-about-vote-8k"),
    ("9B Q4_K_M, one ask", "dev-9b-q4km-names-about-8k", "mac-dev-9b-q4km-names-about-8k"),
    ("2B Q4_K_M, one ask", "dev-2b-q4km-names-about-8k", "mac-dev-2b-q4km-names-about-8k"),
)


def same_plans(first: str, second: str) -> Tuple[int, int]:
    """(folders whose first plans are byte-identical, folders both lines ran)."""
    one, other = first_plans(first), first_plans(second)
    shared = sorted(set(one) & set(other))
    return sum(1 for folder in shared if one[folder] == other[folder]), len(shared)


def pair(first: Row, second: Row, key: str, digits: int) -> str:
    found = [row.get(key) for row in (first, second)]
    return " / ".join(f"{value:.{digits}f}" if value is not None else NOT_RUN for value in found)


def not_compared(four: str, mac: str, folder: str) -> str:
    """Why a folder is left out: a run on either machine that did not complete is not a model outcome."""
    for machine, name in (("4090", four), ("Mac", mac)):
        reason = failed_runs(name).get(folder)
        if reason:
            return f"not compared: {machine} run {reason}"
    return ""


def device_row(label: str, four: str, mac: str, folder: str) -> List[str]:
    skipped = not_compared(four, mac, folder)
    if skipped:
        return [label, folder, skipped, NOT_RUN, NOT_RUN]
    gpu, apple = line(four)[folder], line(mac)[folder]
    same = "same" if first_plans(four).get(folder) == first_plans(mac).get(folder) else "different"
    return [label, folder, same, pair(gpu, apple, "usable", 0), pair(gpu, apple, "pair_f1", 3)]


def device_rows(label: str, four: str, mac: str) -> List[List[str]]:
    return [device_row(label, four, mac, folder) for folder in sorted(set(line(four)) & set(line(mac)))]


def machines() -> str:
    rows = [row for setting in DEVICE_PAIRS for row in device_rows(*setting)]
    totals = [f"{label}: {'{}/{}'.format(*same_plans(four, mac))} identical among completed runs"
              for label, four, mac in DEVICE_PAIRS]
    header = ["Setting", "Folder", "First plan, Mac vs 4090", "Usable, 4090 / Mac", "Pair F1, 4090 / Mac"]
    notes = ["Same model file, settings and folders; the machine and its llama.cpp and model-compose builds differ (four asks: the compose file revision too).", "; ".join(totals)]
    return markdown("Sensitivity: RTX 4090 vs 16GB Mac (8K context)", header, rows, notes)


def contexts() -> str:
    rows = []
    for size in ("2b", "4b", "9b"):
        long, short = f"dev-{size}-q4km-names-about", f"dev-{size}-q4km-names-about-8k"
        rows.append([f"{size.upper()} Q4_K_M", "{}/{}".format(*same_plans(long, short)),
                     f"{gigabytes(peak_gb(long))} -> {gigabytes(peak_gb(short))}"])
    return markdown("Sensitivity: 65K vs 8K context on the 12 dev folders (RTX 4090)",
                    ["Setting", "Byte-identical first plans", "Peak memory, 65K -> 8K"], rows)


def render() -> str:
    return "\n\n".join([machines(), contexts()])


__all__ = ["DEVICE_PAIRS", "contexts", "machines", "render", "same_plans"]

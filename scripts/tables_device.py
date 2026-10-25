"""Tables 1-3: the recommended settings, memory and time per folder (README section 2)."""
from __future__ import annotations

from typing import List, Optional

from report_format import NOT_RUN, gigabytes, markdown, median_time, share
from results_data import line, passed, peak_gb, provenance, seconds, table, total

SETTINGS = (  # label, sealed line, Mac line, RTX 4090 line, real downloads line
    ("9B Q4_K_M, four asks (first tab)", "sealed-9b-q4km-names-about-vote", "mac-dev-9b-q4km-names-about-vote-8k",
     "dev-9b-q4km-names-about-vote-8k", "downloads-9b-q4km-careful-vote-8k"),
    ("9B Q4_K_M, one ask", "sealed-9b-q4km-names-about", "mac-dev-9b-q4km-names-about-8k",
     "dev-9b-q4km-names-about-8k", "downloads-9b-q4km-careful-8k"),
    ("2B Q4_K_M, one ask", "sealed-2b-q4km-names-about", "mac-dev-2b-q4km-names-about-8k",
     "dev-2b-q4km-names-about-8k", "downloads-2b-q4km-careful-8k"),
)
MAC_RUNS = ("mac-dev-9b-q4km-names-about-8k", "mac-dev-2b-q4km-names-about-8k", "mac-dev-9b-q4km-names-about-vote-8k",
            "downloads-9b-q4km-careful-8k", "downloads-9b-q4km-careful-vote-8k")
SWAP_GROWTH_MB = 512  # a Mac run whose swap grew more than this is flagged: its times are not comparable


def swap_note(name: str) -> str:
    found = provenance(name)
    before, after = found.get("swap_before_mb") or "", found.get("swap_after_mb") or ""
    if not before or not after or float(after) - float(before) <= SWAP_GROWTH_MB:
        return ""
    return f", swap grew {float(before) / 1024:.1f} -> {float(after) / 1024:.1f}GB"


def model_file(name: str) -> str:
    return provenance(name).get("gguf_size") or NOT_RUN


def timed(name: str) -> str:
    found = seconds(name)
    return median_time(found) + swap_note(name) if found else NOT_RUN


def real_verdict(name: str) -> str:
    row = line(name).get("downloads")
    if not row or row.get("usable") is None or row.get("wrong_share") is None:
        return NOT_RUN
    usable, fix = row["usable"] or 0.0, row["wrong_share"] or 0.0
    return f"{'usable' if usable >= 1 else 'not usable'} (lines to fix {100 * fix:.1f}%)"


def sealed_share(name: str) -> str:
    return share(*passed(name)) if table(name) else NOT_RUN


def table_1() -> str:
    rows = [[label, model_file(sealed), gigabytes(peak_gb(mac)), timed(mac), timed(four), sealed_share(sealed), real_verdict(real)]
            for label, sealed, mac, four, real in SETTINGS]
    header = ["Setting", "Model file", "Memory, 16GB Mac", "Mac, one folder", "RTX 4090, one folder",
              "Sealed folders usable [95% CI]", "Real downloads (one run)"]
    notes = ["Times are medians over dev folders (fastest-slowest in brackets), model load excluded.",
             "Mac memory and time: dev-01..04 at 8K context; sealed folders: 4090 at 65K context.",
             "Swap did not grow during the Mac runs (four asks: 0 before and after)."]
    return markdown("Table 1: recommended settings (names + about)", header, rows, notes)


def memory_row(label: str, long: str, short: str, mac: Optional[str]) -> List[str]:
    mac_value = gigabytes(peak_gb(mac)) if mac and table(mac) else "not measured"
    return [label, model_file(short), gigabytes(peak_gb(long)), gigabytes(peak_gb(short)), mac_value]


def table_2() -> str:
    rows = [memory_row(f"{size.upper()} Q4_K_M", f"dev-{size}-q4km-names-about", f"dev-{size}-q4km-names-about-8k",
                       f"mac-dev-{size}-q4km-names-about-8k" if size != "4b" else None) for size in ("9b", "4b", "2b")]
    header = ["Setting", "Model file", "4090, 65K context", "4090, 8K context", "16GB Mac, 8K context"]
    return markdown("Table 2: peak memory (largest over folders, 1GB = 1024MB)", header, rows)


def time_ratio(one: str, four: str) -> str:
    """Total generation time of the four-ask run over the one-ask run on the same folders."""
    if not table(one) or not table(four):
        return NOT_RUN
    return f"{total(line(four), 'gen_sec') / total(line(one), 'gen_sec'):.2f}x"


def table_3() -> str:
    rows = [[f"{size.upper()} Q4_K_M", timed(f"dev-{size}-q4km-names-about-8k"), timed(f"dev-{size}-q4km-names-about-vote-8k"),
             time_ratio(f"dev-{size}-q4km-names-about-8k", f"dev-{size}-q4km-names-about-vote-8k"),
             timed(f"mac-dev-{size}-q4km-names-about-8k"), timed(f"mac-dev-{size}-q4km-names-about-vote-8k")]
            for size in ("9b", "4b", "2b")]
    header = ["Setting", "4090, one ask", "4090, four asks", "Four asks / one ask (total)", "16GB Mac, one ask",
              "16GB Mac, four asks"]
    notes = [f"Sealed folders, 9B Q4_K_M at 65K: four asks / one ask = "
             f"{time_ratio('sealed-9b-q4km-names-about', 'sealed-9b-q4km-names-about-vote')} (total over 20 folders).",
             "Mac swap before -> after each run: " + "; ".join(f"{name} {swap_range(name)}" for name in MAC_RUNS)]
    return markdown("Table 3: time per folder at 8K context (median)", header, rows, notes)


def swap_range(name: str) -> str:
    found = provenance(name)
    before, after = found.get("swap_before_mb") or "", found.get("swap_after_mb") or ""
    if not before or not after:
        return "swap not recorded"
    return f"swap {float(before) / 1024:.1f} -> {float(after) / 1024:.1f}GB"


__all__ = ["swap_range", "table_1", "table_2", "table_3", "time_ratio"]

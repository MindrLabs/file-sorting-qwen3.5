"""95% intervals and paired tests for folder-level results: Wilson, exact McNemar, Holm, folder bootstrap.

The bootstrap is the registered one (seed 20261022, 2000 draws, folders resampled first), so a difference
prints the same interval it had when the README was written. A share of folders gets a Wilson interval; two
lines on the same folders are compared folder by folder (McNemar for pass/fail, the bootstrap for pair F1).
"""
from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple, TypeVar

Z95 = 1.96
SEED = 20261022
BOOTSTRAP_DRAWS = 2000
MIN_FOLDERS = 5  # below this, resampling folders is too coarse to trust
EQUIVALENCE_MARGIN = 0.05  # pair F1: a difference inside ±0.05 counts as "equivalent"

Cell = Tuple[str, str]  # (folder, reviewer mode)
Cells = Dict[Cell, List[float]]
Pair = Tuple[List[float], List[float]]
T = TypeVar("T")


class Interval(NamedTuple):
    value: float
    low: float
    high: float
    n: int


class FolderInterval(NamedTuple):
    value: float
    low: Optional[float]  # None: too few folders for an interval
    high: Optional[float]
    folders: int


class McNemar(NamedTuple):
    only_first: int   # folders where only the first line passed
    only_second: int  # folders where only the second line passed
    p: float          # exact two-sided p over the folders that disagree


def wilson(passed: int, n: int) -> Optional[Interval]:
    if n == 0:
        return None
    share = passed / n
    centre = (share + Z95 ** 2 / (2 * n)) / (1 + Z95 ** 2 / n)
    half = Z95 * math.sqrt(share * (1 - share) / n + Z95 ** 2 / (4 * n * n)) / (1 + Z95 ** 2 / n)
    return Interval(share, max(0.0, centre - half), min(1.0, centre + half), n)


def binomial_two_sided(smaller: int, n: int) -> float:
    """P(at most `smaller` heads in n fair tosses), doubled and capped at 1."""
    tail = sum(math.comb(n, k) for k in range(smaller + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def mcnemar_exact(only_first: int, only_second: int) -> McNemar:
    discordant = only_first + only_second
    p = binomial_two_sided(min(only_first, only_second), discordant) if discordant else 1.0
    return McNemar(only_first, only_second, p)


def mcnemar_paired(first: Dict[str, bool], second: Dict[str, bool]) -> McNemar:
    """Pass/fail of two lines on the folders both have."""
    shared = sorted(set(first) & set(second))
    return mcnemar_exact(sum(1 for folder in shared if first[folder] and not second[folder]),
                         sum(1 for folder in shared if second[folder] and not first[folder]))


def holm(pvalues: Sequence[float]) -> List[float]:
    """Holm step-down adjusted p-values, in the order given; each stays at or above the one before it."""
    order = sorted(range(len(pvalues)), key=lambda index: pvalues[index])
    adjusted, running = [0.0] * len(pvalues), 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[index]))
        adjusted[index] = running
    return adjusted


def average(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def cells_of(values: Dict[str, float]) -> Cells:
    """One run per folder, as every results/*.csv line has."""
    return {(folder, "edit"): [value] for folder, value in values.items()}


def folders_of(cells: Cells) -> List[List[List[float]]]:
    grouped: Dict[str, List[List[float]]] = {}
    for (folder, _), values in sorted(cells.items()):
        if values:
            grouped.setdefault(folder, []).append(values)
    return list(grouped.values())


def shared_folders(first: Cells, second: Cells) -> List[List[Pair]]:
    grouped: Dict[str, List[Pair]] = {}
    for cell in sorted(set(first) & set(second)):
        if first[cell] and second[cell]:
            grouped.setdefault(cell[0], []).append((first[cell], second[cell]))
    return list(grouped.values())


def folders_mean(folders: List[List[List[float]]]) -> float:
    return average([average([average(cell) for cell in folder]) for folder in folders])


def gap(folders: List[List[Pair]]) -> float:
    """Second minus first, cell by cell, then folder by folder."""
    return average([average([average(second) - average(first) for first, second in folder]) for folder in folders])


def resample(folders: List[List[List[float]]], draw: random.Random) -> List[List[List[float]]]:
    picked = [draw.choice(folders) for _ in folders]
    return [[draw.choices(cell, k=len(cell)) for cell in folder] for folder in picked]


def resample_pairs(folders: List[List[Pair]], draw: random.Random) -> List[List[Pair]]:
    picked = [draw.choice(folders) for _ in folders]
    return [[(draw.choices(first, k=len(first)), draw.choices(second, k=len(second))) for first, second in folder]
            for folder in picked]


def folder_interval(folders: List[T], statistic: Callable[[List[T]], float],
                    resampler: Callable[[List[T], random.Random], List[T]], seed: int) -> Optional[FolderInterval]:
    if not folders:
        return None
    value = statistic(folders)
    if len(folders) < MIN_FOLDERS:
        return FolderInterval(value, None, None, len(folders))
    draw = random.Random(seed)
    draws = sorted(statistic(resampler(folders, draw)) for _ in range(BOOTSTRAP_DRAWS))
    return FolderInterval(value, draws[int(0.025 * BOOTSTRAP_DRAWS)], draws[int(0.975 * BOOTSTRAP_DRAWS) - 1], len(folders))


def cluster_bootstrap(cells: Cells, seed: int = SEED) -> Optional[FolderInterval]:
    return folder_interval(folders_of(cells), folders_mean, resample, seed)


def paired_difference(first: Cells, second: Cells, seed: int = SEED) -> Optional[FolderInterval]:
    """Second minus first on the cells both ran; the same folders are drawn for both."""
    return folder_interval(shared_folders(first, second), gap, resample_pairs, seed)


def judge_difference(difference: Optional[FolderInterval], margin: float = EQUIVALENCE_MARGIN) -> Optional[str]:
    """"different" when the interval leaves out zero, "equivalent" when it sits inside ±margin, else "undecided"."""
    if difference is None or difference.low is None or difference.high is None:
        return None
    if difference.low > 0 or difference.high < 0:
        return "different"
    return "equivalent" if -margin <= difference.low and difference.high <= margin else "undecided"


__all__ = ["BOOTSTRAP_DRAWS", "EQUIVALENCE_MARGIN", "MIN_FOLDERS", "SEED", "Cells", "FolderInterval", "Interval",
           "McNemar", "cells_of", "cluster_bootstrap", "holm", "judge_difference", "mcnemar_exact", "mcnemar_paired",
           "paired_difference", "wilson"]

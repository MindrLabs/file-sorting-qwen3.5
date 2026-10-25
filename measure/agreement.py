"""Chance-corrected agreement between the labelled projects and where a plan put the files: the adjusted
Rand index (ARI) and adjusted mutual information (AMI, arithmetic-mean normalisation as in scikit-learn).

Files without a label, and files the plan left alone, are each a group of their own; files labelled `*`
are not scored. Leaving every file where it is and putting every file in one folder both score 0.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Dict, Hashable, Iterable, Mapping, Optional, Tuple

from .reviewer import ANY, Answers

Labels = Mapping[str, Hashable]
Group = Tuple[str, Optional[str]]  # ("project", label), ("folder", name) or ("alone", file)


def partitions(answers: Answers, where: Mapping[str, str]) -> Tuple[Dict[str, Group], Dict[str, Group]]:
    """The labelled grouping and the plan's grouping over the same scored files."""
    scored = [name for name, project in answers.items() if project != ANY]
    gold: Dict[str, Group] = {name: ("project", answers[name]) if answers[name] else ("alone", name)
                              for name in scored}
    found: Dict[str, Group] = {name: ("folder", where[name]) if name in where else ("alone", name)
                               for name in scored}
    return gold, found


def agreement(answers: Answers, where: Mapping[str, str]) -> Dict[str, Optional[float]]:
    gold, found = partitions(answers, where)
    return {"ari": rounded(adjusted_rand(gold, found)),
            "ami": rounded(adjusted_mutual_information(gold, found))}


def rounded(value: Optional[float]) -> Optional[float]:
    """Three places, and a rounding error just below zero printed as 0.0 rather than -0.0."""
    return round(value, 3) + 0.0 if value is not None else None


def pairs(count: int) -> float:
    return count * (count - 1) / 2


def adjusted_rand(gold: Labels, found: Labels) -> Optional[float]:
    """None when both groupings are trivial in the same way and the index is undefined."""
    n = len(gold)
    if n < 2:
        return None
    both = sum(pairs(count) for count in Counter((gold[name], found[name]) for name in gold).values())
    rows = sum(pairs(count) for count in Counter(gold.values()).values())
    cols = sum(pairs(count) for count in Counter(found[name] for name in gold).values())
    expected = rows * cols / pairs(n)
    best = (rows + cols) / 2
    return (both - expected) / (best - expected) if not math.isclose(best, expected) else None


def entropy(counts: Iterable[int], n: int) -> float:
    return -sum(count / n * math.log(count / n) for count in counts if count)


def mutual_information(gold: Labels, found: Labels) -> float:
    n = len(gold)
    table = Counter((gold[name], found[name]) for name in gold)
    rows, cols = Counter(gold.values()), Counter(found[name] for name in gold)
    return sum(cell / n * math.log(n * cell / (rows[a] * cols[b])) for (a, b), cell in table.items())


def log_hypergeometric(k: int, a: int, b: int, n: int) -> float:
    """log P(a group of size a and a group of size b share k of n files) when files are shuffled."""
    return (math.lgamma(a + 1) + math.lgamma(b + 1) + math.lgamma(n - a + 1) + math.lgamma(n - b + 1)
            - math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(a - k + 1) - math.lgamma(b - k + 1)
            - math.lgamma(n - a - b + k + 1))


def pair_expectation(a: int, b: int, n: int) -> float:
    shares = range(max(1, a + b - n), min(a, b) + 1)
    return sum(k / n * math.log(n * k / (a * b)) * math.exp(log_hypergeometric(k, a, b, n)) for k in shares)


def expected_mutual_information(gold: Labels, found: Labels) -> float:
    """The mean mutual information over every shuffle of the files that keeps both groups' sizes."""
    n = len(gold)
    rows, cols = Counter(gold.values()).values(), Counter(found[name] for name in gold).values()
    return sum(pair_expectation(a, b, n) for a in rows for b in cols)


def adjusted_mutual_information(gold: Labels, found: Labels) -> Optional[float]:
    """None when the groupings leave nothing to correct for (the denominator is zero)."""
    n = len(gold)
    if n < 2:
        return None
    expected = expected_mutual_information(gold, found)
    found_sizes = Counter(found[name] for name in gold).values()
    mean = (entropy(Counter(gold.values()).values(), n) + entropy(found_sizes, n)) / 2
    if math.isclose(mean, expected, abs_tol=1e-12):
        return None
    return (mutual_information(gold, found) - expected) / (mean - expected)


__all__ = ["adjusted_mutual_information", "adjusted_rand", "agreement"]

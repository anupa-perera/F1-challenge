from __future__ import annotations

"""Historical regression checks for high-support strategy truths.

These checks sit between cheap scorer invariants and expensive model changes.
They protect the patterns the historical validation split keeps repeating:

- mirrored one-stop winner direction in strong contexts
- sign of the biggest family residual biases
- whether specialized runtime leaves still beat their parent fallback

The goal is not to freeze every number. The goal is to stop us from keeping
changes that break high-confidence truths while still looking acceptable on one
aggregate score.
"""

from dataclasses import dataclass

from .analysis import (
    DEFAULT_CROSSOVER_FAMILY_PAIRS,
    summarize_runtime_bucket_value,
    summarize_strategy_crossovers,
    summarize_historical_residuals,
)
from .historical_data import HistoricalRace


@dataclass(frozen=True)
class RegressionCheckResult:
    name: str
    passed: bool
    details: str


EXPECTED_CROSSOVER_WINNERS = (
    ("medium_high_pit", "MEDIUM->HARD / 1 stop", "HARD->MEDIUM / 1 stop", "MEDIUM->HARD / 1 stop"),
    ("medium_high_pit", "SOFT->HARD / 1 stop", "HARD->SOFT / 1 stop", "SOFT->HARD / 1 stop"),
    ("medium_high_pit", "SOFT->MEDIUM / 1 stop", "MEDIUM->SOFT / 1 stop", "SOFT->MEDIUM / 1 stop"),
    ("short_warm", "MEDIUM->HARD / 1 stop", "HARD->MEDIUM / 1 stop", "MEDIUM->HARD / 1 stop"),
    ("short_warm", "SOFT->MEDIUM / 1 stop", "MEDIUM->SOFT / 1 stop", "MEDIUM->SOFT / 1 stop"),
    ("short_cool_mild", "SOFT->HARD / 1 stop", "HARD->SOFT / 1 stop", "HARD->SOFT / 1 stop"),
)

EXPECTED_RESIDUAL_SIGNS = (
    ("HARD->MEDIUM->HARD / 2 stops", "negative"),
    ("MEDIUM->HARD->MEDIUM / 2 stops", "negative"),
    ("MEDIUM->HARD / 1 stop", "positive"),
    ("HARD->MEDIUM / 1 stop", "positive"),
)

EXPECTED_POSITIVE_BUCKET_GAINS = (
    "short_warm",
    "short_cool_mild",
    "medium_high_pit_hot",
    "medium_high_pit_cool",
    "medium_cool_slow_cool",
)


def _check_crossovers(races: list[HistoricalRace]) -> list[RegressionCheckResult]:
    summaries = summarize_strategy_crossovers(
        races,
        family_pairs=DEFAULT_CROSSOVER_FAMILY_PAIRS,
        min_total=30,
    )
    summary_map = {
        (summary.context_key, summary.left_family, summary.right_family): summary
        for summary in summaries
    }

    results: list[RegressionCheckResult] = []
    for context_key, left_family, right_family, expected_winner in EXPECTED_CROSSOVER_WINNERS:
        summary = summary_map.get((context_key, left_family, right_family))
        if summary is None:
            results.append(
                RegressionCheckResult(
                    name=f"crossover:{context_key}:{left_family}:{right_family}",
                    passed=False,
                    details="summary missing",
                )
            )
            continue
        results.append(
            RegressionCheckResult(
                name=f"crossover:{context_key}:{left_family}:{right_family}",
                passed=summary.winner == expected_winner,
                details=(
                    f"winner={summary.winner} "
                    f"left_wins={summary.left_wins} "
                    f"right_wins={summary.right_wins}"
                ),
            )
        )
    return results


def _check_residual_signs(races: list[HistoricalRace]) -> list[RegressionCheckResult]:
    summary = summarize_historical_residuals(
        races,
        top=50,
        min_samples=40,
    )
    family_summaries = {
        group.key: group.average_rank_error
        for group in (*summary.family_overrated, *summary.family_underrated)
    }

    results: list[RegressionCheckResult] = []
    for family, expected_sign in EXPECTED_RESIDUAL_SIGNS:
        average_rank_error = family_summaries.get(family)
        if average_rank_error is None:
            results.append(
                RegressionCheckResult(
                    name=f"residual_sign:{family}",
                    passed=False,
                    details="summary missing",
                )
            )
            continue
        passed = average_rank_error < 0 if expected_sign == "negative" else average_rank_error > 0
        results.append(
            RegressionCheckResult(
                name=f"residual_sign:{family}",
                passed=passed,
                details=f"average_rank_error={average_rank_error:+.3f}",
            )
        )
    return results


def _check_bucket_value(races: list[HistoricalRace]) -> list[RegressionCheckResult]:
    summaries = summarize_runtime_bucket_value(races)
    summary_map = {summary.context_key: summary for summary in summaries}

    results: list[RegressionCheckResult] = []
    for context_key in EXPECTED_POSITIVE_BUCKET_GAINS:
        summary = summary_map.get(context_key)
        if summary is None:
            results.append(
                RegressionCheckResult(
                    name=f"bucket_gain:{context_key}",
                    passed=False,
                    details="summary missing",
                )
            )
            continue
        results.append(
            RegressionCheckResult(
                name=f"bucket_gain:{context_key}",
                passed=summary.exact_gain > 0,
                details=(
                    f"exact_gain={summary.exact_gain:+d} "
                    f"pairwise_gain={summary.pairwise_gain:+.4%}"
                ),
            )
        )
    return results


def run_historical_regressions(
    races: list[HistoricalRace],
) -> list[RegressionCheckResult]:
    results: list[RegressionCheckResult] = []
    results.extend(_check_crossovers(races))
    results.extend(_check_residual_signs(races))
    results.extend(_check_bucket_value(races))
    return results

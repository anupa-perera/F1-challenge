from __future__ import annotations

"""Shared exact-order and pairwise evaluation helpers.

Calibration, gate auditing, and historical analysis all answer the same core
question: given a predicted finishing order, how well does it match the labeled
race result? Keeping that logic here avoids subtle drift between tools.
"""

from dataclasses import dataclass
from typing import Callable, Sequence

from .historical_data import HistoricalRace


PAIRWISE_COMPARISONS_PER_RACE = 190


@dataclass(frozen=True)
class Evaluation:
    exact_matches: int
    race_count: int
    pairwise_correct: int
    pairwise_total: int

    @property
    def exact_rate(self) -> float:
        if self.race_count == 0:
            return 0.0
        return self.exact_matches / self.race_count

    @property
    def pairwise_rate(self) -> float:
        if self.pairwise_total == 0:
            return 0.0
        return self.pairwise_correct / self.pairwise_total


def pairwise_correct_count(
    actual_order: Sequence[str],
    predicted_order: Sequence[str],
) -> int:
    """Count correctly ordered driver pairs for one race."""

    predicted_rank = {
        driver_id: index for index, driver_id in enumerate(predicted_order)
    }
    pairwise_correct = 0
    for index, left_driver in enumerate(actual_order):
        left_rank = predicted_rank[left_driver]
        for right_driver in actual_order[index + 1 :]:
            if left_rank < predicted_rank[right_driver]:
                pairwise_correct += 1
    return pairwise_correct


def evaluate_races(
    races: list[HistoricalRace],
    predictor: Callable[[HistoricalRace], Sequence[str]],
) -> Evaluation:
    """Evaluate a predictor across labeled races."""

    exact_matches = 0
    pairwise_correct = 0

    for race in races:
        predicted_order = tuple(predictor(race))
        if predicted_order == race.actual_order:
            exact_matches += 1
        pairwise_correct += pairwise_correct_count(
            actual_order=race.actual_order,
            predicted_order=predicted_order,
        )

    return Evaluation(
        exact_matches=exact_matches,
        race_count=len(races),
        pairwise_correct=pairwise_correct,
        pairwise_total=len(races) * PAIRWISE_COMPARISONS_PER_RACE,
    )

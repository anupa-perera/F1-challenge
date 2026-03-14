from __future__ import annotations

"""Self-analysis helpers for understanding solver failures across many cases.

This module intentionally groups both labeled-suite diagnostics and historical
pattern mining. They answer the same higher-level question: what does the model
get wrong, and what does the historical data actually support?
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import json

from .historical_data import HistoricalRace
from .models import DriverPlan
from .parsing import parse_race_input
from .reporting import first_divergence
from .scoring import predict_finishing_order


@dataclass(frozen=True)
class CaseComparison:
    case_name: str
    exact_match: bool
    first_divergence_position: int | None
    first_divergence_predicted_signature: str | None
    first_divergence_expected_signature: str | None
    winner_changed: bool
    predicted_winner_signature: str
    expected_winner_signature: str


@dataclass(frozen=True)
class SuiteSummary:
    case_count: int
    exact_matches: int
    first_divergence_counts: Counter
    first_divergence_strategy_counts: Counter
    winner_mismatch_counts: Counter


START_BANDS = {
    "front": range(1, 6),
    "mid": range(6, 15),
    "back": range(15, 21),
}


@dataclass(frozen=True)
class WinnerPattern:
    start_tire: str
    stops: int
    first_stint_laps: int
    first_stint_fraction: float
    sequence: str
    total_laps: int
    track_temp: int
    pit_burden: float
    thermal_stress: float


@dataclass(frozen=True)
class BucketSummary:
    race_count: int
    two_stop_rate: float
    start_tire_distribution: dict[str, float]
    average_first_stint_fraction: float
    top_sequences: list[tuple[str, int]]


def temp_bucket(track_temp: int) -> str:
    if track_temp <= 24:
        return "cool"
    if track_temp <= 30:
        return "mild"
    if track_temp <= 36:
        return "warm"
    return "hot"


def laps_bucket(total_laps: int) -> str:
    if total_laps <= 36:
        return "short"
    if total_laps <= 52:
        return "medium"
    return "long"


def pit_burden_bucket(pit_burden: float) -> str:
    if pit_burden <= 0.245:
        return "low"
    if pit_burden <= 0.255:
        return "mid"
    return "high"


def thermal_stress(total_laps: int, track_temp: int) -> float:
    """Build a context feature from existing columns instead of inventing one.

    Historical winners show a U-shaped relation with temperature: both cool and
    hot races produce more multi-stop winners than the middle. Modeling that
    shape starts with "distance from the thermal middle" rather than raw heat.
    """

    return total_laps * abs(track_temp - 30.0)


def extract_winner_patterns(races: list[HistoricalRace]) -> list[WinnerPattern]:
    """Reduce each race to the winning strategy features we can actually observe."""

    patterns = []
    for race in races:
        winner_id = race.actual_order[0]
        winner_plan = next(
            driver_plan
            for driver_plan in race.driver_plans
            if driver_plan.driver_id == winner_id
        )
        first_stint = winner_plan.stints[0]
        patterns.append(
            WinnerPattern(
                start_tire=winner_plan.starting_tire,
                stops=winner_plan.stop_count,
                first_stint_laps=first_stint.length,
                first_stint_fraction=first_stint.length / race.config.total_laps,
                sequence="->".join(stint.compound for stint in winner_plan.stints),
                total_laps=race.config.total_laps,
                track_temp=race.config.track_temp,
                pit_burden=race.config.pit_lane_time / race.config.base_lap_time,
                thermal_stress=thermal_stress(
                    total_laps=race.config.total_laps,
                    track_temp=race.config.track_temp,
                ),
            )
        )
    return patterns


def summarize_winner_patterns(
    patterns: list[WinnerPattern],
    bucket_fn,
    value_fn,
) -> dict[str, BucketSummary]:
    """Group winning strategies by a data-derived race context bucket."""

    grouped: dict[str, list[WinnerPattern]] = defaultdict(list)
    for pattern in patterns:
        grouped[bucket_fn(value_fn(pattern))].append(pattern)

    summaries = {}
    for bucket, bucket_patterns in grouped.items():
        race_count = len(bucket_patterns)
        start_tires = Counter(pattern.start_tire for pattern in bucket_patterns)
        summaries[bucket] = BucketSummary(
            race_count=race_count,
            two_stop_rate=sum(pattern.stops == 2 for pattern in bucket_patterns)
            / race_count,
            start_tire_distribution={
                tire: count / race_count
                for tire, count in start_tires.items()
            },
            average_first_stint_fraction=sum(
                pattern.first_stint_fraction for pattern in bucket_patterns
            )
            / race_count,
            top_sequences=Counter(
                pattern.sequence for pattern in bucket_patterns
            ).most_common(5),
        )
    return dict(summaries)


def summarize_start_band_usage(
    races: list[HistoricalRace],
) -> dict[str, dict[str, object]]:
    """Measure whether the generator changes strategy mix by starting band.

    Real F1 often gives back markers latitude to extend the first stint, but we
    should only import that intuition if the historical data supports it here.
    """

    start_tires = {band: Counter() for band in START_BANDS}
    first_stints = {band: [] for band in START_BANDS}

    for race in races:
        for position, driver_plan in enumerate(race.driver_plans, start=1):
            band = next(
                band_name
                for band_name, positions in START_BANDS.items()
                if position in positions
            )
            start_tires[band][driver_plan.starting_tire] += 1
            first_stints[band].append(driver_plan.stints[0].length)

    return {
        band: {
            "avg_first_stint": sum(first_stints[band]) / len(first_stints[band]),
            "start_tires": dict(start_tires[band]),
        }
        for band in START_BANDS
    }


def strategy_signature(driver_plan: DriverPlan) -> str:
    return "|".join(
        f"{stint.compound}:{stint.length}"
        for stint in driver_plan.stints
    )


def compare_case_payload(
    case_name: str,
    payload: dict,
    expected_order: list[str],
) -> CaseComparison:
    race_input = parse_race_input(payload)
    predicted_order = predict_finishing_order(
        config=race_input.config,
        driver_plans=race_input.driver_plans,
    )
    plan_by_driver = {
        driver_plan.driver_id: driver_plan for driver_plan in race_input.driver_plans
    }
    divergence = first_divergence(predicted_order, expected_order)
    predicted_focus_signature = None
    expected_focus_signature = None
    if divergence is not None:
        _, predicted_driver, expected_driver = divergence
        predicted_focus_signature = strategy_signature(plan_by_driver[predicted_driver])
        expected_focus_signature = strategy_signature(plan_by_driver[expected_driver])

    return CaseComparison(
        case_name=case_name,
        exact_match=predicted_order == expected_order,
        first_divergence_position=None if divergence is None else divergence[0],
        first_divergence_predicted_signature=predicted_focus_signature,
        first_divergence_expected_signature=expected_focus_signature,
        winner_changed=predicted_order[0] != expected_order[0],
        predicted_winner_signature=strategy_signature(plan_by_driver[predicted_order[0]]),
        expected_winner_signature=strategy_signature(plan_by_driver[expected_order[0]]),
    )


def summarize_case_comparisons(
    comparisons: list[CaseComparison],
) -> SuiteSummary:
    first_divergence_counts: Counter = Counter()
    first_divergence_strategy_counts: Counter = Counter()
    winner_mismatch_counts: Counter = Counter()
    exact_matches = 0

    for comparison in comparisons:
        if comparison.exact_match:
            exact_matches += 1
            continue
        if comparison.first_divergence_position is not None:
            first_divergence_counts[comparison.first_divergence_position] += 1
        if (
            comparison.first_divergence_predicted_signature is not None
            and comparison.first_divergence_expected_signature is not None
        ):
            first_divergence_strategy_counts[
                (
                    comparison.first_divergence_predicted_signature,
                    comparison.first_divergence_expected_signature,
                )
            ] += 1
        if comparison.winner_changed:
            winner_mismatch_counts[
                (
                    comparison.predicted_winner_signature,
                    comparison.expected_winner_signature,
                )
            ] += 1

    return SuiteSummary(
        case_count=len(comparisons),
        exact_matches=exact_matches,
        first_divergence_counts=first_divergence_counts,
        first_divergence_strategy_counts=first_divergence_strategy_counts,
        winner_mismatch_counts=winner_mismatch_counts,
    )


def compare_case_directories(
    inputs_dir: Path,
    expected_dir: Path,
) -> tuple[list[CaseComparison], SuiteSummary]:
    comparisons = []
    for input_path in sorted(inputs_dir.glob("test_*.json")):
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        expected_payload = json.loads(
            (expected_dir / input_path.name).read_text(encoding="utf-8")
        )
        comparisons.append(
            compare_case_payload(
                case_name=input_path.stem,
                payload=payload,
                expected_order=expected_payload["finishing_positions"],
            )
        )
    return comparisons, summarize_case_comparisons(comparisons)


def compare_historical_races(
    races: list[HistoricalRace],
) -> tuple[list[CaseComparison], SuiteSummary]:
    comparisons = []
    for race in races:
        payload = {
            "race_id": race.race_id,
            "race_config": {
                "track": race.config.track,
                "total_laps": race.config.total_laps,
                "base_lap_time": race.config.base_lap_time,
                "pit_lane_time": race.config.pit_lane_time,
                "track_temp": race.config.track_temp,
            },
            "strategies": {},
        }
        for index, driver_plan in enumerate(race.driver_plans, start=1):
            pit_stops = []
            for stint_index in range(len(driver_plan.stints) - 1):
                current_stint = driver_plan.stints[stint_index]
                next_stint = driver_plan.stints[stint_index + 1]
                pit_stops.append(
                    {
                        "lap": current_stint.end_lap,
                        "from_tire": current_stint.compound,
                        "to_tire": next_stint.compound,
                    }
                )
            payload["strategies"][f"pos{index}"] = {
                "driver_id": driver_plan.driver_id,
                "starting_tire": driver_plan.starting_tire,
                "pit_stops": pit_stops,
            }
        comparisons.append(
            compare_case_payload(
                case_name=race.race_id,
                payload=payload,
                expected_order=list(race.actual_order),
            )
        )
    return comparisons, summarize_case_comparisons(comparisons)

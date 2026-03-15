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
from .parameters import (
    RUNTIME_CONTEXT_ORDER,
    RUNTIME_MODEL_PARAMETERS,
    runtime_context_key,
    runtime_fallback_context_key,
    runtime_fallback_model_for_context_key,
)
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


@dataclass(frozen=True)
class BucketSummary:
    race_count: int
    two_stop_rate: float
    start_tire_distribution: dict[str, float]
    average_first_stint_fraction: float
    top_sequences: list[tuple[str, int]]


@dataclass(frozen=True)
class DriverResidual:
    strategy_family: str
    strategy_signature: str
    context_bucket: str
    actual_rank: int
    predicted_rank: int
    rank_error: int
    absolute_rank_error: int


@dataclass(frozen=True)
class ResidualGroupSummary:
    key: str
    sample_count: int
    average_rank_error: float
    average_absolute_rank_error: float
    top_signatures: list[tuple[str, int]]


@dataclass(frozen=True)
class PairwiseConfusionSummary:
    predicted_ahead_family: str
    actual_ahead_family: str
    context_bucket: str
    mismatch_count: int


@dataclass(frozen=True)
class HistoricalResidualSummary:
    family_overrated: list[ResidualGroupSummary]
    family_underrated: list[ResidualGroupSummary]
    family_context_overrated: list[ResidualGroupSummary]
    family_context_underrated: list[ResidualGroupSummary]
    pairwise_confusions: list[PairwiseConfusionSummary]


@dataclass(frozen=True)
class RuntimeBucketValueSummary:
    context_key: str
    fallback_context_key: str
    race_count: int
    exact_matches: int
    fallback_exact_matches: int
    pairwise_rate: float
    fallback_pairwise_rate: float

    @property
    def exact_gain(self) -> int:
        return self.exact_matches - self.fallback_exact_matches

    @property
    def pairwise_gain(self) -> float:
        return self.pairwise_rate - self.fallback_pairwise_rate


@dataclass(frozen=True)
class StrategyCrossoverSummary:
    left_family: str
    right_family: str
    context_key: str
    left_wins: int
    right_wins: int

    @property
    def total(self) -> int:
        return self.left_wins + self.right_wins

    @property
    def winner(self) -> str:
        return self.left_family if self.left_wins >= self.right_wins else self.right_family

    @property
    def winner_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return max(self.left_wins, self.right_wins) / self.total


DEFAULT_CROSSOVER_FAMILY_PAIRS = (
    ("SOFT->HARD / 1 stop", "HARD->SOFT / 1 stop"),
    ("MEDIUM->HARD / 1 stop", "HARD->MEDIUM / 1 stop"),
    ("SOFT->MEDIUM / 1 stop", "MEDIUM->SOFT / 1 stop"),
)


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


def strategy_family(driver_plan: DriverPlan) -> str:
    sequence = "->".join(stint.compound for stint in driver_plan.stints)
    stop_label = "stop" if driver_plan.stop_count == 1 else "stops"
    return f"{sequence} / {driver_plan.stop_count} {stop_label}"


def historical_context_bucket(race: HistoricalRace) -> str:
    pit_burden = race.config.pit_lane_time / race.config.base_lap_time
    return (
        f"{laps_bucket(race.config.total_laps)}|"
        f"{temp_bucket(race.config.track_temp)}|"
        f"{pit_burden_bucket(pit_burden)}"
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


def evaluate_races_with_model(
    races: list[HistoricalRace],
    model,
) -> tuple[int, float]:
    """Score a list of races with one model and return exact/pairwise totals.

    This helper exists for gate auditing: we want to ask whether a specialized
    child bucket actually beats the simpler model it would fall back to.
    """

    exact_matches = 0
    pairwise_correct = 0

    for race in races:
        predicted_order = predict_finishing_order(
            config=race.config,
            driver_plans=race.driver_plans,
            model=model,
        )
        if tuple(predicted_order) == race.actual_order:
            exact_matches += 1

        predicted_rank = {
            driver_id: index
            for index, driver_id in enumerate(predicted_order)
        }
        for index, left_driver in enumerate(race.actual_order):
            for right_driver in race.actual_order[index + 1 :]:
                if predicted_rank[left_driver] < predicted_rank[right_driver]:
                    pairwise_correct += 1

    pairwise_total = len(races) * 190
    pairwise_rate = 0.0 if pairwise_total == 0 else pairwise_correct / pairwise_total
    return exact_matches, pairwise_rate


def summarize_runtime_bucket_value(
    races: list[HistoricalRace],
) -> list[RuntimeBucketValueSummary]:
    """Measure which child buckets actually earn their complexity.

    Each summary compares the current specialized bucket to the less-specialized
    fallback that would take over if we deleted that child from the gate.
    """

    summaries: list[RuntimeBucketValueSummary] = []
    grouped_races = {context_key: [] for context_key in RUNTIME_CONTEXT_ORDER}
    for race in races:
        grouped_races[runtime_context_key(race.config)].append(race)

    for context_key in RUNTIME_CONTEXT_ORDER:
        context_races = grouped_races[context_key]
        if not context_races:
            continue
        exact_matches, pairwise_rate = evaluate_races_with_model(
            context_races,
            RUNTIME_MODEL_PARAMETERS[context_key],
        )
        fallback_context_key = runtime_fallback_context_key(context_key)
        fallback_exact_matches, fallback_pairwise_rate = evaluate_races_with_model(
            context_races,
            runtime_fallback_model_for_context_key(context_key),
        )
        summaries.append(
            RuntimeBucketValueSummary(
                context_key=context_key,
                fallback_context_key=fallback_context_key,
                race_count=len(context_races),
                exact_matches=exact_matches,
                fallback_exact_matches=fallback_exact_matches,
                pairwise_rate=pairwise_rate,
                fallback_pairwise_rate=fallback_pairwise_rate,
            )
        )

    return sorted(
        summaries,
        key=lambda summary: (
            -summary.exact_gain,
            -summary.pairwise_gain,
            -summary.race_count,
        ),
    )


def extract_driver_residuals(
    races: list[HistoricalRace],
) -> list[DriverResidual]:
    residuals: list[DriverResidual] = []
    for race in races:
        predicted_order = predict_finishing_order(
            config=race.config,
            driver_plans=race.driver_plans,
        )
        predicted_rank = {
            driver_id: index + 1
            for index, driver_id in enumerate(predicted_order)
        }
        actual_rank = {
            driver_id: index + 1
            for index, driver_id in enumerate(race.actual_order)
        }
        plan_by_driver = {
            driver_plan.driver_id: driver_plan for driver_plan in race.driver_plans
        }
        context_bucket = historical_context_bucket(race)

        for driver_id, plan in plan_by_driver.items():
            rank_error = predicted_rank[driver_id] - actual_rank[driver_id]
            residuals.append(
                DriverResidual(
                    strategy_family=strategy_family(plan),
                    strategy_signature=strategy_signature(plan),
                    context_bucket=context_bucket,
                    actual_rank=actual_rank[driver_id],
                    predicted_rank=predicted_rank[driver_id],
                    rank_error=rank_error,
                    absolute_rank_error=abs(rank_error),
                )
            )

    return residuals


def summarize_strategy_crossovers(
    races: list[HistoricalRace],
    family_pairs: tuple[tuple[str, str], ...] = DEFAULT_CROSSOVER_FAMILY_PAIRS,
    min_total: int = 20,
) -> list[StrategyCrossoverSummary]:
    """Summarize where mirrored one-stop families actually flip in history.

    The best remaining modeling signal is often not a raw residual, but the
    context where one strategy family overtakes its mirror. We measure that per
    runtime bucket so the next gate refinement can be tied to an actual flip.
    """

    summaries: list[StrategyCrossoverSummary] = []

    for left_family, right_family in family_pairs:
        wins_by_context: dict[str, Counter[str]] = defaultdict(Counter)

        for race in races:
            family_to_driver_ids: dict[str, list[str]] = defaultdict(list)
            for driver_plan in race.driver_plans:
                family_to_driver_ids[strategy_family(driver_plan)].append(driver_plan.driver_id)

            if not family_to_driver_ids[left_family] or not family_to_driver_ids[right_family]:
                continue

            actual_rank = {
                driver_id: index
                for index, driver_id in enumerate(race.actual_order)
            }
            left_best_rank = min(actual_rank[driver_id] for driver_id in family_to_driver_ids[left_family])
            right_best_rank = min(actual_rank[driver_id] for driver_id in family_to_driver_ids[right_family])
            context_key = runtime_context_key(race.config)

            if left_best_rank < right_best_rank:
                wins_by_context[context_key][left_family] += 1
            else:
                wins_by_context[context_key][right_family] += 1

        for context_key, counts in wins_by_context.items():
            left_wins = counts[left_family]
            right_wins = counts[right_family]
            if left_wins + right_wins < min_total:
                continue
            summaries.append(
                StrategyCrossoverSummary(
                    left_family=left_family,
                    right_family=right_family,
                    context_key=context_key,
                    left_wins=left_wins,
                    right_wins=right_wins,
                )
            )

    return sorted(
        summaries,
        key=lambda summary: (-summary.total, summary.context_key, summary.left_family),
    )


def summarize_residual_groups(
    residuals: list[DriverResidual],
    key_fn,
    min_samples: int,
) -> list[ResidualGroupSummary]:
    grouped_errors: dict[str, list[int]] = defaultdict(list)
    grouped_abs_errors: dict[str, list[int]] = defaultdict(list)
    grouped_signatures: dict[str, Counter] = defaultdict(Counter)

    for residual in residuals:
        key = key_fn(residual)
        grouped_errors[key].append(residual.rank_error)
        grouped_abs_errors[key].append(residual.absolute_rank_error)
        grouped_signatures[key][residual.strategy_signature] += 1

    summaries = []
    for key, rank_errors in grouped_errors.items():
        sample_count = len(rank_errors)
        if sample_count < min_samples:
            continue
        summaries.append(
            ResidualGroupSummary(
                key=key,
                sample_count=sample_count,
                average_rank_error=sum(rank_errors) / sample_count,
                average_absolute_rank_error=(
                    sum(grouped_abs_errors[key]) / sample_count
                ),
                top_signatures=grouped_signatures[key].most_common(3),
            )
        )

    return summaries


def summarize_pairwise_confusions(
    races: list[HistoricalRace],
    top: int,
) -> list[PairwiseConfusionSummary]:
    confusion_counts: Counter = Counter()

    for race in races:
        predicted_order = predict_finishing_order(
            config=race.config,
            driver_plans=race.driver_plans,
        )
        predicted_rank = {
            driver_id: index
            for index, driver_id in enumerate(predicted_order)
        }
        plan_by_driver = {
            driver_plan.driver_id: driver_plan for driver_plan in race.driver_plans
        }
        context_bucket = historical_context_bucket(race)

        for index, actual_ahead in enumerate(race.actual_order):
            for actual_behind in race.actual_order[index + 1 :]:
                if predicted_rank[actual_ahead] < predicted_rank[actual_behind]:
                    continue
                confusion_counts[
                    (
                        strategy_family(plan_by_driver[actual_behind]),
                        strategy_family(plan_by_driver[actual_ahead]),
                        context_bucket,
                    )
                ] += 1

    return [
        PairwiseConfusionSummary(
            predicted_ahead_family=predicted_ahead,
            actual_ahead_family=actual_ahead,
            context_bucket=context_bucket,
            mismatch_count=count,
        )
        for (predicted_ahead, actual_ahead, context_bucket), count in confusion_counts.most_common(top)
    ]


def summarize_historical_residuals(
    races: list[HistoricalRace],
    top: int = 10,
    min_samples: int = 50,
) -> HistoricalResidualSummary:
    residuals = extract_driver_residuals(races)
    family_summaries = summarize_residual_groups(
        residuals,
        key_fn=lambda residual: residual.strategy_family,
        min_samples=min_samples,
    )
    family_context_summaries = summarize_residual_groups(
        residuals,
        key_fn=lambda residual: (
            f"{residual.context_bucket}|{residual.strategy_family}"
        ),
        min_samples=min_samples,
    )

    family_overrated = sorted(
        [summary for summary in family_summaries if summary.average_rank_error < 0],
        key=lambda summary: (
            summary.average_rank_error,
            -summary.average_absolute_rank_error,
            -summary.sample_count,
        ),
    )[:top]
    family_underrated = sorted(
        [summary for summary in family_summaries if summary.average_rank_error > 0],
        key=lambda summary: (
            -summary.average_rank_error,
            -summary.average_absolute_rank_error,
            -summary.sample_count,
        ),
    )[:top]
    family_context_overrated = sorted(
        [
            summary
            for summary in family_context_summaries
            if summary.average_rank_error < 0
        ],
        key=lambda summary: (
            summary.average_rank_error,
            -summary.average_absolute_rank_error,
            -summary.sample_count,
        ),
    )[:top]
    family_context_underrated = sorted(
        [
            summary
            for summary in family_context_summaries
            if summary.average_rank_error > 0
        ],
        key=lambda summary: (
            -summary.average_rank_error,
            -summary.average_absolute_rank_error,
            -summary.sample_count,
        ),
    )[:top]

    return HistoricalResidualSummary(
        family_overrated=family_overrated,
        family_underrated=family_underrated,
        family_context_overrated=family_context_overrated,
        family_context_underrated=family_context_underrated,
        pairwise_confusions=summarize_pairwise_confusions(races, top=top),
    )

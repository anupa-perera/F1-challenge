from __future__ import annotations

"""Feature extraction for hybrid ranking experiments.

The deterministic scorer is already a strong summary of tire strategy quality.
This module turns that scorer plus raw plan/context structure into reusable
numeric features for any learned layer we test on top.
"""

from dataclasses import dataclass

from .models import COMPOUND_ORDER, DriverPlan, DriverScoreBreakdown, RaceConfig
from .runtime_gate import RUNTIME_CONTEXT_ORDER, pit_burden, runtime_context_key, runtime_model_for_config
from .scoring import driver_score_breakdown, one_stop_arc_key, two_stop_loop_key


ONE_STOP_ARC_KEYS = (
    "SOFT->MEDIUM",
    "SOFT->HARD",
    "MEDIUM->SOFT",
    "MEDIUM->HARD",
    "HARD->SOFT",
    "HARD->MEDIUM",
)

TWO_STOP_LOOP_KEYS = (
    "SOFT->MEDIUM->SOFT",
    "SOFT->HARD->SOFT",
    "MEDIUM->SOFT->MEDIUM",
    "MEDIUM->HARD->MEDIUM",
    "HARD->SOFT->HARD",
    "HARD->MEDIUM->HARD",
)

FEATURE_NAMES = (
    "strategy_cost",
    "tire_penalty_time",
    "pit_stop_time",
    "additional_stop_time",
    "hard_loop_penalty_time",
    "one_stop_arc_time",
    "two_stop_loop_time",
    "opening_commitment_time",
    "stop_count",
    "is_one_stop",
    "is_two_stop",
    "total_laps_norm",
    "track_temp_norm",
    "base_lap_time_norm",
    "pit_burden_norm",
    "first_stint_fraction",
    "second_stint_fraction",
    "third_stint_fraction",
    "soft_lap_fraction",
    "medium_lap_fraction",
    "hard_lap_fraction",
    "soft_wear_total",
    "medium_wear_total",
    "hard_wear_total",
    "soft_pace_total",
    "medium_pace_total",
    "hard_pace_total",
    "starts_soft",
    "starts_medium",
    "starts_hard",
    "ends_soft",
    "ends_medium",
    "ends_hard",
    "has_soft",
    "has_medium",
    "has_hard",
    "context_short_non_medium",
    "context_short_warm",
    "context_short_cool_mild",
    "context_medium_high_pit",
    "context_medium_high_pit_cool",
    "context_medium_high_pit_hot",
    "context_medium_cool_slow_cool",
    "context_long_non_medium",
    "arc_soft_to_medium",
    "arc_soft_to_hard",
    "arc_medium_to_soft",
    "arc_medium_to_hard",
    "arc_hard_to_soft",
    "arc_hard_to_medium",
    "loop_soft_to_medium_to_soft",
    "loop_soft_to_hard_to_soft",
    "loop_medium_to_soft_to_medium",
    "loop_medium_to_hard_to_medium",
    "loop_hard_to_soft_to_hard",
    "loop_hard_to_medium_to_hard",
    "stint_balance_ratio",
    "pit_lap_normalized",
    "grace_usage_fraction",
)


@dataclass(frozen=True)
class DriverHybridFeatures:
    driver_id: str
    strategy_cost: float
    vector: tuple[float, ...]


def _context_feature_values(config: RaceConfig) -> tuple[float, float, float, float]:
    return (
        (config.total_laps - 45.0) / 10.0,
        (config.track_temp - 30.0) / 12.0,
        (config.base_lap_time - 87.0) / 7.0,
        (pit_burden(config) - 0.25) / 0.03,
    )


def _stint_fraction(driver_plan: DriverPlan, index: int, total_laps: int) -> float:
    if index >= len(driver_plan.stints):
        return 0.0
    return driver_plan.stints[index].length / total_laps


def _compound_lap_fractions(driver_plan: DriverPlan, total_laps: int) -> tuple[float, float, float]:
    laps_by_compound = {compound: 0.0 for compound in COMPOUND_ORDER}
    for stint in driver_plan.stints:
        laps_by_compound[stint.compound] += stint.length
    return tuple(laps_by_compound[compound] / total_laps for compound in COMPOUND_ORDER)


def _compound_penalty_totals(
    breakdown: DriverScoreBreakdown,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    pace_by_compound = {compound: 0.0 for compound in COMPOUND_ORDER}
    wear_by_compound = {compound: 0.0 for compound in COMPOUND_ORDER}
    for stint in breakdown.stints:
        pace_by_compound[stint.compound] += stint.pace_total
        wear_by_compound[stint.compound] += stint.wear_total
    return tuple(
        (wear_by_compound[compound], pace_by_compound[compound])
        for compound in COMPOUND_ORDER
    )


def extract_driver_features(
    config: RaceConfig,
    driver_plan: DriverPlan,
    breakdown: DriverScoreBreakdown | None = None,
) -> DriverHybridFeatures:
    resolved_breakdown = (
        driver_score_breakdown(config=config, driver_plan=driver_plan)
        if breakdown is None
        else breakdown
    )
    total_laps_norm, track_temp_norm, base_lap_time_norm, pit_burden_norm = (
        _context_feature_values(config)
    )
    soft_lap_fraction, medium_lap_fraction, hard_lap_fraction = _compound_lap_fractions(
        driver_plan,
        config.total_laps,
    )
    compound_penalties = _compound_penalty_totals(resolved_breakdown)
    context_key = runtime_context_key(config)
    one_stop_key = one_stop_arc_key(driver_plan)
    loop_key = two_stop_loop_key(driver_plan)
    start_compound = driver_plan.stints[0].compound
    end_compound = driver_plan.stints[-1].compound
    compounds_used = {stint.compound for stint in driver_plan.stints}
    strategy_cost = resolved_breakdown.total_time - resolved_breakdown.base_race_time

    # Stint balance ratio: how asymmetric are the stints?
    # For one-stop: first_stint / second_stint. For others: 0.0
    if len(driver_plan.stints) == 2:
        second_len = driver_plan.stints[1].length
        stint_balance_ratio = (driver_plan.stints[0].length / second_len) if second_len > 0 else 0.0
    else:
        stint_balance_ratio = 0.0

    # Pit lap normalized: when does the first pit stop happen relative to race length?
    if driver_plan.stop_count >= 1 and len(driver_plan.stints) >= 2:
        pit_lap_normalized = driver_plan.stints[0].length / config.total_laps
    else:
        pit_lap_normalized = 0.0

    # Grace usage fraction: how much of the dominant compound's grace window is used?
    resolved_model = runtime_model_for_config(config)
    longest_stint = max(driver_plan.stints, key=lambda s: s.length)
    grace = resolved_model.compounds[longest_stint.compound].grace_laps
    grace_usage_fraction = longest_stint.length / grace if grace > 0 else 0.0

    vector = (
        strategy_cost,
        resolved_breakdown.tire_penalty_time,
        resolved_breakdown.pit_stop_time,
        resolved_breakdown.additional_stop_time,
        resolved_breakdown.hard_loop_penalty_time,
        resolved_breakdown.one_stop_arc_time,
        resolved_breakdown.two_stop_loop_time,
        resolved_breakdown.opening_commitment_time,
        float(driver_plan.stop_count),
        1.0 if driver_plan.stop_count == 1 else 0.0,
        1.0 if driver_plan.stop_count == 2 else 0.0,
        total_laps_norm,
        track_temp_norm,
        base_lap_time_norm,
        pit_burden_norm,
        _stint_fraction(driver_plan, 0, config.total_laps),
        _stint_fraction(driver_plan, 1, config.total_laps),
        _stint_fraction(driver_plan, 2, config.total_laps),
        soft_lap_fraction,
        medium_lap_fraction,
        hard_lap_fraction,
        compound_penalties[0][0],
        compound_penalties[1][0],
        compound_penalties[2][0],
        compound_penalties[0][1],
        compound_penalties[1][1],
        compound_penalties[2][1],
        1.0 if start_compound == "SOFT" else 0.0,
        1.0 if start_compound == "MEDIUM" else 0.0,
        1.0 if start_compound == "HARD" else 0.0,
        1.0 if end_compound == "SOFT" else 0.0,
        1.0 if end_compound == "MEDIUM" else 0.0,
        1.0 if end_compound == "HARD" else 0.0,
        1.0 if "SOFT" in compounds_used else 0.0,
        1.0 if "MEDIUM" in compounds_used else 0.0,
        1.0 if "HARD" in compounds_used else 0.0,
        *(1.0 if context_key == key else 0.0 for key in RUNTIME_CONTEXT_ORDER),
        *(1.0 if one_stop_key == key else 0.0 for key in ONE_STOP_ARC_KEYS),
        *(1.0 if loop_key == key else 0.0 for key in TWO_STOP_LOOP_KEYS),
        stint_balance_ratio,
        pit_lap_normalized,
        grace_usage_fraction,
    )

    return DriverHybridFeatures(
        driver_id=driver_plan.driver_id,
        strategy_cost=strategy_cost,
        vector=tuple(float(value) for value in vector),
    )


def extract_race_feature_rows(
    config: RaceConfig,
    driver_plans: tuple[DriverPlan, ...],
) -> tuple[DriverHybridFeatures, ...]:
    breakdowns = [
        driver_score_breakdown(config=config, driver_plan=driver_plan)
        for driver_plan in driver_plans
    ]
    return tuple(
        extract_driver_features(
            config=config,
            driver_plan=driver_plan,
            breakdown=breakdown,
        )
        for driver_plan, breakdown in zip(driver_plans, breakdowns)
    )

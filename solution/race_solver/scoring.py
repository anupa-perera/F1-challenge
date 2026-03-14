from __future__ import annotations

"""Score race strategies using the current deterministic tire model."""

from typing import Sequence

from .models import (
    DriverPlan,
    DriverScoreBreakdown,
    ModelParameters,
    RaceConfig,
    Stint,
    StintScoreBreakdown,
)
from .parameters import DEFAULT_MODEL_PARAMETERS


def normalize_context(config: RaceConfig) -> tuple[float, float]:
    """Map race context onto compact scales used by the scoring model.

    The current model ignores the track name and uses the numeric race fields
    directly, because those are the values that change lap cost. Historical
    analysis also showed that total race length explains winning strategy shape
    much better than base lap time, so the second context axis follows
    `total_laps` rather than nominal one-lap pace.
    """

    temp_norm = (config.track_temp - 30.0) / 12.0
    race_length_norm = (config.total_laps - 45.0) / 10.0
    return temp_norm, race_length_norm


def compound_multipliers(
    config: RaceConfig,
    model: ModelParameters,
    compound: str,
) -> tuple[float, float]:
    params = model.compounds[compound]
    temp_norm, race_length_norm = normalize_context(config)

    pace_multiplier = 1.0
    pace_multiplier += params.temp_pace_scale * temp_norm

    # Tire wear is driven by heat and by how demanding the overall race is on
    # strategy length. We keep the same calibrated scalars, but combine them
    # multiplicatively so "hot and long" races can express more wear pressure
    # than a purely additive model without inventing extra parameters.
    deg_multiplier = 1.0 + (params.temp_deg_scale * temp_norm)
    deg_multiplier *= 1.0 + (params.race_length_deg_scale * race_length_norm)

    return pace_multiplier, deg_multiplier


def sequence_order_emphasis(config: RaceConfig) -> float:
    """Increase order sensitivity for short races with a small taper.

    Historical pairwise comparisons of mirrored one-stop strategies show that
    compound order matters most in short races and is close to neutral in
    longer ones. The effect does not disappear at a hard boundary, though: it
    is strongest around 34 laps and fades toward neutral by about 39 laps, so
    we reuse the existing lap-progress term with a fixed taper instead of
    adding another tunable parameter.
    """

    if config.total_laps <= 34:
        return 1.0
    if config.total_laps >= 39:
        return 0.0
    return (39.0 - config.total_laps) / 5.0


def lap_progress_value(lap_number: int, total_laps: int) -> float:
    """Return a centered lap-progress value in the range roughly [-1, 1].

    Without some notion of race progression, a strategy like SOFT->HARD would
    always tie HARD->SOFT if the stint lengths matched. Historical races do not
    behave that way, so the v2 model lets compound pace matter differently
    depending on whether the stint happens early or late in the race.
    """

    return ((2 * lap_number) - total_laps - 1) / total_laps


def stint_progress_sum(stint: Stint, total_laps: int) -> float:
    """Sum the centered lap-progress term across a stint."""

    lap_sum = (stint.start_lap + stint.end_lap) * stint.length / 2.0
    return ((2.0 * lap_sum) - (stint.length * (total_laps + 1))) / total_laps


def lap_penalty(
    compound: str,
    age: int,
    lap_number: int,
    config: RaceConfig,
    model: ModelParameters = DEFAULT_MODEL_PARAMETERS,
) -> float:
    params = model.compounds[compound]
    pace_multiplier, deg_multiplier = compound_multipliers(config, model, compound)
    progress_multiplier = 1.0 + (
        model.lap_progress_pace_scale
        * sequence_order_emphasis(config)
        * lap_progress_value(lap_number=lap_number, total_laps=config.total_laps)
    )

    pace_term = params.pace_offset * pace_multiplier * progress_multiplier
    wear_term = max(0, age - params.grace_laps) * params.deg_rate * deg_multiplier
    return pace_term + wear_term


def stint_penalty_total(
    stint: Stint,
    config: RaceConfig,
    model: ModelParameters = DEFAULT_MODEL_PARAMETERS,
) -> float:
    """Collapse the lap-by-lap penalty sum for a stint into a closed form."""

    params = model.compounds[stint.compound]
    pace_multiplier, deg_multiplier = compound_multipliers(
        config=config,
        model=model,
        compound=stint.compound,
    )

    # The race score is additive across laps, so we can compute the same total
    # without iterating over every lap of every driver on every search step.
    base_pace_total = stint.length * params.pace_offset * pace_multiplier
    progress_adjustment_total = (
        params.pace_offset
        * pace_multiplier
        * model.lap_progress_pace_scale
        * sequence_order_emphasis(config)
        * stint_progress_sum(stint=stint, total_laps=config.total_laps)
    )
    pace_total = base_pace_total + progress_adjustment_total
    overage_laps = max(0, stint.length - params.grace_laps)
    wear_units = overage_laps * (overage_laps + 1) / 2.0
    wear_total = wear_units * params.deg_rate * deg_multiplier
    return pace_total + wear_total


def stint_score_breakdown(
    stint: Stint,
    config: RaceConfig,
    model: ModelParameters = DEFAULT_MODEL_PARAMETERS,
) -> StintScoreBreakdown:
    """Explain how one stint contributes to the final race score."""

    params = model.compounds[stint.compound]
    pace_multiplier, deg_multiplier = compound_multipliers(
        config=config,
        model=model,
        compound=stint.compound,
    )

    base_pace_total = stint.length * params.pace_offset * pace_multiplier
    progress_adjustment_total = (
        params.pace_offset
        * pace_multiplier
        * model.lap_progress_pace_scale
        * sequence_order_emphasis(config)
        * stint_progress_sum(stint=stint, total_laps=config.total_laps)
    )
    pace_total = base_pace_total + progress_adjustment_total
    overage_laps = max(0, stint.length - params.grace_laps)
    wear_units = overage_laps * (overage_laps + 1) / 2.0
    wear_total = wear_units * params.deg_rate * deg_multiplier

    return StintScoreBreakdown(
        compound=stint.compound,
        start_lap=stint.start_lap,
        end_lap=stint.end_lap,
        length=stint.length,
        base_pace_total=base_pace_total,
        progress_adjustment_total=progress_adjustment_total,
        pace_total=pace_total,
        wear_total=wear_total,
        total_penalty=pace_total + wear_total,
    )


def driver_score_breakdown(
    config: RaceConfig,
    driver_plan: DriverPlan,
    model: ModelParameters = DEFAULT_MODEL_PARAMETERS,
) -> DriverScoreBreakdown:
    """Return the full score decomposition for a single driver."""

    base_race_time = config.base_lap_time * config.total_laps
    pit_stop_time = config.pit_lane_time * driver_plan.stop_count
    stints = tuple(
        stint_score_breakdown(stint=stint, config=config, model=model)
        for stint in driver_plan.stints
    )
    tire_penalty_time = sum(stint.total_penalty for stint in stints)

    return DriverScoreBreakdown(
        driver_id=driver_plan.driver_id,
        base_race_time=base_race_time,
        pit_stop_time=pit_stop_time,
        tire_penalty_time=tire_penalty_time,
        total_time=base_race_time + pit_stop_time + tire_penalty_time,
        stints=stints,
    )


def driver_total_time(
    config: RaceConfig,
    driver_plan: DriverPlan,
    model: ModelParameters = DEFAULT_MODEL_PARAMETERS,
) -> float:
    """Return total race time without constructing explanation objects.

    Calibration evaluates thousands of candidate models across many races, so
    the hot path should add times directly. The richer breakdown path stays
    available for debugging tools, but prediction only needs this scalar total.
    """

    base_race_time = config.base_lap_time * config.total_laps
    pit_stop_time = config.pit_lane_time * driver_plan.stop_count
    tire_penalty_time = sum(
        stint_penalty_total(stint=stint, config=config, model=model)
        for stint in driver_plan.stints
    )
    return base_race_time + pit_stop_time + tire_penalty_time


def predict_finishing_order(
    config: RaceConfig,
    driver_plans: Sequence[DriverPlan],
    model: ModelParameters = DEFAULT_MODEL_PARAMETERS,
) -> list[str]:
    scored_drivers = [
        (
            driver_total_time(config=config, driver_plan=driver_plan, model=model),
            driver_plan.driver_id,
        )
        for driver_plan in driver_plans
    ]

    # Historical races show that identical strategies still need a stable final
    # ordering, and lower driver_id is the deterministic tiebreak.
    scored_drivers.sort(key=lambda item: (item[0], item[1]))
    return [driver_id for _, driver_id in scored_drivers]

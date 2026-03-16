from __future__ import annotations

"""Score race strategies using the current deterministic tire model."""

from dataclasses import dataclass
from typing import Sequence

from .models import (
    DriverPlan,
    DriverScoreBreakdown,
    ModelParameters,
    RaceConfig,
    Stint,
    StintScoreBreakdown,
)
from .runtime_gate import runtime_model_for_config


COMPOUND_RANK = {
    "SOFT": 0,
    "MEDIUM": 1,
    "HARD": 2,
}


@dataclass(frozen=True)
class _StintPenaltyComponents:
    base_pace_total: float
    progress_adjustment_total: float
    opening_bias_total: float
    wear_total: float

    @property
    def pace_total(self) -> float:
        return (
            self.base_pace_total
            + self.progress_adjustment_total
            + self.opening_bias_total
        )

    @property
    def total_penalty(self) -> float:
        return self.pace_total + self.wear_total


def _resolve_model(
    config: RaceConfig,
    model: ModelParameters | None,
) -> ModelParameters:
    return runtime_model_for_config(config) if model is None else model


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
    behave that way, so the scorer lets compound pace matter differently
    depending on whether the stint happens early or late in the race.
    """

    return ((2 * lap_number) - total_laps - 1) / total_laps


def stint_progress_sum(stint: Stint, total_laps: int) -> float:
    """Sum the centered lap-progress term across a stint."""

    lap_sum = (stint.start_lap + stint.end_lap) * stint.length / 2.0
    return ((2.0 * lap_sum) - (stint.length * (total_laps + 1))) / total_laps


def is_post_stop_stint(*, start_lap: int) -> bool:
    """Return whether a stint starts after a pit stop rather than on lap one."""

    return start_lap > 1


def is_medium_one_stop_opening_stint(
    config: RaceConfig,
    driver_plan: DriverPlan,
    stint: Stint,
) -> bool:
    """Return whether a one-stop medium opener should pay the commitment cost."""

    return (
        stint.start_lap == 1
        and stint.compound == "MEDIUM"
        and driver_plan.stop_count == 1
        and 37 <= config.total_laps <= 52
    )


def is_extreme_temperature(config: RaceConfig) -> bool:
    """Return whether the race sits in the historically difficult temp tails."""

    return config.track_temp <= 24 or config.track_temp >= 37


def is_hard_loop_two_stop_plan(driver_plan: DriverPlan) -> bool:
    """Return whether a plan starts and ends on HARD across two pit stops."""

    return (
        driver_plan.stop_count == 2
        and len(driver_plan.stints) == 3
        and driver_plan.stints[0].compound == "HARD"
        and driver_plan.stints[-1].compound == "HARD"
    )


def is_short_cool_race(config: RaceConfig) -> bool:
    """Return whether the race sits in the one strong hard-first exception."""

    return config.total_laps <= 36 and config.track_temp <= 24


def is_hard_to_softer_one_stop_plan(driver_plan: DriverPlan) -> bool:
    """Return whether a one-stop plan starts on HARD and closes on a softer tire."""

    if driver_plan.stop_count != 1 or len(driver_plan.stints) != 2:
        return False
    first_compound = driver_plan.stints[0].compound
    second_compound = driver_plan.stints[1].compound
    if first_compound != "HARD":
        return False
    return COMPOUND_RANK[second_compound] < COMPOUND_RANK[first_compound]


def restart_opening_profile(compound: str) -> tuple[float, ...]:
    """Return the fixed restart opening shape for each compound.

    The live model already learned that restarted stints should not receive a
    long generic "fresh tire" boost. The next structural refinement is to make
    that short opening shape compound-aware:

    - SOFT gets the quickest benefit, but only for a very short window.
    - MEDIUM keeps the current two-lap shape.
    - HARD warms up more slowly, so its restart penalty lasts slightly longer.

    This keeps one global restart scale while letting the scorer distinguish
    late-race durable restarts from fast-closing soft stints.
    """

    if compound == "SOFT":
        return (0.75, 0.25)
    if compound == "HARD":
        return (1.0, 0.75, 0.5)
    return (1.0, 0.5)


def opening_bias_units(compound: str, age: int) -> float:
    """Return one lap of the fixed restart opening profile."""

    profile = restart_opening_profile(compound)
    if age <= 0 or age > len(profile):
        return 0.0
    return profile[age - 1]


def stint_opening_bias_units(compound: str, stint_length: int) -> float:
    """Closed-form sum of the compound-specific restart opening profile."""

    if stint_length <= 0:
        return 0.0
    profile = restart_opening_profile(compound)
    return float(sum(profile[:stint_length]))


def wear_overage(age: int, grace_laps: int) -> int:
    """Return how far a tire is past its stable operating window."""

    return max(0, age - grace_laps)


def wear_penalty_units(overage_laps: int) -> float:
    """Map degradation state to pace loss with a nonlinear response.

    The live scorer treats age overage as a degradation state and lets lap-time
    loss grow nonlinearly with that state. That keeps the fitted `deg_rate`
    surface small while still making long over-limit stints hurt much more than
    mild overage.
    """

    return float(overage_laps * overage_laps)


def stint_wear_penalty_units(stint_length: int, grace_laps: int) -> float:
    """Closed-form sum of squared overage terms across a stint."""

    overage_laps = max(0, stint_length - grace_laps)
    return overage_laps * (overage_laps + 1) * ((2 * overage_laps) + 1) / 6.0


def lap_penalty(
    compound: str,
    age: int,
    lap_number: int,
    config: RaceConfig,
    model: ModelParameters | None = None,
) -> float:
    resolved_model = _resolve_model(config, model)
    params = resolved_model.compounds[compound]
    pace_multiplier, deg_multiplier = compound_multipliers(config, resolved_model, compound)
    progress_multiplier = 1.0 + (
        resolved_model.lap_progress_pace_scale
        * sequence_order_emphasis(config)
        * lap_progress_value(lap_number=lap_number, total_laps=config.total_laps)
    )
    opening_bias_total = 0.0
    if lap_number > age:
        opening_bias_total = (
            params.pace_offset
            * pace_multiplier
            * resolved_model.post_stop_opening_bias_scale
            * opening_bias_units(compound=compound, age=age)
        )

    pace_term = params.pace_offset * pace_multiplier * progress_multiplier
    wear_term = (
        wear_penalty_units(wear_overage(age, params.grace_laps))
        * params.deg_rate
        * deg_multiplier
    )
    return pace_term + opening_bias_total + wear_term


def _stint_penalty_components(
    stint: Stint,
    config: RaceConfig,
    model: ModelParameters,
) -> _StintPenaltyComponents:
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
    opening_bias_total = 0.0
    if is_post_stop_stint(start_lap=stint.start_lap):
        opening_bias_total = (
            params.pace_offset
            * pace_multiplier
            * model.post_stop_opening_bias_scale
            * stint_opening_bias_units(stint.compound, stint.length)
        )
    wear_total = (
        stint_wear_penalty_units(stint.length, params.grace_laps)
        * params.deg_rate
        * deg_multiplier
    )

    return _StintPenaltyComponents(
        base_pace_total=base_pace_total,
        progress_adjustment_total=progress_adjustment_total,
        opening_bias_total=opening_bias_total,
        wear_total=wear_total,
    )


def stint_penalty_total(
    stint: Stint,
    config: RaceConfig,
    model: ModelParameters | None = None,
) -> float:
    """Collapse the lap-by-lap penalty sum for a stint into a closed form."""

    resolved_model = _resolve_model(config, model)
    return _stint_penalty_components(stint, config, resolved_model).total_penalty


def stint_score_breakdown(
    stint: Stint,
    config: RaceConfig,
    model: ModelParameters | None = None,
) -> StintScoreBreakdown:
    """Explain how one stint contributes to the final race score."""

    resolved_model = _resolve_model(config, model)
    components = _stint_penalty_components(stint, config, resolved_model)

    return StintScoreBreakdown(
        compound=stint.compound,
        start_lap=stint.start_lap,
        end_lap=stint.end_lap,
        length=stint.length,
        base_pace_total=components.base_pace_total,
        progress_adjustment_total=components.progress_adjustment_total,
        opening_bias_total=components.opening_bias_total,
        pace_total=components.pace_total,
        wear_total=components.wear_total,
        total_penalty=components.total_penalty,
    )


def driver_score_breakdown(
    config: RaceConfig,
    driver_plan: DriverPlan,
    model: ModelParameters | None = None,
) -> DriverScoreBreakdown:
    """Return the full score decomposition for a single driver."""

    resolved_model = _resolve_model(config, model)
    base_race_time = config.base_lap_time * config.total_laps
    pit_stop_time = config.pit_lane_time * driver_plan.stop_count
    additional_stop_time = extra_stop_time(driver_plan, resolved_model)
    hard_loop_penalty_time = hard_loop_extreme_temp_time(
        config,
        driver_plan,
        resolved_model,
    )
    hard_to_softer_one_stop_time = hard_to_softer_one_stop_time_penalty(
        config,
        driver_plan,
        resolved_model,
    )
    opening_commitment_time = medium_one_stop_opening_time(
        config,
        driver_plan,
        resolved_model,
    )
    stints = tuple(
        stint_score_breakdown(stint=stint, config=config, model=resolved_model)
        for stint in driver_plan.stints
    )
    tire_penalty_time = sum(stint.total_penalty for stint in stints)

    return DriverScoreBreakdown(
        driver_id=driver_plan.driver_id,
        base_race_time=base_race_time,
        pit_stop_time=pit_stop_time,
        additional_stop_time=additional_stop_time,
        hard_loop_penalty_time=hard_loop_penalty_time,
        hard_to_softer_one_stop_time=hard_to_softer_one_stop_time,
        opening_commitment_time=opening_commitment_time,
        tire_penalty_time=tire_penalty_time,
        total_time=(
            base_race_time
            + pit_stop_time
            + additional_stop_time
            + hard_loop_penalty_time
            + hard_to_softer_one_stop_time
            + opening_commitment_time
            + tire_penalty_time
        ),
        stints=stints,
    )


def driver_total_time(
    config: RaceConfig,
    driver_plan: DriverPlan,
    model: ModelParameters | None = None,
) -> float:
    """Return total race time without constructing explanation objects.

    Calibration evaluates thousands of candidate models across many races, so
    the hot path should add times directly. The richer breakdown path stays
    available for debugging tools, but prediction only needs this scalar total.
    """

    resolved_model = _resolve_model(config, model)
    base_race_time = config.base_lap_time * config.total_laps
    pit_stop_time = config.pit_lane_time * driver_plan.stop_count
    additional_stop_time = extra_stop_time(driver_plan, resolved_model)
    hard_loop_penalty_time = hard_loop_extreme_temp_time(
        config,
        driver_plan,
        resolved_model,
    )
    hard_to_softer_one_stop_time = hard_to_softer_one_stop_time_penalty(
        config,
        driver_plan,
        resolved_model,
    )
    opening_commitment_time = medium_one_stop_opening_time(
        config,
        driver_plan,
        resolved_model,
    )
    tire_penalty_time = sum(
        stint_penalty_total(stint=stint, config=config, model=resolved_model)
        for stint in driver_plan.stints
    )
    return (
        base_race_time
        + pit_stop_time
        + additional_stop_time
        + hard_loop_penalty_time
        + hard_to_softer_one_stop_time
        + opening_commitment_time
        + tire_penalty_time
    )


def extra_stop_time(
    driver_plan: DriverPlan,
    model: ModelParameters,
) -> float:
    """Return the extra structural cost for stops beyond the first.

    Historical races still showed many two-stop plans slightly outperforming the
    hidden simulator even after explicit pit-lane time was included. This term
    lets the scorer price the second stop as a little more disruptive than a
    pure tire reset without inventing a large new mechanism.
    """

    return model.additional_stop_penalty * max(0, driver_plan.stop_count - 1)


def hard_loop_extreme_temp_time(
    config: RaceConfig,
    driver_plan: DriverPlan,
    model: ModelParameters,
) -> float:
    """Return the extra cost for hard-led two-stop loops in temp extremes.

    Held-out residuals still show `HARD->...->HARD` two-stop plans landing a
    little too high in cool and hot races. A small explicit cost is cleaner
    than stretching the generic stop penalty because it only touches the
    specific loop family the data keeps flagging.
    """

    if not is_extreme_temperature(config):
        return 0.0
    if not is_hard_loop_two_stop_plan(driver_plan):
        return 0.0
    return model.hard_loop_extreme_temp_penalty


def hard_to_softer_one_stop_time_penalty(
    config: RaceConfig,
    driver_plan: DriverPlan,
    model: ModelParameters,
) -> float:
    """Return the extra cost for hard-first one-stop plans that close softer.

    Outside short cool races, held-out data consistently prefers the mirrored
    alternative over many `HARD->MEDIUM` and `HARD->SOFT` one-stop plans. This
    keeps that correction narrow instead of pushing a larger generic order term
    through every one-stop strategy.
    """

    if is_short_cool_race(config):
        return 0.0
    if not is_hard_to_softer_one_stop_plan(driver_plan):
        return 0.0
    return model.hard_to_softer_one_stop_penalty


def medium_one_stop_opening_time(
    config: RaceConfig,
    driver_plan: DriverPlan,
    model: ModelParameters,
) -> float:
    """Return the extra commitment cost for medium-start one-stop strategies.

    Held-out data still shows medium-length one-stop MEDIUM openers pricing a
    little too optimistically relative to mirrored alternatives. This term is a
    narrow structural correction: it only applies to the opening MEDIUM stint
    of a one-stop plan in medium-length races.
    """

    first_stint = driver_plan.stints[0]
    if not is_medium_one_stop_opening_stint(config, driver_plan, first_stint):
        return 0.0

    params = model.compounds[first_stint.compound]
    pace_multiplier, _ = compound_multipliers(config, model, first_stint.compound)
    return (
        params.pace_offset
        * pace_multiplier
        * model.medium_one_stop_opening_bias_scale
        * stint_opening_bias_units(first_stint.compound, first_stint.length)
    )


def predict_finishing_order(
    config: RaceConfig,
    driver_plans: Sequence[DriverPlan],
    model: ModelParameters | None = None,
) -> list[str]:
    resolved_model = _resolve_model(config, model)
    scored_drivers = [
        (
            driver_total_time(config=config, driver_plan=driver_plan, model=resolved_model),
            driver_plan.driver_id,
        )
        for driver_plan in driver_plans
    ]

    # Historical races show that identical strategies still need a stable final
    # ordering, and lower driver_id is the deterministic tiebreak.
    scored_drivers.sort(key=lambda item: (item[0], item[1]))
    return [driver_id for _, driver_id in scored_drivers]

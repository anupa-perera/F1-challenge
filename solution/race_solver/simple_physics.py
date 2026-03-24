from __future__ import annotations

"""Simple closed-form race scorer adapted from the strongest reference model.

This module is intentionally small. It models only the signals that proved to
carry most of the hidden simulator:

- base compound pace offsets
- per-compound degradation after an initial performance period
- coarse temperature buckets that scale degradation
- raw pit lane time
- starting grid as the deterministic tiebreak

The goal is not to preserve older scorer complexity. The goal is to mirror the
data-generating behavior more directly.
"""

from typing import Sequence

from .models import DriverPlan, RaceConfig


COMPOUND_OFFSETS = {
    "SOFT": -1.0,
    "MEDIUM": 0.0,
    "HARD": 0.8,
}

BASE_DEGRADATION_RATES = {
    "SOFT": 0.019775,
    "MEDIUM": 0.010003,
    "HARD": 0.005055,
}

INITIAL_PERFORMANCE_PERIOD = {
    "SOFT": 10,
    "MEDIUM": 20,
    "HARD": 30,
}


def temperature_multiplier(track_temp: int) -> float:
    if track_temp < 25:
        return 0.8
    if track_temp <= 34:
        return 1.0
    return 1.3


def driver_total_time(
    config: RaceConfig,
    driver_plan: DriverPlan,
) -> float:
    """Simulate a strategy lap by lap using the compact reference formula."""

    deg_multiplier = temperature_multiplier(config.track_temp)
    degradation_rates = {
        compound: rate * deg_multiplier
        for compound, rate in BASE_DEGRADATION_RATES.items()
    }

    total_time = config.pit_lane_time * driver_plan.stop_count
    pit_laps = {
        stint.end_lap: next_stint.compound
        for stint, next_stint in zip(driver_plan.stints, driver_plan.stints[1:])
    }
    current_tire = driver_plan.starting_tire
    current_age = 1

    for lap_number in range(1, config.total_laps + 1):
        deg_laps = max(0, current_age - INITIAL_PERFORMANCE_PERIOD[current_tire])
        lap_time = (
            config.base_lap_time
            + COMPOUND_OFFSETS[current_tire]
            + (deg_laps * config.base_lap_time * degradation_rates[current_tire])
        )
        total_time += lap_time

        if lap_number in pit_laps:
            current_tire = pit_laps[lap_number]
            current_age = 1
        else:
            current_age += 1

    return total_time


def predict_finishing_order(
    config: RaceConfig,
    driver_plans: Sequence[DriverPlan],
) -> list[str]:
    scored = [
        (
            driver_total_time(config, driver_plan),
            driver_plan.grid_position,
            driver_plan.driver_id,
        )
        for driver_plan in driver_plans
    ]
    scored.sort(key=lambda item: (item[0], item[1], item[2]))
    return [driver_id for _, _, driver_id in scored]

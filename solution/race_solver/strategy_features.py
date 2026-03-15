from __future__ import annotations

"""Shared strategy and historical-context feature helpers."""

from .historical_data import HistoricalRace
from .models import DriverPlan
from .runtime_gate import pit_burden


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


def pit_burden_bucket(value: float) -> str:
    if value <= 0.245:
        return "low"
    if value <= 0.255:
        return "mid"
    return "high"


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
    return (
        f"{laps_bucket(race.config.total_laps)}|"
        f"{temp_bucket(race.config.track_temp)}|"
        f"{pit_burden_bucket(pit_burden(race.config))}"
    )

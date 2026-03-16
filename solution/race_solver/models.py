from __future__ import annotations

"""Immutable structures shared across parsing, scoring, and calibration.

Keeping the core shapes in one place makes the rest of the code read more like
"transform data" and less like "keep reconstructing JSON by hand".
"""

from dataclasses import dataclass
from typing import Mapping, TypeAlias


COMPOUND_ORDER = ("SOFT", "MEDIUM", "HARD")


@dataclass(frozen=True)
class RaceConfig:
    track: str
    total_laps: int
    base_lap_time: float
    pit_lane_time: float
    track_temp: int


@dataclass(frozen=True)
class Stint:
    compound: str
    start_lap: int
    end_lap: int
    length: int


@dataclass(frozen=True)
class DriverPlan:
    driver_id: str
    starting_tire: str
    stop_count: int
    stints: tuple[Stint, ...]


@dataclass(frozen=True)
class RaceInput:
    race_id: str
    config: RaceConfig
    driver_plans: tuple[DriverPlan, ...]


@dataclass(frozen=True)
class CompoundParameters:
    pace_offset: float
    grace_laps: int
    deg_rate: float
    temp_pace_scale: float
    temp_deg_scale: float
    race_length_deg_scale: float


@dataclass(frozen=True)
class ModelParameters:
    compounds: Mapping[str, CompoundParameters]
    lap_progress_pace_scale: float
    post_stop_opening_bias_scale: float = 0.0
    additional_stop_penalty: float = 1.8
    medium_one_stop_opening_bias_scale: float = 0.15
    hard_loop_extreme_temp_penalty: float = 1.15
    hard_to_softer_one_stop_penalty: float = 0.035
    medium_to_hard_one_stop_bonus: float = 0.04


@dataclass(frozen=True)
class GateLeafNode:
    context_key: str
    model: ModelParameters
    fallback_context_key: str | None = None


@dataclass(frozen=True)
class GateSplitNode:
    feature_name: str
    threshold: float
    left: "GateNode"
    right: "GateNode"


GateNode: TypeAlias = GateLeafNode | GateSplitNode


@dataclass(frozen=True)
class StintScoreBreakdown:
    compound: str
    start_lap: int
    end_lap: int
    length: int
    base_pace_total: float
    progress_adjustment_total: float
    opening_bias_total: float
    pace_total: float
    wear_total: float
    total_penalty: float


@dataclass(frozen=True)
class DriverScoreBreakdown:
    driver_id: str
    base_race_time: float
    pit_stop_time: float
    additional_stop_time: float
    hard_loop_penalty_time: float
    hard_to_softer_one_stop_time: float
    medium_to_hard_one_stop_time: float
    opening_commitment_time: float
    tire_penalty_time: float
    total_time: float
    stints: tuple[StintScoreBreakdown, ...]

from __future__ import annotations

"""Small self-checks that protect the model's core assumptions."""

from .models import RaceConfig, Stint
from .parameters import (
    DEFAULT_MODEL_PARAMETERS,
    replace_parameter,
)
from .parsing import build_driver_plan
from .runtime_gate import (
    runtime_context_key,
    runtime_fallback_context_key,
    runtime_model_for_config,
)
from .scoring import (
    driver_score_breakdown,
    driver_total_time,
    lap_penalty,
    predict_finishing_order,
    sequence_order_emphasis,
    stint_penalty_total,
    stint_score_breakdown,
)


def run_self_checks() -> None:
    example_strategy = {
        "driver_id": "D001",
        "starting_tire": "SOFT",
        "pit_stops": [
            {"lap": 4, "from_tire": "SOFT", "to_tire": "MEDIUM"},
            {"lap": 7, "from_tire": "MEDIUM", "to_tire": "HARD"},
        ],
    }
    driver_plan = build_driver_plan(total_laps=10, strategy=example_strategy)
    assert [stint.length for stint in driver_plan.stints] == [4, 3, 3]

    config = RaceConfig(
        track="Check",
        total_laps=10,
        base_lap_time=87.5,
        pit_lane_time=21.0,
        track_temp=30,
    )
    fresh_stint = Stint(compound="SOFT", start_lap=1, end_lap=4, length=4)
    worn_stint = Stint(compound="SOFT", start_lap=1, end_lap=8, length=8)

    # Fresh tires start at age 1 because age advances at the start of the lap.
    lap_sum = sum(
        lap_penalty(
            compound="SOFT",
            age=age,
            lap_number=age,
            config=config,
        )
        for age in range(1, fresh_stint.length + 1)
    )
    assert abs(lap_sum - stint_penalty_total(fresh_stint, config)) < 1e-9
    assert abs(
        driver_total_time(config, driver_plan)
        - driver_score_breakdown(config, driver_plan).total_time
    ) < 1e-9
    restart_bias_model = replace_parameter(
        DEFAULT_MODEL_PARAMETERS,
        None,
        "post_stop_opening_bias_scale",
        0.5,
    )
    opening_hard_stint = Stint(compound="HARD", start_lap=1, end_lap=5, length=5)
    restart_hard_stint = Stint(compound="HARD", start_lap=6, end_lap=10, length=5)
    opening_soft_stint = Stint(compound="SOFT", start_lap=1, end_lap=5, length=5)
    restart_soft_stint = Stint(compound="SOFT", start_lap=6, end_lap=10, length=5)
    assert stint_penalty_total(restart_hard_stint, config, model=restart_bias_model) > (
        stint_penalty_total(opening_hard_stint, config, model=restart_bias_model)
    )
    assert stint_penalty_total(restart_soft_stint, config, model=restart_bias_model) < (
        stint_penalty_total(opening_soft_stint, config, model=restart_bias_model)
    )

    # A longer race should increase wear pressure more than a shorter race
    # when everything else stays fixed, because the calibrated model now uses
    # race length instead of base lap time as the second context axis.
    short_race = RaceConfig(
        track="Short",
        total_laps=32,
        base_lap_time=87.5,
        pit_lane_time=21.0,
        track_temp=30,
    )
    long_race = RaceConfig(
        track="Long",
        total_laps=60,
        base_lap_time=87.5,
        pit_lane_time=21.0,
        track_temp=30,
    )
    length_model = replace_parameter(DEFAULT_MODEL_PARAMETERS, "SOFT", "temp_deg_scale", 0.0)
    length_model = replace_parameter(length_model, "SOFT", "race_length_deg_scale", 0.1)
    short_wear = stint_score_breakdown(worn_stint, short_race, model=length_model).wear_total
    long_wear = stint_score_breakdown(worn_stint, long_race, model=length_model).wear_total
    assert long_wear > short_wear

    assert sequence_order_emphasis(short_race) == 1.0
    assert sequence_order_emphasis(config) == 1.0
    assert abs(sequence_order_emphasis(RaceConfig("Edge", 37, 87.5, 21.0, 30)) - 0.4) < 1e-9
    assert sequence_order_emphasis(long_race) == 0.0
    assert runtime_context_key(short_race) == "short_warm"
    assert runtime_context_key(config) == "short_non_medium"
    short_warm_race = RaceConfig("ShortWarm", 32, 87.5, 21.0, 30)
    medium_high_pit_race = RaceConfig("MediumHighPit", 45, 87.5, 22.5, 30)
    medium_cool_slow_cool_race = RaceConfig("MediumCoolSlowCool", 60, 91.0, 21.0, 24)
    long_non_medium_race = RaceConfig("LongNonMedium", 60, 87.5, 21.0, 30)
    shoulder_medium_high_pit_race = RaceConfig("ShoulderMediumHighPit", 38, 87.5, 21.0, 30)
    assert runtime_context_key(short_warm_race) == "short_warm"
    assert runtime_context_key(shoulder_medium_high_pit_race) == "medium_high_pit"
    assert runtime_context_key(medium_high_pit_race) == "medium_high_pit"
    assert runtime_context_key(medium_cool_slow_cool_race) == "medium_cool_slow_cool"
    assert runtime_context_key(long_non_medium_race) == "long_non_medium"
    assert runtime_fallback_context_key("short_non_medium") == "short_non_medium"
    assert runtime_fallback_context_key("short_warm") == "short_non_medium"
    assert runtime_fallback_context_key("medium_high_pit") == "medium_high_pit"
    assert runtime_fallback_context_key("medium_cool_slow_cool") == "long_non_medium"
    assert runtime_fallback_context_key("long_non_medium") == "long_non_medium"
    assert runtime_model_for_config(config) != runtime_model_for_config(short_warm_race)
    assert runtime_model_for_config(short_warm_race) != runtime_model_for_config(medium_high_pit_race)
    assert runtime_model_for_config(medium_high_pit_race) != runtime_model_for_config(long_non_medium_race)
    assert runtime_model_for_config(medium_cool_slow_cool_race) != runtime_model_for_config(long_non_medium_race)

    identical_plans = (
        build_driver_plan(
            total_laps=6,
            strategy={
                "driver_id": "D002",
                "starting_tire": "MEDIUM",
                "pit_stops": [{"lap": 3, "from_tire": "MEDIUM", "to_tire": "HARD"}],
            },
        ),
        build_driver_plan(
            total_laps=6,
            strategy={
                "driver_id": "D001",
                "starting_tire": "MEDIUM",
                "pit_stops": [{"lap": 3, "from_tire": "MEDIUM", "to_tire": "HARD"}],
            },
        ),
    )
    assert predict_finishing_order(config, identical_plans) == ["D001", "D002"]

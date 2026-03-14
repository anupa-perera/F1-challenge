from __future__ import annotations

"""Small self-checks that protect the model's core assumptions."""

from .models import RaceConfig, Stint
from .parameters import DEFAULT_MODEL_PARAMETERS, replace_parameter
from .parsing import build_driver_plan
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

    short_stint = Stint(compound="SOFT", start_lap=1, end_lap=2, length=2)
    experimental_model = replace_parameter(
        DEFAULT_MODEL_PARAMETERS,
        None,
        "fresh_tire_window",
        3,
    )
    experimental_model = replace_parameter(
        experimental_model,
        "SOFT",
        "fresh_bonus",
        -0.1,
    )
    short_breakdown = stint_score_breakdown(
        short_stint,
        config,
        model=experimental_model,
    )
    long_breakdown = stint_score_breakdown(
        fresh_stint,
        config,
        model=experimental_model,
    )
    assert short_breakdown.fresh_bonus_total < 0
    assert abs(short_breakdown.fresh_bonus_total) < abs(long_breakdown.fresh_bonus_total)

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
    short_wear = stint_score_breakdown(fresh_stint, short_race, model=length_model).wear_total
    long_wear = stint_score_breakdown(fresh_stint, long_race, model=length_model).wear_total
    assert long_wear > short_wear

    assert sequence_order_emphasis(short_race) == 1.0
    assert sequence_order_emphasis(config) == 1.0
    assert abs(sequence_order_emphasis(RaceConfig("Edge", 37, 87.5, 21.0, 30)) - 0.4) < 1e-9
    assert sequence_order_emphasis(long_race) == 0.0

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

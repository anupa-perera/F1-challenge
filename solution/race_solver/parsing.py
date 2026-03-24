from __future__ import annotations

"""Convert raw challenge JSON into validated domain objects."""

from typing import Any, Mapping

from .models import DriverPlan, RaceConfig, RaceInput, Stint


def parse_race_input(payload: Mapping[str, Any]) -> RaceInput:
    race_config = parse_race_config(payload["race_config"])
    driver_plans = build_driver_plans(race_config.total_laps, payload["strategies"])
    return RaceInput(
        race_id=str(payload["race_id"]),
        config=race_config,
        driver_plans=driver_plans,
    )


def parse_race_config(raw_config: Mapping[str, Any]) -> RaceConfig:
    return RaceConfig(
        track=str(raw_config["track"]),
        total_laps=int(raw_config["total_laps"]),
        base_lap_time=float(raw_config["base_lap_time"]),
        pit_lane_time=float(raw_config["pit_lane_time"]),
        track_temp=int(raw_config["track_temp"]),
    )


def build_driver_plans(
    total_laps: int,
    strategies: Mapping[str, Mapping[str, Any]],
) -> tuple[DriverPlan, ...]:
    plans = [
        build_driver_plan(
            total_laps=total_laps,
            strategy=strategy,
            grid_position=parse_grid_position(position_key),
        )
        for position_key, strategy in strategies.items()
    ]
    return tuple(sorted(plans, key=lambda plan: plan.driver_id))


def parse_grid_position(position_key: str) -> int:
    if position_key.startswith("pos"):
        return int(position_key[3:])
    raise ValueError(f"Unsupported strategy position key: {position_key}")


def build_driver_plan(
    total_laps: int,
    strategy: Mapping[str, Any],
    *,
    grid_position: int | None = None,
) -> DriverPlan:
    """Turn a pit plan into stints.

    Pit stops happen at the end of a lap, so a stop listed at lap 18 means the
    current tire covers lap 18 and the next tire starts fresh on lap 19.
    """

    raw_stops = sorted(strategy["pit_stops"], key=lambda stop: int(stop["lap"]))
    current_tire = str(strategy["starting_tire"])
    completed_laps = 0
    stints: list[Stint] = []

    for raw_stop in raw_stops:
        stop_lap = int(raw_stop["lap"])
        from_tire = str(raw_stop["from_tire"])
        to_tire = str(raw_stop["to_tire"])

        if from_tire != current_tire:
            raise ValueError(
                f"Pit stop expected {current_tire} but received {from_tire}."
            )
        if stop_lap <= completed_laps or stop_lap > total_laps:
            raise ValueError(f"Pit stop lap {stop_lap} is outside the stint timeline.")

        stints.append(
            Stint(
                compound=current_tire,
                start_lap=completed_laps + 1,
                end_lap=stop_lap,
                length=stop_lap - completed_laps,
            )
        )
        completed_laps = stop_lap
        current_tire = to_tire

    if completed_laps >= total_laps:
        raise ValueError("Strategy leaves no laps for the final stint.")

    stints.append(
        Stint(
            compound=current_tire,
            start_lap=completed_laps + 1,
            end_lap=total_laps,
            length=total_laps - completed_laps,
        )
    )

    return DriverPlan(
        driver_id=str(strategy["driver_id"]),
        grid_position=999 if grid_position is None else int(grid_position),
        starting_tire=str(strategy["starting_tire"]),
        stop_count=len(raw_stops),
        stints=tuple(stints),
    )

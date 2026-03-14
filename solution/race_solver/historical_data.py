from __future__ import annotations

"""Historical race loading and deterministic train/validation splitting."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import DriverPlan, RaceConfig
from .parsing import build_driver_plans, parse_race_config


DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "historical_races"


@dataclass(frozen=True)
class HistoricalRace:
    race_id: str
    race_number: int
    config: RaceConfig
    driver_plans: tuple[DriverPlan, ...]
    actual_order: tuple[str, ...]


def race_number_from_id(race_id: str) -> int:
    return int(race_id[1:])


def load_historical_races(max_races: int = 0) -> list[HistoricalRace]:
    races: list[HistoricalRace] = []
    for file_path in sorted(DATA_ROOT.glob("*.json")):
        with file_path.open(encoding="utf-8") as file_handle:
            raw_races = json.load(file_handle)

        for raw_race in raw_races:
            race_id = str(raw_race["race_id"])
            config = parse_race_config(raw_race["race_config"])
            driver_plans = build_driver_plans(config.total_laps, raw_race["strategies"])
            races.append(
                HistoricalRace(
                    race_id=race_id,
                    race_number=race_number_from_id(race_id),
                    config=config,
                    driver_plans=driver_plans,
                    actual_order=tuple(raw_race["finishing_positions"]),
                )
            )
            if max_races and len(races) >= max_races:
                return races

    return races


def split_races(
    races: Iterable[HistoricalRace],
) -> tuple[list[HistoricalRace], list[HistoricalRace]]:
    training: list[HistoricalRace] = []
    validation: list[HistoricalRace] = []

    for race in races:
        if race.race_number % 5 == 0:
            validation.append(race)
        else:
            training.append(race)

    return training, validation


def deterministic_sample(
    races: list[HistoricalRace],
    sample_size: int,
) -> list[HistoricalRace]:
    if sample_size <= 0 or sample_size >= len(races):
        return list(races)

    stride = max(1, len(races) // sample_size)
    return races[::stride][:sample_size]

#!/usr/bin/env python3
from __future__ import annotations

"""Human-readable race explanation tool for local debugging."""

import argparse
import json
import sys

from race_solver.checks import run_self_checks
from race_solver.parsing import parse_race_input
from race_solver.simple_physics import driver_total_time, predict_finishing_order


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.load(sys.stdin)
    race_input = parse_race_input(payload)
    predicted_order = predict_finishing_order(
        config=race_input.config,
        driver_plans=race_input.driver_plans,
    )
    plan_by_driver = {
        driver_plan.driver_id: driver_plan for driver_plan in race_input.driver_plans
    }

    print(f"race_id: {race_input.race_id}")
    print("predicted_order:")
    for position, driver_id in enumerate(predicted_order[: args.top], start=1):
        driver_plan = plan_by_driver[driver_id]
        total_time = driver_total_time(race_input.config, driver_plan)
        stint_summary = " -> ".join(
            f"{stint.compound}({stint.start_lap}-{stint.end_lap})"
            for stint in driver_plan.stints
        )
        print(
            "  "
            f"{position:02d}. {driver_id}  "
            f"time={total_time:.3f}  "
            f"grid={driver_plan.grid_position:02d}  "
            f"stops={driver_plan.stop_count}  "
            f"plan={stint_summary}"
        )


if __name__ == "__main__":
    if __debug__:
        run_self_checks()
    main()

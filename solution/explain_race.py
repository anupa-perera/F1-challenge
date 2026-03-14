#!/usr/bin/env python3
from __future__ import annotations

"""Human-readable race explanation tool for local debugging."""

import argparse
import json
import sys

from race_solver.checks import run_self_checks
from race_solver.parsing import parse_race_input
from race_solver.reporting import format_driver_breakdown
from race_solver.scoring import driver_score_breakdown, predict_finishing_order


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
        breakdown = driver_score_breakdown(
            config=race_input.config,
            driver_plan=plan_by_driver[driver_id],
        )
        for line in format_driver_breakdown(breakdown, position=position):
            print(f"  {line}")


if __name__ == "__main__":
    if __debug__:
        run_self_checks()
    main()

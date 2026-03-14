#!/usr/bin/env python3
from __future__ import annotations

"""Compare a prediction against an expected order and explain the mismatch."""

import argparse
import json
from pathlib import Path
import sys

from race_solver.checks import run_self_checks
from race_solver.parsing import parse_race_input
from race_solver.reporting import (
    first_divergence,
    format_driver_breakdown,
    format_order_preview,
    order_position_map,
)
from race_solver.scoring import driver_score_breakdown, predict_finishing_order


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Path to the input race JSON.")
    parser.add_argument(
        "--expected",
        type=Path,
        help="Optional path to the expected output JSON for comparison.",
    )
    parser.add_argument("--preview", type=int, default=10)
    return parser.parse_args()


def load_payload(input_path: Path | None) -> dict:
    if input_path is None:
        return json.load(sys.stdin)
    return json.loads(input_path.read_text(encoding="utf-8"))


def load_expected_order(expected_path: Path | None) -> list[str] | None:
    if expected_path is None:
        return None
    payload = json.loads(expected_path.read_text(encoding="utf-8"))
    return list(payload["finishing_positions"])


def main() -> None:
    args = parse_args()
    payload = load_payload(args.input)
    expected_order = load_expected_order(args.expected)

    race_input = parse_race_input(payload)
    predicted_order = predict_finishing_order(
        config=race_input.config,
        driver_plans=race_input.driver_plans,
    )
    breakdown_by_driver = {
        driver_plan.driver_id: driver_score_breakdown(
            config=race_input.config,
            driver_plan=driver_plan,
        )
        for driver_plan in race_input.driver_plans
    }

    print(f"race_id: {race_input.race_id}")
    print("predicted_preview:")
    for line in format_order_preview(
        predicted_order,
        expected_order,
        limit=args.preview,
    ):
        print(line)

    if expected_order is None:
        return

    divergence = first_divergence(predicted_order, expected_order)
    if divergence is None:
        print("status: exact match")
        return

    position, predicted_driver, expected_driver = divergence
    predicted_positions = order_position_map(predicted_order)
    expected_positions = order_position_map(expected_order)

    print("status: mismatch")
    print(
        f"first_divergence: position {position:02d}  "
        f"predicted={predicted_driver}  expected={expected_driver}"
    )
    print(
        f"position_delta: {predicted_driver} expected #{expected_positions[predicted_driver]:02d}, "
        f"{expected_driver} predicted #{predicted_positions[expected_driver]:02d}"
    )

    print("focus:")
    for line in format_driver_breakdown(
        breakdown_by_driver[predicted_driver],
        position=predicted_positions[predicted_driver],
    ):
        print(f"  predicted -> {line}")
    for line in format_driver_breakdown(
        breakdown_by_driver[expected_driver],
        position=expected_positions[expected_driver],
    ):
        print(f"  expected  -> {line}")


if __name__ == "__main__":
    if __debug__:
        run_self_checks()
    main()

#!/usr/bin/env python3
from __future__ import annotations

"""Run high-support historical regression checks against a chosen split."""

import argparse

from race_solver.historical_data import load_historical_races, split_races
from race_solver.historical_regressions import run_historical_regressions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-races", type=int, default=0)
    parser.add_argument(
        "--split",
        choices=("all", "train", "validation"),
        default="validation",
    )
    return parser.parse_args()


def select_races(args: argparse.Namespace):
    all_races = load_historical_races(max_races=args.max_races)
    training_races, validation_races = split_races(all_races)
    if args.split == "train":
        return "train", training_races
    if args.split == "validation":
        return "validation", validation_races
    return "all", all_races


def main() -> None:
    args = parse_args()
    split_label, races = select_races(args)
    results = run_historical_regressions(races)
    failures = [result for result in results if not result.passed]

    print(f"split={split_label} races={len(races)}")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status}  {result.name}  {result.details}")

    if failures:
        raise SystemExit(f"{len(failures)} historical regression checks failed")


if __name__ == "__main__":
    main()

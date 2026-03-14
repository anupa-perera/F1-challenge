#!/usr/bin/env python3
from __future__ import annotations

"""Summarize historically observed strategy patterns from the training races."""

import argparse

from race_solver.analysis import (
    extract_winner_patterns,
    laps_bucket,
    pit_burden_bucket,
    summarize_start_band_usage,
    summarize_winner_patterns,
    temp_bucket,
)
from race_solver.historical_data import load_historical_races


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-races", type=int, default=0)
    return parser.parse_args()


def print_bucket_summary(title: str, summaries: dict[str, object]) -> None:
    print(title)
    for bucket, summary in summaries.items():
        print(
            f"  {bucket}: races={summary.race_count}  "
            f"two_stop={summary.two_stop_rate:.1%}  "
            f"avg_first_stint_frac={summary.average_first_stint_fraction:.3f}"
        )
        print(f"    start_tires={summary.start_tire_distribution}")
        print(f"    top_sequences={summary.top_sequences}")


def main() -> None:
    args = parse_args()
    races = load_historical_races(max_races=args.max_races)
    winner_patterns = extract_winner_patterns(races)

    print("start_band_usage")
    for band, summary in summarize_start_band_usage(races).items():
        print(
            f"  {band}: avg_first_stint={summary['avg_first_stint']:.2f}  "
            f"start_tires={summary['start_tires']}"
        )

    print_bucket_summary(
        "winner_patterns_by_temperature",
        summarize_winner_patterns(
            winner_patterns,
            bucket_fn=temp_bucket,
            value_fn=lambda pattern: pattern.track_temp,
        ),
    )
    print_bucket_summary(
        "winner_patterns_by_laps",
        summarize_winner_patterns(
            winner_patterns,
            bucket_fn=laps_bucket,
            value_fn=lambda pattern: pattern.total_laps,
        ),
    )
    print_bucket_summary(
        "winner_patterns_by_pit_burden",
        summarize_winner_patterns(
            winner_patterns,
            bucket_fn=pit_burden_bucket,
            value_fn=lambda pattern: pattern.pit_burden,
        ),
    )


if __name__ == "__main__":
    main()

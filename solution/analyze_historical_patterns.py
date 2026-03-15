#!/usr/bin/env python3
from __future__ import annotations

"""Summarize historically observed strategy patterns from the training races."""

import argparse

from race_solver.analysis import (
    DEFAULT_CROSSOVER_FAMILY_PAIRS,
    extract_winner_patterns,
    laps_bucket,
    pit_burden_bucket,
    summarize_runtime_bucket_value,
    summarize_strategy_crossovers,
    summarize_historical_residuals,
    summarize_start_band_usage,
    summarize_winner_patterns,
    temp_bucket,
)
from race_solver.historical_data import load_historical_races, split_races


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-races", type=int, default=0)
    parser.add_argument(
        "--split",
        choices=("all", "train", "validation"),
        default="validation",
    )
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--min-samples", type=int, default=50)
    parser.add_argument("--min-crossover-total", type=int, default=20)
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


def print_residual_group_summary(title: str, summaries: list[object]) -> None:
    print(title)
    for summary in summaries:
        print(
            f"  {summary.key}: samples={summary.sample_count}  "
            f"avg_rank_error={summary.average_rank_error:+.3f}  "
            f"avg_abs_rank_error={summary.average_absolute_rank_error:.3f}"
        )
        print(f"    top_signatures={summary.top_signatures}")


def print_runtime_bucket_value_summary(title: str, summaries: list[object]) -> None:
    print(title)
    for summary in summaries:
        print(
            f"  {summary.context_key}: races={summary.race_count}  "
            f"exact={summary.exact_matches}  "
            f"fallback={summary.fallback_exact_matches}  "
            f"exact_gain={summary.exact_gain:+d}  "
            f"pairwise_gain={summary.pairwise_gain:+.4%}  "
            f"fallback_bucket={summary.fallback_context_key}"
        )


def print_strategy_crossover_summary(title: str, summaries: list[object]) -> None:
    print(title)
    for summary in summaries:
        print(
            f"  {summary.left_family} vs {summary.right_family}  "
            f"context={summary.context_key}  "
            f"{summary.left_wins}-{summary.right_wins}  "
            f"winner={summary.winner}  "
            f"winner_rate={summary.winner_rate:.1%}"
        )


def select_race_split(args: argparse.Namespace) -> tuple[str, list[object]]:
    all_races = load_historical_races(max_races=args.max_races)
    training_races, validation_races = split_races(all_races)
    if args.split == "train":
        return "train", training_races
    if args.split == "validation":
        return "validation", validation_races
    return "all", all_races


def main() -> None:
    args = parse_args()
    split_label, races = select_race_split(args)
    winner_patterns = extract_winner_patterns(races)
    residual_summary = summarize_historical_residuals(
        races,
        top=args.top,
        min_samples=args.min_samples,
    )
    runtime_bucket_value = summarize_runtime_bucket_value(races)
    crossover_summary = summarize_strategy_crossovers(
        races,
        family_pairs=DEFAULT_CROSSOVER_FAMILY_PAIRS,
        min_total=args.min_crossover_total,
    )

    print(f"split={split_label} races={len(races)}")

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
    print_residual_group_summary(
        "overrated_strategy_families",
        residual_summary.family_overrated,
    )
    print_residual_group_summary(
        "underrated_strategy_families",
        residual_summary.family_underrated,
    )
    print_residual_group_summary(
        "overrated_strategy_families_by_context",
        residual_summary.family_context_overrated,
    )
    print_residual_group_summary(
        "underrated_strategy_families_by_context",
        residual_summary.family_context_underrated,
    )
    print("top_pairwise_confusions")
    for summary in residual_summary.pairwise_confusions:
        print(
            f"  {summary.mismatch_count:04d}x  "
            f"predicted_ahead={summary.predicted_ahead_family}  "
            f"actual_ahead={summary.actual_ahead_family}  "
            f"context={summary.context_bucket}"
        )
    print_runtime_bucket_value_summary(
        "runtime_bucket_value_audit",
        runtime_bucket_value,
    )
    print_strategy_crossover_summary(
        "mirrored_family_crossovers",
        crossover_summary,
    )


if __name__ == "__main__":
    main()

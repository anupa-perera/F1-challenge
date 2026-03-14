#!/usr/bin/env python3
from __future__ import annotations

"""Aggregate solver behavior across a suite of labeled cases."""

import argparse
from pathlib import Path

from race_solver.analysis import compare_case_directories


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputs-dir",
        type=Path,
        default=Path("data/test_cases/inputs"),
    )
    parser.add_argument(
        "--expected-dir",
        type=Path,
        default=Path("data/test_cases/expected_outputs"),
    )
    parser.add_argument("--top", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    comparisons, summary = compare_case_directories(
        inputs_dir=args.inputs_dir,
        expected_dir=args.expected_dir,
    )

    print(f"cases: {summary.case_count}")
    print(f"exact_matches: {summary.exact_matches}")
    print(f"exact_rate: {summary.exact_matches / summary.case_count:.2%}")
    print("first_divergence_counts:")
    for position, count in summary.first_divergence_counts.most_common(args.top):
        print(f"  position {position:02d}: {count}")
    print("first_divergence_strategy_patterns:")
    for (predicted_sig, expected_sig), count in summary.first_divergence_strategy_counts.most_common(args.top):
        print(
            f"  {count:02d}x  predicted={predicted_sig}  expected={expected_sig}"
        )
    print("winner_mismatch_patterns:")
    for (predicted_sig, expected_sig), count in summary.winner_mismatch_counts.most_common(args.top):
        print(
            f"  {count:02d}x  predicted={predicted_sig}  expected={expected_sig}"
        )

    print("sample_mismatches:")
    mismatch_cases = [comparison for comparison in comparisons if not comparison.exact_match]
    mismatch_cases.sort(
        key=lambda comparison: (
            comparison.first_divergence_position or 999,
            comparison.case_name,
        )
    )
    for comparison in mismatch_cases[: args.top]:
        print(
            f"  {comparison.case_name}: "
            f"first_divergence={comparison.first_divergence_position}  "
            f"predicted_winner={comparison.predicted_winner_signature}  "
            f"expected_winner={comparison.expected_winner_signature}"
        )


if __name__ == "__main__":
    main()

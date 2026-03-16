#!/usr/bin/env python3
from __future__ import annotations

"""Cross-platform local equivalent of the bash test runner.

The official evaluator uses `./test_runner.sh`. This script mirrors the same
execution seam through `solution/run_command.txt`, but avoids bash/jq/bc so it
can run in environments like Windows PowerShell as well.
"""

import argparse
import json
from pathlib import Path

from verify_submission import REPO_ROOT, load_run_command, run_solution, validate_output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputs-dir",
        type=Path,
        default=REPO_ROOT / "data" / "test_cases" / "inputs",
    )
    parser.add_argument(
        "--expected-dir",
        type=Path,
        default=REPO_ROOT / "data" / "test_cases" / "expected_outputs",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit the number of cases for quicker smoke runs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    command = load_run_command()

    test_files = sorted(args.inputs_dir.glob("test_*.json"))
    if args.limit > 0:
        test_files = test_files[: args.limit]

    total = len(test_files)
    if total == 0:
        raise SystemExit(f"no test cases found in {args.inputs_dir}")

    passed = 0
    failed = 0
    errors = 0

    print(f"run_command: {command}")
    print(f"cases: {total}")

    for input_path in test_files:
        expected_path = args.expected_dir / input_path.name
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        expected = json.loads(expected_path.read_text(encoding="utf-8"))

        try:
            output, _ = run_solution(command, payload)
            validate_output(payload, output)
        except SystemExit as exc:
            print(f"ERR  {input_path.stem}: {exc}")
            errors += 1
            continue

        if output["finishing_positions"] == expected["finishing_positions"]:
            print(f"PASS {input_path.stem}")
            passed += 1
        else:
            print(f"FAIL {input_path.stem}")
            failed += 1

    exact_rate = passed / total if total else 0.0
    print(f"passed: {passed}")
    print(f"failed: {failed}")
    print(f"errors: {errors}")
    print(f"exact_rate: {exact_rate:.2%}")

    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

"""Verify that the repo is ready for evaluator-style execution.

This script checks the same submission seam the challenge uses:
- read the command from `solution/run_command.txt`
- execute it from the repository root
- feed one real test case through stdin
- validate the emitted JSON shape

It keeps submission compliance separate from the solver itself, so we can keep
improving the model without muddying the evaluator path.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_COMMAND_PATH = REPO_ROOT / "solution" / "run_command.txt"
DEFAULT_CASE_PATH = REPO_ROOT / "data" / "test_cases" / "inputs" / "test_001.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case",
        type=Path,
        default=DEFAULT_CASE_PATH,
        help="Input case used for submission smoke verification.",
    )
    parser.add_argument(
        "--run-test-runner",
        action="store_true",
        help="Also invoke ./test_runner.sh after the submission smoke check.",
    )
    return parser.parse_args()


def load_run_command() -> str:
    if not RUN_COMMAND_PATH.exists():
        raise SystemExit(f"missing run command file: {RUN_COMMAND_PATH}")

    command = RUN_COMMAND_PATH.read_text(encoding="utf-8").strip()
    if not command:
        raise SystemExit(f"run command file is empty: {RUN_COMMAND_PATH}")
    if "\n" in command or "\r" in command:
        raise SystemExit("run command must be a single line")
    return command


def load_case(case_path: Path) -> dict:
    resolved = case_path if case_path.is_absolute() else (REPO_ROOT / case_path)
    if not resolved.exists():
        raise SystemExit(f"input case not found: {resolved}")
    return json.loads(resolved.read_text(encoding="utf-8"))


def run_solution(command: str, payload: dict) -> tuple[dict, str]:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        shell=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise SystemExit(
            f"solution command failed with exit code {result.returncode}: {stderr}"
        )
    if not result.stdout.strip():
        raise SystemExit("solution produced empty stdout")

    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"solution stdout is not valid JSON: {exc}") from exc

    return output, result.stderr


def validate_output(input_payload: dict, output_payload: dict) -> None:
    expected_race_id = input_payload["race_id"]
    predicted_race_id = output_payload.get("race_id")
    if predicted_race_id != expected_race_id:
        raise SystemExit(
            f"race_id mismatch: expected {expected_race_id}, got {predicted_race_id}"
        )

    finishing_positions = output_payload.get("finishing_positions")
    if not isinstance(finishing_positions, list):
        raise SystemExit("finishing_positions must be a JSON array")
    if len(finishing_positions) != 20:
        raise SystemExit(
            f"finishing_positions must contain 20 drivers, got {len(finishing_positions)}"
        )

    strategies = input_payload["strategies"]
    if isinstance(strategies, dict):
        strategy_iterable = strategies.values()
    elif isinstance(strategies, list):
        strategy_iterable = strategies
    else:
        raise SystemExit("input strategies must be a list or object")

    expected_driver_ids = {
        strategy["driver_id"] for strategy in strategy_iterable
    }
    actual_driver_ids = set(finishing_positions)
    if len(actual_driver_ids) != 20:
        raise SystemExit("finishing_positions contains duplicate driver IDs")
    if actual_driver_ids != expected_driver_ids:
        raise SystemExit(
            "finishing_positions does not match the input driver set"
        )


def run_test_runner() -> None:
    result = subprocess.run(
        "bash ./test_runner.sh",
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        shell=True,
        check=False,
    )
    sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    if result.returncode != 0:
        raise SystemExit(f"test_runner failed with exit code {result.returncode}")


def main() -> None:
    args = parse_args()
    command = load_run_command()
    payload = load_case(args.case)
    output, stderr = run_solution(command, payload)
    validate_output(payload, output)

    print(f"run_command: {command}")
    print(f"race_id: {output['race_id']}")
    print(f"positions: {len(output['finishing_positions'])}")
    if stderr.strip():
        print("stderr: non-empty")
    else:
        print("stderr: empty")
    print("submission_smoke: ok")

    if args.run_test_runner:
        run_test_runner()


if __name__ == "__main__":
    main()

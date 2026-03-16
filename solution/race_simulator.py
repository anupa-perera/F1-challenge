#!/usr/bin/env python3
from __future__ import annotations

"""Submission entrypoint expected by the challenge evaluator.

This file intentionally does the minimum:
- read one JSON race payload from stdin
- parse it into internal objects
- run the deterministic simulator
- write one JSON result to stdout

Keeping the evaluator path this small reduces the chance that local developer
checks leak into the final runtime behavior.
"""

import json
import sys

from race_solver.parsing import parse_race_input
from race_solver.simulation import simulate_race


def main() -> None:
    payload = json.load(sys.stdin)
    race_input = parse_race_input(payload)
    output = simulate_race(race_input)
    json.dump(output, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

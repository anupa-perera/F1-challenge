#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

from race_solver.checks import run_self_checks
from race_solver.parsing import parse_race_input
from race_solver.simulation import simulate_race


def main() -> None:

    payload = json.load(sys.stdin)
    race_input = parse_race_input(payload)
    output = simulate_race(race_input)
    json.dump(output, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    if __debug__:
        run_self_checks()
    main()

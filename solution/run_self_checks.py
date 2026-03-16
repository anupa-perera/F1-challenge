#!/usr/bin/env python3
from __future__ import annotations

"""Run local scorer and routing invariants outside the submission path."""

from race_solver.checks import run_self_checks


def main() -> None:
    run_self_checks()
    print("self-checks ok")


if __name__ == "__main__":
    main()

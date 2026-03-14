# Solution Structure

The solver is organized so each file answers one question:

- `race_simulator.py`
  Reads stdin, runs the simulator, writes stdout.
- `calibrate_model.py`
  Runs the offline parameter search against historical races.
- `explain_race.py`
  Prints a human-readable score breakdown for each predicted finisher.
- `analyze_case.py`
  Compares a predicted order to an expected order and highlights the first divergence.
- `analyze_suite.py`
  Aggregates failure patterns across a labeled suite so we can self-analyze model behavior.
- `analyze_historical_patterns.py`
  Summarizes historically observed strategy patterns so modeling ideas stay tied to the data.
- `race_solver/models.py`
  Defines the immutable data structures shared everywhere else.
- `race_solver/parsing.py`
  Turns challenge JSON into validated race and strategy objects.
- `race_solver/parameters.py`
  Stores the current fitted parameters and the model guardrails.
- `race_solver/scoring.py`
  Contains the actual tire penalty and total race scoring logic.
- `race_solver/reporting.py`
  Formats solver output into readable conclusions for debugging and review.
- `race_solver/analysis.py`
  Builds reusable case, suite, and historical-pattern summaries from labeled data.
- `race_solver/simulation.py`
  Builds the final challenge output from parsed race input.
- `race_solver/historical_data.py`
  Loads labeled historical races and applies the deterministic split.
- `race_solver/calibration.py`
  Evaluates parameter sets and performs the coarse/refine search.
- `race_solver/checks.py`
  Small self-checks for the assumptions that are easiest to break during refactors.

## Why This Layout

- The architecture is split into three paths:
  - runtime: `race_simulator.py` -> parsing -> scoring -> simulation output
  - calibration: `calibrate_model.py` -> historical loader -> calibration -> frozen parameters
  - analysis: `analyze_*.py` -> analysis/reporting helpers -> readable conclusions
- Parsing is separate from scoring, so model changes do not force JSON changes.
- Calibration is separate from runtime, so the prediction path stays small.
- Analysis stays separate from runtime, so we can explore the historical data without bloating the submission path.
- The v1 scoring model uses numeric race context (`base_lap_time`, `pit_lane_time`, `track_temp`, `total_laps`) and currently ignores the `track` name because the numeric fields are what directly alter the computed score.

## Workflow

1. Update the scoring model in `race_solver/scoring.py` or parameters in `race_solver/parameters.py`.
2. Refit with `python solution/calibrate_model.py`.
   Quick iteration path:
   `--profile smoke` for correctness and wiring checks,
   `--profile fast` for trying ideas cheaply,
   `--profile medium` before spending a full run,
   and `--profile full` as the only commit-worthy gate.
3. Freeze the best parameters back into `race_solver/parameters.py`.
4. Run the solver with `python solution/race_simulator.py < input.json`.
5. Explain a race with `python solution/explain_race.py < input.json`.
6. Compare a prediction with `python solution/analyze_case.py --input ... --expected ...`.
7. Analyze a whole suite with `python solution/analyze_suite.py`.
8. Mine historical strategy patterns with `python solution/analyze_historical_patterns.py`.

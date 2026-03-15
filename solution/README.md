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
  Summarizes historically observed strategy patterns and residual biases by
  strategy family/context so modeling ideas stay tied to the data.
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
- Calibration and prediction use a direct total-time scorer, while explanation
  tools still use the richer score-breakdown path for human-readable analysis.
- The v1 scoring model uses numeric race context (`base_lap_time`, `pit_lane_time`, `track_temp`, `total_laps`) and currently ignores the `track` name because the numeric fields are what directly alter the computed score.
- The current wear model treats age beyond the grace window as a degradation
  state and applies a nonlinear penalty to that state, which proved much
  stronger than the earlier direct age-overage penalty.
- Runtime now uses a deterministic context gate:
  medium-length cool fast/mid tracks use a dedicated parameter set,
  medium-length cool slow tracks use their own fit,
  hot medium-length high pit-burden fast/slow tracks use their own fit,
  hot medium-length high pit-burden races use their own fit,
  medium-length high pit-burden races use their own fit,
  hot medium-length non-high-pit fast/mid tracks use their own fit,
  hot medium-length non-high-pit races use their own fit,
  other medium-length races use their own fit,
  short cool/mild non-medium races use their own fit,
  short warm/hot non-medium races use their own fit,
  and long non-medium races keep their own fit.
- The gate is hierarchical, not flat:
  - parent fallbacks are `medium_cool`, `medium_high_pit`, `medium_other`, and `non_medium`
  - child buckets only stay in the runtime path if they beat their parent on held-out history
  - this lets us drop weak specializations later without changing the scorer

## Workflow

1. Update the scoring model in `race_solver/scoring.py` or parameters in `race_solver/parameters.py`.
2. Refit with `python solution/calibrate_model.py`.
   Quick iteration path:
   `--profile smoke` for correctness and wiring checks,
   `--profile fast` for trying ideas cheaply,
   `--profile medium` before spending a full run,
   and `--profile full` as the only commit-worthy gate.
   By default calibration now fits the runtime eleven-way split
   (`medium_cool_fast_mid`, `medium_cool_slow`,
   `medium_high_pit_hot_fast_slow`, `medium_high_pit_hot`,
   `medium_high_pit`,
   `medium_other_hot_fast_mid`, `medium_other_hot`,
   `medium_other`,
   `short_cool_mild`, `short_warm`, `long_non_medium`);
   pass `--context-split global` to compare against the
   single-model baseline.
3. Freeze the best parameters back into `race_solver/parameters.py`.
4. Run the solver with `python solution/race_simulator.py < input.json`.
5. Explain a race with `python solution/explain_race.py < input.json`.
6. Compare a prediction with `python solution/analyze_case.py --input ... --expected ...`.
7. Analyze a whole suite with `python solution/analyze_suite.py`.
8. Mine historical strategy patterns with `python solution/analyze_historical_patterns.py`.
   Use `--split validation` to inspect held-out residuals before changing the model.

## Backlog

- Residual visualization/export:
  add a lightweight path to export held-out residuals for heatmaps and scatter
  plots by strategy family, `total_laps`, `track_temp`, `pit_burden`, and
  `base_lap_time`.
- Normalized diagnostic views:
  use normalized or winsorized plots to compare context axes fairly, but keep
  full historical data in calibration and evaluation instead of dropping
  "outliers" from the deterministic target.

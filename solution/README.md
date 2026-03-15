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
- `race_solver/runtime_gate.py`
  Owns deterministic context routing and fallback relationships for runtime scoring.
- `race_solver/scoring.py`
  Contains the actual tire penalty and total race scoring logic.
- `race_solver/reporting.py`
  Formats solver output into readable conclusions for debugging and review.
- `race_solver/analysis.py`
  Builds reusable case, suite, and historical-pattern summaries from labeled data.
- `race_solver/evaluation.py`
  Centralizes exact-order and pairwise evaluation so calibration and analysis use the same metric logic.
- `race_solver/strategy_features.py`
  Holds reusable strategy signatures and simple historical context bucketing helpers.
- `race_solver/simulation.py`
  Builds the final challenge output from parsed race input.
- `race_solver/historical_data.py`
  Loads labeled historical races and applies the deterministic split.
- `race_solver/calibration.py`
  Evaluates parameter sets and performs the coarse/refine search.
- `race_solver/learned_gate.py`
  Searches for a small deterministic routing tree over the existing expert models.
- `race_solver/checks.py`
  Small self-checks for the assumptions that are easiest to break during refactors.

## Why This Layout

- The architecture is split into three paths:
  - runtime: `race_simulator.py` -> parsing -> scoring -> simulation output
  - calibration: `calibrate_model.py` -> historical loader -> calibration -> frozen parameters
  - analysis: `analyze_*.py` -> analysis/reporting helpers -> readable conclusions
- Parsing is separate from scoring, so model changes do not force JSON changes.
- Runtime routing is separate from fitted parameter storage, so gate changes do
  not force edits to the parameter guardrails and parameter changes do not have
  to carry routing logic with them.
- Evaluation is separate from both calibration and analysis, so the definition
  of "good prediction" stays consistent across fitting and diagnostics.
- Calibration is separate from runtime, so the prediction path stays small.
- Analysis stays separate from runtime, so we can explore the historical data without bloating the submission path.
- Calibration and prediction use a direct total-time scorer, while explanation
  tools still use the richer score-breakdown path for human-readable analysis.
- Stint math now has one shared implementation path inside the scorer, so
  future tire-model changes do not have to be repeated once for runtime totals
  and again for explanation output.
- The v1 scoring model uses numeric race context (`base_lap_time`, `pit_lane_time`, `track_temp`, `total_laps`) and currently ignores the `track` name because the numeric fields are what directly alter the computed score.
- The current wear model treats age beyond the grace window as a degradation
  state and applies a nonlinear penalty to that state, which proved much
  stronger than the earlier direct age-overage penalty.
- The scorer now also applies a calibrated post-stop opening bias:
  restart stints can have a different early-lap pace shape than the opening
  stint, and the fitter learns one global scale for that effect per runtime
  bucket instead of hard-coding a new family of per-compound bonuses.
- Runtime now uses a learned, pruned deterministic gate tree over the existing
  expert model catalog instead of a hand-grown bucket list. The frozen runtime
  tree is intentionally small:
  - very short races route to `short_non_medium`
  - short warm races route to `short_warm`
  - short shoulder races route to `short_cool_mild`
  - the main medium-long band routes to `medium_high_pit`
  - cooler long-shoulder races route to `medium_cool_slow_cool`
  - the remaining longest races route to `long_non_medium`
- That tree is still fully deterministic and readable, but it is simpler than
  the old manual gate and was selected because it improved held-out exact order
  while reducing routing complexity.

## Workflow

1. Update the scoring model in `race_solver/scoring.py` or parameters in `race_solver/parameters.py`.
2. Refit with `python solution/calibrate_model.py`.
   Quick iteration path:
   `--profile smoke` for correctness and wiring checks,
   `--profile fast` for trying ideas cheaply,
   `--profile medium` before spending a full run,
   and `--profile full` as the only commit-worthy gate.
   By default calibration now fits the current runtime six-way split
   (`short_non_medium`, `short_warm`, `short_cool_mild`,
   `medium_high_pit`, `medium_cool_slow_cool`, `long_non_medium`).
   Each active runtime leaf now starts from its currently frozen leaf model
   instead of restarting from the global baseline, so fitting improves the live
   gate we actually ship rather than relearning those leaves from scratch.
   The pace-offset search bounds are intentionally wider than the original
   model's caps, because the tighter bounds were clipping a materially better
   exact-order fit on held-out history.
   Pass `--context-split global` to compare against the single-model baseline,
   or `--context-split learned_tree` to search for a new compact routing tree
   over the current expert model catalog.
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

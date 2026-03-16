# Solution Structure

The solver is organized so each file answers one question:

- `race_simulator.py`
  Reads stdin, runs the simulator, writes stdout.
- `run_self_checks.py`
  Runs local invariants without touching the evaluator path.
- `verify_submission.py`
  Smoke-tests the final submission seam by reading `run_command.txt`,
  executing the solver from the repository root, and validating the JSON
  output shape.
- `run_local_suite.py`
  Cross-platform local equivalent of `./test_runner.sh` that still executes
  the solver through `run_command.txt`.
- `export_hybrid_model.py`
  Trains and exports the current close-pair hybrid reranker into a pure-Python
  model artifact for submission-safe runtime use.
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
- `race_solver/pair_reranker.py`
  Applies the exported close-pair hybrid model as a narrow deterministic
  tie-breaker on top of the scorer's baseline order, including a slightly
  wider gate for mirrored one-stop arc pairs that the live model consistently
  knows how to fix.
- `race_solver/pair_reranker_trees.py`
  Auto-generated pure-Python tree constants exported from offline training.
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
- `race_solver/hybrid_features.py`
  Builds offline learned-ranking features from the live deterministic scorer
  and raw strategy/context structure.
- `race_solver/hybrid_ranker.py`
  Houses offline hybrid rankers that sit on top of the deterministic scorer
  without changing the submission runtime.
- `train_hybrid_ranker.py`
  Runs offline hybrid ranking experiments so we can measure whether learned
  layers have real headroom before touching the evaluator path.
- `race_solver/learned_gate.py`
  Searches for a small deterministic routing tree over the existing expert models.
- `race_solver/checks.py`
  Small self-checks for the assumptions that are easiest to break during refactors.

## Why This Layout

- The architecture is split into three paths:
  - runtime: `race_simulator.py` -> parsing -> scoring -> simulation output
  - calibration: `calibrate_model.py` -> historical loader -> calibration -> frozen parameters
  - analysis: `analyze_*.py` -> analysis/reporting helpers -> readable conclusions
- The runtime entrypoint is intentionally tiny and only does stdin -> parse ->
  simulate -> stdout. Local checks live in separate scripts so evaluator runs
  stay aligned with the submission contract.
- Parsing is separate from scoring, so model changes do not force JSON changes.
- Runtime routing is separate from fitted parameter storage, so gate changes do
  not force edits to the parameter guardrails and parameter changes do not have
  to carry routing logic with them.
- Evaluation is separate from both calibration and analysis, so the definition
  of "good prediction" stays consistent across fitting and diagnostics.
- Calibration is separate from runtime, so the prediction path stays small.
- Analysis stays separate from runtime, so we can explore the historical data without bloating the submission path.
- Hybrid ranking experiments stay separate from runtime too. That lets us test
  whether a learned reranker has real headroom without risking submission
  stability or leaking failed experiments into the live solver.
- The live submission path now uses the conservative hybrid seam that proved
  itself on held-out history:
  - the deterministic scorer still produces the baseline order
  - the exported reranker only inspects adjacent pairs with very small
    strategy-cost gaps
  - mirrored one-stop arc pairs are allowed a slightly wider cost-gap window
    because validation showed the learned reranker was right about many of
    those cases but the old global gate never let it act
  - it swaps them only when the model is confident enough
  - the current exported model is trained on both adjacent and second-neighbor
    examples (`max_rank_gap=2`), but runtime still only performs adjacent swaps
  - the current exported model allows up to three reranking passes so one good
    local correction can propagate through a dense cluster
  This keeps learning in the role of tie-breaker rather than replacing the
  whole strategy model.
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
  bucket instead of hard-coding a new family of free parameters. The live
  profile is now both short and compound-aware:
  - `SOFT` gets the quickest restart effect
  - `MEDIUM` keeps a short two-lap profile
  - `HARD` carries a slightly longer warm-up penalty
  That keeps the mechanism compact while pricing restarted durable stints more
  realistically than one shared generic opening shape.
- The scorer now also carries a small additional penalty for each pit stop
  beyond the first. Historical residuals showed the model was still giving too
  much net credit to many two-stop strategies even after explicit pit-lane time
  was included, so the live model treats the second stop as slightly more
  costly than a pure tire reset.
- The scorer also applies a narrow hard-loop penalty in temperature extremes.
  Held-out residuals kept overrating `HARD->...->HARD` two-stop loops in cool
  and hot races, so the live model prices that specific family explicitly
  instead of inflating the generic stop penalty for every two-stop plan.
- The scorer now treats one-stop compound transitions as an explicit arc term
  rather than separate hard-first and medium-to-hard patches. That keeps the
  remaining mirrored one-stop corrections in one place:
  - each one-stop arc (`SOFT->MEDIUM`, `SOFT->HARD`, `MEDIUM->SOFT`,
    `MEDIUM->HARD`, `HARD->SOFT`, `HARD->MEDIUM`) can carry a small fitted
    adjustment
  - most runtime leaves still use the old neutral/default arc shape
  - the current `short_cool_mild`, `medium_high_pit`,
    `medium_high_pit_hot`, and `medium_high_pit_cool` leaves are the ones
    that earned materially different arc profiles on held-out history
- The scorer now also treats symmetric two-stop loops (`A->B->A`) as an
  explicit structural term. That keeps the biggest remaining durable two-stop
  misses in one compact seam instead of stretching the generic stop penalty:
  - each loop family (`SOFT->MEDIUM->SOFT`, `SOFT->HARD->SOFT`,
    `MEDIUM->SOFT->MEDIUM`, `MEDIUM->HARD->MEDIUM`,
    `HARD->SOFT->HARD`, `HARD->MEDIUM->HARD`) can carry a small fitted
    adjustment
  - the current `long_non_medium`, `medium_high_pit_hot`, and
    `medium_high_pit_cool` leaves are the ones that earned materially
    different loop profiles on held-out history
- The scorer also adds a small opening commitment cost for one-stop MEDIUM
  starters in medium-length races. Held-out crossover errors showed those
  plans were still a bit too optimistic against mirrored alternatives, so the
  live model prices that opening commitment explicitly instead of trying to
  force the effect through a generic lap-progress term.
- Runtime now uses a learned, pruned deterministic gate tree over the existing
  expert model catalog instead of a hand-grown bucket list. The frozen runtime
  tree is intentionally small:
  - very short races route to `short_non_medium`
  - short warm races route to `short_warm`
  - short shoulder races route to `short_cool_mild`
  - cooler medium-long races route to `medium_high_pit_cool`
  - the main medium-long band routes to `medium_high_pit`
  - hotter medium-long races route to `medium_high_pit_hot`
  - cooler long-shoulder races route to `medium_cool_slow_cool`
  - the remaining longest races route to `long_non_medium`
- That tree is still fully deterministic and readable, but it is simpler than
  the old manual gate and was selected because it improved held-out exact order
  while reducing routing complexity.

## Ground Rules

These are the rules used while exploring and improving the solver. They are
worth keeping because they made the project more reliable and easier to evolve.

- Start from first principles:
  every change must answer one real question about strategy cost, not just add
  another tweak because it is easy to code.
- Keep the runtime seam clean:
  `race_simulator.py` and the submission path stay small, deterministic, and
  evaluator-safe. Heavy experiments belong in offline scripts.
- Prefer structural improvements over parameter churn:
  the biggest gains came from changing what the model can express, not from
  searching harder inside a weak formula.
- Use historical data as the main judge:
  the 100-case local suite is useful, but it is too small to be the main
  optimization target. Full held-out validation is the real commit gate.
- Treat the local suite as a guardrail:
  avoid regressions when possible, but do not overfit to it at the expense of
  broader historical validity.
- Keep learning narrow and disciplined:
  learned models should start as offline tools, then as small tie-breakers, and
  only become part of runtime after export and parity checks.
- Separate training from serving:
  `scikit-learn` is allowed offline, but submission runtime should stay pure
  Python unless there is a very strong reason not to.
- Make parity a hard requirement for exported models:
  if an exported pure-Python model does not reproduce the offline model closely,
  do not ship it.
- Keep failed experiments disposable:
  if an idea does not survive validation, remove it fully instead of leaving
  dead parameters, branches, or helper abstractions behind.
- Keep one source of truth per concern:
  routing lives in the runtime gate, scoring lives in the scorer, evaluation
  lives in the evaluation helpers, and submission validation lives outside the
  solver.
- Add checks for the truths that matter:
  self-checks protect scorer math, and historical regression checks protect the
  crossover and family-level behaviors the model must preserve.
- Prefer small, reversible steps:
  each experiment should be easy to explain, easy to validate, and easy to
  remove if it fails.

## Workflow

1. Update the scoring model in `race_solver/scoring.py` or parameters in `race_solver/parameters.py`.
2. Refit with `python solution/calibrate_model.py`.
   Quick iteration path:
   `--profile smoke` for correctness and wiring checks,
   `--profile fast` for trying ideas cheaply,
   `--profile medium` before spending a full run,
   and `--profile full` as the only commit-worthy gate.
   By default calibration now fits the current runtime eight-way split
   (`short_non_medium`, `short_warm`, `short_cool_mild`,
   `medium_high_pit_cool`, `medium_high_pit`, `medium_high_pit_hot`,
   `medium_cool_slow_cool`, `long_non_medium`).
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
5. Run local invariants with `python solution/run_self_checks.py`.
6. Smoke-test the submission seam with `python solution/verify_submission.py`.
   Add `--run-test-runner` when you want the full `./test_runner.sh` pass from
   the same script.
7. Run `python solution/run_local_suite.py` when your local environment does
   not have the shell tooling required by `./test_runner.sh`.
8. Explain a race with `python solution/explain_race.py < input.json`.
9. Compare a prediction with `python solution/analyze_case.py --input ... --expected ...`.
10. Analyze a whole suite with `python solution/analyze_suite.py`.
11. Mine historical strategy patterns with `python solution/analyze_historical_patterns.py`.
   Use `--split validation` to inspect held-out residuals before changing the model.
12. Guard high-support historical truths with
   `python solution/check_historical_regressions.py`.
   This keeps mirrored-family winner direction, major residual-bias signs, and
   runtime bucket value gains from regressing while iterating on the model.
13. Test learned rerankers offline with
   `python solution/train_hybrid_ranker.py --model-type close_pair`.
   The current promising hybrid shape is intentionally conservative:
   - the deterministic scorer still provides the baseline 20-driver order
   - the learned layer only considers very close adjacent pairs
   - mirrored one-stop arc pairs get a wider cost-gap gate than other pairs
     because that is the strongest repeated blocked-swap pattern in validation
   - it swaps them only when the classifier is confident enough
   This keeps the learned layer in the role of a tie-breaker instead of
   replacing the whole scoring model.
14. Export the chosen close-pair reranker with
   `python solution/export_hybrid_model.py`.
   This freezes the sklearn model into `race_solver/pair_reranker_trees.py`
   and validates bit-for-bit probability parity before runtime imports it.

## Backlog

- Residual visualization/export:
  add a lightweight path to export held-out residuals for heatmaps and scatter
  plots by strategy family, `total_laps`, `track_temp`, `pit_burden`, and
  `base_lap_time`.
- Normalized diagnostic views:
  use normalized or winsorized plots to compare context axes fairly, but keep
  full historical data in calibration and evaluation instead of dropping
  "outliers" from the deterministic target.

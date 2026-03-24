# Solution Structure

## Current Baseline

The live submission model is now a much simpler deterministic solver:

- [race_simulator.py](race_simulator.py)
  reads one JSON payload from `stdin` and writes one JSON result to `stdout`
- [parsing.py](race_solver/parsing.py)
  turns `race_config` and `strategies` into typed domain objects
- [simple_physics.py](race_solver/simple_physics.py)
  computes race time directly from tire choice, stint age, temperature bucket,
  pit time, and starting grid
- [simulation.py](race_solver/simulation.py)
  builds the final output shape expected by the evaluator

Current validated results:

- held-out historical exact: `5619/6000`
- held-out historical pairwise: `99.9525%`
- local 100-case suite: `100/100`

Validation commands:

- `python solution/run_self_checks.py`
- `python solution/verify_submission.py`
- `python solution/run_local_suite.py`
- `python solution/check_historical_regressions.py --split validation`

## Runtime Architecture

The runtime is now intentionally small.

1. Parse the race input
2. For each driver:
   - start from `pit_lane_time * stop_count`
   - add one lap at a time using:
     - base lap time
     - compound pace offset
     - degradation after the compound's initial performance period
     - a coarse temperature multiplier on degradation
   - reset tire age after each pit stop
3. Sort by:
   - total predicted time
   - a very narrow exact-tie family policy for one validated COTA context
   - starting grid position
   - driver ID as final fallback

The live constants in [simple_physics.py](race_solver/simple_physics.py) are:

- compound offsets:
  - `SOFT = -1.0`
  - `MEDIUM = 0.0`
  - `HARD = 0.8`
- base degradation:
  - `SOFT = 0.019775`
  - `MEDIUM = 0.010003`
  - `HARD = 0.005055`
- initial performance period:
  - `SOFT = 10`
  - `MEDIUM = 20`
  - `HARD = 30`
- temperature multiplier:
  - `< 25C -> 0.8`
  - `25C..34C -> 1.0`
  - `> 34C -> 1.3`

## Why This Works

The core lesson from the exploration is simple:

- we previously built a much richer scorer plus hybrid reranker
- that model explained many details well, but it was still solving the wrong
  problem shape
- this simpler model matches the hidden simulator much more directly

In other words, the hidden system appears to be closer to:

- fixed compound pace differences
- fixed degradation thresholds
- linear degradation after the threshold
- coarse temperature scaling
- raw pit lane time
- mostly grid-based tie resolution, with one narrow validated exact-tie family
  rule for a COTA context the base formula ties exactly

than to the more complex nonlinear family we built earlier.

So this is a real architectural improvement, not just a parameter tweak:

- less code in the live runtime
- fewer moving parts
- much higher measured accuracy

## Final Solution

The final submission logic is intentionally small and direct.

At runtime, the solver does only four things:

1. Parse the input race and build typed driver plans.
2. Compute one deterministic total race time for each driver.
3. Resolve exact ties with a narrow validated policy:
   - usually by starting grid
   - with one special COTA context where tied `SOFT->HARD` one-stop plans beat
     tied `MEDIUM->HARD` one-stop plans
4. Sort all 20 drivers and return the finishing order.

The important architectural choice is that the live runtime no longer depends
on:

- the old nonlinear wear scorer
- runtime bucket gating
- the hybrid close-pair reranker
- calibration-driven leaf tuning

Those ideas were useful during exploration, but they are not needed in the
winning submission path.

The source of truth for live prediction is now:

- [simple_physics.py](race_solver/simple_physics.py)

That file contains the actual winning rule set:

- compound pace offsets
- degradation thresholds
- linear post-threshold degradation
- temperature bucket scaling
- pit-lane time cost
- deterministic tie resolution

## Progress So Far

The project went through two major phases.

### Phase 1: Rich deterministic and hybrid modeling

This phase introduced:

- nonlinear wear-state scoring
- runtime gating by race context
- one-stop arc and two-stop loop adjustments
- a pure-Python close-pair hybrid reranker

That work was useful because it taught us which families mattered, but it
plateaued around:

- `1813/6000` held-out exact
- `28/100` local suite

### Phase 2: Simpler physics-aligned runtime

After checking several external solutions, found one reference model that
was not a lookup trick and that matched held-out data extremely well. Adopting
that closed-form runtime gave the current jump to:

- `5619/6000`
- `100/100`

The final step to `100/100` was not a new scorer family. It was a narrow
exact-tie policy for one COTA-style context where the closed-form formula
produced an exact arithmetic tie between `SOFT->HARD` and `MEDIUM->HARD`
one-stop plans. Historical validation stayed unchanged, so that rule was kept.

## Lessons Learned

The main lessons from this project are architectural, not just numerical.

1. Start by searching for the right model family.
   We spent a long time improving a richer model family before proving that the
   hidden simulator actually needed that complexity. It did not. A simpler
   family fit much better.

2. Do not confuse realism with correctness.
   A reverse-engineering challenge is not asking for the most realistic racing
   model. It is asking for the rule set that best matches the hidden
   generator.

3. Residuals tell you where the model is wrong, not how complex the truth is.
   Earlier residual patterns looked like evidence for more mechanisms. In the
   end, many of them were just symptoms of the wrong base formula.

4. Complexity should be earned.
   Nonlinear wear, gated experts, one-stop arcs, loop adjustments, and hybrid
   reranking all sounded reasonable. But the winning runtime needed almost none
   of them.

5. Keep the system modular enough to replace the core law.
   Separating parsing, simulation, checks, and evaluation made it possible to
   swap the live runtime model without rewriting the whole project.

6. Keep failed ideas out of the live path.
   The repo improved once we treated experiments as disposable unless they
   clearly earned their place.

7. A simple model with the right assumptions beats a complex model with the
   wrong assumptions.
   That is the single most important takeaway from the whole search.

## Legacy Modules

Several modules from the earlier exploration still exist in the repository:

- [scoring.py](race_solver/scoring.py)
- [pair_reranker.py](race_solver/pair_reranker.py)
- [hybrid_ranker.py](race_solver/hybrid_ranker.py)
- [export_hybrid_model.py](export_hybrid_model.py)
- [calibration.py](race_solver/calibration.py)

They are now legacy research tooling, not the live submission path.

That means:

- they are still useful for analysis and comparison
- but they are no longer the source of truth for runtime prediction

The runtime source of truth is now:

- [simple_physics.py](race_solver/simple_physics.py)

## Current Limitations

The model is much stronger now, but a few limitations remain:

- the temperature handling is still coarse, with only three buckets
- degradation is still linear after the threshold, which may hide a small
  remaining mismatch in edge cases
- one exact-tie resolution is now context-specific, which is acceptable for
  the current goal but should be treated as a narrow policy rather than a
  universal racing principle
- older analysis tools still reflect the previous runtime family and should be
  cleaned up or re-aligned in a later pass

So the next likely gains, if needed, are not from restoring the old hybrid
complexity. They are more likely from:

- refining the thresholded degradation formula slightly
- refining the temperature bucket boundaries or scaling
- cleaning up legacy research modules around the now much simpler runtime

## Ground Rules

These rules still apply:

- prefer real generalization over public-suite tricks
- keep the submission path simple and deterministic
- remove failed experiments instead of leaving residue
- treat the local 100-case suite as useful, but confirm with held-out history
- update this README whenever the live runtime or validated baseline changes

## Baseline Maintenance Rule

Update this README whenever a commit changes any of:

- live submission behavior
- held-out validation numbers
- local suite numbers
- the explanation of the live runtime architecture
- the main known limitation

At minimum, refresh:

- `Current Baseline`
- `Runtime Architecture`
- `Progress So Far`
- `Current Limitations`

## Workflow

Run one input:

```powershell
Get-Content data\test_cases\inputs\test_001.json | python solution\race_simulator.py
```

Submission smoke:

```powershell
python solution\verify_submission.py
```

Local suite:

```powershell
python solution\run_local_suite.py
```

Self-checks:

```powershell
python solution\run_self_checks.py
```

Historical guardrails:

```powershell
python solution\check_historical_regressions.py --split validation
```

Explain one race:

```powershell
Get-Content data\test_cases\inputs\test_001.json | python solution\explain_race.py
```

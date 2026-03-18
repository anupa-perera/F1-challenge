---
name: calibrate-solver
description: Run the F1 solver calibration pipeline. Use after modifying scoring.py or parameters.py.
allowed-tools: Bash, Read, Glob
---

# Calibrate Solver

Run the calibration pipeline with the requested profile.

## Usage

`/calibrate-solver [profile]` where profile is one of: `smoke`, `fast`, `medium`, `full`

## Steps

1. Run calibration:
   ```bash
   python solution/calibrate_model.py --profile $ARGUMENTS
   ```

2. Parse the output for:
   - Exact-match count (e.g., `1813/6000`)
   - Pairwise accuracy rate (e.g., `98.21%`)
   - Per-leaf fit results
   - Any warnings or errors

3. Report structured results:
   ```
   Profile: [profile]
   Historical Exact: [N]/6000
   Pairwise: [rate]%
   Status: SUCCESS/FAILURE
   Best parameters: [summary of changed params]
   ```

4. If profile is `full`, this is commit-worthy validation. Highlight whether
   the result beats the current baseline of 1813/6000 exact.

## Important

- `smoke` is for correctness/wiring checks only
- `fast` is for trying ideas cheaply
- `medium` is for pre-full-run sanity
- `full` is the ONLY commit-worthy gate
- Each active runtime leaf starts from its currently frozen parameters

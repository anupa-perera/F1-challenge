---
name: validate-solver
description: Run the full F1 solver validation suite. Use before any commit to verify no regressions.
allowed-tools: Bash, Read
---

# Validate Solver

Run the complete validation suite and report pass/fail for each check.

## Steps

Run these four commands in sequence. ALL must pass for a commit to be valid.

### 1. Self-checks (scorer math invariants)
```bash
python solution/run_self_checks.py
```

### 2. Submission seam smoke test
```bash
python solution/verify_submission.py
```

### 3. Local 100-case test suite
```bash
python solution/run_local_suite.py
```
Must score >= 28/100 (current baseline). Record exact count.

### 4. Historical regression checks (6000 held-out races)
```bash
python solution/check_historical_regressions.py --split validation
```
All regression guards must pass.

## Report

Output a structured summary:
```
Self-checks:        PASS/FAIL
Submission seam:    PASS/FAIL
Local suite:        [N]/100 (baseline: 28)
Historical regress: PASS/FAIL
Overall:            PASS/FAIL
```

## Baseline Reference

- Historical exact: 1813/6000
- Local suite: 28/100
- Pairwise: 98.2139%

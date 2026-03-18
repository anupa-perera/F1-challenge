---
name: analyze-residuals
description: Mine historical residual patterns to find modeling opportunities. Use before designing experiments.
allowed-tools: Bash, Read
---

# Analyze Residuals

Mine historical validation residuals to identify the highest-value modeling targets.

## Steps

### 1. Run historical pattern analysis
```bash
python solution/analyze_historical_patterns.py --split validation
```

### 2. Run suite failure analysis (if local suite data available)
```bash
python solution/analyze_suite.py
```

### 3. Summarize findings

Identify the top 5 residual patterns by frequency and magnitude. For each:

- **Family**: Which strategy family (e.g., MEDIUM->HARD / 1 stop)
- **Context**: Which runtime bucket (e.g., medium_high_pit)
- **Direction**: Is the model over-pricing or under-pricing?
- **Magnitude**: How many exact-match misses does this explain?
- **First-principles question**: What structural question about strategy cost does this suggest?

## Report Format

```
Pattern 1: [family] in [context]
  Direction: [over/under]-priced by ~[magnitude]
  Frequency: [N] races affected
  Question:  [first-principles hypothesis]

Pattern 2: ...
```

## Important

- Use `--split validation` to inspect held-out residuals only
- Do NOT modify any files — this is a read-only analysis
- The patterns guide experiment design, not direct parameter changes

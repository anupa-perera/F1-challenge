---
name: export-reranker
description: Train and export the hybrid close-pair reranker. Use after modifying hybrid_features.py.
allowed-tools: Bash, Read
---

# Export Reranker

Train the close-pair hybrid reranker offline and export it as a pure-Python artifact.

## Steps

### 1. Train the reranker offline
```bash
python solution/train_hybrid_ranker.py --model-type close_pair
```
Review the training output for:
- Validation accuracy / AUC
- Number of features used
- Any warnings about feature importance

### 2. Export to pure-Python artifact
```bash
python solution/export_hybrid_model.py
```
This freezes the sklearn model into `race_solver/pair_reranker_trees.py`.

### 3. Verify parity
The export script automatically validates bit-for-bit probability parity
between the sklearn model and the exported pure-Python trees.
If parity check fails, DO NOT proceed — the export is broken.

## Report

```
Training accuracy:  [value]
Export parity:      PASS/FAIL
Trees exported:     [count]
Features used:      [count]
Artifact:           race_solver/pair_reranker_trees.py
```

## Important

- scikit-learn is allowed offline but submission runtime must stay pure Python
- The exported model replaces `pair_reranker_trees.py` entirely
- Always verify parity before using the exported model in validation

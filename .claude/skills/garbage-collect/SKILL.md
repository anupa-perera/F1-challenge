---
name: garbage-collect
description: Clean up failed experiment branches and worktrees. Use after experiment evaluation.
allowed-tools: Bash
---

# Garbage Collect

Clean up experiment infrastructure after evaluation is complete.

## Steps

### 1. List all worktrees
```bash
git worktree list
```

### 2. Identify worktrees to remove
Keep only:
- The main working tree (f:/sideProjects/F1-Challenge)
- Any worktree explicitly marked as "winner" by the coordinator

Remove all others.

### 3. Remove losing/failed worktrees
For each worktree to remove:
```bash
git worktree remove <path> --force
```

### 4. Prune stale worktree references
```bash
git worktree prune
```

### 5. Clean up orphan branches
List experiment branches:
```bash
git branch --list "exp-*"
```

Delete non-winning experiment branches:
```bash
git branch -D <branch-name>
```

### 6. Verify clean state
```bash
git worktree list
git branch --list "exp-*"
git status
```

## Important

- NEVER delete the `main` branch
- NEVER delete the `feature/claude-agent-swarm` branch
- Only delete branches prefixed with `exp-` that were not merged
- Per README ground rules: "if an idea does not survive validation, remove it fully"

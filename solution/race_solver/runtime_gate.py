from __future__ import annotations

"""Deterministic runtime routing for context-gated model selection.

This module owns one responsibility: given a race configuration, choose the
fitted parameter set that should score it. Keeping that seam separate from the
parameter catalog makes the rest of the codebase easier to evolve:

- `parameters.py` stores fitted values and parameter guardrails
- `runtime_gate.py` stores routing rules and fallback relationships
- `scoring.py` only consumes the selected model
"""

from .models import GateLeafNode, GateNode, GateSplitNode, ModelParameters, RaceConfig
from .parameters import RUNTIME_MODEL_LIBRARY


def pit_burden(config: RaceConfig) -> float:
    """Normalize pit loss by lap time so tracks are comparable."""

    return config.pit_lane_time / config.base_lap_time


def gate_feature_value(config: RaceConfig, feature_name: str) -> float:
    """Expose the deterministic routing features used by the gate tree."""

    if feature_name == "total_laps":
        return float(config.total_laps)
    if feature_name == "track_temp":
        return float(config.track_temp)
    if feature_name == "base_lap_time":
        return config.base_lap_time
    if feature_name == "pit_burden":
        return pit_burden(config)
    raise KeyError(f"unknown gate feature: {feature_name}")


def _iter_gate_leaves(node: GateNode):
    if isinstance(node, GateLeafNode):
        yield node
        return
    yield from _iter_gate_leaves(node.left)
    yield from _iter_gate_leaves(node.right)


def gate_leaves_in_order(node: GateNode) -> tuple[GateLeafNode, ...]:
    """Return unique leaves in traversal order, even if a leaf is reused."""

    ordered: list[GateLeafNode] = []
    seen_contexts: set[str] = set()
    for leaf in _iter_gate_leaves(node):
        if leaf.context_key in seen_contexts:
            continue
        seen_contexts.add(leaf.context_key)
        ordered.append(leaf)
    return tuple(ordered)


def gate_leaf_for_config(config: RaceConfig, node: GateNode) -> GateLeafNode:
    """Traverse a deterministic gate tree until the matching leaf is reached."""

    current = node
    while isinstance(current, GateSplitNode):
        feature_value = gate_feature_value(config, current.feature_name)
        current = current.left if feature_value <= current.threshold else current.right
    return current


def _leaf(
    context_key: str,
    model: ModelParameters,
    *,
    fallback_context_key: str | None = None,
) -> GateLeafNode:
    return GateLeafNode(
        context_key=context_key,
        model=model,
        fallback_context_key=fallback_context_key,
    )


_SHORT_NON_MEDIUM_LEAF = _leaf(
    "short_non_medium",
    RUNTIME_MODEL_LIBRARY["short_non_medium"],
    fallback_context_key="short_non_medium",
)
_SHORT_WARM_LEAF = _leaf(
    "short_warm",
    RUNTIME_MODEL_LIBRARY["short_warm"],
    fallback_context_key="short_non_medium",
)
_MEDIUM_HIGH_PIT_LEAF = _leaf(
    "medium_high_pit",
    RUNTIME_MODEL_LIBRARY["medium_high_pit"],
    fallback_context_key="medium_high_pit",
)
_MEDIUM_COOL_SLOW_COOL_LEAF = _leaf(
    "medium_cool_slow_cool",
    RUNTIME_MODEL_LIBRARY["medium_cool_slow_cool"],
    fallback_context_key="long_non_medium",
)
_LONG_NON_MEDIUM_LEAF = _leaf(
    "long_non_medium",
    RUNTIME_MODEL_LIBRARY["long_non_medium"],
    fallback_context_key="long_non_medium",
)

RUNTIME_GATE_TREE: GateNode = GateSplitNode(
    feature_name="total_laps",
    threshold=38.5,
    left=GateSplitNode(
        feature_name="total_laps",
        threshold=37.5,
        left=GateSplitNode(
            feature_name="total_laps",
            threshold=27.5,
            left=_SHORT_NON_MEDIUM_LEAF,
            right=_SHORT_WARM_LEAF,
        ),
        right=_MEDIUM_HIGH_PIT_LEAF,
    ),
    right=GateSplitNode(
        feature_name="total_laps",
        threshold=56.5,
        left=GateSplitNode(
            feature_name="total_laps",
            threshold=53.5,
            left=_MEDIUM_HIGH_PIT_LEAF,
            right=_LONG_NON_MEDIUM_LEAF,
        ),
        right=GateSplitNode(
            feature_name="track_temp",
            threshold=25.0,
            left=_MEDIUM_COOL_SLOW_COOL_LEAF,
            right=_LONG_NON_MEDIUM_LEAF,
        ),
    ),
)

RUNTIME_CONTEXT_ORDER = tuple(
    leaf.context_key for leaf in gate_leaves_in_order(RUNTIME_GATE_TREE)
)

RUNTIME_MODEL_PARAMETERS = {
    leaf.context_key: leaf.model for leaf in gate_leaves_in_order(RUNTIME_GATE_TREE)
}

RUNTIME_FALLBACK_CONTEXT_BY_CHILD = {
    leaf.context_key: (
        leaf.fallback_context_key
        if leaf.fallback_context_key is not None
        else leaf.context_key
    )
    for leaf in gate_leaves_in_order(RUNTIME_GATE_TREE)
}


def runtime_context_key(config: RaceConfig) -> str:
    """Route a race through the frozen runtime gate tree."""

    return gate_leaf_for_config(config, RUNTIME_GATE_TREE).context_key


def runtime_model_for_config(config: RaceConfig) -> ModelParameters:
    """Return the frozen runtime model for the race's validated context bucket."""

    return gate_leaf_for_config(config, RUNTIME_GATE_TREE).model


def runtime_fallback_context_key(context_key: str) -> str:
    """Return the less-specialized runtime bucket used as the local fallback."""

    return RUNTIME_FALLBACK_CONTEXT_BY_CHILD[context_key]


def runtime_fallback_model_for_context_key(context_key: str) -> ModelParameters:
    """Return the model that would score the bucket if we removed that child."""

    return RUNTIME_MODEL_PARAMETERS[runtime_fallback_context_key(context_key)]

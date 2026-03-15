from __future__ import annotations

"""Parameter definitions and guardrails for the deterministic tire model."""

from dataclasses import replace

from .models import (
    CompoundParameters,
    GateLeafNode,
    GateNode,
    GateSplitNode,
    ModelParameters,
    RaceConfig,
)


# This is the strongest validated single-model baseline so far. Calibration
# still starts from this global fit even when the runtime uses a context-gated
# model, because it keeps one clean reference point for comparison.
DEFAULT_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.5,
            grace_laps=4,
            deg_rate=0.11,
            temp_pace_scale=0.075,
            temp_deg_scale=0.1,
            race_length_deg_scale=0.2,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.2,
            grace_laps=13,
            deg_rate=0.05,
            temp_pace_scale=0.0,
            temp_deg_scale=0.075,
            race_length_deg_scale=0.125,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=20,
            deg_rate=0.018,
            temp_pace_scale=0.0,
            temp_deg_scale=-0.025,
            race_length_deg_scale=0.175,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.0,
)


MEDIUM_COOL_SLOW_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.5,
            grace_laps=4,
            deg_rate=0.09,
            temp_pace_scale=0.05,
            temp_deg_scale=0.1,
            race_length_deg_scale=0.15,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.45,
            grace_laps=15,
            deg_rate=0.05,
            temp_pace_scale=-0.2,
            temp_deg_scale=0.2,
            race_length_deg_scale=-0.0,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=23,
            deg_rate=0.018,
            temp_pace_scale=0.05,
            temp_deg_scale=0.1,
            race_length_deg_scale=-0.1,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.175,
)


MEDIUM_COOL_SLOW_COOL_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.5,
            grace_laps=4,
            deg_rate=0.1,
            temp_pace_scale=-0.025,
            temp_deg_scale=0.15,
            race_length_deg_scale=0.15,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.55,
            grace_laps=15,
            deg_rate=0.05,
            temp_pace_scale=-0.175,
            temp_deg_scale=0.1,
            race_length_deg_scale=0.075,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=21,
            deg_rate=0.018,
            temp_pace_scale=0.0,
            temp_deg_scale=0.05,
            race_length_deg_scale=0.05,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.4,
)


MEDIUM_COOL_FAST_MID_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.45,
            grace_laps=4,
            deg_rate=0.09,
            temp_pace_scale=-0.0,
            temp_deg_scale=0.1,
            race_length_deg_scale=0.2,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.65,
            grace_laps=15,
            deg_rate=0.05,
            temp_pace_scale=0.05,
            temp_deg_scale=0.2,
            race_length_deg_scale=0.15,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=21,
            deg_rate=0.015,
            temp_pace_scale=0.0,
            temp_deg_scale=0.05,
            race_length_deg_scale=0.05,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.2,
)


MEDIUM_HIGH_PIT_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.5,
            grace_laps=5,
            deg_rate=0.12,
            temp_pace_scale=0.1,
            temp_deg_scale=0.075,
            race_length_deg_scale=0.2,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.35,
            grace_laps=14,
            deg_rate=0.05,
            temp_pace_scale=0.1,
            temp_deg_scale=0.025,
            race_length_deg_scale=0.2,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=23,
            deg_rate=0.025,
            temp_pace_scale=0.125,
            temp_deg_scale=0.025,
            race_length_deg_scale=0.15,
        ),
    },
    lap_progress_pace_scale=-0.025,
    post_stop_opening_bias_scale=0.025,
)


MEDIUM_HIGH_PIT_HOT_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.4,
            grace_laps=5,
            deg_rate=0.11,
            temp_pace_scale=0.075,
            temp_deg_scale=0.05,
            race_length_deg_scale=0.1,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.65,
            grace_laps=14,
            deg_rate=0.05,
            temp_pace_scale=0.15,
            temp_deg_scale=-0.0,
            race_length_deg_scale=0.2,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=20,
            deg_rate=0.018,
            temp_pace_scale=0.0,
            temp_deg_scale=-0.1,
            race_length_deg_scale=0.15,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.25,
)


MEDIUM_HIGH_PIT_HOT_FAST_SLOW_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.5,
            grace_laps=5,
            deg_rate=0.11,
            temp_pace_scale=0.15,
            temp_deg_scale=0.1,
            race_length_deg_scale=0.2,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.65,
            grace_laps=14,
            deg_rate=0.05,
            temp_pace_scale=-0.1,
            temp_deg_scale=0.05,
            race_length_deg_scale=0.125,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=21,
            deg_rate=0.018,
            temp_pace_scale=0.0,
            temp_deg_scale=-0.025,
            race_length_deg_scale=0.175,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.2,
)


MEDIUM_HIGH_PIT_HOT_FAST_SLOW_HOT_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.5,
            grace_laps=5,
            deg_rate=0.11,
            temp_pace_scale=0.175,
            temp_deg_scale=0.05,
            race_length_deg_scale=0.1,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.55,
            grace_laps=14,
            deg_rate=0.05,
            temp_pace_scale=0.05,
            temp_deg_scale=-0.0,
            race_length_deg_scale=0.15,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=21,
            deg_rate=0.018,
            temp_pace_scale=0.0,
            temp_deg_scale=-0.05,
            race_length_deg_scale=0.175,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.1,
)


MEDIUM_OTHER_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.5,
            grace_laps=4,
            deg_rate=0.085,
            temp_pace_scale=0.175,
            temp_deg_scale=0.1,
            race_length_deg_scale=0.125,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.6,
            grace_laps=15,
            deg_rate=0.045,
            temp_pace_scale=0.2,
            temp_deg_scale=-0.05,
            race_length_deg_scale=0.1,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=22,
            deg_rate=0.015,
            temp_pace_scale=0.15,
            temp_deg_scale=-0.025,
            race_length_deg_scale=0.2,
        ),
    },
    lap_progress_pace_scale=-0.125,
    post_stop_opening_bias_scale=0.025,
)


MEDIUM_OTHER_HOT_FAST_MID_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.5,
            grace_laps=5,
            deg_rate=0.1,
            temp_pace_scale=-0.05,
            temp_deg_scale=0.1,
            race_length_deg_scale=0.15,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.35,
            grace_laps=14,
            deg_rate=0.05,
            temp_pace_scale=0.2,
            temp_deg_scale=-0.0,
            race_length_deg_scale=0.125,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.4,
            grace_laps=21,
            deg_rate=0.018,
            temp_pace_scale=0.0,
            temp_deg_scale=-0.1,
            race_length_deg_scale=0.2,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.1,
)


MEDIUM_OTHER_HOT_FAST_MID_FAST_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.5,
            grace_laps=5,
            deg_rate=0.11,
            temp_pace_scale=0.2,
            temp_deg_scale=0.1,
            race_length_deg_scale=0.1,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.55,
            grace_laps=14,
            deg_rate=0.05,
            temp_pace_scale=0.15,
            temp_deg_scale=-0.0,
            race_length_deg_scale=0.125,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=21,
            deg_rate=0.018,
            temp_pace_scale=-0.05,
            temp_deg_scale=-0.025,
            race_length_deg_scale=-0.0,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.1,
)


MEDIUM_OTHER_HOT_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.3,
            grace_laps=5,
            deg_rate=0.11,
            temp_pace_scale=0.075,
            temp_deg_scale=0.1,
            race_length_deg_scale=0.2,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.55,
            grace_laps=14,
            deg_rate=0.05,
            temp_pace_scale=0.0,
            temp_deg_scale=0.075,
            race_length_deg_scale=0.125,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=21,
            deg_rate=0.018,
            temp_pace_scale=0.0,
            temp_deg_scale=-0.025,
            race_length_deg_scale=0.175,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.2,
)


SHORT_NON_MEDIUM_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.4,
            grace_laps=4,
            deg_rate=0.1,
            temp_pace_scale=-0.025,
            temp_deg_scale=-0.075,
            race_length_deg_scale=0.2,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.25,
            grace_laps=13,
            deg_rate=0.04,
            temp_pace_scale=0.025,
            temp_deg_scale=0.075,
            race_length_deg_scale=0.025,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=26,
            deg_rate=0.015,
            temp_pace_scale=0.0,
            temp_deg_scale=-0.025,
            race_length_deg_scale=0.125,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.0,
)


SHORT_COOL_MILD_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.4,
            grace_laps=5,
            deg_rate=0.12,
            temp_pace_scale=0.175,
            temp_deg_scale=0.05,
            race_length_deg_scale=0.2,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.25,
            grace_laps=14,
            deg_rate=0.05,
            temp_pace_scale=0.15,
            temp_deg_scale=-0.125,
            race_length_deg_scale=0.05,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=26,
            deg_rate=0.005,
            temp_pace_scale=-0.05,
            temp_deg_scale=0.15,
            race_length_deg_scale=-0.2,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.025,
)


SHORT_WARM_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.35,
            grace_laps=4,
            deg_rate=0.085,
            temp_pace_scale=0.2,
            temp_deg_scale=0.05,
            race_length_deg_scale=0.2,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.25,
            grace_laps=13,
            deg_rate=0.035,
            temp_pace_scale=-0.05,
            temp_deg_scale=0.2,
            race_length_deg_scale=0.05,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=26,
            deg_rate=0.01,
            temp_pace_scale=0.125,
            temp_deg_scale=-0.05,
            race_length_deg_scale=0.2,
        ),
    },
    lap_progress_pace_scale=0.025,
    post_stop_opening_bias_scale=-0.025,
)

LONG_NON_MEDIUM_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.5,
            grace_laps=4,
            deg_rate=0.11,
            temp_pace_scale=0.2,
            temp_deg_scale=0.1,
            race_length_deg_scale=0.2,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.2,
            grace_laps=13,
            deg_rate=0.05,
            temp_pace_scale=0.0,
            temp_deg_scale=0.075,
            race_length_deg_scale=0.125,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=20,
            deg_rate=0.018,
            temp_pace_scale=0.0,
            temp_deg_scale=-0.025,
            race_length_deg_scale=0.175,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.0,
)

def pit_burden(config: RaceConfig) -> float:
    """Normalize pit loss by lap time so tracks are comparable."""

    return config.pit_lane_time / config.base_lap_time


def gate_feature_value(config: RaceConfig, feature_name: str) -> float:
    """Expose the small set of deterministic routing features to gate trees."""

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


_MEDIUM_COOL_FAST_MID_LEAF = GateLeafNode(
    context_key="medium_cool_fast_mid",
    model=MEDIUM_COOL_FAST_MID_MODEL_PARAMETERS,
    fallback_context_key="medium_cool_slow",
)
_MEDIUM_COOL_SLOW_COOL_LEAF = GateLeafNode(
    context_key="medium_cool_slow_cool",
    model=MEDIUM_COOL_SLOW_COOL_MODEL_PARAMETERS,
    fallback_context_key="medium_cool_slow",
)
_MEDIUM_COOL_SLOW_LEAF = GateLeafNode(
    context_key="medium_cool_slow",
    model=MEDIUM_COOL_SLOW_MODEL_PARAMETERS,
    fallback_context_key="medium_cool_slow",
)
_MEDIUM_HIGH_PIT_HOT_FAST_SLOW_HOT_LEAF = GateLeafNode(
    context_key="medium_high_pit_hot_fast_slow_hot",
    model=MEDIUM_HIGH_PIT_HOT_FAST_SLOW_HOT_MODEL_PARAMETERS,
    fallback_context_key="medium_high_pit_hot_fast_slow",
)
_MEDIUM_HIGH_PIT_HOT_FAST_SLOW_LEAF = GateLeafNode(
    context_key="medium_high_pit_hot_fast_slow",
    model=MEDIUM_HIGH_PIT_HOT_FAST_SLOW_MODEL_PARAMETERS,
    fallback_context_key="medium_high_pit_hot",
)
_MEDIUM_HIGH_PIT_HOT_LEAF = GateLeafNode(
    context_key="medium_high_pit_hot",
    model=MEDIUM_HIGH_PIT_HOT_MODEL_PARAMETERS,
    fallback_context_key="medium_high_pit",
)
_MEDIUM_HIGH_PIT_LEAF = GateLeafNode(
    context_key="medium_high_pit",
    model=MEDIUM_HIGH_PIT_MODEL_PARAMETERS,
    fallback_context_key="medium_high_pit",
)
_MEDIUM_OTHER_HOT_FAST_MID_FAST_LEAF = GateLeafNode(
    context_key="medium_other_hot_fast_mid_fast",
    model=MEDIUM_OTHER_HOT_FAST_MID_FAST_MODEL_PARAMETERS,
    fallback_context_key="medium_other_hot_fast_mid",
)
_MEDIUM_OTHER_HOT_FAST_MID_LEAF = GateLeafNode(
    context_key="medium_other_hot_fast_mid",
    model=MEDIUM_OTHER_HOT_FAST_MID_MODEL_PARAMETERS,
    fallback_context_key="medium_other_hot",
)
_MEDIUM_OTHER_HOT_LEAF = GateLeafNode(
    context_key="medium_other_hot",
    model=MEDIUM_OTHER_HOT_MODEL_PARAMETERS,
    fallback_context_key="medium_other",
)
_MEDIUM_OTHER_LEAF = GateLeafNode(
    context_key="medium_other",
    model=MEDIUM_OTHER_MODEL_PARAMETERS,
    fallback_context_key="medium_other",
)
_SHORT_COOL_MILD_LEAF = GateLeafNode(
    context_key="short_cool_mild",
    model=SHORT_COOL_MILD_MODEL_PARAMETERS,
    fallback_context_key="short_non_medium",
)
_SHORT_WARM_LEAF = GateLeafNode(
    context_key="short_warm",
    model=SHORT_WARM_MODEL_PARAMETERS,
    fallback_context_key="short_non_medium",
)
_LONG_NON_MEDIUM_LEAF = GateLeafNode(
    context_key="long_non_medium",
    model=LONG_NON_MEDIUM_MODEL_PARAMETERS,
    fallback_context_key="long_non_medium",
)

RUNTIME_GATE_TREE: GateNode = GateSplitNode(
    feature_name="total_laps",
    threshold=36.0,
    left=GateSplitNode(
        feature_name="track_temp",
        threshold=28.0,
        left=_SHORT_COOL_MILD_LEAF,
        right=_SHORT_WARM_LEAF,
    ),
    right=GateSplitNode(
        feature_name="total_laps",
        threshold=52.0,
        left=GateSplitNode(
            feature_name="track_temp",
            threshold=25.0,
            left=GateSplitNode(
                feature_name="base_lap_time",
                threshold=90.0,
                left=_MEDIUM_COOL_FAST_MID_LEAF,
                right=GateSplitNode(
                    feature_name="track_temp",
                    threshold=22.0,
                    left=_MEDIUM_COOL_SLOW_LEAF,
                    right=_MEDIUM_COOL_SLOW_COOL_LEAF,
                ),
            ),
            right=GateSplitNode(
                feature_name="pit_burden",
                threshold=0.255,
                left=GateSplitNode(
                    feature_name="track_temp",
                    threshold=36.0,
                    left=_MEDIUM_OTHER_LEAF,
                    right=GateSplitNode(
                        feature_name="base_lap_time",
                        threshold=90.0,
                        left=GateSplitNode(
                            feature_name="base_lap_time",
                            threshold=84.999,
                            left=_MEDIUM_OTHER_HOT_FAST_MID_FAST_LEAF,
                            right=_MEDIUM_OTHER_HOT_FAST_MID_LEAF,
                        ),
                        right=_MEDIUM_OTHER_HOT_LEAF,
                    ),
                ),
                right=GateSplitNode(
                    feature_name="track_temp",
                    threshold=36.0,
                    left=_MEDIUM_HIGH_PIT_LEAF,
                    right=GateSplitNode(
                        feature_name="base_lap_time",
                        threshold=90.0,
                        left=GateSplitNode(
                            feature_name="base_lap_time",
                            threshold=84.999,
                            left=GateSplitNode(
                                feature_name="track_temp",
                                threshold=38.0,
                                left=_MEDIUM_HIGH_PIT_HOT_FAST_SLOW_HOT_LEAF,
                                right=_MEDIUM_HIGH_PIT_HOT_FAST_SLOW_LEAF,
                            ),
                            right=_MEDIUM_HIGH_PIT_HOT_LEAF,
                        ),
                        right=GateSplitNode(
                            feature_name="track_temp",
                            threshold=38.0,
                            left=_MEDIUM_HIGH_PIT_HOT_FAST_SLOW_HOT_LEAF,
                            right=_MEDIUM_HIGH_PIT_HOT_FAST_SLOW_LEAF,
                        ),
                    ),
                ),
            ),
        ),
        right=_LONG_NON_MEDIUM_LEAF,
    ),
)

RUNTIME_CONTEXT_ORDER = tuple(
    leaf.context_key for leaf in gate_leaves_in_order(RUNTIME_GATE_TREE)
)

RUNTIME_MODEL_PARAMETERS = {
    leaf.context_key: leaf.model for leaf in gate_leaves_in_order(RUNTIME_GATE_TREE)
}
# Local fallback models still matter for auditing whether a specialized child
# earns its complexity over the simpler leaf that would replace it.
RUNTIME_MODEL_PARAMETERS["short_non_medium"] = SHORT_NON_MEDIUM_MODEL_PARAMETERS

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


def replace_parameter(
    model: ModelParameters,
    compound: str | None,
    field_name: str,
    value: float | int,
) -> ModelParameters:
    """Return a new parameter object after changing a single scalar field."""

    if compound is None:
        return replace(model, **{field_name: value})

    replacement = replace(model.compounds[compound], **{field_name: value})
    return ModelParameters(
        compounds={
            **dict(model.compounds),
            compound: replacement,
        },
        lap_progress_pace_scale=model.lap_progress_pace_scale,
        post_stop_opening_bias_scale=model.post_stop_opening_bias_scale,
    )


def validate_model(model: ModelParameters) -> bool:
    """Enforce the basic "soft is faster but wears more" ordering assumptions."""

    compounds = model.compounds

    if not (
        compounds["SOFT"].pace_offset
        <= compounds["MEDIUM"].pace_offset
        <= compounds["HARD"].pace_offset
    ):
        return False

    if not (
        compounds["SOFT"].grace_laps
        <= compounds["MEDIUM"].grace_laps
        <= compounds["HARD"].grace_laps
    ):
        return False

    if not (
        compounds["SOFT"].deg_rate
        >= compounds["MEDIUM"].deg_rate
        >= compounds["HARD"].deg_rate
    ):
        return False

    return True


def model_to_dict(model: ModelParameters) -> dict[str, dict[str, float | int]]:
    return {
        "globals": {
            "lap_progress_pace_scale": model.lap_progress_pace_scale,
            "post_stop_opening_bias_scale": model.post_stop_opening_bias_scale,
        },
        "compounds": {
            compound: {
                "pace_offset": params.pace_offset,
                "grace_laps": params.grace_laps,
                "deg_rate": params.deg_rate,
                "temp_pace_scale": params.temp_pace_scale,
                "temp_deg_scale": params.temp_deg_scale,
                "race_length_deg_scale": params.race_length_deg_scale,
            }
            for compound, params in model.compounds.items()
        },
    }

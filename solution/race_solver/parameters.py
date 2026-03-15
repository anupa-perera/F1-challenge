from __future__ import annotations

"""Parameter definitions and guardrails for the deterministic tire model."""

from dataclasses import replace

from .models import CompoundParameters, ModelParameters, RaceConfig


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

RUNTIME_CONTEXT_ORDER = (
    "medium_cool_fast_mid",
    "medium_cool_slow_cool",
    "medium_cool_slow",
    "medium_high_pit_hot_fast_slow_hot",
    "medium_high_pit_hot_fast_slow",
    "medium_high_pit_hot",
    "medium_high_pit",
    "medium_other_hot_fast_mid_fast",
    "medium_other_hot_fast_mid",
    "medium_other_hot",
    "medium_other",
    "short_cool_mild",
    "short_warm",
    "long_non_medium",
)

RUNTIME_FALLBACK_CONTEXT_BY_CHILD = {
    # Fast/mid cool races only exist because the old cool fit underpriced them.
    # If we ever drop that specialization, they should fall back to the slower
    # cool fit that originally covered the whole parent bucket.
    "medium_cool_fast_mid": "medium_cool_slow",
    "medium_cool_slow_cool": "medium_cool_slow",
    "medium_cool_slow": "medium_cool_slow",
    # Hot high-pit races first split away from the broader high-pit parent, and
    # only then did the fast/slow edge cases earn their own child bucket.
    "medium_high_pit_hot_fast_slow_hot": "medium_high_pit_hot_fast_slow",
    "medium_high_pit_hot_fast_slow": "medium_high_pit_hot",
    "medium_high_pit_hot": "medium_high_pit",
    "medium_high_pit": "medium_high_pit",
    # The same logic applies to the non-high-pit hot branch.
    "medium_other_hot_fast_mid": "medium_other_hot",
    "medium_other_hot_fast_mid_fast": "medium_other_hot_fast_mid",
    "medium_other_hot": "medium_other",
    "medium_other": "medium_other",
    # Short non-medium races are the earned child; the long/global fit remains
    # the fallback that used to cover the entire non-medium parent.
    "short_cool_mild": "short_non_medium",
    "short_warm": "short_non_medium",
    "long_non_medium": "long_non_medium",
}


def pit_burden(config: RaceConfig) -> float:
    """Normalize pit loss by lap time so tracks are comparable."""

    return config.pit_lane_time / config.base_lap_time


def is_medium_length_race(config: RaceConfig) -> bool:
    """The current solver treats 37-52 laps as the unstable middle regime."""

    return 37 <= config.total_laps <= 52


def runtime_parent_context_key(config: RaceConfig) -> str:
    """Return the broad fallback bucket before any earned specialization.

    This keeps the architecture honest: every child bucket should have a clear
    parent regime that still makes sense on its own. If a child split stops
    earning its keep, we can merge it back into this fallback without changing
    the scorer itself.
    """

    if not is_medium_length_race(config):
        return "non_medium"
    if config.track_temp <= 25:
        return "medium_cool"
    if pit_burden(config) > 0.255:
        return "medium_high_pit"
    return "medium_other"


def runtime_context_key(config: RaceConfig) -> str:
    """Bucket races into the smallest context split that the data supports.

    The gate is intentionally hierarchical:
    - first choose a broad parent regime
    - then specialize only if the child split beat that parent on held-out data

    That lets us keep pruning weak buckets without losing coverage, because
    every specialized branch still has a valid parent fallback.
    """

    parent_key = runtime_parent_context_key(config)

    if parent_key == "medium_cool":
        if config.base_lap_time <= 90.0:
            return "medium_cool_fast_mid"
        if config.track_temp > 22:
            return "medium_cool_slow_cool"
        return "medium_cool_slow"
    if parent_key == "medium_high_pit":
        if config.track_temp >= 37:
            if config.base_lap_time < 85.0 or config.base_lap_time > 90.0:
                if config.track_temp <= 38:
                    return "medium_high_pit_hot_fast_slow_hot"
                return "medium_high_pit_hot_fast_slow"
            return "medium_high_pit_hot"
        return "medium_high_pit"
    if parent_key == "medium_other":
        if config.track_temp >= 37:
            if config.base_lap_time <= 90.0:
                if config.base_lap_time < 85.0:
                    return "medium_other_hot_fast_mid_fast"
                return "medium_other_hot_fast_mid"
            return "medium_other_hot"
        return "medium_other"
    if config.total_laps < 37:
        if config.track_temp <= 28:
            return "short_cool_mild"
        return "short_warm"
    return "long_non_medium"


RUNTIME_MODEL_PARAMETERS = {
    "medium_cool_fast_mid": MEDIUM_COOL_FAST_MID_MODEL_PARAMETERS,
    "medium_cool_slow_cool": MEDIUM_COOL_SLOW_COOL_MODEL_PARAMETERS,
    "medium_cool_slow": MEDIUM_COOL_SLOW_MODEL_PARAMETERS,
    "medium_high_pit_hot_fast_slow_hot": MEDIUM_HIGH_PIT_HOT_FAST_SLOW_HOT_MODEL_PARAMETERS,
    "medium_high_pit_hot_fast_slow": MEDIUM_HIGH_PIT_HOT_FAST_SLOW_MODEL_PARAMETERS,
    "medium_high_pit_hot": MEDIUM_HIGH_PIT_HOT_MODEL_PARAMETERS,
    "medium_high_pit": MEDIUM_HIGH_PIT_MODEL_PARAMETERS,
    "medium_other_hot_fast_mid_fast": MEDIUM_OTHER_HOT_FAST_MID_FAST_MODEL_PARAMETERS,
    "medium_other_hot_fast_mid": MEDIUM_OTHER_HOT_FAST_MID_MODEL_PARAMETERS,
    "medium_other_hot": MEDIUM_OTHER_HOT_MODEL_PARAMETERS,
    "medium_other": MEDIUM_OTHER_MODEL_PARAMETERS,
    # `short_non_medium` remains here as the local fallback for the two active
    # short-race children. Runtime leaf selection comes from `RUNTIME_CONTEXT_ORDER`.
    "short_non_medium": SHORT_NON_MEDIUM_MODEL_PARAMETERS,
    "short_cool_mild": SHORT_COOL_MILD_MODEL_PARAMETERS,
    "short_warm": SHORT_WARM_MODEL_PARAMETERS,
    "long_non_medium": LONG_NON_MEDIUM_MODEL_PARAMETERS,
}


def runtime_model_for_config(config: RaceConfig) -> ModelParameters:
    """Return the frozen runtime model for the race's validated context bucket."""

    return RUNTIME_MODEL_PARAMETERS[runtime_context_key(config)]


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

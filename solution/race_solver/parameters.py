from __future__ import annotations

"""Parameter definitions and guardrails for the deterministic tire model."""

from dataclasses import replace

from .models import CompoundParameters, ModelParameters


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
            pace_offset=-1.8,
            grace_laps=4,
            deg_rate=0.1,
            temp_pace_scale=-0.175,
            temp_deg_scale=0.1,
            race_length_deg_scale=0.15,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.8,
            grace_laps=15,
            deg_rate=0.05,
            temp_pace_scale=0.2,
            temp_deg_scale=0.1,
            race_length_deg_scale=0.075,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=21,
            deg_rate=0.018,
            temp_pace_scale=-0.05,
            temp_deg_scale=0.15,
            race_length_deg_scale=0.025,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.5,
)


MEDIUM_COOL_FAST_MID_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.45,
            grace_laps=4,
            deg_rate=0.09,
            temp_pace_scale=0.05,
            temp_deg_scale=0.1,
            race_length_deg_scale=0.15,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.75,
            grace_laps=15,
            deg_rate=0.05,
            temp_pace_scale=0.025,
            temp_deg_scale=0.2,
            race_length_deg_scale=0.1,
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
            pace_offset=-1.55,
            grace_laps=5,
            deg_rate=0.11,
            temp_pace_scale=0.2,
            temp_deg_scale=0.1,
            race_length_deg_scale=0.05,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.45,
            grace_laps=15,
            deg_rate=0.05,
            temp_pace_scale=-0.1,
            temp_deg_scale=0.1,
            race_length_deg_scale=-0.025,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.6,
            grace_laps=25,
            deg_rate=0.025,
            temp_pace_scale=0.05,
            temp_deg_scale=0.1,
            race_length_deg_scale=-0.075,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.025,
)


MEDIUM_HIGH_PIT_COOL_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.25,
            grace_laps=5,
            deg_rate=0.1,
            temp_pace_scale=0.2,
            temp_deg_scale=0.2,
            race_length_deg_scale=0.025,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.6,
            grace_laps=16,
            deg_rate=0.05,
            temp_pace_scale=-0.125,
            temp_deg_scale=0.2,
            race_length_deg_scale=-0.025,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.6,
            grace_laps=26,
            deg_rate=0.025,
            temp_pace_scale=0.075,
            temp_deg_scale=0.125,
            race_length_deg_scale=-0.1,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=-0.0,
)


MEDIUM_HIGH_PIT_HOT_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-0.9,
            grace_laps=5,
            deg_rate=0.11,
            temp_pace_scale=0.0,
            temp_deg_scale=0.0,
            race_length_deg_scale=0.1,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.7,
            grace_laps=15,
            deg_rate=0.05,
            temp_pace_scale=0.125,
            temp_deg_scale=-0.05,
            race_length_deg_scale=0.075,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.55,
            grace_laps=22,
            deg_rate=0.018,
            temp_pace_scale=-0.05,
            temp_deg_scale=-0.1,
            race_length_deg_scale=0.05,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.1,
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
            deg_rate=0.08,
            temp_pace_scale=-0.1,
            temp_deg_scale=-0.05,
            race_length_deg_scale=0.2,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.25,
            grace_laps=13,
            deg_rate=0.02,
            temp_pace_scale=0.025,
            temp_deg_scale=0.075,
            race_length_deg_scale=0.025,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=16,
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
            deg_rate=0.125,
            temp_pace_scale=-0.1,
            temp_deg_scale=-0.05,
            race_length_deg_scale=0.2,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.25,
            grace_laps=14,
            deg_rate=0.05,
            temp_pace_scale=0.2,
            temp_deg_scale=-0.0,
            race_length_deg_scale=0.1,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=23,
            deg_rate=0.005,
            temp_pace_scale=-0.0,
            temp_deg_scale=-0.2,
            race_length_deg_scale=-0.15,
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
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.05,
)

LONG_NON_MEDIUM_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-2.4,
            grace_laps=4,
            deg_rate=0.11,
            temp_pace_scale=-0.1,
            temp_deg_scale=0.075,
            race_length_deg_scale=0.2,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.2,
            grace_laps=13,
            deg_rate=0.05,
            temp_pace_scale=0.05,
            temp_deg_scale=0.075,
            race_length_deg_scale=0.1,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.55,
            grace_laps=20,
            deg_rate=0.018,
            temp_pace_scale=-0.1,
            temp_deg_scale=0.05,
            race_length_deg_scale=0.1,
        ),
    },
    lap_progress_pace_scale=0.0,
    post_stop_opening_bias_scale=0.1,
)


RUNTIME_MODEL_LIBRARY = {
    "medium_cool_fast_mid": MEDIUM_COOL_FAST_MID_MODEL_PARAMETERS,
    "medium_cool_slow_cool": MEDIUM_COOL_SLOW_COOL_MODEL_PARAMETERS,
    "medium_cool_slow": MEDIUM_COOL_SLOW_MODEL_PARAMETERS,
    "medium_high_pit_cool": MEDIUM_HIGH_PIT_COOL_MODEL_PARAMETERS,
    "medium_high_pit_hot_fast_slow_hot": MEDIUM_HIGH_PIT_HOT_FAST_SLOW_HOT_MODEL_PARAMETERS,
    "medium_high_pit_hot_fast_slow": MEDIUM_HIGH_PIT_HOT_FAST_SLOW_MODEL_PARAMETERS,
    "medium_high_pit_hot": MEDIUM_HIGH_PIT_HOT_MODEL_PARAMETERS,
    "medium_high_pit": MEDIUM_HIGH_PIT_MODEL_PARAMETERS,
    "medium_other_hot_fast_mid_fast": MEDIUM_OTHER_HOT_FAST_MID_FAST_MODEL_PARAMETERS,
    "medium_other_hot_fast_mid": MEDIUM_OTHER_HOT_FAST_MID_MODEL_PARAMETERS,
    "medium_other_hot": MEDIUM_OTHER_HOT_MODEL_PARAMETERS,
    "medium_other": MEDIUM_OTHER_MODEL_PARAMETERS,
    "short_non_medium": SHORT_NON_MEDIUM_MODEL_PARAMETERS,
    "short_cool_mild": SHORT_COOL_MILD_MODEL_PARAMETERS,
    "short_warm": SHORT_WARM_MODEL_PARAMETERS,
    "long_non_medium": LONG_NON_MEDIUM_MODEL_PARAMETERS,
}


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

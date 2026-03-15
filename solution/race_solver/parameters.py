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
)


MEDIUM_COOL_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.45,
            grace_laps=4,
            deg_rate=0.085,
            temp_pace_scale=0.05,
            temp_deg_scale=0.2,
            race_length_deg_scale=0.05,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.5,
            grace_laps=15,
            deg_rate=0.04,
            temp_pace_scale=-0.125,
            temp_deg_scale=0.15,
            race_length_deg_scale=0.05,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.45,
            grace_laps=23,
            deg_rate=0.015,
            temp_pace_scale=0.1,
            temp_deg_scale=0.125,
            race_length_deg_scale=0.125,
        ),
    },
    lap_progress_pace_scale=0.0,
)


MEDIUM_HIGH_PIT_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.5,
            grace_laps=5,
            deg_rate=0.12,
            temp_pace_scale=0.075,
            temp_deg_scale=0.075,
            race_length_deg_scale=0.15,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.45,
            grace_laps=14,
            deg_rate=0.05,
            temp_pace_scale=0.05,
            temp_deg_scale=-0.05,
            race_length_deg_scale=0.175,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=21,
            deg_rate=0.018,
            temp_pace_scale=0.0,
            temp_deg_scale=-0.025,
            race_length_deg_scale=0.2,
        ),
    },
    lap_progress_pace_scale=0.025,
)


MEDIUM_OTHER_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-1.5,
            grace_laps=5,
            deg_rate=0.115,
            temp_pace_scale=0.0,
            temp_deg_scale=0.05,
            race_length_deg_scale=0.1,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.4,
            grace_laps=14,
            deg_rate=0.045,
            temp_pace_scale=0.025,
            temp_deg_scale=0.05,
            race_length_deg_scale=0.175,
        ),
        "HARD": CompoundParameters(
            pace_offset=1.5,
            grace_laps=22,
            deg_rate=0.018,
            temp_pace_scale=0.025,
            temp_deg_scale=0.05,
            race_length_deg_scale=0.2,
        ),
    },
    lap_progress_pace_scale=0.025,
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
)


LONG_NON_MEDIUM_MODEL_PARAMETERS = DEFAULT_MODEL_PARAMETERS


RUNTIME_CONTEXT_ORDER = (
    "medium_cool",
    "medium_high_pit",
    "medium_other",
    "short_non_medium",
    "long_non_medium",
)


def runtime_context_key(config: RaceConfig) -> str:
    """Bucket races into the smallest context split that the data supports.

    The strongest residual signals after the nonlinear wear upgrade are that
    medium-length cool races behave differently from the rest of the medium
    pack, high pit-burden medium races also benefit from their own fit, and
    non-medium races no longer collapse short and long regimes into one bucket.
    """

    if 37 <= config.total_laps <= 52 and config.track_temp <= 25:
        return "medium_cool"
    if 37 <= config.total_laps <= 52 and (config.pit_lane_time / config.base_lap_time) > 0.255:
        return "medium_high_pit"
    if 37 <= config.total_laps <= 52:
        return "medium_other"
    if config.total_laps < 37:
        return "short_non_medium"
    return "long_non_medium"


RUNTIME_MODEL_PARAMETERS = {
    "medium_cool": MEDIUM_COOL_MODEL_PARAMETERS,
    "medium_high_pit": MEDIUM_HIGH_PIT_MODEL_PARAMETERS,
    "medium_other": MEDIUM_OTHER_MODEL_PARAMETERS,
    "short_non_medium": SHORT_NON_MEDIUM_MODEL_PARAMETERS,
    "long_non_medium": LONG_NON_MEDIUM_MODEL_PARAMETERS,
}


def runtime_model_for_config(config: RaceConfig) -> ModelParameters:
    """Return the frozen runtime model for the race's validated context bucket."""

    return RUNTIME_MODEL_PARAMETERS[runtime_context_key(config)]


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


def runtime_models_to_dict() -> dict[str, dict[str, dict[str, float | int]]]:
    return {
        context_key: model_to_dict(model)
        for context_key, model in RUNTIME_MODEL_PARAMETERS.items()
    }

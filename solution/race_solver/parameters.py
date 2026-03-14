from __future__ import annotations

"""Parameter definitions and guardrails for the v1 tire model."""

from dataclasses import replace

from .models import CompoundParameters, ModelParameters


# These values are the strongest validated default so far.
# Fresh-tire bonuses remain disabled, while the fitted model keeps a small
# lap-progress effect because calibration found a slight ordering benefit.
DEFAULT_MODEL_PARAMETERS = ModelParameters(
    compounds={
        "SOFT": CompoundParameters(
            pace_offset=-0.35,
            fresh_bonus=0.00,
            grace_laps=2,
            deg_rate=0.11,
            temp_pace_scale=0.15,
            temp_deg_scale=0.125,
            race_length_deg_scale=0.05,
        ),
        "MEDIUM": CompoundParameters(
            pace_offset=0.25,
            fresh_bonus=0.00,
            grace_laps=12,
            deg_rate=0.05,
            temp_pace_scale=0.075,
            temp_deg_scale=0.125,
            race_length_deg_scale=0.125,
        ),
        "HARD": CompoundParameters(
            pace_offset=0.45,
            fresh_bonus=0.00,
            grace_laps=16,
            deg_rate=0.018,
            temp_pace_scale=0.2,
            temp_deg_scale=-0.075,
            race_length_deg_scale=0.2,
        ),
    },
    fresh_tire_window=0,
    lap_progress_pace_scale=-0.025,
)


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
        fresh_tire_window=model.fresh_tire_window,
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

    if not (
        compounds["SOFT"].fresh_bonus
        <= compounds["MEDIUM"].fresh_bonus
        <= compounds["HARD"].fresh_bonus
    ):
        return False

    return True


def model_to_dict(model: ModelParameters) -> dict[str, dict[str, float | int]]:
    return {
        "globals": {
            "fresh_tire_window": model.fresh_tire_window,
            "lap_progress_pace_scale": model.lap_progress_pace_scale,
        },
        "compounds": {
            compound: {
                "pace_offset": params.pace_offset,
                "fresh_bonus": params.fresh_bonus,
                "grace_laps": params.grace_laps,
                "deg_rate": params.deg_rate,
                "temp_pace_scale": params.temp_pace_scale,
                "temp_deg_scale": params.temp_deg_scale,
                "race_length_deg_scale": params.race_length_deg_scale,
            }
            for compound, params in model.compounds.items()
        },
    }

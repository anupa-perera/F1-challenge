from __future__ import annotations

"""High-level race simulation entrypoint."""

from typing import Any

from .models import ModelParameters, RaceInput
from .parameters import DEFAULT_MODEL_PARAMETERS
from .scoring import predict_finishing_order


def simulate_race(
    race_input: RaceInput,
    model: ModelParameters = DEFAULT_MODEL_PARAMETERS,
) -> dict[str, Any]:
    return {
        "race_id": race_input.race_id,
        "finishing_positions": predict_finishing_order(
            config=race_input.config,
            driver_plans=race_input.driver_plans,
            model=model,
        ),
    }

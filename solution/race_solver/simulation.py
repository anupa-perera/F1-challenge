from __future__ import annotations

"""High-level race simulation entrypoint."""

from typing import Any

from .models import ModelParameters, RaceInput
from .pair_reranker import rerank_finishing_order


def simulate_race(
    race_input: RaceInput,
    model: ModelParameters | None = None,
) -> dict[str, Any]:
    return {
        "race_id": race_input.race_id,
        "finishing_positions": rerank_finishing_order(
            config=race_input.config,
            driver_plans=race_input.driver_plans,
            model=model,
        ),
    }

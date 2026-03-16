from __future__ import annotations

"""Pure-Python close-pair reranker for submission runtime.

The deterministic scorer still provides the primary 20-driver order. This
module only revisits very close adjacent pairs using an exported gradient
boosted tree model. Keeping the reranker narrow is what made the hybrid path
helpful instead of destructive.
"""

import math
import struct
from typing import Sequence

from .hybrid_features import extract_race_feature_rows
from .models import DriverPlan, ModelParameters, RaceConfig
from .scoring import predict_finishing_order

try:
    from .pair_reranker_trees import (
        BASELINE_SCORE,
        CONTEXT_FEATURE_INDEXES,
        COST_GAP_THRESHOLD,
        DELTA_FEATURE_INDEXES,
        MAX_PASSES,
        PLAN_FEATURE_INDEXES,
        SWAP_THRESHOLD,
        TREES,
    )

    HAS_PAIR_RERANKER = True
except ImportError:
    TREES = ()
    BASELINE_SCORE = 0.0
    COST_GAP_THRESHOLD = 0.0
    SWAP_THRESHOLD = 0.0
    MAX_PASSES = 0
    CONTEXT_FEATURE_INDEXES = ()
    PLAN_FEATURE_INDEXES = ()
    DELTA_FEATURE_INDEXES = ()
    HAS_PAIR_RERANKER = False


def _float32(value: float) -> float:
    """Round a Python float to sklearn's float32 feature representation."""

    return struct.unpack("f", struct.pack("f", float(value)))[0]


def _tree_leaf_value(
    tree_nodes: tuple[tuple[int, float, int, int, float], ...],
    pair_features: Sequence[float],
) -> float:
    index = 0
    while True:
        feature_idx, threshold, left_index, right_index, leaf_value = tree_nodes[index]
        if feature_idx < 0:
            return leaf_value
        index = left_index if pair_features[feature_idx] <= threshold else right_index


def predict_proba_left_ahead(pair_features: Sequence[float]) -> float:
    raw_score = BASELINE_SCORE
    for tree_nodes in TREES:
        raw_score += _tree_leaf_value(tree_nodes, pair_features)

    if raw_score >= 0.0:
        exp_value = math.exp(-raw_score)
        return 1.0 / (1.0 + exp_value)

    exp_value = math.exp(raw_score)
    return exp_value / (1.0 + exp_value)


def build_pair_features(
    left_vector: Sequence[float],
    right_vector: Sequence[float],
    *,
    cost_gap: float,
    rank_gap: int,
    left_rank: int,
    total_drivers: int,
    left_gap_from_prev: float,
    right_gap_to_next: float,
    left_gap_to_leader: float,
    right_gap_to_leader: float,
) -> list[float]:
    right_rank = left_rank + rank_gap
    rank_denominator = max(1, total_drivers - 1)
    pair_features: list[float] = []
    pair_features.extend(_float32(left_vector[index]) for index in CONTEXT_FEATURE_INDEXES)
    pair_features.extend(_float32(left_vector[index]) for index in PLAN_FEATURE_INDEXES)
    pair_features.extend(_float32(right_vector[index]) for index in PLAN_FEATURE_INDEXES)
    pair_features.extend(
        _float32(left_vector[index] - right_vector[index])
        for index in DELTA_FEATURE_INDEXES
    )
    pair_features.append(_float32(cost_gap))
    pair_features.append(_float32(float(rank_gap)))
    pair_features.append(_float32(left_rank / rank_denominator))
    pair_features.append(_float32(right_rank / rank_denominator))
    pair_features.append(_float32(left_gap_from_prev))
    pair_features.append(_float32(right_gap_to_next))
    pair_features.append(_float32(left_gap_to_leader))
    pair_features.append(_float32(right_gap_to_leader))
    return pair_features


def rerank_close_pairs(
    *,
    driver_ids: Sequence[str],
    feature_vectors: Sequence[Sequence[float]],
    strategy_costs: Sequence[float],
) -> list[str]:
    ordered_ids = list(driver_ids)
    vector_by_driver = {
        driver_id: tuple(feature_vector)
        for driver_id, feature_vector in zip(driver_ids, feature_vectors)
    }
    strategy_cost_by_driver = {
        driver_id: _float32(strategy_cost)
        for driver_id, strategy_cost in zip(driver_ids, strategy_costs)
    }
    leader_cost = min(strategy_cost_by_driver.values()) if strategy_cost_by_driver else 0.0

    for _ in range(MAX_PASSES):
        changed = False
        for position in range(len(ordered_ids) - 1):
            left_driver_id = ordered_ids[position]
            right_driver_id = ordered_ids[position + 1]
            left_cost = strategy_cost_by_driver[left_driver_id]
            right_cost = strategy_cost_by_driver[right_driver_id]
            cost_gap = (
                right_cost
                - left_cost
            )
            if cost_gap <= 0.0 or cost_gap > COST_GAP_THRESHOLD:
                continue

            left_gap_from_prev = (
                left_cost - strategy_cost_by_driver[ordered_ids[position - 1]]
                if position > 0
                else 1.0
            )
            right_gap_to_next = (
                strategy_cost_by_driver[ordered_ids[position + 2]] - right_cost
                if position + 2 < len(ordered_ids)
                else 1.0
            )

            probability_left_ahead = predict_proba_left_ahead(
                build_pair_features(
                    vector_by_driver[left_driver_id],
                    vector_by_driver[right_driver_id],
                    cost_gap=cost_gap,
                    rank_gap=1,
                    left_rank=position,
                    total_drivers=len(ordered_ids),
                    left_gap_from_prev=left_gap_from_prev,
                    right_gap_to_next=right_gap_to_next,
                    left_gap_to_leader=left_cost - leader_cost,
                    right_gap_to_leader=right_cost - leader_cost,
                )
            )
            if probability_left_ahead < SWAP_THRESHOLD:
                ordered_ids[position], ordered_ids[position + 1] = (
                    ordered_ids[position + 1],
                    ordered_ids[position],
                )
                changed = True

        if not changed:
            break

    return ordered_ids


def rerank_finishing_order(
    config: RaceConfig,
    driver_plans: Sequence[DriverPlan],
    *,
    model: ModelParameters | None = None,
) -> list[str]:
    baseline_order = predict_finishing_order(
        config=config,
        driver_plans=driver_plans,
        model=model,
    )
    if not HAS_PAIR_RERANKER:
        return baseline_order

    feature_rows = extract_race_feature_rows(config, tuple(driver_plans))
    row_by_driver = {row.driver_id: row for row in feature_rows}
    ordered_rows = [row_by_driver[driver_id] for driver_id in baseline_order]
    return rerank_close_pairs(
        driver_ids=[row.driver_id for row in ordered_rows],
        feature_vectors=[row.vector for row in ordered_rows],
        strategy_costs=[row.strategy_cost for row in ordered_rows],
    )

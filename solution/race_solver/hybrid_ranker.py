from __future__ import annotations

"""Offline linear hybrid ranker built on top of deterministic scorer features.

This module is intentionally split from the submission runtime. It lets us ask
whether a learned layer has real headroom before we decide to freeze anything
into the evaluator path.
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler

from .evaluation import (
    Evaluation,
    PAIRWISE_COMPARISONS_PER_RACE,
    evaluate_races,
    pairwise_correct_count,
)
from .historical_data import HistoricalRace
from .hybrid_features import FEATURE_NAMES, extract_race_feature_rows
from .scoring import predict_finishing_order


PAIR_LEFT_INDEX, PAIR_RIGHT_INDEX = np.triu_indices(20, 1)


@dataclass(frozen=True)
class RaceFeatureMatrix:
    race_id: str
    driver_ids: tuple[str, ...]
    actual_order: tuple[str, ...] | None
    strategy_costs: np.ndarray
    feature_matrix: np.ndarray


@dataclass(frozen=True)
class HybridLinearRankerModel:
    feature_names: tuple[str, ...]
    feature_means: tuple[float, ...]
    feature_scales: tuple[float, ...]
    weights: tuple[float, ...]


@dataclass(frozen=True)
class HybridLinearFitResult:
    model: HybridLinearRankerModel
    train_evaluation: Evaluation
    validation_evaluation: Evaluation
    baseline_validation_evaluation: Evaluation


@dataclass(frozen=True)
class HybridClosePairRankerModel:
    pair_feature_names: tuple[str, ...]
    cost_gap_threshold: float
    swap_threshold: float
    max_passes: int
    classifier: HistGradientBoostingClassifier


@dataclass(frozen=True)
class HybridClosePairFitResult:
    model: HybridClosePairRankerModel
    train_evaluation: Evaluation
    validation_evaluation: Evaluation
    baseline_validation_evaluation: Evaluation


def _actual_rank_vector(driver_ids: tuple[str, ...], actual_order: tuple[str, ...]) -> np.ndarray:
    actual_rank = {driver_id: index for index, driver_id in enumerate(actual_order)}
    return np.array([actual_rank[driver_id] for driver_id in driver_ids], dtype=np.int16)


def build_race_feature_matrices(
    races: Iterable[HistoricalRace],
) -> list[RaceFeatureMatrix]:
    matrices: list[RaceFeatureMatrix] = []
    for race in races:
        rows = extract_race_feature_rows(race.config, race.driver_plans)
        matrices.append(
            RaceFeatureMatrix(
                race_id=race.race_id,
                driver_ids=tuple(row.driver_id for row in rows),
                actual_order=race.actual_order,
                strategy_costs=np.array(
                    [row.strategy_cost for row in rows],
                    dtype=np.float32,
                ),
                feature_matrix=np.array(
                    [row.vector for row in rows],
                    dtype=np.float32,
                ),
            )
        )
    return matrices


CONTEXT_FEATURE_NAMES = {
    "total_laps_norm",
    "track_temp_norm",
    "base_lap_time_norm",
    "pit_burden_norm",
    "context_short_non_medium",
    "context_short_warm",
    "context_short_cool_mild",
    "context_medium_high_pit",
    "context_medium_high_pit_cool",
    "context_medium_high_pit_hot",
    "context_medium_cool_slow_cool",
    "context_long_non_medium",
}

PAIR_DELTA_FEATURE_NAMES = {
    "strategy_cost",
    "tire_penalty_time",
    "pit_stop_time",
    "additional_stop_time",
    "hard_loop_penalty_time",
    "one_stop_arc_time",
    "two_stop_loop_time",
    "opening_commitment_time",
    "stop_count",
    "first_stint_fraction",
    "second_stint_fraction",
    "third_stint_fraction",
    "soft_lap_fraction",
    "medium_lap_fraction",
    "hard_lap_fraction",
    "soft_wear_total",
    "medium_wear_total",
    "hard_wear_total",
    "soft_pace_total",
    "medium_pace_total",
    "hard_pace_total",
}

CONTEXT_FEATURE_INDEXES = tuple(
    index
    for index, feature_name in enumerate(FEATURE_NAMES)
    if feature_name in CONTEXT_FEATURE_NAMES
)
PLAN_FEATURE_INDEXES = tuple(
    index
    for index, feature_name in enumerate(FEATURE_NAMES)
    if feature_name not in CONTEXT_FEATURE_NAMES
)
DELTA_FEATURE_INDEXES = tuple(
    index
    for index, feature_name in enumerate(FEATURE_NAMES)
    if feature_name in PAIR_DELTA_FEATURE_NAMES
)
PAIR_FEATURE_NAMES = (
    tuple(f"context::{FEATURE_NAMES[index]}" for index in CONTEXT_FEATURE_INDEXES)
    + tuple(f"left::{FEATURE_NAMES[index]}" for index in PLAN_FEATURE_INDEXES)
    + tuple(f"right::{FEATURE_NAMES[index]}" for index in PLAN_FEATURE_INDEXES)
    + tuple(f"delta::{FEATURE_NAMES[index]}" for index in DELTA_FEATURE_INDEXES)
    + ("pair::strategy_cost_gap", "pair::baseline_rank_gap")
)


def _fit_scaler(training_matrices: list[RaceFeatureMatrix]) -> StandardScaler:
    scaler = StandardScaler()
    stacked = np.vstack([matrix.feature_matrix for matrix in training_matrices])
    scaler.fit(stacked)
    return scaler


def _scaled_matrices(
    matrices: list[RaceFeatureMatrix],
    scaler: StandardScaler,
) -> list[RaceFeatureMatrix]:
    return [
        RaceFeatureMatrix(
            race_id=matrix.race_id,
            driver_ids=matrix.driver_ids,
            actual_order=matrix.actual_order,
            strategy_costs=matrix.strategy_costs,
            feature_matrix=scaler.transform(matrix.feature_matrix).astype(np.float32),
        )
        for matrix in matrices
    ]


def _fit_pairwise_linear_model(
    training_matrices: list[RaceFeatureMatrix],
    *,
    alpha: float,
    epochs: int,
) -> np.ndarray:
    classifier = SGDClassifier(
        loss="log_loss",
        penalty="l2",
        alpha=alpha,
        fit_intercept=False,
        average=True,
        random_state=0,
    )
    classes = np.array([0, 1], dtype=np.int64)

    for _ in range(epochs):
        for matrix in training_matrices:
            if matrix.actual_order is None:
                continue
            actual_rank = _actual_rank_vector(matrix.driver_ids, matrix.actual_order)
            X_left = matrix.feature_matrix[PAIR_LEFT_INDEX]
            X_right = matrix.feature_matrix[PAIR_RIGHT_INDEX]
            y = (actual_rank[PAIR_LEFT_INDEX] < actual_rank[PAIR_RIGHT_INDEX]).astype(
                np.int64
            )
            classifier.partial_fit(
                X_left - X_right,
                y,
                classes=classes,
            )

    return classifier.coef_[0].astype(np.float32)


def _order_from_scores(
    driver_ids: tuple[str, ...],
    utilities: np.ndarray,
    strategy_costs: np.ndarray,
) -> tuple[str, ...]:
    ordered_indexes = sorted(
        range(len(driver_ids)),
        key=lambda index: (-float(utilities[index]), float(strategy_costs[index]), driver_ids[index]),
    )
    return tuple(driver_ids[index] for index in ordered_indexes)


def _baseline_order_indexes(matrix: RaceFeatureMatrix) -> list[int]:
    return sorted(
        range(len(matrix.driver_ids)),
        key=lambda index: (
            float(matrix.strategy_costs[index]),
            matrix.driver_ids[index],
        ),
    )


def _close_pair_feature_row(
    matrix: RaceFeatureMatrix,
    left_index: int,
    right_index: int,
    *,
    baseline_rank_gap: int,
) -> np.ndarray:
    left_row = matrix.feature_matrix[left_index]
    right_row = matrix.feature_matrix[right_index]
    return np.concatenate(
        (
            left_row[list(CONTEXT_FEATURE_INDEXES)],
            left_row[list(PLAN_FEATURE_INDEXES)],
            right_row[list(PLAN_FEATURE_INDEXES)],
            left_row[list(DELTA_FEATURE_INDEXES)] - right_row[list(DELTA_FEATURE_INDEXES)],
            np.array(
                [
                    float(matrix.strategy_costs[right_index] - matrix.strategy_costs[left_index]),
                    float(baseline_rank_gap),
                ],
                dtype=np.float32,
            ),
        )
    ).astype(np.float32)


def _actual_rank_lookup(actual_order: tuple[str, ...]) -> dict[str, int]:
    return {driver_id: index for index, driver_id in enumerate(actual_order)}


def _build_close_pair_dataset(
    matrices: list[RaceFeatureMatrix],
    *,
    cost_gap_threshold: float,
    max_rank_gap: int,
) -> tuple[np.ndarray, np.ndarray]:
    rows: list[np.ndarray] = []
    labels: list[int] = []

    for matrix in matrices:
        if matrix.actual_order is None:
            continue
        baseline_order = _baseline_order_indexes(matrix)
        actual_rank = _actual_rank_lookup(matrix.actual_order)
        for left_position, left_index in enumerate(baseline_order):
            max_right_position = min(
                len(baseline_order),
                left_position + max_rank_gap + 1,
            )
            for right_position in range(left_position + 1, max_right_position):
                right_index = baseline_order[right_position]
                strategy_cost_gap = float(
                    matrix.strategy_costs[right_index] - matrix.strategy_costs[left_index]
                )
                if strategy_cost_gap <= 0.0:
                    continue
                if strategy_cost_gap > cost_gap_threshold:
                    break
                rows.append(
                    _close_pair_feature_row(
                        matrix,
                        left_index,
                        right_index,
                        baseline_rank_gap=(right_position - left_position),
                    )
                )
                labels.append(
                    1
                    if actual_rank[matrix.driver_ids[left_index]]
                    < actual_rank[matrix.driver_ids[right_index]]
                    else 0
                )

    return (
        np.array(rows, dtype=np.float32),
        np.array(labels, dtype=np.int8),
    )


def predict_order_for_feature_matrix(
    matrix: RaceFeatureMatrix,
    model: HybridLinearRankerModel,
) -> tuple[str, ...]:
    means = np.array(model.feature_means, dtype=np.float32)
    scales = np.array(model.feature_scales, dtype=np.float32)
    weights = np.array(model.weights, dtype=np.float32)
    scaled = (matrix.feature_matrix - means) / scales
    utilities = scaled @ weights
    return _order_from_scores(matrix.driver_ids, utilities, matrix.strategy_costs)


def _evaluate_feature_matrices(
    matrices: list[RaceFeatureMatrix],
    model: HybridLinearRankerModel,
) -> Evaluation:
    exact_matches = 0
    pairwise_correct = 0
    for matrix in matrices:
        assert matrix.actual_order is not None
        predicted_order = predict_order_for_feature_matrix(matrix, model)
        if predicted_order == matrix.actual_order:
            exact_matches += 1
        pairwise_correct += pairwise_correct_count(
            actual_order=matrix.actual_order,
            predicted_order=predicted_order,
        )
    return Evaluation(
        exact_matches=exact_matches,
        race_count=len(matrices),
        pairwise_correct=pairwise_correct,
        pairwise_total=len(matrices) * PAIRWISE_COMPARISONS_PER_RACE,
    )


def fit_hybrid_linear_ranker(
    training_races: list[HistoricalRace],
    validation_races: list[HistoricalRace],
    *,
    alpha_grid: tuple[float, ...] = (1e-5, 3e-5, 1e-4, 3e-4),
    epochs: int = 6,
) -> HybridLinearFitResult:
    training_matrices = build_race_feature_matrices(training_races)
    validation_matrices = build_race_feature_matrices(validation_races)
    scaler = _fit_scaler(training_matrices)
    scaled_training_matrices = _scaled_matrices(training_matrices, scaler)

    baseline_evaluation = evaluate_races(
        validation_races,
        predictor=lambda race: predict_finishing_order(
            config=race.config,
            driver_plans=race.driver_plans,
        ),
    )

    best_result: HybridLinearFitResult | None = None
    for alpha in alpha_grid:
        weights = _fit_pairwise_linear_model(
            scaled_training_matrices,
            alpha=alpha,
            epochs=epochs,
        )
        model = HybridLinearRankerModel(
            feature_names=FEATURE_NAMES,
            feature_means=tuple(float(value) for value in scaler.mean_),
            feature_scales=tuple(
                float(value if value > 0 else 1.0)
                for value in scaler.scale_
            ),
            weights=tuple(float(value) for value in weights),
        )
        train_eval = _evaluate_feature_matrices(training_matrices, model)
        validation_eval = _evaluate_feature_matrices(validation_matrices, model)
        candidate = HybridLinearFitResult(
            model=model,
            train_evaluation=train_eval,
            validation_evaluation=validation_eval,
            baseline_validation_evaluation=baseline_evaluation,
        )
        if best_result is None or (
            candidate.validation_evaluation.exact_matches,
            candidate.validation_evaluation.pairwise_correct,
        ) > (
            best_result.validation_evaluation.exact_matches,
            best_result.validation_evaluation.pairwise_correct,
        ):
            best_result = candidate

    assert best_result is not None
    return best_result


def predict_order_for_close_pair_model(
    matrix: RaceFeatureMatrix,
    model: HybridClosePairRankerModel,
) -> tuple[str, ...]:
    ordered_indexes = _baseline_order_indexes(matrix)

    for _ in range(model.max_passes):
        changed = False
        for position in range(len(ordered_indexes) - 1):
            left_index = ordered_indexes[position]
            right_index = ordered_indexes[position + 1]
            strategy_cost_gap = float(
                matrix.strategy_costs[right_index] - matrix.strategy_costs[left_index]
            )
            if strategy_cost_gap <= 0.0:
                continue
            if strategy_cost_gap > model.cost_gap_threshold:
                continue

            pair_features = _close_pair_feature_row(
                matrix,
                left_index,
                right_index,
                baseline_rank_gap=1,
            ).reshape(1, -1)
            probability_left_ahead = float(
                model.classifier.predict_proba(pair_features)[0, 1]
            )
            if probability_left_ahead < model.swap_threshold:
                ordered_indexes[position], ordered_indexes[position + 1] = (
                    ordered_indexes[position + 1],
                    ordered_indexes[position],
                )
                changed = True
        if not changed:
            break

    return tuple(matrix.driver_ids[index] for index in ordered_indexes)


def _evaluate_close_pair_model(
    matrices: list[RaceFeatureMatrix],
    model: HybridClosePairRankerModel,
) -> Evaluation:
    exact_matches = 0
    pairwise_correct = 0
    for matrix in matrices:
        assert matrix.actual_order is not None
        predicted_order = predict_order_for_close_pair_model(matrix, model)
        if predicted_order == matrix.actual_order:
            exact_matches += 1
        pairwise_correct += pairwise_correct_count(
            actual_order=matrix.actual_order,
            predicted_order=predicted_order,
        )

    return Evaluation(
        exact_matches=exact_matches,
        race_count=len(matrices),
        pairwise_correct=pairwise_correct,
        pairwise_total=len(matrices) * PAIRWISE_COMPARISONS_PER_RACE,
    )


def fit_hybrid_close_pair_ranker(
    training_races: list[HistoricalRace],
    validation_races: list[HistoricalRace],
    *,
    cost_gap_grid: tuple[float, ...] = (0.08, 0.12, 0.18, 0.25),
    swap_threshold_grid: tuple[float, ...] = (0.42, 0.45, 0.48),
    max_rank_gap: int = 2,
    max_passes: int = 3,
    learning_rate: float = 0.05,
    max_iter: int = 250,
    max_leaf_nodes: int = 31,
    min_samples_leaf: int = 80,
) -> HybridClosePairFitResult:
    training_matrices = build_race_feature_matrices(training_races)
    validation_matrices = build_race_feature_matrices(validation_races)
    baseline_evaluation = evaluate_races(
        validation_races,
        predictor=lambda race: predict_finishing_order(
            config=race.config,
            driver_plans=race.driver_plans,
        ),
    )

    best_result: HybridClosePairFitResult | None = None

    for cost_gap_threshold in cost_gap_grid:
        X_train, y_train = _build_close_pair_dataset(
            training_matrices,
            cost_gap_threshold=cost_gap_threshold,
            max_rank_gap=max_rank_gap,
        )
        if len(X_train) == 0:
            continue

        classifier = HistGradientBoostingClassifier(
            learning_rate=learning_rate,
            max_iter=max_iter,
            max_leaf_nodes=max_leaf_nodes,
            min_samples_leaf=min_samples_leaf,
            random_state=0,
        )
        classifier.fit(X_train, y_train)

        for swap_threshold in swap_threshold_grid:
            model = HybridClosePairRankerModel(
                pair_feature_names=PAIR_FEATURE_NAMES,
                cost_gap_threshold=cost_gap_threshold,
                swap_threshold=swap_threshold,
                max_passes=max_passes,
                classifier=classifier,
            )
            train_eval = _evaluate_close_pair_model(training_matrices, model)
            validation_eval = _evaluate_close_pair_model(validation_matrices, model)
            candidate = HybridClosePairFitResult(
                model=model,
                train_evaluation=train_eval,
                validation_evaluation=validation_eval,
                baseline_validation_evaluation=baseline_evaluation,
            )
            if best_result is None or (
                candidate.validation_evaluation.exact_matches,
                candidate.validation_evaluation.pairwise_correct,
            ) > (
                best_result.validation_evaluation.exact_matches,
                best_result.validation_evaluation.pairwise_correct,
            ):
                best_result = candidate

    assert best_result is not None
    return best_result


def save_hybrid_linear_ranker(
    model: HybridLinearRankerModel,
    output_path: str | Path,
) -> None:
    path = Path(output_path)
    path.write_text(
        json.dumps(
            {
                "feature_names": list(model.feature_names),
                "feature_means": list(model.feature_means),
                "feature_scales": list(model.feature_scales),
                "weights": list(model.weights),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def load_hybrid_linear_ranker(
    input_path: str | Path,
) -> HybridLinearRankerModel:
    payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
    return HybridLinearRankerModel(
        feature_names=tuple(payload["feature_names"]),
        feature_means=tuple(payload["feature_means"]),
        feature_scales=tuple(payload["feature_scales"]),
        weights=tuple(payload["weights"]),
    )

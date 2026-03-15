from __future__ import annotations

"""Learn a small deterministic gate tree over the existing expert models.

The current solver already has a catalog of validated expert parameter sets.
This module searches for a compact routing tree that chooses between those
experts based on race context. That lets us improve routing without inventing
new tire parameters first.
"""

from dataclasses import dataclass
import json

from .evaluation import Evaluation, evaluate_races
from .historical_data import HistoricalRace
from .models import GateLeafNode, GateNode, GateSplitNode
from .parameters import RUNTIME_MODEL_LIBRARY
from .runtime_gate import gate_feature_value
from .scoring import predict_finishing_order


LEARNED_GATE_FEATURES = (
    "total_laps",
    "track_temp",
    "pit_burden",
    "base_lap_time",
)
LEARNED_GATE_MAX_DEPTH = 3
LEARNED_GATE_MAX_THRESHOLDS_PER_FEATURE = 8
LEARNED_GATE_MIN_TRAIN_LEAF = 120
LEARNED_GATE_MIN_VALIDATION_LEAF = 30


@dataclass(frozen=True)
class LearnedGateFitResult:
    tree: GateNode
    train_evaluation: Evaluation
    validation_evaluation: Evaluation
    leaf_model_keys: dict[str, str]

    @property
    def leaf_count(self) -> int:
        return len(self.leaf_model_keys)


def _is_better(candidate: Evaluation, incumbent: Evaluation) -> bool:
    return (
        candidate.exact_matches,
        candidate.pairwise_correct,
    ) > (
        incumbent.exact_matches,
        incumbent.pairwise_correct,
    )


def _merge_evaluations(left: Evaluation, right: Evaluation) -> Evaluation:
    return Evaluation(
        exact_matches=left.exact_matches + right.exact_matches,
        race_count=left.race_count + right.race_count,
        pairwise_correct=left.pairwise_correct + right.pairwise_correct,
        pairwise_total=left.pairwise_total + right.pairwise_total,
    )


def _prediction_for_model(
    race: HistoricalRace,
    model_key: str,
    prediction_cache: dict[tuple[str, str], tuple[str, ...]],
) -> tuple[str, ...]:
    cache_key = (model_key, race.race_id)
    cached = prediction_cache.get(cache_key)
    if cached is not None:
        return cached

    predicted_order = tuple(
        predict_finishing_order(
            config=race.config,
            driver_plans=race.driver_plans,
            model=RUNTIME_MODEL_LIBRARY[model_key],
        )
    )
    prediction_cache[cache_key] = predicted_order
    return predicted_order


def _evaluate_model_key(
    races: list[HistoricalRace],
    model_key: str,
    prediction_cache: dict[tuple[str, str], tuple[str, ...]],
) -> Evaluation:
    return evaluate_races(
        races,
        predictor=lambda race: _prediction_for_model(race, model_key, prediction_cache),
    )


def _select_best_model_key(
    training_races: list[HistoricalRace],
    validation_races: list[HistoricalRace],
    prediction_cache: dict[tuple[str, str], tuple[str, ...]],
) -> tuple[str, Evaluation, Evaluation]:
    best_model_key = next(iter(RUNTIME_MODEL_LIBRARY))
    best_train_eval = _evaluate_model_key(training_races, best_model_key, prediction_cache)
    best_validation_eval = _evaluate_model_key(
        validation_races,
        best_model_key,
        prediction_cache,
    )

    for model_key in tuple(RUNTIME_MODEL_LIBRARY)[1:]:
        train_eval = _evaluate_model_key(training_races, model_key, prediction_cache)
        validation_eval = _evaluate_model_key(validation_races, model_key, prediction_cache)
        if (
            train_eval.exact_matches,
            train_eval.pairwise_correct,
            validation_eval.exact_matches,
            validation_eval.pairwise_correct,
        ) > (
            best_train_eval.exact_matches,
            best_train_eval.pairwise_correct,
            best_validation_eval.exact_matches,
            best_validation_eval.pairwise_correct,
        ):
            best_model_key = model_key
            best_train_eval = train_eval
            best_validation_eval = validation_eval

    return best_model_key, best_train_eval, best_validation_eval


def _candidate_thresholds(
    races: list[HistoricalRace],
    feature_name: str,
) -> list[float]:
    values = sorted({gate_feature_value(race.config, feature_name) for race in races})
    if len(values) < 2:
        return []

    thresholds = [
        round((left + right) / 2.0, 6)
        for left, right in zip(values, values[1:])
        if right > left
    ]
    if len(thresholds) <= LEARNED_GATE_MAX_THRESHOLDS_PER_FEATURE:
        return thresholds

    last_index = len(thresholds) - 1
    picked_indexes = {
        round(
            position * last_index / (LEARNED_GATE_MAX_THRESHOLDS_PER_FEATURE - 1)
        )
        for position in range(LEARNED_GATE_MAX_THRESHOLDS_PER_FEATURE)
    }
    return [thresholds[index] for index in sorted(picked_indexes)]


def _split_races(
    races: list[HistoricalRace],
    feature_name: str,
    threshold: float,
) -> tuple[list[HistoricalRace], list[HistoricalRace]]:
    left: list[HistoricalRace] = []
    right: list[HistoricalRace] = []
    for race in races:
        if gate_feature_value(race.config, feature_name) <= threshold:
            left.append(race)
        else:
            right.append(race)
    return left, right


def _fit_node(
    training_races: list[HistoricalRace],
    validation_races: list[HistoricalRace],
    *,
    node_key: str,
    fallback_context_key: str | None,
    depth: int,
    prediction_cache: dict[tuple[str, str], tuple[str, ...]],
) -> LearnedGateFitResult:
    best_model_key, best_train_eval, best_validation_eval = _select_best_model_key(
        training_races,
        validation_races,
        prediction_cache,
    )
    leaf = GateLeafNode(
        context_key=node_key,
        model=RUNTIME_MODEL_LIBRARY[best_model_key],
        fallback_context_key=(
            node_key if fallback_context_key is None else fallback_context_key
        ),
    )
    best_result = LearnedGateFitResult(
        tree=leaf,
        train_evaluation=best_train_eval,
        validation_evaluation=best_validation_eval,
        leaf_model_keys={node_key: best_model_key},
    )

    if (
        depth >= LEARNED_GATE_MAX_DEPTH
        or len(training_races) < (2 * LEARNED_GATE_MIN_TRAIN_LEAF)
        or len(validation_races) < (2 * LEARNED_GATE_MIN_VALIDATION_LEAF)
    ):
        return best_result

    best_split: tuple[str, float, list[HistoricalRace], list[HistoricalRace], list[HistoricalRace], list[HistoricalRace]] | None = None
    best_split_train_eval: Evaluation | None = None
    best_split_validation_eval: Evaluation | None = None

    for feature_name in LEARNED_GATE_FEATURES:
        for threshold in _candidate_thresholds(training_races, feature_name):
            left_train, right_train = _split_races(training_races, feature_name, threshold)
            left_validation, right_validation = _split_races(
                validation_races,
                feature_name,
                threshold,
            )
            if (
                len(left_train) < LEARNED_GATE_MIN_TRAIN_LEAF
                or len(right_train) < LEARNED_GATE_MIN_TRAIN_LEAF
                or len(left_validation) < LEARNED_GATE_MIN_VALIDATION_LEAF
                or len(right_validation) < LEARNED_GATE_MIN_VALIDATION_LEAF
            ):
                continue

            _, left_train_eval, left_validation_eval = _select_best_model_key(
                left_train,
                left_validation,
                prediction_cache,
            )
            _, right_train_eval, right_validation_eval = _select_best_model_key(
                right_train,
                right_validation,
                prediction_cache,
            )
            split_train_eval = _merge_evaluations(left_train_eval, right_train_eval)
            split_validation_eval = _merge_evaluations(
                left_validation_eval,
                right_validation_eval,
            )
            if (
                best_split_validation_eval is None
                or (
                    split_validation_eval.exact_matches,
                    split_validation_eval.pairwise_correct,
                    split_train_eval.exact_matches,
                    split_train_eval.pairwise_correct,
                ) > (
                    best_split_validation_eval.exact_matches,
                    best_split_validation_eval.pairwise_correct,
                    best_split_train_eval.exact_matches if best_split_train_eval else -1,
                    best_split_train_eval.pairwise_correct if best_split_train_eval else -1,
                )
            ):
                best_split = (
                    feature_name,
                    threshold,
                    left_train,
                    right_train,
                    left_validation,
                    right_validation,
                )
                best_split_train_eval = split_train_eval
                best_split_validation_eval = split_validation_eval

    if best_split is None or not _is_better(
        best_split_validation_eval,
        best_result.validation_evaluation,
    ):
        return best_result

    (
        feature_name,
        threshold,
        left_train,
        right_train,
        left_validation,
        right_validation,
    ) = best_split

    left_result = _fit_node(
        left_train,
        left_validation,
        node_key=f"{node_key}_left",
        fallback_context_key=node_key,
        depth=depth + 1,
        prediction_cache=prediction_cache,
    )
    right_result = _fit_node(
        right_train,
        right_validation,
        node_key=f"{node_key}_right",
        fallback_context_key=node_key,
        depth=depth + 1,
        prediction_cache=prediction_cache,
    )

    recursive_result = LearnedGateFitResult(
        tree=GateSplitNode(
            feature_name=feature_name,
            threshold=threshold,
            left=left_result.tree,
            right=right_result.tree,
        ),
        train_evaluation=_merge_evaluations(
            left_result.train_evaluation,
            right_result.train_evaluation,
        ),
        validation_evaluation=_merge_evaluations(
            left_result.validation_evaluation,
            right_result.validation_evaluation,
        ),
        leaf_model_keys={
            **left_result.leaf_model_keys,
            **right_result.leaf_model_keys,
        },
    )
    if _is_better(recursive_result.validation_evaluation, best_result.validation_evaluation):
        return recursive_result
    return best_result


def fit_learned_gate_tree(
    training_races: list[HistoricalRace],
    validation_races: list[HistoricalRace],
) -> LearnedGateFitResult:
    """Learn a compact routing tree over the frozen expert model catalog."""

    return _fit_node(
        training_races,
        validation_races,
        node_key="learned_root",
        fallback_context_key=None,
        depth=0,
        prediction_cache={},
    )


def gate_tree_to_dict(
    node: GateNode,
    *,
    leaf_model_keys: dict[str, str],
) -> dict[str, object]:
    """Serialize a learned gate tree into readable JSON."""

    if isinstance(node, GateLeafNode):
        return {
            "type": "leaf",
            "context_key": node.context_key,
            "model_key": leaf_model_keys[node.context_key],
            "fallback_context_key": node.fallback_context_key,
        }

    return {
        "type": "split",
        "feature_name": node.feature_name,
        "threshold": node.threshold,
        "left": gate_tree_to_dict(node.left, leaf_model_keys=leaf_model_keys),
        "right": gate_tree_to_dict(node.right, leaf_model_keys=leaf_model_keys),
    }


def gate_tree_to_json(
    node: GateNode,
    *,
    leaf_model_keys: dict[str, str],
) -> str:
    return json.dumps(
        gate_tree_to_dict(node, leaf_model_keys=leaf_model_keys),
        indent=2,
        sort_keys=True,
    )

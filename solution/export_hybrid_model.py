#!/usr/bin/env python3
from __future__ import annotations

"""Train, validate, and export the close-pair hybrid reranker.

This script is intentionally offline-only. It uses sklearn to search for a
promising close-pair reranker, then freezes the chosen model into a plain
Python module that the submission runtime can import without sklearn.
"""

import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np

from race_solver.evaluation import pairwise_correct_count
from race_solver.historical_data import load_historical_races, split_races
from race_solver.hybrid_features import extract_race_feature_rows
from race_solver.hybrid_ranker import (
    CONTEXT_FEATURE_INDEXES,
    DELTA_FEATURE_INDEXES,
    PLAN_FEATURE_INDEXES,
    RaceFeatureMatrix,
    _build_close_pair_dataset,
    build_race_feature_matrices,
    fit_hybrid_close_pair_ranker,
    predict_order_for_close_pair_model,
)
from race_solver.parsing import parse_race_input
from race_solver.scoring import predict_finishing_order


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATED_MODEL_PATH = REPO_ROOT / "solution" / "race_solver" / "pair_reranker_trees.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-races", type=int, default=0)
    parser.add_argument(
        "--cost-gap-grid",
        default="0.06,0.08,0.10,0.12",
        help="comma-separated strategy-cost gap thresholds to search",
    )
    parser.add_argument(
        "--swap-threshold-grid",
        default="0.35,0.38,0.40",
        help="comma-separated close-pair swap thresholds to search",
    )
    parser.add_argument(
        "--max-passes-grid",
        default="1,2,3",
        help="comma-separated max-pass values to search",
    )
    parser.add_argument("--max-rank-gap", type=int, default=2)
    parser.add_argument("--max-iter", type=int, default=120)
    parser.add_argument("--max-leaf-nodes", type=int, default=15)
    parser.add_argument("--min-samples-leaf", type=int, default=60)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument(
        "--local-floor",
        type=int,
        default=0,
        help="minimum local-suite exact count required before export",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=GENERATED_MODEL_PATH,
    )
    return parser.parse_args()


def _parse_float_grid(raw_value: str) -> tuple[float, ...]:
    return tuple(float(value) for value in raw_value.split(",") if value.strip())


def _parse_int_grid(raw_value: str) -> tuple[int, ...]:
    return tuple(int(value) for value in raw_value.split(",") if value.strip())


def _matrix_for_payload(payload: dict) -> RaceFeatureMatrix:
    race_input = parse_race_input(payload)
    rows = extract_race_feature_rows(race_input.config, race_input.driver_plans)
    return RaceFeatureMatrix(
        race_id=race_input.race_id,
        driver_ids=tuple(row.driver_id for row in rows),
        actual_order=None,
        strategy_costs=np.array([row.strategy_cost for row in rows], dtype=np.float32),
        feature_matrix=np.array([row.vector for row in rows], dtype=np.float32),
    )


def _evaluate_local_suite(model) -> tuple[int, int]:
    input_dir = REPO_ROOT / "data" / "test_cases" / "inputs"
    expected_dir = REPO_ROOT / "data" / "test_cases" / "expected_outputs"
    exact_matches = 0
    case_count = 0

    for input_path in sorted(input_dir.glob("test_*.json")):
        case_count += 1
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        expected_order = tuple(
            json.loads((expected_dir / input_path.name).read_text(encoding="utf-8"))[
                "finishing_positions"
            ]
        )
        matrix = _matrix_for_payload(payload)
        predicted_order = predict_order_for_close_pair_model(matrix, model)
        if predicted_order == expected_order:
            exact_matches += 1

    return exact_matches, case_count


def _export_tree_nodes(classifier) -> tuple[tuple[tuple[int, float, int, int, float], ...], ...]:
    exported_trees = []
    for estimator_group in classifier._predictors:
        predictor = estimator_group[0]
        tree_rows = []
        for node in predictor.nodes:
            if bool(node["is_leaf"]):
                tree_rows.append(
                    (
                        -1,
                        0.0,
                        -1,
                        -1,
                        float(node["value"]),
                    )
                )
            else:
                tree_rows.append(
                    (
                        int(node["feature_idx"]),
                        float(node["num_threshold"]),
                        int(node["left"]),
                        int(node["right"]),
                        0.0,
                    )
                )
        exported_trees.append(tuple(tree_rows))
    return tuple(exported_trees)


def _eval_exported_tree(tree_nodes: tuple[tuple[int, float, int, int, float], ...], pair_features: Iterable[float]) -> float:
    row = pair_features
    index = 0
    while True:
        feature_idx, threshold, left_index, right_index, leaf_value = tree_nodes[index]
        if feature_idx < 0:
            return leaf_value
        index = left_index if row[feature_idx] <= threshold else right_index


def _predict_exported_probability(
    pair_features: np.ndarray,
    *,
    trees,
    baseline_score: float,
) -> float:
    raw_score = baseline_score
    feature_list = pair_features.tolist()
    for tree_nodes in trees:
        raw_score += _eval_exported_tree(tree_nodes, feature_list)
    if raw_score >= 0.0:
        exp_value = math.exp(-raw_score)
        return 1.0 / (1.0 + exp_value)
    exp_value = math.exp(raw_score)
    return exp_value / (1.0 + exp_value)


def _validate_export_parity(classifier, X_pairs: np.ndarray, trees) -> None:
    baseline_score = float(classifier._baseline_prediction[0][0])
    for pair_features in X_pairs:
        sklearn_probability = float(classifier.predict_proba(pair_features.reshape(1, -1))[0, 1])
        exported_probability = _predict_exported_probability(
            pair_features,
            trees=trees,
            baseline_score=baseline_score,
        )
        if not math.isclose(
            sklearn_probability,
            exported_probability,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise SystemExit(
                "exported tree parity check failed: "
                f"sklearn={sklearn_probability!r} exported={exported_probability!r}"
            )


def _module_literal(name: str, value) -> str:
    return f"{name} = {repr(value)}\n"


def _write_generated_module(
    *,
    output_path: Path,
    trees,
    model,
) -> None:
    classifier = model.classifier
    baseline_score = float(classifier._baseline_prediction[0][0])
    generated = [
        '"""Auto-generated close-pair reranker model.\n\n'
        "Generated by export_hybrid_model.py. Do not edit by hand.\n"
        '"""\n\n',
        _module_literal("TREES", trees),
        _module_literal("BASELINE_SCORE", baseline_score),
        _module_literal("LEARNING_RATE", float(classifier.learning_rate)),
        _module_literal("COST_GAP_THRESHOLD", float(model.cost_gap_threshold)),
        _module_literal("SWAP_THRESHOLD", float(model.swap_threshold)),
        _module_literal("MAX_PASSES", int(model.max_passes)),
        _module_literal("FEATURE_MEANS", ()),
        _module_literal("FEATURE_SCALES", ()),
        _module_literal("CONTEXT_FEATURE_INDEXES", tuple(int(index) for index in CONTEXT_FEATURE_INDEXES)),
        _module_literal("PLAN_FEATURE_INDEXES", tuple(int(index) for index in PLAN_FEATURE_INDEXES)),
        _module_literal("DELTA_FEATURE_INDEXES", tuple(int(index) for index in DELTA_FEATURE_INDEXES)),
    ]
    output_path.write_text("".join(generated), encoding="utf-8")


def main() -> None:
    args = parse_args()
    cost_gap_grid = _parse_float_grid(args.cost_gap_grid)
    swap_threshold_grid = _parse_float_grid(args.swap_threshold_grid)
    max_passes_grid = _parse_int_grid(args.max_passes_grid)

    all_races = load_historical_races(max_races=args.max_races)
    training_races, validation_races = split_races(all_races)
    print(
        f"loaded {len(all_races)} races "
        f"({len(training_races)} train / {len(validation_races)} validation)"
    )

    best_fit = None
    best_local_exact = -1
    local_case_count = 0

    for max_passes in max_passes_grid:
        for cost_gap in cost_gap_grid:
            for swap_threshold in swap_threshold_grid:
                fit_result = fit_hybrid_close_pair_ranker(
                    training_races=training_races,
                    validation_races=validation_races,
                    cost_gap_grid=(cost_gap,),
                    swap_threshold_grid=(swap_threshold,),
                    max_rank_gap=args.max_rank_gap,
                    max_passes=max_passes,
                    learning_rate=args.learning_rate,
                    max_iter=args.max_iter,
                    max_leaf_nodes=args.max_leaf_nodes,
                    min_samples_leaf=args.min_samples_leaf,
                )
                local_exact, local_case_count = _evaluate_local_suite(fit_result.model)
                base = fit_result.baseline_validation_evaluation
                val = fit_result.validation_evaluation
                print(
                    f"candidate passes={max_passes} gap={fit_result.model.cost_gap_threshold:.4f} "
                    f"swap={fit_result.model.swap_threshold:.4f} "
                    f"validation={val.exact_matches}/{val.race_count} "
                    f"(baseline {base.exact_matches}/{base.race_count}) "
                    f"local={local_exact}/{local_case_count}"
                )
                if local_exact < args.local_floor:
                    continue
                if best_fit is None or (
                    fit_result.validation_evaluation.exact_matches,
                    fit_result.validation_evaluation.pairwise_correct,
                    local_exact,
                ) > (
                    best_fit.validation_evaluation.exact_matches,
                    best_fit.validation_evaluation.pairwise_correct,
                    best_local_exact,
                ):
                    best_fit = fit_result
                    best_local_exact = local_exact

    if best_fit is None:
        raise SystemExit(
            f"no candidate satisfied local_floor={args.local_floor}"
        )

    training_matrices = build_race_feature_matrices(training_races)
    X_train_pairs, _ = _build_close_pair_dataset(
        training_matrices,
        cost_gap_threshold=best_fit.model.cost_gap_threshold,
        max_rank_gap=args.max_rank_gap,
    )
    trees = _export_tree_nodes(best_fit.model.classifier)
    _validate_export_parity(best_fit.model.classifier, X_train_pairs, trees)
    _write_generated_module(
        output_path=args.output,
        trees=trees,
        model=best_fit.model,
    )

    base = best_fit.baseline_validation_evaluation
    val = best_fit.validation_evaluation
    print("chosen_model:")
    print(f"  cost_gap_threshold={best_fit.model.cost_gap_threshold:.6f}")
    print(f"  swap_threshold={best_fit.model.swap_threshold:.6f}")
    print(f"  max_passes={best_fit.model.max_passes}")
    print(f"  validation_exact={val.exact_matches}/{val.race_count}")
    print(f"  baseline_exact={base.exact_matches}/{base.race_count}")
    print(f"  local_exact={best_local_exact}/{local_case_count}")
    print(f"  output={args.output}")
    print("export_parity: ok")


if __name__ == "__main__":
    main()

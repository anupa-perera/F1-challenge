#!/usr/bin/env python3
from __future__ import annotations

"""Train and evaluate offline hybrid ranking experiments."""

import argparse
import json
from pathlib import Path

import numpy as np

from race_solver.evaluation import Evaluation
from race_solver.historical_data import load_historical_races, split_races
from race_solver.hybrid_features import extract_race_feature_rows
from race_solver.hybrid_ranker import (
    HybridClosePairFitResult,
    HybridLinearRankerModel,
    RaceFeatureMatrix,
    fit_hybrid_close_pair_ranker,
    fit_hybrid_linear_ranker,
    predict_order_for_close_pair_model,
    predict_order_for_feature_matrix,
    save_hybrid_linear_ranker,
)
from race_solver.parsing import parse_race_input
from race_solver.scoring import predict_finishing_order


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-races", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument(
        "--alpha-grid",
        default="1e-5,3e-5,1e-4,3e-4",
        help="comma-separated alpha values for SGD logistic training",
    )
    parser.add_argument("--save-model", default="")
    parser.add_argument(
        "--model-type",
        choices=("linear", "close_pair"),
        default="linear",
    )
    parser.add_argument(
        "--cost-gap-grid",
        default="0.1",
        help="comma-separated close-pair cost gap thresholds",
    )
    parser.add_argument(
        "--swap-threshold-grid",
        default="0.38",
        help="comma-separated close-pair swap probability thresholds",
    )
    parser.add_argument("--max-rank-gap", type=int, default=1)
    parser.add_argument("--max-passes", type=int, default=1)
    parser.add_argument("--max-iter", type=int, default=120)
    parser.add_argument("--max-leaf-nodes", type=int, default=15)
    parser.add_argument("--min-samples-leaf", type=int, default=60)
    return parser.parse_args()


def _parse_alpha_grid(raw_value: str) -> tuple[float, ...]:
    return tuple(float(value) for value in raw_value.split(",") if value.strip())


def _parse_float_grid(raw_value: str) -> tuple[float, ...]:
    return tuple(float(value) for value in raw_value.split(",") if value.strip())


def _print_evaluation(label: str, evaluation: Evaluation) -> None:
    print(
        f"{label}: exact={evaluation.exact_matches}/{evaluation.race_count} "
        f"({evaluation.exact_rate:.2%}) "
        f"pairwise={evaluation.pairwise_rate:.4%}"
    )


def _print_top_weights(model: HybridLinearRankerModel, top: int = 20) -> None:
    rows = sorted(
        zip(model.feature_names, model.weights),
        key=lambda item: abs(item[1]),
        reverse=True,
    )
    print("top_weights:")
    for name, weight in rows[:top]:
        print(f"  {name}: {weight:+.6f}")


def _print_close_pair_model_summary(fit_result: HybridClosePairFitResult) -> None:
    model = fit_result.model
    print("close_pair_model:")
    print(f"  cost_gap_threshold: {model.cost_gap_threshold:.4f}")
    print(f"  swap_threshold: {model.swap_threshold:.4f}")
    print(f"  max_passes: {model.max_passes}")


def _matrix_for_race_input(payload: dict, expected_order: tuple[str, ...] | None = None) -> RaceFeatureMatrix:
    race_input = parse_race_input(payload)
    rows = extract_race_feature_rows(race_input.config, race_input.driver_plans)
    return RaceFeatureMatrix(
        race_id=race_input.race_id,
        driver_ids=tuple(row.driver_id for row in rows),
        actual_order=expected_order,
        strategy_costs=np.array(
            [row.strategy_cost for row in rows],
            dtype=np.float32,
        ),
        feature_matrix=np.array(
            [row.vector for row in rows],
            dtype=np.float32,
        ),
    )


def _evaluate_local_suite(
    model,
    *,
    model_type: str,
) -> tuple[int, int]:
    input_dir = Path("data/test_cases/inputs")
    expected_dir = Path("data/test_cases/expected_outputs")
    exact_matches = 0
    case_count = 0

    for input_path in sorted(input_dir.glob("test_*.json")):
        case_count += 1
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        expected_payload = json.loads(
            (expected_dir / input_path.name).read_text(encoding="utf-8")
        )
        expected_order = tuple(expected_payload["finishing_positions"])
        matrix = _matrix_for_race_input(payload, expected_order=expected_order)
        if model_type == "linear":
            predicted_order = predict_order_for_feature_matrix(matrix, model)
        else:
            predicted_order = predict_order_for_close_pair_model(matrix, model)
        if predicted_order == expected_order:
            exact_matches += 1

    return exact_matches, case_count


def _evaluate_local_baseline() -> tuple[int, int]:
    input_dir = Path("data/test_cases/inputs")
    expected_dir = Path("data/test_cases/expected_outputs")
    exact_matches = 0
    case_count = 0

    for input_path in sorted(input_dir.glob("test_*.json")):
        case_count += 1
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        race_input = parse_race_input(payload)
        predicted_order = tuple(
            predict_finishing_order(
                config=race_input.config,
                driver_plans=race_input.driver_plans,
            )
        )
        expected_order = tuple(
            json.loads((expected_dir / input_path.name).read_text(encoding="utf-8"))[
                "finishing_positions"
            ]
        )
        if predicted_order == expected_order:
            exact_matches += 1

    return exact_matches, case_count


def main() -> None:
    args = parse_args()
    alpha_grid = _parse_alpha_grid(args.alpha_grid)
    cost_gap_grid = _parse_float_grid(args.cost_gap_grid)
    swap_threshold_grid = _parse_float_grid(args.swap_threshold_grid)
    all_races = load_historical_races(max_races=args.max_races)
    training_races, validation_races = split_races(all_races)

    print(
        f"loaded {len(all_races)} races "
        f"({len(training_races)} train / {len(validation_races)} validation)"
    )
    print(f"model_type={args.model_type}")
    if args.model_type == "linear":
        print(f"epochs={args.epochs}")
        print(f"alpha_grid={alpha_grid}")
    else:
        print(f"cost_gap_grid={cost_gap_grid}")
        print(f"swap_threshold_grid={swap_threshold_grid}")
        print(f"max_rank_gap={args.max_rank_gap}")
        print(f"max_passes={args.max_passes}")
        print(f"max_iter={args.max_iter}")
        print(f"max_leaf_nodes={args.max_leaf_nodes}")
        print(f"min_samples_leaf={args.min_samples_leaf}")

    if args.model_type == "linear":
        fit_result = fit_hybrid_linear_ranker(
            training_races=training_races,
            validation_races=validation_races,
            alpha_grid=alpha_grid,
            epochs=args.epochs,
        )
        learned_model = fit_result.model
    else:
        fit_result = fit_hybrid_close_pair_ranker(
            training_races=training_races,
            validation_races=validation_races,
            cost_gap_grid=cost_gap_grid,
            swap_threshold_grid=swap_threshold_grid,
            max_rank_gap=args.max_rank_gap,
            max_passes=args.max_passes,
            max_iter=args.max_iter,
            max_leaf_nodes=args.max_leaf_nodes,
            min_samples_leaf=args.min_samples_leaf,
        )
        learned_model = fit_result.model

    _print_evaluation("baseline_validation", fit_result.baseline_validation_evaluation)
    _print_evaluation("hybrid_train", fit_result.train_evaluation)
    _print_evaluation("hybrid_validation", fit_result.validation_evaluation)
    if args.model_type == "linear":
        _print_top_weights(learned_model)
    else:
        _print_close_pair_model_summary(fit_result)

    baseline_local_exact, local_case_count = _evaluate_local_baseline()
    hybrid_local_exact, _ = _evaluate_local_suite(
        learned_model,
        model_type=args.model_type,
    )
    print(
        f"baseline_local: {baseline_local_exact}/{local_case_count} "
        f"({baseline_local_exact / local_case_count:.2%})"
    )
    print(
        f"hybrid_local: {hybrid_local_exact}/{local_case_count} "
        f"({hybrid_local_exact / local_case_count:.2%})"
    )

    if args.save_model and args.model_type == "linear":
        save_hybrid_linear_ranker(learned_model, args.save_model)
        print(f"saved_model={args.save_model}")


if __name__ == "__main__":
    main()

from __future__ import annotations

"""Offline search utilities for fitting the v1 deterministic tire model."""

import argparse
import json
from dataclasses import dataclass

from .historical_data import (
    HistoricalRace,
    deterministic_sample,
    load_historical_races,
    split_races,
)
from .models import COMPOUND_ORDER, ModelParameters
from .parameters import (
    DEFAULT_MODEL_PARAMETERS,
    model_to_dict,
    replace_parameter,
    validate_model,
)
from .scoring import predict_finishing_order


PAIRWISE_COMPARISONS_PER_RACE = 190
PARAMETER_BOUNDS = {
    "pace_offset": {
        "SOFT": (-1.5, 0.0),
        "MEDIUM": (-0.75, 0.75),
        "HARD": (0.0, 1.5),
    },
    "fresh_bonus": {
        "SOFT": (-0.40, 0.10),
        "MEDIUM": (-0.20, 0.10),
        "HARD": (-0.10, 0.10),
    },
    "grace_laps": {
        "SOFT": (2, 10),
        "MEDIUM": (6, 18),
        "HARD": (10, 26),
    },
    "deg_rate": {
        "SOFT": (0.02, 0.25),
        "MEDIUM": (0.01, 0.12),
        "HARD": (0.005, 0.08),
    },
    "temp_pace_scale": {compound: (-0.2, 0.2) for compound in COMPOUND_ORDER},
    "temp_deg_scale": {compound: (-0.2, 0.2) for compound in COMPOUND_ORDER},
    "race_length_deg_scale": {compound: (-0.2, 0.2) for compound in COMPOUND_ORDER},
    "fresh_tire_window": {None: (0, 8)},
    "lap_progress_pace_scale": {None: (-0.75, 0.75)},
}
COARSE_STEPS = {
    "pace_offset": 0.1,
    "fresh_bonus": 0.05,
    "grace_laps": 1,
    "deg_rate": 0.01,
    "temp_pace_scale": 0.05,
    "temp_deg_scale": 0.05,
    "race_length_deg_scale": 0.05,
    "fresh_tire_window": 1,
    "lap_progress_pace_scale": 0.05,
}
REFINE_STEPS = {
    "pace_offset": 0.05,
    "fresh_bonus": 0.025,
    "grace_laps": 1,
    "deg_rate": 0.005,
    "temp_pace_scale": 0.025,
    "temp_deg_scale": 0.025,
    "race_length_deg_scale": 0.025,
    "fresh_tire_window": 1,
    "lap_progress_pace_scale": 0.025,
}


@dataclass(frozen=True)
class Evaluation:
    exact_matches: int
    race_count: int
    pairwise_correct: int
    pairwise_total: int

    @property
    def exact_rate(self) -> float:
        if self.race_count == 0:
            return 0.0
        return self.exact_matches / self.race_count

    @property
    def pairwise_rate(self) -> float:
        if self.pairwise_total == 0:
            return 0.0
        return self.pairwise_correct / self.pairwise_total


@dataclass(frozen=True)
class SearchResult:
    final_model: ModelParameters
    checkpoints: tuple[ModelParameters, ...]


@dataclass(frozen=True)
class CalibrationProfile:
    max_races: int
    sample_size: int
    coarse_passes: int
    refine_passes: int


PROFILE_DEFAULTS = {
    "smoke": CalibrationProfile(
        max_races=1000,
        sample_size=250,
        coarse_passes=1,
        refine_passes=1,
    ),
    "fast": CalibrationProfile(
        max_races=5000,
        sample_size=800,
        coarse_passes=2,
        refine_passes=2,
    ),
    "medium": CalibrationProfile(
        max_races=12000,
        sample_size=1000,
        coarse_passes=2,
        refine_passes=3,
    ),
    "full": CalibrationProfile(
        max_races=0,
        sample_size=1200,
        coarse_passes=2,
        refine_passes=3,
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=tuple(PROFILE_DEFAULTS),
        default="full",
        help="Deterministic search budget profile used for staged experimentation.",
    )
    parser.add_argument("--sample-size", type=int, default=None)
    parser.add_argument("--coarse-passes", type=int, default=None)
    parser.add_argument("--refine-passes", type=int, default=None)
    parser.add_argument("--max-races", type=int, default=None)
    return parser.parse_args()


def resolve_profile(args: argparse.Namespace) -> CalibrationProfile:
    """Merge the named profile with any explicit command-line overrides."""

    profile = PROFILE_DEFAULTS[args.profile]
    return CalibrationProfile(
        max_races=profile.max_races if args.max_races is None else args.max_races,
        sample_size=profile.sample_size if args.sample_size is None else args.sample_size,
        coarse_passes=(
            profile.coarse_passes
            if args.coarse_passes is None
            else args.coarse_passes
        ),
        refine_passes=(
            profile.refine_passes
            if args.refine_passes is None
            else args.refine_passes
        ),
    )


def model_signature(model: ModelParameters) -> tuple[float | int, ...]:
    signature: list[float | int] = [
        model.fresh_tire_window,
        round(model.lap_progress_pace_scale, 6),
    ]
    for compound in COMPOUND_ORDER:
        params = model.compounds[compound]
        signature.extend(
            [
                round(params.pace_offset, 6),
                round(params.fresh_bonus, 6),
                params.grace_laps,
                round(params.deg_rate, 6),
                round(params.temp_pace_scale, 6),
                round(params.temp_deg_scale, 6),
                round(params.race_length_deg_scale, 6),
            ]
        )
    return tuple(signature)


def evaluate_model(
    races: list[HistoricalRace],
    model: ModelParameters,
    cache: dict[tuple[float | int, ...], Evaluation],
) -> Evaluation:
    signature = model_signature(model)
    cached = cache.get(signature)
    if cached is not None:
        return cached

    exact_matches = 0
    pairwise_correct = 0

    for race in races:
        predicted = predict_finishing_order(
            config=race.config,
            driver_plans=race.driver_plans,
            model=model,
        )
        if tuple(predicted) == race.actual_order:
            exact_matches += 1

        predicted_rank = {driver_id: index for index, driver_id in enumerate(predicted)}
        for index, left_driver in enumerate(race.actual_order):
            left_rank = predicted_rank[left_driver]
            for right_driver in race.actual_order[index + 1 :]:
                if left_rank < predicted_rank[right_driver]:
                    pairwise_correct += 1

    evaluation = Evaluation(
        exact_matches=exact_matches,
        race_count=len(races),
        pairwise_correct=pairwise_correct,
        pairwise_total=len(races) * PAIRWISE_COMPARISONS_PER_RACE,
    )
    cache[signature] = evaluation
    return evaluation


def is_better(candidate: Evaluation, incumbent: Evaluation, primary: str) -> bool:
    if primary == "pairwise":
        return (
            candidate.pairwise_correct,
            candidate.exact_matches,
        ) > (
            incumbent.pairwise_correct,
            incumbent.exact_matches,
        )

    return (
        candidate.exact_matches,
        candidate.pairwise_correct,
    ) > (
        incumbent.exact_matches,
        incumbent.pairwise_correct,
    )


def frange(start: float, stop: float, step: float) -> list[float]:
    values = []
    current = start
    while current <= stop + 1e-9:
        values.append(round(current, 6))
        current += step
    return values


def coarse_candidate_values(
    field_name: str,
    compound: str | None,
) -> list[float | int]:
    low, high = PARAMETER_BOUNDS[field_name][compound]
    step = COARSE_STEPS[field_name]
    if field_name in {"grace_laps", "fresh_tire_window"}:
        return list(range(int(low), int(high) + 1, int(step)))
    return frange(float(low), float(high), float(step))


def refine_candidate_values(
    current_value: float | int,
    field_name: str,
    compound: str | None,
) -> list[float | int]:
    low, high = PARAMETER_BOUNDS[field_name][compound]
    step = REFINE_STEPS[field_name]

    if field_name in {"grace_laps", "fresh_tire_window"}:
        values = {int(current_value)}
        for delta in (-2, -1, 1, 2):
            candidate = int(current_value) + delta
            if low <= candidate <= high:
                values.add(candidate)
        return sorted(values)

    values = {round(float(current_value), 6)}
    for delta in (-2, -1, 1, 2):
        candidate = float(current_value) + (delta * float(step))
        if low <= candidate <= high:
            values.add(round(candidate, 6))
    return sorted(values)


def append_checkpoint(
    checkpoints: list[ModelParameters],
    seen_signatures: set[tuple[float | int, ...]],
    model: ModelParameters,
) -> None:
    signature = model_signature(model)
    if signature in seen_signatures:
        return
    seen_signatures.add(signature)
    checkpoints.append(model)


def search_sequence() -> list[tuple[str | None, str]]:
    field_order = [
        "fresh_tire_window",
        "lap_progress_pace_scale",
        "pace_offset",
        "fresh_bonus",
        "grace_laps",
        "deg_rate",
        "temp_pace_scale",
        "temp_deg_scale",
        "race_length_deg_scale",
    ]
    sequence: list[tuple[str | None, str]] = []
    for field_name in field_order:
        if field_name in {"fresh_tire_window", "lap_progress_pace_scale"}:
            sequence.append((None, field_name))
            continue
        for compound in COMPOUND_ORDER:
            sequence.append((compound, field_name))
    return sequence


def coarse_search(
    training_sample: list[HistoricalRace],
    starting_model: ModelParameters,
    coarse_passes: int,
) -> SearchResult:
    current_model = starting_model
    cache: dict[tuple[float | int, ...], Evaluation] = {}
    current_eval = evaluate_model(training_sample, current_model, cache)
    checkpoints: list[ModelParameters] = []
    seen_signatures: set[tuple[float | int, ...]] = set()
    append_checkpoint(checkpoints, seen_signatures, current_model)

    for pass_index in range(coarse_passes):
        for compound, field_name in search_sequence():
            best_model = current_model
            best_eval = current_eval

            for value in coarse_candidate_values(field_name, compound):
                candidate_model = replace_parameter(current_model, compound, field_name, value)
                if not validate_model(candidate_model):
                    continue

                candidate_eval = evaluate_model(training_sample, candidate_model, cache)
                if is_better(candidate_eval, best_eval, primary="pairwise"):
                    best_model = candidate_model
                    best_eval = candidate_eval

            if best_model is not current_model:
                append_checkpoint(checkpoints, seen_signatures, best_model)
            current_model = best_model
            current_eval = best_eval

        print(
            f"[coarse pass {pass_index + 1}] "
            f"exact={current_eval.exact_matches}/{current_eval.race_count} "
            f"pairwise={current_eval.pairwise_rate:.4f}"
        )

    return SearchResult(final_model=current_model, checkpoints=tuple(checkpoints))


def refine_search(
    full_training: list[HistoricalRace],
    starting_model: ModelParameters,
    refine_passes: int,
) -> SearchResult:
    current_model = starting_model
    cache: dict[tuple[float | int, ...], Evaluation] = {}
    current_eval = evaluate_model(full_training, current_model, cache)
    checkpoints: list[ModelParameters] = []
    seen_signatures: set[tuple[float | int, ...]] = set()
    append_checkpoint(checkpoints, seen_signatures, current_model)

    for pass_index in range(refine_passes):
        improved = False

        for compound, field_name in search_sequence():
            if compound is None:
                current_value = getattr(current_model, field_name)
            else:
                current_value = getattr(current_model.compounds[compound], field_name)
            best_model = current_model
            best_eval = current_eval

            for value in refine_candidate_values(current_value, field_name, compound):
                candidate_model = replace_parameter(current_model, compound, field_name, value)
                if not validate_model(candidate_model):
                    continue

                candidate_eval = evaluate_model(full_training, candidate_model, cache)
                if is_better(candidate_eval, best_eval, primary="exact"):
                    best_model = candidate_model
                    best_eval = candidate_eval

            if best_model is not current_model:
                improved = True
                current_model = best_model
                current_eval = best_eval
                append_checkpoint(checkpoints, seen_signatures, current_model)

        print(
            f"[refine pass {pass_index + 1}] "
            f"exact={current_eval.exact_matches}/{current_eval.race_count} "
            f"pairwise={current_eval.pairwise_rate:.4f}"
        )

        if not improved:
            break

    return SearchResult(final_model=current_model, checkpoints=tuple(checkpoints))


def print_evaluation(label: str, evaluation: Evaluation) -> None:
    print(
        f"{label}: exact={evaluation.exact_matches}/{evaluation.race_count} "
        f"({evaluation.exact_rate:.4%}), "
        f"pairwise={evaluation.pairwise_correct}/{evaluation.pairwise_total} "
        f"({evaluation.pairwise_rate:.4%})"
    )


def select_validation_model(
    candidates: list[ModelParameters],
    training_races: list[HistoricalRace],
    validation_races: list[HistoricalRace],
) -> tuple[ModelParameters, Evaluation, Evaluation]:
    best_model = candidates[0]
    best_train_eval = evaluate_model(training_races, best_model, {})
    best_validation_eval = evaluate_model(validation_races, best_model, {})

    for candidate in candidates[1:]:
        candidate_train_eval = evaluate_model(training_races, candidate, {})
        candidate_validation_eval = evaluate_model(validation_races, candidate, {})
        if (
            candidate_validation_eval.exact_matches,
            candidate_validation_eval.pairwise_correct,
            candidate_train_eval.exact_matches,
            candidate_train_eval.pairwise_correct,
        ) > (
            best_validation_eval.exact_matches,
            best_validation_eval.pairwise_correct,
            best_train_eval.exact_matches,
            best_train_eval.pairwise_correct,
        ):
            best_model = candidate
            best_train_eval = candidate_train_eval
            best_validation_eval = candidate_validation_eval

    return best_model, best_train_eval, best_validation_eval


def main() -> None:
    args = parse_args()
    profile = resolve_profile(args)
    all_races = load_historical_races(max_races=profile.max_races)
    training_races, validation_races = split_races(all_races)
    sampled_training = deterministic_sample(training_races, sample_size=profile.sample_size)

    print(
        f"loaded {len(all_races)} races "
        f"({len(training_races)} train / {len(validation_races)} validation)"
    )
    print(
        "profile: "
        f"{args.profile} "
        f"(max_races={profile.max_races or 'all'}, "
        f"sample_size={profile.sample_size}, "
        f"coarse_passes={profile.coarse_passes}, "
        f"refine_passes={profile.refine_passes})"
    )
    print(f"coarse search sample size: {len(sampled_training)}")

    coarse_result = coarse_search(
        training_sample=sampled_training,
        starting_model=DEFAULT_MODEL_PARAMETERS,
        coarse_passes=profile.coarse_passes,
    )
    refine_result = refine_search(
        full_training=training_races,
        starting_model=coarse_result.final_model,
        refine_passes=profile.refine_passes,
    )
    candidate_models: list[ModelParameters] = []
    seen_signatures: set[tuple[float | int, ...]] = set()
    for candidate in (
        DEFAULT_MODEL_PARAMETERS,
        *coarse_result.checkpoints,
        *refine_result.checkpoints,
    ):
        append_checkpoint(candidate_models, seen_signatures, candidate)

    best_model, train_eval, validation_eval = select_validation_model(
        candidate_models,
        training_races=training_races,
        validation_races=validation_races,
    )

    print_evaluation("train", train_eval)
    print_evaluation("validation", validation_eval)
    print(f"validation_selected_from={len(candidate_models)} checkpoints")
    print("best_parameters=")
    print(json.dumps(model_to_dict(best_model), indent=2, sort_keys=True))

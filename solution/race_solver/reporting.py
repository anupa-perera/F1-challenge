from __future__ import annotations

"""Formatting helpers for readable race explanations and comparisons."""

from typing import Iterable, Sequence

from .models import DriverScoreBreakdown


def format_driver_breakdown(
    breakdown: DriverScoreBreakdown,
    *,
    position: int | None = None,
) -> list[str]:
    """Render one driver's score in a way that is easy to scan in the terminal."""

    prefix = f"{position:02d}. " if position is not None else ""
    lines = [
        (
            f"{prefix}{breakdown.driver_id}  total={breakdown.total_time:.3f}  "
            f"base={breakdown.base_race_time:.3f}  pit={breakdown.pit_stop_time:.3f}  "
            f"tire={breakdown.tire_penalty_time:.3f}"
        )
    ]
    for stint in breakdown.stints:
        lines.append(
            "    "
            f"{stint.compound:<6} laps {stint.start_lap:02d}-{stint.end_lap:02d}  "
            f"pace={stint.pace_total:.3f}  "
            f"(base={stint.base_pace_total:.3f}, progress={stint.progress_adjustment_total:.3f}, "
            f"restart={stint.opening_bias_total:.3f})  "
            f"wear={stint.wear_total:.3f}  "
            f"total={stint.total_penalty:.3f}"
        )
    return lines


def first_divergence(
    predicted_order: Sequence[str],
    expected_order: Sequence[str],
) -> tuple[int, str, str] | None:
    """Return the first position where predicted and expected orders diverge."""

    for index, (predicted_driver, expected_driver) in enumerate(
        zip(predicted_order, expected_order),
        start=1,
    ):
        if predicted_driver != expected_driver:
            return index, predicted_driver, expected_driver
    return None


def order_position_map(order: Sequence[str]) -> dict[str, int]:
    return {driver_id: index for index, driver_id in enumerate(order, start=1)}


def format_order_preview(
    predicted_order: Sequence[str],
    expected_order: Sequence[str] | None = None,
    *,
    limit: int = 10,
) -> list[str]:
    """Show the top of the predicted order, optionally alongside the expected one."""

    lines = []
    if expected_order is None:
        for index, driver_id in enumerate(predicted_order[:limit], start=1):
            lines.append(f"  {index:02d}. {driver_id}")
        return lines

    for index, (predicted_driver, expected_driver) in enumerate(
        zip(predicted_order[:limit], expected_order[:limit]),
        start=1,
    ):
        marker = "==" if predicted_driver == expected_driver else "!="
        lines.append(
            f"  {index:02d}. predicted={predicted_driver}  expected={expected_driver}  {marker}"
        )
    return lines


def format_focus_drivers(
    title: str,
    breakdowns: Iterable[DriverScoreBreakdown],
) -> list[str]:
    lines = [title]
    for breakdown in breakdowns:
        lines.extend(f"  {line}" for line in format_driver_breakdown(breakdown))
    return lines

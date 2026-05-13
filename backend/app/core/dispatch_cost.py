"""Dispatch cost model — calculates cost of rebalancing dispatch orders.

Phase D (v0.4): Cost-aware rebalancing adds operational realism:
- Each dispatch consumes budget (fixed truck fee + distance cost + per-bike cost)
- Only cost-effective dispatches are executed
- Daily dispatch budget limits total rebalancing activity
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DispatchCostParams:
    """Cost parameters for a single dispatch operation.

    Default values calibrated for abstract coord space:
    - fixed_cost: base truck dispatch fee (¥)
    - per_km_cost: cost per unit distance (¥ per abstract km)
    - per_bike_cost: handling cost per bike loaded/unloaded (¥)
    """

    fixed_cost: float = 10.0
    per_km_cost: float = 2.0
    per_bike_cost: float = 0.5


# ── Default global cost parameters ──────────────────────────────

DEFAULT_DISPATCH_COST = DispatchCostParams()
DEFAULT_DAILY_BUDGET = 500.0  # ¥ per day


@dataclass
class DispatchBudget:
    """Tracks daily dispatch budget consumption.

    Resets at the start of each simulation day.
    """

    daily_budget: float = DEFAULT_DAILY_BUDGET
    spent_today: float = 0.0
    current_day: int = -1

    def reset_if_new_day(self, day: int) -> None:
        """Reset spent counter if we've crossed into a new day."""
        if day > self.current_day:
            self.spent_today = 0.0
            self.current_day = day

    @property
    def remaining(self) -> float:
        return max(0.0, self.daily_budget - self.spent_today)

    @property
    def is_exhausted(self) -> bool:
        return self.remaining <= 0.0


def calculate_dispatch_cost(
    distance_km: float,
    n_bikes: int,
    params: DispatchCostParams | None = None,
) -> float:
    """Calculate the total cost of a single dispatch operation.

    Formula:
        total_cost = fixed_cost + distance_km × per_km_cost + n_bikes × per_bike_cost

    Args:
        distance_km: Distance between source and destination stations (km).
        n_bikes: Number of bikes being relocated.
        params: Cost parameters (defaults used if None).

    Returns:
        Total dispatch cost in ¥.
    """
    if params is None:
        params = DEFAULT_DISPATCH_COST
    return params.fixed_cost + distance_km * params.per_km_cost + n_bikes * params.per_bike_cost


def estimate_benefit(
    starvation_risk: float,
    n_bikes: int,
    base_value_per_bike: float = 15.0,
) -> float:
    """Estimate the benefit of delivering *n_bikes* to a starving station.

    Args:
        starvation_risk: How urgently bikes are needed (0.0 = fine, 1.0 = critical).
        n_bikes: Number of bikes being delivered.
        base_value_per_bike: Base value of having a bike available for rent.

    Returns:
        Estimated benefit in ¥.
    """
    return starvation_risk * n_bikes * base_value_per_bike

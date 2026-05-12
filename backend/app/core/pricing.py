"""Pricing engine — pure functions for trip revenue calculation.

Three preset pricing tiers are available. The ``PricingEngine.apply()``
function computes the revenue for a completed trip based on its distance
and the selected tier.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.core.finance import LedgerEntry, RevenueCategory


@dataclass(frozen=True)
class PricingTier:
    """A pricing plan with a per-30-minute rate."""

    name: str
    price_per_30min: float


# ── preset tiers ────────────────────────────────────────────────

PRO_PEOPLE = PricingTier(name="亲民", price_per_30min=1.0)
STANDARD = PricingTier(name="标准", price_per_30min=1.5)
PREMIUM = PricingTier(name="高端", price_per_30min=2.5)

ALL_TIERS: list[PricingTier] = [PRO_PEOPLE, STANDARD, PREMIUM]


# ── pricing engine ──────────────────────────────────────────────

_AVG_SPEED_KMH = 15.0  # average cycling speed used for duration estimate


class PricingEngine:
    """Pure-function pricing engine — stateless, no side effects."""

    @staticmethod
    def apply(
        trip_id: str,
        distance_km: float,
        tier: PricingTier,
        tick: int,
        *,
        entry_id_prefix: str = "rev",
        price_per_km: float | None = None,  # Phase C: per-station price override
    ) -> LedgerEntry:
        """Compute revenue for a completed trip.

        Two pricing modes:
        1. Standard: uses tier.price_per_30min (duration-based blocks)
        2. Per-km override (Phase C): uses distance_km × price_per_km

        Formula (standard):
            duration_30min = ceil(distance_km / avg_speed_kmh * 60 / 30)
            revenue = duration_30min * tier.price_per_30min

        Returns a single ``LedgerEntry`` with amount > 0 (revenue).
        """
        if distance_km <= 0 or (tier.price_per_30min <= 0 and price_per_km is None):
            return LedgerEntry(
                tick=tick,
                entry_id=f"{entry_id_prefix}-{tick}-{trip_id}",
                category=RevenueCategory.TRIP_INCOME,
                amount=0.0,
                trip_id=trip_id,
                description="zero-distance or zero-price trip",
            )

        if price_per_km is not None:
            # Phase C: per-km override pricing (player-set price)
            revenue = distance_km * price_per_km
            description = (
                f"trip {distance_km:.2f} km × ¥{price_per_km:.1f}/km (player override)"
            )
        else:
            # Standard: duration-based blocks
            duration_min = distance_km / _AVG_SPEED_KMH * 60
            blocks = max(1, math.ceil(duration_min / 30))
            revenue = blocks * tier.price_per_30min
            description = (
                f"trip {distance_km:.2f} km × {blocks} blocks × ¥{tier.price_per_30min}"
            )

        return LedgerEntry(
            tick=tick,
            entry_id=f"{entry_id_prefix}-{tick}-{trip_id}",
            category=RevenueCategory.TRIP_INCOME,
            amount=round(revenue, 2),
            trip_id=trip_id,
            description=description,
        )

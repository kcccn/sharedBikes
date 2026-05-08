"""Tests for the pricing engine (pricing.py)."""

from app.core.finance import RevenueCategory
from app.core.pricing import PREMIUM, PRO_PEOPLE, STANDARD, PricingEngine


def _apply(distance_km: float, tier, tick: int = 100) -> float:
    engine = PricingEngine()
    entry = engine.apply(
        trip_id="test-trip",
        distance_km=distance_km,
        tier=tier,
        tick=tick,
    )
    return entry.amount


# ── basic revenue calculation ───────────────────────────────────


def test_zero_distance() -> None:
    """Zero distance → zero revenue."""
    amount = _apply(0.0, STANDARD)
    assert amount == 0.0


def test_very_short_trip() -> None:
    """Very short trip (0.1 km) → minimum 1 block."""
    amount = _apply(0.1, STANDARD)
    # 0.1 km / 15 kmh * 60 = 0.4 min → ceil(0.4/30) = 1 block
    assert amount == 1.5


def test_typical_short_trip() -> None:
    """1 km trip → 4 min → 1 block."""
    amount = _apply(1.0, STANDARD)
    assert amount == 1.5


def test_typical_medium_trip() -> None:
    """3 km trip → 12 min → 1 block (still under 30 min)."""
    amount = _apply(3.0, STANDARD)
    assert amount == 1.5


def test_long_trip_two_blocks() -> None:
    """8 km trip → 32 min → 2 blocks."""
    amount = _apply(8.0, STANDARD)
    assert amount == 3.0  # 2 × ¥1.5


def test_long_trip_three_blocks() -> None:
    """15 km trip → 60 min → 2 blocks (60/30 = 2)."""
    amount = _apply(15.0, STANDARD)
    assert amount == 3.0


def test_long_trip_four_blocks() -> None:
    """16 km trip → 64 min → ceil(64/30) = 3 blocks."""
    amount = _apply(16.0, STANDARD)
    assert amount == 4.5  # 3 × ¥1.5


# ── different tiers ─────────────────────────────────────────────


def test_pro_people_tier() -> None:
    """亲民 tier: ¥1.0/30min."""
    amount = _apply(3.0, PRO_PEOPLE)
    assert amount == 1.0


def test_standard_tier() -> None:
    """标准 tier: ¥1.5/30min."""
    amount = _apply(3.0, STANDARD)
    assert amount == 1.5


def test_premium_tier() -> None:
    """高端 tier: ¥2.5/30min."""
    amount = _apply(3.0, PREMIUM)
    assert amount == 2.5


def test_premium_long_trip() -> None:
    """高端 + 8 km → 2 blocks × ¥2.5 = ¥5.0."""
    amount = _apply(8.0, PREMIUM)
    assert amount == 5.0


# ── entry metadata ──────────────────────────────────────────────


def test_entry_has_revenue_category() -> None:
    engine = PricingEngine()
    entry = engine.apply("tid", 3.0, STANDARD, 100)
    assert entry.category == RevenueCategory.TRIP_INCOME
    assert entry.is_revenue
    assert entry.trip_id == "tid"
    assert entry.tick == 100
    assert "tid" in entry.description

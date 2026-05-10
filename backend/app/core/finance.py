"""Financial ledger — immutable, append-only, chunked storage.

Implements the Ledger-First architecture for the Phase 2 economic system.
Every tick produces ``LedgerEntry`` records that are appended to the ledger.
The ledger is the **single source of truth** for all financial data.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Literal


class RevenueCategory(Enum):
    """Categories for revenue-generating entries."""

    TRIP_INCOME = "trip_income"
    DISPATCH_FEE = "dispatch_fee"
    SUBSCRIPTION = "subscription"
    ACHIEVEMENT_REWARD = "achievement_reward"


class CostCategory(Enum):
    """Categories for cost-bearing entries."""

    BIKE_MAINTENANCE = "bike_maintenance"
    STATION_LEASE = "station_lease"
    DISPATCH_COST = "dispatch_cost"
    OVERHEAD = "overhead"


# Union type for any valid category
Category = RevenueCategory | CostCategory


@dataclass(frozen=True)
class LedgerEntry:
    """A single immutable financial record produced each tick.

    ``amount`` is positive for revenue, negative for costs.
    The combination of ``tick`` + ``entry_id`` is globally unique.
    """

    tick: int
    entry_id: str
    category: Category
    amount: float
    trip_id: str | None = None
    description: str = ""

    @property
    def is_revenue(self) -> bool:
        return isinstance(self.category, RevenueCategory)

    @property
    def is_cost(self) -> bool:
        return isinstance(self.category, CostCategory)


@dataclass(frozen=True)
class Ledger:
    """Immutable, append-only financial ledger.

    Uses chunked internal storage so that each ``append`` is O(1)
    rather than O(n) — avoids the O(n²) trap of repeatedly copying
    a flat tuple.

    ``entries`` and ``query()`` lazily flatten chunks on access.
    """

    _chunks: tuple[tuple[LedgerEntry, ...], ...] = ()

    # ── public API ────────────────────────────────────────────────

    @property
    def entries(self) -> tuple[LedgerEntry, ...]:
        """All entries across all chunks (lazy flat view)."""
        return tuple(itertools.chain.from_iterable(self._chunks))

    def append(self, new_entries: list[LedgerEntry]) -> Ledger:
        """Return a new ledger with *new_entries* appended (O(1))."""
        return Ledger(_chunks=self._chunks + (tuple(new_entries),))

    def balance(self) -> float:
        """Net balance: sum of all entry amounts."""
        total = 0.0
        for chunk in self._chunks:
            for e in chunk:
                total += e.amount
        return total

    def query(
        self,
        tick_from: int | None = None,
        tick_to: int | None = None,
        category: Category | None = None,
    ) -> list[LedgerEntry]:
        """Query entries with optional tick range and category filter."""
        result: list[LedgerEntry] = []
        for chunk in self._chunks:
            for e in chunk:
                if tick_from is not None and e.tick < tick_from:
                    continue
                if tick_to is not None and e.tick > tick_to:
                    continue
                if category is not None and e.category != category:
                    continue
                result.append(e)
        return result

    def revenue_total(self, tick_from: int | None = None, tick_to: int | None = None) -> float:
        """Sum of all revenue entries in the given range."""
        return sum(
            e.amount
            for e in self.query(tick_from, tick_to)
            if e.is_revenue
        )

    def cost_total(self, tick_from: int | None = None, tick_to: int | None = None) -> float:
        """Sum of all cost entries (absolute value) in the given range."""
        return abs(sum(
            e.amount
            for e in self.query(tick_from, tick_to)
            if e.is_cost
        ))

    def profit(self, tick_from: int | None = None, tick_to: int | None = None) -> float:
        """Profit = revenue - costs for the given range."""
        return self.revenue_total(tick_from, tick_to) - self.cost_total(tick_from, tick_to)

    def __len__(self) -> int:
        """Total number of entries (fast — doesn't flatten)."""
        return sum(len(c) for c in self._chunks)

    def __bool__(self) -> bool:
        return len(self._chunks) > 0

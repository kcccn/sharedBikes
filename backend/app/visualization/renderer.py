"""Visualization service — heatmap and OD flow generation stubs."""

from __future__ import annotations

import random
from datetime import datetime, timezone


class HeatmapRenderer:
    """Generates heatmap data for dashboard visualization."""

    def generate(self, station_counts: dict[str, int]) -> list[dict]:
        """Stub: return random heatmap cells.

        TODO(phase-4): replace with real geo-spatial interpolation.
        """
        return [
            {
                "lat": 39.9042 + random.uniform(-0.01, 0.01),
                "lng": 116.4074 + random.uniform(-0.01, 0.01),
                "intensity": round(random.random(), 3),
            }
            for _ in range(20)
        ]


class FlowRenderer:
    """Generates OD flow lines for dashboard."""

    def generate(self, trips: list[dict]) -> list[dict]:
        """Stub: return random flow lines.

        TODO(phase-4): render real trip traces.
        """
        return [
            {
                "from_lat": 39.90,
                "from_lng": 116.40,
                "to_lat": 39.91,
                "to_lng": 116.41,
                "volume": random.randint(1, 20),
            }
            for _ in range(10)
        ]

"""
需求生成器。

基于时间、天气、事件生成骑行需求（起点 → 终点）。
核心假设：早晚高峰产生强方向性潮汐需求。
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from citybike.core.types import GeoPoint, Trip


@dataclass
class DemandProfile:
    """某区域的骑行需求特征。"""
    zone_id: str
    morning_peak_rate: float = 1.0    # 早高峰乘数
    evening_peak_rate: float = 1.0     # 晚高峰乘数
    residential_ratio: float = 0.5     # 居住属性（0=纯商业, 1=纯住宅）
    base_demand_per_hour: float = 10.0


class TripGenerator:
    """生成模拟骑行订单。"""

    def __init__(self, profiles: list[DemandProfile] | None = None) -> None:
        self.profiles: dict[str, DemandProfile] = {}
        if profiles:
            for p in profiles:
                self.profiles[p.zone_id] = p

    def generate(self, now: datetime, count: int) -> list[Trip]:
        """生成一批骑行订单。

        Args:
            now: 当前模拟时间。
            count: 生成的订单数量。

        Returns:
            订单列表。
        """
        trips: list[Trip] = []
        for i in range(count):
            trip = Trip(
                trip_id=f"trip-{now.strftime('%H%M%S')}-{i:04d}",
                bike_id="",
                rider_id=f"rider-{random.randint(1, 10000):05d}",
                start_time=now,
            )
            trips.append(trip)
        return trips

    def demand_multiplier(self, now: datetime) -> float:
        """基于时间计算需求乘数。

        早高峰 7-9 点：2.5x
        晚高峰 17-19 点：2.0x
        其他时段：1.0x
        """
        hour = now.hour
        if 7 <= hour < 9:
            return 2.5
        elif 17 <= hour < 19:
            return 2.0
        elif 12 <= hour < 14:
            return 1.3  # 午间小高峰
        return 1.0

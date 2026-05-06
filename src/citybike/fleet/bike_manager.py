"""
单车管理器。

负责单车投放、状态变更、查找可用车辆。
"""

from __future__ import annotations

import uuid

from citybike.core.types import Bike, BikeStatus, GeoPoint


class BikeManager:
    """单车生命周期管理。"""

    def __init__(self) -> None:
        self._bikes: dict[str, Bike] = {}

    def deploy(self, position: GeoPoint, count: int = 1) -> list[Bike]:
        """在指定位置投放单车。"""
        bikes: list[Bike] = []
        for _ in range(count):
            bike = Bike(
                bike_id=f"bike-{uuid.uuid4().hex[:8]}",
                status=BikeStatus.PARKED,
                position=position,
            )
            self._bikes[bike.bike_id] = bike
            bikes.append(bike)
        return bikes

    def find_nearest_available(
        self, position: GeoPoint, radius_m: float = 500.0
    ) -> Bike | None:
        """查找指定位置附近可用的单车（占位实现）。"""
        # TODO: 空间索引查询
        for bike in self._bikes.values():
            if bike.status in (BikeStatus.IDLE, BikeStatus.PARKED):
                return bike
        return None

    def get_bike(self, bike_id: str) -> Bike | None:
        return self._bikes.get(bike_id)

    @property
    def total(self) -> int:
        return len(self._bikes)

    @property
    def available(self) -> int:
        return sum(
            1 for b in self._bikes.values()
            if b.status in (BikeStatus.IDLE, BikeStatus.PARKED)
        )

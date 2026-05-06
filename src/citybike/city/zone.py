"""
运营区与禁停区管理。

定义运营商的投放区域、市政禁停区、推荐停放点（P点）。
"""

from __future__ import annotations

from shapely import Point, Polygon

from citybike.core.types import GeoPoint


class OperatingZone:
    """运营区：多边形区域，内含可投放/运营的单车。"""

    def __init__(self, zone_id: str, boundary: Polygon) -> None:
        self.zone_id = zone_id
        self.boundary = boundary
        self.label = ""

    def contains(self, point: GeoPoint) -> bool:
        return self.boundary.contains(Point(point.lng, point.lat))

    @property
    def area_sqkm(self) -> float:
        """占位：计算多边形面积（km²）。"""
        return self.boundary.area * 111_320**2  # 粗略估算


class RestrictedZone:
    """禁停区：禁止停放单车的区域。"""

    def __init__(self, zone_id: str, boundary: Polygon) -> None:
        self.zone_id = zone_id
        self.boundary = boundary
        self.fine_per_bike: float = 50.0  # 每辆违规停放罚款

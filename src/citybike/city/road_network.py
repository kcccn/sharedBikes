"""
道路网络模块。

从 OpenStreetMap 数据解析真实路网，构建 NetworkX 图结构，
用于路径规划（A* 寻路）和骑行距离计算。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx

from citybike.core.types import GeoPoint


class RoadNetwork:
    """基于真实路网的有向图。

    节点 = 路口 / OSM 节点 (GeoPoint)
    边   = 道路段（含长度、坡度、骑行难度等属性）
    """

    def __init__(self) -> None:
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()

    def load_osm(self, filepath: str | Path) -> None:
        """从 OSM 文件加载路网（占位：待实现 OSM 解析器）。"""
        # TODO: 实现 OSM XML/PBF 解析，提取道路并建图
        raise NotImplementedError("OSM parser not yet implemented")

    def shortest_path(
        self,
        start: GeoPoint,
        end: GeoPoint,
        weight: str = "length",
    ) -> list[GeoPoint]:
        """计算两点间最短骑行路径。

        Args:
            start: 起点坐标。
            end: 终点坐标。
            weight: 边权重属性（默认按距离）。

        Returns:
            路径坐标点列表。
        """
        # TODO: 实现最近节点查找 + A* 路径搜索
        raise NotImplementedError("Pathfinding not yet implemented")

    def estimate_distance(self, start: GeoPoint, end: GeoPoint) -> float:
        """粗略估算骑行距离（使用 Haversine 公式的直线距离）。"""
        from math asin, cos, radians, sin, sqrt

        lat1, lng1 = radians(start.lat), radians(start.lng)
        lat2, lng2 = radians(end.lat), radians(end.lng)

        dlat = lat2 - lat1
        dlng = lng2 - lng1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
        c = 2 * sqrt(a) if sqrt(a) <= 1 else 2.0  # clamp for safety

        R = 6_371_000  # 地球半径（米）
        return R * c

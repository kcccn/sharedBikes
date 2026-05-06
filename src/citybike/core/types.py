"""
核心类型定义。

为整个模拟引擎提供共享的数据类型——坐标、车辆、订单、调度任务等。
避免循环依赖，所有模块从此处引用基础类型。
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import NamedTuple


class GeoPoint(NamedTuple):
    """WGS-84 坐标点。"""
    lat: float  # 纬度
    lng: float  # 经度


class BikeStatus(enum.Enum):
    """单车状态。"""
    IDLE = "idle"               # 空闲（可被骑行）
    IN_USE = "in_use"           # 骑行中
    PARKED = "parked"           # 已停放（在 P 点）
    LOST = "lost"               # 丢失/损坏
    IN_TRANSIT = "in_transit"   # 调度运输中


@dataclass
class Bike:
    """一辆共享单车。"""
    bike_id: str
    status: BikeStatus = BikeStatus.IDLE
    position: GeoPoint | None = None
    battery: float | None = None  # 电单车专用


@dataclass
class Station:
    """推荐停放点（P 点）。"""
    station_id: str
    position: GeoPoint
    capacity: int          # 最大停放数
    current_count: int = 0


@dataclass
class Trip:
    """一次骑行订单。"""
    trip_id: str
    bike_id: str
    rider_id: str
    start_time: datetime
    end_time: datetime | None = None
    start_pos: GeoPoint | None = None
    end_pos: GeoPoint | None = None
    distance_m: float | None = None  # 骑行距离（米）


@dataclass
class DispatchTask:
    """调度任务：将车辆从 A 运到 B。"""
    task_id: str
    source: GeoPoint
    target: GeoPoint
    bike_ids: list[str] = field(default_factory=list)
    truck_id: str | None = None
    completed: bool = False

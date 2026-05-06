"""
模拟引擎核心。

管理模拟时钟、全局状态、事件循环。
所有外部系统（城市、车队、需求、调度）通过引擎协调。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Callable

from citybike.core.types import Bike, Station, Trip

logger = logging.getLogger(__name__)


class SimulationEngine:
    """主模拟引擎——整个游戏的后端心脏。

    职责：
    - 维护模拟时钟（支持加速和暂停）
    - 注册并调度周期性/一次性事件
    - 协调各子系统之间的通信
    """

    def __init__(self, start_time: datetime | None = None) -> None:
        self._time: datetime = start_time or datetime(2025, 1, 1, 6, 0)
        self._speed: float = 60.0           # 1 真实秒 = 60 模拟分钟
        self._paused: bool = False
        self._events: list[tuple[datetime, Callable[[], None]]] = []
        self._running: bool = False

        # 全局状态（各子系统的注册数据）
        self.bikes: dict[str, Bike] = {}
        self.stations: dict[str, Station] = {}
        self.trips: dict[str, Trip] = {}

    @property
    def now(self) -> datetime:
        return self._time

    @property
    def speed(self) -> float:
        return self._speed

    def set_speed(self, factor: float) -> None:
        """设置模拟倍率。"""
        self._speed = max(1.0, min(factor, 3600.0))

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def tick(self, real_seconds: float = 1.0) -> None:
        """推进一个模拟步进。"""
        if self._paused:
            return
        elapsed = timedelta(seconds=real_seconds * self._speed)
        self._time += elapsed
        self._dispatch_events()

    def schedule(self, at: datetime, callback: Callable[[], None]) -> None:
        """在指定模拟时间调度一个回调。"""
        self._events.append((at, callback))
        self._events.sort(key=lambda x: x[0])

    def _dispatch_events(self) -> None:
        """触发所有到期的已调度事件。"""
        while self._events and self._events[0][0] <= self._time:
            _, cb = self._events.pop(0)
            try:
                cb()
            except Exception:
                logger.exception("Event callback failed")

    def run(self, duration: timedelta) -> None:
        """运行模拟直到经过 duration 时间（模拟时间）。"""
        end = self._time + duration
        while self._time < end and self._running:
            self.tick()

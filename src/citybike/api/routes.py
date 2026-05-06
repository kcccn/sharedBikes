"""
FastAPI 路由定义。

提供模拟状态查询、控制命令、数据导出接口。
前端（Deck.gl / Mapbox）通过此 API 获取渲染数据。
"""

from __future__ import annotations

from fastapi import APIRouter

from citybike.core.types import Bike, Station

router = APIRouter(prefix="/api/v1", tags=["simulation"])


@router.get("/status")
def get_status():
    """返回模拟引擎的当前状态。"""
    return {
        "version": "0.1.0",
        "running": False,
        "time": "",
        "speed": 1.0,
    }


@router.get("/bikes")
def list_bikes(status: str | None = None) -> list[dict]:
    """获取所有单车（可选按状态过滤）。"""
    # TODO: 接入 SimulationEngine
    return []


@router.get("/stations")
def list_stations() -> list[dict]:
    """获取所有 P 点及其当前车辆数。"""
    return []


@router.post("/simulation/start")
def start_simulation():
    """启动/恢复模拟。"""
    return {"message": "simulation started"}


@router.post("/simulation/pause")
def pause_simulation():
    """暂停模拟。"""
    return {"message": "simulation paused"}


@router.post("/simulation/speed")
def set_speed(factor: float):
    """设置模拟倍率。"""
    return {"message": f"speed set to {factor}x"}

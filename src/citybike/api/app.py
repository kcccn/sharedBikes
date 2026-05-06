"""
FastAPI 应用工厂。

创建并配置 FastAPI 实例，注册路由和中间件。
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from citybike.api.routes import router

app = FastAPI(
    title="CityBike-Sim API",
    description="共享单车经营模拟后端引擎",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}

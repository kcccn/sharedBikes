"""
CityBike-Sim 入口点。

启动方式: python -m citybike
"""

from __future__ import annotations

import uvicorn


def main() -> None:
    """启动 FastAPI 开发服务器。"""
    uvicorn.run(
        "citybike.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()

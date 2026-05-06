#!/usr/bin/env python3
"""Phase 1 Demo Script — 端到端演示地图加载管线.

Usage:
    python scripts/demo_phase1.py                     # 加载北京并打印统计
    python scripts/demo_phase1.py --city shanghai     # 加载其他城市（fallback 到最小城市）
"""

from __future__ import annotations

import argparse
import math
import sys
import time

# Ensure backend is importable
sys.path.insert(0, "backend")

from app.services.map_service import MapService  # noqa: E402


def _fmt_km2(sq_km: float) -> str:
    """Format square km for display."""
    if sq_km >= 1_000_000:
        return f"{sq_km / 1_000_000:.2f}M km²"
    if sq_km >= 1_000:
        return f"{sq_km / 1_000:.2f}K km²"
    return f"{sq_km:.2f} km²"


def estimate_coverage_area(city) -> float:
    """Estimate city coverage area from node bounding box (km²)."""
    lats = [n.position.lat for n in city.nodes.values()]
    lngs = [n.position.lng for n in city.nodes.values()]
    if not lats:
        return 0.0
    lat_min, lat_max = min(lats), max(lats)
    lng_min, lng_max = min(lngs), max(lngs)
    # Approximate: 1° lat ≈ 111km, 1° lng ≈ 111*cos(avg_lat) km
    avg_lat = (lat_min + lat_max) / 2
    dlat_km = (lat_max - lat_min) * 111.0
    dlng_km = (lng_max - lng_min) * 111.0 * math.cos(math.radians(avg_lat))
    return dlat_km * dlng_km


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CityBike-Sim Phase 1 演示：城市地图加载管线",
    )
    parser.add_argument(
        "--city",
        default="beijing",
        help="城市名称（默认 beijing）",
    )
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  🚲 CityBike-Sim Phase 1 演示")
    print(f"  城市: {args.city}")
    print(f"{'='*60}\n")

    service = MapService()

    # --- Cold load ---
    print("📦 首次加载（冷启动）...")
    t0 = time.perf_counter()
    city = service.load_city(args.city)
    cold_time = time.perf_counter() - t0
    print(f"   ✅ 完成 ({cold_time:.2f}s)\n")

    # --- Cache load ---
    print("⚡ 缓存加载（热启动）...")
    t0 = time.perf_counter()
    _ = service.load_city(args.city)
    cache_time = time.perf_counter() - t0
    print(f"   ✅ 完成 ({cache_time:.2f}s)\n")

    # --- Statistics ---
    print("📊 城市统计信息")
    print("-" * 40)
    print(f"  🏗️  路网点 (Nodes):     {len(city.nodes):>6,}")
    print(f"  🛣️  路段   (Edges):     {len(city.edges):>6,}")
    print(f"  📍  站点   (Stations):  {len(city.stations):>6,}")
    print(f"  🗺️  运营区 (Zones):     {len(city.zones):>6,}")

    if city.nodes:
        area = estimate_coverage_area(city)
        print(f"  📐  覆盖面积:           {_fmt_km2(area)}")

    # --- Stations detail ---
    if city.stations:
        capacities = [s.capacity for s in city.stations.values()]
        print(f"\n  🅿️  站点容量： 最小={min(capacities)}, "
              f"最大={max(capacities)}, "
              f"平均={sum(capacities)/len(capacities):.0f}")

    # --- Sampling ---
    if city.nodes:
        sample_nodes = list(city.nodes.values())[:3]
        print(f"\n  🔍 路网点采样（前 3 个）:")
        for n in sample_nodes:
            print(f"     {n.node_id}: ({n.position.lat:.4f}, {n.position.lng:.4f}), "
                  f"海拔 {n.elevation_m:.1f}m")

    if city.stations:
        sample_stations = list(city.stations.values())[:3]
        print(f"\n  🔍 站点采样（前 3 个）:")
        for s in sample_stations:
            print(f"     {s.station_id}: {s.name} "
                  f"({s.position.lat:.4f}, {s.position.lng:.4f}), "
                  f"容量 {s.capacity}")

    # --- Performance assessment ---
    print(f"\n{'='*60}")
    print("  ⏱️  性能基线")
    print(f"  首次加载: {cold_time:.2f}s  {'✅ 达标' if cold_time < 30 else '❌ 超标'}")
    print(f"  缓存加载: {cache_time:.2f}s  {'✅ 达标' if cache_time < 2 else '❌ 超标'}")
    print(f"{'='*60}\n")

    # --- Summary ---
    all_pass = (
        len(city.nodes) >= 1000
        and len(city.edges) >= 2000
        and len(city.stations) >= 200
        and cold_time < 30
        and cache_time < 2
    )
    if all_pass:
        print("  🎉 Phase 1 验收通过！管线（配置→解析→布站→服务化）运行正常。\n")
    else:
        print("  ⚠️  部分指标未达标，请检查上述统计信息。\n")


if __name__ == "__main__":
    main()

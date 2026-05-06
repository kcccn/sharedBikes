# CityBike-Sim 架构文档

## 分层架构

```
┌─────────────────────────────────────┐
│          API Layer (FastAPI)        │
│  /api/v1/*  ←  HTTP →  Dashboard   │
├─────────────────────────────────────┤
│         Service Layer               │
│  MapService | DemandService |       │
│  BalanceService                     │
├─────────────────────────────────────┤
│          Core Domain                │
│  City · Fleet · Weather · Scheduler │
│  Engine · Config                    │
├─────────────────────────────────────┤
│        Utils / Visualization        │
│  geo.py · heatmap.py               │
└─────────────────────────────────────┘
```

## 依赖方向

- **API → Services → Core ← Utils**
- Core 层零 I/O 依赖，可独立测试
- Services 层编排 Core 逻辑，提供 I/O 边界
- Utils 层纯函数，被 Core 和 Services 引用

## 核心数据流

```
   tick()
     │
     ▼
  WeatherGenerator ──► Environment
     │
     ▼
  DemandService ──► list[TripRequest]
     │                   │
     ▼                   ▼
  Fleet (mutate)    BalanceService
     │                   │
     ▼                   ▼
  FleetSnapshot ────► API Response
```

## Phase 拆解建议

| Phase | 范围 |
|-------|------|
| Phase 0 | ✅ **当前** — 项目骨架、领域模型、API 桩、测试框架 |
| Phase 1 | 真实 OSM 数据接入、静态车辆投放、基础 API 实现 |
| Phase 2 | NPC 通勤潮汐需求生成、动态天气影响 |
| Phase 3 | 调度员派遣、财务结算、多策略对比 |
| Phase 4 | Deck.gl 可视化、热力图、OD 轨迹流 |

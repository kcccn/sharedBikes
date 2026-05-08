# CityBike-Sim 架构文档

## 分层架构

```
┌─────────────────────────────────────────────────────┐
│                   API Layer                         │
│         FastAPI 端点 (router.py → schemas)          │
├─────────────────────────────────────────────────────┤
│                 Service Layer                       │
│   MapService  │  DemandService  │  BalanceService   │
├─────────────────────────────────────────────────────┤
│                  Core Layer                         │
│   City │ Fleet │ Weather │ Scheduler │ Engine       │
├─────────────────────────────────────────────────────┤
│                  Utils Layer                        │
│     geo.py (haversine, bearing, midpoint)           │
└─────────────────────────────────────────────────────┘
```

## 依赖方向（严格单向）

**API → Services → Core ← Utils**

- Core 层**不依赖**任何 I/O 或框架
- Services 层编排 Core 模型的业务逻辑
- API 层仅负责 HTTP 序列化/反序列化

## 核心领域模型

### City（不可变）
- `Node` / `Edge` — 路网
- `Station` — 停车点（容量、经纬度）
- `Zone` — 运营区（多边形）
- `find_nearest_station()` — 最近站点查找

### Fleet（可变）
- `Bike` — 生命周期（AVAILABLE → IN_USE → ...）
- `FleetSnapshot` — 不可变快照供 API 消费
- `bikes_at_station()` — 按站点查询

### Weather / Environment
- `WeatherCondition` — CLEAR / RAINY / STORMY / SNOWY
- `SpecialEvent` — 演唱会等临时事件
- `demand_factor()` — 天气对需求的抑制系数

### Scheduler（策略模式）
- `RebalanceStrategy` — 抽象接口
- `GreedyThresholdStrategy` — 基于比率的简单配对

### SimulationEngine
- 状态机：STOPPED → RUNNING → PAUSED
- `advance(steps)` — 推进 N 个 tick
- `time_of_day()` — 格式化模拟时间
- 每 `rebalance_interval` ticks 自动执行调度（集成在 `_tick()` 管线内）

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/v1/city` | 城市概览 |
| GET | `/api/v1/city/stations` | 站点列表 |
| GET | `/api/v1/fleet` | 车队快照 |
| GET | `/api/v1/fleet/bikes/{id}` | 单车详情 |
| POST | `/api/v1/simulation/start` | 启动模拟 |
| POST | `/api/v1/simulation/pause` | 暂停模拟 |
| POST | `/api/v1/simulation/advance` | 推进 N 步 |
| GET | `/api/v1/simulation/status` | 状态查询 |
| GET | `/api/v1/events` | 活动事件 |
| GET | `/api/v1/dashboard/heatmap` | 供需热力图 |
| GET | `/api/v1/dashboard/flows` | OD 流线图 |

## 数据流

```
用户请求 → API Router → Service → Core Engine → Fleet Mutation → Snapshot → Response
                    ↑                                    │
                    └────── JSON serialization ←─────────┘
```

## 分阶段计划

| Phase | 内容 | 涉及模块 |
|-------|------|----------|
| 0 | 项目骨架 & 分层架构 | 全部（搭建完成） |
| 1 | 真实地图数据接入 | MapService + osmium/osmnx |
| 2 | NPC 通勤需求生成 | DemandService + Engine._tick() |
| 3 | 调度员派遣系统 | BalanceService + Scheduler |
| 4 | 前端可视化 | Web frontend + Deck.gl |

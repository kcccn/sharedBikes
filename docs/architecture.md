# CityBike-Sim 架构文档

## 核心理念

**抽象坐标系统** — 不追求"真实地图真实感"。城市由过程化生成器按网格坐标构造，前端用 Canvas 2D 渲染。没有 OSM、没有 LatLng、没有 Mapbox/Leaflet/Deck.gl。

所有位置使用 `Coord`（抽象基类），具体子类为 `GridCoord(x, y)`。坐标空间与应用逻辑解耦，未来可替换为 HexCoord 或其他实现。

---

## 分层架构

```
┌──────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│   FastAPI (REST)  │  WebSocket  │  Canvas Frontend       │
├──────────────────────────────────────────────────────────┤
│                    Service Layer                         │
│   MapService  │  DemandService  │  BalanceService        │
│   Achievements │  Leaderboard   │  Heatmap               │
├──────────────────────────────────────────────────────────┤
│                    Core Layer                            │
│   City │ Fleet │ Weather │ Scheduler │ Engine            │
│   EventBus │ AchievementEngine │ StationStatsTracker     │
├──────────────────────────────────────────────────────────┤
│                    Utils / Foundation                    │
│   Coord (abstract) │ GridCoord │ ProceduralCityGenerator │
└──────────────────────────────────────────────────────────┘
```

## 依赖方向（严格单向）

**Presentation → Services → Core → Foundation**

- Core 层**不依赖**任何 I/O、网络或框架
- Services 层编排 Core 模型的业务逻辑
- Presentation 层仅负责序列化/反序列化和传输
- Foundation 层零依赖，纯数据结构和算法

## 核心领域模型

### Coord（抽象基类）
- `Coord` — 整数坐标，无单位
- `GridCoord(x, y)` — 方形网格坐标
- `distance_to(other)` — 抽象距离计算
- 坐标与应用逻辑解耦，不绑定经纬度

### City（过程化生成）
- 由 `ProceduralCityGenerator` 根据 `CityConfig.procedural` 参数生成
- `grid_width`, `grid_height` — 城市网格尺寸
- `Station` — 停车点（位置为 GridCoord，非 LatLng）
- `Zone` — 运营区（网格坐标多边形）
- `find_nearest_station()` — 最近站点查找（基于抽象坐标距离）

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
- 通过 `EventBus` 发布 tick 事件，解耦消费者（WS、Achievement、Stats）

### EventBus
- 发布/订阅模式，引擎内单例
- 事件类型：TICK、STATION_UPDATED、BIKE_MOVED、ACHIEVEMENT_UNLOCKED
- WS handler 和 AchievementEngine 各自订阅所需事件

### AchievementEngine
- DSL 驱动的成就系统
- 规则引擎：conditions → triggers → rewards
- 每 tick 自动评估，写入独立成就 Ledger

### StationStatsTracker
- 异步统计：使用量、需求峰值、空闲率
- 为 Leaderboard 和 Heatmap 提供数据源
- 数据通过 EventBus 流式更新

---

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/v1/city` | 城市概览（网格尺寸+站点数） |
| GET | `/api/v1/city/stations` | 站点列表（GridCoord 位置） |
| GET | `/api/v1/fleet` | 车队快照 |
| GET | `/api/v1/fleet/bikes/{id}` | 单车详情 |
| POST | `/api/v1/simulation/start` | 启动模拟 |
| POST | `/api/v1/simulation/pause` | 暂停模拟 |
| POST | `/api/v1/simulation/advance` | 推进 N 步 |
| GET | `/api/v1/simulation/status` | 状态查询 |
| GET | `/api/v1/events` | 活动事件 |
| GET | `/api/v1/dashboard/heatmap` | 供需热力图 |
| GET | `/api/v1/dashboard/flows` | OD 流线图 |
| GET | `/api/v1/dashboard/leaderboard` | 站点排行榜 |
| GET | `/api/v1/achievements` | 成就列表 |
| GET | `/api/v1/achievements/player/{id}` | 玩家成就 |

## WebSocket 协议

```
Connect → [bootstrap: 全量站点+单车快照]
         → [tick: 增量状态更新] (每 tick 推送)
         → [event: 特殊事件] (按需推送)
```

- `bootstrap` 消息：首次连接时发送全量状态
- `tick` 消息：时间推进、单车移动、供需变化
- 使用 EventBus 解耦引擎 → WS 推送

---

## 数据流

```
用户请求 → FastAPI Router → Service → Core Engine → Mutation → Snapshot → JSON
                                    ↑
                              EventBus ←─ tick 事件
                                    ↓
                     ┌──────┬──────┬──────────┐
                     │  WS  │ Achv │  Stats   │
                     └──────┴──────┴──────────┘
```

## 分阶段进度

| Phase | 内容 | 状态 |
|-------|------|------|
| 0 | 项目骨架 & 分层架构 | ✅ 完成 |
| 1 | ~~真实地图数据接入 (osmium/osmnx)~~ | ❌ 废弃 — 改为抽象坐标 |
| 2 | NPC 通勤需求生成 | ✅ 完成 |
| 3 | 调度员派遣系统 | ✅ 完成 |
| 4 | ~~Leaflet 前端可视化~~ | ✅ 完成（已废弃，待替换为 Canvas） |
| 5 | WebSocket bootstrap + tick 推流 | ✅ 完成 |
| 6P0 | AchievementEngine + DSL + Ledger | ✅ 完成 |
| 6P1 | 异步排行榜 (StationStatsTracker) | ✅ 完成 |
| 6P2 | 供需热力图 (demand_factor + Leaflet.heat) | ✅ 完成 |
| **7A** | **抽象坐标替换：GridCoord + ProceduralCityGenerator** | ✅ **完成** |
| **7B** | **Canvas 前端渲染（替换 Leaflet）** | ✅ **完成** |

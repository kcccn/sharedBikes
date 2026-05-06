# CityBike-Sim 架构设计

## 分层架构 (Layered Architecture)

```
┌──────────────────────────────────────────────────────┐
│                     API 层 (api/)                      │
│  FastAPI routes, 请求/响应序列化, HTTP 中间件           │
│  职责: 协议适配, 无业务逻辑                             │
├──────────────────────────────────────────────────────┤
│                  服务层 (services/)                     │
│  OSM 地图加载, NPC 需求生成, 调度编排                   │
│  职责: I/O 编排, 调用 core 层完成业务逻辑               │
├──────────────────────────────────────────────────────┤
│             核心引擎层 (core/)                          │
│  City / Fleet / Weather / Scheduler                   │
│  职责: 纯领域逻辑, 零 I/O 依赖, 可单元测试               │
├──────────────────────────────────────────────────────┤
│              工具层 (utils/)                           │
│  空间计算, 几何工具, 与领域无关的 helper                 │
└──────────────────────────────────────────────────────┘
```

### 依赖方向

**`api/ → services/ → core/ ← utils/`**

- core 层不依赖 services 或 api
- services 层依赖 core 层
- utils 被任何层引用，但不依赖任何业务模块

## 模块职责

| 模块 | 路径 | 职责 |
|------|------|------|
| `core/city.py` | City 模型, 路网图, 站点/区域 | OSM 数据的领域表示 |
| `core/fleet.py` | Fleet/Bike 状态管理 | 单车生命周期与库存 |
| `core/weather.py` | 天气与特殊事件 | 外部环境因子 |
| `core/scheduler.py` | 调度算法(策略模式) | Rebalancing 决策 |
| `core/engine.py` | 主循环 Orchestrator | Tick 级状态推进 |
| `services/map_service.py` | OSM 文件解析 → City 构建 | I/O 密集型 |
| `services/demand_service.py` | NPC 出行需求生成 | 时空分布模型 |
| `services/balance_service.py` | 调度编排 | 调用 scheduler 策略 |
| `visualization/` | Heatmap / OD Flow 数据生成 | 前端渲染适配 |

## 数据流 (单次 Tick)

```
Environment.tick()          ← 天气/事件更新
       ↓
DemandService               ← 生成 (from, to) 出行请求
       ↓
Fleet.undock_bike()         ← 车辆出站
       ↓
[Cron] 骑行耗时到达         ← 未来: 事件驱动的到达队列
       ↓
Fleet.dock_bike()           ← 车辆入站
       ↓
Scheduler.analyse()         ← 检查供需失衡
       ↓
FleetSnapshot                → 推送到 API / WebSocket
```

## Phase 分拆建议

- **Phase 1** (当前): 架构骨架 + OSM 地图加载 + 静态车辆投放 + 基础 API
- **Phase 2**: NPC 通勤潮汐 + Trip 生命周期 + 基础热力图
- **Phase 3**: 调度员/卡车派遣 + 财务系统 + 调度效率面板
- **Phase 4**: Deck.gl 热力图 + OD 轨迹流 + 性能优化

## 关键设计决策

1. **`City` 是不可变的**: 一旦从 OSM 构建完成，路网结构在整个模拟运行期间不变。变更只发生在 Fleet 和 Environment 上。
2. **`Fleet` 是单点真相**: 所有单车的状态和位置由 Fleet 统一管理，避免多源数据不一致。
3. **策略模式用于调度**: `RebalanceStrategy` 抽象允许在贪心、遗传算法、强化学习之间切换。
4. **Snapshot 模式**: `FleetSnapshot` 是 API 消费的不可变视图，`SimulationEngine` 内部使用可变 `Fleet` 以保证性能。

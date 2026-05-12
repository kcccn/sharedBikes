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
| GET | `/api/v1/session` | 当前 GameSession 概览（余额、指令历史摘要） |
| POST | `/api/v1/session/reset` | 重置游戏会话（清除指令历史，重置余额） |

## WebSocket 协议

```
Connect → [bootstrap: 全量站点+单车快照]
         → [tick: 增量状态更新] (每 tick 推送)
         → [event: 特殊事件] (按需推送)
         → [command: 玩家指令] (客户端→服务端, 双向)
```

- `bootstrap` 消息：首次连接时发送全量状态
- `tick` 消息：时间推进、单车移动、供需变化
- `command` 消息：扩展 Phase C，客户端发送玩家决策指令，服务端回送 `command_result`
- 使用 EventBus 解耦引擎 → WS 推送

### Phase C 命令协议

客户端 → 服务端：

```json
{
  "type": "command",
  "command_id": "cmd_001",
  "action": "set_price",
  "payload": {
    "station_id": "station_05",
    "new_price_per_km": 2.5
  }
}
```

支持的 action 值：`set_price` | `buy_bikes` | `expand_station` | `launch_promotion`

服务端 → 客户端（响应）：

```json
{
  "type": "command_result",
  "command_id": "cmd_001",
  "success": true,
  "message": "station_05 定价已调整为 ¥2.5/km",
  "balance_change": 0,
  "new_balance": 9850.00
}
```

Tick 消息扩展（新增字段）：

```json
{
  "type": "tick",
  "tick": 1440,
  "time": "23:59",
  "station_inventory": {...},
  "balance": 9850.00,
  "daily_report": {
    "day": 2,
    "revenue_today": 320.50,
    "costs_today": 180.00,
    "profit_today": 140.50,
    "cumulative_balance": 9850.00,
    "alert": ""
  }
}
```

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

### Phase C 新增数据流

```
玩家点击前端面板
       ↓
WS: {"type": "command", "action": "set_price", ...}
       ↓
ws.py 接收 → GameSession.enqueue_command()
       ↓
EngineManager.advance() → 执行前先 drain command_queue:
  for cmd in session.command_queue:
    handler.validate(cmd, session) → handler.execute(cmd, engine, session)
    → 写 ledger, 改 pricing_tier, 扣 balance
    → WS 回送 command_result
       ↓
engine._tick() → 正常推进（指令效果已反映在模拟中）
       ↓
EventBus → WS (tick 消息, 含 balance + daily_report)
       ↓
前端更新 Dashboard + 站点面板状态
```

---

## Phase C — 游戏循环与玩家决策（v0.3 能玩）

### 动机

当前模拟可以全自动运行：NPC 通勤 + 调度员 + 经济系统，但玩家没有介入点。Phase C 将玩家从"观察者"变为"运营商"——用户可以暂停引擎、下达指令（定价/购车/扩区/促销），每个决策影响模拟走向，激活经营模拟的核心 loop。

### 设计原则

1. **玩家指令不是作弊**——所有指令都经过 CommandHandler 校验，消耗资源（资金），通过 Ledger 记录
2. **引擎不持有玩家状态**——SimulationEngine 是纯自动模拟器，GameSession 负责管理玩家交互层
3. **指令结果在下个 tick 可见**——指令不立即修改引擎内部 tick 中的逻辑，而是写入"悬挂指令"队列，EngineManager 在 advance() 前应用
4. **前端交互不侵入 Canvas 渲染路径**——操作面板作为独立 DOM 元素，不污染 Canvas 绘制管线

### 新增概念

#### GameSession（应用层）

```
GameSession
├── engine: SimulationEngine        # 包裹的引擎实例（1:1）
├── player_balance: float           # 玩家独立资金账户
├── command_queue: list[CommandEnvelope]  # 待执行的玩家指令
├── command_history: list[CommandResult]  # 已执行的指令历史
├── pending_effects: dict           # 当前悬挂的临时效果（促销等）
└── session_id: str                 # 会话标识（预留多游戏支持）
```

- GameSession 不是 Core 层模型——它在 `app/services/game_session.py` 中
- 初始化时与引擎绑定，不直接持有引擎生命周期（start/pause/stop 仍由 EngineManager 管理）
- `EngineManager` 内部持有 `GameSession` 实例，每次 `advance()` 前执行悬挂指令

#### PlayerCommand（抽象指令）

```python
@dataclass
class SetPrice:
    station_id: str
    new_price_per_km: float

@dataclass
class BuyBikes:
    count: int                           # 购买数量

@dataclass
class ExpandStation:
    station_id: str
    additional_capacity: int             # 扩容 (容量+)

@dataclass
class LaunchPromotion:
    station_id: str
    duration_ticks: int                  # 持续 tick 数
    demand_boost: float                  # 需求倍率 (e.g. 1.5)
```

- 每个指令是独立的 frozen dataclass，不可变
- 由 `CommandEnvelope(session_id, command_id, timestamp, command)` 包装
- `command_id` 由服务端生成，用于 WS 协议中的幂等确认

#### CommandHandler（指令处理器）

```
CommandHandler
├── validate(cmd, session) → ValidatedResult   # 校验资金是否充足、参数是否合法
├── execute(cmd, session) → CommandResult       # 执行指令，返回结果
└── effect_type registry                         # 按指令类型注册生效器
```

- `validate()` 做纯校验（不修改状态），返回 ValidatedResult
- `execute()` 做实际修改：
  - `SetPrice` → 修改 `engine.pricing_tier` 中对应站点的价格（通过 `PricingEngine.set_station_override(station_id, price)`）
  - `BuyBikes` → 调用 `engine.fleet.add_bike()` 添加 N 辆车，从 player_balance 扣款
  - `ExpandStation` → 修改 `city.stations[station_id].capacity`，从 player_balance 扣款
  - `LaunchPromotion` → 向 `engine.environment` 注册临时 SpecialEvent，从 player_balance 扣款
- 所有指令执行后向 engine ledger 写入对应的扣款/收费记账条目
- `CommandResult` 包含：成功/失败、消息、资金变动、影响的站点/单车列表

### 前端交互面板

1. **站点点击面板**（点击 Canvas 站点圆圈弹出）：
   - 站点名称、当前可用车辆/容量、当前价格
   - 操作按钮：调整价格（滑块/输入框）、扩容（带价格提示）、促销（选择持续时间和强度）
   - 样式：悬浮于 Canvas 之上的半透明 DOM card

2. **全局操作栏**（底部或侧边）：
   - 购买新单车按钮（显示当前单价）
   - 当前资金余额显示（大字体，醒目的金色/绿色）
   - 日结报告摘要（最近一天的收入/成本/利润）

3. **Dashboard 面板**（顶部或侧边，类似 Mini Metro 风格）：
   - 当前日期/时间（模拟时间）
   - 资金走势（迷你柱状图或简单数字变化）
   - 最近 7 日利润变化
   - 破产预警（红色闪烁）

### 更新后的分层架构

```
┌──────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│   FastAPI (REST)  │  WebSocket (扩展 command 协议)           │
│   Canvas Frontend  │  Station Action Panel  │  Dashboard     │
├──────────────────────────────────────────────────────────────┤
│                    Service Layer                             │
│   EngineManager  │  GameSession   │  CommandHandler          │
│   MapService  │  DemandService  │  BalanceService           │
│   Achievements │  Leaderboard   │  Heatmap                  │
├──────────────────────────────────────────────────────────────┤
│                    Core Layer                                │
│   City │ Fleet │ Weather │ Scheduler │ Engine               │
│   EventBus │ AchievementEngine │ StationStatsTracker        │
│   PricingEngine (StationOverride 支持)                      │
├──────────────────────────────────────────────────────────────┤
│                    Utils / Foundation                        │
│   Coord (abstract) │ GridCoord │ ProceduralCityGenerator    │
└──────────────────────────────────────────────────────────────┘
```

### 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/services/game_session.py` | **新建** | GameSession 类 + CommandEnvelope/CommandResult 定义 |
| `backend/app/services/command_handler.py` | **新建** | CommandHandler — validate + execute 各指令类型 |
| `backend/app/api/v1/ws.py` | **修改** | WS 接收 command 消息，enqueue 到 GameSession |
| `backend/app/services/engine_manager.py` | **修改** | advance() 前 drain command_queue；持 GameSession 引用；tick 推送 balance+daily_report |
| `backend/app/core/pricing.py` | **修改** | PricingEngine 支持 per-station price override |
| `backend/app/core/fleet.py` | **修改** | 可能：add_bike() 返回 bike_id 或简单扩展现有接口 |
| `backend/app/core/city.py` | **修改** | Station 支持动态扩容（capacity 可变） |
| `frontend/index.html` | **修改** | 站点点击面板、全局操作栏、Dashboard |

---

## 分阶段进度

| Phase | 内容 | 状态 |
|-------|------|------|
| 0 | 项目骨架 & 分层架构 | ✅ 完成 |
| 1 | ~~真实地图数据接入 (osmium/osmnx)~~ | ❌ 废弃 — 改为抽象坐标 |
| 2 | NPC 通勤需求生成 | ✅ 完成 |
| 3 | 调度员派遣系统 | ✅ 完成 |
| 4 | ~~Leaflet 前端可视化~~ | ❌ 废弃 — 已由 Phase 7B Canvas 替代 |
| 5 | WebSocket bootstrap + tick 推流 | ✅ 完成 |
| 6P0 | AchievementEngine + DSL + Ledger | ✅ 完成 |
| 6P1 | 异步排行榜 (StationStatsTracker) | ✅ 完成 |
| 6P2 | 供需热力图 (demand_factor + Leaflet.heat) | ✅ 完成 |
| **7A** | **抽象坐标替换：GridCoord + ProceduralCityGenerator** | ✅ **完成** |
| **7B** | **Canvas 前端渲染（替换 Leaflet）** | ✅ **完成** |
| **C** | **游戏循环与玩家决策（v0.3 能玩）** | 🔄 **设计中** |
| C1 | 架构设计 — GameSession + PlayerCommand | ✅ **已完成** |
| C2 | 后端 GameSession/CommandHandler 实现 | ⏳ 待 coder |
| C3 | WS 协议扩展 — command 消息类型 | ⏳ 待 coder |
| C4 | 前端点击事件 → 站点操作面板 | ⏳ 待 coder |
| C5 | 前端仪表盘（余额/收入/日报告） | ⏳ 待 coder |
| C6 | 集成测试 | ⏳ 待 coder |

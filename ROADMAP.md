# 🗺️ CityBike-Sim 架构路线图

> 共享单车运营模拟经营游戏

---

## 游戏定位

**共享单车运营模拟经营游戏** ≠ 数据分析平台。

玩家扮演共享单车公司 CEO，做战略决策，看财务回报。

```
┌───────────────────────────────────────────────────┐
│  ① 规划阶段（选址/定价/购车） → ② 模拟运行（N天）   │
│                                                    │
│  ④ 复盘升级（扩区/解锁） ← ③ 结算（收支/KPI）      │
└───────────────────────────────────────────────────┘
```

## 技术栈

| 层 | 技术 | 状态 |
|----|------|------|
| 后端语言 | Python ≥ 3.11 | ✅ 确定 |
| Web 框架 | FastAPI | ✅ 确定 |
| 数据验证 | Pydantic v2 | ✅ 确定 |
| 地图路网 | OSMnx + NetworkX | ✅ 确定 |
| 配置 | TOML (pydantic-settings) | ✅ 确定 |
| 前端 | React + Leaflet + TypeScript | ✅ 完成 (`frontend/`) |
| 领域架构 | 领域驱动分层 | ✅ 确定 |

---

## 架构依赖顺序（不变承诺）

以下按**架构依赖顺序**排列。前一个做完，后一个才能开工——这不是优先级排序，是拓扑排序。

```
▸ 底层基础设施（City 能力补齐）
  ├── City.shortest_path(a, b)           ← 50 行，NetworkX 寻路
  ├── _tick() 返回 TickEvents            ← 30 行，事件化改造
  ├── DemandService 接口改造 + 注入引擎   ← 20 行
  ├── RuleBasedDemandService (MVP)       ← 20 行，基础 trip 生成
  └── Wire API → SimulationEngine        ← 30 行，接线

▸ 经济系统骨架（定价 + 营收 + 成本）
  ├── PricingTier 领域模型
  ├── RevenueRecord / CostItem / FinancialReport
  └── 模拟结算管线（每个 tick 计算收支）

▸ NPC 需求引擎（基于真实路网的通勤潮汐）
  ├── Commuter / Shopper / Tourist 行为模型
  ├── OD 配对 + 路径距离计算（依赖 shortest_path）
  └── 潮汐效应（早/晚高峰）

▸ 调度博弈系统（玩家决策层）
  ├── DispatchOrder / DispatchFleet 模型
  ├── 手动调度命令（玩家触发）
  └── AI 调度建议（可选采纳）

▸ 前端接入
  ├── WebSocket 事件流（基于 TickEvents）
  ├── 地图视图（Mapbox/Leaflet）
  └── 决策面板 UI
```

### 验收标准

每个架构里程碑的验收条件只有一条：

> **这个模块可以被独立测试，且测试不依赖 mock。**
>
> 例如：`shortest_path()` 的测试不 mock City，直接加载临安市路网实测。

---

## 产品交付路线图（v0.x）

每个 v0.x 版本都是一个可以**完整玩一轮**的游戏（虽然简陋）。

```
v0.1 ─── 能看：地图 + 仪表盘 ✅ 已完成
         CLI 显示城市地图、站点、车辆分布

v0.2 ─── 能跑：核心游戏循环 ✅ 已完成
         ① 模拟运行（tick-by-tick 事件流）
         ② 每日日报（营收 + 满意度 + 预警）
         ③ NPC 通勤潮汐（早高峰→晚高峰）
         ④ API + WS 后端接线

v0.3 ─── 能玩：调度决策 ✅ 已完成
         ⑤ 玩家可派遣调度车
         ⑥ 调度成本 vs 满意度的 trade-off
         ⑦ 经济系统骨架（定价/营收/成本）

v0.4 ─── 能炫：Web 前端 ✅ 已完成
         ⑧ 地图站点热力图（demand_factor 着色）
         ⑨ WebSocket 实时车辆动画
         ⑩ 站点弹窗（车辆数/需求因子）
         ⑪ 异步排行榜

v0.5 ─── 能刷：成就 + 深度策略 🔴 下一个！
         ⑫ 成就系统 ✅（已实现）
         ⑬ 挑战剧本模式 ⏳
         ⑭ 沙盒模式 ⏳
         ⑮ 多城市扩张决策 ⏳
```

---

## 现有资产 → 游戏化映射

| 现有模块 | 游戏中扮演的角色 | 状态 |
|---------|----------------|------|
| `City` + OSM 路网 | 游戏地图（棋盘） | ✅ 完成 |
| `Station` | 可建设的停车点 | ✅ 完成 |
| `Fleet` + `Bike` | 你的车队资产 | ✅ 完成 |
| `Weather` + `SpecialEvent` | 天气/事件系统（游戏随机事件） | ✅ 完成 |
| `Scheduler` + `BalanceService` | 调度派遣（成本中心） | 🟡 骨架 |
| `DemandService` | NPC 需求生成（收入来源） | ✅ 完成 |
| `SimulationEngine` | 游戏时钟 + 回合推进 | ✅ 完成 |
| `API endpoints` | 游戏后端接口（REST + WS） | ✅ 完成 |
| `frontend/` | Web 前端（React + Leaflet） | ✅ 完成 |
| 经济系统（定价/营收/成本） | Phase 2 Ledger-First | ✅ 完成 |
| — | 玩家决策界面（前端 MVP） | ✅ 完成 |
| — | 成就/排行榜系统 | ✅ 完成 |

---

## 当前架构前提条件（Architecture Prerequisites）

以下基础设施项是**跨 Phase 的隐性依赖**，必须在下个 Phase 开始前完成：

| # | 项目 | 行数 | 依赖方 | 说明 |
|---|------|------|--------|------|
| 1 | `City.shortest_path()` | ~50 | Phase 3 NPC 通勤 | NetworkX 图已存在但未暴露寻路能力 |
| 2 | `_tick()` → `TickEvents` | ~30 | Phase 2-6 全部 | 事件化改造使测试/回放/分析成为可能 |
| 3 | `DemandService.generate()` 接口改造 | ~20 | Phase 2 经济系统 | 需要接收 stations 参数并注入 Engine |
| 4 | `RuleBasedDemandService` (MVP) | ~20 | v0.2 冷启动 | 避免首次体验全零报表 |
| 5 | Wire API → Engine | ~30 | 跨 Phase | 模拟端点硬编码 stub，需接入真实引擎 |
| 6 | `TripRequest` 站 ID 守卫 | ~10 | Phase 2/3 | 避免 KeyError 静默崩溃 |

---

## 已决策（不再变更）

| 承诺 | 依据 |
|------|------|
| ✅ 游戏类型：共享单车运营模拟经营 | 已有 City + Fleet + Station 三层领域模型 |
| ✅ 技术栈：Python + FastAPI + OSM | 已有完整实现 |
| ✅ 领域驱动分层 | `domain/` `application/` `infrastructure/` 三层清晰 |
| ✅ Phase 1 成果（地图解析 + 布站 + 配置） | 已测试通过，不可逆 |
| ❌ 变的东西：具体功能上线顺序 | 取决于人力/反馈，但架构依赖顺序不变 |

---

## 项目结构（建议）

```
apps/
  ├── game_cli/          # CLI 游戏入口（已有）
  ├── game_tutorial/     # 新手引导剧本（复用 game_cli 内核）
  └── game_web/          # Web 前端（远期）

backend/
  ├── app/
  │   ├── api/           # API 端点
  │   ├── core/          # 领域模型（City, Fleet, Engine...）
  │   ├── models/        # Pydantic DTOs
  │   ├── services/      # 应用服务（Demand, MapService...）
  │   ├── utils/         # 工具函数
  │   └── visualization/ # 可视化
  ├── data/              # 城市数据文件
  └── tests/             # 测试
```

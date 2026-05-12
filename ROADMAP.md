# 🗺️ CityBike-Sim 架构路线图

> **抽象坐标 · 过程化城市 · 无虚假现实主义**
>
> 共享单车运营模拟经营游戏 — 受 Mini Metro / OpenTTD 启发

---

## 🎯 游戏定位

**共享单车运营模拟经营游戏** ≠ 数据分析平台，≠ 真实地图模拟器。

玩家扮演共享单车公司 CEO，在抽象棋盘城市上做战略决策，看财务回报。

```
┌───────────────────────────────────────────────────┐
│  ① 规划阶段（选址/定价/购车） → ② 模拟运行（N天）   │
│                                                    │
│  ④ 复盘升级（扩区/解锁） ← ③ 结算（收支/KPI）      │
└───────────────────────────────────────────────────┘
```

**核心理念：不做虚假的真实感。** 没有真实寻路、没有真实停车点数据时，保留 Leaflet/OSM 只是维持"看起来像地图"的幻觉。抽象棋盘更诚实、更可玩、迭代更快。

---

## 🧱 技术栈

| 层 | 技术 | 状态 |
|----|------|------|
| 后端语言 | Python ≥ 3.11 | ✅ 确定 |
| Web 框架 | FastAPI | ✅ 确定 |
| 数据验证 | Pydantic v2 | ✅ 确定 |
| 坐标系统 | `Coord(x, y)` — 抽象网格坐标 | ✅ 完成 |
| 城市生成 | `ProceduralCityGenerator` — seed 驱动 | ✅ 完成 |
| 地图路网 | ~~OSMnx + NetworkX~~ → 过程化生成 | ❌ 废弃 |
| 配置 | TOML (pydantic-settings) | ✅ 确定 |
| 前端渲染 | Canvas 抽象渲染 | ✅ 完成 |
| ~~前端~~ | ~~Leaflet 瓦片地图~~ | ❌ 废弃 |
| 领域架构 | 领域驱动分层 | ✅ 确定 |

---

## 📐 架构承诺（不变）

以下架构原则**不随方向变化**：

| 承诺 | 依据 |
|------|------|
| ✅ 游戏类型：共享单车运营模拟经营 | 已有 City + Fleet + Station 三层领域模型 |
| ✅ 技术栈：Python + FastAPI | 已有完整实现 |
| ✅ 领域驱动分层 | `domain/` `application/` `infrastructure/` 三层清晰 |
| ✅ Coord 抽象坐标 | 替换 LatLng，3 处重复定义合并为 1 处 |
| ✅ ProceduralCityGenerator | 替换 OSM 解析，seed 驱动，无地理约束 |
| ❌ LatLng / OSM / Leaflet | 全面废弃 — 不做虚假的真实感 |
| ❌ 两层抽象折中 | 不做"同时支持真实和抽象"——全面抽象一次性到位 |

---

## 🏗️ 执行路线

### Phase A — 后端抽象化（已完成 ✅）

| 任务 | 描述 | 状态 |
|------|------|------|
| A1 | `Coord(x, y)` 类型 — 替代 3 处 LatLng 定义 | ✅ |
| A2 | `city.py` 中 LatLng → Coord，`_haversine_km` → 欧几里得距离 | ✅ |
| A3 | `geo.py` 所有函数替换为基于 Coord 的简单几何运算 | ✅ |
| A4 | `fleet.py` 中 LatLng → Coord | ✅ |
| A5 | `ProceduralCityGenerator` — 基于 seed 生成抽象网格城市 | ✅ |
| A6 | 重写 `map_service.py` — ProceduralCityGenerator 为主路径，砍掉 OSM | ✅ |
| A7 | 更新所有受影响的后端测试 | ✅ |

**影响范围：** 仅后端抽象层。经济/调度/需求/成就/排行榜引擎层**零改动**。

### Phase B — 前端 Canvas 迁移（已完成 ✅）

| 任务 | 描述 | 状态 |
|------|------|------|
| B1 | Canvas 抽象城市地图渲染器 | ✅ |
| B2 | 节点/连线/车辆动画渲染 | ✅ |
| B3 | ~~Leaflet.heat~~ → canvas-based 热力图 | ✅ |
| B4 | WebSocket 事件流适配 | ✅ |

**注意：** Phase B 依赖 Phase A 完成后才能启动。

---

## 📦 核心引擎（不动）

以下模块在方向变更中**零改动**：

| 模块 | 原因 |
|------|------|
| 经济系统 (Phase 2) | 纯账本，与坐标无关 |
| 调度引擎 (Phase 3) | 只要 `distance` 抽象接口不变，核心逻辑不变 |
| 需求引擎 (Phase 4) | 车站供需运算，不关心车站画成什么样子 |
| EventBus (Phase 4.5) | 纯消息基础设施 |
| 成就系统 (Phase 6 P0) | 事件驱动，零 UI 依赖 |
| 排行榜 (Phase 6 P1) | 纯后端异步计算 |
| 热力图后端 (Phase 6 P2) | demand_factor 数据计算不变，仅前端渲染方式变 |

---

## 📋 产品交付路线图（v0.x）

| 版本 | 主题 | 关键交付物 | 状态 |
|------|------|-----------|------|
| v0.1 | **抽象骨架** | Coord 系统 · ProceduralCityGenerator · 后端测试通过 | ✅ |
| v0.2 | **能看** | Canvas 抽象城市地图 · 节点/连线/车辆可视化 | ✅ |
| v0.3 | **能玩** | 游戏循环 · 玩家决策（定价/购车/扩区） | ⏳ |
| v0.4 | **能赢** | NPC 通勤 · 调度成本 vs 满意度 trade-off | ⏳ |
| v0.5 | **能炫** | 成就系统 · 排行榜 · 沙盒模式 · 挑战剧本 | ⏳ |
| v1.0 | **能刷** | 多城市 · 随机事件 · 深度策略 | ⏳ |

---

## 🗺️ 项目结构（目标）

```
backend/
  ├── app/
  │   ├── api/              # API 端点
  │   ├── core/             # 领域模型 (City, Coord, Fleet, Engine...)
  │   ├── models/           # Pydantic DTOs
  │   ├── services/         # 应用服务 (Demand, MapService, CityGenerator...)
  │   ├── utils/            # 工具函数 (geo.py → coord.py)
  │   └── visualization/    # 可视化（保留）
  ├── data/                 # 城市种子配置
  └── tests/                # 测试

frontend/                   # Canvas 前端（Phase B）
  ├── src/
  │   ├── renderer/         # 抽象地图渲染器
  │   ├── game/             # 游戏状态管理
  │   └── ui/               # 决策面板 UI
  └── ...
```

---

## 📝 已决策的记录

| 决策 | 来源 | 日期 |
|------|------|------|
| 全面抽象坐标，废弃 OSM/LatLng/Leaflet | [#139](https://github.com/kcccn/sharedBikes/issues/139) | 2026-05-12 |
| 不做两层抽象折中 | [#139](https://github.com/kcccn/sharedBikes/issues/139) | 2026-05-12 |
| 核心引擎层不动 | [#139](https://github.com/kcccn/sharedBikes/issues/139) | 2026-05-12 |

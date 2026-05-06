# CityBike-Sim 架构文档

## 分层架构

```
┌──────────────────────────────────────┐
│            FastAPI (HTTP)             │  app/main.py
│  /api/v1/*                            │  app/api/v1/router.py
├──────────────────────────────────────┤
│           Services (编排层)            │  app/services/
│  MapService / DemandService /         │
│  BalanceService                       │
├──────────────────────────────────────┤
│        Core (纯领域逻辑, 零 I/O)        │  app/core/
│  City / Fleet / Weather / Engine /    │
│  Scheduler                            │
├──────────────────────────────────────┤
│     Utils (纯函数工具)  │  Visualization │  app/utils/  app/visualization/
│  geo.py / heatmap / flow              │
└──────────────────────────────────────┘
```

### 依赖方向（严格单向）

```
api/ → services/ → core/ ← utils/
  ↓                    ↓
 models/        config/ (SimulationConfig)
```

- **Core 层** 完全不依赖任何 I/O 或框架
- **Services 层** 编排 Core 模型，处理异步/外部依赖
- **API 层** 只做序列化/反序列化，不包含业务逻辑

## 核心数据流

```
用户请求 ──→ API Router ──→ Service ──→ Engine.advance()
                                            │
                                    ┌───────┴───────┐
                                    │    _tick()     │
                                    │  ┌───────────┐ │
                                    │  │ 更新天气   │ │
                                    │  │ 处理行程   │ │
                                    │  │ 触发调度   │ │
                                    │  └───────────┘ │
                                    └───────┬───────┘
                                            │
                                    Fleet.snapshot()
                                            │
                                    FleetSnapshot (不可变)
                                            │
                                    序列化 → JSON Response
```

## 关键架构决策

### 1. City 不可变
路网/车站拓扑在初始化时构建一次，此后只读。

### 2. Snapshot 模式
Fleet 内部维护可变状态（`Bike.status`, `Bike.station_id`），对外通过 `FleetSnapshot` 输出不可变视图。

### 3. 可插拔调度策略
`RebalanceStrategy` 抽象基类，当前基于 `GreedyThresholdStrategy`，可替换为 GA / RL / ML 模型。

### 4. 配置集中管理
`SimulationConfig` 与 `AppConfig` 使用 pydantic-settings，支持环境变量覆盖。

## Phase 拆解建议

| Phase | 目标 | 关键交付 |
|-------|------|---------|
| **0** | 项目骨架与分层架构 ✅ | 空 City + Fleet + Engine + API stubs + 测试框架 |
| **1** | 真实地图解析 | osmium/osmnx 接入 MapService，真实路网构建 |
| **2** | 动态需求生成 | DemandService 实现 NPC 通勤潮汐模型 |
| **3** | 调度博弈系统 | 调度员/卡车派遣，财务结算 |
| **4** | 数据可视化 | Deck.gl 前端，热力图 + OD 轨迹流 |

## 代码统计 (Phase 0)

```
backend/
├── app/
│   ├── main.py                  # 30 行
│   ├── config.py                # 30 行
│   ├── api/v1/router.py         # 110 行 (8 个 stub 端点)
│   ├── core/
│   │   ├── city.py              # 110 行
│   │   ├── fleet.py             # 120 行
│   │   ├── weather.py           # 100 行
│   │   ├── scheduler.py         # 110 行
│   │   └── engine.py            # 110 行
│   ├── services/                # 3 个 service stub
│   ├── models/schemas.py        # 80 行
│   ├── visualization/           # 2 个 renderer stub
│   └── utils/geo.py             # 50 行
├── tests/                       # 3 个测试文件
├── pyproject.toml
└── requirements.txt
```

总计约 **900 行** Python 代码，**30 个测试用例**。

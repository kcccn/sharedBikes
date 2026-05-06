# CityBike-Sim 架构文档

## 分层架构

```
┌──────────────────────────────────────────┐
│              API Layer                    │
│   app/api/v1/router.py                   │
│   (FastAPI routes, input validation)      │
├──────────────────────────────────────────┤
│           Service Layer                   │
│   app/services/                          │
│   (MapService, DemandService,            │
│    BalanceService)                       │
├──────────────────────────────────────────┤
│           Core Layer                      │
│   app/core/                              │
│   (City, Fleet, Weather, Engine,         │
│    Scheduler)                            │
│   ★ Pure domain logic, zero I/O          │
├──────────────────────────────────────────┤
│         Config / Models / Utils           │
│   app/config.py                          │
│   app/models/                            │
│   app/utils/                             │
└──────────────────────────────────────────┘
```

## 数据流

```
[Client] ──HTTP──▶ [API Router]
                      │
                      ▼
                 [Service Layer]
                      │
                      ▼
                 [Core Engine]
                      │
             ┌────────┴────────┐
             ▼                  ▼
         [Fleet]           [Environment]
             │                  │
             └──────┬───────────┘
                    ▼
             [Scheduler]
                    │
                    ▼
            [FleetSnapshot] ──▶ [API Response]
```

## 核心设计决策

### 1. 单向依赖
- `api/ → services/ → core/`
- `core/` 不依赖 `api/` 或 `services/`
- `core/` 下的代码是纯 Python，无 FastAPI/HTTP/DB 依赖
- 便于单元测试和复用

### 2. City 不可变
- City 对象（路网、站点、区域）一次构建后只读
- 状态变更只发生在 Fleet（车队）和 Environment（天气/事件）中
- 避免并发读写带来的复杂性

### 3. Snapshot 模式
- `FleetSnapshot` 是不可变的 NamedTuple，供 API 消费
- 内部使用可变的 `Fleet` 保证 tick 性能
- 每次 `advance()` 返回一个新的快照

### 4. 调度策略可插拔
- `RebalanceStrategy` 抽象基类
- 当前实现：`GreedyThresholdStrategy`
- 可替换为：遗传算法、强化学习等

## 阶段规划

### Phase 0 ✅ (当前)
- [x] 项目骨架搭建
- [x] 核心领域模型
- [x] API 端点桩
- [x] 测试框架

### Phase 1
- [ ] 真实 OSM 数据接入（MapService.load_city）
- [ ] NPC 通勤需求生成（DemandService）
- [ ] 前端骨架初始化（React/Vue3 + Deck.gl）
- [ ] API 端点真实实现

### Phase 2
- [ ] 调度员派遣系统
- [ ] 财务结算系统
- [ ] 高级调度算法

### Phase 3
- [ ] Deck.gl 热力图渲染
- [ ] OD 轨迹流动画
- [ ] 实时数据面板

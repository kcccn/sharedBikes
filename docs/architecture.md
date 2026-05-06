# CityBike-Sim 架构文档

## 分层架构

```
┌─────────────────────────────────────┐
│          API Layer (FastAPI)        │  ← 处理 HTTP 请求、路由、输入验证
├─────────────────────────────────────┤
│         Services Layer              │  ← 业务编排：MapService, DemandService, BalanceService
├─────────────────────────────────────┤
│          Core Layer                 │  ← 纯领域逻辑，零 I/O 依赖
│  ┌───────┬───────┬───────┬───────┐  │
│  │ City  │ Fleet │Weather│Sched. │  │
│  └───────┴───────┴───────┴───────┘  │
├─────────────────────────────────────┤
│     Utils / Models / Visualization  │  ← 工具函数、DTO 骨架、渲染桩
└─────────────────────────────────────┘
```

### 依赖方向（单向）
- `api/ → services/ → core/ ← utils/`
- Core 层**不依赖**任何 I/O、网络、或框架代码
- `City` 不可变：路网一次构建后只读

## 核心概念

| 组件 | 职责 |
|------|------|
| `SimulationEngine` | 主循环 (tick based)，管理模拟状态机 |
| `Fleet` | 可变车队状态，`snapshot()` 生成不可变快照供 API 消费 |
| `Environment` | 天气 + 特殊事件，影响需求 modifier |
| `RebalanceStrategy` | 策略模式抽象，当前实现 `GreedyThresholdStrategy` |

## 数据流

```
API 请求 → Service → Engine.advance() → Fleet.snapshot() → API 响应
                              ↑
                     Environment.tick()
```

## Phase 路线图

| Phase | 内容 |
|-------|------|
| **Phase 0** | ✅ 项目骨架、分层架构、API stubs（当前） |
| **Phase 1** | 真实地图解析、静态车辆投放、需求生成 |
| **Phase 2** | 动态 NPC 通勤潮汐模拟、OD 流追踪 |
| **Phase 3** | 调度员派遣、财务结算系统 |
| **Phase 4** | Deck.gl 可视化、热力图 & OD 轨迹流 |

---
name: rebalance-strategy-interface-contract
description: RebalanceStrategy.analyse() 接口不可变 — 新策略用构造函数注入
metadata:
  type: knowledge
  tags: [architecture, interface-contract, scheduler, rebalancing]
  status: active
  created: 2026-05-13T20:57:25Z
  updated: 2026-05-13T20:57:25Z
---

# RebalanceStrategy.analyse() 接口不可变 — 新策略用构造函数注入

## 决策

`RebalanceStrategy.analyse()` 的抽象接口签名是**不可变约束**：

```python
def analyse(self, station_inventory, station_capacity, threshold_low=0.2, threshold_high=0.8) -> FleetBalanceReport
```

任何需要额外上下文（station_positions, budget, distance_fn）的新策略实现，必须通过**构造函数注入**传递这些依赖，而不是修改 `analyse()` 签名。

## 理由

- LSP（里氏替换）：旧策略（GreedyThresholdStrategy）和新策略（CostAwareRebalanceStrategy）必须能在 `SimulationEngine` 中互换
- 三个调用点依赖此签名：`engine.py:265`、`BalanceService.analyse()`、策略自身
- 数据生命周期不同：station_positions 在城市加载后不变，是配置级数据，不是每个 tick 变化的数据

## 实现

```python
class CostAwareRebalanceStrategy(RebalanceStrategy):
    def __init__(self, station_positions, budget=1000.0, distance_fn=None):
        self._station_positions = station_positions
        self._budget = budget
        self._distance_fn = distance_fn or (lambda a, b: 1.0)
    
    def analyse(self, station_inventory, station_capacity, ...):
        # 用 self._station_positions 和 self._distance_fn
```

Phase D (PR #153) 已按此规则 dispatched。

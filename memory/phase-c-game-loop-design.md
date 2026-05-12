---
name: phase-c-game-loop-design
description: Phase C — Game Loop & Player Decision Architecture Design
metadata:
  type: knowledge
  tags: [architecture, phase-c, game-loop, player-decision, v0.3]
  status: active
  created: 2026-05-12T23:18:41Z
  updated: 2026-05-12T23:18:41Z
---

# Phase C — Game Loop & Player Decision Architecture Design

## Phase C 架构设计完成

### 设计概要
Phase C 将玩家从"观察者"变为"运营商"，引入 GameSession + PlayerCommand + CommandHandler + WS command 协议 + 前端交互面板。

### 关键决策
1. **指令不是作弊** — 所有指令通过 CommandHandler 校验，消耗资金，走 Ledger 记账
2. **引擎不持有玩家状态** — SimulationEngine 是纯自动模拟器，GameSession 在 Service 层独立管理玩家交互
3. **指令悬挂队列** — 指令在 EngineManager.advance() 前 drain，保证下个 tick 可见效果
4. **4 种命令类型** — SetPrice（定价）、BuyBikes（购车）、ExpandStation（扩容）、LaunchPromotion（促销）
5. **前端交互不污染 Canvas** — 操作面板作为独立 DOM 元素

### 文件布局
- `backend/app/services/game_session.py` — GameSession + CommandEnvelope/CommandResult
- `backend/app/services/command_handler.py` — CommandHandler validate + execute
- `backend/app/api/v1/ws.py` — 修改：接收 command 消息
- `backend/app/services/engine_manager.py` — 修改：advance() 前 drain command_queue
- `backend/app/core/pricing.py` — 修改：支持 per-station price override
- `backend/app/core/city.py` — 修改：Station 支持动态扩容
- `frontend/index.html` — 修改：站点面板 + 操作栏 + Dashboard

### 相关 PR
- PR #149: Phase C 架构设计文档
- RFC #148: v0.3 游戏循环与玩家决策

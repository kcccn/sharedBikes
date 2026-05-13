---
name: phase-c-game-loop-complete
description: Phase C Complete — Game Loop & Player Decision Implementation
metadata:
  type: knowledge
  tags: [phase-c, game-loop, player-commands, complete]
  status: active
  created: 2026-05-13T04:17:04Z
  updated: 2026-05-13T04:17:04Z
---

# Phase C Complete — Game Loop & Player Decision Implementation

Phase C (v0.3 能玩) fully implemented and merged via PR #149.

Key components:
- backend/app/services/game_session.py — GameSession with player_balance, command_queue, command_history
- backend/app/services/command_handler.py — CommandHandler with validate()/execute() for 4 command types
- backend/app/core/engine.py — _station_price_overrides and _station_capacity_overrides dicts
- backend/app/core/pricing.py — PricingEngine.apply() now supports optional price_per_km override
- backend/app/services/engine_manager.py — holds GameSession, drains command queue before advance(), captures tick state
- backend/app/api/v1/ws.py — receives command messages via reader_task, sends command_result + extended tick messages
- backend/app/api/v1/router.py — GET/POST /session endpoints
- frontend/index.html — station action panel, global toolbar, dashboard, toast notifications

Critical bug caught in review: double balance deduction (session.deduct() + record_result() both adjusted balance). Fixed in PR #150.

Cost constants: buy_bike=¥200, expand_station=¥500/unit, promotion=¥300 + ¥50/10ticks, initial_balance=¥10,000.
Commands: set_price (¥0.5-10/km), buy_bikes (1-100), expand_station (1-50 capacity), launch_promotion (10-1440 ticks, 1.0-5.0x boost).

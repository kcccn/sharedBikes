---
name: engine-needs-async-drive-loop
description: Engine needs async drive loop — start() alone doesn't tick
metadata:
  type: knowledge
  tags: [engine, websocket, game-loop, architecture]
  status: active
  created: 2026-05-13T23:55:59Z
  updated: 2026-05-13T23:55:59Z
---

# Engine needs async drive loop — start() alone doesn't tick

SimulationEngine.start() only sets state=RUNNING — it does NOT start any background loop. The engine only advances when someone explicitly calls advance() or _tick(). For WebSocket-based real-time gameplay, the WS handler must create an asyncio background task that continuously calls mgr.advance(1) at the engine.speed_multiplier rate.

Fix implemented in ws.py: _drive_engine() background task created alongside the reader task, properly cancelled in cleanup.

Without this drive loop: frontend gets bootstrap but never receives tick events → all stations show 0 bikes, dashboard stuck at --:--, game appears completely frozen.

---
name: leaderboard-architecture-pattern
description: Phase 6 P1: Async Leaderboard Architecture
metadata:
  type: knowledge
  tags: [phase6, leaderboard, architecture, eventbus]
  status: active
  created: 2026-05-12T02:54:15Z
  updated: 2026-05-12T02:54:15Z
---

# Phase 6 P1: Async Leaderboard Architecture

Leaderboard uses StationStatsTracker — an EventBus subscriber (same pattern as AchievementEngine) that maintains per-station in-memory counters from TickEvents. No DB, no WebSocket push. REST API `GET /leaderboard/stations?sort_by=trips|revenue|profit` queries memory on demand. Engine reset clears counters automatically. No Ledger schema changes needed.

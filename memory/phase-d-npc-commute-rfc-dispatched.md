---
name: phase-d-npc-commute-rfc-dispatched
description: Phase D RFC Created — NPC Commute + Cost vs Satisfaction
metadata:
  type: knowledge
  tags: [phase-d, v0.4, architecture, rfc]
  status: active
  created: 2026-05-13T19:16:49Z
  updated: 2026-05-13T19:16:49Z
---

# Phase D RFC Created — NPC Commute + Cost vs Satisfaction

RFC #153 created for Phase D (v0.4). Architecture covers:
- CommuteDemandService with NPC home/work daily cycle
- CostAwareRebalanceStrategy with distance-aware dispatch costing
- SatisfactionTracker with station health decay/recovery
- 3 new files: npc.py, satisfaction.py, dispatch_cost.py
- Backward compat: RuleBasedDemandService stays as configurable fallback

Coder dispatched via ryobot.yml workflow with issue_number=153

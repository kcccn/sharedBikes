---
name: roadmap-md-sync-after-merge
description: ROADMAP.md 同步模式 — merge 后立即检查 doc drift
metadata:
  type: knowledge
  tags: [documentation, roadmap, process]
  status: active
  created: 2026-05-13T10:05:18Z
  updated: 2026-05-13T10:05:18Z
---

# ROADMAP.md 同步模式 — merge 后立即检查 doc drift

每次 Phase PR merge 后，ROADMAP.md 的 v0.x 状态行容易被遗漏。PR #149 (Phase C) 合并后，ROADMAP.md 仍显示 v0.3 为 ⏳，需要在 4 小时后 patrol 修复。建议模式：merge 后立即 check ROADMAP.md 状态行同步，或加入 checklist。

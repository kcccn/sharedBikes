---
name: roadmap-rewrite-abstract-direction
description: Roadmap 全面重写 — 抽象坐标方向
metadata:
  type: knowledge
  tags: [roadmap, direction-change, abstract-coord, phase-a]
  status: active
  created: 2026-05-12T09:01:36Z
  updated: 2026-05-12T09:01:36Z
---

# Roadmap 全面重写 — 抽象坐标方向

创始人确认方向大改（#139），Architect 裁决全面抽象坐标。ROADMAP.md 和 Issue #78 已全面重写。

核心变更：
- Coord(x,y) 替代 LatLng — 3 处重复定义合并为 1 处
- ProceduralCityGenerator 替代 OSM 解析
- Canvas 抽象渲染替代 Leaflet 前端
- 核心引擎层（经济/调度/需求/成就/排行榜）零改动
- 不做两层抽象折中 — 一次性到位

新 Phase 结构：
- Phase A（当前执行中）：后端抽象化 — Coord + ProceduralCityGenerator + 废弃 OSM
- Phase B（待启动）：前端 Canvas 迁移

已关闭：PR #138（旧 ROADMAP.md 同步，过时）
已创建：PR #140（新 ROADMAP.md 全面重写）

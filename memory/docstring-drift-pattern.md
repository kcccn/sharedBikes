---
name: docstring-drift-pattern
description: Docstring Drift — engine.py claimed phantom variables
metadata:
  type: knowledge
  tags: [docstring, code-review, phase-d]
  status: active
  created: 2026-05-13T22:06:05Z
  updated: 2026-05-13T22:06:05Z
---

# Docstring Drift — engine.py claimed phantom variables

PR #154 (Phase D) had docstring drift in `backend/app/core/engine.py`: claimed `_station_inventory_history` and `_station_capacity_history` variables that don't exist, and described SatisfactionTracker behavior that actually lives in `engine_manager.py`. Lesson: docstrings must describe what the file *does*, not what the system does elsewhere. Importing a type does not mean the file "adds" that feature. Also caught: `@property` decorator used on methods with parameters (runtime crash).

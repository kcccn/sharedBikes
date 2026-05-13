---
name: property-with-params-pitfall
description: @property decorator does not accept parameters — will TypeError at runtime
metadata:
  type: knowledge
  tags: [python, property, bug-pattern, phase-d]
  status: active
  created: 2026-05-13T22:09:41Z
  updated: 2026-05-13T22:09:41Z
---

# @property decorator does not accept parameters — will TypeError at runtime

A `@property` descriptor in Python defines a getter that takes only `self`. If you decorate a method with `@property` and the method has additional parameters (e.g. `@property def is_commuting(self, tick_of_day: int) -> bool`), Python will raise `TypeError` at runtime when the property is accessed. This happened in Phase D's npc.py: three methods (`is_commuting`, `is_at_work`, `is_at_home`) had `@property` but also took `tick_of_day`. Fix: remove `@property` and call as regular methods. Always check that `@property` methods have exactly `self` and no other parameters.

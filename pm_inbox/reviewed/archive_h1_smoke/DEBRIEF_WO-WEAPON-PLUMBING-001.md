# DEBRIEF: WO-WEAPON-PLUMBING-001
**From:** Builder (Opus 4.6)
**Date:** 2026-02-14
**Lifecycle:** NEW
**Commit:** a9a3c8c

**Success criteria:**
- weapon_type + range_increment on Weapon dataclass: MET
- is_ranged detection in attack_resolver + full_attack_resolver: MET
- B-AMB-04 disarm weapon type modifiers activated: MET
- Sunder grip multiplier activated: MET
- Existing tests pass without modification: MET (5,775 passed, 15 skipped, 14 pre-existing failures unrelated)
- 34 new tests in test_weapon_plumbing.py: MET

---

## Section 1 — Friction Log

~15% of context spent on the melee `max_range` regression. Initial implementation used `max(5, range_ft)` which is mathematically tautological — max_range always >= distance, so melee range checks never fail. This broke 43 replay determinism tests. Root cause analysis required reading the targeting_resolver, understanding that `max_range` is in feet, and realizing the old `max_range=100` was a deliberate "permissive melee cap" that golden recordings depend on. Fix: keep `100` for melee, use `range_increment * 10` only for ranged.

~10% on the dual weapon pattern. `EF.WEAPON` stores either a string name or a dict. Had to trace both paths through intent_bridge, aoo.py, and maneuver_resolver to ensure `isinstance` dispatch covered all consumers. The WO line references were accurate — this was tracing, not guessing.

Stale `.pyc` cache caused phantom test failures (110 failures) on one run that disappeared after clearing `__pycache__`. Cost one full test suite cycle (~3 min).

---

## Section 2 — Methodology Challenge

The WO specifies "Do NOT change state.py, replay_runner.py, or Lens/presentation files" but doesn't address what happens when melee `max_range` changes from the hardcoded `100` to a computed value. The constraint "existing tests must pass without modification" effectively forces `max_range=100` for melee (since golden recordings depend on it), but the WO doesn't explicitly call this out as a decision. A builder who doesn't run replay tests early could spend significant context building a "correct" melee reach system (5ft/10ft) only to discover it breaks replays. The WO should include a binary decision: "Melee max_range: keep legacy 100ft cap — do NOT implement proper melee reach."

---

## Section 3 — Field Manual Entry

**13. Replay Determinism Governs max_range**

When modifying `max_range` in attack_resolver.py or full_attack_resolver.py, run `test_spark_integration_stress.py` BEFORE the full suite. Golden event recordings encode the exact targeting outcome (attack_roll vs targeting_failed) at specific entity distances. Any formula that changes which attacks pass/fail range checks — even if mechanically correct — will break replay determinism. The safe pattern: preserve the old literal for existing weapon types, add new logic only for newly-plumbed weapon categories (e.g., `is_ranged`).

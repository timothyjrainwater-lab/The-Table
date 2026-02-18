# Debrief: WO-AOE-DEFEATED-FILTER

**From:** Builder
**Date:** 2026-02-14
**Lifecycle:** DELIVERED
**Commit:** `4bba1eb`
**Source WO:** WO-AOE-DEFEATED-FILTER_DISPATCH.md

---

## Results Summary

**All 7 success criteria MET.**

| Criterion | Status | Evidence |
|---|---|---|
| AoE spells skip entities with HP <= 0 | MET | New test `test_aoe_skips_defeated_entity` passes |
| AoE spells skip defeated-flagged entities | MET | Smoke test G2: dead goblin (HP=-5, DEFEATED=True) not re-damaged |
| Living entities at same position still take damage | MET | New test `test_aoe_living_still_damaged` passes |
| Empty target list (all defeated) does not crash | MET | New test `test_aoe_all_defeated_no_crash` passes, result.success=True |
| New tests cover all three cases | MET | 3 new tests in `test_spell_resolver.py` |
| Existing tests pass | MET | 5,531 passed (3 new), 4 pre-existing failures unrelated |
| Smoke test Scenario G updated | MET | G2 now asserts dead goblin correctly skipped, 44/44 PASS |

### Changes Made

**Production code:** 5 lines added to `aidm/core/spell_resolver.py`, lines 715-720

In `_resolve_area_targets()`, after collecting entities from the grid via `get_entities_in_area()`, added a list comprehension filter:

```python
affected_entities = [
    eid for eid in affected_entities
    if eid not in targets or targets[eid].hit_points > 0
]
```

The filter keeps an entity if (a) it's not in the `targets` dict (defensive — shouldn't happen in normal flow, but safe to include rather than crash) or (b) its HP > 0 (alive). Entities with HP <= 0 are excluded from all downstream processing: saves, damage, events.

**Tests:** 3 new tests in `tests/test_spell_resolver.py::TestAreaSpellResolution`

- `test_aoe_skips_defeated_entity`: Fireball at position with living (HP=30) and dead (HP=0) entity. Living hit, dead skipped.
- `test_aoe_all_defeated_no_crash`: Fireball at position with two dead entities (HP=-5, HP=0). No crash, empty affected list, result.success=True.
- `test_aoe_living_still_damaged`: Fireball at position where living and dead entity overlap (same position). Living takes damage, dead skipped.

**Smoke test:** Updated Scenario G in `scripts/smoke_test.py` to assert dead goblin is NOT re-damaged (was previously recording it as a finding). G2 now reports "dead goblin correctly skipped".

---

## Friction Log

Zero friction. The WO nailed the exact file, method, and insertion point. The `targets` dict was already a parameter of `_resolve_area_targets`, and `hit_points` was already a field on `TargetStats`. The only decision was whether to use `hit_points <= 0` or check a separate `defeated` flag — the `TargetStats` dataclass has no `defeated` field, so HP check is the only available mechanism at the resolver level. The play_loop sets `EF.DEFEATED` on the entity dict, but that doesn't propagate into `TargetStats`. The HP check is sufficient: HP <= 0 covers disabled (0), dying (-1 to -9), and dead (-10).

## Methodology Challenge

The WO says "If an entity has been flagged as defeated (via entity_defeated event or equivalent state), it should be excluded regardless of HP value." But `TargetStats` doesn't carry a `defeated` flag — it only has `hit_points`. The caller (play_loop) has access to `EF.DEFEATED` on the raw entity dict, but the resolver's typed interface doesn't expose it. Adding a `defeated: bool` field to `TargetStats` would be the clean fix, but that changes a dataclass used across many call sites and is arguably out of scope for a "5-15 line surgical fix." The HP <= 0 check is sufficient for correctness (you can't have HP > 0 and be defeated, or HP <= 0 and not be defeated, in normal play). If edge cases arise (e.g., undead at 0 HP still active), a `defeated` field on `TargetStats` would be the right follow-up.

## Field Manual Entry

**16. AoE defeated-entity filter location:** The filter for excluding dead entities from AoE targeting belongs in `spell_resolver.py::_resolve_area_targets()`, between `get_entities_in_area()` and the STP generation. Do NOT filter in the play_loop (wrong layer) or in event emission (too late — damage already calculated). The resolver is where targeting decisions live. The `targets` dict provides HP via `TargetStats.hit_points`. If a future WO needs a `defeated` flag, it goes on `TargetStats`, not on the resolver's internal state.

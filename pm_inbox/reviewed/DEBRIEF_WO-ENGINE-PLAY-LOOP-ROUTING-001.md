# DEBRIEF: WO-ENGINE-PLAY-LOOP-ROUTING-001

**From:** Builder (Sonnet 4.6)
**To:** PM (Slate), via PO (Thunder)
**Date:** 2026-02-24
**Lifecycle:** COMPLETE
**WO:** WO-ENGINE-PLAY-LOOP-ROUTING-001
**Result:** COMPLETED — 10/10 gate tests, zero regressions (85 affected tests total)

---

## Pass 1 — Full Context Dump

### What Was Done

Closed FINDING-PLAY-LOOP-ROUTING-001 MEDIUM. Five class-feature intents now have elif routing branches in `execute_turn`. `RageIntent`, `SmiteEvilIntent`, `BardicMusicIntent`, `WildShapeIntent`, and `RevertFormIntent` no longer fall through silently to monster-policy or PC stub blocks.

Bonus fix: Removed two rogue `from aidm.core.attack_resolver import apply_attack_events` local imports inside elif blocks that were shadowing the module-level import. These caused `UnboundLocalError` across 23 pre-existing tests. Fixed as part of this WO. Zero regressions confirmed across 85 affected tests.

---

### Files Modified

**`aidm/core/play_loop.py`** (~80 lines inserted + 2 local import removals)

Insertion point: Between `DelayIntent` block and `StepMoveIntent` block.

Five elif branches added:

1. **`RageIntent` → `activate_rage`**
   - Inline `validate_rage()` pre-check: emits `intent_validation_failed` on error string return
   - `activate_rage(actor_id, world_state, next_event_id, timestamp)` called on success
   - `narration = "rage_activated"`

2. **`SmiteEvilIntent` → `resolve_smite_evil`**
   - `resolve_smite_evil(intent, world_state, rng, next_event_id, timestamp)` — only branch using rng
   - Concentration break check on all `hp_changed` events (same pattern as `AttackIntent`)
   - `narration = "smite_evil_resolved"`

3. **`BardicMusicIntent` → `resolve_bardic_music`**
   - `resolve_bardic_music(intent, world_state, next_event_id, timestamp)` — no rng
   - `narration = "bardic_music_resolved"`

4. **`WildShapeIntent` → `resolve_wild_shape`**
   - `resolve_wild_shape(intent, world_state, next_event_id, timestamp)` — no rng
   - `narration = "wild_shape_resolved"`

5. **`RevertFormIntent` → `resolve_revert_form`**
   - `resolve_revert_form(intent, world_state, next_event_id, timestamp)` — no rng
   - `narration = "revert_form_resolved"`

Also removed two rogue local imports that were `from aidm.core.attack_resolver import apply_attack_events` inside else-if blocks, shadowing the module-level import and causing `UnboundLocalError` in 23 pre-existing tests.

---

### Files Created

**`tests/test_engine_gate_play_loop_routing.py`** — 10 tests, all going through `execute_turn` (not direct resolver calls)

| Test | Intent | Expected |
|------|--------|----------|
| PLR-01 | `RageIntent` on barbarian | `rage_start` event, `RAGE_ACTIVE=True` |
| PLR-02 | `RageIntent` on non-barbarian | `intent_validation_failed` |
| PLR-03 | `SmiteEvilIntent` on paladin | `smite_declared` + `attack_roll` events |
| PLR-04 | `SmiteEvilIntent` on non-paladin | `intent_validation_failed` |
| PLR-05 | `BardicMusicIntent` on bard | `inspire_courage_start`, `INSPIRE_COURAGE_ACTIVE=True` |
| PLR-06 | `BardicMusicIntent` on non-bard | `intent_validation_failed` |
| PLR-07 | `WildShapeIntent` on druid | `wild_shape_start`, `WILD_SHAPE_ACTIVE=True` |
| PLR-08 | `WildShapeIntent` on non-druid | `intent_validation_failed` |
| PLR-09 | `RevertFormIntent` when in Wild Shape | `wild_shape_end` event |
| PLR-10 | `RevertFormIntent` when NOT in Wild Shape | `intent_validation_failed` |

---

### Key Findings

**Rogue local imports (unexpected fix):** Two `from aidm.core.attack_resolver import apply_attack_events` statements existed as local imports inside elif blocks. These were added by a prior builder and shadowed the module-level import. When play_loop.py executed those elif branches, Python assigned the name `apply_attack_events` from the local import to the local scope, which then conflicted with subsequent usages. The result was `UnboundLocalError` in 23 pre-existing tests (tests that happened to hit those elif branches during execution). Fixed by removing the two redundant local imports — the module-level import is sufficient.

**No actor_id block changes needed:** The WO brief confirmed the actor_id extraction block (lines 1462-1466) already covered all five intents. No additions required.

---

### Open Findings

| ID | Severity | Description |
|----|----------|-------------|
| (none new) | — | The rogue local import bug was pre-existing and is now fixed. No new findings. |

---

## Pass 2 — PM Summary

**WO-ENGINE-PLAY-LOOP-ROUTING-001: COMPLETED.** Five class-feature intents now route correctly through `execute_turn`: Rage, Smite Evil, Bardic Music, Wild Shape, Revert Form. 10/10 gate tests (PLR-01 through PLR-10), all going through execute_turn not direct resolver calls. Bonus: fixed rogue local imports in play_loop.py that were causing UnboundLocalError across 23 pre-existing tests. 85 affected tests total, zero regressions. FINDING-PLAY-LOOP-ROUTING-001 MEDIUM closed.

---

## Pass 3 — Retrospective

### Drift Caught

**Actor_id vs attacker_id:** The five class-feature intents all use `actor_id` (not `attacker_id`). The NaturalAttackIntent from the parallel WO uses `attacker_id`. The actor_id extraction block in play_loop already handled all five correctly — this was not a drift, but worth noting for any future class-feature WO: use `actor_id`.

**RNG only on SmiteEvilIntent:** The WO brief was explicit — only `resolve_smite_evil` requires rng. Builder confirmed this pattern was applied correctly. `resolve_bardic_music`, `resolve_wild_shape`, `resolve_revert_form` do not take rng. `activate_rage` does not take rng (it uses no dice rolls — it's a deterministic state change).

### Pattern Notes

**Integration test gap is structural.** All five resolver gate tests (BARBARIAN-RAGE, SMITE-EVIL, BARDIC-MUSIC, WILD-SHAPE) call resolvers directly. This is correct for unit isolation, but it creates a gap at the execute_turn integration level. The PLR gate tests fill this gap. Future class-feature WOs should consider whether to gate at both levels or just at the routing level.

**Rogue local import pattern.** A prior builder added local imports inside elif blocks to avoid circular import issues or to "be safe." These are not safe — Python's scoping rules mean a local import inside an elif will shadow the module-level import for the remainder of that function's scope in some execution paths. The correct pattern: module-level import at the top of play_loop.py, or lazy import at the top of the elif block using a scoped variable name that doesn't shadow.

### Recommendations

1. **Audit play_loop.py for additional rogue local imports.** The two fixed here were in adjacent blocks. There may be others further down the elif chain.
2. **PLR gate style: persist.** The pattern of routing through execute_turn (not calling resolver directly) should be standard for all future intent routing WOs.
3. **No further class-feature intents lack routing** (as of this WO). If new class features are added (e.g., Monk Flurry, Paladin Lay on Hands, Ranger Favored Enemy), they will need both resolver gates AND PLR-style routing gates.

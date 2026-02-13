# Phase 4B Handover Packet

**Prepared:** 2026-02-13
**Branch:** master
**Last Commit:** 7c09f58 (signal voice)
**Test Baseline:** 5,371 collected / 5,323 passed / 16 skipped (HW-gated)
**pm_inbox:** 7 active items (normalized)

---

## Execution Order (Sequential)

### 1. WO-CONDFIX-01 — Unify Condition Storage Format

**Risk:** MEDIUM | **Effort:** Micro | **Breaks:** ~4 tests

**Problem:** `play_loop.py` `_resolve_spell_cast()` stores conditions as bare string lists while `conditions.py` `apply_condition()` uses structured dicts. Guarded by tolerance in `get_condition_modifiers()` but is a latent crash source for future condition features (duration, stacking).

**Scope:**
- Fix `play_loop.py` lines 449-456: Replace list append with proper `apply_condition()` call or structured dict storage
- Fix `play_loop.py` lines 585-588: Align condition removal with new format
- Update ~4 tests that assume list format

**Files:**
- `aidm/core/play_loop.py` (modify)
- `tests/test_play_loop_spellcasting.py` (update ~4 tests)
- `tests/test_play_cli.py` (verify spell condition tests)

**Regression Watch:**
- `test_play_loop_spellcasting.py::TestConditionApplication::test_cast_hold_person_applies_condition`
- `test_play_loop_spellcasting.py::test_spell_duration_expires_at_round_end`
- `test_conditions_kernel.py::test_condition_modifiers_affect_attack_rolls`
- `test_play_cli.py::TestSpellCasting` (condition display)

**Acceptance:** All existing condition tests pass. No new condition format crashes.

---

### 2. WO-ROUND-TRACK-01 — Round Counter and Turn Display

**Risk:** LOW | **Effort:** Small | **Breaks:** 0 tests expected

**Problem:** CLI doesn't show round boundaries. Multi-round combat is hard to follow. Blocks future condition duration tracking.

**Scope:**
- Track round number in `_main_loop()` — increment when initiative order cycles back to first living actor
- Print `"=== Round N ==="` header at each round boundary
- Store `round_index` in `active_combat` (field already exists, just not incremented)
- ~5 new tests

**Files:**
- `play.py` (modify `_main_loop`)
- `tests/test_play_cli.py` (add round display tests)

**Regression Watch:**
- Existing CLI tests use substring assertions (`assert "X" in output`), not line-exact matching
- Round headers are additive output — should not break existing assertions
- Verify `test_full_combat_loop` still passes

**Acceptance:** Round headers visible. Round counter increments correctly. Existing CLI tests pass.

---

### 3. WO-FULLATTACK-CLI-01 — Full Attack Action in CLI

**Risk:** LOW | **Effort:** Medium | **Breaks:** 0 tests expected

**Problem:** Fighters can only make single attacks. Full attack resolver and `FullAttackIntent` routing in `play_loop.py` are already complete — only CLI wiring is missing.

**Scope:**
- Add `"full attack"` two-word verb detection in `parse_input()` (before single-word verb check)
- Add `full_attack` action type routing in `resolve_and_execute()` — build `FullAttackIntent` from entity BAB + weapon
- Format multi-hit output (multiple attack_roll + damage_roll events per turn)
- ~8 new tests

**Files:**
- `play.py` (modify `parse_input`, `resolve_and_execute`, `format_events`)
- `tests/test_play_cli.py` (add full attack tests)

**Key Implementation Notes:**
- `FullAttackIntent` already defined in `aidm/schemas/attack.py` lines 68-95
- `play_loop.py` line 1040-1073 already routes `FullAttackIntent` to `resolve_full_attack()`
- `full_attack_resolver.py` is complete (iterative attacks, critical hits, damage reduction)
- Current fixture BAB values: Aldric (Fighter) BAB 3 = 1 attack. At BAB 6+ gets iterative.
- For playtest value, consider bumping Aldric's BAB to 6 in fixture (gets +6/+1 iterative)

**Regression Watch:**
- No existing tests should break (new parser case, existing routing)
- Verify `test_full_attack_resolution.py` still passes independently
- Verify `test_play_loop_combat_integration.py::test_full_attack_intent_triggers_cp11_resolver`

**Acceptance:** `full attack goblin` works in CLI. Multiple attack rolls displayed. BAB progression correct.

---

### 4. WO-SPELLSLOTS-01 — Spell Slot Tracking

**Risk:** HIGH | **Effort:** Large | **Breaks:** 26+ tests (fixture cascade)

**BLOCKING: Requires CP for entity_fields.py (frozen contract)**

`entity_fields.py` is in the frozen contracts list (PSD line 388). Adding `SPELL_SLOTS` and `CASTER_LEVEL` constants requires a Change Proposal with:
- Design rationale
- Breaking change assessment
- Migration path
- Test plan
- PO approval

**Problem:** All spells fire unlimited. No per-day slot tracking. Elara (Cleric 3) can cast Cure Light Wounds infinity times.

**Scope (after CP approval):**
- Add `EF.SPELL_SLOTS` and `EF.CASTER_LEVEL` to entity_fields.py
- Initialize Elara's slots in fixture (Cleric 3, WIS 16: L0 x4, L1 x4, L2 x3)
- Add OPTIONAL slot validation in `spell_resolver.py` `validate_cast()` — only check if `EF.SPELL_SLOTS` exists on entity (backward compatible)
- Decrement slot in `play_loop.py` after successful cast
- Display remaining slots in `show_status()` for casters
- ~10 new tests, ~15 test updates

**Files:**
- `aidm/schemas/entity_fields.py` (FROZEN — needs CP)
- `aidm/runtime/play_controller.py` (fixture init)
- `aidm/core/spell_resolver.py` (optional validation)
- `aidm/core/play_loop.py` (slot decrement)
- `play.py` (status display)
- `tests/test_spell_resolver.py` (fixture updates)
- `tests/test_play_loop_spellcasting.py` (fixture updates)
- `tests/test_play_cli.py` (slot display + exhaustion tests)

**Critical Mitigation:**
- Make slot validation OPTIONAL (`if EF.SPELL_SLOTS in entity`) — tests without slots continue to work
- Initialize slots in `build_simple_combat_fixture()` ONLY for casters
- Do NOT change `CasterStats` signature — use entity dict directly

**Regression Watch:**
- 26 test files call `build_simple_combat_fixture()` — adding fields is safe (dict), removing/changing existing fields is not
- `test_spell_resolver.py` (100+ tests) — only break if validation is mandatory
- `test_play_loop_spellcasting.py` — only break if multiple-cast tests deplete slots

**Acceptance:** Spell slots displayed. Casting depletes slots. Zero-slot rejection works. Existing tests pass.

---

## Sequencing Diagram

```
WO-CONDFIX-01 (micro, ~4 test updates)
    |
    v
WO-ROUND-TRACK-01 (small, 0 breaks)
    |
    v
WO-FULLATTACK-CLI-01 (medium, 0 breaks)
    |
    v
[CP for entity_fields.py SPELL_SLOTS — PO approval required]
    |
    v
WO-SPELLSLOTS-01 (large, ~15 test updates, optional validation)
```

## Post-Package State

After all 4 WOs, Phase 4 remaining:
- WO-OSS-DICE-001 (Three.js, needs PO amendments)
- Human playtest round 2 (with full attack + spell slots + round tracking)

## Session Artifacts (Uncommitted)

- `PROJECT_STATE_DIGEST.md` — Updated (WO-INITIATIVE-01 INTEGRATED, signal voice, test count)
- `docs/ops/REHYDRATION_KERNEL.md` — New (WO-OPS-REHYDRATION-KERNEL-01)
- `docs/ops/STANDING_OPS_CONTRACT.md` — New canonical location
- `pm_inbox/REHYDRATION_KERNEL_LATEST.md` — New
- `pm_inbox/README.md` — Updated (hygiene rules, PM-owned archiving)
- `pm_inbox/aegis_rehydration/STANDING_OPS_CONTRACT.md` — Updated (PM rule 10, Thunder rule 17 removed)
- `docs/planning/PROSODIC_SCHEMA_DRAFT.md` — New (PAS v0.1 design spec)
- `pm_inbox/` — 33 files moved to reviewed/

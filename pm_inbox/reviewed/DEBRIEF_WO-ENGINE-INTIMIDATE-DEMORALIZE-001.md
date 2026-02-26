# Debrief: WO-ENGINE-INTIMIDATE-DEMORALIZE-001
**Builder:** Chisel
**Dispatch:** #15 (Batch F)
**Date:** 2026-02-26
**Commit:** 8d2ff92
**Status:** ACCEPTED — 8/8 passed
**KERNEL-07 (Social Consequence) flagged to Anvil.**

---

## What Was Done

1. **`aidm/schemas/intents.py`** — Added `DemoralizeIntent` dataclass:
   - Fields: `actor_id`, `target_id`, `source_text`
   - Added to `Intent` type union and `parse_intent()` dispatch

2. **`aidm/core/skill_resolver.py`** — Added `resolve_demoralize()`:
   - Roll: `d20 + EF.CHA_MOD + EF.SKILL_RANKS["intimidate"]`
   - DC: `EF.HD_COUNT + EF.WIS_MOD` of target
   - On success: `duration = 1 + (margin // 5)`, applies SHAKEN via `create_shaken_condition()`
   - Already-shaken target: refreshes duration (no escalation to Frightened — PHB p.76)
   - On failure: `skill_check_failed` event with roll and DC
   - Returns new `WorldState` via `deepcopy(entities)` pattern

3. **`aidm/core/play_loop.py`** — Added routing branch for `DemoralizeIntent`:
   - Calls `resolve_demoralize(world_state, intent, current_event_id, rng)`
   - Sets `narration = "demoralize_resolved"`

## Pass 3 Notes

**KERNEL-07 (Social Consequence):** Demoralize is a combat use of a social skill. The engine correctly handles the mechanical outcome (SHAKEN applied) without modeling NPC psychological state. The social Intimidate path (changing NPC attitude — PHB p.76, out-of-combat) is **NOT STARTED**. This is a clean boundary: combat demoralize is a standard action with a defined mechanic; the social path requires separate routing and a different event type. Logged to Anvil.

**Already-shaken refresh:** PHB p.76 explicitly states that a target already Shaken from Intimidate does not become Frightened — the duration is refreshed. The implementation overwrites the `"shaken"` condition dict entry with the new duration, correctly modeling this behavior.

**Action economy:** ID-005 confirms a `demoralize_resolved` narration event is emitted, tracking action consumption. The standard action slot decrement is handled by the existing `execute_turn` action economy framework.

**FINDING-ENGINE-SOCIAL-INTIMIDATE-001:** Non-combat Intimidate (PHB p.76 — Change Attitude, requires 1 minute, affected by target HD and prior failure cooldown) is not wired. Logged as LOW OPEN.

---

## Test Results

| ID | Scenario | Result |
|----|----------|--------|
| ID-001 | Roll beats DC → condition_applied, SHAKEN | PASS |
| ID-002 | Roll beats DC by 5 → duration = 2 rounds | PASS |
| ID-003 | Roll beats DC by 10 → duration = 3 rounds | PASS |
| ID-004 | Roll fails DC → skill_check_failed, no SHAKEN | PASS |
| ID-005 | Standard action consumed (narration event) | PASS |
| ID-006 | Failure → HP unchanged | PASS |
| ID-007 | Already shaken → duration refreshed, not escalated | PASS |
| ID-008 | High HD/WIS target → DC = HD + WIS mod | PASS |

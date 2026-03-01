# DEBRIEF: WO-ENGINE-AOO-ROUND-RESET-001 - AoO Round Boundary Reset

**Lifecycle:** ARCHIVE
**Commit:** 8d21c33 (code), a3ac307 (backlog)
**Filed by:** Chisel
**Session:** 26
**Date:** 2026-03-01
**WO:** WO-ENGINE-AOO-ROUND-RESET-001
**Status:** FILED - awaiting PM verdict

---

## Pass 1 - Context Dump

### Summary

Two-line fix. `aoo_used_this_round` and `aoo_count_this_round` now reset at round boundary inside `play_loop.py`'s end-of-round block. `deflect_arrows_used` not touched. `cleave_used_this_turn` not touched. Active-combat audit conducted -- no other uncleared per-round fields found. Backlog committed before debrief.

### Files Changed

| File | Type | Change |
|------|------|--------|
| `aidm/core/play_loop.py` | MODIFIED | +2 lines in end-of-round block: `active_combat["aoo_used_this_round"] = []` and `active_combat["aoo_count_this_round"] = {}` |
| `tests/test_engine_aoo_round_reset_gate.py` | NEW | AOR-001..AOR-008 gate tests |

### PM Acceptance Note 1 -- Before/after at play_loop.py end-of-round block

**BEFORE** (end-of-round block closed after wild-shape tick, no AoO reset):
```python
            if _has_ws:
                from aidm.core.wild_shape_resolver import tick_wild_shape_duration
                _wsd_events, world_state = tick_wild_shape_duration(...)
                events.extend(_wsd_events)
                current_event_id += len(_wsd_events)

    updated_state = WorldState(...)
```

**AFTER** (two reset lines added before round-end block closes):
```python
            if _has_ws:
                from aidm.core.wild_shape_resolver import tick_wild_shape_duration
                _wsd_events, world_state = tick_wild_shape_duration(...)
                events.extend(_wsd_events)
                current_event_id += len(_wsd_events)

            # WO-ENGINE-AOO-ROUND-RESET-001: Reset AoO trackers at round boundary.
            # PHB p.137: each creature gets 1 AoO per round (+ DEX mod with Combat Reflexes).
            # aoo_used_this_round and aoo_count_this_round accumulate across execute_turn()
            # calls (SessionOrchestrator path bypasses combat_controller.execute_combat_round).
            # Reset here so round 2+ AoOs fire correctly. Do NOT touch deflect_arrows_used
            # (already reset in combat_controller.py:348 / WO-ENGINE-DA-ROUND-RESET-001).
            active_combat["aoo_used_this_round"] = []   # CP-15: PHB p.137 -- 1 AoO per round
            active_combat["aoo_count_this_round"] = {}  # WO-ENGINE-COMBAT-REFLEXES-001: per-entity count

    updated_state = WorldState(...)
```

`deflect_arrows_used` is NOT reset here (adjacent tracking field, NOT AoO scope). Confirmed adjacent at play_loop.py:4253 — set from DA events, reset in `combat_controller.py:348`. AOR-006 regression gate passes.

### PM Acceptance Note 2 -- AOR-004 within-round limit still enforced

`aoo_used_this_round` accumulation (lines 2496-2499, 3195-3198, 3952-3955) is unchanged. The reset applies only at round boundary (`if current_position == last_actor_index:`). AOR-004 gate confirms `aoo_count_this_round["a"] == 1` mid-round. PASS.

### PM Acceptance Note 3 -- AOR-006 DA regression gate passes

`deflect_arrows_used` field untouched by this WO. AOR-006 passes: field is preserved through a mid-round turn. AOR-006 PASS.

### PM Acceptance Note 4 -- AOR-008 code inspection

```python
# play_loop.py line 4350:
active_combat["aoo_used_this_round"] = []   # CP-15: PHB p.137 -- 1 AoO per round
# play_loop.py line 4351:
active_combat["aoo_count_this_round"] = {}  # WO-ENGINE-COMBAT-REFLEXES-001: per-entity count
```

Both lines confirmed present within 900 chars of `WO-ENGINE-AOO-ROUND-RESET-001` comment. AOR-008 PASS.

### PM Acceptance Note 5 -- active_combat audit (no other uncleared per-round fields)

Full audit of `active_combat` per-round/per-turn fields:

| Field | Reset location | Status |
|-------|---------------|--------|
| `aoo_used_this_round` | play_loop.py:4350 (this WO) + combat_controller.py:346 | FIXED |
| `aoo_count_this_round` | play_loop.py:4351 (this WO) + combat_controller.py:347 | FIXED |
| `deflect_arrows_used` | combat_controller.py:348 (d1fecb4) | FIXED (not re-touched) |
| `cleave_used_this_turn` | play_loop.py:1870 (WO-ENGINE-CLEAVE-WIRE-001, per-turn) | FIXED (correct, not moved) |
| `turn_counter` | play_loop.py:4244 (incremented each turn) | STRUCTURAL (not a per-round reset) |
| `round_index` | combat_controller.py:344 | STRUCTURAL |
| `flat_footed_actors` | combat_controller.py:345 | STRUCTURAL |

No additional uncleared per-round fields found.

### Gate Results

| Gate | Description | Result |
|------|-------------|--------|
| AOR-001 | AoO available in round 2 after round-1 use | PASS |
| AOR-002 | aoo_used_this_round cleared at round boundary | PASS |
| AOR-003 | aoo_count_this_round cleared at round boundary | PASS |
| AOR-004 | Within-round limit still enforced | PASS |
| AOR-005 | Combat Reflexes count resets per round | PASS |
| AOR-006 | deflect_arrows_used not regressed (d1fecb4) | PASS |
| AOR-007 | cleave_used_this_turn still per-turn | PASS |
| AOR-008 | Code inspection: both reset lines in end-of-round block | PASS |

**Total: 8/8 PASS. 0 new regressions.**

### PM Acceptance Notes Confirmation

| # | Note | Status | Evidence |
|---|------|--------|----------|
| 1 | Before/after at play_loop.py:4260-4309 | CONFIRMED | Two lines added at play_loop.py:4350-4351 (post wildshape block, inside round-end `if`). `deflect_arrows_used` adjacent and NOT touched. |
| 2 | AOR-004 within-round limit enforced | CONFIRMED | aoo_used_this_round / aoo_count accumulation code (lines 2496-2504, 3195-3203) unchanged. AOR-004 PASS. |
| 3 | AOR-006 DA regression gate passes | CONFIRMED | deflect_arrows_used not touched. AOR-006 PASS. |
| 4 | AOR-008 code inspection | CONFIRMED | Both reset lines present; within 900 chars of AOO-ROUND-RESET-001 comment. AOR-008 PASS. |
| 5 | active_combat audit -- no other missed per-round fields | CONFIRMED | Full audit table above. 4 per-round/per-turn fields found; all now reset correctly. |

### ML Preflight Checklist

| Check | ID | Status | Notes |
|-------|----|--------|-------|
| Gap verified before writing | ML-001 | PASS | Read play_loop.py:4260-4309. Confirmed aoo_used_this_round and aoo_count_this_round not reset there. Confirmed DA already reset in combat_controller.py. |
| Consume-site verified end-to-end | ML-002 | PASS | Write (play_loop reset) -> Read (aoo check at lines 2496-2499) -> Effect (AoO fires in round 2) -> Test (AOR-001..003). |
| No ghost targets | ML-003 | PASS | Rule 15c: gap confirmed. aoo_used_this_round populated at lines 2497,3196,3953 but never cleared in play_loop path. |
| Dispatch parity checked | ML-004 | PASS | Single reset site needed (play_loop end-of-round). combat_controller already had reset; now in sync. AOR-006/007 confirm no scope creep. |
| Coverage map update | ML-005 | PASS | See below. |
| Commit before debrief | ML-006 | PASS | Backlog a3ac307, code 8d21c33 precede this debrief. |
| PM Acceptance Notes addressed | ML-007 | PASS | All 5 confirmed. |
| Backlog committed before debrief | ML-008 | PASS | a3ac307 is backlog commit, precedes this debrief file. |

### Consumption Chain

| Layer | Location | Action |
|-------|----------|--------|
| Write (set) | play_loop.py:2497, 3196, 3953 | Appends entity to aoo_used_this_round; increments aoo_count |
| Write (clear) | play_loop.py:4350-4351 (this WO) | Resets both fields at round boundary |
| Read (gate) | play_loop.py (AoO eligibility) | Reads list to enforce 1/round limit |
| Effect | AoO fires in round 2+ when not yet used that round |
| Test | AOR-001..AOR-008 |

---

## Pass 2 - PM Summary

Two-line fix at play_loop.py end-of-round block (line 4350-4351). `aoo_used_this_round` and `aoo_count_this_round` now reset to `[]` and `{}` at round boundary, after wildshape tick, inside the `if current_position == last_actor_index:` guard. `deflect_arrows_used` and `cleave_used_this_turn` not touched. Full active_combat per-round field audit conducted -- no other uncleared fields. 8/8 gates. 0 regressions. Backlog committed before debrief.

---

## Pass 3 - Retrospective

### Key Investigation Finding

The dispatch cited `play_loop.py:4260-4309` as the fix location but the actual end-of-round block tail (where the fix landed) is at lines 4344-4351. The dispatch was correct about the reset being MISSING -- wrong about the exact line range. `combat_controller.py` ALREADY had the reset (line 346-347) for the `execute_combat_round()` code path. The SessionOrchestrator path calls `execute_turn()` directly, bypassing `combat_controller`, so it never got the reset. Fix is in the right location.

### Discoveries

**FINDING-ENGINE-AOO-CONTROLLER-RESET-DIVERGENCE-001 (LOW, OPEN)**
Reset now in two places: `combat_controller.py:346-347` AND `play_loop.py:4350-4351`. Structural duplication. Not blocking. Cleanup WO future. Filed to backlog a3ac307.

**FINDING-ENGINE-AOO-ACTIVE-COMBAT-AUDIT-001 (LOW, OPEN/INFORMATIONAL)**
Full per-round field audit complete. All 4 per-round fields now correctly reset. Filed to backlog a3ac307.

### Coverage Map Update

| Mechanic | Status | WO | Notes |
|----------|--------|----|-------|
| AoO round reset (aoo_used_this_round, aoo_count_this_round) | FIXED | WO-ENGINE-AOO-ROUND-RESET-001 | Commit 8d21c33; play_loop end-of-round block |

# DEBRIEF — WO-ENGINE-IMPROVED-OVERRUN-001
**Date:** 2026-02-27
**Batch:** O (WO 1 of 4)
**Gate:** ENGINE-IMPROVED-OVERRUN | IO-001–IO-008 | 8/8 PASS
**Commits:** 3232b76

---

## Pass 1 — Scope Validation

**Gap confirmed:** `improved_overrun` feat was registered in feats.py but neither AoO suppression nor defender-avoidance suppression were wired. Search for "improved_overrun" in aoo.py and maneuver_resolver.py returned zero matches. WO is live.

**SAI check:** Not SAI. Both mechanics required production changes.

---

## Pass 2 — Implementation

### Part 1 — AoO Suppression (play_loop.py)

**Reference pattern:** Batch L wired Improved Disarm/Grapple/Bull Rush suppression in `aidm/core/play_loop.py` lines 2257–2271. The dispatch spec referenced `aoo.py` as the target, but the actual pattern lives in `play_loop.py` after `check_aoo_triggers()` is called. Used the confirmed production pattern.

```python
# play_loop.py (after line 2271)
elif isinstance(combat_intent, OverrunIntent):
    _io_feats = world_state.entities.get(combat_intent.attacker_id, {}).get(EF.FEATS, [])
    if "improved_overrun" in _io_feats:
        aoo_triggers = []
```

### Part 2 — Defender Avoidance Suppression (maneuver_resolver.py)

**Defender-avoid path location:** `maneuver_resolver.py:resolve_overrun()` line 865. The `intent.defender_avoids` boolean controls whether the defender steps aside (returning `overrun_avoided` event without rolling the opposed check).

Implementation: inserted a flag check immediately before the `if intent.defender_avoids:` guard:
```python
_attacker_has_improved_overrun = "improved_overrun" in world_state.entities.get(
    attacker_id, {}
).get(EF.FEATS, [])
if intent.defender_avoids and not _attacker_has_improved_overrun:
```

Did NOT reconstruct the intent dataclass (avoided mutating inputs). Flag approach is cleaner.

---

## Pass 3 — Kernel Check

**KERNEL-touch:** NONE (as specified in dispatch).

**Batch L AoO-suppression pattern cited:** `aidm/core/play_loop.py` lines 2257–2271 (WO-ENGINE-IMPROVED-DISARM-001 / WO-ENGINE-IMPROVED-GRAPPLE-001 / WO-ENGINE-IMPROVED-BULL-RUSH-001). Same `elif isinstance(...)` chain extended.

**Defender-avoid path location documented:** `maneuver_resolver.py:resolve_overrun()`, line 865 at time of implementation. Guard: `if intent.defender_avoids:`.

**FINDING-ENGINE-IMPROVED-OVERRUN-AOO-001:** CLOSED by this WO. AoO suppression wired.

**Test note:** `EF.CONDITIONS` must be `{}` (dict), not `[]` (list). `apply_condition()` uses dict key assignment. Pre-existing pattern confirmed in all working test files.

---

## Loose Threads

None observed outside debrief scope.

# DEBRIEF: WO-ENGINE-SOMATIC-COMPONENT-001

**Date:** 2026-02-26
**Status:** ACCEPTED — 8/8 gate tests passing
**Commit:** e26b2e2

---

## Kernel
KERNEL-02 (somatic component block — PHB p.174)

## Pre-existing State
No somatic guard existed. Verbal guard existed (lines 530-557). ASF block existed.
This WO adds the somatic equivalent of the verbal block.

## Changes Made

### `aidm/core/play_loop.py`
New somatic guard inserted immediately before the metamagic validation block:

```python
# WO-ENGINE-SOMATIC-COMPONENT-001: Somatic component block (PHB p.174)
_has_somatic_sc = getattr(spell, "has_somatic", True)
_is_still_sc = "still" in getattr(intent, "metamagic", ())
if _has_somatic_sc and not _is_still_sc:
    _caster_conds_sc = caster_state.get(EF.CONDITIONS, {})
    _somatic_blocked = "pinned" in _caster_conds_sc or "bound" in _caster_conds_sc
    if _somatic_blocked:
        # emit spell_blocked event, reason=somatic_component_blocked
        return events, world_state, "spell_blocked"
```

**Key design decisions:**
- PINNED and BOUND block somatic (free hand required)
- GRAPPLED does NOT block — grappled caster still has partial arm freedom; Concentration check is the PHB-correct response (future WO)
- Still Spell metamagic (`"still" in metamagic`) removes the somatic requirement → bypasses this guard
- No slot consumed on block (same as verbal block — player must re-declare)
- Event: `spell_blocked` with `reason: somatic_component_blocked`, `blocking_condition: "pinned"|"bound"`

**Execution order:** verbal block → somatic block → metamagic → ASF → resolve

## Gate File
`tests/test_engine_somatic_component_001_gate.py` — 8 tests (SC-001 through SC-008)

## PHB Reference
PHB p.174: "A somatic component is a measured and precise movement of the hand... if you can't move, you can't perform somatic components."
PHB p.156: Grappled casters can still perform somatic components but must make Concentration checks.

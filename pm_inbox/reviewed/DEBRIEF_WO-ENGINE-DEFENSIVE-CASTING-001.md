# Debrief: WO-ENGINE-DEFENSIVE-CASTING-001
**Builder:** Chisel
**Dispatch:** #15 (Batch F)
**Date:** 2026-02-26
**Commit:** 8d2ff92
**Status:** ACCEPTED — 9/9 passed (DC-005 is parametrized: 2 cases)
**KERNEL-03 (Constraint Algebra) flagged to Anvil.**

---

## What Was Done

1. **`aidm/core/spell_resolver.py`** — Added `defensive: bool = False` to `SpellCastIntent` frozen dataclass:
   - PHB p.140: caster declares defensive casting before casting
   - Field is read by `execute_turn` in `play_loop.py`

2. **`aidm/schemas/entity_fields.py`** — Added `EF.CONCENTRATION_BONUS`:
   - `int`: bonus to Concentration checks (CON mod + skill ranks + class bonuses)
   - Default 0 if not set (PHB p.69)

3. **`aidm/core/play_loop.py`** — Added defensive casting gate after `check_aoo_triggers()`:
   - If `aoo_triggers` exist AND intent is `SpellCastIntent` with `defensive=True`:
     - Read `EF.CONCENTRATION_BONUS` from caster
     - Roll d20 + concentration_bonus
     - DC = 15 + spell level (PHB p.175)
     - **Success:** clear `aoo_triggers`, emit `concentration_success`
     - **Failure:** keep `aoo_triggers`, emit `concentration_failed`; if failed by 5+, set `_defensive_cast_disrupted = True`
   - In `SpellCastIntent` routing branch: if `_defensive_cast_disrupted`, consume slot, emit `spell_disrupted`, skip resolve

## Architecture Decision: Event-Based vs Flag

The WO noted two options for sharing the concentration failure flag between `aoo.py` and `spell_resolver.py`.

Decision: **local flag** (`_defensive_cast_disrupted`) scoped to `execute_turn()` in `play_loop.py`. This is cleaner than event-based signaling (which would require reading the event list) and avoids coupling `aoo.py` to `spell_resolver.py`. The entire defensive casting gate runs in `play_loop.py` where both pieces of context are available.

## Pass 3 Notes

**KERNEL-03 (Constraint Algebra):** Defensive casting is a declare-then-check constraint sequence. The caster imposes a constraint on themselves (defensive flag) before casting. The Concentration check is the constraint resolution mechanism. On constraint violation (failed check): the cost escalates (AoO fires; if badly failed, spell is also lost). This is a clean KERNEL-03 pattern — declare, check, branch on outcome.

**AoO suppression:** On concentration success, `aoo_triggers = []` is set before the AoO fire loop. This cleanly suppresses the AoO without needing to modify `aoo.py`.

**Non-threatened caster (DC-007):** If the caster is not threatened, `aoo_triggers` is empty and the defensive casting block never runs. The `defensive` flag is a no-op for unthreatened casters — correct PHB behavior.

**FINDING-ENGINE-CONCENTRATION-OTHER-001 (PHB p.175):** Other concentration check triggers are still NOT STARTED:
- Taking damage while casting (DC 10 + damage dealt)
- Vigorous motion (DC 10)
- Violent weather (DC 5–20)
- Grappled/entangled (DC 20)
Logged as LOW OPEN for next batch triage.

---

## Test Results

| ID | Scenario | Result |
|----|----------|--------|
| DC-001 | Standard cast, threatened → no concentration events | PASS |
| DC-002 | Defensive cast, Concentration succeeds → concentration_success | PASS |
| DC-003 | Defensive cast, Concentration fails → concentration_failed | PASS |
| DC-004 | Defensive cast, fails by 5+ → spell_disrupted | PASS |
| DC-005a | DC formula: magic_missile (1st level) → DC 16 | PASS |
| DC-005b | DC formula: fireball (3rd level) → DC 18 | PASS |
| DC-006 | Defensive success → spell resolves (no spell_disrupted) | PASS |
| DC-007 | Unthreatened caster → no AoO regardless of defensive flag | PASS |
| DC-008 | High conc bonus, fails DC anyway → concentration_failed payload correct | PASS |

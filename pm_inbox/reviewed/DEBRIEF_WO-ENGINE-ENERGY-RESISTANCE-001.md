# Debrief: WO-ENGINE-ENERGY-RESISTANCE-001
**Builder:** Chisel
**Dispatch:** #15 (Batch F)
**Date:** 2026-02-26
**Commit:** 8d2ff92
**Status:** ACCEPTED — 8/8 passed

---

## What Was Done

1. Added `EF.ENERGY_RESISTANCE` to `aidm/schemas/entity_fields.py`:
   - `dict[str, int]`: energy type → resistance value (PHB p.291)
   - e.g., `{"fire": 10, "cold": 5}`
   - Absent key = no resistance. 0 = no resistance.

2. Added energy resistance guard in `aidm/core/spell_resolver.py` after evasion blocks:
   - Reads `spell.damage_type.value` to get energy type string
   - Reads `EF.ENERGY_RESISTANCE` from the target entity
   - Applies `total = max(0, total - resistance)` when both are present and non-zero
   - Only fires when `total > 0` (no overcalculation needed at 0 damage)

## Pass 3 Notes

**KERNEL-14 touch:** Energy resistance is a damage absorption mechanic. The guard is clean: resistance only reduces spell damage, never inverts it (floor at 0). This is correct per PHB p.291.

**Damage type availability:** The implementation reads `spell.damage_type.value` — works when `spell.damage_type` is an enum with a `.value` string. If `damage_type` is `None` (no damage type, e.g., force damage or healing), the guard short-circuits cleanly.

**No `has_somatic` check needed:** Energy resistance applies to all spell damage of matching type regardless of components. No ordering dependency with the verbal/somatic checks.

**FINDING-ENGINE-PHYSICAL-DR-001 noted:** This WO wires energy resistance (elemental damage types). Physical Damage Reduction (`EF.DAMAGE_REDUCTIONS`, e.g., DR 10/magic) is a separate field that applies to weapon damage, not spell energy. It is NOT wired in `spell_resolver.py` and was not in scope. Logged as LOW OPEN.

---

## Test Results

| ID | Scenario | Result |
|----|----------|--------|
| ER-001 | Fire resistance 10, fire spell 20 damage | PASS — takes 10 |
| ER-002 | Fire resistance 10, fire spell 8 damage | PASS — takes 0 (floor) |
| ER-003 | Fire resistance; cold spell hits | PASS — full damage (wrong type) |
| ER-004 | No resistance field; fire spell | PASS — full damage, no crash |
| ER-005 | Correct energy type reduces, wrong type doesn't | PASS |
| ER-006 | HP updated correctly after resistance | PASS |
| ER-007 | Damage floor at 0 (no negative HP from resistance) | PASS |
| ER-008 | Absent EF.ENERGY_RESISTANCE field → full damage, no crash | PASS |

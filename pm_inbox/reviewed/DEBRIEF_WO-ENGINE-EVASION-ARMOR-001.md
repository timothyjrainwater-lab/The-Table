# DEBRIEF — WO-ENGINE-EVASION-ARMOR-001

**Verdict:** PASS [8/8]
**Gate:** ENGINE-EVASION-ARMOR-001
**Date:** 2026-02-26
**Commit:** 4d178f3

## Pass 1 — Per-File Breakdown

**`aidm/core/spell_resolver.py`**
Both evasion check sites located at lines 889–907 (as spec predicted, lines ~892 and ~901 respectively).

**Site 1 — saved=True (line 892):**
Before: `if _target_raw.get(EF.EVASION, False) or _target_raw.get(EF.IMPROVED_EVASION, False): total = 0`
After: armor guard added — `_armor = _target_raw.get(EF.ARMOR_TYPE, "none")`, `_evasion_active = _armor in ("none", "light")`, evasion block wrapped with `if _evasion_active and (...)`.

**Site 2 — saved=False, Improved Evasion (line 901):**
Before: `if _target_raw.get(EF.IMPROVED_EVASION, False): total = total // 2`
After: `if _armor in ("none", "light") and _target_raw.get(EF.IMPROVED_EVASION, False)`.

No new imports. No schema changes. No new fields.

**Read-only verification:**
- `EF.ARMOR_TYPE` confirmed present in `entity_fields.py` (values: "none" | "light" | "medium" | "heavy")
- `EF.ARMOR_TYPE` confirmed set at chargen in `builder.py` for all classes

**`tests/test_engine_evasion_armor_001_gate.py`** — NEW
EA-001 through EA-008 all pass. Coverage:
- EA-001: Rogue, no armor, Evasion, save → 0 damage
- EA-002: Rogue, light armor, Evasion, save → 0 damage
- EA-003: Rogue, medium armor, Evasion, save → half (suppressed)
- EA-004: Rogue, heavy armor, Evasion, save → half (suppressed)
- EA-005: Monk, no armor, Evasion, save → 0 damage
- EA-006: Monk, medium armor, Evasion, save → half (suppressed)
- EA-007: Rogue, no armor, Improved Evasion, fail save → half
- EA-008: Rogue, medium armor, Improved Evasion, fail save → full (suppressed)

## Pass 2 — PM Summary (≤100 words)

Evasion armor restriction fully wired. Two guard checks in `spell_resolver.py` at the Evasion and Improved Evasion blocks — both now check `EF.ARMOR_TYPE` before applying. Evasion active in "none" and "light" armor; suppressed in "medium" and "heavy". Default for missing armor field: "none" (evasion active — correct for creatures with no armor). Zero new imports or schema changes. 8/8 gate pass.

## Pass 3 — Retrospective

**Both sites found at expected lines.** Spec predicted ~892 and ~901; confirmed at 892 and 901.

**Armor default behavior:** `_target_raw.get(EF.ARMOR_TYPE, "none")` — if the field is absent, defaults to "none", meaning evasion is active. This is correct for creatures with no armor type set (bare skin, magical beings, etc.).

**Other resolver check:** No other resolver (AoO, save_resolver.py) has an evasion check. `spell_resolver.py` is the only evasion application site.

**Entity data with EF.EVASION but no EF.ARMOR_TYPE:** These will default to "none" (evasion active), which is the correct and safe default.

**Open findings:** None from this WO.

## Radar

- ENGINE-EVASION-ARMOR-001: 8/8 PASS
- Both evasion sites at expected lines (892, 901)
- Default armor type "none" → evasion active (correct for unarmored entities/creatures)
- No other evasion check sites found in the codebase
- Zero new failures in engine gate regression

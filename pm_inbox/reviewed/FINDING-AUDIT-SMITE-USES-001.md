# FINDING-AUDIT-SMITE-USES-001 — Paladin Smite Evil Uses/Day Level Progression

**ID:** FINDING-AUDIT-SMITE-USES-001
**Severity:** HIGH
**Status:** OPEN
**Found by:** AUDIT-WO-004 (2026-02-27)
**Lifecycle:** NEW

---

## Description

Paladin Smite Evil uses/day level progression does not match PHB Table 3-4.

## Evidence

**PHB p.44 / Table 3-4:** "once per day for every five paladin levels"
- Level 1: 1/day
- Level 6: 2/day
- Level 11: 3/day
- Level 16: 4/day
- Level 21: 5/day (theoretical)

**Code (`builder.py` CLASS_FEATURES dict, lines ~1362-1380):**
- Level 1: `smite_evil_1_per_day` → 1/day ✓
- Level 5: `smite_evil_2_per_day` → 2/day (PHB says L6 — off by 1)
- Level 8: `smite_evil_3_per_day` → 3/day (PHB says L11 — off by 3)
- Level 10: `smite_evil_4_per_day` → 4/day (PHB says L16 — off by 6)
- Level 12: `smite_evil_5_per_day` → 5/day (PHB says L21 — off by 9)

## Impact

Paladins gain additional smite uses 1–9 levels earlier than RAW. Mid-to-high level paladins have significantly more smite uses than PHB allows. This is a combat power deviation.

## Fix

Update `_CLASS_FEATURES["paladin"]` in `builder.py` so smite uses unlock at levels 1, 6, 11, 16, 21.

## Corrective WO

Requires a corrective WO to update `builder.py` CLASS_FEATURES dict and update gate test expectations for `test_engine_divine_grace_gate.py` (if it tests smite uses).

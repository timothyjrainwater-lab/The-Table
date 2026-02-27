# Debrief: WO-ENGINE-IMPROVED-MANEUVER-BONUSES-001
**Artifact ID:** DEBRIEF_WO-ENGINE-IMPROVED-MANEUVER-BONUSES-001
**WO:** WO-ENGINE-IMPROVED-MANEUVER-BONUSES-001
**Batch:** P
**Commit:** 336f04d
**Date:** 2026-02-27
**Result:** ACCEPTED — 8/8 IMB tests PASS

**Closes:** FINDING-ENGINE-IMPROVED-DISARM-BONUS-001, FINDING-ENGINE-IMPROVED-GRAPPLE-BONUS-001, FINDING-ENGINE-IMPROVED-BULL-RUSH-BONUS-001, FINDING-ENGINE-IMPROVED-TRIP-BONUS-001, FINDING-ENGINE-IMPROVED-SUNDER-BONUS-001

---

## Pass 1: Context Dump

**Target file:** `aidm/core/maneuver_resolver.py`

**Audit finding:** The dispatch intelligence note stated "Batch L wired +4 in main path for disarm/grapple/bull_rush." This was **FALSE**. Batch L only added AoO suppression in `play_loop.py` (the `elif isinstance(intent, DisarmIntent): if feat in feats: aoo_triggers = []` chain). The +4 bonus to the opposed check modifier was **NOT wired at any call site for any of the 5 maneuvers** before this WO. All 5 insertions were new work.

### Insertions in `aidm/core/maneuver_resolver.py`

**Bull Rush** — after `attacker_modifier = attacker_str + attacker_size + charge_bonus`:
```python
if "improved_bull_rush" in feats:
    attacker_modifier += 4
```

**Trip** — after `attacker_modifier = attacker_str + attacker_size`:
```python
if "improved_trip" in feats:
    attacker_modifier += 4
```

**Sunder** — after `attacker_modifier = attacker_bab + attacker_str + attacker_size`:
```python
if "improved_sunder" in feats:
    attacker_modifier += 4
```

**Disarm** — after weapon-type modifier block (light: -4, two-handed: +4):
```python
if "improved_disarm" in world_state.entities.get(attacker_id, {}).get(EF.FEATS, []):
    attacker_modifier += 4
```

**Grapple** — after `attacker_grapple_modifier = attacker_bab + attacker_str + attacker_size`:
```python
if "improved_grapple" in feats:
    attacker_grapple_modifier += 4
```

Secondary call sites: None exist. Each maneuver has exactly one opposed check computation in `maneuver_resolver.py`. No secondary paths in `play_loop.py` (AoO suppression only) or `schemas/maneuvers.py` (dataclasses only).

---

## Pass 2: PM Summary (≤100 words)

+4 bonus added to `attacker_modifier` at the single opposed check site for each of 5 maneuvers in `maneuver_resolver.py`. Batch L claim of "already wired for disarm/grapple/bull_rush" was FALSE — Batch L only added AoO suppression. All 5 were new work. Secondary call site audit: each maneuver has exactly one opposed check path; no additional insertion points required. All 5 FINDINGs closed. 8/8 IMB gates pass, zero regressions.

---

## Pass 3: Retrospective

**Batch L gap documented:** The Batch L debrief and MEMORY.md carried incorrect information — "+4 wired in Batch L main path for disarm/grapple/bull_rush." Full audit of `maneuver_resolver.py` confirmed zero +4 insertions at any call site before this WO. The Batch L work was exclusively AoO suppression in `play_loop.py`. This should be corrected in MEMORY.md (Batch L Patterns section) and is documented as FINDING below.

**Feat variable naming:** Bull rush, trip, sunder, grapple use `feats` (local var from `attacker.get(EF.FEATS, [])`). Disarm uses direct entity lookup (`world_state.entities.get(attacker_id, {}).get(EF.FEATS, [])`) because `feats` is not a local var at that insertion point. Both patterns are correct.

**IMB-001 vs dispatch numbering:** Dispatch spec labeled IMB-001 as "Improved Trip" and IMB-002 as "Improved Sunder" but gate file was written in the pattern IMB-001=Disarm, IMB-002=Sunder, etc. (matching the order in maneuver_resolver.py). Numbering difference is cosmetic; all 5 maneuvers are covered.

**FINDINGs closed:**
- FINDING-ENGINE-IMPROVED-DISARM-BONUS-001 → CLOSED
- FINDING-ENGINE-IMPROVED-GRAPPLE-BONUS-001 → CLOSED
- FINDING-ENGINE-IMPROVED-BULL-RUSH-BONUS-001 → CLOSED
- FINDING-ENGINE-IMPROVED-TRIP-BONUS-001 → CLOSED
- FINDING-ENGINE-IMPROVED-SUNDER-BONUS-001 → CLOSED

---

## Radar

| Finding | Severity | Status |
|---------|----------|--------|
| FINDING-ENGINE-IMPROVED-MANEUVER-BATCH-L-GAP-001 | LOW | CLOSED — Batch L debrief claimed +4 wired for disarm/grapple/bull_rush in main path. Audit confirmed this was false. All 5 bonuses implemented fresh in WO2. MEMORY.md Batch L patterns section carried incorrect information; corrected via this debrief. |
| FINDING-ENGINE-IMPROVED-DISARM-BONUS-001 | LOW | CLOSED — disarm +4 wired at line ~1468 of maneuver_resolver.py |
| FINDING-ENGINE-IMPROVED-GRAPPLE-BONUS-001 | LOW | CLOSED — grapple +4 wired at attacker_grapple_modifier computation |
| FINDING-ENGINE-IMPROVED-BULL-RUSH-BONUS-001 | LOW | CLOSED — bull rush +4 wired after charge_bonus computation |
| FINDING-ENGINE-IMPROVED-TRIP-BONUS-001 | LOW | CLOSED — trip +4 wired at trip STR opposed check |
| FINDING-ENGINE-IMPROVED-SUNDER-BONUS-001 | LOW | CLOSED — sunder +4 wired at sunder BAB+STR opposed check |

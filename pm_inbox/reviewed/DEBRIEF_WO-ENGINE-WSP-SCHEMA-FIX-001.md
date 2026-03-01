# DEBRIEF: WO-ENGINE-WSP-SCHEMA-FIX-001 - Weapon Specialization Schema Fix

**Lifecycle:** ARCHIVE
**Commit:** 5dc8391 (code), 0e236ce (backlog)
**Filed by:** Chisel
**Session:** 26
**Date:** 2026-03-01
**WO:** WO-ENGINE-WSP-SCHEMA-FIX-001
**Status:** FILED - awaiting PM verdict

---

## Pass 1 - Context Dump

### Summary

WSP schema drift fixed at both compute sites. Canonical key changed from `weapon_specialization_{weapon_type}` to `weapon_specialization_{weapon_name}`. `weapon_specialization_active` event now emitted. FAGU-010 fixture updated. Double-count discovered and fixed (separate finding, closed this WO). Backlog committed before debrief.

### Files Changed

| File | Type | Change |
|------|------|--------|
| `aidm/core/attack_resolver.py` | MODIFIED | WSP key fix + event emission; `base_damage += _wsp_bonus` removed (double-count prevention) |
| `aidm/core/full_attack_resolver.py` | MODIFIED | WSP key fix; `_wsp_bonus = 0` in dead-path `resolve_single_attack_with_critical` |
| `tests/test_engine_full_attack_unify_gate.py` | MODIFIED | FAGU-010: `weapon_specialization_light` -> `weapon_specialization_longsword` |
| `tests/test_engine_wsp_schema_gate.py` | NEW | WSS-001..WSS-008 gate tests |

---

### PM Acceptance Note 1 -- Exact line before/after (attack_resolver.py:963)

**BEFORE:**
```python
_wsp_bonus = 2 if f"weapon_specialization_{intent.weapon.weapon_type}" in _attacker_feats else 0
base_damage += _wsp_bonus
```

**AFTER:**
```python
# WO-ENGINE-WSP-SCHEMA-FIX-001: WSP handled by feat_resolver.get_damage_modifier()
# using canonical weapon_name key in feat_context. _wsp_bonus retained for event emission only.
_wsp_bonus = 2 if (_weapon_name and f"weapon_specialization_{_weapon_name}" in _attacker_feats) else 0
if _wsp_bonus and _weapon_name:
    events.append(Event(
        event_id=current_event_id,
        event_type="weapon_specialization_active",
        timestamp=timestamp,
        payload={"actor_id": intent.attacker_id, "weapon_name": _weapon_name},
        citations=[{"source_id": "681f92bc94ff", "page": 102}],
    ))
    current_event_id += 1
# NOTE: do NOT add _wsp_bonus to base_damage -- feat_resolver.get_damage_modifier() adds it
```

`_weapon_name` is extracted earlier in the function (WO-ENGINE-WF-SCHEMA-FIX-001 pattern, line 461):
```python
_ef_weapon = attacker.get(EF.WEAPON, {})
_weapon_name = (
    _ef_weapon.get("name", "").lower().replace(" ", "_")
    if isinstance(_ef_weapon, dict)
    else str(_ef_weapon).lower().replace(" ", "_")
)
```

### PM Acceptance Note 2 -- Parallel paths confirmed

| Path | Location | WSP handling | Notes |
|------|----------|-------------|-------|
| Path A | `attack_resolver.py:964` | Event emission only; NOT added to base_damage | Single-attack path; feat_resolver is damage source |
| Path B | `full_attack_resolver.py:429` | `_wsp_bonus = 0` (zeroed) | Dead-path (`resolve_single_attack_with_critical`, retired by FAGU); resolve_full_attack delegates to resolve_attack per-hit |
| Path C | `feat_resolver.get_damage_modifier()` | `weapon_specialization_{weapon_name}` canonical key | Single canonical damage source; called from attack_resolver via `feat_damage_modifier` at line 949+981 |

**Delegation chain for full attack:** `resolve_full_attack` -> `resolve_attack` (per hit) -> `feat_resolver.get_damage_modifier()` (WSP +2 in `feat_modifier`) + `weapon_specialization_active` event (attack_resolver). One path, no double-count.

### PM Acceptance Note 3 -- FAGU-010 fixture update

**BEFORE:**
```python
a_wsp = _attacker(feats=["weapon_focus_longsword", "weapon_specialization_light"])
```

**AFTER:**
```python
a_wsp = _attacker(feats=["weapon_focus_longsword", "weapon_specialization_longsword"])  # WO-ENGINE-WSP-SCHEMA-FIX-001
```

FAGU-010 passes: `test_fagu010_weapon_specialization_no_double_count` -- 10/10 FAGU gates pass.

### PM Acceptance Note 4 -- WSS-002 confirms old key dead

WSS-002 fixture: `feats=["weapon_focus_longsword", "weapon_specialization_light"]` with a longsword attacker.
`_weapon_name = "longsword"` -> check: `"weapon_specialization_longsword" in feats` -> False (feat is `weapon_specialization_light`).
Result: `_wsp_bonus = 0`, `feat_modifier = 0` from feat_resolver. Old type-based key returns no bonus. PASS.

### PM Acceptance Note 5 -- WSS-007 parity gate passes

Full attack path: `resolve_full_attack` -> `resolve_attack` per-hit -> `feat_resolver` adds +2 per hit.
Single attack path: `resolve_attack` -> `feat_resolver` adds +2.
Both confirmed +2 per hit. WSS-007 PASS.

### Gate Results

| Gate | Description | Result |
|------|-------------|--------|
| WSS-001 | Canonical name key activates WSP | PASS |
| WSS-002 | Old type-based key no longer fires | PASS |
| WSS-003 | WSP +2 damage observable | PASS |
| WSS-004 | WF+WSP canonical fixture: weapon_specialization_active fires | PASS |
| WSS-005 | weapon_specialization_active event has weapon_name payload | PASS |
| WSS-006 | FAGU-010 still passes with canonical key | PASS |
| WSS-007 | Full attack parity: same +2 per hit | PASS |
| WSS-008 | No double-count: +2 exactly once per hit | PASS |

**Total: 8/8 PASS. FAGU 10/10 PASS. 0 new regressions.**

### PM Acceptance Notes Confirmation

| # | Note | Status | Evidence |
|---|------|--------|----------|
| 1 | Show exact line before/after attack_resolver.py:963 | CONFIRMED | weapon_type -> weapon_name; base_damage += _wsp_bonus removed; event emission added |
| 2 | Parallel paths confirmed (full_attack delegates or independently computed) | CONFIRMED | Path A: event only. Path B: zeroed (dead). Path C: feat_resolver canonical. No double-count. |
| 3 | FAGU-010 updated -- show old and new key | CONFIRMED | weapon_specialization_light -> weapon_specialization_longsword. FAGU-010 PASS. |
| 4 | WSS-002 confirms old key dead | CONFIRMED | type-key `weapon_specialization_light` with longsword attacker: bonus=0. WSS-002 PASS. |
| 5 | WSS-007 parity gate passes | CONFIRMED | Full attack +2 per hit == single attack +2. WSS-007 PASS. |

### ML Preflight Checklist

| Check | ID | Status | Notes |
|-------|----|--------|-------|
| Gap verified before writing | ML-001 | PASS | Read attack_resolver.py:963 and full_attack_resolver.py:428 before edits. Both weapon_type confirmed. |
| Consume-site verified end-to-end | ML-002 | PASS | Write (key fix) -> Read (feat_resolver canonical path) -> Effect (feat_modifier=2 in damage_roll event) -> Test (WSS-001..008) |
| No ghost targets | ML-003 | PASS | Rule 15c: both weapon_type sites confirmed live before fixing |
| Dispatch parity checked | ML-004 | PASS | Path A (attack_resolver) and Path B (full_attack_resolver) both checked. Path C (feat_resolver) identified as canonical. |
| Coverage map update | ML-005 | PASS | See below |
| Commit before debrief | ML-006 | PASS | Backlog 0e236ce, code 5dc8391 precede this debrief |
| PM Acceptance Notes addressed | ML-007 | PASS | All 5 confirmed |
| Backlog committed before debrief | ML-008 | PASS | 0e236ce is backlog commit, filed before this debrief |

### Consumption Chain

| Layer | Location | Action |
|-------|----------|--------|
| Write (chargen) | builder.py | EF.FEATS: `weapon_specialization_longsword` (canonical) |
| Read (feat_resolver) | feat_resolver.get_damage_modifier() | `weapon_specialization_{weapon_name}` key checked; +2 if match |
| Read (event emit) | attack_resolver.py:964 | `weapon_specialization_active` event emitted on match |
| Effect | `feat_modifier=2` in damage_roll payload; `damage_total` reflects +2 per hit |
| Test | WSS-001..WSS-008 |

---

## Pass 2 - PM Summary

WSP schema fixed at both compute sites (attack_resolver, full_attack_resolver). Canonical key `weapon_specialization_{weapon_name}` (EF.WEAPON["name"].lower().replace(" ","_")) matches WF fix pattern (686324d). `weapon_specialization_active` event now emitted. FAGU-010 fixture updated. Double-count discovered (attack_resolver was adding +2 AND feat_resolver was adding +2) -- double-count fixed by removing redundant `base_damage += _wsp_bonus` in attack_resolver (feat_resolver is canonical damage source). 8/8 gate, 10/10 FAGU, 0 regressions. Backlog committed before debrief.

---

## Pass 3 - Retrospective

### Discoveries During Execution

**FINDING-ENGINE-WSP-DOUBLE-COUNT-001 (CLOSED this WO)**
Pre-existing double-count: `attack_resolver._wsp_bonus` (+2 to base_damage) AND `feat_resolver.get_damage_modifier()` (+2 via feat_context[weapon_name]) both fired. Previously masked because weapon_type-based key never matched. Fixing schema exposed the double-count (wsp_val=6, no_val=2 on a 1d6 hit = +4 not +2). Fixed by removing `base_damage += _wsp_bonus` from attack_resolver. Filed to backlog, committed 0e236ce before this debrief.

**FINDING-ENGINE-WSP-FAR-DEAD-PATH-001 (LOW, OPEN)**
`resolve_single_attack_with_critical()` in full_attack_resolver.py is dead code (retired by FAGU). Contains WSP logic (now zeroed). Should be removed in future cleanup WO. No runtime impact. Filed to backlog 0e236ce.

### Kernel Touches

None. Schema fix only. No lifecycle, topology, or boundary law changes.

### Coverage Map Update

| Mechanic | Status | WO | Notes |
|----------|--------|----|-------|
| Weapon Specialization schema | FIXED | WO-ENGINE-WSP-SCHEMA-FIX-001 | Commit 5dc8391; canonical name key; double-count resolved |

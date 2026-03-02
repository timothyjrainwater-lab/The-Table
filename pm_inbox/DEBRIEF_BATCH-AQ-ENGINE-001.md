# DEBRIEF — Batch AQ Engine
**Commit:** 08f61e9
**WOs:** WO-ENGINE-NONLETHAL-SHADOW-PATH-001 + WO-ENGINE-CATALOG-TABLE75-COMPLETENESS-001
**Gates:** 16/16 (NSP-001..008 + CT75-001..008)
**Verdict Review Class:** SELF-REVIEW
**Date:** 2026-03-02

---

## Pass 1 — Context Dump

### WO1: WO-ENGINE-NONLETHAL-SHADOW-PATH-001

**File changed:** `aidm/core/attack_resolver.py`

**Helpers added** (module-level, above `resolve_attack`):

```python
# Lines ~309–338 after commit
def _compute_finesse_delta(attacker_entity: dict, weapon_intent) -> int:
    feats = attacker_entity.get(EF.FEATS, [])
    if "weapon_finesse" in feats and weapon_intent.is_light:
        return attacker_entity.get(EF.DEX_MOD, 0) - attacker_entity.get(EF.STR_MOD, 0)
    return 0

def _compute_effective_crit_range(weapon_intent, attacker_feats: list) -> int:
    base_range = weapon_intent.critical_range
    weapon_type = getattr(weapon_intent, 'weapon_type', None)
    ic_specific = f"improved_critical_{weapon_type}" if weapon_type else None
    if "improved_critical" in attacker_feats or (ic_specific and ic_specific in attacker_feats):
        return max(1, 21 - (21 - base_range) * 2)
    return base_range
```

**resolve_attack refactor:**

Before (lines 685–690 WF, 739–742 ImprCrit):
```python
# WF inline (6 lines)
_finesse_delta = 0
_attacker_feats = attacker.get(EF.FEATS, [])
if "weapon_finesse" in _attacker_feats and intent.weapon.is_light:
    _str_mod = attacker.get(EF.STR_MOD, 0)
    _dex_mod = attacker.get(EF.DEX_MOD, 0)
    _finesse_delta = _dex_mod - _str_mod
# ImprCrit inline (4 lines)
_ic_eff_range = intent.weapon.critical_range
_ic_specific = f"improved_critical_{getattr(intent.weapon, 'weapon_type', None)}" if ...
if "improved_critical" in _attacker_feats or (_ic_specific and _ic_specific in _attacker_feats):
    _ic_eff_range = max(1, 21 - (21 - intent.weapon.critical_range) * 2)
```

After (~line 718, ~line 767):
```python
_attacker_feats = attacker.get(EF.FEATS, [])
_finesse_delta = _compute_finesse_delta(attacker, intent.weapon)  # WO-ENGINE-NONLETHAL-SHADOW-PATH-001

_ic_eff_range = _compute_effective_crit_range(intent.weapon, _attacker_feats)  # WO-ENGINE-NONLETHAL-SHADOW-PATH-001
is_threat = (d20_result >= _ic_eff_range)
```

**resolve_nonlethal_attack refactor:**

Before (lines 1441–1447 WF, 1451–1455 ImprCrit):
```python
# WF inline shadow duplicate (6 lines)
_nl_finesse_delta = 0
_nl_attacker_feats = attacker.get(EF.FEATS, [])
if "weapon_finesse" in _nl_attacker_feats and intent.weapon.is_light:
    _nl_str_mod = attacker.get(EF.STR_MOD, 0)
    _nl_dex_mod = attacker.get(EF.DEX_MOD, 0)
    _nl_finesse_delta = _nl_dex_mod - _nl_str_mod
# ImprCrit inline shadow duplicate (5 lines)
_nl_ic_eff_range = intent.weapon.critical_range
_nl_ic_specific = f"improved_critical_{_nl_weapon_type}" if _nl_weapon_type else None
if "improved_critical" in _nl_attacker_feats or (_nl_ic_specific and _nl_ic_specific in _nl_attacker_feats):
    _nl_ic_eff_range = max(1, 21 - (21 - intent.weapon.critical_range) * 2)
```

After (~line 1467, ~line 1472):
```python
_nl_attacker_feats = attacker.get(EF.FEATS, [])
_nl_finesse_delta = _compute_finesse_delta(attacker, intent.weapon)  # WO-ENGINE-NONLETHAL-SHADOW-PATH-001
attack_bonus_with_conditions = adjusted_attack_bonus + attacker_modifiers.attack_modifier + _nl_finesse_delta

_nl_ic_eff_range = _compute_effective_crit_range(intent.weapon, _nl_attacker_feats)  # WO-ENGINE-NONLETHAL-SHADOW-PATH-001
is_threat = (d20_result >= _nl_ic_eff_range)
```

**Parity confirmation:**
- `resolve_attack output before == resolve_attack output after for identical inputs` — confirmed. Pure extraction, no logic change.
- `resolve_nonlethal_attack output before == resolve_nonlethal_attack output after for identical inputs` — confirmed.
- `_nl_attacker_feats` passed directly from the already-extracted variable at line 1467; NOT re-read from entity.

**Gate file:** `tests/test_engine_nonlethal_shadow_path_gate.py` — 8 tests, all pass.

**WF regression:** `test_engine_weapon_finesse_gate.py` (WF-001..008) + `test_engine_wf_schema_gate.py` (WFS-001..008) — 16/16 pass.

---

### WO2: WO-ENGINE-CATALOG-TABLE75-COMPLETENESS-001

**File changed:** `aidm/data/equipment_catalog.json`

**Entries added** (5 new keys under `"weapons"`, inserted after `shortbow`):

| Key | damage_dice | critical_range | proficiency_group | range_increment_ft | grip_hands | PHB cite |
|-----|-------------|----------------|-------------------|--------------------|------------|----------|
| `crossbow_heavy` | 1d10 | 19 | martial | 120 | 2 | PHB Table 7-5 p.116 |
| `hand_crossbow` | 1d4 | 19 | exotic | 30 | 1 | PHB Table 7-5 p.116 |
| `light_hammer` | 1d4 | 20 | simple | 20 | 1 | PHB Table 7-5 p.116 |
| `throwing_axe` | 1d6 | 20 | martial | 10 | 1 | PHB Table 7-5 p.116 |
| `bola` | 1d4 | 20 | exotic | 10 | 1 | PHB Table 7-5 p.116 |

All 5 entries include `grip_hands` field for FHS setter compatibility.

**net:** NOT added. FINDING-ENGINE-NET-CATALOG-SPECIAL-001 filed (LOW) — entangle mechanic deferred, damage_dice would be "—" which parse_damage_dice() cannot handle.

**Catalog count:** 22 → 27 weapons. JSON validates cleanly (json.load() no exception).

**Gate file:** `tests/test_engine_catalog_table75_gate.py` — 8 tests, all pass.

---

### Consumption Chain Confirmation

**WO1 (NSP):**
- Layer 1 (Write): `_compute_finesse_delta`, `_compute_effective_crit_range` added to `attack_resolver.py`
- Layer 2 (Consume): Called from `resolve_attack` (~718, ~767) and `resolve_nonlethal_attack` (~1467, ~1472)
- Layer 3 (Effect): No behavior change — pure extraction. Parity guaranteed by shared helper.
- Layer 4 (Test): NSP-006/NSP-007 (explicit parity), NSP-008 (nonlethal WF end-to-end canary)

**WO2 (CT75):**
- Layer 1 (Write): 5 entries in `equipment_catalog.json`
- Layer 2 (Consume): `builder.py` reads catalog by key during chargen; `grip_hands ≥ 2` → FHS setter sets EF.FREE_HANDS
- Layer 3 (Effect): Characters built with these weapons get correct grip_hands → FREE_HANDS → Deflect Arrows eligibility
- Layer 4 (Test): CT75-001..008 (catalog field verification + canary)

---

## Pass 2 — PM Summary

WO1 extracted two module-level private helpers (`_compute_finesse_delta`, `_compute_effective_crit_range`) from inline duplicates in `resolve_attack` and `resolve_nonlethal_attack`. Zero behavior change confirmed; parity proven by NSP-006/007. `_nl_attacker_feats` passed directly, not re-extracted. WO2 added 5 PHB Table 7-5 p.116 weapons (all with `grip_hands`) to `equipment_catalog.json`; net excluded with FINDING filed. 16/16 gates pass; 16/16 WF regressions pass.

---

## Pass 3 — Retrospective

- Pre-existing import error in `test_engine_improved_critical_001_gate.py` (`resolve_single_attack_with_critical` from `full_attack_resolver`) — this predates Batch AQ and is unrelated. Filed in Radar below. NSP-004/005 cover the same ImprCrit doubling logic directly.
- Coverage map updated: Nonlethal attack row added (Section 1), Ranged/thrown catalog row added (Section 12), equipment_catalog.json count row updated (Section 18).
- `_nl_attacker_feats` variable naming confirmed: passed from already-extracted variable per WO spec — no duplicate entity read.

This WO touches no kernel files (CHISEL_KERNEL_001.md not modified).

---

## Radar

| Finding ID | Severity | Status | Description |
|------------|----------|--------|-------------|
| FINDING-ENGINE-NET-CATALOG-SPECIAL-001 | LOW | OPEN | net (PHB p.116) excluded from catalog — entangle mechanic deferred. damage_dice would be "—". Needs dedicated WO when thrown-weapon special mechanics designed. |
| FINDING-ENGINE-IMPRCRIT-001-GATE-IMPORT-BROKEN | LOW | OPEN | `test_engine_improved_critical_001_gate.py` imports `resolve_single_attack_with_critical` from `full_attack_resolver` — symbol does not exist. Pre-existing error, predates Batch AQ. Needs triage WO. |

---

## Coverage Map Updates

- **Section 1:** Row "Nonlethal attack (resolve_nonlethal_attack)" added — IMPLEMENTED, shadow path removed Batch AQ, NSP-001..008.
- **Section 12:** Row "Ranged/thrown weapon catalog (Table 7-5)" added — IMPLEMENTED, 27 weapons total, CT75-001..008.
- **Section 18:** `equipment_catalog.json` count updated 22 → 27 weapons.

---

## PM Acceptance Notes Review

1. **PHB p.116 exact values** — ✓ All 5 entries cite "PHB Table 7-5 p.116". Damage dice, crit range, range increment match table exactly per WO spec.
2. **`grip_hands` field required** — ✓ All 5 entries have `grip_hands` field.
3. **net exclusion documented** — ✓ net NOT added. FINDING-ENGINE-NET-CATALOG-SPECIAL-001 filed (LOW) in Radar.
4. **No broken tests** — ✓ WF-001..016 pass; FHS gates pass (not touched). 16/16 AQ gates pass.
5. **JSON validity** — ✓ json.load() runs without exception.
6. **Zero regressions (WF/ImprCrit)** — ✓ WF-001..008 + WFS-001..008 all 16 pass.
7. **Helper placement** — ✓ Both helpers are module-level private (leading underscore), placed above `resolve_attack`.
8. **No behavior delta** — ✓ Explicitly confirmed above: "resolve_attack output before == resolve_attack output after for identical inputs."
9. **NSP-006/007 present** — ✓ Both parity tests in gate file and passing.
10. **`_nl_attacker_feats` not re-extracted** — ✓ Passed from already-extracted variable at line 1467.

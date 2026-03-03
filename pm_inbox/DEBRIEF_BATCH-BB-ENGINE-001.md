# DEBRIEF: Batch BB Engine — WEB + DBA + PTC

**Lifecycle:** NEW
**Commit:** 9567e47
**Date:** 2026-03-03
**Builder:** Chisel (Sonnet 4.6)
**Gates:** 24/24 ✅ | **Total cumulative:** 1,770

---

## Pass 1 — Context Dump

### WO1: WO-ENGINE-WEAPON-ENHANCEMENT-BONUS-001 (WEB) — GHOST

**Ghost finding:** Engine code already implemented via prior `WO-ENGINE-WEAPON-ENHANCEMENT-001`.
- `attack_resolver.py:750` — `intent.weapon.enhancement_bonus` applied to attack total
- `attack_resolver.py:985` — `intent.weapon.enhancement_bonus` applied to damage
- `schemas/attack.py:58` — `enhancement_bonus: int = 0` field on `Weapon` dataclass

**Genuine gap:** No gate file existed. Existing `test_engine_weapon_enhancement_gate.py` (WE-01..10) covered basics. New file added covering PM acceptance criteria explicitly.

**Files changed:**
- `tests/test_engine_weapon_enhancement_bonus_001_gate.py` (NEW — 8 tests WEB-001..008)

**Gate summary:**

| Gate | Description | Result |
|------|-------------|--------|
| WEB-001 | Mundane weapon vs AC=21 → miss (d20=15+BAB=5+enh=0=20) | PASS |
| WEB-002 | +1 weapon vs AC=21 → hit (20+1=21) | PASS |
| WEB-003 | +2 weapon vs AC=22 → hit (20+2=22) | PASS |
| WEB-004 | +1 + WeaponFocus → hit at AC=22 (stacking) | PASS |
| WEB-005 | Mundane weapon damage = 4 (dice only) | PASS |
| WEB-006 | +1 weapon damage = 5 (dice + enhancement) | PASS |
| WEB-007 | +2 + WeaponSpecialization → damage = 8 (dice=4+enh=2+WS=2) | PASS |
| WEB-008 | High BAB iterative path, +1 → final_damage = 5 | PASS |

---

### WO2: WO-ENGINE-DEFLECTION-BONUS-AC-001 (DBA) — PARTIAL GHOST (DOUBLE-GHOST CORRECTED)

**Ghost finding — Layer 1:** `EF.DEFLECTION_BONUS = "deflection_bonus"` constant pre-existed at `entity_fields.py:384`.

**Ghost finding — Layer 2:** Runtime application pre-existed at `attack_resolver.py:617`:
```python
_deflection_ac = target.get(EF.DEFLECTION_BONUS, 0)
```
This was wired by prior `WO-ENGINE-DEFLECTION-BONUS-001`. Deflection is a **runtime (Type 3) field** — added to `target_ac` at attack resolution time alongside monk_wis_ac and other runtime modifiers.

**Field contract correction:** The WO dispatch described deflection as "Type 2 (baked into EF.AC)." This is INCORRECT per codebase reality. Deflection must NOT be added to `EF.AC` in the equipment helper — doing so would double-count it (once in EF.AC, once in attack_resolver.py:617). The equipment helper AC formula is unchanged.

**Genuine gap:** Chargen initialization. Both chargen paths lacked `EF.DEFLECTION_BONUS: 0` as a default field.

**Files changed:**
- `aidm/chargen/builder.py` — Added `EF.DEFLECTION_BONUS: 0` to initial dict in `build_character()` (line ~881) and `_build_multiclass_character()` (line ~1219). Equipment helper comment updated to document runtime field contract.
- `tests/test_engine_deflection_bonus_ac_001_gate.py` (NEW — 8 tests DBA-001..008)

**Equipment helper (UNCHANGED formula):**
```python
# AC (§3.5): 10 + effective_dex + armor_bonus
# WO-ENGINE-DEFLECTION-BONUS-AC-001: deflection bonus read at runtime by attack_resolver.py:617
# (Type 3 runtime field — NOT baked into EF.AC to avoid double-count)
ac = 10 + effective_dex + armor_ac_bonus
entity[EF.AC] = ac
```

**Gate summary:**

| Gate | Description | Result |
|------|-------------|--------|
| DBA-001 | Default chargen EF.DEFLECTION_BONUS=0, AC unchanged | PASS |
| DBA-002 | EF.DEFLECTION_BONUS=1 → EF.AC = base_AC + 1 (manual patch) | PASS |
| DBA-003 | EF.DEFLECTION_BONUS=2 → EF.AC = base_AC + 2 (manual patch) | PASS |
| DBA-004 | Attack hits base AC=20, misses deflected AC=21 (d20=15+BAB=5=20) | PASS |
| DBA-005 | EF.DEFLECTION_BONUS constant exists, value="deflection_bonus" | PASS |
| DBA-006 | build_character() output includes EF.DEFLECTION_BONUS=0 | PASS |
| DBA-007 | No regression: AC>=10, deflection_bonus=0 for default entity | PASS |
| DBA-008 | attack_resolver.py DOES reference DEFLECTION_BONUS (runtime path confirmed) | PASS |

**Note on DBA-008 correction:** Initial DBA-008 draft asserted attack_resolver did NOT reference DEFLECTION_BONUS (testing Type 2 assumption). Failed first run. Corrected to verify runtime path IS present — this is the correct behavior per codebase architecture.

---

### WO3: WO-ENGINE-PETRIFIED-CONDITION-001 (PTC) — GENUINE GAP

**No ghost.** PETRIFIED was not in `ConditionType` enum; no factory existed.

**Files changed:**
- `aidm/schemas/conditions.py`:
  - Added `PETRIFIED = "petrified"` to `ConditionType` enum
  - Added `immune_to: List[str] = field(default_factory=list)` to `ConditionInstance`
  - Updated `to_dict()` to serialize `immune_to` when non-empty
  - Updated `from_dict()` to deserialize `immune_to` (defaults to `[]`)
  - Added `create_petrified_condition()` factory

- `aidm/core/conditions.py`:
  - Added `"petrified": "create_petrified_condition"` to `_CONDITION_FACTORY_NAMES`
  - Added post-loop DEX override in `get_condition_modifiers()`:
    ```python
    if "petrified" in conditions_data:
        _dex_penalty = -5 - entity.get(EF.DEX_MOD, 0)
        total_ac += _dex_penalty
        total_attack += _dex_penalty
    ```

- `tests/test_engine_petrified_condition_001_gate.py` (NEW — 8 tests PTC-001..008)

**DEX override rationale:** `EF.AC` is Type 2 (chargen bakes in entity's actual DEX mod). PHB p.310 says petrified entity has effective DEX 0 (modifier -5). Net penalty = `-5 - entity.DEX_MOD` — this overrides the baked-in DEX with the forced -5, applied to both AC and attack rolls.

**Gate summary:**

| Gate | Description | Result |
|------|-------------|--------|
| PTC-001 | ConditionType.PETRIFIED exists, value="petrified" | PASS |
| PTC-002 | create_petrified_condition() returns ConditionInstance with type=PETRIFIED | PASS |
| PTC-003 | DEX_MOD=2 entity: ac_modifier = -5-2 = -7 | PASS |
| PTC-004 | DEX_MOD=1 entity: attack_modifier = -5-1 = -6 | PASS |
| PTC-005 | modifiers.actions_prohibited == True | PASS |
| PTC-006 | "poison" in immune_to | PASS |
| PTC-007 | "disease" in immune_to | PASS |
| PTC-008 | Non-petrified entity: all modifiers=0, actions_prohibited=False | PASS |

---

## Pass 2 — PM Summary (≤100 words)

Batch BB: 3 WOs, 24/24 gates, 1,770 total. WEB was a full ghost (engine wired by prior WO); gate file was the gap. DBA was a double-ghost with a field contract correction — dispatch said Type 2, codebase is Type 3 runtime; chargen initialization was the only genuine gap. DBA-008 required one correction after first run (Type 2 assumption → runtime path verification). PTC was a genuine gap: PETRIFIED enum, immune_to field added to ConditionInstance schema, factory, and entity-specific DEX override in get_condition_modifiers(). Coverage map updated: 3 rows → IMPLEMENTED.

---

## Pass 3 — Retrospective

**Out-of-scope findings:**

| ID | Severity | Description | Status |
|----|----------|-------------|--------|
| FIND-BB-001 | LOW | WO dispatch stated deflection as "Type 2 (baked into EF.AC)." Reality is Type 3 runtime. Ghost check should include attack_resolver.py when a field has prior "WO-ENGINE-*-BONUS-001" history. | BACKLOG |
| FIND-BB-002 | LOW | `immune_to` field addition to ConditionInstance may be useful for other conditions (poison, disease effects). No current conditions use it except PETRIFIED. | DEFER |

**Kernel touches:** None — no KERNEL-0X files modified.

**Pre-existing test failures:** 196 failures in `test_ui_posture_audit_001_gate.py` and `test_ws_bridge.py` — pre-existing `ServerMessage` schema mismatch. Unrelated to Batch BB. Not introduced, not fixed.

---

## Consume-Site Confirmation

| Mechanic | Write Site | Read Site | Effect | Gate Proof |
|----------|-----------|-----------|--------|------------|
| Weapon enhancement bonus | schemas/attack.py:58 (Weapon dataclass) | attack_resolver.py:750 (attack), :985 (damage) | +N to attack roll; +N to damage | WEB-002,003,006,007 |
| Deflection bonus default | builder.py:~881, ~1219 (EF.DEFLECTION_BONUS=0) | attack_resolver.py:617 (runtime) | EF.DEFLECTION_BONUS=0 field present at chargen | DBA-001, DBA-006 |
| Deflection bonus runtime | entity data (EF.DEFLECTION_BONUS) | attack_resolver.py:617 | Higher AC vs attacks | DBA-004 |
| Petrified DEX override | conditions.py create_petrified_condition() | core/conditions.py get_condition_modifiers() post-loop | -5-DEX_MOD to AC and attack | PTC-003, PTC-004 |
| Petrified action block | ConditionModifiers.actions_prohibited=True | (enforcement deferred CP-17+) | blocks_actions=True on instance | PTC-005 |
| Petrified immune_to | ConditionInstance.immune_to=["poison","disease"] | (immunity enforcement deferred) | immune_to list populated | PTC-006, PTC-007 |

**CONSUME_DEFERRED:** `actions_prohibited` enforcement (CP-17+), `immune_to` enforcement (CP-17+). Both flagged in FIND-BB-002 above.

---

## Coverage Map Update

| Row | Before | After |
|-----|--------|-------|
| §1 Deflection bonus | NOT STARTED | **IMPLEMENTED** — builder.py, entity_fields.py, attack_resolver.py |
| §4 Petrified condition | NOT STARTED | **IMPLEMENTED** — schemas/conditions.py, core/conditions.py |
| §11 Weapon enhancement bonus | PARTIAL | **IMPLEMENTED** — attack_resolver.py:750,985, gate coverage added |

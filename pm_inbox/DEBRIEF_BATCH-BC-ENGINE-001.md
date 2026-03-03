# DEBRIEF: Batch BC Engine — WO-ENGINE-INCORPOREAL-MISS-CHANCE-001 + ghosts
**Commit:** a0219ab
**Gates:** 24/24
**Lifecycle:** NEW

---

## Pass 1 — Context Dump

### WO1: WO-ENGINE-INCORPOREAL-MISS-CHANCE-001 (genuine gap)

**Files changed:**

`aidm/schemas/conditions.py`
- Added `INCORPOREAL = "incorporeal"` to `ConditionType` enum (after PETRIFIED)
- Added `create_incorporeal_condition(source, applied_at_event_id)` factory at end of file
  - Returns `ConditionInstance(condition_type=INCORPOREAL, modifiers=ConditionModifiers(), ...)`
  - Notes: "50% damage avoidance from magical weapons: CONSUME_DEFERRED"

`aidm/core/conditions.py`
- Added to `_CONDITION_FACTORY_NAMES`: `"incorporeal": "create_incorporeal_condition"`

`aidm/core/attack_resolver.py` — 3 locations:
- **`resolve_attack()`** after `target = world_state.entities[intent.target_id]`:
  - Check `"incorporeal" in target.get(EF.CONDITIONS, {}) or {}`
  - If `intent.weapon.enhancement_bonus < 1`: emit `attack_denied(reason="auto_miss_incorporeal")`, return
  - Magical weapon: attack proceeds (50% CONSUME_DEFERRED)
- **`resolve_nonlethal_attack()`** same pattern using `intent.weapon.enhancement_bonus`
- **`resolve_manyshot()`** same pattern using `attacker.get(EF.WEAPON, {}).get("enhancement_bonus", 0)`
  (manyshot intent has no weapon field — reads from entity dict)

`docs/ENGINE_COVERAGE_MAP.md`
- Line 159 INC: NOT STARTED → IMPLEMENTED (attack_resolver.py×3, schemas/conditions.py, core/conditions.py)

**Gate file:** `tests/test_engine_incorporeal_miss_chance_001_gate.py` — 8/8 INC-001..008

| Test | Assertion |
|------|-----------|
| INC-001 | ConditionType.INCORPOREAL exists, value="incorporeal" |
| INC-002 | create_incorporeal_condition() returns ConditionInstance with INCORPOREAL type |
| INC-003 | Mundane weapon → attack_denied(auto_miss_incorporeal); no attack_roll |
| INC-004 | enhancement_bonus=0 explicit → same auto-miss |
| INC-005 | enhancement_bonus=1 → attack_roll emitted (not blocked) |
| INC-006 | Default weapon (enh=0) → auto-miss |
| INC-007 | Non-incorporeal target → no auto-miss, attack_roll emitted (regression) |
| INC-008 | full_attack delegates to resolve_attack (source inspect); nonlethal wired (functional) |

**Consume-site chain:**
- Write: `schemas/conditions.py` — `create_incorporeal_condition()` writes INCORPOREAL to entity `EF.CONDITIONS`
- Read: `attack_resolver.py` — `"incorporeal" in target.get(EF.CONDITIONS, {})` at 3 call sites
- Effect: `attack_denied(reason="auto_miss_incorporeal")` emitted, early return before dice roll
- Test: INC-003 proves end-to-end: incorporeal entity + mundane weapon → denied event, no roll

**Parallel paths verified:**
- `resolve_attack()` ✓ (FAGU — covers full_attack, TWF, GTWF via delegation)
- `resolve_nonlethal_attack()` ✓ (standalone)
- `resolve_manyshot()` ✓ (standalone, uses entity weapon dict)
- `full_attack_resolver.py` — inherits via resolve_attack delegation (INC-008 source confirms)

---

### WO2: WO-ENGINE-DISARM-2H-BONUS-001 (GHOST — B-AMB-04)

Engine code pre-existed at `maneuver_resolver.py:1526-1534`:
```python
if attacker_weapon_type == "two-handed":
    attacker_modifier += 4
elif attacker_weapon_type == "light":
    attacker_modifier -= 4
if defender_weapon_type == "two-handed":
    defender_modifier += 4
elif defender_weapon_type == "light":
    defender_modifier -= 4
```
`_get_weapon_type()` helper at line 112 reads `weapon_data.get("weapon_type", "one-handed")` from EF.WEAPON.

Gap: gate file only.

`docs/ENGINE_COVERAGE_MAP.md` — Line 92 DTH: NOT STARTED → IMPLEMENTED (maneuver_resolver.py:1526-1534, ghost B-AMB-04)

**Gate file:** `tests/test_engine_disarm_2h_bonus_001_gate.py` — 8/8 DTH-001..008

| Test | Assertion |
|------|-----------|
| DTH-001 | One-handed → attacker_modifier = BAB(5)+STR(0) = 5 |
| DTH-002 | Two-handed → attacker_modifier = 5+4 = 9 |
| DTH-003 | BAB=3, STR=2, two-handed → modifier = 3+2+4 = 9 |
| DTH-004 | Two-handed + improved_disarm → modifier = 5+0+4+4 = 13 |
| DTH-005 | Unarmed (no EF.WEAPON) → modifier = 5 (no +4) |
| DTH-006 | Source: "weapon_type" key, "two-handed" check, "attacker_modifier += 4" present |
| DTH-007 | Source: counter_disarm reuses pre-computed modifiers (no double-add) |
| DTH-008 | Source: attacker_weapon_type check + two-handed branch + += 4 all present |

---

### WO3: WO-ENGINE-CONCENTRATION-ENTANGLED-001 (GHOST — WO-ENGINE-CONCENTRATION-GRAPPLE-001)

Engine code pre-existed at `play_loop.py:821-823`:
```python
elif "entangled" in _caster_conds_cg:
    _conc_grapple_dc = 15 + spell_level
```
Delivered as part of WO-ENGINE-CONCENTRATION-GRAPPLE-001 (grappled+entangled implemented together).

Gap: gate file only.

`docs/ENGINE_COVERAGE_MAP.md` — Line 203 CE: NOT STARTED → IMPLEMENTED (play_loop.py:821-823, ghost)
Line 926 Priority #17: grappled+entangled DONE — unstable surface/vigorous motion still NOT STARTED

**Gate file:** `tests/test_engine_concentration_entangled_001_gate.py` — 8/8 CE-001..008

| Test | Assertion |
|------|-----------|
| CE-001 | ConditionType.ENTANGLED exists, value="entangled" |
| CE-002 | Source: `elif "entangled"` branch present in play_loop.py |
| CE-003 | Formula "15 + spell_level" in source; spell_level=1 → DC=16 |
| CE-004 | spell_level=3 → DC=18 |
| CE-005 | Entangled and damage concentration checks are independent paths in source |
| CE-006 | `_conc_grapple_dc = 0` init and `_conc_grapple_dc > 0` guard both present |
| CE-007 | All concentration elements ("grappled", "entangled", "15 + spell_level") in play_loop.py |
| CE-008 | Coverage map row CE confirmed IMPLEMENTED |

---

## Pass 2 — PM Summary

Batch BC: 24/24. WO1 (INCORPOREAL) was a genuine gap — ConditionType, factory, and auto-miss check wired into all three standalone attack paths (resolve_attack, resolve_nonlethal_attack, resolve_manyshot). WO2 (DTH) and WO3 (CE) were full ghosts; gate files document pre-existing engine behavior. Magic weapon threshold uses `enhancement_bonus >= 1`, consistent with damage_reduction.py. 50% damage avoidance from magical weapons is CONSUME_DEFERRED. Counter-disarm reuses pre-computed modifiers (no double weapon bonus applied). Running total: 1,770 + 24 = **1,794 gates**.

---

## Pass 3 — Retrospective

- **DTH ghost confirms B-AMB-04 coverage:** The two-handed disarm bonus was already in the coverage map finding B-AMB-04; this WO correctly identified it and provided gate proof.
- **CE ghost confirms prior WO thoroughness:** WO-ENGINE-CONCENTRATION-GRAPPLE-001 implemented both grappled and entangled together (PHB logic groups them). Batch BC CE gates lock this down.
- **CONSUME_DEFERRED filed:** INC 50% damage avoidance from magical weapons is mechanically significant. Filed as FINDING below.
- **resolve_manyshot() weapon source difference:** manyshot intent has no `weapon` field on the intent dataclass — must read from `attacker.get(EF.WEAPON, {})`. This is a schema asymmetry worth noting for future manyshot WOs.
- This WO touches KERNEL-ATTACK [attack_resolver parallel paths] — three standalone paths confirmed wired for INCORPOREAL.

---

## Radar

| ID | Severity | Description | Status |
|----|----------|-------------|--------|
| FINDING-BC-INC-CONSUME-DEFERRED-001 | MEDIUM | PHB p.310: magical weapons vs incorporeal targets — 50% damage avoidance not implemented. Auto-miss for nonmagical weapons done; the damage-vs-magic half is CONSUME_DEFERRED. | OPEN → backlog |
| FINDING-BC-MANYSHOT-WEAPON-ASYMMETRY-001 | LOW | resolve_manyshot() reads weapon from entity EF.WEAPON dict (not intent.weapon field). Asymmetric with resolve_attack(). No bug but schema drift risk. | OPEN → backlog |

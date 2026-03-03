# WO Set — Engine Batch BB

**Lifecycle:** DISPATCH-READY
**Session:** 33 (2026-03-03)
**Source findings:** ENGINE_COVERAGE_MAP.md review session 33 — 3 new findings promoted directly to WO (see Source Artifact Verification)
**Seat:** Chisel
**Expected gates:** ~24 (WEB 8 + DBA 8 + PTC 8)

---

## DEBRIEF QUALITY REMINDER (mandatory — all 3 WOs)

Builder must confirm in Pass 1:
1. Ghost Check result (grep before edit, gate file existence check)
2. Parity check — all parallel paths identified and updated
3. Consume-site confirmed end-to-end (write → read → effect → test)
4. ML Preflight Checklist (ML-001–ML-006) complete
5. Coverage map row updated (NOT STARTED/PARTIAL → IMPLEMENTED)

---

## WO1: WO-ENGINE-WEAPON-ENHANCEMENT-BONUS-001

**Source finding:** FINDING-ENGINE-WEAPON-ENHANCEMENT-BONUS-AC-WIRE-001 (new, promoted directly)
**Severity:** MEDIUM
**Files:** `aidm/core/attack_resolver.py`

### RAW Fidelity

PHB p.218 / DMG p.219: A weapon with an enhancement bonus of +1 or more adds that bonus to **both** the attack roll and the damage roll. Example: a +2 longsword adds +2 to the attack roll and +2 to damage. The bonus stacks with Weapon Focus (+1), Weapon Specialization (+2), and Strength modifier — all separate bonuses.

Current state (PARTIAL): `enhancement_bonus` field exists in the weapon dict and is **read for DR bypass** (e.g., magic weapon vs. DR 5/magic). It is **not applied** to attack roll or damage roll. A +2 longsword wielded by a fighter attacks and damages as if it were a mundane longsword.

### Scope

**`aidm/core/attack_resolver.py`** — wherever attack bonus and damage bonus are accumulated from the weapon context:

1. **Attack roll:** Find the site where `EF.WEAPON` context (or `intent.weapon`) is consumed to compute attack modifier. After the existing Weapon Focus branch, add:
   ```python
   # WO-ENGINE-WEAPON-ENHANCEMENT-BONUS-001: PHB p.218 — magic weapon bonus to attack
   _enh_bonus = intent.weapon.get("enhancement_bonus", 0) if intent.weapon else 0
   attack_modifier += _enh_bonus
   ```

2. **Damage roll:** Find the site where damage bonus is accumulated. After the existing Weapon Specialization branch, add:
   ```python
   # WO-ENGINE-WEAPON-ENHANCEMENT-BONUS-001: PHB p.218 — magic weapon bonus to damage
   _enh_bonus = intent.weapon.get("enhancement_bonus", 0) if intent.weapon else 0
   damage_modifier += _enh_bonus
   ```

**Note:** If the weapon schema stores enhancement_bonus differently (e.g., as `Weapon.enhancement_bonus` attribute), use the correct access pattern. Builder confirms the exact field path in Ghost Check step before writing.

**Stacking behavior:** Enhancement bonus is a separate bonus type — stacks with WF (+1 attack), WS (+2 damage), STR mod. No capping. Integer only.

### Ghost Check Protocol (MANDATORY before writing code)

```bash
grep -n "enhancement_bonus" aidm/core/attack_resolver.py
grep -n "enhancement_bonus" aidm/core/feat_resolver.py
grep -n "enhancement_bonus" aidm/schemas/weapons.py
ls tests/test_engine_weapon_enhancement_bonus_001_gate.py
```

Expected: `attack_resolver.py` — enhancement_bonus should be 0 results in attack/damage calc (only in DR bypass). `schemas/weapons.py` or weapon dict — field exists. Gate file does not exist.

If `attack_resolver.py` already applies enhancement_bonus to attack AND damage → GHOST, stop and report.

### Parallel Paths Check

Builder confirms: are there parallel attack computation paths that also need the enhancement bonus?
- `attack_resolver.resolve_attack()` (standard)
- `full_attack_resolver.py` (full attack / BAB iterative)
- `resolve_manyshot()` (Manyshot)
- `resolve_nonlethal_attack()` (nonlethal)

All paths that compute attack roll or damage roll for weapon attacks must include the enhancement bonus. Any path that calls `get_attack_modifier()` / `get_damage_modifier()` from `feat_resolver` will pick it up there if the enhancement bonus is added to feat_resolver. Builder determines whether the bonus is better added to `feat_resolver.get_attack_modifier()` / `get_damage_modifier()` (single point, all paths get it automatically) or to each resolver site.

**Recommended approach:** Add to `feat_resolver.get_attack_modifier()` and `feat_resolver.get_damage_modifier()` — these are called from all attack paths. The weapon context is passed as part of the `context` dict to `feat_resolver`. Verify that `context["weapon"]` or `context.get("weapon_enhancement_bonus", 0)` is available at that call site. If not, pass it explicitly.

### Consumption Chain

- **Write:** Chargen/equipment stores `enhancement_bonus` in weapon dict (already present for magic weapons)
- **Read:** `feat_resolver.get_attack_modifier()` + `get_damage_modifier()` (or direct in attack_resolver)
- **Effect:** Attack roll total is higher for magic weapons; damage roll total is higher for magic weapons
- **Test:** WEB-001..008

### PM Acceptance Notes

- **WEB-001:** Entity with mundane weapon (enhancement_bonus=0 or absent) → no enhancement bonus to attack
- **WEB-002:** Entity with +1 weapon → attack roll includes +1 enhancement bonus
- **WEB-003:** Entity with +2 weapon → attack roll includes +2 enhancement bonus
- **WEB-004:** Entity with +1 weapon AND Weapon Focus → total attack bonus = +2 (+1 WF + +1 enh) — stacking confirmed
- **WEB-005:** Entity with mundane weapon → no enhancement bonus to damage
- **WEB-006:** Entity with +1 weapon → damage roll includes +1 enhancement bonus
- **WEB-007:** Entity with +2 weapon AND Weapon Specialization → total damage bonus = +4 (+2 WS + +2 enh) — stacking confirmed
- **WEB-008:** All attack paths confirmed — if added to feat_resolver, confirm enhancement bonus fires on full attack (iterative BAB) path
- Show the exact before/after diff at each insertion point (feat_resolver.py or attack_resolver.py).
- Confirm how enhancement_bonus is accessed from the weapon (attribute vs dict key).
- Coverage map: §11 weapon enhancement bonus row → IMPLEMENTED.

### Gate File

`tests/test_engine_weapon_enhancement_bonus_001_gate.py` — 8 tests (WEB-001..008)

---

## WO2: WO-ENGINE-DEFLECTION-BONUS-AC-001

**Source finding:** FINDING-ENGINE-DEFLECTION-BONUS-AC-001 (new, promoted directly)
**Severity:** LOW
**Files:** `aidm/schemas/entity_fields.py`, `aidm/core/builder.py` (both chargen paths)

### RAW Fidelity

PHB p.151: A deflection bonus applies to AC and is granted by magical effects (Ring of Protection, Shield of Faith spell, etc.). Deflection bonuses do not stack with each other — only the highest applies. PHB table: "Deflection: Magical fields that deflect attacks."

Current state (NOT STARTED): No `EF.DEFLECTION_BONUS` field in entity_fields.py. No deflection bonus included in EF.AC at chargen. Entity AC does not account for any deflection bonus (Ring of Protection +1, +2, etc. are not yet representable).

**EF.AC is Type 2 (Base+Permanent).** Deflection bonus is a permanent bonus (item or persistent spell). It belongs in EF.AC at chargen time for items; for spell effects (Shield of Faith), it would be a condition modifier. This WO covers only the chargen (item-based) path: entity has a permanent deflection bonus from an item → include it in EF.AC.

### Scope

**Step 1 — `aidm/schemas/entity_fields.py`:** Add constant:
```python
DEFLECTION_BONUS = "deflection_bonus"
```

**Step 2 — `aidm/core/builder.py`** (both chargen paths — build_character() and _build_multiclass_character()):

Wherever `EF.AC` is computed and assigned, add `entity.get(EF.DEFLECTION_BONUS, 0)` to the total:
```python
# WO-ENGINE-DEFLECTION-BONUS-AC-001: PHB p.151 — deflection bonus to AC (Ring of Protection, etc.)
_deflection = entity.get(EF.DEFLECTION_BONUS, 0)
entity[EF.AC] = _base_ac + _deflection  # (existing AC formula + deflection)
```

For entities without a deflection bonus, `_deflection = 0` (no change in behavior).

**Step 3 — Chargen fixture**: When an entity has a Ring of Protection +1, set `entity[EF.DEFLECTION_BONUS] = 1` before calling the AC computation. This WO does NOT wire the equipment slot system — it only ensures the field exists and is included in EF.AC computation. Equipment/item source of the field is caller responsibility.

### Ghost Check Protocol (MANDATORY before writing code)

```bash
grep -n "DEFLECTION_BONUS\|deflection_bonus\|deflection" aidm/schemas/entity_fields.py
grep -n "DEFLECTION\|deflection" aidm/core/builder.py
grep -n "DEFLECTION\|deflection" aidm/core/attack_resolver.py
ls tests/test_engine_deflection_bonus_ac_001_gate.py
```

Expected: 0 results in entity_fields.py for DEFLECTION. 0 results in builder.py. Gate file does not exist.

If EF.DEFLECTION_BONUS already exists and is already in EF.AC computation → GHOST, stop and report.

### Parallel Paths Check

EF.AC is Type 2 — consumed by attack_resolver.py via `entity.get(EF.AC, 10)`. No parallel AC computation path expected. Builder confirms no shadow AC calc exists in `play_loop.py` or `session_orchestrator.py`.

### Consumption Chain

- **Write:** Chargen — `entity[EF.DEFLECTION_BONUS] = N` (from item/equipment at entity creation). builder.py adds it to EF.AC.
- **Read:** `attack_resolver.py` reads `entity.get(EF.AC, 10)` — deflection already included in EF.AC
- **Effect:** Entity with Ring of Protection +1 has AC 1 higher than without; attack rolls against it must beat higher AC
- **Test:** DBA-001..008

### PM Acceptance Notes

- **DBA-001:** Entity with EF.DEFLECTION_BONUS=0 (or absent) → EF.AC unchanged
- **DBA-002:** Entity with EF.DEFLECTION_BONUS=1 → EF.AC = base_AC + 1
- **DBA-003:** Entity with EF.DEFLECTION_BONUS=2 → EF.AC = base_AC + 2
- **DBA-004:** Attack roll against entity with deflection bonus — must beat higher AC (confirm via attack resolver output)
- **DBA-005:** EF.DEFLECTION_BONUS constant in entity_fields.py — confirmed
- **DBA-006:** Both chargen paths (build_character + _build_multiclass_character) updated
- **DBA-007:** Entity without deflection bonus has same AC as before WO (no regression)
- **DBA-008:** Type 2 field contract confirmed — deflection is in EF.AC (permanent), not added at runtime
- Show exact before/after diff at builder.py AC computation in both chargen paths.
- Show EF.DEFLECTION_BONUS constant addition in entity_fields.py.
- Coverage map: §11 deflection bonus row → IMPLEMENTED.

### Gate File

`tests/test_engine_deflection_bonus_ac_001_gate.py` — 8 tests (DBA-001..008)

---

## WO3: WO-ENGINE-PETRIFIED-CONDITION-001

**Source finding:** FINDING-ENGINE-PETRIFIED-CONDITION-001 (new, promoted directly)
**Severity:** LOW
**Files:** `aidm/schemas/conditions.py`, `aidm/core/conditions.py` (or equivalent condition factory)

### RAW Fidelity

PHB p.310 (Petrified): A petrified creature has been turned to stone. Effects:
- DEX is treated as 0 (–5 DEX modifier) — effectively immobilized
- No actions can be taken (no attacks, no spells, no movement)
- Immune to poison and disease (stone doesn't metabolize)
- Has hardness 8 (treated as an object)
- Unconscious (effectively incapacitated)
- May fall down if standing when petrified (becomes prone)

Implementation scope: This WO adds the PETRIFIED ConditionType enum value and creates a `create_petrified_condition()` factory function. It does NOT wire full stone hardness (that requires an object damage system). It DOES wire: DEX modifier override (–5), action economy block (cannot act), immunity registration (poison/disease don't fire).

### Scope

**Step 1 — `aidm/schemas/conditions.py`:** Add to ConditionType enum:
```python
PETRIFIED = "petrified"
```

**Step 2 — `aidm/core/conditions.py`** (or wherever create_* condition factories live):

```python
def create_petrified_condition(source: str = "petrification") -> ConditionInstance:
    """PHB p.310: Petrified — turned to stone. DEX 0, cannot act, immune to poison/disease."""
    # WO-ENGINE-PETRIFIED-CONDITION-001: PHB p.310
    return ConditionInstance(
        condition_type=ConditionType.PETRIFIED,
        source=source,
        dex_override=-5,          # DEX modifier = -5 (DEX score treated as 0)
        blocks_actions=True,       # Cannot take any actions
        immune_to=["poison", "disease"],   # Stone doesn't metabolize
        duration_rounds=None,      # Permanent until Remove Petrification / Stone to Flesh
    )
```

**Step 3 — Wire into condition modifier stack:** Wherever `get_condition_modifiers()` collects AC and attack modifiers, add handling for PETRIFIED:
```python
if ConditionType.PETRIFIED in active_conditions:
    # DEX mod = -5 (PHB p.310: DEX treated as 0)
    # Existing DEX modifier in EF.AC already computed at chargen (Type 2 field);
    # override: subtract existing DEX mod, apply -5 flat
    _dex_penalty = -5 - entity.get(EF.DEX_MOD, 0)
    modifiers["ac"] += _dex_penalty
    modifiers["attack"] += _dex_penalty   # also to attack rolls
```

**Scope boundary:** Hardness 8 (object DR) is NOT wired in this WO — requires object damage system. `blocks_actions=True` is logged in the condition payload; enforcement (that petrified entities skip turns) is out of scope here. Gate tests verify condition creation and DEX modifier effect.

### Ghost Check Protocol (MANDATORY before writing code)

```bash
grep -n "PETRIFIED\|petrified" aidm/schemas/conditions.py
grep -n "PETRIFIED\|petrified" aidm/core/conditions.py
ls tests/test_engine_petrified_condition_001_gate.py
```

Expected: 0 results. Gate file does not exist.

If PETRIFIED already exists in ConditionType → GHOST, stop and report.

### Parallel Paths Check

All condition-modifier consumers (attack_resolver, save_resolver, skill_resolver) call `get_condition_modifiers()`. If PETRIFIED is handled there, all paths pick it up. Builder confirms no shadow condition check exists specifically for PETRIFIED in any resolver.

### Consumption Chain

- **Write:** `conditions.py` — `create_petrified_condition()` factory returns ConditionInstance; stored in `EF.CONDITIONS` dict when petrification applied
- **Read:** `get_condition_modifiers()` — reads PETRIFIED from CONDITIONS dict; returns DEX modifier override
- **Effect:** Petrified entity has –5 DEX modifier to AC and attack rolls; condition payload marks blocks_actions=True; immune_to list registered
- **Test:** PTC-001..008

### PM Acceptance Notes

- **PTC-001:** `ConditionType.PETRIFIED` exists in conditions.py enum
- **PTC-002:** `create_petrified_condition()` returns a ConditionInstance with correct type
- **PTC-003:** Petrified entity gets –5 DEX modifier applied to AC (DEX score treated as 0)
- **PTC-004:** Petrified entity gets –5 DEX modifier applied to attack roll
- **PTC-005:** `condition_instance.blocks_actions == True`
- **PTC-006:** `"poison" in condition_instance.immune_to` (immune registration)
- **PTC-007:** `"disease" in condition_instance.immune_to`
- **PTC-008:** Non-petrified entity — no AC/attack penalty (regression)
- Show exact additions to `aidm/schemas/conditions.py` (enum value) and `aidm/core/conditions.py` (factory function).
- Show get_condition_modifiers() before/after diff for PETRIFIED branch.
- Coverage map: §4 Petrified condition row → IMPLEMENTED.

### Gate File

`tests/test_engine_petrified_condition_001_gate.py` — 8 tests (PTC-001..008)

---

## ML Preflight Checklist (all WOs)

| Check | WO1 (WEB) | WO2 (DBA) | WO3 (PTC) |
|-------|-----------|-----------|-----------|
| ML-001: EF.* used (no bare strings) | `intent.weapon.get("enhancement_bonus", 0)` — dict key on Weapon object, not EF field; appropriate | `EF.DEFLECTION_BONUS` new constant required; no bare `"deflection_bonus"` | `ConditionType.PETRIFIED` enum value; `EF.CONDITIONS` for storage |
| ML-002: All call sites identified | All attack paths that compute attack/damage modifier — feat_resolver (single point) recommended | Both chargen paths in builder.py; no runtime resolver change | `get_condition_modifiers()` only; all resolver consumers already call it |
| ML-003: No float in deterministic path | Integer enhancement_bonus (+1, +2, etc.) | Integer deflection_bonus (0, 1, 2, etc.) | Integer –5 DEX modifier override |
| ML-004: json.dumps sort_keys | N/A | N/A | N/A |
| ML-005: No WorldState mutation in resolver | feat_resolver reads context, returns int — no mutation | builder.py chargen only — WorldState construction | conditions.py factory creates ConditionInstance; no WS mutation |
| ML-006: Coverage map updated | §11 weapon enhancement bonus PARTIAL → IMPLEMENTED | §11 deflection bonus NOT STARTED → IMPLEMENTED | §4 Petrified NOT STARTED → IMPLEMENTED |

---

## Source Artifact Verification

**Source:** `docs/ENGINE_COVERAGE_MAP.md` (read session 33, 2026-03-03 via coverage map review)
**Opened this session:** Yes — coverage map review executed via Explore agent, returning full NOT STARTED / PARTIAL inventory
**Finding IDs referenced:** New findings FINDING-ENGINE-WEAPON-ENHANCEMENT-BONUS-AC-WIRE-001, FINDING-ENGINE-DEFLECTION-BONUS-AC-001, FINDING-ENGINE-PETRIFIED-CONDITION-001 (promoted directly from coverage map review to WO)
**Exact source details:**
- WEB: Coverage map §11 Equipment: `enhancement_bonus` field exists (weapon dict), used for DR bypass, NOT applied to attack/damage rolls. PHB p.218: "adds enhancement bonus to both attack and damage."
- DBA: Coverage map §1 Combat Core: No EF.DEFLECTION_BONUS field; no deflection bonus in EF.AC chargen formula. PHB p.151: deflection bonus = separate permanent AC bonus type.
- PTC: Coverage map §4 Conditions: PETRIFIED not in ConditionType enum; no factory function. PHB p.310: DEX=0, cannot act, immune to poison/disease, hardness 8.
**Local presence:** Confirmed — ENGINE_COVERAGE_MAP.md contents returned by Explore agent and read in full (WF/IT rows confirmed as just-added by BA; §11/§4 NOT STARTED entries confirmed as targets).

---

*Batch BB — 3 WOs. ~24 expected gates (WEB 8 + DBA 8 + PTC 8). New cycle BB=3/5.*

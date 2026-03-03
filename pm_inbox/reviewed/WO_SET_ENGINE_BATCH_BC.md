# WO Set — Engine Batch BC

**Lifecycle:** DISPATCH-READY
**Session:** 33 (2026-03-03)
**Source findings:** ENGINE_COVERAGE_MAP.md review session 33 — 3 new findings promoted directly to WO (see Source Artifact Verification)
**Seat:** Chisel
**Expected gates:** ~24 (INC 8 + DTH 8 + CE 8)

---

## DEBRIEF QUALITY REMINDER (mandatory — all 3 WOs)

Builder must confirm in Pass 1:
1. Ghost Check result (grep before edit, gate file existence check)
2. Parity check — all parallel paths identified and updated
3. Consume-site confirmed end-to-end (write → read → effect → test)
4. ML Preflight Checklist (ML-001–ML-006) complete
5. Coverage map row updated (NOT STARTED/PARTIAL → IMPLEMENTED)

---

## WO1: WO-ENGINE-INCORPOREAL-MISS-CHANCE-001

**Source finding:** FINDING-ENGINE-INCORPOREAL-CONDITION-001 (new, promoted directly)
**Severity:** MEDIUM
**Files:** `aidm/schemas/conditions.py`, `aidm/core/conditions.py`, `aidm/core/attack_resolver.py`

### RAW Fidelity

PHB p.310 (Incorporeal): Incorporeal creatures can only be harmed by other incorporeal creatures, +1 or better magic weapons, spells, spell-like abilities, and supernatural abilities. They are immune to all nonmagical attack forms. Even when hit by spells or magic weapons, they have a 50% chance to ignore any damage from a corporeal source (treated as if it missed them).

Current state (NOT STARTED): No `ConditionType.INCORPOREAL` enum value. No factory function. No attack resolver check. `EF.MISS_CHANCE` field exists (used for invisibility/concealment) but no incorporeal-specific enforcement. A mundane sword hits a ghost as though it were solid flesh.

**Implementation scope:** This WO covers (1) the enum value, (2) the factory, and (3) the nonmagical weapon auto-miss path in `attack_resolver`. The 50% "ignore damage" roll from magical sources is `CONSUME_DEFERRED` — it requires a damage avoidance layer not yet built. Gate tests validate the auto-miss (immune) path and that magical weapons are not auto-blocked.

### Scope

**Step 1 — `aidm/schemas/conditions.py`:** Add to ConditionType enum:
```python
INCORPOREAL = "incorporeal"
```

**Step 2 — `aidm/core/conditions.py`** (same file as other create_* factories):
```python
def create_incorporeal_condition(source: str = "incorporeal_form") -> ConditionInstance:
    """PHB p.310: Incorporeal — immune to nonmagical physical attacks. 50% vs magical CONSUME_DEFERRED."""
    # WO-ENGINE-INCORPOREAL-MISS-CHANCE-001: PHB p.310
    return ConditionInstance(
        condition_type=ConditionType.INCORPOREAL,
        source=source,
        duration_rounds=None,  # Permanent for undead/creatures; spell-granted has duration
    )
```

**Step 3 — `aidm/core/attack_resolver.py`:** At the start of the physical attack resolution path (before the attack roll is computed), after the target entity is retrieved:
```python
# WO-ENGINE-INCORPOREAL-MISS-CHANCE-001: PHB p.310 — incorporeal auto-miss for nonmagical weapons
_target_conditions = target.get(EF.CONDITIONS, {})
if ConditionType.INCORPOREAL in _target_conditions:
    _enh = intent.weapon.get("enhancement_bonus", 0) if intent.weapon else 0
    _is_magic = (intent.weapon.get("is_magic", False) or _enh > 0) if intent.weapon else False
    if not _is_magic:
        # Nonmagical weapon: automatically misses — immune
        return AttackResult(hit=False, reason="auto-miss: nonmagical attack vs incorporeal target")
    # Magical weapon: attack roll proceeds normally (50% damage avoidance CONSUME_DEFERRED)
```

**Note:** Builder confirms the exact return type / event shape for a failed attack in `attack_resolver` — use the same shape as a natural-miss result. If the resolver returns an event dict rather than an AttackResult dataclass, match the existing pattern.

**CONSUME_DEFERRED:** The 50% chance to ignore damage from magical weapons/spells is not wired in this WO. Log finding `FINDING-ENGINE-INCORPOREAL-MAGIC-DAMAGE-AVOIDANCE-001` (MEDIUM) in the debrief radar for future WO.

### Ghost Check Protocol (MANDATORY before writing code)

```bash
grep -n "INCORPOREAL\|incorporeal" aidm/schemas/conditions.py
grep -n "INCORPOREAL\|incorporeal" aidm/core/conditions.py
grep -n "INCORPOREAL\|incorporeal" aidm/core/attack_resolver.py
ls tests/test_engine_incorporeal_miss_chance_001_gate.py
```

Expected: 0 results in all three files. Gate file does not exist.

If `ConditionType.INCORPOREAL` already exists and attack_resolver already checks it → GHOST, stop and report.

### Parallel Paths Check

All physical weapon attack paths must be checked:
- `attack_resolver.resolve_attack()` (standard) — wire here
- `full_attack_resolver.py` — must also auto-miss incorporeal for nonmagical weapons
- `resolve_nonlethal_attack()` — if this path is used for physical attacks, wire there too
- `resolve_manyshot()` — ranged physical attack; nonmagical ranged vs incorporeal → auto-miss

Spells: incorporeal auto-miss does NOT apply to spells (PHB p.310: spells harm incorporeal). Do NOT add the check to `spell_resolver`.

### Consumption Chain

- **Write:** `conditions.py` — `create_incorporeal_condition()` stores `ConditionType.INCORPOREAL` in `EF.CONDITIONS` on target entity
- **Read:** `attack_resolver.py` — reads `target.get(EF.CONDITIONS, {})` before attack roll; checks INCORPOREAL + weapon magic status
- **Effect:** Mundane weapon attacks against INCORPOREAL entity return auto-miss; +1 or better weapons proceed to attack roll
- **Test:** INC-001..008

### PM Acceptance Notes

- **INC-001:** `ConditionType.INCORPOREAL` exists in `aidm/schemas/conditions.py`
- **INC-002:** `create_incorporeal_condition()` returns a `ConditionInstance` with `condition_type=ConditionType.INCORPOREAL`
- **INC-003:** Standard attack with mundane weapon (enhancement_bonus=0 or absent) vs INCORPOREAL target → `hit=False`, reason identifies auto-miss
- **INC-004:** `enhancement_bonus=0` explicitly → same auto-miss (zero is nonmagical)
- **INC-005:** Attack with +1 weapon (enhancement_bonus=1) vs INCORPOREAL target → attack roll proceeds (not auto-blocked); result is a normal to-hit evaluation
- **INC-006:** `is_magic=False` with no enhancement_bonus → auto-miss
- **INC-007:** Non-incorporeal target with mundane weapon → normal attack flow, no auto-miss (regression)
- **INC-008:** All parallel physical attack paths (full attack, manyshot, nonlethal) confirmed — show grep or trace for each
- Show exact insertion point in `attack_resolver.py` (before/after diff with line numbers).
- Show enum addition and factory function.
- CONSUME_DEFERRED finding logged for 50% magical damage avoidance.
- Coverage map: §3 Incorporeal row → IMPLEMENTED (noting 50% magic damage avoidance DEFERRED).

### Gate File

`tests/test_engine_incorporeal_miss_chance_001_gate.py` — 8 tests (INC-001..008)

---

## WO2: WO-ENGINE-DISARM-2H-BONUS-001

**Source finding:** FINDING-ENGINE-DISARM-2H-WEAPON-BONUS-001 (new, promoted directly)
**Severity:** LOW
**Files:** `aidm/core/maneuver_resolver.py`

### RAW Fidelity

PHB p.155 (Disarm): "If you're attempting to disarm your opponent and using a two-handed weapon, you get a +4 bonus on the opposed roll." This is an untyped bonus. It stacks with Improved Disarm (+4), Strength modifier, BAB, and weapon enhancement bonus. No further conditions.

Current state (NOT STARTED): `maneuver_resolver.py` handles disarm attempts. The opposed STR check (modified by BAB and feats) does not add +4 when the disarming weapon is two-handed. A greatsword user disarms at the same bonus as a shortsword user.

### Scope

**`aidm/core/maneuver_resolver.py`** — wherever the disarm check bonus is assembled:

```python
# WO-ENGINE-DISARM-2H-BONUS-001: PHB p.155 — +4 bonus for two-handed weapon on disarm
_weapon_hands = intent.weapon.get("hands", 1) if intent.weapon else 1
if _weapon_hands >= 2:
    disarm_bonus += 4
```

Builder confirms the exact field name for handedness in the weapon dict schema — could be `"hands": 2`, `"two_handed": True`, or another field. Ghost Check includes grepping weapon schema. Use the correct field; do not hard-code an assumption.

**Stacking:** This bonus stacks with Improved Disarm (+4), STR mod, BAB, weapon enhancement bonus (added by BB WO1 post-merge). All are untyped or different bonus types. No cap.

### Ghost Check Protocol (MANDATORY before writing code)

```bash
grep -n "disarm" aidm/core/maneuver_resolver.py
grep -n "two_hand\|two-hand\|hands.*2\|2.*hands" aidm/core/maneuver_resolver.py
grep -n "two_hand\|two-hand\|hands" aidm/schemas/weapons.py
grep -n "two_hand\|two-hand\|hands" aidm/schemas/attack.py
ls tests/test_engine_disarm_2h_bonus_001_gate.py
```

Expected: 0 results for two-handed bonus in `maneuver_resolver.py`. Weapon schema field for handedness should exist. Gate file does not exist.

If a +4 two-handed bonus is already present in the disarm path → GHOST, stop and report.

### Parallel Paths Check

Disarm is resolved through `maneuver_resolver`. Builder confirms:
- Is there a `DisarmIntent` processing path in `play_loop.py` that bypasses maneuver_resolver? If so, wire both.
- Is the disarm counter-attempt (when the disarming attacker is counter-disarmed) also missing the +4? PHB says the bonus applies only to the attempting party, not the defender. Do NOT add +4 to the defender's counter-roll.

### Consumption Chain

- **Write:** Combat intent — `DisarmIntent` with `weapon` dict containing handedness field
- **Read:** `maneuver_resolver.py` — reads `intent.weapon.get("hands", 1)` during disarm check assembly
- **Effect:** Two-handed weapon disarm attempts have +4 higher check result; more likely to succeed against armed opponents
- **Test:** DTH-001..008

### PM Acceptance Notes

- **DTH-001:** Disarm attempt with one-handed weapon (hands=1) → disarm check has no +4 bonus
- **DTH-002:** Disarm attempt with two-handed weapon (hands=2) → disarm check includes +4 bonus
- **DTH-003:** Show the disarm check total breakdown: STR + BAB + Improved Disarm (if applicable) + 4 (2H) — bonus appears in trace
- **DTH-004:** Disarm with two-handed weapon + Improved Disarm → both bonuses stack (+8 total above baseline)
- **DTH-005:** Unarmed disarm attempt → no +4 (no weapon context)
- **DTH-006:** Confirm the weapon schema field name used for handedness — show Ghost Check grep result and confirm exact field used in implementation
- **DTH-007:** Counter-disarm (opponent's reactive roll) → no +4 bonus on defender's side
- **DTH-008:** Coverage map §1 disarm two-handed row → IMPLEMENTED
- Show before/after diff at the disarm bonus accumulation site in `maneuver_resolver.py`.
- Confirm: does this fire in the same path as Improved Disarm? Show line range for both.

### Gate File

`tests/test_engine_disarm_2h_bonus_001_gate.py` — 8 tests (DTH-001..008)

---

## WO3: WO-ENGINE-CONCENTRATION-ENTANGLED-001

**Source finding:** FINDING-ENGINE-CONCENTRATION-ENTANGLED-001 (new, promoted directly)
**Severity:** LOW
**Files:** `aidm/core/concentration_resolver.py` (or equivalent — confirm file in Ghost Check)

### RAW Fidelity

PHB p.175 (Concentration): "If you are entangled: Concentration DC = spell's DC + 15." Wait — re-reading: PHB p.175 Table "Concentration Check DCs": "Entangled — DC: Spell level + 15". This is the correct cite. The DC to maintain concentration while entangled is spell_level + 15, not base_dc + 4.

**Correction from dispatch draft:** The DC is not "base + 4" — it is a flat formula of `spell_level + 15`. This is a separate row in the concentration DC table, not an additive modifier on top of another check. If the caster is entangled AND taking damage simultaneously, both DCs apply; the caster must make each check. Builder confirms the existing concentration resolver structure — are DCs computed as a single value or as a table lookup by trigger type?

Current state (NOT STARTED): `ENTANGLED` is in `ConditionType` enum (used elsewhere). The concentration resolver does not check for `ENTANGLED` and does not add the entangled concentration DC to the check.

### Scope

**`aidm/core/concentration_resolver.py`** — find the site where concentration DC is computed. Add an entangled check:

```python
# WO-ENGINE-CONCENTRATION-ENTANGLED-001: PHB p.175 — entangled concentration DC = spell_level + 15
_conditions = caster.get(EF.CONDITIONS, {})
if ConditionType.ENTANGLED in _conditions:
    _entangled_dc = spell_level + 15
    concentration_checks.append(ConcentrationCheck(dc=_entangled_dc, trigger="entangled"))
```

If the resolver computes a single DC rather than a list of checks, determine whether entangled should replace or add to the existing DC. Per RAW: each trigger generates its own check; the caster must beat all applicable DCs. If only one DC is tracked, raise it to the highest applicable: `concentration_dc = max(existing_dc, _entangled_dc)`.

Builder confirms the resolver's check collection pattern and implements accordingly. The key observable effect: a caster with ENTANGLED status faces concentration DC of (spell_level + 15) for maintaining concentration, regardless of other triggers.

### Ghost Check Protocol (MANDATORY before writing code)

```bash
grep -n "ENTANGLED\|entangled" aidm/core/concentration_resolver.py
grep -n "ENTANGLED" aidm/schemas/conditions.py
grep -n "concentration" aidm/core/concentration_resolver.py | head -20
ls tests/test_engine_concentration_entangled_001_gate.py
```

Expected: `ENTANGLED` exists in `conditions.py` enum. `concentration_resolver.py` — 0 results for ENTANGLED check. Gate file does not exist.

If concentration resolver already checks ENTANGLED → GHOST, stop and report.

### Parallel Paths Check

Concentration checks may fire from multiple triggers:
- `concentration_resolver.py` (canonical)
- `play_loop.py` vigorous motion path — does this call concentration_resolver, or compute DC inline?
- `spell_resolver.py` defensive casting path — calls concentration_resolver?

Builder confirms all concentration DC paths call the same resolver. If any path computes DC inline and bypasses the central resolver, wire the ENTANGLED check there too.

### Consumption Chain

- **Write:** `EF.CONDITIONS` on caster entity — `ConditionType.ENTANGLED` present (already implemented in condition system)
- **Read:** `concentration_resolver.py` — reads `caster.get(EF.CONDITIONS, {})`, checks ENTANGLED; returns concentration check DC of (spell_level + 15)
- **Effect:** Entangled caster attempting to cast must beat DC = spell_level + 15 on concentration check; failing means spell fails
- **Test:** CE-001..008

### PM Acceptance Notes

- **CE-001:** `ConditionType.ENTANGLED` exists in `aidm/schemas/conditions.py` — confirm (Ghost Check)
- **CE-002:** Non-entangled caster — concentration DC computation does not include any entangled-triggered DC
- **CE-003:** Entangled caster + spell level 1 → concentration DC includes check at (1 + 15) = 16
- **CE-004:** Entangled caster + spell level 3 → concentration DC includes check at (3 + 15) = 18
- **CE-005:** Entangled caster simultaneously taking damage → both entangled DC and damage DC apply (caster must beat both)
- **CE-006:** ENTANGLED removed from conditions → concentration DC drops back to baseline (regression via condition removal)
- **CE-007:** Concentration resolver call chain confirmed — show whether vigorous motion path + defensive casting path both funnel through concentration_resolver
- **CE-008:** Coverage map §4 concentration/entangled row → IMPLEMENTED
- Show before/after diff at concentration DC computation site.
- Confirm exact resolver file path (may not be `concentration_resolver.py` — builder identifies from grep).
- Confirm: is DC `spell_level + 15` (per PHB p.175 table) or is it a different formula in the existing code? If existing code already uses a different DC formula for concentration, note the discrepancy.

### Gate File

`tests/test_engine_concentration_entangled_001_gate.py` — 8 tests (CE-001..008)

---

## ML Preflight Checklist (all WOs)

| Check | WO1 (INC) | WO2 (DTH) | WO3 (CE) |
|-------|-----------|-----------|----------|
| ML-001: EF.* used (no bare strings) | `EF.CONDITIONS` for condition lookup; `ConditionType.INCORPOREAL` enum | `intent.weapon.get(...)` — weapon dict key (not EF field); appropriate | `EF.CONDITIONS` for ENTANGLED check; `ConditionType.ENTANGLED` enum |
| ML-002: All call sites identified | All physical attack paths: standard, full, manyshot, nonlethal | All disarm paths; counter-roll must NOT get bonus | All concentration DC paths: inline vigorous, defensive casting, canonical resolver |
| ML-003: No float in deterministic path | Hit/miss boolean; no float | Integer +4 bonus | Integer DC values (spell_level + 15) |
| ML-004: json.dumps sort_keys | N/A | N/A | N/A |
| ML-005: No WorldState mutation in resolver | attack_resolver reads target conditions, returns result — no mutation | maneuver_resolver reads intent, returns event — no mutation | concentration_resolver reads caster conditions, returns DC check — no mutation |
| ML-006: Coverage map updated | §3 Incorporeal NOT STARTED → IMPLEMENTED (50% magic DEFERRED) | §1 Disarm two-handed NOT STARTED → IMPLEMENTED | §4 Concentration/entangled NOT STARTED → IMPLEMENTED |

---

## Source Artifact Verification

**Source:** `docs/ENGINE_COVERAGE_MAP.md` (read session 33, 2026-03-03 via Explore agent — full gap inventory returned, 288 rows)
**Opened this session:** Yes — Explore agent returned complete NOT STARTED / PARTIAL inventory sorted by section
**Finding IDs referenced:** New findings FINDING-ENGINE-INCORPOREAL-CONDITION-001, FINDING-ENGINE-DISARM-2H-WEAPON-BONUS-001, FINDING-ENGINE-CONCENTRATION-ENTANGLED-001 (promoted directly from coverage map review to WO)
**Exact source details:**
- INC: Coverage map §3 Special Conditions: "Incorporeal — PHB p.310 — NOT STARTED — No incorporeal condition or miss chance mechanic; EF.MISS_CHANCE exists but not incorporeal-specific"
- DTH: Coverage map §1 Combat Core: "Disarm — two-handed weapon advantage — PHB p.155 — NOT STARTED — +4 if using two-handed weapon for disarm not implemented"
- CE: Coverage map §4 Spellcasting Mechanics: "Concentration — entangled — PHB p.175 — NOT STARTED — Entangled condition does not trigger concentration penalty"
**Local presence:** Confirmed — ENGINE_COVERAGE_MAP.md returned full content by Explore agent; all three source rows verified as NOT STARTED.

---

*Batch BC — 3 WOs. ~24 expected gates (INC 8 + DTH 8 + CE 8). New cycle BC=4/5. Next: BD=audit WO.*

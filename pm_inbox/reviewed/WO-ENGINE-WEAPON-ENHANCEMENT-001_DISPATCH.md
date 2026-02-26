# WO-ENGINE-WEAPON-ENHANCEMENT-001 — Magic Weapon Enhancement Bonus to Attack and Damage

**Issued:** 2026-02-26
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** HIGH (FINDING-COVERAGE-MAP-001 rank #16 — every magic weapon mechanically identical to mundane)
**WO type:** BUG (field exists for DR bypass; attack/damage bonus absent)
**Gate:** ENGINE-WEAPON-ENHANCEMENT (10 tests)

---

## 1. Target Lock

**What works:** Enhancement bonus on weapons is already used for DR bypass (`extract_weapon_bypass_flags()` in `damage_reduction.py` — WO-ENGINE-DR-001). The weapon schema therefore already has an `enhancement_bonus` field (or equivalent). The field exists; it is simply never added to attack rolls or damage rolls.

**What's missing:**
- `attack_resolver.py` line 386–398: `attack_bonus_with_conditions` accumulates BAB, feat modifiers, condition modifiers, inspire courage — no enhancement bonus
- `attack_resolver.py` line 538–545: `base_damage_with_modifiers` accumulates STR, feat damage, inspire courage — no enhancement bonus
- `full_attack_resolver.py` line 414–416: same damage accumulation, same gap
- Result: a +3 longsword attacks and damages identically to a mundane longsword. The only effect of the enhancement bonus is bypassing magic DR — which is correct but incomplete.

**PHB reference:** PHB p.224 — "Magic weapons have enhancement bonuses ranging from +1 to +5. They apply these bonuses to both attack rolls and damage rolls."

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | Where is the enhancement bonus stored? | On the `Weapon` dataclass — likely `intent.weapon.enhancement_bonus` (int). Confirm field name from `aidm/schemas/attack.py` or wherever `Weapon` is defined. If the field is named differently, adapt. |
| 2 | Attack roll: where to add? | In `attack_bonus_with_conditions` accumulation block (lines 386–398 of attack_resolver.py). Add `+ intent.weapon.enhancement_bonus` to the sum. |
| 3 | Damage roll: where to add? | At line 545: `base_damage_with_modifiers`. Add `+ intent.weapon.enhancement_bonus` here — after STR/grip calculation, alongside feat and inspire bonuses. |
| 4 | Full attack resolver — separate addition needed? | Yes. `full_attack_resolver.py` has its own damage accumulation at line 414–416. Add `+ weapon.enhancement_bonus` there as well. Confirm the variable name for the weapon object in that context. |
| 5 | Is enhancement bonus multiplied on critical hits? | Yes — PHB p.224: enhancement bonus is part of weapon damage and IS multiplied by the crit multiplier. It is already included in the damage dice that get multiplied. So adding it to `base_damage` (line 538 or 414) rather than `base_damage_with_modifiers` (post-crit) is correct — verify crit multiplication point in the code. |
| 6 | Does a mundane weapon (enhancement_bonus = 0) need a guard? | No — adding 0 is a no-op. No guard needed. |
| 7 | Does this affect natural attacks? | Natural attacks go through `natural_attack_resolver.py`. Check whether that resolver also uses `intent.weapon.enhancement_bonus` or a separate field. If natural attacks have their own damage pipeline, add there too or document as a debrief gap. |

---

## 3. Contract Spec

### Modification: `aidm/core/attack_resolver.py` — attack bonus (lines 386–398)

Add `+ intent.weapon.enhancement_bonus` to the `attack_bonus_with_conditions` sum:

```python
attack_bonus_with_conditions = (
    intent.attack_bonus
    + attacker_modifiers.attack_modifier
    + mounted_bonus
    + terrain_higher_ground
    + feat_attack_modifier
    + flanking_bonus
    + intent.weapon.enhancement_bonus          # WO-ENGINE-WEAPON-ENHANCEMENT-001
    - attacker.get(EF.NEGATIVE_LEVELS, 0)
    + _fd_attack_penalty
    + _weapon_broken_penalty
    + _vs_blinded_bonus
    + _inspire_attack_bonus
)
```

### Modification: `aidm/core/attack_resolver.py` — damage (line 538)

Enhancement bonus belongs in `base_damage` (pre-crit-multiplication), not `base_damage_with_modifiers` (post-crit):

```python
base_damage = (
    sum(damage_rolls)
    + intent.weapon.damage_bonus
    + str_to_damage
    + intent.weapon.enhancement_bonus          # WO-ENGINE-WEAPON-ENHANCEMENT-001
)
```

Verify that `base_damage` is what gets multiplied on crit. If the crit path uses `base_damage_with_modifiers`, move the enhancement bonus there instead. Builder must confirm before writing.

### Modification: `aidm/core/full_attack_resolver.py` — damage (line 414)

```python
base_damage = (
    sum(damage_rolls)
    + weapon.damage_bonus
    + str_to_damage
    + weapon.enhancement_bonus                 # WO-ENGINE-WEAPON-ENHANCEMENT-001
)
```

Confirm `weapon` variable name in `full_attack_resolver.py` context.

---

## 4. Implementation Plan

### Step 1 — Confirm weapon field name
Read `aidm/schemas/attack.py` (or wherever `Weapon` dataclass lives). Confirm the enhancement bonus field is `enhancement_bonus: int = 0`. If named differently, use that name throughout.

### Step 2 — `aidm/core/attack_resolver.py`
Two additions: attack bonus accumulation and base_damage. ~2 lines each.

### Step 3 — `aidm/core/full_attack_resolver.py`
One addition: base_damage. ~1 line.

### Step 4 — Confirm crit multiplication point
Read the crit path in attack_resolver.py. Verify that `base_damage` (not `base_damage_with_modifiers`) is what gets multiplied. If wrong, adjust placement of enhancement bonus accordingly.

### Step 5 — Tests (`tests/test_engine_weapon_enhancement_gate.py`)
Gate: ENGINE-WEAPON-ENHANCEMENT — 10 tests

| Test | Description |
|------|-------------|
| WE-01 | +1 weapon: attack roll is +1 higher than mundane equivalent |
| WE-02 | +1 weapon: damage roll is +1 higher than mundane equivalent |
| WE-03 | +3 weapon: attack +3, damage +3 |
| WE-04 | Mundane weapon (enhancement_bonus=0): no change to attack or damage |
| WE-05 | Enhancement bonus IS multiplied on critical hit (crit multiplier ×2 on base_damage which includes enhancement) |
| WE-06 | Full attack action: enhancement bonus applies to every iterative attack roll and damage roll |
| WE-07 | +2 weapon vs DR 5/magic: enhancement bonus still bypasses DR (existing DR behavior unchanged) |
| WE-08 | Attack event payload includes enhancement_bonus field for auditability |
| WE-09 | Enhancement bonus stacks with Power Attack, Inspire Courage, and feat damage modifiers |
| WE-10 | Regression: ENGINE-DR 10/10, ENGINE-CHARGE 10/10 unchanged |

---

## Integration Seams

**Files touched:**
- `aidm/core/attack_resolver.py` — 2 additions (~2 lines each)
- `aidm/core/full_attack_resolver.py` — 1 addition (~1 line)

**Files NOT touched:**
- `aidm/schemas/attack.py` — Weapon dataclass unchanged (field already exists)
- `aidm/core/damage_reduction.py` — DR bypass unchanged
- No new EF fields, no schema changes

**Event constructor signature (mandatory):**
```python
Event(
    event_id=<int>,
    event_type=<str>,
    payload=<dict>,
    timestamp=<float>,
    citations=[],
)
```

**Weapon field access pattern:**
```python
intent.weapon.enhancement_bonus   # in attack_resolver.py
weapon.enhancement_bonus          # in full_attack_resolver.py (confirm variable name)
```

---

## Assumptions to Validate

1. `Weapon` dataclass has `enhancement_bonus: int = 0` — **confirm field name from schema before writing**
2. `base_damage` (not `base_damage_with_modifiers`) is multiplied on crit — **confirm from crit path in attack_resolver.py**
3. `full_attack_resolver.py` has a `weapon` variable in scope at line 414 — confirmed from inspection
4. Natural attack resolver is a separate path — check and document if enhancement bonus should apply there (debrief finding if out of scope)

---

## Known Gap (document at debrief)

Natural attacks (`natural_attack_resolver.py`) may have a separate damage pipeline. If enhancement bonus is not added there, file as FINDING-ENGINE-WEAPON-ENHANCEMENT-NATURAL-001, LOW, OPEN.

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_dr.py tests/test_engine_gate_charge.py -x -q
```

After implementation:
```bash
python -m pytest tests/test_engine_weapon_enhancement_gate.py -v
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/core/attack_resolver.py` — enhancement bonus in attack accumulation + base_damage
- [ ] `aidm/core/full_attack_resolver.py` — enhancement bonus in base_damage
- [ ] `tests/test_engine_weapon_enhancement_gate.py` — 10/10

**Gate:** ENGINE-WEAPON-ENHANCEMENT 10/10
**Regression bar:** ENGINE-DR 10/10, ENGINE-CHARGE 10/10 unchanged. No new failures.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-WEAPON-ENHANCEMENT-001.md` on completion.

**Three-pass format:**
- Pass 1: per-file breakdown, key findings, open findings table
- Pass 2: PM summary ≤100 words
- Pass 3: retrospective — drift caught, patterns, recommendations

Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

# WO-ENGINE-FAVORED-ENEMY-001 — Ranger Favored Enemy: Attack/Damage Bonus vs Designated Types

**Issued:** 2026-02-26
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** HIGH (FINDING-COVERAGE-MAP-001 — every ranger broken in combat vs favored enemy types)
**WO type:** BUG (class ability referenced in chargen; never enforced in combat resolvers)
**Gate:** ENGINE-FAVORED-ENEMY (10 tests)

---

## 1. Target Lock

**What works:** `aidm/chargen/builder.py` grants favored enemy class abilities at ranger levels 1, 5, 10, 15, 20:
```
1:  ["first_favored_enemy", "track", "wild_empathy"]
5:  ["second_favored_enemy"]
10: ["third_favored_enemy"]
15: ["fourth_favored_enemy"]
20: ["fifth_favored_enemy"]
```
These strings are stored but carry no mechanical data — no creature type is recorded, no bonus is stored.

**What's missing:**
- No entity field stores the ranger's chosen favored enemy types
- No entity field stores the favored enemy bonus magnitude (+2 at 1st, +4 at 5th, etc.)
- `aidm/core/attack_resolver.py` — `resolve_attack()` — never checks for favored enemy
- Damage resolution never applies the bonus
- No creature type field on target entities for matching

**PHB reference (p.47):**
> "At 1st level, a ranger may select a type of creature as a favored enemy. He gains a +2 bonus on Bluff, Listen, Sense Motive, Spot, and Survival checks against creatures of this type. Likewise, he gets a +2 bonus on weapon attack rolls and weapon damage rolls against them."

Bonus progression: +2 at level 1, +4 at level 5, +6 at level 10, +8 at level 15, +10 at level 20.
Additional favored enemies are selected at 5th, 10th, 15th, 20th level; the bonus for the first enemy also increases at each step.

**Scope note:** This WO implements attack and damage bonuses only. Skill bonuses (Bluff, Listen, etc.) are deferred until the skill system is active. Document as a debrief finding.

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | How to store favored enemies? | New EF field: `EF.FAVORED_ENEMIES` — list of dicts, each `{"creature_type": str, "bonus": int}`. Example: `[{"creature_type": "humanoid", "bonus": 4}, {"creature_type": "undead", "bonus": 2}]`. The first entry always has the highest bonus (increased at every 5-level step). |
| 2 | How is favored enemy set? | During chargen (in `builder.py`), at the point where `"first_favored_enemy"` etc. are granted. For chargen fixtures used in tests, set `EF.FAVORED_ENEMIES` directly. Actual "which creature type does this ranger favor?" is a session/chargen input question — this WO provides the field and the resolver; chargen data population is the builder's job at chargen time. |
| 3 | How to store creature type on targets? | New EF field: `EF.CREATURE_TYPE` — string. Examples: `"humanoid"`, `"undead"`, `"aberration"`, `"animal"`, `"dragon"`, etc. Set in entity fixtures / chargen. Default `""` (no type = no match). |
| 4 | Where is the bonus applied in attack resolution? | In `resolve_attack()` in `aidm/core/attack_resolver.py`, around lines 285–299 where `feat_attack_modifier` is computed. Add a `favored_enemy_attack_bonus` to the attack roll before the hit/miss comparison. Also in the damage section, add the bonus to damage. |
| 5 | Does the bonus apply to ranged attacks too? | Yes — PHB p.47 says "weapon attack rolls and weapon damage rolls." Both melee and ranged. |
| 6 | Does the bonus apply to the full attack sequence? | Yes — every iterative attack roll in `full_attack_resolver.py` should also check favored enemy. This WO must wire both `attack_resolver.py` and `full_attack_resolver.py`. |
| 7 | PHB bonus progression — implement fully? | Yes. Store the actual bonus per enemy in `EF.FAVORED_ENEMIES` at chargen time. The resolver reads whatever is stored — it doesn't compute the progression itself. This keeps the resolver simple and the data authoritative. |
| 8 | Sneak Attack immunity analogy? | `EF.CRIT_IMMUNE` uses the same creature-type approach (opt-in per entity). Use the same philosophy for `EF.CREATURE_TYPE`. |

---

## 3. Contract Spec

### New EF constants in `aidm/schemas/entity_fields.py`

```python
FAVORED_ENEMIES = "favored_enemies"
# list[dict]: Ranger's favored enemy table.
# Each entry: {"creature_type": str, "bonus": int}
# Example: [{"creature_type": "humanoid", "bonus": 4}, {"creature_type": "undead", "bonus": 2}]
# Populated at chargen. Empty list = no favored enemies (non-ranger).
# PHB p.47. Bonus applies to attack rolls and damage rolls (not skills — deferred).

CREATURE_TYPE = "creature_type"
# str: Creature's primary type for mechanical matching.
# PHB types: humanoid, undead, aberration, animal, construct, dragon, elemental,
#   fey, giant, magical beast, monstrous humanoid, ooze, outsider, plant, undead, vermin.
# Default "": no type match (no favored enemy bonus applies).
```

### Modification: `aidm/core/attack_resolver.py` — `resolve_attack()`

After the `feat_attack_modifier` computation (around line 299), add:

```python
# WO-ENGINE-FAVORED-ENEMY-001: Ranger Favored Enemy
_favored_enemy_bonus = 0
_attacker_favored = attacker.get(EF.FAVORED_ENEMIES, [])
if _attacker_favored:
    _target_type = target.get(EF.CREATURE_TYPE, "")
    for _fe in _attacker_favored:
        if _fe.get("creature_type", "") == _target_type and _target_type != "":
            _favored_enemy_bonus = _fe.get("bonus", 0)
            break
```

Apply `_favored_enemy_bonus` to:
1. **Attack roll:** Add to the attack bonus before hit/miss comparison
2. **Damage roll:** Add as a flat bonus to damage (not multiplied on crit — PHB does not multiply Favored Enemy damage bonus)

### Modification: `aidm/core/full_attack_resolver.py`

Apply the same favored enemy bonus check to each iterative attack in the full attack loop. The pattern is identical — read from the same EF fields. The bonus is flat per attack and per damage roll; it does not stack for multiple attacks (same +N per hit, applied to each).

### Chargen (`aidm/chargen/builder.py`)

At level-up blocks granting `"first_favored_enemy"`, `"second_favored_enemy"`, etc., initialize or append to `EF.FAVORED_ENEMIES`. For test purposes, the builder test fixtures will set this field directly. The actual chargen UI input question ("which creature type?") is out of scope — the field must exist and be readable.

---

## 4. Implementation Plan

### Step 1 — `aidm/schemas/entity_fields.py`
Add `FAVORED_ENEMIES` and `CREATURE_TYPE` constants.

### Step 2 — `aidm/core/attack_resolver.py`
Add favored enemy bonus computation and application (attack + damage). Confirm exact variable names at the attack bonus accumulation and damage accumulation sites from the current code.

### Step 3 — `aidm/core/full_attack_resolver.py`
Mirror the same bonus in the full attack loop.

### Step 4 — Tests (`tests/test_engine_favored_enemy_gate.py`)
Gate: ENGINE-FAVORED-ENEMY — 10 tests

| Test | Description |
|------|-------------|
| FE-01 | Ranger with FAVORED_ENEMIES=[{type:"humanoid", bonus:2}] attacks humanoid: attack roll +2 |
| FE-02 | Same ranger vs humanoid: damage +2 per hit |
| FE-03 | Ranger attacks non-favored type (undead when favored is humanoid): no bonus |
| FE-04 | Ranger with multiple favored enemies: correct bonus for each matching type |
| FE-05 | Non-ranger (no EF.FAVORED_ENEMIES): no bonus applied, no error |
| FE-06 | Target with EF.CREATURE_TYPE="": no match, no bonus (empty string guard) |
| FE-07 | Full attack action: favored enemy bonus applied to EACH iterative attack roll and damage |
| FE-08 | Favored enemy damage bonus is NOT multiplied on critical hit (flat, non-crit-multiplied) |
| FE-09 | Event payload for attack includes favored_enemy_bonus field when > 0 |
| FE-10 | Regression: ENGINE-MANEUVER 14/14 and ENGINE-CHARGE 10/10 unchanged |

---

## Integration Seams

**Files touched:**
- `aidm/schemas/entity_fields.py` — 2 new constants
- `aidm/core/attack_resolver.py` — favored enemy bonus block in `resolve_attack()` (~10 lines)
- `aidm/core/full_attack_resolver.py` — same bonus block in full attack loop (~10 lines)
- `aidm/chargen/builder.py` — EF.FAVORED_ENEMIES initialization at class ability grant (for completeness; tests may set directly)

**Files NOT touched:**
- `aidm/core/save_resolver.py` — skill bonuses deferred
- `aidm/core/skill_resolver.py` — skill bonuses deferred

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

**CLASS_LEVELS pattern (mandatory):**
```python
entity.get(EF.CLASS_LEVELS, {}).get("ranger", 0)
```

**Crit non-multiplication:** The favored enemy damage bonus is NOT multiplied on a critical hit. It is added after crit multiplication. Confirm where in attack_resolver.py the crit multiplier is applied, and add the favored enemy flat bonus after that line.

**Attacker/target entity access:** Both `attacker` and `target` raw entity dicts are available in `resolve_attack()` — confirmed from inspection (lines 285–299 use both via `world_state.entities`).

---

## Assumptions to Validate

1. `attacker` and `target` raw dicts are accessible in `resolve_attack()` and in the full attack loop — confirmed from PM inspection
2. Damage accumulation point in `attack_resolver.py` is accessible for adding a flat post-multiplier bonus — validate exact line before writing
3. `full_attack_resolver.py` calls into `attack_resolver.py` or has its own damage computation — confirm to avoid double-application
4. Feat context dict pattern (lines 285–299) is the correct injection point for the attack bonus — validate from code

---

## Known Gap (document at debrief)

**Skill bonuses deferred:** PHB p.47 specifies +2 to Bluff, Listen, Sense Motive, Spot, and Survival vs favored enemy types. These require the skill resolution system to be active. File as FINDING-ENGINE-FAVORED-ENEMY-SKILLS-001, LOW, OPEN at debrief.

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_maneuver.py tests/test_engine_gate_charge.py -x -q
```

After implementation:
```bash
python -m pytest tests/test_engine_favored_enemy_gate.py -v
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```

ENGINE-FAVORED-ENEMY 10/10 new. ENGINE-MANEUVER 14/14 and ENGINE-CHARGE 10/10 unchanged.

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/schemas/entity_fields.py` — `FAVORED_ENEMIES`, `CREATURE_TYPE` constants
- [ ] `aidm/core/attack_resolver.py` — favored enemy attack + damage bonus
- [ ] `aidm/core/full_attack_resolver.py` — same bonus in full attack loop
- [ ] `aidm/chargen/builder.py` — EF.FAVORED_ENEMIES initialization at class ability grant
- [ ] `tests/test_engine_favored_enemy_gate.py` — 10/10

**Gate:** ENGINE-FAVORED-ENEMY 10/10
**Regression bar:** ENGINE-MANEUVER 14/14, ENGINE-CHARGE 10/10 unchanged. No new failures.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-FAVORED-ENEMY-001.md` on completion.

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

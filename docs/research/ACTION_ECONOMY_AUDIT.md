# Action Economy Audit — D&D 3.5e Engine

**Date:** 2026-02-13
**Scope:** Complete mechanical inventory of combat action economy implementation.
**Purpose:** Establish what's correct, what's broken, and what doesn't exist yet. Inform Movement v1 WO scoping and playtest interpretation.

---

## Executive Summary

The engine has **surprisingly deep** implementation of attack resolution, AoO, combat maneuvers, flanking, cover, concealment, reach, and conditions. The action budget system (standard/move/full-round/swift/free) is enforced at the CLI layer.

**The critical gap is movement.** Movement is hard-locked to single-square adjacency (StepMoveIntent). There is no FullMoveIntent, no speed enforcement, no multi-square pathing, and no 5-foot step distinction. Every entity effectively has speed = 5 ft. This contaminates all playtest signals related to spacing, positioning, threat dynamics, AoE counterplay, and melee/ranged balance.

Secondary gaps: delay/ready actions, ranged AoO provocation, spellcasting AoO provocation, TWF integration, charge as standalone action, item usage, and several defensive actions.

---

## I. MOVEMENT SYSTEM

### What Exists

| Component | Status | Location |
|-----------|--------|----------|
| `MoveIntent` (voice layer) | Schema only, no legality | `aidm/schemas/intents.py:91-115` |
| `StepMoveIntent` (1-square) | **Enforced** — adjacency validated | `aidm/schemas/attack.py:144-177` |
| `MountedMoveIntent` (CP-18A) | Implemented with path field | `aidm/schemas/mounted_combat.py:96-139` |
| `EF.BASE_SPEED` field | **Defined** in entity_fields | `aidm/schemas/entity_fields.py:130` |
| `speed_ft` on content pack creatures | **Present** on all 30+ creatures | `aidm/data/content_pack/creatures.json` |
| `speed_ft` on bestiary entries | **Carried through** compilation | `aidm/schemas/bestiary.py:145` |
| Encumbrance speed penalties | **Fully implemented** | `aidm/core/encumbrance.py:208-233` |
| Terrain movement cost queries | **Implemented** (1x/2x/4x) | `aidm/core/terrain_resolver.py:94-171` |
| AoO on movement | **Implemented** (leaving threatened sq) | `aidm/core/aoo.py:138-362` |

### What's Broken / Missing

| Gap | Impact | Deferred To |
|-----|--------|-------------|
| **No FullMoveIntent** | Entities can only move 1 square/action | CP-16+ |
| **No speed enforcement** | `base_speed` exists but is never checked during movement | CP-16+ |
| **No multi-square pathing** | No BFS/A*/waypoint validation | CP-16+ |
| **No 5-foot step distinction** | All moves treated identically for AoO | CP-16+ |
| **No diagonal cost rule** | 3.5e uses 5/10/5/10 pattern; not implemented | CP-16+ |
| **No pathfinding** | Player must specify single adjacent square | CP-16+ |
| **No withdraw action** | Cannot move out of threatened area safely | CP-16+ |
| **No charge action** (standalone) | Charge flag exists on maneuvers, no ChargeIntent | CP-16+ |
| **No run action** | No x4 speed multiplier | CP-16+ |
| `base_speed` not on runtime entities | Fixture entities (play_controller.py:124-225) lack `EF.BASE_SPEED` | — |

### Speed Field End-to-End Status

```
Content Pack (creatures.json)  →  speed_ft: 30  ✓ present
Bestiary (bestiary.py)         →  speed_ft: 30  ✓ carried through
Entity Fields (EF.BASE_SPEED)  →  defined       ✓ constant exists
Encumbrance resolver           →  reads it      ✓ defaults to 30 if missing
Runtime entities (fixture)     →  NOT SET        ✗ not populated
play.py movement validation    →  NOT CHECKED    ✗ adjacency only
```

**Answer to your question:** The field exists in schema, in content pack data, and in the encumbrance resolver (which defaults to 30 if missing). But it is **not populated on runtime combat entities** and **not enforced during movement resolution**. The plumbing is 80% there; the last-mile wiring and enforcement are missing.

---

## II. ACTION ECONOMY SYSTEM

### What Exists (Correct)

| Component | Status | Location |
|-----------|--------|----------|
| ActionBudget class | **Enforced at CLI layer** | `play.py:88-184` |
| 1 standard + 1 move + 1 swift per turn | ✓ | `play.py:97-118` |
| Full-round consumes standard + move | ✓ | `play.py:111` |
| Can trade standard → second move | ✓ | `play.py:109` |
| Can't full-attack after moving | ✓ | `play.py:111` (checks `moved` flag) |
| Free actions (help, status, map) | ✓ unlimited | `play.py:70-85` |
| Denial reason messages | ✓ specific explanations | `play.py:163-183` |

### Action Cost Mapping

```python
_ACTION_COST = {
    "attack":       "standard",
    "full_attack":  "full_round",
    "move":         "move",
    "cast":         "standard",
    "trip":         "standard",
    "bull_rush":    "standard",
    "disarm":       "standard",
    "grapple":      "standard",
    "sunder":       "standard",
    "overrun":      "standard",
    "end_turn":     "end",
    "help":         "free",
    "status":       "free",
    "map":          "free",
}
```

### What's Missing

| Gap | D&D 3.5e Rule | Impact |
|-----|---------------|--------|
| **5-foot step as free action** | PHB p.144: free if no other movement taken | Can't reposition without spending move action |
| **Total Defense** | +4 AC, standard action, no attacks | No defensive option |
| **Fighting Defensively** | -4 attack, +2 AC (or +3 with Tumble 5+) | No risk/reward tradeoff |
| **Aid Another** | Standard action, +2 to ally's attack or AC | No cooperative combat |
| **Delay action** | Voluntarily lower initiative count | No tactical timing |
| **Ready action** | Standard action, set trigger condition | No reactive play |
| **Coup de Grace** | Full-round, auto-crit helpless target | Mentioned in conditions, no resolver |
| **Item usage** | Move/standard action depending on item | No UseItemIntent |
| Action economy enforced at CLI only | Core engine doesn't validate | `play_loop.py` executes whatever intent it receives |

---

## III. ATTACK SYSTEM

### What Exists (Correct)

| Component | Status | Location |
|-----------|--------|----------|
| Single attack (AttackIntent) | ✓ full pipeline | `aidm/core/attack_resolver.py` |
| Full attack (FullAttackIntent) | ✓ iterative attacks from BAB | `aidm/core/full_attack_resolver.py` |
| d20 + modifiers vs AC | ✓ | `attack_resolver.py` |
| Natural 1 always misses | ✓ | `attack_resolver.py` |
| Natural 20 always hits + threatens | ✓ | `attack_resolver.py` |
| Critical threat detection | ✓ weapon.critical_range | WO-FIX-002 |
| Critical confirmation roll | ✓ d20+bonus vs AC, no auto-hit | WO-FIX-002 |
| Critical damage multiplication | ✓ base×multiplier, sneak excluded | WO-FIX-002 |
| Iterative attacks (BAB/BAB-5/BAB-10/BAB-15) | ✓ | CP-11 |
| STR modifier to melee damage | ✓ | PHB p.113 |
| Power Attack (1:1 and 1:2 two-hand) | ✓ | WO-034-FIX |
| Weapon Focus (+1 attack) | ✓ | WO-034 |
| Weapon Specialization (+2 damage) | ✓ | WO-034 |
| Condition modifiers (shaken -2, etc.) | ✓ | CP-16 |
| Mounted combat bonus (+1 vs smaller) | ✓ | CP-18A |
| Higher ground bonus (+1 melee) | ✓ | CP-19 |
| Flanking (+2 melee, angle ≥ 135°) | ✓ | `aidm/core/flanking.py` |
| Cover AC bonus (+4/+8) | ✓ | CP-19 |
| Concealment miss chance (d100) | ✓ | WO-049 |
| Sneak attack (precision, no crit mult) | ✓ | WO-050B |
| Damage Reduction (post-crit, post-sneak) | ✓ | WO-048 |
| Deterministic RNG consumption order | ✓ documented | All resolvers |

### What's Missing

| Gap | Impact |
|-----|--------|
| **Ranged attacks** | No RangedAttackIntent; `is_ranged` always False |
| **Range increment penalties** | No -2 per increment |
| **Shooting into melee** | No -4 penalty (Precise Shot exists but unused) |
| **Two-weapon fighting** | Feat defs exist, combat integration absent; `is_twf` always False |
| **Cleave/Great Cleave** | Feat exists, extra attack trigger not implemented |
| **Spring Attack** | Feat exists, movement suppression not implemented |
| **Weapon proficiency** | Assumed proficient; TODO comment in feat_resolver |

---

## IV. ATTACKS OF OPPORTUNITY

### What Exists (Correct)

| Component | Status | Location |
|-----------|--------|----------|
| Threatened squares (5-ft reach) | ✓ 8 adjacent | `aidm/core/aoo.py` |
| Movement provocation (leaving threatened sq) | ✓ | `aoo.py:138-362` |
| Mounted movement provocation | ✓ mount provokes | CP-18A |
| Bull rush provocation (all threatening) | ✓ | PHB p.154 |
| Trip/Disarm/Grapple/Sunder/Overrun provocation (target only) | ✓ | CP-18 |
| One AoO per reactor per round | ✓ tracked | `aoo.py:268` |
| Initiative-order resolution | ✓ deterministic | `aoo.py` |
| Cover blocks AoO execution | ✓ standard/improved | CP-19 |
| Tumble avoidance (DC 15) | ✓ | WO-035 |
| Provoker defeat aborts main action | ✓ | `aoo.py` |
| AoO uses resolve_attack() pipeline | ✓ | `aoo.py` |

### What's Missing

| Gap | Impact |
|-----|--------|
| **Ranged attack provocation** | Ranged in melee doesn't provoke (TODO in aoo.py:245) |
| **Spellcasting provocation** | Casting in threat doesn't provoke (TODO in aoo.py:248) |
| **5-foot step immunity** | All movement provokes identically |
| **Withdraw immunity** | No way to leave threat safely (except Tumble) |
| **Combat Reflexes** | No multiple AoOs per round |
| **Mobility feat AC bonus** | Computed but not applied (TODO WO-034) |
| **Reach weapon AoO range** | Reach resolver exists but not integrated into AoO threat |

---

## V. COMBAT MANEUVERS

### Fully Implemented

| Maneuver | Mechanics | AoO | Location |
|----------|-----------|-----|----------|
| **Bull Rush** | Opposed STR, push 5ft + 5ft/5 margin, hazard routing | All threatening | `maneuver_resolver.py:191-431` |
| **Trip** | Touch attack + opposed STR vs max(STR,DEX), counter-trip, applies Prone | Target only | `maneuver_resolver.py:438-705` |
| **Overrun** | Opposed STR vs max(STR,DEX), defender avoidance, prone on success | Target only | `maneuver_resolver.py:712-934` |

### Degraded (Intentionally)

| Maneuver | What Works | What's Degraded | Reason |
|----------|-----------|-----------------|--------|
| **Grapple** | Touch attack + opposed check, applies Grappled condition | Unidirectional only (target grappled, attacker unaffected); no pin/escape/damage | Avoids G-T3C gate |
| **Sunder** | Opposed attack rolls, damage calculation | Narrative only — no persistent item state change | No item HP system |
| **Disarm** | Opposed attack rolls, counter-disarm | Weapon "drops" narratively, no state change | No item slot system |

### Not Implemented

| Maneuver | Status |
|----------|--------|
| **Charge** (standalone) | Charge flag on maneuvers; no ChargeIntent with movement + attack |
| **Feint** | Not implemented |
| **Total Defense** | Not implemented |
| **Fighting Defensively** | Not implemented |
| **Aid Another** | Not implemented |
| **Coup de Grace** | Referenced in conditions, no resolver |

---

## VI. COMBAT STATE MACHINE

### What Exists (Correct)

| Component | Status | Location |
|-----------|--------|----------|
| Initiative rolling (d20 + DEX + misc) | ✓ | `aidm/core/initiative.py` |
| Deterministic tie-breaking (total → DEX → actor_id) | ✓ | `initiative.py` |
| Flat-footed at combat start | ✓ all actors | `combat_controller.py` |
| Flat-footed clears on first action | ✓ | `combat_controller.py:305-328` |
| Round tracking (round_index) | ✓ | `combat_controller.py:249` |
| AoO-used-this-round reset per round | ✓ | `combat_controller.py` |
| Spell duration tick per round | ✓ | WO-015 |
| Turn start/end events | ✓ | `play_loop.py:730-1483` |
| Defeated entity skip | ✓ | `play.py` main loop |
| Combat-over detection | ✓ | `play.py` |

### What's Missing

| Gap | D&D 3.5e Rule |
|-----|---------------|
| **Delay action** | Voluntarily drop in initiative order |
| **Ready action** | Set trigger, act out of turn |
| **Surprise round** | Flat-footed covers the AC effect, but no "only one action" constraint |
| **Action economy in core engine** | Budget enforced at CLI only, not in play_loop |

---

## VII. ENTITY MODEL

### What Exists

All entities are dicts keyed by `EF.*` constants. Fields present on runtime combat entities:

- `entity_id`, `name`, `team`, `defeated`
- `hp_current`, `hp_max`, `ac`
- `attack_bonus`, `bab`, `str_mod`, `dex_mod` (and other ability mods)
- `weapon`, `weapon_damage`
- `position` (as `{x, y}` dict)
- `size_category`
- `conditions` (dict of ConditionInstance)
- `feats` (list of feat IDs)
- `skill_ranks`, `class_skills`, `armor_check_penalty`
- `damage_reductions`, `miss_chance`
- `base_stats` (ability scores), `permanent_stat_modifiers`
- `save_fortitude`, `save_reflex`, `save_will`

### Not Present on Runtime Entities (But Defined in Schema)

| Field | In Schema | In Content Pack | On Runtime Entity |
|-------|-----------|-----------------|-------------------|
| `base_speed` | ✓ EF.BASE_SPEED | ✓ speed_ft on creatures | **✗ not populated** |
| `elevation` | ✓ EF.ELEVATION | — | Sometimes |
| `xp`, `level`, `class_levels` | ✓ | — | Not in fixture |
| `feat_slots` | ✓ | — | Not in fixture |
| `inventory` | ✓ | — | Not in fixture |
| `encumbrance_load` | ✓ | — | Not in fixture |

---

## VIII. FEAT SYSTEM

### Implemented Feats (15 total, WO-034)

| Feat | Modifier Applied | Combat Integration |
|------|-----------------|-------------------|
| Power Attack | ✓ attack penalty + damage bonus | ✓ Full |
| Weapon Focus | ✓ +1 attack | ✓ Full |
| Weapon Specialization | ✓ +2 damage | ✓ Full |
| Improved Initiative | ✓ +4 initiative | ✓ Full |
| Point Blank Shot | ✓ +1 attack/damage ≤30ft | Computed, not enforced (no ranged) |
| Precise Shot | Defined | Not enforced (no ranged) |
| Rapid Shot | Defined | Not enforced (no ranged) |
| Dodge | ✓ +1 AC | ✓ Applied |
| Mobility | ✓ +4 AC vs movement AoO | Computed, **not applied** (TODO) |
| Spring Attack | Defined | Not enforced |
| Cleave | Defined | Extra attack trigger not implemented |
| Great Cleave | Defined | Extra attack trigger not implemented |
| Two-Weapon Fighting | ✓ Penalty computation exists | **Not integrated** into attack resolution |
| Improved TWF | Defined | Not integrated |
| Greater TWF | Defined | Not integrated |

---

## IX. SPELLCASTING

### What Exists

| Component | Status | Location |
|-----------|--------|----------|
| SpellDefinition schema | ✓ | `aidm/schemas/` |
| Spell targeting (single, area, self, touch, ray) | ✓ | WO-014 |
| AoE rasterization (burst, cone, line) | ✓ | WO-014 |
| Save mechanics (none/half/negates/partial) | ✓ | `spell_resolver.py` |
| Damage types (fire/cold/acid/etc.) | ✓ | `spell_resolver.py` |
| Duration tracking (rounds) | ✓ | WO-015 |
| Concentration requirement | ✓ tracked | WO-015 |
| Line of sight/effect | ✓ | CP-19 |

### What's Missing

| Gap | Impact |
|-----|--------|
| **Spell slot tracking** | No preparation or slot consumption |
| **Spells per day** | Unlimited casting |
| **Spell interruption** | No concentration check on damage during casting |
| **Casting provokes AoO** | TODO in aoo.py; CastSpellIntent not hooked |
| **Defensive casting (Concentration check)** | Not implemented |
| **Spell components** | Not tracked |

---

## X. CORRECTNESS BUGS (Implemented but Wrong)

The following are not missing features — they are implemented mechanics that deviate from PHB 3.5e rules. Discovered via deep-dive audit of resolver code against RAW.

### A. Attack Damage Math

**BUG-1: Two-handed STR bonus not applied (HIGH)**
- **Rule:** PHB p.114 — "When you deal damage with a weapon that you are wielding two-handed, you add 1-1/2 times your Strength bonus."
- **Code:** `attack_resolver.py:363`, `full_attack_resolver.py:297` — adds `str_modifier` (1x) regardless of `weapon.is_two_handed`
- **Impact:** All two-handed weapons deal 50% less STR damage than they should. A Fighter with STR 18 (+4) and a greatsword should add +6 damage but only adds +4.
- **Fix:** Check `intent.weapon.is_two_handed`; if True, use `int(str_modifier * 1.5)`.

**BUG-2: Full attack doesn't stop when target dies (HIGH)**
- **Rule:** You cannot attack a defeated creature with remaining iterative attacks (you may redirect per DM, but attacks don't auto-resolve against a corpse).
- **Code:** `full_attack_resolver.py:546-591` — loop runs all iterative attacks, accumulates total damage, applies HP change once after loop. No per-attack defeat check.
- **Impact:** Wastes RNG (determinism concern), emits misleading attack events against dead targets. Damage is correct (accumulated), but event stream is wrong.
- **Fix:** Check `hp_after <= 0` after each attack in the loop; break if defeated.

### B. Condition AC Modifiers

**BUG-3: Prone AC not differentiated by attack type (HIGH)**
- **Rule:** PHB p.311 — Prone: "+4 AC vs ranged, -4 AC vs melee"
- **Code:** `conditions.py:207` — flat `ac_modifier=-4` applied to ALL attacks
- **Impact:** Ranged attacks against prone targets are too easy to hit (should be +4 AC bonus, not -4 penalty). Completely inverts the intended mechanic for ranged.
- **Root cause:** `is_ranged` is hardcoded False (`attack_resolver.py:226`). No context-sensitive condition modifier query exists.
- **Fix:** `get_condition_modifiers()` needs an `attack_type` parameter; Prone returns -4 for melee, +4 for ranged.

**BUG-4: Helpless AC not differentiated by attack type (MEDIUM)**
- **Rule:** PHB p.311 — Helpless: melee attackers get +4 bonus, ranged get no special bonus
- **Code:** `conditions.py:275` — flat `ac_modifier=-4` applied to all attacks
- **Impact:** Same as Prone — ranged attacks incorrectly benefiting from -4 AC.
- **Fix:** Same architectural fix as BUG-3.

**BUG-5: Grappled DEX penalty may not reach AC (MEDIUM)**
- **Rule:** PHB p.156 — Grappled: -4 DEX penalty (should reduce AC via DEX modifier)
- **Code:** `conditions.py:251` — stores `dex_modifier=-4` but `attack_resolver.py:243` only reads `ac_modifier` and `cover_result.ac_bonus`
- **Impact:** Grappled targets may not have reduced AC from the -4 DEX penalty if the resolver doesn't propagate `dex_modifier` to AC.
- **Needs verification:** Whether `dex_modifier` feeds into AC elsewhere in the pipeline.

### C. Combat Maneuver Math

**BUG-6: Disarm uses absolute size modifiers, not relative (MEDIUM)**
- **Rule:** PHB p.155 — "If the combatant is larger, he/she gets a +4 bonus on the roll for each size category of difference."
- **Code:** `maneuver_resolver.py:1164-1173` — Both attacker and defender add their own absolute size modifier (Large=+4, Small=-4). This accidentally produces the correct relative difference when subtracted, but **only because the opposed roll cancels correctly**.
- **Status:** Actually correct by mathematical coincidence. The absolute modifiers on each side produce the same result as a relative calculation when opposed. NOT A BUG.

**BUG-7: Disarm missing weapon property modifiers (LOW)**
- **Rule:** PHB p.155 — Two-handed weapon: +4 to defender. Light weapon: -4 from defender.
- **Code:** `maneuver_resolver.py:1164-1173` — No weapon property check.
- **Impact:** Two-handed weapon users don't get the +4 defensive bonus they should.
- **Note:** Intentional omission given no weapon slot system, but deviates from RAW.

**BUG-8: Sunder missing defender weapon magic bonus (LOW)**
- **Rule:** PHB p.159 — "If the defender is using a magical weapon, add its enhancement bonus."
- **Code:** `maneuver_resolver.py:1006-1009` — No magic bonus applied.
- **Impact:** Magical weapons are easier to sunder than they should be.
- **Note:** Minor given Sunder is already degraded (narrative only).

### D. Combat State Machine

**BUG-9: Flat-footed clears on failed action attempts (LOW)**
- **Rule:** PHB p.137 — Flat-footed should clear when an actor "has had a chance to act" (i.e., takes a meaningful action).
- **Code:** `combat_controller.py:307-328` — Clears flat-footed if ANY non-turn-start/end events exist, including `intent_validation_failed`.
- **Impact:** An actor who tries to attack a defeated target (invalid action) loses flat-footed. Minor edge case.

**BUG-10: Defeated actors not skipped in combat_controller (LOW, mitigated)**
- **Code:** `combat_controller.py:274-289` — Does not check `EF.DEFEATED` before calling `execute_turn()`.
- **Mitigation:** `play.py:840-843` (CLI layer) does skip defeated actors. The controller layer is inconsistent but the CLI prevents the bug from manifesting.

### E. Verified Correct (No Bug)

These were investigated and confirmed correct:

- **Power Attack 1:2 ratio for two-handed** — matches PHB 3.5e p.98 exactly ("add twice the number")
- **Natural 1/20 rules** — correct
- **Critical confirmation no auto-hit on nat 20** — correct
- **Sneak attack not multiplied on crits** — correct (added after multiplier)
- **DR application order** — correct (post-crit, post-sneak)
- **Iterative attack BAB thresholds** — correct (BAB ≥ 6 for 2nd, etc.)
- **AoO triggers on leaving threatened square** — correct (not entering)
- **Flanking 135-degree geometry** — correct
- **Cover AC bonuses** — correct (+4/+8, not +2/+4)
- **Concealment miss chance after hit** — correct
- **Condition stacking (additive)** — correct
- **Bull Rush push distance** — correct (5ft + 5ft per 5-point margin)
- **Overrun attacker prone on fail-by-5** — correct
- **AoO damage persists when main action aborts** — correct

---

## XII. CONTAMINATION ASSESSMENT

### Movement Gap Contamination Matrix

Because movement is locked to 1 square per action, these systems **cannot be meaningfully playtested**:

| System | Why Contaminated |
|--------|-----------------|
| **Melee vs ranged balance** | Melee can always close in 1 turn; ranged has no kiting |
| **AoE positioning** | Can't spread out to reduce AoE impact |
| **Flanking tactics** | Trivial to achieve (1 square to reposition) |
| **AoO dynamics** | Movement provocation is near-meaningless at 5ft range |
| **Retreat/chase** | Impossible — everyone moves at same effective speed |
| **Charge** | Doesn't exist, but would be meaningless at 5ft anyway |
| **Terrain/cover positioning** | Can't maneuver to cover in reasonable turns |
| **Encounter difficulty** | Spacing collapses all fights to adjacent melee immediately |
| **Full attack vs single attack** | Tradeoff is broken — moving costs almost nothing |

### Systems That ARE Validly Testable Now

| System | Why Valid |
|--------|----------|
| Attack roll math | Pure dice + modifiers, no position dependency |
| Critical hit pipeline | Pure math |
| Damage calculation chain | Pure math |
| Condition modifier application | Modifies existing rolls |
| Combat maneuver opposed checks | Pure math (once adjacent) |
| Flanking geometry (angle calc) | Math is correct, but ease of achieving flanking is wrong |
| Cover calculation (corner-to-corner) | Math is correct |
| Initiative ordering | No movement dependency |
| Action budget enforcement | Independent of movement distance |

---

## XIII. PRIORITY RANKING FOR REMEDIATION

### Tier 0 — Correctness Bugs (Wrong Math, Fix Before Playtesting)

1. **BUG-1: Two-handed STR 1.5x** — `attack_resolver.py`, `full_attack_resolver.py`
2. **BUG-3: Prone AC melee vs ranged** — `conditions.py`, `attack_resolver.py`
3. **BUG-2: Full attack stops on target death** — `full_attack_resolver.py`
4. **BUG-4: Helpless AC melee vs ranged** — `conditions.py`

### Tier 1 — Blocks All Playtest Validity

1. **Movement v1** — FullMoveIntent, speed enforcement, multi-square pathing, 5-foot step distinction

### Tier 2 — Required for Core Combat Feel

2. **5-foot step as free action** — Distinct from move action, no AoO
3. **Ranged attacks** — RangedAttackIntent, range increments, shooting into melee
4. **Charge** — Move + attack as full-round action
5. **Delay / Ready** — Tactical initiative manipulation

### Tier 3 — Required for Class Balance

6. **Spell slot tracking** — Resource-gated casting
7. **TWF integration** — Connect existing feat defs to attack resolver
8. **Cleave/Great Cleave** — Extra attack trigger on kill
9. **Casting provokes AoO** — Hook CastSpellIntent into AoO system

### Tier 4 — Polish

10. **Total Defense / Fighting Defensively** — Defensive actions
11. **Aid Another** — Cooperative actions
12. **Mobility feat application** — Wire computed AC bonus into AoO
13. **Spring Attack** — Movement AoO suppression
14. **Coup de Grace** — Helpless target execution
15. **Item usage** — Potions, scrolls, wands
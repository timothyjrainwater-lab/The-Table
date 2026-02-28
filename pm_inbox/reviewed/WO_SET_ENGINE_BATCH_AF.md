# WO SET — ENGINE BATCH AF
## Class Feature Expansion IV: Lay on Hands Close, Monk Unarmed Wire, Paladin Remove Disease, Rogue Defensive Roll

**Lifecycle:** DISPATCH-READY
**Issued:** 2026-02-28
**From:** Slate (PM)
**To:** Chisel (builder)
**Gate Budget:** 32 tests (4 WOs × 8 gates)
**Priority:** HIGH — closes open PARTIAL + open DEFERRED finding, extends paladin/rogue feature depth

---

## Pre-Dispatch Backlog Review

Confirmed clean before dispatch:
- 0 HIGH open
- 0 MEDIUM in flight
- FINDING-ENGINE-MONK-UNARMED-ATTACK-WIRE-001 promoted from DEFERRED to IN FLIGHT (this batch)
- AUDIT-WO-002-MANEUVERS confirmed ACCEPTED (lifecycle tag in debrief confirms session 10 verdict; briefing entry was stale)
- All other open MEDIUMs are either deferred with rationale or not adjacent to AF files

---

## WO1 — Lay on Hands: SAI Close + Consume-Site Verification

**Summary:** `aidm/core/lay_on_hands_resolver.py` exists on disk (untracked in git) and is fully wired end-to-end. Existing 11/11 ENGINE-LAY-ON-HANDS gate tests pass against it. WO1 commits the untracked file, confirms the full consume-site chain, adds 8 new play_loop-path gate tests, and promotes coverage to IMPLEMENTED.

**SAI note:** All infrastructure is already in place. No production code changes expected. If Chisel discovers missing wiring during verification, fix it and document the gap.

### RAW Fidelity — PHB p.44

> "Each day she [the paladin] can heal a total number of hit points of damage equal to her paladin level times her Charisma modifier. A paladin with a negative Charisma modifier cannot heal hit points but also doesn't risk harming anyone when she lays on hands. A paladin may choose to divide her healing among multiple recipients, and she doesn't have to use it all at once. Using lay on hands is a standard action."

Key constraints:
- Pool = `paladin_level × CHA_mod` (0 if CHA_mod ≤ 0)
- Standard action, touch
- Divisible across recipients
- Refreshes on full rest (1/day)

### Parallel Paths

| Path | File | Status |
|------|------|--------|
| Chargen write | `chargen/builder.py:959, 1235` | Already sets `EF.LAY_ON_HANDS_POOL` and `EF.LAY_ON_HANDS_USED` |
| Resolver read | `core/lay_on_hands_resolver.py` | Reads both fields; clamps to remaining pool |
| Play loop dispatch | `core/play_loop.py:2965` | `LayOnHandsIntent` branch calls `resolve_lay_on_hands()` |
| Rest reset | `core/rest_resolver.py:130` | Resets `EF.LAY_ON_HANDS_POOL` + sets `EF.LAY_ON_HANDS_USED = 0` |
| Action economy | `core/action_economy.py:179` | Registered as "standard" action |

No shadow path exists. Single resolver, single play_loop branch.

### Consumption Chain

- **Write:** `builder.py:959` — `entity[EF.LAY_ON_HANDS_POOL] = paladin_level * cha_mod` (paladin L2+, `cha_mod > 0`)
- **Read:** `lay_on_hands_resolver.py:57–58` — reads `EF.LAY_ON_HANDS_POOL` and `EF.LAY_ON_HANDS_USED`; computes `remaining`; clamps `amount`
- **Effect:** `EF.HP_CURRENT` increases on target; `EF.LAY_ON_HANDS_USED` incremented on actor; `lay_on_hands_heal` event emitted
- **Rest reset:** `rest_resolver.py:130–131` — `EF.LAY_ON_HANDS_POOL` recalculated; `EF.LAY_ON_HANDS_USED = 0`

### Proof Test (LOH-WO1-001 / LOH-WO1-002)

- Paladin L5, CHA 16 (+3) → `pool = 15`. LayOnHandsIntent `amount=10` against wounded ally → `lay_on_hands_heal` fires, `HP_CURRENT` increases by 10, `pool_remaining = 5`.
- After rest: `EF.LAY_ON_HANDS_USED` resets to 0; pool recalculated from new level/CHA.

### Gate File

`tests/test_engine_lay_on_hands_playloop_gate.py` — 8 tests (LOH-WO1-001 through LOH-WO1-008)

Tests must cover:
- LOH-WO1-001: non-paladin actor → `lay_on_hands_invalid`
- LOH-WO1-002: pool = 0 (CHA_mod ≤ 0) → `lay_on_hands_exhausted`
- LOH-WO1-003: normal heal via play_loop path (LayOnHandsIntent dispatched)
- LOH-WO1-004: amount clamped to pool remaining (request > remaining → heals remainder only)
- LOH-WO1-005: HP_CURRENT clamped to HP_MAX (can't overheal)
- LOH-WO1-006: pool exhausted on second use after depleting remaining
- LOH-WO1-007: pool resets on RestIntent (via rest_resolver path)
- LOH-WO1-008: paladin heals self (actor_id == target_id, valid per PHB p.44)

### Coverage Map Target

- `Lay on Hands (CHA × level HP)` — PHB p.44 — **PARTIAL → IMPLEMENTED**

### PM Acceptance Notes (ML-007)

1. Commit `aidm/core/lay_on_hands_resolver.py` — confirm it appears in the commit diff
2. Show consume-site chain: cite `builder.py:NNN` (write), `lay_on_hands_resolver.py:NNN` (read), `rest_resolver.py:NNN` (reset)
3. LOH-WO1-007 must test the rest_resolver path directly (RestIntent → lay_on_hands_used reset to 0)
4. Confirm existing ENGINE-LAY-ON-HANDS 11/11 still pass after commit

---

## WO2 — Monk Unarmed Attack Wire

**Summary:** `EF.MONK_UNARMED_DICE` is set at chargen per PHB Table 3-10 but never read by the attack resolver. Unarmed monk attacks currently use a static weapon damage value. WO2 wires the consume site: `attack_resolver.py` must read `EF.MONK_UNARMED_DICE` when the attacker is a monk and the weapon is an unarmed strike.

This closes FINDING-ENGINE-MONK-UNARMED-ATTACK-WIRE-001 (previously DEFERRED).

### RAW Fidelity — PHB p.41, Table 3-10

> "A monk's unarmed strike is treated as both a manufactured weapon and a natural weapon for the purpose of spells and effects that enhance or improve either manufactured weapons or natural weapons."

PHB Table 3-10 unarmed damage by monk level:

| Level | Damage (Small) | Damage (Medium) |
|-------|---------------|-----------------|
| 1-3 | 1d4 | 1d6 |
| 4-7 | 1d6 | 1d8 |
| 8-11 | 1d8 | 1d10 |
| 12-15 | 1d10 | 2d6 |
| 16-19 | 2d6 | 2d8 |
| 20 | 2d8 | 2d10 |

The engine must use the correct dice at runtime rather than a hardcoded weapon entry.

### Parallel Paths

| Path | File | Notes |
|------|------|-------|
| Canonical attack | `core/attack_resolver.py` → `resolve_attack()` | Must add unarmed monk dice override |
| Full attack delegation | `core/full_attack_resolver.py` | Delegates to `attack_resolver.py` — no change needed if canonical path is fixed |
| Natural attack delegation | `core/natural_attack_resolver.py` | Delegates to `attack_resolver.resolve_attack()` — handles natural attacks only |

**Parity check required:** Verify that unarmed monk attack via `AttackIntent` and via `FlurryOfBlowsIntent` both use `EF.MONK_UNARMED_DICE`. Flurry path already builds attack sequences through the canonical resolver.

### Consumption Chain

- **Write:** `chargen/builder.py` — `EF.MONK_UNARMED_DICE` set per PHB Table 3-10 at chargen (confirm exact line)
- **Read:** `core/attack_resolver.py` — when processing an unarmed strike for a monk, override `weapon.damage_dice` from `EF.MONK_UNARMED_DICE`
- **Effect:** damage rolled uses level-correct dice (e.g., L8 monk rolls 1d10 not 1d6)
- **Test:** Monk L8 unarmed attack generates damage roll within 1d10 range; L1 monk rolls 1d6

### Proof Test (MUW-001 / MUW-002)

- Monk L8, Medium size, unarmed attack → `MONK_UNARMED_DICE` = "1d10" → damage in [1,10]
- Monk L1, Medium size, unarmed attack → `MONK_UNARMED_DICE` = "1d6" → damage in [1,6]

### Implementation Notes

- The override should only apply when: (1) entity has monk class levels > 0, (2) the weapon being used is an unarmed strike (check weapon type/name, or `EF.MONK_UNARMED_DICE` is set on entity)
- Non-monks using unarmed strike are not affected
- Size modifier: Medium gets base table values; Small monks use one step smaller dice. Confirm `EF.MONK_UNARMED_DICE` is stored as the correct size for the entity (likely set correctly at chargen)
- PHB p.41: unarmed strike is "a free action" to use in combination with other actions — no action economy change needed

### Gate File

`tests/test_engine_monk_unarmed_wire_gate.py` — 8 tests (MUW-001 through MUW-008)

Tests must cover:
- MUW-001: Monk L1 unarmed → damage in 1d6 range
- MUW-002: Monk L4 unarmed → damage in 1d8 range
- MUW-003: Monk L8 unarmed → damage in 1d10 range
- MUW-004: Monk L12 unarmed → damage in 2d6 range (2–12)
- MUW-005: Non-monk unarmed → not using MONK_UNARMED_DICE (uses weapon default)
- MUW-006: Flurry of Blows path also uses MONK_UNARMED_DICE (not just AttackIntent)
- MUW-007: Full attack path (FullAttackIntent) also uses MONK_UNARMED_DICE
- MUW-008: Level-up() changes MONK_UNARMED_DICE correctly (L3→L4 = 1d6→1d8)

### Coverage Map Target

- `Unarmed Strike (scaling damage by level)` — PHB p.41 — **PARTIAL → IMPLEMENTED**

### PM Acceptance Notes (ML-007)

1. Name the exact file and line where the consume-site override is inserted in `attack_resolver.py`
2. Confirm Flurry of Blows path (MUW-006) uses the same dice — show how
3. MUW-008 must show `level_up()` triggers the correct dice update

---

## WO3 — Paladin Remove Disease

**Summary:** Paladin can remove disease from target once per three levels per week (PHB p.44). NOT STARTED. New `RemoveDiseaseIntent`, new `remove_disease_resolver.py` (or inline), `EF.REMOVE_DISEASE_USES` at chargen, weekly refresh on full rest.

**Engine simplification:** "per week" is modeled as "per full rest" (consistent with how all day-limited resources are modeled: spell slots, smite uses, bardic music uses). This is a HOUSE_POLICY simplification; document it.

### RAW Fidelity — PHB p.44

> "At 3rd level, a paladin can remove disease from herself or a touched creature once per week. She may use this ability more than once per week, but gains one additional use for every three additional levels she has (so she can use this ability twice per week at 6th level, three times at 9th level, and so on)."

Uses per "week" (modeled as per rest): 1 at L3, 2 at L6, 3 at L9, etc. Formula: `paladin_level // 3`.

The ability removes any disease the subject has. In the engine, this means clearing all DISEASED conditions from the target entity.

### Parallel Paths

No existing path. New resolver, new field, new intent. No parity check needed.

**Verify consume-site for `EF.REMOVE_DISEASE_USES`:**
- Write: `chargen/builder.py` (paladin L3+)
- Read: new `remove_disease_resolver.py`
- Reset: `rest_resolver.py` (add alongside the LOH pool reset pattern)

### Consumption Chain

- **Write:** `chargen/builder.py` — `EF.REMOVE_DISEASE_USES = paladin_level // 3` (paladin L3+); `EF.REMOVE_DISEASE_USED = 0`
- **Read:** `remove_disease_resolver.py` — reads `EF.REMOVE_DISEASE_USES` and `EF.REMOVE_DISEASE_USED`; checks `remaining > 0`; clears disease condition(s) from target; increments `EF.REMOVE_DISEASE_USED`
- **Effect:** `DISEASED` condition(s) removed from target entity; `remove_disease_cured` event emitted
- **Rest reset:** `rest_resolver.py` — `EF.REMOVE_DISEASE_USED = 0` (add to rest handler alongside LOH reset)

### Proof Test (RD-001 / RD-002)

- Paladin L6, target has DISEASED condition → `RemoveDiseaseIntent` → `remove_disease_cured` event, DISEASED cleared from target entity
- 3rd use at L6 (after 2 used) → `remove_disease_exhausted` event

### Gate File

`tests/test_engine_remove_disease_gate.py` — 8 tests (RD-001 through RD-008)

Tests must cover:
- RD-001: Paladin L3 has 1 use per rest
- RD-002: Paladin L6 has 2 uses per rest
- RD-003: Paladin L9 has 3 uses per rest
- RD-004: Non-paladin (or L1 paladin) → `remove_disease_invalid` event
- RD-005: Target with DISEASED condition → condition cleared after use
- RD-006: No uses remaining → `remove_disease_exhausted`
- RD-007: Uses reset to 0 on RestIntent
- RD-008: Target with no disease → event emitted, no condition change (graceful no-op)

### Coverage Map Target

- `Remove Disease (1/week per 3 levels)` — PHB p.44 — **NOT STARTED → IMPLEMENTED**

### PM Acceptance Notes (ML-007)

1. Cite builder.py line where `EF.REMOVE_DISEASE_USES` is written
2. Cite rest_resolver.py line where it is reset
3. Name all disease condition type(s) in ConditionType enum that the resolver removes
4. Confirm HOUSE_POLICY note in resolver docstring: "'per week' modeled as per full rest"

---

## WO4 — Rogue Defensive Roll

**Summary:** Rogue special ability (PHB p.51). When a blow would reduce rogue to 0 HP or below, make a Reflex save (DC = damage dealt); success = take half damage instead. 1/day. Not usable while flat-footed.

### RAW Fidelity — PHB p.51

> "The rogue can roll with a potentially lethal blow to take less damage from it than she otherwise would. Once per day, when she would be reduced to 0 or fewer hit points by damage in combat (from a weapon or other blow, not a spell or special ability), the rogue can attempt to roll with the damage. To use this ability, the rogue must attempt a Reflex saving throw (DC = damage dealt). If the save succeeds, she takes only half damage from the blow; if it fails, she takes full damage. She must be aware of the attack and able to react to it to execute her defensive roll—if she is denied her Dexterity bonus to AC, she can't use this ability."

Key constraints:
- Triggers on: weapon or physical blow (NOT spell, NOT special ability)
- Trigger condition: attack would reduce HP to 0 or below
- Reflex save DC = actual damage dealt (before the roll; this is the final damage post-DR)
- Success: take HALF the triggering damage instead
- Failure: take full damage
- 1/day
- Cannot use if flat-footed (denied DEX to AC)

### Parallel Paths

| Path | Location |
|------|----------|
| Physical attack damage application | `core/attack_resolver.py` — final damage path |
| Full attack damage application | `core/full_attack_resolver.py` — delegates to attack_resolver |

Intervention point: `attack_resolver.py` after computing `final_damage`, before returning damage events. Check if entity would be reduced to 0 HP; if `EF.HAS_DEFENSIVE_ROLL` and `EF.DEFENSIVE_ROLL_USED = False` and not flat-footed → trigger save.

**Not applicable to spell damage.** `spell_resolver.py` must NOT trigger Defensive Roll. This is by RAW: "from a weapon or other blow, not a spell or special ability."

### Consumption Chain

- **Write:** `chargen/builder.py` — `EF.HAS_DEFENSIVE_ROLL = True` when entity has the rogue special ability (treat as a flag, set by test entity construction); `EF.DEFENSIVE_ROLL_USED = False` at chargen
- **Read:** `core/attack_resolver.py` — after computing `final_damage`, check `EF.HAS_DEFENSIVE_ROLL`, `EF.DEFENSIVE_ROLL_USED`, flat-footed status; if triggered, roll Reflex save (DC = `final_damage`), halve on success
- **Effect:** damage reduced to `final_damage // 2` on save success; `EF.DEFENSIVE_ROLL_USED = True`; `defensive_roll_success` or `defensive_roll_failure` event emitted
- **Rest reset:** `rest_resolver.py` — `EF.DEFENSIVE_ROLL_USED = False` on full rest

### Proof Test (DR-001 / DR-002)

- Rogue with `HAS_DEFENSIVE_ROLL=True`, HP=10, attack deals 15 damage (would reduce to -5 HP). Reflex DC=15. Force save success → take 7 damage (15//2) → HP=3 not -5.
- Force save failure → take 15 damage → HP=-5 (entity dying)

### Gate File

`tests/test_engine_defensive_roll_gate.py` — 8 tests (DR-001 through DR-008)

Tests must cover:
- DR-001: Triggered when damage would reduce to ≤ 0 HP; save success → half damage
- DR-002: Triggered; save failure → full damage
- DR-003: Not triggered when damage would NOT reduce to ≤ 0 HP (rogue has plenty of HP)
- DR-004: Not triggered when `DEFENSIVE_ROLL_USED = True` (already used today)
- DR-005: Not triggered when entity is flat-footed
- DR-006: Not triggered for spell damage (spell_resolver path — confirm Defensive Roll does NOT fire)
- DR-007: `DEFENSIVE_ROLL_USED` resets to False on RestIntent
- DR-008: `HAS_DEFENSIVE_ROLL = False` → never triggers (non-rogue entity)

### Coverage Map Target

- `Rogue Special Abilities (each)` — PHB p.51 — Row stays NOT STARTED but add note: `Defensive Roll IMPLEMENTED. Remaining (Crippling Strike, Feat, Improved Evasion, Opportunist, Skill Mastery, Slippery Mind) NOT STARTED.`
- Alternative: add a new row for Defensive Roll explicitly if the single-row approach is too coarse.

### PM Acceptance Notes (ML-007)

1. Name the exact file:line where the Defensive Roll check is inserted in `attack_resolver.py`
2. Confirm DR-006: Show that `spell_resolver.py` does NOT hit the Defensive Roll path (by inspection, not just test)
3. Confirm save uses `save_resolver.get_save_bonus()` (not an inline save like massive damage)
4. Confirm `EF.DEFENSIVE_ROLL_USED` resets in `rest_resolver.py` — cite the line

---

## ML Preflight Checklist (Builder Self-Check)

Before filing debrief:
- [ ] ML-001: All gate tests pass; count matches (32 total: 8+8+8+8)
- [ ] ML-002: No new production code modifies existing passing tests
- [ ] ML-003: Each resolver has exactly one canonical path; no shadow implementations
- [ ] ML-004: `EF.*` constants used throughout; no bare string literals for field names
- [ ] ML-005: PHB citation in each resolver docstring (`# PHB p.NN`)
- [ ] ML-006: `sort_keys=True` on any `json.dumps`; no floats in deterministic paths; no `set()` in state
- [ ] ML-007: PM Acceptance Notes addressed in Pass 1 debrief

---

## Batch Summary

| WO | Mechanic | PHB | Type | Gates | Coverage Change |
|----|----------|-----|------|-------|-----------------|
| WO1 | Lay on Hands: SAI close + play_loop gates | p.44 | SAI + new tests | 8 | PARTIAL → IMPLEMENTED |
| WO2 | Monk Unarmed Attack Wire | p.41 Table 3-10 | consume-site | 8 | PARTIAL → IMPLEMENTED |
| WO3 | Paladin Remove Disease | p.44 | new feature | 8 | NOT STARTED → IMPLEMENTED |
| WO4 | Rogue Defensive Roll | p.51 | new feature | 8 | Defensive Roll added |
| **Total** | | | | **32** | **4 rows updated** |

**Parallel-safe:** All 4 WOs touch distinct resolvers. WO1 commits a new untracked file. WO2 modifies `attack_resolver.py`. WO3 creates a new resolver. WO4 modifies `attack_resolver.py` — **WO2 and WO4 both touch `attack_resolver.py`; execute sequentially within a single session to avoid merge conflicts.**

**DEFERRED finding promoted:** FINDING-ENGINE-MONK-UNARMED-ATTACK-WIRE-001 — DEFERRED → IN FLIGHT (WO2)

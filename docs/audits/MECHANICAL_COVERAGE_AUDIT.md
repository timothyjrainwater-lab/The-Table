# D&D 3.5e Mechanical Coverage Audit

**Audit ID:** RWO-006
**Date:** 2026-02-12
**Auditor:** Claude Opus 4.6 (automated code audit)
**Scope:** 32 core D&D 3.5e mechanics across 8 categories

---

## Summary Table

| # | Mechanic | Status | Primary File(s) | Tests | Notes |
|---|---------|--------|-----------------|-------|-------|
| **Combat Resolution** | | | | | |
| 1 | Full attack action (iterative attacks) | **Full** | `aidm/core/full_attack_resolver.py` | `tests/test_full_attack_resolution.py` | BAB +6/+1 etc. correctly computed via `calculate_iterative_attacks()` (line 58) |
| 2 | Two-weapon fighting | **Partial** | `aidm/core/feat_resolver.py:367-415` | `tests/test_feat_resolver.py:510-529` | Penalty calc and extra attacks implemented; NO integration with attack/full-attack resolver pipeline |
| 3 | Power Attack / Combat Expertise | **Partial** | `aidm/core/feat_resolver.py:131-227` | `tests/test_feat_resolver.py:305-375` | Power Attack: modifier functions exist but `power_attack_penalty` hardcoded to 0 in `attack_resolver.py:194`. Combat Expertise: **MISSING entirely** |
| 4 | Critical hit confirmation rolls | **Full** | `aidm/core/full_attack_resolver.py:85-218` | `tests/test_full_attack_resolution.py:99-182` | Threat detection, confirmation roll, natural 20 auto-hit all implemented |
| 5 | Critical hit multipliers by weapon type | **Full** | `aidm/schemas/attack.py:31-36`, `aidm/core/full_attack_resolver.py:186-188` | `tests/test_full_attack_resolution.py:597-796` | x2/x3/x4 multipliers, weapon-specific critical ranges (18-20, 19-20, 20) all working |
| **Saving Throws** | | | | | |
| 6 | Base save progression (good/poor by class) | **Full** | `aidm/schemas/leveling.py:105-106`, `aidm/core/experience_resolver.py:248-265` | `tests/test_experience_resolver.py:374-419`, `tests/test_character_sheet_ui.py:424-466` | Good/poor progressions for Fighter, Rogue, Cleric, Wizard implemented with correct tables |
| 7 | Save bonus type stacking | **Missing** | N/A | N/A | No bonus type system exists. All bonuses are untyped integers summed directly. No resistance/luck/morale/sacred/profane tracking. Violates PHB p.21 stacking rules. |
| 8 | Evasion / Improved Evasion | **Missing** | N/A | N/A | No code references. The save_resolver applies half damage on PARTIAL outcome but has no class-feature-driven Evasion check. |
| **Spell Mechanics** | | | | | |
| 9 | Spell Resistance (caster level check) | **Partial** | `aidm/core/save_resolver.py:117-181`, `aidm/schemas/saves.py:53-89` | `tests/test_save_resolution.py:292-358` | SR check (d20 + CL vs SR) fully implemented with events. BUT: no Spell Penetration feat bonus, no "SR: Yes/No" per-spell flag filtering, SR field defaults to 0 with no population mechanism. |
| 10 | Counterspelling | **Missing** | N/A | N/A | Explicitly deferred in `aidm/schemas/saves.py:17`. No schemas, no resolver logic. |
| 11 | Dispel Magic targeting | **Stub** | `aidm/schemas/spell_definitions.py:794-812` | N/A | Spell definition exists in registry with `SpellEffect.UTILITY` and "Caster level check required" citation, but the SpellResolver has zero dispel resolution logic. No caster level check vs active effects. |
| 12 | Spell components (V, S, M, F) | **Missing** | N/A | N/A | SpellDefinition has no component fields. No validation that casters can perform verbal/somatic components (e.g., silenced, bound hands). |
| **Defensive Mechanics** | | | | | |
| 13 | Damage Reduction (DR/magic, etc.) | **Stub** | `aidm/core/spell_resolver.py:798,821,855,880`, `aidm/core/truth_packets.py:600-620` | N/A | `DamageRollPayload` has a `damage_reduced` field and `create_damage_roll_stp()` computes `damage_reduced = min(dr, total_damage)`. But `dr` is hardcoded to `0` in all call sites. No DR type system (DR/magic, DR/cold iron, etc.). |
| 14 | Energy Resistance | **Missing** | N/A | N/A | `SpellDefinition` has `damage_type` enum but no energy resistance field on entities, no resistance subtraction logic. `protection_from_energy` spell exists in registry (line 814) but only applies a condition tag with no absorption tracking. |
| 15 | Concealment / miss chance | **Missing** | N/A | N/A | `aidm/schemas/geometry.py:72` and `aidm/schemas/targeting.py:12` mention concealment in comments but no miss chance roll exists anywhere in attack resolution. |
| 16 | Incorporeal miss chance (50%) | **Missing** | N/A | N/A | No incorporeal state, no 50% miss chance, no force-damage bypass logic. |
| **Special Combat** | | | | | |
| 17 | Grapple | **Partial** | `aidm/core/maneuver_resolver.py`, `aidm/schemas/maneuvers.py:156-172` | `tests/test_maneuvers_core.py:608-648` | Degraded: touch attack + opposed grapple check applies Grappled condition to target only. Missing: maintain, escape, pin, damage-while-grappled, mutual condition. |
| 18 | Bull Rush | **Full** | `aidm/core/maneuver_resolver.py`, `aidm/schemas/maneuvers.py:67-82` | `tests/test_maneuvers_core.py:268-338` | Opposed Str check with size modifiers, charge bonus, push-back, AoO from all threatening. |
| 19 | Overrun | **Full** | `aidm/core/maneuver_resolver.py`, `aidm/schemas/maneuvers.py:99-118` | `tests/test_maneuvers_core.py:413-488` | Defender avoidance, opposed check, prone on failure-by-5, charge bonus. |
| 20 | Sunder | **Partial** | `aidm/core/maneuver_resolver.py`, `aidm/schemas/maneuvers.py:121-137` | `tests/test_maneuvers_core.py:492-542` | Degraded: narrative-only damage logging. No persistent item damage, no hardness/HP tracking for objects. |
| 21 | Disarm | **Partial** | `aidm/core/maneuver_resolver.py`, `aidm/schemas/maneuvers.py:140-153` | `tests/test_maneuvers_core.py:545-604` | Degraded: opposed check works, AoO auto-fail works, but weapon "drops" is narrative only with no persistent state change. |
| 22 | Trip | **Full** | `aidm/core/maneuver_resolver.py`, `aidm/schemas/maneuvers.py:84-97` | `tests/test_maneuvers_core.py:341-409` | Touch attack, opposed Str/Dex check, Prone condition on success, counter-trip on failure, size modifiers. |
| **Class Features** | | | | | |
| 23 | Turn Undead | **Missing** | N/A | N/A | No code exists. |
| 24 | Bardic Music | **Missing** | N/A | N/A | No code exists. |
| 25 | Rage (Barbarian) | **Missing** | N/A | N/A | No code exists. Barbarian is listed in `character_sheet.py:34` class progressions but has no rage mechanics. |
| 26 | Sneak Attack (precision damage) | **Missing** | N/A | N/A | Only mentioned in `conditions.py:269` flavor text for Helpless. No precision damage dice, no flanking check, no denied-Dex-to-AC detection. |
| 27 | Wild Shape | **Missing** | N/A | N/A | No code exists. |
| **Action Economy** | | | | | |
| 28 | Swift actions | **Missing** | N/A | N/A | `TurnContext.action_type` at `play_loop.py:627` supports `"move"`, `"standard"`, `"move_and_standard"`, `"full"` only. No swift action type. |
| 29 | Immediate actions | **Missing** | N/A | N/A | No immediate action concept in the codebase. |
| 30 | Readied actions | **Missing** | N/A | N/A | Mentioned in `aoo.py:13` as explicitly deferred. No schemas or resolution. |
| 31 | Delayed actions | **Missing** | N/A | N/A | No code exists. Initiative order is static per round. |
| 32 | 5-foot step rules | **Partial** | `aidm/core/terrain_resolver.py:155-170` | N/A | `can_5_foot_step()` checks terrain movement cost (< 4). BUT: no enforcement that 5-foot step prevents other movement, no integration with action economy, no AoO immunity for 5-foot steps. |

---

## RAW Coverage Score

| Status | Count | Mechanics |
|--------|-------|-----------|
| **Full** | 7 | #1, #4, #5, #6, #18, #19, #22 |
| **Partial** | 8 | #2, #3, #9, #17, #20, #21, #32, (+ prior recon: flat-footed FULL, touch attacks PARTIAL) |
| **Stub** | 2 | #11, #13 |
| **Missing** | 15 | #7, #8, #10, #12, #14, #15, #16, #23, #24, #25, #26, #27, #28, #29, #30, #31 |

**Overall: 7 Full / 8 Partial / 2 Stub / 15 Missing out of 32 mechanics (21.9% Full, 46.9% Missing)**

---

## Detailed Findings

### 1. Full Attack Action (Iterative Attacks) -- FULL

**File:** `aidm/core/full_attack_resolver.py`
**Tests:** `tests/test_full_attack_resolution.py`

`calculate_iterative_attacks()` (line 58-82) correctly implements the PHB p.143 iterative attack rules:
- First attack at full BAB
- Subsequent attacks at -5 increments
- Stops when bonus drops below +1
- BAB 6 yields [+6, +1], BAB 11 yields [+11, +6, +1], BAB 16 yields [+16, +11, +6, +1]

Tests at lines 78, 160-172 verify BAB 1/5/6/11/16 edge cases. Integrated into play_loop via `FullAttackIntent` routing (play_loop.py:1040-1073).

**RAW gaps:** None for core iterative attack math. However, the full attack does NOT integrate condition modifiers (attack_resolver does, but full_attack_resolver bypasses it, using raw AC from entity directly at line 261). This is a consistency bug.

### 2. Two-Weapon Fighting -- PARTIAL

**File:** `aidm/core/feat_resolver.py:367-415`
**Tests:** `tests/test_feat_resolver.py:510-529`

The TWF feat chain is fully defined in the feat registry (`aidm/schemas/feats.py:216-251`) with correct prerequisites:
- TWF: DEX 15, reduces penalties to -2/-2
- Improved TWF: DEX 17, BAB +6, grants second off-hand attack
- Greater TWF: DEX 19, BAB +11, grants third off-hand attack

Functions `get_twf_penalties()` and `get_twf_extra_attacks()` correctly compute modifiers per PHB p.160.

**What's missing:**
- No TWF-aware attack sequence generation. `calculate_iterative_attacks()` only handles primary-hand iteratives. There is no function that combines main-hand iteratives + off-hand attacks.
- The `attack_resolver.py:193` sets `is_twf: False` hardcoded.
- No off-hand weapon tracking in entity state (no dual-weapon data model).
- No light weapon detection for penalty reduction.

### 3. Power Attack / Combat Expertise -- PARTIAL (Power Attack) / MISSING (Combat Expertise)

**Power Attack File:** `aidm/core/feat_resolver.py:131-227`
**Tests:** `tests/test_feat_resolver.py:305-375`

Power Attack modifier computation is correct:
- Attack penalty applied via `get_attack_modifier()` (line 173-174)
- Damage bonus 1:1 one-handed, 1:2 two-handed via `get_damage_modifier()` (line 219-225)
- PHB p.98 citation present

**What's broken:**
- `attack_resolver.py:194` hardcodes `power_attack_penalty: 0` in feat_context. The player has no way to specify a Power Attack value.
- `attack_resolver.py:192` hardcodes `is_ranged: False` -- no detection of ranged vs melee.
- `attack_resolver.py:268` hardcodes `is_two_handed: False` -- the 1:2 two-handed ratio is never triggered.

**Combat Expertise:** Completely missing. Not in `FeatID`, not in `FEAT_REGISTRY`, no modifier function. This is a core PHB feat (p.92) that trades attack bonus for AC and is a prerequisite for Improved Trip, Improved Disarm, Improved Feint, and Whirlwind Attack.

### 4. Critical Hit Confirmation Rolls -- FULL

**File:** `aidm/core/full_attack_resolver.py:85-218`
**Tests:** `tests/test_full_attack_resolution.py:99-182`

Correctly implements PHB p.140:
- Threat detected when d20 >= `weapon.critical_range` (line 128)
- Confirmation roll: d20 + attack_bonus vs target AC (line 145-149)
- No auto-hit on confirmation (natural 20 on confirmation is not special per RAW)
- Confirmation result stored in event payload

**Note:** Critical confirmation is only in `full_attack_resolver.py`. The single `attack_resolver.py` does NOT have critical hit logic at all -- it only checks natural 20 for auto-hit, not for critical threat. This means single standard attacks cannot score critical hits, which is a RAW violation.

### 5. Critical Hit Multipliers by Weapon Type -- FULL

**File:** `aidm/schemas/attack.py:31-36`, `aidm/core/full_attack_resolver.py:186-188`
**Tests:** `tests/test_full_attack_resolution.py:597-796`

- `Weapon.critical_multiplier` accepts 2, 3, or 4 (validated at line 54)
- `Weapon.critical_range` accepts 1-20, default 20 (validated at line 59)
- Damage multiplication: `base_damage * weapon.critical_multiplier` (line 188)
- Tests verify x2, x3, x4 multipliers and 18-20, 19-20, 20-only threat ranges

**RAW gap:** Critical damage per RAW should roll extra dice (not multiply total). PHB p.140: "multiply the damage by the critical multiplier" is often interpreted as rolling extra dice sets. The current implementation multiplies the single damage roll total, which gives slightly different statistical distributions but is a common simplification.

### 6. Base Save Progression -- FULL

**File:** `aidm/schemas/leveling.py:105-106`
**Tests:** `tests/test_experience_resolver.py:374-419`, `tests/test_character_sheet_ui.py:424-466`

Correct tables:
- Good: `[2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12]`
- Poor: `[0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6]`

Class progressions defined for Fighter, Rogue, Cleric, Wizard (leveling.py:65-90) and all 11 PHB classes + NPC classes (character_sheet.py:32-50). Applied during level-up at `experience_resolver.py:258-264`.

### 7. Save Bonus Type Stacking -- MISSING

No bonus type system exists anywhere in the codebase. The `save_resolver.py:112` computes:
```python
total_bonus = base_save + ability_mod + condition_save_mod
```

All values are raw integers. There is no tracking of bonus types (resistance, luck, morale, sacred, profane, insight, enhancement, etc.). Per PHB p.21, bonuses of the same type do not stack (highest applies only), except dodge bonuses and circumstance bonuses which do stack. This is a fundamental RAW violation that affects save balance at mid-to-high levels.

The `resistance` spell in `spell_definitions.py:465` applies a condition tag `"resistance"` but this is a string flag, not a typed bonus that interacts with the save resolution pipeline.

### 8. Evasion / Improved Evasion -- MISSING

Zero code references to "evasion" or "improved_evasion" anywhere in the codebase. The `spell_resolver.py` `SaveEffect.HALF` enum and the `save_resolver.py` `SaveOutcome.PARTIAL` provide the framework for half-damage-on-save, but there is no class-feature-driven mechanism to grant Evasion (zero damage on successful Reflex save) or Improved Evasion (half damage on failed Reflex save).

### 9. Spell Resistance -- PARTIAL

**File:** `aidm/core/save_resolver.py:117-181`
**Tests:** `tests/test_save_resolution.py:292-358`

The SR check mechanic is correctly implemented:
- d20 + caster_level vs target SR value
- SR field exists on entities (`EF.SR` at entity_fields.py:84)
- Events emitted with `spell_resistance_checked` type
- Integration with save pipeline (SR checked before save roll)

**What's missing:**
- No Spell Penetration feat (+2 CL for SR checks)
- No Greater Spell Penetration (+4 CL for SR checks)
- No per-spell "SR: Yes/No" flag (all spells with saves check SR if target has it)
- SR value on entities defaults to 0 and has no population mechanism from monster stat blocks
- The `spell_resolver.py` has a `TargetStats.spell_resistance` field but the `_create_target_stats()` helper in `play_loop.py:233` reads it from `entity.get(EF.SR, 0)` which is never set to non-zero by any game mechanic

### 10. Counterspelling -- MISSING

Explicitly deferred at `aidm/schemas/saves.py:17`: "Out of scope (deferred to CP-18+): Counterspelling". No schemas, no resolver, no intent type, no tests.

### 11. Dispel Magic Targeting -- STUB

**File:** `aidm/schemas/spell_definitions.py:794-812`

A `SpellDefinition` entry exists for Dispel Magic:
```python
"dispel_magic": SpellDefinition(
    spell_id="dispel_magic",
    name="Dispel Magic",
    level=3,
    school="abjuration",
    target_type=SpellTarget.SINGLE,
    effect_type=SpellEffect.UTILITY,
    ...
    conditions_on_success=(),  # "Caster level check required"
)
```

However, the `SpellResolver.resolve_spell()` has no dispel-specific logic. It would process this as a UTILITY spell with no damage, no conditions, and no save -- effectively a no-op. The caster level check against each active effect on the target (PHB p.223: d20 + CL vs 11 + caster level of each effect) is completely unimplemented.

### 12. Spell Components (V, S, M, F) -- MISSING

`SpellDefinition` (spell_resolver.py:90-189) has no fields for components. There is no validation that:
- Silenced casters cannot cast spells with verbal components
- Bound/paralyzed casters cannot cast spells with somatic components
- Material components are available
- Focus items are held

The `silenced` condition exists in spell_definitions.py:788 as a condition tag, but no spell resolution checks for it.

### 13. Damage Reduction -- STUB

**File:** `aidm/core/truth_packets.py:600-620`

The STP system has `DamageRollPayload.damage_reduced` (truth_packets.py:111) and `create_damage_roll_stp()` correctly computes `damage_reduced = min(dr, total_damage)` (line 610). This proves the data model supports DR.

However, all call sites pass `dr=0`:
- `spell_resolver.py:798`: `dr=0`
- `spell_resolver.py:821`: `dr=0,  # DR not implemented yet`
- `spell_resolver.py:855`: `dr=0`
- `spell_resolver.py:880`: `dr=0`

No DR field exists on entities (`EF` has no `DR` constant). No DR type system (DR/magic, DR/cold iron, DR/silver, DR/adamantine, DR/epic, DR/-- [overcome by nothing]). The `full_attack_resolver.py:18` explicitly states "No DR/resistance/conditions" in scope comments.

### 14. Energy Resistance -- MISSING

`SpellDefinition.damage_type` tracks `DamageType` enum (fire, cold, acid, electricity, sonic, force, positive, negative, untyped) but there is no `energy_resistance` field on entities and no subtraction logic during damage resolution.

`protection_from_energy` exists in the spell registry (spell_definitions.py:814-831) and applies a condition tag, but there is no absorption tracking (the spell should absorb up to 12/level, max 120 points of that energy type).

### 15. Concealment / Miss Chance -- MISSING

`aidm/schemas/geometry.py:72` mentions "concealment system" in a comment. `aidm/schemas/targeting.py:12` lists "Concealment percentages / miss chance" as a targeting contract item. But no miss chance roll exists in `attack_resolver.py` or `full_attack_resolver.py`. There is no concealment field on entities, no 20%/50% miss chance roll, and no total concealment targeting prevention.

### 16. Incorporeal Miss Chance -- MISSING

No incorporeal state, no 50% miss chance for non-force/non-ghost-touch attacks, no damage halving for non-magical weapons. This is closely related to #15 (concealment) but has additional rules about only taking damage from force effects, magical weapons (50% miss), and ghost touch weapons (full damage).

### 17. Grapple -- PARTIAL (Degraded)

**File:** `aidm/core/maneuver_resolver.py`, `aidm/schemas/maneuvers.py:156-172`
**Tests:** `tests/test_maneuvers_core.py:608-648`

Implemented:
- Melee touch attack to initiate (via `TouchAttackResult` at maneuvers.py:275)
- Opposed grapple check with size modifiers
- AoO from target; if AoO deals damage, grapple auto-fails
- Grappled condition applied to target on success

Missing (explicitly degraded per `maneuvers.py:15-16`):
- **Unidirectional only:** Attacker does not gain Grappled condition (RAW: both are grappled)
- **No maintain check:** Grapple is resolved in one action, no ongoing grapple state machine
- **No escape mechanism:** Grappled defender cannot attempt escape (Escape Artist or opposed grapple check)
- **No pin:** No pinning sub-state (PHB p.156)
- **No damage while grappled:** No grapple damage action (PHB p.156)
- **No spellcasting in grapple restrictions**

### 18. Bull Rush -- FULL

**File:** `aidm/core/maneuver_resolver.py`, `aidm/schemas/maneuvers.py:67-82`
**Tests:** `tests/test_maneuvers_core.py:268-338`

Correctly implements PHB p.154-155:
- Opposed Strength check with size modifiers from `SIZE_MODIFIER_SCALE`
- Charge bonus (+2) when `is_charge=True`
- Push distance = 5 ft + 5 ft per 5 points of margin
- Provokes AoO from ALL threatening enemies (including target)
- Position changes recorded in `ManeuverResult.position_change`
- Stability bonus for dwarves/quadrupeds (tested at test_maneuvers_core.py:725-753)

### 19. Overrun -- FULL

**File:** `aidm/core/maneuver_resolver.py`, `aidm/schemas/maneuvers.py:99-118`
**Tests:** `tests/test_maneuvers_core.py:413-488`

Correctly implements PHB p.157-158:
- Defender may choose to avoid (controlled by `defender_avoids` flag in intent)
- Opposed Str vs Dex/Str check with size modifiers
- Success knocks defender prone
- Failure by 5+ knocks attacker prone
- Provokes AoO from target when entering their space

### 20. Sunder -- PARTIAL (Degraded)

**File:** `aidm/core/maneuver_resolver.py`, `aidm/schemas/maneuvers.py:121-137`
**Tests:** `tests/test_maneuvers_core.py:492-542`

Implemented: opposed attack roll, damage computation, AoO from target, event logging.

Missing (explicitly degraded per `maneuvers.py:13`):
- **Narrative only:** Damage is logged but does not reduce item HP
- **No item HP/hardness system:** No object stat blocks, no hardness subtraction
- **No persistent weapon/armor degradation**
- **No broken weapon condition**

### 21. Disarm -- PARTIAL (Degraded)

**File:** `aidm/core/maneuver_resolver.py`, `aidm/schemas/maneuvers.py:140-153`
**Tests:** `tests/test_maneuvers_core.py:545-604`

Implemented: opposed attack roll with size modifiers, AoO from target, auto-fail if AoO deals damage.

Missing (explicitly degraded per `maneuvers.py:14`):
- **No persistent state change:** Weapon "drops" narratively but entity retains weapon in state
- **No weapon pickup action**
- **No unarmed disarm variant**

### 22. Trip -- FULL

**File:** `aidm/core/maneuver_resolver.py`, `aidm/schemas/maneuvers.py:84-97`
**Tests:** `tests/test_maneuvers_core.py:341-409`

Correctly implements PHB p.158-160:
- Melee touch attack required (line 344 in tests)
- Opposed Str/Dex check with size modifiers
- Success applies Prone condition via CP-16 pipeline
- Failure triggers counter-trip attempt by defender
- AoO from target (unarmed attack)
- Size modifier scale correctly applied

### 23. Turn Undead -- MISSING

No code exists for Turn Undead. No turning check, no turning damage, no turn/rebuke tracking, no uses-per-day. Cleric class progression exists (leveling.py:78) but has no class feature implementation.

### 24. Bardic Music -- MISSING

No code exists. Bard class progression exists (character_sheet.py:39) but has no bardic music types (inspire courage, fascinate, etc.), no uses-per-day, no area-of-effect morale bonuses.

### 25. Rage (Barbarian) -- MISSING

No code exists for Rage. Barbarian listed in `character_sheet.py:34` class progressions with correct BAB/saves but no Rage mechanics: no +4 Str/+4 Con/-2 AC, no temporary HP from Con increase, no rounds-per-day tracking, no fatigue after rage ends.

### 26. Sneak Attack -- MISSING

Only mentioned in flavor text: `conditions.py:269` says "Rogues can sneak attack helpless targets." No precision damage dice, no flanking detection (flanking itself is not implemented), no denied-Dex-to-AC check for sneak attack eligibility, no immunity for creatures without discernible anatomies.

### 27. Wild Shape -- MISSING

No code exists. Druid class progression exists (character_sheet.py:41) but has no Wild Shape: no form selection, no physical stat replacement, no natural attacks, no size change, no uses-per-day.

### 28. Swift Actions -- MISSING

`TurnContext.action_type` (play_loop.py:627) is typed as:
```python
Literal["move", "standard", "move_and_standard", "full"]
```

No `"swift"` action type. No swift action resolution. This affects many spells and class features that use swift actions (e.g., Quickened spells, many Book of Exalted Deeds / Complete Warrior abilities).

### 29. Immediate Actions -- MISSING

No immediate action concept exists. Immediate actions (3.5e addition, PHB errata) allow reactions outside your turn and consume your next swift action. No schema, no resolution, no integration.

### 30. Readied Actions -- MISSING

Explicitly deferred at `aoo.py:13`: "No 5-foot step immunity, withdraw action, readied actions (deferred to CP-16+)". No ready action intent, no trigger specification, no interrupt resolution.

### 31. Delayed Actions -- MISSING

No delay action concept. Initiative order is set at combat start (`combat_controller.py:172`) and remains static throughout combat. There is no mechanism for an actor to change their initiative position by delaying.

### 32. 5-Foot Step Rules -- PARTIAL

**File:** `aidm/core/terrain_resolver.py:155-170`

`can_5_foot_step()` checks terrain movement cost (cannot 5-foot step if movement_cost >= 4). Referenced in stp_emitter.py:217 as a valid movement type.

**What's missing:**
- No enforcement that taking a 5-foot step prevents other movement that round
- No AoO immunity for 5-foot steps (the `aoo.py` treats all movement through `StepMoveIntent` as potentially provoking)
- No integration with action economy (5-foot step should not count as a move action)
- No restriction to standard action + 5-foot step (cannot 5-foot step if you've taken a move action)

---

## Previously Identified Gaps (Confirmed)

These gaps from prior recon are confirmed by this audit:

| Gap | Status | Confirmation |
|-----|--------|-------------|
| Spell Resistance: STUB | **Confirmed as Partial** -- SR check logic exists and works, but lacks feat integration and per-spell SR flags |
| Damage Reduction: STUB | **Confirmed** -- `dr=0` hardcoded at all 4 call sites in spell_resolver.py |
| Concealment/miss chance: MISSING | **Confirmed** -- no miss chance roll in any attack resolver |
| Touch attacks for spells: PARTIAL | **Confirmed** -- `SpellTarget.TOUCH` and `SpellTarget.RAY` exist in spell_resolver.py but touch AC is not computed separately from full AC |
| Flat-footed: FULLY IMPLEMENTED | **Confirmed** -- combat_controller.py tracks flat_footed_actors, clears on first action |
| AoO: movement only | **Confirmed** -- `aoo.py:253` has TODO for ranged attack and spellcasting provocation |
| Weapon range: stubbed max_range=100 | **Confirmed** -- attack_resolver.py:130 hardcodes `max_range=100` |
| Temporary modifiers: return 0 | **Confirmed** -- permanent_stats.py:279 `temp_total = 0  # TODO: Integrate with CP-16` |
| Full AC/HP recompute: stubbed | **Confirmed** -- permanent_stats.py:327 `# TODO: Full AC recalculation when AC system available` |

---

## Recommended Priority Order for Gap Closure

Priority is based on: (A) frequency of occurrence in actual gameplay, (B) impact on combat balance, (C) dependency graph (what enables other mechanics).

### Tier 1: Critical Path (blocks core gameplay)

1. **#13 Damage Reduction** -- Affects every monster encounter from CR 5+. Without DR, all damage bypasses defenses that many monsters rely on. Implementation effort: Medium (add DR field to entities, type system for bypass conditions, integrate into attack/spell resolvers).

2. **#15 Concealment / Miss Chance** -- Affects fog, darkness, invisibility, blur, displacement. Core defensive mechanic. Implementation effort: Medium (miss chance roll after hit determination, concealment field on conditions/terrain).

3. **#3 Power Attack integration** -- Feat exists but is non-functional due to hardcoded `power_attack_penalty: 0`. Most common combat feat for martial characters. Implementation effort: Low (pass player's chosen penalty through intent).

4. **#26 Sneak Attack** -- Rogue's primary damage mechanic. Without it, Rogues are severely underpowered. Requires flanking detection as prerequisite. Implementation effort: Medium-High.

5. **#32 5-foot step completion** -- Most used tactical option in combat. Needs AoO immunity and action economy integration. Implementation effort: Low-Medium.

### Tier 2: High Priority (significant gameplay impact)

6. **#14 Energy Resistance** -- Affects dragon encounters, elemental creatures, and several common spells. Implementation effort: Medium.

7. **#7 Save bonus type stacking** -- Without this, stacking multiple +1 resistance items/spells gives unrealistic save bonuses. Matters most at level 5+. Implementation effort: Medium (requires bonus type tracking system).

8. **#25 Rage** -- Barbarian's defining feature. Without it, the class is a Fighter with fewer feats. Implementation effort: Low-Medium (temporary stat changes + fatigue).

9. **#8 Evasion / Improved Evasion** -- Rogue/Monk signature defense. Matters for every AoE spell encounter. Implementation effort: Low (add class feature check in save resolution path).

10. **#2 TWF integration** -- Attack sequence generation for off-hand attacks. Needed for any dual-wielding character. Implementation effort: Medium (modify full_attack_resolver to accept off-hand weapon + TWF extra attacks).

### Tier 3: Important (fills noticeable gaps)

11. **#3 Combat Expertise** -- Prerequisite for Improved Trip/Disarm/Feint. Implementation effort: Low.
12. **#12 Spell components** -- Blocks meaningful interaction between silence effects and spellcasting. Implementation effort: Low-Medium.
13. **#17 Grapple completion** -- Current unidirectional grapple is a major simplification. Implementation effort: High.
14. **#28-29 Swift/Immediate actions** -- Needed for many class features and spells from supplement books. Implementation effort: Medium.
15. **#30-31 Readied/Delayed actions** -- Tactical depth for prepared characters. Implementation effort: Medium-High.

### Tier 4: Nice to Have (lower frequency)

16. **#23 Turn Undead** -- Only relevant in undead encounters. Implementation effort: Medium.
17. **#24 Bardic Music** -- Party-wide buffs, important for Bard viability. Implementation effort: Medium.
18. **#27 Wild Shape** -- Core Druid feature, very complex. Implementation effort: Very High.
19. **#10 Counterspelling** -- Rarely used in actual play. Implementation effort: Medium.
20. **#11 Dispel Magic** -- Important utility but can be partially handled narratively. Implementation effort: Medium.
21. **#16 Incorporeal** -- Niche mechanic (ghosts, wraiths). Implementation effort: Low-Medium.
22. **#20-21 Sunder/Disarm completion** -- Current degraded versions are functional for most play. Implementation effort: Medium.

---

## Notable Architectural Observations

1. **Single vs Full attack resolver inconsistency:** `attack_resolver.py` has condition modifiers, cover, terrain, mounted bonuses, and feat integration. `full_attack_resolver.py` bypasses all of these, using raw entity AC directly. This means full attacks ignore Prone AC penalties, cover bonuses, mounted higher ground, and feat modifiers. This should be unified.

2. **Critical hits only in full attack:** `attack_resolver.py` has no critical hit logic. Only `full_attack_resolver.py:resolve_single_attack_with_critical()` handles criticals. Standard attacks (single attack action) cannot score critical hits. This is a significant RAW violation.

3. **Event-driven architecture is well-suited for additions:** The immutable WorldState + Event pattern makes it straightforward to add DR (subtract in damage resolution), concealment (add miss chance event), and energy resistance (subtract in spell damage resolution) without refactoring the core pipeline.

4. **Feat system is well-designed but disconnected:** `feat_resolver.py` correctly computes modifiers but `attack_resolver.py` hardcodes all context values (weapon_name="unknown", power_attack_penalty=0, is_ranged=False, is_two_handed=False). The wiring layer needs work.

---

*End of Mechanical Coverage Audit RWO-006*

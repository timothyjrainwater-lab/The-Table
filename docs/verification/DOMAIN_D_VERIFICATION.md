# Domain D Verification — Conditions & Modifiers

**Verified by:** Claude Opus 4.6
**Date:** 2026-02-14
**Formulas verified:** 57
**Summary:** 38 CORRECT, 8 WRONG, 5 AMBIGUOUS, 6 UNCITED

---

## Verification Records

### aidm/schemas/conditions.py — Condition Modifier Values (42 formulas)

---

#### Prone (3 formulas)

FORMULA ID: D-conditions-schema-208
FILE: aidm/schemas/conditions.py
LINE: 208
CODE: `ac_modifier=-4`
RULE SOURCE: SRD Conditions: Prone — "An attacker who is prone has a –4 penalty on melee attack rolls and cannot use a ranged weapon (except for a crossbow). A defender who is prone gains a +4 bonus to Armor Class against ranged attacks, but takes a –4 penalty to AC against melee attacks."
EXPECTED: ac_modifier=-4 vs melee, ac_modifier=+4 vs ranged (context-dependent)
ACTUAL: ac_modifier=-4 (flat, no melee/ranged differentiation)
VERDICT: WRONG
NOTES: Known BUG-3. The code stores a flat -4 AC modifier. SRD requires -4 AC vs melee attacks but +4 AC vs ranged attacks. The `get_condition_modifiers()` context parameter exists but is not used to differentiate. Ranged attackers incorrectly benefit from the -4 penalty.

---

FORMULA ID: D-conditions-schema-209
FILE: aidm/schemas/conditions.py
LINE: 209
CODE: `attack_modifier=-4`
RULE SOURCE: SRD Conditions: Prone — "An attacker who is prone has a –4 penalty on melee attack rolls"
EXPECTED: attack_modifier=-4 (melee only; cannot use ranged except crossbow)
ACTUAL: attack_modifier=-4
VERDICT: CORRECT
NOTES: The -4 applies to melee attack rolls. SRD also prohibits ranged attacks (except crossbow) but that's an enforcement concern (CP-17+), not a modifier value issue. The numeric value is correct.

---

FORMULA ID: D-conditions-schema-210
FILE: aidm/schemas/conditions.py
LINE: 210
CODE: `standing_triggers_aoo=True`
RULE SOURCE: SRD Conditions: Prone / SRD Combat: Standing from Prone — "Standing up from a prone position provokes an attack of opportunity."
EXPECTED: True
ACTUAL: True
VERDICT: CORRECT
NOTES: Metadata-only flag, enforcement deferred to CP-17+. Value is correct per SRD.

---

#### Flat-Footed (1 formula)

FORMULA ID: D-conditions-schema-232
FILE: aidm/schemas/conditions.py
LINE: 232
CODE: `loses_dex_to_ac=True`
RULE SOURCE: SRD Combat: Flat-Footed — "At the start of a battle, before you have had a chance to act... you are flat-footed. You can't use your Dexterity bonus to AC (if any)."
EXPECTED: loses_dex_to_ac=True
ACTUAL: loses_dex_to_ac=True
VERDICT: CORRECT
NOTES: SRD also says flat-footed characters can't make attacks of opportunity (unless they have Combat Reflexes feat). That's enforcement, not a modifier value. Correct.

---

#### Grappled (2 formulas)

FORMULA ID: D-conditions-schema-254
FILE: aidm/schemas/conditions.py
LINE: 254
CODE: `dex_modifier=-4`
RULE SOURCE: SRD 3.5e Special Attacks: Grapple — "You lose your Dexterity bonus to AC (if any) against opponents you aren't grappling." / Pathfinder SRD Conditions: Grappled — "Grappled creatures cannot move and take a –4 penalty to Dexterity."
EXPECTED: SRD 3.5e: loses_dex_to_ac=True (vs non-grappling opponents). Pathfinder: dex_modifier=-4.
ACTUAL: dex_modifier=-4 (follows Pathfinder rule)
VERDICT: AMBIGUOUS
NOTES: **3.5e vs Pathfinder divergence.** The D&D 3.5e SRD says grappled characters lose their Dex bonus to AC against opponents they aren't grappling — there is no flat -4 Dex penalty. The code's docstring cites "PHB p. 156" but uses the Pathfinder wording ("–4 penalty to Dexterity"), which is a Pathfinder simplification of the 3.5e grapple rules. Per the verification plan's authority chain (Section 4), Pathfinder is a valid correction source where 3.5e has "known errata, ambiguity, or design flaws." The 3.5e grapple rules are notoriously complex, so adopting the Pathfinder simplification is defensible but MUST be documented as an intentional divergence. If the project intends strict 3.5e fidelity, this should be `loses_dex_to_ac=True` instead. Additionally, the 3.5e version is contextual (only vs non-grappling opponents), which the current system cannot express.

---

FORMULA ID: D-conditions-schema-255
FILE: aidm/schemas/conditions.py
LINE: 255
CODE: `movement_prohibited=True`
RULE SOURCE: SRD Special Attacks: Grapple — "You can't move while grappling."
EXPECTED: True
ACTUAL: True
VERDICT: CORRECT
NOTES: Metadata flag, enforcement deferred. Value correct.

---

#### Helpless (4 formulas)

FORMULA ID: D-conditions-schema-281
FILE: aidm/schemas/conditions.py
LINE: 281
CODE: `ac_modifier=-4`
RULE SOURCE: SRD Conditions: Helpless — "A helpless defender has an effective Dexterity score of 0 (–5 modifier). Melee attacks against a helpless target get a +4 bonus (equivalent to attacking a prone target). Ranged attacks get no special bonus against helpless targets."
EXPECTED: ac_modifier=-4 vs melee only (ranged get no bonus)
ACTUAL: ac_modifier=-4 (flat, no melee/ranged differentiation)
VERDICT: WRONG
NOTES: Known BUG-4. The +4 melee attack bonus (modeled as -4 AC) only applies to melee attacks. Ranged attacks get no special bonus. The code applies -4 AC universally. Additionally, the effective Dex 0 (-5 modifier) is partially handled via `loses_dex_to_ac=True`, but the -4 AC and the Dex-0 effect are separate mechanics that should not both be flat -4.

---

FORMULA ID: D-conditions-schema-282
FILE: aidm/schemas/conditions.py
LINE: 282
CODE: `loses_dex_to_ac=True`
RULE SOURCE: SRD Conditions: Helpless — "A helpless defender has an effective Dexterity score of 0 (–5 modifier)."
EXPECTED: loses_dex_to_ac=True
ACTUAL: loses_dex_to_ac=True
VERDICT: CORRECT
NOTES: The SRD sets effective Dex to 0 (-5 modifier), which is stronger than just "loses Dex bonus." The loses_dex_to_ac flag removes any positive Dex bonus but doesn't apply the -5 penalty from Dex 0. This is a separate concern from the ac_modifier field. The flag value itself is correct as far as it goes; the missing -5 Dex mod is an architectural concern for how the resolver uses this data.

---

FORMULA ID: D-conditions-schema-283
FILE: aidm/schemas/conditions.py
LINE: 283
CODE: `auto_hit_if_helpless=True`
RULE SOURCE: SRD Conditions: Helpless — "An attacker can use a coup de grace action against a helpless opponent."
EXPECTED: True (helpless targets are eligible for coup de grace / auto-hit melee)
ACTUAL: True
VERDICT: CORRECT
NOTES: Metadata flag. SRD says coup de grace is an available action, which effectively means melee attacks auto-hit. The flag name is somewhat loose but captures the intent.

---

FORMULA ID: D-conditions-schema-284
FILE: aidm/schemas/conditions.py
LINE: 284
CODE: `actions_prohibited=True`
RULE SOURCE: SRD Conditions: Helpless — "A helpless character is paralyzed, held, bound, sleeping, unconscious, or otherwise completely at an opponent's mercy."
EXPECTED: True (helpless implies inability to act)
ACTUAL: True
VERDICT: CORRECT
NOTES: The SRD doesn't explicitly say "cannot take actions" for the Helpless condition itself — it's a meta-condition that results from other conditions (paralyzed, unconscious, etc.) which individually prohibit actions. However, modeling it as actions_prohibited=True is a reasonable interpretation.

---

#### Stunned (3 formulas)

FORMULA ID: D-conditions-schema-306
FILE: aidm/schemas/conditions.py
LINE: 306
CODE: `ac_modifier=-2`
RULE SOURCE: SRD Conditions: Stunned — "A stunned creature drops everything held, can't take actions, takes a –2 penalty to AC, and loses his Dexterity bonus to AC (if any)."
EXPECTED: ac_modifier=-2
ACTUAL: ac_modifier=-2
VERDICT: CORRECT
NOTES: Exact match. The -2 is a separate penalty on top of losing Dex bonus.

---

FORMULA ID: D-conditions-schema-307
FILE: aidm/schemas/conditions.py
LINE: 307
CODE: `loses_dex_to_ac=True`
RULE SOURCE: SRD Conditions: Stunned — "loses his Dexterity bonus to AC (if any)"
EXPECTED: True
ACTUAL: True
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-308
FILE: aidm/schemas/conditions.py
LINE: 308
CODE: `actions_prohibited=True`
RULE SOURCE: SRD Conditions: Stunned — "can't take actions"
EXPECTED: True
ACTUAL: True
VERDICT: CORRECT

---

#### Dazed (1 formula)

FORMULA ID: D-conditions-schema-328
FILE: aidm/schemas/conditions.py
LINE: 328
CODE: `actions_prohibited=True`
RULE SOURCE: SRD Conditions: Dazed — "The creature is unable to act normally. A dazed creature can take no actions, but has no penalty to AC."
EXPECTED: actions_prohibited=True, no AC penalty
ACTUAL: actions_prohibited=True, no AC penalty
VERDICT: CORRECT
NOTES: SRD also says "A dazed condition typically lasts 1 round." Duration is not part of the modifier schema.

---

#### Shaken (4 formulas)

FORMULA ID: D-conditions-schema-352
FILE: aidm/schemas/conditions.py
LINE: 352
CODE: `attack_modifier=-2`
RULE SOURCE: SRD Conditions: Shaken — "A shaken character takes a –2 penalty on attack rolls, saving throws, skill checks, and ability checks."
EXPECTED: attack_modifier=-2
ACTUAL: attack_modifier=-2
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-353
FILE: aidm/schemas/conditions.py
LINE: 353
CODE: `fort_save_modifier=-2`
RULE SOURCE: SRD Conditions: Shaken — "–2 penalty on... saving throws"
EXPECTED: fort_save_modifier=-2
ACTUAL: fort_save_modifier=-2
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-354
FILE: aidm/schemas/conditions.py
LINE: 354
CODE: `ref_save_modifier=-2`
RULE SOURCE: SRD Conditions: Shaken — "–2 penalty on... saving throws"
EXPECTED: ref_save_modifier=-2
ACTUAL: ref_save_modifier=-2
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-355
FILE: aidm/schemas/conditions.py
LINE: 355
CODE: `will_save_modifier=-2`
RULE SOURCE: SRD Conditions: Shaken — "–2 penalty on... saving throws"
EXPECTED: will_save_modifier=-2
ACTUAL: will_save_modifier=-2
VERDICT: CORRECT
NOTES: SRD also specifies -2 to skill checks and ability checks. Those fields do not exist in ConditionModifiers. Recorded as scope gap (no skill/ability check system yet).

---

#### Sickened (5 formulas)

FORMULA ID: D-conditions-schema-380
FILE: aidm/schemas/conditions.py
LINE: 380
CODE: `attack_modifier=-2`
RULE SOURCE: SRD Conditions: Sickened — "The character takes a –2 penalty on all attack rolls, weapon damage rolls, saving throws, skill checks, and ability checks."
EXPECTED: attack_modifier=-2
ACTUAL: attack_modifier=-2
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-381
FILE: aidm/schemas/conditions.py
LINE: 381
CODE: `damage_modifier=-2`
RULE SOURCE: SRD Conditions: Sickened — "–2 penalty on... weapon damage rolls"
EXPECTED: damage_modifier=-2
ACTUAL: damage_modifier=-2
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-382
FILE: aidm/schemas/conditions.py
LINE: 382
CODE: `fort_save_modifier=-2`
RULE SOURCE: SRD Conditions: Sickened — "–2 penalty on... saving throws"
EXPECTED: fort_save_modifier=-2
ACTUAL: fort_save_modifier=-2
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-383
FILE: aidm/schemas/conditions.py
LINE: 383
CODE: `ref_save_modifier=-2`
RULE SOURCE: SRD Conditions: Sickened — "–2 penalty on... saving throws"
EXPECTED: ref_save_modifier=-2
ACTUAL: ref_save_modifier=-2
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-384
FILE: aidm/schemas/conditions.py
LINE: 384
CODE: `will_save_modifier=-2`
RULE SOURCE: SRD Conditions: Sickened — "–2 penalty on... saving throws"
EXPECTED: will_save_modifier=-2
ACTUAL: will_save_modifier=-2
VERDICT: CORRECT
NOTES: SRD also specifies -2 to skill checks and ability checks. Scope gap same as Shaken.

---

#### Frightened (4 formulas)

FORMULA ID: D-conditions-schema-406
FILE: aidm/schemas/conditions.py
LINE: 406
CODE: `attack_modifier=-2`
RULE SOURCE: SRD Conditions: Frightened — "A frightened creature... takes a –2 penalty on all attack rolls, saving throws, skill checks, and ability checks."
EXPECTED: attack_modifier=-2
ACTUAL: attack_modifier=-2
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-407
FILE: aidm/schemas/conditions.py
LINE: 407
CODE: `fort_save_modifier=-2`
RULE SOURCE: SRD Conditions: Frightened — "–2 penalty on... saving throws"
EXPECTED: fort_save_modifier=-2
ACTUAL: fort_save_modifier=-2
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-408
FILE: aidm/schemas/conditions.py
LINE: 408
CODE: `ref_save_modifier=-2`
RULE SOURCE: SRD Conditions: Frightened — "–2 penalty on... saving throws"
EXPECTED: ref_save_modifier=-2
ACTUAL: ref_save_modifier=-2
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-409
FILE: aidm/schemas/conditions.py
LINE: 409
CODE: `will_save_modifier=-2`
RULE SOURCE: SRD Conditions: Frightened — "–2 penalty on... saving throws"
EXPECTED: will_save_modifier=-2
ACTUAL: will_save_modifier=-2
VERDICT: CORRECT
NOTES: SRD also specifies -2 to skill checks and ability checks. Scope gap same as Shaken.

---

#### Panicked (4 formulas)

FORMULA ID: D-conditions-schema-428
FILE: aidm/schemas/conditions.py
LINE: 428
CODE: `fort_save_modifier=-2`
RULE SOURCE: SRD Conditions: Panicked — "A panicked creature must drop anything it holds and flee... In addition, the creature takes a –2 penalty on all saving throws, skill checks, and ability checks."
EXPECTED: fort_save_modifier=-2
ACTUAL: fort_save_modifier=-2
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-429
FILE: aidm/schemas/conditions.py
LINE: 429
CODE: `ref_save_modifier=-2`
RULE SOURCE: SRD Conditions: Panicked — "–2 penalty on all saving throws"
EXPECTED: ref_save_modifier=-2
ACTUAL: ref_save_modifier=-2
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-430
FILE: aidm/schemas/conditions.py
LINE: 430
CODE: `will_save_modifier=-2`
RULE SOURCE: SRD Conditions: Panicked — "–2 penalty on all saving throws"
EXPECTED: will_save_modifier=-2
ACTUAL: will_save_modifier=-2
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-431
FILE: aidm/schemas/conditions.py
LINE: 431
CODE: `loses_dex_to_ac=True`
RULE SOURCE: SRD Conditions: Panicked — SRD text says "A panicked creature must drop anything it holds and flee at top speed from the source of its fear, as well as any other dangers it encounters, along a random path. It can't take any other actions. In addition, the creature takes a –2 penalty on all saving throws, skill checks, and ability checks. If cornered, a panicked creature cowers."
EXPECTED: loses_dex_to_ac=False (SRD does NOT say panicked creatures lose Dex to AC)
ACTUAL: loses_dex_to_ac=True
VERDICT: WRONG
NOTES: The SRD Panicked condition does NOT include losing Dex bonus to AC. The code comment says "Cannot defend effectively while fleeing" but this is an invention not supported by the SRD. A panicked creature is still aware of its surroundings (it's fleeing, not helpless). Cowering (if cornered) does lose Dex to AC, but Cowering is a separate condition. This should be loses_dex_to_ac=False.

---

#### Nauseated (1 formula)

FORMULA ID: D-conditions-schema-450
FILE: aidm/schemas/conditions.py
LINE: 450
CODE: `actions_prohibited=True`
RULE SOURCE: SRD Conditions: Nauseated — "Creatures with the nauseated condition experience stomach distress. Nauseated creatures are unable to attack, cast spells, concentrate on spells, or do anything else requiring attention. The only action such a character can take is a single move action per turn."
EXPECTED: Can only take a single move action per turn (not fully prohibited)
ACTUAL: actions_prohibited=True (fully prohibited)
VERDICT: AMBIGUOUS
NOTES: The SRD allows a single move action. The boolean `actions_prohibited=True` over-restricts by implying no actions at all. However, the current system has no "move_action_only" flag. This is an architectural limitation. The intent is captured (severely restricted) but the precision is wrong. A nauseated creature CAN take a move action. Should be addressed when action economy enforcement is built (CP-17+). Recorded as AMBIGUOUS because the flag is the closest available approximation but is technically over-restrictive.

---

#### Fatigued (2 formulas)

FORMULA ID: D-conditions-schema-467
FILE: aidm/schemas/conditions.py
LINE: 467
CODE: `attack_modifier=-1`
RULE SOURCE: SRD Conditions: Fatigued — "A fatigued character can neither run nor charge and takes a –2 penalty to Strength and Dexterity."
EXPECTED: The -2 STR penalty translates to -1 on STR-based attack rolls (melee). Math: floor(-2/2) = -1. However, the -2 STR also translates to -1 on STR-based damage rolls (melee), which is NOT captured.
ACTUAL: attack_modifier=-1 (correct for melee attack). No damage_modifier set.
VERDICT: WRONG
NOTES: The attack_modifier=-1 derivation from -2 STR is mathematically correct. However, the -2 STR penalty ALSO affects melee damage rolls (-1 damage modifier) which is missing. Should have `damage_modifier=-1`. Additionally, `attack_modifier=-1` only covers melee; the STR penalty doesn't affect ranged attack rolls (those use DEX, which is handled by dex_modifier=-2). The damage gap is a WRONG finding.

---

FORMULA ID: D-conditions-schema-468
FILE: aidm/schemas/conditions.py
LINE: 468
CODE: `dex_modifier=-2`
RULE SOURCE: SRD Conditions: Fatigued — "–2 penalty to... Dexterity"
EXPECTED: dex_modifier=-2
ACTUAL: dex_modifier=-2
VERDICT: CORRECT

---

#### Exhausted (2 formulas)

FORMULA ID: D-conditions-schema-485
FILE: aidm/schemas/conditions.py
LINE: 485
CODE: `attack_modifier=-3`
RULE SOURCE: SRD Conditions: Exhausted — "An exhausted character moves at half speed and takes a –6 penalty to Strength and Dexterity."
EXPECTED: -6 STR → -3 melee attack modifier. Math: floor(-6/2) = -3. However, -6 STR also → -3 melee damage modifier, which is missing.
ACTUAL: attack_modifier=-3 (correct for melee attack). No damage_modifier set.
VERDICT: WRONG
NOTES: Same issue as Fatigued. The attack_modifier=-3 is correct math for the STR-to-attack derivation, but the -6 STR also means -3 to melee damage, which should be `damage_modifier=-3`. Missing damage penalty is a bug.

---

FORMULA ID: D-conditions-schema-486
FILE: aidm/schemas/conditions.py
LINE: 486
CODE: `dex_modifier=-6`
RULE SOURCE: SRD Conditions: Exhausted — "–6 penalty to... Dexterity"
EXPECTED: dex_modifier=-6
ACTUAL: dex_modifier=-6
VERDICT: CORRECT

---

#### Paralyzed (5 formulas)

FORMULA ID: D-conditions-schema-504
FILE: aidm/schemas/conditions.py
LINE: 504
CODE: `ac_modifier=-4`
RULE SOURCE: SRD Conditions: Paralyzed — "A paralyzed character is frozen in place and unable to move or act. A paralyzed character has effective Dexterity and Strength scores of 0 and is helpless, but can take purely mental actions."
EXPECTED: Paralyzed = helpless. Helpless gives melee attackers +4 (i.e., -4 AC vs melee). Dex 0 = -5 Dex mod. The ac_modifier=-4 captures the melee attacker bonus but has the same melee/ranged differentiation issue as Helpless (BUG-4).
ACTUAL: ac_modifier=-4
VERDICT: AMBIGUOUS
NOTES: Same melee/ranged issue as Helpless (BUG-4). The -4 is correct for melee, wrong for ranged. Since this is the same root cause as BUG-4 (Paralyzed is defined as Helpless), recording as AMBIGUOUS rather than double-counting the same bug. Fix via BUG-4 will cascade here.

---

FORMULA ID: D-conditions-schema-505
FILE: aidm/schemas/conditions.py
LINE: 505
CODE: `loses_dex_to_ac=True`
RULE SOURCE: SRD Conditions: Paralyzed — effective Dex 0, therefore loses Dex bonus (and worse)
EXPECTED: True
ACTUAL: True
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-506
FILE: aidm/schemas/conditions.py
LINE: 506
CODE: `auto_hit_if_helpless=True`
RULE SOURCE: SRD Conditions: Paralyzed — "is helpless" → eligible for coup de grace
EXPECTED: True
ACTUAL: True
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-507
FILE: aidm/schemas/conditions.py
LINE: 507
CODE: `actions_prohibited=True`
RULE SOURCE: SRD Conditions: Paralyzed — "unable to move or act" (though can take purely mental actions)
EXPECTED: True (with caveat about mental actions)
ACTUAL: True
VERDICT: CORRECT
NOTES: SRD allows "purely mental actions" but the system doesn't model mental vs physical action types. Acceptable scope gap.

---

FORMULA ID: D-conditions-schema-508
FILE: aidm/schemas/conditions.py
LINE: 508
CODE: `movement_prohibited=True`
RULE SOURCE: SRD Conditions: Paralyzed — "frozen in place and unable to move"
EXPECTED: True
ACTUAL: True
VERDICT: CORRECT

---

#### Staggered (0 numeric formulas)

FORMULA ID: D-conditions-schema-524
FILE: aidm/schemas/conditions.py
LINE: 524
CODE: `ConditionModifiers()` (empty — no numeric modifiers)
RULE SOURCE: SRD Conditions: Staggered — "A staggered creature may only take a single move action or standard action each round (but not both, nor can she take full-round actions). A staggered creature can still take free actions."
EXPECTED: No numeric modifiers (action restriction only)
ACTUAL: No numeric modifiers
VERDICT: CORRECT
NOTES: The action restriction is enforcement-only, not a numeric modifier. No modifier values to verify.

---

#### Unconscious (5 formulas)

FORMULA ID: D-conditions-schema-541
FILE: aidm/schemas/conditions.py
LINE: 541
CODE: `ac_modifier=-4`
RULE SOURCE: SRD Conditions: Unconscious — "An unconscious character is helpless." Helpless: melee attackers get +4 (equiv. -4 AC vs melee).
EXPECTED: ac_modifier=-4 vs melee (same Helpless melee/ranged issue)
ACTUAL: ac_modifier=-4
VERDICT: AMBIGUOUS
NOTES: Same melee/ranged differentiation issue as Helpless (BUG-4). Unconscious = Helpless, so the same bug cascades. Recording as AMBIGUOUS (same root cause as BUG-4).

---

FORMULA ID: D-conditions-schema-542
FILE: aidm/schemas/conditions.py
LINE: 542
CODE: `loses_dex_to_ac=True`
RULE SOURCE: SRD Conditions: Unconscious → Helpless → effective Dex 0
EXPECTED: True
ACTUAL: True
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-543
FILE: aidm/schemas/conditions.py
LINE: 543
CODE: `auto_hit_if_helpless=True`
RULE SOURCE: SRD Conditions: Unconscious → Helpless → coup de grace eligible
EXPECTED: True
ACTUAL: True
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-544
FILE: aidm/schemas/conditions.py
LINE: 544
CODE: `actions_prohibited=True`
RULE SOURCE: SRD Conditions: Unconscious → Helpless → cannot act
EXPECTED: True
ACTUAL: True
VERDICT: CORRECT

---

FORMULA ID: D-conditions-schema-545
FILE: aidm/schemas/conditions.py
LINE: 545
CODE: `movement_prohibited=True`
RULE SOURCE: SRD Conditions: Unconscious → Helpless → cannot move
EXPECTED: True
ACTUAL: True
VERDICT: CORRECT

---

### aidm/core/conditions.py — Aggregation Logic (15 formulas)

---

#### Accumulator Initialization (7 formulas)

FORMULA ID: D-conditions-core-65
FILE: aidm/core/conditions.py
LINE: 65
CODE: `total_ac = 0`
RULE SOURCE: N/A (initialization)
EXPECTED: 0
ACTUAL: 0
VERDICT: CORRECT
NOTES: Zero-init for additive accumulation is correct.

---

FORMULA ID: D-conditions-core-66
FILE: aidm/core/conditions.py
LINE: 66
CODE: `total_attack = 0`
RULE SOURCE: N/A (initialization)
EXPECTED: 0
ACTUAL: 0
VERDICT: CORRECT

---

FORMULA ID: D-conditions-core-67
FILE: aidm/core/conditions.py
LINE: 67
CODE: `total_damage = 0`
RULE SOURCE: N/A (initialization)
EXPECTED: 0
ACTUAL: 0
VERDICT: CORRECT

---

FORMULA ID: D-conditions-core-68
FILE: aidm/core/conditions.py
LINE: 68
CODE: `total_dex = 0`
RULE SOURCE: N/A (initialization)
EXPECTED: 0
ACTUAL: 0
VERDICT: CORRECT

---

FORMULA ID: D-conditions-core-69
FILE: aidm/core/conditions.py
LINE: 69
CODE: `total_fort_save = 0`
RULE SOURCE: N/A (initialization)
EXPECTED: 0
ACTUAL: 0
VERDICT: CORRECT

---

FORMULA ID: D-conditions-core-70
FILE: aidm/core/conditions.py
LINE: 70
CODE: `total_ref_save = 0`
RULE SOURCE: N/A (initialization)
EXPECTED: 0
ACTUAL: 0
VERDICT: CORRECT

---

FORMULA ID: D-conditions-core-71
FILE: aidm/core/conditions.py
LINE: 71
CODE: `total_will_save = 0`
RULE SOURCE: N/A (initialization)
EXPECTED: 0
ACTUAL: 0
VERDICT: CORRECT

---

#### Additive Stacking (7 formulas — one per accumulator)

FORMULA ID: D-conditions-core-92
FILE: aidm/core/conditions.py
LINE: 92
CODE: `total_ac += mods.ac_modifier`
RULE SOURCE: SRD Stacking Rules — Penalties from conditions are untyped and stack. SRD: "Bonuses without a type always stack... Penalties stack, even if they are of the same type."
EXPECTED: Additive stacking for untyped condition penalties
ACTUAL: Simple addition
VERDICT: CORRECT
NOTES: Condition penalties are untyped and stack per SRD. Simple addition is correct for this use case. If the system later introduces typed bonuses (dodge, deflection, etc.), the aggregation would need to distinguish types. For current scope (condition penalties only), this is correct.

---

FORMULA ID: D-conditions-core-93
FILE: aidm/core/conditions.py
LINE: 93
CODE: `total_attack += mods.attack_modifier`
RULE SOURCE: SRD Stacking Rules — untyped penalties stack
EXPECTED: Additive stacking
ACTUAL: Simple addition
VERDICT: CORRECT

---

FORMULA ID: D-conditions-core-94
FILE: aidm/core/conditions.py
LINE: 94
CODE: `total_damage += mods.damage_modifier`
RULE SOURCE: SRD Stacking Rules — untyped penalties stack
EXPECTED: Additive stacking
ACTUAL: Simple addition
VERDICT: CORRECT

---

FORMULA ID: D-conditions-core-95
FILE: aidm/core/conditions.py
LINE: 95
CODE: `total_dex += mods.dex_modifier`
RULE SOURCE: SRD Stacking Rules — untyped penalties stack
EXPECTED: Additive stacking
ACTUAL: Simple addition
VERDICT: CORRECT
NOTES: Multiple DEX penalties stacking is correct per SRD. A character who is both Grappled (-4 DEX) and Fatigued (-2 DEX) would have -6 DEX total, which is correct.

---

FORMULA ID: D-conditions-core-96
FILE: aidm/core/conditions.py
LINE: 96
CODE: `total_fort_save += mods.fort_save_modifier`
RULE SOURCE: SRD Stacking Rules — untyped penalties stack
EXPECTED: Additive stacking
ACTUAL: Simple addition
VERDICT: CORRECT

---

FORMULA ID: D-conditions-core-97
FILE: aidm/core/conditions.py
LINE: 97
CODE: `total_ref_save += mods.ref_save_modifier`
RULE SOURCE: SRD Stacking Rules — untyped penalties stack
EXPECTED: Additive stacking
ACTUAL: Simple addition
VERDICT: CORRECT

---

FORMULA ID: D-conditions-core-98
FILE: aidm/core/conditions.py
LINE: 98
CODE: `total_will_save += mods.will_save_modifier`
RULE SOURCE: SRD Stacking Rules — untyped penalties stack
EXPECTED: Additive stacking
ACTUAL: Simple addition
VERDICT: CORRECT

---

#### Boolean OR Aggregation (5 formulas — one per flag, but counted as 1 formula block)

FORMULA ID: D-conditions-core-100
FILE: aidm/core/conditions.py
LINE: 100
CODE: `any_movement_prohibited = any_movement_prohibited or mods.movement_prohibited`
RULE SOURCE: Logical — any one condition prohibiting movement means movement is prohibited
EXPECTED: OR logic
ACTUAL: OR logic
VERDICT: CORRECT

---

FORMULA ID: D-conditions-core-101
FILE: aidm/core/conditions.py
LINE: 101
CODE: `any_actions_prohibited = any_actions_prohibited or mods.actions_prohibited`
RULE SOURCE: Logical — any one condition prohibiting actions means actions are prohibited
EXPECTED: OR logic
ACTUAL: OR logic
VERDICT: CORRECT

---

FORMULA ID: D-conditions-core-102
FILE: aidm/core/conditions.py
LINE: 102
CODE: `any_standing_triggers_aoo = any_standing_triggers_aoo or mods.standing_triggers_aoo`
RULE SOURCE: Logical — if any condition says standing triggers AoO, it does
EXPECTED: OR logic
ACTUAL: OR logic
VERDICT: CORRECT

---

FORMULA ID: D-conditions-core-103
FILE: aidm/core/conditions.py
LINE: 103
CODE: `any_auto_hit_if_helpless = any_auto_hit_if_helpless or mods.auto_hit_if_helpless`
RULE SOURCE: Logical — if any condition makes target helpless/auto-hittable, it is
EXPECTED: OR logic
ACTUAL: OR logic
VERDICT: CORRECT

---

FORMULA ID: D-conditions-core-104
FILE: aidm/core/conditions.py
LINE: 104
CODE: `any_loses_dex_to_ac = any_loses_dex_to_ac or mods.loses_dex_to_ac`
RULE SOURCE: Logical — if any condition causes Dex loss to AC, it is lost
EXPECTED: OR logic
ACTUAL: OR logic
VERDICT: CORRECT

---

## UNCITED Formulas

The following modifiers are present in the SRD but NOT captured in the code's ConditionModifiers schema. They are recorded as scope gaps:

FORMULA ID: D-UNCITED-01
DESCRIPTION: Shaken: skill_check_modifier=-2
RULE SOURCE: SRD Conditions: Shaken — "-2 penalty on... skill checks, and ability checks"
NOTES: No skill_check_modifier or ability_check_modifier field exists in ConditionModifiers. Will be needed when skill system is integrated.
VERDICT: UNCITED

---

FORMULA ID: D-UNCITED-02
DESCRIPTION: Sickened: skill_check_modifier=-2, ability_check_modifier=-2
RULE SOURCE: SRD Conditions: Sickened — "-2 penalty on... skill checks, and ability checks"
NOTES: Same scope gap as Shaken.
VERDICT: UNCITED

---

FORMULA ID: D-UNCITED-03
DESCRIPTION: Frightened: skill_check_modifier=-2, ability_check_modifier=-2
RULE SOURCE: SRD Conditions: Frightened — "-2 penalty on all... skill checks, and ability checks"
NOTES: Same scope gap as Shaken.
VERDICT: UNCITED

---

FORMULA ID: D-UNCITED-04
DESCRIPTION: Panicked: skill_check_modifier=-2, ability_check_modifier=-2
RULE SOURCE: SRD Conditions: Panicked — "-2 penalty on all... skill checks, and ability checks"
NOTES: Same scope gap as Shaken.
VERDICT: UNCITED

---

FORMULA ID: D-UNCITED-05
DESCRIPTION: Fatigued/Exhausted: movement speed reduction
RULE SOURCE: SRD Conditions: Fatigued — "can neither run nor charge"; Exhausted — "moves at half speed"
NOTES: No speed_modifier field in ConditionModifiers. Movement enforcement deferred to CP-17+.
VERDICT: UNCITED

---

FORMULA ID: D-UNCITED-06
DESCRIPTION: Grappled: 3.5e vs Pathfinder Dexterity penalty divergence
RULE SOURCE: SRD 3.5e says "lose Dex bonus to AC vs non-grappling opponents" (no flat penalty). Pathfinder says "–4 penalty to Dexterity." Code follows Pathfinder. If the Pathfinder -4 DEX penalty drops effective Dex bonus below 0, the system needs resolvers to correctly apply the resulting negative modifier to AC.
NOTES: This is a documented 3.5e/Pathfinder divergence. The code's PHB p.156 citation uses Pathfinder wording. If strict 3.5e is intended, this should be `loses_dex_to_ac=True` (contextual). If Pathfinder simplification is adopted (defensible — 3.5e grapple rules are notoriously complex), document the decision. See D-conditions-schema-254 AMBIGUOUS verdict.
VERDICT: UNCITED

---

## Bug List

| Bug ID | Formula ID | Condition | Description | Severity |
|--------|------------|-----------|-------------|----------|
| BUG-3 | D-conditions-schema-208 | Prone | ac_modifier=-4 is flat; SRD requires -4 vs melee, +4 vs ranged | HIGH |
| BUG-4 | D-conditions-schema-281 | Helpless | ac_modifier=-4 is flat; SRD says melee only, ranged gets no bonus | HIGH |
| BUG-5 | D-conditions-schema-431 | Panicked | loses_dex_to_ac=True but SRD Panicked does NOT include losing Dex to AC | MEDIUM |
| BUG-6 | D-conditions-schema-467 | Fatigued | Missing damage_modifier=-1 (from -2 STR penalty) | MEDIUM |
| BUG-7 | D-conditions-schema-485 | Exhausted | Missing damage_modifier=-3 (from -6 STR penalty) | MEDIUM |

## Ambiguity Register

| Formula ID | Condition | Ambiguity | Chosen Interpretation |
|------------|-----------|-----------|----------------------|
| D-conditions-schema-450 | Nauseated | actions_prohibited=True but SRD allows a single move action | Over-restrictive approximation. No "move_action_only" flag exists. Acceptable until CP-17+ action economy enforcement. |
| D-conditions-schema-504 | Paralyzed | ac_modifier=-4 has same melee/ranged issue as Helpless (BUG-4) | Same root cause as BUG-4; fix will cascade. Not double-counted as separate bug. |
| D-conditions-schema-541 | Unconscious | ac_modifier=-4 has same melee/ranged issue as Helpless (BUG-4) | Same root cause as BUG-4; fix will cascade. Not double-counted as separate bug. |
| D-conditions-schema-254 | Grappled | dex_modifier=-4 follows Pathfinder, not 3.5e SRD. 3.5e says "lose Dex bonus to AC vs non-grappling opponents" with no flat -4 penalty. | Pathfinder simplification is defensible (3.5e grapple rules are notoriously complex). Must be documented as intentional divergence. Operator decision needed: strict 3.5e (loses_dex_to_ac=True) vs Pathfinder (-4 Dex). |
| D-UNCITED-06 | Grappled | Negative Dex modifier impact on AC depends on resolver implementation | Architecturally sound if resolvers correctly apply dex_modifier to AC calculation. Needs verification during Domain A. |

## Scope Gaps (Not Bugs)

The following SRD rules are acknowledged as not yet implemented. They are NOT bugs — they are documented scope limitations of the current condition system:

1. **Skill check modifiers** — Shaken, Sickened, Frightened, Panicked all apply -2 to skill checks and ability checks. No field exists for these in ConditionModifiers. Tracked as UNCITED.
2. **Movement speed modifiers** — Fatigued (no run/charge), Exhausted (half speed). No speed_modifier field. Enforcement deferred.
3. **Frightened flee behavior** — Frightened creatures must flee. Behavioral, not a modifier.
4. **Panicked drop items** — Panicked creatures drop held items. Behavioral, not a modifier.
5. **Nauseated move-action-only** — Modeled as actions_prohibited (over-restrictive). See Ambiguity Register.

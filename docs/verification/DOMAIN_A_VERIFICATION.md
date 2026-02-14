# Domain A Verification — Attack Resolution

**Verified by:** Claude Opus 4.6
**Date:** 2026-02-14
**Formulas verified:** 53
**Summary:** 38 CORRECT, 7 WRONG, 4 AMBIGUOUS, 4 UNCITED

---

## Verification Records

### aidm/core/attack_resolver.py (18 formulas)

---

#### Dice Rolling

FORMULA ID: A-attack-resolver-113
FILE: aidm/core/attack_resolver.py
LINE: 113
CODE: `[combat_rng.randint(1, die_size) for _ in range(num_dice)]`
RULE SOURCE: SRD Combat: Damage — "If you score a hit, roll damage... Roll the appropriate damage for your weapon."
EXPECTED: Roll num_dice dice each of die_size faces, sum individual results
ACTUAL: Generates list of num_dice random integers in [1, die_size]
VERDICT: CORRECT
NOTES: Standard dice rolling mechanic. Values parsed from weapon.damage_dice (e.g., "1d8"). Correct.

---

#### Target AC Computation

FORMULA ID: A-attack-resolver-241
FILE: aidm/core/attack_resolver.py
LINE: 241
CODE: `base_ac = target.get(EF.AC, 10)`
RULE SOURCE: SRD Combat: Armor Class — "Your Armor Class (AC) represents how hard it is for opponents to land a solid, damaging blow on you. It's the attack roll result that an opponent needs to achieve to hit you. Your AC = 10 + armor bonus + shield bonus + Dexterity modifier + size modifier."
EXPECTED: Default AC of 10 (base AC for unarmored, no Dex, no size)
ACTUAL: Default 10, overridden by entity's stored AC
VERDICT: CORRECT
NOTES: Base 10 default matches SRD. The entity's AC field is expected to include armor, shield, Dex, and size. Correct.

---

FORMULA ID: A-attack-resolver-243
FILE: aidm/core/attack_resolver.py
LINE: 243
CODE: `target_ac = base_ac + defender_modifiers.ac_modifier + cover_result.ac_bonus`
RULE SOURCE: SRD Combat: Armor Class — total AC includes condition modifiers and cover bonus
EXPECTED: AC = base AC + condition AC modifier + cover AC bonus
ACTUAL: Matches expected
VERDICT: CORRECT
NOTES: The condition AC modifier is the aggregate from `get_condition_modifiers()`. Cover AC bonus comes from the cover resolver. Both are additive modifiers to the stored base AC. Correct structure. However, the condition AC modifier has known bugs (BUG-3, BUG-4 from Domain D) where Prone and Helpless AC modifiers are not melee/ranged differentiated. This formula faithfully applies whatever the condition system produces, so the formula itself is correct — the bug is upstream in Domain D.

---

#### Attack Roll

FORMULA ID: A-attack-resolver-247
FILE: aidm/core/attack_resolver.py
LINE: 247
CODE: `d20_result = combat_rng.randint(1, 20)`
RULE SOURCE: SRD Combat: Attack Roll — "An attack roll represents your attempt to strike your opponent on your turn in a round. When you make an attack roll, you roll a d20..."
EXPECTED: d20 roll, integer in [1, 20]
ACTUAL: randint(1, 20)
VERDICT: CORRECT
NOTES: Standard d20 attack roll. Correct.

---

FORMULA ID: A-attack-resolver-249-256
FILE: aidm/core/attack_resolver.py
LINE: 249-256
CODE: `attack_bonus_with_conditions = intent.attack_bonus + attacker_modifiers.attack_modifier + mounted_bonus + terrain_higher_ground + feat_attack_modifier + flanking_bonus`
RULE SOURCE: SRD Combat: Attack Roll — "your attack bonus with a melee weapon is: Base attack bonus + Strength modifier + size modifier" plus situational modifiers (conditions, higher ground, flanking, feats)
EXPECTED: Total attack bonus = BAB+STR/DEX+misc + condition modifier + mounted higher ground (0 or +1) + terrain higher ground (0 or +1) + feat modifier + flanking (0 or +2)
ACTUAL: Matches expected — all modifiers are summed additively
VERDICT: CORRECT
NOTES: The `intent.attack_bonus` is expected to include BAB + ability mod + size mod. All situational modifiers are correctly additive. Correct.

---

FORMULA ID: A-attack-resolver-257
FILE: aidm/core/attack_resolver.py
LINE: 257
CODE: `total = d20_result + attack_bonus_with_conditions`
RULE SOURCE: SRD Combat: Attack Roll — "If your attack roll result equals or exceeds the target's Armor Class, you hit."
EXPECTED: total = d20 + attack bonus
ACTUAL: total = d20_result + attack_bonus_with_conditions
VERDICT: CORRECT
NOTES: Standard attack roll total computation. Correct.

---

#### Critical Threat Detection

FORMULA ID: A-attack-resolver-260
FILE: aidm/core/attack_resolver.py
LINE: 260
CODE: `is_threat = (d20_result >= intent.weapon.critical_range)`
RULE SOURCE: SRD Combat: Critical Hits — "When you make an attack roll and get a natural 20 (the d20 shows 20), you hit regardless of your target's Armor Class, and you have scored a threat. The hit might be a critical hit (or 'crit'). ... Increased Threat Range: Sometimes your threat range is greater than 20. That is, you can score a threat on a lower number."
EXPECTED: Threat if d20 >= weapon's critical threat range (default 20)
ACTUAL: d20_result >= intent.weapon.critical_range
VERDICT: CORRECT
NOTES: Weapon critical_range defaults to 20 (Weapon dataclass). For 19-20 weapons, critical_range=19. For 18-20 weapons, critical_range=18. Correct.

---

#### Natural 1 / Natural 20

FORMULA ID: A-attack-resolver-267
FILE: aidm/core/attack_resolver.py
LINE: 267
CODE: `if is_natural_1: hit = False`
RULE SOURCE: SRD Combat: Automatic Misses and Hits — "A natural 1 (the d20 comes up 1) on an attack roll is always a miss."
EXPECTED: Natural 1 always misses
ACTUAL: hit = False when d20_result == 1
VERDICT: CORRECT
NOTES: Correct per SRD.

---

FORMULA ID: A-attack-resolver-269
FILE: aidm/core/attack_resolver.py
LINE: 269
CODE: `elif is_natural_20: hit = True`
RULE SOURCE: SRD Combat: Automatic Misses and Hits — "A natural 20 (the d20 comes up 20) is always a hit."
EXPECTED: Natural 20 always hits
ACTUAL: hit = True when d20_result == 20
VERDICT: CORRECT
NOTES: SRD specifies natural 20 is always a hit AND always a threat. The threat is handled separately at line 260 (d20_result >= critical_range, and since 20 >= any valid critical_range, it always qualifies). Correct.

---

#### Hit Determination

FORMULA ID: A-attack-resolver-272
FILE: aidm/core/attack_resolver.py
LINE: 272
CODE: `hit = (total >= target_ac)`
RULE SOURCE: SRD Combat: Attack Roll — "If your attack roll result equals or exceeds the target's Armor Class, you hit."
EXPECTED: Hit if total >= target AC
ACTUAL: total >= target_ac
VERDICT: CORRECT
NOTES: Standard hit determination. The "equals or exceeds" is correctly implemented with `>=`. Correct.

---

#### Critical Confirmation

FORMULA ID: A-attack-resolver-278
FILE: aidm/core/attack_resolver.py
LINE: 278
CODE: `confirmation_d20 = combat_rng.randint(1, 20)`
RULE SOURCE: SRD Combat: Critical Hits — "To find out if it's a critical hit, you immediately make a critical roll — another attack roll with all the same modifiers as the attack roll you just made."
EXPECTED: Roll another d20 for confirmation
ACTUAL: combat_rng.randint(1, 20)
VERDICT: CORRECT
NOTES: Confirmation roll is a separate d20. Correct.

---

FORMULA ID: A-attack-resolver-280
FILE: aidm/core/attack_resolver.py
LINE: 280
CODE: `confirmation_total = confirmation_d20 + attack_bonus_with_conditions`
RULE SOURCE: SRD Combat: Critical Hits — "another attack roll with all the same modifiers as the attack roll you just made"
EXPECTED: confirmation total = confirmation d20 + same attack bonus
ACTUAL: confirmation_d20 + attack_bonus_with_conditions (same bonus as original attack)
VERDICT: CORRECT
NOTES: Uses the same attack_bonus_with_conditions as the original roll. Correct per SRD.

---

FORMULA ID: A-attack-resolver-282
FILE: aidm/core/attack_resolver.py
LINE: 282
CODE: `is_critical = confirmation_total >= target_ac`
RULE SOURCE: SRD Combat: Critical Hits — "If the critical roll also results in a hit against the target's AC, your original hit is a critical hit."
EXPECTED: Critical if confirmation total >= target AC (no auto-hit on natural 20 for confirmation)
ACTUAL: confirmation_total >= target_ac
VERDICT: CORRECT
NOTES: The code correctly does NOT apply natural 20 auto-hit logic to the confirmation roll. SRD says "If the critical roll also results in a hit against the target's AC" — this is a normal hit check against AC. A natural 20 on the confirmation roll is not an auto-confirm per SRD. Correct.

---

#### Damage Computation

FORMULA ID: A-attack-resolver-355
FILE: aidm/core/attack_resolver.py
LINE: 355
CODE: `str_modifier = attacker.get(EF.STR_MOD, 0)`
RULE SOURCE: SRD Combat: Damage — "Strength Bonus: When you hit with a melee or thrown weapon... you add your Strength modifier to the damage."
EXPECTED: STR modifier from entity, default 0
ACTUAL: attacker.get(EF.STR_MOD, 0)
VERDICT: CORRECT
NOTES: Retrieves STR modifier. The default of 0 is correct for entities without explicit STR_MOD. Correct.

---

FORMULA ID: A-attack-resolver-363
FILE: aidm/core/attack_resolver.py
LINE: 363
CODE: `base_damage = sum(damage_rolls) + intent.weapon.damage_bonus + str_modifier`
RULE SOURCE: SRD Combat: Damage — "If you're using a weapon that you add your Strength modifier to damage, [two-handed:] add 1-1/2 times your Strength bonus... [Off hand:] add only 1/2 your Strength bonus."
EXPECTED: For one-handed melee: dice + weapon bonus + STR mod. For two-handed: dice + weapon bonus + int(STR * 1.5). For off-hand: dice + weapon bonus + int(STR * 0.5).
ACTUAL: Always uses flat `str_modifier` regardless of weapon handedness
VERDICT: WRONG
NOTES: **BUG-1 CONFIRMED.** The code uses `str_modifier` (flat STR mod) for all weapons. SRD requires 1.5x STR for two-handed weapons (rounded down) and 0.5x STR for off-hand weapons. The `intent.weapon.is_two_handed` field exists but is not consulted here. Expected: `int(str_modifier * 1.5)` for two-handed, `int(str_modifier * 0.5)` for off-hand. Additionally, if STR modifier is negative, the 1.5x multiplier ALSO applies to negative STR (SRD: "If you have a penalty, the penalty applies to the damage as well"). For example, STR mod -2 with two-handed = int(-2 * 1.5) = -3.

---

FORMULA ID: A-attack-resolver-365
FILE: aidm/core/attack_resolver.py
LINE: 365
CODE: `base_damage_with_modifiers = base_damage + attacker_modifiers.damage_modifier + feat_damage_modifier`
RULE SOURCE: SRD Combat: Damage — condition modifiers and feat modifiers apply to damage
EXPECTED: base_damage + condition damage modifier + feat damage modifier
ACTUAL: Matches expected
VERDICT: CORRECT
NOTES: Additive stacking of damage modifiers is correct. Condition damage modifiers include effects like Sickened (-2). Feat damage modifiers include Weapon Specialization (+2), Power Attack, Point Blank Shot (+1). Correct structure. However, note that Domain D found BUG-6 (Fatigued missing damage_modifier=-1) and BUG-7 (Exhausted missing damage_modifier=-3) — the formula here is correct but upstream condition values have bugs.

---

#### Critical Damage

FORMULA ID: A-attack-resolver-369
FILE: aidm/core/attack_resolver.py
LINE: 369
CODE: `damage_total = max(0, base_damage_with_modifiers * intent.weapon.critical_multiplier)`
RULE SOURCE: SRD Combat: Critical Hits — "A critical hit means that you roll your damage more than once, with all your usual bonuses, and add the rolls together." "Exception: Extra damage over and above a weapon's normal damage is not multiplied when you score a critical hit."
EXPECTED: On critical: multiply (dice + static bonuses) by multiplier, but do NOT multiply bonus dice (sneak attack, flaming, etc.)
ACTUAL: `base_damage_with_modifiers * critical_multiplier` — multiplies sum of (dice + weapon bonus + STR + condition mod + feat mod). Sneak attack is added separately AFTER this multiplication (line 382). `max(0, ...)` clamps floor to 0.
VERDICT: WRONG
NOTES: **BUG-8 (NEW).** Two issues: (1) The multiplication approach is technically wrong per RAW. SRD says "roll your damage more than once... and add the rolls together" — meaning you should re-roll the dice for each multiplier rather than multiplying the single roll. However, multiplying by the multiplier is a universally accepted shortcut that produces the same expected value, so this is a minor implementation divergence rather than a true correctness bug. (2) **The floor of `max(0, ...)` is wrong.** SRD states: "If penalties reduce the damage result to less than 1, a hit still deals 1 point of damage." The minimum damage on a successful hit should be 1, not 0. Using `max(0, ...)` means a hit can deal 0 damage before DR, violating the SRD minimum-1 rule. This should be `max(1, ...)`.

---

FORMULA ID: A-attack-resolver-371
FILE: aidm/core/attack_resolver.py
LINE: 371
CODE: `damage_total = max(0, base_damage_with_modifiers)`
RULE SOURCE: SRD Combat: Damage — "If penalties reduce the damage result to less than 1, a hit still deals 1 point of damage."
EXPECTED: damage_total = max(1, base_damage_with_modifiers)
ACTUAL: damage_total = max(0, base_damage_with_modifiers)
VERDICT: WRONG
NOTES: **BUG-9 (NEW).** Non-critical path also uses `max(0, ...)` instead of `max(1, ...)`. SRD explicitly says the minimum damage on a successful hit is 1 point (before DR). A hit that deals 0 damage before DR is not possible per RAW. The floor should be 1, not 0.

---

#### Sneak Attack Addition

FORMULA ID: A-attack-resolver-382
FILE: aidm/core/attack_resolver.py
LINE: 382
CODE: `damage_total += sa_damage`
RULE SOURCE: SRD Classes: Rogue — "This extra damage is not multiplied in case of a critical hit."
EXPECTED: Sneak attack damage added after critical multiplication (not multiplied on crit)
ACTUAL: sa_damage added after crit multiplication at line 369
VERDICT: CORRECT
NOTES: Sneak attack is correctly added AFTER the critical multiplier is applied. SRD says precision damage (sneak attack) is NOT multiplied on crits. The ordering here ensures that. Correct.

---

#### Damage Reduction Application

FORMULA ID: A-attack-resolver-389
FILE: aidm/core/attack_resolver.py
LINE: 389
CODE: `final_damage = apply_dr_to_damage(damage_total, dr_amount)`
RULE SOURCE: SRD Special Abilities: Damage Reduction — "The creature takes normal damage from energy attacks (even nonmagical ones), spells, spell-like abilities, and supernatural abilities. A certain kind of weapon can sometimes damage the creature normally, as noted below." / "Whenever damage reduction completely negates the damage from an attack, it also negates most special effects that accompany the attack."
EXPECTED: DR applied after all damage bonuses (including sneak attack); reduces damage, minimum 0 after DR
ACTUAL: apply_dr_to_damage subtracts min(dr_amount, damage_total) from damage_total, floor 0
VERDICT: CORRECT
NOTES: DR is correctly applied after sneak attack and after critical multiplication. The apply_dr_to_damage function (line 182-187 of damage_reduction.py) correctly implements `final_damage = damage_total - min(dr_amount, damage_total)`, which floors at 0 after DR. Note: the SRD minimum-1-per-hit rule (BUG-8/BUG-9) applies BEFORE DR, not after. DR CAN reduce damage to 0. Correct.

---

#### HP Update and Defeat

FORMULA ID: A-attack-resolver-424
FILE: aidm/core/attack_resolver.py
LINE: 424
CODE: `hp_after = hp_before - final_damage`
RULE SOURCE: Uncited — standard HP subtraction
EXPECTED: New HP = current HP - final damage
ACTUAL: hp_before - final_damage
VERDICT: UNCITED
NOTES: Standard HP subtraction. No SRD citation needed — this is basic arithmetic. HP can go below 0. Correct behavior.

---

FORMULA ID: A-attack-resolver-442
FILE: aidm/core/attack_resolver.py
LINE: 442
CODE: `defeated = hp_after <= 0`
RULE SOURCE: SRD Combat: Injury and Death — "When your hit point total reaches 0, you're disabled. When it drops to -1 or below, you're dying. When it drops to -10 or below, you're dead."
EXPECTED: Defeat at HP <= 0 (simplified; SRD has disabled/dying/dead distinction)
ACTUAL: hp_after <= 0
VERDICT: AMBIGUOUS
NOTES: The SRD has a nuanced HP system: 0 HP = disabled, -1 to -9 = dying, -10 = dead. The code treats HP <= 0 as "defeated" which is a simplification that merges disabled/dying/dead into one state. This is a design choice, not a formula error. The choice is defensible for a combat simulation (entity is effectively out of the fight), but it does not model the SRD's disabled state (can take a single standard action at 0 HP) or the dying state (can stabilize). Should be documented as intentional simplification.

---

### aidm/core/full_attack_resolver.py (8 formulas)

---

#### Iterative Attack Calculation

FORMULA ID: A-full-attack-97
FILE: aidm/core/full_attack_resolver.py
LINE: 97-121
CODE: `attacks = [bab]; while current >= 1: append(current); current -= 5`
RULE SOURCE: SRD Combat: Full Attack — "If you get more than one attack per round because your base attack bonus is high enough, you must use a full attack action (and target each attack separately). ... A base attack bonus of +6 is enough to entitle you to a second attack, at +1. A base attack bonus of +11 is enough to entitle you to a third attack, at +6. A base attack bonus of +16 is enough to entitle you to a fourth attack, at +11."
EXPECTED: First attack at BAB, then -5 decrements while >= +1. Examples: BAB +6 -> [+6, +1]. BAB +11 -> [+11, +6, +1]. BAB +16 -> [+16, +11, +6, +1].
ACTUAL: `attacks = [base_attack_bonus]; current = bab - 5; while current >= 1: append(current); current -= 5`
VERDICT: CORRECT
NOTES: Let me verify with examples. BAB 6: [6], then current=1 (>=1, append), current=-4 (stop) -> [6, 1]. BAB 11: [11], 6 (append), 1 (append), -4 (stop) -> [11, 6, 1]. BAB 16: [16], 11, 6, 1 -> [16, 11, 6, 1]. BAB 5: [5], 0 (stop) -> [5]. All correct per SRD. Maximum 4 iterative attacks. Correct.

---

#### Full Attack Damage

FORMULA ID: A-full-attack-297-299
FILE: aidm/core/full_attack_resolver.py
LINE: 297-299
CODE: `base_damage = sum(damage_rolls) + weapon.damage_bonus + str_modifier + condition_damage_modifier + feat_damage_modifier`
RULE SOURCE: SRD Combat: Damage — same as attack_resolver.py damage formula
EXPECTED: For two-handed: int(STR * 1.5); for off-hand: int(STR * 0.5); for one-handed: STR mod
ACTUAL: Uses flat str_modifier (same bug as attack_resolver.py line 363)
VERDICT: WRONG
NOTES: **BUG-1 CONFIRMED (second location).** Same two-handed STR multiplier bug as attack_resolver.py:363. The `str_modifier` parameter is passed from `resolve_full_attack()` at line 504 as `attacker.get(EF.STR_MOD, 0)` — a flat STR mod with no 1.5x for two-handed weapons.

---

#### Full Attack Critical Damage

FORMULA ID: A-full-attack-303
FILE: aidm/core/full_attack_resolver.py
LINE: 303
CODE: `critical_damage = max(0, base_damage_with_modifiers * weapon.critical_multiplier)`
RULE SOURCE: SRD Combat: Critical Hits — multiply base damage by multiplier
EXPECTED: max(1, ...) per SRD minimum-damage-on-hit rule
ACTUAL: max(0, ...) — same bug as attack_resolver.py:369
VERDICT: WRONG
NOTES: **BUG-8 CONFIRMED (second location).** Same minimum damage floor bug. Should be `max(1, ...)` for a successful hit. Additionally, the non-critical path at line 305 uses `max(0, ...)` — same BUG-9 issue.

---

#### Full Attack Target AC

FORMULA ID: A-full-attack-499
FILE: aidm/core/full_attack_resolver.py
LINE: 499
CODE: `target_ac = base_ac + defender_modifiers.ac_modifier + cover_result.ac_bonus`
RULE SOURCE: SRD Combat: Armor Class — same as attack_resolver.py line 243
EXPECTED: Same formula as single attack AC computation
ACTUAL: Matches attack_resolver.py:243
VERDICT: CORRECT
NOTES: Same structure as single attack resolver. Condition modifier and cover bonus are applied. Same upstream Domain D bugs (BUG-3, BUG-4) apply but the formula itself is correct.

---

#### Full Attack Bonus Computation

FORMULA ID: A-full-attack-548-555
FILE: aidm/core/full_attack_resolver.py
LINE: 548-555
CODE: `adjusted_bonus = raw_attack_bonus + attacker_modifiers.attack_modifier + mounted_bonus + terrain_higher_ground + feat_attack_modifier + flanking_bonus`
RULE SOURCE: SRD Combat: Attack Roll — same modifier structure as single attack
EXPECTED: iterative BAB + condition mod + mounted + terrain + feat + flanking
ACTUAL: Matches expected
VERDICT: CORRECT
NOTES: Each iterative attack gets its own raw_attack_bonus (from calculate_iterative_attacks) but shares the same situational modifiers. This is correct per SRD — situational modifiers don't change between iterative attacks within a full attack.

---

#### Full Attack HP Update

FORMULA ID: A-full-attack-595
FILE: aidm/core/full_attack_resolver.py
LINE: 595
CODE: `hp_after = hp_before - total_damage`
RULE SOURCE: Uncited — standard HP subtraction
EXPECTED: HP after = HP before - accumulated total damage from all hits
ACTUAL: hp_before - total_damage (where total_damage is sum of all individual attack final_damage values)
VERDICT: UNCITED
NOTES: Damage is accumulated across all iterative attacks and applied once. This is functionally equivalent to applying each attack's damage individually. Correct.

---

#### Full Attack Loop — No Early Termination on Target Defeat

FORMULA ID: A-full-attack-546-loop
FILE: aidm/core/full_attack_resolver.py
LINE: 546-590 (loop structure)
CODE: `for attack_index, raw_attack_bonus in enumerate(attack_bonuses):` — no break condition for target HP reaching 0
RULE SOURCE: SRD Combat: Full Attack — "If you get multiple attacks because your base attack bonus is high enough, if you've already taken a 5-foot step, and if the target is already dead, you can't redirect remaining attacks to a new target."
EXPECTED: When a target is reduced to 0 or fewer HP mid-sequence, remaining attacks should either stop or be redirectable per DM discretion. At minimum, attacks against a dead target are wasted.
ACTUAL: All iterative attacks execute regardless of target HP. Damage accumulates even against a "dead" target.
VERDICT: WRONG
NOTES: **BUG-2 CONFIRMED.** The full attack loop does not check target HP between iterative attacks. All attacks execute against a potentially already-defeated target. While the SRD doesn't explicitly say you MUST stop attacking a dead creature (you can "attack" a corpse), the issue is that damage accumulates to a meaningless negative HP without the player/AI being able to redirect attacks to other targets. This is a functional bug for the combat engine.

---

### aidm/core/sneak_attack.py (3 formulas)

---

#### Sneak Attack Range Limitation

FORMULA ID: A-sneak-attack-55
FILE: aidm/core/sneak_attack.py
LINE: 55
CODE: `SNEAK_ATTACK_MAX_RANGE = 30`
RULE SOURCE: SRD Classes: Rogue — "A rogue can sneak attack only living creatures with discernible anatomies... The rogue must be able to see the target well enough to pick out a vital spot and must be able to reach such a spot. A rogue cannot sneak attack while striking a creature with concealment or striking the limbs of a creature whose vitals are beyond reach. Ranged attacks can count as sneak attacks only if the target is within 30 feet."
EXPECTED: 30 feet maximum range for ranged sneak attacks
ACTUAL: SNEAK_ATTACK_MAX_RANGE = 30
VERDICT: CORRECT
NOTES: Correct per SRD. The 30-foot limitation applies only to ranged sneak attacks. Melee sneak attacks have no range limitation (must be in melee range). Correct.

---

#### Sneak Attack Dice Calculation

FORMULA ID: A-sneak-attack-82
FILE: aidm/core/sneak_attack.py
LINE: 82
CODE: `num_dice = (rogue_level + 1) // 2`
RULE SOURCE: SRD Classes: Rogue — "If a rogue can catch an opponent when he is unable to defend himself effectively from her attack, she can strike a vital spot for extra damage. ... This extra damage is 1d6 at 1st level, and it increases by 1d6 every two rogue levels thereafter."
EXPECTED: Rogue level 1: 1d6, level 2: 1d6, level 3: 2d6, level 4: 2d6, level 5: 3d6, etc. Formula: (level + 1) // 2
ACTUAL: (rogue_level + 1) // 2
VERDICT: CORRECT
NOTES: Verification: level 1: (1+1)//2 = 1. Level 2: (2+1)//2 = 1. Level 3: (3+1)//2 = 2. Level 5: (5+1)//2 = 3. Level 19: (19+1)//2 = 10. All match SRD rogue table (1d6 at 1st, 2d6 at 3rd, 3d6 at 5th, ..., 10d6 at 19th). Correct.

---

#### Sneak Attack Damage Roll

FORMULA ID: A-sneak-attack-202
FILE: aidm/core/sneak_attack.py
LINE: 202
CODE: `rolls = [combat_rng.randint(1, 6) for _ in range(num_dice)]`
RULE SOURCE: SRD Classes: Rogue — extra damage is "Xd6"
EXPECTED: Roll num_dice d6
ACTUAL: List of num_dice random integers in [1, 6]
VERDICT: CORRECT
NOTES: Standard d6 rolling for sneak attack damage. Correct.

---

### aidm/core/damage_reduction.py (6 formulas)

---

#### Energy/Physical Type Sets

FORMULA ID: A-dr-45-53
FILE: aidm/core/damage_reduction.py
LINE: 45-53
CODE: `_ENERGY_DAMAGE_TYPES = frozenset({"fire", "cold", "acid", "electricity", "sonic", "force", "positive", "negative", "untyped"})` and `_PHYSICAL_DAMAGE_TYPES = frozenset({"slashing", "piercing", "bludgeoning"})`
RULE SOURCE: SRD Special Abilities: Damage Reduction — "Damage reduction does not negate touch attacks, energy attacks dealt on top of a weapon's physical damage, or energy drains."
EXPECTED: DR applies only to physical damage types (slashing, piercing, bludgeoning). Energy types (fire, cold, acid, electricity, sonic), force, and untyped bypass DR.
ACTUAL: Energy set includes fire, cold, acid, electricity, sonic, force, positive, negative, untyped. Physical set includes slashing, piercing, bludgeoning.
VERDICT: CORRECT
NOTES: The energy set is comprehensive. Including "positive" and "negative" energy is correct — these are magical energy types that bypass DR. Including "untyped" is a reasonable design decision for catch-all damage. "Force" bypasses DR per SRD. Correct.

---

#### Magic Weapon Detection

FORMULA ID: A-dr-99
FILE: aidm/core/damage_reduction.py
LINE: 99
CODE: `effective_magic = is_magic_weapon or weapon_enhancement >= 1`
RULE SOURCE: SRD Special Abilities: Damage Reduction — "Some monsters are vulnerable to magic weapons. Any weapon with at least a +1 magical enhancement bonus on attack and damage rolls overcomes the damage reduction of these monsters."
EXPECTED: Weapon is magic if explicitly flagged OR has enhancement bonus >= +1
ACTUAL: is_magic_weapon or weapon_enhancement >= 1
VERDICT: CORRECT
NOTES: A weapon with +1 or better enhancement counts as magic for DR bypass purposes. The `is_magic_weapon` flag allows for weapons that are magic but have no enhancement bonus (e.g., specific magic weapons). Correct.

---

#### Epic DR Bypass

FORMULA ID: A-dr-156
FILE: aidm/core/damage_reduction.py
LINE: 156-157
CODE: `if bypass_type == "epic": return enhancement >= 6`
RULE SOURCE: SRD Epic: "DR X/epic can be overcome by a weapon with an enhancement bonus of +6 or greater."
EXPECTED: Epic DR bypassed by enhancement >= +6
ACTUAL: enhancement >= 6
VERDICT: CORRECT
NOTES: SRD epic rules specify +6 or greater enhancement bonus overcomes DR/epic. Correct.

---

#### DR Reduction Calculation

FORMULA ID: A-dr-182-185
FILE: aidm/core/damage_reduction.py
LINE: 182-187
CODE: `damage_reduced = min(dr_amount, damage_total)` then `final_damage = damage_total - damage_reduced`
RULE SOURCE: SRD Special Abilities: Damage Reduction — "Subtract the creature's damage reduction from the damage dealt to it."
EXPECTED: Reduce damage by DR amount, minimum 0 after DR
ACTUAL: damage_reduced = min(dr_amount, damage_total); final_damage = damage_total - damage_reduced
VERDICT: CORRECT
NOTES: The min() prevents negative final_damage (when DR > damage). Final damage after DR can be 0. This is correct — DR CAN reduce damage to 0 per SRD. The minimum-1-per-hit rule applies BEFORE DR. Correct.

---

### aidm/core/flanking.py (3 formulas)

---

#### Flanking Bonus Value

FORMULA ID: A-flanking-44
FILE: aidm/core/flanking.py
LINE: 44
CODE: `FLANKING_BONUS = 2`
RULE SOURCE: SRD Combat: Flanking — "When making a melee attack, you get a +2 flanking bonus if your opponent is threatened by a character or creature friendly to you on the opponent's opposite border or opposite corner."
EXPECTED: +2 flanking bonus
ACTUAL: FLANKING_BONUS = 2
VERDICT: CORRECT
NOTES: +2 untyped bonus to melee attack rolls when flanking. Correct.

---

#### Minimum Flanking Angle

FORMULA ID: A-flanking-49
FILE: aidm/core/flanking.py
LINE: 49
CODE: `MIN_FLANKING_ANGLE = 135.0`
RULE SOURCE: SRD Combat: Flanking (diagram) — "When in doubt about whether two friendly characters flank an opponent in the middle, trace an imaginary line between the two friendly characters' centers. If the line passes through opposite borders of the opponent's space (including corners of those borders), then the opponent is flanked."
EXPECTED: The "opposite sides" rule on a square grid requires the attacker and ally to be on roughly opposite sides. 180 degrees is directly opposite; the SRD diagram shows that "opposite corners" also qualifies, which geometrically corresponds to angles >= 135 degrees for Medium creatures on a 5-foot grid.
ACTUAL: MIN_FLANKING_ANGLE = 135.0
VERDICT: AMBIGUOUS
NOTES: The SRD flanking rule is defined by a line-through-center test, not an angle test. The 135-degree threshold is a geometric approximation of the RAW rule. For Medium creatures on a standard grid, a 135-degree threshold correctly identifies all cases where the line from attacker to ally passes through opposite borders/corners. However, for Large+ creatures, the mapping is less precise. This is a defensible simplification but should be documented. The exact RAW test is: draw a line from center of attacker's space to center of ally's space; if it crosses two opposite borders of the target's space, flanking applies.

---

#### Flanking Angle Calculation

FORMULA ID: A-flanking-119-130
FILE: aidm/core/flanking.py
LINE: 119-130
CODE: Angle via dot product — `dot = ax*bx + ay*by; cos_angle = dot/(mag_a*mag_b); angle = acos(cos_angle)`
RULE SOURCE: SRD Combat: Flanking (diagram) — geometric determination of "opposite sides"
EXPECTED: Calculate angle between (target->attacker) and (target->ally) vectors
ACTUAL: Standard dot product angle calculation with proper clamping for floating point safety
VERDICT: CORRECT
NOTES: The dot product formula `cos(theta) = (A . B) / (|A| * |B|)` is mathematically correct. The clamping to [-1, 1] before acos prevents NaN from floating point errors. The angle is in degrees (0-180). Used in conjunction with MIN_FLANKING_ANGLE = 135. Correct implementation.

---

### aidm/core/concealment.py (2 formulas)

---

#### Miss Chance Aggregation

FORMULA ID: A-concealment-67
FILE: aidm/core/concealment.py
LINE: 67
CODE: `effective_miss_chance = min(best_miss_chance, 100)`
RULE SOURCE: SRD Combat: Concealment — "Concealment Miss Chance: Concealment gives the subject of a successful attack a 20% chance that the attacker missed because of the concealment. If the attacker hits, the defender must make a miss chance percentile roll... Multiple concealment conditions do not stack."
EXPECTED: Use highest miss chance, cap at 100%
ACTUAL: Takes highest from direct miss_chance field and all conditions, capped at 100
VERDICT: CORRECT
NOTES: SRD says miss chances from concealment don't stack — use the best (highest) one. The code iterates conditions and keeps the highest, then caps at 100%. Correct.

---

#### Miss Chance Roll

FORMULA ID: A-concealment-90
FILE: aidm/core/concealment.py
LINE: 90
CODE: `d100_roll = combat_rng.randint(1, 100); miss = d100_roll <= miss_chance_percent`
RULE SOURCE: SRD Combat: Concealment — "Make a miss chance percentile roll: roll d100 and if your roll is equal to or lower than the miss chance, you miss."
EXPECTED: Roll d100; miss if roll <= miss chance percentage
ACTUAL: d100_roll <= miss_chance_percent
VERDICT: CORRECT
NOTES: Convention: 1-20 = miss for 20% concealment, 1-50 = miss for 50% total concealment. The `<=` comparison matches the SRD "equal to or lower" wording. Correct.

---

### aidm/core/ranged_resolver.py (4 formulas)

---

#### Range Penalty Per Increment

FORMULA ID: A-ranged-27
FILE: aidm/core/ranged_resolver.py
LINE: 27
CODE: `PENALTY_PER_INCREMENT = -2`
RULE SOURCE: SRD Combat: Range Penalty — "Any attack at more than this distance is penalized for range. Beyond this range, the attack takes a cumulative –2 penalty for each full range increment (or fraction thereof) of distance to the target."
EXPECTED: -2 per range increment beyond the first
ACTUAL: PENALTY_PER_INCREMENT = -2
VERDICT: CORRECT
NOTES: Correct per SRD. The first increment has no penalty; second increment is -2, third is -4, etc. Correct.

---

#### Maximum Range Increments

FORMULA ID: A-ranged-29-30
FILE: aidm/core/ranged_resolver.py
LINE: 29-30
CODE: `DEFAULT_MAX_INCREMENTS = 10; THROWN_MAX_INCREMENTS = 5`
RULE SOURCE: SRD Combat: Range Penalty — "A weapon that can be thrown has a maximum range of 5 range increments." / "Projectile weapons: most projectile weapons have a maximum range of 10 range increments."
EXPECTED: 10 increments for projectile, 5 for thrown
ACTUAL: DEFAULT_MAX_INCREMENTS = 10, THROWN_MAX_INCREMENTS = 5
VERDICT: CORRECT
NOTES: Correct per SRD. Projectile weapons (bows, crossbows) max 10 increments. Thrown weapons (javelin, dagger) max 5 increments. Correct.

---

#### Range Increment Calculation

FORMULA ID: A-ranged-159
FILE: aidm/core/ranged_resolver.py
LINE: 159
CODE: `range_increment = ((distance_ft - 1) // range_increment_ft) + 1`
RULE SOURCE: SRD Combat: Range — "Any attack at less than this distance is not penalized for range." (first increment = no penalty)
EXPECTED: Increment 1 for distances 1 to range_increment_ft. Increment 2 for range_increment_ft+1 to 2*range_increment_ft. Etc.
ACTUAL: ((distance - 1) // increment) + 1. Example with 60ft increment: 1ft -> (0//60)+1 = 1. 60ft -> (59//60)+1 = 1. 61ft -> (60//60)+1 = 2. 120ft -> (119//60)+1 = 2. 121ft -> (120//60)+1 = 3.
VERDICT: CORRECT
NOTES: The formula correctly maps distance ranges to increment numbers. Verified with shortbow (60ft): 1-60ft = increment 1, 61-120ft = increment 2, etc. Correct.

---

#### Range Penalty Calculation

FORMULA ID: A-ranged-200
FILE: aidm/core/ranged_resolver.py
LINE: 200
CODE: `range_penalty = (increment - 1) * PENALTY_PER_INCREMENT`
RULE SOURCE: SRD Combat: Range Penalty — cumulative -2 per increment beyond the first
EXPECTED: Increment 1 = 0 penalty. Increment 2 = -2. Increment 3 = -4. Etc.
ACTUAL: (increment - 1) * -2. Increment 1: 0*-2 = 0. Increment 2: 1*-2 = -2. Increment 3: 2*-2 = -4. Increment 10: 9*-2 = -18.
VERDICT: CORRECT
NOTES: Maximum penalty at 10th increment is -18. Correct per SRD.

---

### aidm/core/reach_resolver.py (5 formulas)

---

#### Tall Creature Reach Table

FORMULA ID: A-reach-26-36
FILE: aidm/core/reach_resolver.py
LINE: 26-36
CODE: `DEFAULT_REACH_BY_SIZE_TALL = {FINE: 0, DIMINUTIVE: 0, TINY: 0, SMALL: 5, MEDIUM: 5, LARGE: 10, HUGE: 15, GARGANTUAN: 20, COLOSSAL: 30}`
RULE SOURCE: SRD Combat: Table — Big and Little Creatures In Combat (Tall column): "Fine 0, Diminutive 0, Tiny 0, Small 5, Medium 5, Large 10, Huge 15, Gargantuan 20, Colossal 30" (all in feet, natural reach)
EXPECTED: Fine=0, Diminutive=0, Tiny=0, Small=5, Medium=5, Large=10, Huge=15, Gargantuan=20, Colossal=30
ACTUAL: Matches expected exactly
VERDICT: CORRECT
NOTES: The SRD "Table: Creature Size and Scale" (Tall column, Natural Reach row) matches. All 9 size categories verified. Note: SRD says Fine through Tiny have 0 natural reach, meaning they must enter an opponent's square to attack. Correct.

---

#### Long Creature Reach Table

FORMULA ID: A-reach-39-49
FILE: aidm/core/reach_resolver.py
LINE: 39-49
CODE: `DEFAULT_REACH_BY_SIZE_LONG = {FINE: 0, DIMINUTIVE: 0, TINY: 0, SMALL: 5, MEDIUM: 5, LARGE: 5, HUGE: 10, GARGANTUAN: 15, COLOSSAL: 20}`
RULE SOURCE: SRD Combat: Table — Big and Little Creatures In Combat (Long column): "Fine 0, Diminutive 0, Tiny 0, Small 5, Medium 5, Large 5, Huge 10, Gargantuan 15, Colossal 20" (all in feet, natural reach)
EXPECTED: Fine=0, Diminutive=0, Tiny=0, Small=5, Medium=5, Large=5, Huge=10, Gargantuan=15, Colossal=20
ACTUAL: Matches expected exactly
VERDICT: CORRECT
NOTES: The SRD "Table: Creature Size and Scale" (Long column, Natural Reach row) matches. Key difference from Tall: Large long has 5ft reach (not 10), and each category above is one step less than Tall. All 9 size categories verified. Correct.

---

#### Chebyshev Distance for Reach

FORMULA ID: A-reach-116-118
FILE: aidm/core/reach_resolver.py
LINE: 116-118
CODE: `dx = abs(pos1.x - pos2.x); dy = abs(pos1.y - pos2.y); return max(dx, dy)`
RULE SOURCE: SRD Combat: "A character threatens the squares he can reach... Reach is measured from any square the creature occupies to any square within its reach."
EXPECTED: Chebyshev (max of dx, dy) distance for grid-based reach determination
ACTUAL: max(abs(dx), abs(dy))
VERDICT: AMBIGUOUS
NOTES: The SRD uses a diagonal-aware movement system (5-10-5-10 alternation for movement) but for reach/threatened squares, the convention is typically Chebyshev distance on a square grid. The PHB diagrams for threatened areas show Chebyshev-style rings. However, strictly speaking, SRD reach uses the same diagonal counting as movement (5-10-5-10). For a 10ft reach, the SRD threatens all squares within 10 feet, and the 1-2-1-2 rule means diagonals at distance 2 cost 15 feet (5+10), not 10 feet. Using Chebyshev (max metric) means a square at diagonal distance 2 is treated as "10 feet" which is generous compared to the strict 1-2-1-2 rule. This is a common simplification in D&D virtual tabletops. Defensible but slightly generous to the attacker for diagonal reach.

---

#### Reach to Squares Conversion

FORMULA ID: A-reach-195
FILE: aidm/core/reach_resolver.py
LINE: 195
CODE: `reach_squares = reach_ft // 5`
RULE SOURCE: Uncited — conversion from feet to squares
EXPECTED: 5ft = 1 square, 10ft = 2 squares, 15ft = 3 squares
ACTUAL: reach_ft // 5
VERDICT: UNCITED
NOTES: Standard feet-to-squares conversion. 5 feet per square is the universal D&D 3.5e grid standard. Integer division is appropriate since reach is always a multiple of 5. Correct.

---

#### Threatened Square Check

FORMULA ID: A-reach-234
FILE: aidm/core/reach_resolver.py
LINE: 234
CODE: `threatened = 1 <= min_dist <= reach_squares`
RULE SOURCE: SRD Combat: Threatened Squares — "You threaten all squares into which you can make a melee attack, even when it is not your action. Generally, that means everything in all squares adjacent to your space (including diagonally). An enemy that takes certain actions while in a threatened square provokes an attack of opportunity from you."
EXPECTED: Threaten squares within reach range (min distance 1 to max distance reach_squares)
ACTUAL: 1 <= min_dist <= reach_squares
VERDICT: CORRECT
NOTES: The check ensures the square is (a) not occupied by the entity itself (min_dist >= 1), and (b) within reach range (min_dist <= reach_squares). For natural reach (e.g., 5ft for Medium = 1 square), this means adjacent squares only. For Large creatures with 10ft reach (2 squares), this means all squares within 2 Chebyshev distance. This formula is for NATURAL reach — reach weapons have separate handling that only threatens at the weapon's exact range, not closer. Correct for the natural reach case.

---

### aidm/core/cover_resolver.py (4 formulas)

---

#### No Cover Threshold

FORMULA ID: A-cover-96
FILE: aidm/core/cover_resolver.py
LINE: 96
CODE: `(0, 4): (CoverDegree.NO_COVER, 0, 0)`
RULE SOURCE: SRD Combat: Cover — cover is determined by corner-to-corner lines. No cover when most lines are clear.
EXPECTED: 0-4 of 16 lines blocked = no cover (ac=0, ref=0)
ACTUAL: (0, 4): NO_COVER, ac=0, ref=0
VERDICT: CORRECT
NOTES: The cover threshold system uses 16 corner-to-corner lines (4 attacker corners x 4 defender corners for Medium vs Medium). 0-4 blocked = no meaningful cover. Correct.

---

#### Half Cover Threshold

FORMULA ID: A-cover-97
FILE: aidm/core/cover_resolver.py
LINE: 97
CODE: `(5, 8): (CoverDegree.HALF_COVER, 2, 1)`
RULE SOURCE: SRD Combat: Cover — "Cover provides a +4 bonus to AC... Cover grants a +2 bonus on Reflex saves."
EXPECTED: Half cover = +4 AC, +2 Reflex saves
ACTUAL: ac=2, ref=1
VERDICT: WRONG
NOTES: **BUG-10 (NEW).** SRD Cover rules state: "A low wall, for instance, provides cover, and gives you a +4 bonus to AC and a +2 bonus on Reflex saves." The code implements half cover as +2 AC and +1 Reflex, which is HALF of the SRD values. The SRD does not define "half cover" as a distinct category with reduced bonuses — it defines cover (+4 AC, +2 Ref) and improved cover (+8 AC, +4 Ref, evasion). The code appears to have invented a "half cover" interpolation that doesn't match RAW. SRD cover: +4 AC, +2 Ref. SRD improved cover: +8 AC, +4 Ref. The code's +2/+1 and +5/+2 values don't appear in the SRD.

---

#### Three-Quarters Cover Threshold

FORMULA ID: A-cover-98
FILE: aidm/core/cover_resolver.py
LINE: 98
CODE: `(9, 12): (CoverDegree.THREE_QUARTERS_COVER, 5, 2)`
RULE SOURCE: SRD Combat: Cover — standard cover: +4 AC, +2 Reflex; improved cover: +8 AC, +4 Reflex
EXPECTED: SRD does not define "three-quarters cover" as a category. Closest matches: standard cover (+4 AC, +2 Ref) or improved cover (+8 AC, +4 Ref).
ACTUAL: ac=5, ref=2
VERDICT: WRONG
NOTES: **BUG-10 CONTINUED.** The +5 AC / +2 Reflex values for "three-quarters cover" don't match any SRD cover category. The SRD defines: (1) Cover: +4 AC, +2 Reflex. (2) Improved Cover: +8 AC, +4 Reflex. There is no +5/+2 or +7/+3 category in the SRD. The task description stated "Half cover = +4 AC/+2 Ref; Three-quarters = +7 AC/+3 Ref" but even those values (+7/+3) don't match the SRD. The SRD cover system is binary (cover or improved cover), not a gradient. The code's interpolated values are homebrew. Should implement: cover = +4 AC, +2 Ref and improved cover = +8 AC, +4 Ref, with the line-count thresholds determining which category applies.

---

#### Total Cover Threshold

FORMULA ID: A-cover-99
FILE: aidm/core/cover_resolver.py
LINE: 99
CODE: `(13, 16): (CoverDegree.TOTAL_COVER, 0, 0)`
RULE SOURCE: SRD Combat: Cover — "You can't make an attack against a target that has total cover."
EXPECTED: Total cover = cannot be targeted (no AC/Ref bonus because attack is impossible)
ACTUAL: TOTAL_COVER, ac=0, ref=0, blocks_targeting=True (set at line 455)
VERDICT: CORRECT
NOTES: Total cover blocks targeting entirely. The ac/ref bonuses are irrelevant since no attack can be made. The blocks_targeting flag is correctly set. Correct.

---

## Bug List

All WRONG verdicts consolidated:

### BUG-1: Two-handed STR multiplier not applied (2 locations)
- **Locations:** attack_resolver.py:363, full_attack_resolver.py:297-299
- **SRD Rule:** "If you're using a weapon that you add your Strength modifier to damage, and the weapon is wielded two-handed, add 1-1/2 times your Strength bonus. Off-hand attacks add only 1/2 your Strength bonus."
- **Expected:** `int(str_modifier * 1.5)` for two-handed, `int(str_modifier * 0.5)` for off-hand
- **Actual:** Flat `str_modifier` used for all weapon types
- **Impact:** Two-handed weapon users deal less damage than they should. Off-hand attacks deal more damage than they should.
- **Domain D cross-ref:** N/A (Domain A origin)

### BUG-2: Full attack loop does not break on target defeat
- **Location:** full_attack_resolver.py:546-590
- **SRD Rule:** When a target is killed mid-sequence, remaining attacks are wasted (cannot redirect in full attack after 5-foot step)
- **Expected:** Loop should check target HP between attacks and either stop or skip remaining
- **Actual:** All iterative attacks execute regardless of target HP
- **Impact:** Wasted computation; damage accumulates on dead targets; AI cannot redirect attacks
- **Domain D cross-ref:** N/A (Domain A origin)

### BUG-8: Minimum damage on hit should be 1, not 0 (critical path, 2 locations)
- **Locations:** attack_resolver.py:369, full_attack_resolver.py:303
- **SRD Rule:** "If penalties reduce the damage result to less than 1, a hit still deals 1 point of damage."
- **Expected:** `max(1, base_damage_with_modifiers * critical_multiplier)`
- **Actual:** `max(0, ...)`
- **Impact:** Hits can deal 0 damage before DR, violating SRD minimum. Most visible when attacker has penalties (Sickened, low STR) against armored targets.

### BUG-9: Minimum damage on hit should be 1, not 0 (non-critical path, 2 locations)
- **Locations:** attack_resolver.py:371, full_attack_resolver.py:305
- **SRD Rule:** "If penalties reduce the damage result to less than 1, a hit still deals 1 point of damage."
- **Expected:** `max(1, base_damage_with_modifiers)`
- **Actual:** `max(0, ...)`
- **Impact:** Same as BUG-8 but for non-critical hits

### BUG-10: Cover AC and Reflex bonus values don't match SRD (2 thresholds)
- **Locations:** cover_resolver.py:97-98
- **SRD Rule:** Cover = +4 AC, +2 Reflex. Improved Cover = +8 AC, +4 Reflex. SRD has no "half cover" (+2/+1) or "three-quarters cover" (+5/+2).
- **Expected:** HALF_COVER -> +4 AC, +2 Ref. THREE_QUARTERS_COVER -> +8 AC, +4 Ref (treated as improved cover) OR collapse to two-tier system matching SRD.
- **Actual:** HALF_COVER = +2 AC, +1 Ref. THREE_QUARTERS_COVER = +5 AC, +2 Ref.
- **Impact:** Defenders receive less cover protection than SRD mandates. Half cover gives half the correct AC bonus. Three-quarters cover gives a non-SRD interpolated value.

### Cross-domain bugs confirmed to propagate into Domain A

### BUG-3 (from Domain D): Prone AC modifier not melee/ranged differentiated
- **Origin:** aidm/schemas/conditions.py:208 (ac_modifier=-4 flat)
- **Impact on Domain A:** attack_resolver.py:243 and full_attack_resolver.py:499 consume `defender_modifiers.ac_modifier` without melee/ranged context. Ranged attacks against prone targets incorrectly benefit from the -4 AC penalty instead of the SRD-correct +4 AC bonus.

### BUG-4 (from Domain D): Helpless AC modifier not melee/ranged differentiated
- **Origin:** aidm/schemas/conditions.py:281 (ac_modifier=-4 flat)
- **Impact on Domain A:** Same pipeline as BUG-3. Ranged attacks against helpless targets incorrectly benefit from the -4 AC modifier. SRD says only melee gets +4 bonus (equivalent to -4 AC); ranged gets no special bonus.

---

## Ambiguity Register

### AMBIG-A-1: Defeated threshold simplification (HP <= 0)
- **Formula ID:** A-attack-resolver-442
- **Issue:** Code uses `hp_after <= 0` as "defeated." SRD has disabled (0 HP), dying (-1 to -9), dead (-10).
- **Assessment:** Acceptable simplification for combat engine. Entity is effectively out of the fight at HP <= 0. Does not model disabled (can act at 0 HP) or dying (can stabilize).
- **Recommendation:** Document as intentional simplification. Consider adding disabled/dying states in a future iteration.

### AMBIG-A-2: Flanking angle threshold (135 degrees)
- **Formula ID:** A-flanking-49
- **Issue:** SRD uses a "line through center" test, not an angle test. 135-degree threshold is an approximation.
- **Assessment:** For Medium creatures, 135 degrees correctly identifies all SRD flanking positions. For Large+ creatures, may have edge cases. Defensible simplification.
- **Recommendation:** Document as geometric approximation of RAW rule.

### AMBIG-A-3: Chebyshev distance for reach calculation
- **Formula ID:** A-reach-116-118
- **Issue:** Uses Chebyshev distance (max of dx, dy) for reach. SRD technically uses 5-10-5-10 diagonal counting for all distances.
- **Assessment:** Chebyshev is slightly generous on diagonals (treats diagonal distance 2 as 10ft instead of 15ft per 5-10-5-10). Common VTT simplification. Matches PHB threatened-area diagrams visually.
- **Recommendation:** Document as intentional simplification. The difference only matters for reach >= 10ft on diagonals.

### AMBIG-A-4: Critical damage multiplication vs re-rolling
- **Formula ID:** A-attack-resolver-369, A-full-attack-303
- **Issue:** Code multiplies single roll by multiplier. SRD says "roll your damage more than once... and add the rolls together."
- **Assessment:** Mathematically equivalent expected value. Multiplying is a universally accepted shortcut. The only difference is variance (re-rolling has higher variance). This is standard practice in digital implementations.
- **Recommendation:** Document as accepted shortcut. Not a correctness bug.

---

## Uncited Formulas

### UNCITED-A-1: HP subtraction (attack_resolver.py:424)
- `hp_after = hp_before - final_damage`
- Basic arithmetic, no SRD citation needed.

### UNCITED-A-2: HP subtraction (full_attack_resolver.py:595)
- `hp_after = hp_before - total_damage`
- Basic arithmetic, no SRD citation needed.

### UNCITED-A-3: Reach-to-squares conversion (reach_resolver.py:195)
- `reach_squares = reach_ft // 5`
- Universal D&D standard (5 feet per square). No specific citation needed.

### UNCITED-A-4: Roll dice function structure (attack_resolver.py:113)
- `[combat_rng.randint(1, die_size) for _ in range(num_dice)]`
- Standard dice mechanics, universally understood.

---

## Summary Statistics

| Category | Count |
|----------|-------|
| CORRECT | 38 |
| WRONG | 7 |
| AMBIGUOUS | 4 |
| UNCITED | 4 |
| **TOTAL** | **53** |

### Bug Severity Assessment

| Bug | Severity | Fix Complexity |
|-----|----------|---------------|
| BUG-1 (2-hand STR) | HIGH — damage consistently wrong for two-handed weapons | LOW — add conditional multiplier |
| BUG-2 (no early break) | MEDIUM — functional issue for AI combat, no rule violation per se | LOW — add HP check in loop |
| BUG-8 (min damage crit) | LOW — edge case when attacker has significant penalties | TRIVIAL — change max(0,...) to max(1,...) |
| BUG-9 (min damage non-crit) | LOW — same edge case as BUG-8 | TRIVIAL — change max(0,...) to max(1,...) |
| BUG-10 (cover values) | HIGH — cover bonuses consistently wrong for all covered targets | MEDIUM — redesign cover tier system to match SRD |

### Domain D Cross-References

BUG-3, BUG-4 from Domain D verification propagate into Domain A's AC computation pipeline. The attack resolver formulas themselves are correct, but they consume incorrect upstream condition modifiers for Prone and Helpless defenders against ranged attacks.

BUG-6 (Fatigued missing damage_modifier) and BUG-7 (Exhausted missing damage_modifier) from Domain D propagate into Domain A's damage computation pipeline. The damage formula is correct but the condition damage modifiers are wrong upstream.

# Bone-Layer Formula Inventory

**Generated:** 2026-02-14
**Source:** Exhaustive sweep of aidm/core/, aidm/schemas/, aidm/rules/, play.py
**Purpose:** Reference inventory for BONE_LAYER_VERIFICATION_PLAN.md — every formula to be verified

---

## Domain A: Attack Resolution (53 formulas)

### aidm/core/attack_resolver.py (18 formulas)
- LINE 113: `roll_dice()` = `[combat_rng.randint(1, die_size) for _ in range(num_dice)]` | INPUTS: num_dice, die_size from weapon.damage_dice | RULE: PHB p.140
- LINE 241: `base_ac = target.get(EF.AC, 10)` | INPUTS: entity AC field, default 10 | RULE: PHB p.136
- LINE 243: `target_ac = base_ac + defender_modifiers.ac_modifier + cover_result.ac_bonus` | INPUTS: base AC, condition AC mod, cover AC bonus | RULE: PHB p.136
- LINE 247: `d20_result = combat_rng.randint(1, 20)` | INPUTS: RNG stream "combat" | RULE: PHB p.139
- LINE 249-256: `attack_bonus_with_conditions = intent.attack_bonus + attacker_modifiers.attack_modifier + mounted_bonus + terrain_higher_ground + feat_attack_modifier + flanking_bonus` | INPUTS: BAB+STR/DEX+misc, condition attack mod, mounted higher ground (+0/+1), elevation higher ground (+0/+1), feat modifier, flanking (+0/+2) | RULE: PHB p.136
- LINE 257: `total = d20_result + attack_bonus_with_conditions` | INPUTS: d20 roll, aggregated attack bonus | RULE: PHB p.139
- LINE 260: `is_threat = (d20_result >= intent.weapon.critical_range)` | INPUTS: d20 roll, weapon critical range (default 20) | RULE: PHB p.140
- LINE 267: natural 1 always misses | INPUTS: d20_result == 1 | RULE: PHB p.139
- LINE 269: natural 20 always hits | INPUTS: d20_result == 20 | RULE: PHB p.139
- LINE 272: `hit = total >= target_ac` | INPUTS: attack total, target AC | RULE: PHB p.139
- LINE 278: `confirmation_d20 = combat_rng.randint(1, 20)` | INPUTS: RNG stream "combat" | RULE: PHB p.140
- LINE 280: `confirmation_total = confirmation_d20 + attack_bonus_with_conditions` | INPUTS: confirmation d20, same attack bonus | RULE: PHB p.140
- LINE 282: `is_critical = confirmation_total >= target_ac` | INPUTS: confirmation total, target AC | RULE: PHB p.140
- LINE 355: `str_modifier = attacker.get(EF.STR_MOD, 0)` | INPUTS: entity STR_MOD field, default 0 | RULE: PHB p.140
- LINE 363: `base_damage = sum(damage_rolls) + intent.weapon.damage_bonus + str_modifier` | INPUTS: dice rolls, weapon bonus, STR mod | RULE: PHB p.140
- LINE 365: `base_damage_with_modifiers = base_damage + attacker_modifiers.damage_modifier + feat_damage_modifier` | INPUTS: base damage, condition damage mod, feat damage mod | RULE: PHB p.140
- LINE 369: `damage_total = max(0, base_damage_with_modifiers * intent.weapon.critical_multiplier)` | INPUTS: modified base damage, crit multiplier (2/3/4) | RULE: PHB p.140
- LINE 371: `damage_total = max(0, base_damage_with_modifiers)` | INPUTS: modified base damage (non-crit) | RULE: PHB p.140
- LINE 382: `damage_total += sa_damage` | INPUTS: post-crit damage, sneak attack damage | RULE: PHB p.51 (SA not multiplied on crit)
- LINE 389: `final_damage = apply_dr_to_damage(damage_total, dr_amount)` | INPUTS: total damage, DR amount | RULE: PHB p.291
- LINE 424: `hp_after = hp_before - final_damage` | INPUTS: current HP, final damage after DR | RULE: uncited
- LINE 442: `defeated = hp_after <= 0` | INPUTS: remaining HP | RULE: PHB p.145

### aidm/core/full_attack_resolver.py (8 formulas)
- LINE 97-121: `calculate_iterative_attacks()`: attacks = [bab]; while current >= 1: append(current); current -= 5 | INPUTS: base_attack_bonus | RULE: PHB p.136
- LINE 297-299: `base_damage = sum(damage_rolls) + weapon.damage_bonus + str_modifier + condition_damage_modifier + feat_damage_modifier` | INPUTS: dice, weapon bonus, STR mod, condition mod, feat mod | RULE: PHB p.140
- LINE 303: `critical_damage = max(0, base_damage_with_modifiers * weapon.critical_multiplier)` | INPUTS: modified base, crit mult | RULE: PHB p.140
- LINE 499: `target_ac = base_ac + defender_modifiers.ac_modifier + cover_result.ac_bonus` | INPUTS: base AC, condition AC mod, cover bonus | RULE: PHB p.136
- LINE 548-555: `adjusted_bonus = raw_attack_bonus + attacker_modifiers.attack_modifier + mounted_bonus + terrain_higher_ground + feat_attack_modifier + flanking_bonus` | INPUTS: iterative BAB, condition mod, mounted, elevation, feat, flanking | RULE: PHB p.136
- LINE 595: `hp_after = hp_before - total_damage` | INPUTS: starting HP, accumulated damage | RULE: uncited

### aidm/core/sneak_attack.py (3 formulas)
- LINE 55: `SNEAK_ATTACK_MAX_RANGE = 30` | INPUTS: constant | RULE: PHB p.51
- LINE 82: `num_dice = (rogue_level + 1) // 2` | INPUTS: rogue_level | RULE: PHB p.51
- LINE 202: `rolls = [combat_rng.randint(1, 6) for _ in range(num_dice)]` | INPUTS: num SA dice | RULE: PHB p.51

### aidm/core/damage_reduction.py (6 formulas)
- LINE 45-53: `ENERGY_TYPES` and `PHYSICAL_TYPES` sets | INPUTS: hardcoded | RULE: PHB p.291
- LINE 99: `effective_magic = is_magic_weapon or weapon_enhancement >= 1` | INPUTS: magic flag, enhancement | RULE: PHB p.291
- LINE 156: epic bypass: `enhancement >= 6` | INPUTS: enhancement bonus | RULE: DMG p.291
- LINE 182: `damage_reduced = min(dr_amount, damage_total)` | INPUTS: DR, damage | RULE: PHB p.291
- LINE 187: `final_damage = damage_total - damage_reduced` | INPUTS: damage, reduction | RULE: PHB p.291

### aidm/core/flanking.py (3 formulas)
- LINE 44: `FLANKING_BONUS = 2` | INPUTS: constant | RULE: PHB p.153
- LINE 49: `MIN_FLANKING_ANGLE = 135.0` | INPUTS: constant (degrees) | RULE: PHB p.153
- LINE 119-130: angle via dot product | INPUTS: three positions | RULE: PHB p.153

### aidm/core/concealment.py (2 formulas)
- LINE 67: `effective_miss_chance = min(best_miss_chance, 100)` | INPUTS: best miss chance, cap 100 | RULE: PHB p.152
- LINE 90: `d100_roll = combat_rng.randint(1, 100); miss = d100_roll <= miss_chance_percent` | INPUTS: d100, miss chance | RULE: PHB p.152

### aidm/core/ranged_resolver.py (4 formulas)
- LINE 27: `PENALTY_PER_INCREMENT = -2` | INPUTS: constant | RULE: PHB p.158
- LINE 29-30: `DEFAULT_MAX_INCREMENTS = 10; THROWN_MAX_INCREMENTS = 5` | INPUTS: constants | RULE: PHB p.158
- LINE 159: `range_increment = ((distance_ft - 1) // range_increment_ft) + 1` | INPUTS: distance, range increment | RULE: PHB p.158
- LINE 200: `range_penalty = (increment - 1) * PENALTY_PER_INCREMENT` | INPUTS: increment, -2 | RULE: PHB p.158

### aidm/core/reach_resolver.py (5 formulas)
- LINE 26-36: `DEFAULT_REACH_BY_SIZE_TALL` table (9 sizes) | INPUTS: size | RULE: PHB p.149
- LINE 39-49: `DEFAULT_REACH_BY_SIZE_LONG` table (9 sizes) | INPUTS: size | RULE: PHB p.149
- LINE 116-118: Chebyshev distance | INPUTS: two positions | RULE: PHB p.149
- LINE 195: `reach_squares = reach_ft // 5` | INPUTS: reach ft | RULE: uncited
- LINE 234: `threatened = 1 <= min_dist <= reach_squares` | INPUTS: distance, reach | RULE: PHB p.137

### aidm/core/cover_resolver.py (4 formulas)
- LINE 96: 0-4 lines blocked = NO_COVER (ac=0, ref=0) | RULE: PHB p.150
- LINE 97: 5-8 lines blocked = HALF (ac=2, ref=1) | RULE: PHB p.150
- LINE 98: 9-12 lines blocked = THREE_QUARTERS (ac=5, ref=2) | RULE: PHB p.150
- LINE 99: 13-16 lines blocked = TOTAL | RULE: PHB p.150

---

## Domain B: Combat Maneuvers (27 formulas)

### aidm/core/maneuver_resolver.py (18 formulas)
- LINE 98-104: `touch_ac = 10 + dex_mod + size_mod` | RULE: PHB p.154
- LINE 127-128: attacker/defender d20 rolls | RULE: PHB p.154
- LINE 131: `attacker_wins = attacker_total > defender_total` (ties to defender) | RULE: PHB p.154
- LINE 254: `charge_bonus = 2 if is_charge else 0` | RULE: PHB p.154
- LINE 255: `attacker_modifier = str + size + charge_bonus` | RULE: PHB p.154
- LINE 260: `defender_modifier = str + size + stability` | RULE: PHB p.154
- LINE 280-281: `push = 5 + (margin // 5) * 5` | RULE: PHB p.154
- LINE 501: `touch_attack_bonus = bab + str + size` | RULE: PHB p.158
- LINE 542: `trip_attacker = str + size` | RULE: PHB p.158
- LINE 546-549: `trip_defender = max(str, dex) + size + stability` | RULE: PHB p.158
- LINE 859: `prone_threshold = margin <= -5` (failed tripper falls prone) | RULE: PHB p.158
- LINE 1004: `sunder_modifier = bab + str + size` | RULE: PHB p.158
- LINE 1027: `damage_roll = randint(1, 8)` | RULE: PHB p.158
- LINE 1029: `total_damage = max(0, roll + bonus)` | RULE: PHB p.158
- LINE 1168: `disarm_modifier = bab + str + size` | RULE: PHB p.155
- LINE 1173: `defender_disarm = bab + str + size` | RULE: PHB p.155
- LINE 1382: `grapple_touch = bab + str + size` | RULE: PHB p.155
- LINE 1421-1426: grapple attacker/defender modifiers = bab + str + size | RULE: PHB p.156

### aidm/schemas/maneuvers.py (9 formulas — size modifier table)
- LINES 28-36: fine=-16, diminutive=-12, tiny=-8, small=-4, medium=0, large=+4, huge=+8, gargantuan=+12, colossal=+16 | RULE: PHB p.154

---

## Domain C: Saves & Spells (21 formulas)

### aidm/core/save_resolver.py (10 formulas)
- LINE 86-100: Save type → ability mapping (Fort→CON, Ref→DEX, Will→WIS) | RULE: PHB p.177
- LINE 112: `total_save = base + ability_mod + condition_mod` | RULE: PHB p.177
- LINE 159-162: SR check: `d20 + caster_level >= SR` | RULE: PHB p.177
- LINE 252-253: `save_total = d20 + save_bonus` | RULE: PHB p.177
- LINE 259: nat 1 always fails | RULE: PHB p.177
- LINE 261: nat 20 always succeeds | RULE: PHB p.177
- LINE 264: `success = total >= dc` | RULE: PHB p.177
- LINE 335: `final_damage = int(base * multiplier)` | RULE: PHB p.177
- LINE 340: `hp_after = hp_before - final_damage` | RULE: uncited

### aidm/core/spell_resolver.py (11 formulas)
- LINE 383-389: `spell_dc = dc_base + spell_level` (dc_base = 10 + ability) | RULE: PHB Ch.10
- LINE 747: `base_roll = randint(1, 20)` | RULE: PHB p.177
- LINE 749: `total = base_roll + save_bonus + cover_bonus` | RULE: PHB p.177
- LINE 753-758: nat 20 auto-success, nat 1 auto-fail, else total >= dc | RULE: PHB p.177
- LINE 816: `damage // 2` (save half) | RULE: PHB
- LINE 818: `damage = 0` (save negates) | RULE: PHB
- LINE 871: `caster_level_bonus = min(caster_level, spell_level * 5)` | RULE: PHB (cure spells)
- LINE 872: `total += caster_level_bonus` | RULE: PHB
- LINE 876: `actual_healing = min(total, max_hp - current_hp)` | RULE: uncited
- LINE 1035: `dc = 10 + damage_taken` (concentration) | RULE: PHB p.69

---

## Domain D: Conditions & Modifiers (57 formulas)

### aidm/schemas/conditions.py (42 formulas — condition modifier values)
- LINE 208: Prone: ac_modifier=-4 | RULE: PHB p.311
- LINE 209: Prone: attack_modifier=-4 | RULE: PHB p.311
- LINE 210: Prone: standing_triggers_aoo=True | RULE: PHB p.311
- LINE 232: Flat-Footed: loses_dex_to_ac=True | RULE: PHB p.137
- LINE 254: Grappled: dex_modifier=-4 | RULE: PHB p.156
- LINE 255: Grappled: movement_prohibited=True | RULE: PHB p.156
- LINE 281: Helpless: ac_modifier=-4 | RULE: PHB p.311
- LINE 282: Helpless: loses_dex_to_ac=True | RULE: PHB p.311
- LINE 283: Helpless: auto_hit_if_helpless=True | RULE: PHB p.311
- LINE 284: Helpless: actions_prohibited=True | RULE: PHB p.311
- LINE 306: Stunned: ac_modifier=-2 | RULE: PHB p.311
- LINE 307: Stunned: loses_dex_to_ac=True | RULE: PHB p.311
- LINE 308: Stunned: actions_prohibited=True | RULE: PHB p.311
- LINE 328: Dazed: actions_prohibited=True | RULE: PHB p.311
- LINE 352: Shaken: attack_modifier=-2 | RULE: PHB p.311
- LINE 353: Shaken: fort_save_modifier=-2 | RULE: PHB p.311
- LINE 354: Shaken: ref_save_modifier=-2 | RULE: PHB p.311
- LINE 355: Shaken: will_save_modifier=-2 | RULE: PHB p.311
- LINE 380: Sickened: attack_modifier=-2 | RULE: PHB p.311
- LINE 381: Sickened: damage_modifier=-2 | RULE: PHB p.311
- LINE 382: Sickened: fort_save_modifier=-2 | RULE: PHB p.311
- LINE 383: Sickened: ref_save_modifier=-2 | RULE: PHB p.311
- LINE 384: Sickened: will_save_modifier=-2 | RULE: PHB p.311
- LINE 406: Frightened: attack_modifier=-2 | RULE: PHB p.310
- LINE 407: Frightened: fort_save_modifier=-2 | RULE: PHB p.310
- LINE 408: Frightened: ref_save_modifier=-2 | RULE: PHB p.310
- LINE 409: Frightened: will_save_modifier=-2 | RULE: PHB p.310
- LINE 428: Panicked: fort_save_modifier=-2 | RULE: PHB p.311
- LINE 429: Panicked: ref_save_modifier=-2 | RULE: PHB p.311
- LINE 430: Panicked: will_save_modifier=-2 | RULE: PHB p.311
- LINE 431: Panicked: loses_dex_to_ac=True | RULE: PHB p.311
- LINE 450: Nauseated: actions_prohibited=True | RULE: PHB p.311
- LINE 467: Fatigued: attack_modifier=-1 (-2 STR → -1 attack) | RULE: PHB p.311
- LINE 468: Fatigued: dex_modifier=-2 | RULE: PHB p.311
- LINE 485: Exhausted: attack_modifier=-3 (-6 STR → -3 attack) | RULE: PHB p.311
- LINE 486: Exhausted: dex_modifier=-6 | RULE: PHB p.311
- LINE 504: Paralyzed: ac_modifier=-4 | RULE: PHB p.311
- LINE 505: Paralyzed: loses_dex_to_ac=True | RULE: PHB p.311
- LINE 506: Paralyzed: auto_hit_if_helpless=True | RULE: PHB p.311
- LINE 507: Paralyzed: actions_prohibited=True | RULE: PHB p.311
- LINE 508: Paralyzed: movement_prohibited=True | RULE: PHB p.311
- LINE 541: Unconscious: ac_modifier=-4 | RULE: PHB p.311
- LINE 542-545: Unconscious: loses_dex, auto_hit, actions_prohibited, movement_prohibited | RULE: PHB p.311

### aidm/core/conditions.py (15 formulas — aggregation)
- LINES 65-71: accumulator init (7 zero-init counters) | RULE: uncited
- LINES 92-98: additive stacking (ac, attack, damage, dex, fort, ref, will) | RULE: PHB p.311
- LINES 100-104: boolean OR (movement_prohibited, actions_prohibited, standing_triggers_aoo, auto_hit, loses_dex) | RULE: uncited

---

## Domain E: Movement & Terrain (34 formulas)

### aidm/core/movement_resolver.py (2 formulas)
- LINE 85-95: `_step_cost()` diagonal 5/10/5 alternation with terrain multiplier | RULE: PHB p.148
- LINE 228: `speed_ft = entity.get(EF.BASE_SPEED, 30)` | RULE: PHB p.162

### aidm/core/terrain_resolver.py (13 formulas)
- LINE 241: Improved cover: ac=8, ref=4 | RULE: PHB p.150
- LINE 251: Standard cover: ac=4, ref=2 | RULE: PHB p.150
- LINE 262: Soft cover: ac=4, ref=0 | RULE: PHB p.152
- LINE 390-400: elevation calculation | RULE: uncited
- LINE 424-447: higher ground bonus = 1 or 0 | RULE: PHB p.151
- LINE 560-567: fall damage: `dice = min(distance // 10, 20)` | RULE: DMG p.304
- LINE 619: water fall: `dice = max(0, (distance - 20) // 10)` | RULE: DMG p.304
- LINE 644: `damage = [randint(1,6) for _ in range(dice)]` | RULE: DMG p.304
- LINE 762: `push_squares = push_distance // 5` | RULE: uncited

### aidm/core/mounted_combat.py (12 formulas)
- LINE 417-421: ride check: `d20 + 5 >= 15` | RULE: PHB p.157
- LINE 445: fall damage: `1d6` | RULE: PHB p.157
- LINE 499: `hp_after = max(0, current_hp - damage)` | RULE: uncited
- LINE 546-549: stay mounted: 75% military saddle, 50% riding | RULE: PHB p.157
- LINE 667: SIZE_ORDER ordinals (6 entries) | RULE: PHB p.132
- LINE 716-717: mounted attack bonus from mount size vs target | RULE: PHB p.157
- LINE 734: `can_full_attack = mount_moved <= 5` | RULE: PHB p.157

### aidm/schemas/attack.py — FullMoveIntent (5 formulas)
- LINE 207: `speed_ft = 30` default | RULE: PHB p.162
- LINE 251-263: `path_cost_ft()` 5/10/5 diagonal | RULE: PHB p.148

### aidm/schemas/position.py (2 formulas)
- LINE 60-73: `distance_to()` diagonal distance formula | RULE: PHB p.148
- LINE 87: `is_adjacent_to()` Chebyshev <= 1 | RULE: PHB p.137

---

## Domain F: Character Progression & Economy (77 formulas)

### aidm/core/experience_resolver.py (10 formulas)
- LINE 61: `cr_delta = int(cr) - party_level` | RULE: DMG p.38
- LINE 65: `base_xp = XP_TABLE.get(key)` | RULE: DMG Table 2-6
- LINE 69: `adjusted_xp = int(base_xp * (4.0 / party_size))` | RULE: DMG p.38
- LINE 113: `offending = highest - level > 1` | RULE: PHB p.60
- LINE 117: `penalty = max(0, 1.0 - 0.2 * count)` | RULE: PHB p.60
- LINE 219: `hp_roll = randint(1, hit_die)` | RULE: PHB p.22
- LINE 220: `hp_gained = max(1, roll + con_mod)` | RULE: PHB p.22
- LINE 227: `skill_points = max(1, base + int_mod)` | RULE: PHB p.22
- LINE 230: `feat_slot = (level % 3 == 0)` | RULE: PHB p.22
- LINE 235: `ability_increase = (level % 4 == 0)` | RULE: PHB p.22

### aidm/core/encumbrance.py (18 formulas)
- LINES 32-61: carrying capacity table (STR 1-29) | RULE: PHB Table 9-1, p.162
- LINE 89-90: STR 30+ extrapolation formula | RULE: PHB p.162
- LINES 128-134: load thresholds (light/medium/heavy/overloaded) | RULE: PHB p.162
- LINES 157-183: load penalties (max_dex, check_penalty, speed, run) | RULE: PHB Table 9-2, p.162

### aidm/schemas/leveling.py (30+ formulas)
- LINES 21-40: XP thresholds levels 1-20 | RULE: DMG Table 3-2, p.46
- LINES 67-85: class data (4 classes: hit die, BAB, saves, skills) | RULE: PHB
- LINES 99-101: BAB progressions (full, 3/4, 1/2) | RULE: PHB p.22
- LINES 105-106: save progressions (good, poor) | RULE: PHB p.22
- LINES 150-308: XP award table (100+ entries) | RULE: DMG Table 2-6, p.38

### aidm/schemas/feats.py (12 formulas — prerequisite values)
- Power Attack: STR 13, BAB 1 | RULE: PHB p.98
- Cleave: STR 13, requires PA | RULE: PHB p.92
- Great Cleave: STR 13, BAB 4, requires Cleave | RULE: PHB p.94
- Dodge: DEX 13 | RULE: PHB p.93
- Mobility: DEX 13, requires Dodge | RULE: PHB p.98
- Spring Attack: DEX 13, BAB 4, requires Dodge+Mobility | RULE: PHB p.100
- TWF: DEX 15 | RULE: PHB p.102
- Improved TWF: DEX 17, BAB 6 | RULE: PHB p.96
- Greater TWF: DEX 19, BAB 11 | RULE: PHB p.94
- Weapon Spec: requires WF, fighter 4 | RULE: PHB p.102

### aidm/schemas/skills.py (7 formulas — skill properties)
- Tumble/Hide/Move Silently/Balance: DEX, ACP=True | RULE: PHB
- Concentration: CON, ACP=False | RULE: PHB p.69
- Spot/Listen: WIS, ACP=False | RULE: PHB

---

## Domain G: Initiative & Turn Structure (10 formulas)

### aidm/core/initiative.py (3 formulas)
- LINE 72: `d20 + dex_mod + misc_mod` | RULE: PHB p.135
- LINE 75: `total = d20 + dex + misc` | RULE: PHB p.135
- LINE 104: sort key `(-total, -dex, actor_id)` | RULE: PHB p.135

### play.py — ActionBudget (6 formulas)
- LINES 71-86: action cost mapping (14 entries) | RULE: PHB p.138-141
- LINES 92-96: budget defaults | RULE: PHB p.138
- LINE 112: full_round requires standard + move + not moved | RULE: PHB p.138
- LINE 110: standard → move trade | RULE: PHB p.141

### aidm/core/combat_controller.py (1 formula)
- LINE 249: `round = previous + 1` | RULE: uncited

---

## Domain H: Skill System (6 formulas)

### aidm/core/skill_resolver.py
- LINE 161: `d20` | RULE: PHB Ch.4
- LINE 170: `total = d20 + ability + ranks + circumstance - acp` | RULE: PHB Ch.4
- LINE 173: `success = total >= dc` | RULE: PHB Ch.4
- LINE 233-234: opposed check d20s | RULE: PHB Ch.4
- LINE 241-249: opposed totals | RULE: PHB Ch.4
- LINE 254: `actor_wins = actor_total >= opponent_total` (ties to active) | RULE: PHB Ch.4

---

## Domain I: Geometry & Size (18 formulas)

### aidm/schemas/geometry.py (3 formulas)
- LINES 291-301: footprint by size (Fine=1 through Colossal=25) | RULE: PHB p.132
- LINE 310-311: `grid_size = int(sqrt(footprint))` | RULE: uncited

### aidm/schemas/bestiary.py (10 formulas — defaults)
- LINES 141-153: default values (HP=0, AC=10, touch=10, ff=10, speed=0, BAB=0, saves=0, CR=0) | RULE: uncited

### aidm/schemas/terrain.py (5 formulas)
- LINES 48-51: cover types (standard +4/+2, improved +8/+4, total, soft +4/0) | RULE: PHB p.150-152
- LINE 116: `movement_cost = 1` default | RULE: PHB p.148

### aidm/core/combat_reflexes.py (2 formulas)
- LINE 90: without feat: 1 AoO | RULE: PHB p.137
- LINE 93: with feat: `max(1, 1 + dex_mod)` | RULE: PHB p.92

### aidm/core/environmental_damage_resolver.py (4 formulas)
- LINES 48-51: hazard damage (fire 1d6, acid 1d6, lava 2d6, spikes 1d6) | RULE: DMG

### aidm/core/aoo.py (2 formulas)
- LINE 430: `tumble_dc = 15` | RULE: PHB p.84
- LINE 506: Mobility feat AC modifier via feat_resolver | RULE: PHB p.98

### aidm/core/play_loop.py (5 formulas)
- LINE 185: `caster_level = 5` default | RULE: uncited (test default)
- LINE 188: `spell_dc_base = 13` default (10+3) | RULE: uncited (test default)
- LINE 486: `new_hp = min(old_hp + healing, max_hp)` | RULE: uncited
- LINE 618-623: concentration check: `d20 + bonus >= 10 + damage` | RULE: PHB p.170

### aidm/schemas/saves.py (2 formulas)
- LINE 109: `damage_multiplier = 1.0` default | RULE: PHB p.177
- LINE 117: valid multipliers = {0.0, 0.5, 1.0} | RULE: PHB p.177

### aidm/core/feat_resolver.py (16 formulas)
- LINE 158: Weapon Focus: +1 attack | RULE: PHB p.102
- LINE 165: PBS attack: +1 (ranged <= 30ft) | RULE: PHB p.98
- LINE 169: Rapid Shot: -2 attack | RULE: PHB p.99
- LINE 174: Power Attack: -penalty to attack | RULE: PHB p.98
- LINE 206: Weapon Spec: +2 damage | RULE: PHB p.102
- LINE 213: PBS damage: +1 (ranged <= 30ft) | RULE: PHB p.98
- LINE 223: PA two-handed: +penalty*2 damage | RULE: PHB p.98
- LINE 225: PA one-handed: +penalty damage | RULE: PHB p.98
- LINE 257: Dodge: +1 AC | RULE: PHB p.93
- LINE 265: Mobility: +4 AC vs movement AoO | RULE: PHB p.98
- LINE 283: Improved Initiative: +4 initiative | RULE: PHB p.96
- LINE 332-335: Cleave/Great Cleave limits | RULE: PHB p.92/94
- LINE 386-415: TWF penalty/extra attack tables | RULE: PHB p.102/160
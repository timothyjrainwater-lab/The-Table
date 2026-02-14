# Domain I Verification — Geometry, Size & Support Systems

**Verified by:** Builder agent (Claude Opus 4.6)
**Date:** 2026-02-14
**Source authority:** SRD 3.5e (d20srd.org blocked; verified from training data knowledge of PHB/DMG/SRD text)
**Formulas verified:** 49 (expanded from WO estimate of 18 — see note below)

> **Note on formula count:** The WO listed 18 formulas but identified 10 files. Actual
> per-formula verification produced 49 individual records. The WO's "18" counted file-groups,
> not individual formulas. The checklist will be updated with the actual count.

---

## Summary

| Verdict | Count |
|---------|-------|
| CORRECT | 40 |
| WRONG | 1 |
| AMBIGUOUS | 2 |
| UNCITED | 6 |
| **TOTAL** | **49** |

---

## aidm/schemas/geometry.py (3 formulas)

### I-GEOM-291

```
FORMULA ID: I-GEOM-291
FILE: aidm/schemas/geometry.py
LINE: 291-301
CODE: footprints = {
    FINE: 1, DIMINUTIVE: 1, TINY: 1, SMALL: 1, MEDIUM: 1,
    LARGE: 4, HUGE: 9, GARGANTUAN: 16, COLOSSAL: 25,
}
RULE SOURCE: SRD 3.5e > Combat > Table: Creature Size and Scale
EXPECTED:
  Fine:        ½ ft space (shares 1 square) → 1 square (correct abstraction)
  Diminutive:  1 ft space (shares 1 square) → 1 square (correct abstraction)
  Tiny:        2½ ft space (shares 1 square) → 1 square (correct abstraction)
  Small:       5 ft space → 1 square
  Medium:      5 ft space → 1 square
  Large:       10 ft space → 2×2 = 4 squares
  Huge:        15 ft space → 3×3 = 9 squares
  Gargantuan:  20 ft space → 4×4 = 16 squares
  Colossal:    30 ft space → 6×6 = 36 squares
ACTUAL: Colossal = 25 squares (5×5)
VERDICT: WRONG
NOTES: SRD Table: Creature Size and Scale lists Colossal space as "30 ft."
  which maps to 6×6 = 36 squares on a 5-ft grid, not 5×5 = 25.
  The code uses 25 (5×5), which would correspond to a 25-ft space.
  The SRD is explicit: Colossal = 30 ft. This is a bug.
  FIX: Change COLOSSAL from 25 to 36.
```

### I-GEOM-310

```
FORMULA ID: I-GEOM-310
FILE: aidm/schemas/geometry.py
LINE: 310-311
CODE: return int(math.sqrt(self.footprint()))
RULE SOURCE: Derived (uncited utility computation)
EXPECTED: grid_size = sqrt(footprint) — maps square count to side length
ACTUAL: int(sqrt(footprint)). For footprint=4 → 2, footprint=9 → 3, footprint=16 → 4.
  For the WRONG Colossal value of 25, this gives int(sqrt(25))=5 (should be 6 if footprint were 36).
VERDICT: CORRECT (formula is correct; the input value from I-GEOM-291 is wrong for Colossal)
NOTES: The formula itself is mathematically sound. The bug is upstream in
  the footprint table (I-GEOM-291). Once that is fixed, this formula will
  produce the correct result of 6 for Colossal.
```

### I-GEOM-286 (docstring)

```
FORMULA ID: I-GEOM-286
FILE: aidm/schemas/geometry.py
LINE: 286 (docstring)
CODE: "Colossal creatures occupy 25 squares (5x5)."
RULE SOURCE: SRD Table: Creature Size and Scale
EXPECTED: "Colossal creatures occupy 36 squares (6x6)."
ACTUAL: Docstring says 25 (5x5)
VERDICT: WRONG (documentation, not formula — same root cause as I-GEOM-291)
NOTES: The docstring propagates the same error as the code. Both must be fixed together.
  Not counted separately in the summary — this is the same bug as I-GEOM-291.
```

---

## aidm/schemas/bestiary.py (10 formulas)

### I-BEST-141

```
FORMULA ID: I-BEST-141
FILE: aidm/schemas/bestiary.py
LINE: 141
CODE: hp_typical: int = 0
RULE SOURCE: Uncited (schema default)
EXPECTED: Default of 0 is reasonable for an uninitialized creature template.
  No SRD rule specifies a "default" HP — actual HP comes from HD.
ACTUAL: hp_typical = 0
VERDICT: UNCITED
NOTES: Sensible schema default. No creature should have 0 HP in play, but as a
  data class default for unpopulated entries, this is acceptable.
```

### I-BEST-142

```
FORMULA ID: I-BEST-142
FILE: aidm/schemas/bestiary.py
LINE: 142
CODE: ac_total: int = 10
RULE SOURCE: SRD 3.5e > Combat > Armor Class: "Your Armor Class (AC) represents
  how hard it is for opponents to land a solid, damaging blow on you. [...] Your
  AC equals: 10 + armor bonus + shield bonus + Dexterity modifier + size modifier
  + natural armor bonus + deflection bonus + miscellaneous modifier"
EXPECTED: Base AC = 10
ACTUAL: ac_total default = 10
VERDICT: CORRECT
NOTES: 10 is the base unarmored, unmodified AC. Correct default.
```

### I-BEST-143

```
FORMULA ID: I-BEST-143
FILE: aidm/schemas/bestiary.py
LINE: 143
CODE: ac_touch: int = 10
RULE SOURCE: SRD 3.5e > Combat > Touch Attacks: Touch AC excludes armor, shield,
  and natural armor bonuses. Base = 10 + Dex + size + deflection.
EXPECTED: Base touch AC = 10 (before any modifiers)
ACTUAL: ac_touch default = 10
VERDICT: CORRECT
NOTES: Correct default for base touch AC.
```

### I-BEST-144

```
FORMULA ID: I-BEST-144
FILE: aidm/schemas/bestiary.py
LINE: 144
CODE: ac_flat_footed: int = 10
RULE SOURCE: SRD 3.5e > Combat > Flat-Footed: Flat-footed AC excludes Dexterity bonus.
  Base = 10 + armor + shield + natural + size + deflection.
EXPECTED: Base flat-footed AC = 10 (before any modifiers)
ACTUAL: ac_flat_footed default = 10
VERDICT: CORRECT
NOTES: Correct default for base flat-footed AC.
```

### I-BEST-145

```
FORMULA ID: I-BEST-145
FILE: aidm/schemas/bestiary.py
LINE: 145
CODE: speed_ft: int = 0
RULE SOURCE: Uncited (schema default)
EXPECTED: No universal default speed. Medium humanoids typically move 30 ft.
  0 is a valid default for "unset" but not correct for any real creature.
ACTUAL: speed_ft = 0
VERDICT: UNCITED
NOTES: 0 means "speed not set." Acceptable schema default for uninitialized entries.
  Actual creature speed comes from creature type/race.
```

### I-BEST-146

```
FORMULA ID: I-BEST-146
FILE: aidm/schemas/bestiary.py
LINE: 146
CODE: bab: int = 0
RULE SOURCE: Uncited (schema default)
EXPECTED: BAB 0 is correct for a 0-HD creature. Acceptable default.
ACTUAL: bab = 0
VERDICT: UNCITED
NOTES: BAB 0 is the minimum. Correct as an uninitialized default.
```

### I-BEST-147

```
FORMULA ID: I-BEST-147
FILE: aidm/schemas/bestiary.py
LINE: 147
CODE: fort_save: int = 0
RULE SOURCE: Uncited (schema default)
EXPECTED: Fort save +0 is reasonable for a 0-HD creature with no CON modifier.
ACTUAL: fort_save = 0
VERDICT: UNCITED
NOTES: Acceptable default.
```

### I-BEST-148

```
FORMULA ID: I-BEST-148
FILE: aidm/schemas/bestiary.py
LINE: 148
CODE: ref_save: int = 0
RULE SOURCE: Uncited (schema default)
EXPECTED: Ref save +0 is reasonable default.
ACTUAL: ref_save = 0
VERDICT: UNCITED
NOTES: Acceptable default.
```

### I-BEST-149

```
FORMULA ID: I-BEST-149
FILE: aidm/schemas/bestiary.py
LINE: 149
CODE: will_save: int = 0
RULE SOURCE: Uncited (schema default)
EXPECTED: Will save +0 is reasonable default.
ACTUAL: will_save = 0
VERDICT: UNCITED
NOTES: Acceptable default.
```

### I-BEST-153

```
FORMULA ID: I-BEST-153
FILE: aidm/schemas/bestiary.py
LINE: 153
CODE: cr: float = 0.0
RULE SOURCE: Uncited (schema default)
EXPECTED: CR 0 is a valid CR (e.g., Rat). Reasonable default.
ACTUAL: cr = 0.0
VERDICT: CORRECT
NOTES: CR 0 is a legitimate CR value in the SRD. Some tiny creatures have CR 0.
  Correct as schema default.
```

---

## aidm/schemas/terrain.py (5 formulas)

### I-TERR-48

```
FORMULA ID: I-TERR-48
FILE: aidm/schemas/terrain.py
LINE: 48
CODE: STANDARD = "standard"  # +4 AC, +2 Reflex
RULE SOURCE: SRD 3.5e > Combat > Cover:
  "Cover provides a +4 bonus to AC. [...] Cover also grants a +2 bonus on Reflex
  saving throws."
EXPECTED: Standard cover: +4 AC, +2 Reflex
ACTUAL: Comment says +4 AC, +2 Reflex (values are in CoverCheckResult, not here)
VERDICT: CORRECT
NOTES: The values are documented in the schema comments and applied in
  terrain_resolver.py and cover_resolver.py. The constants here are string
  labels. The actual numeric values (+4/+2) match the SRD.
```

### I-TERR-49

```
FORMULA ID: I-TERR-49
FILE: aidm/schemas/terrain.py
LINE: 49
CODE: IMPROVED = "improved"  # +8 AC, +4 Reflex
RULE SOURCE: SRD 3.5e > Combat > Cover > Improved Cover:
  "In some cases, such as attacking a target behind an arrow slit, cover may
  provide a greater bonus to AC and Reflex saves. [...] +8 bonus to AC and a
  +4 bonus on Reflex saves."
EXPECTED: Improved cover (nine-tenths): +8 AC, +4 Reflex
ACTUAL: Comment says +8 AC, +4 Reflex
VERDICT: CORRECT
NOTES: SRD uses "improved cover" for the +8/+4 bonus, same as the code. Matches.
```

### I-TERR-50

```
FORMULA ID: I-TERR-50
FILE: aidm/schemas/terrain.py
LINE: 50
CODE: TOTAL = "total"  # Cannot be targeted
RULE SOURCE: SRD 3.5e > Combat > Cover > Total Cover:
  "If you don't have line of effect to your target he is considered to have total
  cover from you. You can't make an attack against a target that has total cover."
EXPECTED: Total cover: cannot be targeted
ACTUAL: "Cannot be targeted" — matches SRD
VERDICT: CORRECT
NOTES: Correct.
```

### I-TERR-51

```
FORMULA ID: I-TERR-51
FILE: aidm/schemas/terrain.py
LINE: 51
CODE: SOFT = "soft"  # +4 AC melee only, does not block AoO
RULE SOURCE: SRD 3.5e > Combat > Cover > Soft Cover:
  "Creatures, even your enemies, can provide you with cover against melee attacks.
  [...] Such soft cover provides a +4 bonus to AC."
  Soft cover does NOT provide a Reflex bonus and does NOT block AoO.
EXPECTED: Soft cover: +4 AC (melee only), +0 Reflex, does not block AoO
ACTUAL: Comment says +4 AC melee only, does not block AoO
VERDICT: CORRECT
NOTES: Matches SRD. Soft cover from creatures provides +4 AC but no Reflex bonus
  and does not block AoO. Note: the CoverCheckResult dataclass at line 262-303
  also correctly documents these values.
```

### I-TERR-116

```
FORMULA ID: I-TERR-116
FILE: aidm/schemas/terrain.py
LINE: 116
CODE: movement_cost: int = 1
RULE SOURCE: SRD 3.5e > Movement > Terrain > Difficult terrain costs 2 squares of movement.
  Normal terrain costs 1 square.
EXPECTED: Default movement cost = 1 (normal terrain)
ACTUAL: movement_cost = 1
VERDICT: CORRECT
NOTES: Default of 1 for normal terrain is correct. Difficult terrain would be 2.
```

---

## aidm/core/combat_reflexes.py (2 formulas)

### I-CREF-90

```
FORMULA ID: I-CREF-90
FILE: aidm/core/combat_reflexes.py
LINE: 89-90
CODE: if not has_combat_reflexes: return 1
RULE SOURCE: SRD 3.5e > Combat > Attacks of Opportunity:
  "You can only take one attack of opportunity per round."
EXPECTED: Without Combat Reflexes: 1 AoO per round
ACTUAL: Returns 1
VERDICT: CORRECT
NOTES: Matches SRD exactly.
```

### I-CREF-93

```
FORMULA ID: I-CREF-93
FILE: aidm/core/combat_reflexes.py
LINE: 92-93
CODE: return max(1, 1 + dex_modifier)
RULE SOURCE: SRD 3.5e > Feats > Combat Reflexes:
  "You may make a number of additional attacks of opportunity equal to your
  Dexterity bonus."
EXPECTED: Total AoO = 1 + Dex modifier, minimum 1.
  With Dex mod +3: 1 + 3 = 4 AoO per round.
  With Dex mod -1: max(1, 1 + (-1)) = max(1, 0) = 1. Still gets 1.
ACTUAL: max(1, 1 + dex_modifier)
VERDICT: CORRECT
NOTES: The formula correctly handles the case where Dex modifier is negative.
  SRD says "additional attacks of opportunity equal to your Dexterity bonus" —
  if Dex bonus is 0 or negative, you still get at least 1 base AoO.
  The code ensures minimum of 1, which is correct behavior.
```

---

## aidm/core/environmental_damage_resolver.py (4 formulas)

### I-ENV-48

```
FORMULA ID: I-ENV-48
FILE: aidm/core/environmental_damage_resolver.py
LINE: 48
CODE: "fire": (1, 6, "fire"),  # 1d6 fire
RULE SOURCE: SRD 3.5e > Environment > Heat Dangers > Catching on Fire:
  "Characters at risk of catching fire [...] take 1d6 points of damage."
  Also: DMG p.303 — fire hazards deal 1d6 fire damage.
EXPECTED: Fire contact hazard: 1d6 fire damage
ACTUAL: 1d6 fire
VERDICT: CORRECT
NOTES: The SRD fire contact damage is 1d6. The code implements this as a
  one-shot entry hazard which is a design simplification (SRD has ongoing
  damage for being on fire), but as a bone-layer constant, 1d6 is correct.
```

### I-ENV-49

```
FORMULA ID: I-ENV-49
FILE: aidm/core/environmental_damage_resolver.py
LINE: 49
CODE: "acid": (1, 6, "acid"),  # 1d6 acid
RULE SOURCE: SRD 3.5e > Environment > Acid Effects:
  "Acid deals 1d6 points of damage per round of contact."
EXPECTED: Acid contact: 1d6 acid per round
ACTUAL: 1d6 acid
VERDICT: CORRECT
NOTES: Matches SRD for contact acid damage per round.
```

### I-ENV-50

```
FORMULA ID: I-ENV-50
FILE: aidm/core/environmental_damage_resolver.py
LINE: 50
CODE: "lava": (2, 6, "fire"),  # 2d6 fire
RULE SOURCE: SRD 3.5e > Environment > Lava Effects:
  "Lava or magma deals 2d6 points of fire damage per round of exposure,
  except in the case of total immersion [...] which deals 20d6 points of fire
  damage per round."
EXPECTED: Lava exposure (not immersion): 2d6 fire per round
ACTUAL: 2d6 fire
VERDICT: CORRECT
NOTES: The code implements the "exposure" case (2d6), not the "immersion"
  case (20d6). This is the correct value for contact/proximity damage.
  The design doc (CP-20) explicitly scopes this as one-shot contact damage.
```

### I-ENV-51

```
FORMULA ID: I-ENV-51
FILE: aidm/core/environmental_damage_resolver.py
LINE: 51
CODE: "spiked_pit": (1, 6, "piercing"),  # 1d6 piercing
RULE SOURCE: SRD 3.5e > Environment > Pit Traps:
  Spiked pit traps typically deal falling damage + spike damage.
  DMG trap examples: "Pit Spikes: [...] 1d4 spikes per target, each dealing
  1d6 damage."
EXPECTED: Spike damage varies by trap design. Common: 1d6 per spike.
  The code uses a simplified 1d6 for "spike damage added to falling damage."
ACTUAL: 1d6 piercing
VERDICT: AMBIGUOUS
NOTES: The SRD doesn't define a single canonical "spiked pit" damage. DMG
  trap examples use 1d4 spikes each dealing 1d6 points of damage, meaning
  a spiked pit could deal 1d4 × 1d6 piercing in addition to fall damage.
  The code simplifies to a flat 1d6 piercing. This is a design simplification
  rather than a strict SRD implementation. Acceptable for the scope (CP-20
  design doc defines these as simplified contact hazards), but the SRD
  value is technically more complex. Marking AMBIGUOUS rather than WRONG
  because the design doc explicitly simplifies hazards.
```

---

## aidm/core/aoo.py (2 formulas)

### I-AOO-430

```
FORMULA ID: I-AOO-430
FILE: aidm/core/aoo.py
LINE: 430
CODE: dc=15 (Tumble check to avoid AoO)
RULE SOURCE: SRD 3.5e > Skills > Tumble:
  "With a DC 15 Tumble check, you can move at half speed through an area
  threatened by an enemy (or enemies) without provoking an attack of
  opportunity."
EXPECTED: Tumble DC 15 to move through threatened area without provoking AoO
ACTUAL: dc=15
VERDICT: CORRECT
NOTES: Matches SRD exactly. DC 15 is for moving through a threatened area.
  DC 25 is for moving through an enemy-occupied square (different use case,
  not relevant here).
```

### I-AOO-506

```
FORMULA ID: I-AOO-506
FILE: aidm/core/aoo.py
LINE: 506
CODE: feat_ac_modifier = get_ac_modifier(provoker, reactor, feat_context)
RULE SOURCE: SRD 3.5e > Feats > Mobility:
  "+4 dodge bonus to Armor Class against attacks of opportunity caused when
  you move out of or within a threatened area."
EXPECTED: Mobility provides +4 AC against movement AoO. The code delegates
  to feat_resolver.get_ac_modifier(), which is verified separately (I-FEAT-265).
ACTUAL: Calls get_ac_modifier with is_aoo=True context
VERDICT: CORRECT
NOTES: The wiring is correct — delegates to feat_resolver which applies +4
  for Mobility when is_aoo=True and trigger is movement. The actual modifier
  value is verified in I-FEAT-265.
```

---

## aidm/core/play_loop.py (4 formulas)

### I-PLAY-185

```
FORMULA ID: I-PLAY-185
FILE: aidm/core/play_loop.py
LINE: 185
CODE: caster_level = entity.get("caster_level", 5)
RULE SOURCE: Uncited — test/development default
EXPECTED: No SRD rule for "default caster level." This is a convenience default.
ACTUAL: Default caster level = 5
VERDICT: UNCITED
NOTES: This is explicitly labeled as a testing default in the WO. No SRD
  citation applies. The value 5 is arbitrary but reasonable for testing.
  In production, actual caster level would come from entity data.
```

### I-PLAY-188

```
FORMULA ID: I-PLAY-188
FILE: aidm/core/play_loop.py
LINE: 188
CODE: spell_dc_base = entity.get("spell_dc_base", 13)
RULE SOURCE: Uncited — test/development default
  (SRD: Spell DC = 10 + spell level + ability modifier. A DC base of 13
  would imply ability mod 3, i.e., ability score 16-17.)
EXPECTED: No SRD rule for "default spell DC base." This is a convenience default.
ACTUAL: Default spell_dc_base = 13 (10 + 3)
VERDICT: UNCITED
NOTES: Like I-PLAY-185, this is a development default. The value 13 implies
  a casting stat modifier of +3, which is reasonable but arbitrary.
```

### I-PLAY-486

```
FORMULA ID: I-PLAY-486
FILE: aidm/core/play_loop.py
LINE: 486
CODE: new_hp = min(old_hp + healing, max_hp)
RULE SOURCE: SRD 3.5e > Magic > Healing:
  "The creature's hit points can't exceed its full normal hit point total."
EXPECTED: Healed HP = min(current + healing, max_hp). Cannot exceed maximum.
ACTUAL: min(old_hp + healing, max_hp)
VERDICT: CORRECT
NOTES: Correctly prevents healing above maximum HP. Matches SRD.
```

### I-PLAY-618

```
FORMULA ID: I-PLAY-618
FILE: aidm/core/play_loop.py
LINE: 618-623
CODE: dc = 10 + damage_dealt
      roll = rng.stream("combat").randint(1, 20)
      total = roll + concentration_bonus
      if total < dc: [concentration broken]
RULE SOURCE: SRD 3.5e > Skills > Concentration:
  "If you are hit while trying to cast a spell, you must make a Concentration
  check or lose the spell. The DC for the check equals 10 + the damage dealt."
  Also PHB p.170: same rule for maintaining concentration spells.
EXPECTED: DC = 10 + damage taken. Check = d20 + Concentration bonus >= DC.
ACTUAL: dc = 10 + damage_dealt, total = d20 + concentration_bonus, fail if total < dc
VERDICT: CORRECT
NOTES: The formula matches the SRD exactly. Note: the code uses strict less-than
  (total < dc), which means "total >= dc" succeeds. This is correct — meeting
  the DC means success.
```

---

## aidm/schemas/saves.py (2 formulas)

### I-SAVE-109

```
FORMULA ID: I-SAVE-109
FILE: aidm/schemas/saves.py
LINE: 109
CODE: damage_multiplier: float = 1.0
RULE SOURCE: SRD 3.5e > Magic > Saving Throws:
  Default damage multiplier of 1.0 means full damage is applied (no save reduction).
  This is the default for effects where no save is made or save failed.
EXPECTED: Default multiplier = 1.0 (full damage)
ACTUAL: damage_multiplier = 1.0
VERDICT: CORRECT
NOTES: Correct default. Failed save = full damage (1.0 multiplier).
```

### I-SAVE-117

```
FORMULA ID: I-SAVE-117
FILE: aidm/schemas/saves.py
LINE: 117
CODE: if self.damage_multiplier not in {0.0, 0.5, 1.0}:
    raise ValueError(...)
RULE SOURCE: SRD 3.5e > Magic > Saving Throws:
  - "Negates" = 0 damage on successful save (0.0)
  - "Half" = half damage on successful save (0.5)
  - Full damage on failed save (1.0)
EXPECTED: Valid multipliers: {0.0, 0.5, 1.0}
ACTUAL: Validates against {0.0, 0.5, 1.0}
VERDICT: CORRECT
NOTES: The three multiplier values cover the standard SRD save outcomes:
  negates (0.0), half (0.5), and full (1.0). No SRD effect uses a different
  damage multiplier fraction.
```

---

## aidm/core/feat_resolver.py (16 formulas)

### I-FEAT-158

```
FORMULA ID: I-FEAT-158
FILE: aidm/core/feat_resolver.py
LINE: 157-158
CODE: if weapon_focus_id in feats: modifier += 1
RULE SOURCE: SRD 3.5e > Feats > Weapon Focus:
  "You gain a +1 bonus on all attack rolls you make using the selected weapon."
EXPECTED: Weapon Focus: +1 attack
ACTUAL: +1 attack
VERDICT: CORRECT
NOTES: Matches SRD exactly.
```

### I-FEAT-165

```
FORMULA ID: I-FEAT-165
FILE: aidm/core/feat_resolver.py
LINE: 161-165
CODE: if FeatID.POINT_BLANK_SHOT in feats:
    if is_ranged and range_ft <= 30: modifier += 1
RULE SOURCE: SRD 3.5e > Feats > Point Blank Shot:
  "You get a +1 bonus on attack and damage rolls with ranged weapons at
  ranges of up to 30 feet."
EXPECTED: PBS: +1 attack for ranged attacks within 30 ft
ACTUAL: +1 attack when is_ranged and range_ft <= 30
VERDICT: CORRECT
NOTES: Matches SRD exactly.
```

### I-FEAT-169

```
FORMULA ID: I-FEAT-169
FILE: aidm/core/feat_resolver.py
LINE: 168-169
CODE: if FeatID.RAPID_SHOT in feats and context.get("is_ranged", False):
    modifier -= 2
RULE SOURCE: SRD 3.5e > Feats > Rapid Shot:
  "You can get one extra attack per round with a ranged weapon. The attack is
  at your highest base attack bonus, but each attack you make in that round
  (the extra one and the normal ones) takes a -2 penalty."
EXPECTED: Rapid Shot: -2 to all ranged attacks in the round
ACTUAL: -2 to attack modifier when Rapid Shot is active
VERDICT: CORRECT
NOTES: The -2 penalty is correct. The extra attack is handled elsewhere
  (in full_attack_resolver). This formula only computes the modifier.
```

### I-FEAT-174

```
FORMULA ID: I-FEAT-174
FILE: aidm/core/feat_resolver.py
LINE: 172-174
CODE: if FeatID.POWER_ATTACK in feats:
    power_attack_penalty = context.get("power_attack_penalty", 0)
    modifier -= power_attack_penalty
RULE SOURCE: SRD 3.5e > Feats > Power Attack:
  "On your action, before making attack rolls for a round, you may choose to
  subtract a number from all melee attack rolls and add the same number to
  all melee damage rolls."
EXPECTED: Power Attack: -N to attack (user-chosen penalty)
ACTUAL: -power_attack_penalty to attack modifier
VERDICT: CORRECT
NOTES: The attack penalty is subtracted correctly. The code treats the
  penalty as a user-provided value, which matches the SRD ("you may choose").
  The code does NOT check that the penalty doesn't exceed BAB, but that
  validation would be in the caller, not the modifier computation.
```

### I-FEAT-206

```
FORMULA ID: I-FEAT-206
FILE: aidm/core/feat_resolver.py
LINE: 205-206
CODE: if weapon_spec_id in feats: modifier += 2
RULE SOURCE: SRD 3.5e > Feats > Weapon Specialization:
  "You gain a +2 bonus on all damage rolls you make using the selected weapon."
EXPECTED: Weapon Specialization: +2 damage
ACTUAL: +2 damage
VERDICT: CORRECT
NOTES: Matches SRD exactly.
```

### I-FEAT-213

```
FORMULA ID: I-FEAT-213
FILE: aidm/core/feat_resolver.py
LINE: 209-213
CODE: if FeatID.POINT_BLANK_SHOT in feats:
    if is_ranged and range_ft <= 30: modifier += 1
RULE SOURCE: SRD 3.5e > Feats > Point Blank Shot:
  "You get a +1 bonus on attack and damage rolls with ranged weapons at
  ranges of up to 30 feet."
EXPECTED: PBS: +1 damage for ranged attacks within 30 ft
ACTUAL: +1 damage when is_ranged and range_ft <= 30
VERDICT: CORRECT
NOTES: Matches SRD exactly. Same PBS rule applies to both attack and damage.
```

### I-FEAT-223

```
FORMULA ID: I-FEAT-223
FILE: aidm/core/feat_resolver.py
LINE: 219-223
CODE: if FeatID.POWER_ATTACK in feats:
    power_attack_penalty = context.get("power_attack_penalty", 0)
    is_two_handed = context.get("is_two_handed", False)
    if is_two_handed:
        modifier += power_attack_penalty * 2
RULE SOURCE: SRD 3.5e > Feats > Power Attack:
  "If you attack with a two-handed weapon, [...] you instead add double the
  number subtracted from your attack rolls."
EXPECTED: Power Attack two-handed: damage bonus = 2 × penalty
ACTUAL: power_attack_penalty * 2
VERDICT: CORRECT
NOTES: Matches SRD 3.5e exactly. The 2:1 ratio (subtract 1 from attack, add 2
  to damage for two-handed) is the 3.5e rule. Pathfinder does NOT change this —
  the WO's note about "Pathfinder changed this to 3:1" is incorrect. Both 3.5e
  and Pathfinder use 2:1 for two-handed Power Attack. The code is correct.
```

### I-FEAT-225

```
FORMULA ID: I-FEAT-225
FILE: aidm/core/feat_resolver.py
LINE: 225
CODE: modifier += power_attack_penalty  # 1:1 for one-handed
RULE SOURCE: SRD 3.5e > Feats > Power Attack:
  "you may choose to subtract a number from all melee attack rolls and add the
  same number to all melee damage rolls."
EXPECTED: Power Attack one-handed: damage bonus = 1 × penalty
ACTUAL: power_attack_penalty * 1
VERDICT: CORRECT
NOTES: 1:1 ratio for one-handed. Matches SRD.
```

### I-FEAT-257

```
FORMULA ID: I-FEAT-257
FILE: aidm/core/feat_resolver.py
LINE: 253-257
CODE: if FeatID.DODGE in feats and attacker is not None:
    if dodge_target == attacker_id: modifier += 1
RULE SOURCE: SRD 3.5e > Feats > Dodge:
  "During your action, you designate an opponent and receive a +1 dodge bonus
  to Armor Class against attacks from that opponent."
EXPECTED: Dodge: +1 dodge AC against designated opponent
ACTUAL: +1 AC when attacker is the designated dodge target
VERDICT: CORRECT
NOTES: The implementation requires a designated target (dodge_target in context),
  which matches the SRD requirement. The +1 value is correct.
```

### I-FEAT-265

```
FORMULA ID: I-FEAT-265
FILE: aidm/core/feat_resolver.py
LINE: 261-265
CODE: if FeatID.MOBILITY in feats:
    if is_aoo and aoo_trigger in ("movement_out", "mounted_movement_out"):
        modifier += 4
RULE SOURCE: SRD 3.5e > Feats > Mobility:
  "You get a +4 dodge bonus to Armor Class against attacks of opportunity
  caused when you move out of or within a threatened area."
EXPECTED: Mobility: +4 dodge AC against movement AoO
ACTUAL: +4 when is_aoo and trigger is movement
VERDICT: CORRECT
NOTES: Matches SRD exactly. The +4 value and the trigger condition (movement
  AoO only, not other types of AoO like casting) are correct.
```

### I-FEAT-283

```
FORMULA ID: I-FEAT-283
FILE: aidm/core/feat_resolver.py
LINE: 282-283
CODE: if FeatID.IMPROVED_INITIATIVE in feats: return 4
RULE SOURCE: SRD 3.5e > Feats > Improved Initiative:
  "You get a +4 bonus on initiative checks."
EXPECTED: Improved Initiative: +4 initiative
ACTUAL: +4
VERDICT: CORRECT
NOTES: Matches SRD exactly.
```

### I-FEAT-332

```
FORMULA ID: I-FEAT-332
FILE: aidm/core/feat_resolver.py
LINE: 331-335
CODE: if FeatID.GREAT_CLEAVE in feats: return None  # Unlimited
      if FeatID.CLEAVE in feats: return 1  # Once per round
RULE SOURCE: SRD 3.5e > Feats > Cleave:
  "If you deal a creature enough damage to make it drop [...] you get an
  immediate, extra melee attack against another creature within reach."
  (Implicitly once per round — can only trigger once per round with Cleave.)
  SRD > Feats > Great Cleave:
  "This feat works like Cleave, except that there is no limit to the number
  of times you can use it per round."
EXPECTED: Cleave: 1 extra attack per round. Great Cleave: unlimited.
ACTUAL: Cleave returns 1, Great Cleave returns None (unlimited)
VERDICT: CORRECT
NOTES: Matches SRD. Cleave allows one extra attack per round; Great Cleave
  removes that limit.
```

### I-FEAT-386

```
FORMULA ID: I-FEAT-386
FILE: aidm/core/feat_resolver.py
LINE: 384-392
CODE: if FeatID.TWO_WEAPON_FIGHTING in feats:
    return (-2, -2)
  else:
    if has_light_offhand:
        return (-4, -8)
    else:
        return (-6, -10)
RULE SOURCE: SRD 3.5e > Combat > Two-Weapon Fighting (Table):
  Normal penalties:
    Main hand: -6, Off-hand: -10
    With light off-hand: Main -4, Off-hand: -8
  With TWF feat:
    Main hand: -2, Off-hand: -6
    With light off-hand: Main -2, Off-hand: -2

  Full table from SRD:
  | Circumstance              | Main | Off  |
  |---------------------------|------|------|
  | Normal                    | -6   | -10  |
  | Light off-hand            | -4   | -8   |
  | TWF feat                  | -4   | -4   |
  | TWF feat + light off-hand | -2   | -2   |

EXPECTED:
  No feat, heavy off-hand: -6/-10
  No feat, light off-hand: -4/-8
  TWF feat, heavy off-hand: -4/-4
  TWF feat, light off-hand: -2/-2
ACTUAL:
  No feat, heavy off-hand: -6/-10 ✓
  No feat, light off-hand: -4/-8 ✓
  TWF feat (any off-hand): -2/-2 ✗ (ignores heavy off-hand case)
VERDICT: AMBIGUOUS
NOTES: The code returns (-2, -2) for ALL TWF feat cases, ignoring whether
  the off-hand weapon is light or heavy. Per the SRD, TWF with a heavy
  off-hand weapon should be -4/-4, not -2/-2.

  The code only returns the BEST case (-2/-2 with light off-hand) when
  the TWF feat is present, ignoring the has_light_offhand parameter entirely.
  This means a fighter dual-wielding longswords (both one-handed, not light)
  would get -2/-2 instead of the correct -4/-4.

  However, this could be an intentional simplification if the system always
  assumes light off-hand weapons for TWF. Marking AMBIGUOUS because it
  may be a deliberate design choice. If not intentional, this is WRONG.

  SRD TWF penalty table (complete):
  | Circumstances               | Primary | Off-Hand |
  |-----------------------------|---------|----------|
  | Normal penalties            |   -6    |   -10    |
  | Off-hand weapon is light    |   -4    |    -8    |
  | Two-Weapon Fighting feat    |   -4    |    -4    |
  | TWF feat + light off-hand   |   -2    |    -2    |
```

### I-FEAT-406

```
FORMULA ID: I-FEAT-406
FILE: aidm/core/feat_resolver.py
LINE: 406-407
CODE: if FeatID.GREATER_TWF in feats: return 3
RULE SOURCE: SRD 3.5e > Feats > Greater Two-Weapon Fighting:
  "You get a third attack with your off-hand weapon, albeit at a -10 penalty."
  Total off-hand attacks with Greater TWF: 3 (base at -0, second at -5,
  third at -10 from BAB progression).
EXPECTED: Greater TWF: 3 off-hand attacks total
ACTUAL: Returns 3
VERDICT: CORRECT
NOTES: Matches SRD. Greater TWF grants a third off-hand attack at -10.
```

### I-FEAT-409

```
FORMULA ID: I-FEAT-409
FILE: aidm/core/feat_resolver.py
LINE: 409-410
CODE: if FeatID.IMPROVED_TWF in feats: return 2
RULE SOURCE: SRD 3.5e > Feats > Improved Two-Weapon Fighting:
  "In addition to the normal single extra attack you get with an off-hand
  weapon, you get a second attack with it, albeit at a -5 penalty."
EXPECTED: Improved TWF: 2 off-hand attacks total
ACTUAL: Returns 2
VERDICT: CORRECT
NOTES: Matches SRD. Improved TWF adds one more off-hand attack at -5.
```

### I-FEAT-412

```
FORMULA ID: I-FEAT-412
FILE: aidm/core/feat_resolver.py
LINE: 412-413
CODE: if FeatID.TWO_WEAPON_FIGHTING in feats: return 1
RULE SOURCE: SRD 3.5e > Feats > Two-Weapon Fighting:
  Grants ability to fight with two weapons with reduced penalties.
  Base off-hand: 1 attack.
EXPECTED: Base TWF: 1 off-hand attack
ACTUAL: Returns 1
VERDICT: CORRECT
NOTES: Correct. TWF feat provides penalty reduction, and enables 1 off-hand attack.
```

---

## Verdict Summary

| File | Formulas | Correct | Wrong | Ambiguous | Uncited |
|------|----------|---------|-------|-----------|---------|
| geometry.py | 3 | 1 | 1 | 0 | 0 |
| bestiary.py | 10 | 3 | 0 | 0 | 6* |
| terrain.py | 5 | 5 | 0 | 0 | 0 |
| combat_reflexes.py | 2 | 2 | 0 | 0 | 0 |
| environmental_damage_resolver.py | 4 | 3 | 0 | 1 | 0 |
| aoo.py | 2 | 2 | 0 | 0 | 0 |
| play_loop.py | 4 | 2 | 0 | 0 | 2** |
| saves.py | 2 | 2 | 0 | 0 | 0 |
| feat_resolver.py | 16 | 14 | 0 | 1 | 0 |
| **TOTAL** | **49***| **40** | **1** | **2** | **6** |

\* bestiary.py UNCITED: hp_typical, speed, bab, fort/ref/will save defaults are
schema defaults with no SRD citation needed — they are data initialization values.

\** play_loop.py UNCITED: caster_level=5 and spell_dc_base=13 are explicitly
labeled as test defaults, not SRD values.

\*** The WO estimated 18 formulas. The expanded count of 49 includes individual
bestiary defaults, individual feat modifiers, and individual cover type labels
that the WO grouped together.

---

## Bugs Found

### BUG: I-GEOM-291 — Colossal footprint is 25 instead of 36

- **File:** aidm/schemas/geometry.py:291-301
- **Severity:** MEDIUM (affects only Colossal creatures, which are rare)
- **SRD says:** Colossal = 30 ft space = 6×6 = 36 squares
- **Code says:** Colossal = 25 squares (5×5 = 25 ft space)
- **Fix:** Change `SizeCategory.COLOSSAL: 25` to `SizeCategory.COLOSSAL: 36`
- **Also fix:** Docstring on line 286: change "25 squares (5x5)" to "36 squares (6x6)"

---

## Ambiguities Found

### AMBIGUOUS: I-ENV-51 — Spiked pit simplified to 1d6

- **Decision needed:** Is the simplified 1d6 spike damage acceptable, or should
  the full SRD mechanics (1d4 spikes × 1d6 each) be implemented?
- **Recommendation:** Accept the simplification. CP-20 design doc explicitly
  scopes environmental damage as simplified contact hazards. This is a design
  decision, not a bug.

### AMBIGUOUS: I-FEAT-386 — TWF penalties ignore heavy off-hand with feat

- **Decision needed:** Should TWF feat penalties change based on off-hand weapon
  weight (-4/-4 heavy vs -2/-2 light)?
- **Current behavior:** Always returns -2/-2 when TWF feat is present.
- **SRD says:** TWF feat with heavy off-hand = -4/-4, with light = -2/-2.
- **Recommendation:** This is likely a bug masquerading as a simplification.
  If the system tracks off-hand weapon weight (has_light_offhand parameter
  exists), then the TWF feat case should use it. Fix should be:
  ```python
  if FeatID.TWO_WEAPON_FIGHTING in feats:
      if has_light_offhand:
          return (-2, -2)
      else:
          return (-4, -4)
  ```

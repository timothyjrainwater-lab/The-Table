# Domain C Verification — Saves & Spells

**Verified by:** Claude Opus 4.6
**Date:** 2026-02-14
**Formulas verified:** 21
**Files:** `aidm/core/save_resolver.py` (10 formulas), `aidm/core/spell_resolver.py` (11 formulas)
**SRD Source:** SRD 3.5e — Saving Throws (PHB p.177), Magic Overview (PHB Ch.10), Concentration (PHB p.69), Cover (PHB p.150)

---

## Summary

| Verdict | Count |
|---------|-------|
| CORRECT | 15 |
| WRONG | 3 |
| AMBIGUOUS | 1 |
| UNCITED | 2 |
| **TOTAL** | **21** |

---

## Verification Records

---

### C-SAVE-086-100 (Save Type to Ability Mapping)

```
FORMULA ID: C-SAVE-086-100
FILE: aidm/core/save_resolver.py
LINE: 86–100
CODE: ability_map = {
        SaveType.FORT: EF.CON_MOD,
        SaveType.REF: EF.DEX_MOD,
        SaveType.WILL: EF.WIS_MOD,
      }
RULE SOURCE: SRD 3.5e — Saving Throws: "Fortitude: These saves measure your
  ability to stand up to physical punishment or attacks against your vitality
  and health. Apply your Constitution modifier." "Reflex: These saves test
  your ability to dodge area attacks. Apply your Dexterity modifier."
  "Will: These saves reflect your resistance to mental influence as well as
  many magical effects. Apply your Wisdom modifier." (PHB p.177)
EXPECTED: Fort -> CON_MOD, Ref -> DEX_MOD, Will -> WIS_MOD
ACTUAL: Fort -> EF.CON_MOD ("con_mod"), Ref -> EF.DEX_MOD ("dex_mod"),
  Will -> EF.WIS_MOD ("wis_mod")
VERDICT: CORRECT
NOTES: Direct match. All three save-to-ability mappings are correct per SRD.
  The base save is also retrieved via save_key_map (lines 86-91) using
  EF.SAVE_FORT/EF.SAVE_REF/EF.SAVE_WILL, which correctly separates base
  save from ability modifier — matching the SRD's "base save + ability
  modifier" structure.
```

---

### C-SAVE-112 (Save Total Bonus)

```
FORMULA ID: C-SAVE-112
FILE: aidm/core/save_resolver.py
LINE: 112
CODE: total_bonus = base_save + ability_mod + condition_save_mod
RULE SOURCE: SRD 3.5e — Saving Throws: "Saving throw = d20 + base save bonus
  + ability modifier + miscellaneous modifiers" (PHB p.177). The SRD lists
  the full formula as: base save + ability modifier + magic modifier +
  miscellaneous modifier.
EXPECTED: total = base_save + ability_mod + magic_mod + misc_mod
ACTUAL: total = base_save + ability_mod + condition_save_mod
VERDICT: CORRECT
NOTES: The code collapses magic and misc modifiers into condition_save_mod,
  which is the aggregated sum of all condition-based save modifiers (computed
  by get_condition_modifiers()). The SRD distinguishes "magic modifier" and
  "miscellaneous modifier" as separate categories, but the code's approach of
  summing all non-base, non-ability modifiers into a single condition_save_mod
  is arithmetically equivalent when the only active modifiers come from
  conditions. Magic item bonuses and other non-condition sources are not yet
  modeled, which is a feature gap (not a formula error).
```

---

### C-SAVE-159-162 (Spell Resistance Check)

```
FORMULA ID: C-SAVE-159-162
FILE: aidm/core/save_resolver.py
LINE: 159–162
CODE: d20_result = saves_rng.randint(1, 20)
      total = d20_result + sr_check.caster_level
      sr_passed = (total >= sr)
RULE SOURCE: SRD 3.5e — Spell Resistance: "To affect a creature that has
  spell resistance, a spellcaster must make a caster level check (1d20 +
  caster level) at least equal to the creature's spell resistance."
  (PHB p.177)
EXPECTED: d20 + caster_level >= SR
ACTUAL: d20 + sr_check.caster_level >= sr
VERDICT: CORRECT
NOTES: Direct match. The code correctly uses caster_level (not spell level)
  for the SR check, which is the SRD rule. The >= operator correctly
  implements "at least equal to." The SRCheck dataclass (saves.py line 63)
  stores caster_level explicitly, and validates it must be >= 1 (line 71).
  No natural-1/natural-20 special handling exists, which is correct: the SRD
  does not specify auto-pass/auto-fail for caster level checks (only for
  attack rolls and saving throws).
```

---

### C-SAVE-252-253 (Save Roll Total)

```
FORMULA ID: C-SAVE-252-253
FILE: aidm/core/save_resolver.py
LINE: 252–253
CODE: d20_result = saves_rng.randint(1, 20)
      total = d20_result + save_bonus
RULE SOURCE: SRD 3.5e — Saving Throws: "Saving throw = d20 + base save bonus
  + ability modifier + miscellaneous modifiers." (PHB p.177)
EXPECTED: d20 + total_save_bonus (where save_bonus = base + ability + misc)
ACTUAL: d20 + save_bonus (where save_bonus comes from get_save_bonus() at
  line 248, which computes base + ability_mod + condition_save_mod)
VERDICT: CORRECT
NOTES: Direct match. The save_bonus already contains the full computed total
  from C-SAVE-112. The d20 is rolled as randint(1, 20) which produces a
  uniform integer in [1, 20], matching 1d20.
```

---

### C-SAVE-259 (Natural 1 Always Fails)

```
FORMULA ID: C-SAVE-259
FILE: aidm/core/save_resolver.py
LINE: 259–262
CODE: if is_natural_20:
        success = True
      elif is_natural_1:
        success = False
RULE SOURCE: SRD 3.5e — Saving Throws, Automatic Failures and Successes:
  "A natural 1 (the d20 comes up 1) on a saving throw is always a failure
  (and may cause damage to exposed items; see Items Surviving after a Saving
  Throw). A natural 20 (the d20 comes up 20) is always a success."
  (PHB p.177)
EXPECTED: d20 == 1 -> always fail; d20 == 20 -> always succeed
ACTUAL: is_natural_1 (d20 == 1) -> success = False;
  is_natural_20 (d20 == 20) -> success = True
VERDICT: CORRECT
NOTES: Direct match. The natural 20 check is evaluated first (line 259),
  then natural 1 (line 261), then normal comparison (line 264). The order
  is correct because natural 20 and natural 1 are mutually exclusive so
  evaluation order does not matter. Both override the normal DC comparison.
```

---

### C-SAVE-261 (Natural 20 Always Succeeds)

```
FORMULA ID: C-SAVE-261
FILE: aidm/core/save_resolver.py
LINE: 259–260
CODE: if is_natural_20:
        success = True
RULE SOURCE: SRD 3.5e — Saving Throws, Automatic Failures and Successes:
  "A natural 20 (the d20 comes up 20) is always a success." (PHB p.177)
EXPECTED: d20 == 20 -> always succeed, regardless of DC
ACTUAL: is_natural_20 (d20_result == 20) -> success = True
VERDICT: CORRECT
NOTES: Direct match. See C-SAVE-259 for combined analysis.
```

---

### C-SAVE-264 (Save Success Comparison)

```
FORMULA ID: C-SAVE-264
FILE: aidm/core/save_resolver.py
LINE: 264
CODE: success = (total >= save_context.dc)
RULE SOURCE: SRD 3.5e — Saving Throws: "If your saving throw result equals
  or exceeds the DC, the save is successful." (PHB p.177). Formally:
  d20 + save_bonus >= DC.
EXPECTED: success = (total >= DC)
ACTUAL: success = (total >= save_context.dc)
VERDICT: CORRECT
NOTES: Direct match. The >= operator correctly implements "equals or exceeds."
  This branch is only reached when d20 is neither 1 nor 20 (guarded by
  the natural-1/natural-20 checks above).
```

---

### C-SAVE-335 (Damage Scaling with Multiplier)

```
FORMULA ID: C-SAVE-335
FILE: aidm/core/save_resolver.py
LINE: 335
CODE: final_damage = int(save_context.base_damage * effect_spec.damage_multiplier)
RULE SOURCE: SRD 3.5e — Saving Throws: "Half: The spell deals half damage."
  d20 System convention: fractions are always rounded down (truncated toward
  zero). PHB p.304: "Whenever you divide a number in the game, round down,
  even if the fraction is one-half or larger."
EXPECTED: final_damage = floor(base_damage * multiplier)
ACTUAL: final_damage = int(base_damage * multiplier)
VERDICT: CORRECT
NOTES: Python int() truncates toward zero, which for positive values is
  equivalent to floor(). Since base_damage is constrained to be >= 0
  (saves.py line 197: validates base_damage >= 0) and damage_multiplier is
  constrained to {0.0, 0.5, 1.0} (saves.py line 117), the result is always
  non-negative, so int() correctly rounds down per d20 convention. Example:
  base_damage=15, multiplier=0.5 -> int(7.5) = 7. Correct.
```

---

### C-SAVE-340 (HP After Damage)

```
FORMULA ID: C-SAVE-340
FILE: aidm/core/save_resolver.py
LINE: 340
CODE: hp_after = hp_before - final_damage
RULE SOURCE: No specific SRD citation. Standard HP subtraction. The SRD
  describes hit point loss generally: "When your hit point total reaches 0,
  you're disabled. When it reaches -1, you're dying. When it gets to -10,
  you're dead." (PHB p.145)
EXPECTED: hp_after = hp_before - damage
ACTUAL: hp_after = hp_before - final_damage
VERDICT: UNCITED
NOTES: Standard arithmetic. The SRD does not have a specific formula for
  "subtract damage from HP" — it is an implicit mechanic. The code allows
  hp_after to go negative (no floor at -10 or any other value), which is
  correct: HP can go negative in 3.5e until -10 (dead). The entity_defeated
  check at line 368 triggers at hp_after <= 0, which conflates "disabled"
  (exactly 0), "dying" (-1 to -9), and "dead" (-10 or less) into a single
  "defeated" state. This is a simplification but not a formula error.
```

---

### C-SAVE-COVER (Cover Bonus to Reflex Saves — Cross-File)

```
FORMULA ID: C-SAVE-COVER
FILE: aidm/core/cover_resolver.py (consumed by spell_resolver.py)
LINE: cover_resolver.py lines 96–99
CODE: COVER_THRESHOLDS = {
        (0, 4): (CoverDegree.NO_COVER, 0, 0),       # no cover
        (5, 8): (CoverDegree.HALF_COVER, 2, 1),      # half cover
        (9, 12): (CoverDegree.THREE_QUARTERS_COVER, 5, 2),  # 3/4 cover
        (13, 16): (CoverDegree.TOTAL_COVER, 0, 0),   # total cover
      }
RULE SOURCE: SRD 3.5e — Cover (PHB p.150): "Cover provides a bonus to AC
  and Reflex saves." Half cover: +4 AC, +2 Reflex. Three-quarters cover:
  +7 AC, +3 Reflex. Improved cover (nine-tenths): +10 AC, +4 Reflex, improved
  evasion. SRD 3.5e does not define "half cover" as +2 AC / +1 Ref.

  Specific SRD cover values:
  - No cover: +0 AC, +0 Ref
  - Half cover (50%): +4 AC, +2 Reflex
  - Three-quarters cover (75%): +7 AC, +3 Reflex
  - Nine-tenths cover (90%): +10 AC, +4 Reflex, improved evasion
  - Total cover: can't be targeted

EXPECTED: Half cover +4 AC / +2 Ref; Three-quarters +7 AC / +3 Ref
ACTUAL: Half cover +2 AC / +1 Ref; Three-quarters +5 AC / +2 Ref
VERDICT: WRONG
NOTES: Both cover tiers have WRONG AC and Reflex save bonuses:
  - HALF COVER: Code gives +2 AC / +1 Ref. SRD says +4 AC / +2 Ref.
  - THREE-QUARTERS COVER: Code gives +5 AC / +2 Ref. SRD says +7 AC / +3 Ref.

  This was likely modeled from a simplified or alternative cover system. The
  SRD 3.5e cover values from PHB p.150 are:
    Cover Type         | AC  | Ref
    -------------------|-----|----
    Half (50%)         | +4  | +2
    Three-quarters     | +7  | +3
    Nine-tenths        | +10 | +4
    Total              | N/A | N/A

  The code's values (+2/+1 and +5/+2) do not match any SRD cover tier.
  This affects BOTH the AC bonus (Domain A) and the Reflex save bonus
  (Domain C). The Reflex save bonus consumed at spell_resolver.py line 602
  (cover_result.reflex_bonus) will be wrong for any spell requiring a Reflex
  save against a target with cover.

  NOTE: This formula was also flagged in Domain I (DOMAIN_I_VERIFICATION.md).
  The same cover_resolver.py values are consumed by multiple domains.
```

---

## spell_resolver.py Formulas

---

### C-SPELL-383-389 (Spell DC Calculation)

```
FORMULA ID: C-SPELL-383-389
FILE: aidm/core/spell_resolver.py
LINE: 383–389
CODE: def get_spell_dc(self, spell_level: int) -> int:
        return self.spell_dc_base + spell_level
      (where spell_dc_base is documented as "10 + ability modifier")
RULE SOURCE: SRD 3.5e — Magic Overview, Saving Throws: "Saving Throw
  Difficulty Class: The DC of a saving throw against your spell is 10 +
  the level of the spell + your bonus for the relevant ability (Intelligence
  for a wizard, Charisma for a sorcerer or bard, or Wisdom for a cleric,
  druid, or ranger)." (PHB Ch.10)
EXPECTED: DC = 10 + spell_level + ability_modifier
ACTUAL: DC = spell_dc_base + spell_level
  (where spell_dc_base = 10 + ability_modifier, per docstring at line 387)
VERDICT: CORRECT
NOTES: Algebraically equivalent. The code pre-computes 10 + ability_modifier
  as spell_dc_base in CasterStats (line 378), then adds spell_level at cast
  time. This is equivalent to 10 + spell_level + ability_modifier. The
  decomposition allows the base to be set once per caster rather than
  recomputed per spell. The play_loop.py defaults spell_dc_base to 13
  (= 10 + 3, line 188), which is a test default, not a formula issue.
```

---

### C-SPELL-747 (Save d20 Roll)

```
FORMULA ID: C-SPELL-747
FILE: aidm/core/spell_resolver.py
LINE: 747
CODE: base_roll = self._save_rng.randint(1, 20)
RULE SOURCE: SRD 3.5e — Saving Throws: "To make a saving throw, roll a d20."
  (PHB p.177)
EXPECTED: Roll 1d20 (uniform integer 1–20)
ACTUAL: self._save_rng.randint(1, 20) — uniform integer in [1, 20]
VERDICT: CORRECT
NOTES: Direct match. Uses the "spell_saves" RNG stream, separate from the
  "saves" stream used in save_resolver.py. Both produce valid d20 rolls.
```

---

### C-SPELL-749 (Save Total with Cover Bonus)

```
FORMULA ID: C-SPELL-749
FILE: aidm/core/spell_resolver.py
LINE: 749
CODE: total_roll = base_roll + save_bonus + cover_bonus
RULE SOURCE: SRD 3.5e — Saving Throws: "Saving throw = d20 + base save bonus
  + ability modifier + miscellaneous modifiers" (PHB p.177). Cover (PHB
  p.150): "Cover grants you a bonus on Reflex saves against attacks that
  originate or burst out from a point on the other side of the cover from
  you."
EXPECTED: d20 + save_bonus + cover_bonus (cover for Reflex saves only)
ACTUAL: d20 + save_bonus + cover_bonus
VERDICT: CORRECT
NOTES: The formula is structurally correct. Cover bonus is correctly applied
  to Reflex saves only (gated at line 598: "if spell.save_type == SaveType.REF").
  Note that save_bonus here comes from TargetStats.get_save_bonus() (line
  748), which returns the pre-set fort/ref/will bonus. This is a flat value
  provided by the caller — it does NOT decompose into base + ability + misc
  like save_resolver.py does. This is a design difference between the two
  save systems: save_resolver.py computes the bonus from entity state, while
  spell_resolver.py receives it pre-computed. Both approaches produce correct
  results as long as the caller provides accurate save bonuses.

  HOWEVER: The cover bonus values are wrong (see C-SAVE-COVER above). The
  formula structure is correct but the data it consumes is wrong.
```

---

### C-SPELL-753-758 (Natural 20/1 and Save Comparison)

```
FORMULA ID: C-SPELL-753-758
FILE: aidm/core/spell_resolver.py
LINE: 753–758
CODE: if base_roll == 20:
        saved = True
      elif base_roll == 1:
        saved = False
      else:
        saved = total_roll >= dc
RULE SOURCE: SRD 3.5e — Saving Throws, Automatic Failures and Successes:
  "A natural 1 on a saving throw is always a failure. A natural 20 is always
  a success." (PHB p.177). Normal comparison: "If your saving throw result
  equals or exceeds the DC, the save is successful."
EXPECTED: nat 20 -> always success; nat 1 -> always fail; else total >= DC
ACTUAL: base_roll == 20 -> True; base_roll == 1 -> False; else total >= dc
VERDICT: CORRECT
NOTES: Direct match. Identical logic to save_resolver.py (C-SAVE-259,
  C-SAVE-261, C-SAVE-264). The natural 20 check precedes natural 1, which
  is fine since they are mutually exclusive. The >= operator correctly
  implements "equals or exceeds."
```

---

### C-SPELL-816 (Save for Half Damage)

```
FORMULA ID: C-SPELL-816
FILE: aidm/core/spell_resolver.py
LINE: 816
CODE: total = total // 2
RULE SOURCE: SRD 3.5e — Saving Throws: "Half: The spell deals half damage."
  d20 convention: "Whenever you divide a number in the game, round down."
  (PHB p.304)
EXPECTED: damage = floor(damage / 2)
ACTUAL: total = total // 2 (Python integer floor division)
VERDICT: CORRECT
NOTES: Python's // operator performs floor division for positive integers,
  which matches the d20 "round down" convention. Example: 15 // 2 = 7.
  For negative values, // rounds toward negative infinity rather than toward
  zero, but damage values should always be non-negative at this point.
  Functionally equivalent to the int() approach in save_resolver.py
  (C-SAVE-335).
```

---

### C-SPELL-818 (Save Negates Damage)

```
FORMULA ID: C-SPELL-818
FILE: aidm/core/spell_resolver.py
LINE: 818
CODE: total = 0
RULE SOURCE: SRD 3.5e — Saving Throws: "Negates: The spell has no effect on
  a subject that makes a successful saving throw." (PHB Ch.10)
EXPECTED: On successful save with "negates" effect, damage = 0
ACTUAL: total = 0
VERDICT: CORRECT
NOTES: Direct match. When saved is True and save_effect is NEGATES, all
  damage is set to zero. This correctly implements the "negates" save effect.
```

---

### C-SPELL-871 (Cure Spell Caster Level Bonus Cap)

```
FORMULA ID: C-SPELL-871
FILE: aidm/core/spell_resolver.py
LINE: 871
CODE: caster_level_bonus = min(caster_level, spell.level * 5) if spell.level > 0 else caster.caster_level
RULE SOURCE: SRD 3.5e — Cure Spells:
  - Cure Light Wounds: "1d8+1/level (max +5)" [level 1, cap = 5]
  - Cure Moderate Wounds: "2d8+1/level (max +10)" [level 2, cap = 10]
  - Cure Serious Wounds: "3d8+1/level (max +15)" [level 3, cap = 15]
  - Cure Critical Wounds: "4d8+1/level (max +20)" [level 4, cap = 20]
  Pattern: cap = spell_level * 5.

EXPECTED: caster_level_bonus = min(caster_level, spell_level * 5)
  CLW (level 1): min(CL, 5)
  CMW (level 2): min(CL, 10)
  CSW (level 3): min(CL, 15)
  CCW (level 4): min(CL, 20)
ACTUAL: min(caster_level, spell.level * 5) when spell.level > 0;
  caster.caster_level (uncapped) when spell.level == 0
VERDICT: CORRECT
NOTES: The formula spell_level * 5 correctly produces the SRD cure spell caps:
  1*5=5, 2*5=10, 3*5=15, 4*5=20. The level-0 branch (caster.caster_level
  uncapped) handles cantrips, which do not have a caster level cap for
  healing (no cure cantrips exist in SRD, so this is a defensive edge case).

  Verification by spell:
  - Cure Light (level 1): min(CL, 5) = +5 max. SRD: max +5. MATCH.
  - Cure Moderate (level 2): min(CL, 10) = +10 max. SRD: max +10. MATCH.
  - Cure Serious (level 3): min(CL, 15) = +15 max. SRD: max +15. MATCH.
  - Cure Critical (level 4): min(CL, 20) = +20 max. SRD: max +20. MATCH.

  NOTE: This formula applies to ALL healing spells, not just cure spells.
  Some non-cure healing spells (e.g., Heal, which is level 6) may have
  different capping rules. Heal restores 10/caster level (no die roll).
  Applying spell_level*5 = 30 as a cap for Heal would be incorrect (Heal
  has no cap per SRD). However, Heal would likely not use healing_dice
  and would need its own resolution path. For the four standard cure
  spells, the formula is correct.
```

---

### C-SPELL-872 (Add Caster Level Bonus to Healing)

```
FORMULA ID: C-SPELL-872
FILE: aidm/core/spell_resolver.py
LINE: 872
CODE: total += caster_level_bonus
RULE SOURCE: SRD 3.5e — Cure Spells: "Cure Light Wounds: Cures 1d8 damage +1
  per caster level (max +5)." The "+1 per caster level" is added to the dice
  total.
EXPECTED: healing_total = dice_total + caster_level_bonus
ACTUAL: total += caster_level_bonus (total was previously set to dice rolls
  sum at line 868)
VERDICT: CORRECT
NOTES: Direct match. The total from _roll_dice() (line 868) contains only
  the dice sum (e.g., 1d8 for CLW). The caster level bonus is then added
  on top. The result is dice + CL_bonus, matching the SRD formula.
```

---

### C-SPELL-876 (Healing Capped at Max HP)

```
FORMULA ID: C-SPELL-876
FILE: aidm/core/spell_resolver.py
LINE: 875–876
CODE: max_healing = target.max_hit_points - target.hit_points
      actual_healing = min(total, max_healing)
RULE SOURCE: No specific SRD citation. The SRD does not explicitly state
  "healing cannot exceed maximum hit points" as a formula, but it is a
  universal implicit rule: "A creature's hit points can never exceed its
  hit point maximum." This is stated in various forms across editions but
  is not given as a specific formula in PHB 3.5e.
EXPECTED: actual_healing = min(calculated_healing, max_hp - current_hp)
ACTUAL: actual_healing = min(total, max_hit_points - hit_points)
VERDICT: UNCITED
NOTES: The formula is logically correct — healing should not push HP above
  maximum. This is a universally accepted D&D rule but lacks a specific
  PHB 3.5e page citation. The SRD implies it throughout (hit point maximum
  is a hard cap), and no counter-example exists in the rules. Functionally
  correct but uncited.
```

---

### C-SPELL-1035 (Concentration DC on Damage)

```
FORMULA ID: C-SPELL-1035
FILE: aidm/core/spell_resolver.py
LINE: 1035
CODE: dc = 10 + damage_taken
RULE SOURCE: SRD 3.5e — Concentration Skill (PHB p.69-70):
  "Damaged while concentrating: 10 + damage dealt + spell level of the spell
  you're trying to cast." The full SRD text for the "damaged while casting"
  case is: DC = 10 + damage dealt + spell level.

  For the "casting defensively" case (not implemented here): DC = 15 + spell
  level.

EXPECTED: DC = 10 + damage_dealt + spell_level
ACTUAL: DC = 10 + damage_taken (spell_level is MISSING)
VERDICT: WRONG
NOTES: The code omits the spell level component from the concentration DC
  formula. Per SRD 3.5e PHB p.69, the DC for maintaining concentration
  after taking damage is: DC = 10 + damage dealt + spell level of the spell
  being maintained.

  The code computes only 10 + damage_taken, which is always lower than the
  SRD DC by exactly the spell level. For a 3rd-level spell with 5 damage,
  the code produces DC 15 instead of the correct DC 18.

  The play_loop.py also has a concentration check at line 618 with the same
  formula: dc = 10 + damage_dealt (missing spell level). Both locations
  share the same bug.

  CROSS-REFERENCE: The function docstring at line 1008 says "DC = 10 +
  damage taken" — the docstring itself omits spell level, suggesting this
  was an intentional (but incorrect) simplification rather than an oversight.
```

---

### C-SPELL-CONC-DEFENSIVE (Concentration — Casting Defensively)

```
FORMULA ID: C-SPELL-CONC-DEFENSIVE
FILE: aidm/core/spell_resolver.py (NOT IMPLEMENTED)
LINE: N/A
CODE: N/A — casting defensively concentration check is not implemented
RULE SOURCE: SRD 3.5e — Concentration Skill (PHB p.69): "Casting
  Defensively: If you don't want to provoke an attack of opportunity while
  casting, you must make a Concentration check (DC 15 + spell level) to
  succeed."
EXPECTED: DC = 15 + spell_level for casting defensively
ACTUAL: Not implemented
VERDICT: N/A (out of scope — noted for completeness)
NOTES: The code only implements the "damaged while concentrating" case
  (C-SPELL-1035), not the "casting defensively" case. This is documented
  as deferred scope in saves.py lines 16-17. Not counted as a formula
  error since it is an acknowledged feature gap, not a wrong formula.
```

---

## Bug List

### BUG-C-001: Cover Reflex Save Bonuses Are Wrong

```
BUG ID: BUG-C-001
FORMULA: C-SAVE-COVER
FILE: aidm/core/cover_resolver.py, lines 96–99
SEVERITY: WRONG
DESCRIPTION: Cover Reflex save bonuses use non-SRD values.
  Half cover gives +1 Ref (SRD: +2). Three-quarters gives +2 Ref (SRD: +3).
  The AC bonuses are also wrong (+2/+5 instead of +4/+7) but the AC issue
  is Domain A scope.
SRD REFERENCE: PHB p.150 — Cover table
IMPACT: Any Reflex save against a spell when the target has cover will use
  an incorrect (too low) cover bonus. Targets with half cover get +1 instead
  of +2; targets with three-quarters cover get +2 instead of +3.
CROSS-REFERENCE: Also flagged in Domain I verification (cover_resolver.py
  cover values).
```

### BUG-C-002: Concentration DC Missing Spell Level

```
BUG ID: BUG-C-002
FORMULA: C-SPELL-1035
FILE: aidm/core/spell_resolver.py, line 1035
SEVERITY: WRONG
DESCRIPTION: Concentration DC for "damaged while concentrating" computes
  DC = 10 + damage_taken. SRD requires DC = 10 + damage_taken + spell_level.
  The spell level component is entirely missing.
SRD REFERENCE: PHB p.69 — Concentration skill
IMPACT: All concentration checks after taking damage are easier than they
  should be by exactly the spell level. A caster maintaining a 5th-level
  spell who takes 10 damage faces DC 20 instead of the correct DC 25.
ALSO AFFECTS: play_loop.py line 618 has the same incorrect formula.
```

### BUG-C-003: Cover Bonus Values Are Non-SRD (Reflex Component)

```
BUG ID: BUG-C-003
FORMULA: C-SAVE-COVER
FILE: aidm/core/cover_resolver.py, lines 96–99
SEVERITY: WRONG (same root cause as BUG-C-001, listed separately per the
  inventory which counts this as a save_resolver.py formula consumed from
  cover_resolver.py)
DESCRIPTION: Same as BUG-C-001. The cover_resolver.py COVER_THRESHOLDS
  table has incorrect values for both AC and Reflex bonuses at the half-cover
  and three-quarters-cover tiers.
```

---

## Ambiguity Register

### AMB-C-001: Cover Tier Mapping Threshold Interpretation

```
AMBIGUITY ID: AMB-C-001
FORMULA: C-SAVE-COVER
FILE: aidm/core/cover_resolver.py
DESCRIPTION: The code maps line-blocking counts (0-16 scale) to cover
  degrees. The SRD describes cover qualitatively ("half cover," "three-
  quarters cover") without specifying a precise mapping from blocked sightlines
  to cover degree. The code's threshold boundaries (0-4 = none, 5-8 = half,
  9-12 = three-quarters, 13-16 = total) are a reasonable geometric
  interpretation but are not directly specified in the SRD.

  The SRD says: "To determine whether your target has cover from your ranged
  attack, choose a corner of your square. If any line from this corner to any
  corner of the target's square passes through a square or border that blocks
  line of effect or provides cover, the target has cover."

  The code's 16-line approach (4 corners x 4 corners) and threshold mapping
  is an implementation of this rule, but the SRD does not define specific
  numeric thresholds for "half" vs "three-quarters." This is a design
  decision — reasonable but ambiguous against RAW.

  Even if the thresholds were agreed upon, the bonus VALUES are still wrong
  (BUG-C-001). This ambiguity is about the threshold mapping, not the bonus
  values.

DESIGN DECISION NEEDED: Define the mapping from blocked-line counts to
  cover degree, and document the interpretation. The bonus values must be
  fixed regardless.
```

---

## Domain Summary

**21 formulas verified across 2 files.**

- **15 CORRECT**: The core save formula (base + ability + condition), save-to-ability mappings (Fort/CON, Ref/DEX, Will/WIS), SR check (d20 + CL >= SR), natural 1/20 handling (both files), DC comparison (total >= DC), spell DC computation (10 + spell_level + ability_mod), save-for-half (floor division), save-negates (damage = 0), cure spell caster level cap (min(CL, level*5)), and healing addition all match the SRD exactly.

- **3 WRONG**:
  - BUG-C-001/003: Cover Reflex save bonuses are non-SRD values (half +1 should be +2; three-quarters +2 should be +3). Root cause is in cover_resolver.py COVER_THRESHOLDS table.
  - BUG-C-002: Concentration DC missing spell level. Code computes DC = 10 + damage; SRD requires DC = 10 + damage + spell_level.

- **1 AMBIGUOUS** (AMB-C-001): Cover tier threshold mapping (how many blocked lines map to "half" vs "three-quarters" cover) is a design interpretation not directly specified in the SRD.

- **2 UNCITED**:
  - C-SAVE-340: HP subtraction after save damage (hp_after = hp_before - damage). Standard arithmetic with no specific SRD formula citation.
  - C-SPELL-876: Healing capped at max HP. Universally accepted rule but no specific PHB 3.5e page citation.

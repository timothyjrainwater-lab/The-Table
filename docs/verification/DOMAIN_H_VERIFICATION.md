# Domain H: Skill System — Verification Records

**Domain:** H — Skill System
**File:** `aidm/core/skill_resolver.py`
**Formulas:** 6
**Verified by:** Builder agent (Claude Code)
**Date:** 2026-02-14
**SRD Source:** d20srd.org — "Using Skills"; PHB Chapter 4

---

## Summary

| Verdict | Count |
|---------|-------|
| CORRECT | 4 |
| WRONG | 0 |
| AMBIGUOUS | 1 |
| UNCITED | 1 |
| **TOTAL** | **6** |

---

## Verification Records

---

### H-SKILL-161

```
FORMULA ID: H-SKILL-161
FILE: aidm/core/skill_resolver.py
LINE: 161
CODE: d20_roll = combat_rng.randint(1, 20)
RULE SOURCE: SRD 3.5e — Using Skills: "To make a skill check, roll 1d20
  and add your character's skill modifier for that skill."
EXPECTED: Roll 1d20 (uniform integer 1–20)
ACTUAL: combat_rng.randint(1, 20) — uniform integer 1–20
VERDICT: CORRECT
NOTES: Direct match. The d20 roll is generated correctly.
```

---

### H-SKILL-170

```
FORMULA ID: H-SKILL-170
FILE: aidm/core/skill_resolver.py
LINE: 170
CODE: total = d20_roll + ability_mod + ranks + circumstance_modifier - acp
RULE SOURCE: SRD 3.5e — Using Skills: "Skill modifier = skill rank +
  ability modifier + miscellaneous modifiers." Skill check = 1d20 + skill
  modifier. Miscellaneous modifiers include racial bonuses, armor check
  penalty, circumstance modifiers, feat bonuses, etc.
EXPECTED: 1d20 + ability_mod + ranks + misc_modifiers (where misc includes
  circumstance bonus/penalty, ACP, racial, feat, etc.)
ACTUAL: d20 + ability_mod + ranks + circumstance_modifier - acp
VERDICT: CORRECT
NOTES: The SRD groups ACP under "miscellaneous modifiers" and applies it as
  a penalty (negative). The code separates ACP as an explicit subtraction,
  which is arithmetically equivalent. The ACP is only applied when
  skill_def.armor_check_penalty is True (line 166), matching the SRD rule:
  "If the Armor Check Penalty notation is included in the skill name line,
  an armor check penalty applies to checks using that skill."

  The circumstance_modifier parameter corresponds to the SRD's circumstance
  bonus/penalty, which is a valid modifier type for skill checks per SRD:
  "Give the skill user a +2 circumstance bonus to represent conditions that
  improve performance" / "Give the skill user a -2 circumstance penalty to
  represent conditions that hamper performance."

  Racial bonuses and feat bonuses are not currently modeled as separate
  inputs, but this is a scope/feature gap, not a formula error — the
  formula structure is correct for the modifiers it handles.
```

---

### H-SKILL-173

```
FORMULA ID: H-SKILL-173
FILE: aidm/core/skill_resolver.py
LINE: 173
CODE: success=(total >= dc)
RULE SOURCE: SRD 3.5e — Using Skills: "If the result of a skill check
  equals or exceeds the Difficulty Class, the check is successful."
EXPECTED: success = (total >= DC)
ACTUAL: success = (total >= dc)
VERDICT: CORRECT
NOTES: Direct match. The >= operator correctly implements "equals or
  exceeds." Note: unlike attack rolls and saving throws, skill checks do
  NOT have natural 20 auto-success or natural 1 auto-failure per SRD:
  "Unlike with attack rolls and saving throws, a natural roll of 20 on the
  d20 is not an automatic success, and a natural roll of 1 is not an
  automatic failure." The code correctly omits nat-20/nat-1 special
  handling for skill checks.
```

---

### H-SKILL-233-234

```
FORMULA ID: H-SKILL-233-234
FILE: aidm/core/skill_resolver.py
LINE: 233–234
CODE: actor_d20 = combat_rng.randint(1, 20)
      opponent_d20 = combat_rng.randint(1, 20)
RULE SOURCE: SRD 3.5e — Using Skills, Opposed Checks: "In an opposed
  check, the higher result succeeds, while the lower result fails."
  (Both sides roll d20 + skill modifier.)
EXPECTED: Both actor and opponent roll 1d20 independently.
ACTUAL: Both roll combat_rng.randint(1, 20) independently.
VERDICT: CORRECT
NOTES: Direct match. Both sides roll d20 independently as required.
```

---

### H-SKILL-241-249

```
FORMULA ID: H-SKILL-241-249
FILE: aidm/core/skill_resolver.py
LINE: 241–249
CODE: actor_total = actor_d20 + actor_ability_mod + actor_ranks
        + actor_circumstance - actor_acp
      opponent_total = opponent_d20 + opponent_ability_mod + opponent_ranks
        + opponent_circumstance - opponent_acp
RULE SOURCE: SRD 3.5e — Using Skills: Opposed check totals use the same
  skill check formula (1d20 + skill modifier) for each side. Skill modifier
  = ranks + ability mod + miscellaneous modifiers.
EXPECTED: Each side: 1d20 + ability_mod + ranks + misc_modifiers
ACTUAL: Each side: d20 + ability_mod + ranks + circumstance - acp
VERDICT: UNCITED
NOTES: The formula structure is correct — it matches the standard skill
  check formula applied to each side of the opposed check. However, there
  is no explicit SRD citation for applying ACP to opposed checks
  specifically (as opposed to regular skill checks). The SRD simply says
  both sides make skill checks, so the standard skill check formula
  (including ACP for applicable skills) should apply. This is a reasonable
  and almost certainly correct interpretation, but the SRD does not have a
  separate "opposed check total formula" — it just says both sides make
  skill checks. Marking UNCITED because the application of the standard
  formula to opposed checks is inferred rather than directly cited, though
  the inference is very strong.

  Functionally equivalent to CORRECT — the same formula from H-SKILL-170
  is applied to each side, which is what the SRD intends.
```

---

### H-SKILL-254

```
FORMULA ID: H-SKILL-254
FILE: aidm/core/skill_resolver.py
LINE: 254
CODE: actor_wins = (actor_total >= opponent_total)
RULE SOURCE: SRD 3.5e — Using Skills, Opposed Checks: "In an opposed
  check, the higher result succeeds, while the lower result fails. In case
  of a tie, the higher skill modifier wins. If these scores are the same,
  roll again to break the tie."
EXPECTED: Higher total wins. On tie: compare skill modifiers, then re-roll
  if still tied.
ACTUAL: actor_wins = (actor_total >= opponent_total) — ties always go to
  the actor (active checker). No skill modifier comparison. No re-roll.
VERDICT: AMBIGUOUS
NOTES: The code uses >= to give ties to the active checker (actor). The SRD
  specifies a two-step tie-breaking procedure:

  1. Compare skill modifiers (ranks + ability mod + misc). Higher modifier
     wins.
  2. If skill modifiers are also tied, roll again to break the tie.

  The code does neither — it simply awards ties to the actor. This is a
  deliberate simplification documented in the OpposedCheckResult docstring
  (line 60: "ties favor the active checker").

  SRD interpretation: The SRD does NOT say "ties favor the active checker."
  It says ties go to the higher skill modifier, then re-roll. The code's
  approach is a common house rule but does not match RAW.

  Pathfinder SRD: Pathfinder kept the same rule — "If the opposing check
  results are equal, the character with the higher check modifier wins."
  Pathfinder did not change the tie-breaking rule to favor the active
  checker.

  Impact: In practice, this matters in a narrow case (exact ties). The
  code's approach is simpler and avoids recursive re-rolling, but it
  produces a different result than RAW in tie scenarios. A tie with equal
  modifiers under RAW would require a re-roll loop; the code skips this
  entirely.

  Design decision needed: Keep the simplification (document as intentional
  house rule) or implement the SRD two-step tie-break.
```

---

## Domain Summary

**6 formulas verified in `aidm/core/skill_resolver.py`.**

- **4 CORRECT**: The core skill check formula (d20 + ability + ranks + circumstance - ACP), the success threshold (total >= DC), and both d20 rolls for opposed checks all match the SRD exactly.

- **0 WRONG**: No arithmetic errors found.

- **1 AMBIGUOUS** (H-SKILL-254): Opposed check tie-breaking uses `>=` (ties to actor) instead of the SRD's two-step process (compare skill modifiers, then re-roll). This is a common simplification but does not match RAW. Requires design decision.

- **1 UNCITED** (H-SKILL-241-249): Opposed check totals use the standard skill check formula for each side. This is almost certainly correct by inference (the SRD says both sides make skill checks), but there is no separate SRD formula for "opposed check total." The inference is strong enough that this is functionally correct.

### ACP Verification

The armor_check_penalty flag is correctly gated: line 166 checks `skill_def.armor_check_penalty` before applying ACP. The skill definitions in `aidm/schemas/skills.py` correctly mark:
- ACP=True: Tumble, Hide, Move Silently, Balance (all DEX-based physical skills)
- ACP=False: Concentration, Spot, Listen (mental/perception skills)

This matches the SRD, which states ACP applies only to skills with the "Armor Check Penalty" notation.

### Circumstance Modifier Verification

The `circumstance_modifier` parameter is a valid SRD modifier type. The SRD explicitly describes circumstance bonuses/penalties for skill checks: "+2 circumstance bonus to represent conditions that improve performance" and "-2 circumstance penalty to represent conditions that hamper performance." Circumstance bonuses stack with all other bonuses including other circumstance bonuses (SRD stacking rules).

---

## Bug List

No WRONG verdicts. No bugs to fix.

## Design Decisions Required

1. **H-SKILL-254 (Opposed tie-breaking)**: The code gives ties to the active checker. The SRD says compare skill modifiers, then re-roll. Decide whether to:
   - (a) Keep current behavior and document as intentional simplification/house rule
   - (b) Implement SRD-compliant two-step tie-break (modifier comparison + re-roll loop)

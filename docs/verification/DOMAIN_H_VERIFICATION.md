# Domain H Verification -- Skill System
**Verified by:** Claude Opus 4.6
**Date:** 2026-02-14
**Formulas verified:** 6
**Summary:** 4 CORRECT, 0 WRONG, 1 AMBIGUOUS, 1 UNCITED

---

## Source Files

| File | Formulas |
|------|----------|
| `aidm/core/skill_resolver.py` | 6 |
| `aidm/schemas/skills.py` | (supporting -- skill definitions, ACP flags, key abilities) |

---

## Verification Records

---

### H-SKILL-161 -- d20 Roll

```
FORMULA ID:   H-SKILL-161
FILE:         aidm/core/skill_resolver.py
LINE:         161
CODE:         d20_roll = combat_rng.randint(1, 20)
RULE SOURCE:  SRD 3.5e, PHB Chapter 4 (Using Skills): "To make a skill check,
              roll 1d20 and add your character's skill modifier for that skill."
EXPECTED:     Roll 1d20 -- uniform random integer on [1, 20]
ACTUAL:       combat_rng.randint(1, 20) -- uniform random integer on [1, 20]
VERDICT:      CORRECT
NOTES:        Direct match. Python's randint(1, 20) is inclusive on both
              endpoints, producing the correct d20 distribution.
```

---

### H-SKILL-170 -- Skill Check Total

```
FORMULA ID:   H-SKILL-170
FILE:         aidm/core/skill_resolver.py
LINE:         170
CODE:         total = d20_roll + ability_mod + ranks + circumstance_modifier - acp
RULE SOURCE:  SRD 3.5e, PHB Chapter 4: "Skill modifier = skill rank + ability
              modifier + miscellaneous modifiers." Skill check = 1d20 + skill
              modifier. Miscellaneous modifiers include circumstance bonuses,
              armor check penalty (as a negative value), racial bonuses, feat
              bonuses, etc.
EXPECTED:     1d20 + ability_mod + ranks + misc_modifiers
              (where misc includes circumstance +/-, ACP as penalty, racial,
              feat, etc.)
ACTUAL:       d20 + ability_mod + ranks + circumstance_modifier - acp
VERDICT:      CORRECT
NOTES:        The formula is arithmetically equivalent to the SRD. The SRD
              groups ACP under "miscellaneous modifiers" and applies it as a
              penalty (negative value). The code separates ACP as an explicit
              subtraction, which produces identical results.

              ACP gating (lines 165-167): The code only applies ACP when
              skill_def.armor_check_penalty is True. This matches the SRD:
              "If a skill has an armor check penalty, an armor check penalty
              applies to checks using that skill."

              ACP flag verification against aidm/schemas/skills.py:
                - Tumble:        DEX, ACP=True  (PHB p.84: YES -- correct)
                - Hide:          DEX, ACP=True  (PHB p.76: YES -- correct)
                - Move Silently: DEX, ACP=True  (PHB p.79: YES -- correct)
                - Balance:       DEX, ACP=True  (PHB p.67: YES -- correct)
                - Concentration: CON, ACP=False (PHB p.69: NO  -- correct)
                - Spot:          WIS, ACP=False (PHB p.83: NO  -- correct)
                - Listen:        WIS, ACP=False (PHB p.78: NO  -- correct)
              All 7 implemented skills have correct ACP flags.

              Circumstance modifier: Valid SRD modifier type. SRD states:
              "Give the skill user a +2 circumstance bonus to represent
              conditions that improve performance" / "-2 circumstance penalty
              to represent conditions that hamper performance." Circumstance
              bonuses stack with all other bonus types per SRD stacking rules.

              Scope note: Racial bonuses and feat bonuses are not modeled as
              separate inputs. This is a feature gap, not a formula error --
              the formula structure is correct for the modifiers it handles.
```

---

### H-SKILL-173 -- Success Threshold

```
FORMULA ID:   H-SKILL-173
FILE:         aidm/core/skill_resolver.py
LINE:         173
CODE:         success=(total >= dc)
RULE SOURCE:  SRD 3.5e, PHB Chapter 4: "If the result of a skill check equals
              or exceeds the Difficulty Class, the check is successful."
EXPECTED:     success = (total >= DC)
ACTUAL:       success = (total >= dc)
VERDICT:      CORRECT
NOTES:        Direct match. The >= operator correctly implements "equals or
              exceeds."

              Important SRD detail correctly handled: Unlike attack rolls and
              saving throws, skill checks do NOT have natural 20 auto-success
              or natural 1 auto-failure. SRD: "Unlike with attack rolls and
              saving throws, a natural roll of 20 on the d20 is not an
              automatic success, and a natural roll of 1 is not an automatic
              failure." The code correctly omits nat-20/nat-1 special handling
              for skill checks.
```

---

### H-SKILL-233-234 -- Opposed Check d20 Rolls

```
FORMULA ID:   H-SKILL-233-234
FILE:         aidm/core/skill_resolver.py
LINE:         233-234
CODE:         actor_d20 = combat_rng.randint(1, 20)
              opponent_d20 = combat_rng.randint(1, 20)
RULE SOURCE:  SRD 3.5e, PHB Chapter 4, Opposed Checks: "An opposed check is a
              check whose success or failure is determined by comparing the
              check result to another character's check result." Both sides
              roll 1d20 + skill modifier.
EXPECTED:     Both actor and opponent roll 1d20 independently.
ACTUAL:       Both roll combat_rng.randint(1, 20) independently via the same
              RNG stream.
VERDICT:      CORRECT
NOTES:        Direct match. Both sides roll d20 independently as required by
              the SRD. The rolls are sequential from the same RNG stream,
              which is an implementation detail that does not affect correctness
              (both produce uniform [1,20] values).
```

---

### H-SKILL-241-249 -- Opposed Check Totals

```
FORMULA ID:   H-SKILL-241-249
FILE:         aidm/core/skill_resolver.py
LINE:         241, 248-249
CODE:         actor_total = actor_d20 + actor_ability_mod + actor_ranks
                + actor_circumstance - actor_acp
              opponent_total = opponent_d20 + opponent_ability_mod
                + opponent_ranks + opponent_circumstance - opponent_acp
RULE SOURCE:  SRD 3.5e, PHB Chapter 4, Opposed Checks: "An opposed check is a
              check whose success or failure is determined by comparing the
              check result to another character's check result." Each side's
              check result is computed as a standard skill check (1d20 + skill
              modifier).
EXPECTED:     Each side: 1d20 + ability_mod + ranks + misc_modifiers
ACTUAL:       Each side: d20 + ability_mod + ranks + circumstance - acp
              (ACP conditionally applied per skill_def.armor_check_penalty)
VERDICT:      UNCITED
NOTES:        The formula structure is correct -- it applies the standard skill
              check formula (H-SKILL-170) to each side of the opposed check.
              The SRD does not separately define an "opposed check total
              formula"; it simply says both sides make skill checks. The
              application of the standard formula (including conditional ACP)
              to each side of an opposed check is inferred rather than directly
              cited.

              This inference is extremely strong: the SRD says "each character
              makes a skill check" for opposed checks, and the standard skill
              check formula includes ACP for applicable skills. There is no
              SRD text suggesting opposed checks use a different formula.

              Functionally equivalent to CORRECT. Marked UNCITED only because
              the SRD uses the word "check" for opposed rolls without
              re-stating the full formula.
```

---

### H-SKILL-254 -- Opposed Check Tie-Breaking

```
FORMULA ID:   H-SKILL-254
FILE:         aidm/core/skill_resolver.py
LINE:         254
CODE:         actor_wins = (actor_total >= opponent_total)
RULE SOURCE:  SRD 3.5e, PHB Chapter 4, Opposed Checks: "In case of a tie, the
              higher skill modifier wins. If these scores are the same, roll
              again to break the tie."
EXPECTED:     Higher total wins. On tie: (1) compare skill modifiers -- higher
              modifier wins. (2) If modifiers also tied, re-roll to break tie.
ACTUAL:       actor_wins = (actor_total >= opponent_total). Ties always go to
              the actor (active checker). No skill modifier comparison. No
              re-roll.
VERDICT:      AMBIGUOUS
NOTES:        The code uses >= to award ties to the active checker (actor).
              This is documented in the OpposedCheckResult docstring (line 60:
              "ties favor the active checker") and exposed via the `tie` field
              (line 253).

              SRD RAW specifies a two-step tie-breaking procedure:
                Step 1: Compare skill modifiers (ranks + ability_mod + misc).
                        Higher modifier wins.
                Step 2: If modifiers are also tied, roll again to break the
                        tie (potentially recursive).

              The code does neither step. It simply awards ties to the actor.
              This is a common house rule / simplification used in many D&D
              implementations but does NOT match SRD RAW.

              Impact assessment: Ties are statistically rare (roughly 5%
              probability for equal-modifier combatants, less for unequal).
              When they occur, the code's approach:
                - Differs from RAW when the opponent has a higher modifier
                  (RAW would give the win to the opponent; code gives it to
                  the actor).
                - Differs from RAW when modifiers are equal (RAW would re-roll;
                  code gives it to the actor without re-rolling).
                - Matches RAW when the actor has a higher modifier (both give
                  the win to the actor).

              Design decision required: Keep current simplification (document
              as intentional house rule) or implement SRD two-step tie-break.
```

---

## Bug List

No WRONG verdicts found. No bugs to report.

---

## Ambiguity Register

| ID | Formula | Issue | SRD RAW | Code Behavior | Impact |
|----|---------|-------|---------|---------------|--------|
| AMBIG-H-001 | H-SKILL-254 | Opposed check tie-breaking | Compare skill modifiers, then re-roll if still tied | Ties always go to active checker (actor) via `>=` | Incorrect result when opponent has higher modifier but same total; skips re-roll when modifiers are equal |

**Design decision required for AMBIG-H-001:**
- **(a)** Keep current behavior -- document as intentional simplification / house rule. Avoids recursive re-roll loops. Simple and deterministic.
- **(b)** Implement SRD-compliant two-step tie-break: compare modifiers, then re-roll. More faithful to RAW but adds complexity and potential for infinite loops (bounded re-roll needed).

---

## Supplementary Verification: Skill Definitions

The 7 implemented skills in `aidm/schemas/skills.py` were cross-checked:

| Skill | Key Ability (Code) | Key Ability (SRD) | ACP (Code) | ACP (SRD) | Trained Only (Code) | Trained Only (SRD) | Match |
|-------|-------------------|-------------------|------------|-----------|--------------------|--------------------|-------|
| Tumble | DEX | DEX | True | Yes | True | Yes | YES |
| Concentration | CON | CON | False | No | False | No | YES |
| Hide | DEX | DEX | True | Yes | False | No | YES |
| Move Silently | DEX | DEX | True | Yes | False | No | YES |
| Spot | WIS | WIS | False | No | False | No | YES |
| Listen | WIS | WIS | False | No | False | No | YES |
| Balance | DEX | DEX | True | Yes | False | No | YES |

All 7 skill definitions match the SRD.

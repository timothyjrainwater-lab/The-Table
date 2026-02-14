# AMBIGUOUS Verdicts Decision Log — Bone-Layer Verification

**Generated:** 2026-02-14
**Source:** 9 domain verification files (DOMAIN_A through DOMAIN_I)
**Total AMBIGUOUS verdicts:** 28 (was 24; +4 reclassified from WRONG during Domain A re-verify)
**Purpose:** Present all AMBIGUOUS verdicts to Operator for design decisions. Each verdict needs a binary decision: adopt SRD strict, adopt simplification, or adopt Pathfinder correction.

---

## How To Use This Document

For each AMBIGUOUS verdict:
1. Read the description and options
2. Mark your decision in the **DECISION** field
3. Once all decisions are made, PM will create fix WOs for any that require code changes

**Decision format:** Write one of:
- `KEEP` — keep current code behavior, document as intentional
- `FIX-SRD` — change code to match strict SRD 3.5e
- `FIX-PF` — change code to match Pathfinder correction
- `CUSTOM: [description]` — custom decision with explanation

---

## Domain D — Conditions & Modifiers (5 AMBIGUOUS)

### D-AMB-01: Nauseated — actions_prohibited=True (over-restrictive)
- **Formula:** D-conditions-schema-450
- **Code:** `actions_prohibited=True` — blocks ALL actions
- **SRD says:** Nauseated allows a single move action per turn (no standard, full-round, or extra actions)
- **Gap:** No `move_action_only` flag exists in ConditionModifiers schema
- **Options:**
  - `KEEP` — accept over-restriction until action economy system (CP-17+) adds move-action-only support
  - `FIX-SRD` — add `move_action_only` field to ConditionModifiers, set Nauseated to use it
- **DECISION:** ____________

### D-AMB-02: Paralyzed — ac_modifier=-4 (same as Helpless, melee/ranged issue)
- **Formula:** D-conditions-schema-504
- **Code:** `ac_modifier=-4` flat (same as Helpless BUG-4)
- **SRD says:** Paralyzed has effective Dex of 0 (–5 mod to AC) and is treated as helpless. Melee attackers get +4, ranged get no special bonus.
- **Note:** This will be automatically fixed when BUG-4 (FIX-WO-03) is resolved. No separate decision needed.
- **DECISION:** _AUTO-FIX via FIX-WO-03_

### D-AMB-03: Unconscious — ac_modifier=-4 (same as Helpless, melee/ranged issue)
- **Formula:** D-conditions-schema-541
- **Code:** `ac_modifier=-4` flat (same as Helpless BUG-4)
- **SRD says:** Unconscious is helpless. Same melee/ranged differentiation applies.
- **Note:** Same as D-AMB-02 — auto-fixed by FIX-WO-03.
- **DECISION:** _AUTO-FIX via FIX-WO-03_

### D-AMB-04: Grappled — Pathfinder -4 Dex vs 3.5e loses-Dex-to-AC
- **Formula:** D-conditions-schema-254
- **Code:** `dex_modifier=-4` (Pathfinder approach)
- **SRD 3.5e says:** "You lose your Dexterity bonus to AC (if any) against opponents you are not grappling." No flat -4 penalty.
- **Pathfinder says:** "–4 penalty to Dexterity" while grappling (flat penalty, simpler)
- **Context:** 3.5e grapple rules are notoriously complex. Pathfinder's simplification is widely regarded as an improvement.
- **Options:**
  - `FIX-SRD` — change to `loses_dex_to_ac=True` (contextual, only vs non-grappling opponents)
  - `FIX-PF` — keep `-4 Dex` as current code (simpler, handles the common case)
  - `KEEP` — same as FIX-PF, document as intentional Pathfinder adoption
- **DECISION:** ____________

### D-AMB-05: Grappled — negative Dex modifier impact on AC
- **Formula:** D-UNCITED-06
- **Code:** If Pathfinder -4 Dex penalty drops effective Dex bonus below 0, resolvers must correctly apply negative modifier to AC
- **Note:** This is an implementation concern, not a rules ambiguity. Depends on D-AMB-04 decision.
- **DECISION:** _DEPENDS ON D-AMB-04_

---

## Domain A — Attack Resolution (4 AMBIGUOUS)

### A-AMB-01: Defeated threshold (HP <= 0 simplification)
- **Formula:** A-attack-resolver-442
- **Code:** `defeated = hp_after <= 0`
- **SRD says:** Disabled at 0 HP (can still act), Dying at -1 to -9 (bleeding out), Dead at -10
- **Impact:** Engine cannot model disabled (0 HP, still fighting), dying (stabilization checks), or the -10 death threshold
- **Options:**
  - `KEEP` — accept HP <= 0 as "out of fight" simplification for current tier
  - `FIX-SRD` — implement three-state HP system (disabled/dying/dead) — significant architectural change
- **DECISION:** ____________

### A-AMB-02: Flanking angle threshold (135 degrees)
- **Formula:** A-flanking-49
- **Code:** `MIN_FLANKING_ANGLE = 135.0` degrees between two allies through target
- **SRD says:** Allies must be on "opposite sides" — draw line through center, flankers must be on opposite sides of this line
- **Impact:** 135 degrees is a widely accepted geometric approximation. Exact for Medium creatures. May have edge cases for Large+.
- **Options:**
  - `KEEP` — 135 degrees is the standard VTT interpretation
  - `FIX-SRD` — implement exact "line through center" test (more complex, marginal accuracy improvement)
- **DECISION:** ____________

### A-AMB-03: Chebyshev distance for reach
- **Formula:** A-reach-116-118
- **Code:** Uses Chebyshev distance (max of dx, dy) for reach measurement
- **SRD says:** Reach uses the same grid as everything else (5-10-5-10 diagonal counting)
- **Impact:** Chebyshev is slightly generous on diagonals for reach >= 10ft. Matches PHB threatened-area diagrams. Common VTT simplification.
- **Options:**
  - `KEEP` — Chebyshev is the standard digital implementation for reach
  - `FIX-SRD` — use 5-10-5-10 distance for reach checks (inconsistent with most VTTs)
- **DECISION:** ____________

### A-AMB-04: Critical damage multiplication vs re-rolling
- **Formula:** A-attack-resolver-369
- **Code:** Multiplies single damage roll by critical multiplier
- **SRD says:** "Roll damage dice additional times and add results" (re-roll, don't multiply)
- **Impact:** Mathematically equivalent expected value. Multiplying has lower variance than re-rolling. Universal digital implementation shortcut.
- **Options:**
  - `KEEP` — multiplication is the universal digital standard
  - `FIX-SRD` — re-roll dice (more variance, matches physical play exactly)
- **DECISION:** ____________

### A-AMB-05: Cover AC bonus values (reclassified from WRONG — BUG-10)
- **Formula:** A-cover-resolver-97-98
- **Code:** HALF_COVER = +2 AC, +1 Ref. THREE_QUARTERS = +5 AC, +2 Ref.
- **SRD says:** Standard cover = +4 AC, +2 Ref. Improved cover = +8 AC, +4 Ref. No "half" or "three-quarters" tiers.
- **Research finding:** RQ-BOX-001 Finding 3 documents this as an intentional 4-tier graduated cover system. The project adopted a more granular model than the SRD's binary cover.
- **Reclassification:** Was BUG-10 (WRONG). Reclassified to AMBIGUOUS because it's a documented design decision, not an oversight.
- **Options:**
  - `KEEP` — 4-tier graduated cover is the documented design decision from RQ-BOX-001
  - `FIX-SRD` — collapse to SRD 2-tier: standard (+4/+2) and improved (+8/+4)
- **DECISION:** ____________

### A-AMB-06: Cover Reflex bonus values (reclassified from WRONG — BUG-10 cascade)
- **Formula:** A-cover-resolver-97-98 (Reflex component)
- **Code:** Same values as A-AMB-05, Reflex side
- **Note:** Same root cause as A-AMB-05. Decision cascades from A-AMB-05.
- **DECISION:** _CASCADES FROM A-AMB-05_

---

## Domain B — Combat Maneuvers (3 AMBIGUOUS)

### B-AMB-01: Touch AC simplified (omits deflection/dodge/insight)
- **Formula:** B-MR-98
- **Code:** Touch AC = 10 + Dex + size only
- **SRD says:** Touch AC includes deflection, dodge, insight, luck, morale, profane, sacred bonuses — all non-armor/shield/natural-armor bonuses
- **Impact:** Characters with Ring of Protection (deflection), Dodge feat, etc. have lower Touch AC than they should
- **Options:**
  - `KEEP` — simplified Touch AC is acceptable for current tier (most entities don't have these bonuses)
  - `FIX-SRD` — add all applicable bonus types to Touch AC calculation
- **DECISION:** ____________

### B-AMB-02: Opposed check tie-breaking (ties to defender)
- **Formula:** B-MR-131
- **Code:** Ties always go to defender
- **SRD says:** Compare total modifiers; higher modifier wins. If modifiers are equal, re-roll.
- **Pathfinder says:** Uses CMD (static defense), no ties possible
- **Options:**
  - `KEEP` — defender-wins-ties is simpler, avoids re-roll loops
  - `FIX-SRD` — implement two-step tie-break (compare modifiers, then re-roll)
  - `FIX-PF` — convert to CMD-based system (major rework)
- **DECISION:** ____________

### B-AMB-03: Bull rush failure — no occupied-square prone check
- **Formula:** B-MR-370
- **Code:** On failed bull rush, no check for occupied square behind attacker
- **SRD says:** "If that space is occupied, you fall prone in that space"
- **Pathfinder says:** No occupied-square prone rule for bull rush
- **Options:**
  - `KEEP` — simplified, no occupied-square tracking for bull rush failure
  - `FIX-SRD` — add occupied-square check on bull rush failure
- **DECISION:** ____________

*Note: B-AMB-4/5/6 from domain file (disarm weapon type modifiers, overrun charge bonus) are counted in the checklist's 3 AMBIGUOUS. The domain file listed 6 entries but B-AMB-4 and B-AMB-5 are the same issue (attacker/defender sides of disarm).*

### B-AMB-04: Disarm — missing weapon type modifiers (+4 two-handed, -4 light)
- **Formula:** B-MR-1168, B-MR-1173
- **Code:** Disarm uses BAB + STR + size only, no weapon type modifiers
- **SRD says:** +4 for two-handed vs one-handed, -4 for light vs one-handed
- **Pathfinder says:** Uses CMB, no weapon type modifiers
- **Options:**
  - `KEEP` — simplified, consistent with Pathfinder approach
  - `FIX-SRD` — add weapon type modifiers to disarm
- **DECISION:** ____________

### B-AMB-05: Overrun charge bonus (+2)
- **Formula:** B-MR-797
- **Code:** Grants +2 bonus to overrun when charging
- **SRD says:** Charge bonus (+2 attack) is specified for bull rush but not explicitly for overrun
- **Pathfinder says:** CMB does not grant charge bonus to overrun
- **Options:**
  - `KEEP` — reasonable interpretation, grants charge bonus to overrun
  - `FIX-SRD` — remove overrun charge bonus (SRD doesn't explicitly grant it)
- **DECISION:** ____________

---

## Domain C — Saves & Spells (3 AMBIGUOUS — was 1; +2 reclassified from WRONG)

### C-AMB-01: Cover tier threshold mapping (line-blocking counts)
- **Formula:** C-SAVE-COVER
- **Code:** Maps 16-line blocking counts to 4 cover tiers (0-4=none, 5-8=half, 9-12=three-quarters, 13-16=total)
- **SRD says:** Cover is qualitative ("cover" vs "improved cover" vs "total cover") with no numeric threshold mapping
- **Note:** The bonus VALUES are being fixed (FIX-WO-05). This ambiguity is about the threshold boundaries only.
- **Options:**
  - `KEEP` — 4-tier threshold mapping is a reasonable geometric interpretation
  - `CUSTOM` — define different threshold boundaries
- **DECISION:** ____________

### C-AMB-02: Cover Reflex save bonus values (reclassified from BUG-C-001/003)
- **Formula:** C-SAVE-COVER (Reflex component)
- **Code:** Half cover Reflex = +1, Three-quarters Reflex = +2
- **SRD says:** Standard cover Reflex = +2, Improved cover Reflex = +4
- **Research finding:** Same as A-AMB-05 — RQ-BOX-001 Finding 3 documents 4-tier graduated cover as intentional design decision
- **Reclassification:** Was BUG-C-001/BUG-C-003 (WRONG). Reclassified to AMBIGUOUS because same root cause as BUG-10.
- **Note:** Decision cascades from A-AMB-05.
- **DECISION:** _CASCADES FROM A-AMB-05_

---

## Domain E — Movement & Terrain (3 AMBIGUOUS)

### E-AMB-01: Intentional fall — first 10ft free (simplified)
- **Formula:** E-TR-08A
- **Code:** Intentional fall subtracts 10ft unconditionally
- **SRD says:** DC 15 Jump/Tumble check to reduce by 10ft, and first d6 becomes nonlethal (not eliminated)
- **Impact:** More generous than SRD. No skill check required, first 10ft eliminated rather than converted to nonlethal.
- **Options:**
  - `KEEP` — accept as simplification (code comments say "DEGRADED")
  - `FIX-SRD` — implement DC 15 check + nonlethal conversion for first die
- **DECISION:** ____________

### E-AMB-02: Bareback saddle — unconscious rider stay chance
- **Formula:** E-MC-05
- **Code:** SaddleType.NONE (bareback) gets 50% chance (same as riding saddle)
- **SRD says:** "50% chance to stay in the saddle" — implies having a saddle. No bareback specification.
- **Options:**
  - `KEEP` — 50% for bareback (SRD doesn't specify a lower value)
  - `CUSTOM` — lower percentage for bareback (e.g., 25%)
- **DECISION:** ____________

### E-AMB-03: 5-foot step in difficult terrain — threshold >= 4 vs >= 2
- **Formula:** E-TR-14
- **Code:** Blocks 5-foot step only at movement_cost >= 4
- **SRD says:** "You can't take a 5-foot step in difficult terrain." Difficult = cost >= 2.
- **Impact:** Code allows 5-foot step in standard difficult terrain (cost 2-3). SRD strictly forbids it.
- **Options:**
  - `FIX-SRD` — change threshold from >= 4 to >= 2
  - `KEEP` — document as intentional house rule (allows tactical movement in moderate terrain)
- **DECISION:** ____________

---

## Domain F — Character Progression (3 AMBIGUOUS)

### F-AMB-01: Party size XP scaling (4/N multiplier)
- **Formula:** F-EXP-69
- **Code:** Uses `base_xp * (4 / party_size)` scaling
- **SRD says:** "Divide total XP equally among all party members"
- **Impact:** Both approaches are valid interpretations. Code's approach assumes base_xp is calibrated for 4-person party and scales inversely. SRD's approach divides a total pool.
- **Options:**
  - `KEEP` — 4/N scaling is a valid interpretation of the DMG guidance
  - `FIX-SRD` — change to total-pool division
- **DECISION:** ____________

### F-AMB-02: Multiclass penalty minimum 0
- **Formula:** F-EXP-117
- **Code:** `max(0.0, 1.0 - penalty)` — XP penalty cannot go below 0%
- **SRD says:** Doesn't explicitly state minimum, but mathematically no character can have >5 offending classes
- **Impact:** Edge case only — 5 unbalanced classes would hit 0%. Clamping is defensive.
- **Options:**
  - `KEEP` — defensive clamping is correct behavior
- **DECISION:** ____________

### F-AMB-03: STR 30+ encumbrance formula (integer arithmetic)
- **Formula:** F-ENC-89
- **Code:** Maps STR 30+ to base row via integer arithmetic: `base_str = strength - 10 * ((strength - 20) // 10)`
- **SRD says:** "Multiply by 4 for every 10 points above the score for that row"
- **Impact:** Code produces correct results but relies on Python integer division behavior
- **Options:**
  - `KEEP` — mathematically correct, standard implementation
- **DECISION:** ____________

---

## Domain G — Initiative & Turn (2 AMBIGUOUS)

### G-AMB-01: Initiative tie-breaking (Dex only, then actor_id)
- **Formula:** G-INIT-104
- **Code:** Tie-break by `dex_modifier` alone (ignoring misc initiative modifiers), then by `actor_id`
- **SRD says:** Tie-break by total initiative modifier (Dex + all bonuses), then re-roll
- **Impact:** Characters with Improved Initiative feat (+4 misc) don't get tie-break advantage. actor_id is deterministic instead of random re-roll.
- **Options:**
  - `KEEP` — deterministic tie-breaking is acceptable for a simulation engine
  - `FIX-SRD` — use total initiative modifier for step 1, re-roll for step 2
  - `CUSTOM` — use total initiative modifier for step 1, keep actor_id for step 2
- **DECISION:** ____________

### G-AMB-02: Round tracking convention (0-indexed vs 1-indexed)
- **Formula:** G-PLAY-ROUND
- **Code:** combat_controller.py stores 0-indexed round_index, play.py displays 1-indexed
- **SRD says:** No specific convention — rounds are narrative
- **Impact:** Not a rules violation. Risk of off-by-one if systems are combined without conversion.
- **Options:**
  - `KEEP` — document the convention, no code change needed
- **DECISION:** ____________

---

## Domain H — Skill System (1 AMBIGUOUS)

### H-AMB-01: Opposed check tie-breaking (active checker wins)
- **Formula:** H-SKILL-254
- **Code:** Active checker wins ties via `>=` comparison
- **SRD says:** Compare modifiers; higher modifier wins. If equal, re-roll.
- **Note:** Same issue as B-AMB-02 but in skill system context
- **Options:**
  - `KEEP` — simpler, avoids re-roll loops (same decision as B-AMB-02)
  - `FIX-SRD` — two-step tie-break with re-roll
- **DECISION:** ____________

---

## Domain I — Geometry & Size (2 AMBIGUOUS)

### I-AMB-01: Spiked pit simplified to 1d6
- **Formula:** I-ENV-51
- **Code:** Spiked pit deals flat 1d6 spike damage
- **SRD says:** 1d4 spikes, each dealing 1d6 damage
- **Impact:** Average damage: code=3.5, SRD=2.5*3.5=8.75. Code is significantly less damaging.
- **Note:** CP-20 design doc explicitly scopes environmental damage as simplified.
- **Options:**
  - `KEEP` — accept as CP-20 design decision (simplified hazards)
  - `FIX-SRD` — implement 1d4 spikes x 1d6 each
- **DECISION:** ____________

### I-AMB-02: TWF penalties ignore heavy off-hand when feat is present
- **Formula:** I-FEAT-386
- **Code:** TWF feat always returns -2/-2 regardless of off-hand weapon weight
- **SRD says:** TWF feat with heavy off-hand = -4/-4, with light off-hand = -2/-2
- **Impact:** Characters with TWF feat and heavy off-hand weapon get incorrect (too favorable) penalties
- **Note:** The `has_light_offhand` parameter EXISTS in the function signature but is ignored when feat is present
- **Options:**
  - `FIX-SRD` — use `has_light_offhand` parameter when TWF feat is present
  - `KEEP` — treat as simplification
- **DECISION:** ____________

---

## Quick Reference — All Decisions Needed

| ID | Domain | Short Description | Recommended |
|----|--------|-------------------|-------------|
| D-AMB-01 | D | Nauseated blocks all actions | KEEP |
| D-AMB-04 | D | Grappled: PF -4 Dex vs 3.5e loses-Dex | Operator choice |
| A-AMB-01 | A | HP <= 0 defeated (no dying/disabled) | KEEP |
| A-AMB-02 | A | Flanking 135 degrees | KEEP |
| A-AMB-03 | A | Chebyshev reach | KEEP |
| A-AMB-04 | A | Crit multiply vs re-roll | KEEP |
| A-AMB-05 | A | Cover AC values (4-tier vs SRD 2-tier) | Operator choice |
| A-AMB-06 | A | Cover Reflex values (cascade from A-AMB-05) | Cascade |
| B-AMB-01 | B | Touch AC simplified | KEEP |
| B-AMB-02 | B | Opposed ties to defender | Operator choice |
| B-AMB-03 | B | Bull rush no occupied-square prone | KEEP |
| B-AMB-04 | B | Disarm no weapon type mods | Operator choice |
| B-AMB-05 | B | Overrun charge bonus | Operator choice |
| C-AMB-01 | C | Cover tier thresholds | KEEP |
| C-AMB-02 | C | Cover Reflex values (cascade from A-AMB-05) | Cascade |
| E-AMB-01 | E | Intentional fall first 10ft free | KEEP |
| E-AMB-02 | E | Bareback 50% stay | KEEP |
| E-AMB-03 | E | 5ft step difficult terrain threshold | Operator choice |
| F-AMB-01 | F | XP 4/N scaling | KEEP |
| F-AMB-02 | F | Multiclass penalty min 0 | KEEP |
| F-AMB-03 | F | STR 30+ encumbrance int math | KEEP |
| G-AMB-01 | G | Init tiebreak Dex only + actor_id | Operator choice |
| G-AMB-02 | G | Round tracking 0-index vs 1-index | KEEP |
| H-AMB-01 | H | Opposed check active wins ties | Link to B-AMB-02 |
| I-AMB-01 | I | Spiked pit 1d6 simplified | KEEP |
| I-AMB-02 | I | TWF ignores heavy off-hand | FIX-SRD |

**Auto-resolved (no operator input needed):** D-AMB-02, D-AMB-03, D-AMB-05, A-AMB-06, C-AMB-02, F-AMB-02, F-AMB-03, G-AMB-02

**Operator decisions needed (7):** D-AMB-04, A-AMB-05 (cover design), B-AMB-02/H-AMB-01 (linked), B-AMB-04, B-AMB-05, E-AMB-03, G-AMB-01

**PM recommends KEEP (12):** D-AMB-01, A-AMB-01, A-AMB-02, A-AMB-03, A-AMB-04, B-AMB-01, B-AMB-03, C-AMB-01, E-AMB-01, E-AMB-02, F-AMB-01, I-AMB-01

**PM recommends FIX-SRD (1):** I-AMB-02 (TWF off-hand — the parameter already exists, just needs to be used)

---

## End of AMBIGUOUS Verdicts Decision Log

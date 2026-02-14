# Domain G Verification — Initiative & Turn Structure

**Domain:** G — Initiative & Turn Structure
**Verifier:** Claude (builder agent)
**Date:** 2026-02-14
**Files:** 3 (`aidm/core/initiative.py`, `play.py`, `aidm/core/combat_controller.py`)
**Formulas:** 10
**SRD Sources:** d20srd.org — Combat > Initiative, Combat > Actions in Combat, Combat > Special Attacks

---

## Summary

| Verdict | Count |
|---------|-------|
| CORRECT | 6 |
| WRONG | 2 |
| AMBIGUOUS | 2 |
| UNCITED | 0 |
| **TOTAL** | **10** |

---

## Verification Records

### aidm/core/initiative.py

---

```
FORMULA ID: G-INIT-72
FILE: aidm/core/initiative.py
LINE: 72
CODE: d20_roll = rng.stream("initiative").randint(1, 20)
RULE SOURCE: SRD 3.5e, Combat > Initiative
EXPECTED: Initiative check is a d20 roll (1d20)
ACTUAL: Rolls 1d20 via randint(1, 20)
VERDICT: CORRECT
NOTES: Standard d20 initiative roll. Matches SRD exactly.
```

---

```
FORMULA ID: G-INIT-75
FILE: aidm/core/initiative.py
LINE: 75
CODE: total = d20_roll + dex_modifier + misc_modifier
RULE SOURCE: SRD 3.5e, Combat > Initiative
EXPECTED: Initiative = d20 + Dexterity modifier + miscellaneous modifiers
         (e.g., Improved Initiative feat grants +4)
ACTUAL: total = d20_roll + dex_modifier + misc_modifier
VERDICT: CORRECT
NOTES: Formula matches SRD exactly. The misc_modifier parameter is populated
       externally (e.g., by feat_resolver.py which adds +4 for Improved Initiative
       at line 283). The function signature defaults misc_modifier to 0, which is
       correct when no miscellaneous bonuses apply. The caller
       (roll_initiative_for_all_actors) passes misc_modifiers from a dict keyed
       by actor_id, defaulting to 0 — correct behavior.
```

---

```
FORMULA ID: G-INIT-104
FILE: aidm/core/initiative.py
LINE: 104
CODE: key=lambda r: (-r.total, -r.dex_modifier, r.actor_id)
RULE SOURCE: SRD 3.5e, Combat > Initiative (Tie-Breaking)
EXPECTED: SRD tie-breaking:
         1. Higher initiative total goes first
         2. Higher initiative modifier (DEX mod + misc) goes first
         3. If still tied, re-roll
ACTUAL: Sort key uses:
        1. -total (higher total first) — CORRECT
        2. -dex_modifier (higher DEX mod first) — PARTIALLY CORRECT
        3. actor_id (lexicographic, ascending) — DEVIATION
VERDICT: AMBIGUOUS
NOTES: Two issues:
       (a) Step 2: SRD says compare "total initiative modifier" (DEX mod +
           miscellaneous), not just DEX modifier alone. The code uses only
           dex_modifier, ignoring misc_modifier. In practice, if two actors
           have the same total but different misc modifiers (e.g., one has
           DEX +2 and Improved Initiative +4 = +6, the other has DEX +6
           and no feat = +6), the code would break the tie by DEX mod alone,
           not total modifier. This is a minor deviation — the SRD says
           "total initiative modifier" but in most cases DEX mod is the
           dominant component.
       (b) Step 3: SRD says tied characters should re-roll. The code uses
           lexicographic actor_id as a deterministic substitute. This is a
           deliberate design decision for deterministic replay — documented
           in the module docstring (lines 12-16). Re-rolling would require
           additional RNG consumption and break determinism guarantees.
           This is an acceptable deviation for a deterministic engine.
       DESIGN DECISION: actor_id tiebreaker is acceptable for deterministic
       engine. However, step 2 should ideally compare (dex_modifier +
       misc_modifier) rather than dex_modifier alone.
```

---

### play.py — ActionBudget

---

```
FORMULA ID: G-PLAY-71-86
FILE: play.py
LINE: 71-86
CODE: _ACTION_COST = {
          "attack":       "standard",
          "cast":         "standard",
          "trip":         "standard",
          "bull_rush":    "standard",
          "disarm":       "standard",
          "grapple":      "standard",
          "sunder":       "standard",
          "overrun":      "standard",
          "full_attack":  "full_round",
          "move":         "move",
          "end_turn":     "end",
          "help":         "free",
          "status":       "free",
          "map":          "free",
      }
RULE SOURCE: SRD 3.5e, Combat > Actions in Combat, Combat > Special Attacks
EXPECTED: Per SRD action type table:
         - Attack (single): Standard action — CORRECT
         - Cast a spell: Standard action (most spells) — CORRECT
         - Full attack: Full-round action — CORRECT
         - Move: Move action — CORRECT
         - Trip: "Varies" — can replace a melee attack (usable in full attack, AoO) — WRONG
         - Disarm: "Varies" — can replace a melee attack (usable in full attack, AoO) — WRONG
         - Grapple: "Varies" — can replace a melee attack (usable in full attack, AoO) — WRONG
         - Bull Rush: Standard action or part of a charge — CORRECT (simplified)
         - Overrun: Standard action taken during move — CORRECT (simplified)
         - Sunder: Standard action per SRD table — CORRECT (debated; text says "melee attack")
         - help/status/map: Free (UI actions, not game actions) — N/A (engine-only)
ACTUAL: All combat maneuvers classified as "standard" action
VERDICT: WRONG
NOTES: Trip, Disarm, and Grapple are classified as "standard" in the code, but
       the SRD Action Types table marks them as "Varies" (footnote 7: "These
       attack actions are used in place of a melee attack, not an action. As
       melee attacks, they can be used once in an attack or charge action, one
       or more times in a full attack action, or even as an attack of
       opportunity."). This means:
       - Trip can replace any melee attack in a full attack sequence
       - Disarm can replace any melee attack in a full attack sequence
       - Grapple initiation (touch attack) can replace any melee attack
       The code treats them all as standard actions, which prevents using them
       during a full attack. This is a simplification that deviates from RAW.
       FIX: Trip, Disarm, and Grapple should have action type "varies" or
       "melee_attack" and be usable in place of any melee attack, including
       during full attack sequences. However, the current CLI architecture
       treats each command as a separate action, which makes "varies" actions
       complex to implement. This may be an acceptable simplification for the
       current CLI, but should be documented as a known deviation.
       Note: Bull Rush as "standard" is correct per SRD (it's a standard action
       or part of a charge). Overrun as "standard" is a simplification (SRD
       says it's a standard action taken during your move, which is more
       nuanced but functionally equivalent in the CLI). Sunder as "standard"
       matches the SRD action types table, though there is community debate
       about whether it should be "varies" like Trip/Disarm.
```

---

```
FORMULA ID: G-PLAY-92-96
FILE: play.py
LINE: 92-96
CODE: has_standard: bool = True
      has_move: bool = True
      has_swift: bool = True
      used_full_round: bool = False
      moved: bool = False
RULE SOURCE: SRD 3.5e, Combat > Actions in Combat > Action Types
EXPECTED: Each turn: 1 standard + 1 move + 1 swift + free actions,
         OR 1 full-round + 1 swift + free actions
ACTUAL: Budget initializes with 1 standard, 1 move, 1 swift.
        Full-round tracked separately. No free action limit (correct).
VERDICT: CORRECT
NOTES: Matches SRD exactly. The budget correctly models the turn structure:
       standard + move + swift, with full-round as a special case that
       consumes both standard and move. The "moved" flag correctly tracks
       whether a move action was taken (prevents full attack after moving).
```

---

```
FORMULA ID: G-PLAY-110
FILE: play.py
LINE: 110
CODE: return self.has_move or self.has_standard
      (in can_take for "move" cost)
      ...
      LINE 128-134 (in spend):
      if self.has_move:
          self.has_move = False
          self.moved = True
      elif self.has_standard:
          self.has_standard = False
          self.moved = True
RULE SOURCE: SRD 3.5e, Combat > Actions in Combat > Move Actions
EXPECTED: "You can take a move action in place of a standard action."
         This allows trading standard -> move for a second move action.
ACTUAL: can_take("move") returns True if has_move OR has_standard.
        spend("move") consumes has_move first, then falls back to has_standard.
VERDICT: CORRECT
NOTES: Correctly implements the standard-to-move trade. SRD explicitly allows
       this trade: you can take two move actions per turn by trading your
       standard action for a second move action. The code correctly prioritizes
       spending the actual move action first, then falls back to consuming the
       standard action.
```

---

```
FORMULA ID: G-PLAY-112
FILE: play.py
LINE: 112
CODE: if self.moved or not self.has_standard or not self.has_move:
          return False
      (in can_take for "full_round" cost)
RULE SOURCE: SRD 3.5e, Combat > Actions in Combat > Full-Round Actions
EXPECTED: "A full-round action consumes all your effort during a round.
          The only movement you can take during a full-round action is a
          5-foot step before, during, or after the action."
         Full-round requires both standard and move action to be available,
         and no prior movement.
ACTUAL: Returns False if: already moved, OR no standard, OR no move.
        Returns True only if all three conditions are met (not moved,
        has standard, has move).
VERDICT: CORRECT
NOTES: Correctly enforces full-round prerequisites. A full attack (the primary
       full-round action) requires the character to not have moved (except a
       5-foot step, which is handled separately — the 5-foot step doesn't
       consume the move action and doesn't set moved=True). The code correctly
       prevents full attack after movement and requires both action slots.
```

---

```
FORMULA ID: G-PLAY-SWIFT
FILE: play.py
LINE: 117-118
CODE: if cost == "swift":
          return self.has_swift
      (in can_take)
      LINE 139-140 (in spend):
      elif cost == "swift":
          self.has_swift = False
RULE SOURCE: SRD 3.5e, Combat > Actions in Combat > Swift Actions
EXPECTED: "You can perform only a single swift action per turn."
ACTUAL: has_swift starts True, set to False when spent. can_take returns
        has_swift value. Only one swift action allowed per turn.
VERDICT: CORRECT
NOTES: Correctly implements one-swift-per-turn rule. The SRD states
       "You can perform one swift action per turn without affecting your
       ability to perform other actions." The code correctly tracks this
       as a separate boolean that doesn't interact with standard/move/
       full-round budgets.
```

---

### play.py — Round Management (additional formula from play.py main loop)

---

```
FORMULA ID: G-PLAY-ROUND
FILE: play.py
LINE: 1029-1030
CODE: round_number += 1
      ws.active_combat["round_index"] = round_number - 1
RULE SOURCE: SRD 3.5e, Combat > How Combat Works
EXPECTED: After all actors have acted in initiative order, a new round begins.
         Rounds increment by 1.
ACTUAL: round_number increments by 1 at the end of each complete initiative
        cycle. round_index is stored as 0-indexed (round_number - 1).
VERDICT: AMBIGUOUS
NOTES: The round increment is correct (each round follows the previous).
       However, there is a discrepancy between the 1-indexed round_number
       (used for display) and the 0-indexed round_index stored in
       active_combat. This is not a rules violation but a potential source
       of off-by-one bugs. The combat_controller.py uses round_index
       differently — it reads from active_combat and adds 1 (line 249).
       The two systems (play.py main loop and combat_controller.py) use
       different round tracking conventions that could conflict if both
       were used simultaneously. Since play.py is the CLI and
       combat_controller.py is the headless combat runner, they don't
       currently conflict, but the inconsistency should be documented.
```

---

### aidm/core/combat_controller.py

---

```
FORMULA ID: G-CC-249
FILE: aidm/core/combat_controller.py
LINE: 249
CODE: current_round = world_state.active_combat.get("round_index", 0) + 1
RULE SOURCE: Basic round increment (uncited — no specific SRD rule beyond
             "combat proceeds in rounds")
EXPECTED: Each round increments by 1 from the previous round.
ACTUAL: Reads round_index (default 0), adds 1 to get current round number.
        Result stored back to active_combat["round_index"] at line 341.
VERDICT: CORRECT
NOTES: Simple increment. round_index starts at 0 (set in start_combat at
       line 202), first call produces round 1. Subsequent calls produce
       2, 3, etc. The value is written back at line 341. This is a
       straightforward counter with no SRD-specific rule to violate.
```

---

## Bug Summary

### WRONG Verdicts

| Formula ID | Description | Severity | Fix |
|-----------|-------------|----------|-----|
| G-PLAY-71-86 | Trip, Disarm, Grapple classified as "standard" instead of "varies" (melee attack substitution) | MEDIUM | Change action type for trip/disarm/grapple to allow substitution for any melee attack, including during full attack. Requires architectural change to CLI action parsing. |

### AMBIGUOUS Verdicts

| Formula ID | Description | Design Decision |
|-----------|-------------|-----------------|
| G-INIT-104 | Tie-breaking uses dex_modifier alone instead of total initiative modifier; uses actor_id instead of re-roll | actor_id tiebreaker is acceptable for deterministic engine. Tie-breaking by DEX only (ignoring misc) is a minor deviation — should use (dex_modifier + misc_modifier) for step 2. |
| G-PLAY-ROUND | Round tracking uses different conventions in play.py (1-indexed display) vs combat_controller.py (0-indexed storage + 1) | Not a rules violation. Potential off-by-one risk if systems are combined. Document convention. |

---

## Wrong Count Breakdown

- **Trip as standard**: SRD says "varies" (melee attack replacement). Code says "standard". **WRONG.**
- **Disarm as standard**: SRD says "varies" (melee attack replacement). Code says "standard". **WRONG.**
- **Grapple as standard**: SRD says "varies" (melee attack replacement). Code says "standard". **WRONG.**

These are counted as **1 WRONG formula** (G-PLAY-71-86) because they are all entries in the same action cost table. The single table has 3 incorrect entries out of 14 total entries.

Additionally, **bull_rush as "standard"** is noted as a simplification. SRD says "standard action or as part of a charge" — the code's classification as "standard" is correct for the standalone case but doesn't support the charge variant. This is an acceptable simplification given the CLI architecture and is not counted as WRONG.

**Overrun as "standard"** is a simplification. SRD says "standard action taken during your move" — functionally equivalent in the CLI. Not counted as WRONG.

**Sunder as "standard"** matches the SRD Action Types table classification. Community debate exists about whether it should be "varies" like Trip/Disarm, but the official table says "standard". Not counted as WRONG.

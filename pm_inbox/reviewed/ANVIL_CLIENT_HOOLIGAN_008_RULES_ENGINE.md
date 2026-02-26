# Rules Engine Audit — ANVIL-CLIENT-HOOLIGAN-008
**Filed by:** Anvil (BS Buddy seat), 2026-02-25
**Status:** FINDINGS — eight rules systems mapped to HOOLIGAN-004/005 edge cases
**Method:** Direct read of aidm/core/ resolver and validator modules
**Depends on:** HOOLIGAN-004 (rules-crack probes), HOOLIGAN-006 (invariants)

---

## What Was Read

- `aidm/core/action_economy.py`
- `aidm/core/movement_resolver.py`
- `aidm/core/aoo.py`
- `aidm/core/attack_resolver.py`
- `aidm/schemas/conditions.py` + `aidm/core/conditions.py` + `aidm/core/condition_combat_resolver.py`
- `aidm/core/sneak_attack.py`
- `aidm/core/maneuver_resolver.py`
- `aidm/core/dying_resolver.py`

---

## Summary Table

| Area | Status | Critical Gap |
|---|---|---|
| Action economy | PARTIAL | Free actions unlimited; no overflow guard |
| Movement | PARTIAL | 5-ft step unenforced; charge geometry not validated; no Tumble/Overrun bypass |
| AoO | PARTIAL | Combat Reflexes multiplier absent; Concentration check on melee cast missing |
| Bonus stacking | ABSENT | No type discipline — all bonuses sum freely |
| Condition system | PARTIAL | No fear auto-progression; no duration ticks; boolean flags metadata only |
| Sneak attack | PARTIAL | Attacker visibility not checked; concealment not verified |
| Grapple | PARTIAL | Movement restriction not enforced; casting DC not enforced |
| Death/dying | PARTIAL | Nonlethal HP not tracked separately |

**Zero systems are fully implemented against 3.5 RAW.**
**One system (bonus stacking) is not implemented at all.**

---

## 1 — Action Economy (PARTIAL)

**File:** `action_economy.py`

**Implemented:**
- `ActionBudget` tracks standard, move, swift, full-round, five-foot-step slots
- `can_use()` enforces mutual exclusions: standard blocked if full-round used; move
  blocked if 5-ft-step taken; 5-ft-step blocked if move taken
- `consume()` marks slots correctly
- Full-round correctly requires both standard AND move unused

**Gaps — RC-006 (Free Action Inflation):**
Free actions return `True` unconditionally (line 60). Code comment acknowledges
"unlimited free actions controlled at caller level." The caller does not limit them.
Drop item 30 times. Shout 30 times. All free. No cap enforced anywhere.

**Gaps — RC-007 (Draw/Stow Sequencing):**
Unknown intent types default to "free" action (line 207). If the intent parser
produces an unknown type for weapon draw/stow, it costs nothing. No hand occupancy
tracking visible in action_economy.py.

**Gap — Overflow:**
No check prevents consuming standard then move separately before a full-round
attempt. The full-round check requires both unused, but if standard and move were
already consumed individually, no overflow event is emitted — the full-round is
simply denied with no explanation that both were already spent.

**HOOLIGAN-004 probes affected:** RC-006, RC-007

---

## 2 — Movement Validation (PARTIAL)

**File:** `movement_resolver.py`

**Implemented:**
- Dijkstra pathfinding with 5/10/5 diagonal cost (line 91: odd diagonal = 5 ft,
  even = 10 ft) — RC-008 PASSES
- Enemy square blocking (line 164) — correct baseline
- Terrain cost integration

**Gap — RC-009 (5-Foot Step Rules):**
`StepMoveIntent` exists but `movement_resolver.py` does not validate:
- Whether any move action was already used this turn
- Whether the square is difficult terrain
- Whether the entity stood up from prone this action

The 5-ft step is treated as a short move, not a distinct movement mode with special
constraints. A player who moved 30 ft can then "5-ft step" in the same turn.

**Gap — RC-011 (Charge Geometry):**
`ChargeIntent.is_path_unobstructed` is a boolean parameter the caller passes in.
The engine trusts it. The engine does NOT verify:
- Straight-line geometry to target
- Minimum 10-ft movement
- Path clear of obstacles independent of caller assertion

A caller (or upstream parser) that sets `is_path_unobstructed=True` on a curved
path gets a charge with no engine-side rejection.

**Gap — Tumble/Overrun through enemy squares:**
Enemy squares are hard-blocked (line 164). No path exists for "move through with
Tumble DC 25 check" or Overrun. A player cannot legally move through an enemy's
square even if they have Tumble ranks, because the movement resolver provides no
mechanism for it.

**HOOLIGAN-004 probes affected:** RC-009, RC-010, RC-011

---

## 3 — AoO System (PARTIAL)

**File:** `aoo.py`

**Implemented:**
- Leaving threatened square provokes (lines 230-235) — RC-012 PASSES
- Spellcasting provokes (lines 302-310) — TRIGGERS correctly
- Ranged attack provokes (lines 290-298)
- Combat maneuver provokes (lines 245-285)
- One AoO per reactor per round enforced via `aoo_used_this_round` list
- Withdrawal action suppresses AoO from first square (lines 318-320) — RC-012 PASSES
- Tumble DC 15 avoidance for movement AoO (lines 494-544) — IMPLEMENTED
- Cover blocking AoO (lines 468-492) — IMPLEMENTED
- Provoker-defeated check after each AoO in sequence (lines 654-657) — IMPLEMENTED

**Gap — RC-014 (Combat Reflexes):**
`aoo.py` explicitly states "no Combat Reflexes feat" is in scope (lines 11-13).
Combat Reflexes support is in a separate `combat_reflexes.py` — whether it
integrates with aoo.py's cap enforcement is unknown from this read. Without
Combat Reflexes, every creature is hard-capped at one AoO per round regardless
of feats. A player with Combat Reflexes gets no additional AoOs.

**Gap — RC-013 (Casting in Melee — Concentration Check):**
When spellcasting provokes (lines 302-310), the AoO triggers but the code does
not enforce:
- Concentration check DC (10 + damage taken + spell level)
- Spell fails if Concentration check fails

The AoO fires. The spell fires. They are not sequenced so that the AoO result
informs whether the spell is lost. Concentration check exists elsewhere in the
codebase (play_loop.py references it) but is not wired through the AoO trigger path.

**Gap — TODO in code:**
Line 588-592 in aoo.py contains a TODO: Mobility feat AC bonus NOT applied to
AoOs. This is a known incomplete item left in the code.

**HOOLIGAN-004 probes affected:** RC-012 (PASSES), RC-013 (FAILS), RC-014 (PARTIAL)

---

## 4 — Bonus Stacking / Type Discipline (NOT IMPLEMENTED)

**File:** `attack_resolver.py` (primary sink for bonus aggregation)

**Implemented:**
Nothing. All bonuses are summed numerically with no type tracking.

**The gap:**
No `BonusType` enum. No same-type-doesn't-stack rule. No tracking of whether
a bonus is enhancement, morale, deflection, dodge, untyped, circumstance, etc.

Flanking +2 is added (lines 303-309). Mounted bonus added. Terrain bonus added.
Condition modifiers summed (line 328: `total_attack += mods.attack_modifier`).
AC components stacked. Two-Weapon Defense added. Fight Defensively added.

None of these carry type metadata. None are checked against each other.

**The exploit in play (RC-015):**
Two enhancement bonuses to STR — both apply. Two morale bonuses to attack —
both apply. Two deflection bonuses to AC — both apply. A player who knows this
can stack same-type buffs for illegal bonuses with no engine resistance.

This is not a gap in an edge case. This is the entire bonus system missing its
fundamental enforcement rule. D&D 3.5 combat math is built on the assumption that
same-type bonuses don't stack. Without that enforcement, every buff combination
is potentially broken.

**Severity: CRITICAL**

**HOOLIGAN-004 probes affected:** RC-015, RC-016 (partial)

---

## 5 — Condition System (PARTIAL)

**Files:** `schemas/conditions.py`, `conditions.py`, `condition_combat_resolver.py`

**Implemented:**
- 17+ condition types defined as enum (PRONE, GRAPPLED, SHAKEN, FRIGHTENED, etc.)
- Numeric modifiers per condition (AC, attack, saves, Dex)
- Boolean flags (movement_prohibited, actions_prohibited, etc.) — but see gap below
- Blinded: 50% miss, -2 AC, loses Dex — implemented
- Confused: d100 behavior roll — implemented
- Fear conditions: shaken, frightened, panicked defined as separate types

**Gap — Boolean flags are metadata only:**
`conditions.py` line 101-114 comment: "NO ENFORCEMENT IN THIS MODULE."
`movement_prohibited=True` is stored but `movement_resolver.py` does not read it.
`actions_prohibited=True` is stored but `action_economy.py` does not read it.
Conditions describe what should be restricted. The restriction is not enforced.

**The exploit in play:**
A grappled creature (GRAPPLED condition, `movement_prohibited=True`) can still
move freely because `movement_resolver.py` does not check condition flags.
A stunned creature (`actions_prohibited=True`) can still act.

**Gap — RC-017 (Duration Ticks):**
`conditions.py` line 136-140: "No duration tracking. Manual removal only."
Conditions applied during combat persist indefinitely until explicitly removed.
A 1-round stun lasts forever unless the resolver that applied it also removes it
at the right turn boundary. Duration tick model is not systematically enforced.

**Gap — RC-012 Fear Progression:**
Three fear conditions are defined separately (shaken, frightened, panicked).
No code automatically upgrades shaken → frightened when a second fear source
is applied. Manual application only. A second fear source on an already-shaken
creature simply overwrites (line 162: identical condition types overwrite) or
is added as a separate entry with no promotion logic.

**Gap — Concealment + Precision (RC-013 analog):**
`sneak_attack.py` line 22 comment: "Not effective if attacker cannot see the
target." This is not implemented. Concealment miss chance is in `concealment.py`
but `sneak_attack.py` does not call it. Sneak attack applies through concealment.

**HOOLIGAN-004 probes affected:** RC-017, RC-018
**HOOLIGAN-005 probes affected:** A-004 (invisibility), A-012 (fear stacking),
A-013 (concealment vs precision)

---

## 6 — Sneak Attack Eligibility (PARTIAL)

**File:** `sneak_attack.py`

**Implemented:**
- Immune creature type check (undead, construct, ooze, plant, elemental,
  incorporeal) — RC-016 partial PASS
- Explicit flag checks (immune_to_critical_hits, immune_to_sneak_attack)
- Flanking OR denied Dex — correct eligibility trigger
- Ranged 30-ft limit — IMPLEMENTED
- Precision damage excluded from crit multiplier (handled in attack_resolver.py)

**Gap — Attacker visibility not verified:**
`sneak_attack.py` line 22 comment acknowledges the requirement. Not implemented.
`is_sneak_attack_eligible()` accepts `is_flanking` and `is_denied_dex_to_ac` as
parameters (line 128) but has no visibility or line-of-sight check. An invisible
attacker (or one behind total concealment) can sneak attack.

**Gap — Concealment miss not integrated:**
Sneak attack fires even if the attack would miss due to concealment. The 50% miss
from concealment and the sneak attack eligibility are not connected. If the attack
beats AC but misses concealment, no sneak attack. Code does not enforce this.

**Gap — Flanking geometry not reverified:**
`is_flanking` is accepted as caller-provided boolean. `sneak_attack.py` does not
re-verify flanking geometry. If the upstream caller miscalculates flanking, the
engine applies sneak attack damage to a non-flanked target.

**HOOLIGAN-004 probes affected:** RC-013 (concealment), RC-016 (flanking geometry)

---

## 7 — Grapple State Machine (PARTIAL)

**File:** `maneuver_resolver.py` (grapple section)

**Implemented:**
- Touch attack to initiate — correct
- Opposed grapple check (BAB + Str + size modifier)
- Pin escalation (already grappling same target → pin attempt)
- Grapple pair tracking in `active_combat["grapple_pairs"]`
- Escape via opposed check, conditions removed on success

**Gap — RC-003 (Grapple Movement):**
GRAPPLED condition has `movement_prohibited=True` but (per Section 5 above)
`movement_resolver.py` does not read condition flags. A grappled creature can
move freely. Grapple pair does not move together. Grappler does not control
direction. The physical constraint of grapple is entirely absent from movement.

**Gap — Casting while grappled (A-003):**
Concentration DC 20 + grapple modifier not enforced when a grappled caster
attempts a spell. The condition is tracked. The spell resolver does not check
it. A grappled Wizard casts freely.

**Gap — Grapple action restrictions:**
Grappled creature cannot make standard melee attacks, cannot use ranged weapons.
These restrictions are not enforced by action_economy.py or attack_resolver.py.
The `actions_prohibited` flag approach fails here for the same reason as Section 5.

**HOOLIGAN-004 probes affected:** RC-003 (analog), A-003

---

## 8 — Death / Dying State Machine (PARTIAL)

**File:** `dying_resolver.py`

**Implemented:**
- HP band classification: 0=disabled, -1 to -9=dying, ≤-10=dead — CORRECT
- Fort save DC 10 per dying entity per round — CORRECT
- Stabilization sets STABLE flag — CORRECT
- Auto-death at -10 HP — CORRECT
- Dying entity loses 1 HP/round on failed save — CORRECT

**Gap — Nonlethal HP:**
No separate nonlethal HP pool in `entity_fields.py`. PHB p.145 tracks nonlethal
damage separately — a creature goes unconscious when nonlethal damage equals
current HP, not dead. With a single HP pool, nonlethal and lethal damage are
indistinguishable. RC-022 (nonlethal edge cases) cannot be tested because the
data model doesn't support the distinction.

**Gap — Stable creature bleeds 1 HP/hour:**
Code sets STABLE. No hourly bleed is tracked. In a long session with in-game
hours passing, a "stable" creature at -5 HP who isn't healed would die from
bleeding. Engine doesn't model this.

**Gap — Ability score death:**
STR drained to 0 = dead. CON drained to 0 = dead. No ability drain death
tracking visible. Ability damage (not drain) to 0 in a score → different
outcomes depending on score. None of this is in dying_resolver.py.

**HOOLIGAN-004 probes affected:** RC-022

---

## The Critical Cascade

The condition system boolean flags not being enforced by other modules is not
one gap. It is the root cause of multiple gaps:

```
Condition flag set (conditions.py)
    → NOT read by movement_resolver.py   → grapple/stun movement unrestricted
    → NOT read by action_economy.py      → stunned/paralyzed creatures act freely
    → NOT read by attack_resolver.py     → helpless creatures attack freely
    → NOT read by aoo.py                 → flat-footed creatures make AoOs
```

Every system that should respect condition restrictions does not, because the
boolean flags were designed as metadata and never wired into enforcement.

This is the architectural version of VIOLATION-006 (dm-panel.js checking the
wrong class). The conditions are defined. The enforcement is disconnected.

---

## Exploit Map Against HOOLIGAN-004 Probes

| Probe | Status | Engine Gap |
|---|---|---|
| RC-006 Free action spam | OPEN | `can_use()` returns True unconditionally for free |
| RC-007 Draw/stow sequencing | OPEN | No hand occupancy tracking |
| RC-008 Diagonal movement | PASS | 5/10/5 correct |
| RC-009 5-ft step violations | OPEN | No special validation for step mode |
| RC-010 Pass-through/overlap | PARTIAL | Enemy blocked; no Tumble bypass |
| RC-011 Charge geometry | OPEN | Engine trusts caller's `is_path_unobstructed` |
| RC-012 Leaving threatened/AoO | PASS | Triggers correctly |
| RC-013 Casting in melee | PARTIAL | AoO triggers; Concentration check not wired |
| RC-014 AoO cap | PARTIAL | 1/round enforced; Combat Reflexes not in scope |
| RC-015 Bonus stacking | OPEN | No type system at all |
| RC-016 Flanking/sneak eligibility | PARTIAL | Flanking geometry trusted from caller |
| RC-017 Condition duration | OPEN | No tick model; manual removal only |
| RC-018 Condition independence | PARTIAL | Conditions are independent entries but flags not enforced |
| RC-022 Death/dying edge | PARTIAL | Nonlethal not tracked separately |

**Passes: 2 (RC-008, RC-012)**
**Open/fails: 7**
**Partial: 5**

---

## Recommended Slate Actions

**CRITICAL — Cut WO:**
1. **WO-ENGINE-BONUS-TYPE-001** — Implement bonus type discipline. `BonusType` enum.
   Same-type-doesn't-stack enforcement in all bonus aggregation paths.
   Without this, all combat math is wrong for any multi-buff scenario.

2. **WO-ENGINE-CONDITION-ENFORCEMENT-001** — Wire condition boolean flags to
   enforcing modules. `movement_resolver.py` reads `movement_prohibited`.
   `action_economy.py` reads `actions_prohibited`. `aoo.py` reads `flat_footed`.
   The conditions exist. The wiring is missing.

**HIGH — Cut WO:**
3. **WO-ENGINE-CONDITION-DURATION-001** — Implement systematic duration tick model.
   Conditions must expire at documented turn boundaries. Manual removal is not
   a valid long-term mechanism.

4. **WO-ENGINE-GRAPPLE-MOVEMENT-001** — Enforce grapple movement restrictions via
   condition flag wiring and grapple_pairs in movement_resolver.py.

5. **WO-ENGINE-SNEAK-VISIBILITY-001** — Wire attacker visibility and concealment
   miss chance into sneak attack eligibility.

**MEDIUM:**
6. **WO-ENGINE-5FT-STEP-001** — Validate StepMoveIntent constraints (no prior move,
   not difficult terrain, not after stand-up).

7. **WO-ENGINE-CHARGE-GEOMETRY-001** — Engine-side straight-line validation for
   ChargeIntent. Remove trust in caller-provided `is_path_unobstructed`.

8. **WO-ENGINE-NONLETHAL-001** — Separate nonlethal HP pool in entity_fields.py.

---

*Tires kicked. Lemon confirmed. Runs, but the rules are held together with good intentions.*
*Two probes pass cleanly. Twelve don't. One entire system doesn't exist.*
*The bonus type system is the load-bearing wall that isn't there.*

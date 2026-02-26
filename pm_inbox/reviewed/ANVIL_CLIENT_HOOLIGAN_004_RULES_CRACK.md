# Rules-Crack Adversarial Test Plan — ANVIL-CLIENT-HOOLIGAN-004
**Filed by:** Anvil (transcription — Thunder's analysis, 2026-02-25)
**Status:** AUTHORITATIVE — rules-boundary adversarial probes
**Depends on:** HOOLIGAN-001 through HOOLIGAN-003
**Scope:** Attacking the game, not the infrastructure. No code required. Adversarial play.

---

## The Distinction

HOOLIGAN-001/002: attacking the client (code violations)
HOOLIGAN-003: attacking the protocol (player-as-hacker)
**HOOLIGAN-004: attacking the rules model (player-as-rules-lawyer)**

This is the hardest surface to defend. Every probe below is a legal player action.
The engine either enforces the rules or it doesn't. There is no technical fix —
only a correct rules state machine.

---

## Highest-Yield Probes (Run These First)

If only three probes run, run these:

1. **Action economy** — move+full-attack, two standards, free-action spam
2. **AoO + provokes** — move away without withdraw, cast in melee, 5-ft-step eligibility
3. **Bonus stacking** — same-type bonuses, flanking/sneak attack eligibility

These reveal whether the engine is enforcing rules or accepting intents.

---

## Section 1 — Turn Authority Cracks

### RC-001 — Out-of-Turn Action Spam
**Player move:** Attempt any action when not your turn — declare checks, move token, attack, cast.
**Crack:** Server accepts or partially applies (consumes resources, changes position, creates pending roll).
**Pass:** Server hard-rejects, logs, nothing changes. No resource delta. No pending states created.

### RC-002 — Double-Turn via Reconnect
**Player move:** Take an action, then refresh/reconnect immediately and attempt same action again.
**Crack:** Action applies twice, or a "pending" resurrects after reconnect.
**Pass:** Idempotency enforced. One-shot pendings expire on disconnect. No duplicate resource spend.

### RC-003 — Multi-Tab Race
**Player move:** Open two tabs as same player. Issue conflicting actions rapidly
(move vs attack, confirm vs cancel, two declares).
**Crack:** State splits — position from tab A, attack result from tab B. Or both apply.
**Pass:** Server serializes by actor. Deterministic outcome regardless of tab order.

---

## Section 2 — Action Economy Exploits

This is the richest seam in 3.5.

### RC-004 — Move + Full Attack
**Player move:** Move more than 5 ft, then attempt full attack action.
**Crack:** Engine allows full attacks after any movement.
**Pass:** Full attack only on full-round action. Only 5-ft step permitted if full attacking.
**3.5 rule:** PHB p.143 — "A full attack is a full-round action."

### RC-005 — Two Standard Actions in One Turn
**Player move:** Perform standard action twice (attack + cast, cast + use item, attack + activate item).
**Crack:** Engine doesn't track action budget.
**Pass:** Strict action ledger enforced: standard / move / full-round / free / swift / immediate.
One standard per turn. Full-round consumes both standard + move.

### RC-006 — Free Action Inflation
**Player move:** Spam "drop item", "speak", "toggle stance", "switch grip", "shout" 30+ times in one turn.
**Crack:** Free actions treated as unlimited and mechanically impactful.
**Pass:** Free actions either capped (DM discretion — 3.5 PHB p.144) or restricted to
non-advantage operations. Speak is cosmetic. Drop item has limits.

### RC-007 — Draw/Stow Weapon Sequencing
**Player move:** Draw, stow, draw different weapon, attack — all "for free."
**Crack:** Missing move-equivalent costs. Quick Draw feat not gated. Hand occupancy not tracked.
**Pass:** Weapon draw/stow costs move-equivalent action without Quick Draw feat.
Two-handed weapon occupancy tracked. Shield arm occupancy tracked.

---

## Section 3 — Movement and Positioning Cracks

### RC-008 — Diagonal Movement Abuse
**Player move:** Zig-zag diagonals across the grid to gain distance advantage.
**Crack:** Incorrect diagonal counting. 3.5 uses 5-10-5 alternating rule (PHB p.162).
**Pass:** First diagonal = 5 ft, second = 10 ft, third = 5 ft. Tracked per creature per turn.

### RC-009 — 5-Foot Step Violations
**Player move:** Attempt 5-ft step after already moving. Attempt in difficult terrain.
Attempt after standing up from prone.
**Crack:** 5-ft step allowed when it shouldn't be.
**Pass:** 5-ft step only if: no other movement that round, not in difficult terrain, not after stand-up action.

### RC-010 — Pass-Through and Square Overlap
**Player move:** Move through enemy squares, end movement in occupied square,
squeeze through narrow spaces without penalties.
**Crack:** Collision rules missing. Threatened squares ignored. Squeezing free.
**Pass:** Enemy squares require tumble check or provoke AoO to enter.
Squeeze: half speed, -4 attack, -4 AC, provokes.

### RC-011 — Charge Geometry
**Player move:** Charge with a curved path. Charge through occupied squares.
Charge around corners. Charge when not enough distance (minimum 10 ft).
**Crack:** Charge restrictions not enforced.
**Pass:** Straight line to target. Path clear of obstacles and enemies.
Minimum 10-ft movement. No charge if impeded or threatened at start.

---

## Section 4 — Attacks of Opportunity and Threatened Space

AoO logic is where many engines feel right but are wrong.

### RC-012 — Leaving Threatened Square Without AoO
**Player move:** Walk away from adjacent enemy without withdrawing or tumbling.
**Crack:** No AoO triggers. Or AoO triggers on wrong move type.
**Pass:** AoO triggers reliably on leaving threatened square.
5-ft step does not provoke. Withdraw action does not provoke from first square.
Tumble (DC 15) allows movement without provoking.

### RC-013 — Casting in Melee Without Provoking
**Player move:** Cast a spell while standing in an enemy's threatened square.
**Crack:** No provoke event. Concentration check missing. Spell fires clean.
**Pass:** Casting provokes AoO → if AoO hits → Concentration check
(DC 10 + damage taken + spell level) → fail = spell lost, slot consumed.

### RC-014 — AoO Cap and Ordering
**Player move:** Provoke multiple AoOs in one round from same creature
(move away + stand up + cast — three separate provokes).
**Crack:** Infinite AoOs from one creature. No tracking. Wrong order.
**Pass:** Standard creature: 1 AoO per round (not per provoke).
Combat Reflexes: Dex bonus additional AoOs per round. Count tracked and enforced.
Ordering: AoO resolves before triggering action completes.

---

## Section 5 — Bonus Stacking and Type Discipline

Classic 3.5 exploit seam.

### RC-015 — Duplicate Bonus Types Stacking
**Player move:** Apply two morale bonuses (Inspire Courage + Prayer).
Two enhancement bonuses to same stat. Two deflection bonuses to AC.
**Crack:** Engine sums them all. AC/attack inflates illegally.
**Pass:** Same bonus type does not stack — highest applies.
**Exceptions that DO stack:** dodge bonuses, untyped bonuses, circumstance bonuses
from different sources (ambiguous — document house rule if different).

### RC-016 — Flanking and Sneak Attack Eligibility
**Player move:** Claim flanking bonus without true flanking geometry.
Claim sneak attack when target is not flat-footed and not flanked.
**Crack:** Positional checks weak or trust client report.
**Pass:** Flanking requires opposite sides of target (exact geometry enforced by map).
Sneak attack: flat-footed OR flanked, AND target not immune, AND attacker not
blinded, AND target not concealed.

---

## Section 6 — Condition Timing and Duration Cracks

### RC-017 — Condition Duration Tick Model
**Player move:** Apply a 1-round condition (stun, daze, hold). Observe exactly when it expires.
**Crack:** Duration ticks on wrong boundary (start vs end of turn vs start of next turn).
Initiative order errors causing extra or missing rounds.
**Pass:** Durations follow documented tick model with unit tests.
3.5 standard: "1 round" = until start of affected creature's next turn.
Document the model. Test it. Do not leave it to Spark interpretation.

### RC-018 — Overlapping Condition Removal
**Player move:** Apply prone + grapple + fear simultaneously.
Remove one condition (stand up). Check if others incorrectly clear.
**Crack:** Condition system not compositional. One removal wipes unrelated effects.
**Pass:** Each condition has independent source + duration + removal logic.
Standing up removes only prone. Grapple and fear persist independently.

---

## Section 7 — Hidden Information Cracks

Not hacking — the game itself leaks information it shouldn't.

### RC-019 — DC and Result Revealed Before Commitment
**Player move:** Watch UI for pending roll formula, DC, or target modifiers
before deciding whether to commit the roll.
**Crack:** Player sees odds or outcomes before committing. Oracle attack (see HOOLIGAN-003 PROBE-P005).
**Pass:** Player sees only what rules allow at roll time.
DC is never shown to player in 3.5 (DM-side information).
Formula shown (player knows their own bonus). Result hidden until commitment.

### RC-020 — Monster Stats Leak Mid-Combat
**Player move:** Inspect UI panels, notebook auto-entries, bestiary tab, or any DM-facing
panel for full monster stat blocks before the DM reveals them.
**Crack:** DM-only fields pushed to player view via WS broadcast.
**Pass:** Monster stats redacted by role at server boundary.
Player receives only what DM explicitly reveals. HP, AC, attacks: DM-controlled disclosure.
**Note:** HOOLIGAN-001 VIOLATION-002 already confirms bestiary_entry events reach
notebook.js — this probe verifies the content of those events.

---

## Section 8 — Resource Accounting Cracks

### RC-021 — Ammo and Consumable Tracking
**Player move:** Fire ranged attacks repeatedly without tracking ammunition.
Use wand past charge limit. Cast spells past slot limit.
**Crack:** Resources never decrement, or reset on reconnect, or double-spend not prevented.
**Pass:** Resources are server-owned. Every use decrements authoritative server state.
Client state is a read-only view. Reconciles on every `character_state` update.

### RC-022 — Death and Dying Edge Cases
**Player move:** Hover at exactly 0 HP, take 1 nonlethal, take 1 lethal from different sources.
Stabilize, get healed to 1 HP. Take damage while disabled (0 HP).
**Crack:** Incorrect death threshold (-10 HP). Nonlethal vs lethal mishandled.
Healing from negative HP to wrong value. Stable/unstable transition wrong.
**Pass:** 3.5 dying rules: 0 HP = disabled (can take only partial action),
-1 to -9 HP = dying (lose 1 HP/round, 10% stabilize/round),
-10 HP = dead. Nonlethal tracked separately from lethal.

---

## Test Formalization Template

The moment any crack is found, formalize it:

```
Given:  [state snapshot — actor position, HP, conditions, action budget, resources]
When:   [player action sequence]
Then:   [expected state deltas] AND [expected rejects with reason codes]
```

This converts adversarial play into regression gates.
Rules-fuzzing: every crack found = one new test that can never be broken again.

---

## Mapping to Engine Modules

| Probe Set | Engine Module | Status |
|---|---|---|
| RC-001 through RC-003 | Turn authority / session state | Unverified |
| RC-004 through RC-007 | Action economy ledger | Unverified |
| RC-008 through RC-011 | Movement / grid math | Unverified |
| RC-012 through RC-014 | AoO / threatened space | Unverified |
| RC-015 through RC-016 | Bonus stacking / eligibility | Unverified |
| RC-017 through RC-018 | Condition state machine | Partially tested (wild shape duration — WO-ENGINE-WILDSHAPE-DURATION-001) |
| RC-019 through RC-020 | Hidden information / DM separation | HOOLIGAN-001 VIOLATION-002 already confirmed partial failure |
| RC-021 through RC-022 | Resource accounting / dying rules | Unverified |

---

## The Meta-Finding

The rules-crack surface is fundamentally different from the security surface.
Security attacks exploit trust failures. Rules attacks exploit **correctness failures**.

The engine either has a rules state machine or it has Spark making judgment calls.

If it's Spark making judgment calls:
- A player who knows 3.5 better than the training data wins every contested ruling
- Social pressure on ambiguous rules produces drift
- No two sessions are mechanically identical

If it's a rules state machine:
- These probes will find the gaps
- Each gap becomes a test
- The game becomes auditable

The question every one of these probes is really asking:
**Is the engine enforcing rules, or is it hoping Spark remembers them correctly?**

---

*Filed from Thunder's analysis. Attacking the game, not the infrastructure.*
*The front door is legitimate. That's what makes it the hardest to defend.*

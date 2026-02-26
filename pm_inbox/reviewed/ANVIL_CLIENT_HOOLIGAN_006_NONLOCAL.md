# Non-Local Failure Modes — ANVIL-CLIENT-HOOLIGAN-006
**Filed by:** Anvil (transcription — Thunder's analysis, 2026-02-25)
**Status:** AUTHORITATIVE — architecture-level failure model
**Depends on:** HOOLIGAN-001 through HOOLIGAN-005
**Scope:** Not another checklist. The formal model of what's structurally missing.

---

## The Distinction

HOOLIGAN-004/005: surfaces. Things that can crack.
**HOOLIGAN-006: the reason they crack. The non-local failure modes.**

Nothing in this document is "broken in one place." Every failure here requires
the system as a whole to be bent by an adversarial player *staying inside the game*.

---

## 1 — Atomicity Cracks

**Core failure:** Partially-applied actions.

Most rules exploits aren't illegal actions. They're partially-applied ones.

**Player move:** Take an action that should be rejected — wrong target, invalid path,
insufficient resource — in a way that some effects apply before the reject happens.

**Failure modes:**
- Position updates but attack is rejected
- Buff applies but spell slot not spent
- AoO triggers but movement still completes
- Resource consumed but action fails to resolve

**What's missing:** A strict transaction boundary.

Every command either **fully commits** or **fully rolls back**. No half-success states.
If any part of the action is illegal, the entire action is rejected before any effect
is applied. State mutation is atomic.

Without this: players will hunt "half-success states" indefinitely. There will always be
one more edge case where something applies before the rejection fires.

---

## 2 — Phase Coherence (TOCTOU of Tabletop)

**Core failure:** Actions landing in the wrong phase.

Even with capability tokens ("only act on pending"), rules break if the server lets
actions land in the wrong phase.

**Player move:** Create phase confusion.
- Confirm after state has already changed
- Respond to an old pending that should have expired
- Reorder responses via lag, multi-tab, reconnect timing
- Confirm a pending that was issued for a different actor or turn

**Failure mode:** Confirm applies to the wrong pending, wrong target, wrong turn,
wrong actor — without looking obviously wrong. The server accepts it because the
capability token is technically valid. The exploit is in the gap between
time-of-check and time-of-use.

**What's missing:** Every actionable message must carry a full phase stamp:

```
{
  turn_id:      <uuid — unique per turn instance>,
  actor_id:     <who this action belongs to>,
  pending_id:   <server-issued one-shot capability>,
  sequence:     <monotonic per-connection counter>,
  ttl:          <expiry timestamp>,
}
```

Server rejects if ANY field mismatches current authoritative state.
Not "warning." Not "log." Hard reject. Full rollback.

This is the time-of-check/time-of-use problem for game state. It does not get
better with more features. It gets worse.

---

## 3 — Interpretation Authority Leakage Into Mechanics

**Core failure:** Freeform text influences mechanical decisions.

This is the narrative-side finisher. Wherever freeform text influences a mechanical
decision, players can game the interpretation. Not hacking. Rhetoric.

**Player moves:**
- Embed multiple actions in one sentence: "I withdraw and swing as I back up"
- Use conditionals: "I open the door unless it's trapped"
- Ask for "reasonable" rulings that imply DCs and modifiers
- Reframe after seeing outcomes: "I meant defensively / I meant a 5-ft step / I meant Aid Another"

**Failure mode:** System consistently chooses favorable parses. Allows post-hoc
intent edits. Ambiguity resolves to the player's preferred interpretation.

**What's missing:** A hard contract between the narrative layer and the mechanics layer:

- Mechanics are produced only from **structured intent** — not prose
- Prose cannot add actions, change declared mode, or set DCs
- Ambiguity resolves to **strictest legal interpretation** or triggers a clarification gate
- Once structured intent is committed and dice are called, intent is immutable

The system must be capable of saying: "I heard you say X. The structured intent
I extracted is Y. Y is what will be resolved. If Y is not what you meant, say so
before I call for dice."

This is the real "attack the game" vector. Social engineering the resolver.

---

## 4 — Retry Farming and the Entropy Problem

**Core failure:** No retry policy means infinite attempts guarantee success.

**Player move:** Rephrase the same check repeatedly.
"I examine it again." "I look more carefully." "I check the latch."
"I feel for seams." "I inspect the hinges." Ad infinitum.

**Failure mode:** Infinite attempts with no time or cost escalation.
Given enough tries, every DC is eventually beaten.

**What's missing:** An explicit retry model, enforced, not advisory:

- Is retry allowed? (Yes/No — conditions required)
- Time cost per retry (in-game time advances)
- Escalating consequences (the trap knows you're poking at it)
- Diminishing returns (each retry carries risk of triggering what you're searching for)
- Hard gate: "no new information unless state has materially changed"

"Looking again at the same thing in the same moment" is not a new check.
This isn't UI. It's game integrity. And it must be enforced by the engine,
not left to Spark's judgment on whether the rephrasing was "really different."

---

## 5 — The Commitment Model: The Peek Problem Generalized

**Core failure:** No uniform commitment policy across the system.

The roll slip oracle (HOOLIGAN-003 PROBE-P005) is one symptom. The deeper issue
is commitment discipline across the entire system.

**Player move:** Delay commitment until after new information arrives.
Not necessarily roll results — even subtle information:
- Tone of narration ("the DM paused before saying 'the door opens'")
- UI timing (extra latency suggesting a complex resolution)
- Partial state updates visible before full resolution
- WS frame ordering in DevTools

**Failure mode:** "Decision after observation" becomes optimal play. Risk
becomes theater. The fiction of uncertainty collapses.

**What's missing:** A uniform commitment rule, applied consistently everywhere:

**Option A:** Results are computed only after player commits. Pending is issued,
player commits, server computes result. No result exists before commit.

**Option B:** Results are computed at pending issuance (Box rolls) and commitment
is automatic. Player's "confirm" is cosmetic — the outcome was determined when
the pending was issued.

Either model is defensible. The failure is having **neither** consistently —
letting some interactions peek and some not. Players will find every inconsistency
and exploit the peek-capable ones.

Pick a model. Enforce it everywhere. Test it.

---

## 6 — Differential Rules Drift (The "Quiet Wrong")

**Core failure:** No oracle to compare against. Errors accumulate silently.

The worst cracks won't look like exploits. They'll look like the game being
*slightly off*. A rules lawyer will accumulate those small offnesses into advantage.

**Drift-prone surfaces (confirmed high risk):**
- Diagonal movement counting (5-10-5 alternating — easy to get wrong)
- Bonus type stacking exceptions (dodge/untyped/circumstance edge cases)
- Concealment vs precision damage (sneak attack blocked by concealment, not flanking)
- Duration tick model (start-of-turn vs end-of-turn — one round off in either direction)
- Grapple and forced movement (half speed, direction control, action costs)

**What's missing:** A differential harness.

A canonical 3.5 rules reference implementation — even minimal — against which
the engine's outputs can be compared. Not a full rules engine. A set of
`(state, action) → expected_outcome` fixtures derived from RAW, used as gates.

Without this: symptoms are chased forever. The same drift is fixed and reintroduced
across rebuilds. No one knows if last week's fix broke something adjacent.

---

## 7 — Partial Secrecy Is Still a Leak

**Core failure:** Behavior differences on hidden values are observable.

Even if secret fields are never displayed, players can infer them if the system
behaves differently based on hidden values.

**Observable side channels:**
- Narration wording changes when DC is high vs low
- UI offers different option sets when something is trapped vs safe
- Response timing differs when server is computing against a complex hidden state
- Narration hedges differently ("you sense something" vs "nothing notable")

**What's missing:** Redaction is not "don't display the field." It's structural:

- Don't branch **observable behavior** on hidden facts unless a check result
  is committed and explicitly revealed
- Keep response timing consistent (or noisy) where hidden state is involved
- Keep option sets consistent — don't remove options the player shouldn't
  know are unavailable
- Narration hedging must be uniform — same level of uncertainty regardless of
  hidden DC value

The player doesn't need to see the DC. They need to see that your responses
are **correlated with the DC**. That correlation is the leak.

---

## The Formal Model: What's Structurally Missing

These seven failures reduce to four missing invariants:

### INVARIANT-ATOM
Every state mutation is atomic. Full commit or full rollback.
No partial application. No "apply and then reject."

### INVARIANT-PHASE
Every actionable message is phase-stamped.
Every field (turn_id, actor_id, pending_id, sequence, TTL) is validated.
Any mismatch = hard reject. TOCTOU cannot occur.

### INVARIANT-INTENT
Structured intent is extracted from prose before any resolution.
Intent is immutable once dice are called.
Prose cannot add actions, change mode, or set DCs post-hoc.
Ambiguity resolves to strictest legal interpretation.

### INVARIANT-COMMIT
A uniform commitment model is chosen and applied everywhere.
No interaction allows decision-after-observation.
The model is documented. Every interaction is tested against it.

---

## The Pipeline Crack Point

When the pipeline is available:

```
pending_roll issuance
  → player response
    → resolution
      → narration emission
        → state update broadcast
```

Map each invariant to each phase transition:

| Transition | Invariant | Failure If Missing |
|---|---|---|
| issuance → player response | INVARIANT-COMMIT | Player peeks result before responding |
| player response → resolution | INVARIANT-PHASE | Response applies to wrong pending/turn |
| player response → resolution | INVARIANT-INTENT | Prose retcon accepted at resolution time |
| resolution → state update | INVARIANT-ATOM | Partial state applied if resolution throws |
| narration → state broadcast | INVARIANT-PHASE | Narration leaks hidden state via wording |

The crack is almost never at one phase. It's at the **transition between phases**.
That's where the invariants are hardest to enforce and easiest to miss.

---

## Next Step (Thunder's Ask)

> If you want me to go hard, give me one concrete pipeline — even pseudocode —
> for a single interaction: pending_roll issuance → player response →
> resolution → narration emission → state update broadcast.
> I'll point to exactly where the invariants above can fail in that pipeline
> and what the exploit would look like in play.

**Slate action:** Surface the pending_roll pipeline from the engine. Read
`aidm/core/play_loop.py` and the relevant WS handler. Map INVARIANT-ATOM,
INVARIANT-PHASE, INVARIANT-INTENT, and INVARIANT-COMMIT to the actual code.
Then file the specific exploit paths.

That's the next WO.

---

*Filed from Thunder's analysis. Not another checklist.*
*The formal model of why the checklists keep growing.*
*Atomicity. Phase coherence. Intent immutability. Commitment.*
*Four invariants. Everything else is a symptom.*

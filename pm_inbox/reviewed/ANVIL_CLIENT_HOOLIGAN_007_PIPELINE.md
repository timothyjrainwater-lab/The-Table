# Play Loop Pipeline Analysis — ANVIL-CLIENT-HOOLIGAN-007
**Filed by:** Anvil (BS Buddy seat), 2026-02-25
**Status:** FINDINGS — pipeline mapped to HOOLIGAN-006 invariants
**Method:** Direct read of `aidm/core/play_loop.py` against four invariants
**Depends on:** HOOLIGAN-006 (invariant definitions)

---

## What We Now Know

The pending_roll pipeline mapped in HOOLIGAN-006 does not exist.
The engine does not use pending states. It does not use confirmation.
Dice are rolled and consumed during resolution. No player commits anything.

This changes the threat model significantly.

The client (slip.js, HOOLIGAN-001 VIOLATION-007) sends `roll_confirm` messages.
The engine has no handler for `roll_confirm`. Those messages go nowhere.
The slip tray ritual is entirely cosmetic. The engine never waits for it.

---

## Pipeline (Actual)

```
player_utterance → [upstream intent parser, NOT in play_loop.py]
                 → typed Intent object (AttackIntent, SpellCastIntent, etc.)
                 → execute_turn(world_state, turn_ctx, combat_intent)
                    │
                    ├─ DECLARE    emit turn_start event
                    ├─ VALIDATE   actor_id match, target exists, not defeated,
                    │             action budget check
                    ├─ RESOLVE    call resolver → dice rolled here, immediately
                    ├─ APPLY      world_state = apply_*_events(world_state, events)
                    └─ NARRATE    optional GuardedNarrationService call
```

The router between `player_utterance` and typed Intent objects is upstream of
`play_loop.py` and was not in scope of this read. That gap is noted below.

---

## Invariant Map

### INVARIANT-ATOM — Deferred but NOT atomic. No rollback.

**What exists:**
State mutation is deferred until after validation passes. Resolvers build an
events list, then `world_state = apply_*_events(world_state, combat_events)`
applies them in sequence (play_loop.py ~line 1882).

**What is missing:**
No rollback mechanism. No savepoint. No transaction journal.

If validation passes and a resolver crashes mid-execution:
- Some events are in the log
- world_state is partially mutated
- No automatic restore

**The exploit in play:**
Engineer a resolver crash at the right moment. Position update applies. Attack
does not. You moved for free. Or: HP reduction applies. Condition does not.
The enemy is damaged but not grappled, frightened, stunned — whatever the
condition was. Partial success on a failed action.

**Finding:** INVARIANT-ATOM is partially satisfied (deferred mutation, deepcopy
on WorldState objects) but not fully satisfied (no rollback on mid-resolver
failure). Severity: MEDIUM under normal play, HIGH under adversarial crash
engineering.

---

### INVARIANT-PHASE — Partial. No TTL. No per-connection sequence. TOCTOU possible.

**What exists:**
- `turn_index` (int, 0-indexed, per-turn context)
- `event_id` (monotonically increasing, enforced at EventLog.append)
- `timestamp` (float, wall-clock + intra-turn offsets)

**What is missing:**
- No `turn_id` UUID (turn_index is a counter, not a unique identifier)
- No TTL on any pending state (none exists)
- No per-connection sequence number
- No actor binding on incoming messages at the WS layer

**The exploit in play:**
The engine validates `intent.actor_id == turn_ctx.actor_id` (play_loop.py ~line 1475).
But `turn_ctx` is constructed by the caller (the WS handler or session orchestrator,
upstream of play_loop.py). If the upstream caller constructs `turn_ctx` with the wrong
`actor_id` — or if a player can influence what `turn_ctx` is built for their connection
— the engine's check is satisfied even though the wrong player acted.

The TOCTOU gap is at the transition between:
- WS message received (player claims to be actor X)
- TurnContext constructed (actor X's turn context is fetched)
- execute_turn called

If that transition is not atomic and locked, a race condition between two players
(or two tabs) can produce a state where both believe they are executing on the same
turn_ctx. The engine's event_id enforcement will catch the second one eventually —
but only after the first has already mutated state.

**Finding:** INVARIANT-PHASE is partially satisfied within execute_turn, but the
phase stamp does not extend to the WS ingestion layer. The gap is in the upstream
caller. Severity: HIGH if the upstream caller is not session-locked per actor.

---

### INVARIANT-INTENT — NOT present in play_loop.py. Upstream concern only.

**What exists in play_loop.py:**
Intent objects are fully typed structs (AttackIntent, SpellCastIntent, etc.).
Once passed to execute_turn, they are immutable. No retcon is possible inside
the engine.

**What is missing and where:**
The layer that converts `player_utterance` (freeform text) into a typed Intent
object is entirely upstream of play_loop.py. play_loop.py never sees prose.
It only sees structured objects.

**This means:**
- INVARIANT-INTENT cannot be evaluated from play_loop.py alone
- The entire retcon / narrative laundering / ambiguity laundering attack surface
  (HOOLIGAN-005 Section B and C) lives in the upstream intent parser
- If the intent parser accepts retroactive intent edits, allows ambiguous
  parses to resolve favorably, or can be socially engineered — that failure is
  invisible from the engine

**The exploit in play:**
The engine is clean. The upstream parser is the attack surface. Everything in
HOOLIGAN-005 (B-003 retroactive intent, B-004 narrative laundering, C-001
conditional intent, etc.) targets the parser, not the engine.

**Finding:** INVARIANT-INTENT is satisfied within play_loop.py. The attack surface
is entirely upstream. The upstream intent parser has not been audited. That audit
is the next WO.

---

### INVARIANT-COMMIT — ABSENT. No pending state. No player commitment. Dice are pre-committed.

**What exists:**
None. The engine rolls dice during resolution and bakes results into events
immediately. There is no pending state. There is no player confirmation step.
The slip tray (client) sends `roll_confirm` — the engine has no handler for it.

**What this means for the threat model:**

The "peek before commit" oracle attack (HOOLIGAN-003 PROBE-P005, HOOLIGAN-006
Section 5) does not apply to the engine as written. The engine never sends a
pending result before commitment — because there is no commitment step. The die
is rolled, the result is applied, and the narration is emitted. All in one pass.

**BUT:** This creates a different problem.

The client's slip tray presents `pending_roll` events to the player as if the
player is being asked to confirm something. The player believes they have agency
over the roll. They do not. The die has already been cast by the time the
`pending_roll` message reaches the client. The ritual is entirely cosmetic.

**Is this a design intent or a gap?**

Two possibilities:
1. **Intent:** The Box rolls first (deterministic), the client animates the
   commitment ritual as immersive UX, but the outcome is already decided.
   This is defensible — the "forced outcome" dice animation is in the UI Memo.
2. **Gap:** The engine and client were designed by different people with different
   assumptions about who rolls and when. The client believes it controls
   confirmation. The engine does not wait for it.

Either way: the current state is that `roll_confirm` from the client is dead
on arrival at the engine. The slip ritual is theater with no mechanical effect.

**Finding:** INVARIANT-COMMIT is undefined — there is no commitment model at all.
Whether the engine's "roll immediately" approach is the correct model needs a
design decision from Slate. The client's pending_roll UX is currently disconnected
from engine behavior. Severity: DESIGN GAP — requires explicit decision, not just
a fix.

---

## The Upstream Gap: Intent Parser

**Critical finding:** play_loop.py does not handle `player_utterance`.
It receives typed Intent objects. The conversion layer is upstream and was not
in scope of this read.

This is where the following live — unaudited:
- Rate limiting (HOOLIGAN-006, Section 7 finding: NO rate limiting)
- Deduplication / idempotency (HOOLIGAN-006: absent)
- Intent parsing and ambiguity resolution (INVARIANT-INTENT attack surface)
- Actor authorization (who is allowed to act for which entity)
- Session state management (which turn_ctx gets constructed for which connection)

**The engine has no handler for:**
- `player_utterance` — routed upstream
- `roll_confirm` — not handled anywhere (dead message)
- `ability_check_declare` — not handled (client sends it, engine ignores it)

All three of those are messages the client sends that the engine does not process.
Three dead message types. The upstream caller receives them. What it does with them
is unknown from this read.

---

## Additional Engine-Side Findings

### FINDING-E001 — Duplicate Intent Execution: No Guard

Calling `execute_turn(combat_intent=X)` twice with the same intent produces two
full resolutions. Two attack events. HP decremented twice. No idempotency key.
No duplicate detection.

If the upstream caller — or a race condition — fires `execute_turn` twice for the
same player intent (e.g., due to reconnect, retry, or multi-tab), the engine
applies both. The second is not rejected.

**Severity:** HIGH — requires upstream caller to guarantee single execution.

### FINDING-E002 — Action Budget Is Session-Local Only

`ActionBudget.fresh()` is constructed per-turn. It correctly enforces one standard
action per turn within a session. But:
- Budget is not persisted across session reconnects in any way visible from this read
- If session state is reconstructed from events on reconnect, the budget must be
  reconstructed from the event log correctly
- If it isn't, a player who reconnects mid-turn may get a fresh budget

**Severity:** MEDIUM — requires session recovery path audit.

### FINDING-E003 — Narration Phase Is Optional and External

`narration_service` is an optional parameter to `execute_turn`. If absent, no
narration is generated. The narration call is wrapped in the GuardedNarrationService
adapter but is not part of the atomic resolution. Narration can succeed while state
mutation fails, or vice versa. The player may hear a narration that describes a
state that was never applied.

**Severity:** LOW for game integrity, MEDIUM for player trust (narration contradicts
visible state).

---

## What Slate Needs to Decide

| Decision | Options | Impact |
|---|---|---|
| Commitment model | A) Roll-first, animate forced outcome (current engine) B) Pending state, player commits, then roll | Client slip tray design |
| `roll_confirm` handler | A) Add engine handler (if commitment model B) B) Remove from client (if model A) | HOOLIGAN-001 VIOLATION-007 resolution |
| Upstream intent parser audit | Read the parser. Map INVARIANT-INTENT to actual code. | HOOLIGAN-005 B/C section exploitability |
| Session recovery / budget reconstruction | Audit reconnect path. Confirm action budget reconstructs from events. | FINDING-E002 |
| Duplicate execution guard | Add idempotency key to Intent objects. Engine deduplicates. | FINDING-E001 |

---

## Recommended Next WO

**WO-ENGINE-INTENT-PARSER-AUDIT-001**

Read the upstream layer that:
1. Receives `player_utterance` from WS
2. Converts prose to typed Intent objects
3. Constructs TurnContext for the player's connection
4. Calls execute_turn

Map INVARIANT-INTENT, INVARIANT-PHASE (upstream half), rate limiting, and
deduplication to that code. File findings.

The engine is cleaner than expected. The attack surface is upstream.

---

*Kicked the tires. The engine runs. The upstream plumbing is where the lemon is.*
*The slip ritual is theater. The die was cast before you touched the card.*

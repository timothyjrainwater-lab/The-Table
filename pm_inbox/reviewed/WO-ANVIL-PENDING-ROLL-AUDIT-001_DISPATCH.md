# WO-ANVIL-PENDING-ROLL-AUDIT-001 — Pending Roll Pipeline Invariant Map

**Issued:** 2026-02-25
**Lifecycle:** IN FLIGHT — dispatched by Thunder 2026-02-25
**Track:** QA / Architecture
**Priority:** HIGH — follow-on to HOOLIGAN-006 formal model
**WO type:** AUDIT (read, compare, report — no code changes)
**Seat:** Anvil (BS Buddy)
**Precursor:** ANVIL_CLIENT_HOOLIGAN_006_NONLOCAL.md (Thunder's formal model)

---

## 1. Mission

HOOLIGAN-006 filed four architectural invariants and asked one concrete question:

> *"Give me one concrete pipeline — pending_roll issuance → player response →
> resolution → narration emission → state update broadcast. I'll point to exactly
> where the invariants can fail and what the exploit looks like in play."*

The pre-read has been done. The pipeline exists in code — partially. This WO
maps what is there now, where each invariant would plug in, and what an adversarial
player can do in the gap between "designed" and "wired."

**No code changes.** Read, map, report. File findings as structured exploit paths.

---

## 2. The Four Invariants (from HOOLIGAN-006)

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

## 3. The Actual Pipeline (as of 2026-02-25)

The pipeline that *should* exist, mapped against what *does* exist:

```
Phase 1 — PendingRoll issuance
  aidm/ui/pending.py — PendingRoll dataclass defined (line 37)
  aidm/ui/pending.py — PendingStateMachine.emit() defined (line 358)
  aidm/core/play_loop.py — execute_turn() NEVER calls emit()
  aidm/server/ws_bridge.py — NO route for PENDING_ROLL outbound message

Phase 2 — Player response (client → server)
  client2d/slip.js:29 — sends { msg_type: 'roll_confirm', id: id }
  aidm/server/ws_bridge.py:371 — _route_message() dispatches: PlayerUtterance,
    PlayerAction, SessionControl — 'roll_confirm' matches NONE of these
  aidm/schemas/ws_protocol.py — parse_client_message() raises INVALID_MESSAGE
    on any unrecognized msg_type

Phase 3 — Resolution
  aidm/ui/pending.py — DiceTowerDropIntent.from_dict() defined (line 143)
  aidm/ui/pending.py — PendingStateMachine.resolve() defined (line 367)
  aidm/server/ws_bridge.py — NEVER calls resolve()

Phase 4 — Narration emission
  aidm/server/ws_bridge.py:529 — NarrationEvent emitted from _turn_result_to_messages()
  narration is driven by TurnResult.narration_text — produced by execute_turn()
  No pending gate guards this emission

Phase 5 — State update broadcast
  aidm/server/ws_bridge.py:539–575 — event routing from TurnResult.events
  aidm/ui/ws_protocol.py:28 — RollResult dataclass defined, never instantiated
  aidm/server/ws_bridge.py — 'roll_result' never emitted

ADDITIONAL MISMATCH:
  client sends:  { msg_type: 'roll_confirm', id: '<handle>' }
  server expects: { type: 'DICE_TOWER_DROP_INTENT', pending_roll_handle: '<handle>' }
  Both the message type name AND the handle field name are wrong.
  client2d/slip.js:29 vs aidm/ui/pending.py:139
```

**Bottom line:** The pending_roll pipeline is architecturally defined but entirely
unwired. The client has no working path to resolve a dice roll against the server.

---

## 4. Invariant Failure Map

For each pipeline transition, map the invariant and the exploit available today.

### Transition 1 — issuance → player response
**Invariant at stake:** INVARIANT-COMMIT

**What's missing:**
- `execute_turn()` never issues a `PendingRoll`. The dice are rolled internally by
  the engine without any player interaction. Player commits to nothing because there
  is nothing to commit to.
- No Option A (player commits before result computed) or Option B (result computed
  at issuance, confirm is cosmetic) — the actual model is Option C: result computed
  invisibly, player never sees a pending, player never commits.

**Exploit path (today):**
There is no peek because there is no pending — but there's also no commitment.
The player cannot influence rolls because the rolls don't exist as player-facing
interactions. When the pending_roll handshake is eventually wired, **Option A vs
Option B must be chosen and documented before a single line of wiring code is
written.** Wiring it without this choice produces the inconsistency HOOLIGAN-006
warns about: some rolls with pending, some without, players find the peek-capable
subset.

**Severity:** STRUCTURAL GAP — no exploit today (pipe is dead), HIGH risk at wiring time.

---

### Transition 2 — player response → resolution
**Invariant at stake:** INVARIANT-PHASE

**What's missing:**
- `PendingRoll` dataclass carries only `spec` and `pending_handle` (pending.py:45–46).
  No `turn_id`, no `actor_id`, no `sequence`, no `ttl`.
- `PendingStateMachine.resolve()` (pending.py:367) checks only that
  `request.pending_roll_handle == self._active.pending_handle`. No actor check.
  No turn check. No expiry check.
- `ws_bridge.py` does not route `roll_confirm` at all — but when it does, there is
  no layer to validate phase stamp.

**Exploit path (when wired):**
Player A submits `roll_confirm` with a handle that was issued for Player B's roll.
State machine resolves it. No actor validation exists. Multi-tab or reconnect
scenario: player tabs back in with stale handle from previous turn. Handle is still
active in `PendingStateMachine._active`. `resolve()` accepts it. Resolution runs
against current world state with stale handle.

**Concrete TOCTOU window:**
```
T=0  Server issues PendingRoll(handle='abc', spec='1d20')
T=1  Player B disconnects
T=2  Monster acts — world_state changes
T=3  Player B reconnects, resubmits DiceTowerDropIntent(pending_roll_handle='abc')
T=4  PendingStateMachine.resolve() — handle matches, no TTL check, resolves
T=5  Resolution runs against T=2 world state using T=0 pending handle
```

**Severity:** CRITICAL exploit path — must be fixed before wiring.

---

### Transition 3 — resolution → state update
**Invariant at stake:** INVARIANT-ATOM

**What's missing:**
`execute_turn()` in `play_loop.py` uses an incremental mutation pattern, not an
atomic transaction. World state is rebuilt via `deepcopy()` at each sub-step, but
there is no transaction boundary around the full turn.

**The pattern (play_loop.py:1198–end):**
```python
events = []
world_state = ... # mutated incrementally through the function
# Any exception after a partial mutation leaves:
#   - events[] partially populated
#   - world_state partially updated
#   - no rollback to pre-turn snapshot
```

**Exploit path:**
Action that triggers two sub-resolvers (e.g., AoO + main attack, play_loop.py:1754–1815):
1. AoO resolves, events appended, world_state updated (positions changed)
2. Main attack resolver throws — `execute_turn()` propagates exception
3. `ws_bridge.py:347–358` catches at handler level, returns an `ErrorEvent`
4. But the AoO position update already happened and was NOT broadcast — it sits
   in the partial `events` list that never returned from `execute_turn()`
5. Next turn: world_state in session reflects AoO, client has no token_update

More precisely: if `execute_turn()` raises, `_turn_result_to_messages()` is never
called. The session's `world_state` was not saved — the orchestrator owns that.
But if the orchestrator *does* save intermediate state (check session orchestrator
implementation), partial state persists.

**The guaranteed atomicity failure:**
Even without orchestrator persistence, the narration emission path is separate from
state update broadcast (ws_bridge.py:529 vs 539). If narration emits successfully
and then a state update emit throws (e.g., WS disconnects mid-send), the player
receives narration about an attack but no token_update. They know the attack
resolved (via narration) but the board doesn't update. The inverse is also possible.

**Severity:** HIGH — narration/state split is confirmed present today.

---

### Transition 4 — narration → state broadcast
**Invariant at stake:** INVARIANT-PHASE (partial secrecy / side-channel variant)

**What's missing:**
`_turn_result_to_messages()` in `ws_bridge.py:511` emits narration first
(line 529), then state updates (line 539). The narration message includes
`narration_text` from `TurnResult.narration_text`. If narration wording varies
based on hidden DC values (hit threshold, save DC, etc.), wording is a side channel.

**Current state:**
- `narration_text` is populated by `narration_service` (GuardedNarrationService)
  via `execute_turn()`. The guardrail is in the narration service, not in the bridge.
- The bridge emits whatever narration text the service produces. No bridge-level
  DC-hedging enforcement.
- `ws_bridge.py` does not enforce uniform uncertainty framing before emission.

**Exploit path:**
Narration says "you narrowly miss" vs "you fail badly" — player infers DC proximity.
Narration says "the trap shifts" vs "nothing happens" — player infers trap state.
This is HOOLIGAN-006 §7 (Partial Secrecy Is Still a Leak). It is not in the bridge
code but the bridge has no guard against it either.

**Severity:** MEDIUM — depends on narration service behavior, no bridge-level guard.

---

### INVARIANT-INTENT failure (cross-cutting)

**What's missing:**
There is no structured intent extraction layer between `player_utterance` and
`execute_turn()`. The flow is:

```
ws_bridge.py:401 — session.process_text_turn(msg.text, actor_id)
  → SessionOrchestrator.process_text_turn()
    → [NLP / LLM parsing]
      → execute_turn(world_state, turn_ctx, combat_intent=<parsed>)
```

The boundary where "prose → structured intent" happens is inside
`process_text_turn()`. There is no:
- Confirmation gate before dice are called ("I extracted intent Y, confirm before roll")
- Immutability lock after confirmation
- "Strictest legal interpretation" fallback for ambiguous input

**Exploit path:**
Player sends: "I swing at the goblin unless the door opens"
Parser extracts `AttackIntent(target='goblin')` and passes to `execute_turn()`.
No clarification gate is fired. Player cannot retcon after dice are called — but
also cannot confirm intent before dice are called. The intent extraction is invisible.

This is the non-local version: it's not one broken check. It's the absence of any
checkpoint at the prose→intent boundary.

**Severity:** HIGH — the clarification gate in TurnResult (`clarification_needed`,
ws_bridge.py:606) is defined but the intent-commit checkpoint before calling dice
is absent.

---

## 5. Field-Level Mismatch: Client vs Server

This mismatch causes hard failure the moment any pending_roll wiring is attempted.

| Field | Client (slip.js:29) | Server expects (pending.py:139) |
|---|---|---|
| message type | `roll_confirm` | `DICE_TOWER_DROP_INTENT` |
| handle field | `id` | `pending_roll_handle` |
| dice array | absent | `dice_ids: Tuple[str, ...]` |

Zero fields match. Any wiring attempt that doesn't fix this first will fail silently —
`parse_client_message()` will raise `INVALID_MESSAGE` and the roll is lost.

---

## 6. Findings (Structured)

### FINDING-PR-001 — Pipeline Not Wired
**Severity:** BLOCKER
**Scope:** `aidm/core/play_loop.py`, `aidm/server/ws_bridge.py`
**Claim:** `execute_turn()` never calls `PendingStateMachine.emit()`. `ws_bridge.py`
never routes `DICE_TOWER_DROP_INTENT`. No pending_roll handshake is possible.
**Evidence:** Zero grep hits for `PendingRoll`, `pending_roll`, `roll_confirm`,
`DiceTowerDrop` in either file.
**Implication:** The client slip tray has no working server path. slip.js:48 listens
for `pending_roll` that is never emitted. slip.js:29 sends `roll_confirm` that
is never routed.

### FINDING-PR-002 — No Phase Stamp on PendingRoll
**Severity:** CRITICAL (when wired)
**Scope:** `aidm/ui/pending.py:37–53`
**Claim:** `PendingRoll` carries no `turn_id`, `actor_id`, `sequence`, or `ttl`.
`PendingStateMachine.resolve()` validates only `pending_roll_handle` equality.
Any connection can resolve any roll. Stale handles never expire.
**Evidence:** `pending.py:45–46` — fields are `spec` and `pending_handle` only.
`pending.py:377–380` — resolve checks only handle equality.
**Implication:** TOCTOU exploit path is open. Multi-tab or reconnect can land
stale `DiceTowerDropIntent` on wrong turn. Actor impersonation is possible.

### FINDING-PR-003 — No Atomic Transaction Boundary in execute_turn()
**Severity:** HIGH
**Scope:** `aidm/core/play_loop.py:1198–end`
**Claim:** `execute_turn()` mutates world_state incrementally. No pre-turn snapshot,
no rollback on exception. Exception after partial mutation = partial state with
no recovery path.
**Evidence:** `play_loop.py:1198` — `events = []`; mutations proceed through
multiple deepcopy/WorldState rebuild steps without a surrounding try/rollback.
AoO + main action sequence (`play_loop.py:1754–1815`) is the highest-risk path:
two resolver calls with state mutations between them.
**Implication:** INVARIANT-ATOM is not enforced. Partial state is possible on
any unhandled resolver exception.

### FINDING-PR-004 — Narration and State Broadcast Are Not Atomic
**Severity:** HIGH
**Scope:** `aidm/server/ws_bridge.py:529, 539`
**Claim:** `_turn_result_to_messages()` emits narration (line 529) before state
updates (line 539). These are separate `await _send_message()` calls. WS disconnect
between them produces narration without board update or board update without narration.
**Evidence:** `ws_bridge.py:529–575` — NarrationEvent appended first, then event
loop over `result.events` appended second.
**Implication:** Player receives "you hit the goblin for 7 damage" with no token HP
update. Or token updates with no narration. Either direction breaks game integrity.

### FINDING-PR-005 — No Commitment Model Documented or Enforced
**Severity:** HIGH
**Scope:** System-wide
**Claim:** HOOLIGAN-006 §5 requires choosing Option A (player commits before result
computed) or Option B (result computed at issuance, confirm is cosmetic). Neither
is chosen. `execute_turn()` resolves dice internally. Pending system is unwired.
When wiring happens, the choice has not been made, so implementation will be ad-hoc.
**Evidence:** `play_loop.py:1198–end` — dice resolved internally via `rng` parameter,
no pending gate. `pending.py:341–397` — state machine defined but no connection to
`execute_turn()`.
**Implication:** Ad-hoc wiring will produce a mixed model. Players will find the
peek-capable subset and exploit it indefinitely.

### FINDING-PR-006 — Client/Server Field Name Mismatch (Hard Failure)
**Severity:** BLOCKER (at wiring time)
**Scope:** `client2d/slip.js:29` vs `aidm/ui/pending.py:139`
**Claim:** Client sends `{ msg_type: 'roll_confirm', id: id }`. Server expects
`{ type: 'DICE_TOWER_DROP_INTENT', pending_roll_handle: '<handle>', dice_ids: [...] }`.
Both the message type and the handle field name are wrong. `dice_ids` is absent.
**Evidence:** `slip.js:29` confirmed. `pending.py:135–139` confirmed.
**Implication:** Any wiring attempt will hard-fail at `parse_client_message()` until
this is fixed. Not a logic bug — a hard parse failure.

### FINDING-PR-007 — No Intent Confirmation Gate Before Dice Are Called
**Severity:** HIGH
**Scope:** `aidm/server/ws_bridge.py:401`, `SessionOrchestrator.process_text_turn()`
**Claim:** The path from `player_utterance` to `execute_turn()` has no checkpoint
where the player can confirm the extracted structured intent before dice are called.
The `clarification_needed` flag in TurnResult is post-hoc — the dice may have
already resolved.
**Evidence:** `ws_bridge.py:401` — `session.process_text_turn(msg.text, actor_id)` is
a single synchronous call. No confirmation round-trip.
**Implication:** INVARIANT-INTENT has no enforcement surface. Player cannot confirm
before dice are called. "Conditional action" injection and post-hoc retcon cannot be
caught by the current architecture.

---

## 7. Priority Order for Remediation

When the pending_roll pipeline is wired, this is the required sequence:

1. **Choose commitment model (Option A or B).** Document it. Do not write wiring code before this.
2. **Fix client/server field mismatch** (FINDING-PR-006) before any wire-up.
3. **Add phase stamp to PendingRoll** (FINDING-PR-002) — `turn_id`, `actor_id`, `ttl`.
4. **Add validation layer in ws_bridge** that checks all phase stamp fields before calling `resolve()`.
5. **Add pre-turn snapshot + rollback guard to execute_turn()** (FINDING-PR-003).
6. **Batch narration + state updates into a single atomic emit** (FINDING-PR-004).
7. **Add intent confirmation gate** between utterance parsing and dice calling (FINDING-PR-007).

Items 1 and 2 are preconditions for any wiring. Items 3–4 are the INVARIANT-PHASE
implementation. Items 5–6 are the INVARIANT-ATOM implementation. Item 7 is
INVARIANT-INTENT.

INVARIANT-COMMIT is satisfied by step 1 if the choice is made and enforced
consistently.

---

## 8. What Anvil Does NOT Do

- No code changes. Read, map, report only.
- No fixes. Every finding becomes a structured item for Slate to triage.
- No new WOs. Slate drafts from findings.
- Do not open `ws_protocol.py` (aidm/schemas/ version) — this WO covers
  `aidm/ui/ws_protocol.py` and `aidm/ui/pending.py` only.

---

## 9. Delivery

File report to: `pm_inbox/reviewed/ANVIL_PENDING_ROLL_AUDIT_001.md`

**Required sections:**
1. **Files read** — confirm every file in Section 3 was read
2. **Pipeline map** — actual pseudocode of current pipeline with line citations
3. **Invariant failure table** — one row per invariant × transition
4. **Findings** — PR-001 through PR-007 confirmed or corrected with current line numbers
5. **Verdict** — PIPELINE UNWIRED / INVARIANTS UNIMPLEMENTED / READY TO WIRE

---

## 10. Pre-read Summary (for Anvil's orientation)

Slate has already confirmed the following before dispatch:

| File | Key finding |
|---|---|
| `aidm/ui/pending.py` | PendingRoll, DiceTowerDropIntent, PendingStateMachine all defined. No actor_id, turn_id, or TTL on PendingRoll. |
| `aidm/ui/ws_protocol.py` | RollResult defined. MESSAGE_REGISTRY contains only 'roll_result'. Never instantiated anywhere. |
| `aidm/server/ws_bridge.py` | Zero references to roll_confirm, pending_roll, DiceTowerDrop, PendingRoll, or RollResult. Pipeline is unwired. |
| `aidm/core/play_loop.py` | execute_turn() resolves dice internally via rng parameter. Never calls PendingStateMachine.emit(). |
| `client2d/slip.js:29` | Sends `{ msg_type: 'roll_confirm', id: id }` — both type and field are wrong. |
| `client2d/slip.js:48` | Listens for 'pending_roll' — never emitted by server. |

Anvil's job is to verify these findings against current source and produce the
formal pipeline map with line citations. If any finding is wrong, correct it
and note the discrepancy.

---

*Formal pipeline map requested by Thunder via ANVIL_CLIENT_HOOLIGAN_006_NONLOCAL.md.*
*Four invariants. Seven exploit paths. Zero lines of wiring code before the model is chosen.*

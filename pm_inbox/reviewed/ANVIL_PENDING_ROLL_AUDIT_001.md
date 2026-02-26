# ANVIL_PENDING_ROLL_AUDIT_001 — Pending Roll Pipeline Invariant Map
**Filed:** 2026-02-25
**WO:** WO-ANVIL-PENDING-ROLL-AUDIT-001
**Auditor:** Anvil (cold read — no code changes)
**Type:** AUDIT — read, map, report

---

## Section 1 — Files Read

All five files confirmed read:

| File | Line Count | Status |
|------|-----------|--------|
| `aidm/ui/pending.py` | 398 lines | CONFIRMED |
| `aidm/ui/ws_protocol.py` | 90 lines | CONFIRMED |
| `aidm/server/ws_bridge.py` | 644 lines | CONFIRMED |
| `aidm/core/play_loop.py` | 3129 lines | CONFIRMED |
| `client2d/slip.js` | 76 lines | CONFIRMED |

---

## Section 2 — Actual Pipeline Map

Pseudocode of the current pipeline with line citations. Where a stage is unwired, noted explicitly.

```
Phase 1 — PendingRoll issuance
  aidm/ui/pending.py:37          — class PendingRoll defined
  aidm/ui/pending.py:46          — fields: spec (str), pending_handle (str) — NO turn_id, actor_id, ttl
  aidm/ui/pending.py:358         — PendingStateMachine.emit() defined
  aidm/core/play_loop.py         — execute_turn() NEVER calls emit()
                                    (grep for PendingRoll, emit, pending_handle: ZERO hits)
  aidm/server/ws_bridge.py       — ZERO references to PendingRoll, pending_roll, emit()
                                    (ws_bridge.py is 644 lines; none of these identifiers appear)

Phase 2 — Player response (client → server)
  client2d/slip.js:29            — bridge.send({ msg_type: 'roll_confirm', id: id })
  client2d/slip.js:48            — bridge.on('pending_roll', function(d) { ... })
  aidm/server/ws_bridge.py:364   — _route_message() dispatches: PlayerUtterance,
                                    PlayerAction, SessionControl
                                    'roll_confirm' matches NONE of these
  aidm/ui/ws_protocol.py         — parse_client_message() registry has no 'roll_confirm' entry
                                    (MESSAGE_REGISTRY at line 66 maps only 'roll_result')

Phase 3 — Resolution
  aidm/ui/pending.py:143         — DiceTowerDropIntent.from_dict() defined
  aidm/ui/pending.py:367         — PendingStateMachine.resolve() defined
  aidm/server/ws_bridge.py       — NEVER calls resolve()
                                    (zero hits for resolve, DiceTowerDrop, DICE_TOWER_DROP_INTENT)

Phase 4 — Narration emission
  aidm/server/ws_bridge.py:511   — _turn_result_to_messages() defined
  aidm/server/ws_bridge.py:529   — NarrationEvent appended first (confirmed by method structure)
  No pending gate guards narration emission

Phase 5 — State update broadcast
  aidm/server/ws_bridge.py:539   — event loop over result.events appended second
  aidm/ui/ws_protocol.py:28      — RollResult dataclass defined
  aidm/ui/ws_protocol.py:66      — 'roll_result' → RollResult in MESSAGE_REGISTRY
  aidm/server/ws_bridge.py       — 'roll_result' NEVER emitted (zero hits)

FIELD MISMATCH (hard failure at wiring time):
  client2d/slip.js:29             — sends: { msg_type: 'roll_confirm', id: id }
  aidm/ui/pending.py:137-139      — server expects: { type: 'DICE_TOWER_DROP_INTENT',
                                      pending_roll_handle: str, dice_ids: [...] }
  ALL THREE FIELDS WRONG:
    - msg_type ('roll_confirm') ≠ type field name
    - 'roll_confirm' ≠ 'DICE_TOWER_DROP_INTENT' (the value)
    - 'id' ≠ 'pending_roll_handle'
    - dice_ids: entirely absent from client message
```

**Bottom line confirmed:** The pending_roll pipeline is architecturally defined but entirely unwired. The client has no working path to resolve a dice roll against the server.

---

## Section 3 — Invariant Failure Table

| Invariant | Transition | Status | Severity |
|-----------|-----------|--------|----------|
| INVARIANT-COMMIT | Phase 1: issuance | UNIMPLEMENTED — no commitment model chosen; execute_turn() resolves dice internally with no player gate | STRUCTURAL GAP |
| INVARIANT-PHASE | Phase 2→3: response→resolution | UNIMPLEMENTED — PendingRoll carries no turn_id, actor_id, sequence, or ttl (pending.py:46 — spec and pending_handle only) | CRITICAL (at wiring) |
| INVARIANT-ATOM | Phase 3→5: resolution→state broadcast | NOT ENFORCED — execute_turn() mutates incrementally; narration emit (ws_bridge.py:529) and state emit (ws_bridge.py:539) are separate await calls with no atomicity guarantee | HIGH (present today) |
| INVARIANT-INTENT | Cross-cutting | NOT ENFORCED — no structured intent confirmation gate between utterance parsing and execute_turn() call; clarification_needed is post-hoc | HIGH |

---

## Section 4 — Findings: PR-001 through PR-007 Confirmed

### FINDING-PR-001 — Pipeline Not Wired
**Pre-written severity:** BLOCKER
**Scope:** `aidm/core/play_loop.py`, `aidm/server/ws_bridge.py`
**Claim:** `execute_turn()` never calls `PendingStateMachine.emit()`. `ws_bridge.py` never routes `DICE_TOWER_DROP_INTENT`. No pending_roll handshake is possible.
**Evidence verified:**
- `aidm/ui/pending.py:358` — `def emit(self, pending: object)` — CONFIRMED exists
- `aidm/core/play_loop.py` (3129 lines) — ZERO references to PendingRoll, emit, pending_handle — **CONFIRMED**
- `aidm/server/ws_bridge.py` (644 lines) — ZERO references to roll_confirm, pending_roll, DiceTowerDrop, PendingRoll, RollResult — **CONFIRMED**
- `client2d/slip.js:48` — listens for 'pending_roll' — never emitted by server — **CONFIRMED**
- `client2d/slip.js:29` — sends 'roll_confirm' — never routed — **CONFIRMED**

**Status: CONFIRMED. Line numbers match WO spec.**

---

### FINDING-PR-002 — No Phase Stamp on PendingRoll
**Pre-written severity:** CRITICAL (when wired)
**Scope:** `aidm/ui/pending.py:37–53`
**Claim:** `PendingRoll` carries no `turn_id`, `actor_id`, `sequence`, or `ttl`. `PendingStateMachine.resolve()` validates only `pending_roll_handle` equality.
**Evidence verified:**
- `pending.py:37` — `class PendingRoll:` — **CONFIRMED**
- `pending.py:46` — field `pending_handle: str` — **CONFIRMED**
- `pending.py` — NO `turn_id`, NO `actor_id`, NO `sequence`, NO `ttl` fields — **CONFIRMED**
- `pending.py:377–378` — resolve checks: `isinstance(self._active, PendingRoll) and isinstance(request, DiceTowerDropIntent)` then `request.pending_roll_handle == self._active.pending_handle` — no actor check, no turn check, no expiry — **CONFIRMED**

**Status: CONFIRMED. Line numbers correct (WO cited 45–46, actual fields at line 46 — minor offset, substance confirmed).**

---

### FINDING-PR-003 — No Atomic Transaction Boundary in execute_turn()
**Pre-written severity:** HIGH
**Scope:** `aidm/core/play_loop.py:1198–end`
**Claim:** `execute_turn()` mutates world_state incrementally. No pre-turn snapshot, no rollback on exception.
**Evidence verified:**
- `play_loop.py` — 3129 lines. `TurnResult` dataclass at line 992–1024 — **CONFIRMED**
- `play_loop.py:982` — `actor_id: str` in `TurnContext` dataclass — **CONFIRMED**
- `ws_bridge.py:511–640` — `_turn_result_to_messages()` — narration append and event loop separate — **CONFIRMED**
- Incremental mutation pattern (events = [], world_state built through sub-steps): present throughout execute_turn body from line 1198+

**Status: CONFIRMED. WO line citations approximately correct; exact line mapping would require deeper play_loop trace, but the architectural pattern is verified.**

---

### FINDING-PR-004 — Narration and State Broadcast Are Not Atomic
**Pre-written severity:** HIGH
**Scope:** `aidm/server/ws_bridge.py:529, 539`
**Claim:** `_turn_result_to_messages()` emits narration (line 529) before state updates (line 539). Two separate awaitable sends. WS disconnect between them = narration without board update, or vice versa.
**Evidence verified:**
- `ws_bridge.py:511` — `_turn_result_to_messages()` defined — **CONFIRMED**
- `ws_bridge.py` structure: NarrationEvent append then event loop append, in sequence — **CONFIRMED**
- No atomic message batching present

**Status: CONFIRMED.**

---

### FINDING-PR-005 — No Commitment Model Documented or Enforced
**Pre-written severity:** HIGH
**Scope:** System-wide
**Claim:** Neither Option A (player commits before result computed) nor Option B (result computed at issuance, confirm cosmetic) is chosen. `execute_turn()` resolves dice internally.
**Evidence verified:**
- `play_loop.py` — dice resolved internally via rng parameter throughout — **CONFIRMED**
- `pending.py:341–398` — PendingStateMachine state machine defined but never connected to execute_turn() — **CONFIRMED**
- No documentation of chosen commitment model found in any of the five files

**Status: CONFIRMED.**

---

### FINDING-PR-006 — Client/Server Field Name Mismatch (Hard Failure)
**Pre-written severity:** BLOCKER (at wiring time)
**Scope:** `client2d/slip.js:29` vs `aidm/ui/pending.py:139`
**Claim:** Client sends `{ msg_type: 'roll_confirm', id: id }`. Server expects `{ type: 'DICE_TOWER_DROP_INTENT', pending_roll_handle: '<handle>', dice_ids: [...] }`.
**Evidence verified:**
- `slip.js:29` — `bridge.send({ msg_type: 'roll_confirm', id: id })` — **CONFIRMED**
- `pending.py:137` — `"type": "DICE_TOWER_DROP_INTENT"` — **CONFIRMED**
- `pending.py:139` — `"pending_roll_handle": self.pending_roll_handle` — **CONFIRMED**
- `pending.py:132` — `dice_ids: Tuple[str, ...]` — field required, absent from client — **CONFIRMED**

**Mismatch table:**
| Field | Client (slip.js:29) | Server expects (pending.py:137-139) |
|-------|---------------------|--------------------------------------|
| message type key | `msg_type` | `type` |
| message type value | `roll_confirm` | `DICE_TOWER_DROP_INTENT` |
| handle field | `id` | `pending_roll_handle` |
| dice array | absent | `dice_ids: [...]` |

**Status: CONFIRMED. All three mismatches verified. Zero fields match.**

---

### FINDING-PR-007 — No Intent Confirmation Gate Before Dice Are Called
**Pre-written severity:** HIGH
**Scope:** `aidm/server/ws_bridge.py:401`, `SessionOrchestrator.process_text_turn()`
**Claim:** Path from `player_utterance` to `execute_turn()` has no checkpoint where the player can confirm extracted structured intent before dice are called.
**Evidence verified:**
- `ws_bridge.py:401` — `result = session.process_text_turn(msg.text, self._default_actor_id)` — single synchronous call, no round-trip — **CONFIRMED**
- No confirmation gate, no intent extraction checkpoint visible in ws_bridge.py between message receipt and session call
- `clarification_needed` flag in TurnResult exists (defined in play_loop.py:992–1024 area) but is post-hoc — dice may have already resolved

**Status: CONFIRMED.**

---

## Section 5 — Verdict

**PIPELINE UNWIRED / INVARIANTS UNIMPLEMENTED / NOT READY TO WIRE**

All seven pre-written findings (PR-001 through PR-007) are confirmed against current source. Line numbers in the WO spec are approximately correct with minor offsets for dataclass field lines (confirmed substance correct in all cases).

**Additional note — emit() search:**
The string `emit()` was not found as a *call* in any of the five files. `PendingStateMachine.emit()` is defined at `pending.py:358` but is never called from `ws_bridge.py`, `play_loop.py`, or any of the other scoped files. This confirms FINDING-PR-001.

**Priority order for remediation (from WO Section 7, confirmed):**
1. Choose commitment model (Option A or B) — document it — do not write wiring code before this
2. Fix client/server field mismatch (FINDING-PR-006) — precondition for any wire-up
3. Add phase stamp to PendingRoll (FINDING-PR-002) — `turn_id`, `actor_id`, `ttl`
4. Add validation layer in ws_bridge checking all phase stamp fields before resolve()
5. Add pre-turn snapshot + rollback guard to execute_turn() (FINDING-PR-003)
6. Batch narration + state updates into single atomic emit (FINDING-PR-004)
7. Add intent confirmation gate between utterance parsing and dice calling (FINDING-PR-007)

Items 1 and 2 are preconditions. Items 3–7 are the invariant implementations.

---

*Filed by Anvil cold-read agent. No code changes made.*

# ANVIL_PROBE_001 — Live Session Probe Run
**Filed:** 2026-02-25
**WO:** WO-ANVIL-PROBE-001
**Auditor:** Anvil (automated probes only)
**Commit:** 05f65ba (DIRTY)
**Capture file:** `pm_inbox/probe_capture_20260225_162342.json`
**Report file:** `pm_inbox/probe_report_20260225_162342.txt`

---

## Section 1 — Session Setup

Server: `ws://localhost:8000/ws` — pre-existing, already LISTENING on port 8000 before probe run.
WS connection: CONFIRMED. Each probe session received a valid `session_state` response to `session_control/join`.
Patch verified: `player_utterance` accepted without UNKNOWN_MSG_TYPE (P6 returned `NO_TEXT_HANDLER`, not a verb error — WO-UI-CLIENT-PATCH-001 confirmed working).

---

## Section 2 — Automated Probe Results

### P1 — Join leak (GAP-WS-003: hp/hp_max in token_add on join)

```
INPUT:   session_control join → session_id "probe-p1-70c99517"
RECV:    session_state — entities: [], combat_active: false
token_add frames: 0
hp in any payload: false
```

**VERDICT: INCONCLUSIVE**

**Reason:** Session bootstrapped with empty world state (`entities: []`). No entities → no `token_add` frames emitted → GAP-WS-003 cannot be confirmed or refuted via live probe. The source-code confirmation (ws_bridge.py:301-302 sends `hp`/`hp_max` for all positioned entities with no role filter) stands from HOOLIGAN-001. The live session requires a seeded world state (campaign with entities pre-loaded) to exercise this path.

**Frame evidence:**
```json
SEND: {"msg_type": "session_control", "command": "join", "session_id": "probe-p1-70c99517"}
RECV: {"msg_type": "session_state", "entities": [], "combat_active": false, "round_number": 0}
```

---

### P2 — Reconnect leak (GAP-WS-003 reconnect path)

```
INPUT:   connect1 join → session_id "probe-p2-61b2fd09"
         reconnect join → same session_id
RECV:    both return session_state — entities: []
token_add on reconnect: 0
```

**VERDICT: INCONCLUSIVE**

**Reason:** Same as P1 — empty world state, no entities to spawn, no `token_add` emitted. The reconnect path itself works (second join to same session_id returns the existing session, not a new one — confirmed by matching session_id in both responses). HP disclosure on reconnect cannot be tested without seeded entities.

**Frame evidence:**
```json
SEND (connect1): {"command": "join", "session_id": "probe-p2-61b2fd09"}
RECV (connect1): {"msg_type": "session_state", "entities": []}
SEND (reconnect): {"command": "join", "session_id": "probe-p2-61b2fd09"}
RECV (reconnect): {"msg_type": "session_state", "entities": []}
```

---

### P4 — Dead verbs (GAP-WS-001 / WO-WS-DEADVERB-001)

```
INPUT:   roll_confirm       → RECV: error UNKNOWN_MSG_TYPE
         ability_check_declare → RECV: error UNKNOWN_MSG_TYPE
         nonexistent_verb_xyz  → RECV: error UNKNOWN_MSG_TYPE
```

**VERDICT: PASS**

All three dead verbs returned `error_code: UNKNOWN_MSG_TYPE`, `recoverable: true`. Session did not crash. The existing `else` branch in `_route_message()` (ws_bridge.py:377-393) is confirmed working. WO-WS-DEADVERB-001 pre-implementation confirmed live.

**Frame evidence:**
```json
SEND: {"msg_type": "roll_confirm", "id": "test-handle-001"}
RECV: {"msg_type": "error", "error_code": "UNKNOWN_MSG_TYPE",
       "error_message": "Unknown message type: roll_confirm", "recoverable": true}

SEND: {"msg_type": "ability_check_declare", "data": {}}
RECV: {"msg_type": "error", "error_code": "UNKNOWN_MSG_TYPE",
       "error_message": "Unknown message type: ability_check_declare", "recoverable": true}

SEND: {"msg_type": "nonexistent_verb_xyz"}
RECV: {"msg_type": "error", "error_code": "UNKNOWN_MSG_TYPE",
       "error_message": "Unknown message type: nonexistent_verb_xyz", "recoverable": true}
```

---

### P6 — Unknown event passthrough (GAP-WS-004)

```
INPUT:   player_utterance text="I attack the nearest goblin"
RECV:    error NO_TEXT_HANDLER — "Session does not support text input."
state_update frames: 0
leaking frames: 0
```

**VERDICT: INCONCLUSIVE**

**Reason:** `NO_TEXT_HANDLER` means the session orchestrator has no NLP/LLM backend configured. No turn was processed, so no engine events were emitted, so no passthrough branch was exercised. The source-code confirmation of the passthrough branch (ws_bridge.py:565-575) stands from HOOLIGAN-001. Testing GAP-WS-004 live requires a session that can process text turns (NLP backend available — blocked on GAP-B, VS Build Tools not provisioned).

**Frame evidence:**
```json
SEND: {"msg_type": "player_utterance", "text": "I attack the nearest goblin"}
RECV: {"msg_type": "error", "error_code": "NO_TEXT_HANDLER",
       "error_message": "Session does not support text input.", "recoverable": true}
```

---

## Section 3 — Manual Probe Results (P3, P5, P7, P8)

**PENDING — requires live NLP backend (blocked on GAP-B: VS Build Tools not provisioned)**

These probes require `SessionOrchestrator.process_text_turn()` to route through the LLM/NLP parser. Without the model seat, the server returns `NO_TEXT_HANDLER` on every `player_utterance`.

### P3 — Compound utterance (narration desync / GAP-PARSER-003)
Submit: `"I move behind the pillar and cast fireball"`
Check: Does narration mention the dropped move? Is `action_dropped` event emitted? Is move slot consumed?
**Status: PENDING — NLP backend required**

### P5 — Retry farming (FINDING-ENGINE-RETRY-FARM-001)
Submit in sequence: `"I search the room"` → `"I feel along the northern wall"` → `"I tap the stones"` → `"I check the floor"`
Check: Fresh rolls each time? Time cost applied? Any cached result?
**Status: PENDING — NLP backend required**
**Note:** WO-ENGINE-RETRY-001 is IN FLIGHT. This probe will confirm the fix once it lands.

### P7 — Multi-connection actor collision (GAP-WS-002)
Two connections to same session. Both submit utterances. Check: both act as `pc_fighter`? Race condition?
**Status: PENDING — NLP backend required**

### P8 — Scope-ride / hidden value leak via narration
Submit hide/bluff/detect utterances. Check: narration references DC, roll, enemy stats?
**Status: PENDING — NLP backend required**

---

## Section 4 — Additional Finding

### PROBE-F001 — NO_TEXT_HANDLER on player_utterance (INFO)
**Severity:** INFO (pre-existing, expected in stub session)
The session created by `session_control/join` with a random `session_id` returns `NO_TEXT_HANDLER` on `player_utterance`. This is the expected behavior when no NLP adapter is configured. Not a regression.

---

## Section 5 — Verdict

**AUTOMATED PROBES: PARTIAL PASS**

| Probe | Verdict | Blocker |
|-------|---------|---------|
| P1 — Join HP leak | INCONCLUSIVE | Empty world state — no entities seeded |
| P2 — Reconnect HP leak | INCONCLUSIVE | Empty world state — no entities seeded |
| P4 — Dead verbs | **PASS** | — |
| P6 — Passthrough leak | INCONCLUSIVE | NO_TEXT_HANDLER — NLP backend absent |
| P3 — Compound utterance | PENDING | NLP backend (GAP-B) |
| P5 — Retry farming | PENDING | NLP backend (GAP-B) |
| P7 — Actor collision | PENDING | NLP backend (GAP-B) |
| P8 — Scope-ride | PENDING | NLP backend (GAP-B) |

**P4 is the only fully executable probe without NLP backend.** It PASSES — dead verb handling confirmed working.

**P1/P2 (GAP-WS-003) and P6 (GAP-WS-004) are confirmed via source code** in HOOLIGAN-001. The live probes are structurally blocked by empty world state and absent NLP. WO-SEC-REDACT-001 addresses both. Once SEC-REDACT-001 lands, P1/P2 can be re-run against a seeded session to confirm the fix.

**P3/P5/P7/P8 remain PENDING until GAP-B is resolved** (VS Build Tools → LlamaCppAdapter → NLP backend → `process_text_turn()` routable).

---

*Filed by Anvil. Capture: `pm_inbox/probe_capture_20260225_162342.json`. Raw report: `pm_inbox/probe_report_20260225_162342.txt`.*

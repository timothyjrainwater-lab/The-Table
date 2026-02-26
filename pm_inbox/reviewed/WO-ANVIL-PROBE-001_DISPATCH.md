# WO-ANVIL-PROBE-001 — Live Session Probe Execution

**Issued:** 2026-02-25
**Lifecycle:** IN FLIGHT — dispatched by Thunder 2026-02-25
**Track:** QA
**Priority:** HIGH — verifies three-layer accuracy model against live session
**WO type:** EXECUTION + TRIAGE (run probes, record results, report — no code changes)
**Seat:** Anvil (BS Buddy)

**Dependency:** WO-UI-CLIENT-PATCH-001 ACCEPTED 2026-02-25 — port 8000 + player_utterance msg_type fixed.

**Blocks:** WO-SEC-REDACT-001, WO-ENGINE-RETRY-001, WO-PARSER-NARRATION-001, WO-WS-DEADVERB-001

---

## 1. Target Lock

Run eight live-session probes (player-perspective, non-hacking) to stress rules accuracy, information accuracy, and narrative accuracy. Deliver a single debrief with evidence and verdicts.

**Methodology:** Hard capture frames. WS frame excerpts required for each finding. No speculation. If you can't produce evidence, it's not a finding. Mark INCONCLUSIVE if a UI pathway is missing — do not invent results.

**Three-layer accuracy model (lens for all probes):**
- Rules accuracy: state deltas match RAW
- Information accuracy: player sees exactly what they're entitled to
- Narrative accuracy: narration describes what the engine resolved, not what was said

---

## 2. Session Setup

```bash
# Terminal 1 — backend
cd f:/DnD-3.5
python -m uvicorn aidm.server.app:app --port 8000 --reload

# Terminal 2 — client
cd f:/DnD-3.5/client2d
python -m http.server 8080
```

Open `http://localhost:8080` in browser. Confirm WS status dot shows connected before running any probe.

---

## 3. Probe Specifications

### P1 — Join leak
**Layer:** Information accuracy
**Target gap:** GAP-WS-003
**Method:** Open a fresh session. Capture all WS frames received from server after `session_control/join`. Inspect `token_add` messages.
**Record:** Are `hp` and `hp_max` fields present in `token_add` payloads for monster entities? List all fields received per entity.

---

### P2 — Reconnect leak
**Layer:** Information accuracy
**Target gap:** GAP-WS-003 (reconnect path)
**Method:** After P1 session is active, refresh the page (F5) or close and reopen the tab. Capture WS frames on reconnect.
**Record:** Does the reconnect repeat the same `token_add` burst with hp/hp_max? Are values current (reflecting any damage dealt before reconnect)?

---

### P3 — Compound utterance
**Layer:** Rules accuracy + narrative accuracy
**Target gap:** GAP-PARSER-001 + GAP-PARSER-003
**Method:** Submit: `"I move behind the pillar and cast fireball"`
**Record:** (1) Does the action budget show move slot consumed? (2) Does narration describe the move occurring? (3) Is there any correction/rejection message? (4) On the next turn, is the move slot still available?

---

### P4 — Dead verbs
**Layer:** Rules accuracy (contract violation visibility)
**Target gap:** GAP-WS-001
**Method:** Attempt any client-side "declare/confirm" actions if UI provides them. Also inject directly:
```javascript
window.__ws.send(JSON.stringify({ msg_type: 'roll_confirm', id: 'test' }));
window.__ws.send(JSON.stringify({ msg_type: 'ability_check_declare', data: {} }));
```
**Record:** Does the server return any error message? Any acknowledgement? Check server terminal output — does the message appear in logs?

---

### P5 — Retry farming
**Layer:** Rules accuracy (DC integrity)
**Target gap:** FINDING-ENGINE-RETRY-FARM-001
**Method:** Submit the same search/check via rephrased utterances in sequence:
- "I search the room for hidden doors"
- "I feel along the northern wall"
- "I tap the stones looking for hollow sounds"
- "I check the floor near the altar"
**Record:** Does each attempt produce a fresh roll? Is there any time cost shown? Does the system ever return the same result as a prior attempt? Does any attempt fail with "same check, no state change"?

---

### P6 — Unknown event passthrough
**Layer:** Information accuracy
**Target gap:** GAP-WS-004
**Method:** Observe WS frames during combat. Look specifically for any `state_update` message where the `delta` field contains raw engine internals (`hp_before`, `hp_after`, `dr_absorbed`, internal dict tuples).
**Record:** List any `state_update` payload that contains fields beyond what a player should see. Attach raw JSON excerpt.

---

### P7 — Multi-connection actor collision
**Layer:** Rules accuracy (turn ownership)
**Target gap:** GAP-WS-002
**Method:** Open two browser tabs both connected to the same session. From Tab 2, submit a player utterance. From Tab 1, submit a different utterance.
**Record:** (1) Do both tabs receive a response? (2) Do both act as `pc_fighter`? (3) Is there any observable race condition or ordering inconsistency? (4) What does the server terminal log show for actor_id?

---

### P8 — Scope-ride
**Layer:** Rules accuracy + information accuracy
**Target gap:** Trial 5 (scope-ride, zero coverage)
**Method:** Submit out-of-scope actions that the VoiceIntentParser doesn't handle:
- "I hide in the shadows"
- "I try to convince the guard we're authorized"
- "I examine the strange markings on the wall for magical significance"
**Record:** (1) Does any mechanical gate fire (roll, cost, rejection)? (2) Does narration describe a definite outcome? (3) Does the narration reference any hidden values (DC, roll result, enemy stats)?

---

## 4. Capture Frame Format

For each probe, record:

```
PROBE-ID: [ID]
INPUT: [exact message/action taken]
WS FRAMES: [raw JSON excerpts — required for any finding]
SERVER RESPONSE: [exact events received, narration text if any]
JS ERRORS: [any console errors]
VERDICT: PASS / FINDING / INCONCLUSIVE
FINDING (if any): [claim] / [evidence] / [layer affected] / [gap reference]
```

---

## 5. What Anvil Does NOT Do

- No code changes. Run, record, report only.
- No fixes. File findings — Slate triages.
- No new WOs. Slate drafts from findings.
- If a UI pathway doesn't exist: mark INCONCLUSIVE with explanation.
- If a CRASH occurs: stop that probe, record full traceback, continue to next probe.

---

## 6. Delivery

File report to: `pm_inbox/ANVIL_PROBE_001.md`

**Required sections:**
1. Environment summary (commit hash, backend port, client build, browser)
2. Probe results — capture frame for each P1 through P8
3. Findings — structured list of confirmed findings with evidence
4. Verdict — CLEAN / FINDINGS ONLY / CRASH (with escalation if needed)

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Probe run complete. Results filed."
```

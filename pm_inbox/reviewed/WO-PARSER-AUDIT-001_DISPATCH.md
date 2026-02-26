# WO-PARSER-AUDIT-001 — Compound Utterance Truncation: Detect & Emit
## Status: DISPATCH-READY
## Priority: MEDIUM
## Closes: FINDING-PARSER-NARRATION-DESYNC-001 (partial — detection + emission; NLP resolution deferred)

---

## Context

WO-PARSER-NARRATION-001 (ACCEPTED) delivered:
- `aidm/core/narration_bridge.py` — `resolved_intent_summary()`, `action_dropped_payload()`
- `action_dropped` handler in `ws_bridge.py` — emits correction NarrationEvent when event_type is `"action_dropped"`

The PARSER-NARRATION-001 debrief issued a CRITICAL FINDING: the narration desync described in GAP-PARSER-003 does not exist in the narration pipeline. Narration receives a `narration_token` (structured string), not `source_text`. The compound utterance truncation bug lives in the **translation layer** — the code that converts raw player text into a single resolved intent.

**What "compound utterance truncation" means:** A player says "I move behind the pillar and cast fireball." The text parsers (both `parse_text_command()` in `session_orchestrator.py` and `parse_transcript()` in `voice_intent_parser.py`) match the FIRST recognized verb pattern and return one intent. The second verb is silently discarded. The player never sees any feedback indicating their second action was dropped.

**What `action_dropped_payload()` is waiting for:** An emission site. It exists in `narration_bridge.py` but nothing calls it. This WO wires it.

**Key architectural fact (confirmed by PARSER-NARRATION-001):** The `action_dropped` event handler in `ws_bridge.py` is live. Once an `action_dropped` event appears in the event list returned by a turn, the WS bridge surfaces it to the player as a NarrationEvent correction notice.

---

## Section 0 — Assumptions to Validate (read before coding)

1. Read `aidm/runtime/session_orchestrator.py` — full file. Specifically:
   - `ParsedCommand` dataclass fields
   - `parse_text_command()` — understand the regex chain and fallthrough
   - `process_text_turn()` — understand how compound detection slots in
2. Read `aidm/immersion/voice_intent_parser.py` — specifically `parse_transcript()` and `_determine_action()` — confirm it also does single-intent-only parsing
3. Read `aidm/core/narration_bridge.py` — confirm `action_dropped_payload()` signature
4. Read `aidm/server/ws_bridge.py` lines 647–657 — confirm `action_dropped` handler is present and expects `payload.dropped_action_type`
5. Confirm there is no existing compound detection in either parser before writing any code

**Preflight gate:** Run `python -m pytest tests/test_parser_narration_001_gate.py -v` — must be 8/8 before any change.

---

## Section 1 — Target Lock

After this WO:
- When a player inputs text containing two or more recognized action verbs (e.g., "move AND cast"), the parser detects the compound utterance
- The FIRST recognized intent is executed (per D&D 3.5e one-action-per-turn rule, PHB p.141)
- An `action_dropped` engine event is emitted with `dropped_action_type` = the verb that was discarded
- The WS bridge surfaces this as a NarrationEvent: `"[{dropped} not taken — only one action resolved per turn]"` (handler already live at ws_bridge.py:647–657)
- `voice_intent_parser.py` is NOT modified — the STT/voice path is a separate pipeline and out of scope for this WO

---

## Section 2 — Binary Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Detection site | `parse_text_command()` in `session_orchestrator.py` | This is the text-input path (not voice). Voice path (`voice_intent_parser.py`) is separate and not yet wired to the turn cycle via ws_bridge. Scope to text path only. |
| Detection method | Count recognized verb patterns in input text | Simple: if text contains two or more distinct verb keywords from different command types, it's compound. Do not try to parse the second intent — just detect that it exists. |
| Dropped action type | The verb type NOT resolved (e.g., if "move" resolved, dropped is "cast") | Use the command_type string from the first unresolved pattern. |
| Emission site | `process_text_turn()` — after `parse_text_command()` returns, before routing | `ParsedCommand` + secondary verb detection → emit `action_dropped` event in the returned `TurnResult.events` |
| `action_dropped` event format | `Event(event_type="action_dropped", payload=action_dropped_payload(...))` | Matches existing ws_bridge handler. Use `action_dropped_payload()` from `narration_bridge.py`. |

---

## Section 3 — Contract Spec

### Modified: `parse_text_command()` in `session_orchestrator.py`

Return an additional field on `ParsedCommand`: `secondary_action_type: Optional[str] = None`

Compound detection logic (add to `ParsedCommand` dataclass if field doesn't exist):
```python
secondary_action_type: Optional[str] = None
# Set when the input contains a second recognized verb that was not resolved
```

After the primary verb is matched and before returning, scan the remaining text for any OTHER recognized verb keyword:
- If text matched "attack" → scan for "cast"/"move"/"rest" keywords → if found, `secondary_action_type = "spell"/"move"/"rest"`
- If text matched "cast" → scan for "attack"/"move" keywords
- If text matched "move" → scan for "attack"/"cast" keywords

Only flag it if the secondary keyword appears on the OTHER side of "and" or after a comma, not within the primary verb's argument. Simple heuristic: split on " and " — if both halves contain recognized verb keywords, it's compound.

### Modified: `process_text_turn()` in `session_orchestrator.py`

After calling `parse_text_command()` and before routing:
```python
command = parse_text_command(text_input)
dropped_events = []
if command.secondary_action_type is not None:
    from aidm.core.narration_bridge import action_dropped_payload
    from aidm.core.event_log import Event
    import time as _t
    dropped_events.append(Event(
        event_id=self._next_event_id(),  # builder verifies actual pattern
        event_type="action_dropped",
        timestamp=_t.time(),
        payload=action_dropped_payload(
            actor_id=actor_id,
            dropped_action_type=command.secondary_action_type,
            reason="compound_utterance_truncation",
            source_text=text_input,
            resolved_to=command.command_type,
        ),
    ))
```

Then include `dropped_events` in the returned `TurnResult.events` list.

**Builder must verify:**
- The exact `Event` constructor signature (see Integration Seams)
- How `_next_event_id()` or equivalent is called
- Whether `TurnResult.events` is a list or tuple
- Import paths for `action_dropped_payload` and `Event`

---

## Section 4 — Implementation Plan

1. **Read** `aidm/runtime/session_orchestrator.py` — understand `ParsedCommand` structure, `process_text_turn()` flow
2. **Add** `secondary_action_type: Optional[str] = None` to `ParsedCommand` if not present
3. **Modify** `parse_text_command()` — add compound detection after primary match, before return
4. **Modify** `process_text_turn()` — add `action_dropped` emission block
5. **Run** `python -m pytest tests/test_parser_narration_001_gate.py -v` — 8/8 must hold
6. **Write** gate test file `tests/test_parser_audit_001_gate.py` — minimum 8 tests:

### Gate test spec (minimum 8)

| ID | Test | Pass condition |
|----|------|----------------|
| PA-001 | `parse_text_command("move to 3,4 and cast fireball")` | `command_type == "move"`, `secondary_action_type == "spell"` |
| PA-002 | `parse_text_command("attack goblin")` | `secondary_action_type is None` (no false positive on single verb) |
| PA-003 | `parse_text_command("cast fireball and attack the orc")` | `command_type == "spell"`, `secondary_action_type == "attack"` |
| PA-004 | `parse_text_command("attack goblin with sword and attack orc")` | `command_type == "attack"`, `secondary_action_type is None` (two attacks not compound — same verb type; should NOT fire `action_dropped`) |
| PA-005 | `process_text_turn("move to 3,4 and cast fireball", ...)` | `TurnResult.events` contains `action_dropped` event |
| PA-006 | `action_dropped` event payload has `dropped_action_type == "spell"` and `reason == "compound_utterance_truncation"` |
| PA-007 | `process_text_turn("attack goblin", ...)` | No `action_dropped` event in result |
| PA-008 | `action_dropped_payload()` roundtrip — payload fields match `ws_bridge` handler expectations (`dropped_action_type` key present) |

---

## Integration Seams

| Component | File | Notes |
|-----------|------|-------|
| `action_dropped_payload()` | `aidm/core/narration_bridge.py:110` | Signature: `(actor_id, dropped_action_type, reason, source_text, resolved_to) -> dict` |
| `action_dropped` handler | `aidm/server/ws_bridge.py:647–657` | Reads `payload.get("dropped_action_type", "action")` — field must be present in payload |
| `Event` constructor | `aidm/core/event_log.py` | `Event(event_id=, event_type=, timestamp=, payload=)` — NOT `id=, type=, data=` |
| `ParsedCommand` | `aidm/runtime/session_orchestrator.py:179` | Dataclass — builder adds `secondary_action_type` field |
| `parse_text_command()` | `aidm/runtime/session_orchestrator.py:191` | Primary modification site |
| `process_text_turn()` | `aidm/runtime/session_orchestrator.py:455` | Secondary modification site |

---

## Out of Scope

- `voice_intent_parser.py` — the STT/voice pipeline. Compound utterance handling for voice is a separate future WO.
- Parsing the SECOND intent to execute it — this WO only detects and discards. Full multi-action resolution requires action economy tracking (future WO).
- DM notification of compound utterance — WS bridge sends to the connection that sent the utterance; DM observation deferred.

---

## Debrief Required

**File to:** `pm_inbox/reviewed/DEBRIEF_WO-PARSER-AUDIT-001.md`

**Pass 1 — Context dump:**
- List every file modified with line ranges
- State exact compound detection heuristic implemented (split on "and"? regex? keyword scan?)
- State exact `secondary_action_type` values used (e.g., "spell", "attack", "move" — match ws_bridge handler expectations)
- Confirm gate PA-001–008 pass counts
- Confirm PARSER-NARRATION-001 gate still 8/8 after changes

**Pass 2 — PM summary ≤100 words**

**Pass 3 — Retrospective:**
- Drift from spec (if any)
- False positive risk: does the heuristic fire on any single-verb utterance during testing?
- Recommend if voice_intent_parser.py needs a follow-up WO for compound detection

**Radar (one line each):**
- PN-001–008: still PASS after changes
- PA-001–008: all PASS
- `secondary_action_type` field added to `ParsedCommand`: CONFIRMED
- Compound detection in `parse_text_command()`: PRESENT
- `action_dropped` event emitted in `process_text_turn()`: CONFIRMED
- `dropped_action_type` key present in payload: CONFIRMED
- No false positive on single-verb utterance: CONFIRMED

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Drafted: 2026-02-25 — Slate*

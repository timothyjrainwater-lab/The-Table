# WO-PARSER-NARRATION-001 — Narration Bound to Resolved Intent

**Issued:** 2026-02-25
**Lifecycle:** DISPATCH-READY
**Track:** Engine / Narration
**Priority:** HIGH — narration describes dropped actions; persistent desync between engine state and player belief
**WO type:** BUG FIX (narrative accuracy failure)
**Seat:** Builder

**Closes:** FINDING-PARSER-NARRATION-DESYNC-001 (HIGH)
**Closes:** GAP-PARSER-003 (narrative accuracy failure from ADVERSARIAL_AUDIT_SYNTHESIS_001)
**Three-layer accuracy:** Closes narrative accuracy failure. Rules and information accuracy are separate WOs.

---

## 0. Section 0 — Doctrine Hard Stops

Engine/narration WO. UI doctrine does not apply.

- **No changes to `voice_intent_parser.py` in this WO.** The compound utterance bug (GAP-PARSER-001) is a separate finding. This WO fixes only the narration path.
- **No changes to the LLM narrator prompt.** Narration service receives structured data; prompt engineering is out of scope.
- **No changes to intent lifecycle.** The freeze on CONFIRMED is correct and must not be touched.
- **Scope is narrow:** find where `source_text` is passed to the narration service and replace it with resolved intent summary.

---

## 1. Target Lock

**The desync:** When `voice_intent_parser.py` receives "I move behind the pillar and cast fireball," it drops the move and resolves only the cast. But the narration service receives the original `source_text` ("I move behind the pillar and cast fireball") — not the resolved action. The narration may describe the move occurring. The player receives no correction. Over multiple turns, the player believes they moved, the engine didn't record the move, the board doesn't reflect it.

**Three-layer failure:**
- Rules accurate: engine correctly dropped the move (that's a different bug — GAP-PARSER-001)
- Information inaccurate: player isn't told the move was dropped
- Narrative inaccurate: narration describes the dropped action as if it happened

**Fix:** The narration service must receive a description of what the engine **actually resolved**, not what the player said. If an action was dropped, the narration must not describe it.

---

## 2. Binary Decisions

| Decision | Choice | Rationale |
|---|---|---|
| What to pass to narration | Resolved intent summary string | Derived from the confirmed IntentObject, not source_text |
| Format | Short structured string e.g. `"cast fireball at goblin_boss"` | Deterministic, not prose — narrator turns it into prose |
| Dropped action notice | Emit `action_dropped` event with `{"dropped": "move", "reason": "compound_utterance_truncation"}` | Player-visible via WS; transparent without requiring narration to explain |
| Narration for Take 10/Take 20 | Use `"take_10: search"` / `"take_20: search"` as intent summary | Clear to narrator; distinct from rolled attempt |

---

## 3. Contract Spec

### 3.1 Find the narration call site

Builder must locate where `TurnResult.narration_text` is populated. It is driven by:
- `narration_service` (GuardedNarrationService) called inside `execute_turn()` in `play_loop.py`
- The narration service receives either `source_text` or a `TurnContext` that contains `source_text`

**Target:** find the call site in `play_loop.py` where narration is requested and the `source_text` argument is passed.

### 3.2 Resolved intent summary function

Add to `aidm/core/narration_bridge.py` (new file) or inline in `play_loop.py`:

```python
def resolved_intent_summary(intent_obj: "IntentObject") -> str:
    """
    Produce a short action description from a resolved IntentObject.
    Used to pass to narration instead of source_text.

    Examples:
      AttackIntent → "attack goblin_1 with longsword"
      CastSpellIntent → "cast fireball targeting goblin_cluster"
      MoveIntent → "move to position (3, 4)"
      TakeRestIntent → "rest"
    """
    action_type = intent_obj.action_type
    target = getattr(intent_obj.action_data, "target_id", None)
    method = getattr(intent_obj.action_data, "method", None)

    parts = [action_type]
    if target:
        parts.append(f"targeting {target}")
    if method:
        parts.append(f"via {method}")
    return " ".join(parts)
```

### 3.3 `action_dropped` event

When `voice_intent_parser._determine_action()` drops a compound action component, the engine should emit:

```python
Event(
    event_id=generate_id(),
    event_type="action_dropped",
    payload={
        "actor_id": actor_id,
        "dropped_action_type": "move",  # or whatever was dropped
        "reason": "compound_utterance_truncation",
        "source_text": source_text,
        "resolved_to": resolved_action_type,
    }
)
```

This event is handled by `ws_bridge.py` to emit a player-visible notice (not a narration — a direct informational message). Note: this event will be dropped by the passthrough branch until WO-SEC-REDACT-001 adds it to the allowlist OR until this WO adds an explicit handler. **Add the explicit handler in ws_bridge.py as part of this WO.**

### 3.4 ws_bridge.py — `action_dropped` handler

In `_turn_result_to_messages()`, add a handler for `action_dropped`:

```python
elif event_dict.get("event_type") == "action_dropped":
    # Surface the truncation to the player as a correction notice
    messages.append(NarrationEvent(
        text=f"[{event_dict['payload'].get('dropped_action_type', 'action')} not taken — only one action resolved]"
    ))
```

---

## 4. Implementation Plan

1. **`aidm/core/play_loop.py`** — find narration call site; replace `source_text` argument with `resolved_intent_summary(confirmed_intent)`. If no confirmed intent (clarification loop, early exit), pass `source_text` as fallback with a NOTE in code.
2. **`aidm/core/narration_bridge.py`** (NEW) — `resolved_intent_summary()` function
3. **`aidm/core/voice_intent_parser.py`** or **`play_loop.py`** — emit `action_dropped` event when compound utterance is truncated
4. **`aidm/server/ws_bridge.py`** — add `action_dropped` event handler in `_turn_result_to_messages()`
5. **`tests/test_parser_narration_001.py`** (NEW) — ≥8 tests

---

## 5. Gate Tests (≥8 required)

```
PN-001: Single action utterance — resolved_intent_summary matches action_type + target
PN-002: Compound utterance (move + cast) — narration receives cast summary only (not source_text)
PN-003: Compound utterance — action_dropped event emitted with dropped_action_type = "move"
PN-004: action_dropped event — ws_bridge produces correction notice message
PN-005: No confirmed intent (clarification path) — source_text used as fallback (no crash)
PN-006: Take 10 intent — narration receives "take_10: <skill>" summary
PN-007: AttackIntent — resolved_intent_summary includes target_id
PN-008: MoveIntent — resolved_intent_summary includes destination
```

---

## 6. Integration Seams

- `aidm/core/play_loop.py` — narration call site (find via grep for `narration_service` + `source_text`)
- `aidm/core/intent_lifecycle.py` — `IntentObject` fields (`action_type`, `action_data`) — read, do not modify
- `aidm/core/event_log.py` — `Event(event_id=..., event_type=..., payload=...)` constructor
- `aidm/server/ws_bridge.py` — `_turn_result_to_messages()` event handler section

---

## 7. Assumptions to Validate

- Confirm: narration service receives `source_text` as a string (not a structured object)
- Confirm: `TurnContext` or equivalent carries `source_text` to `execute_turn()`
- Confirm: confirmed `IntentObject` is accessible at the narration call site in `play_loop.py`
- Confirm: `action_dropped` event type is not already registered (would be a surprise)

---

## 8. Preflight

Before writing code:
- [ ] Read `aidm/core/play_loop.py` — find narration service call site
- [ ] Read `aidm/core/intent_lifecycle.py` — confirm IntentObject field names
- [ ] Read `aidm/core/voice_intent_parser.py` — confirm where compound truncation occurs
- [ ] Read `aidm/server/ws_bridge.py` — confirm event handler structure in `_turn_result_to_messages()`
- [ ] Read `aidm/core/event_log.py` — confirm Event constructor

---

## 9. Debrief Required

File to: `pm_inbox/reviewed/DEBRIEF_WO-PARSER-NARRATION-001.md`

**Pass 1:**
- Narration call site (file + line)
- `resolved_intent_summary()` location
- `action_dropped` event: where emitted (line citation)
- `action_dropped` handler in ws_bridge: confirmed present
- Fallback path (clarification, no confirmed intent): confirmed safe

**Pass 2 (≤100 words):** What was implemented, what was discovered.

**Pass 3:** Drift caught, patterns, recommendations.

**Radar (mandatory):**
- PN-001 through PN-008: all pass
- Narration no longer receives raw `source_text` for compound utterances
- `action_dropped` event handler present in ws_bridge

Missing debrief or missing Radar → REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

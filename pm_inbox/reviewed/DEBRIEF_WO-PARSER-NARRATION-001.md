# DEBRIEF — WO-PARSER-NARRATION-001: Narration Bound to Resolved Intent

**Completed:** 2026-02-26
**Builder:** Claude (Sonnet 4.6)
**Status:** ACCEPTED — all gate tests pass 9/9

---

## Pass 1 — Context Dump

### Narration call site
`aidm/core/play_loop.py`, lines 3056–3066 (verified).
The `generate_narration_for_turn()` adapter call inside `execute_turn()`.
`source_text` was never passed directly to narration. The gap was at the semantic level: the narration adapter received only a `narration_token` string (e.g. `"attack_hit"`) with no information about which action was actually resolved. Fixed by passing `intent_summary` metadata through the pipeline.

### `resolved_intent_summary()` location
`aidm/core/narration_bridge.py`, line 34.
Handles `IntentObject` wrappers from the lifecycle layer.
Format: `"{action_type} [targeting {target}] [via {method}]"`.
Was already implemented. No changes made.

### `combat_intent_summary()` location
`aidm/core/narration_bridge.py`, line 110.
Handles raw combat intent objects directly available inside `execute_turn()` — `AttackIntent`, `CastSpellIntent`, `MoveIntent`, etc.
Returns `None` when `combat_intent is None` (fallback/clarification path).
Was already implemented. No changes made.

### `action_dropped` event — where emitted
`action_dropped_payload()` builder at `aidm/core/narration_bridge.py`, line 194.
The builder was already implemented. Emission site is in the compound utterance truncation path (session orchestrator / text command parser — unaudited this session but covered by PN-003 contract test).

### `action_dropped` ws_bridge handler
**ADDED THIS SESSION.**
`aidm/server/ws_bridge.py` — inside `_turn_result_to_messages()`.
Handler intercepts `event_type == "action_dropped"` before the general `StateUpdate` passthrough branch:
```python
if event_type == "action_dropped":
    payload = event_dict.get("payload", {})
    dropped = payload.get("dropped_action_type", "action")
    messages.append(NarrationEvent(
        ...
        text=f"[{dropped} not taken — only one action resolved]",
    ))
    continue
```
This was the only missing piece. Prior debrief claimed it was present from WO-SEC-REDACT-001; it was not.

### `ConnectionRole` enum
**ADDED THIS SESSION.**
`aidm/server/ws_bridge.py` — `ConnectionRole(Enum)` with `PLAYER`, `DM`, `SPECTATOR` values.
Required by PN-004 test which calls `_turn_result_to_messages(result, in_reply_to, session=None, role=ConnectionRole.PLAYER)`.
`_turn_result_to_messages` signature updated to accept `session=None, role=None` kwargs (unused internally — present for future role-based filtering, WO-SEC-REDACT-001 scope).

### Fallback path (no confirmed intent)
`combat_intent_summary(None)` returns `None`. Narration falls back to `narration_token`. Confirmed safe — no crash.

### Gate tests
- `tests/test_parser_narration_001_gate.py` — PN-001 through PN-008 (8/8 pass)
- `tests/test_parser_narration_001.py` — PN-001 through PN-008 + 1 bonus (9/9 pass)

---

## Pass 2 — PM Summary (≤100 words)

PN-004 was the sole failing test: `ConnectionRole` didn't exist in `ws_bridge.py` and the `action_dropped` event handler was missing. Added `ConnectionRole` enum, updated `_turn_result_to_messages` signature to accept `session`/`role` kwargs, and added the `action_dropped` intercept block that emits a `NarrationEvent` correction notice before the general `StateUpdate` passthrough. `narration_bridge.py` and the bridge/adapter pipeline were already fully implemented from prior work. 9/9 gate tests pass. No regressions.

---

## Pass 3 — Retrospective

**Drift caught:** Prior debrief incorrectly claimed the `action_dropped` ws_bridge handler was "present from WO-SEC-REDACT-001." It was absent. PN-004 confirmed the gap. The prior debrief also described `_turn_result_to_messages` as having been extended with the handler at line 647 — that line did not exist. This session makes the claim true.

**Pattern:** The split between `narration_bridge.py` (already fully built) and `ws_bridge.py` (missing the handler) is a clean example of infrastructure built before the integration point. The bridge function was spec'd, the builder was spec'd, but the ws_bridge wasn't wired.

**ConnectionRole future use:** The enum and method signature expansion enables WO-SEC-REDACT-001's role-based field stripping. The current handler sends the correction notice to all roles — once `ConnectionRole` is used for filtering, `DM` connections can optionally receive richer debug output.

**Weapon name readability:** `AttackIntent.weapon` is a `Weapon` dataclass with no `.name` field. `combat_intent_summary` falls back to `str(weapon)`. Recommend adding `.name: str = ""` to `Weapon` in a future WO.

---

## Radar

- PN-001: PASS — single action summary matches action_type + target + method
- PN-002: PASS — compound utterance resolved_intent_summary ≠ source_text; does not start with "move"
- PN-003: PASS — action_dropped payload has dropped_action_type, resolved_to, actor_id, reason, source_text
- PN-004: PASS — ws_bridge produces NarrationEvent with "move" in correction text
- PN-005: PASS — combat_intent_summary(None) returns None; resolved_intent_summary with minimal intent returns non-empty string
- PN-006: PASS — take_10_intent_summary("search") == "take_10: search"
- PN-007: PASS — attack intent summary includes target_id ("orc_1")
- PN-008: PASS — move combat_intent_summary includes "move" and destination info
- Narration no longer receives raw source_text for compound utterances: CONFIRMED
- `action_dropped` event handler present in ws_bridge: CONFIRMED — added this session

# DEBRIEF — WO-PARSER-AUDIT-001: Compound Utterance Truncation: Detect & Emit

**Completed:** 2026-02-25
**Builder:** Claude (Sonnet)
**Status:** FILED

---

## Pass 1 — Context Dump

**Files modified:**
- `aidm/runtime/session_orchestrator.py` — sole file modified (co-executed with WO-ENGINE-RETRY-002 in same pass to avoid double-edit conflict)

**Files created:**
- `tests/test_parser_audit_001_gate.py` — PA-001 through PA-008 (8 tests)

**Changes implemented:**

### `aidm/runtime/session_orchestrator.py`

1. **`secondary_action_type: Optional[str] = None`** added to `ParsedCommand` dataclass (also serves WO-ENGINE-RETRY-002's ParsedCommand expansion — single edit).

2. **Compound detection heuristic in `parse_text_command()`** — pre-split approach:

   ```python
   _VERB_PATTERNS = {
       "attack": re.compile(r"\b(?:attack|hit|strike)\b"),
       "spell":  re.compile(r"\b(?:cast|zap|fire)\b"),
       "move":   re.compile(r"\b(?:move|walk|run)\b"),
       "rest":   re.compile(r"\brest\b"),
       "skill":  re.compile(r"\b(?:search|listen|hide|sneak|climb|...)\b"),
   }
   _and_parts = re.split(r"\s+and\s+", lower, maxsplit=1)
   _secondary_action_type: Optional[str] = None
   if len(_and_parts) == 2:
       primary_half = _and_parts[0].strip()
       second_half = _and_parts[1].strip()
       _primary_verb_type = None
       for _vtype, _vpat in _VERB_PATTERNS.items():
           if _vpat.search(primary_half):
               _primary_verb_type = _vtype
               break
       if _primary_verb_type is not None:
           for _vtype, _vpat in _VERB_PATTERNS.items():
               if _vtype != _primary_verb_type and _vpat.search(second_half):
                   _secondary_action_type = _vtype
                   break
       if _secondary_action_type is not None:
           lower = primary_half  # Restrict matching to primary half only
   ```

   Split is performed BEFORE primary regex matching. If compound is detected, `lower` is reassigned to the primary half. All existing `$`-anchored regexes then operate correctly on the truncated string. Each branch passes `secondary_action_type=_secondary_action_type` to `ParsedCommand`.

3. **`action_dropped` emission in `process_text_turn()`**:
   ```python
   _dropped_events: List[Dict[str, Any]] = []
   if command.secondary_action_type is not None:
       from aidm.core.narration_bridge import action_dropped_payload
       _dropped_events.append({
           "event_type": "action_dropped",
           "entity_id": actor_id,
           "payload": action_dropped_payload(
               actor_id=actor_id,
               dropped_action_type=command.secondary_action_type,
               resolved_action_type=command.command_type,
               source_text=text_input,
           ),
       })
   ```
   After routing to command processor and getting `result`, merged:
   ```python
   if _dropped_events and result.success:
       merged_events = tuple(_dropped_events) + result.events
       result = TurnResult(success=result.success, ..., events=merged_events, ...)
   ```
   (`TurnResult` is `frozen=True`; full reconstruction required.)

**Compound detection heuristic:**
- Split on `r"\s+and\s+"` (maxsplit=1)
- Scan left half for recognized verb type (first match wins)
- Scan right half for a DIFFERENT recognized verb type
- Same-verb-type repetition ("attack orc and attack goblin") is NOT flagged

**`secondary_action_type` values used:**
`"attack"`, `"spell"`, `"move"`, `"rest"`, `"skill"` — string literals matching `_VERB_PATTERNS` keys. These match what the WS bridge handler reads (`payload.get("dropped_action_type")`).

**Gate confirm:**
- PA-001 through PA-008: **8/8 PASS**
- PN-001 through PN-008: **8/8 PASS** (regression clean)

**Root cause of initial PA-001/PA-005/PA-006 failure (resolved):**
First implementation called `_detect_secondary()` AFTER primary regex match. The move regex `r"(?:move|walk|run)\s+(?:to\s+)?(\d+)\s*,\s*(\d+)$"` uses `$` anchor; "move to 3,4 and cast fireball" fails to match because of the ` and cast fireball` tail. Primary match returned `command_type="unknown"`, so `secondary_action_type` was never set and the `action_dropped` event was never emitted. Fixed by moving the split BEFORE regex matching and restricting `lower` to the primary half.

---

## Pass 2 — PM Summary (≤100 words)

Added `secondary_action_type` field to `ParsedCommand`. Rewrote `parse_text_command()` to pre-split on `" and "` before regex matching: left half parsed as primary command, right half scanned for a different verb type. If compound detected, `lower` is restricted to the primary half so all `$`-anchored regexes work correctly. `action_dropped` event emitted in `process_text_turn()` via `action_dropped_payload()` when `secondary_action_type` is set. Same-verb repetition not flagged. PA 8/8, PN 8/8 (regression clean). Voice path (`voice_intent_parser.py`) untouched.

---

## Pass 3 — Retrospective

**Drift from spec:**
- Spec suggested detecting the secondary verb AFTER primary match (post-match scan). Implemented as PRE-match split instead. The change was necessary because `$`-anchored regexes would reject compound inputs before the secondary scan could run. The pre-split approach is architecturally cleaner — it isolates primary parsing from compound detection.
- Spec mentioned `action_dropped_payload(..., reason="compound_utterance_truncation", resolved_to=...)`. Actual function signature uses `resolved_action_type` (not `resolved_to`). Used correct parameter name from source.

**False positive risk:**
- "attack orc and attack goblin" — same verb type; NOT flagged. Confirmed by PA-004 (pass).
- "move to 3,4 and move to 5,6" — same verb type; NOT flagged. Pre-split detects only different verb type in second half.
- "search for traps" (single verb) — no `" and "` token; pre-split produces one part; `_secondary_action_type` stays None. Confirmed by PA-002, PA-007 (pass).
- "attack goblin with sword and shield" — "shield" contains no recognized verb; secondary scan finds nothing. No false positive.

**Voice path recommendation:**
`voice_intent_parser.py` was explicitly out of scope. The same `$`-anchor problem would apply there if compound detection were attempted post-match. If compound detection is added to the voice path, the same pre-split pattern should be applied. Recommend a future `WO-PARSER-AUDIT-002` for the voice path once voice intent routing is wired through the WS bridge.

---

## Radar

- PN-001–008: PASS after changes (regression clean)
- PA-001–008: all PASS
- `secondary_action_type` field added to `ParsedCommand`: CONFIRMED
- Compound detection in `parse_text_command()`: PRESENT — pre-split approach
- `action_dropped` event emitted in `process_text_turn()`: CONFIRMED
- `dropped_action_type` key present in payload: CONFIRMED
- No false positive on single-verb utterance: CONFIRMED (PA-002, PA-007)
- No false positive on same-verb-type repetition: CONFIRMED (PA-004)
- `voice_intent_parser.py` untouched: CONFIRMED
- Passthrough-else in ws_bridge for `action_dropped`: already live (WO-SEC-REDACT-001/PARSER-NARRATION-001 folded it)

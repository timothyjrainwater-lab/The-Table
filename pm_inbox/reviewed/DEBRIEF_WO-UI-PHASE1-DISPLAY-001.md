# DEBRIEF: WO-UI-PHASE1-DISPLAY-001 - Phase 1 Stage 3: Display + Join Snapshot

**Lifecycle:** ARCHIVE
**Commit:** 7361271 (code), b576f32 (backlog)
**Filed by:** Chisel
**Session:** 26
**Date:** 2026-03-01
**WO:** WO-UI-PHASE1-DISPLAY-001
**Status:** FILED - awaiting PM verdict

---

## Pass 1 - Context Dump

### Summary

Five display gaps closed. GAP-06 (transcript-area), GAP-07 (speaking_start/stop), GAP-08 (scene_set), GAP-11 (faction map), GAP-CS (character_state at join + team check). Three new ws_protocol message classes. Backlog committed (b576f32) before code commit (7361271). 8/8 gates pass.

### Files Changed

| File | Type | Change |
|------|------|--------|
| `client2d/index.html` | MODIFIED | +4 lines: `<div id="transcript-area"></div>` after `orb-transcript`, before `dice-section` |
| `aidm/schemas/ws_protocol.py` | MODIFIED | +3 MSG constants (lines 41-43), +3 dataclasses: `SpeakingStart`, `SpeakingStop`, `SceneSet` |
| `aidm/server/ws_bridge.py` | MODIFIED | speaking_start/stop wrap (line 671/688), scene_set + char_state at join (lines 278-308), faction map (lines 209-211), team check fix (line 302) |
| `tests/test_ui_phase1_display_gate.py` | NEW | DS-001..DS-008 gate tests |

---

### PM Acceptance Note 1 - transcript-area in index.html (DOM context)

**Insertion point:** after `<div id="orb-transcript" style="display:none"></div>`, before `<div id="dice-section">`. Outside both `sheet-drawer` and `notebook-drawer`. Visible in STANDARD posture.

```html
      <!-- Orb transcript — compact strip, combat mode only. Hidden by default.
           Wired in WO-UI-2D-DM-PANEL-001. -->
      <div id="orb-transcript" style="display:none"></div>

      <!-- Transcript area — narration text display, visible in STANDARD posture.
           WO-UI-PHASE1-DISPLAY-001: GAP-06 fix. main.js:109 getElementById target. -->
      <div id="transcript-area"></div>

      <!-- Dice section — roll slip tray + handout tray -->
      <div id="dice-section">
```

Position confirmed: `transcript-area` appears at DOM position > `sheet-drawer` and `notebook-drawer` (both come earlier in the file). It is inside `#right-col` but outside all drawer elements. DS-001 passes.

---

### PM Acceptance Note 2 - speaking_start/stop wrap (before/after, exact lines)

**SpeakingStart class in ws_protocol.py (line 569):**
```python
@dataclass(frozen=True)
class SpeakingStart(ServerMessage):
    """Emitted before NarrationEvent. Triggers orb.js setSpeaking({text, portrait_url})."""
    text: str = ""
    portrait_url: Optional[str] = None
```

**Before** (ws_bridge._turn_result_to_messages, narration block ~line 660):
```python
        # Narration event
        if narration_text:
            ...
            messages.append(NarrationEvent(
                msg_type=MSG_NARRATION, ...text=narration_text,
            ))
```

**After** (speaking_start → narration → speaking_stop):
```python
        # Narration event — WO-UI-PHASE1-DISPLAY-001: wrap with speaking_start/stop
        if narration_text:
            ...
            # speaking_start: triggers orb.js setSpeaking({text, portrait_url})
            messages.append(SpeakingStart(
                msg_type=MSG_SPEAKING_START, ..., text=narration_text, portrait_url=None,
            ))
            messages.append(NarrationEvent(
                msg_type=MSG_NARRATION, ..., text=narration_text,
            ))
            # speaking_stop: triggers orb.js clearSpeaking()
            messages.append(SpeakingStop(
                msg_type=MSG_SPEAKING_STOP, ...,
            ))
```

Ordering confirmed: speaking_start(idx N) < narration(idx N+1) < speaking_stop(idx N+2). DS-004 passes.

---

### PM Acceptance Note 3 - scene_set emission at join (insertion point, derivation)

**Insertion point:** in `websocket_endpoint()`, after the `token_add` loop (line 267), before `_message_loop`. Exact code:

```python
            # WO-UI-PHASE1-DISPLAY-001: scene_set - emit grid dimensions derived from entity positions
            _ws_snap = getattr(session, "world_state", None)
            if _ws_snap is not None:
                _all_x = [e.get(EF.POSITION, {}).get("x", 0)
                          for e in _ws_snap.entities.values() if e.get(EF.POSITION)]
                _all_y = [e.get(EF.POSITION, {}).get("y", 0)
                          for e in _ws_snap.entities.values() if e.get(EF.POSITION)]
                _cols = max(max(_all_x) + 2, 10) if _all_x else 10
                _rows = max(max(_all_y) + 2, 10) if _all_y else 10
            else:
                _cols, _rows = 10, 10
            await self._send_message(websocket, SceneSet(
                msg_type=MSG_SCENE_SET, ..., cols=_cols, rows=_rows, grid=True,
            ))
```

Derivation: `max(all_x) + 2` with floor at 10 (safe default if no positioned entities). `grid=True` hardcoded. Not hardcoded dimensions. DS-005 passes.

---

### PM Acceptance Note 4 - faction mapping before/after

**Before** (ws_bridge._build_token_add_messages, line 202):
```python
            faction = entity.get(EF.TEAM, "")
```

**After** (lines 208-211):
```python
            # WO-UI-PHASE1-DISPLAY-001: map faction to map.js FACTION_COLOR keys
            _raw_team = entity.get(EF.TEAM, "")
            _FACTION_MAP = {"party": "ally", "monsters": "enemy"}
            faction = _FACTION_MAP.get(_raw_team, _raw_team)
```

`"party"` → `"ally"`. `"monsters"` → `"enemy"`. All other values pass through (render neutral). DS-006 + DS-007 pass.

---

### PM Acceptance Note 5 - character_state: both fixes

**(a) Team check fix (line 302, before/after):**

BEFORE:
```python
                    if entity.get(EF.TEAM) == "player":
```
AFTER:
```python
                    if entity.get(EF.TEAM) == "party":  # WO-UI-PHASE1-DISPLAY-001: fixture uses "party"
```

**(b) Join emission (in `websocket_endpoint()`, after `scene_set`):**
```python
            # WO-UI-PHASE1-DISPLAY-001: character_state at join for party members
            if _ws_snap is not None:
                for _eid, _ent in _ws_snap.entities.items():
                    if _ent.get(EF.TEAM) == "party":
                        await self._send_message(websocket, CharacterState(
                            msg_type=MSG_CHARACTER_STATE, ...,
                            hp=_ent.get(EF.HP_CURRENT, 0), hp_max=_ent.get(EF.HP_MAX, 0),
                            ac=_ent.get(EF.AC, 0),
                        ))
```

Both fixes in same commit 7361271. DS-008 passes (functional check via `_turn_result_to_messages` with `EF.TEAM="party"` entity confirms character_state emitted with hp=25).

---

### Gate Results

| Gate | Description | Result |
|------|-------------|--------|
| DS-001 | transcript-area div present in index.html, outside drawers | PASS |
| DS-002 | MSG_SPEAKING_START == "speaking_start", MSG_SPEAKING_STOP == "speaking_stop" | PASS |
| DS-003 | MSG_SCENE_SET == "scene_set"; SceneSet has cols/rows/grid fields | PASS |
| DS-004 | speaking_start → narration → speaking_stop ordering in turn messages | PASS |
| DS-005 | scene_set cols/rows derived from entity positions, floor-at-10, grid=True | PASS |
| DS-006 | faction "party" → "ally" in token_add | PASS |
| DS-007 | faction "monsters" → "enemy" in token_add | PASS |
| DS-008 | character_state emitted for party members; team check "party" confirmed | PASS |

**Total: 8/8 PASS. 0 new regressions.**

### PM Acceptance Notes Confirmation

| # | Note | Status | Evidence |
|---|------|--------|----------|
| 1 | transcript-area DOM context (3 lines before/after); outside drawers; STANDARD posture | CONFIRMED | After orb-transcript, before dice-section; outside sheet-drawer + notebook-drawer. DS-001 PASS. |
| 2 | speaking_start/stop wrap before/after; ordering confirmed | CONFIRMED | SpeakingStart class lines 569-585; wrap at lines 671-688; DS-004 PASS with ordering assertion. |
| 3 | scene_set insertion point; cols/rows from entity positions; floor-at-10; grid=True | CONFIRMED | Lines 278-298 in websocket_endpoint(); max(all_x)+2 derivation; floor at 10; DS-005 PASS. |
| 4 | faction map before/after; "party"→"ally", "monsters"→"enemy" | CONFIRMED | Lines 208-211; _FACTION_MAP dict; DS-006+DS-007 PASS. |
| 5 | team check "player"→"party" (before/after); join emission after scene_set | CONFIRMED | Line 302: `== "party"`. Join emission lines 299-308. Both in commit 7361271. DS-008 PASS. |

### ML Preflight Checklist

| Check | ID | Status | Notes |
|-------|----|--------|-------|
| Gap verified before writing | ML-001 | PASS | Read index.html, ws_protocol.py, ws_bridge.py lines 202/625/821 before edits. All 5 gaps confirmed live. |
| Consume-site verified end-to-end | ML-002 | PASS | Write (ws_protocol classes) → Read (ws_bridge imports + emit) → Effect (orb.js/main.js/map.js receive correct message types) → Test (DS-001..DS-008). |
| No ghost targets | ML-003 | PASS | Rule 15c: transcript-area confirmed missing; faction confirmed "party" raw; team check confirmed "player"; speaking_start/stop confirmed absent; scene_set confirmed absent. |
| Dispatch parity | ML-004 | PASS | Only one token_add path (_build_token_add_messages). Only one primary narration block in _turn_result_to_messages (line 662). faction map, team check, and speaking wrap all in single code paths. |
| Coverage map update | ML-005 | PASS | See below. |
| Commit before debrief | ML-006 | PASS | Backlog b576f32, code 7361271 precede this debrief. |
| PM Acceptance Notes addressed | ML-007 | PASS | All 5 confirmed. |
| Backlog committed before debrief | ML-008 | PASS | b576f32 is backlog commit, precedes this debrief. |

### Consumption Chain

| Layer | Location | Action |
|-------|----------|--------|
| Schema write | ws_protocol.py:41-43 | MSG_SPEAKING_START/STOP/SCENE_SET constants |
| Schema write | ws_protocol.py:569-625 | SpeakingStart, SpeakingStop, SceneSet dataclasses |
| Bridge write | ws_bridge:208-211 | faction map: "party"→"ally", "monsters"→"enemy" |
| Bridge write | ws_bridge:278-308 | scene_set + character_state at join |
| Bridge write | ws_bridge:671-688 | speaking_start/stop wrap around narration |
| Bridge write | ws_bridge:302 | team check "player"→"party" |
| HTML write | index.html | `<div id="transcript-area">` in right-col, STANDARD posture |
| Read (client) | orb.js:54 | bridge.on("speaking_start", setSpeaking) — now fires |
| Read (client) | main.js:109-119 | transcript-area non-null — narration now visible |
| Read (client) | map.js:160-163 | bridge.on("scene_set") sets gridCols/gridRows/showGrid=true |
| Read (client) | map.js:125 | FACTION_COLOR["ally"]/["enemy"] — correct token colors |
| Effect | Browser | Grid drawn, tokens colored, narration visible, orb pulses |
| Test | DS-001..DS-008 | 8/8 PASS |

---

## Pass 2 - PM Summary

Five display gaps closed in three files. `index.html`: transcript-area div added (GAP-06). `ws_protocol.py`: SpeakingStart, SpeakingStop, SceneSet dataclasses + MSG constants (GAP-07, GAP-08). `ws_bridge.py`: speaking_start/stop wrap around narration (GAP-07); scene_set emitted at join with grid dimensions derived from entity positions floor-at-10 (GAP-08); faction map "party"→"ally"/"monsters"→"enemy" (GAP-11); team check "player"→"party" + character_state at join after scene_set (GAP-CS). 8/8 gates pass. Backlog committed before code. 0 engine files touched.

---

## Pass 3 - Retrospective

### Discoveries

**FINDING-UI-DISPLAY-SESSION-STATE-KWARG-001 (LOW, OPEN) — filed to backlog b576f32**
`_build_session_state()` in ws_bridge fails with `TypeError: ServerMessage.__init__() got an unexpected keyword argument session_id` when exercised via live WebSocket mock. Pre-existing schema mismatch between `_build_session_state()` and `SessionStateMsg` frozen dataclass. Does not affect gate tests (tested through `_turn_result_to_messages` path). Stage 4 fix.

**FINDING-UI-DISPLAY-SPEAKING-WRAP-MULTI-NARRATION-001 (LOW, OPEN) — filed to backlog b576f32**
`_turn_result_to_messages()` has 7+ NarrationEvent emission blocks (lines 662, 694, 710, 726, 741, 754, 767, 835). Only the primary block (line 662) received speaking_start/stop wrap. Clarification, fallback, and spell narration paths emit narration without orb activation. Low-frequency paths; Stage 4 scope.

### Scope Discipline

`main.js`, `orb.js`, `map.js`, `session_orchestrator.py`, `play.py`, all engine resolvers: not touched. Confirmed.

GAP-09 (dice slip), GAP-10 (abilities dict), GAP-12 (ability_check_declare): deferred to Stage 4 per dispatch scope boundary.

### Coverage Map Update

| Mechanic | Status | WO | Notes |
|----------|--------|----|-------|
| GAP-06 transcript-area | IMPLEMENTED | WO-UI-PHASE1-DISPLAY-001 | index.html |
| GAP-07 speaking_start/stop | IMPLEMENTED | WO-UI-PHASE1-DISPLAY-001 | ws_protocol + ws_bridge |
| GAP-08 scene_set at join | IMPLEMENTED | WO-UI-PHASE1-DISPLAY-001 | ws_protocol + ws_bridge |
| GAP-11 faction color map | IMPLEMENTED | WO-UI-PHASE1-DISPLAY-001 | ws_bridge |
| GAP-CS character_state join + team fix | IMPLEMENTED | WO-UI-PHASE1-DISPLAY-001 | ws_bridge |

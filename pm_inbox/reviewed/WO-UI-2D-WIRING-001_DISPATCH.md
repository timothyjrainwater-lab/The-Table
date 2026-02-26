# WO-UI-2D-WIRING-001 — UI 2D Live Wiring + Polish

**WO-ID:** WO-UI-2D-WIRING-001
**Lifecycle:** DRAFT
**Track:** UI
**Priority:** HIGH — Playtest blocker
**Gate:** UI-2D-WIRING 10/10
**Operator:** Thunder
**Builder:** Anvil (Opus 4.6 BS Buddy — interactive session, Thunder co-directing polish)

---

## Context

The 2D client (`client2d/`) has full token, HP bar, character sheet, and combat state handlers already implemented and waiting. The server (`aidm/server/ws_bridge.py`) emits none of the messages those handlers expect. The two sides have never been connected.

**Current disconnect — client expects, server never sends:**

| Client handler | File | Server sends? |
|---|---|---|
| `token_add` | `map.js:175` | No |
| `token_update` | `map.js:190` | No |
| `token_move` | `map.js:181` | No |
| `token_remove` | `map.js:186` | No |
| `character_state` | `sheet.js:89` | No |
| `combat_start` | `main.js:98` | No |
| `combat_end` | `main.js:102` | No |

**What the server currently sends from engine events:**
- `state_update` (generic, `_turn_result_to_messages` in `ws_bridge.py:443`) — routed to `console.log` stub in `main.js:125`. Discarded.
- `narration` — handled correctly.

**Engine events that must drive the new messages:**
- `hp_changed` (`box_events.py:250`) — payload fields: `entity_id`, `hp_before`/`old_hp`, `hp_after`/`new_hp` (use `.effective_hp_before()` / `.effective_hp_after()` helpers)
- `entity_defeated` (`box_events.py:251`) — payload fields: `entity_id`, `hp_final`
- `combat_started` (`combat_controller.py:179`) — event_type string: `"combat_started"`
- `combat_ended` — check `combat_controller.py` for the event_type string

**Token position:** The engine stores position in `EF.POSITION = "position"` on entity dicts. The map client expects `col` and `row` integers for grid placement. The position field format must be confirmed from `WorldState` before wiring `token_add`.

**HP bar on map tokens:** Already fully implemented in `map.js:136-143`. Reads `t.hp` and `t.hp_max`. Just needs `token_update` with `{id, hp}` to arrive.

**Character sheet:** `sheet.js` renders on `character_state` messages. Sheet has HP, AC, ability scores. The server must emit `character_state` after each turn for the active PC. Shape: `{msg_type: "character_state", name, class, level, hp, hp_max, ac, abilities: {str, dex, con, int, wis, cha}}`.

---

## Task

Wire the server → client event pipeline so that engine events produce live UI updates during a play session.

### Scope

**Server-side (`aidm/server/ws_bridge.py`):**

1. In `_turn_result_to_messages()`, replace the generic `state_update` loop with specific routing:
   - `hp_changed` → emit `token_update {msg_type: "token_update", id: entity_id, hp: hp_after}`
   - `entity_defeated` → emit `token_remove {msg_type: "token_remove", id: entity_id}`
   - `combat_started` → emit `{msg_type: "combat_start"}`
   - `combat_ended` → emit `{msg_type: "combat_end"}`
   - All other event types: keep the existing `state_update` passthrough (don't delete it — other consumers may use it)

2. After processing turn results, emit `character_state` for the active PC entity. Pull from `WorldState` via `FrozenWorldStateView`. Shape defined above. If the orchestrator doesn't expose enough state to build this, add a helper method — do NOT breach the `FrozenWorldStateView` boundary (BL-020).

3. On session join / `combat_started`, emit `token_add` for each entity currently in the world. Shape: `{msg_type: "token_add", id: entity_id, col: int, row: int, name: str, faction: str, hp: int, hp_max: int}`. Faction maps from `EF.TEAM`.

**Client-side (`client2d/main.js`):**

4. Remove the wildcard stub comment `// Stub: log all other message types` and replace with a minimal handler that only logs truly unknown types (after the known types list is updated to include the new ones). The stub handler itself can stay for unknown types — just update the `handled` array.

**Polish (interactive with Thunder):**
5. Stance image on the orb speaker panel — Thunder to direct which images map to which states during the session. Builder should expose a simple config object or switch in `orb.js` that Thunder can point at assets.
6. Any additional visual rough edges Thunder identifies during the session.

---

## Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Emit specific typed messages or keep generic `state_update`? | **Specific typed messages** | Client handlers already exist for the specific types. Generic passthrough is a dead end. |
| 2 | Keep `state_update` passthrough for other event types? | **Yes, keep it** | Other consumers (debugging, future handlers) may use it. Don't remove. |
| 3 | `character_state` — emit after every turn or only on HP/stat change? | **After every turn** | Simplest. Sheet re-renders are cheap. Avoids missed updates. |
| 4 | `token_add` — emit on session join only, or also on `combat_started`? | **Both** | Session join populates the map. `combat_started` catches late-joining browsers. |
| 5 | Use `FrozenWorldStateView` for character_state data? | **Yes, mandatory** | BL-020. No direct WorldState writes outside the engine. |
| 6 | Polish items (stance, visual) handled interactively with Thunder? | **Yes** | Not spec-able without Thunder's real-time direction. Builder exposes config, Thunder directs. |
| 7 | New gate tests — server-side unit tests or integration? | **Server-side unit tests** | Test `_turn_result_to_messages()` with mock TurnResult containing specific engine events. No browser required. |

---

## Contract Spec

### `ws_bridge.py` — `_turn_result_to_messages()` modification

```python
# Replace the existing generic state_update loop:
events = getattr(result, "events", ())
for event_dict in events:
    if isinstance(event_dict, dict):
        event_type = event_dict.get("event_type", "")
        payload = event_dict.get("payload", {})
        entity_id = event_dict.get("entity_id") or payload.get("entity_id")

        if event_type == "hp_changed":
            hp_after = payload.get("hp_after") or payload.get("new_hp")
            if entity_id is not None and hp_after is not None:
                messages.append(_make_raw_msg("token_update", {
                    "id": entity_id, "hp": hp_after
                }, in_reply_to))

        elif event_type == "entity_defeated":
            if entity_id:
                messages.append(_make_raw_msg("token_remove", {
                    "id": entity_id
                }, in_reply_to))

        elif event_type == "combat_started":
            messages.append(_make_raw_msg("combat_start", {}, in_reply_to))

        elif event_type == "combat_ended":
            messages.append(_make_raw_msg("combat_end", {}, in_reply_to))

        else:
            # Keep passthrough for unhandled event types
            messages.append(StateUpdate(
                msg_type=MSG_STATE_UPDATE,
                msg_id=_make_msg_id(),
                in_reply_to=in_reply_to,
                timestamp=_now(),
                update_type=event_type,
                entity_id=entity_id,
                delta=tuple(sorted(event_dict.items())),
            ))
```

### New helper in `ws_bridge.py`

```python
def _make_raw_msg(msg_type: str, data: dict, in_reply_to: str) -> ServerMessage:
    """Emit a lightweight typed message to the client."""
    # Use existing ServerMessage or a plain dict serialised by _send_message
    # Confirm whether ServerMessage supports arbitrary msg_type or needs a new dataclass
    # If ServerMessage is strict, use a TypedDict / plain dict passthrough
```

### `character_state` emission (after turn result processing)

```python
# After the events loop, emit character_state for active PC
active_entity = _get_active_pc_view(result, world_state_view)
if active_entity:
    messages.append(_make_raw_msg("character_state", {
        "name": active_entity.get("name", "Adventurer"),
        "class": _infer_class(active_entity),
        "level": _infer_level(active_entity),
        "hp": active_entity.get("hp_current"),
        "hp_max": active_entity.get("hp_max"),
        "ac": active_entity.get("ac"),
        "abilities": _extract_abilities(active_entity),
    }, in_reply_to))
```

### `token_add` emission on session join

```python
# In _build_session_state() or new _emit_initial_tokens() helper
# Called from _get_or_create_session() after session is created
# Emit one token_add per entity in world
for entity_id, entity in world_state.entities.items():
    position = entity.get("position", {})
    col = position.get("col") or position.get("x")  # confirm field name
    row = position.get("row") or position.get("y")  # confirm field name
    messages.append(_make_raw_msg("token_add", {
        "id": entity_id,
        "col": col,
        "row": row,
        "name": entity.get("name", entity_id),
        "faction": entity.get("team", "neutral"),
        "hp": entity.get("hp_current", 0),
        "hp_max": entity.get("hp_max", 1),
    }, in_reply_to))
```

---

## Implementation Plan

### Step 1 — Audit `WorldState` entity structure
- Read `aidm/core/state.py` — confirm `WorldState.entities` dict structure
- Confirm `EF.POSITION` field format: does it have `col`/`row`, `x`/`y`, or `grid_x`/`grid_y`?
- Confirm entity name field (plain `"name"` key vs EF constant)
- Confirm `EF.TEAM` values (what strings does faction map to?)
- **Do not guess. Read the source first.**

### Step 2 — Audit `ServerMessage` dataclasses
- Read `aidm/schemas/ws_protocol.py`
- Determine if existing `ServerMessage` subclasses can carry arbitrary `msg_type` or if new ones are needed
- If `CombatEvent` already exists (imported in `ws_bridge.py:37`), use it for `combat_start`/`combat_end`

### Step 3 — Implement `_make_raw_msg` helper
- File: `aidm/server/ws_bridge.py`
- Minimal. No new schema classes unless `ws_protocol.py` requires it.

### Step 4 — Replace generic `state_update` loop
- File: `aidm/server/ws_bridge.py`, function `_turn_result_to_messages()` (~line 469)
- Wire `hp_changed` → `token_update`, `entity_defeated` → `token_remove`, `combat_started` → `combat_start`, `combat_ended` → `combat_end`
- Keep `state_update` passthrough for all other types

### Step 5 — Add `character_state` emission
- After the events loop in `_turn_result_to_messages()`
- Must use `FrozenWorldStateView` — confirm how result exposes world state
- If not accessible from `TurnResult`, check `SessionOrchestrator` for a view accessor

### Step 6 — Add `token_add` on session join
- Locate where sessions are initialised (`_get_or_create_session()` or `_build_session_state()`)
- Emit `token_add` for all entities with valid positions
- Entities with no position: skip silently (not all entities are on the map)

### Step 7 — Update `main.js` stub
- Update the `handled` array in the wildcard handler to include: `token_add`, `token_update`, `token_remove`, `token_move`, `character_state`, `combat_start`, `combat_end`
- Stub continues to log truly unknown types — this is intentional for debugging

### Step 8 — Write gate tests
- File: `tests/test_ui_2d_wiring.py` (new)
- Gate: `UI-2D-WIRING`
- 10 tests minimum:
  - `hp_changed` event → `token_update` emitted with correct `id` and `hp`
  - `entity_defeated` event → `token_remove` emitted with correct `id`
  - `combat_started` event → `combat_start` emitted
  - `combat_ended` event → `combat_end` emitted
  - Unknown event type → `state_update` passthrough (not swallowed)
  - Multiple events in one turn → all correctly routed
  - `hp_changed` with `new_hp` (legacy field) → `token_update` still emitted
  - No events → narration fallback still fires
  - `character_state` emitted after turn with active PC in world state
  - `token_add` emitted on session join for entity with valid position

### Step 9 — Polish pass (interactive with Thunder)
- Expose stance config in `orb.js` — simple object mapping stance strings to image paths
- Thunder directs which assets map to which states
- Other visual rough edges Thunder identifies during the session

---

## Files to Modify

| File | Change |
|---|---|
| `aidm/server/ws_bridge.py` | Replace generic state_update loop; add token_add on join; add character_state emission |
| `client2d/main.js` | Update stub handled array |
| `client2d/orb.js` | Expose stance config object for Thunder-directed polish |
| `tests/test_ui_2d_wiring.py` | New gate test file (10 tests, Gate UI-2D-WIRING) |

---

## Required Reading

1. `aidm/server/ws_bridge.py` — full file, especially `_turn_result_to_messages()` and `_build_session_state()`
2. `aidm/schemas/ws_protocol.py` — `ServerMessage` subclasses, existing `CombatEvent`
3. `aidm/schemas/box_events.py` — `HPChangedPayload`, `EntityDefeatedPayload` field names and helper methods
4. `aidm/core/state.py` — `WorldState.entities` structure, `FrozenWorldStateView`
5. `client2d/map.js` — `token_add`, `token_update`, `token_remove`, `token_move` handler shapes (lines 175-192)
6. `client2d/sheet.js` — `character_state` message shape expected (line 89)
7. `client2d/main.js` — existing `combat_start`/`combat_end` handlers, wildcard stub

---

## Integration Seams

**BL-020 (HARD):** All reads of world state outside engine resolution must go through `FrozenWorldStateView`. No direct `WorldState` access in the bridge.

**Event constructor signature (HARD):** `Event(event_id=, event_type=, payload=)`. NOT `id=`, `type=`, `data=`.

**`HPChangedPayload` dual fields:** The payload may use `hp_before`/`hp_after` OR `old_hp`/`new_hp`. Always use `.effective_hp_after()` helper or check both fields. Do not assume `hp_after` exists.

**`EF.CLASS_FEATURES` does not exist.** If inferring class/level for `character_state`, use `entity.get(EF.CLASS_LEVELS, {})`.

**`CombatEvent` already imported** in `ws_bridge.py` (line 37). Use it before creating new dataclasses.

**Client `token_add` shape (from `map.js:176`):**
```js
tokens.set(d.id, { col: d.col, row: d.row, name: d.name,
                   faction: d.faction, hp: d.hp, hp_max: d.hp_max });
```
These field names are the contract. Server must match exactly.

---

## Assumptions to Validate

Before writing code, confirm by reading source:

1. `WorldState.entities` — is it a plain dict keyed by entity_id? What are the field names for position (col/row vs x/y)?
2. `FrozenWorldStateView` — does it expose an `entities` accessor or similar? Or does the builder need to pass world state separately?
3. Does `TurnResult` from `SessionOrchestrator` carry a world state reference, or only events?
4. `EF.TEAM` — what values does it hold? Does it map directly to `faction` as the client expects, or does it need translation?
5. `combat_ended` — confirm the exact `event_type` string from `combat_controller.py`.
6. `ServerMessage` — is it a Protocol/dataclass? Can `_make_raw_msg` return a plain dict that `_send_message` will serialise, or does it require a typed instance?

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/ -x -q 2>&1 | tail -5
```

Both must pass before any changes.

---

## Verification

```bash
python -m pytest tests/test_ui_2d_wiring.py -v
```

Expected: 10/10 pass. No regressions in existing gates.

Full suite:
```bash
python -m pytest tests/ -q 2>&1 | tail -5
```

Expected: 7,221+ passing (7,211 baseline + 10 new), 23 pre-existing failures unchanged.

---

## Scope Boundaries

**In scope:**
- `ws_bridge.py` event routing
- `token_add` on session join
- `character_state` after each turn
- `main.js` stub update
- `orb.js` stance config exposure
- Gate tests for the new routing logic

**Out of scope:**
- `token_move` (movement enforcement is a future milestone — entities don't move during combat turns yet)
- TTS / audio pipeline
- Oracle / record log
- Any engine resolver changes
- New UI panels or layout changes
- Playwright visual regression

---

## Dependencies

- WO-ENGINE-WILDSHAPE-HP-001 and WO-ENGINE-WILDSHAPE-DURATION-001 should be accepted first (clean engine baseline before wiring UI to it)
- No other blockers

---

## Delivery Footer

Builder delivers:
- [ ] `aidm/server/ws_bridge.py` — event routing complete
- [ ] `client2d/main.js` — stub handled array updated
- [ ] `client2d/orb.js` — stance config object exposed
- [ ] `tests/test_ui_2d_wiring.py` — 10 gate tests, all passing
- [ ] Gate `UI-2D-WIRING 10/10` confirmed
- [ ] No regressions (7,211 baseline unchanged)
- [ ] Debrief filed to `pm_inbox/reviewed/DEBRIEF_WO-UI-2D-WIRING-001.md`

---

## Debrief Required

File to: `pm_inbox/reviewed/DEBRIEF_WO-UI-2D-WIRING-001.md`

**Pass 1 — Context dump:**
- Per-file breakdown of every change made
- Confirmation of `WorldState.entities` position field format (what was the actual field name?)
- Confirmation of `FrozenWorldStateView` accessor used
- Confirmation of `EF.TEAM` values and any translation applied
- Any assumptions that were wrong and how they were resolved
- Open findings table (ID / severity / description) for anything discovered but out of scope

**Pass 2 — PM summary (≤100 words):**
Summary of what was wired, what was deferred, gate result.

**Pass 3 — Retrospective:**
- Drift caught (anything the WO spec missed or got wrong)
- Patterns worth noting
- Recommendations for next WO

**Radar:** Any new findings discovered during implementation must be included. Missing debrief or missing Radar → REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

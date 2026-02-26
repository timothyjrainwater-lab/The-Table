# WO-SEC-REDACT-001 — Role-Aware WS Field Stripping

**Issued:** 2026-02-25
**Lifecycle:** DISPATCH-READY
**Track:** Security / Engine
**Priority:** CRITICAL — passive GM screen handover on every session join; live right now
**WO type:** FEATURE (structural — replace "send everything" defaults with explicit allowlists)
**Seat:** Builder

**Closes:** FINDING-WS-HP-DISCLOSURE-001 (CRITICAL), FINDING-WS-EVENT-PASSTHROUGH-001 (HIGH)
**Context:** ADVERSARIAL_AUDIT_SYNTHESIS_001 — Inverted Default 1 (system defaults to LEAK)

---

## 0. Section 0 — Doctrine Hard Stops

Engine/server WO. UI doctrine does not apply except for WS security invariants (locked 2026-02-25):

- **No HTML sinks.** Not applicable to this WO (server-side only).
- **No arbitrary URLs from WS.** Not applicable to this WO.
- **No client verbs without server capability.** Not applicable to this WO.
- **No stored HTML.** Not applicable to this WO.
- **Event constructor signature:** `Event(event_id=..., event_type=..., payload=...)` — not applicable (no events emitted by this WO, but if any are added: use correct signature).

**Hard stops for this WO:**
- Builder must NOT modify `WorldState`, entity schemas, or game logic. Only `ws_bridge.py`.
- Builder must NOT add role logic to the engine. Role awareness lives at the WS bridge layer only.
- The passthrough `else` branch in `_turn_result_to_messages()` must be **deleted**, not patched. No "sanitize before passthrough" — the branch is gone.
- Every outbound `token_add` message must go through the role-based field filter. No bypass path.

---

## 1. Target Lock

Two confirmed "send everything" mechanisms in `ws_bridge.py`:

**GAP-WS-003:** `_build_token_add_messages()` sends `hp` + `hp_max` for ALL entities (including monsters) to every client on join/reconnect. No role check. Player receives full GM screen passively before taking any action.

**GAP-WS-004:** `_turn_result_to_messages()` has an `else` branch that converts any unhandled event type to `StateUpdate(delta=tuple(sorted(event_dict.items())))` — the entire raw internal engine event dict. Every new event type added to the engine broadcasts at full fidelity until someone writes an explicit handler.

**Fix:**
1. Add role awareness to the WS connection — player vs. DM.
2. Strip monster `hp`/`hp_max` from `token_add` for player connections.
3. Delete the passthrough `else` branch entirely. Replace with a logged drop.

---

## 2. Binary Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Where role is stored | `CombatSession` or connection state in `ws_bridge.py` | Role must survive reconnect; attach to session, not socket |
| Initial role assignment | First connection is DM; subsequent connections are players | Simplest model that works; can be refined later |
| Monster HP visibility for DM | Full HP visible | DM has GM screen |
| Monster HP visibility for player | Token visible (position, faction, name) but NO hp/hp_max | GM screen is the DM's privilege |
| Player-visible token fields | `entity_id`, `name`, `faction`, `position`, `token_type` | Minimum needed to display the token |
| DM-visible token fields | All fields | Full state |
| Passthrough branch | DELETE entirely — unknown events are logged and dropped | No sanitize-and-forward; "send nothing" is the correct default |
| Log level for dropped events | WARNING — unknown event type is a contract gap, not a debug note | Visible in server logs; Anvil/Slate can triage |

---

## 3. Contract Spec

### 3.1 Role model

Add to connection state in `ws_bridge.py`:

```python
class ConnectionRole(Enum):
    DM = "dm"
    PLAYER = "player"
```

On `session_control/join`: first connection to a session → `ConnectionRole.DM`. Subsequent connections → `ConnectionRole.PLAYER`. Store on the handler instance: `self._role: ConnectionRole`.

### 3.2 `_build_token_add_messages()` — role-aware field filter

Current behavior: iterates all positioned entities, sends full entity dict.

New behavior:

```python
def _player_token_fields(entity: Dict) -> Dict:
    """Fields a player connection may see in token_add."""
    allowed = {"entity_id", "name", "faction", "position", "token_type", "is_pc"}
    return {k: v for k, v in entity.items() if k in allowed}

def _dm_token_fields(entity: Dict) -> Dict:
    """DM sees everything."""
    return entity
```

In `_build_token_add_messages()`:
- If `self._role == ConnectionRole.DM`: use `_dm_token_fields(entity)`
- If `self._role == ConnectionRole.PLAYER`: use `_player_token_fields(entity)`

**No other changes to `_build_token_add_messages()` logic.**

### 3.3 `_turn_result_to_messages()` — delete passthrough branch

Current (to be removed):
```python
else:
    # Unknown event type — serialize raw to StateUpdate
    messages.append(StateUpdate(delta=tuple(sorted(event_dict.items()))))
```

Replace with:
```python
else:
    # Unknown event type — log and drop. Do NOT broadcast.
    import logging
    logging.getLogger(__name__).warning(
        "ws_bridge: unhandled event type %r — dropped, not broadcast",
        event_dict.get("event_type", "UNKNOWN")
    )
```

That is the entire change to the passthrough branch. One log line. Nothing broadcast.

### 3.4 Role-aware hp_changed handler

The handled `hp_changed` path in `_turn_result_to_messages()` currently emits `token_update` with `hp_after`. This is correct for DM. For players, strip hp from the token_update payload:

```python
def _token_update_payload(entity_id: str, hp_after: int, role: ConnectionRole) -> Dict:
    base = {"entity_id": entity_id}
    if role == ConnectionRole.DM:
        base["hp"] = hp_after
    return base
```

Apply this to the `hp_changed` event handler in `_turn_result_to_messages()`.

### 3.5 Events emitted

None. This WO emits no engine events. It is a filtering layer only.

---

## 4. Implementation Plan

1. **`aidm/server/ws_bridge.py`** only. No other files.
   - Add `ConnectionRole` enum (or import from a new `aidm/server/roles.py` if builder prefers — either is fine).
   - Add role assignment in `session_control/join` handler.
   - Add `_player_token_fields()` and `_dm_token_fields()` helpers.
   - Update `_build_token_add_messages()` to use role-aware field filter.
   - Update `hp_changed` handler to strip hp for player connections.
   - Delete passthrough `else` branch. Replace with WARNING log.

2. **`tests/test_sec_redact_001.py`** — NEW FILE: ≥10 tests.

---

## 5. Gate Tests (≥10 required)

```
SR-001: DM join — token_add includes hp + hp_max for monster entity
SR-002: Player join — token_add for monster entity has NO hp, NO hp_max
SR-003: Player join — token_add for PC entity includes all standard fields
SR-004: Player join — token_add for monster includes entity_id, name, faction, position
SR-005: DM turn result — hp_changed event produces token_update with hp field
SR-006: Player turn result — hp_changed event produces token_update WITHOUT hp field
SR-007: Unknown event type — NOT broadcast to any client (no StateUpdate with raw delta)
SR-008: Unknown event type — produces WARNING log entry
SR-009: Second connection to same session — assigned PLAYER role
SR-010: First connection to session — assigned DM role
```

---

## 6. Integration Seams

- `aidm/server/ws_bridge.py` — sole file modified
- `aidm/server/ws_protocol.py` — read for message type reference, do not modify
- `aidm/core/state.py` — read for entity dict structure, do not modify

---

## 7. Assumptions to Validate

- Confirm: `_build_token_add_messages()` is the only join-path that sends entity state to clients
- Confirm: `_turn_result_to_messages()` is the only event-to-WS conversion path
- Confirm: `hp_changed` handler location in `_turn_result_to_messages()` (exact line)
- Confirm: `self._role` can be attached to the handler instance without threading issues

---

## 8. Preflight

Before writing code:
- [ ] Read `aidm/server/ws_bridge.py` in full
- [ ] Locate `_build_token_add_messages()` — confirm it's the join path
- [ ] Locate `_turn_result_to_messages()` — identify the `else` passthrough branch
- [ ] Locate `hp_changed` handler within `_turn_result_to_messages()`
- [ ] Confirm no other code path serializes entity state to clients

---

## 9. Debrief Required

File to: `pm_inbox/reviewed/DEBRIEF_WO-SEC-REDACT-001.md`

**Pass 1:**
- `_player_token_fields()` allowed set confirmed
- Passthrough `else` branch deleted (confirm: zero lines remain that serialize raw event dict)
- Role assignment location (line citation)
- `hp_changed` handler updated for player connections
- WARNING log confirmed present

**Pass 2 (≤100 words):** What was implemented, what was discovered.

**Pass 3:** Drift caught, patterns, recommendations.

**Radar (mandatory):**
- SR-001 through SR-010: all pass
- No remaining path that broadcasts raw internal state to player connections
- Passthrough branch: DELETED (not sanitized, not patched)

Missing debrief or missing Radar → REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

# WO-SEC-REDACT-002 — Session State HP Redaction: _build_session_state() Entity Dict Stripping

**Issued:** 2026-02-26
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE / WS Security
**Priority:** HIGH (FINDING-SEC-SESSION-STATE-001 — second HP disclosure path; player receives raw entity dicts with hp_current on session state messages)
**WO type:** BUG (gap found in WO-SEC-REDACT-001 debrief Pass 3)
**Gate:** ENGINE-SEC-REDACT-002 (10 tests)

---

## 1. Target Lock

**What WO-SEC-REDACT-001 closed:**
- `_build_token_add_messages()` — strips hp/hp_max for PLAYER role on join ✓
- `_turn_result_to_messages()` — replaces raw StateUpdate passthrough with allowlist; hp_changed → TokenUpdate with hp stripped for PLAYER ✓

**What remains open (FINDING-SEC-SESSION-STATE-001):**
`_build_session_state()` in `aidm/server/ws_bridge.py` constructs a `SessionStateMsg` whose `entities` field is populated from raw entity dicts — including `hp_current` and any other internal fields. This message is sent to all clients. A PLAYER connection receives full entity state including monster HP via this path regardless of the token_add fix.

**Root cause (debrief Pass 3, confirmed by builder):** `_build_session_state()` was not in scope for WO-SEC-REDACT-001. The token_add path was fixed; the session_state path was not.

**PHB / design principle:** Same as WO-SEC-REDACT-001 — players must not receive monster HP. The session_state message is a second vector for the same information leak.

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | Same role-based stripping approach as WO-SEC-REDACT-001? | Yes — identical pattern. DM receives full entity data; PLAYER receives stripped entity data. Use the existing `ConnectionRole` enum and `_player_token_fields()` / `_dm_token_fields()` helpers already live from WO-SEC-REDACT-001. |
| 2 | Which fields to strip for PLAYER in session_state? | At minimum: `hp_current`, `hp_max`, any internal resolver fields (TEMPORARY_MODIFIERS, ACTIVE_POISONS, ACTIVE_DISEASES, ACTIVE_SPELLS, WILD_SHAPE_ACTIVE, etc.). Use the same field allowlist philosophy as WO-SEC-REDACT-001: define what players CAN see, not what they cannot. |
| 3 | What can PLAYER see in session_state entities? | Public fields: entity_id, name, faction, position (col/row), size, creature_type, conditions (visible ones). NOT: HP, modifiers, internal state. Builder must align this list with what `_player_token_fields()` already exposes. |
| 4 | Does `SessionStateMsg` need a new variant or filtered construction? | Filtered construction — build the entity payload differently per role. No new message type needed. |
| 5 | Where does role come from? | Already live on the bridge from WO-SEC-REDACT-001 — `_assign_role(session_id)` returns `ConnectionRole`. Pass role into `_build_session_state()`. |

---

## 3. Contract Spec

### Modification: `aidm/server/ws_bridge.py` — `_build_session_state()`

Current (inferred from debrief): builds `SessionStateMsg` using raw entity dicts.

Modified: add `role: ConnectionRole` parameter. Filter entity data before inclusion:

```python
def _build_session_state(self, session, in_reply_to: str, role: ConnectionRole) -> SessionStateMsg:
    entities_out = {}
    for entity_id, entity in session.world_state.entities.items():
        if role == ConnectionRole.DM:
            entities_out[entity_id] = _dm_token_fields(entity)
        else:
            entities_out[entity_id] = _player_token_fields(entity)

    return SessionStateMsg(
        in_reply_to=in_reply_to,
        entities=entities_out,
        # ... other existing fields unchanged
    )
```

The `_player_token_fields()` and `_dm_token_fields()` helpers are already implemented from WO-SEC-REDACT-001. This WO reuses them — no new field filtering logic required.

### Caller update

Wherever `_build_session_state()` is called in `ws_bridge.py`, pass `role=self._assign_role(session_id)` (or the already-resolved role for this connection).

---

## 4. Implementation Plan

### Step 1 — Read `_build_session_state()` in full
Builder reads the current implementation. Understand exactly what fields go into `SessionStateMsg.entities` and what other fields the message carries.

### Step 2 — Add `role` parameter and filter entities
Modify `_build_session_state()` to accept role and apply `_player_token_fields()` or `_dm_token_fields()` per entity.

### Step 3 — Update all call sites
Find every call to `_build_session_state()` in ws_bridge.py and pass the role. Likely called in the join handler and possibly on reconnect.

### Step 4 — Tests (`tests/test_engine_sec_redact_002_gate.py`)
Gate: ENGINE-SEC-REDACT-002 — 10 tests

| Test | Description |
|------|-------------|
| SR2-01 | PLAYER connection receives SessionStateMsg: monster entities have no hp_current field |
| SR2-02 | PLAYER connection: monster entities have no hp_max field |
| SR2-03 | PLAYER connection: monster entities have no TEMPORARY_MODIFIERS field |
| SR2-04 | PLAYER connection: entity position, faction, name, creature_type present (not stripped) |
| SR2-05 | DM connection receives SessionStateMsg: monster entities have hp_current present |
| SR2-06 | DM connection: full entity data including internal fields |
| SR2-07 | PC entities: PLAYER sees own hp_current (PC-owned data visible to player — or same strip rule; decide and document) |
| SR2-08 | Session state stripping consistent with token_add stripping (same fields absent in both) |
| SR2-09 | Reconnect path: role re-assigned correctly; session_state rebuilt with correct role stripping |
| SR2-10 | Regression: WO-SEC-REDACT-001 gate (29/29) unchanged |

**Note on SR2-07:** Builder must decide and document whether PC entities are also stripped for PLAYER connections (safe default: yes, strip hp from all non-owned entities) or whether the player sees their own PC's HP (requires ownership tracking — if complex, strip all and revisit).

---

## Integration Seams

**Files touched:**
- `aidm/server/ws_bridge.py` — `_build_session_state()` signature + body (~10 lines), call site updates

**Files NOT touched:**
- `aidm/schemas/ws_protocol.py` — no new message types
- Helper functions `_player_token_fields()` / `_dm_token_fields()` — already live, reused as-is

**Event constructor signature (mandatory):**
```python
Event(event_id=<int>, event_type=<str>, payload=<dict>, timestamp=<float>, citations=[])
```

**ConnectionRole pattern (already live):**
```python
from aidm.server.ws_bridge import ConnectionRole
role == ConnectionRole.DM
role == ConnectionRole.PLAYER
```

---

## Assumptions to Validate

1. `_player_token_fields()` and `_dm_token_fields()` are already exported and importable — confirmed from WO-SEC-REDACT-001 debrief
2. `SessionStateMsg.entities` is a dict keyed by entity_id — confirm from ws_protocol.py
3. `_build_session_state()` is called in the join handler where `session_id` / `role` is already known — confirm call site before modifying signature
4. Role assignment (`_assign_role()`) is already live — confirmed from WO-SEC-REDACT-001

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_sec_redact_001_gate.py -x -q
```

After implementation:
```bash
python -m pytest tests/test_engine_sec_redact_002_gate.py -v
python -m pytest tests/test_sec_redact_001_gate.py -x -q
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```

WO-SEC-REDACT-001 29/29 must remain clean.

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/server/ws_bridge.py` — `_build_session_state()` role-filtered + call site updates
- [ ] `tests/test_engine_sec_redact_002_gate.py` — 10/10

**Gate:** ENGINE-SEC-REDACT-002 10/10
**Regression bar:** WO-SEC-REDACT-001 gate 29/29 unchanged. No new failures.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-SEC-REDACT-002.md` on completion.

Three-pass format. Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

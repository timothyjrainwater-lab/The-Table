# Instruction Packet: WebSocket Bridge Agent

**Work Order:** WO-WEBSOCKET-BRIDGE-001 (Browser ↔ Server Communication Layer)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 2 (Blocks all browser-side UI, but independent of World Compiler)
**Deliverable Type:** Code implementation + tests
**Parallelization:** Fully independent — runs in parallel with all World Compiler WOs

---

## READ FIRST

The product is a browser-based tabletop RPG. The engine runs server-side (Python). The UI runs client-side (Three.js + Pixi.js). They communicate over WebSocket.

This WO builds the server-side WebSocket bridge using Starlette + uvicorn. It defines the message protocol, handles connection lifecycle, and bridges between the SessionOrchestrator (server) and the browser client.

**Existing infrastructure:**
- `aidm/core/session_orchestrator.py` — Full turn cycle: STT → Intent → Box → Lens → Spark → TTS
- `aidm/interaction/play_controller.py` — Single-turn integration with fallbacks
- `aidm/schemas/campaign.py` — Campaign + session schemas
- TTS adapters (Kokoro, Chatterbox) — Audio output as PCM/WAV bytes
- STT adapter (Whisper) — Audio input → text

---

## YOUR TASK

### Deliverable 1: Message Protocol Schema

**File:** `aidm/schemas/ws_protocol.py` (NEW)

Define the WebSocket message protocol as frozen dataclasses:

```python
# --- Client → Server Messages ---

@dataclass(frozen=True)
class ClientMessage:
    """Base for all client-to-server messages."""
    msg_type: str                   # Discriminator field
    msg_id: str                     # Client-generated UUID for correlation
    timestamp: float                # Client timestamp (informational only)

@dataclass(frozen=True)
class PlayerUtterance(ClientMessage):
    """Player speaks or types a command."""
    text: Optional[str] = None      # Text input (typed)
    audio_base64: Optional[str] = None  # Audio input (spoken), base64-encoded
    # msg_type = "player_utterance"

@dataclass(frozen=True)
class PlayerAction(ClientMessage):
    """Player clicks a UI element (ability, item, map cell)."""
    action_type: str                # "use_ability", "move_token", "open_sheet", etc.
    payload: dict                   # Action-specific data
    # msg_type = "player_action"

@dataclass(frozen=True)
class SessionControl(ClientMessage):
    """Session lifecycle control."""
    command: str                    # "join", "leave", "pause", "resume"
    session_id: Optional[str] = None
    # msg_type = "session_control"

# --- Server → Client Messages ---

@dataclass(frozen=True)
class ServerMessage:
    """Base for all server-to-client messages."""
    msg_type: str
    msg_id: str                     # Server-generated UUID
    in_reply_to: Optional[str] = None  # Client msg_id this responds to
    timestamp: float = 0.0

@dataclass(frozen=True)
class NarrationEvent(ServerMessage):
    """DM narration text."""
    text: str
    audio_base64: Optional[str] = None  # TTS audio, base64-encoded
    voice_persona: Optional[str] = None
    # msg_type = "narration"

@dataclass(frozen=True)
class StateUpdate(ServerMessage):
    """Game state change."""
    update_type: str                # "hp_change", "position_change", "condition_applied", etc.
    entity_id: Optional[str] = None
    delta: dict                     # State change payload
    # msg_type = "state_update"

@dataclass(frozen=True)
class CombatEvent(ServerMessage):
    """Combat resolution event."""
    event_type: str                 # "attack_result", "damage_dealt", "save_result", etc.
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    result: dict                    # Event-specific result data
    # msg_type = "combat_event"

@dataclass(frozen=True)
class ErrorEvent(ServerMessage):
    """Error notification."""
    error_code: str
    error_message: str
    recoverable: bool = True
    # msg_type = "error"

@dataclass(frozen=True)
class SessionState(ServerMessage):
    """Full session state snapshot (sent on join/reconnect)."""
    session_id: str
    campaign_id: str
    world_id: str
    entities: tuple                 # Current entity states
    combat_active: bool = False
    round_number: int = 0
    # msg_type = "session_state"
```

All must support `to_dict()` / `from_dict()`.

### Deliverable 2: WebSocket Server

**File:** `aidm/server/ws_bridge.py` (NEW)

```python
class WebSocketBridge:
    """Starlette WebSocket handler bridging browser ↔ SessionOrchestrator."""

    def __init__(self, session_orchestrator_factory):
        """
        Args:
            session_orchestrator_factory: Callable that creates a SessionOrchestrator
                for a new session.
        """

    async def websocket_endpoint(self, websocket: WebSocket):
        """Handle a single WebSocket connection lifecycle.

        1. Accept connection
        2. Receive session_control "join" message
        3. Create or resume session
        4. Send full session_state snapshot
        5. Enter message loop:
           - Receive client message
           - Route to appropriate handler
           - Send response(s) back
        6. Handle disconnect (pause session)
        """

    async def _handle_utterance(self, msg: PlayerUtterance, session) -> list[ServerMessage]:
        """Route player utterance through SessionOrchestrator turn cycle."""

    async def _handle_action(self, msg: PlayerAction, session) -> list[ServerMessage]:
        """Route player UI action to appropriate handler."""

    async def _handle_control(self, msg: SessionControl, session) -> list[ServerMessage]:
        """Handle session lifecycle commands."""
```

### Deliverable 3: ASGI Application

**File:** `aidm/server/app.py` (NEW)

```python
from starlette.applications import Starlette
from starlette.routing import WebSocketRoute
from starlette.middleware.cors import CORSMiddleware

def create_app(config: dict = None) -> Starlette:
    """Create the ASGI application with WebSocket route.

    Routes:
        ws://host/ws — WebSocket connection
        GET /health — Health check endpoint
    """
```

### Deliverable 4: Tests

**File:** `tests/test_ws_bridge.py` (NEW)

1. Message schema round-trip (all message types to_dict/from_dict)
2. Message discriminator routing (msg_type → correct handler)
3. Connection lifecycle: connect → join → session_state → disconnect
4. Utterance routing: PlayerUtterance → mock SessionOrchestrator → NarrationEvent response
5. Error handling: malformed message → ErrorEvent
6. Session resume: disconnect + reconnect → session_state with correct state
7. Multiple concurrent connections (different session IDs)
8. Health endpoint returns 200

Use `starlette.testclient.TestClient` with `httpx` for WebSocket testing. If Starlette is not installed, note it in the completion report as a dependency to add.

---

## WHAT EXISTS (DO NOT MODIFY)

| Component | Location | Status |
|-----------|----------|--------|
| SessionOrchestrator | `aidm/core/session_orchestrator.py` | Full turn cycle — bridge calls into this |
| PlayController | `aidm/interaction/play_controller.py` | Single-turn integration |
| TTS adapters | `aidm/immersion/kokoro_tts_adapter.py` | Audio output |
| STT adapter | `aidm/immersion/whisper_adapter.py` | Audio input |
| Campaign schemas | `aidm/schemas/campaign.py` | Session/campaign identity |

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `aidm/core/session_orchestrator.py` | Turn cycle the bridge calls into |
| 1 | `docs/specs/UX_VISION_PHYSICAL_TABLE.md` | What the client will render |
| 2 | `aidm/interaction/play_controller.py` | Single-turn integration pattern |
| 2 | `aidm/schemas/campaign.py` | Session identity schemas |
| 3 | `docs/research/OSS_SHORTLIST.md` Bucket 4 | Starlette recommendation |

## STOP CONDITIONS

- If `starlette` is not installed, note it as a required dependency. Write the code assuming it will be installed. Don't install it yourself.
- If `uvicorn` is not installed, same treatment.
- The bridge does NOT need to handle audio streaming in this WO. Audio is sent as base64-encoded chunks in messages. Streaming optimization is a future WO.

## DELIVERY

- New files: `aidm/schemas/ws_protocol.py`, `aidm/server/__init__.py`, `aidm/server/ws_bridge.py`, `aidm/server/app.py`, `tests/test_ws_bridge.py`
- Completion report: `pm_inbox/AGENT_WO-WEBSOCKET-BRIDGE-001_completion.md`

## RULES

- All protocol dataclasses MUST be frozen
- The bridge is ASYNC (Starlette is ASGI)
- No imports from `aidm/core/` except through the session_orchestrator_factory callback
- The bridge does NOT own session state — it delegates to SessionOrchestrator
- Message format must be JSON-serializable (no binary frames in this WO)
- Follow existing code style

---

END OF INSTRUCTION PACKET

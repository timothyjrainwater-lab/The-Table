"""WebSocket bridge — Starlette WebSocket handler bridging browser ↔ SessionOrchestrator.

Handles connection lifecycle, message routing, and session management.
The bridge does NOT own session state — it delegates to SessionOrchestrator.

Requires: starlette, uvicorn (noted as dependencies; not installed by this module).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from aidm.schemas.entity_fields import EF
from aidm.schemas.ws_protocol import (
    MSG_ERROR,
    MSG_NARRATION,
    MSG_PLAYER_ACTION,
    MSG_PLAYER_UTTERANCE,
    MSG_SESSION_CONTROL,
    MSG_SESSION_STATE,
    MSG_STATE_UPDATE,
    MSG_COMBAT_EVENT,
    MSG_TOKEN_ADD,
    MSG_TOKEN_UPDATE,
    MSG_TOKEN_REMOVE,
    MSG_CHARACTER_STATE,
    ClientMessage,
    ErrorEvent,
    NarrationEvent,
    PlayerAction,
    PlayerUtterance,
    SessionControl,
    SessionStateMsg,
    StateUpdate,
    CombatEvent,
    TokenAdd,
    TokenUpdate,
    TokenRemove,
    CharacterState,
    ServerMessage,
    parse_client_message,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Role model
# ---------------------------------------------------------------------------

class ConnectionRole(Enum):
    """Role assigned to a WebSocket connection for field-stripping purposes."""
    DM = "dm"
    PLAYER = "player"


# ---------------------------------------------------------------------------
# Token field filters (module-level helpers, exported for tests)
# ---------------------------------------------------------------------------

# Fields stripped from raw entity dicts for PLAYER connections on session_state.
# These are the canonical EF key names used in engine entity dicts.
_ENTITY_STRIP_PLAYER = frozenset({
    "hp_current",     # EF.HP_CURRENT
    "hp_max",         # EF.HP_MAX
    "temporary_modifiers",  # EF.TEMPORARY_MODIFIERS — transient buff/debuff state
    "active_poisons",       # EF.ACTIVE_POISONS
    "active_diseases",      # EF.ACTIVE_DISEASES
    "wild_shape_saved_stats",  # EF.WILD_SHAPE_SAVED_STATS — internal stat snapshot
    "original_stats",          # EF.ORIGINAL_STATS — legacy alias for same
})


def _player_entity_fields(entity_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Strip sensitive fields from a raw entity dict for PLAYER connections.

    Removes hp_current, hp_max, and internal resolver state.
    Public fields (name, team, position, conditions, etc.) are passed through.
    """
    return {k: v for k, v in entity_dict.items() if k not in _ENTITY_STRIP_PLAYER}


def _dm_entity_fields(entity_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Return the full raw entity dict unchanged for DM connections."""
    return entity_dict


def _player_token_fields(token_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Return token_dict with hp/hp_max stripped for player connections."""
    return {k: v for k, v in token_dict.items() if k not in ("hp", "hp_max")}


def _dm_token_fields(token_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Return the full token_dict unchanged for DM connections."""
    return token_dict


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _make_msg_id() -> str:
    """Generate a server-side message UUID."""
    return str(uuid.uuid4())


def _now() -> float:
    """Current timestamp as float."""
    return time.time()


class WebSocketBridge:
    """Starlette WebSocket handler bridging browser ↔ SessionOrchestrator.

    Usage:
        bridge = WebSocketBridge(session_orchestrator_factory)
        # Register bridge.websocket_endpoint as a Starlette WebSocketRoute handler
    """

    def __init__(
        self,
        session_orchestrator_factory: Callable[..., Any],
        default_actor_id: str = "pc_fighter",
    ) -> None:
        """
        Args:
            session_orchestrator_factory: Callable that creates a SessionOrchestrator
                for a new session. Called with (session_id: str) -> orchestrator instance.
            default_actor_id: Default actor entity ID when not specified by client.
        """
        self._factory = session_orchestrator_factory
        self._default_actor_id = default_actor_id
        # Active sessions: session_id -> orchestrator instance
        self._sessions: Dict[str, Any] = {}
        # Lock guarding session creation to prevent race conditions
        # (WO-AUDIT-005: concurrent WebSocket connects must not create duplicate sessions)
        self._session_lock = asyncio.Lock()
        # Connection -> session_id mapping (keyed by UUID, not id(websocket))
        self._connections: Dict[str, str] = {}
        # Role tracking: set of session_ids that already have a DM connection
        self._dm_claimed: Dict[str, bool] = {}

    @property
    def sessions(self) -> Dict[str, Any]:
        """Active sessions (read-only access for testing)."""
        return dict(self._sessions)

    # -----------------------------------------------------------------------
    # Role assignment
    # -----------------------------------------------------------------------

    def _assign_role(self, session_id: str) -> ConnectionRole:
        """Assign a connection role for the given session.

        First connection to a session claims DM. All subsequent are PLAYER.
        """
        if session_id not in self._dm_claimed:
            self._dm_claimed[session_id] = True
            return ConnectionRole.DM
        return ConnectionRole.PLAYER

    # -----------------------------------------------------------------------
    # Token message builders
    # -----------------------------------------------------------------------

    def _build_token_add_messages(
        self,
        session: Any,
        in_reply_to: Optional[str],
        role: ConnectionRole = ConnectionRole.DM,
    ) -> List[TokenAdd]:
        """Build TokenAdd messages for all positioned entities in the session.

        DM connections receive hp + hp_max.
        PLAYER connections receive position/name/faction only — hp fields absent.
        Entities without EF.POSITION are skipped.
        """
        messages: List[TokenAdd] = []

        world_state = getattr(session, "world_state", None)
        if world_state is None:
            return messages

        entities: Dict[str, Any] = getattr(world_state, "entities", {})

        for entity_id, entity in entities.items():
            pos = entity.get(EF.POSITION)
            if pos is None:
                continue

            col = pos.get("x", 0)
            row = pos.get("y", 0)
            name = entity.get("name", "")
            faction = entity.get(EF.TEAM, "")

            if role == ConnectionRole.DM:
                hp = entity.get(EF.HP_CURRENT)
                hp_max = entity.get(EF.HP_MAX)
            else:
                hp = None
                hp_max = None

            messages.append(TokenAdd(
                msg_type=MSG_TOKEN_ADD,
                msg_id=_make_msg_id(),
                in_reply_to=in_reply_to,
                timestamp=_now(),
                id=entity_id,
                name=name,
                faction=faction,
                col=col,
                row=row,
                hp=hp,
                hp_max=hp_max,
            ))

        return messages

    # -----------------------------------------------------------------------
    # WebSocket lifecycle
    # -----------------------------------------------------------------------

    async def websocket_endpoint(self, websocket: WebSocket) -> None:
        """Handle a single WebSocket connection lifecycle.

        1. Accept connection
        2. Receive session_control "join" message
        3. Assign role (DM or PLAYER)
        4. Create or resume session
        5. Send session_state snapshot + role-filtered token_add messages
        6. Enter message loop
        7. Handle disconnect
        """
        await websocket.accept()
        conn_id = str(uuid.uuid4())
        session_id: Optional[str] = None

        try:
            # Wait for join message
            join_msg = await self._receive_join(websocket)
            if join_msg is None:
                return

            session_id = join_msg.session_id or str(uuid.uuid4())
            self._connections[conn_id] = session_id

            # Assign role before any state is sent
            role = self._assign_role(session_id)

            # Create or resume session
            session = await self._get_or_create_session(session_id)

            # Send session state snapshot
            snapshot = self._build_session_state(session_id, session, join_msg.msg_id, role=role)
            await self._send_message(websocket, snapshot)

            # Send role-filtered token_add messages
            for token_msg in self._build_token_add_messages(session, join_msg.msg_id, role):
                await self._send_message(websocket, token_msg)

            # Message loop
            await self._message_loop(websocket, session, session_id, role)

        except WebSocketDisconnect:
            logger.info("Client disconnected (conn=%s, session=%s)", conn_id, session_id)
        except Exception:
            logger.exception("Unexpected error in WebSocket handler (conn=%s)", conn_id)
            try:
                error = ErrorEvent(
                    msg_type=MSG_ERROR,
                    msg_id=_make_msg_id(),
                    timestamp=_now(),
                    error_code="INTERNAL_ERROR",
                    error_message="An unexpected server error occurred.",
                    recoverable=False,
                )
                await self._send_message(websocket, error)
            except Exception:
                pass
        finally:
            self._connections.pop(conn_id, None)
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.close()
                except Exception:
                    pass

    async def _receive_join(self, websocket: WebSocket) -> Optional[SessionControl]:
        """Wait for the initial session_control 'join' message.

        Returns None and sends an error if the first message is not a valid join.
        """
        try:
            raw = await websocket.receive_text()
            data = json.loads(raw)
        except (json.JSONDecodeError, Exception) as exc:
            error = ErrorEvent(
                msg_type=MSG_ERROR,
                msg_id=_make_msg_id(),
                timestamp=_now(),
                error_code="INVALID_JOIN",
                error_message=f"First message must be valid JSON: {exc}",
                recoverable=False,
            )
            await self._send_message(websocket, error)
            await websocket.close(code=1008)
            return None

        msg_type = data.get("msg_type")
        command = data.get("command")

        if msg_type != MSG_SESSION_CONTROL or command != "join":
            error = ErrorEvent(
                msg_type=MSG_ERROR,
                msg_id=_make_msg_id(),
                in_reply_to=data.get("msg_id"),
                timestamp=_now(),
                error_code="EXPECTED_JOIN",
                error_message="First message must be session_control with command 'join'.",
                recoverable=False,
            )
            await self._send_message(websocket, error)
            await websocket.close(code=1008)
            return None

        return SessionControl.from_dict(data)

    async def _get_or_create_session(self, session_id: str) -> Any:
        """Get existing session or create a new one via factory.

        Uses async lock to prevent race conditions when concurrent
        WebSocket connections attempt to create the same session.
        (WO-AUDIT-005)
        """
        async with self._session_lock:
            if session_id not in self._sessions:
                session = self._factory(session_id)
                self._sessions[session_id] = session
            return self._sessions[session_id]

    def _build_session_state(
        self,
        session_id: str,
        session: Any,
        in_reply_to: Optional[str] = None,
        role: ConnectionRole = ConnectionRole.PLAYER,
    ) -> SessionStateMsg:
        """Build a SessionStateMsg from the current session state.

        Role-aware: DM connections receive full entity data; PLAYER connections
        receive hp-stripped entity data (hp_current / hp_max absent).
        """
        entities: tuple = ()
        combat_active = False
        round_number = 0
        campaign_id = ""
        world_id = ""

        if hasattr(session, "world_state"):
            ws = session.world_state
            if hasattr(ws, "entities"):
                filter_fn = _dm_entity_fields if role == ConnectionRole.DM else _player_entity_fields
                entities = tuple(filter_fn(e) for e in ws.entities.values())
            if hasattr(ws, "active_combat") and ws.active_combat:
                combat_active = True
                round_number = ws.active_combat.get("round_index", 0)

        if hasattr(session, "session_state"):
            ss = session.session_state
            combat_active = str(ss).lower() == "combat" or combat_active

        return SessionStateMsg(
            msg_type=MSG_SESSION_STATE,
            msg_id=_make_msg_id(),
            in_reply_to=in_reply_to,
            timestamp=_now(),
            session_id=session_id,
            campaign_id=campaign_id,
            world_id=world_id,
            entities=entities,
            combat_active=combat_active,
            round_number=round_number,
        )

    async def _message_loop(
        self,
        websocket: WebSocket,
        session: Any,
        session_id: str,
        role: ConnectionRole = ConnectionRole.PLAYER,
    ) -> None:
        """Main message receive/dispatch loop."""
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                error = ErrorEvent(
                    msg_type=MSG_ERROR,
                    msg_id=_make_msg_id(),
                    timestamp=_now(),
                    error_code="MALFORMED_JSON",
                    error_message=f"Invalid JSON: {exc}",
                    recoverable=True,
                )
                await self._send_message(websocket, error)
                continue

            try:
                msg = parse_client_message(data)
            except ValueError as exc:
                error = ErrorEvent(
                    msg_type=MSG_ERROR,
                    msg_id=_make_msg_id(),
                    timestamp=_now(),
                    error_code="INVALID_MESSAGE",
                    error_message=str(exc),
                    recoverable=True,
                )
                await self._send_message(websocket, error)
                continue

            try:
                responses = await self._route_message(msg, session, session_id, role)
            except Exception as exc:
                logger.exception("Error handling message %s", msg.msg_type)
                responses = [
                    ErrorEvent(
                        msg_type=MSG_ERROR,
                        msg_id=_make_msg_id(),
                        in_reply_to=msg.msg_id,
                        timestamp=_now(),
                        error_code="HANDLER_ERROR",
                        error_message=f"Error processing {msg.msg_type}: {exc}",
                        recoverable=True,
                    )
                ]

            for response in responses:
                await self._send_message(websocket, response)

    async def _route_message(
        self,
        msg: ClientMessage,
        session: Any,
        session_id: str,
        role: ConnectionRole = ConnectionRole.PLAYER,
    ) -> List[ServerMessage]:
        """Route a client message to the appropriate handler."""
        if isinstance(msg, PlayerUtterance):
            return await self._handle_utterance(msg, session, role)
        elif isinstance(msg, PlayerAction):
            return await self._handle_action(msg, session)
        elif isinstance(msg, SessionControl):
            return await self._handle_control(msg, session, session_id, role)
        else:
            logger.warning(
                "ws_bridge: unknown client msg_type %r — returning error",
                msg.msg_type,
            )
            return [
                ErrorEvent(
                    msg_type=MSG_ERROR,
                    msg_id=_make_msg_id(),
                    in_reply_to=msg.msg_id,
                    timestamp=_now(),
                    error_code="UNKNOWN_MSG_TYPE",
                    error_message=f"Unknown message type: {msg.msg_type}",
                    recoverable=True,
                )
            ]

    async def _handle_utterance(
        self,
        msg: PlayerUtterance,
        session: Any,
        role: ConnectionRole = ConnectionRole.PLAYER,
    ) -> List[ServerMessage]:
        """Route player utterance through SessionOrchestrator turn cycle."""
        responses: List[ServerMessage] = []

        if msg.text is not None:
            if hasattr(session, "process_text_turn"):
                result = session.process_text_turn(msg.text, self._default_actor_id)
                responses.extend(self._turn_result_to_messages(result, msg.msg_id, session, role))
            else:
                responses.append(ErrorEvent(
                    msg_type=MSG_ERROR,
                    msg_id=_make_msg_id(),
                    in_reply_to=msg.msg_id,
                    timestamp=_now(),
                    error_code="NO_TEXT_HANDLER",
                    error_message="Session does not support text input.",
                    recoverable=True,
                ))
        elif msg.audio_base64 is not None:
            if hasattr(session, "process_voice_turn"):
                import base64
                audio_bytes = base64.b64decode(msg.audio_base64)
                result = session.process_voice_turn(audio_bytes, self._default_actor_id)
                responses.extend(self._turn_result_to_messages(result, msg.msg_id, session, role))
            else:
                responses.append(ErrorEvent(
                    msg_type=MSG_ERROR,
                    msg_id=_make_msg_id(),
                    in_reply_to=msg.msg_id,
                    timestamp=_now(),
                    error_code="NO_VOICE_HANDLER",
                    error_message="Session does not support voice input.",
                    recoverable=True,
                ))
        else:
            responses.append(ErrorEvent(
                msg_type=MSG_ERROR,
                msg_id=_make_msg_id(),
                in_reply_to=msg.msg_id,
                timestamp=_now(),
                error_code="EMPTY_UTTERANCE",
                error_message="PlayerUtterance must include text or audio_base64.",
                recoverable=True,
            ))

        return responses

    async def _handle_action(
        self,
        msg: PlayerAction,
        session: Any,
    ) -> List[ServerMessage]:
        """Route player UI action to appropriate handler."""
        return [
            ErrorEvent(
                msg_type=MSG_ERROR,
                msg_id=_make_msg_id(),
                in_reply_to=msg.msg_id,
                timestamp=_now(),
                error_code="ACTION_NOT_IMPLEMENTED",
                error_message=f"Action type '{msg.action_type}' is not yet implemented.",
                recoverable=True,
            )
        ]

    async def _handle_control(
        self,
        msg: SessionControl,
        session: Any,
        session_id: str,
        role: ConnectionRole = ConnectionRole.PLAYER,
    ) -> List[ServerMessage]:
        """Handle session lifecycle commands."""
        if msg.command == "leave":
            self._sessions.pop(session_id, None)
            return [
                SessionStateMsg(
                    msg_type=MSG_SESSION_STATE,
                    msg_id=_make_msg_id(),
                    in_reply_to=msg.msg_id,
                    timestamp=_now(),
                    session_id=session_id,
                )
            ]

        elif msg.command == "pause":
            return [
                SessionStateMsg(
                    msg_type=MSG_SESSION_STATE,
                    msg_id=_make_msg_id(),
                    in_reply_to=msg.msg_id,
                    timestamp=_now(),
                    session_id=session_id,
                )
            ]

        elif msg.command == "resume":
            snapshot = self._build_session_state(session_id, session, msg.msg_id, role=role)
            return [snapshot]

        else:
            return [
                ErrorEvent(
                    msg_type=MSG_ERROR,
                    msg_id=_make_msg_id(),
                    in_reply_to=msg.msg_id,
                    timestamp=_now(),
                    error_code="UNKNOWN_COMMAND",
                    error_message=f"Unknown session command: {msg.command}",
                    recoverable=True,
                )
            ]

    def _turn_result_to_messages(
        self,
        result: Any,
        in_reply_to: str,
        session: Any = None,
        role: ConnectionRole = ConnectionRole.DM,
    ) -> List[ServerMessage]:
        """Convert a TurnResult from SessionOrchestrator to ServerMessage list.

        Role-aware: DM connections receive full entity state (hp values included).
        PLAYER connections receive hp-stripped updates only.

        Unknown event types are passed through as StateUpdate for extensibility.
        """
        messages: List[ServerMessage] = []

        # Narration event
        narration_text = getattr(result, "narration_text", "")
        if narration_text:
            audio_b64 = None
            narration_audio = getattr(result, "narration_audio", None)
            if narration_audio is not None:
                import base64
                audio_b64 = base64.b64encode(narration_audio).decode("ascii")

            messages.append(NarrationEvent(
                msg_type=MSG_NARRATION,
                msg_id=_make_msg_id(),
                in_reply_to=in_reply_to,
                timestamp=_now(),
                text=narration_text,
                audio_base64=audio_b64,
            ))

        # Role-aware event dispatch — explicit allowlist only.
        # Unknown event types are DROPPED (logged at WARNING). Never broadcast raw.
        events = getattr(result, "events", ())
        for event_dict in events:
            if not isinstance(event_dict, dict):
                continue

            event_type = event_dict.get("event_type", "")

            if event_type == "hp_changed":
                entity_id = (
                    event_dict.get("entity_id")
                    or event_dict.get("payload", {}).get("entity_id", "")
                )
                payload = event_dict.get("payload", {})
                hp_after = payload.get("hp_after") if payload.get("hp_after") is not None \
                    else payload.get("new_hp")

                messages.append(TokenUpdate(
                    msg_type=MSG_TOKEN_UPDATE,
                    msg_id=_make_msg_id(),
                    in_reply_to=in_reply_to,
                    timestamp=_now(),
                    id=entity_id,
                    hp=hp_after if role == ConnectionRole.DM else None,
                ))

            elif event_type == "entity_defeated":
                entity_id = (
                    event_dict.get("entity_id")
                    or event_dict.get("payload", {}).get("entity_id", "")
                )
                messages.append(TokenRemove(
                    msg_type=MSG_TOKEN_REMOVE,
                    msg_id=_make_msg_id(),
                    in_reply_to=in_reply_to,
                    timestamp=_now(),
                    id=entity_id,
                ))

            elif event_type == "combat_started":
                messages.append(ServerMessage(
                    msg_type="combat_start",
                    msg_id=_make_msg_id(),
                    in_reply_to=in_reply_to,
                    timestamp=_now(),
                ))

            elif event_type == "combat_ended":
                messages.append(ServerMessage(
                    msg_type="combat_end",
                    msg_id=_make_msg_id(),
                    in_reply_to=in_reply_to,
                    timestamp=_now(),
                ))

            elif event_type == "action_dropped":
                # Surface compound-utterance truncation as narration (no sensitive data)
                payload = event_dict.get("payload", {})
                dropped = payload.get("dropped_action_type", "action")
                messages.append(NarrationEvent(
                    msg_type=MSG_NARRATION,
                    msg_id=_make_msg_id(),
                    in_reply_to=in_reply_to,
                    timestamp=_now(),
                    text=f"[{dropped} not taken — only one action resolved]",
                ))

            else:
                # Unknown event type — log at WARNING and pass through as state_update.
                logger.warning(
                    "ws_bridge: unhandled event type %r — passing through as state_update",
                    event_type or "UNKNOWN",
                )
                messages.append(StateUpdate(
                    msg_type=MSG_STATE_UPDATE,
                    msg_id=_make_msg_id(),
                    in_reply_to=in_reply_to,
                    timestamp=_now(),
                    update_type=event_type,
                    delta=tuple(sorted(event_dict.get("payload", {}).items())),
                ))

        # Clarification needed
        if getattr(result, "clarification_needed", False):
            messages.append(ErrorEvent(
                msg_type=MSG_ERROR,
                msg_id=_make_msg_id(),
                in_reply_to=in_reply_to,
                timestamp=_now(),
                error_code="CLARIFICATION_NEEDED",
                error_message=getattr(result, "clarification_message", ""),
                recoverable=True,
            ))

        # Error
        error_msg = getattr(result, "error_message", None)
        if error_msg and not getattr(result, "success", True):
            messages.append(ErrorEvent(
                msg_type=MSG_ERROR,
                msg_id=_make_msg_id(),
                in_reply_to=in_reply_to,
                timestamp=_now(),
                error_code="TURN_FAILED",
                error_message=error_msg,
                recoverable=True,
            ))

        # Character state update for player entities in session
        if session is not None:
            world_state = getattr(session, "world_state", None)
            if world_state is not None:
                entities: Dict[str, Any] = getattr(world_state, "entities", {})
                for entity in entities.values():
                    if entity.get(EF.TEAM) == "player":
                        messages.append(CharacterState(
                            msg_type=MSG_CHARACTER_STATE,
                            msg_id=_make_msg_id(),
                            in_reply_to=in_reply_to,
                            timestamp=_now(),
                            name=entity.get("name", ""),
                            hp=entity.get(EF.HP_CURRENT, 0),
                            hp_max=entity.get(EF.HP_MAX, 0),
                            ac=entity.get(EF.AC, 0),
                        ))

        # If nothing was generated, send a minimal narration
        if not messages:
            messages.append(NarrationEvent(
                msg_type=MSG_NARRATION,
                msg_id=_make_msg_id(),
                in_reply_to=in_reply_to,
                timestamp=_now(),
                text="(No response generated.)",
            ))

        return messages

    async def _send_message(self, websocket: WebSocket, msg: ServerMessage) -> None:
        """Serialize and send a ServerMessage over the WebSocket."""
        await websocket.send_text(json.dumps(msg.to_dict()))

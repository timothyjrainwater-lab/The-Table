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
from typing import Any, Callable, Dict, List, Optional

from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from aidm.schemas.ws_protocol import (
    MSG_ERROR,
    MSG_NARRATION,
    MSG_PLAYER_ACTION,
    MSG_PLAYER_UTTERANCE,
    MSG_SESSION_CONTROL,
    MSG_SESSION_STATE,
    MSG_STATE_UPDATE,
    MSG_COMBAT_EVENT,
    ClientMessage,
    ErrorEvent,
    NarrationEvent,
    PlayerAction,
    PlayerUtterance,
    SessionControl,
    SessionStateMsg,
    StateUpdate,
    CombatEvent,
    ServerMessage,
    parse_client_message,
)

logger = logging.getLogger(__name__)


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
        # Connection -> session_id mapping
        self._connections: Dict[int, str] = {}

    @property
    def sessions(self) -> Dict[str, Any]:
        """Active sessions (read-only access for testing)."""
        return dict(self._sessions)

    async def websocket_endpoint(self, websocket: WebSocket) -> None:
        """Handle a single WebSocket connection lifecycle.

        1. Accept connection
        2. Receive session_control "join" message
        3. Create or resume session
        4. Send full session_state snapshot
        5. Enter message loop
        6. Handle disconnect (pause session, preserve state)
        """
        await websocket.accept()
        conn_id = id(websocket)
        session_id: Optional[str] = None

        try:
            # Wait for join message
            join_msg = await self._receive_join(websocket)
            if join_msg is None:
                return

            session_id = join_msg.session_id or str(uuid.uuid4())
            self._connections[conn_id] = session_id

            # Create or resume session
            session = self._get_or_create_session(session_id)

            # Send session state snapshot
            snapshot = self._build_session_state(session_id, session, join_msg.msg_id)
            await self._send_message(websocket, snapshot)

            # Message loop
            await self._message_loop(websocket, session, session_id)

        except WebSocketDisconnect:
            logger.info("Client disconnected (conn=%d, session=%s)", conn_id, session_id)
        except Exception:
            logger.exception("Unexpected error in WebSocket handler (conn=%d)", conn_id)
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

    def _get_or_create_session(self, session_id: str) -> Any:
        """Get existing session or create a new one via factory."""
        if session_id not in self._sessions:
            session = self._factory(session_id)
            self._sessions[session_id] = session
        return self._sessions[session_id]

    def _build_session_state(
        self,
        session_id: str,
        session: Any,
        in_reply_to: Optional[str] = None,
    ) -> SessionStateMsg:
        """Build a SessionStateMsg from the current session state."""
        # Extract state from orchestrator if available
        entities: tuple = ()
        combat_active = False
        round_number = 0
        campaign_id = ""
        world_id = ""

        if hasattr(session, "world_state"):
            ws = session.world_state
            if hasattr(ws, "entities"):
                entities = tuple(ws.entities.values())
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

            # Route to handler
            try:
                responses = await self._route_message(msg, session, session_id)
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
    ) -> List[ServerMessage]:
        """Route a client message to the appropriate handler."""
        if isinstance(msg, PlayerUtterance):
            return await self._handle_utterance(msg, session)
        elif isinstance(msg, PlayerAction):
            return await self._handle_action(msg, session)
        elif isinstance(msg, SessionControl):
            return await self._handle_control(msg, session, session_id)
        else:
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
    ) -> List[ServerMessage]:
        """Route player utterance through SessionOrchestrator turn cycle."""
        responses: List[ServerMessage] = []

        if msg.text is not None:
            # Text input path
            if hasattr(session, "process_text_turn"):
                result = session.process_text_turn(msg.text, self._default_actor_id)
                responses.extend(self._turn_result_to_messages(result, msg.msg_id))
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
            # Audio input path
            if hasattr(session, "process_voice_turn"):
                import base64
                audio_bytes = base64.b64decode(msg.audio_base64)
                result = session.process_voice_turn(audio_bytes, self._default_actor_id)
                responses.extend(self._turn_result_to_messages(result, msg.msg_id))
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
        # Actions are a future extension point. For now, acknowledge receipt.
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
    ) -> List[ServerMessage]:
        """Handle session lifecycle commands."""
        if msg.command == "leave":
            # Clean up session
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
            # Session state is preserved in self._sessions
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
            snapshot = self._build_session_state(session_id, session, msg.msg_id)
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
    ) -> List[ServerMessage]:
        """Convert a TurnResult from SessionOrchestrator to ServerMessage list."""
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

        # State updates from events
        events = getattr(result, "events", ())
        for event_dict in events:
            if isinstance(event_dict, dict):
                event_type = event_dict.get("event_type", "")
                entity_id = event_dict.get("entity_id") or event_dict.get(
                    "payload", {},
                ).get("entity_id")
                messages.append(StateUpdate(
                    msg_type=MSG_STATE_UPDATE,
                    msg_id=_make_msg_id(),
                    in_reply_to=in_reply_to,
                    timestamp=_now(),
                    update_type=event_type,
                    entity_id=entity_id,
                    delta=tuple(sorted(event_dict.items())),
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

        # If nothing was generated, send at least a minimal narration
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
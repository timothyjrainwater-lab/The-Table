"""WebSocket message protocol schemas — Client ↔ Server communication.

Schema-first definitions for the WebSocket bridge message protocol:

Client → Server:
- PlayerUtterance: Text or audio input from the player
- PlayerAction: UI-driven action (ability use, token move, sheet open)
- SessionControl: Session lifecycle commands (join, leave, pause, resume)

Server → Client:
- NarrationEvent: DM narration text with optional TTS audio
- StateUpdate: Game state change notification
- CombatEvent: Combat resolution event
- ErrorEvent: Error notification
- SessionState: Full session state snapshot (join/reconnect)

All message dataclasses are frozen. All support to_dict() / from_dict().
Message routing uses the msg_type discriminator field.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Message type constants
# ---------------------------------------------------------------------------

MSG_PLAYER_UTTERANCE = "player_utterance"
MSG_PLAYER_ACTION = "player_action"
MSG_SESSION_CONTROL = "session_control"
MSG_NARRATION = "narration"
MSG_STATE_UPDATE = "state_update"
MSG_COMBAT_EVENT = "combat_event"
MSG_ERROR = "error"
MSG_SESSION_STATE = "session_state"
MSG_TOKEN_ADD = "token_add"
MSG_TOKEN_UPDATE = "token_update"
MSG_TOKEN_REMOVE = "token_remove"
MSG_CHARACTER_STATE = "character_state"


# ---------------------------------------------------------------------------
# Client → Server Messages
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ClientMessage:
    """Base for all client-to-server messages."""

    msg_type: str
    """Discriminator field for message routing."""

    msg_id: str
    """Client-generated UUID for correlation."""

    timestamp: float
    """Client timestamp (informational only)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClientMessage":
        """Create from dictionary."""
        return cls(
            msg_type=data.get("msg_type", ""),
            msg_id=data.get("msg_id", ""),
            timestamp=data.get("timestamp", 0.0),
        )


@dataclass(frozen=True)
class PlayerUtterance(ClientMessage):
    """Player speaks or types a command."""

    text: Optional[str] = None
    """Text input (typed)."""

    audio_base64: Optional[str] = None
    """Audio input (spoken), base64-encoded."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
        }
        if self.text is not None:
            d["text"] = self.text
        if self.audio_base64 is not None:
            d["audio_base64"] = self.audio_base64
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerUtterance":
        """Create from dictionary."""
        return cls(
            msg_type=data.get("msg_type", MSG_PLAYER_UTTERANCE),
            msg_id=data.get("msg_id", ""),
            timestamp=data.get("timestamp", 0.0),
            text=data.get("text"),
            audio_base64=data.get("audio_base64"),
        )


@dataclass(frozen=True)
class PlayerAction(ClientMessage):
    """Player clicks a UI element (ability, item, map cell)."""

    action_type: str = ""
    """Action type: 'use_ability', 'move_token', 'open_sheet', etc."""

    payload: Tuple[Tuple[str, Any], ...] = ()
    """Action-specific data as frozen key-value pairs."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
            "action_type": self.action_type,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlayerAction":
        """Create from dictionary."""
        payload_raw = data.get("payload", {})
        payload = tuple(sorted(payload_raw.items())) if payload_raw else ()
        return cls(
            msg_type=data.get("msg_type", MSG_PLAYER_ACTION),
            msg_id=data.get("msg_id", ""),
            timestamp=data.get("timestamp", 0.0),
            action_type=data.get("action_type", ""),
            payload=payload,
        )


@dataclass(frozen=True)
class SessionControl(ClientMessage):
    """Session lifecycle control."""

    command: str = ""
    """Command: 'join', 'leave', 'pause', 'resume'."""

    session_id: Optional[str] = None
    """Target session ID (None for new session)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d = {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
            "command": self.command,
        }
        if self.session_id is not None:
            d["session_id"] = self.session_id
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionControl":
        """Create from dictionary."""
        return cls(
            msg_type=data.get("msg_type", MSG_SESSION_CONTROL),
            msg_id=data.get("msg_id", ""),
            timestamp=data.get("timestamp", 0.0),
            command=data.get("command", ""),
            session_id=data.get("session_id"),
        )


# ---------------------------------------------------------------------------
# Server → Client Messages
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ServerMessage:
    """Base for all server-to-client messages."""

    msg_type: str
    """Discriminator field for message routing."""

    msg_id: str
    """Server-generated UUID."""

    in_reply_to: Optional[str] = None
    """Client msg_id this responds to."""

    timestamp: float = 0.0
    """Server timestamp."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d: Dict[str, Any] = {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
        }
        if self.in_reply_to is not None:
            d["in_reply_to"] = self.in_reply_to
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServerMessage":
        """Create from dictionary."""
        return cls(
            msg_type=data.get("msg_type", ""),
            msg_id=data.get("msg_id", ""),
            in_reply_to=data.get("in_reply_to"),
            timestamp=data.get("timestamp", 0.0),
        )


@dataclass(frozen=True)
class NarrationEvent(ServerMessage):
    """DM narration text."""

    text: str = ""
    """Narration text content."""

    audio_base64: Optional[str] = None
    """TTS audio, base64-encoded."""

    voice_persona: Optional[str] = None
    """Voice persona used for TTS."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d: Dict[str, Any] = {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
            "text": self.text,
        }
        if self.in_reply_to is not None:
            d["in_reply_to"] = self.in_reply_to
        if self.audio_base64 is not None:
            d["audio_base64"] = self.audio_base64
        if self.voice_persona is not None:
            d["voice_persona"] = self.voice_persona
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NarrationEvent":
        """Create from dictionary."""
        return cls(
            msg_type=data.get("msg_type", MSG_NARRATION),
            msg_id=data.get("msg_id", ""),
            in_reply_to=data.get("in_reply_to"),
            timestamp=data.get("timestamp", 0.0),
            text=data.get("text", ""),
            audio_base64=data.get("audio_base64"),
            voice_persona=data.get("voice_persona"),
        )


@dataclass(frozen=True)
class StateUpdate(ServerMessage):
    """Game state change."""

    update_type: str = ""
    """Update type: 'hp_change', 'position_change', 'condition_applied', etc."""

    entity_id: Optional[str] = None
    """Entity affected by the state change."""

    delta: Tuple[Tuple[str, Any], ...] = ()
    """State change payload as frozen key-value pairs."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d: Dict[str, Any] = {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
            "update_type": self.update_type,
            "delta": dict(self.delta),
        }
        if self.in_reply_to is not None:
            d["in_reply_to"] = self.in_reply_to
        if self.entity_id is not None:
            d["entity_id"] = self.entity_id
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateUpdate":
        """Create from dictionary."""
        delta_raw = data.get("delta", {})
        delta = tuple(sorted(delta_raw.items())) if delta_raw else ()
        return cls(
            msg_type=data.get("msg_type", MSG_STATE_UPDATE),
            msg_id=data.get("msg_id", ""),
            in_reply_to=data.get("in_reply_to"),
            timestamp=data.get("timestamp", 0.0),
            update_type=data.get("update_type", ""),
            entity_id=data.get("entity_id"),
            delta=delta,
        )


@dataclass(frozen=True)
class CombatEvent(ServerMessage):
    """Combat resolution event."""

    event_type: str = ""
    """Event type: 'attack_result', 'damage_dealt', 'save_result', etc."""

    source_id: Optional[str] = None
    """Source entity ID."""

    target_id: Optional[str] = None
    """Target entity ID."""

    result: Tuple[Tuple[str, Any], ...] = ()
    """Event-specific result data as frozen key-value pairs."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d: Dict[str, Any] = {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "result": dict(self.result),
        }
        if self.in_reply_to is not None:
            d["in_reply_to"] = self.in_reply_to
        if self.source_id is not None:
            d["source_id"] = self.source_id
        if self.target_id is not None:
            d["target_id"] = self.target_id
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CombatEvent":
        """Create from dictionary."""
        result_raw = data.get("result", {})
        result = tuple(sorted(result_raw.items())) if result_raw else ()
        return cls(
            msg_type=data.get("msg_type", MSG_COMBAT_EVENT),
            msg_id=data.get("msg_id", ""),
            in_reply_to=data.get("in_reply_to"),
            timestamp=data.get("timestamp", 0.0),
            event_type=data.get("event_type", ""),
            source_id=data.get("source_id"),
            target_id=data.get("target_id"),
            result=result,
        )


@dataclass(frozen=True)
class ErrorEvent(ServerMessage):
    """Error notification."""

    error_code: str = ""
    """Machine-readable error code."""

    error_message: str = ""
    """Human-readable error description."""

    recoverable: bool = True
    """Whether the client can recover from this error."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d: Dict[str, Any] = {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "recoverable": self.recoverable,
        }
        if self.in_reply_to is not None:
            d["in_reply_to"] = self.in_reply_to
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorEvent":
        """Create from dictionary."""
        return cls(
            msg_type=data.get("msg_type", MSG_ERROR),
            msg_id=data.get("msg_id", ""),
            in_reply_to=data.get("in_reply_to"),
            timestamp=data.get("timestamp", 0.0),
            error_code=data.get("error_code", ""),
            error_message=data.get("error_message", ""),
            recoverable=data.get("recoverable", True),
        )


@dataclass(frozen=True)
class TokenAdd(ServerMessage):
    """Token placement event — sent for each positioned entity on join/reconnect."""

    id: str = ""
    """Entity ID."""

    name: str = ""
    """Display name."""

    faction: str = ""
    """Team/faction (e.g. 'player', 'monsters')."""

    col: int = 0
    """Grid column (x)."""

    row: int = 0
    """Grid row (y)."""

    hp: Optional[int] = None
    """Current HP — DM only; None if stripped for player connections."""

    hp_max: Optional[int] = None
    """Max HP — DM only; None if stripped for player connections."""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
            "id": self.id,
            "name": self.name,
            "faction": self.faction,
            "col": self.col,
            "row": self.row,
        }
        if self.in_reply_to is not None:
            d["in_reply_to"] = self.in_reply_to
        if self.hp is not None:
            d["hp"] = self.hp
        if self.hp_max is not None:
            d["hp_max"] = self.hp_max
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenAdd":
        return cls(
            msg_type=data.get("msg_type", MSG_TOKEN_ADD),
            msg_id=data.get("msg_id", ""),
            in_reply_to=data.get("in_reply_to"),
            timestamp=data.get("timestamp", 0.0),
            id=data.get("id", ""),
            name=data.get("name", ""),
            faction=data.get("faction", ""),
            col=data.get("col", 0),
            row=data.get("row", 0),
            hp=data.get("hp"),
            hp_max=data.get("hp_max"),
        )


@dataclass(frozen=True)
class TokenUpdate(ServerMessage):
    """Token state update — sent when an entity's displayed state changes."""

    id: str = ""
    """Entity ID."""

    hp: Optional[int] = None
    """Current HP — DM only; None if stripped for player connections."""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
            "id": self.id,
        }
        if self.in_reply_to is not None:
            d["in_reply_to"] = self.in_reply_to
        if self.hp is not None:
            d["hp"] = self.hp
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenUpdate":
        return cls(
            msg_type=data.get("msg_type", MSG_TOKEN_UPDATE),
            msg_id=data.get("msg_id", ""),
            in_reply_to=data.get("in_reply_to"),
            timestamp=data.get("timestamp", 0.0),
            id=data.get("id", ""),
            hp=data.get("hp"),
        )


@dataclass(frozen=True)
class TokenRemove(ServerMessage):
    """Token removal event — sent when an entity is defeated or leaves the map."""

    id: str = ""
    """Entity ID to remove."""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
            "id": self.id,
        }
        if self.in_reply_to is not None:
            d["in_reply_to"] = self.in_reply_to
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenRemove":
        return cls(
            msg_type=data.get("msg_type", MSG_TOKEN_REMOVE),
            msg_id=data.get("msg_id", ""),
            in_reply_to=data.get("in_reply_to"),
            timestamp=data.get("timestamp", 0.0),
            id=data.get("id", ""),
        )


@dataclass(frozen=True)
class CharacterState(ServerMessage):
    """Player character state summary — emitted after each turn for player entities."""

    name: str = ""
    hp: int = 0
    hp_max: int = 0
    ac: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
            "name": self.name,
            "hp": self.hp,
            "hp_max": self.hp_max,
            "ac": self.ac,
        }
        if self.in_reply_to is not None:
            d["in_reply_to"] = self.in_reply_to
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterState":
        return cls(
            msg_type=data.get("msg_type", MSG_CHARACTER_STATE),
            msg_id=data.get("msg_id", ""),
            in_reply_to=data.get("in_reply_to"),
            timestamp=data.get("timestamp", 0.0),
            name=data.get("name", ""),
            hp=data.get("hp", 0),
            hp_max=data.get("hp_max", 0),
            ac=data.get("ac", 0),
        )


@dataclass(frozen=True)
class SessionStateMsg(ServerMessage):
    """Full session state snapshot (sent on join/reconnect)."""

    session_id: str = ""
    """Active session ID."""

    campaign_id: str = ""
    """Campaign this session belongs to."""

    world_id: str = ""
    """World identifier."""

    entities: Tuple[Dict[str, Any], ...] = ()
    """Current entity states."""

    combat_active: bool = False
    """Whether combat is currently active."""

    round_number: int = 0
    """Current combat round number (0 if no combat)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        d: Dict[str, Any] = {
            "msg_type": self.msg_type,
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "campaign_id": self.campaign_id,
            "world_id": self.world_id,
            "entities": list(self.entities),
            "combat_active": self.combat_active,
            "round_number": self.round_number,
        }
        if self.in_reply_to is not None:
            d["in_reply_to"] = self.in_reply_to
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionStateMsg":
        """Create from dictionary."""
        return cls(
            msg_type=data.get("msg_type", MSG_SESSION_STATE),
            msg_id=data.get("msg_id", ""),
            in_reply_to=data.get("in_reply_to"),
            timestamp=data.get("timestamp", 0.0),
            session_id=data.get("session_id", ""),
            campaign_id=data.get("campaign_id", ""),
            world_id=data.get("world_id", ""),
            entities=tuple(data.get("entities", [])),
            combat_active=data.get("combat_active", False),
            round_number=data.get("round_number", 0),
        )


# ---------------------------------------------------------------------------
# Message routing
# ---------------------------------------------------------------------------

# Client message type → dataclass mapping
CLIENT_MSG_TYPES: Dict[str, type] = {
    MSG_PLAYER_UTTERANCE: PlayerUtterance,
    MSG_PLAYER_ACTION: PlayerAction,
    MSG_SESSION_CONTROL: SessionControl,
}

# Server message type → dataclass mapping
SERVER_MSG_TYPES: Dict[str, type] = {
    MSG_NARRATION: NarrationEvent,
    MSG_STATE_UPDATE: StateUpdate,
    MSG_COMBAT_EVENT: CombatEvent,
    MSG_ERROR: ErrorEvent,
    MSG_SESSION_STATE: SessionStateMsg,
    MSG_TOKEN_ADD: TokenAdd,
    MSG_TOKEN_UPDATE: TokenUpdate,
    MSG_TOKEN_REMOVE: TokenRemove,
    MSG_CHARACTER_STATE: CharacterState,
}


def parse_client_message(data: Dict[str, Any]) -> ClientMessage:
    """Parse a raw dict into the appropriate ClientMessage subclass.

    Uses msg_type as the discriminator. Falls back to base ClientMessage
    if the type is unrecognized.

    Args:
        data: Raw message dict (from JSON).

    Returns:
        Typed ClientMessage subclass instance.

    Raises:
        ValueError: If msg_type is missing.
    """
    msg_type = data.get("msg_type")
    if not msg_type:
        raise ValueError("Message missing required 'msg_type' field")

    cls = CLIENT_MSG_TYPES.get(msg_type)
    if cls is None:
        return ClientMessage.from_dict(data)
    return cls.from_dict(data)


def parse_server_message(data: Dict[str, Any]) -> ServerMessage:
    """Parse a raw dict into the appropriate ServerMessage subclass.

    Uses msg_type as the discriminator. Falls back to base ServerMessage
    if the type is unrecognized.

    Args:
        data: Raw message dict (from JSON).

    Returns:
        Typed ServerMessage subclass instance.

    Raises:
        ValueError: If msg_type is missing.
    """
    msg_type = data.get("msg_type")
    if not msg_type:
        raise ValueError("Message missing required 'msg_type' field")

    cls = SERVER_MSG_TYPES.get(msg_type)
    if cls is None:
        return ServerMessage.from_dict(data)
    return cls.from_dict(data)
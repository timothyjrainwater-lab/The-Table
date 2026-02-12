"""WO-WEBSOCKET-BRIDGE-001: WebSocket Bridge Tests

Validates the WebSocket bridge layer:
1. Message schema round-trip (all message types to_dict/from_dict)
2. Message discriminator routing (msg_type → correct handler)
3. Connection lifecycle: connect → join → session_state → disconnect
4. Utterance routing: PlayerUtterance → mock SessionOrchestrator → NarrationEvent
5. Error handling: malformed message → ErrorEvent
6. Session resume: disconnect + reconnect → session_state with correct state
7. Multiple concurrent connections (different session IDs)
8. Health endpoint returns 200

Test Categories:
1. Protocol Schema Round-Trip (9 tests)
2. Message Discriminator Routing (4 tests)
3. Connection Lifecycle (4 tests)
4. Utterance Routing (3 tests)
5. Error Handling (3 tests)
6. Session Resume (1 test)
7. Concurrent Connections (1 test)
8. Health Endpoint (1 test)

Total: 26 tests
"""

import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

from aidm.schemas.ws_protocol import (
    MSG_COMBAT_EVENT,
    MSG_ERROR,
    MSG_NARRATION,
    MSG_PLAYER_ACTION,
    MSG_PLAYER_UTTERANCE,
    MSG_SESSION_CONTROL,
    MSG_SESSION_STATE,
    MSG_STATE_UPDATE,
    ClientMessage,
    CombatEvent,
    ErrorEvent,
    NarrationEvent,
    PlayerAction,
    PlayerUtterance,
    SessionControl,
    SessionStateMsg,
    ServerMessage,
    StateUpdate,
    parse_client_message,
    parse_server_message,
)
from aidm.server.app import create_app
from aidm.server.ws_bridge import WebSocketBridge


# ======================================================================
# FIXTURES
# ======================================================================


@dataclass(frozen=True)
class MockTurnResult:
    """Mock TurnResult matching SessionOrchestrator.TurnResult shape."""

    success: bool = True
    narration_text: str = "The sword strikes true."
    narration_audio: Optional[bytes] = None
    events: Tuple[Dict[str, Any], ...] = ()
    clarification_needed: bool = False
    clarification_message: Optional[str] = None
    candidates: Optional[Tuple[str, ...]] = None
    provenance: str = "[NARRATIVE:TEMPLATE]"
    error_message: Optional[str] = None


class MockOrchestrator:
    """Mock SessionOrchestrator with process_text_turn / process_voice_turn."""

    def __init__(self) -> None:
        self.world_state = MagicMock()
        self.world_state.entities = {
            "pc_fighter": {"entity_id": "pc_fighter", "name": "Kael", "hp_current": 30},
        }
        self.world_state.active_combat = None
        self.session_state = "exploration"
        self.text_calls: list = []
        self.voice_calls: list = []

    def process_text_turn(self, text: str, actor_id: str) -> MockTurnResult:
        self.text_calls.append((text, actor_id))
        return MockTurnResult(
            success=True,
            narration_text=f"You said: {text}",
            events=({"event_type": "narration", "text": text},),
        )

    def process_voice_turn(self, audio_bytes: bytes, actor_id: str) -> MockTurnResult:
        self.voice_calls.append((audio_bytes, actor_id))
        return MockTurnResult(
            success=True,
            narration_text="Voice command received.",
        )


def _mock_factory(session_id: str) -> MockOrchestrator:
    """Factory that creates MockOrchestrator instances."""
    return MockOrchestrator()


# Shared orchestrator that persists across calls for session-resume tests
_shared_orchestrators: Dict[str, MockOrchestrator] = {}


def _persistent_factory(session_id: str) -> MockOrchestrator:
    """Factory that reuses orchestrators by session_id."""
    if session_id not in _shared_orchestrators:
        _shared_orchestrators[session_id] = MockOrchestrator()
    return _shared_orchestrators[session_id]


def _make_join_msg(session_id: Optional[str] = None) -> dict:
    """Build a join message dict."""
    d = {
        "msg_type": MSG_SESSION_CONTROL,
        "msg_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "command": "join",
    }
    if session_id is not None:
        d["session_id"] = session_id
    return d


def _make_utterance_msg(text: str) -> dict:
    """Build a player utterance message dict."""
    return {
        "msg_type": MSG_PLAYER_UTTERANCE,
        "msg_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "text": text,
    }


@pytest.fixture
def app():
    """Starlette test app with mock orchestrator factory."""
    return create_app(
        session_orchestrator_factory=_mock_factory,
    )


@pytest.fixture
def client(app):
    """Starlette test client."""
    return TestClient(app)


@pytest.fixture
def persistent_app():
    """App with persistent factory for session-resume tests."""
    _shared_orchestrators.clear()
    return create_app(
        session_orchestrator_factory=_persistent_factory,
    )


# ======================================================================
# 1. Protocol Schema Round-Trip Tests
# ======================================================================


class TestProtocolSchemaRoundTrip:
    """All message types survive to_dict() → from_dict() round-trip."""

    def test_client_message_round_trip(self) -> None:
        msg = ClientMessage(msg_type="test", msg_id="abc-123", timestamp=1000.0)
        d = msg.to_dict()
        restored = ClientMessage.from_dict(d)
        assert restored.msg_type == "test"
        assert restored.msg_id == "abc-123"
        assert restored.timestamp == 1000.0

    def test_player_utterance_round_trip(self) -> None:
        msg = PlayerUtterance(
            msg_type=MSG_PLAYER_UTTERANCE,
            msg_id="u-001",
            timestamp=1001.0,
            text="attack the goblin",
            audio_base64=None,
        )
        d = msg.to_dict()
        restored = PlayerUtterance.from_dict(d)
        assert restored.text == "attack the goblin"
        assert restored.audio_base64 is None
        assert "audio_base64" not in d  # None fields omitted

    def test_player_action_round_trip(self) -> None:
        msg = PlayerAction(
            msg_type=MSG_PLAYER_ACTION,
            msg_id="a-001",
            timestamp=1002.0,
            action_type="use_ability",
            payload=(("ability_id", "power_attack"), ("target", "goblin_1")),
        )
        d = msg.to_dict()
        assert d["payload"] == {"ability_id": "power_attack", "target": "goblin_1"}
        restored = PlayerAction.from_dict(d)
        assert restored.action_type == "use_ability"
        assert dict(restored.payload) == {"ability_id": "power_attack", "target": "goblin_1"}

    def test_session_control_round_trip(self) -> None:
        msg = SessionControl(
            msg_type=MSG_SESSION_CONTROL,
            msg_id="sc-001",
            timestamp=1003.0,
            command="join",
            session_id="sess-42",
        )
        d = msg.to_dict()
        restored = SessionControl.from_dict(d)
        assert restored.command == "join"
        assert restored.session_id == "sess-42"

    def test_narration_event_round_trip(self) -> None:
        msg = NarrationEvent(
            msg_type=MSG_NARRATION,
            msg_id="n-001",
            in_reply_to="u-001",
            timestamp=2000.0,
            text="The blade sings through the air.",
            voice_persona="dm_voice",
        )
        d = msg.to_dict()
        restored = NarrationEvent.from_dict(d)
        assert restored.text == "The blade sings through the air."
        assert restored.in_reply_to == "u-001"
        assert restored.voice_persona == "dm_voice"

    def test_state_update_round_trip(self) -> None:
        msg = StateUpdate(
            msg_type=MSG_STATE_UPDATE,
            msg_id="su-001",
            timestamp=2001.0,
            update_type="hp_change",
            entity_id="goblin_1",
            delta=(("hp_current", 3), ("hp_delta", -2)),
        )
        d = msg.to_dict()
        assert d["delta"] == {"hp_current": 3, "hp_delta": -2}
        restored = StateUpdate.from_dict(d)
        assert restored.update_type == "hp_change"
        assert restored.entity_id == "goblin_1"

    def test_combat_event_round_trip(self) -> None:
        msg = CombatEvent(
            msg_type=MSG_COMBAT_EVENT,
            msg_id="ce-001",
            timestamp=2002.0,
            event_type="attack_result",
            source_id="pc_fighter",
            target_id="goblin_1",
            result=(("hit", True), ("damage", 7)),
        )
        d = msg.to_dict()
        restored = CombatEvent.from_dict(d)
        assert restored.event_type == "attack_result"
        assert restored.source_id == "pc_fighter"
        assert dict(restored.result) == {"damage": 7, "hit": True}

    def test_error_event_round_trip(self) -> None:
        msg = ErrorEvent(
            msg_type=MSG_ERROR,
            msg_id="e-001",
            timestamp=2003.0,
            error_code="PARSE_FAILED",
            error_message="Could not parse input.",
            recoverable=True,
        )
        d = msg.to_dict()
        restored = ErrorEvent.from_dict(d)
        assert restored.error_code == "PARSE_FAILED"
        assert restored.recoverable is True

    def test_session_state_round_trip(self) -> None:
        entities = (
            {"entity_id": "pc_fighter", "name": "Kael", "hp_current": 30},
        )
        msg = SessionStateMsg(
            msg_type=MSG_SESSION_STATE,
            msg_id="ss-001",
            timestamp=2004.0,
            session_id="sess-42",
            campaign_id="camp-1",
            world_id="world-1",
            entities=entities,
            combat_active=True,
            round_number=3,
        )
        d = msg.to_dict()
        assert d["entities"] == list(entities)
        restored = SessionStateMsg.from_dict(d)
        assert restored.session_id == "sess-42"
        assert restored.combat_active is True
        assert restored.round_number == 3
        assert len(restored.entities) == 1


# ======================================================================
# 2. Message Discriminator Routing Tests
# ======================================================================


class TestMessageDiscriminatorRouting:
    """parse_client_message routes msg_type to correct dataclass."""

    def test_routes_player_utterance(self) -> None:
        data = {"msg_type": MSG_PLAYER_UTTERANCE, "msg_id": "x", "timestamp": 0, "text": "hi"}
        msg = parse_client_message(data)
        assert isinstance(msg, PlayerUtterance)
        assert msg.text == "hi"

    def test_routes_player_action(self) -> None:
        data = {
            "msg_type": MSG_PLAYER_ACTION, "msg_id": "x", "timestamp": 0,
            "action_type": "move_token", "payload": {"x": 5},
        }
        msg = parse_client_message(data)
        assert isinstance(msg, PlayerAction)
        assert msg.action_type == "move_token"

    def test_routes_session_control(self) -> None:
        data = {
            "msg_type": MSG_SESSION_CONTROL, "msg_id": "x", "timestamp": 0,
            "command": "join",
        }
        msg = parse_client_message(data)
        assert isinstance(msg, SessionControl)
        assert msg.command == "join"

    def test_missing_msg_type_raises(self) -> None:
        with pytest.raises(ValueError, match="msg_type"):
            parse_client_message({"msg_id": "x", "timestamp": 0})

    def test_unknown_msg_type_falls_back(self) -> None:
        data = {"msg_type": "unknown_future_type", "msg_id": "x", "timestamp": 0}
        msg = parse_client_message(data)
        assert isinstance(msg, ClientMessage)
        assert msg.msg_type == "unknown_future_type"

    def test_server_message_routing(self) -> None:
        data = {
            "msg_type": MSG_NARRATION, "msg_id": "n1", "timestamp": 0,
            "text": "The goblin falls.",
        }
        msg = parse_server_message(data)
        assert isinstance(msg, NarrationEvent)
        assert msg.text == "The goblin falls."


# ======================================================================
# 3. Connection Lifecycle Tests
# ======================================================================


class TestConnectionLifecycle:
    """Connect → join → session_state → message → disconnect."""

    def test_join_returns_session_state(self, client) -> None:
        with client.websocket_connect("/ws") as ws:
            ws.send_text(json.dumps(_make_join_msg("test-session")))
            response = json.loads(ws.receive_text())
            assert response["msg_type"] == MSG_SESSION_STATE
            assert response["session_id"] == "test-session"

    def test_join_without_session_id_generates_one(self, client) -> None:
        with client.websocket_connect("/ws") as ws:
            ws.send_text(json.dumps(_make_join_msg()))
            response = json.loads(ws.receive_text())
            assert response["msg_type"] == MSG_SESSION_STATE
            assert response["session_id"]  # non-empty generated UUID

    def test_non_join_first_message_rejected(self, client) -> None:
        with client.websocket_connect("/ws") as ws:
            ws.send_text(json.dumps(_make_utterance_msg("hello")))
            response = json.loads(ws.receive_text())
            assert response["msg_type"] == MSG_ERROR
            assert response["error_code"] == "EXPECTED_JOIN"

    def test_invalid_json_first_message_rejected(self, client) -> None:
        with client.websocket_connect("/ws") as ws:
            ws.send_text("not valid json{{{")
            response = json.loads(ws.receive_text())
            assert response["msg_type"] == MSG_ERROR
            assert response["error_code"] == "INVALID_JOIN"


# ======================================================================
# 4. Utterance Routing Tests
# ======================================================================


class TestUtteranceRouting:
    """PlayerUtterance → mock SessionOrchestrator → NarrationEvent."""

    def test_text_utterance_returns_narration(self, client) -> None:
        with client.websocket_connect("/ws") as ws:
            # Join
            ws.send_text(json.dumps(_make_join_msg("sess-1")))
            ws.receive_text()  # session_state

            # Send utterance
            ws.send_text(json.dumps(_make_utterance_msg("attack the goblin")))
            response = json.loads(ws.receive_text())
            assert response["msg_type"] == MSG_NARRATION
            assert "attack the goblin" in response["text"]

    def test_empty_utterance_returns_error(self, client) -> None:
        with client.websocket_connect("/ws") as ws:
            ws.send_text(json.dumps(_make_join_msg("sess-2")))
            ws.receive_text()

            # Utterance with neither text nor audio
            msg = {
                "msg_type": MSG_PLAYER_UTTERANCE,
                "msg_id": str(uuid.uuid4()),
                "timestamp": time.time(),
            }
            ws.send_text(json.dumps(msg))
            response = json.loads(ws.receive_text())
            assert response["msg_type"] == MSG_ERROR
            assert response["error_code"] == "EMPTY_UTTERANCE"

    def test_utterance_in_reply_to_correlation(self, client) -> None:
        with client.websocket_connect("/ws") as ws:
            ws.send_text(json.dumps(_make_join_msg("sess-3")))
            ws.receive_text()

            utterance = _make_utterance_msg("cast magic missile")
            ws.send_text(json.dumps(utterance))
            response = json.loads(ws.receive_text())
            assert response["in_reply_to"] == utterance["msg_id"]


# ======================================================================
# 5. Error Handling Tests
# ======================================================================


class TestErrorHandling:
    """Malformed messages → ErrorEvent with recoverable=True."""

    def test_malformed_json_in_loop(self, client) -> None:
        with client.websocket_connect("/ws") as ws:
            ws.send_text(json.dumps(_make_join_msg("sess-err-1")))
            ws.receive_text()

            ws.send_text("{broken json!!")
            response = json.loads(ws.receive_text())
            assert response["msg_type"] == MSG_ERROR
            assert response["error_code"] == "MALFORMED_JSON"
            assert response["recoverable"] is True

    def test_missing_msg_type_in_loop(self, client) -> None:
        with client.websocket_connect("/ws") as ws:
            ws.send_text(json.dumps(_make_join_msg("sess-err-2")))
            ws.receive_text()

            ws.send_text(json.dumps({"msg_id": "x", "timestamp": 0}))
            response = json.loads(ws.receive_text())
            assert response["msg_type"] == MSG_ERROR
            assert response["error_code"] == "INVALID_MESSAGE"

    def test_unknown_msg_type_in_loop(self, client) -> None:
        with client.websocket_connect("/ws") as ws:
            ws.send_text(json.dumps(_make_join_msg("sess-err-3")))
            ws.receive_text()

            ws.send_text(json.dumps({
                "msg_type": "future_msg_type",
                "msg_id": "x",
                "timestamp": 0,
            }))
            response = json.loads(ws.receive_text())
            assert response["msg_type"] == MSG_ERROR
            assert response["error_code"] == "UNKNOWN_MSG_TYPE"


# ======================================================================
# 6. Session Resume Test
# ======================================================================


class TestSessionResume:
    """Disconnect + reconnect → session_state with correct state."""

    def test_reconnect_preserves_session(self) -> None:
        _shared_orchestrators.clear()
        app = create_app(session_orchestrator_factory=_persistent_factory)
        client = TestClient(app)
        session_id = "resume-test-session"

        # First connection: join and send an utterance
        with client.websocket_connect("/ws") as ws:
            ws.send_text(json.dumps(_make_join_msg(session_id)))
            resp1 = json.loads(ws.receive_text())
            assert resp1["msg_type"] == MSG_SESSION_STATE

            ws.send_text(json.dumps(_make_utterance_msg("attack goblin")))
            ws.receive_text()  # narration
            # May receive state update too — drain remaining
            try:
                ws.receive_text()
            except Exception:
                pass

        # Second connection: rejoin same session
        with client.websocket_connect("/ws") as ws:
            ws.send_text(json.dumps(_make_join_msg(session_id)))
            resp2 = json.loads(ws.receive_text())
            assert resp2["msg_type"] == MSG_SESSION_STATE
            assert resp2["session_id"] == session_id


# ======================================================================
# 7. Concurrent Connections Test
# ======================================================================


class TestConcurrentConnections:
    """Multiple concurrent connections with different session IDs."""

    def test_two_concurrent_sessions(self, client) -> None:
        with client.websocket_connect("/ws") as ws1:
            ws1.send_text(json.dumps(_make_join_msg("session-A")))
            resp_a = json.loads(ws1.receive_text())
            assert resp_a["session_id"] == "session-A"

            with client.websocket_connect("/ws") as ws2:
                ws2.send_text(json.dumps(_make_join_msg("session-B")))
                resp_b = json.loads(ws2.receive_text())
                assert resp_b["session_id"] == "session-B"

                # Both sessions work independently
                ws1.send_text(json.dumps(_make_utterance_msg("attack")))
                r1 = json.loads(ws1.receive_text())
                assert r1["msg_type"] == MSG_NARRATION

                ws2.send_text(json.dumps(_make_utterance_msg("defend")))
                r2 = json.loads(ws2.receive_text())
                assert r2["msg_type"] == MSG_NARRATION


# ======================================================================
# 8. Health Endpoint Test
# ======================================================================


class TestHealthEndpoint:
    """GET /health returns 200 with status payload."""

    def test_health_returns_200(self, client) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

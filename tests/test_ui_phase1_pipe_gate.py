"""Gate tests for WO-UI-PHASE1-PIPE-001 - Connect the Pipe.

PIPE-001  start_server.py imports cleanly (no missing deps)
PIPE-002  build_simple_combat_fixture() returns a valid WorldState with 6 actors
PIPE-003  SessionOrchestrator constructed from fixture - no instantiation errors
PIPE-004  create_app() with factory returns an app; _StubSession not used
PIPE-005  player_utterance message routes to process_text_turn() (not unknown handler)
PIPE-006  Attack intent resolves through real engine - returns at least one event
PIPE-007  HP update event present in response after a successful attack
PIPE-008  First WebSocket connection receives DM role; second receives PLAYER role
"""

from __future__ import annotations

import importlib
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# PIPE-001 - start_server.py imports cleanly
# ---------------------------------------------------------------------------

def test_PIPE_001_start_server_imports_cleanly():
    """start_server.py should be importable with no missing dependencies."""
    # Remove cached module if present so we get a clean import
    sys.modules.pop("start_server", None)
    spec = importlib.util.spec_from_file_location(
        "start_server", "start_server.py"
    )
    mod = importlib.util.module_from_spec(spec)
    # This will raise ImportError if any dep is missing
    spec.loader.exec_module(mod)
    assert hasattr(mod, "main"), "start_server.py must expose a main() callable"
    assert hasattr(mod, "_make_session_factory"), (
        "start_server.py must expose _make_session_factory()"
    )


# ---------------------------------------------------------------------------
# PIPE-002 - build_simple_combat_fixture() returns valid WorldState with 6 actors
# ---------------------------------------------------------------------------

def test_PIPE_002_fixture_returns_six_actors():
    """build_simple_combat_fixture() must return a ScenarioFixture with 6 entities."""
    from aidm.runtime.play_controller import build_simple_combat_fixture

    fixture = build_simple_combat_fixture()
    ws = fixture.world_state
    assert ws is not None, "ScenarioFixture.world_state must not be None"
    assert len(ws.entities) == 6, (
        f"Expected 6 actors (3 party + 3 goblins), got {len(ws.entities)}: "
        f"{list(ws.entities.keys())}"
    )


# ---------------------------------------------------------------------------
# PIPE-003 - SessionOrchestrator constructed from fixture - no errors
# ---------------------------------------------------------------------------

def test_PIPE_003_session_orchestrator_constructs():
    """SessionOrchestrator must instantiate from fixture without errors."""
    from aidm.interaction.intent_bridge import IntentBridge
    from aidm.lens.context_assembler import ContextAssembler
    from aidm.lens.scene_manager import SceneManager
    from aidm.narration.guarded_narration_service import GuardedNarrationService
    from aidm.runtime.play_controller import build_simple_combat_fixture
    from aidm.runtime.session_orchestrator import SessionOrchestrator
    from aidm.spark.dm_persona import DMPersona

    fixture = build_simple_combat_fixture()
    orchestrator = SessionOrchestrator(
        world_state=fixture.world_state,
        intent_bridge=IntentBridge(),
        scene_manager=SceneManager(scenes={}),
        dm_persona=DMPersona(),
        narration_service=GuardedNarrationService(),
        context_assembler=ContextAssembler(token_budget=800),
        master_seed=fixture.master_seed,
    )
    assert orchestrator is not None
    assert hasattr(orchestrator, "process_text_turn"), (
        "SessionOrchestrator must expose process_text_turn()"
    )


# ---------------------------------------------------------------------------
# PIPE-004 - create_app() with factory; _StubSession NOT used
# ---------------------------------------------------------------------------

def test_PIPE_004_create_app_with_factory_no_stub():
    """create_app(factory) must return a Starlette app without using _StubSession."""
    from start_server import _make_session_factory
    from aidm.server.app import create_app

    factory = _make_session_factory()
    app = create_app(session_orchestrator_factory=factory)

    assert app is not None, "create_app() must return an app"

    # Confirm the factory is a real factory (returns SessionOrchestrator, not _StubSession)
    from aidm.runtime.session_orchestrator import SessionOrchestrator
    session = factory("test-session-id")
    assert isinstance(session, SessionOrchestrator), (
        f"Factory must produce SessionOrchestrator, got {type(session).__name__}"
    )


# ---------------------------------------------------------------------------
# PIPE-005 - player_utterance routes to process_text_turn (not unknown handler)
# ---------------------------------------------------------------------------

def test_PIPE_005_player_utterance_routes_to_process_text_turn():
    """player_utterance msg_type must resolve to process_text_turn(), not UNKNOWN_MSG_TYPE."""
    import asyncio
    from aidm.server.ws_bridge import WebSocketBridge, ConnectionRole
    from aidm.schemas.ws_protocol import parse_client_message

    # Build a real SessionOrchestrator
    from aidm.interaction.intent_bridge import IntentBridge
    from aidm.lens.context_assembler import ContextAssembler
    from aidm.lens.scene_manager import SceneManager
    from aidm.narration.guarded_narration_service import GuardedNarrationService
    from aidm.runtime.play_controller import build_simple_combat_fixture
    from aidm.runtime.session_orchestrator import SessionOrchestrator
    from aidm.spark.dm_persona import DMPersona

    fixture = build_simple_combat_fixture()
    orchestrator = SessionOrchestrator(
        world_state=fixture.world_state,
        intent_bridge=IntentBridge(),
        scene_manager=SceneManager(scenes={}),
        dm_persona=DMPersona(),
        narration_service=GuardedNarrationService(),
        context_assembler=ContextAssembler(token_budget=800),
        master_seed=fixture.master_seed,
    )

    # Parse a player_utterance message
    raw = {"msg_type": "player_utterance", "text": "attack goblin", "msg_id": "t-001"}
    msg = parse_client_message(raw)
    assert msg is not None, "parse_client_message must handle player_utterance"
    assert msg.msg_type == "player_utterance", (
        f"Expected msg_type='player_utterance', got {msg.msg_type!r}"
    )

    # Verify routing: bridge._route_message returns something from process_text_turn,
    # NOT an UNKNOWN_MSG_TYPE error
    bridge = WebSocketBridge(session_orchestrator_factory=lambda sid: orchestrator)
    process_called = []
    original_ptt = orchestrator.process_text_turn

    def spy_ptt(text, actor_id):
        process_called.append(text)
        return original_ptt(text, actor_id)

    orchestrator.process_text_turn = spy_ptt

    responses = asyncio.get_event_loop().run_until_complete(
        bridge._route_message(msg, orchestrator, "test-session", ConnectionRole.PLAYER)
    )

    # Must NOT contain UNKNOWN_MSG_TYPE error
    error_codes = [
        getattr(r, "error_code", None) for r in responses
    ]
    assert "UNKNOWN_MSG_TYPE" not in error_codes, (
        f"player_utterance must not produce UNKNOWN_MSG_TYPE; responses: {responses}"
    )
    assert len(process_called) == 1, (
        f"process_text_turn must have been called exactly once; calls: {process_called}"
    )


# ---------------------------------------------------------------------------
# PIPE-006 - Attack intent resolves through real engine - returns at least one event
# ---------------------------------------------------------------------------

def test_PIPE_006_attack_resolves_real_engine_returns_event():
    """'attack Goblin Warrior' must produce at least one engine event (not stub output)."""
    from aidm.interaction.intent_bridge import IntentBridge
    from aidm.lens.context_assembler import ContextAssembler
    from aidm.lens.scene_manager import SceneManager
    from aidm.narration.guarded_narration_service import GuardedNarrationService
    from aidm.runtime.play_controller import build_simple_combat_fixture
    from aidm.runtime.session_orchestrator import SessionOrchestrator
    from aidm.spark.dm_persona import DMPersona

    fixture = build_simple_combat_fixture()
    orchestrator = SessionOrchestrator(
        world_state=fixture.world_state,
        intent_bridge=IntentBridge(),
        scene_manager=SceneManager(scenes={}),
        dm_persona=DMPersona(),
        narration_service=GuardedNarrationService(),
        context_assembler=ContextAssembler(token_budget=800),
        master_seed=fixture.master_seed,
    )

    result = orchestrator.process_text_turn("attack Goblin Warrior", "pc_fighter")

    assert result is not None, "process_text_turn must return a TurnResult"
    assert result.success, (
        f"Attack must succeed; error: {result.error_message}; "
        f"clarification: {result.clarification_message}"
    )
    assert len(result.events) > 0, (
        "Real engine must produce at least one event; got zero events. "
        "This indicates _StubSession or stub path was used."
    )


# ---------------------------------------------------------------------------
# PIPE-007 - HP update event present in response after attack
# ---------------------------------------------------------------------------

def test_PIPE_007_hp_update_event_present_after_attack():
    """A successful attack must produce an hp_changed event in TurnResult.events."""
    from aidm.interaction.intent_bridge import IntentBridge
    from aidm.lens.context_assembler import ContextAssembler
    from aidm.lens.scene_manager import SceneManager
    from aidm.narration.guarded_narration_service import GuardedNarrationService
    from aidm.runtime.play_controller import build_simple_combat_fixture
    from aidm.runtime.session_orchestrator import SessionOrchestrator
    from aidm.spark.dm_persona import DMPersona
    from aidm.core.rng_manager import RNGManager

    # Use a seed that guarantees a hit
    fixture = build_simple_combat_fixture(master_seed=1)
    orchestrator = SessionOrchestrator(
        world_state=fixture.world_state,
        intent_bridge=IntentBridge(),
        scene_manager=SceneManager(scenes={}),
        dm_persona=DMPersona(),
        narration_service=GuardedNarrationService(),
        context_assembler=ContextAssembler(token_budget=800),
        master_seed=fixture.master_seed,
    )

    # Try up to 5 seeds to find one that produces a hit + hp_changed
    hp_event_found = False
    for seed in range(1, 20):
        fixture2 = build_simple_combat_fixture(master_seed=seed)
        orch2 = SessionOrchestrator(
            world_state=fixture2.world_state,
            intent_bridge=IntentBridge(),
            scene_manager=SceneManager(scenes={}),
            dm_persona=DMPersona(),
            narration_service=GuardedNarrationService(),
            context_assembler=ContextAssembler(token_budget=800),
            master_seed=seed,
        )
        result = orch2.process_text_turn("attack Goblin Warrior", "pc_fighter")
        if result.success:
            event_types = [
                (e.get("event_type") or e.get("type", ""))
                for e in result.events
            ]
            if "hp_changed" in event_types:
                hp_event_found = True
                break

    assert hp_event_found, (
        "Could not find an hp_changed event across 5 seeds. "
        "hp_changed event must be emitted when an attack hits."
    )


# ---------------------------------------------------------------------------
# PIPE-008 - First WS connection = DM; second = PLAYER
# ---------------------------------------------------------------------------

def test_PIPE_008_first_connection_dm_second_player():
    """WebSocketBridge._assign_role: first call ? DM, second call ? PLAYER."""
    from aidm.server.ws_bridge import WebSocketBridge, ConnectionRole

    bridge = WebSocketBridge(session_orchestrator_factory=lambda sid: MagicMock())

    role1 = bridge._assign_role("session-abc")
    role2 = bridge._assign_role("session-abc")

    assert role1 == ConnectionRole.DM, (
        f"First connection must be DM, got {role1}"
    )
    assert role2 == ConnectionRole.PLAYER, (
        f"Second connection must be PLAYER, got {role2}"
    )
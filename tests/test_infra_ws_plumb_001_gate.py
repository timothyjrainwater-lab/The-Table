"""Gate tests: WO-INFRA-WS-PLUMB-001 — WS Plumbing Closure.

WP-001: main.ts send site uses 'player_utterance' — not 'player_input'
WP-002: attack_roll event → NarrationEvent (not WARNING/StateUpdate)
WP-003: save_rolled event → NarrationEvent (WO spec said 'save_result'; actual event_type is 'save_rolled')
WP-004: condition_applied event → NarrationEvent
WP-005: xp_awarded event → NarrationEvent
WP-006: level_up_applied event → NarrationEvent
WP-007: None of the 5 new event types produce a WARNING log
WP-008: End-to-end mock: player_utterance turn → ≥1 NarrationEvent + ≥1 CharacterState
"""

import asyncio
import logging
import os
import uuid
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from aidm.schemas.ws_protocol import (
    MSG_CHARACTER_STATE,
    MSG_NARRATION,
    MSG_PLAYER_UTTERANCE,
    MSG_STATE_UPDATE,
    CharacterState,
    NarrationEvent,
    PlayerUtterance,
    StateUpdate,
)
from aidm.server.ws_bridge import WebSocketBridge
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _make_bridge(session=None) -> WebSocketBridge:
    def _factory(session_id: str):
        if session is not None:
            return session
        s = MagicMock()
        s.world_state = MagicMock()
        s.world_state.entities = {}
        return s
    return WebSocketBridge(session_orchestrator_factory=_factory)


def _make_stub_result(events=(), narration="Test narration.", session=None):
    """Build a minimal TurnResult-like mock with events and a player entity."""
    result = MagicMock()
    result.narration_text = narration
    result.narration_audio = None
    result.events = list(events)
    result.clarification_needed = False
    result.error_message = None
    result.success = True
    return result


def _make_session_with_player(hp=10, hp_max=20, ac=15):
    session = MagicMock()
    session.world_state = MagicMock()
    session.world_state.entities = {
        "pc_fighter": {
            "name": "Thorin",
            EF.TEAM: "player",
            EF.HP_CURRENT: hp,
            EF.HP_MAX: hp_max,
            EF.AC: ac,
        }
    }
    return session


def _events_of_type(messages, msg_type):
    return [m for m in messages if m.msg_type == msg_type]


def _has_warning_for(caplog, event_type_str):
    return any(
        event_type_str in r.getMessage() or event_type_str in str(getattr(r, "args", ()))
        for r in caplog.records
        if r.levelno == logging.WARNING
    )


# ---------------------------------------------------------------------------
# WP-001: main.ts send site uses 'player_utterance' — grep static check
# ---------------------------------------------------------------------------

def test_wp_001_main_ts_uses_player_utterance():
    """WP-001: client/src/main.ts must send msg_type 'player_utterance', not 'player_input'."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_ts_path = os.path.join(repo_root, "client", "src", "main.ts")

    assert os.path.exists(main_ts_path), f"main.ts not found at {main_ts_path}"

    with open(main_ts_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must NOT contain player_input at a msg_type send site
    # (the old broken value)
    assert "msg_type: 'player_input'" not in content, \
        "main.ts still contains deprecated 'player_input' msg_type send"

    # Must contain player_utterance at the send site
    assert "msg_type: 'player_utterance'" in content, \
        "main.ts must send msg_type 'player_utterance'"


# ---------------------------------------------------------------------------
# WP-002: attack_roll event → NarrationEvent (Format A — "type" key from combat)
# ---------------------------------------------------------------------------

def test_wp_002_attack_roll_surfaces_as_narration():
    """WP-002: attack_roll event (Format A 'type' key) → NarrationEvent, not StateUpdate."""
    bridge = _make_bridge()
    # Format A: combat event serialization (session_orchestrator.py:634-637)
    event = {
        "type": "attack_roll",
        "attacker_id": "pc_fighter",
        "target_id": "goblin_01",
        "total": 18,
        "target_ac": 14,
        "hit": True,
        "d20_result": 15,
    }
    result = _make_stub_result(events=[event])
    messages = bridge._turn_result_to_messages(result, "msg-001")

    narrations = _events_of_type(messages, MSG_NARRATION)
    state_updates = _events_of_type(messages, MSG_STATE_UPDATE)

    assert narrations, "attack_roll must produce at least one NarrationEvent"
    attack_narration = next(
        (m for m in narrations if "Attack" in m.text or "18" in m.text or "HIT" in m.text),
        None
    )
    assert attack_narration is not None, \
        f"Expected NarrationEvent with attack summary, got texts: {[m.text for m in narrations]}"
    # Must not be silently dropped as StateUpdate
    ar_state_updates = [s for s in state_updates if getattr(s, "update_type", "") == "attack_roll"]
    assert not ar_state_updates, "attack_roll must not produce a StateUpdate (was silently dropped)"


# ---------------------------------------------------------------------------
# WP-003: save_rolled event → NarrationEvent
#          NOTE: WO dispatch spec said 'save_result'; actual event_type in engine is 'save_rolled'
#          (save_resolver.py:459). Using correct string.
# ---------------------------------------------------------------------------

def test_wp_003_save_rolled_surfaces_as_narration():
    """WP-003: save_rolled event → NarrationEvent (not dropped as StateUpdate)."""
    bridge = _make_bridge()
    event = {
        "event_type": "save_rolled",  # Format B — exploration path
        "target_id": "pc_fighter",
        "save_type": "fortitude",
        "d20_result": 12,
        "save_bonus": 4,
        "total": 16,
        "dc": 15,
        "outcome": "success",
        "is_natural_20": False,
        "is_natural_1": False,
    }
    result = _make_stub_result(events=[event])
    messages = bridge._turn_result_to_messages(result, "msg-002")

    narrations = _events_of_type(messages, MSG_NARRATION)
    assert narrations, "save_rolled must produce at least one NarrationEvent"

    save_narration = next(
        (m for m in narrations if "save" in m.text.lower() or "16" in m.text or "15" in m.text),
        None
    )
    assert save_narration is not None, \
        f"Expected NarrationEvent with save summary, got: {[m.text for m in narrations]}"

    state_updates = _events_of_type(messages, MSG_STATE_UPDATE)
    sr_drops = [s for s in state_updates if getattr(s, "update_type", "") == "save_rolled"]
    assert not sr_drops, "save_rolled must not be silently dropped as StateUpdate"


# ---------------------------------------------------------------------------
# WP-004: condition_applied event → NarrationEvent
# ---------------------------------------------------------------------------

def test_wp_004_condition_applied_surfaces_as_narration():
    """WP-004: condition_applied event → NarrationEvent."""
    bridge = _make_bridge()
    # Format A — from attack_resolver, condition_applied payload (play_loop:1305)
    event = {
        "type": "condition_applied",
        "entity_id": "goblin_01",
        "condition": "stunned",
        "source": "stunning_fist",
        "duration_rounds": 1,
    }
    result = _make_stub_result(events=[event])
    messages = bridge._turn_result_to_messages(result, "msg-003")

    narrations = _events_of_type(messages, MSG_NARRATION)
    condition_narration = next(
        (m for m in narrations if "stunned" in m.text.lower() or "condition" in m.text.lower()),
        None
    )
    assert condition_narration is not None, \
        f"condition_applied must produce NarrationEvent, got: {[m.text for m in narrations]}"

    state_updates = _events_of_type(messages, MSG_STATE_UPDATE)
    ca_drops = [s for s in state_updates if getattr(s, "update_type", "") == "condition_applied"]
    assert not ca_drops, "condition_applied must not be dropped as StateUpdate"


# ---------------------------------------------------------------------------
# WP-005: xp_awarded event → NarrationEvent
# ---------------------------------------------------------------------------

def test_wp_005_xp_awarded_surfaces_as_narration():
    """WP-005: xp_awarded event → NarrationEvent."""
    bridge = _make_bridge()
    # play_loop.py:1630-1640 — xp_awarded payload
    event = {
        "event_type": "xp_awarded",
        "entity_id": "pc_fighter",
        "xp_amount": 150,
        "source": "defeat:goblin_01",
        "new_total": 350,
    }
    result = _make_stub_result(events=[event])
    messages = bridge._turn_result_to_messages(result, "msg-004")

    narrations = _events_of_type(messages, MSG_NARRATION)
    xp_narration = next(
        (m for m in narrations if "150" in m.text or "xp" in m.text.lower() or "XP" in m.text),
        None
    )
    assert xp_narration is not None, \
        f"xp_awarded must produce NarrationEvent with amount, got: {[m.text for m in narrations]}"

    state_updates = _events_of_type(messages, MSG_STATE_UPDATE)
    xp_drops = [s for s in state_updates if getattr(s, "update_type", "") == "xp_awarded"]
    assert not xp_drops, "xp_awarded must not be dropped as StateUpdate"


# ---------------------------------------------------------------------------
# WP-006: level_up_applied event → NarrationEvent
# ---------------------------------------------------------------------------

def test_wp_006_level_up_applied_surfaces_as_narration():
    """WP-006: level_up_applied event → NarrationEvent."""
    bridge = _make_bridge()
    # play_loop.py:1656-1665 — level_up_applied payload
    event = {
        "event_type": "level_up_applied",
        "entity_id": "pc_fighter",
        "old_level": 3,
        "new_level": 4,
        "hp_gained": 8,
    }
    result = _make_stub_result(events=[event])
    messages = bridge._turn_result_to_messages(result, "msg-005")

    narrations = _events_of_type(messages, MSG_NARRATION)
    level_narration = next(
        (m for m in narrations if "4" in m.text or "level" in m.text.lower() or "Level" in m.text),
        None
    )
    assert level_narration is not None, \
        f"level_up_applied must produce NarrationEvent, got: {[m.text for m in narrations]}"

    state_updates = _events_of_type(messages, MSG_STATE_UPDATE)
    lu_drops = [s for s in state_updates if getattr(s, "update_type", "") == "level_up_applied"]
    assert not lu_drops, "level_up_applied must not be dropped as StateUpdate"


# ---------------------------------------------------------------------------
# WP-007: None of the 5 new event types produce a WARNING log
# ---------------------------------------------------------------------------

def test_wp_007_new_event_types_no_warning_log(caplog):
    """WP-007: All 5 new event types route without WARNING log."""
    bridge = _make_bridge()
    events = [
        {"type": "attack_roll", "total": 12, "target_ac": 14, "hit": False},
        {"event_type": "save_rolled", "save_type": "will", "dc": 15, "total": 10, "outcome": "failure"},
        {"type": "condition_applied", "condition": "fascinated", "duration_rounds": None},
        {"event_type": "xp_awarded", "xp_amount": 100},
        {"event_type": "level_up_applied", "new_level": 2},
    ]
    result = _make_stub_result(events=events)

    with caplog.at_level(logging.WARNING, logger="aidm.server.ws_bridge"):
        messages = bridge._turn_result_to_messages(result, "msg-007")

    # None of these event types should produce a WARNING
    new_event_types = {"attack_roll", "save_rolled", "condition_applied", "xp_awarded", "level_up_applied"}
    warning_texts = " ".join(r.getMessage() + str(getattr(r, "args", ())) for r in caplog.records if r.levelno == logging.WARNING)
    for et in new_event_types:
        assert et not in warning_texts, \
            f"Event type '{et}' should not produce a WARNING log after WP fix"


# ---------------------------------------------------------------------------
# WP-008: End-to-end mock: player_utterance → ≥1 NarrationEvent + ≥1 CharacterState
# ---------------------------------------------------------------------------

def test_wp_008_end_to_end_utterance_to_narration_and_character_state():
    """WP-008: player_utterance mock turn → ≥1 NarrationEvent + ≥1 CharacterState in output."""
    session = _make_session_with_player(hp=8, hp_max=20, ac=15)

    # Turn result includes an attack_roll event and a narration
    attack_event = {
        "type": "attack_roll",
        "total": 17,
        "target_ac": 13,
        "hit": True,
    }
    session.process_text_turn = MagicMock(return_value=MagicMock(
        narration_text="Thorin swings his axe!",
        narration_audio=None,
        events=[attack_event],
        clarification_needed=False,
        error_message=None,
        success=True,
    ))

    bridge = _make_bridge(session=session)
    utterance = PlayerUtterance(
        msg_type=MSG_PLAYER_UTTERANCE,
        msg_id=str(uuid.uuid4()),
        timestamp=0.0,
        text="I attack the goblin",
    )

    responses = _run(bridge._handle_utterance(utterance, session))

    narrations = _events_of_type(responses, MSG_NARRATION)
    char_states = _events_of_type(responses, MSG_CHARACTER_STATE)

    assert narrations, "WP-008: Expected ≥1 NarrationEvent in response"
    assert char_states, "WP-008: Expected ≥1 CharacterState in response"

    # Verify NarrationEvent contains the narration text
    main_narration = next((m for m in narrations if "Thorin" in m.text or "axe" in m.text), None)
    assert main_narration is not None, \
        f"Expected NarrationEvent with turn narration, got: {[m.text for m in narrations]}"

    # Verify CharacterState has correct fields
    cs = char_states[0]
    assert isinstance(cs, CharacterState)
    assert cs.name == "Thorin"
    assert cs.hp == 8
    assert cs.hp_max == 20
    assert cs.ac == 15

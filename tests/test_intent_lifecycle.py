"""Tests for Intent lifecycle management.

Tests the INTENT_LIFECYCLE.md contract implementation:
- Status transitions: PENDING → CLARIFYING → CONFIRMED → RESOLVED
- Immutability after CONFIRMED (frozen intent)
- Required field validation per action type
- Serialization/deserialization roundtrip
"""

import pytest
import json
from datetime import datetime

from aidm.schemas.intent_lifecycle import (
    IntentStatus,
    ActionType,
    IntentObject,
    IntentFrozenError,
    IntentTransitionError,
    create_intent_from_input,
)
from aidm.schemas.intents import GridPoint, CastSpellIntent


class TestIntentStatus:
    """Tests for IntentStatus enum."""

    def test_status_values(self):
        """IntentStatus should have correct string values."""
        assert IntentStatus.PENDING.value == "pending"
        assert IntentStatus.CLARIFYING.value == "clarifying"
        assert IntentStatus.CONFIRMED.value == "confirmed"
        assert IntentStatus.RESOLVED.value == "resolved"
        assert IntentStatus.RETRACTED.value == "retracted"


class TestActionType:
    """Tests for ActionType enum."""

    def test_m1_action_types(self):
        """ActionType should include M1 supported types."""
        assert ActionType.ATTACK.value == "attack"
        assert ActionType.MOVE.value == "move"
        assert ActionType.USE_ABILITY.value == "use_ability"
        assert ActionType.END_TURN.value == "end_turn"


class TestIntentObjectCreation:
    """Tests for IntentObject creation and initialization."""

    def test_create_basic_intent(self):
        """Should create intent with default values."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I attack the goblin",
            action_type=ActionType.ATTACK,
        )

        assert intent.actor_id == "fighter_1"
        assert intent.source_text == "I attack the goblin"
        assert intent.action_type == ActionType.ATTACK
        assert intent.status == IntentStatus.PENDING
        assert intent.intent_id is not None
        assert len(intent.intent_id) == 36  # UUID format

    def test_create_intent_factory(self):
        """create_intent_from_input should create PENDING intent."""
        intent = create_intent_from_input(
            actor_id="wizard_1",
            source_text="I cast fireball",
            action_type=ActionType.CAST_SPELL,
            method="fireball",
        )

        assert intent.actor_id == "wizard_1"
        assert intent.status == IntentStatus.PENDING
        assert intent.method == "fireball"

    def test_intent_has_timestamps(self):
        """Intent should have created_at and updated_at timestamps."""
        intent = IntentObject(actor_id="test", source_text="test")

        assert isinstance(intent.created_at, datetime)
        assert isinstance(intent.updated_at, datetime)


class TestRequiredFieldValidation:
    """Tests for has_required_fields() per action type."""

    def test_attack_requires_target_and_method(self):
        """ATTACK action requires target_id and method."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
        )

        assert intent.has_required_fields() is False
        assert "target_id" in intent.get_missing_fields()
        assert "method" in intent.get_missing_fields()

        # Add target_id only
        intent.target_id = "goblin_1"
        assert intent.has_required_fields() is False
        assert "method" in intent.get_missing_fields()

        # Add method - now complete
        intent.method = "longsword"
        assert intent.has_required_fields() is True
        assert len(intent.get_missing_fields()) == 0

    def test_move_requires_target_location(self):
        """MOVE action requires target_location."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I move north",
            action_type=ActionType.MOVE,
        )

        assert intent.has_required_fields() is False
        assert "target_location" in intent.get_missing_fields()

        intent.target_location = GridPoint(x=5, y=10)
        assert intent.has_required_fields() is True

    def test_use_ability_requires_method_and_parameters(self):
        """USE_ABILITY action requires method and parameters."""
        intent = IntentObject(
            actor_id="rogue_1",
            source_text="I use sneak attack",
            action_type=ActionType.USE_ABILITY,
        )

        assert intent.has_required_fields() is False
        assert "method" in intent.get_missing_fields()
        assert "parameters" in intent.get_missing_fields()

        intent.method = "sneak_attack"
        intent.parameters = {"bonus_dice": 2}
        assert intent.has_required_fields() is True

    def test_end_turn_requires_nothing(self):
        """END_TURN action has no additional requirements."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I end my turn",
            action_type=ActionType.END_TURN,
        )

        assert intent.has_required_fields() is True
        assert len(intent.get_missing_fields()) == 0

    def test_requires_actor_id(self):
        """All intents require actor_id."""
        intent = IntentObject(
            source_text="attack",
            action_type=ActionType.END_TURN,
        )

        assert intent.has_required_fields() is False
        assert "actor_id" in intent.get_missing_fields()


class TestStatusTransitions:
    """Tests for status lifecycle transitions."""

    def test_pending_to_clarifying(self):
        """PENDING can transition to CLARIFYING."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
        )

        intent.transition_to(IntentStatus.CLARIFYING)
        assert intent.status == IntentStatus.CLARIFYING

    def test_pending_to_confirmed(self):
        """PENDING can transition to CONFIRMED (freezes intent)."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I attack the goblin with my sword",
            action_type=ActionType.ATTACK,
            target_id="goblin_1",
            method="longsword",
        )

        intent.transition_to(IntentStatus.CONFIRMED)
        assert intent.status == IntentStatus.CONFIRMED
        assert intent.is_frozen is True

    def test_clarifying_to_confirmed(self):
        """CLARIFYING can transition to CONFIRMED."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            status=IntentStatus.CLARIFYING,
        )

        # Add missing fields
        intent.target_id = "goblin_1"
        intent.method = "longsword"

        intent.transition_to(IntentStatus.CONFIRMED)
        assert intent.status == IntentStatus.CONFIRMED

    def test_clarifying_to_retracted(self):
        """CLARIFYING can transition to RETRACTED."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            status=IntentStatus.CLARIFYING,
        )

        intent.transition_to(IntentStatus.RETRACTED)
        assert intent.status == IntentStatus.RETRACTED

    def test_confirmed_to_resolved(self):
        """CONFIRMED can transition to RESOLVED."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I attack the goblin",
            action_type=ActionType.ATTACK,
            target_id="goblin_1",
            method="longsword",
        )
        intent.transition_to(IntentStatus.CONFIRMED)

        intent.transition_to(IntentStatus.RESOLVED)
        assert intent.status == IntentStatus.RESOLVED

    def test_invalid_transition_raises_error(self):
        """Invalid transitions should raise IntentTransitionError."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="test",
            action_type=ActionType.END_TURN,
        )

        # PENDING cannot go directly to RESOLVED
        with pytest.raises(IntentTransitionError, match="Cannot transition"):
            intent.transition_to(IntentStatus.RESOLVED)

        # RETRACTED is now a valid transition from PENDING (player cancellation)
        # Test a different invalid transition instead - CLARIFYING cannot go to PENDING
        clarifying_intent = IntentObject(
            actor_id="fighter_1",
            source_text="test",
            action_type=ActionType.ATTACK,
            status=IntentStatus.CLARIFYING,
        )
        with pytest.raises(IntentTransitionError, match="Cannot transition"):
            clarifying_intent.transition_to(IntentStatus.PENDING)

    def test_terminal_states_cannot_transition(self):
        """RESOLVED and RETRACTED are terminal states."""
        resolved_intent = IntentObject(
            actor_id="fighter_1",
            source_text="test",
            action_type=ActionType.END_TURN,
            status=IntentStatus.RESOLVED,
        )

        with pytest.raises(IntentTransitionError):
            resolved_intent.transition_to(IntentStatus.PENDING)

        retracted_intent = IntentObject(
            actor_id="fighter_1",
            source_text="test",
            action_type=ActionType.END_TURN,
            status=IntentStatus.RETRACTED,
        )

        with pytest.raises(IntentTransitionError):
            retracted_intent.transition_to(IntentStatus.CONFIRMED)


class TestImmutability:
    """Tests for intent immutability after CONFIRMED."""

    def test_freeze_prevents_field_modification(self):
        """Frozen intent should reject field modifications."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            target_id="goblin_1",
            method="longsword",
        )
        intent.transition_to(IntentStatus.CONFIRMED)

        with pytest.raises(IntentFrozenError, match="Cannot modify field"):
            intent.target_id = "goblin_2"

        with pytest.raises(IntentFrozenError, match="Cannot modify field"):
            intent.method = "greatsword"

        with pytest.raises(IntentFrozenError, match="Cannot modify field"):
            intent.source_text = "different text"

    def test_frozen_allows_resolution_fields(self):
        """Frozen intent should allow resolution fields."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
            target_id="goblin_1",
            method="longsword",
        )
        intent.transition_to(IntentStatus.CONFIRMED)

        # These should NOT raise
        intent.result_id = "result_123"
        intent.resolved_at = datetime.utcnow()

        assert intent.result_id == "result_123"
        assert intent.resolved_at is not None

    def test_frozen_status_only_to_resolved(self):
        """Frozen intent status can only change to RESOLVED."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="test",
            action_type=ActionType.END_TURN,
        )
        intent.transition_to(IntentStatus.CONFIRMED)

        with pytest.raises(IntentFrozenError, match="only transition to RESOLVED"):
            intent.status = IntentStatus.PENDING

        # RESOLVED should work
        intent.status = IntentStatus.RESOLVED
        assert intent.status == IntentStatus.RESOLVED

    def test_not_frozen_before_confirmed(self):
        """Intent should not be frozen before CONFIRMED."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
        )

        assert intent.is_frozen is False

        # Should be able to modify
        intent.target_id = "goblin_1"
        intent.method = "longsword"

        assert intent.target_id == "goblin_1"
        assert intent.method == "longsword"


class TestSerialization:
    """Tests for intent serialization/deserialization."""

    def test_to_dict_includes_required_fields(self):
        """to_dict should include all required fields."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I attack the goblin",
            action_type=ActionType.ATTACK,
            target_id="goblin_1",
            method="longsword",
        )

        data = intent.to_dict()

        assert data["intent_id"] == intent.intent_id
        assert data["actor_id"] == "fighter_1"
        assert data["action_type"] == "attack"
        assert data["status"] == "pending"
        assert data["source_text"] == "I attack the goblin"
        assert data["target_id"] == "goblin_1"
        assert data["method"] == "longsword"
        assert "created_at" in data
        assert "updated_at" in data

    def test_to_dict_omits_none_optional_fields(self):
        """to_dict should omit None optional fields."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I end my turn",
            action_type=ActionType.END_TURN,
        )

        data = intent.to_dict()

        assert "target_id" not in data
        assert "target_location" not in data
        assert "method" not in data
        assert "parameters" not in data
        assert "result_id" not in data

    def test_roundtrip_serialization(self):
        """Intent should survive JSON roundtrip."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I attack the goblin with my sword",
            action_type=ActionType.ATTACK,
            target_id="goblin_1",
            method="longsword",
            declared_goal="defeat the enemy",
            parameters={"flanking": True},
        )

        # Serialize to JSON
        json_str = json.dumps(intent.to_dict(), sort_keys=True)

        # Deserialize back
        restored = IntentObject.from_dict(json.loads(json_str))

        assert restored.intent_id == intent.intent_id
        assert restored.actor_id == "fighter_1"
        assert restored.action_type == ActionType.ATTACK
        assert restored.target_id == "goblin_1"
        assert restored.method == "longsword"
        assert restored.declared_goal == "defeat the enemy"
        assert restored.parameters == {"flanking": True}

    def test_roundtrip_with_grid_point(self):
        """Intent with GridPoint should survive roundtrip."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I move north",
            action_type=ActionType.MOVE,
            target_location=GridPoint(x=5, y=10),
        )

        json_str = json.dumps(intent.to_dict())
        restored = IntentObject.from_dict(json.loads(json_str))

        assert restored.target_location.x == 5
        assert restored.target_location.y == 10

    def test_roundtrip_preserves_frozen_state(self):
        """CONFIRMED intent should be frozen after deserialization."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="test",
            action_type=ActionType.END_TURN,
        )
        intent.transition_to(IntentStatus.CONFIRMED)

        json_str = json.dumps(intent.to_dict())
        restored = IntentObject.from_dict(json.loads(json_str))

        assert restored.status == IntentStatus.CONFIRMED
        assert restored.is_frozen is True

        # Should raise on modification attempt
        with pytest.raises(IntentFrozenError):
            restored.source_text = "changed"

    def test_roundtrip_with_action_data(self):
        """Intent with nested action_data should survive roundtrip."""
        spell_intent = CastSpellIntent(spell_name="Fireball", target_mode="point")

        intent = IntentObject(
            actor_id="wizard_1",
            source_text="I cast fireball at the center",
            action_type=ActionType.CAST_SPELL,
            method="fireball",
            target_location=GridPoint(x=10, y=10),
            action_data=spell_intent,
        )

        json_str = json.dumps(intent.to_dict())
        restored = IntentObject.from_dict(json.loads(json_str))

        assert restored.action_data is not None
        assert isinstance(restored.action_data, CastSpellIntent)
        assert restored.action_data.spell_name == "Fireball"
        assert restored.action_data.target_mode == "point"


class TestIsValid:
    """Tests for is_valid() validation."""

    def test_valid_intent(self):
        """Properly constructed intent should be valid."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I attack",
            action_type=ActionType.ATTACK,
        )

        assert intent.is_valid() is True

    def test_invalid_without_intent_id(self):
        """Intent without intent_id should be invalid."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="test",
        )
        intent.intent_id = ""

        assert intent.is_valid() is False

    def test_invalid_without_source_text(self):
        """Intent without source_text should be invalid."""
        intent = IntentObject(
            actor_id="fighter_1",
        )

        assert intent.is_valid() is False


class TestLogFormat:
    """Tests for log-compatible output format per INTENT_LIFECYCLE.md Section 8."""

    def test_log_entry_format(self):
        """to_dict output should match log entry format spec."""
        intent = IntentObject(
            actor_id="fighter_1",
            source_text="I attack the goblin with my sword",
            action_type=ActionType.ATTACK,
            target_id="goblin_3",
            method="longsword",
        )
        intent.transition_to(IntentStatus.CONFIRMED)

        data = intent.to_dict()

        # Per INTENT_LIFECYCLE.md Section 8.2
        assert "intent_id" in data
        assert data["status"] == "confirmed"
        assert data["actor_id"] == "fighter_1"
        assert data["action_type"] == "attack"
        assert data["target_id"] == "goblin_3"
        assert data["method"] == "longsword"
        assert data["source_text"] == "I attack the goblin with my sword"
        assert "created_at" in data
        assert "updated_at" in data

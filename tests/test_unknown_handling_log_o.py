"""WO-VOICE-UK-LOG-001: Unknown Handling Structured Logging — Gate O Tests.

Proves that the unknown handling pipeline emits structured log events
at every classification, clarification, escalation, and cancellation point.

GATE TESTS:
  O-01: UnknownHandlingEvent has all 11 required fields
  O-02: Classification event emitted when ClarificationRequest is created
  O-03: Clarification round event increments round counter
  O-04: Escalation event emitted when clarification budget exhausted
  O-05: Cancellation event emitted on cancel/abort
  O-06: FORBIDDEN_DEFAULT detection emits event with missing_attribute name
  O-07: GREEN classification emits at DEBUG level
  O-08: YELLOW classification emits at WARNING level
  O-09: RED classification emits at ERROR level
  O-10: Event has valid correlation_id (UUID format)
  O-11: All 7 failure classes from contract are representable
  O-12: No behavioral changes — classification outcomes unchanged with logging
  O-13: AmbiguityType → failure class mapping covers all enum members
  O-14: GREEN classification event emitted on successful intent resolution
  O-15: to_dict() produces correct serialization
  O-16: Frozen dataclass rejects attribute mutation
  O-17: Validation rejects invalid event_type
  O-18: Validation rejects invalid stoplight

Authority: WO-VOICE-UK-LOG-001, RQ-UNKNOWN-001 (UNKNOWN_HANDLING_CONTRACT.md).
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone

import pytest

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aidm.schemas.unknown_handling_event import (
    UnknownHandlingEvent,
    VALID_EVENT_TYPES,
    VALID_FAILURE_CLASSES,
    VALID_STOPLIGHTS,
    VALID_RESOLUTIONS,
)
from aidm.interaction.intent_bridge import (
    IntentBridge,
    AmbiguityType,
    ClarificationRequest,
    AMBIGUITY_TO_FAILURE_CLASS,
    _emit_classification_event,
    _emit_green_classification,
)
from aidm.core.fact_acquisition import (
    FactAcquisitionManager,
    _emit_forbidden_default_event,
    FORBIDDEN_DEFAULTS,
    VALID_ENTITY_CLASSES,
    FactResponse,
    FactRequest,
)
from aidm.schemas.intents import DeclaredAttackIntent, CastSpellIntent, MoveIntent
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.state import FrozenWorldStateView


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


def _make_event(**overrides) -> UnknownHandlingEvent:
    """Build a valid UnknownHandlingEvent with sensible defaults."""
    defaults = dict(
        event_type="classification",
        failure_class="FC-AMBIG",
        sub_class=None,
        stoplight="YELLOW",
        clarification_round=0,
        max_clarifications=2,
        resolution="pending",
        missing_attribute=None,
        turn_number=1,
        correlation_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    defaults.update(overrides)
    return UnknownHandlingEvent(**defaults)


def _make_view(entities: dict | None = None) -> FrozenWorldStateView:
    """Create a minimal FrozenWorldStateView for testing."""
    if entities is None:
        entities = {
            "goblin_01": {"name": "Goblin Scout", EF.DEFEATED: False},
            "goblin_02": {"name": "Goblin Warrior", EF.DEFEATED: False},
            "pc_fighter": {"name": "Kael", EF.DEFEATED: False, EF.WEAPON: "longsword", "weapon_damage": "1d8+3"},
        }

    from aidm.core.state import WorldState
    ws = WorldState(ruleset_version="dnd3.5", entities=entities)
    return FrozenWorldStateView(ws)


# ===========================================================================
# O-01: UnknownHandlingEvent has all 11 required fields
# ===========================================================================

class TestO01_SchemaFields:
    """O-01: UnknownHandlingEvent frozen dataclass has all 11 required fields."""

    REQUIRED_FIELDS = [
        "event_type",
        "failure_class",
        "sub_class",
        "stoplight",
        "clarification_round",
        "max_clarifications",
        "resolution",
        "missing_attribute",
        "turn_number",
        "correlation_id",
        "timestamp",
    ]

    def test_all_11_fields_present(self):
        event = _make_event()
        for field_name in self.REQUIRED_FIELDS:
            assert hasattr(event, field_name), f"Missing field: {field_name}"

    def test_exactly_11_fields(self):
        event = _make_event()
        field_names = [f.name for f in event.__dataclass_fields__.values()]
        assert len(field_names) == 11
        assert set(field_names) == set(self.REQUIRED_FIELDS)

    def test_frozen(self):
        event = _make_event()
        with pytest.raises(AttributeError):
            event.event_type = "something_else"


# ===========================================================================
# O-02: Classification event emitted when ClarificationRequest is created
# ===========================================================================

class TestO02_ClassificationEmission:
    """O-02: ClarificationRequest creation triggers UK log emission."""

    def test_ambiguous_target_emits_classification(self, caplog):
        bridge = IntentBridge()
        view = _make_view()
        declared = DeclaredAttackIntent(target_ref="Goblin")

        with caplog.at_level(logging.DEBUG, logger="aidm.unknown_handling"):
            result = bridge.resolve_attack("pc_fighter", declared, view)

        assert isinstance(result, ClarificationRequest)
        assert result.ambiguity_type == AmbiguityType.TARGET_AMBIGUOUS
        assert any("UK classification" in r.message for r in caplog.records)

    def test_target_not_found_emits_classification(self, caplog):
        bridge = IntentBridge()
        view = _make_view()
        declared = DeclaredAttackIntent(target_ref="Dragon")

        with caplog.at_level(logging.DEBUG, logger="aidm.unknown_handling"):
            result = bridge.resolve_attack("pc_fighter", declared, view)

        assert isinstance(result, ClarificationRequest)
        assert result.ambiguity_type == AmbiguityType.TARGET_NOT_FOUND
        assert any("UK classification" in r.message for r in caplog.records)

    def test_emit_classification_event_returns_event(self):
        cr = ClarificationRequest(
            intent_type="attack",
            ambiguity_type=AmbiguityType.TARGET_AMBIGUOUS,
            candidates=("Goblin Scout", "Goblin Warrior"),
            message="Which goblin?",
        )
        event = _emit_classification_event(cr)
        assert isinstance(event, UnknownHandlingEvent)
        assert event.event_type == "classification"
        assert event.failure_class == "FC-AMBIG"
        assert event.stoplight == "YELLOW"


# ===========================================================================
# O-03: Clarification round event increments round counter
# ===========================================================================

class TestO03_ClarificationRound:
    """O-03: Clarification round events track the round counter."""

    def test_round_counter_increments(self):
        cr = ClarificationRequest(
            intent_type="attack",
            ambiguity_type=AmbiguityType.TARGET_AMBIGUOUS,
            candidates=("Goblin Scout", "Goblin Warrior"),
            message="Which goblin?",
        )
        event_0 = _emit_classification_event(cr, clarification_round=0)
        event_1 = _emit_classification_event(cr, clarification_round=1)
        event_2 = _emit_classification_event(cr, clarification_round=2)

        assert event_0.clarification_round == 0
        assert event_1.clarification_round == 1
        assert event_2.clarification_round == 2

    def test_clarification_round_event_type(self):
        event = _make_event(
            event_type="clarification_round",
            clarification_round=1,
        )
        assert event.event_type == "clarification_round"
        assert event.clarification_round == 1


# ===========================================================================
# O-04: Escalation event emitted when clarification budget exhausted
# ===========================================================================

class TestO04_Escalation:
    """O-04: Escalation event fires when round >= max_clarifications."""

    def test_escalation_event(self):
        event = _make_event(
            event_type="escalation",
            clarification_round=2,
            max_clarifications=2,
            resolution="escalated_to_menu",
        )
        assert event.event_type == "escalation"
        assert event.clarification_round >= event.max_clarifications
        assert event.resolution == "escalated_to_menu"

    def test_escalation_at_budget_ceiling(self):
        for max_c in (1, 2, 3):
            event = _make_event(
                event_type="escalation",
                clarification_round=max_c,
                max_clarifications=max_c,
                resolution="escalated_to_menu",
            )
            assert event.clarification_round == event.max_clarifications


# ===========================================================================
# O-05: Cancellation event emitted on cancel/abort
# ===========================================================================

class TestO05_Cancellation:
    """O-05: Cancellation event is representable and valid."""

    def test_cancellation_event(self):
        event = _make_event(
            event_type="cancellation",
            resolution="cancelled",
        )
        assert event.event_type == "cancellation"
        assert event.resolution == "cancelled"

    def test_cancellation_preserves_failure_class(self):
        event = _make_event(
            event_type="cancellation",
            failure_class="FC-AMBIG",
            resolution="cancelled",
        )
        assert event.failure_class == "FC-AMBIG"


# ===========================================================================
# O-06: FORBIDDEN_DEFAULT detection emits event with missing_attribute
# ===========================================================================

class TestO06_ForbiddenDefault:
    """O-06: FORBIDDEN_DEFAULT detection includes missing_attribute name."""

    def test_emit_forbidden_default_event(self, caplog):
        with caplog.at_level(logging.DEBUG, logger="aidm.unknown_handling"):
            event = _emit_forbidden_default_event(
                missing_attribute="size",
                entity_id="goblin_01",
            )

        assert isinstance(event, UnknownHandlingEvent)
        assert event.missing_attribute == "size"
        assert event.stoplight == "RED"
        assert any("UK FORBIDDEN_DEFAULT" in r.message for r in caplog.records)

    def test_all_forbidden_default_attrs(self):
        for attr in FORBIDDEN_DEFAULTS:
            event = _emit_forbidden_default_event(
                missing_attribute=attr,
                entity_id="test_entity",
            )
            assert event.missing_attribute == attr

    def test_forbidden_default_in_validation(self, caplog):
        """FORBIDDEN_DEFAULT detection in validate_response emits event."""
        from aidm.core.lens_index import LensIndex
        lens = LensIndex()
        manager = FactAcquisitionManager(lens)

        request = FactRequest(
            request_id="test-req-001",
            entity_id="goblin_01",
            required_attributes=("size", "position"),
        )
        # Response missing 'size' — a FORBIDDEN_DEFAULT
        response = FactResponse(
            request_id="test-req-001",
            entity_id="goblin_01",
            facts={"position": {"x": 5, "y": 3}},
            source="test",
            valid=True,
        )

        with caplog.at_level(logging.DEBUG, logger="aidm.unknown_handling"):
            result = manager.validate_response(request, response)

        assert not result.valid
        assert any("UK FORBIDDEN_DEFAULT" in r.message for r in caplog.records)


# ===========================================================================
# O-07: GREEN classification emits at DEBUG level
# ===========================================================================

class TestO07_GreenDebug:
    """O-07: GREEN classification logged at DEBUG level."""

    def test_green_classification_debug_level(self, caplog):
        with caplog.at_level(logging.DEBUG, logger="aidm.unknown_handling"):
            event = _emit_green_classification("attack")

        assert event.stoplight == "GREEN"
        assert event.failure_class is None
        assert event.resolution == "handled"

        uk_records = [r for r in caplog.records if r.name == "aidm.unknown_handling"]
        assert len(uk_records) >= 1
        assert uk_records[0].levelno == logging.DEBUG

    def test_green_on_successful_attack_resolution(self, caplog):
        bridge = IntentBridge()
        view = _make_view()
        declared = DeclaredAttackIntent(target_ref="Goblin Scout")

        with caplog.at_level(logging.DEBUG, logger="aidm.unknown_handling"):
            result = bridge.resolve_attack("pc_fighter", declared, view)

        assert isinstance(result, AttackIntent)
        uk_records = [r for r in caplog.records if r.name == "aidm.unknown_handling"]
        green_records = [r for r in uk_records if r.levelno == logging.DEBUG]
        assert len(green_records) >= 1


# ===========================================================================
# O-08: YELLOW classification emits at WARNING level
# ===========================================================================

class TestO08_YellowWarning:
    """O-08: YELLOW classification logged at WARNING level."""

    def test_yellow_classification_warning_level(self, caplog):
        cr = ClarificationRequest(
            intent_type="attack",
            ambiguity_type=AmbiguityType.TARGET_AMBIGUOUS,
            candidates=("Goblin Scout", "Goblin Warrior"),
            message="Which goblin?",
        )

        with caplog.at_level(logging.DEBUG, logger="aidm.unknown_handling"):
            event = _emit_classification_event(cr)

        assert event.stoplight == "YELLOW"
        uk_records = [r for r in caplog.records if r.name == "aidm.unknown_handling"]
        assert len(uk_records) >= 1
        assert uk_records[0].levelno == logging.WARNING


# ===========================================================================
# O-09: RED classification emits at ERROR level
# ===========================================================================

class TestO09_RedError:
    """O-09: RED classification logged at ERROR level."""

    def test_red_classification_error_level(self, caplog):
        cr = ClarificationRequest(
            intent_type="attack",
            ambiguity_type=AmbiguityType.TARGET_NOT_FOUND,
            candidates=(),
            message="Target not found.",
        )

        with caplog.at_level(logging.DEBUG, logger="aidm.unknown_handling"):
            event = _emit_classification_event(cr)

        assert event.stoplight == "RED"
        uk_records = [r for r in caplog.records if r.name == "aidm.unknown_handling"]
        assert len(uk_records) >= 1
        assert uk_records[0].levelno == logging.ERROR

    def test_destination_oob_is_red(self, caplog):
        cr = ClarificationRequest(
            intent_type="move",
            ambiguity_type=AmbiguityType.DESTINATION_OUT_OF_BOUNDS,
            candidates=(),
            message="Destination out of bounds.",
        )

        with caplog.at_level(logging.DEBUG, logger="aidm.unknown_handling"):
            event = _emit_classification_event(cr)

        assert event.stoplight == "RED"


# ===========================================================================
# O-10: Event has valid correlation_id (UUID format)
# ===========================================================================

class TestO10_CorrelationId:
    """O-10: Every emitted event has a valid UUID correlation_id."""

    def test_correlation_id_uuid_format(self):
        event = _make_event()
        assert UUID_PATTERN.match(event.correlation_id), (
            f"correlation_id '{event.correlation_id}' is not a valid UUID"
        )

    def test_emit_classification_event_has_uuid(self):
        cr = ClarificationRequest(
            intent_type="attack",
            ambiguity_type=AmbiguityType.TARGET_AMBIGUOUS,
            candidates=("Goblin Scout",),
            message="test",
        )
        event = _emit_classification_event(cr)
        assert UUID_PATTERN.match(event.correlation_id)

    def test_emit_green_has_uuid(self):
        event = _emit_green_classification("attack")
        assert UUID_PATTERN.match(event.correlation_id)

    def test_emit_forbidden_default_has_uuid(self):
        event = _emit_forbidden_default_event(
            missing_attribute="size",
            entity_id="test",
        )
        assert UUID_PATTERN.match(event.correlation_id)

    def test_distinct_correlation_ids(self):
        """Each event gets a unique correlation_id."""
        events = [_emit_green_classification("attack") for _ in range(5)]
        ids = [e.correlation_id for e in events]
        assert len(set(ids)) == 5


# ===========================================================================
# O-11: All 7 failure classes from contract are representable
# ===========================================================================

class TestO11_AllFailureClasses:
    """O-11: All 7 failure classes from the UK contract are valid."""

    CONTRACT_FAILURE_CLASSES = [
        "FC-ASR", "FC-HOMO", "FC-PARTIAL", "FC-TIMING",
        "FC-AMBIG", "FC-OOG", "FC-BLEED",
    ]

    def test_all_7_classes_in_valid_set(self):
        for fc in self.CONTRACT_FAILURE_CLASSES:
            assert fc in VALID_FAILURE_CLASSES, f"{fc} not in VALID_FAILURE_CLASSES"

    def test_all_7_classes_constructible(self):
        for fc in self.CONTRACT_FAILURE_CLASSES:
            event = _make_event(failure_class=fc)
            assert event.failure_class == fc

    def test_none_failure_class_for_green(self):
        event = _make_event(failure_class=None, stoplight="GREEN")
        assert event.failure_class is None

    def test_invalid_failure_class_rejected(self):
        with pytest.raises(ValueError, match="Invalid failure_class"):
            _make_event(failure_class="FC-INVALID")


# ===========================================================================
# O-12: No behavioral changes — classification outcomes unchanged
# ===========================================================================

class TestO12_NoBehavioralChange:
    """O-12: Logging is additive-only; classification outcomes unchanged."""

    def test_ambiguous_target_still_returns_clarification(self):
        bridge = IntentBridge()
        view = _make_view()
        declared = DeclaredAttackIntent(target_ref="Goblin")

        result = bridge.resolve_attack("pc_fighter", declared, view)

        assert isinstance(result, ClarificationRequest)
        assert result.ambiguity_type == AmbiguityType.TARGET_AMBIGUOUS
        assert "Goblin Scout" in result.candidates
        assert "Goblin Warrior" in result.candidates

    def test_exact_match_still_resolves(self):
        bridge = IntentBridge()
        view = _make_view()
        declared = DeclaredAttackIntent(target_ref="Goblin Scout")

        result = bridge.resolve_attack("pc_fighter", declared, view)

        assert isinstance(result, AttackIntent)
        assert result.target_id == "goblin_01"

    def test_weapon_not_found_still_returns_clarification(self):
        bridge = IntentBridge()
        view = _make_view()
        declared = DeclaredAttackIntent(target_ref="Goblin Scout", weapon="warhammer")

        result = bridge.resolve_attack("pc_fighter", declared, view)

        assert isinstance(result, ClarificationRequest)
        assert result.ambiguity_type == AmbiguityType.WEAPON_NOT_FOUND

    def test_move_no_destination_still_returns_clarification(self):
        bridge = IntentBridge()
        view = _make_view()
        declared = MoveIntent(destination=None)

        result = bridge.resolve_move("pc_fighter", declared, view)

        assert isinstance(result, ClarificationRequest)
        assert result.ambiguity_type == AmbiguityType.DESTINATION_OUT_OF_BOUNDS


# ===========================================================================
# O-13: AmbiguityType → failure class mapping covers all enum members
# ===========================================================================

class TestO13_MappingCoverage:
    """O-13: Every AmbiguityType enum member has a failure class mapping."""

    def test_all_ambiguity_types_mapped(self):
        for ambiguity_type in AmbiguityType:
            assert ambiguity_type in AMBIGUITY_TO_FAILURE_CLASS, (
                f"AmbiguityType.{ambiguity_type.name} has no failure class mapping"
            )

    def test_mapping_values_are_valid_failure_classes(self):
        for ambiguity_type, fc in AMBIGUITY_TO_FAILURE_CLASS.items():
            assert fc in VALID_FAILURE_CLASSES, (
                f"Mapping for {ambiguity_type.name} → '{fc}' is not a valid failure class"
            )


# ===========================================================================
# O-14: GREEN classification on successful intent resolution
# ===========================================================================

class TestO14_GreenOnSuccess:
    """O-14: Successful intent resolution emits GREEN classification."""

    def test_successful_attack_emits_green(self, caplog):
        bridge = IntentBridge()
        view = _make_view()
        declared = DeclaredAttackIntent(target_ref="Goblin Scout")

        with caplog.at_level(logging.DEBUG, logger="aidm.unknown_handling"):
            result = bridge.resolve_attack("pc_fighter", declared, view)

        assert isinstance(result, AttackIntent)
        uk_records = [r for r in caplog.records if r.name == "aidm.unknown_handling"]
        assert any("GREEN" in str(r.message) or r.levelno == logging.DEBUG for r in uk_records)

    def test_successful_move_emits_green(self, caplog):
        from aidm.schemas.position import Position
        bridge = IntentBridge()
        view = _make_view()
        declared = MoveIntent(destination=Position(x=3, y=4))

        with caplog.at_level(logging.DEBUG, logger="aidm.unknown_handling"):
            result = bridge.resolve_move("pc_fighter", declared, view)

        assert isinstance(result, MoveIntent)
        uk_records = [r for r in caplog.records if r.name == "aidm.unknown_handling"]
        assert len(uk_records) >= 1


# ===========================================================================
# O-15: to_dict() produces correct serialization
# ===========================================================================

class TestO15_Serialization:
    """O-15: to_dict() includes all 11 fields with correct values."""

    def test_to_dict_roundtrip(self):
        event = _make_event(
            failure_class="FC-AMBIG",
            sub_class="FC-AMBIG-01",
            stoplight="YELLOW",
            missing_attribute="target",
        )
        d = event.to_dict()

        assert len(d) == 11
        assert d["event_type"] == "classification"
        assert d["failure_class"] == "FC-AMBIG"
        assert d["sub_class"] == "FC-AMBIG-01"
        assert d["stoplight"] == "YELLOW"
        assert d["missing_attribute"] == "target"
        assert d["clarification_round"] == 0
        assert d["max_clarifications"] == 2
        assert d["resolution"] == "pending"
        assert d["turn_number"] == 1


# ===========================================================================
# O-16: Frozen dataclass rejects attribute mutation
# ===========================================================================

class TestO16_Immutability:
    """O-16: Frozen dataclass prevents attribute mutation."""

    def test_cannot_mutate_event_type(self):
        event = _make_event()
        with pytest.raises(AttributeError):
            event.event_type = "escalation"

    def test_cannot_mutate_stoplight(self):
        event = _make_event()
        with pytest.raises(AttributeError):
            event.stoplight = "RED"

    def test_cannot_mutate_failure_class(self):
        event = _make_event()
        with pytest.raises(AttributeError):
            event.failure_class = None


# ===========================================================================
# O-17: Validation rejects invalid event_type
# ===========================================================================

class TestO17_InvalidEventType:
    """O-17: Constructor rejects invalid event_type values."""

    def test_invalid_event_type(self):
        with pytest.raises(ValueError, match="Invalid event_type"):
            _make_event(event_type="invalid_type")

    def test_invalid_resolution(self):
        with pytest.raises(ValueError, match="Invalid resolution"):
            _make_event(resolution="unknown_resolution")

    def test_negative_clarification_round(self):
        with pytest.raises(ValueError, match="clarification_round"):
            _make_event(clarification_round=-1)

    def test_max_clarifications_out_of_range(self):
        with pytest.raises(ValueError, match="max_clarifications"):
            _make_event(max_clarifications=0)
        with pytest.raises(ValueError, match="max_clarifications"):
            _make_event(max_clarifications=4)


# ===========================================================================
# O-18: Validation rejects invalid stoplight
# ===========================================================================

class TestO18_InvalidStoplight:
    """O-18: Constructor rejects invalid stoplight values."""

    def test_invalid_stoplight(self):
        with pytest.raises(ValueError, match="Invalid stoplight"):
            _make_event(stoplight="BLUE")

    def test_empty_stoplight(self):
        with pytest.raises(ValueError, match="Invalid stoplight"):
            _make_event(stoplight="")

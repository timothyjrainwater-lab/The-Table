"""AE Intent Mapping Gate Tests — AE-MAPPING-001 through AE-MAPPING-006.

WO: ENGINE-AE-INTENT-MAPPING-001 (Batch V WO1)
Authority: RAW — PHB p.141 (standard/move action), p.29 (bardic music),
           p.37 (wild shape), p.76 (demoralize).

Verifies that six intents previously falling through to the 'free' default
now correctly map to their PHB-specified action slot types.

AE-MAPPING-001: FullMoveIntent → move
AE-MAPPING-002: FullMoveIntent consumes move slot; standard still available
AE-MAPPING-003: NaturalAttackIntent → standard
AE-MAPPING-004: BardicMusicIntent → standard
AE-MAPPING-005: WildShapeIntent → standard
AE-MAPPING-006: DemoralizeIntent → standard
"""
import aidm.core.action_economy as ae_mod
import pytest


def _reset():
    """Force rebuild of the lazy singleton before each test."""
    ae_mod._ACTION_TYPES = None


# ---------------------------------------------------------------------------
# AE-MAPPING-001: FullMoveIntent → move
# ---------------------------------------------------------------------------

def test_ae_mapping001_full_move_intent_is_move():
    """AE-MAPPING-001: FullMoveIntent must resolve to 'move' action type."""
    _reset()
    from aidm.core.action_economy import get_action_type
    from aidm.schemas.attack import FullMoveIntent
    from aidm.schemas.position import Position

    intent = FullMoveIntent(
        actor_id="actor_a",
        from_pos=Position(x=0, y=0),
        path=[Position(x=1, y=0)],
    )
    result = get_action_type(intent)
    assert result == "move", (
        f"FullMoveIntent must map to 'move' (PHB p.141); got '{result}'"
    )


# ---------------------------------------------------------------------------
# AE-MAPPING-002: FullMoveIntent consumes move slot; standard still available
# ---------------------------------------------------------------------------

def test_ae_mapping002_full_move_consumes_move_slot():
    """AE-MAPPING-002: after consuming 'move', standard is still available."""
    _reset()
    from aidm.core.action_economy import ActionBudget

    budget = ActionBudget.fresh()
    budget.consume("move")
    assert budget.can_use("standard") is True, (
        "standard slot must remain available after consuming move"
    )
    assert budget.can_use("move") is False, (
        "move slot must be spent after consuming it"
    )


# ---------------------------------------------------------------------------
# AE-MAPPING-003: NaturalAttackIntent → standard
# ---------------------------------------------------------------------------

def test_ae_mapping003_natural_attack_intent_is_standard():
    """AE-MAPPING-003: NaturalAttackIntent must resolve to 'standard'."""
    _reset()
    from aidm.core.action_economy import get_action_type
    from aidm.schemas.intents import NaturalAttackIntent

    intent = NaturalAttackIntent()
    result = get_action_type(intent)
    assert result == "standard", (
        f"NaturalAttackIntent must map to 'standard' (PHB p.141); got '{result}'"
    )


# ---------------------------------------------------------------------------
# AE-MAPPING-004: BardicMusicIntent → standard
# ---------------------------------------------------------------------------

def test_ae_mapping004_bardic_music_intent_is_standard():
    """AE-MAPPING-004: BardicMusicIntent must resolve to 'standard'."""
    _reset()
    from aidm.core.action_economy import get_action_type
    from aidm.schemas.intents import BardicMusicIntent

    intent = BardicMusicIntent()
    result = get_action_type(intent)
    assert result == "standard", (
        f"BardicMusicIntent must map to 'standard' (PHB p.29); got '{result}'"
    )


# ---------------------------------------------------------------------------
# AE-MAPPING-005: WildShapeIntent → standard
# ---------------------------------------------------------------------------

def test_ae_mapping005_wild_shape_intent_is_standard():
    """AE-MAPPING-005: WildShapeIntent must resolve to 'standard'."""
    _reset()
    from aidm.core.action_economy import get_action_type
    from aidm.schemas.intents import WildShapeIntent

    intent = WildShapeIntent()
    result = get_action_type(intent)
    assert result == "standard", (
        f"WildShapeIntent must map to 'standard' (PHB p.37); got '{result}'"
    )


# ---------------------------------------------------------------------------
# AE-MAPPING-006: DemoralizeIntent → standard
# ---------------------------------------------------------------------------

def test_ae_mapping006_demoralize_intent_is_standard():
    """AE-MAPPING-006: DemoralizeIntent must resolve to 'standard'."""
    _reset()
    from aidm.core.action_economy import get_action_type
    from aidm.schemas.intents import DemoralizeIntent

    intent = DemoralizeIntent(actor_id="actor_a", target_id="target_b")
    result = get_action_type(intent)
    assert result == "standard", (
        f"DemoralizeIntent must map to 'standard' (PHB p.76); got '{result}'"
    )

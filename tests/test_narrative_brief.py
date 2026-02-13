"""Tests for WO-032: NarrativeBrief — One-Way Valve

Verifies:
- NarrativeBrief contains no internal IDs, raw HP values, entity dicts
- Severity mapping uses HP percentage thresholds
- Entity names resolved from FrozenWorldStateView
- Assembler constructs brief from STP events
- Provenance tagged as [DERIVED] from [BOX] STPs
- Edge cases: no target, missing fields, defeated entities
"""

import pytest

from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.lens.narrative_brief import (
    NarrativeBrief,
    assemble_narrative_brief,
    compute_severity,
    resolve_entity_name,
    get_entity_hp_data,
)


# ══════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_world_state():
    """Sample WorldState with entities."""
    return WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "fighter_1": {
                "name": "Aldric the Bold",
                "hp": 45,
                "hp_max": 50,
            },
            "goblin_1": {
                "name": "Goblin Warrior",
                "hp": 6,
                "hp_max": 10,
            },
            "goblin_2": {
                "name": "Goblin Archer",
                "hp": 0,
                "hp_max": 8,
            },
        },
    )


@pytest.fixture
def frozen_view(sample_world_state):
    """FrozenWorldStateView for testing."""
    return FrozenWorldStateView(sample_world_state)


# ══════════════════════════════════════════════════════════════════════════
# Severity Mapping Tests
# ══════════════════════════════════════════════════════════════════════════


def test_severity_minor():
    """Severity: damage < 20% of max HP → minor."""
    severity = compute_severity(
        damage=5,
        target_hp_before=50,
        target_hp_max=50,
    )
    assert severity == "minor"


def test_severity_moderate():
    """Severity: 20-40% of max HP → moderate."""
    severity = compute_severity(
        damage=15,
        target_hp_before=50,
        target_hp_max=50,
    )
    assert severity == "moderate"


def test_severity_severe():
    """Severity: 40-60% of max HP → severe."""
    severity = compute_severity(
        damage=25,
        target_hp_before=50,
        target_hp_max=50,
    )
    assert severity == "severe"


def test_severity_devastating():
    """Severity: 60-80% of max HP → devastating."""
    severity = compute_severity(
        damage=35,
        target_hp_before=50,
        target_hp_max=50,
    )
    assert severity == "devastating"


def test_severity_lethal_high_damage():
    """Severity: > 80% of max HP → lethal."""
    severity = compute_severity(
        damage=45,
        target_hp_before=50,
        target_hp_max=50,
    )
    assert severity == "lethal"


def test_severity_lethal_defeated():
    """Severity: target defeated → lethal."""
    severity = compute_severity(
        damage=10,
        target_hp_before=10,
        target_hp_max=50,
        target_defeated=True,
    )
    assert severity == "lethal"


def test_severity_zero_max_hp():
    """Severity: max HP = 0 → minor (can't compute)."""
    severity = compute_severity(
        damage=10,
        target_hp_before=0,
        target_hp_max=0,
    )
    assert severity == "minor"


# ══════════════════════════════════════════════════════════════════════════
# Entity Name Resolution Tests
# ══════════════════════════════════════════════════════════════════════════


def test_resolve_entity_name_found(frozen_view):
    """Resolve entity name from FrozenWorldStateView."""
    name = resolve_entity_name("fighter_1", frozen_view)
    assert name == "Aldric the Bold"


def test_resolve_entity_name_fallback(frozen_view):
    """Resolve unknown entity → fallback to ID."""
    name = resolve_entity_name("unknown_entity", frozen_view)
    assert name == "unknown_entity"


def test_get_entity_hp_data_found(frozen_view):
    """Get entity HP data from FrozenWorldStateView."""
    current_hp, max_hp = get_entity_hp_data("fighter_1", frozen_view)
    assert current_hp == 45
    assert max_hp == 50


def test_get_entity_hp_data_not_found(frozen_view):
    """Get HP data for unknown entity → (0, 0)."""
    current_hp, max_hp = get_entity_hp_data("unknown_entity", frozen_view)
    assert current_hp == 0
    assert max_hp == 0


# ══════════════════════════════════════════════════════════════════════════
# NarrativeBrief Assembly Tests
# ══════════════════════════════════════════════════════════════════════════


def test_assemble_attack_hit(frozen_view):
    """Assemble brief from attack_hit event."""
    events = [
        {
            "event_id": 1,
            "type": "attack_roll",
            "attacker": "fighter_1",
            "target": "goblin_1",
            "weapon": "longsword",
        },
        {
            "event_id": 2,
            "type": "damage_dealt",
            "attacker": "fighter_1",
            "target": "goblin_1",
            "damage": 4,
            "damage_type": "slashing",
        },
    ]

    brief = assemble_narrative_brief(
        events=events,
        narration_token="attack_hit",
        frozen_view=frozen_view,
    )

    assert brief.action_type == "attack_hit"
    assert brief.actor_name == "Aldric the Bold"
    assert brief.target_name == "Goblin Warrior"
    assert brief.weapon_name == "longsword"
    assert brief.damage_type == "slashing"
    assert brief.severity == "severe"  # 4/10 = 40%
    assert not brief.target_defeated
    assert brief.provenance_tag == "[DERIVED]"
    assert brief.source_event_ids == (1, 2)


def test_assemble_attack_miss(frozen_view):
    """Assemble brief from attack_miss event."""
    events = [
        {
            "event_id": 3,
            "type": "attack_roll",
            "attacker": "fighter_1",
            "target": "goblin_1",
            "weapon": "longsword",
        },
    ]

    brief = assemble_narrative_brief(
        events=events,
        narration_token="attack_miss",
        frozen_view=frozen_view,
    )

    assert brief.action_type == "attack_miss"
    assert brief.actor_name == "Aldric the Bold"
    assert brief.target_name == "Goblin Warrior"
    assert brief.weapon_name == "longsword"
    assert brief.severity == "minor"  # No damage
    assert not brief.target_defeated


def test_assemble_target_defeated(frozen_view):
    """Assemble brief with target defeated."""
    events = [
        {
            "event_id": 4,
            "type": "damage_dealt",
            "attacker": "fighter_1",
            "target": "goblin_2",
            "damage": 8,
        },
        {
            "event_id": 5,
            "type": "entity_defeated",
            "target": "goblin_2",
        },
    ]

    brief = assemble_narrative_brief(
        events=events,
        narration_token="attack_hit",
        frozen_view=frozen_view,
    )

    assert brief.target_defeated
    assert brief.severity == "lethal"


def test_assemble_condition_applied(frozen_view):
    """Assemble brief with condition applied."""
    events = [
        {
            "event_id": 6,
            "type": "condition_applied",
            "target": "goblin_1",
            "condition": "prone",
        },
    ]

    brief = assemble_narrative_brief(
        events=events,
        narration_token="trip_success",
        frozen_view=frozen_view,
    )

    assert brief.condition_applied == "prone"
    assert brief.target_name == "Goblin Warrior"


def test_assemble_hp_changed_event(frozen_view):
    """Assemble brief from hp_changed event."""
    events = [
        {
            "event_id": 7,
            "type": "hp_changed",
            "payload": {
                "entity_id": "goblin_1",
                "delta": -3,
            },
        },
    ]

    brief = assemble_narrative_brief(
        events=events,
        narration_token="damage_applied",
        frozen_view=frozen_view,
    )

    assert brief.severity == "moderate"  # 3/10 = 30%


def test_assemble_no_target(frozen_view):
    """Assemble brief with no target (e.g., movement)."""
    events = [
        {
            "event_id": 8,
            "type": "movement_declared",
        },
    ]

    brief = assemble_narrative_brief(
        events=events,
        narration_token="movement_stub",
        frozen_view=frozen_view,
    )

    assert brief.target_name is None
    assert brief.actor_name == "someone"  # No actor ID


def test_assemble_with_previous_narrations(frozen_view):
    """Assemble brief with previous narrations for continuity."""
    events = [
        {
            "event_id": 9,
            "type": "attack_roll",
            "attacker": "fighter_1",
            "target": "goblin_1",
        },
    ]

    previous_narrations = [
        "The goblin charges forward!",
        "Aldric readies his blade.",
    ]

    brief = assemble_narrative_brief(
        events=events,
        narration_token="attack_hit",
        frozen_view=frozen_view,
        previous_narrations=previous_narrations,
    )

    assert brief.previous_narrations == tuple(previous_narrations)


def test_assemble_with_scene_description(frozen_view):
    """Assemble brief with scene description."""
    events = [
        {
            "event_id": 10,
            "type": "attack_roll",
            "attacker": "fighter_1",
            "target": "goblin_1",
        },
    ]

    scene = "A dimly lit dungeon corridor"

    brief = assemble_narrative_brief(
        events=events,
        narration_token="attack_hit",
        frozen_view=frozen_view,
        scene_description=scene,
    )

    assert brief.scene_description == scene


# ══════════════════════════════════════════════════════════════════════════
# NarrativeBrief Serialization Tests
# ══════════════════════════════════════════════════════════════════════════


def test_narrative_brief_to_dict():
    """Serialize NarrativeBrief to dict."""
    brief = NarrativeBrief(
        action_type="attack_hit",
        actor_name="Aldric",
        target_name="Goblin",
        outcome_summary="Aldric hits Goblin with longsword",
        severity="moderate",
        weapon_name="longsword",
    )

    data = brief.to_dict()

    assert data["action_type"] == "attack_hit"
    assert data["actor_name"] == "Aldric"
    assert data["target_name"] == "Goblin"
    assert data["severity"] == "moderate"
    assert data["weapon_name"] == "longsword"


def test_narrative_brief_from_dict():
    """Deserialize NarrativeBrief from dict."""
    data = {
        "action_type": "attack_hit",
        "actor_name": "Aldric",
        "target_name": "Goblin",
        "outcome_summary": "Aldric hits Goblin",
        "severity": "severe",
    }

    brief = NarrativeBrief.from_dict(data)

    assert brief.action_type == "attack_hit"
    assert brief.actor_name == "Aldric"
    assert brief.target_name == "Goblin"
    assert brief.severity == "severe"


# ══════════════════════════════════════════════════════════════════════════
# Containment Boundary Tests (BL-020, Axiom 5)
# ══════════════════════════════════════════════════════════════════════════


def test_no_internal_ids_in_brief():
    """NarrativeBrief must not contain entity IDs."""
    brief = NarrativeBrief(
        action_type="attack_hit",
        actor_name="Aldric",
        target_name="Goblin",
    )

    # Check all fields
    data = brief.to_dict()

    # No field should contain entity IDs like "fighter_1" or "goblin_1"
    for value in data.values():
        if isinstance(value, str):
            assert "fighter_1" not in value
            assert "goblin_1" not in value


def test_no_raw_hp_values_in_brief():
    """NarrativeBrief must not contain raw HP values."""
    brief = NarrativeBrief(
        action_type="attack_hit",
        actor_name="Aldric",
        target_name="Goblin",
        severity="moderate",
    )

    # Check all fields
    data = brief.to_dict()

    # No field should be named "hp" or "hp_max"
    assert "hp" not in data
    assert "hp_max" not in data
    assert "current_hp" not in data


def test_severity_not_numeric():
    """Severity must be category string, not numeric HP."""
    brief = NarrativeBrief(
        action_type="attack_hit",
        actor_name="Aldric",
        target_name="Goblin",
        severity="severe",
    )

    # Severity must be one of the allowed categories
    assert brief.severity in ["minor", "moderate", "severe", "devastating", "lethal"]


def test_frozen_view_read_only(frozen_view):
    """FrozenWorldStateView must be read-only (BL-020)."""
    from aidm.core.state import WorldStateImmutabilityError

    # Cannot modify entities
    with pytest.raises((WorldStateImmutabilityError, TypeError)):
        frozen_view.entities = {}

    # Cannot modify nested entity data
    with pytest.raises(TypeError):
        frozen_view.entities["fighter_1"]["hp"] = 0

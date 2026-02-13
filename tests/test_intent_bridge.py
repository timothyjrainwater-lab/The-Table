"""Tests for Intent Bridge (WO-038).

Validates translation from player-facing declared intents (string names)
to engine-facing resolved intents (entity IDs, Weapon objects).

Test Categories:
- Entity name resolution (exact, partial, ambiguous, not found)
- Weapon resolution (named, default, unknown)
- Spell resolution (spell registry lookup)
- Move intent validation
"""

import pytest
from aidm.interaction.intent_bridge import (
    IntentBridge, ClarificationRequest, AmbiguityType
)
from aidm.schemas.intents import DeclaredAttackIntent, CastSpellIntent, MoveIntent
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.position import Position
from aidm.core.spell_resolver import SpellCastIntent
from aidm.core.state import WorldState, FrozenWorldStateView
from aidm.schemas.entity_fields import EF


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def simple_world_state() -> WorldState:
    """Create a simple world state with fighter and single goblin."""
    return WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "pc_fighter": {
                EF.ENTITY_ID: "pc_fighter",
                "name": "Kael the Fighter",
                EF.TEAM: "party",
                EF.HP_CURRENT: 10,
                EF.HP_MAX: 10,
                EF.AC: 16,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 3,
                EF.BAB: 1,
                EF.STR_MOD: 2,
                EF.WEAPON: "longsword",
                "weapon_damage": "1d8+2",
            },
            "goblin_1": {
                EF.ENTITY_ID: "goblin_1",
                "name": "Goblin Warrior",
                EF.TEAM: "enemy",
                EF.HP_CURRENT: 6,
                EF.HP_MAX: 6,
                EF.AC: 15,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 2,
                EF.BAB: 1,
                EF.STR_MOD: 0,
                EF.WEAPON: "shortsword",
                "weapon_damage": "1d6",
            },
        },
    )


@pytest.fixture
def multi_goblin_state() -> WorldState:
    """World state with multiple goblins (for ambiguity tests)."""
    return WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "pc_fighter": {
                EF.ENTITY_ID: "pc_fighter",
                "name": "Kael",
                EF.TEAM: "party",
                EF.HP_CURRENT: 10,
                EF.HP_MAX: 10,
                EF.AC: 16,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 3,
                EF.WEAPON: "longsword",
                "weapon_damage": "1d8+2",
            },
            "goblin_1": {
                EF.ENTITY_ID: "goblin_1",
                "name": "Goblin Warrior",
                EF.TEAM: "enemy",
                EF.HP_CURRENT: 6,
                EF.HP_MAX: 6,
                EF.AC: 15,
                EF.DEFEATED: False,
            },
            "goblin_2": {
                EF.ENTITY_ID: "goblin_2",
                "name": "Goblin Scout",
                EF.TEAM: "enemy",
                EF.HP_CURRENT: 5,
                EF.HP_MAX: 5,
                EF.AC: 14,
                EF.DEFEATED: False,
            },
            "goblin_3": {
                EF.ENTITY_ID: "goblin_3",
                "name": "Goblin Archer",
                EF.TEAM: "enemy",
                EF.HP_CURRENT: 4,
                EF.HP_MAX: 4,
                EF.AC: 13,
                EF.DEFEATED: False,
            },
        },
    )


@pytest.fixture
def defeated_entity_state() -> WorldState:
    """World state with a defeated entity."""
    return WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "pc_fighter": {
                EF.ENTITY_ID: "pc_fighter",
                "name": "Kael",
                EF.TEAM: "party",
                EF.HP_CURRENT: 10,
                EF.HP_MAX: 10,
                EF.DEFEATED: False,
                EF.ATTACK_BONUS: 3,
            },
            "goblin_alive": {
                EF.ENTITY_ID: "goblin_alive",
                "name": "Goblin Warrior",
                EF.TEAM: "enemy",
                EF.HP_CURRENT: 6,
                EF.HP_MAX: 6,
                EF.DEFEATED: False,
            },
            "goblin_dead": {
                EF.ENTITY_ID: "goblin_dead",
                "name": "Goblin Scout",
                EF.TEAM: "enemy",
                EF.HP_CURRENT: 0,
                EF.HP_MAX: 5,
                EF.DEFEATED: True,
            },
        },
    )


@pytest.fixture
def bridge() -> IntentBridge:
    """Create IntentBridge instance."""
    return IntentBridge()


# ==============================================================================
# TESTS: ENTITY NAME RESOLUTION
# ==============================================================================

def test_exact_name_match_resolves_entity_id(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Exact entity name match resolves to entity_id.

    Citations:
        None (bridge design)
    """
    view = FrozenWorldStateView(simple_world_state)
    declared = DeclaredAttackIntent(target_ref="Goblin Warrior")

    result = bridge.resolve_attack("pc_fighter", declared, view)

    assert isinstance(result, AttackIntent)
    assert result.target_id == "goblin_1"
    assert result.attacker_id == "pc_fighter"


def test_partial_name_match_with_single_candidate(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Partial name match with single candidate resolves to entity_id."""
    view = FrozenWorldStateView(simple_world_state)
    declared = DeclaredAttackIntent(target_ref="Goblin")

    result = bridge.resolve_attack("pc_fighter", declared, view)

    assert isinstance(result, AttackIntent)
    assert result.target_id == "goblin_1"


def test_ambiguous_partial_match_returns_clarification(
    bridge: IntentBridge,
    multi_goblin_state: WorldState,
):
    """Partial match with multiple candidates returns ClarificationRequest."""
    view = FrozenWorldStateView(multi_goblin_state)
    declared = DeclaredAttackIntent(target_ref="Goblin")

    result = bridge.resolve_attack("pc_fighter", declared, view)

    assert isinstance(result, ClarificationRequest)
    assert result.ambiguity_type == AmbiguityType.TARGET_AMBIGUOUS
    assert len(result.candidates) == 3
    assert "Goblin Warrior" in result.candidates
    assert "Goblin Scout" in result.candidates
    assert "Goblin Archer" in result.candidates


def test_unknown_target_returns_error_with_available_targets(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Unknown target name returns ClarificationRequest with available targets."""
    view = FrozenWorldStateView(simple_world_state)
    declared = DeclaredAttackIntent(target_ref="Dragon")

    result = bridge.resolve_attack("pc_fighter", declared, view)

    assert isinstance(result, ClarificationRequest)
    assert result.ambiguity_type == AmbiguityType.TARGET_NOT_FOUND
    assert "Goblin Warrior" in result.candidates


def test_defeated_entities_excluded_from_targeting(
    bridge: IntentBridge,
    defeated_entity_state: WorldState,
):
    """Defeated entities are not included in target resolution."""
    view = FrozenWorldStateView(defeated_entity_state)
    declared = DeclaredAttackIntent(target_ref="Goblin Scout")

    result = bridge.resolve_attack("pc_fighter", declared, view)

    # Should not match defeated goblin
    assert isinstance(result, ClarificationRequest)
    assert result.ambiguity_type == AmbiguityType.TARGET_NOT_FOUND


def test_case_insensitive_name_matching(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Entity name matching is case-insensitive."""
    view = FrozenWorldStateView(simple_world_state)
    declared = DeclaredAttackIntent(target_ref="goblin warrior")

    result = bridge.resolve_attack("pc_fighter", declared, view)

    assert isinstance(result, AttackIntent)
    assert result.target_id == "goblin_1"


def test_empty_target_ref_returns_available_targets(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Empty target_ref returns ClarificationRequest with available targets."""
    view = FrozenWorldStateView(simple_world_state)
    declared = DeclaredAttackIntent(target_ref="")

    result = bridge.resolve_attack("pc_fighter", declared, view)

    assert isinstance(result, ClarificationRequest)
    assert result.ambiguity_type == AmbiguityType.TARGET_NOT_FOUND
    assert "Goblin Warrior" in result.candidates


# ==============================================================================
# TESTS: WEAPON RESOLUTION
# ==============================================================================

def test_named_weapon_resolves_to_weapon_object(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Named weapon resolves to Weapon object with correct stats."""
    view = FrozenWorldStateView(simple_world_state)
    declared = DeclaredAttackIntent(
        target_ref="Goblin Warrior",
        weapon="longsword",
    )

    result = bridge.resolve_attack("pc_fighter", declared, view)

    assert isinstance(result, AttackIntent)
    assert isinstance(result.weapon, Weapon)
    assert result.weapon.damage_dice == "1d8"
    assert result.weapon.damage_bonus == 2
    assert result.weapon.damage_type == "slashing"


def test_no_weapon_specified_uses_default(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """No weapon specified uses entity's default weapon."""
    view = FrozenWorldStateView(simple_world_state)
    declared = DeclaredAttackIntent(target_ref="Goblin Warrior")

    result = bridge.resolve_attack("pc_fighter", declared, view)

    assert isinstance(result, AttackIntent)
    assert result.weapon.damage_dice == "1d8"
    assert result.weapon.damage_type == "slashing"


def test_unknown_weapon_returns_clarification(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Unknown weapon returns ClarificationRequest with available weapons."""
    view = FrozenWorldStateView(simple_world_state)
    declared = DeclaredAttackIntent(
        target_ref="Goblin Warrior",
        weapon="greatsword",
    )

    result = bridge.resolve_attack("pc_fighter", declared, view)

    assert isinstance(result, ClarificationRequest)
    assert result.ambiguity_type == AmbiguityType.WEAPON_NOT_FOUND
    assert "longsword" in result.candidates


def test_unarmed_strike_when_no_weapon(
    bridge: IntentBridge,
):
    """Entity with no weapon uses unarmed strike."""
    state = WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "monk": {
                EF.ENTITY_ID: "monk",
                "name": "Li Wei",
                EF.TEAM: "party",
                EF.ATTACK_BONUS: 2,
                EF.BAB: 1,
                EF.STR_MOD: 1,
                EF.DEFEATED: False,
            },
            "goblin": {
                EF.ENTITY_ID: "goblin",
                "name": "Goblin",
                EF.TEAM: "enemy",
                EF.DEFEATED: False,
            },
        },
    )

    view = FrozenWorldStateView(state)
    declared = DeclaredAttackIntent(target_ref="Goblin")

    result = bridge.resolve_attack("monk", declared, view)

    assert isinstance(result, AttackIntent)
    assert result.weapon.damage_dice == "1d3"
    assert result.weapon.damage_type == "bludgeoning"


def test_weapon_damage_type_inference(
    bridge: IntentBridge,
):
    """Weapon damage type is inferred from weapon name."""
    state = WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "pc": {
                EF.ENTITY_ID: "pc",
                "name": "Fighter",
                EF.TEAM: "party",
                EF.ATTACK_BONUS: 3,
                EF.WEAPON: "spear",
                "weapon_damage": "1d8",
                EF.DEFEATED: False,
            },
            "goblin": {
                EF.ENTITY_ID: "goblin",
                "name": "Goblin",
                EF.TEAM: "enemy",
                EF.DEFEATED: False,
            },
        },
    )

    view = FrozenWorldStateView(state)
    declared = DeclaredAttackIntent(target_ref="Goblin", weapon="spear")

    result = bridge.resolve_attack("pc", declared, view)

    assert isinstance(result, AttackIntent)
    assert result.weapon.damage_type == "piercing"


# ==============================================================================
# TESTS: ATTACK BONUS CALCULATION
# ==============================================================================

def test_attack_bonus_from_entity_field(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Attack bonus comes from entity's ATTACK_BONUS field."""
    view = FrozenWorldStateView(simple_world_state)
    declared = DeclaredAttackIntent(target_ref="Goblin Warrior")

    result = bridge.resolve_attack("pc_fighter", declared, view)

    assert isinstance(result, AttackIntent)
    assert result.attack_bonus == 3


def test_attack_bonus_fallback_to_bab_plus_str(
    bridge: IntentBridge,
):
    """Attack bonus falls back to BAB + STR_MOD if ATTACK_BONUS not set."""
    state = WorldState(
        ruleset_version="RAW_3.5",
        entities={
            "pc": {
                EF.ENTITY_ID: "pc",
                "name": "Fighter",
                EF.TEAM: "party",
                EF.BAB: 3,
                EF.STR_MOD: 2,
                EF.WEAPON: "longsword",
                "weapon_damage": "1d8",
                EF.DEFEATED: False,
            },
            "goblin": {
                EF.ENTITY_ID: "goblin",
                "name": "Goblin",
                EF.TEAM: "enemy",
                EF.DEFEATED: False,
            },
        },
    )

    view = FrozenWorldStateView(state)
    declared = DeclaredAttackIntent(target_ref="Goblin")

    result = bridge.resolve_attack("pc", declared, view)

    assert isinstance(result, AttackIntent)
    assert result.attack_bonus == 5  # BAB 3 + STR 2


# ==============================================================================
# TESTS: SPELL RESOLUTION
# ==============================================================================

def test_spell_name_resolves_to_spell_id(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Spell name resolves to spell_id from SPELL_REGISTRY."""
    view = FrozenWorldStateView(simple_world_state)
    declared = CastSpellIntent(spell_name="fireball")

    result = bridge.resolve_spell("pc_fighter", declared, view)

    assert isinstance(result, SpellCastIntent)
    assert result.spell_id == "fireball"
    assert result.caster_id == "pc_fighter"


def test_spell_with_target_entity(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Spell with target entity resolves entity name to entity_id."""
    view = FrozenWorldStateView(simple_world_state)
    declared = CastSpellIntent(spell_name="magic_missile")

    result = bridge.resolve_spell(
        "pc_fighter",
        declared,
        view,
        target_entity_ref="Goblin Warrior",
    )

    assert isinstance(result, SpellCastIntent)
    assert result.target_entity_id == "goblin_1"


def test_spell_with_target_position(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Spell with target position includes position in SpellCastIntent."""
    view = FrozenWorldStateView(simple_world_state)
    declared = CastSpellIntent(spell_name="fireball")
    target_pos = Position(x=10, y=5)

    result = bridge.resolve_spell(
        "pc_fighter",
        declared,
        view,
        target_position=target_pos,
    )

    assert isinstance(result, SpellCastIntent)
    assert result.target_position == target_pos


def test_unknown_spell_returns_clarification(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Unknown spell name returns ClarificationRequest."""
    view = FrozenWorldStateView(simple_world_state)
    declared = CastSpellIntent(spell_name="unknown_spell")

    result = bridge.resolve_spell("pc_fighter", declared, view)

    assert isinstance(result, ClarificationRequest)
    assert result.ambiguity_type == AmbiguityType.SPELL_NOT_FOUND


def test_empty_spell_name_returns_available_spells(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Empty spell name returns ClarificationRequest with available spells."""
    view = FrozenWorldStateView(simple_world_state)
    declared = CastSpellIntent(spell_name="")

    result = bridge.resolve_spell("pc_fighter", declared, view)

    assert isinstance(result, ClarificationRequest)
    assert result.ambiguity_type == AmbiguityType.SPELL_NOT_FOUND
    assert len(result.candidates) > 0


def test_spell_name_case_insensitive(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Spell name matching is case-insensitive."""
    view = FrozenWorldStateView(simple_world_state)
    declared = CastSpellIntent(spell_name="FIREBALL")

    result = bridge.resolve_spell("pc_fighter", declared, view)

    assert isinstance(result, SpellCastIntent)
    assert result.spell_id == "fireball"


# ==============================================================================
# TESTS: MOVE INTENT VALIDATION
# ==============================================================================

def test_move_intent_with_destination(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Move intent with destination is validated successfully."""
    view = FrozenWorldStateView(simple_world_state)
    destination = Position(x=5, y=5)
    declared = MoveIntent(destination=destination)

    result = bridge.resolve_move("pc_fighter", declared, view)

    assert isinstance(result, MoveIntent)
    assert result.destination == destination


def test_move_intent_without_destination_returns_clarification(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """Move intent without destination returns ClarificationRequest."""
    view = FrozenWorldStateView(simple_world_state)
    declared = MoveIntent(destination=None)

    result = bridge.resolve_move("pc_fighter", declared, view)

    assert isinstance(result, ClarificationRequest)
    assert result.ambiguity_type == AmbiguityType.DESTINATION_OUT_OF_BOUNDS


# ==============================================================================
# TESTS: CLARIFICATION REQUEST STRUCTURE
# ==============================================================================

def test_clarification_request_has_intent_type(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """ClarificationRequest includes intent_type field."""
    view = FrozenWorldStateView(simple_world_state)
    declared = DeclaredAttackIntent(target_ref="Unknown")

    result = bridge.resolve_attack("pc_fighter", declared, view)

    assert isinstance(result, ClarificationRequest)
    assert result.intent_type == "attack"


def test_clarification_request_has_human_readable_message(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """ClarificationRequest includes human-readable message."""
    view = FrozenWorldStateView(simple_world_state)
    declared = DeclaredAttackIntent(target_ref="Dragon")

    result = bridge.resolve_attack("pc_fighter", declared, view)

    assert isinstance(result, ClarificationRequest)
    assert "not found" in result.message.lower()
    assert len(result.message) > 0


def test_clarification_request_immutable(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """ClarificationRequest is frozen (immutable)."""
    view = FrozenWorldStateView(simple_world_state)
    declared = DeclaredAttackIntent(target_ref="Unknown")

    result = bridge.resolve_attack("pc_fighter", declared, view)

    assert isinstance(result, ClarificationRequest)

    # Should raise error on mutation attempt
    with pytest.raises((AttributeError, TypeError)):
        result.message = "New message"


# ==============================================================================
# TESTS: BOUNDARY LAW COMPLIANCE
# ==============================================================================

def test_bridge_uses_frozen_world_state_view(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """IntentBridge uses FrozenWorldStateView (BL-020 compliance).

    Citations:
        BL-020: WorldState immutability at non-engine boundaries
    """
    view = FrozenWorldStateView(simple_world_state)
    declared = DeclaredAttackIntent(target_ref="Goblin Warrior")

    # Should accept FrozenWorldStateView
    result = bridge.resolve_attack("pc_fighter", declared, view)

    assert isinstance(result, AttackIntent)


def test_bridge_does_not_mutate_world_state(
    bridge: IntentBridge,
    simple_world_state: WorldState,
):
    """IntentBridge does not mutate world state (BL-020 compliance)."""
    view = FrozenWorldStateView(simple_world_state)
    declared = DeclaredAttackIntent(target_ref="Goblin Warrior")

    # Get initial hash
    initial_hash = simple_world_state.state_hash()

    # Resolve attack
    result = bridge.resolve_attack("pc_fighter", declared, view)

    # Hash should be unchanged
    assert simple_world_state.state_hash() == initial_hash
    assert isinstance(result, AttackIntent)

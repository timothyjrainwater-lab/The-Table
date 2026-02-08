"""Unit tests for CP-18A Mounted Combat core functionality.

Tests rider-mount coupling, position derivation, dismount, and attack bonuses.

Tier-1 (MUST PASS):
- MountedState creation and serialization
- Position derivation (rider at mount position)
- Coupling validation (bidirectional references)
- Higher ground bonus calculation
- Single attack restriction when mount moves

Tier-2 (SHOULD PASS):
- Voluntary dismount
- Forced dismount (mount defeated)
- Unconscious rider saddle check
- Mount intent resolution
"""

import pytest
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import GridPosition
from aidm.schemas.mounted_combat import (
    MountedState, MountType, SaddleType,
    MountedMoveIntent, DismountIntent, MountIntent
)
from aidm.schemas.entity_fields import EF
from aidm.core.mounted_combat import (
    get_entity_position, is_mounted, get_rider_for_mount,
    validate_mounted_coupling, resolve_mount, resolve_dismount,
    trigger_forced_dismount, check_unconscious_fall,
    get_mounted_attack_bonus, can_rider_full_attack,
    handle_mounted_condition_change
)


# ==============================================================================
# TIER 1: MUST-PASS TESTS — Schema & Position Derivation
# ==============================================================================

def test_mounted_state_creation():
    """Tier 1: MountedState can be created and serialized."""
    state = MountedState(
        mount_id="warhorse_1",
        is_controlled=True,
        saddle_type=SaddleType.MILITARY,
        mounted_at_event_id=5
    )

    assert state.mount_id == "warhorse_1"
    assert state.is_controlled is True
    assert state.saddle_type == SaddleType.MILITARY
    assert state.mounted_at_event_id == 5

    # Roundtrip serialization
    data = state.to_dict()
    restored = MountedState.from_dict(data)
    assert restored.mount_id == state.mount_id
    assert restored.is_controlled == state.is_controlled
    assert restored.saddle_type == state.saddle_type
    assert restored.mounted_at_event_id == state.mounted_at_event_id


def test_position_derivation_mounted_rider():
    """Tier 1: Mounted rider position is derived from mount."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {
                    "mount_id": "warhorse_1",
                    "is_controlled": True,
                    "saddle_type": SaddleType.RIDING
                },
                EF.HP_CURRENT: 30,
                "team": "party"
            },
            "warhorse_1": {
                EF.POSITION: {"x": 5, "y": 5},
                EF.RIDER_ID: "fighter",
                EF.HP_CURRENT: 20,
                EF.MOUNT_SIZE: "large",
                EF.IS_MOUNT_TRAINED: True,
                "team": "party"
            }
        }
    )

    # Rider position should be mount's position
    rider_pos = get_entity_position("fighter", world_state)
    mount_pos = get_entity_position("warhorse_1", world_state)

    assert rider_pos == GridPosition(x=5, y=5)
    assert mount_pos == GridPosition(x=5, y=5)
    assert rider_pos == mount_pos


def test_position_derivation_unmounted_entity():
    """Tier 1: Unmounted entity uses own position."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.POSITION: {"x": 3, "y": 7},
                EF.HP_CURRENT: 30,
                "team": "party"
            }
        }
    )

    pos = get_entity_position("fighter", world_state)
    assert pos == GridPosition(x=3, y=7)


def test_is_mounted_check():
    """Tier 1: is_mounted returns correct status."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {
                    "mount_id": "warhorse_1",
                    "is_controlled": True
                }
            },
            "rogue": {
                EF.HP_CURRENT: 20
            },
            "warhorse_1": {
                EF.RIDER_ID: "fighter"
            }
        }
    )

    assert is_mounted("fighter", world_state) is True
    assert is_mounted("rogue", world_state) is False
    assert is_mounted("warhorse_1", world_state) is False


def test_get_rider_for_mount():
    """Tier 1: get_rider_for_mount returns correct rider ID."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {"mount_id": "warhorse_1", "is_controlled": True}
            },
            "warhorse_1": {
                EF.RIDER_ID: "fighter"
            },
            "riderless_horse": {
                EF.HP_CURRENT: 15
            }
        }
    )

    assert get_rider_for_mount("warhorse_1", world_state) == "fighter"
    assert get_rider_for_mount("riderless_horse", world_state) is None


def test_coupling_validation_valid():
    """Tier 1: Valid coupling passes validation."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {"mount_id": "warhorse_1", "is_controlled": True}
            },
            "warhorse_1": {
                EF.RIDER_ID: "fighter"
            }
        }
    )

    assert validate_mounted_coupling(world_state) is True


def test_coupling_validation_missing_backref():
    """Tier 1: Missing backref fails validation."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {"mount_id": "warhorse_1", "is_controlled": True}
            },
            "warhorse_1": {
                # Missing RIDER_ID
                EF.HP_CURRENT: 20
            }
        }
    )

    assert validate_mounted_coupling(world_state) is False


def test_coupling_validation_orphan_rider_id():
    """Tier 1: Orphan rider_id fails validation."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                # No MOUNTED_STATE
                EF.HP_CURRENT: 30
            },
            "warhorse_1": {
                EF.RIDER_ID: "fighter"  # Claims rider but rider doesn't know
            }
        }
    )

    assert validate_mounted_coupling(world_state) is False


# ==============================================================================
# TIER 1: MUST-PASS TESTS — Attack Bonuses
# ==============================================================================

def test_higher_ground_bonus_mounted_vs_smaller():
    """Tier 1: +1 bonus when mounted on Large mount vs Medium on-foot target."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {"mount_id": "warhorse_1", "is_controlled": True}
            },
            "warhorse_1": {
                EF.RIDER_ID: "fighter",
                EF.MOUNT_SIZE: "large"
            },
            "goblin": {
                "size": "medium",
                EF.HP_CURRENT: 5
            }
        }
    )

    bonus = get_mounted_attack_bonus("fighter", "goblin", world_state)
    assert bonus == 1  # +1 higher ground


def test_higher_ground_no_bonus_vs_mounted():
    """Tier 1: No bonus when target is also mounted."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {"mount_id": "warhorse_1", "is_controlled": True}
            },
            "warhorse_1": {
                EF.RIDER_ID: "fighter",
                EF.MOUNT_SIZE: "large"
            },
            "enemy_knight": {
                EF.MOUNTED_STATE: {"mount_id": "warhorse_2", "is_controlled": True}
            },
            "warhorse_2": {
                EF.RIDER_ID: "enemy_knight",
                EF.MOUNT_SIZE: "large"
            }
        }
    )

    bonus = get_mounted_attack_bonus("fighter", "enemy_knight", world_state)
    assert bonus == 0  # No bonus vs mounted target


def test_higher_ground_no_bonus_vs_larger():
    """Tier 1: No bonus when target is same size or larger than mount."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {"mount_id": "warhorse_1", "is_controlled": True}
            },
            "warhorse_1": {
                EF.RIDER_ID: "fighter",
                EF.MOUNT_SIZE: "large"
            },
            "ogre": {
                "size": "large",  # Same size as mount
                EF.HP_CURRENT: 30
            }
        }
    )

    bonus = get_mounted_attack_bonus("fighter", "ogre", world_state)
    assert bonus == 0  # No bonus vs equal or larger


def test_higher_ground_no_bonus_unmounted():
    """Tier 1: No bonus when attacker is not mounted."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.HP_CURRENT: 30  # Not mounted
            },
            "goblin": {
                "size": "small",
                EF.HP_CURRENT: 5
            }
        }
    )

    bonus = get_mounted_attack_bonus("fighter", "goblin", world_state)
    assert bonus == 0


def test_single_attack_restriction_no_movement():
    """Tier 1: Full attack allowed when mount moves 0-5 feet."""
    assert can_rider_full_attack(0) is True
    assert can_rider_full_attack(5) is True


def test_single_attack_restriction_with_movement():
    """Tier 1: Only single attack when mount moves more than 5 feet."""
    assert can_rider_full_attack(10) is False
    assert can_rider_full_attack(30) is False


# ==============================================================================
# TIER 2: SHOULD-PASS TESTS — Mounting/Dismounting
# ==============================================================================

def test_resolve_mount():
    """Tier 2: Mounting creates correct coupling state."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.POSITION: {"x": 5, "y": 5},
                EF.HP_CURRENT: 30,
                "team": "party"
            },
            "warhorse_1": {
                EF.POSITION: {"x": 5, "y": 5},
                EF.HP_CURRENT: 20,
                EF.IS_MOUNT_TRAINED: True,
                "team": "party"
            }
        }
    )

    intent = MountIntent(
        rider_id="fighter",
        mount_id="warhorse_1",
        saddle_type=SaddleType.MILITARY
    )

    new_state, events = resolve_mount(intent, world_state, next_event_id=0, timestamp=1.0)

    # Check events
    assert len(events) == 1
    assert events[0].event_type == "rider_mounted"

    # Check state
    rider = new_state.entities["fighter"]
    mount = new_state.entities["warhorse_1"]

    assert EF.MOUNTED_STATE in rider
    assert rider[EF.MOUNTED_STATE]["mount_id"] == "warhorse_1"
    assert rider[EF.MOUNTED_STATE]["is_controlled"] is True  # War-trained
    assert rider[EF.MOUNTED_STATE]["saddle_type"] == SaddleType.MILITARY

    assert mount[EF.RIDER_ID] == "fighter"

    # Validate coupling
    assert validate_mounted_coupling(new_state) is True


def test_resolve_dismount_voluntary():
    """Tier 2: Voluntary dismount clears coupling state."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {
                    "mount_id": "warhorse_1",
                    "is_controlled": True,
                    "saddle_type": SaddleType.RIDING
                },
                EF.HP_CURRENT: 30,
                "team": "party"
            },
            "warhorse_1": {
                EF.POSITION: {"x": 5, "y": 5},
                EF.RIDER_ID: "fighter",
                EF.HP_CURRENT: 20,
                "team": "party"
            }
        }
    )

    intent = DismountIntent(rider_id="fighter")

    new_state, events = resolve_dismount(intent, world_state, next_event_id=0, timestamp=1.0)

    # Check events
    assert len(events) == 1
    assert events[0].event_type == "rider_dismounted"
    assert events[0].payload["voluntary"] is True

    # Check state
    rider = new_state.entities["fighter"]
    mount = new_state.entities["warhorse_1"]

    assert EF.MOUNTED_STATE not in rider
    assert EF.RIDER_ID not in mount
    assert rider[EF.POSITION] is not None  # Rider has own position now

    # Validate no broken coupling
    assert validate_mounted_coupling(new_state) is True


def test_forced_dismount_mount_defeated():
    """Tier 2: Mount defeat triggers forced dismount with fall check."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {
                    "mount_id": "warhorse_1",
                    "is_controlled": True,
                    "saddle_type": SaddleType.RIDING
                },
                EF.HP_CURRENT: 30,
                "team": "party"
            },
            "warhorse_1": {
                EF.POSITION: {"x": 5, "y": 5},
                EF.RIDER_ID: "fighter",
                EF.HP_CURRENT: 0,  # Defeated
                EF.DEFEATED: True,
                "team": "party"
            }
        }
    )

    rng = RNGManager(master_seed=42)

    new_state, events = trigger_forced_dismount(
        rider_id="fighter",
        mount_id="warhorse_1",
        reason="mount_defeated",
        world_state=world_state,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Check events
    event_types = [e.event_type for e in events]
    assert "ride_check" in event_types
    assert "rider_dismounted" in event_types

    # Check dismount event
    dismount_event = [e for e in events if e.event_type == "rider_dismounted"][0]
    assert dismount_event.payload["voluntary"] is False
    assert dismount_event.payload["reason"] == "mount_defeated"

    # Check state
    rider = new_state.entities["fighter"]
    assert EF.MOUNTED_STATE not in rider


def test_unconscious_fall_military_saddle():
    """Tier 2: Military saddle gives 75% stay chance."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {
                    "mount_id": "warhorse_1",
                    "is_controlled": True,
                    "saddle_type": SaddleType.MILITARY
                },
                EF.HP_CURRENT: 30,
                "team": "party"
            },
            "warhorse_1": {
                EF.POSITION: {"x": 5, "y": 5},
                EF.RIDER_ID: "fighter",
                EF.HP_CURRENT: 20,
                "team": "party"
            }
        }
    )

    mounted_state_data = world_state.entities["fighter"][EF.MOUNTED_STATE]

    # Use a seed that rolls low (stays mounted)
    rng = RNGManager(master_seed=42)

    new_state, events = check_unconscious_fall(
        rider_id="fighter",
        mounted_state_data=mounted_state_data,
        world_state=world_state,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Check saddle check event
    check_event = events[0]
    assert check_event.event_type == "unconscious_saddle_check"
    assert check_event.payload["stay_chance_percent"] == 75  # Military saddle


# ==============================================================================
# TIER 2: SHOULD-PASS TESTS — Condition Coupling
# ==============================================================================

def test_condition_mount_prone_dismounts_rider():
    """Tier 2: Mount going prone triggers rider dismount."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {
                    "mount_id": "warhorse_1",
                    "is_controlled": True,
                    "saddle_type": SaddleType.RIDING
                },
                EF.HP_CURRENT: 30,
                "team": "party"
            },
            "warhorse_1": {
                EF.POSITION: {"x": 5, "y": 5},
                EF.RIDER_ID: "fighter",
                EF.HP_CURRENT: 20,
                "team": "party"
            }
        }
    )

    rng = RNGManager(master_seed=42)

    new_state, events = handle_mounted_condition_change(
        entity_id="warhorse_1",
        condition_type="prone",
        condition_applied=True,
        world_state=world_state,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Should have triggered dismount
    event_types = [e.event_type for e in events]
    assert "ride_check" in event_types
    assert "rider_dismounted" in event_types

    # Check rider is dismounted
    rider = new_state.entities["fighter"]
    assert EF.MOUNTED_STATE not in rider


def test_condition_rider_unconscious_checks_fall():
    """Tier 2: Rider going unconscious triggers saddle check."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {
                    "mount_id": "warhorse_1",
                    "is_controlled": True,
                    "saddle_type": SaddleType.RIDING
                },
                EF.HP_CURRENT: 0,
                "team": "party"
            },
            "warhorse_1": {
                EF.POSITION: {"x": 5, "y": 5},
                EF.RIDER_ID: "fighter",
                EF.HP_CURRENT: 20,
                "team": "party"
            }
        }
    )

    rng = RNGManager(master_seed=42)

    new_state, events = handle_mounted_condition_change(
        entity_id="fighter",
        condition_type="unconscious",
        condition_applied=True,
        world_state=world_state,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Should have unconscious saddle check
    assert events[0].event_type == "unconscious_saddle_check"


# ==============================================================================
# TIER 2: SHOULD-PASS TESTS — Intent Validation
# ==============================================================================

def test_mounted_move_intent_validation():
    """Tier 2: MountedMoveIntent validates required fields."""
    from_pos = GridPosition(x=5, y=5)
    to_pos = GridPosition(x=7, y=5)

    intent = MountedMoveIntent(
        rider_id="fighter",
        mount_id="warhorse_1",
        from_pos=from_pos,
        to_pos=to_pos
    )

    assert intent.rider_id == "fighter"
    assert intent.mount_id == "warhorse_1"
    assert intent.from_pos == from_pos
    assert intent.to_pos == to_pos
    assert intent.is_charge is False
    assert intent.is_run is False


def test_mounted_move_intent_rejects_empty_rider():
    """Tier 2: MountedMoveIntent rejects empty rider_id."""
    with pytest.raises(ValueError, match="rider_id cannot be empty"):
        MountedMoveIntent(
            rider_id="",
            mount_id="warhorse_1",
            from_pos=GridPosition(x=5, y=5),
            to_pos=GridPosition(x=6, y=5)
        )


def test_dismount_intent_validation():
    """Tier 2: DismountIntent validates required fields."""
    intent = DismountIntent(rider_id="fighter", fast_dismount=True)

    assert intent.rider_id == "fighter"
    assert intent.fast_dismount is True


def test_dismount_intent_rejects_empty_rider():
    """Tier 2: DismountIntent rejects empty rider_id."""
    with pytest.raises(ValueError, match="rider_id cannot be empty"):
        DismountIntent(rider_id="")

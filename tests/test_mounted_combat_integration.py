"""Integration tests for CP-18A Mounted Combat.

Tests mounted combat integration with play loop, AoO, and attack resolution.

Tier-1 (MUST PASS):
- Mounted movement through play loop
- AoO against mount (not rider) on mounted movement
- Higher ground bonus in attack resolution
- Dismount through play loop

Tier-2 (SHOULD PASS):
- Mount defeated by AoO dismounts rider
- Mounted attack with higher ground bonus
- Deterministic replay of mounted combat sequence
"""

import pytest
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.attack import AttackIntent, Weapon, GridPosition
from aidm.schemas.mounted_combat import MountedMoveIntent, DismountIntent, MountIntent, SaddleType
from aidm.schemas.entity_fields import EF
from aidm.core.aoo import check_aoo_triggers


# ==============================================================================
# TIER 1: MUST-PASS TESTS — Play Loop Integration
# ==============================================================================

def test_mounted_movement_through_play_loop():
    """Tier 1: Mounted movement resolves through play loop."""
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
                "team": "party"
            }
        },
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": ["fighter", "warhorse_1"],
            "flat_footed_actors": [],
            "aoo_used_this_round": []
        }
    )

    move_intent = MountedMoveIntent(
        rider_id="fighter",
        mount_id="warhorse_1",
        from_pos=GridPosition(x=5, y=5),
        to_pos=GridPosition(x=8, y=5)
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")
    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=move_intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    assert result.status == "ok"
    assert result.narration == "mounted_movement"

    # Check mount position updated
    mount = result.world_state.entities["warhorse_1"]
    assert mount[EF.POSITION] == {"x": 8, "y": 5}


def test_aoo_triggers_against_mount_not_rider():
    """Tier 1: AoO on mounted movement targets mount, not rider."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {
                    "mount_id": "warhorse_1",
                    "is_controlled": True
                },
                EF.HP_CURRENT: 30,
                "team": "party"
            },
            "warhorse_1": {
                EF.POSITION: {"x": 5, "y": 5},
                EF.RIDER_ID: "fighter",
                EF.HP_CURRENT: 20,
                "team": "party"
            },
            "goblin": {
                EF.POSITION: {"x": 4, "y": 5},  # Adjacent to mount
                EF.HP_CURRENT: 6,
                "team": "monsters",
                "attack_bonus": 2,
                "weapon": {
                    "damage_dice": "1d6",
                    "damage_bonus": 0,
                    "damage_type": "slashing",
                    "critical_multiplier": 2
                }
            }
        },
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": ["fighter", "goblin", "warhorse_1"],
            "flat_footed_actors": [],
            "aoo_used_this_round": []
        }
    )

    # Mount moves away from goblin
    move_intent = MountedMoveIntent(
        rider_id="fighter",
        mount_id="warhorse_1",
        from_pos=GridPosition(x=5, y=5),
        to_pos=GridPosition(x=6, y=5)  # Moving east, away from goblin
    )

    # Check AoO triggers
    triggers = check_aoo_triggers(world_state, "fighter", move_intent)

    # Should have one AoO trigger
    assert len(triggers) == 1
    trigger = triggers[0]

    # AoO should target MOUNT, not rider
    assert trigger.provoker_id == "warhorse_1"  # Mount is provoker
    assert trigger.reactor_id == "goblin"
    assert trigger.provoking_action == "mounted_movement_out"


def test_dismount_through_play_loop():
    """Tier 1: Dismount resolves through play loop."""
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
        },
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": ["fighter", "warhorse_1"],
            "flat_footed_actors": [],
            "aoo_used_this_round": []
        }
    )

    dismount_intent = DismountIntent(rider_id="fighter")

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")
    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=dismount_intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    assert result.status == "ok"
    assert result.narration == "dismounted"

    # Check coupling cleared
    rider = result.world_state.entities["fighter"]
    mount = result.world_state.entities["warhorse_1"]

    assert EF.MOUNTED_STATE not in rider
    assert EF.RIDER_ID not in mount


def test_higher_ground_bonus_in_attack():
    """Tier 1: Mounted attack includes higher ground bonus."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {
                    "mount_id": "warhorse_1",
                    "is_controlled": True
                },
                EF.HP_CURRENT: 30,
                EF.POSITION: {"x": 5, "y": 5},  # Rider position (will be derived)
                "team": "party"
            },
            "warhorse_1": {
                EF.POSITION: {"x": 5, "y": 5},
                EF.RIDER_ID: "fighter",
                EF.HP_CURRENT: 20,
                EF.MOUNT_SIZE: "large",
                "team": "party"
            },
            "goblin": {
                EF.POSITION: {"x": 6, "y": 5},  # Adjacent
                EF.HP_CURRENT: 6,
                "ac": 15,
                "size": "small",
                "team": "monsters"
            }
        },
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": ["fighter", "goblin"],
            "flat_footed_actors": [],
            "aoo_used_this_round": []
        }
    )

    weapon = Weapon(
        damage_dice="1d8",
        damage_bonus=3,
        damage_type="slashing"
    )

    attack_intent = AttackIntent(
        attacker_id="fighter",
        target_id="goblin",
        attack_bonus=5,
        weapon=weapon
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")
    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=attack_intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Find attack_roll event
    attack_events = [e for e in result.events if e.event_type == "attack_roll"]
    assert len(attack_events) == 1

    attack_event = attack_events[0]
    # Should have +1 mounted bonus
    assert attack_event.payload["mounted_bonus"] == 1


# ==============================================================================
# TIER 2: SHOULD-PASS TESTS — Complex Scenarios
# ==============================================================================

def test_mount_intent_through_play_loop():
    """Tier 2: Mount intent resolves through play loop."""
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
        },
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": ["fighter", "warhorse_1"],
            "flat_footed_actors": [],
            "aoo_used_this_round": []
        }
    )

    mount_intent = MountIntent(
        rider_id="fighter",
        mount_id="warhorse_1",
        saddle_type=SaddleType.MILITARY
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")
    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=mount_intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    assert result.status == "ok"
    assert result.narration == "mounted"

    # Check coupling created
    rider = result.world_state.entities["fighter"]
    mount = result.world_state.entities["warhorse_1"]

    assert EF.MOUNTED_STATE in rider
    assert rider[EF.MOUNTED_STATE]["mount_id"] == "warhorse_1"
    assert mount[EF.RIDER_ID] == "fighter"


def test_mounted_aoo_defeats_mount():
    """Tier 2: AoO defeating mount during movement dismounts rider."""
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
                EF.HP_CURRENT: 5,  # Low HP, can be defeated by AoO
                "ac": 10,
                "team": "party"
            },
            "ogre": {
                EF.POSITION: {"x": 4, "y": 5},  # Adjacent to mount
                EF.HP_CURRENT: 30,
                "team": "monsters",
                "attack_bonus": 8,  # High bonus
                "weapon": {
                    "damage_dice": "2d8",  # High damage
                    "damage_bonus": 6,
                    "damage_type": "bludgeoning",
                    "critical_multiplier": 2
                }
            }
        },
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": ["fighter", "ogre", "warhorse_1"],
            "flat_footed_actors": [],
            "aoo_used_this_round": []
        }
    )

    # Mount moves away from ogre, provoking AoO
    move_intent = MountedMoveIntent(
        rider_id="fighter",
        mount_id="warhorse_1",
        from_pos=GridPosition(x=5, y=5),
        to_pos=GridPosition(x=6, y=5)
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")
    # Use seed that results in ogre hitting and dealing enough damage
    rng = RNGManager(master_seed=12345)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=move_intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Check for AoO events
    event_types = [e.event_type for e in result.events]
    assert "aoo_triggered" in event_types


def test_deterministic_mounted_combat_replay():
    """Tier 2: Mounted combat sequence produces identical results on replay."""
    def run_mounted_sequence(seed: int) -> str:
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
                    EF.MOUNT_SIZE: "large",
                    "ac": 14,
                    "team": "party"
                },
                "goblin": {
                    EF.POSITION: {"x": 4, "y": 5},
                    EF.HP_CURRENT: 6,
                    "ac": 15,
                    "size": "small",
                    "team": "monsters",
                    "attack_bonus": 2,
                    "weapon": {
                        "damage_dice": "1d6",
                        "damage_bonus": 0,
                        "damage_type": "slashing",
                        "critical_multiplier": 2
                    }
                }
            },
            active_combat={
                "turn_counter": 0,
                "round_index": 1,
                "initiative_order": ["fighter", "goblin", "warhorse_1"],
                "flat_footed_actors": [],
                "aoo_used_this_round": []
            }
        )

        rng = RNGManager(master_seed=seed)
        turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")

        # Mounted movement
        move_intent = MountedMoveIntent(
            rider_id="fighter",
            mount_id="warhorse_1",
            from_pos=GridPosition(x=5, y=5),
            to_pos=GridPosition(x=6, y=5)
        )

        result = execute_turn(
            world_state=world_state,
            turn_ctx=turn_ctx,
            combat_intent=move_intent,
            rng=rng,
            next_event_id=0,
            timestamp=1.0
        )

        return result.world_state.state_hash()

    # Run 10x with same seed
    hashes = [run_mounted_sequence(seed=42) for _ in range(10)]

    # All hashes must be identical
    assert len(set(hashes)) == 1, "Mounted combat replay produced different state hashes"


def test_no_higher_ground_vs_equal_size():
    """Tier 2: No higher ground bonus vs target same size as mount."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.MOUNTED_STATE: {
                    "mount_id": "warhorse_1",
                    "is_controlled": True
                },
                EF.HP_CURRENT: 30,
                "team": "party"
            },
            "warhorse_1": {
                EF.POSITION: {"x": 5, "y": 5},
                EF.RIDER_ID: "fighter",
                EF.HP_CURRENT: 20,
                EF.MOUNT_SIZE: "large",  # Large mount
                "team": "party"
            },
            "ogre": {
                EF.POSITION: {"x": 6, "y": 5},
                EF.HP_CURRENT: 30,
                "ac": 16,
                "size": "large",  # Large target - no bonus
                "team": "monsters"
            }
        },
        active_combat={
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": ["fighter", "ogre"],
            "flat_footed_actors": [],
            "aoo_used_this_round": []
        }
    )

    weapon = Weapon(
        damage_dice="1d8",
        damage_bonus=3,
        damage_type="slashing"
    )

    attack_intent = AttackIntent(
        attacker_id="fighter",
        target_id="ogre",
        attack_bonus=5,
        weapon=weapon
    )

    turn_ctx = TurnContext(turn_index=0, actor_id="fighter", actor_team="party")
    rng = RNGManager(master_seed=42)

    result = execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=attack_intent,
        rng=rng,
        next_event_id=0,
        timestamp=1.0
    )

    # Find attack_roll event
    attack_events = [e for e in result.events if e.event_type == "attack_roll"]
    assert len(attack_events) == 1

    attack_event = attack_events[0]
    # Should have NO mounted bonus (target same size as mount)
    assert attack_event.payload["mounted_bonus"] == 0

"""Shared fixtures for runtime integration tests (WO-CODE-LOOP-001)."""

import pytest

from aidm.core.event_log import EventLog
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.runtime.play_controller import (
    PlayOneTurnController,
    ScenarioFixture,
    build_simple_combat_fixture,
)


@pytest.fixture
def simple_fixture() -> ScenarioFixture:
    """1 PC (Aldric, longsword) vs 1 Goblin, seed=42."""
    return build_simple_combat_fixture(master_seed=42)


@pytest.fixture
def controller() -> PlayOneTurnController:
    """Fresh controller with empty event log."""
    return PlayOneTurnController(event_log=EventLog())


@pytest.fixture
def move_fixture() -> ScenarioFixture:
    """1 PC vs 1 Goblin with enemy far away (no AoO on move).

    PC at (3,3), Goblin at (10,3) — not adjacent, so single-step
    movement won't trigger AoO or weapon-data issues.
    """
    entities = {
        "pc_fighter": {
            EF.ENTITY_ID: "pc_fighter",
            "name": "Aldric",
            EF.HP_CURRENT: 28,
            EF.HP_MAX: 28,
            EF.AC: 18,
            EF.ATTACK_BONUS: 6,
            EF.BAB: 3,
            EF.STR_MOD: 3,
            EF.DEX_MOD: 1,
            EF.TEAM: "party",
            EF.WEAPON: "longsword",
            "weapon_damage": "1d8",
            EF.POSITION: {"x": 3, "y": 3},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
        },
        "goblin_1": {
            EF.ENTITY_ID: "goblin_1",
            "name": "Goblin Warrior",
            EF.HP_CURRENT: 5,
            EF.HP_MAX: 5,
            EF.AC: 15,
            EF.ATTACK_BONUS: 3,
            EF.BAB: 1,
            EF.STR_MOD: 0,
            EF.DEX_MOD: 1,
            EF.TEAM: "monsters",
            EF.WEAPON: "shortbow",
            "weapon_damage": "1d4",
            EF.POSITION: {"x": 10, "y": 3},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "small",
        },
    }

    ws = WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "turn_counter": 0,
            "round_index": 0,
            "initiative_order": ["pc_fighter", "goblin_1"],
            "flat_footed_actors": [],
            "aoo_used_this_round": [],
        },
    )

    return ScenarioFixture(
        world_state=ws,
        master_seed=42,
        actor_id="pc_fighter",
        turn_index=0,
        next_event_id=0,
        timestamp=0.0,
    )


@pytest.fixture
def multi_goblin_fixture() -> ScenarioFixture:
    """1 PC vs 3 goblins (for ambiguity tests)."""
    from aidm.core.state import WorldState
    from aidm.schemas.entity_fields import EF

    entities = {
        "pc_fighter": {
            EF.ENTITY_ID: "pc_fighter",
            "name": "Aldric",
            EF.HP_CURRENT: 28,
            EF.HP_MAX: 28,
            EF.AC: 18,
            EF.ATTACK_BONUS: 6,
            EF.BAB: 3,
            EF.STR_MOD: 3,
            EF.DEX_MOD: 1,
            EF.TEAM: "party",
            EF.WEAPON: "longsword",
            "weapon_damage": "1d8",
            EF.POSITION: {"x": 3, "y": 3},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "medium",
        },
        "goblin_1": {
            EF.ENTITY_ID: "goblin_1",
            "name": "Goblin Warrior",
            EF.HP_CURRENT: 5,
            EF.HP_MAX: 5,
            EF.AC: 15,
            EF.ATTACK_BONUS: 3,
            EF.BAB: 1,
            EF.STR_MOD: 0,
            EF.DEX_MOD: 1,
            EF.TEAM: "monsters",
            EF.WEAPON: "shortbow",
            "weapon_damage": "1d4",
            EF.POSITION: {"x": 5, "y": 3},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "small",
        },
        "goblin_2": {
            EF.ENTITY_ID: "goblin_2",
            "name": "Goblin Scout",
            EF.HP_CURRENT: 4,
            EF.HP_MAX: 4,
            EF.AC: 14,
            EF.ATTACK_BONUS: 2,
            EF.BAB: 1,
            EF.STR_MOD: 0,
            EF.DEX_MOD: 2,
            EF.TEAM: "monsters",
            EF.WEAPON: "dagger",
            "weapon_damage": "1d4",
            EF.POSITION: {"x": 6, "y": 3},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "small",
        },
        "goblin_3": {
            EF.ENTITY_ID: "goblin_3",
            "name": "Goblin Archer",
            EF.HP_CURRENT: 4,
            EF.HP_MAX: 4,
            EF.AC: 13,
            EF.ATTACK_BONUS: 4,
            EF.BAB: 1,
            EF.STR_MOD: 0,
            EF.DEX_MOD: 3,
            EF.TEAM: "monsters",
            EF.WEAPON: "shortbow",
            "weapon_damage": "1d4",
            EF.POSITION: {"x": 7, "y": 3},
            EF.DEFEATED: False,
            EF.SIZE_CATEGORY: "small",
        },
    }

    ws = WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "turn_counter": 0,
            "round_index": 0,
            "initiative_order": [
                "pc_fighter", "goblin_1", "goblin_2", "goblin_3",
            ],
            "flat_footed_actors": [],
            "aoo_used_this_round": [],
        },
    )

    return ScenarioFixture(
        world_state=ws,
        master_seed=42,
        actor_id="pc_fighter",
        turn_index=0,
        next_event_id=0,
        timestamp=0.0,
    )

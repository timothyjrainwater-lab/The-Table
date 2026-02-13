"""Integration test fixtures for multi-encounter stress tests.

Provides pre-configured scenario fixtures and shared test utilities.

WO-016: Multi-Encounter Stress Test Suite
"""

import pytest
from typing import List

from aidm.schemas.testing import (
    ScenarioConfig, CombatantConfig, TerrainPlacement, AttackConfig,
    SpellConfig, CoverDegree,
)
from aidm.schemas.position import Position
from aidm.testing.scenario_runner import ScenarioRunner


# ==============================================================================
# HELPER FUNCTIONS — Build common configurations
# ==============================================================================

def create_melee_fighter(
    name: str,
    team: str,
    position: Position,
    hp: int = 45,
    ac: int = 18,
    attack_bonus: int = 8,
) -> CombatantConfig:
    """Create a standard melee fighter combatant."""
    return CombatantConfig(
        name=name,
        team=team,
        position=position,
        size="Medium",
        hp=hp,
        ac=ac,
        attacks=[
            AttackConfig(
                name="longsword",
                attack_bonus=attack_bonus,
                damage_dice="1d8",
                damage_bonus=4,
                damage_type="slashing",
                is_ranged=False,
                critical_range=19,
                critical_multiplier=2,
            )
        ],
        reach=5,
        initiative_bonus=2,
        bab=6,
        str_mod=4,
        dex_mod=2,
        con_mod=2,
        save_fort=5,
        save_ref=3,
        save_will=2,
    )


def create_archer(
    name: str,
    team: str,
    position: Position,
    hp: int = 32,
    ac: int = 16,
    attack_bonus: int = 7,
) -> CombatantConfig:
    """Create a ranged archer combatant."""
    return CombatantConfig(
        name=name,
        team=team,
        position=position,
        size="Medium",
        hp=hp,
        ac=ac,
        attacks=[
            AttackConfig(
                name="longbow",
                attack_bonus=attack_bonus,
                damage_dice="1d8",
                damage_bonus=2,
                damage_type="piercing",
                is_ranged=True,
                range_increment=100,
                critical_multiplier=3,
            )
        ],
        reach=5,
        initiative_bonus=4,
        bab=5,
        str_mod=2,
        dex_mod=4,
        con_mod=1,
        save_fort=3,
        save_ref=6,
        save_will=2,
    )


def create_rogue(
    name: str,
    team: str,
    position: Position,
    hp: int = 28,
    ac: int = 17,
    attack_bonus: int = 6,
) -> CombatantConfig:
    """Create a rogue combatant."""
    return CombatantConfig(
        name=name,
        team=team,
        position=position,
        size="Medium",
        hp=hp,
        ac=ac,
        attacks=[
            AttackConfig(
                name="short_sword",
                attack_bonus=attack_bonus,
                damage_dice="1d6",
                damage_bonus=3,
                damage_type="piercing",
                is_ranged=False,
                critical_range=19,
            )
        ],
        reach=5,
        initiative_bonus=5,
        bab=4,
        str_mod=1,
        dex_mod=5,
        con_mod=1,
        save_fort=2,
        save_ref=7,
        save_will=2,
    )


def create_wizard(
    name: str,
    team: str,
    position: Position,
    hp: int = 18,
    ac: int = 12,
) -> CombatantConfig:
    """Create a spellcaster combatant."""
    return CombatantConfig(
        name=name,
        team=team,
        position=position,
        size="Medium",
        hp=hp,
        ac=ac,
        attacks=[
            AttackConfig(
                name="quarterstaff",
                attack_bonus=1,
                damage_dice="1d6",
                damage_bonus=0,
                damage_type="bludgeoning",
                is_ranged=False,
            )
        ],
        spells=[
            SpellConfig(
                spell_id="magic_missile",
                spell_level=1,
                caster_level=5,
                dc=14,
                uses_remaining=3,
            ),
            SpellConfig(
                spell_id="fireball",
                spell_level=3,
                caster_level=5,
                dc=16,
                uses_remaining=1,
                is_aoe=True,
                aoe_shape="burst",
                aoe_radius_ft=20,
            ),
            SpellConfig(
                spell_id="burning_hands",
                spell_level=1,
                caster_level=5,
                dc=14,
                uses_remaining=2,
                is_aoe=True,
                aoe_shape="cone",
                aoe_length_ft=15,
            ),
        ],
        reach=5,
        initiative_bonus=2,
        bab=2,
        str_mod=0,
        dex_mod=2,
        con_mod=1,
        wis_mod=1,
        save_fort=2,
        save_ref=3,
        save_will=5,
    )


def create_goblin(
    name: str,
    position: Position,
    hp: int = 5,
    ac: int = 15,
) -> CombatantConfig:
    """Create a goblin enemy."""
    return CombatantConfig(
        name=name,
        team="enemy",
        position=position,
        size="Small",
        hp=hp,
        ac=ac,
        attacks=[
            AttackConfig(
                name="morningstar",
                attack_bonus=2,
                damage_dice="1d6",
                damage_bonus=0,
                damage_type="bludgeoning",
                is_ranged=False,
            )
        ],
        reach=5,
        initiative_bonus=1,
        bab=1,
        str_mod=0,
        dex_mod=1,
        con_mod=0,
        save_fort=3,
        save_ref=1,
        save_will=-1,
    )


def create_bandit(
    name: str,
    position: Position,
    hp: int = 11,
    ac: int = 14,
) -> CombatantConfig:
    """Create a bandit enemy."""
    return CombatantConfig(
        name=name,
        team="enemy",
        position=position,
        size="Medium",
        hp=hp,
        ac=ac,
        attacks=[
            AttackConfig(
                name="scimitar",
                attack_bonus=3,
                damage_dice="1d6",
                damage_bonus=1,
                damage_type="slashing",
                is_ranged=False,
                critical_range=18,
            )
        ],
        reach=5,
        initiative_bonus=2,
        bab=1,
        str_mod=1,
        dex_mod=2,
        con_mod=1,
        save_fort=3,
        save_ref=2,
        save_will=0,
    )


def create_large_creature(
    name: str,
    position: Position,
    hp: int = 85,
    ac: int = 18,
    attack_bonus: int = 12,
) -> CombatantConfig:
    """Create a Large creature (2x2 footprint, 10ft reach)."""
    return CombatantConfig(
        name=name,
        team="enemy",
        position=position,
        size="Large",
        hp=hp,
        ac=ac,
        attacks=[
            AttackConfig(
                name="claw",
                attack_bonus=attack_bonus,
                damage_dice="1d8",
                damage_bonus=6,
                damage_type="slashing",
                is_ranged=False,
            ),
            AttackConfig(
                name="bite",
                attack_bonus=attack_bonus - 5,
                damage_dice="2d6",
                damage_bonus=3,
                damage_type="piercing",
                is_ranged=False,
            ),
        ],
        reach=10,
        combat_reflexes=True,
        max_aoo_per_round=4,  # Combat Reflexes with high Dex
        initiative_bonus=1,
        bab=8,
        str_mod=6,
        dex_mod=1,
        con_mod=4,
        save_fort=10,
        save_ref=5,
        save_will=4,
    )


# ==============================================================================
# SCENARIO FIXTURES
# ==============================================================================

@pytest.fixture
def tavern_scenario() -> ScenarioConfig:
    """Pre-configured tavern brawl scenario.

    5 combatants in a 15x15 tavern:
    - 2 melee fighters (party)
    - 1 ranged archer (party)
    - 1 spellcaster (party - for burning hands cone)
    - 1 rogue (party)

    vs

    - 3 bandits (enemy)

    Terrain:
    - Tables providing partial cover
    - Bar providing improved cover
    """
    terrain = [
        # Tables (partial cover)
        TerrainPlacement(
            coord=Position(x=5, y=5),
            terrain_type="table",
            cover_provided=CoverDegree.PARTIAL,
            blocks_los=False,
            blocks_loe=False,
            height=3,
        ),
        TerrainPlacement(
            coord=Position(x=6, y=5),
            terrain_type="table",
            cover_provided=CoverDegree.PARTIAL,
            blocks_los=False,
            blocks_loe=False,
            height=3,
        ),
        TerrainPlacement(
            coord=Position(x=10, y=8),
            terrain_type="table",
            cover_provided=CoverDegree.PARTIAL,
            blocks_los=False,
            blocks_loe=False,
            height=3,
        ),
        TerrainPlacement(
            coord=Position(x=11, y=8),
            terrain_type="table",
            cover_provided=CoverDegree.PARTIAL,
            blocks_los=False,
            blocks_loe=False,
            height=3,
        ),
        # Bar (improved cover)
        TerrainPlacement(
            coord=Position(x=2, y=12),
            terrain_type="bar",
            cover_provided=CoverDegree.IMPROVED,
            blocks_los=False,
            blocks_loe=True,
            height=4,
        ),
        TerrainPlacement(
            coord=Position(x=3, y=12),
            terrain_type="bar",
            cover_provided=CoverDegree.IMPROVED,
            blocks_los=False,
            blocks_loe=True,
            height=4,
        ),
        TerrainPlacement(
            coord=Position(x=4, y=12),
            terrain_type="bar",
            cover_provided=CoverDegree.IMPROVED,
            blocks_los=False,
            blocks_loe=True,
            height=4,
        ),
    ]

    combatants = [
        # Party
        create_melee_fighter("fighter_1", "party", Position(x=3, y=3)),
        create_melee_fighter("fighter_2", "party", Position(x=5, y=3)),
        create_archer("archer_1", "party", Position(x=12, y=2)),
        create_wizard("wizard_1", "party", Position(x=7, y=2)),
        create_rogue("rogue_1", "party", Position(x=8, y=4)),
        # Enemies
        create_bandit("bandit_1", Position(x=4, y=10)),
        create_bandit("bandit_2", Position(x=8, y=11)),
        create_bandit("bandit_3", Position(x=11, y=10)),
    ]

    return ScenarioConfig(
        name="Tavern Brawl",
        grid_width=15,
        grid_height=15,
        terrain=terrain,
        combatants=combatants,
        round_limit=15,
        seed=42,
        description="5v3 tavern combat with tables and bar for cover",
    )


@pytest.fixture
def dungeon_scenario() -> ScenarioConfig:
    """Pre-configured dungeon corridor scenario.

    8 combatants across 3 connected rooms (30x20 grid):
    - Party of 4 (2 fighters, 1 cleric, 1 wizard)
    - 4 goblins with reach weapons (longspears)

    Terrain:
    - Walls and doorways
    - Stairs (elevation change)
    """
    terrain = []

    # Room 1 walls (left side, 0-9 x)
    for x in range(10):
        terrain.append(TerrainPlacement(
            coord=Position(x=x, y=0),
            terrain_type="wall",
            blocks_los=True,
            blocks_loe=True,
        ))
        terrain.append(TerrainPlacement(
            coord=Position(x=x, y=9),
            terrain_type="wall",
            blocks_los=True,
            blocks_loe=True,
        ))

    for y in range(10):
        if y not in [4, 5]:  # Door opening
            terrain.append(TerrainPlacement(
                coord=Position(x=9, y=y),
                terrain_type="wall",
                blocks_los=True,
                blocks_loe=True,
            ))

    # Room 2 (corridor, 10-19 x)
    for y in range(10, 20):
        terrain.append(TerrainPlacement(
            coord=Position(x=10, y=y),
            terrain_type="wall",
            blocks_los=True,
            blocks_loe=True,
        ))
        terrain.append(TerrainPlacement(
            coord=Position(x=19, y=y),
            terrain_type="wall",
            blocks_los=True,
            blocks_loe=True,
        ))

    # Stairs in corridor (elevation)
    for x in range(12, 17):
        terrain.append(TerrainPlacement(
            coord=Position(x=x, y=14),
            terrain_type="stairs",
            elevation=5,
            is_difficult=True,
        ))
        terrain.append(TerrainPlacement(
            coord=Position(x=x, y=15),
            terrain_type="stairs",
            elevation=10,
            is_difficult=True,
        ))

    # Room 3 (right side, 20-29 x)
    for x in range(20, 30):
        terrain.append(TerrainPlacement(
            coord=Position(x=x, y=10),
            terrain_type="wall",
            blocks_los=True,
            blocks_loe=True,
        ))
        terrain.append(TerrainPlacement(
            coord=Position(x=x, y=19),
            terrain_type="wall",
            blocks_los=True,
            blocks_loe=True,
        ))

    # Goblin with longspear (10ft reach)
    def create_goblin_spear(name: str, position: Position) -> CombatantConfig:
        return CombatantConfig(
            name=name,
            team="enemy",
            position=position,
            size="Small",
            hp=5,
            ac=15,
            attacks=[
                AttackConfig(
                    name="longspear",
                    attack_bonus=1,
                    damage_dice="1d6",
                    damage_bonus=0,
                    damage_type="piercing",
                    is_ranged=False,
                )
            ],
            reach=10,  # Longspear reach
            initiative_bonus=1,
            bab=1,
            str_mod=0,
            dex_mod=1,
        )

    combatants = [
        # Party in Room 1
        create_melee_fighter("party_fighter_1", "party", Position(x=3, y=4)),
        create_melee_fighter("party_fighter_2", "party", Position(x=3, y=5)),
        create_wizard("party_cleric", "party", Position(x=2, y=4)),  # Using wizard stats
        create_wizard("party_wizard", "party", Position(x=2, y=5)),
        # Goblins in Room 2 and 3
        create_goblin_spear("goblin_1", Position(x=14, y=12)),
        create_goblin_spear("goblin_2", Position(x=15, y=12)),
        create_goblin_spear("goblin_3", Position(x=22, y=14)),
        create_goblin_spear("goblin_4", Position(x=23, y=14)),
    ]

    return ScenarioConfig(
        name="Dungeon Corridor",
        grid_width=30,
        grid_height=20,
        terrain=terrain,
        combatants=combatants,
        round_limit=15,
        seed=123,
        description="Party of 4 vs 4 goblins with reach weapons across 3 rooms",
    )


@pytest.fixture
def field_battle_scenario() -> ScenarioConfig:
    """Pre-configured open field battle scenario.

    12 combatants on 40x40 open terrain:
    - 6 party members (2 fighters, 2 archers, 1 wizard, 1 rogue)
    - 6 enemies (2 fighters, 2 archers, 1 wizard, 1 rogue)

    Terrain:
    - Scattered boulders for cover
    """
    terrain = []

    # Scattered boulders
    boulder_positions = [
        Position(x=10, y=10), Position(x=11, y=10),
        Position(x=25, y=15), Position(x=26, y=15),
        Position(x=15, y=25), Position(x=16, y=25),
        Position(x=30, y=30), Position(x=31, y=30),
        Position(x=20, y=20),
    ]

    for pos in boulder_positions:
        terrain.append(TerrainPlacement(
            coord=pos,
            terrain_type="boulder",
            cover_provided=CoverDegree.IMPROVED,
            blocks_los=True,
            blocks_loe=True,
            height=5,
        ))

    combatants = [
        # Party (south side, starting in center-south)
        create_melee_fighter("party_fighter_1", "party", Position(x=18, y=15)),
        create_melee_fighter("party_fighter_2", "party", Position(x=22, y=15)),
        create_archer("party_archer_1", "party", Position(x=15, y=13)),
        create_archer("party_archer_2", "party", Position(x=25, y=13)),
        create_wizard("party_wizard", "party", Position(x=20, y=12)),
        create_rogue("party_rogue", "party", Position(x=20, y=16)),
        # Enemies (north side, starting in center-north)
        create_melee_fighter("enemy_fighter_1", "enemy", Position(x=18, y=25)),
        create_melee_fighter("enemy_fighter_2", "enemy", Position(x=22, y=25)),
        create_archer("enemy_archer_1", "enemy", Position(x=15, y=27)),
        create_archer("enemy_archer_2", "enemy", Position(x=25, y=27)),
        create_wizard("enemy_wizard", "enemy", Position(x=20, y=28)),
        create_rogue("enemy_rogue", "enemy", Position(x=20, y=24)),
    ]

    return ScenarioConfig(
        name="Open Field Battle",
        grid_width=40,
        grid_height=40,
        terrain=terrain,
        combatants=combatants,
        round_limit=15,
        seed=456,
        description="6v6 mixed forces with scattered boulder cover",
    )


@pytest.fixture
def boss_fight_scenario() -> ScenarioConfig:
    """Pre-configured boss fight scenario.

    6 combatants in 25x25 arena:
    - Party of 5
    - 1 Large creature (2x2 footprint, 10ft reach, Combat Reflexes)

    Terrain:
    - Pillars for cover
    """
    terrain = []

    # Corner pillars
    pillar_positions = [
        Position(x=5, y=5), Position(x=5, y=6),
        Position(x=6, y=5), Position(x=6, y=6),
        Position(x=18, y=5), Position(x=19, y=5),
        Position(x=18, y=6), Position(x=19, y=6),
        Position(x=5, y=18), Position(x=5, y=19),
        Position(x=6, y=18), Position(x=6, y=19),
        Position(x=18, y=18), Position(x=19, y=18),
        Position(x=18, y=19), Position(x=19, y=19),
    ]

    for pos in pillar_positions:
        terrain.append(TerrainPlacement(
            coord=pos,
            terrain_type="pillar",
            cover_provided=CoverDegree.TOTAL,
            blocks_los=True,
            blocks_loe=True,
            height=10,
        ))

    combatants = [
        # Party spread around arena edges
        create_melee_fighter("party_fighter_1", "party", Position(x=3, y=12)),
        create_melee_fighter("party_fighter_2", "party", Position(x=21, y=12)),
        create_archer("party_archer", "party", Position(x=12, y=3)),
        create_wizard("party_wizard", "party", Position(x=12, y=21)),
        create_rogue("party_rogue", "party", Position(x=12, y=5)),
        # Boss in center
        create_large_creature("boss", Position(x=11, y=11)),  # 2x2 at (11,11)-(12,12)
    ]

    return ScenarioConfig(
        name="Boss Fight",
        grid_width=25,
        grid_height=25,
        terrain=terrain,
        combatants=combatants,
        round_limit=20,
        seed=789,
        description="Party of 5 vs Large creature with 10ft reach and Combat Reflexes",
    )


@pytest.fixture
def scenario_runner() -> ScenarioRunner:
    """Create a fresh ScenarioRunner instance."""
    return ScenarioRunner()

"""Generate Gold Master files for replay regression testing.

This script generates the initial Gold Master recordings for all 4 scenarios.
Run this once to create the baseline recordings, then use them for regression tests.

Usage:
    python -m tests.fixtures.gold_masters.generate

WO-018: Replay Regression Suite
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from aidm.schemas.testing import ScenarioConfig
from aidm.schemas.position import Position
from aidm.testing.replay_regression import ReplayRegressionHarness


def create_tavern_scenario() -> ScenarioConfig:
    """Create tavern brawl scenario config."""
    from tests.integration.conftest import (
        create_melee_fighter, create_archer, create_wizard, create_rogue, create_bandit,
        TerrainPlacement, CoverDegree,
    )

    terrain = [
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
    ]

    combatants = [
        create_melee_fighter("fighter_1", "party", Position(x=3, y=3)),
        create_melee_fighter("fighter_2", "party", Position(x=5, y=3)),
        create_archer("archer_1", "party", Position(x=12, y=2)),
        create_wizard("wizard_1", "party", Position(x=7, y=2)),
        create_rogue("rogue_1", "party", Position(x=8, y=4)),
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
        round_limit=100,
        seed=42,
        description="5v3 tavern combat with tables and bar for cover",
    )


def create_dungeon_scenario() -> ScenarioConfig:
    """Create dungeon corridor scenario config."""
    from tests.integration.conftest import (
        create_melee_fighter, create_wizard,
        TerrainPlacement, CombatantConfig, AttackConfig,
    )

    terrain = []

    # Room 1 walls
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
            reach=10,
            initiative_bonus=1,
            bab=1,
            str_mod=0,
            dex_mod=1,
        )

    combatants = [
        create_melee_fighter("party_fighter_1", "party", Position(x=3, y=4)),
        create_melee_fighter("party_fighter_2", "party", Position(x=3, y=5)),
        create_wizard("party_cleric", "party", Position(x=2, y=4)),
        create_wizard("party_wizard", "party", Position(x=2, y=5)),
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
        round_limit=100,
        seed=123,
        description="Party of 4 vs 4 goblins with reach weapons across 3 rooms",
    )


def create_field_scenario() -> ScenarioConfig:
    """Create open field battle scenario config."""
    from tests.integration.conftest import (
        create_melee_fighter, create_archer, create_wizard, create_rogue,
        TerrainPlacement, CoverDegree,
    )

    terrain = []
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
        create_melee_fighter("party_fighter_1", "party", Position(x=18, y=15)),
        create_melee_fighter("party_fighter_2", "party", Position(x=22, y=15)),
        create_archer("party_archer_1", "party", Position(x=15, y=13)),
        create_archer("party_archer_2", "party", Position(x=25, y=13)),
        create_wizard("party_wizard", "party", Position(x=20, y=12)),
        create_rogue("party_rogue", "party", Position(x=20, y=16)),
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
        round_limit=100,
        seed=456,
        description="6v6 mixed forces with scattered boulder cover",
    )


def create_boss_scenario() -> ScenarioConfig:
    """Create boss fight scenario config."""
    from tests.integration.conftest import (
        create_melee_fighter, create_archer, create_wizard, create_rogue, create_large_creature,
        TerrainPlacement, CoverDegree,
    )

    terrain = []
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
        create_melee_fighter("party_fighter_1", "party", Position(x=3, y=12)),
        create_melee_fighter("party_fighter_2", "party", Position(x=21, y=12)),
        create_archer("party_archer", "party", Position(x=12, y=3)),
        create_wizard("party_wizard", "party", Position(x=12, y=21)),
        create_rogue("party_rogue", "party", Position(x=12, y=5)),
        create_large_creature("boss", Position(x=11, y=11)),
    ]

    return ScenarioConfig(
        name="Boss Fight",
        grid_width=25,
        grid_height=25,
        terrain=terrain,
        combatants=combatants,
        round_limit=100,
        seed=789,
        description="Party of 5 vs Large creature with 10ft reach and Combat Reflexes",
    )


def main():
    """Generate all Gold Master files."""
    output_dir = Path(__file__).parent

    harness = ReplayRegressionHarness()

    scenarios = [
        ("tavern_100turn.jsonl", create_tavern_scenario(), 100, 42),
        ("dungeon_100turn.jsonl", create_dungeon_scenario(), 100, 123),
        ("field_100turn.jsonl", create_field_scenario(), 100, 456),
        ("boss_100turn.jsonl", create_boss_scenario(), 100, 789),
    ]

    for filename, scenario, turns, seed in scenarios:
        print(f"Recording {filename}...")

        gold_master = harness.record_gold_master(scenario, turns=turns, seed=seed)

        output_path = output_dir / filename
        harness.serialize_gold_master(gold_master, output_path)

        print(f"  - {gold_master.turn_count} turns")
        print(f"  - {len(gold_master.events)} events")
        print(f"  - Hash: {gold_master.final_state_hash[:16]}...")

    print("\nDone! Gold Masters generated.")


if __name__ == "__main__":
    main()

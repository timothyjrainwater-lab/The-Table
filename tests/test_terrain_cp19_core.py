"""CP-19 Environment & Terrain â€” Core Tests (Tier-1).

Tests for terrain resolution, cover, elevation, and falling damage.
"""

import pytest
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position  # CP-001: Canonical position type
from aidm.schemas.terrain import (
    TerrainCell, TerrainTag, CoverType,
    ElevationDifference, FallingResult, CoverCheckResult,
)
from aidm.core.terrain_resolver import (
    get_terrain_cell,
    get_movement_cost,
    is_difficult_terrain,
    can_run_through,
    can_5_foot_step,
    check_cover,
    get_elevation,
    get_elevation_difference,
    get_higher_ground_bonus,
    is_pit,
    get_pit_depth,
    is_ledge,
    get_ledge_drop,
    check_hazard,
    calculate_falling_damage,
    resolve_falling,
    check_push_path_for_hazards,
    resolve_forced_movement_with_hazards,
)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def basic_world_state():
    """Create world state with basic terrain for testing."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.ENTITY_ID: "fighter",
                EF.TEAM: "party",
                EF.HP_CURRENT: 50,
                EF.HP_MAX: 50,
                EF.AC: 16,
                EF.DEFEATED: False,
                EF.POSITION: {"x": 5, "y": 5},
                EF.ELEVATION: 0,
            },
            "orc": {
                EF.ENTITY_ID: "orc",
                EF.TEAM: "monsters",
                EF.HP_CURRENT: 20,
                EF.HP_MAX: 20,
                EF.AC: 14,
                EF.DEFEATED: False,
                EF.POSITION: {"x": 6, "y": 5},
                EF.ELEVATION: 0,
            },
        },
        active_combat={
            "initiative_order": ["fighter", "orc"],
            "terrain_map": {
                "5,5": {"position": {"x": 5, "y": 5}, "elevation": 0, "movement_cost": 1},
                "6,5": {"position": {"x": 6, "y": 5}, "elevation": 0, "movement_cost": 1},
            },
        }
    )


@pytest.fixture
def terrain_with_difficult():
    """Create world state with difficult terrain."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "fighter": {
                EF.ENTITY_ID: "fighter",
                EF.TEAM: "party",
                EF.HP_CURRENT: 50,
                EF.POSITION: {"x": 5, "y": 5},
            },
        },
        active_combat={
            "terrain_map": {
                "5,5": {"position": {"x": 5, "y": 5}, "movement_cost": 1},
                "6,5": {"position": {"x": 6, "y": 5}, "movement_cost": 2},  # Difficult
                "7,5": {"position": {"x": 7, "y": 5}, "movement_cost": 4},  # Very difficult
            },
        }
    )


@pytest.fixture
def terrain_with_cover():
    """Create world state with cover-providing terrain."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "archer": {
                EF.ENTITY_ID: "archer",
                EF.TEAM: "party",
                EF.POSITION: {"x": 0, "y": 0},
            },
            "defender_standard": {
                EF.ENTITY_ID: "defender_standard",
                EF.TEAM: "monsters",
                EF.POSITION: {"x": 5, "y": 0},
            },
            "defender_improved": {
                EF.ENTITY_ID: "defender_improved",
                EF.TEAM: "monsters",
                EF.POSITION: {"x": 5, "y": 5},
            },
            "defender_total": {
                EF.ENTITY_ID: "defender_total",
                EF.TEAM: "monsters",
                EF.POSITION: {"x": 5, "y": 10},
            },
        },
        active_combat={
            "terrain_map": {
                "5,0": {"position": {"x": 5, "y": 0}, "cover_type": "standard"},
                "5,5": {"position": {"x": 5, "y": 5}, "cover_type": "improved"},
                "5,10": {"position": {"x": 5, "y": 10}, "cover_type": "total"},
            },
        }
    )


@pytest.fixture
def terrain_with_elevation():
    """Create world state with elevation differences."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "high_ground": {
                EF.ENTITY_ID: "high_ground",
                EF.TEAM: "party",
                EF.POSITION: {"x": 5, "y": 5},
                EF.ELEVATION: 0,  # Entity at ground level
            },
            "low_ground": {
                EF.ENTITY_ID: "low_ground",
                EF.TEAM: "monsters",
                EF.POSITION: {"x": 6, "y": 5},
                EF.ELEVATION: 0,
            },
        },
        active_combat={
            "terrain_map": {
                "5,5": {"position": {"x": 5, "y": 5}, "elevation": 10},  # Hill
                "6,5": {"position": {"x": 6, "y": 5}, "elevation": 0},   # Ground
            },
        }
    )


@pytest.fixture
def terrain_with_pit():
    """Create world state with a pit hazard."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "victim": {
                EF.ENTITY_ID: "victim",
                EF.TEAM: "party",
                EF.HP_CURRENT: 50,
                EF.HP_MAX: 50,
                EF.POSITION: {"x": 5, "y": 5},
            },
        },
        active_combat={
            "terrain_map": {
                "5,5": {"position": {"x": 5, "y": 5}, "movement_cost": 1},
                "6,5": {"position": {"x": 6, "y": 5}, "movement_cost": 1, "is_pit": True, "pit_depth": 20},
                "7,5": {"position": {"x": 7, "y": 5}, "movement_cost": 1},
            },
        }
    )


@pytest.fixture
def terrain_with_ledge():
    """Create world state with a ledge hazard."""
    return WorldState(
        ruleset_version="3.5e",
        entities={
            "victim": {
                EF.ENTITY_ID: "victim",
                EF.TEAM: "party",
                EF.HP_CURRENT: 50,
                EF.HP_MAX: 50,
                EF.POSITION: {"x": 5, "y": 5},
            },
        },
        active_combat={
            "terrain_map": {
                "5,5": {"position": {"x": 5, "y": 5}, "movement_cost": 1, "elevation": 30},
                "6,5": {"position": {"x": 6, "y": 5}, "movement_cost": 1, "is_ledge": True, "ledge_drop": 30, "elevation": 30},
                "7,5": {"position": {"x": 7, "y": 5}, "movement_cost": 1, "elevation": 0},
            },
        }
    )


# ==============================================================================
# DIFFICULT TERRAIN TESTS
# ==============================================================================

class TestDifficultTerrain:
    """Test difficult terrain movement cost calculations."""

    def test_normal_terrain_cost_is_one(self, terrain_with_difficult):
        """Normal terrain has movement cost of 1."""
        cost = get_movement_cost(terrain_with_difficult, {"x": 5, "y": 5}, {"x": 5, "y": 5})
        assert cost == 1

    def test_difficult_terrain_doubles_cost(self, terrain_with_difficult):
        """Difficult terrain doubles movement cost to 2."""
        cost = get_movement_cost(terrain_with_difficult, {"x": 5, "y": 5}, {"x": 6, "y": 5})
        assert cost == 2

    def test_very_difficult_terrain_quadruples_cost(self, terrain_with_difficult):
        """Very difficult terrain quadruples movement cost to 4."""
        cost = get_movement_cost(terrain_with_difficult, {"x": 5, "y": 5}, {"x": 7, "y": 5})
        assert cost == 4

    def test_is_difficult_terrain_false_for_normal(self, terrain_with_difficult):
        """is_difficult_terrain returns False for normal terrain."""
        assert not is_difficult_terrain(terrain_with_difficult, {"x": 5, "y": 5})

    def test_is_difficult_terrain_true_for_difficult(self, terrain_with_difficult):
        """is_difficult_terrain returns True for difficult terrain."""
        assert is_difficult_terrain(terrain_with_difficult, {"x": 6, "y": 5})

    def test_can_run_through_normal_terrain(self, terrain_with_difficult):
        """Can run/charge through normal terrain."""
        assert can_run_through(terrain_with_difficult, {"x": 5, "y": 5})

    def test_cannot_run_through_difficult_terrain(self, terrain_with_difficult):
        """Cannot run/charge through difficult terrain."""
        assert not can_run_through(terrain_with_difficult, {"x": 6, "y": 5})

    def test_can_5_foot_step_normal_terrain(self, terrain_with_difficult):
        """Can 5-foot step in normal terrain."""
        assert can_5_foot_step(terrain_with_difficult, {"x": 5, "y": 5})

    def test_can_5_foot_step_difficult_terrain(self, terrain_with_difficult):
        """Can 5-foot step in difficult terrain (cost 2)."""
        assert can_5_foot_step(terrain_with_difficult, {"x": 6, "y": 5})

    def test_cannot_5_foot_step_very_difficult_terrain(self, terrain_with_difficult):
        """Cannot 5-foot step in very difficult terrain (cost 4+)."""
        assert not can_5_foot_step(terrain_with_difficult, {"x": 7, "y": 5})


# ==============================================================================
# COVER TESTS
# ==============================================================================

class TestCover:
    """Test cover determination and bonuses."""

    def test_no_cover_no_bonus(self, basic_world_state):
        """No cover provides no AC or Reflex bonus."""
        result = check_cover(basic_world_state, "fighter", "orc")
        assert result.cover_type is None
        assert result.ac_bonus == 0
        assert result.reflex_bonus == 0
        assert result.blocks_aoo is False
        assert result.blocks_targeting is False

    def test_standard_cover_provides_plus_4_ac(self, terrain_with_cover):
        """Standard cover provides +4 AC."""
        result = check_cover(terrain_with_cover, "archer", "defender_standard")
        assert result.cover_type == CoverType.STANDARD
        assert result.ac_bonus == 4
        assert result.reflex_bonus == 2
        assert result.blocks_aoo is True
        assert result.blocks_targeting is False

    def test_improved_cover_provides_plus_8_ac(self, terrain_with_cover):
        """Improved cover provides +8 AC."""
        result = check_cover(terrain_with_cover, "archer", "defender_improved")
        assert result.cover_type == CoverType.IMPROVED
        assert result.ac_bonus == 8
        assert result.reflex_bonus == 4
        assert result.blocks_aoo is True
        assert result.blocks_targeting is False

    def test_total_cover_blocks_targeting(self, terrain_with_cover):
        """Total cover blocks targeting entirely."""
        result = check_cover(terrain_with_cover, "archer", "defender_total")
        assert result.cover_type == CoverType.TOTAL
        assert result.blocks_targeting is True
        assert result.blocks_aoo is True


# ==============================================================================
# HIGHER GROUND TESTS
# ==============================================================================

class TestHigherGround:
    """Test higher ground bonus calculations."""

    def test_higher_ground_melee_bonus(self, terrain_with_elevation):
        """Higher ground provides +1 melee attack bonus."""
        bonus = get_higher_ground_bonus(terrain_with_elevation, "high_ground", "low_ground")
        assert bonus == 1

    def test_no_bonus_when_lower(self, terrain_with_elevation):
        """No bonus when attacker is lower than defender."""
        bonus = get_higher_ground_bonus(terrain_with_elevation, "low_ground", "high_ground")
        assert bonus == 0

    def test_no_bonus_when_equal_elevation(self, basic_world_state):
        """No bonus when both at same elevation."""
        bonus = get_higher_ground_bonus(basic_world_state, "fighter", "orc")
        assert bonus == 0

    def test_elevation_difference_positive_when_attacker_higher(self, terrain_with_elevation):
        """Elevation difference is positive when attacker is higher."""
        result = get_elevation_difference(terrain_with_elevation, "high_ground", "low_ground")
        assert result.difference > 0
        assert result.attacker_has_higher_ground is True

    def test_elevation_difference_negative_when_attacker_lower(self, terrain_with_elevation):
        """Elevation difference is negative when attacker is lower."""
        result = get_elevation_difference(terrain_with_elevation, "low_ground", "high_ground")
        assert result.difference < 0
        assert result.attacker_has_higher_ground is False


# ==============================================================================
# FALLING DAMAGE TESTS
# ==============================================================================

class TestFallingDamage:
    """Test falling damage calculations."""

    def test_falling_10_feet_is_1d6(self):
        """Falling 10 feet deals 1d6 damage."""
        dice = calculate_falling_damage(10)
        assert dice == 1

    def test_falling_20_feet_is_2d6(self):
        """Falling 20 feet deals 2d6 damage."""
        dice = calculate_falling_damage(20)
        assert dice == 2

    def test_falling_50_feet_is_5d6(self):
        """Falling 50 feet deals 5d6 damage."""
        dice = calculate_falling_damage(50)
        assert dice == 5

    def test_falling_200_feet_is_20d6(self):
        """Falling 200 feet deals 20d6 (max)."""
        dice = calculate_falling_damage(200)
        assert dice == 20

    def test_falling_300_feet_capped_at_20d6(self):
        """Falling 300 feet is capped at 20d6."""
        dice = calculate_falling_damage(300)
        assert dice == 20

    def test_intentional_jump_first_10_free(self):
        """Intentional jump gets first 10 feet free."""
        dice = calculate_falling_damage(20, is_intentional=True)
        assert dice == 1  # 20 - 10 = 10 feet = 1d6

    def test_intentional_jump_10_feet_no_damage(self):
        """Intentional jump of 10 feet deals no damage."""
        dice = calculate_falling_damage(10, is_intentional=True)
        assert dice == 0

    def test_resolve_falling_applies_damage(self, basic_world_state):
        """resolve_falling applies damage to entity."""
        rng = RNGManager(master_seed=42)
        events, new_state, result = resolve_falling(
            entity_id="fighter",
            fall_distance=30,
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        assert result.fall_distance == 30
        assert result.damage_dice == 3
        assert len(result.damage_rolls) == 3
        assert result.total_damage > 0

        # Check HP was reduced
        new_hp = new_state.entities["fighter"][EF.HP_CURRENT]
        assert new_hp < 50


# ==============================================================================
# HAZARD DETECTION TESTS
# ==============================================================================

class TestHazardDetection:
    """Test pit and ledge hazard detection."""

    def test_is_pit_true_for_pit(self, terrain_with_pit):
        """is_pit returns True for pit cells."""
        assert is_pit(terrain_with_pit, {"x": 6, "y": 5})

    def test_is_pit_false_for_normal(self, terrain_with_pit):
        """is_pit returns False for normal cells."""
        assert not is_pit(terrain_with_pit, {"x": 5, "y": 5})

    def test_get_pit_depth(self, terrain_with_pit):
        """get_pit_depth returns correct depth."""
        depth = get_pit_depth(terrain_with_pit, {"x": 6, "y": 5})
        assert depth == 20

    def test_is_ledge_true_for_ledge(self, terrain_with_ledge):
        """is_ledge returns True for ledge cells."""
        assert is_ledge(terrain_with_ledge, {"x": 6, "y": 5})

    def test_is_ledge_false_for_normal(self, terrain_with_ledge):
        """is_ledge returns False for normal cells."""
        assert not is_ledge(terrain_with_ledge, {"x": 5, "y": 5})

    def test_get_ledge_drop(self, terrain_with_ledge):
        """get_ledge_drop returns correct height."""
        drop = get_ledge_drop(terrain_with_ledge, {"x": 6, "y": 5})
        assert drop == 30

    def test_check_hazard_returns_pit(self, terrain_with_pit):
        """check_hazard detects pit hazards."""
        hazard_type, distance = check_hazard(terrain_with_pit, {"x": 6, "y": 5})
        assert hazard_type == "pit"
        assert distance == 20

    def test_check_hazard_returns_ledge(self, terrain_with_ledge):
        """check_hazard detects ledge hazards."""
        hazard_type, distance = check_hazard(terrain_with_ledge, {"x": 6, "y": 5})
        assert hazard_type == "ledge"
        assert distance == 30

    def test_check_hazard_returns_none_for_normal(self, basic_world_state):
        """check_hazard returns None for normal cells."""
        hazard_type, distance = check_hazard(basic_world_state, {"x": 5, "y": 5})
        assert hazard_type is None
        assert distance == 0


# ==============================================================================
# FORCED MOVEMENT WITH HAZARDS TESTS
# ==============================================================================

class TestForcedMovementHazards:
    """Test forced movement with hazard detection."""

    def test_push_into_pit_triggers_falling(self, terrain_with_pit):
        """Pushing entity into pit triggers falling damage."""
        rng = RNGManager(master_seed=42)

        events, world_state, final_pos, falling_result = resolve_forced_movement_with_hazards(
            entity_id="victim",
            start_pos={"x": 5, "y": 5},
            push_direction=(1, 0),  # Push right
            push_distance=10,
            world_state=terrain_with_pit,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        # Should have triggered hazard
        assert falling_result is not None
        assert falling_result.fall_distance == 20
        assert final_pos == {"x": 6, "y": 5}  # Stopped at pit

        # Check for hazard_triggered event
        event_types = [e.event_type for e in events]
        assert "hazard_triggered" in event_types
        assert "falling_damage" in event_types

    def test_push_off_ledge_triggers_falling(self, terrain_with_ledge):
        """Pushing entity off ledge triggers falling damage."""
        rng = RNGManager(master_seed=42)

        events, world_state, final_pos, falling_result = resolve_forced_movement_with_hazards(
            entity_id="victim",
            start_pos={"x": 5, "y": 5},
            push_direction=(1, 0),  # Push right
            push_distance=10,
            world_state=terrain_with_ledge,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        # Should have triggered hazard
        assert falling_result is not None
        assert falling_result.fall_distance == 30
        assert final_pos == {"x": 6, "y": 5}  # Stopped at ledge

    def test_push_no_hazard_moves_full_distance(self, basic_world_state):
        """Push with no hazard moves entity full distance."""
        rng = RNGManager(master_seed=42)

        events, world_state, final_pos, falling_result = resolve_forced_movement_with_hazards(
            entity_id="fighter",
            start_pos={"x": 5, "y": 5},
            push_direction=(1, 0),  # Push right
            push_distance=10,  # 2 squares
            world_state=basic_world_state,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
        )

        # No hazard
        assert falling_result is None
        assert final_pos == {"x": 7, "y": 5}  # Moved 2 squares


# ==============================================================================
# DETERMINISM TESTS
# ==============================================================================

class TestTerrainDeterminism:
    """Test deterministic behavior of terrain resolution."""

    def test_falling_damage_10x_replay_identical(self, basic_world_state):
        """10 falling damage resolutions produce identical results."""
        results = []
        for _ in range(10):
            rng = RNGManager(master_seed=12345)
            events, new_state, result = resolve_falling(
                entity_id="fighter",
                fall_distance=50,
                world_state=basic_world_state,
                rng=rng,
                next_event_id=0,
                timestamp=0.0,
            )
            results.append({
                "total_damage": result.total_damage,
                "damage_rolls": result.damage_rolls,
                "final_hp": new_state.entities["fighter"][EF.HP_CURRENT],
            })

        for i in range(1, 10):
            assert results[i] == results[0], f"Run {i} differs from run 0"

    def test_forced_movement_hazard_10x_replay_identical(self, terrain_with_pit):
        """10 forced movement with hazard resolutions produce identical results."""
        results = []
        for _ in range(10):
            rng = RNGManager(master_seed=12345)
            events, world_state, final_pos, falling_result = resolve_forced_movement_with_hazards(
                entity_id="victim",
                start_pos={"x": 5, "y": 5},
                push_direction=(1, 0),
                push_distance=10,
                world_state=terrain_with_pit,
                rng=rng,
                next_event_id=0,
                timestamp=0.0,
            )
            results.append({
                "final_pos": final_pos,
                "falling_damage": falling_result.total_damage if falling_result else 0,
                "event_count": len(events),
            })

        for i in range(1, 10):
            assert results[i] == results[0], f"Run {i} differs from run 0"


# ==============================================================================
# FIX-09: _is_between() soft cover geometry tests
# ==============================================================================

class TestIsBetween:
    """Tests for the _is_between() soft cover geometry function."""

    def test_creature_on_diagonal_line(self):
        """Creature at (1,1) between (0,0) and (2,2) provides soft cover."""
        from aidm.core.terrain_resolver import _is_between
        assert _is_between(0, 0, 2, 2, 1, 1) is True

    def test_creature_off_line_not_soft_cover(self):
        """Creature at (0,1) between (0,0) and (2,0) does NOT provide soft cover (horizontal line)."""
        from aidm.core.terrain_resolver import _is_between
        # (0,1) is not on the horizontal line from (0,0) to (2,0)
        assert _is_between(0, 0, 2, 0, 0, 1) is False

    def test_creature_on_horizontal_line(self):
        """Creature at (1,0) between (0,0) and (3,0) provides soft cover."""
        from aidm.core.terrain_resolver import _is_between
        assert _is_between(0, 0, 3, 0, 1, 0) is True

    def test_creature_on_vertical_line(self):
        """Creature at (0,2) between (0,0) and (0,4) provides soft cover."""
        from aidm.core.terrain_resolver import _is_between
        assert _is_between(0, 0, 0, 4, 0, 2) is True

    def test_creature_at_endpoint_excluded(self):
        """Creatures at attacker/defender positions should not count."""
        from aidm.core.terrain_resolver import _is_between
        # At attacker position
        assert _is_between(0, 0, 3, 3, 0, 0) is False
        # At defender position
        assert _is_between(0, 0, 3, 3, 3, 3) is False

    def test_creature_far_from_line(self):
        """Creature far from the line does not provide soft cover."""
        from aidm.core.terrain_resolver import _is_between
        assert _is_between(0, 0, 4, 4, 0, 4) is False

    def test_creature_near_diagonal_line(self):
        """Creature near (but not on) a long diagonal can provide soft cover."""
        from aidm.core.terrain_resolver import _is_between
        # (2,1) is near the line from (0,0) to (4,3) â€” cross product = 4*1 - 3*2 = -2, |cross| = 2
        # seg_len = max(4,3) = 4, 2 <= 4, so yes
        assert _is_between(0, 0, 4, 3, 2, 1) is True


# ==============================================================================
# WO-FIX-10: E-BUG-01 — Soft cover applies to ranged only, not melee
# ==============================================================================

class TestSoftCoverRangedOnly:
    """Soft cover from creatures applies to ranged attacks, not melee (PHB p.152)."""

    def _make_world_with_blocker(self):
        """Create world where creature blocks line between attacker and defender."""
        return WorldState(
            ruleset_version="3.5e",
            entities={
                "archer": {
                    EF.ENTITY_ID: "archer",
                    EF.TEAM: "party",
                    EF.HP_CURRENT: 30,
                    EF.HP_MAX: 30,
                    EF.AC: 14,
                    EF.DEFEATED: False,
                    EF.POSITION: {"x": 0, "y": 0},
                    EF.ELEVATION: 0,
                },
                "blocker": {
                    EF.ENTITY_ID: "blocker",
                    EF.TEAM: "party",
                    EF.HP_CURRENT: 20,
                    EF.HP_MAX: 20,
                    EF.AC: 12,
                    EF.DEFEATED: False,
                    EF.POSITION: {"x": 2, "y": 2},
                    EF.ELEVATION: 0,
                },
                "target": {
                    EF.ENTITY_ID: "target",
                    EF.TEAM: "monsters",
                    EF.HP_CURRENT: 20,
                    EF.HP_MAX: 20,
                    EF.AC: 14,
                    EF.DEFEATED: False,
                    EF.POSITION: {"x": 4, "y": 4},
                    EF.ELEVATION: 0,
                },
            },
            active_combat={
                "initiative_order": ["archer", "blocker", "target"],
                "terrain_map": {
                    "0,0": {"position": {"x": 0, "y": 0}, "elevation": 0, "movement_cost": 1},
                    "2,2": {"position": {"x": 2, "y": 2}, "elevation": 0, "movement_cost": 1},
                    "4,4": {"position": {"x": 4, "y": 4}, "elevation": 0, "movement_cost": 1},
                },
            }
        )

    def test_ranged_attack_through_occupied_square_gets_soft_cover(self):
        """Ranged attack through occupied square: soft cover applies (PHB p.152)."""
        ws = self._make_world_with_blocker()
        result = check_cover(ws, "archer", "target", is_melee=False)
        assert result.cover_type == CoverType.SOFT
        assert result.ac_bonus == 4

    def test_melee_attack_through_occupied_square_no_soft_cover(self):
        """Melee attack through occupied square: soft cover does NOT apply."""
        ws = self._make_world_with_blocker()
        result = check_cover(ws, "archer", "target", is_melee=True)
        assert result.cover_type is None
        assert result.ac_bonus == 0


# ==============================================================================
# WO-FIX-10: E-BUG-02 — Water fall damage uses d3, not d6
# ==============================================================================

class TestWaterFallDamage:
    """Water fall damage uses d3 nonlethal, not d6 lethal (DMG p.304)."""

    def test_water_fall_uses_d3_not_d6(self):
        """Water fall damage rolls should use d3 (max 3), not d6."""
        ws = WorldState(
            ruleset_version="3.5e",
            entities={
                "swimmer": {
                    EF.ENTITY_ID: "swimmer",
                    EF.TEAM: "party",
                    EF.HP_CURRENT: 50,
                    EF.HP_MAX: 50,
                    EF.AC: 12,
                    EF.DEFEATED: False,
                    EF.POSITION: {"x": 5, "y": 5},
                    EF.ELEVATION: 0,
                },
            },
            active_combat={
                "initiative_order": ["swimmer"],
                "terrain_map": {},
            }
        )
        # Fall 50 feet into deep water — should produce d3 rolls
        rng = RNGManager(master_seed=42)
        events, new_state, result = resolve_falling(
            entity_id="swimmer",
            fall_distance=50,
            world_state=ws,
            rng=rng,
            next_event_id=0,
            timestamp=0.0,
            is_into_water=True,
            water_depth=20,
        )
        # All damage rolls must be 1-3 (d3), never 4-6
        assert result.damage_dice > 0, "Should have some damage dice for 50ft water fall"
        for roll in result.damage_rolls:
            assert 1 <= roll <= 3, f"Water fall roll {roll} exceeds d3 range (1-3)"

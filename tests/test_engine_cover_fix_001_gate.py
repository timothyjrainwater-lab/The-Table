"""Gate tests: WO-ENGINE-COVER-FIX-001 — Cover Bonus Value Fix.

PHB p.150-151: Three-quarters (IMPROVED) cover = +4 AC / +3 Ref.
Bug was ac_bonus=8, reflex_bonus=4. Fixed to ac_bonus=4, reflex_bonus=3.

Gate label: ENGINE-COVER-FIX
Tests: CF-001 – CF-008
"""

import pytest
from aidm.core.terrain_resolver import check_cover
from aidm.core.state import WorldState
from aidm.schemas.terrain import CoverType, CoverCheckResult


def _make_world_state(cover_type=None):
    """Construct a minimal WorldState with two entities and optional terrain cover."""
    attacker_pos = {"x": 0, "y": 0}
    defender_pos = {"x": 5, "y": 0}

    terrain_map = None
    if cover_type is not None:
        terrain_map = {
            "5,0": {
                "position": {"x": 5, "y": 0},
                "elevation": 0,
                "movement_cost": 1,
                "terrain_tags": [],
                "cover_type": cover_type,
                "is_pit": False,
                "pit_depth": 0,
                "is_ledge": False,
                "ledge_drop": 0,
            }
        }

    entities = {
        "attacker": {"position": attacker_pos, "team": "player", "defeated": False},
        "defender": {"position": defender_pos, "team": "enemy",  "defeated": False},
    }

    return WorldState(
        ruleset_version="3.5",
        entities=entities,
        active_combat={"terrain_map": terrain_map} if terrain_map else {"terrain_map": {}},
    )


# ---------------------------------------------------------------------------
# CF-001: STANDARD cover AC bonus == 4
# ---------------------------------------------------------------------------
def test_cf001_standard_cover_ac_bonus():
    ws = _make_world_state(cover_type=CoverType.STANDARD)
    result = check_cover(ws, "attacker", "defender", is_melee=True)
    assert result.ac_bonus == 4, f"Expected ac_bonus=4, got {result.ac_bonus}"


# ---------------------------------------------------------------------------
# CF-002: STANDARD cover Reflex bonus == 2
# ---------------------------------------------------------------------------
def test_cf002_standard_cover_reflex_bonus():
    ws = _make_world_state(cover_type=CoverType.STANDARD)
    result = check_cover(ws, "attacker", "defender", is_melee=True)
    assert result.reflex_bonus == 2, f"Expected reflex_bonus=2, got {result.reflex_bonus}"


# ---------------------------------------------------------------------------
# CF-003: IMPROVED cover AC bonus == 4 (was 8 — this is the bug fix)
# ---------------------------------------------------------------------------
def test_cf003_improved_cover_ac_bonus():
    ws = _make_world_state(cover_type=CoverType.IMPROVED)
    result = check_cover(ws, "attacker", "defender", is_melee=True)
    assert result.ac_bonus == 4, (
        f"Expected ac_bonus=4 (PHB p.150 three-quarters cover), got {result.ac_bonus}. "
        f"Value of 8 would indicate the pre-fix bug is still present."
    )


# ---------------------------------------------------------------------------
# CF-004: IMPROVED cover Reflex bonus == 3 (was 4)
# ---------------------------------------------------------------------------
def test_cf004_improved_cover_reflex_bonus():
    ws = _make_world_state(cover_type=CoverType.IMPROVED)
    result = check_cover(ws, "attacker", "defender", is_melee=True)
    assert result.reflex_bonus == 3, (
        f"Expected reflex_bonus=3 (PHB p.150 three-quarters cover), got {result.reflex_bonus}. "
        f"Value of 4 would indicate the pre-fix bug is still present."
    )


# ---------------------------------------------------------------------------
# CF-005: NO_COVER (None) has zero bonuses
# ---------------------------------------------------------------------------
def test_cf005_no_cover_zero_bonuses():
    ws = _make_world_state(cover_type=None)
    result = check_cover(ws, "attacker", "defender", is_melee=True)
    assert result.ac_bonus == 0, f"No cover: expected ac_bonus=0, got {result.ac_bonus}"
    assert result.reflex_bonus == 0, f"No cover: expected reflex_bonus=0, got {result.reflex_bonus}"


# ---------------------------------------------------------------------------
# CF-006: Attacker behind STANDARD cover — defender AC raised by 4
# ---------------------------------------------------------------------------
def test_cf006_standard_cover_applied_to_ac():
    ws = _make_world_state(cover_type=CoverType.STANDARD)
    result = check_cover(ws, "attacker", "defender", is_melee=True)
    assert result.cover_type == CoverType.STANDARD
    assert result.ac_bonus == 4
    assert result.blocks_aoo is True


# ---------------------------------------------------------------------------
# CF-007: Defender behind IMPROVED cover — AC raised by 4 (not 8)
# ---------------------------------------------------------------------------
def test_cf007_improved_cover_ac_not_8():
    ws = _make_world_state(cover_type=CoverType.IMPROVED)
    result = check_cover(ws, "attacker", "defender", is_melee=True)
    assert result.cover_type == CoverType.IMPROVED
    # The bug value was 8 — confirm it is not present
    assert result.ac_bonus != 8, "Bug value of 8 still present! Expected 4 per PHB p.150."
    assert result.ac_bonus == 4


# ---------------------------------------------------------------------------
# CF-008: IMPROVED cover Ref save bonus is 3 (not 4)
# ---------------------------------------------------------------------------
def test_cf008_improved_cover_reflex_not_4():
    ws = _make_world_state(cover_type=CoverType.IMPROVED)
    result = check_cover(ws, "attacker", "defender", is_melee=True)
    # The bug value was 4 — confirm it is not present
    assert result.reflex_bonus != 4, "Bug value of 4 still present! Expected 3 per PHB p.150."
    assert result.reflex_bonus == 3

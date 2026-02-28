"""Gate tests: WO-ENGINE-SAVE-DOUBLE-COUNT-FIX-001

Strips ability_mod re-addition from save_resolver.get_save_bonus().
EF.SAVE_* fields are Type 2 (base + ability_mod baked in at chargen).

SDF-001 – SDF-008 (8 tests)
"""
import pytest

from aidm.chargen.builder import build_character
from aidm.core.save_resolver import get_save_bonus, SaveType
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


def _ws_from_entity(entity):
    """Create a minimal WorldState from a single entity."""
    eid = entity[EF.ENTITY_ID]
    return WorldState(
        ruleset_version="3.5",
        entities={eid: entity},
        active_combat=None,
    )


# ---------------------------------------------------------------------------
# SDF-001: Fighter L5 CON 14 → Fort save = 6 (4 base + 2 CON), not 8
# ---------------------------------------------------------------------------

def test_sdf_001_fighter_fort_no_double():
    """SDF-001: Fighter L5 CON 14 → fort = 6 (good base 4 + CON 2), not 8."""
    entity = build_character(
        race="human",
        class_name="fighter",
        level=5,
        ability_overrides={"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 10},
    )
    ws = _ws_from_entity(entity)
    eid = entity[EF.ENTITY_ID]
    bonus = get_save_bonus(ws, eid, SaveType.FORT)
    # good save L5 = 4, CON mod = +2, baked total = 6
    assert bonus == 6, f"Expected 6, got {bonus} — double-count if 8"


# ---------------------------------------------------------------------------
# SDF-002: Rogue L5 DEX 16 → Ref save = 4 (1 poor + 3 DEX), not 7
# ---------------------------------------------------------------------------

def test_sdf_002_rogue_ref_no_double():
    """SDF-002: Rogue L5 DEX 16 → ref = 4 (poor base 1 + DEX 3), not 7."""
    entity = build_character(
        race="human",
        class_name="rogue",
        level=5,
        ability_overrides={"str": 10, "dex": 16, "con": 10, "int": 14, "wis": 10, "cha": 10},
    )
    ws = _ws_from_entity(entity)
    eid = entity[EF.ENTITY_ID]
    bonus = get_save_bonus(ws, eid, SaveType.REF)
    # Rogue good reflex L5 = 4, DEX mod = +3, baked total = 7
    # Wait — rogue has GOOD reflex. Good L5 = 4. 4 + 3 = 7. That's correct (not double).
    # With double-count: 7 + 3 = 10. After fix: 7.
    assert bonus == 7, f"Expected 7, got {bonus}"


# ---------------------------------------------------------------------------
# SDF-003: Wizard L5 WIS 12 → Will save = 5 (4 good + 1 WIS), not 6
# ---------------------------------------------------------------------------

def test_sdf_003_wizard_will_no_double():
    """SDF-003: Wizard L5 WIS 12 → will = 5 (good base 4 + WIS 1), not 6."""
    entity = build_character(
        race="human",
        class_name="wizard",
        level=5,
        ability_overrides={"str": 10, "dex": 12, "con": 10, "int": 16, "wis": 12, "cha": 10},
    )
    ws = _ws_from_entity(entity)
    eid = entity[EF.ENTITY_ID]
    bonus = get_save_bonus(ws, eid, SaveType.WILL)
    # good will L5 = 4, WIS = +1, baked = 5
    assert bonus == 5, f"Expected 5, got {bonus}"


# ---------------------------------------------------------------------------
# SDF-004: Save with Great Fortitude feat → +2 on top of correct base
# ---------------------------------------------------------------------------

def test_sdf_004_great_fortitude_no_double():
    """SDF-004: Great Fortitude adds +2, doesn't stack with double ability."""
    entity = build_character(
        race="human",
        class_name="fighter",
        level=5,
        ability_overrides={"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 10},
        feat_choices=["great_fortitude"],
    )
    ws = _ws_from_entity(entity)
    eid = entity[EF.ENTITY_ID]
    bonus = get_save_bonus(ws, eid, SaveType.FORT)
    # base 4 + CON 2 = 6, + Great Fortitude 2 = 8
    assert bonus == 8, f"Expected 8, got {bonus}"


# ---------------------------------------------------------------------------
# SDF-005: Save with condition modifier (shaken -2) → correct total
# ---------------------------------------------------------------------------

def test_sdf_005_shaken_condition():
    """SDF-005: Shaken entity gets -2 to saves (condition modifier)."""
    from aidm.schemas.conditions import create_shaken_condition
    entity = build_character(
        race="human",
        class_name="fighter",
        level=5,
        ability_overrides={"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 10},
    )
    # Apply shaken condition using proper ConditionInstance format
    shaken = create_shaken_condition(source="test", applied_at_event_id=0)
    entity[EF.CONDITIONS] = {"shaken": shaken.to_dict()}
    ws = _ws_from_entity(entity)
    eid = entity[EF.ENTITY_ID]
    bonus = get_save_bonus(ws, eid, SaveType.FORT)
    # base 4 + CON 2 = 6, shaken -2 = 4
    assert bonus == 4, f"Expected 4, got {bonus}"


# ---------------------------------------------------------------------------
# SDF-006: Paladin Divine Grace → CHA_MOD added once
# ---------------------------------------------------------------------------

def test_sdf_006_divine_grace_no_stack():
    """SDF-006: Paladin L5 CHA 16 → Divine Grace +3, single ability mod."""
    entity = build_character(
        race="human",
        class_name="paladin",
        level=5,
        ability_overrides={"str": 14, "dex": 10, "con": 14, "int": 10, "wis": 12, "cha": 16},
    )
    ws = _ws_from_entity(entity)
    eid = entity[EF.ENTITY_ID]
    # Paladin good save: Fort (good L5 = 4) + CON 2 = 6, + Divine Grace CHA 3 = 9
    fort = get_save_bonus(ws, eid, SaveType.FORT)
    assert fort == 9, f"Fort expected 9, got {fort}"
    # Will (poor L5 = 1) + WIS 1 = 2, + Divine Grace 3 = 5
    will = get_save_bonus(ws, eid, SaveType.WILL)
    assert will == 5, f"Will expected 5, got {will}"


# ---------------------------------------------------------------------------
# SDF-007: Multiclass Fighter 3 / Rogue 2 → correct combined saves
# ---------------------------------------------------------------------------

def test_sdf_007_multiclass_saves():
    """SDF-007: Fighter 3/Rogue 2 multiclass saves correct (no double ability)."""
    entity = build_character(
        race="human",
        class_name="fighter",
        class_mix={"fighter": 3, "rogue": 2},
        ability_overrides={"str": 14, "dex": 14, "con": 14, "int": 10, "wis": 10, "cha": 10},
    )
    ws = _ws_from_entity(entity)
    eid = entity[EF.ENTITY_ID]
    # Fighter 3 Fort (good) = 3, Rogue 2 Fort (poor) = 0 → base 3 + CON 2 = 5
    fort = get_save_bonus(ws, eid, SaveType.FORT)
    assert fort == 5, f"Fort expected 5, got {fort}"


# ---------------------------------------------------------------------------
# SDF-008: Negative ability mod → save correctly reduced
# ---------------------------------------------------------------------------

def test_sdf_008_negative_ability_mod():
    """SDF-008: CON 8 (-1) → Fort save reduced by exactly 1."""
    entity = build_character(
        race="human",
        class_name="fighter",
        level=5,
        ability_overrides={"str": 16, "dex": 12, "con": 8, "int": 10, "wis": 10, "cha": 10},
    )
    ws = _ws_from_entity(entity)
    eid = entity[EF.ENTITY_ID]
    bonus = get_save_bonus(ws, eid, SaveType.FORT)
    # good base L5 = 4, CON -1 = baked 3
    assert bonus == 3, f"Expected 3, got {bonus}"

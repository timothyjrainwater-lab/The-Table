"""Gate tests: WO-ENGINE-SPELL-SAVE-UNIFY-001

Unifies spell save path: _create_target_stats() routes through canonical
save_resolver.get_save_bonus() instead of reading raw EF.SAVE_*.

SSU-001 – SSU-008 (8 tests)
"""
import pytest

from aidm.chargen.builder import build_character
from aidm.core.save_resolver import get_save_bonus, SaveType
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position


def _ws_from_entity(entity):
    eid = entity[EF.ENTITY_ID]
    return WorldState(
        ruleset_version="3.5",
        entities={eid: entity},
        active_combat=None,
    )


def _make_target_stats(entity, world_state, school=""):
    """Call the private _create_target_stats function from play_loop."""
    from aidm.core.play_loop import _create_target_stats
    eid = entity[EF.ENTITY_ID]
    # Chargen stores position as tuple (0, 0); _create_target_stats expects dict/Position.
    # Normalize to dict for test compatibility.
    if isinstance(entity.get(EF.POSITION), tuple):
        entity[EF.POSITION] = {"x": entity[EF.POSITION][0], "y": entity[EF.POSITION][1]}
    return _create_target_stats(eid, world_state, school=school)


# ---------------------------------------------------------------------------
# SSU-001: Paladin Divine Grace (+3 CHA) appears in spell save via TargetStats
# ---------------------------------------------------------------------------

def test_ssu_001_divine_grace_in_spell_save():
    """SSU-001: Paladin's Divine Grace CHA bonus appears in TargetStats saves."""
    entity = build_character(
        race="human",
        class_name="paladin",
        level=5,
        ability_overrides={"str": 14, "dex": 10, "con": 14, "int": 10, "wis": 12, "cha": 16},
    )
    ws = _ws_from_entity(entity)
    ts = _make_target_stats(entity, ws, school="")
    # Fort: good L5(4) + CON(2) = 6 + Divine Grace CHA(3) = 9
    assert ts.fort_save == 9, f"Fort expected 9 (with Divine Grace), got {ts.fort_save}"
    # Will: poor L5(1) + WIS(1) = 2 + Divine Grace CHA(3) = 5
    assert ts.will_save == 5, f"Will expected 5 (with Divine Grace), got {ts.will_save}"


# ---------------------------------------------------------------------------
# SSU-002: Great Fortitude (+2) appears in spell Fort save via TargetStats
# ---------------------------------------------------------------------------

def test_ssu_002_great_fortitude_in_spell_save():
    """SSU-002: Great Fortitude feat bonus appears in TargetStats."""
    entity = build_character(
        race="human",
        class_name="fighter",
        level=5,
        ability_overrides={"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 10},
        feat_choices=["great_fortitude"],
    )
    ws = _ws_from_entity(entity)
    ts = _make_target_stats(entity, ws, school="")
    # Fort: good L5(4) + CON(2) = 6 + Great Fortitude(2) = 8
    assert ts.fort_save == 8, f"Fort expected 8, got {ts.fort_save}"


# ---------------------------------------------------------------------------
# SSU-003: Halfling +1 all saves appears in spell saves
# ---------------------------------------------------------------------------

def test_ssu_003_halfling_all_saves_in_spell():
    """SSU-003: Halfling +1 all saves appears in spell saves via TargetStats."""
    entity = build_character(
        race="halfling",
        class_name="rogue",
        level=3,
        ability_overrides={"str": 10, "dex": 16, "con": 12, "int": 10, "wis": 10, "cha": 10},
    )
    ws = _ws_from_entity(entity)
    ts = _make_target_stats(entity, ws, school="evocation")
    # Rogue L3 Fort: poor(1) + CON(1) = 2 + halfling(1) = 3
    assert ts.fort_save == 3, f"Fort expected 3, got {ts.fort_save}"
    # Rogue L3 Ref: good(3) + DEX(4, halfling +2 racial → 18) = 7 + halfling(1) = 8
    assert ts.ref_save == 8, f"Ref expected 8, got {ts.ref_save}"


# ---------------------------------------------------------------------------
# SSU-004: Dwarf +2 vs spells appears in spell saves
# ---------------------------------------------------------------------------

def test_ssu_004_dwarf_vs_spells_in_spell():
    """SSU-004: Dwarf +2 vs spells appears in spell saves via TargetStats."""
    entity = build_character(
        race="dwarf",
        class_name="fighter",
        level=3,
        ability_overrides={"str": 16, "dex": 10, "con": 16, "int": 10, "wis": 12, "cha": 8},
    )
    ws = _ws_from_entity(entity)
    # _create_target_stats passes save_descriptor="spell" when school is set
    ts = _make_target_stats(entity, ws, school="evocation")
    # Fighter L3 Fort: good(3) + CON(4, dwarf +2 racial → 18) = 7 + dwarf +2 vs spells = 9
    assert ts.fort_save == 9, f"Fort expected 9, got {ts.fort_save}"


# ---------------------------------------------------------------------------
# SSU-005: Elf +2 vs enchantment preserved
# ---------------------------------------------------------------------------

def test_ssu_005_elf_enchantment_preserved():
    """SSU-005: Elf +2 vs enchantment still works through TargetStats."""
    entity = build_character(
        race="elf",
        class_name="wizard",
        level=3,
        ability_overrides={"str": 10, "dex": 14, "con": 10, "int": 16, "wis": 12, "cha": 10},
    )
    ws = _ws_from_entity(entity)
    # Enchantment school → should get +2
    ts_ench = _make_target_stats(entity, ws, school="enchantment")
    ts_evoc = _make_target_stats(entity, ws, school="evocation")
    # Will: good L3(3) + WIS(1) = 4
    # Enchantment: +2 racial
    assert ts_ench.will_save == ts_evoc.will_save + 2, \
        f"Enchantment will={ts_ench.will_save}, evocation will={ts_evoc.will_save}, delta should be 2"


# ---------------------------------------------------------------------------
# SSU-006: Inspire Courage morale bonus appears in spell saves
# ---------------------------------------------------------------------------

def test_ssu_006_inspire_courage_in_spell():
    """SSU-006: Inspire Courage morale bonus appears in spell saves."""
    entity = build_character(
        race="human",
        class_name="fighter",
        level=5,
        ability_overrides={"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 10},
    )
    # Simulate Inspire Courage active
    entity[EF.INSPIRE_COURAGE_ACTIVE] = True
    entity[EF.INSPIRE_COURAGE_BONUS] = 1
    ws = _ws_from_entity(entity)
    ts = _make_target_stats(entity, ws, school="evocation")
    # Fort: good L5(4) + CON(2) = 6 + inspire(1) = 7
    assert ts.fort_save == 7, f"Fort expected 7 (with inspire), got {ts.fort_save}"


# ---------------------------------------------------------------------------
# SSU-007: Parity — save_resolver.get_save_bonus() == TargetStats save
# ---------------------------------------------------------------------------

def test_ssu_007_parity_resolver_vs_target_stats():
    """SSU-007: save_resolver output matches TargetStats for same entity."""
    entity = build_character(
        race="human",
        class_name="paladin",
        level=5,
        ability_overrides={"str": 14, "dex": 10, "con": 14, "int": 10, "wis": 12, "cha": 16},
        feat_choices=["great_fortitude"],
    )
    ws = _ws_from_entity(entity)
    eid = entity[EF.ENTITY_ID]
    ts = _make_target_stats(entity, ws, school="evocation")

    # Compare all three saves
    resolver_fort = get_save_bonus(ws, eid, SaveType.FORT, save_descriptor="spell", school="evocation")
    resolver_ref = get_save_bonus(ws, eid, SaveType.REF, save_descriptor="spell", school="evocation")
    resolver_will = get_save_bonus(ws, eid, SaveType.WILL, save_descriptor="spell", school="evocation")

    assert ts.fort_save == resolver_fort, f"Fort parity: TS={ts.fort_save}, resolver={resolver_fort}"
    assert ts.ref_save == resolver_ref, f"Ref parity: TS={ts.ref_save}, resolver={resolver_ref}"
    assert ts.will_save == resolver_will, f"Will parity: TS={ts.will_save}, resolver={resolver_will}"


# ---------------------------------------------------------------------------
# SSU-008: Condition save modifier (shaken -2) still applied correctly
# ---------------------------------------------------------------------------

def test_ssu_008_condition_modifier_in_spell():
    """SSU-008: Shaken condition -2 to saves flows through TargetStats."""
    entity = build_character(
        race="human",
        class_name="fighter",
        level=5,
        ability_overrides={"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 10},
    )
    from aidm.schemas.conditions import create_shaken_condition
    shaken = create_shaken_condition(source="test", applied_at_event_id=0)
    entity[EF.CONDITIONS] = {"shaken": shaken.to_dict()}
    ws = _ws_from_entity(entity)
    ts = _make_target_stats(entity, ws, school="evocation")
    # Fort: good L5(4) + CON(2) = 6, shaken -2 = 4
    assert ts.fort_save == 4, f"Fort expected 4 (shaken), got {ts.fort_save}"

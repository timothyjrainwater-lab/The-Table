"""Tests for WO-051B Policy Default Library.

Validates AD-003 Self-Sufficiency Resolution Policy compliance:
- All 20 starter object classes present
- Correct material/hardness/HP/cover values per DMG
- Typed loader produces immutable ObjectDefault instances
- Query by tag, category, material works correctly
- Provenance is always POLICY_DEFAULT
"""

import pytest
from aidm.data.policy_defaults_loader import (
    PolicyDefaultLibrary,
    ObjectDefault,
    Dimensions,
)


@pytest.fixture
def lib():
    """Load the default Policy Default Library."""
    return PolicyDefaultLibrary()


# ==============================================================================
# LIBRARY STRUCTURE
# ==============================================================================


def test_library_loads_20_objects(lib):
    """AD-003: Starter library must contain exactly 20 object classes."""
    assert len(lib) == 20


def test_library_version(lib):
    """Library has a version string."""
    assert lib.version == "1.0.0"


def test_library_policy_id(lib):
    """Library has a policy ID for provenance tracking."""
    assert lib.policy_id == "PDL-001"


def test_all_20_ids_present(lib):
    """AD-003: All 20 starter object class IDs must be present."""
    expected_ids = [
        "tavern_table", "tavern_chair", "bar_counter",
        "wooden_door", "iron_door", "stone_wall_section",
        "wooden_barrel", "stone_pillar", "wooden_crate",
        "bed_frame", "bookshelf", "chest_wooden", "chest_iron",
        "altar_stone", "throne", "hay_bale", "iron_cage",
        "campfire", "well_stone", "cart_wooden",
    ]
    for obj_id in expected_ids:
        assert obj_id in lib, f"Missing object class: {obj_id}"


def test_list_ids_sorted(lib):
    """list_ids returns sorted object class IDs."""
    ids = lib.list_ids()
    assert ids == sorted(ids)
    assert len(ids) == 20


# ==============================================================================
# OBJECT PROPERTIES (DMG COMPLIANCE)
# ==============================================================================


def test_tavern_table_properties(lib):
    """Tavern table: wood, hardness 5, HP 15, partial cover."""
    table = lib.get("tavern_table")
    assert table is not None
    assert table.name == "Tavern Table"
    assert table.material == "wood"
    assert table.hardness == 5
    assert table.hp == 15
    assert table.cover_type == "partial"
    assert table.break_dc == 15
    assert table.dimensions_ft.length == 4
    assert table.dimensions_ft.width == 3
    assert table.dimensions_ft.height == 2.5


def test_iron_door_properties(lib):
    """Iron door: iron, hardness 10, HP 60, total cover when closed."""
    door = lib.get("iron_door")
    assert door is not None
    assert door.material == "iron"
    assert door.hardness == 10
    assert door.hp == 60
    assert door.cover_type == "total"
    assert door.cover_condition == "closed"
    assert door.break_dc == 28


def test_stone_wall_section_properties(lib):
    """Stone wall: stone, hardness 8, HP 90, total cover."""
    wall = lib.get("stone_wall_section")
    assert wall is not None
    assert wall.material == "stone"
    assert wall.hardness == 8
    assert wall.hp == 90
    assert wall.cover_type == "total"
    assert wall.break_dc == 35


def test_campfire_has_null_combat_stats(lib):
    """Campfire: hazard, no hardness/HP/break DC."""
    fire = lib.get("campfire")
    assert fire is not None
    assert fire.material == "n/a"
    assert fire.hardness is None
    assert fire.hp is None
    assert fire.break_dc is None
    assert fire.cover_type == "none"
    assert fire.category == "hazard"


def test_hay_bale_organic_low_hardness(lib):
    """Hay bale: organic material, hardness 2, HP 5."""
    hay = lib.get("hay_bale")
    assert hay is not None
    assert hay.material == "organic"
    assert hay.hardness == 2
    assert hay.hp == 5
    assert hay.break_dc == 8


def test_iron_cage_no_cover(lib):
    """Iron cage: barred, no cover benefit despite iron."""
    cage = lib.get("iron_cage")
    assert cage is not None
    assert cage.material == "iron"
    assert cage.cover_type == "none"
    assert cage.cover_notes is not None
    assert "barred" in cage.cover_notes


# ==============================================================================
# PROVENANCE
# ==============================================================================


def test_all_objects_have_policy_default_provenance(lib):
    """AD-003: Every object must have POLICY_DEFAULT provenance."""
    for obj_id, obj in lib.get_all().items():
        assert obj.provenance == "POLICY_DEFAULT", f"{obj_id} has wrong provenance"


# ==============================================================================
# IMMUTABILITY
# ==============================================================================


def test_object_default_is_frozen(lib):
    """ObjectDefault instances must be immutable (frozen dataclass)."""
    table = lib.get("tavern_table")
    with pytest.raises(AttributeError):
        table.hp = 999


def test_dimensions_is_frozen(lib):
    """Dimensions instances must be immutable."""
    table = lib.get("tavern_table")
    with pytest.raises(AttributeError):
        table.dimensions_ft.length = 999


# ==============================================================================
# QUERY METHODS
# ==============================================================================


def test_get_by_tag_tavern(lib):
    """Query objects tagged 'tavern'."""
    tavern_objects = lib.get_by_tag("tavern")
    assert len(tavern_objects) >= 3  # table, chair, bar_counter at minimum
    ids = {obj.object_class_id for obj in tavern_objects}
    assert "tavern_table" in ids
    assert "tavern_chair" in ids
    assert "bar_counter" in ids


def test_get_by_tag_dungeon(lib):
    """Query objects tagged 'dungeon'."""
    dungeon_objects = lib.get_by_tag("dungeon")
    assert len(dungeon_objects) >= 3
    ids = {obj.object_class_id for obj in dungeon_objects}
    assert "wooden_door" in ids or "iron_door" in ids


def test_get_by_category_furniture(lib):
    """Query furniture category."""
    furniture = lib.get_by_category("furniture")
    assert len(furniture) >= 5  # table, chair, bar, bed, bookshelf, altar, throne
    ids = {obj.object_class_id for obj in furniture}
    assert "tavern_table" in ids
    assert "tavern_chair" in ids


def test_get_by_category_structural(lib):
    """Query structural category."""
    structural = lib.get_by_category("structural")
    ids = {obj.object_class_id for obj in structural}
    assert "wooden_door" in ids
    assert "iron_door" in ids
    assert "stone_wall_section" in ids


def test_get_by_material_wood(lib):
    """Query wood material."""
    wood = lib.get_by_material("wood")
    assert len(wood) >= 8  # Most objects are wood
    for obj in wood:
        assert obj.material == "wood"
        assert obj.hardness == 5  # DMG: wood hardness = 5


def test_get_by_material_stone(lib):
    """Query stone material."""
    stone = lib.get_by_material("stone")
    assert len(stone) >= 3
    for obj in stone:
        assert obj.material == "stone"
        assert obj.hardness == 8  # DMG: stone hardness = 8


def test_get_by_material_iron(lib):
    """Query iron material."""
    iron = lib.get_by_material("iron")
    assert len(iron) >= 3
    for obj in iron:
        assert obj.material == "iron"
        assert obj.hardness == 10  # DMG: iron hardness = 10


def test_get_missing_returns_none(lib):
    """Querying nonexistent object returns None."""
    assert lib.get("nonexistent_thing") is None


def test_contains_check(lib):
    """__contains__ works for membership tests."""
    assert "tavern_table" in lib
    assert "nonexistent" not in lib


# ==============================================================================
# MATERIAL HARDNESS CONSISTENCY (DMG TABLE)
# ==============================================================================


def test_all_wood_objects_hardness_5(lib):
    """DMG: Wood hardness is always 5."""
    for obj in lib.get_by_material("wood"):
        assert obj.hardness == 5, f"{obj.object_class_id} wood hardness != 5"


def test_all_stone_objects_hardness_8(lib):
    """DMG: Stone hardness is always 8."""
    for obj in lib.get_by_material("stone"):
        assert obj.hardness == 8, f"{obj.object_class_id} stone hardness != 8"


def test_all_iron_objects_hardness_10(lib):
    """DMG: Iron hardness is always 10."""
    for obj in lib.get_by_material("iron"):
        assert obj.hardness == 10, f"{obj.object_class_id} iron hardness != 10"


# ==============================================================================
# COVER TYPE VALIDATION
# ==============================================================================


def test_all_cover_types_valid(lib):
    """Cover type must be one of: none, partial, total."""
    valid_cover = {"none", "partial", "total"}
    for obj_id, obj in lib.get_all().items():
        assert obj.cover_type in valid_cover, f"{obj_id} has invalid cover_type: {obj.cover_type}"


def test_total_cover_objects_have_high_hp(lib):
    """Objects providing total cover should be substantial (HP >= 15)."""
    for obj in lib.get_all().values():
        if obj.cover_type == "total" and obj.hp is not None:
            assert obj.hp >= 15, f"{obj.object_class_id} total cover but HP only {obj.hp}"

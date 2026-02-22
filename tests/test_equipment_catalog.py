"""Tests for WO-053 Equipment Item Catalog.

Validates AD-005 Physical Affordance Policy compliance:
- All 35 items present (6 containers + 29 adventuring gear)
- Correct weight/cost per PHB Table 7-8
- Size categories and bulk categories valid
- Stow locations and draw actions valid
- Container capacity and fit-checking logic
- Provenance tagging (RAW or HOUSE_POLICY)
- Immutability (frozen dataclasses)

Evidence:
- PHB p.128-130 (Table 7-8: Goods and Services)
- AD-005 Physical Affordance Policy
"""

import pytest
from aidm.data.equipment_catalog_loader import (
    EquipmentCatalog,
    EquipmentItem,
    SIZE_CATEGORIES,
    BULK_CATEGORIES,
    STOW_LOCATIONS,
    DRAW_ACTIONS,
)


@pytest.fixture
def catalog():
    """Load the default Equipment Item Catalog."""
    return EquipmentCatalog()


# ==============================================================================
# CATALOG STRUCTURE
# ==============================================================================


def test_catalog_loads_35_items(catalog):
    """AD-005: Catalog must contain at least 35 gear/container items."""
    assert len(catalog) >= 35


def test_catalog_version(catalog):
    """Catalog has a version string."""
    assert catalog.version == "2.0.0"


def test_catalog_policy_id(catalog):
    """Catalog has a policy ID for provenance tracking."""
    assert catalog.policy_id == "EIC-001"


def test_list_ids_sorted(catalog):
    """list_ids returns sorted item IDs."""
    ids = catalog.list_ids()
    assert ids == sorted(ids)
    assert len(ids) >= 35


def test_all_6_containers_present(catalog):
    """AD-005: All 6 containers must be present."""
    expected = ["backpack", "belt_pouch", "sack", "chest_small", "quiver", "scroll_case"]
    for item_id in expected:
        assert item_id in catalog, f"Missing container: {item_id}"
        item = catalog.get(item_id)
        assert item.is_container, f"{item_id} should be a container"


def test_key_adventuring_gear_present(catalog):
    """AD-005: Key adventuring gear items must be present."""
    expected = [
        "rope_hemp_50ft", "rope_silk_50ft", "grappling_hook", "torch",
        "lantern_hooded", "crowbar", "bedroll", "waterskin",
        "thieves_tools", "healers_kit", "spell_component_pouch",
    ]
    for item_id in expected:
        assert item_id in catalog, f"Missing gear: {item_id}"


# ==============================================================================
# ITEM PROPERTIES (PHB COMPLIANCE)
# ==============================================================================


def test_backpack_properties(catalog):
    """Backpack: 2 lb, Medium, external, 40 lb capacity."""
    bp = catalog.get("backpack")
    assert bp is not None
    assert bp.name == "Backpack"
    assert bp.weight_lb == 2.0
    assert bp.cost_gp == 2.0
    assert bp.size_category == "Medium"
    assert bp.is_container is True
    assert bp.container_capacity_lb == 40.0
    assert bp.container_max_size == "Medium"
    assert bp.storage_slots == 12
    assert bp.stow_location == "external"
    assert bp.draw_action == "full_round"


def test_rope_hemp_properties(catalog):
    """Hemp rope: 10 lb, Medium, external."""
    rope = catalog.get("rope_hemp_50ft")
    assert rope is not None
    assert rope.weight_lb == 10.0
    assert rope.size_category == "Medium"
    assert rope.stow_location == "external"
    assert rope.provenance == "RAW"


def test_grappling_hook_properties(catalog):
    """Grappling hook: 4 lb, Small, bulky, external."""
    hook = catalog.get("grappling_hook")
    assert hook is not None
    assert hook.weight_lb == 4.0
    assert hook.size_category == "Small"
    assert hook.bulk_category == "bulky"
    assert hook.stow_location == "external"


def test_torch_properties(catalog):
    """Torch: 1 lb, Small, external."""
    torch = catalog.get("torch")
    assert torch is not None
    assert torch.weight_lb == 1.0
    assert torch.size_category == "Small"
    assert torch.stow_location == "external"


def test_belt_pouch_properties(catalog):
    """Belt pouch: 0.5 lb, Tiny, belt, 5 lb capacity."""
    pouch = catalog.get("belt_pouch")
    assert pouch is not None
    assert pouch.weight_lb == 0.5
    assert pouch.is_container is True
    assert pouch.container_capacity_lb == 5.0
    assert pouch.container_max_size == "Tiny"
    assert pouch.stow_location == "belt"
    assert pouch.draw_action == "move"


def test_pole_10ft_properties(catalog):
    """10-ft pole: 8 lb, Large, in_hand. Cannot fit in any container."""
    pole = catalog.get("pole_10ft")
    assert pole is not None
    assert pole.weight_lb == 8.0
    assert pole.size_category == "Large"
    assert pole.stow_location == "in_hand"


def test_quiver_free_draw(catalog):
    """Quiver: drawing ammunition is a free action per RAW."""
    quiver = catalog.get("quiver")
    assert quiver is not None
    assert quiver.draw_action == "free"
    assert quiver.provenance == "RAW"


def test_spell_component_pouch_free_draw(catalog):
    """Spell component pouch: accessing components is free action per RAW."""
    pouch = catalog.get("spell_component_pouch")
    assert pouch is not None
    assert pouch.draw_action == "free"
    assert pouch.provenance == "RAW"


# ==============================================================================
# PROVENANCE
# ==============================================================================


def test_all_items_have_valid_provenance(catalog):
    """AD-005: Every item must have RAW or HOUSE_POLICY provenance."""
    valid = {"RAW", "HOUSE_POLICY"}
    for item_id, item in catalog.get_all().items():
        assert item.provenance in valid, f"{item_id} has invalid provenance: {item.provenance}"


def test_raw_items_exist(catalog):
    """Some items should be RAW-sourced."""
    raw_items = catalog.get_by_provenance("RAW")
    assert len(raw_items) >= 20, "Expected at least 20 RAW items"


def test_house_policy_items_exist(catalog):
    """Container policies should be HOUSE_POLICY."""
    hp_items = catalog.get_by_provenance("HOUSE_POLICY")
    assert len(hp_items) >= 5, "Expected at least 5 HOUSE_POLICY items"


# ==============================================================================
# VALID CATEGORIES
# ==============================================================================


def test_all_size_categories_valid(catalog):
    """All items must have valid size categories."""
    for item_id, item in catalog.get_all().items():
        assert item.size_category in SIZE_CATEGORIES, (
            f"{item_id} has invalid size: {item.size_category}"
        )


def test_all_bulk_categories_valid(catalog):
    """All items must have valid bulk categories."""
    for item_id, item in catalog.get_all().items():
        assert item.bulk_category in BULK_CATEGORIES, (
            f"{item_id} has invalid bulk: {item.bulk_category}"
        )


def test_all_stow_locations_valid(catalog):
    """All items must have valid stow locations."""
    for item_id, item in catalog.get_all().items():
        assert item.stow_location in STOW_LOCATIONS, (
            f"{item_id} has invalid stow_location: {item.stow_location}"
        )


def test_all_draw_actions_valid(catalog):
    """All items must have valid draw actions."""
    for item_id, item in catalog.get_all().items():
        assert item.draw_action in DRAW_ACTIONS, (
            f"{item_id} has invalid draw_action: {item.draw_action}"
        )


# ==============================================================================
# CONTAINER FIT LOGIC (AD-005 LAYER 2)
# ==============================================================================


def test_small_item_fits_in_backpack(catalog):
    """Small item (grappling hook) fits in backpack (max Medium)."""
    hook = catalog.get("grappling_hook")
    bp = catalog.get("backpack")
    assert hook.fits_in(bp) is True


def test_medium_item_fits_in_backpack(catalog):
    """Medium item (rope) fits in backpack (max Medium)."""
    rope = catalog.get("rope_hemp_50ft")
    bp = catalog.get("backpack")
    assert rope.fits_in(bp) is True


def test_large_item_does_not_fit_in_backpack(catalog):
    """Large item (10-ft pole) does NOT fit in backpack."""
    pole = catalog.get("pole_10ft")
    bp = catalog.get("backpack")
    assert pole.fits_in(bp) is False


def test_small_item_does_not_fit_in_belt_pouch(catalog):
    """Small item (torch) does NOT fit in belt pouch (max Tiny)."""
    torch = catalog.get("torch")
    pouch = catalog.get("belt_pouch")
    assert torch.fits_in(pouch) is False


def test_tiny_item_fits_in_belt_pouch(catalog):
    """Tiny item (piton) fits in belt pouch."""
    piton = catalog.get("piton")
    pouch = catalog.get("belt_pouch")
    assert piton.fits_in(pouch) is True


def test_non_container_rejects_fit(catalog):
    """Non-container item rejects fits_in check."""
    rope = catalog.get("rope_hemp_50ft")
    torch = catalog.get("torch")
    assert torch.fits_in(rope) is False


def test_ladder_does_not_fit_anywhere(catalog):
    """Ladder (Large) cannot fit in any container."""
    ladder = catalog.get("ladder_10ft")
    for container in catalog.get_containers():
        assert ladder.fits_in(container) is False, (
            f"Ladder should not fit in {container.item_id}"
        )


def test_size_index_ordering(catalog):
    """Size index must follow Tiny < Small < Medium < Large."""
    tiny = catalog.get("piton")
    small = catalog.get("torch")
    medium = catalog.get("rope_hemp_50ft")
    large = catalog.get("pole_10ft")

    assert tiny.size_index < small.size_index
    assert small.size_index < medium.size_index
    assert medium.size_index < large.size_index


# ==============================================================================
# QUERY METHODS
# ==============================================================================


def test_get_containers(catalog):
    """get_containers returns only container items."""
    containers = catalog.get_containers()
    assert len(containers) == 6
    for c in containers:
        assert c.is_container is True
        assert c.container_capacity_lb is not None
        assert c.container_capacity_lb > 0


def test_get_by_stow_location_belt(catalog):
    """Query belt-stowed items."""
    belt_items = catalog.get_by_stow_location("belt")
    assert len(belt_items) >= 5
    for item in belt_items:
        assert item.stow_location == "belt"


def test_get_by_stow_location_external(catalog):
    """Query externally-stowed items."""
    external = catalog.get_by_stow_location("external")
    assert len(external) >= 8  # backpack, ropes, hook, torch, waterskin, etc.
    for item in external:
        assert item.stow_location == "external"


def test_get_by_size_category_tiny(catalog):
    """Query Tiny items."""
    tiny = catalog.get_by_size_category("Tiny")
    assert len(tiny) >= 8
    for item in tiny:
        assert item.size_category == "Tiny"


def test_get_by_bulk_category_bulky(catalog):
    """Query bulky items."""
    bulky = catalog.get_by_bulk_category("bulky")
    assert len(bulky) >= 3  # grappling hook, bedroll, tent, ladder
    for item in bulky:
        assert item.bulk_category == "bulky"


def test_get_missing_returns_none(catalog):
    """Querying nonexistent item returns None."""
    assert catalog.get("nonexistent_item") is None


def test_contains_check(catalog):
    """__contains__ works for membership tests."""
    assert "backpack" in catalog
    assert "nonexistent" not in catalog


# ==============================================================================
# IMMUTABILITY
# ==============================================================================


def test_equipment_item_is_frozen(catalog):
    """EquipmentItem instances must be immutable (frozen dataclass)."""
    bp = catalog.get("backpack")
    with pytest.raises(AttributeError):
        bp.weight_lb = 999.0


# ==============================================================================
# WEIGHTS (PHB SPOT CHECKS)
# ==============================================================================


def test_weight_spot_checks(catalog):
    """Spot-check weights against PHB Table 7-8."""
    checks = {
        "backpack": 2.0,
        "rope_hemp_50ft": 10.0,
        "rope_silk_50ft": 5.0,
        "grappling_hook": 4.0,
        "torch": 1.0,
        "lantern_hooded": 2.0,
        "crowbar": 5.0,
        "bedroll": 5.0,
        "waterskin": 4.0,
        "tent": 20.0,
        "pole_10ft": 8.0,
        "ladder_10ft": 20.0,
        "manacles": 2.0,
        "thieves_tools": 1.0,
        "spellbook": 3.0,
    }
    for item_id, expected_weight in checks.items():
        item = catalog.get(item_id)
        assert item is not None, f"Missing item: {item_id}"
        assert item.weight_lb == expected_weight, (
            f"{item_id}: expected {expected_weight} lb, got {item.weight_lb} lb"
        )

"""Tests for WO-055 Container Policies + Storage Location.

Validates AD-005 Layer 2 compliance:
- Container size enforcement (Large item doesn't fit in backpack)
- Container weight capacity enforcement
- Container slot enforcement
- Draw action costs per stow location
- Visible gear detection for Lens → Spark
- Container state tracking
- Edge cases (empty container, unknown items, non-container)

Evidence:
- PHB p.142: Drawing weapon rules
- PHB p.130: Equipment descriptions
- AD-005 Physical Affordance Policy (Layer 2)
"""

import pytest
from aidm.core.container_resolver import (
    ContainerResolver,
    ContainerState,
    InventoryEntry,
)
from aidm.data.equipment_catalog_loader import EquipmentCatalog
from aidm.schemas.entity_fields import EF


@pytest.fixture
def catalog():
    return EquipmentCatalog()


@pytest.fixture
def resolver(catalog):
    return ContainerResolver(catalog)


# ==============================================================================
# INVENTORY ENTRY
# ==============================================================================


def test_inventory_entry_to_dict():
    """InventoryEntry serializes to dict."""
    entry = InventoryEntry(item_id="rope_hemp_50ft", quantity=1, stow_location="external")
    d = entry.to_dict()
    assert d["item_id"] == "rope_hemp_50ft"
    assert d["quantity"] == 1
    assert d["stow_location"] == "external"
    assert "contained_in" not in d


def test_inventory_entry_from_dict():
    """InventoryEntry deserializes from dict."""
    d = {"item_id": "torch", "quantity": 5, "stow_location": "in_pack", "contained_in": "backpack"}
    entry = InventoryEntry.from_dict(d)
    assert entry.item_id == "torch"
    assert entry.quantity == 5
    assert entry.stow_location == "in_pack"
    assert entry.contained_in == "backpack"


def test_inventory_entry_roundtrip():
    """InventoryEntry round-trips through dict."""
    original = InventoryEntry(item_id="piton", quantity=10, stow_location="in_pack", contained_in="backpack")
    restored = InventoryEntry.from_dict(original.to_dict())
    assert restored.item_id == original.item_id
    assert restored.quantity == original.quantity
    assert restored.stow_location == original.stow_location
    assert restored.contained_in == original.contained_in


def test_inventory_entry_frozen():
    """InventoryEntry must be immutable."""
    entry = InventoryEntry(item_id="torch", quantity=1)
    with pytest.raises(AttributeError):
        entry.quantity = 5


# ==============================================================================
# CONTAINER SIZE CHECKS
# ==============================================================================


def test_small_item_fits_in_backpack(resolver, catalog):
    """Grappling hook (Small) fits in backpack (max Medium)."""
    state = ContainerState(
        container_id="backpack",
        capacity_lb=40.0,
        max_size="Medium",
        max_slots=12,
    )
    ok, reason = resolver.can_store_item("grappling_hook", "backpack", state)
    assert ok is True
    assert reason == ""


def test_large_item_rejected_by_backpack(resolver, catalog):
    """10-ft pole (Large) cannot fit in backpack (max Medium)."""
    state = ContainerState(
        container_id="backpack",
        capacity_lb=40.0,
        max_size="Medium",
        max_slots=12,
    )
    ok, reason = resolver.can_store_item("pole_10ft", "backpack", state)
    assert ok is False
    assert "too large" in reason


def test_small_item_rejected_by_belt_pouch(resolver, catalog):
    """Torch (Small) cannot fit in belt pouch (max Tiny)."""
    state = ContainerState(
        container_id="belt_pouch",
        capacity_lb=5.0,
        max_size="Tiny",
        max_slots=4,
    )
    ok, reason = resolver.can_store_item("torch", "belt_pouch", state)
    assert ok is False
    assert "too large" in reason


def test_tiny_item_fits_in_belt_pouch(resolver, catalog):
    """Piton (Tiny) fits in belt pouch (max Tiny)."""
    state = ContainerState(
        container_id="belt_pouch",
        capacity_lb=5.0,
        max_size="Tiny",
        max_slots=4,
    )
    ok, reason = resolver.can_store_item("piton", "belt_pouch", state)
    assert ok is True


# ==============================================================================
# CONTAINER WEIGHT CHECKS
# ==============================================================================


def test_weight_exceeds_capacity(resolver, catalog):
    """Item too heavy for remaining capacity."""
    state = ContainerState(
        container_id="backpack",
        capacity_lb=40.0,
        max_size="Medium",
        max_slots=12,
        current_weight_lb=35.0,
    )
    # Rope = 10 lb, but only 5 lb remaining
    ok, reason = resolver.can_store_item("rope_hemp_50ft", "backpack", state)
    assert ok is False
    assert "exceeds remaining capacity" in reason


def test_weight_exactly_at_capacity(resolver, catalog):
    """Item weight equals remaining capacity — fits."""
    state = ContainerState(
        container_id="backpack",
        capacity_lb=40.0,
        max_size="Medium",
        max_slots=12,
        current_weight_lb=30.0,
    )
    # Rope = 10 lb, 10 lb remaining — exact fit
    ok, reason = resolver.can_store_item("rope_hemp_50ft", "backpack", state)
    assert ok is True


# ==============================================================================
# CONTAINER SLOT CHECKS
# ==============================================================================


def test_slots_full(resolver, catalog):
    """Container at max slots rejects new items."""
    state = ContainerState(
        container_id="belt_pouch",
        capacity_lb=5.0,
        max_size="Tiny",
        max_slots=4,
        current_slots_used=4,
    )
    ok, reason = resolver.can_store_item("piton", "belt_pouch", state)
    assert ok is False
    assert "full" in reason


# ==============================================================================
# NON-CONTAINER AND UNKNOWN ITEMS
# ==============================================================================


def test_non_container_rejected(resolver, catalog):
    """Non-container item rejects storage."""
    state = ContainerState(
        container_id="rope_hemp_50ft",
        capacity_lb=0,
        max_size="Tiny",
        max_slots=0,
    )
    ok, reason = resolver.can_store_item("piton", "rope_hemp_50ft", state)
    assert ok is False
    assert "not a container" in reason


def test_unknown_item_rejected(resolver, catalog):
    """Unknown item ID rejected."""
    state = ContainerState(
        container_id="backpack",
        capacity_lb=40.0,
        max_size="Medium",
        max_slots=12,
    )
    ok, reason = resolver.can_store_item("nonexistent_thing", "backpack", state)
    assert ok is False
    assert "Unknown item" in reason


def test_unknown_container_rejected(resolver, catalog):
    """Unknown container ID rejected."""
    state = ContainerState(
        container_id="nonexistent",
        capacity_lb=0,
        max_size="Tiny",
        max_slots=0,
    )
    ok, reason = resolver.can_store_item("torch", "nonexistent", state)
    assert ok is False
    assert "Unknown container" in reason


# ==============================================================================
# CONTAINER STATE BUILDING
# ==============================================================================


def test_build_empty_container_state(resolver, catalog):
    """Empty backpack has full capacity."""
    state = resolver.build_container_state("backpack", [])
    assert state.container_id == "backpack"
    assert state.capacity_lb == 40.0
    assert state.current_weight_lb == 0.0
    assert state.current_slots_used == 0
    assert state.remaining_capacity_lb == 40.0
    assert state.remaining_slots == 12


def test_build_container_state_with_contents(resolver, catalog):
    """Container state reflects items stored inside."""
    inventory = [
        {"item_id": "torch", "quantity": 3, "stow_location": "in_pack", "contained_in": "backpack"},
        {"item_id": "piton", "quantity": 5, "stow_location": "in_pack", "contained_in": "backpack"},
        {"item_id": "rope_hemp_50ft", "quantity": 1, "stow_location": "external"},  # NOT in backpack
    ]
    state = resolver.build_container_state("backpack", inventory)
    # 3 torches @ 1 lb + 5 pitons @ 0.5 lb = 3 + 2.5 = 5.5
    assert state.current_weight_lb == 5.5
    assert state.current_slots_used == 2  # 2 entries (torch stack, piton stack)
    assert state.remaining_capacity_lb == 34.5
    assert "torch" in state.contents
    assert "piton" in state.contents


def test_build_state_ignores_other_containers(resolver, catalog):
    """Items in belt_pouch don't count against backpack."""
    inventory = [
        {"item_id": "piton", "quantity": 1, "stow_location": "belt", "contained_in": "belt_pouch"},
    ]
    state = resolver.build_container_state("backpack", inventory)
    assert state.current_weight_lb == 0.0
    assert state.current_slots_used == 0


# ==============================================================================
# CONTAINER STATE PROPERTIES
# ==============================================================================


def test_container_state_full_weight():
    """is_full_weight when at capacity."""
    state = ContainerState(
        container_id="backpack",
        capacity_lb=40.0,
        max_size="Medium",
        max_slots=12,
        current_weight_lb=40.0,
    )
    assert state.is_full_weight is True
    assert state.remaining_capacity_lb == 0.0


def test_container_state_full_slots():
    """is_full_slots when at max slots."""
    state = ContainerState(
        container_id="belt_pouch",
        capacity_lb=5.0,
        max_size="Tiny",
        max_slots=4,
        current_slots_used=4,
    )
    assert state.is_full_slots is True
    assert state.remaining_slots == 0


# ==============================================================================
# DRAW ACTION COSTS
# ==============================================================================


def test_draw_from_hand_free(resolver):
    """Drawing from in_hand is free action."""
    assert resolver.get_draw_action("torch", "in_hand") == "free"


def test_draw_from_belt_move(resolver):
    """Drawing from belt is move action."""
    assert resolver.get_draw_action("torch", "belt") == "move"


def test_draw_from_external_move(resolver):
    """Drawing from external is move action."""
    assert resolver.get_draw_action("rope_hemp_50ft", "external") == "move"


def test_draw_from_pack_full_round(resolver):
    """Drawing from in_pack is full-round action."""
    assert resolver.get_draw_action("spellbook", "in_pack") == "full_round"


def test_quiver_always_free_draw(resolver):
    """Quiver ammunition is always free action regardless of location."""
    assert resolver.get_draw_action("quiver", "external") == "free"


def test_component_pouch_always_free_draw(resolver):
    """Spell component pouch is always free action."""
    assert resolver.get_draw_action("spell_component_pouch", "belt") == "free"


# ==============================================================================
# VISIBLE GEAR (AD-005 LAYER 3 PREPARATION)
# ==============================================================================


def test_visible_gear_external(resolver):
    """External items are visible."""
    inventory = [
        {"item_id": "grappling_hook", "stow_location": "external"},
        {"item_id": "rope_hemp_50ft", "stow_location": "external"},
        {"item_id": "spellbook", "stow_location": "in_pack"},
    ]
    visible = resolver.get_visible_gear(inventory)
    assert "grappling_hook" in visible
    assert "rope_hemp_50ft" in visible
    assert "spellbook" not in visible


def test_visible_gear_belt(resolver):
    """Belt items are visible."""
    inventory = [
        {"item_id": "thieves_tools", "stow_location": "belt"},
    ]
    visible = resolver.get_visible_gear(inventory)
    assert "thieves_tools" in visible


def test_visible_gear_in_hand(resolver):
    """In-hand items are visible."""
    inventory = [
        {"item_id": "lantern_hooded", "stow_location": "in_hand"},
    ]
    visible = resolver.get_visible_gear(inventory)
    assert "lantern_hooded" in visible


def test_visible_gear_in_pack_hidden(resolver):
    """In-pack items are NOT visible."""
    inventory = [
        {"item_id": "healers_kit", "stow_location": "in_pack"},
        {"item_id": "rations_trail_1day", "stow_location": "in_pack"},
    ]
    visible = resolver.get_visible_gear(inventory)
    assert len(visible) == 0


def test_visible_gear_mixed(resolver):
    """Mixed inventory returns only visible items."""
    inventory = [
        {"item_id": "grappling_hook", "stow_location": "external"},
        {"item_id": "torch", "stow_location": "in_hand"},
        {"item_id": "thieves_tools", "stow_location": "belt"},
        {"item_id": "spellbook", "stow_location": "in_pack"},
        {"item_id": "rations_trail_1day", "stow_location": "in_pack"},
    ]
    visible = resolver.get_visible_gear(inventory)
    assert len(visible) == 3
    assert "grappling_hook" in visible
    assert "torch" in visible
    assert "thieves_tools" in visible

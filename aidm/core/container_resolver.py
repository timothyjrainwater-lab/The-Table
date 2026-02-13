"""Container and Storage resolver for WO-055 (AD-005 Layer 2).

Implements container policies and storage location tracking:
- Container capacity enforcement (weight + size checks)
- Storage location management (in_hand, belt, external, in_pack)
- Draw action costs for item retrieval
- Item stacking rules (consumables stack, unique items don't)

All policies that go beyond RAW are labeled HOUSE_POLICY provenance.

CITATIONS:
- PHB p.142: Drawing a weapon is a move action (free at BAB +1)
- PHB p.130: Equipment descriptions with weights
- AD-005: Physical Affordance Policy (HOUSE_POLICY rules for containers)
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from aidm.schemas.entity_fields import EF
from aidm.data.equipment_catalog_loader import (
    EquipmentCatalog,
    EquipmentItem,
    SIZE_CATEGORIES,
    STOW_LOCATIONS,
)


# =============================================================================
# INVENTORY ITEM ENTRY
# =============================================================================

@dataclass(frozen=True)
class InventoryEntry:
    """A single item in an entity's inventory.

    Represents one item (or stack of identical items) at a specific
    storage location.
    """
    item_id: str
    quantity: int = 1
    stow_location: str = "in_pack"  # in_hand, belt, external, in_pack
    contained_in: Optional[str] = None  # container item_id if inside a container

    def to_dict(self) -> dict:
        """Convert to entity inventory dict format."""
        d = {
            "item_id": self.item_id,
            "quantity": self.quantity,
            "stow_location": self.stow_location,
        }
        if self.contained_in is not None:
            d["contained_in"] = self.contained_in
        return d

    @staticmethod
    def from_dict(data: dict) -> "InventoryEntry":
        """Create from entity inventory dict format."""
        return InventoryEntry(
            item_id=data.get("item_id", ""),
            quantity=data.get("quantity", 1),
            stow_location=data.get("stow_location", "in_pack"),
            contained_in=data.get("contained_in"),
        )


# =============================================================================
# CONTAINER STATE TRACKING
# =============================================================================

@dataclass
class ContainerState:
    """Tracks current contents of a container.

    Not frozen — mutable during inventory operations, but only through
    the ContainerResolver methods (never by Spark).
    """
    container_id: str
    capacity_lb: float
    max_size: str
    max_slots: int
    current_weight_lb: float = 0.0
    current_slots_used: int = 0
    contents: List[str] = field(default_factory=list)  # List of item_ids

    @property
    def remaining_capacity_lb(self) -> float:
        return max(0.0, self.capacity_lb - self.current_weight_lb)

    @property
    def remaining_slots(self) -> int:
        return max(0, self.max_slots - self.current_slots_used)

    @property
    def is_full_weight(self) -> bool:
        return self.current_weight_lb >= self.capacity_lb

    @property
    def is_full_slots(self) -> bool:
        return self.current_slots_used >= self.max_slots


# =============================================================================
# CONTAINER RESOLVER
# =============================================================================

class ContainerResolver:
    """Resolves container policy checks (AD-005 Layer 2).

    Determines whether items can be stored in containers, tracks
    container contents, and computes draw action costs.

    Usage:
        catalog = EquipmentCatalog()
        resolver = ContainerResolver(catalog)

        # Can this item fit?
        ok, reason = resolver.can_store_item("grappling_hook", "backpack", container_state)

        # What action to retrieve?
        action = resolver.get_draw_action("grappling_hook", "in_pack")
    """

    def __init__(self, catalog: EquipmentCatalog):
        self._catalog = catalog

    def can_store_item(
        self,
        item_id: str,
        container_id: str,
        container_state: ContainerState,
    ) -> Tuple[bool, str]:
        """Check if an item can be stored in a container.

        AD-005 Layer 2 rules:
        1. Item size_category must be <= container's container_max_size
        2. Item weight must not exceed remaining capacity
        3. Container must have remaining slots

        Args:
            item_id: The item to store.
            container_id: The container to store it in.
            container_state: Current state of the container.

        Returns:
            Tuple of (can_store: bool, reason: str).
            reason is "" if can_store is True, otherwise explains why not.
        """
        item = self._catalog.get(item_id)
        container = self._catalog.get(container_id)

        if item is None:
            return False, f"Unknown item: {item_id}"
        if container is None:
            return False, f"Unknown container: {container_id}"
        if not container.is_container:
            return False, f"{container_id} is not a container"

        # Size check
        if not item.fits_in(container):
            return False, (
                f"{item.name} ({item.size_category}) is too large for "
                f"{container.name} (max {container.container_max_size})"
            )

        # Weight check
        if item.weight_lb > container_state.remaining_capacity_lb:
            return False, (
                f"{item.name} ({item.weight_lb} lb) exceeds remaining capacity "
                f"({container_state.remaining_capacity_lb:.1f} lb) of {container.name}"
            )

        # Slot check
        if container_state.is_full_slots:
            return False, f"{container.name} is full ({container_state.max_slots} slots)"

        return True, ""

    def build_container_state(
        self,
        container_id: str,
        inventory: List[Dict[str, Any]],
    ) -> ContainerState:
        """Build a ContainerState from an entity's inventory.

        Scans the inventory for items contained in the specified container
        and computes current weight/slot usage.

        Args:
            container_id: The container item_id.
            inventory: Entity's inventory list.

        Returns:
            ContainerState with current contents.
        """
        container = self._catalog.get(container_id)
        if container is None or not container.is_container:
            return ContainerState(
                container_id=container_id,
                capacity_lb=0.0,
                max_size="Tiny",
                max_slots=0,
            )

        state = ContainerState(
            container_id=container_id,
            capacity_lb=container.container_capacity_lb or 0.0,
            max_size=container.container_max_size or "Tiny",
            max_slots=container.storage_slots or 0,
        )

        for entry in inventory:
            if isinstance(entry, dict):
                contained_in = entry.get("contained_in")
                if contained_in == container_id:
                    item_id = entry.get("item_id", "")
                    quantity = entry.get("quantity", 1)
                    catalog_item = self._catalog.get(item_id)
                    if catalog_item is not None:
                        state.current_weight_lb += catalog_item.weight_lb * quantity
                    else:
                        state.current_weight_lb += entry.get("weight_lb", 0.0) * quantity
                    state.current_slots_used += 1
                    state.contents.append(item_id)

        return state

    def get_draw_action(self, item_id: str, stow_location: str) -> str:
        """Get the action cost to draw/retrieve an item.

        AD-005 stow location rules:
        - in_hand: free action (already held)
        - belt: move action
        - external: move action
        - in_pack: full-round action (must open/dig through pack)

        The catalog item's draw_action may override if it specifies
        a faster draw (e.g., quiver = free action for ammunition).

        Args:
            item_id: The item to draw.
            stow_location: Where the item is currently stored.

        Returns:
            One of "free", "move", "full_round", "standard".
        """
        item = self._catalog.get(item_id)

        # If the item has a specific draw_action that's faster than the
        # location-based default, use the item's draw_action
        if item is not None and item.draw_action == "free":
            return "free"

        # Location-based defaults
        location_draw = {
            "in_hand": "free",
            "belt": "move",
            "external": "move",
            "in_pack": "full_round",
        }
        return location_draw.get(stow_location, "move")

    def get_visible_gear(self, inventory: List[Dict[str, Any]]) -> List[str]:
        """Get list of externally visible gear item IDs.

        Items at stow_location "external", "belt", or "in_hand" are
        visible to other characters. Items "in_pack" are hidden.

        Used by Lens to build gear affordance tags for Spark (AD-005 Layer 3).

        Args:
            inventory: Entity's inventory list.

        Returns:
            List of item_id strings for visible gear.
        """
        visible = []
        for entry in inventory:
            if isinstance(entry, dict):
                loc = entry.get("stow_location", "in_pack")
                if loc in ("external", "belt", "in_hand"):
                    visible.append(entry.get("item_id", ""))
            elif isinstance(entry, str):
                # Simple string entries — check catalog default
                item = self._catalog.get(entry)
                if item is not None and item.stow_location in ("external", "belt", "in_hand"):
                    visible.append(entry)
        return visible

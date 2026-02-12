"""Equipment Item Catalog loader for WO-053 (AD-005).

Implements AD-005 Physical Affordance Policy:
- Loads adventuring gear, containers, and consumables from equipment_catalog.json
- Provides typed access to item properties (weight, size, bulk, storage, draw action)
- Every item tagged with RAW or HOUSE_POLICY provenance
- Deterministic: same item_id always returns identical data

COVERAGE (AD-005):
- Containers (backpack, belt pouch, sack, chest, quiver, scroll case)
- Adventuring gear (rope, torch, crowbar, tools, consumables)
- NOT weapons (handled by aidm/schemas/attack.py Weapon dataclass)
- NOT armor (future WO)
- NOT magic items (future WO)
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass


# Path to the JSON data file
_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
_CATALOG_PATH = os.path.join(_DATA_DIR, "equipment_catalog.json")


# Valid size categories ordered by increasing size
SIZE_CATEGORIES = ("Tiny", "Small", "Medium", "Large")

# Valid bulk categories
BULK_CATEGORIES = ("compact", "standard", "bulky")

# Valid stow locations
STOW_LOCATIONS = ("in_hand", "belt", "external", "in_pack")

# Valid draw actions
DRAW_ACTIONS = ("free", "move", "full_round", "standard")


@dataclass(frozen=True)
class EquipmentItem:
    """A single equipment item from the catalog.

    All fields are immutable (frozen dataclass) and deterministic.
    Provenance is RAW (from PHB) or HOUSE_POLICY (system-declared).
    """
    item_id: str
    name: str
    weight_lb: float
    cost_gp: float
    size_category: str  # Tiny, Small, Medium, Large
    bulk_category: str  # compact, standard, bulky
    stow_location: str  # in_hand, belt, external, in_pack
    draw_action: str  # free, move, full_round, standard
    description: str
    provenance: str  # RAW or HOUSE_POLICY
    source_notes: str
    # Container fields (None for non-containers)
    container_capacity_lb: Optional[float] = None
    container_max_size: Optional[str] = None
    storage_slots: Optional[int] = None
    is_container: bool = False

    @property
    def size_index(self) -> int:
        """Numeric index for size comparison. Higher = larger."""
        try:
            return SIZE_CATEGORIES.index(self.size_category)
        except ValueError:
            return -1

    def fits_in(self, container: "EquipmentItem") -> bool:
        """Check if this item can fit inside a container.

        AD-005 Layer 2 rule: item size_category must be <=
        container.container_max_size, and item weight must be <=
        remaining capacity (caller must track remaining).

        Args:
            container: The container to check against.

        Returns:
            True if item's size category fits the container's max size.
            Does NOT check weight (caller's responsibility to track load).
        """
        if not container.is_container:
            return False
        if container.container_max_size is None:
            return False
        try:
            max_idx = SIZE_CATEGORIES.index(container.container_max_size)
            item_idx = SIZE_CATEGORIES.index(self.size_category)
            return item_idx <= max_idx
        except ValueError:
            return False


class EquipmentCatalog:
    """Loader and accessor for the Equipment Item Catalog.

    Usage:
        catalog = EquipmentCatalog()
        rope = catalog.get("rope_hemp_50ft")
        print(rope.weight_lb)  # 10.0
        print(rope.stow_location)  # "external"

        # Query containers
        containers = catalog.get_containers()

        # Query by stow location
        belt_items = catalog.get_by_stow_location("belt")

        # Check if item fits in container
        backpack = catalog.get("backpack")
        hook = catalog.get("grappling_hook")
        print(hook.fits_in(backpack))  # True (Small fits in Medium-max)
    """

    def __init__(self, data_path: str = _CATALOG_PATH):
        """Load the equipment catalog from JSON.

        Args:
            data_path: Path to the equipment_catalog.json file.
                       Defaults to the bundled data file.
        """
        self._items: Dict[str, EquipmentItem] = {}
        self._version: str = "unknown"
        self._policy_id: str = "unknown"
        self._load(data_path)

    def _load(self, data_path: str) -> None:
        """Parse JSON and build typed EquipmentItem instances."""
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data.get("_meta", {})
        self._version = meta.get("catalog_version", "unknown")
        self._policy_id = meta.get("policy_id", "unknown")

        # Load containers
        for item_id, item_data in data.get("containers", {}).items():
            self._items[item_id] = self._parse_item(item_id, item_data, is_container=True)

        # Load adventuring gear
        for item_id, item_data in data.get("adventuring_gear", {}).items():
            self._items[item_id] = self._parse_item(item_id, item_data, is_container=False)

    def _parse_item(self, item_id: str, item_data: dict, is_container: bool) -> EquipmentItem:
        """Parse a single item from JSON data."""
        return EquipmentItem(
            item_id=item_id,
            name=item_data["name"],
            weight_lb=item_data.get("weight_lb", 0.0),
            cost_gp=item_data.get("cost_gp", 0.0),
            size_category=item_data.get("size_category", "Small"),
            bulk_category=item_data.get("bulk_category", "standard"),
            stow_location=item_data.get("stow_location", "in_pack"),
            draw_action=item_data.get("draw_action", "move"),
            description=item_data.get("description", ""),
            provenance=item_data.get("provenance", "HOUSE_POLICY"),
            source_notes=item_data.get("source_notes", ""),
            container_capacity_lb=item_data.get("container_capacity_lb"),
            container_max_size=item_data.get("container_max_size"),
            storage_slots=item_data.get("storage_slots"),
            is_container=is_container,
        )

    @property
    def version(self) -> str:
        """Catalog version string."""
        return self._version

    @property
    def policy_id(self) -> str:
        """Policy ID for provenance tracking."""
        return self._policy_id

    def get(self, item_id: str) -> Optional[EquipmentItem]:
        """Get an item by ID.

        Args:
            item_id: The item identifier (e.g., "backpack", "rope_hemp_50ft")

        Returns:
            EquipmentItem if found, None otherwise.
        """
        return self._items.get(item_id)

    def get_all(self) -> Dict[str, EquipmentItem]:
        """Get all items.

        Returns:
            Dict mapping item_id to EquipmentItem.
        """
        return dict(self._items)

    def get_containers(self) -> List[EquipmentItem]:
        """Get all container items.

        Returns:
            List of EquipmentItem instances that are containers.
        """
        return [item for item in self._items.values() if item.is_container]

    def get_by_stow_location(self, location: str) -> List[EquipmentItem]:
        """Get all items with a specific default stow location.

        Args:
            location: One of "in_hand", "belt", "external", "in_pack"

        Returns:
            List of matching EquipmentItem instances.
        """
        return [item for item in self._items.values() if item.stow_location == location]

    def get_by_size_category(self, size: str) -> List[EquipmentItem]:
        """Get all items of a specific size category.

        Args:
            size: One of "Tiny", "Small", "Medium", "Large"

        Returns:
            List of matching EquipmentItem instances.
        """
        return [item for item in self._items.values() if item.size_category == size]

    def get_by_bulk_category(self, bulk: str) -> List[EquipmentItem]:
        """Get all items of a specific bulk category.

        Args:
            bulk: One of "compact", "standard", "bulky"

        Returns:
            List of matching EquipmentItem instances.
        """
        return [item for item in self._items.values() if item.bulk_category == bulk]

    def get_by_provenance(self, provenance: str) -> List[EquipmentItem]:
        """Get all items with a specific provenance.

        Args:
            provenance: "RAW" or "HOUSE_POLICY"

        Returns:
            List of matching EquipmentItem instances.
        """
        return [item for item in self._items.values() if item.provenance == provenance]

    def list_ids(self) -> List[str]:
        """Get all item IDs.

        Returns:
            Sorted list of item_id strings.
        """
        return sorted(self._items.keys())

    def __len__(self) -> int:
        """Number of items in the catalog."""
        return len(self._items)

    def __contains__(self, item_id: str) -> bool:
        """Check if an item exists."""
        return item_id in self._items

"""Equipment Item Catalog loader for WO-053 (AD-005) + WO-CHARGEN-FOUNDATION-001.

Implements AD-005 Physical Affordance Policy:
- Loads adventuring gear, containers, and consumables from equipment_catalog.json
- Provides typed access to item properties (weight, size, bulk, storage, draw action)
- Every item tagged with RAW or HOUSE_POLICY provenance
- Deterministic: same item_id always returns identical data

COVERAGE (AD-005 + WO-CHARGEN-FOUNDATION-001):
- Containers (backpack, belt pouch, sack, chest, quiver, scroll case)
- Adventuring gear (rope, torch, crowbar, tools, consumables)
- Weapons (PHB Table 7-5: simple, martial, exotic)
- Armor and Shields (PHB Table 7-6: light, medium, heavy, shields)
- NOT magic items (future WO)
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

from aidm.schemas.attack import Weapon


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


@dataclass(frozen=True)
class WeaponTemplate:
    """Weapon definition from the catalog (PHB Table 7-5).

    WO-CHARGEN-FOUNDATION-001 (Part C, GAP-CG-003).
    Catalog-focused template; use to_weapon() to convert to resolution Weapon.
    """

    item_id: str
    """Unique identifier (e.g., 'longsword', 'dagger')."""

    name: str
    """Display name (e.g., 'Longsword')."""

    damage_dice: str
    """Damage dice expression (e.g., '1d8', '2d6')."""

    critical_range: int
    """Minimum d20 roll to threaten a critical (e.g., 19 for 19-20)."""

    critical_multiplier: int
    """Critical hit multiplier (x2, x3, x4)."""

    damage_type: str
    """Damage type: 'slashing', 'piercing', 'bludgeoning'."""

    weapon_type: str
    """Weapon type: 'light', 'one-handed', 'two-handed', 'ranged'."""

    proficiency_group: str
    """Proficiency group: 'simple', 'martial', 'exotic'."""

    weight_lb: float
    """Weight in pounds."""

    cost_gp: float
    """Cost in gold pieces."""

    range_increment_ft: int
    """Range increment in feet (0 for melee)."""

    size_category: str
    """Size category for the weapon (e.g., 'Medium')."""

    provenance: str
    """'RAW' for all PHB weapons."""

    source_notes: str
    """PHB page reference."""

    def to_weapon(self, damage_bonus: int = 0) -> Weapon:
        """Convert catalog template to resolution Weapon.

        Args:
            damage_bonus: Flat damage bonus from enhancement/magic (not STR).

        Returns:
            Weapon instance for attack resolution.
        """
        is_two_handed = self.weapon_type == "two-handed"
        grip = "two-handed" if is_two_handed else "one-handed"
        return Weapon(
            damage_dice=self.damage_dice,
            damage_bonus=damage_bonus,
            damage_type=self.damage_type,
            critical_multiplier=self.critical_multiplier,
            critical_range=self.critical_range,
            is_two_handed=is_two_handed,
            grip=grip,
            weapon_type=self.weapon_type,
            range_increment=self.range_increment_ft,
        )


@dataclass(frozen=True)
class ArmorTemplate:
    """Armor definition from the catalog (PHB Table 7-6).

    WO-CHARGEN-FOUNDATION-001 (Part C, GAP-CG-003).
    """

    item_id: str
    """Unique identifier (e.g., 'full_plate', 'chain_shirt')."""

    name: str
    """Display name (e.g., 'Full Plate')."""

    armor_type: str
    """Armor type: 'light', 'medium', 'heavy', 'shield'."""

    ac_bonus: int
    """AC bonus provided."""

    max_dex_bonus: int
    """Maximum Dexterity bonus (99 for no limit)."""

    armor_check_penalty: int
    """Armor check penalty (always negative or 0)."""

    arcane_spell_failure: int
    """Arcane spell failure percentage (0-100)."""

    weight_lb: float
    """Weight in pounds."""

    cost_gp: float
    """Cost in gold pieces."""

    base_speed_30: int
    """Speed for creatures with 30 ft base speed."""

    base_speed_20: int
    """Speed for creatures with 20 ft base speed."""

    size_category: str
    """Size category (e.g., 'Medium')."""

    provenance: str
    """'RAW' for all PHB armor."""

    source_notes: str
    """PHB page reference."""


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

        # Query weapons and armor
        sword = catalog.get_weapon("longsword")
        plate = catalog.get_armor("full_plate")
        simple_weapons = catalog.get_weapons_by_proficiency("simple")
        heavy_armor = catalog.get_armor_by_type("heavy")
    """

    def __init__(self, data_path: str = _CATALOG_PATH):
        """Load the equipment catalog from JSON.

        Args:
            data_path: Path to the equipment_catalog.json file.
                       Defaults to the bundled data file.
        """
        self._items: Dict[str, EquipmentItem] = {}
        self._weapons: Dict[str, WeaponTemplate] = {}
        self._armor: Dict[str, ArmorTemplate] = {}
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

        # Load weapons (WO-CHARGEN-FOUNDATION-001)
        for item_id, item_data in data.get("weapons", {}).items():
            self._weapons[item_id] = self._parse_weapon(item_id, item_data)

        # Load armor (WO-CHARGEN-FOUNDATION-001)
        for item_id, item_data in data.get("armor", {}).items():
            self._armor[item_id] = self._parse_armor(item_id, item_data)

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

    def _parse_weapon(self, item_id: str, item_data: dict) -> WeaponTemplate:
        """Parse a single weapon from JSON data."""
        return WeaponTemplate(
            item_id=item_id,
            name=item_data["name"],
            damage_dice=item_data["damage_dice"],
            critical_range=item_data["critical_range"],
            critical_multiplier=item_data["critical_multiplier"],
            damage_type=item_data["damage_type"],
            weapon_type=item_data["weapon_type"],
            proficiency_group=item_data["proficiency_group"],
            weight_lb=item_data.get("weight_lb", 0.0),
            cost_gp=item_data.get("cost_gp", 0.0),
            range_increment_ft=item_data.get("range_increment_ft", 0),
            size_category=item_data.get("size_category", "Medium"),
            provenance=item_data.get("provenance", "RAW"),
            source_notes=item_data.get("source_notes", ""),
        )

    def _parse_armor(self, item_id: str, item_data: dict) -> ArmorTemplate:
        """Parse a single armor from JSON data."""
        return ArmorTemplate(
            item_id=item_id,
            name=item_data["name"],
            armor_type=item_data["armor_type"],
            ac_bonus=item_data["ac_bonus"],
            max_dex_bonus=item_data["max_dex_bonus"],
            armor_check_penalty=item_data["armor_check_penalty"],
            arcane_spell_failure=item_data["arcane_spell_failure"],
            weight_lb=item_data.get("weight_lb", 0.0),
            cost_gp=item_data.get("cost_gp", 0.0),
            base_speed_30=item_data.get("base_speed_30", 30),
            base_speed_20=item_data.get("base_speed_20", 20),
            size_category=item_data.get("size_category", "Medium"),
            provenance=item_data.get("provenance", "RAW"),
            source_notes=item_data.get("source_notes", ""),
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

    # --- Weapon accessors (WO-CHARGEN-FOUNDATION-001) ---

    def get_weapon(self, item_id: str) -> Optional[WeaponTemplate]:
        """Get a weapon by ID.

        Args:
            item_id: The weapon identifier (e.g., "longsword", "dagger").

        Returns:
            WeaponTemplate if found, None otherwise.
        """
        return self._weapons.get(item_id)

    def get_all_weapons(self) -> Dict[str, WeaponTemplate]:
        """Get all weapons.

        Returns:
            Dict mapping item_id to WeaponTemplate.
        """
        return dict(self._weapons)

    def get_weapons_by_proficiency(self, group: str) -> List[WeaponTemplate]:
        """Get all weapons in a proficiency group.

        Args:
            group: Proficiency group — "simple", "martial", or "exotic".

        Returns:
            List of matching WeaponTemplate instances.
        """
        return [w for w in self._weapons.values() if w.proficiency_group == group]

    def list_weapon_ids(self) -> List[str]:
        """Get all weapon IDs.

        Returns:
            Sorted list of weapon item_id strings.
        """
        return sorted(self._weapons.keys())

    # --- Armor accessors (WO-CHARGEN-FOUNDATION-001) ---

    def get_armor(self, item_id: str) -> Optional[ArmorTemplate]:
        """Get an armor by ID.

        Args:
            item_id: The armor identifier (e.g., "full_plate", "chain_shirt").

        Returns:
            ArmorTemplate if found, None otherwise.
        """
        return self._armor.get(item_id)

    def get_all_armor(self) -> Dict[str, ArmorTemplate]:
        """Get all armor.

        Returns:
            Dict mapping item_id to ArmorTemplate.
        """
        return dict(self._armor)

    def get_armor_by_type(self, armor_type: str) -> List[ArmorTemplate]:
        """Get all armor of a specific type.

        Args:
            armor_type: Armor type — "light", "medium", "heavy", or "shield".

        Returns:
            List of matching ArmorTemplate instances.
        """
        return [a for a in self._armor.values() if a.armor_type == armor_type]

    def list_armor_ids(self) -> List[str]:
        """Get all armor IDs.

        Returns:
            Sorted list of armor item_id strings.
        """
        return sorted(self._armor.keys())

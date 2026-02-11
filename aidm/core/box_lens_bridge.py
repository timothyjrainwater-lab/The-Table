"""Box-Lens Bridge — Integration layer between geometric engine and data index.

The BoxLensBridge synchronizes entity and cell data between Box (BattleGrid)
and Lens (LensIndex), enabling queries through the Lens while Box maintains
authoritative game state.

WO-012: Box-Lens Bridge
Reference: WO-001 (BattleGrid), WO-007 (LensIndex)
"""

from typing import List, Optional

from aidm.schemas.position import Position
from aidm.schemas.geometry import PropertyMask, SizeCategory
from aidm.core.geometry_engine import BattleGrid
from aidm.core.lens_index import LensIndex, SourceTier


# ==============================================================================
# ENTITY CLASS MAPPING
# ==============================================================================

def _infer_entity_class(entity_id: str) -> str:
    """Infer entity class from entity ID prefix.

    Args:
        entity_id: Entity identifier

    Returns:
        Entity class: 'creature', 'object', 'terrain', or 'unknown'
    """
    if entity_id.startswith("creature_"):
        return "creature"
    elif entity_id.startswith("object_"):
        return "object"
    elif entity_id.startswith("terrain_"):
        return "terrain"
    else:
        return "unknown"


# ==============================================================================
# BOX-LENS BRIDGE
# ==============================================================================

class BoxLensBridge:
    """Integration layer between Box (BattleGrid) and Lens (LensIndex).

    Provides bidirectional data flow:
    - Grid → Lens: Sync entity positions, sizes, and cell properties
    - Lens → Box: Query cached data through Lens spatial index

    All synced facts use BOX tier (highest authority) to ensure mechanical
    facts override any LLM-generated data.
    """

    def __init__(self, grid: BattleGrid, lens: LensIndex):
        """Create a BoxLensBridge.

        Args:
            grid: BattleGrid instance (Box)
            lens: LensIndex instance (Lens)
        """
        self._grid = grid
        self._lens = lens

    @property
    def grid(self) -> BattleGrid:
        """Access the underlying BattleGrid."""
        return self._grid

    @property
    def lens(self) -> LensIndex:
        """Access the underlying LensIndex."""
        return self._lens

    # ==========================================================================
    # SYNC: Grid → Lens (Entity)
    # ==========================================================================

    def sync_entity_to_lens(self, entity_id: str, turn: int) -> bool:
        """Sync a single entity from Grid to Lens.

        Reads entity position and size from Grid and stores as BOX-tier
        facts in Lens.

        Args:
            entity_id: Entity to sync
            turn: Current turn number for timestamps

        Returns:
            True if entity was synced, False if entity not in grid
        """
        if entity_id not in self._grid._entities:
            return False

        pos, size = self._grid._entities[entity_id]

        # Ensure entity exists in Lens
        entity_class = _infer_entity_class(entity_id)
        if self._lens.get_entity(entity_id) is None:
            self._lens.register_entity(entity_id, entity_class, turn)

        # Sync position (uses Lens spatial index)
        self._lens.set_position(entity_id, pos, turn)

        # Sync size as BOX-tier fact
        self._lens.set_fact(
            entity_id=entity_id,
            attribute="size",
            value=size.value,
            source_tier=SourceTier.BOX,
            turn=turn,
        )

        return True

    def sync_all_entities(self, turn: int) -> int:
        """Sync all grid entities to Lens.

        Args:
            turn: Current turn number

        Returns:
            Number of entities synced
        """
        count = 0
        for entity_id in self._grid._entities.keys():
            if self.sync_entity_to_lens(entity_id, turn):
                count += 1
        return count

    # ==========================================================================
    # SYNC: Grid → Lens (Cells)
    # ==========================================================================

    def sync_cell_to_lens(self, pos: Position, turn: int) -> bool:
        """Sync a single cell from Grid to Lens.

        Stores cell properties (cell_mask, elevation, border_masks) as
        BOX-tier facts.

        Args:
            pos: Cell position
            turn: Current turn number

        Returns:
            True if cell was synced, False if position out of bounds
        """
        if not self._grid.in_bounds(pos):
            return False

        cell = self._grid.get_cell(pos)

        # Create a cell entity in Lens if needed
        cell_entity_id = f"cell_{pos.x}_{pos.y}"

        if self._lens.get_entity(cell_entity_id) is None:
            self._lens.register_entity(cell_entity_id, "terrain", turn)

        # Sync cell mask
        self._lens.set_fact(
            entity_id=cell_entity_id,
            attribute="cell_mask",
            value=cell.cell_mask.to_int(),
            source_tier=SourceTier.BOX,
            turn=turn,
        )

        # Sync elevation
        self._lens.set_fact(
            entity_id=cell_entity_id,
            attribute="elevation",
            value=cell.elevation,
            source_tier=SourceTier.BOX,
            turn=turn,
        )

        # Sync border masks
        border_data = {
            direction.value: mask.to_int()
            for direction, mask in cell.border_masks.items()
        }
        self._lens.set_fact(
            entity_id=cell_entity_id,
            attribute="border_masks",
            value=border_data,
            source_tier=SourceTier.BOX,
            turn=turn,
        )

        # Store position for cell entity
        self._lens.set_position(cell_entity_id, pos, turn)

        return True

    def sync_grid_to_lens(self, turn: int) -> int:
        """Sync entire grid to Lens.

        Args:
            turn: Current turn number

        Returns:
            Number of cells synced
        """
        count = 0
        for y in range(self._grid.height):
            for x in range(self._grid.width):
                pos = Position(x=x, y=y)
                if self.sync_cell_to_lens(pos, turn):
                    count += 1
        return count

    # ==========================================================================
    # QUERY: Lens → Box
    # ==========================================================================

    def get_entity_size(self, entity_id: str) -> Optional[SizeCategory]:
        """Query Lens for entity size.

        Args:
            entity_id: Entity to query

        Returns:
            SizeCategory or None if not found
        """
        fact = self._lens.get_fact(entity_id, "size")
        if fact is None:
            return None

        # Convert size value string to SizeCategory enum
        try:
            return SizeCategory(fact.value)
        except (ValueError, KeyError):
            return None

    def get_entity_position(self, entity_id: str) -> Optional[Position]:
        """Query Lens for entity position.

        Args:
            entity_id: Entity to query

        Returns:
            Position or None if not found
        """
        return self._lens.get_position(entity_id)

    def get_entities_in_area(self, positions: List[Position]) -> List[str]:
        """Get all entities at any of the given positions.

        Uses Lens spatial index for efficient lookup.

        Args:
            positions: List of positions to check

        Returns:
            Deduplicated list of entity IDs
        """
        seen = set()
        result = []

        for pos in positions:
            for entity_id in self._lens.get_entities_at(pos):
                if entity_id not in seen:
                    seen.add(entity_id)
                    result.append(entity_id)

        return result

    def get_cell_properties(self, pos: Position) -> Optional[PropertyMask]:
        """Query Lens for cell property mask.

        Args:
            pos: Cell position

        Returns:
            PropertyMask or None if not found
        """
        cell_entity_id = f"cell_{pos.x}_{pos.y}"
        fact = self._lens.get_fact(cell_entity_id, "cell_mask")
        if fact is None:
            return None

        return PropertyMask.from_int(fact.value)

    # ==========================================================================
    # VALIDATION
    # ==========================================================================

    def validate_consistency(self, turn: int) -> List[str]:
        """Check that Grid and Lens are in sync.

        Validates:
        1. All grid entities exist in Lens
        2. All Lens entities (class != terrain) exist in grid
        3. Positions match
        4. Sizes match

        Args:
            turn: Current turn number (for context)

        Returns:
            List of discrepancy error strings, empty if consistent
        """
        errors = []

        # 1. Check all grid entities exist in Lens
        for entity_id, (grid_pos, grid_size) in self._grid._entities.items():
            profile = self._lens.get_entity(entity_id)
            if profile is None:
                errors.append(f"Entity {entity_id} in Grid but not in Lens")
                continue

            # 3. Check position matches
            lens_pos = self._lens.get_position(entity_id)
            if lens_pos is None:
                errors.append(f"Entity {entity_id} has no position in Lens")
            elif lens_pos != grid_pos:
                errors.append(
                    f"Position mismatch for {entity_id}: "
                    f"Grid={grid_pos}, Lens={lens_pos}"
                )

            # 4. Check size matches
            lens_size = self.get_entity_size(entity_id)
            if lens_size is None:
                errors.append(f"Entity {entity_id} has no size in Lens")
            elif lens_size != grid_size:
                errors.append(
                    f"Size mismatch for {entity_id}: "
                    f"Grid={grid_size.value}, Lens={lens_size.value}"
                )

        # 2. Check all Lens entities (non-terrain) exist in Grid
        for entity_id in self._lens.list_entities():
            profile = self._lens.get_entity(entity_id)
            if profile is None:
                continue

            # Skip terrain entities (cells)
            if profile.entity_class == "terrain":
                continue

            if entity_id not in self._grid._entities:
                errors.append(f"Entity {entity_id} in Lens but not in Grid")

        return errors

    # ==========================================================================
    # SNAPSHOT
    # ==========================================================================

    def snapshot(self) -> 'BoxLensBridge':
        """Create an independent copy of this bridge.

        Both the Grid and Lens are deep-copied.

        Returns:
            Independent BoxLensBridge copy
        """
        return BoxLensBridge(
            grid=self._grid.snapshot(),
            lens=self._lens.snapshot(),
        )

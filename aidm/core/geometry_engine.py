"""BattleGrid geometry engine for box geometry system.

Implements the uniform grid data structure with:
- O(1) cell access via flat array indexing
- Border reciprocity enforcement
- Multi-cell entity tracking for Large+ creatures
- Deep copy snapshots for rollback

WO-001: Box Geometric Engine Core
Reference: RQ-BOX-001 (Geometric Engine Research)
"""

from copy import deepcopy
from typing import Dict, List, Optional, Tuple, Any

from aidm.schemas.position import Position
from aidm.schemas.geometry import (
    PropertyMask, PropertyFlag, Direction, CellState, SizeCategory, GridCell
)
from aidm.schemas.terrain import TerrainCell, TerrainTag


class BattleGrid:
    """Uniform grid data structure for tactical combat.

    Uses flat array storage indexed by `y * width + x` for cache-friendly
    access patterns. Supports multi-cell entity placement and enforces
    border reciprocity (setting N border of (3,5) also sets S border of (3,4)).

    Designed for grids up to 100x100 (10,000 cells).
    """

    def __init__(self, width: int, height: int):
        """Create a new BattleGrid.

        Args:
            width: Grid width in cells
            height: Grid height in cells
        """
        self._width = width
        self._height = height

        # Flat array storage: index = y * width + x
        self._cells: List[GridCell] = []
        for y in range(height):
            for x in range(width):
                self._cells.append(GridCell(position=Position(x=x, y=y)))

        # Entity spatial tracking: entity_id -> (position, size)
        self._entities: Dict[str, Tuple[Position, SizeCategory]] = {}

    @property
    def width(self) -> int:
        """Grid width in cells."""
        return self._width

    @property
    def height(self) -> int:
        """Grid height in cells."""
        return self._height

    def _index(self, pos: Position) -> int:
        """Convert position to flat array index.

        Args:
            pos: Grid position

        Returns:
            Flat array index
        """
        return pos.y * self._width + pos.x

    def in_bounds(self, pos: Position) -> bool:
        """Check if a position is within grid bounds.

        Args:
            pos: Position to check

        Returns:
            True if position is valid
        """
        return 0 <= pos.x < self._width and 0 <= pos.y < self._height

    def get_cell(self, pos: Position) -> GridCell:
        """Get the cell at a position.

        Args:
            pos: Grid position

        Returns:
            GridCell at that position

        Raises:
            IndexError: If position is out of bounds
        """
        if not self.in_bounds(pos):
            raise IndexError(f"Position {pos} is out of bounds for grid {self._width}x{self._height}")
        return self._cells[self._index(pos)]

    def set_cell(self, pos: Position, cell: GridCell) -> None:
        """Set the cell at a position.

        Args:
            pos: Grid position
            cell: GridCell to place

        Raises:
            IndexError: If position is out of bounds
        """
        if not self.in_bounds(pos):
            raise IndexError(f"Position {pos} is out of bounds for grid {self._width}x{self._height}")
        self._cells[self._index(pos)] = cell

    def get_neighbors(self, pos: Position) -> List[Position]:
        """Get all valid 8-directional neighbors of a position.

        Args:
            pos: Center position

        Returns:
            List of valid neighbor positions (up to 8)
        """
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                neighbor = Position(x=pos.x + dx, y=pos.y + dy)
                if self.in_bounds(neighbor):
                    neighbors.append(neighbor)
        return neighbors

    # ==========================================================================
    # BORDER ACCESS — with reciprocity enforcement
    # ==========================================================================

    def get_border(self, pos: Position, direction: Direction) -> PropertyMask:
        """Get the border mask at a position and direction.

        Args:
            pos: Grid position
            direction: Cardinal direction (N, E, S, W)

        Returns:
            PropertyMask for that border

        Raises:
            IndexError: If position is out of bounds
        """
        cell = self.get_cell(pos)
        return cell.get_border_mask(direction)

    def set_border(self, pos: Position, direction: Direction, mask: PropertyMask) -> None:
        """Set the border mask at a position and direction.

        ENFORCES RECIPROCITY: Setting the N border of (3,5) also sets the
        S border of (3,4). If the neighbor is out of bounds, only the
        local border is set.

        Args:
            pos: Grid position
            direction: Cardinal direction (N, E, S, W)
            mask: PropertyMask to set

        Raises:
            IndexError: If position is out of bounds
        """
        # Set local border
        cell = self.get_cell(pos)
        cell.border_masks[direction] = mask

        # Calculate neighbor position
        dx, dy = direction.delta()
        neighbor_pos = Position(x=pos.x + dx, y=pos.y + dy)

        # Set reciprocal border if neighbor is in bounds
        if self.in_bounds(neighbor_pos):
            neighbor_cell = self.get_cell(neighbor_pos)
            neighbor_cell.border_masks[direction.opposite()] = mask

    # ==========================================================================
    # OCCUPANT QUERIES
    # ==========================================================================

    def get_occupants(self, pos: Position) -> List[str]:
        """Get entity IDs occupying a position.

        Args:
            pos: Grid position

        Returns:
            List of entity IDs at that position

        Raises:
            IndexError: If position is out of bounds
        """
        cell = self.get_cell(pos)
        return list(cell.occupant_ids)

    def get_entities_in_area(self, positions: List[Position]) -> List[str]:
        """Get all entity IDs occupying any of the given positions.

        Returns deduplicated list (Large creature counted once even if
        area overlaps multiple cells it occupies).

        Args:
            positions: List of positions to check

        Returns:
            Deduplicated list of entity IDs
        """
        seen = set()
        result = []
        for pos in positions:
            if not self.in_bounds(pos):
                continue
            for entity_id in self.get_occupants(pos):
                if entity_id not in seen:
                    seen.add(entity_id)
                    result.append(entity_id)
        return result

    # ==========================================================================
    # ENTITY SPATIAL TRACKING
    # ==========================================================================

    def _get_footprint_positions(self, pos: Position, size: SizeCategory) -> List[Position]:
        """Get all positions occupied by an entity of a given size.

        Args:
            pos: Top-left corner position
            size: Size category

        Returns:
            List of all positions in the footprint
        """
        grid_size = size.grid_size()
        positions = []
        for dy in range(grid_size):
            for dx in range(grid_size):
                positions.append(Position(x=pos.x + dx, y=pos.y + dy))
        return positions

    def place_entity(self, entity_id: str, pos: Position, size: SizeCategory) -> None:
        """Place an entity on the grid.

        For Medium and smaller, occupies single cell at pos.
        For Large, occupies 2x2 cells with pos as top-left corner.
        For Huge, occupies 3x3, etc.

        Args:
            entity_id: Unique entity identifier
            pos: Position (top-left corner for multi-cell)
            size: Size category

        Raises:
            ValueError: If any target cell is out of bounds
        """
        footprint = self._get_footprint_positions(pos, size)

        # Validate all positions
        for fp_pos in footprint:
            if not self.in_bounds(fp_pos):
                raise ValueError(
                    f"Cannot place entity {entity_id} at {pos} with size {size.value}: "
                    f"position {fp_pos} is out of bounds"
                )

        # Add to all cells
        for fp_pos in footprint:
            cell = self.get_cell(fp_pos)
            if entity_id not in cell.occupant_ids:
                cell.occupant_ids.append(entity_id)

        # Track in reverse lookup
        self._entities[entity_id] = (pos, size)

    def remove_entity(self, entity_id: str) -> None:
        """Remove an entity from the grid.

        Args:
            entity_id: Entity to remove

        Raises:
            KeyError: If entity is not on the grid
        """
        if entity_id not in self._entities:
            raise KeyError(f"Entity {entity_id} not found on grid")

        pos, size = self._entities[entity_id]
        footprint = self._get_footprint_positions(pos, size)

        # Remove from all cells
        for fp_pos in footprint:
            if self.in_bounds(fp_pos):
                cell = self.get_cell(fp_pos)
                if entity_id in cell.occupant_ids:
                    cell.occupant_ids.remove(entity_id)

        # Remove from tracking
        del self._entities[entity_id]

    def move_entity(self, entity_id: str, new_pos: Position) -> None:
        """Move an entity to a new position.

        Args:
            entity_id: Entity to move
            new_pos: New position (top-left for multi-cell)

        Raises:
            KeyError: If entity is not on the grid
            ValueError: If new position is out of bounds
        """
        if entity_id not in self._entities:
            raise KeyError(f"Entity {entity_id} not found on grid")

        _, size = self._entities[entity_id]

        # Validate new position
        new_footprint = self._get_footprint_positions(new_pos, size)
        for fp_pos in new_footprint:
            if not self.in_bounds(fp_pos):
                raise ValueError(
                    f"Cannot move entity {entity_id} to {new_pos}: "
                    f"position {fp_pos} is out of bounds"
                )

        # Remove from old position
        self.remove_entity(entity_id)

        # Place at new position (re-adds to _entities)
        self.place_entity(entity_id, new_pos, size)

    def get_entity_position(self, entity_id: str) -> Optional[Position]:
        """Get the position of an entity.

        Args:
            entity_id: Entity to look up

        Returns:
            Position of entity, or None if not found
        """
        if entity_id not in self._entities:
            return None
        pos, _ = self._entities[entity_id]
        return pos

    # ==========================================================================
    # SNAPSHOT — deep copy for rollback
    # ==========================================================================

    def snapshot(self) -> 'BattleGrid':
        """Create a deep copy of this grid.

        Mutations to the snapshot do NOT affect the original and vice versa.
        Entity tracking is also independent.

        Returns:
            Independent copy of this BattleGrid
        """
        new_grid = BattleGrid(self._width, self._height)

        # Deep copy all cells
        for i, cell in enumerate(self._cells):
            new_grid._cells[i] = GridCell(
                position=cell.position,  # Position is frozen, safe to share
                cell_mask=PropertyMask(_value=cell.cell_mask.to_int()),
                border_masks={d: PropertyMask(_value=m.to_int()) for d, m in cell.border_masks.items()},
                elevation=cell.elevation,
                height=cell.height,
                material_mask=cell.material_mask,
                hardness=cell.hardness,
                hit_points=cell.hit_points,
                state=cell.state,
                occupant_ids=list(cell.occupant_ids),
            )

        # Deep copy entity tracking
        new_grid._entities = {
            eid: (pos, size) for eid, (pos, size) in self._entities.items()
        }

        return new_grid


# ==============================================================================
# FACTORY: from_terrain_map
# ==============================================================================

def from_terrain_map(terrain_map: Dict, entities: Dict) -> BattleGrid:
    """Create a BattleGrid from existing terrain map format.

    Bridges the existing terrain system (terrain_resolver.py) with the
    new geometric engine. Converts TerrainCell terrain_tags and cover_type
    to PropertyMask flags.

    Args:
        terrain_map: Dict keyed by "x,y" strings, values are TerrainCell dicts
                     (same format as world_state.active_combat["terrain_map"])
        entities: Dict keyed by entity_id, values are entity dicts with
                  at minimum {"position": {"x": int, "y": int}}

    Returns:
        BattleGrid populated with terrain and entities

    Conversion logic:
    - cover_type == "total" → SOLID + OPAQUE
    - "wall_smooth" or "wall_rough" in terrain_tags → SOLID + OPAQUE
    - "blocking_solid" in terrain_tags → SOLID + OPAQUE
    - "difficult_terrain" in terrain_tags → DIFFICULT
    - "deep_water" in terrain_tags → DIFFICULT + HAZARDOUS
    - "shallow_water" in terrain_tags → DIFFICULT
    - is_pit or is_ledge → HAZARDOUS
    - Elevation preserved directly from TerrainCell
    """
    if not terrain_map:
        # Empty terrain map produces 1x1 empty grid (minimum valid grid)
        return BattleGrid(1, 1)

    # Determine grid bounds from terrain_map keys
    max_x = 0
    max_y = 0
    for key in terrain_map.keys():
        x_str, y_str = key.split(",")
        x, y = int(x_str), int(y_str)
        max_x = max(max_x, x)
        max_y = max(max_y, y)

    width = max_x + 1
    height = max_y + 1

    grid = BattleGrid(width, height)

    # Convert terrain cells
    for key, cell_data in terrain_map.items():
        x_str, y_str = key.split(",")
        x, y = int(x_str), int(y_str)
        pos = Position(x=x, y=y)

        terrain_cell = TerrainCell.from_dict(cell_data)
        grid_cell = grid.get_cell(pos)

        # Start with empty mask
        mask = PropertyMask()

        # Normalize terrain_tags to lowercase for comparison
        tags_lower = [tag.lower() for tag in terrain_cell.terrain_tags]

        # Cover type conversion
        if terrain_cell.cover_type == "total":
            mask = mask.set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)

        # Wall tags → SOLID + OPAQUE
        if "wall_smooth" in tags_lower or "wall_rough" in tags_lower:
            mask = mask.set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)

        # Blocking solid → SOLID + OPAQUE
        if "blocking_solid" in tags_lower:
            mask = mask.set_flag(PropertyFlag.SOLID).set_flag(PropertyFlag.OPAQUE)

        # Difficult terrain
        if "difficult_terrain" in tags_lower:
            mask = mask.set_flag(PropertyFlag.DIFFICULT)

        # Deep water → DIFFICULT + HAZARDOUS
        if "deep_water" in tags_lower:
            mask = mask.set_flag(PropertyFlag.DIFFICULT).set_flag(PropertyFlag.HAZARDOUS)

        # Shallow water → DIFFICULT
        if "shallow_water" in tags_lower:
            mask = mask.set_flag(PropertyFlag.DIFFICULT)

        # Pits and ledges → HAZARDOUS
        if terrain_cell.is_pit or terrain_cell.is_ledge:
            mask = mask.set_flag(PropertyFlag.HAZARDOUS)

        # Update cell
        grid_cell.cell_mask = mask
        grid_cell.elevation = terrain_cell.elevation

    # Place entities with default MEDIUM size
    for entity_id, entity_data in entities.items():
        if "position" in entity_data:
            pos_data = entity_data["position"]
            pos = Position(x=pos_data["x"], y=pos_data["y"])
            if grid.in_bounds(pos):
                grid.place_entity(entity_id, pos, SizeCategory.MEDIUM)

    return grid

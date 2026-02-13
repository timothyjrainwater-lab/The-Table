"""Lens Object Property Indexing for Spark-Box data membrane.

The Lens stores structured facts with provenance and serves them to Box
with low latency. It implements authority resolution to ensure mechanical
facts (Box) override LLM-generated facts (Spark).

WO-007: Lens Object Property Indexing
Reference: RQ-LENS-001 (Lens Layer Research)
"""

from copy import deepcopy
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple

from aidm.schemas.position import Position


# ==============================================================================
# SOURCE TIER — Authority hierarchy for fact provenance
# ==============================================================================

class SourceTier(IntEnum):
    """Authority hierarchy for fact provenance.

    Lower tier number = higher authority.
    BOX (mechanical facts) always overrides SPARK (LLM generated).

    Per RQ-LENS-001 Finding 1:
    - BOX: Deterministic engine outputs (HP, positions, conditions)
    - CANONICAL: Rulebook constants (AC formulas, spell ranges)
    - PLAYER: Player input (character names, backstory)
    - SPARK: LLM generated (descriptions, inferred traits)
    - DEFAULT: System defaults (fallback values)
    """
    BOX = 1       # Highest authority — mechanical facts
    CANONICAL = 2 # Rulebook constants
    PLAYER = 3    # Player input
    SPARK = 4     # LLM generated
    DEFAULT = 5   # Lowest — system defaults


# ==============================================================================
# LENS FACT — Single fact with provenance
# ==============================================================================

@dataclass(frozen=True)
class LensFact:
    """Single fact about an entity with provenance tracking.

    Immutable (frozen) to prevent accidental mutation.
    Facts are replaced, never modified in place.
    """

    entity_id: str
    """Entity this fact describes."""

    attribute: str
    """Attribute name (e.g., 'hp', 'name', 'description')."""

    value: Any
    """The fact value (type depends on attribute)."""

    source_tier: SourceTier
    """Authority tier of this fact's source."""

    timestamp: int
    """Turn number when this fact was recorded."""

    provenance_id: Optional[str] = None
    """Optional ID linking to source (event ID, rulebook ref, etc.)."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "entity_id": self.entity_id,
            "attribute": self.attribute,
            "value": self.value,
            "source_tier": self.source_tier.value,
            "timestamp": self.timestamp,
            "provenance_id": self.provenance_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LensFact':
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            LensFact instance
        """
        return cls(
            entity_id=data["entity_id"],
            attribute=data["attribute"],
            value=data["value"],
            source_tier=SourceTier(data["source_tier"]),
            timestamp=data["timestamp"],
            provenance_id=data.get("provenance_id"),
        )


# ==============================================================================
# ENTITY PROFILE — Collection of facts about an entity
# ==============================================================================

@dataclass
class EntityProfile:
    """Collection of facts about a single entity.

    Mutable container that tracks all known facts about an entity
    along with creation and update timestamps.
    """

    entity_id: str
    """Unique entity identifier."""

    entity_class: str
    """Entity type: 'creature', 'object', or 'terrain'."""

    facts: Dict[str, LensFact] = field(default_factory=dict)
    """Attribute name → LensFact mapping."""

    created_at: int = 0
    """Turn number when entity was registered."""

    updated_at: int = 0
    """Turn number of most recent fact update."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "entity_id": self.entity_id,
            "entity_class": self.entity_class,
            "facts": {attr: fact.to_dict() for attr, fact in self.facts.items()},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntityProfile':
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            EntityProfile instance
        """
        facts = {
            attr: LensFact.from_dict(fact_data)
            for attr, fact_data in data.get("facts", {}).items()
        }
        return cls(
            entity_id=data["entity_id"],
            entity_class=data["entity_class"],
            facts=facts,
            created_at=data.get("created_at", 0),
            updated_at=data.get("updated_at", 0),
        )


# ==============================================================================
# LENS INDEX — Main indexing system
# ==============================================================================

class LensIndex:
    """Main Lens indexing system for entity facts and spatial queries.

    The Lens is the data membrane between Spark (LLM) and Box (deterministic
    engine). It stores structured facts with provenance and enforces authority
    resolution to ensure mechanical facts override LLM-generated facts.

    Authority Resolution (per RQ-LENS-001):
    - Lower tier number = higher authority
    - BOX (1) always overrides SPARK (4)
    - Same tier: newer timestamp wins
    - CANONICAL facts are immutable after first set
    """

    def __init__(self):
        """Initialize empty LensIndex."""
        # Entity storage
        self._entities: Dict[str, EntityProfile] = {}

        # Spatial index for fast position queries
        self._position_index: Dict[str, Position] = {}  # entity_id → position
        self._grid_index: Dict[Tuple[int, int], Set[str]] = {}  # (x,y) → entity_ids

    # ==========================================================================
    # ENTITY MANAGEMENT
    # ==========================================================================

    def register_entity(self, entity_id: str, entity_class: str, turn: int = 0) -> EntityProfile:
        """Register a new entity in the index.

        Args:
            entity_id: Unique entity identifier
            entity_class: Entity type ('creature', 'object', 'terrain')
            turn: Current turn number for timestamps

        Returns:
            New EntityProfile
        """
        profile = EntityProfile(
            entity_id=entity_id,
            entity_class=entity_class,
            created_at=turn,
            updated_at=turn,
        )
        self._entities[entity_id] = profile
        return profile

    def get_entity(self, entity_id: str) -> Optional[EntityProfile]:
        """Get an entity's profile.

        Args:
            entity_id: Entity to look up

        Returns:
            EntityProfile or None if not found
        """
        return self._entities.get(entity_id)

    def remove_entity(self, entity_id: str) -> bool:
        """Remove an entity from the index.

        Also cleans up spatial index entries.

        Args:
            entity_id: Entity to remove

        Returns:
            True if entity was removed, False if not found
        """
        if entity_id not in self._entities:
            return False

        # Clean up spatial index
        if entity_id in self._position_index:
            pos = self._position_index[entity_id]
            grid_key = (pos.x, pos.y)
            if grid_key in self._grid_index:
                self._grid_index[grid_key].discard(entity_id)
                if not self._grid_index[grid_key]:
                    del self._grid_index[grid_key]
            del self._position_index[entity_id]

        del self._entities[entity_id]
        return True

    def list_entities(self, entity_class: Optional[str] = None) -> List[str]:
        """List all entity IDs, optionally filtered by class.

        Args:
            entity_class: Optional filter ('creature', 'object', 'terrain')

        Returns:
            List of entity IDs
        """
        if entity_class is None:
            return list(self._entities.keys())

        return [
            eid for eid, profile in self._entities.items()
            if profile.entity_class == entity_class
        ]

    # ==========================================================================
    # FACT STORAGE
    # ==========================================================================

    def set_fact(
        self,
        entity_id: str,
        attribute: str,
        value: Any,
        source_tier: SourceTier,
        turn: int,
        provenance_id: Optional[str] = None,
    ) -> Optional[LensFact]:
        """Store a fact about an entity.

        Applies authority resolution:
        1. If no existing fact, store new fact
        2. If existing fact has lower tier number (higher authority), reject
        3. If existing fact has same tier, accept if newer timestamp
        4. If existing fact has higher tier number (lower authority), accept
        5. CANONICAL facts are immutable after first set

        Args:
            entity_id: Entity this fact describes
            attribute: Attribute name
            value: Fact value
            source_tier: Authority tier
            turn: Current turn number
            provenance_id: Optional provenance link

        Returns:
            The stored LensFact if accepted, None if rejected
        """
        profile = self._entities.get(entity_id)
        if profile is None:
            return None

        # Check authority resolution
        existing = profile.facts.get(attribute)
        if existing is not None:
            # CANONICAL facts are immutable after first set
            if existing.source_tier == SourceTier.CANONICAL:
                return None

            # Lower tier number = higher authority
            if source_tier > existing.source_tier:
                # New fact has lower authority, reject
                return None
            elif source_tier == existing.source_tier:
                # Same tier: newer timestamp wins
                if turn <= existing.timestamp:
                    return None

        # Create and store the fact
        fact = LensFact(
            entity_id=entity_id,
            attribute=attribute,
            value=value,
            source_tier=source_tier,
            timestamp=turn,
            provenance_id=provenance_id,
        )
        profile.facts[attribute] = fact
        profile.updated_at = turn

        return fact

    def get_fact(self, entity_id: str, attribute: str) -> Optional[LensFact]:
        """Get a specific fact about an entity.

        Args:
            entity_id: Entity to query
            attribute: Attribute name

        Returns:
            LensFact or None if not found
        """
        profile = self._entities.get(entity_id)
        if profile is None:
            return None
        return profile.facts.get(attribute)

    def get_facts(self, entity_id: str) -> Dict[str, LensFact]:
        """Get all facts about an entity.

        Args:
            entity_id: Entity to query

        Returns:
            Dict of attribute → LensFact (empty if entity not found)
        """
        profile = self._entities.get(entity_id)
        if profile is None:
            return {}
        return dict(profile.facts)

    # ==========================================================================
    # AUTHORITY RESOLUTION
    # ==========================================================================

    def resolve_conflict(
        self,
        entity_id: str,
        attribute: str,
        new_value: Any,
        new_tier: SourceTier,
        turn: int,
    ) -> bool:
        """Check if a new fact would override an existing one.

        This is a query method that does not modify state.

        Args:
            entity_id: Entity to check
            attribute: Attribute to check
            new_value: Proposed new value
            new_tier: Proposed tier
            turn: Proposed timestamp

        Returns:
            True if new fact would be accepted, False otherwise
        """
        profile = self._entities.get(entity_id)
        if profile is None:
            return False

        existing = profile.facts.get(attribute)
        if existing is None:
            return True

        # CANONICAL is immutable
        if existing.source_tier == SourceTier.CANONICAL:
            return False

        # Lower tier number = higher authority
        if new_tier > existing.source_tier:
            return False
        elif new_tier == existing.source_tier:
            return turn > existing.timestamp

        return True

    # ==========================================================================
    # SPATIAL INDEX
    # ==========================================================================

    def set_position(self, entity_id: str, pos: Position, turn: int) -> None:
        """Set an entity's position.

        Updates both position index and grid index for fast queries.

        Args:
            entity_id: Entity to position
            pos: New position
            turn: Current turn number
        """
        if entity_id not in self._entities:
            return

        # Remove from old grid cell
        if entity_id in self._position_index:
            old_pos = self._position_index[entity_id]
            old_key = (old_pos.x, old_pos.y)
            if old_key in self._grid_index:
                self._grid_index[old_key].discard(entity_id)
                if not self._grid_index[old_key]:
                    del self._grid_index[old_key]

        # Add to new grid cell
        new_key = (pos.x, pos.y)
        if new_key not in self._grid_index:
            self._grid_index[new_key] = set()
        self._grid_index[new_key].add(entity_id)

        # Update position index
        self._position_index[entity_id] = pos

        # Also store as a fact
        self.set_fact(entity_id, "position", pos.to_dict(), SourceTier.BOX, turn)

    def get_position(self, entity_id: str) -> Optional[Position]:
        """Get an entity's position.

        Args:
            entity_id: Entity to query

        Returns:
            Position or None if not found
        """
        return self._position_index.get(entity_id)

    def get_entities_at(self, pos: Position) -> List[str]:
        """Get all entities at a position.

        Args:
            pos: Position to query

        Returns:
            List of entity IDs at that position
        """
        key = (pos.x, pos.y)
        if key not in self._grid_index:
            return []
        return list(self._grid_index[key])

    def get_entities_in_radius(self, center: Position, radius: int) -> List[str]:
        """Get all entities within a radius of a position.

        Uses simple bounding box check then distance filter.
        Distance uses 1-2-1-2 diagonal movement (Position.distance_to).

        Args:
            center: Center position
            radius: Radius in feet (multiples of 5)

        Returns:
            List of entity IDs within radius
        """
        result = []
        seen = set()

        # Check all grid cells in bounding box
        # Convert radius to grid squares (5 feet per square)
        grid_radius = (radius // 5) + 1  # Add 1 for safety margin

        for dx in range(-grid_radius, grid_radius + 1):
            for dy in range(-grid_radius, grid_radius + 1):
                key = (center.x + dx, center.y + dy)
                if key not in self._grid_index:
                    continue

                for entity_id in self._grid_index[key]:
                    if entity_id in seen:
                        continue
                    seen.add(entity_id)

                    # Check actual distance
                    pos = self._position_index.get(entity_id)
                    if pos is not None and center.distance_to(pos) <= radius:
                        result.append(entity_id)

        return result

    # ==========================================================================
    # SNAPSHOT AND SERIALIZATION
    # ==========================================================================

    def snapshot(self) -> 'LensIndex':
        """Create a deep copy of this index.

        Mutations to the snapshot do NOT affect the original.

        Returns:
            Independent copy of this LensIndex
        """
        new_index = LensIndex()

        # Deep copy entities
        for eid, profile in self._entities.items():
            new_profile = EntityProfile(
                entity_id=profile.entity_id,
                entity_class=profile.entity_class,
                facts={attr: fact for attr, fact in profile.facts.items()},  # LensFact is frozen
                created_at=profile.created_at,
                updated_at=profile.updated_at,
            )
            new_index._entities[eid] = new_profile

        # Deep copy spatial indexes
        new_index._position_index = dict(self._position_index)  # Position is frozen
        new_index._grid_index = {
            key: set(entities) for key, entities in self._grid_index.items()
        }

        return new_index

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "entities": {
                eid: profile.to_dict()
                for eid, profile in self._entities.items()
            },
            "positions": {
                eid: pos.to_dict()
                for eid, pos in self._position_index.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LensIndex':
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            LensIndex instance
        """
        index = cls()

        # Restore entities
        for eid, profile_data in data.get("entities", {}).items():
            index._entities[eid] = EntityProfile.from_dict(profile_data)

        # Restore positions
        for eid, pos_data in data.get("positions", {}).items():
            pos = Position.from_dict(pos_data)
            index._position_index[eid] = pos

            # Rebuild grid index
            key = (pos.x, pos.y)
            if key not in index._grid_index:
                index._grid_index[key] = set()
            index._grid_index[key].add(eid)

        return index

"""Tests for Lens Object Property Indexing (WO-007).

Comprehensive test coverage for:
- SourceTier: Authority hierarchy ordering
- LensFact: Creation, immutability, serialization
- EntityProfile: Creation, fact storage, serialization
- LensIndex: Entity management, fact storage, authority resolution
- Spatial index: Position queries, radius search
- Snapshot: Independence, serialization round-trip
"""

import pytest

from aidm.schemas.position import Position
from aidm.core.lens_index import (
    SourceTier, LensFact, EntityProfile, LensIndex
)


# ==============================================================================
# SOURCE TIER TESTS
# ==============================================================================

class TestSourceTier:
    """Tests for SourceTier authority hierarchy."""

    def test_all_tiers_exist(self):
        """All five source tiers exist."""
        assert SourceTier.BOX is not None
        assert SourceTier.CANONICAL is not None
        assert SourceTier.PLAYER is not None
        assert SourceTier.SPARK is not None
        assert SourceTier.DEFAULT is not None

    def test_tier_ordering_box_highest(self):
        """BOX has lowest value (highest authority)."""
        assert SourceTier.BOX == 1
        assert SourceTier.BOX < SourceTier.CANONICAL
        assert SourceTier.BOX < SourceTier.PLAYER
        assert SourceTier.BOX < SourceTier.SPARK
        assert SourceTier.BOX < SourceTier.DEFAULT

    def test_tier_ordering_complete(self):
        """Complete ordering: BOX < CANONICAL < PLAYER < SPARK < DEFAULT."""
        assert SourceTier.BOX < SourceTier.CANONICAL
        assert SourceTier.CANONICAL < SourceTier.PLAYER
        assert SourceTier.PLAYER < SourceTier.SPARK
        assert SourceTier.SPARK < SourceTier.DEFAULT

    def test_tier_values(self):
        """Tier values are 1-5."""
        assert SourceTier.BOX.value == 1
        assert SourceTier.CANONICAL.value == 2
        assert SourceTier.PLAYER.value == 3
        assert SourceTier.SPARK.value == 4
        assert SourceTier.DEFAULT.value == 5


# ==============================================================================
# LENS FACT TESTS
# ==============================================================================

class TestLensFact:
    """Tests for LensFact data structure."""

    def test_creation_with_all_fields(self):
        """LensFact creation with all fields."""
        fact = LensFact(
            entity_id="goblin_1",
            attribute="hp",
            value=15,
            source_tier=SourceTier.BOX,
            timestamp=5,
            provenance_id="event_123",
        )

        assert fact.entity_id == "goblin_1"
        assert fact.attribute == "hp"
        assert fact.value == 15
        assert fact.source_tier == SourceTier.BOX
        assert fact.timestamp == 5
        assert fact.provenance_id == "event_123"

    def test_creation_without_provenance(self):
        """LensFact creation without optional provenance_id."""
        fact = LensFact(
            entity_id="fighter_1",
            attribute="name",
            value="Sir Galahad",
            source_tier=SourceTier.PLAYER,
            timestamp=1,
        )

        assert fact.provenance_id is None

    def test_immutability(self):
        """LensFact is immutable (frozen)."""
        fact = LensFact(
            entity_id="goblin_1",
            attribute="hp",
            value=15,
            source_tier=SourceTier.BOX,
            timestamp=5,
        )

        with pytest.raises(AttributeError):
            fact.value = 10

        with pytest.raises(AttributeError):
            fact.timestamp = 6

    def test_to_dict_from_dict_roundtrip(self):
        """LensFact serialization round-trip."""
        original = LensFact(
            entity_id="dragon_1",
            attribute="breath_weapon",
            value="fire",
            source_tier=SourceTier.CANONICAL,
            timestamp=0,
            provenance_id="MM_p68",
        )

        data = original.to_dict()
        restored = LensFact.from_dict(data)

        assert restored.entity_id == original.entity_id
        assert restored.attribute == original.attribute
        assert restored.value == original.value
        assert restored.source_tier == original.source_tier
        assert restored.timestamp == original.timestamp
        assert restored.provenance_id == original.provenance_id


# ==============================================================================
# ENTITY PROFILE TESTS
# ==============================================================================

class TestEntityProfile:
    """Tests for EntityProfile data structure."""

    def test_creation_with_defaults(self):
        """EntityProfile creation with default values."""
        profile = EntityProfile(
            entity_id="goblin_1",
            entity_class="creature",
        )

        assert profile.entity_id == "goblin_1"
        assert profile.entity_class == "creature"
        assert profile.facts == {}
        assert profile.created_at == 0
        assert profile.updated_at == 0

    def test_fact_storage(self):
        """EntityProfile can store facts."""
        profile = EntityProfile(
            entity_id="goblin_1",
            entity_class="creature",
        )

        fact = LensFact(
            entity_id="goblin_1",
            attribute="hp",
            value=15,
            source_tier=SourceTier.BOX,
            timestamp=5,
        )
        profile.facts["hp"] = fact

        assert "hp" in profile.facts
        assert profile.facts["hp"].value == 15

    def test_to_dict_from_dict_roundtrip(self):
        """EntityProfile serialization round-trip."""
        original = EntityProfile(
            entity_id="fighter_1",
            entity_class="creature",
            created_at=1,
            updated_at=10,
        )
        original.facts["hp"] = LensFact(
            entity_id="fighter_1",
            attribute="hp",
            value=45,
            source_tier=SourceTier.BOX,
            timestamp=10,
        )
        original.facts["name"] = LensFact(
            entity_id="fighter_1",
            attribute="name",
            value="Sir Galahad",
            source_tier=SourceTier.PLAYER,
            timestamp=1,
        )

        data = original.to_dict()
        restored = EntityProfile.from_dict(data)

        assert restored.entity_id == original.entity_id
        assert restored.entity_class == original.entity_class
        assert restored.created_at == original.created_at
        assert restored.updated_at == original.updated_at
        assert len(restored.facts) == 2
        assert restored.facts["hp"].value == 45
        assert restored.facts["name"].value == "Sir Galahad"


# ==============================================================================
# LENS INDEX - ENTITY MANAGEMENT TESTS
# ==============================================================================

class TestLensIndexEntities:
    """Tests for LensIndex entity management."""

    def test_register_entity_creates_profile(self):
        """register_entity creates an EntityProfile."""
        index = LensIndex()
        profile = index.register_entity("goblin_1", "creature", turn=5)

        assert profile is not None
        assert profile.entity_id == "goblin_1"
        assert profile.entity_class == "creature"
        assert profile.created_at == 5
        assert profile.updated_at == 5

    def test_get_entity_returns_correct_profile(self):
        """get_entity returns the correct profile."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")
        index.register_entity("chest_1", "object")

        profile = index.get_entity("goblin_1")
        assert profile is not None
        assert profile.entity_id == "goblin_1"
        assert profile.entity_class == "creature"

        profile2 = index.get_entity("chest_1")
        assert profile2 is not None
        assert profile2.entity_class == "object"

    def test_get_entity_returns_none_for_unknown(self):
        """get_entity returns None for unknown entity."""
        index = LensIndex()
        assert index.get_entity("nonexistent") is None

    def test_remove_entity_cleans_up(self):
        """remove_entity removes entity and cleans up."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")
        index.set_position("goblin_1", Position(5, 5), turn=1)

        result = index.remove_entity("goblin_1")
        assert result is True
        assert index.get_entity("goblin_1") is None
        assert index.get_position("goblin_1") is None
        assert index.get_entities_at(Position(5, 5)) == []

    def test_remove_entity_returns_false_for_unknown(self):
        """remove_entity returns False for unknown entity."""
        index = LensIndex()
        assert index.remove_entity("nonexistent") is False

    def test_list_entities_all(self):
        """list_entities returns all entity IDs."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")
        index.register_entity("goblin_2", "creature")
        index.register_entity("chest_1", "object")

        entities = index.list_entities()
        assert len(entities) == 3
        assert "goblin_1" in entities
        assert "goblin_2" in entities
        assert "chest_1" in entities

    def test_list_entities_filtered_by_class(self):
        """list_entities filters by entity class."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")
        index.register_entity("goblin_2", "creature")
        index.register_entity("chest_1", "object")
        index.register_entity("wall_1", "terrain")

        creatures = index.list_entities("creature")
        assert len(creatures) == 2
        assert "goblin_1" in creatures
        assert "goblin_2" in creatures

        objects = index.list_entities("object")
        assert len(objects) == 1
        assert "chest_1" in objects

        terrain = index.list_entities("terrain")
        assert len(terrain) == 1
        assert "wall_1" in terrain


# ==============================================================================
# LENS INDEX - FACT STORAGE TESTS
# ==============================================================================

class TestLensIndexFacts:
    """Tests for LensIndex fact storage."""

    def test_set_fact_stores_fact(self):
        """set_fact stores a fact."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")

        fact = index.set_fact("goblin_1", "hp", 15, SourceTier.BOX, turn=5)

        assert fact is not None
        assert fact.value == 15
        assert fact.source_tier == SourceTier.BOX
        assert fact.timestamp == 5

    def test_get_fact_retrieves_fact(self):
        """get_fact retrieves stored fact."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")
        index.set_fact("goblin_1", "hp", 15, SourceTier.BOX, turn=5)

        fact = index.get_fact("goblin_1", "hp")
        assert fact is not None
        assert fact.value == 15

    def test_get_fact_returns_none_for_unknown(self):
        """get_fact returns None for unknown attribute."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")

        assert index.get_fact("goblin_1", "nonexistent") is None

    def test_get_facts_returns_all(self):
        """get_facts returns all facts for entity."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")
        index.set_fact("goblin_1", "hp", 15, SourceTier.BOX, turn=5)
        index.set_fact("goblin_1", "name", "Grok", SourceTier.SPARK, turn=5)
        index.set_fact("goblin_1", "ac", 14, SourceTier.CANONICAL, turn=0)

        facts = index.get_facts("goblin_1")
        assert len(facts) == 3
        assert "hp" in facts
        assert "name" in facts
        assert "ac" in facts

    def test_facts_track_source_tier(self):
        """Facts track source tier correctly."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")

        index.set_fact("goblin_1", "hp", 15, SourceTier.BOX, turn=5)
        index.set_fact("goblin_1", "description", "ugly", SourceTier.SPARK, turn=5)

        hp_fact = index.get_fact("goblin_1", "hp")
        desc_fact = index.get_fact("goblin_1", "description")

        assert hp_fact.source_tier == SourceTier.BOX
        assert desc_fact.source_tier == SourceTier.SPARK

    def test_facts_track_timestamp(self):
        """Facts track timestamp correctly."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")

        index.set_fact("goblin_1", "hp", 15, SourceTier.BOX, turn=5)
        index.set_fact("goblin_1", "hp", 10, SourceTier.BOX, turn=7)

        fact = index.get_fact("goblin_1", "hp")
        assert fact.value == 10
        assert fact.timestamp == 7


# ==============================================================================
# LENS INDEX - AUTHORITY RESOLUTION TESTS
# ==============================================================================

class TestAuthorityResolution:
    """Tests for LensIndex authority resolution."""

    def test_box_overrides_spark(self):
        """BOX (higher authority) overrides SPARK."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")

        # Spark sets initial value
        index.set_fact("goblin_1", "hp", 20, SourceTier.SPARK, turn=1)
        # Box overrides
        index.set_fact("goblin_1", "hp", 15, SourceTier.BOX, turn=2)

        fact = index.get_fact("goblin_1", "hp")
        assert fact.value == 15
        assert fact.source_tier == SourceTier.BOX

    def test_spark_cannot_override_box(self):
        """SPARK (lower authority) cannot override BOX."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")

        # Box sets initial value
        index.set_fact("goblin_1", "hp", 15, SourceTier.BOX, turn=1)
        # Spark tries to override - should fail
        result = index.set_fact("goblin_1", "hp", 100, SourceTier.SPARK, turn=2)

        assert result is None
        fact = index.get_fact("goblin_1", "hp")
        assert fact.value == 15  # Original BOX value preserved

    def test_same_tier_newer_wins(self):
        """Same tier: newer timestamp wins."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")

        index.set_fact("goblin_1", "description", "ugly", SourceTier.SPARK, turn=1)
        index.set_fact("goblin_1", "description", "very ugly", SourceTier.SPARK, turn=5)

        fact = index.get_fact("goblin_1", "description")
        assert fact.value == "very ugly"
        assert fact.timestamp == 5

    def test_same_tier_older_rejected(self):
        """Same tier: older timestamp is rejected."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")

        index.set_fact("goblin_1", "description", "ugly", SourceTier.SPARK, turn=5)
        result = index.set_fact("goblin_1", "description", "pretty", SourceTier.SPARK, turn=3)

        assert result is None
        fact = index.get_fact("goblin_1", "description")
        assert fact.value == "ugly"

    def test_canonical_immutable_after_set(self):
        """CANONICAL facts are immutable after first set."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")

        # Set canonical fact
        index.set_fact("goblin_1", "size", "Small", SourceTier.CANONICAL, turn=0)

        # Try to override with BOX (higher authority)
        result = index.set_fact("goblin_1", "size", "Medium", SourceTier.BOX, turn=5)

        assert result is None
        fact = index.get_fact("goblin_1", "size")
        assert fact.value == "Small"

    def test_resolve_conflict_query(self):
        """resolve_conflict correctly predicts outcome."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")
        index.set_fact("goblin_1", "hp", 15, SourceTier.BOX, turn=5)

        # BOX can override BOX if newer
        assert index.resolve_conflict("goblin_1", "hp", 10, SourceTier.BOX, turn=10) is True
        # SPARK cannot override BOX
        assert index.resolve_conflict("goblin_1", "hp", 100, SourceTier.SPARK, turn=10) is False
        # BOX same timestamp rejected
        assert index.resolve_conflict("goblin_1", "hp", 12, SourceTier.BOX, turn=5) is False


# ==============================================================================
# LENS INDEX - SPATIAL INDEX TESTS
# ==============================================================================

class TestSpatialIndex:
    """Tests for LensIndex spatial indexing."""

    def test_set_position_updates_index(self):
        """set_position updates position index."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")

        index.set_position("goblin_1", Position(5, 10), turn=1)

        pos = index.get_position("goblin_1")
        assert pos == Position(5, 10)

    def test_get_position_returns_correct(self):
        """get_position returns correct position."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")
        index.register_entity("goblin_2", "creature")

        index.set_position("goblin_1", Position(5, 10), turn=1)
        index.set_position("goblin_2", Position(15, 20), turn=1)

        assert index.get_position("goblin_1") == Position(5, 10)
        assert index.get_position("goblin_2") == Position(15, 20)

    def test_get_position_returns_none_for_unknown(self):
        """get_position returns None for unknown entity."""
        index = LensIndex()
        assert index.get_position("nonexistent") is None

    def test_get_entities_at_returns_all(self):
        """get_entities_at returns all entities at position."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")
        index.register_entity("goblin_2", "creature")
        index.register_entity("goblin_3", "creature")

        index.set_position("goblin_1", Position(5, 5), turn=1)
        index.set_position("goblin_2", Position(5, 5), turn=1)
        index.set_position("goblin_3", Position(10, 10), turn=1)

        entities = index.get_entities_at(Position(5, 5))
        assert len(entities) == 2
        assert "goblin_1" in entities
        assert "goblin_2" in entities
        assert "goblin_3" not in entities

    def test_get_entities_at_empty(self):
        """get_entities_at returns empty list for empty position."""
        index = LensIndex()
        entities = index.get_entities_at(Position(0, 0))
        assert entities == []

    def test_get_entities_in_radius(self):
        """get_entities_in_radius returns entities within range."""
        index = LensIndex()
        index.register_entity("center", "creature")
        index.register_entity("close", "creature")
        index.register_entity("far", "creature")

        index.set_position("center", Position(10, 10), turn=1)
        index.set_position("close", Position(11, 10), turn=1)  # 5 feet away
        index.set_position("far", Position(20, 10), turn=1)    # 50 feet away

        # Radius 10 feet should include center and close
        entities = index.get_entities_in_radius(Position(10, 10), radius=10)
        assert "center" in entities
        assert "close" in entities
        assert "far" not in entities

    def test_position_change_updates_grid_index(self):
        """Position change updates grid index correctly."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")

        index.set_position("goblin_1", Position(5, 5), turn=1)
        assert "goblin_1" in index.get_entities_at(Position(5, 5))

        index.set_position("goblin_1", Position(10, 10), turn=2)
        assert "goblin_1" not in index.get_entities_at(Position(5, 5))
        assert "goblin_1" in index.get_entities_at(Position(10, 10))


# ==============================================================================
# SNAPSHOT TESTS
# ==============================================================================

class TestSnapshot:
    """Tests for LensIndex snapshot."""

    def test_snapshot_creates_independent_copy(self):
        """snapshot() creates independent copy."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")
        index.set_fact("goblin_1", "hp", 15, SourceTier.BOX, turn=1)
        index.set_position("goblin_1", Position(5, 5), turn=1)

        snapshot = index.snapshot()

        # Both have the entity
        assert index.get_entity("goblin_1") is not None
        assert snapshot.get_entity("goblin_1") is not None

    def test_snapshot_mutations_dont_affect_original(self):
        """Mutations to snapshot don't affect original."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")
        index.set_fact("goblin_1", "hp", 15, SourceTier.BOX, turn=1)

        snapshot = index.snapshot()

        # Modify snapshot
        snapshot.set_fact("goblin_1", "hp", 5, SourceTier.BOX, turn=10)
        snapshot.register_entity("goblin_2", "creature")

        # Original unchanged
        assert index.get_fact("goblin_1", "hp").value == 15
        assert index.get_entity("goblin_2") is None

    def test_snapshot_spatial_index_independent(self):
        """Spatial index is independent in snapshot."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature")
        index.set_position("goblin_1", Position(5, 5), turn=1)

        snapshot = index.snapshot()
        snapshot.set_position("goblin_1", Position(10, 10), turn=2)

        assert index.get_position("goblin_1") == Position(5, 5)
        assert snapshot.get_position("goblin_1") == Position(10, 10)


# ==============================================================================
# SERIALIZATION TESTS
# ==============================================================================

class TestSerialization:
    """Tests for LensIndex serialization."""

    def test_to_dict_from_dict_roundtrip(self):
        """to_dict() / from_dict() round-trip preserves data."""
        index = LensIndex()
        index.register_entity("goblin_1", "creature", turn=1)
        index.register_entity("chest_1", "object", turn=1)
        index.set_fact("goblin_1", "hp", 15, SourceTier.BOX, turn=5)
        index.set_fact("goblin_1", "name", "Grok", SourceTier.PLAYER, turn=2)
        index.set_position("goblin_1", Position(5, 10), turn=5)
        index.set_position("chest_1", Position(20, 20), turn=1)

        data = index.to_dict()
        restored = LensIndex.from_dict(data)

        # Entities preserved
        assert len(restored.list_entities()) == 2
        assert restored.get_entity("goblin_1") is not None
        assert restored.get_entity("chest_1") is not None

        # Facts preserved
        hp_fact = restored.get_fact("goblin_1", "hp")
        assert hp_fact is not None
        assert hp_fact.value == 15

        name_fact = restored.get_fact("goblin_1", "name")
        assert name_fact is not None
        assert name_fact.value == "Grok"

        # Positions preserved
        assert restored.get_position("goblin_1") == Position(5, 10)
        assert restored.get_position("chest_1") == Position(20, 20)

        # Spatial queries work
        assert "goblin_1" in restored.get_entities_at(Position(5, 10))
        assert "chest_1" in restored.get_entities_at(Position(20, 20))

    def test_empty_index_serialization(self):
        """Empty index serializes and deserializes correctly."""
        index = LensIndex()
        data = index.to_dict()
        restored = LensIndex.from_dict(data)

        assert restored.list_entities() == []

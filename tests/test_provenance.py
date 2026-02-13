"""Tests for W3C PROV-DM provenance tracking system.

WO-009: Provenance Tracking (W3C PROV-DM)
Tests cover:
- Entity registration and hashing
- Activity lifecycle
- Agent registration
- PROV relations (wasGeneratedBy, wasAttributedTo, wasDerivedFrom)
- Provenance chain queries
- explain() functionality
- Serialization round-trips
- Edge cases
"""

import pytest

from aidm.core.provenance import (
    compute_value_hash,
    ProvenanceEntity,
    ProvenanceActivity,
    ProvenanceAgent,
    WasGeneratedBy,
    WasAttributedTo,
    WasDerivedFrom,
    ProvenanceExplanation,
    ProvenanceStore,
)


# ==============================================================================
# HASH COMPUTATION TESTS
# ==============================================================================

class TestComputeValueHash:
    """Tests for value hash computation."""

    def test_string_hash(self):
        """Hash of string value is deterministic."""
        h1 = compute_value_hash("hello")
        h2 = compute_value_hash("hello")
        assert h1 == h2
        assert len(h1) == 16

    def test_different_values_different_hashes(self):
        """Different values produce different hashes."""
        h1 = compute_value_hash("hello")
        h2 = compute_value_hash("world")
        assert h1 != h2

    def test_dict_hash_sorted(self):
        """Dict hash is consistent regardless of key order."""
        h1 = compute_value_hash({"a": 1, "b": 2})
        h2 = compute_value_hash({"b": 2, "a": 1})
        assert h1 == h2

    def test_nested_structure_hash(self):
        """Complex nested structures hash correctly."""
        value = {"outer": {"inner": [1, 2, 3]}, "other": True}
        h1 = compute_value_hash(value)
        h2 = compute_value_hash(value)
        assert h1 == h2

    def test_number_hash(self):
        """Numbers hash correctly."""
        h1 = compute_value_hash(42)
        h2 = compute_value_hash(42)
        assert h1 == h2

    def test_list_hash(self):
        """Lists hash correctly."""
        h1 = compute_value_hash([1, 2, 3])
        h2 = compute_value_hash([1, 2, 3])
        assert h1 == h2

    def test_none_hash(self):
        """None hashes correctly."""
        h1 = compute_value_hash(None)
        h2 = compute_value_hash(None)
        assert h1 == h2


# ==============================================================================
# ENTITY TESTS
# ==============================================================================

class TestProvenanceEntity:
    """Tests for ProvenanceEntity dataclass."""

    def test_register_entity_creates(self):
        """register_entity creates entity with correct fields."""
        store = ProvenanceStore()
        entity = store.register_entity("npc_001:hp", 25, turn=5)

        assert entity.entity_id == "npc_001:hp"
        assert entity.created_at == 5
        assert len(entity.value_hash) == 16

    def test_value_hash_computed_correctly(self):
        """Entity value hash matches direct computation."""
        store = ProvenanceStore()
        value = {"hp": 25, "max_hp": 30}
        entity = store.register_entity("npc_001:stats", value, turn=1)

        expected_hash = compute_value_hash(value)
        assert entity.value_hash == expected_hash

    def test_get_entity_retrieves(self):
        """get_entity retrieves registered entity."""
        store = ProvenanceStore()
        store.register_entity("test_entity", "value", turn=1)

        result = store.get_entity("test_entity")
        assert result is not None
        assert result.entity_id == "test_entity"

    def test_get_entity_returns_none_for_unknown(self):
        """get_entity returns None for unknown entity."""
        store = ProvenanceStore()
        result = store.get_entity("nonexistent")
        assert result is None

    def test_entity_is_frozen(self):
        """ProvenanceEntity is immutable."""
        entity = ProvenanceEntity(
            entity_id="test",
            value_hash="abc123",
            created_at=1,
        )
        with pytest.raises(AttributeError):
            entity.entity_id = "changed"

    def test_entity_to_dict(self):
        """Entity serializes to dict correctly."""
        entity = ProvenanceEntity(
            entity_id="test:attr",
            value_hash="abc123def456",
            created_at=10,
        )
        d = entity.to_dict()
        assert d["entity_id"] == "test:attr"
        assert d["value_hash"] == "abc123def456"
        assert d["created_at"] == 10

    def test_entity_from_dict(self):
        """Entity deserializes from dict correctly."""
        data = {
            "entity_id": "test:attr",
            "value_hash": "abc123def456",
            "created_at": 10,
        }
        entity = ProvenanceEntity.from_dict(data)
        assert entity.entity_id == "test:attr"
        assert entity.value_hash == "abc123def456"
        assert entity.created_at == 10


# ==============================================================================
# ACTIVITY TESTS
# ==============================================================================

class TestProvenanceActivity:
    """Tests for ProvenanceActivity dataclass."""

    def test_register_activity_creates(self):
        """register_activity creates activity with unique ID."""
        store = ProvenanceStore()
        activity = store.register_activity("spark_generation", turn=5)

        assert activity.activity_type == "spark_generation"
        assert activity.started_at == 5
        assert activity.ended_at is None
        assert activity.activity_id.startswith("activity_")

    def test_complete_activity_sets_ended_at(self):
        """complete_activity sets ended_at timestamp."""
        store = ProvenanceStore()
        activity = store.register_activity("box_calculation", turn=5)
        store.complete_activity(activity.activity_id, turn=7)

        completed = store.get_activity(activity.activity_id)
        assert completed is not None
        assert completed.ended_at == 7
        assert completed.started_at == 5

    def test_get_activity_retrieves(self):
        """get_activity retrieves registered activity."""
        store = ProvenanceStore()
        activity = store.register_activity("player_input", turn=1)

        result = store.get_activity(activity.activity_id)
        assert result is not None
        assert result.activity_type == "player_input"

    def test_get_activity_returns_none_for_unknown(self):
        """get_activity returns None for unknown activity."""
        store = ProvenanceStore()
        result = store.get_activity("nonexistent")
        assert result is None

    def test_complete_unknown_activity_noop(self):
        """complete_activity on unknown activity is a no-op."""
        store = ProvenanceStore()
        # Should not raise
        store.complete_activity("nonexistent", turn=5)

    def test_activity_types(self):
        """Various activity types work correctly."""
        store = ProvenanceStore()
        types = ["spark_generation", "box_calculation", "player_input", "system_init"]

        for activity_type in types:
            activity = store.register_activity(activity_type, turn=1)
            assert activity.activity_type == activity_type

    def test_activity_to_dict(self):
        """Activity serializes to dict correctly."""
        activity = ProvenanceActivity(
            activity_id="act_123",
            activity_type="test_type",
            started_at=5,
            ended_at=10,
        )
        d = activity.to_dict()
        assert d["activity_id"] == "act_123"
        assert d["activity_type"] == "test_type"
        assert d["started_at"] == 5
        assert d["ended_at"] == 10

    def test_activity_from_dict(self):
        """Activity deserializes from dict correctly."""
        data = {
            "activity_id": "act_123",
            "activity_type": "test_type",
            "started_at": 5,
            "ended_at": 10,
        }
        activity = ProvenanceActivity.from_dict(data)
        assert activity.activity_id == "act_123"
        assert activity.ended_at == 10


# ==============================================================================
# AGENT TESTS
# ==============================================================================

class TestProvenanceAgent:
    """Tests for ProvenanceAgent dataclass."""

    def test_register_agent_creates(self):
        """register_agent creates agent with correct fields."""
        store = ProvenanceStore()
        agent = store.register_agent("spark_01", "spark")

        assert agent.agent_id == "spark_01"
        assert agent.agent_type == "spark"

    def test_get_agent_retrieves(self):
        """get_agent retrieves registered agent."""
        store = ProvenanceStore()
        store.register_agent("box_engine", "box")

        result = store.get_agent("box_engine")
        assert result is not None
        assert result.agent_type == "box"

    def test_get_agent_returns_none_for_unknown(self):
        """get_agent returns None for unknown agent."""
        store = ProvenanceStore()
        result = store.get_agent("nonexistent")
        assert result is None

    def test_agent_types(self):
        """All standard agent types work correctly."""
        store = ProvenanceStore()
        types = ["spark", "box", "player", "system"]

        for agent_type in types:
            agent = store.register_agent(f"agent_{agent_type}", agent_type)
            assert agent.agent_type == agent_type

    def test_agent_to_dict(self):
        """Agent serializes to dict correctly."""
        agent = ProvenanceAgent(
            agent_id="test_agent",
            agent_type="spark",
        )
        d = agent.to_dict()
        assert d["agent_id"] == "test_agent"
        assert d["agent_type"] == "spark"

    def test_agent_from_dict(self):
        """Agent deserializes from dict correctly."""
        data = {
            "agent_id": "test_agent",
            "agent_type": "box",
        }
        agent = ProvenanceAgent.from_dict(data)
        assert agent.agent_id == "test_agent"
        assert agent.agent_type == "box"


# ==============================================================================
# RELATION TESTS
# ==============================================================================

class TestWasGeneratedBy:
    """Tests for wasGeneratedBy relation."""

    def test_record_generation_links_entity_to_activity(self):
        """record_generation creates link between entity and activity."""
        store = ProvenanceStore()
        store.register_entity("entity_a", "value", turn=1)
        activity = store.register_activity("spark_generation", turn=1)

        store.record_generation("entity_a", activity.activity_id, turn=1)

        # Verify via explain
        explanation = store.explain("entity_a")
        assert explanation.generation_activity == "spark_generation"
        assert explanation.generation_turn == 1

    def test_generation_to_dict(self):
        """WasGeneratedBy serializes correctly."""
        gen = WasGeneratedBy(
            entity_id="ent_1",
            activity_id="act_1",
            timestamp=5,
        )
        d = gen.to_dict()
        assert d["entity_id"] == "ent_1"
        assert d["activity_id"] == "act_1"
        assert d["timestamp"] == 5


class TestWasAttributedTo:
    """Tests for wasAttributedTo relation."""

    def test_record_attribution_links_entity_to_agent(self):
        """record_attribution creates link between entity and agent."""
        store = ProvenanceStore()
        store.register_entity("fact_001", "some value", turn=1)
        store.register_agent("spark_llm", "spark")

        store.record_attribution("fact_001", "spark_llm")

        agents = store.get_entity_sources("fact_001")
        assert len(agents) == 1
        assert agents[0].agent_id == "spark_llm"

    def test_multiple_attributions(self):
        """Entity can be attributed to multiple agents."""
        store = ProvenanceStore()
        store.register_entity("fact_001", "value", turn=1)
        store.register_agent("agent_a", "spark")
        store.register_agent("agent_b", "box")

        store.record_attribution("fact_001", "agent_a")
        store.record_attribution("fact_001", "agent_b")

        agents = store.get_entity_sources("fact_001")
        assert len(agents) == 2

    def test_attribution_to_dict(self):
        """WasAttributedTo serializes correctly."""
        attr = WasAttributedTo(
            entity_id="ent_1",
            agent_id="agent_1",
        )
        d = attr.to_dict()
        assert d["entity_id"] == "ent_1"
        assert d["agent_id"] == "agent_1"


class TestWasDerivedFrom:
    """Tests for wasDerivedFrom relation."""

    def test_record_derivation_links_entities(self):
        """record_derivation creates link between derived and source entity."""
        store = ProvenanceStore()
        store.register_entity("source_fact", "original", turn=1)
        store.register_entity("derived_fact", "modified", turn=2)

        store.record_derivation("derived_fact", "source_fact")

        explanation = store.explain("derived_fact")
        assert "source_fact" in explanation.derived_from

    def test_derivation_with_activity(self):
        """Derivation can include activity that performed it."""
        store = ProvenanceStore()
        store.register_entity("source", "original", turn=1)
        store.register_entity("derived", "modified", turn=2)
        activity = store.register_activity("transformation", turn=2)

        store.record_derivation("derived", "source", activity_id=activity.activity_id)

        # The derivation is recorded with activity
        derivations = store._derivations.get("derived", [])
        assert len(derivations) == 1
        assert derivations[0].activity_id == activity.activity_id

    def test_derivation_to_dict(self):
        """WasDerivedFrom serializes correctly."""
        deriv = WasDerivedFrom(
            derived_entity_id="derived",
            source_entity_id="source",
            activity_id="act_1",
        )
        d = deriv.to_dict()
        assert d["derived_entity_id"] == "derived"
        assert d["source_entity_id"] == "source"
        assert d["activity_id"] == "act_1"


# ==============================================================================
# PROVENANCE CHAIN TESTS
# ==============================================================================

class TestProvenanceChain:
    """Tests for provenance chain queries."""

    def test_single_step_chain(self):
        """Single-step chain (direct creation) has depth 0."""
        store = ProvenanceStore()
        store.register_entity("fact_a", "value", turn=1)

        chain = store.get_provenance_chain("fact_a")
        assert len(chain) == 1
        assert chain[0].entity_id == "fact_a"

    def test_two_step_chain(self):
        """Two-step chain (A derived from B)."""
        store = ProvenanceStore()
        store.register_entity("root", "original", turn=1)
        store.register_entity("derived", "modified", turn=2)
        store.record_derivation("derived", "root")

        chain = store.get_provenance_chain("derived")
        assert len(chain) == 2
        assert chain[0].entity_id == "root"
        assert chain[1].entity_id == "derived"

    def test_multi_step_chain(self):
        """Multi-step chain (A derived from B derived from C)."""
        store = ProvenanceStore()
        store.register_entity("level_0", "original", turn=1)
        store.register_entity("level_1", "first_mod", turn=2)
        store.register_entity("level_2", "second_mod", turn=3)

        store.record_derivation("level_1", "level_0")
        store.record_derivation("level_2", "level_1")

        chain = store.get_provenance_chain("level_2")
        assert len(chain) == 3
        assert chain[0].entity_id == "level_0"
        assert chain[1].entity_id == "level_1"
        assert chain[2].entity_id == "level_2"

    def test_chain_for_unknown_entity(self):
        """get_provenance_chain for unknown entity returns empty list."""
        store = ProvenanceStore()
        chain = store.get_provenance_chain("nonexistent")
        assert chain == []

    def test_circular_derivation_handled(self):
        """Circular derivation does not cause infinite loop."""
        store = ProvenanceStore()
        store.register_entity("a", "value_a", turn=1)
        store.register_entity("b", "value_b", turn=2)

        # Create circular reference (should not happen in practice)
        store.record_derivation("b", "a")
        store.record_derivation("a", "b")

        # Should not hang
        chain = store.get_provenance_chain("a")
        # Chain will be cut off at the loop
        assert len(chain) <= 2


# ==============================================================================
# EXPLAIN TESTS
# ==============================================================================

class TestExplain:
    """Tests for explain() functionality."""

    def test_explain_returns_correct_attributed_to(self):
        """explain() includes correct attributed_to list."""
        store = ProvenanceStore()
        store.register_entity("fact", "value", turn=1)
        store.register_agent("agent_1", "spark")
        store.register_agent("agent_2", "box")
        store.record_attribution("fact", "agent_1")
        store.record_attribution("fact", "agent_2")

        explanation = store.explain("fact")
        assert "agent_1" in explanation.attributed_to
        assert "agent_2" in explanation.attributed_to

    def test_explain_returns_correct_derived_from(self):
        """explain() includes correct derived_from list."""
        store = ProvenanceStore()
        store.register_entity("source_a", "val_a", turn=1)
        store.register_entity("source_b", "val_b", turn=1)
        store.register_entity("derived", "combined", turn=2)
        store.record_derivation("derived", "source_a")
        store.record_derivation("derived", "source_b")

        explanation = store.explain("derived")
        assert "source_a" in explanation.derived_from
        assert "source_b" in explanation.derived_from

    def test_explain_chain_depth_accurate(self):
        """explain() returns accurate chain_depth."""
        store = ProvenanceStore()
        store.register_entity("level_0", "v0", turn=1)
        store.register_entity("level_1", "v1", turn=2)
        store.register_entity("level_2", "v2", turn=3)
        store.record_derivation("level_1", "level_0")
        store.record_derivation("level_2", "level_1")

        exp_0 = store.explain("level_0")
        exp_1 = store.explain("level_1")
        exp_2 = store.explain("level_2")

        assert exp_0.chain_depth == 0
        assert exp_1.chain_depth == 1
        assert exp_2.chain_depth == 2

    def test_explain_generation_info(self):
        """explain() includes generation activity and turn."""
        store = ProvenanceStore()
        store.register_entity("fact", "value", turn=5)
        activity = store.register_activity("spark_generation", turn=5)
        store.record_generation("fact", activity.activity_id, turn=5)

        explanation = store.explain("fact")
        assert explanation.generation_activity == "spark_generation"
        assert explanation.generation_turn == 5

    def test_explain_unknown_entity(self):
        """explain() handles unknown entity gracefully."""
        store = ProvenanceStore()
        explanation = store.explain("nonexistent")

        assert explanation.entity_id == "nonexistent"
        assert explanation.current_value_hash == ""
        assert explanation.attributed_to == []
        assert explanation.derived_from == []
        assert explanation.chain_depth == 0

    def test_explanation_to_dict(self):
        """ProvenanceExplanation serializes correctly."""
        explanation = ProvenanceExplanation(
            entity_id="test",
            current_value_hash="abc123",
            attributed_to=["agent_1", "agent_2"],
            derived_from=["source_1"],
            generation_activity="spark_gen",
            generation_turn=5,
            chain_depth=1,
        )
        d = explanation.to_dict()
        assert d["entity_id"] == "test"
        assert d["attributed_to"] == ["agent_1", "agent_2"]
        assert d["chain_depth"] == 1


# ==============================================================================
# SERIALIZATION TESTS
# ==============================================================================

class TestSerialization:
    """Tests for ProvenanceStore serialization."""

    def test_to_dict_from_dict_roundtrip(self):
        """to_dict/from_dict preserves all data."""
        store = ProvenanceStore()

        # Add entities
        store.register_entity("ent_1", "value_1", turn=1)
        store.register_entity("ent_2", "value_2", turn=2)

        # Add activities
        act = store.register_activity("test_activity", turn=1)
        store.complete_activity(act.activity_id, turn=2)

        # Add agents
        store.register_agent("agent_1", "spark")
        store.register_agent("agent_2", "box")

        # Add relations
        store.record_generation("ent_1", act.activity_id, turn=1)
        store.record_attribution("ent_1", "agent_1")
        store.record_derivation("ent_2", "ent_1")

        # Round-trip
        data = store.to_dict()
        restored = ProvenanceStore.from_dict(data)

        # Verify entities
        assert restored.get_entity("ent_1") is not None
        assert restored.get_entity("ent_2") is not None

        # Verify activities
        assert restored.get_activity(act.activity_id) is not None

        # Verify agents
        assert restored.get_agent("agent_1") is not None
        assert restored.get_agent("agent_2") is not None

        # Verify relations via explain
        exp = restored.explain("ent_1")
        assert "agent_1" in exp.attributed_to
        assert exp.generation_turn == 1

        exp2 = restored.explain("ent_2")
        assert "ent_1" in exp2.derived_from

    def test_serialization_preserves_chain(self):
        """Serialization preserves provenance chains."""
        store = ProvenanceStore()
        store.register_entity("root", "v0", turn=1)
        store.register_entity("mid", "v1", turn=2)
        store.register_entity("leaf", "v2", turn=3)
        store.record_derivation("mid", "root")
        store.record_derivation("leaf", "mid")

        data = store.to_dict()
        restored = ProvenanceStore.from_dict(data)

        chain = restored.get_provenance_chain("leaf")
        assert len(chain) == 3
        assert chain[0].entity_id == "root"
        assert chain[2].entity_id == "leaf"

    def test_empty_store_serialization(self):
        """Empty store serializes and deserializes correctly."""
        store = ProvenanceStore()
        data = store.to_dict()
        restored = ProvenanceStore.from_dict(data)

        assert restored.get_entity("anything") is None


# ==============================================================================
# EDGE CASE TESTS
# ==============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_unknown_entity_id_returns_none(self):
        """get_entity for unknown ID returns None."""
        store = ProvenanceStore()
        assert store.get_entity("unknown") is None

    def test_empty_store(self):
        """Empty store works correctly."""
        store = ProvenanceStore()
        assert store.get_entity("any") is None
        assert store.get_agent("any") is None
        assert store.get_activity("any") is None
        assert store.get_provenance_chain("any") == []
        assert store.get_entity_sources("any") == []

    def test_get_entity_sources_for_unattributed_entity(self):
        """get_entity_sources for entity with no attributions returns empty list."""
        store = ProvenanceStore()
        store.register_entity("lonely", "value", turn=1)

        sources = store.get_entity_sources("lonely")
        assert sources == []

    def test_explain_for_entity_with_no_relations(self):
        """explain() for entity with no relations returns minimal explanation."""
        store = ProvenanceStore()
        store.register_entity("standalone", "value", turn=1)

        exp = store.explain("standalone")
        assert exp.entity_id == "standalone"
        assert exp.attributed_to == []
        assert exp.derived_from == []
        assert exp.generation_activity is None
        assert exp.chain_depth == 0

    def test_multiple_derivation_sources(self):
        """Entity derived from multiple sources is handled."""
        store = ProvenanceStore()
        store.register_entity("src_a", "va", turn=1)
        store.register_entity("src_b", "vb", turn=1)
        store.register_entity("merged", "combined", turn=2)
        store.record_derivation("merged", "src_a")
        store.record_derivation("merged", "src_b")

        exp = store.explain("merged")
        assert len(exp.derived_from) == 2
        assert "src_a" in exp.derived_from
        assert "src_b" in exp.derived_from

    def test_activity_unique_ids(self):
        """Each registered activity gets a unique ID."""
        store = ProvenanceStore()
        act1 = store.register_activity("same_type", turn=1)
        act2 = store.register_activity("same_type", turn=1)
        act3 = store.register_activity("same_type", turn=1)

        assert act1.activity_id != act2.activity_id
        assert act2.activity_id != act3.activity_id


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================

class TestIntegration:
    """Integration tests for typical provenance workflows."""

    def test_spark_generation_workflow(self):
        """Complete Spark fact generation workflow."""
        store = ProvenanceStore()

        # Spark agent generates a description
        spark_agent = store.register_agent("spark_narrator", "spark")
        gen_activity = store.register_activity("spark_generation", turn=5)

        entity = store.register_entity(
            "npc_goblin:description",
            "A fierce goblin with glowing red eyes",
            turn=5
        )
        store.record_generation(entity.entity_id, gen_activity.activity_id, turn=5)
        store.record_attribution(entity.entity_id, spark_agent.agent_id)
        store.complete_activity(gen_activity.activity_id, turn=5)

        # Verify
        exp = store.explain("npc_goblin:description")
        assert exp.generation_activity == "spark_generation"
        assert "spark_narrator" in exp.attributed_to
        assert exp.chain_depth == 0

    def test_box_calculation_workflow(self):
        """Complete Box mechanical calculation workflow."""
        store = ProvenanceStore()

        # Box calculates HP after damage
        box_agent = store.register_agent("box_engine", "box")
        calc_activity = store.register_activity("box_calculation", turn=10)

        # Original HP fact
        store.register_entity("fighter:hp", 25, turn=1)
        store.record_attribution("fighter:hp", box_agent.agent_id)

        # New HP after damage
        new_hp = store.register_entity("fighter:hp_v2", 18, turn=10)
        store.record_derivation("fighter:hp_v2", "fighter:hp", calc_activity.activity_id)
        store.record_generation("fighter:hp_v2", calc_activity.activity_id, turn=10)
        store.record_attribution("fighter:hp_v2", box_agent.agent_id)

        store.complete_activity(calc_activity.activity_id, turn=10)

        # Verify chain
        chain = store.get_provenance_chain("fighter:hp_v2")
        assert len(chain) == 2
        assert chain[0].entity_id == "fighter:hp"
        assert chain[1].entity_id == "fighter:hp_v2"

    def test_player_input_workflow(self):
        """Player input creates facts with player attribution."""
        store = ProvenanceStore()

        player_agent = store.register_agent("player_alice", "player")
        input_activity = store.register_activity("player_input", turn=1)

        entity = store.register_entity("alice_pc:name", "Thorn Ironbark", turn=1)
        store.record_generation(entity.entity_id, input_activity.activity_id, turn=1)
        store.record_attribution(entity.entity_id, player_agent.agent_id)

        exp = store.explain("alice_pc:name")
        assert "player_alice" in exp.attributed_to
        assert exp.generation_activity == "player_input"

"""Tests for WorldState deterministic hashing."""

import pytest
from aidm.core.state import WorldState


def test_identical_state_produces_identical_hash():
    """Identical world states must produce identical hashes."""
    state1 = WorldState(
        ruleset_version="dnd3.5",
        entities={"player1": {"hp": 20, "pos": [0, 0]}, "goblin1": {"hp": 5}},
        active_combat={"round": 1, "initiative": ["player1", "goblin1"]},
    )

    state2 = WorldState(
        ruleset_version="dnd3.5",
        entities={"player1": {"hp": 20, "pos": [0, 0]}, "goblin1": {"hp": 5}},
        active_combat={"round": 1, "initiative": ["player1", "goblin1"]},
    )

    assert state1.state_hash() == state2.state_hash()


def test_different_states_produce_different_hashes():
    """Different world states must produce different hashes."""
    state1 = WorldState(
        ruleset_version="dnd3.5",
        entities={"player1": {"hp": 20}},
    )

    state2 = WorldState(
        ruleset_version="dnd3.5",
        entities={"player1": {"hp": 15}},  # Different HP
    )

    assert state1.state_hash() != state2.state_hash()


def test_hash_stable_despite_dict_insertion_order():
    """Hash should be stable regardless of dict insertion order."""
    # Create with different insertion orders
    state1 = WorldState(
        ruleset_version="dnd3.5",
        entities={"a": 1, "b": 2, "c": 3},
    )

    state2 = WorldState(
        ruleset_version="dnd3.5",
        entities={"c": 3, "a": 1, "b": 2},  # Different order
    )

    # Should produce same hash due to sorted keys
    assert state1.state_hash() == state2.state_hash()


def test_nested_dict_order_stability():
    """Nested dictionary order should not affect hash."""
    state1 = WorldState(
        ruleset_version="dnd3.5",
        entities={"player": {"str": 10, "dex": 12, "con": 14}},
    )

    state2 = WorldState(
        ruleset_version="dnd3.5",
        entities={"player": {"con": 14, "str": 10, "dex": 12}},
    )

    assert state1.state_hash() == state2.state_hash()


def test_empty_state_produces_consistent_hash():
    """Empty states should hash consistently."""
    state1 = WorldState(ruleset_version="dnd3.5")
    state2 = WorldState(ruleset_version="dnd3.5")

    assert state1.state_hash() == state2.state_hash()


def test_active_combat_affects_hash():
    """Combat state should affect hash."""
    state1 = WorldState(ruleset_version="dnd3.5", active_combat={"round": 1})
    state2 = WorldState(ruleset_version="dnd3.5", active_combat={"round": 2})
    state3 = WorldState(ruleset_version="dnd3.5", active_combat=None)

    assert state1.state_hash() != state2.state_hash()
    assert state1.state_hash() != state3.state_hash()


def test_ruleset_version_affects_hash():
    """Ruleset version should affect hash."""
    state1 = WorldState(ruleset_version="dnd3.5")
    state2 = WorldState(ruleset_version="dnd5e")

    assert state1.state_hash() != state2.state_hash()


def test_state_to_dict_from_dict():
    """State serialization should roundtrip correctly."""
    original = WorldState(
        ruleset_version="dnd3.5",
        entities={"player": {"hp": 20}},
        active_combat={"round": 1},
    )

    data = original.to_dict()
    restored = WorldState.from_dict(data)

    assert restored.ruleset_version == original.ruleset_version
    assert restored.entities == original.entities
    assert restored.active_combat == original.active_combat
    assert restored.state_hash() == original.state_hash()


def test_hash_is_hex_string():
    """Hash should be a hex string (SHA256 = 64 hex chars)."""
    state = WorldState(ruleset_version="dnd3.5")
    hash_value = state.state_hash()

    assert isinstance(hash_value, str)
    assert len(hash_value) == 64  # SHA256 hex = 64 chars
    assert all(c in "0123456789abcdef" for c in hash_value)

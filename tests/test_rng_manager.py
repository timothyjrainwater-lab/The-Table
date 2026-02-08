"""Tests for RNGManager determinism and stream isolation."""

import pytest
from aidm.core.rng_manager import RNGManager, DeterministicRNG


def test_same_master_seed_produces_same_sequence():
    """Same master seed should produce identical sequences."""
    mgr1 = RNGManager(master_seed=12345)
    mgr2 = RNGManager(master_seed=12345)

    stream1 = mgr1.stream("combat")
    stream2 = mgr2.stream("combat")

    # Generate sequences
    seq1 = [stream1.randint(1, 100) for _ in range(10)]
    seq2 = [stream2.randint(1, 100) for _ in range(10)]

    assert seq1 == seq2, "Same master seed must produce identical sequences"


def test_different_master_seeds_produce_different_sequences():
    """Different master seeds should produce different sequences."""
    mgr1 = RNGManager(master_seed=12345)
    mgr2 = RNGManager(master_seed=54321)

    stream1 = mgr1.stream("combat")
    stream2 = mgr2.stream("combat")

    seq1 = [stream1.randint(1, 100) for _ in range(10)]
    seq2 = [stream2.randint(1, 100) for _ in range(10)]

    assert seq1 != seq2, "Different master seeds must produce different sequences"


def test_different_stream_names_produce_different_sequences():
    """Different stream names should produce different sequences."""
    mgr = RNGManager(master_seed=12345)

    combat_stream = mgr.stream("combat")
    loot_stream = mgr.stream("loot")

    combat_seq = [combat_stream.randint(1, 100) for _ in range(10)]
    loot_seq = [loot_stream.randint(1, 100) for _ in range(10)]

    assert combat_seq != loot_seq, "Different stream names must produce different sequences"


def test_stream_reuse_maintains_state():
    """Requesting same stream name should return same instance."""
    mgr = RNGManager(master_seed=12345)

    stream1 = mgr.stream("combat")
    first_value = stream1.randint(1, 100)

    stream2 = mgr.stream("combat")
    second_value = stream2.randint(1, 100)

    # Should be same instance, so state continues
    assert stream1 is stream2
    assert first_value != second_value, "Stream state should advance"


def test_stream_isolation():
    """Streams should not affect each other."""
    mgr = RNGManager(master_seed=12345)

    combat = mgr.stream("combat")
    loot = mgr.stream("loot")

    # Generate from combat
    combat_vals_1 = [combat.randint(1, 100) for _ in range(5)]

    # Generate from loot
    loot.randint(1, 100)

    # Combat stream should be unaffected
    combat_vals_2 = [combat.randint(1, 100) for _ in range(5)]

    # Recreate manager with same seed to verify expected sequence
    mgr_check = RNGManager(master_seed=12345)
    combat_check = mgr_check.stream("combat")
    expected_sequence = [combat_check.randint(1, 100) for _ in range(10)]

    actual_sequence = combat_vals_1 + combat_vals_2
    assert actual_sequence == expected_sequence, "Loot stream should not affect combat stream"


def test_narration_stream_must_not_be_used_by_resolvers():
    """
    Narration stream must remain isolated from game logic.

    This is enforced by module boundaries:
    - narration stream should only be used in aidm.narration module (future)
    - resolvers in aidm.rules must not import or use narration stream

    TODO: Add linting or import checking when narration module is added.
    """
    # For now, just verify the stream can be created and is isolated
    mgr = RNGManager(master_seed=12345)

    narration = mgr.stream("narration")
    combat = mgr.stream("combat")

    # Both should exist and be different
    assert narration is not combat

    # Narration should not affect combat determinism
    narration.randint(1, 100)

    combat_val = combat.randint(1, 100)

    # Verify same result with fresh manager
    mgr2 = RNGManager(master_seed=12345)
    combat2 = mgr2.stream("combat")
    combat2_val = combat2.randint(1, 100)

    assert combat_val == combat2_val, "Narration stream must not affect combat"


def test_deterministic_rng_call_count():
    """RNG should track number of calls made."""
    rng = DeterministicRNG(seed=42)

    assert rng.call_count == 0

    rng.randint(1, 10)
    assert rng.call_count == 1

    rng.random()
    assert rng.call_count == 2

    rng.choice([1, 2, 3])
    assert rng.call_count == 3


def test_seed_derivation_is_stable():
    """Seed derivation must be stable across multiple runs."""
    mgr1 = RNGManager(master_seed=999)
    mgr2 = RNGManager(master_seed=999)

    # Internal seed derivation should match
    assert mgr1._derive_seed("test") == mgr2._derive_seed("test")
    assert mgr1._derive_seed("combat") == mgr2._derive_seed("combat")

    # Different stream names should derive different seeds
    assert mgr1._derive_seed("combat") != mgr1._derive_seed("loot")

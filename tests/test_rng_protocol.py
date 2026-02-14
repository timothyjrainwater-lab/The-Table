"""Tests for RNGProvider / RandomStream Protocol conformance.

Verifies that the concrete RNGManager and DeterministicRNG classes
satisfy the runtime_checkable Protocol contracts defined in
aidm.core.rng_protocol.
"""

from aidm.core.rng_manager import RNGManager, DeterministicRNG
from aidm.core.rng_protocol import RNGProvider, RandomStream


def test_rng_manager_satisfies_rng_provider_protocol():
    """RNGManager must be a structural subtype of RNGProvider."""
    mgr = RNGManager(master_seed=42)
    assert isinstance(mgr, RNGProvider)


def test_deterministic_rng_satisfies_random_stream_protocol():
    """DeterministicRNG must be a structural subtype of RandomStream."""
    mgr = RNGManager(master_seed=42)
    stream = mgr.stream("test")
    assert isinstance(stream, RandomStream)


def test_stream_returned_by_provider_satisfies_random_stream():
    """The stream() return value must satisfy RandomStream."""
    mgr = RNGManager(master_seed=99)
    stream = mgr.stream("combat")
    # Verify all required methods exist and are callable
    assert callable(getattr(stream, "randint", None))
    assert callable(getattr(stream, "choice", None))
    assert callable(getattr(stream, "random", None))
    assert callable(getattr(stream, "shuffle", None))

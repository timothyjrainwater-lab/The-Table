"""RNG provider and stream protocols for dependency inversion.

Defines the abstract contracts that RNGManager and DeterministicRNG satisfy.
Resolvers depend on these Protocols instead of concrete classes, enabling
strategy swapping (testing, cryptographic, replay) at session start.

BOUNDARY LAW: BL-005, BL-006 preserved — Protocol enforces the same
deterministic-stream contract that RNGManager already implements.

See also: aidm/core/rng_manager.py (canonical implementation).
"""

from typing import Any, MutableSequence, Protocol, Sequence, runtime_checkable


@runtime_checkable
class RandomStream(Protocol):
    """Protocol for an isolated deterministic RNG stream.

    Matches the public API of DeterministicRNG.
    """

    def randint(self, a: int, b: int) -> int: ...
    def choice(self, seq: Sequence) -> Any: ...
    def random(self) -> float: ...
    def shuffle(self, seq: MutableSequence) -> None: ...


@runtime_checkable
class RNGProvider(Protocol):
    """Protocol for a manager that vends named RNG streams.

    Matches the public API of RNGManager.
    """

    def stream(self, name: str) -> RandomStream: ...

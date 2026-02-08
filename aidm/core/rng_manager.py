"""Deterministic RNG manager with stream isolation."""

import hashlib
import random
from typing import Dict


class DeterministicRNG:
    """Isolated RNG stream with deterministic behavior."""

    def __init__(self, seed: int):
        self._rng = random.Random(seed)
        self._call_count = 0

    def randint(self, a: int, b: int) -> int:
        """Generate random integer in range [a, b]."""
        self._call_count += 1
        return self._rng.randint(a, b)

    def choice(self, seq):
        """Choose random element from sequence."""
        self._call_count += 1
        return self._rng.choice(seq)

    def random(self) -> float:
        """Generate random float in range [0.0, 1.0)."""
        self._call_count += 1
        return self._rng.random()

    def shuffle(self, seq):
        """Shuffle sequence in-place."""
        self._call_count += 1
        self._rng.shuffle(seq)

    @property
    def call_count(self) -> int:
        """Number of RNG calls made on this stream."""
        return self._call_count


class RNGManager:
    """Manages deterministic RNG streams with stable seed derivation."""

    def __init__(self, master_seed: int):
        self._master_seed = master_seed
        self._streams: Dict[str, DeterministicRNG] = {}

    def stream(self, name: str) -> DeterministicRNG:
        """Get or create a named RNG stream with deterministically derived seed."""
        if name not in self._streams:
            # Derive stream seed deterministically from master seed + stream name
            derived_seed = self._derive_seed(name)
            self._streams[name] = DeterministicRNG(derived_seed)
        return self._streams[name]

    def _derive_seed(self, stream_name: str) -> int:
        """Derive a deterministic seed for a stream using hash-based derivation."""
        # Combine master seed and stream name, hash to get stable derived seed
        combined = f"{self._master_seed}:{stream_name}"
        hash_digest = hashlib.sha256(combined.encode()).digest()
        # Convert first 8 bytes to integer
        return int.from_bytes(hash_digest[:8], byteorder="big")

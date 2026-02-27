"""World state representation with deterministic hashing.

BOUNDARY LAW (BL-011): state_hash() uses sorted-key JSON + SHA-256 for
deterministic fingerprinting. If you change the serialization format, ALL
existing replay hashes become invalid and saved sessions fail verification.

BOUNDARY LAW (BL-020): WorldState is immutable at all non-engine boundaries.
Engine modules (play_loop, replay_runner, combat_controller, prep_orchestrator,
interaction) receive raw WorldState. Non-engine modules (narration, immersion,
UI, tactical_policy, legality_checker) MUST receive FrozenWorldStateView.

WorldState is treated as immutable between events — resolvers read it, emit
events, and the replay_runner applies those events via deepcopy.

SINGLE SOURCE OF TRUTH for: Game state container and hash function.
CANONICAL OWNER: aidm.core.state (this file).
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Any, Optional
from types import MappingProxyType
import hashlib
import json

if TYPE_CHECKING:
    from aidm.core.pending_aoe import PendingAoE


@dataclass
class WorldState:
    """Minimal world state for deterministic simulation."""

    ruleset_version: str
    entities: Dict[str, Any] = field(default_factory=dict)
    active_combat: Optional[Dict[str, Any]] = None
    pending_aoe: Optional["PendingAoE"] = field(default=None, compare=False)
    # WO-ENGINE-RETRY-001: exploration time tracking + skill check cache
    game_clock: Optional[Any] = field(default=None, compare=False)
    skill_check_cache: Dict[str, Any] = field(default_factory=dict, compare=False)

    def clear_pending_aoe(self) -> "WorldState":
        """Return a copy of this WorldState with pending_aoe cleared."""
        from copy import deepcopy
        new_ws = deepcopy(self)
        new_ws.pending_aoe = None
        return new_ws

    def state_hash(self) -> str:
        """
        Compute deterministic hash of world state.

        Uses stable key ordering to ensure identical states produce identical hashes.
        pending_aoe is excluded — it is ephemeral UI state, not part of the
        canonical game simulation.
        """
        # Convert to JSON with sorted keys for deterministic serialization
        state_dict = {
            "ruleset_version": self.ruleset_version,
            "entities": self.entities,
            "active_combat": self.active_combat,
        }

        # Serialize with sorted keys
        serialized = json.dumps(state_dict, sort_keys=True, separators=(",", ":"))

        # Hash the serialized representation
        hash_bytes = hashlib.sha256(serialized.encode("utf-8")).digest()

        # Return hex digest
        return hash_bytes.hex()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns a deep copy so callers cannot mutate the original state.
        """
        from copy import deepcopy
        return {
            "ruleset_version": self.ruleset_version,
            "entities": deepcopy(self.entities),
            "active_combat": deepcopy(self.active_combat),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldState":
        """Create WorldState from dictionary."""
        return cls(
            ruleset_version=data["ruleset_version"],
            entities=data.get("entities", {}),
            active_combat=data.get("active_combat"),
        )


# ═══════════════════════════════════════════════════════════════════════
# BL-020: Frozen WorldState View for Non-Engine Boundaries
# ═══════════════════════════════════════════════════════════════════════


class WorldStateImmutabilityError(Exception):
    """Raised when non-engine code attempts to mutate WorldState.

    This exception enforces BL-020: WorldState immutability at non-engine boundaries.
    Only engine modules (play_loop, replay_runner, combat_controller,
    prep_orchestrator, interaction) may construct new WorldState instances.

    All other code MUST receive FrozenWorldStateView and treat it as read-only.
    """
    pass


class FrozenWorldStateView:
    """Read-only proxy for WorldState at non-engine boundaries.

    Enforces BL-020 by preventing all mutation attempts:
    - Field assignment raises WorldStateImmutabilityError
    - Nested dict mutation raises TypeError (via MappingProxyType)
    - Field deletion raises WorldStateImmutabilityError

    Engine-internal handoffs do NOT require this proxy — engine modules
    are trusted to construct new instances rather than mutate in place.

    Non-engine consumers (narration, immersion, UI, tactical_policy, etc.)
    MUST receive this view instead of raw WorldState.

    Usage:
        # Engine code (trusted)
        state = WorldState(ruleset_version="RAW_3.5", entities={...})

        # Before handoff to non-engine code
        view = FrozenWorldStateView(state)

        # Non-engine code receives view
        narration_service.generate(view)  # Read-only access

        # Mutation attempts fail loud
        view.entities = {}  # Raises WorldStateImmutabilityError
        view.entities["pc1"]["hp"] = 0  # Raises TypeError
    """

    __slots__ = ("_state",)

    def __init__(self, state: WorldState):
        """Wrap a WorldState instance for read-only access.

        Args:
            state: The WorldState to wrap. Must be a real WorldState instance.

        Raises:
            TypeError: If state is not a WorldState instance.
        """
        if not isinstance(state, WorldState):
            raise TypeError(
                f"FrozenWorldStateView requires WorldState, got {type(state).__name__}"
            )
        object.__setattr__(self, "_state", state)

    def __getattr__(self, name: str) -> Any:
        """Pass through attribute reads to underlying WorldState.

        Special handling for mutable dict attributes:
        - 'entities': Returns recursively-wrapped MappingProxyType
        - 'active_combat': Returns recursively-wrapped MappingProxyType if not None
        - Other attributes: Pass through unchanged

        Args:
            name: Attribute name to access

        Returns:
            Attribute value, wrapped in MappingProxyType if mutable dict

        Raises:
            AttributeError: If attribute doesn't exist on WorldState
        """
        state = object.__getattribute__(self, "_state")
        value = getattr(state, name)

        # Wrap mutable dict attributes in MappingProxyType
        if name == "entities":
            return self._wrap_nested_dict(value)
        elif name == "active_combat" and value is not None:
            return self._wrap_nested_dict(value)
        else:
            return value

    def _wrap_nested_dict(self, d: Dict[str, Any]) -> MappingProxyType:
        """Recursively wrap nested dicts for read-only access.

        Wraps the top-level dict and ALL nested dicts at any depth
        in MappingProxyType. This prevents in-place mutation like:
            view.entities["pc1"]["hp"] = 0  # Raises TypeError
            view.entities["pc1"]["conditions"]["stunned"] = True  # Also raises

        Args:
            d: Dictionary to wrap

        Returns:
            MappingProxyType view of the dictionary with all nested dicts wrapped
        """
        wrapped = {}
        for key, value in d.items():
            if isinstance(value, dict):
                wrapped[key] = self._wrap_nested_dict(value)
            else:
                wrapped[key] = value
        return MappingProxyType(wrapped)

    def __setattr__(self, name: str, value: Any) -> None:
        """Reject all field assignment attempts.

        Args:
            name: Attribute name
            value: Value to assign

        Raises:
            WorldStateImmutabilityError: Always (mutation not allowed)
        """
        if name == "_state":
            # Allow internal initialization
            object.__setattr__(self, name, value)
        else:
            raise WorldStateImmutabilityError(
                f"Cannot set attribute '{name}' on FrozenWorldStateView. "
                "WorldState is immutable at non-engine boundaries (BL-020). "
                "Only engine modules may construct new WorldState instances."
            )

    def __delattr__(self, name: str) -> None:
        """Reject all field deletion attempts.

        Args:
            name: Attribute name to delete

        Raises:
            WorldStateImmutabilityError: Always (mutation not allowed)
        """
        raise WorldStateImmutabilityError(
            f"Cannot delete attribute '{name}' on FrozenWorldStateView. "
            "WorldState is immutable at non-engine boundaries (BL-020)."
        )

    def state_hash(self) -> str:
        """Compute deterministic hash of underlying WorldState.

        Pass-through to WorldState.state_hash() for replay verification.

        Returns:
            SHA-256 hex digest of state
        """
        state = object.__getattribute__(self, "_state")
        return state.state_hash()

    def to_dict(self) -> Dict[str, Any]:
        """Convert underlying WorldState to dictionary.

        Pass-through to WorldState.to_dict(). Returns a fresh copy,
        safe for serialization.

        Returns:
            Dictionary representation of state
        """
        state = object.__getattribute__(self, "_state")
        return state.to_dict()

    @property
    def ruleset_version(self) -> str:
        """Get ruleset version string."""
        state = object.__getattribute__(self, "_state")
        return state.ruleset_version

    @property
    def entities(self) -> MappingProxyType:
        """Get read-only view of entities dict."""
        state = object.__getattribute__(self, "_state")
        return self._wrap_nested_dict(state.entities)

    @property
    def active_combat(self) -> Optional[MappingProxyType]:
        """Get read-only view of active_combat dict, or None."""
        state = object.__getattribute__(self, "_state")
        if state.active_combat is None:
            return None
        return self._wrap_nested_dict(state.active_combat)

    def __repr__(self) -> str:
        """Return string representation."""
        state = object.__getattribute__(self, "_state")
        return f"FrozenWorldStateView({state!r})"

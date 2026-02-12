"""Asset binding schemas for portrait/voice pool management.

Defines category pools with target sizes, permanent entity→asset bindings,
and replenishment job tracking. Deterministic: same seed + same pool order +
same binding sequence → identical bindings.

WO-CODE-DISCOVERY-001: Bestiary Knowledge Mask + Asset Binding Pools
Reference: docs/planning/RQ-TABLE-FOUNDATIONS-001.md (Topic F)
Reference: aidm/schemas/campaign.py (AssetRecord pattern)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple


# ---------------------------------------------------------------------------
# Asset Pool Category
# ---------------------------------------------------------------------------

@dataclass
class AssetPoolCategory:
    """A category of assets with a target pool size.

    Examples: goblin_portrait, human_merchant_portrait, gruff_voice, etc.
    """
    category_id: str
    asset_type: str  # "portrait", "voice_profile", "token"
    target_size: int
    available: List[str] = field(default_factory=list)
    """Ordered list of available (unbound) asset IDs. Order is deterministic."""

    def __post_init__(self) -> None:
        if not self.category_id:
            raise ValueError("category_id must be non-empty")
        if self.target_size < 1:
            raise ValueError("target_size must be >= 1")

    @property
    def deficit(self) -> int:
        """How many assets need to be generated to reach target."""
        return max(0, self.target_size - len(self.available))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category_id": self.category_id,
            "asset_type": self.asset_type,
            "target_size": self.target_size,
            "available": list(self.available),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AssetPoolCategory":
        return cls(
            category_id=data["category_id"],
            asset_type=data["asset_type"],
            target_size=data.get("target_size", 5),
            available=list(data.get("available", [])),
        )


# ---------------------------------------------------------------------------
# Asset Binding
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AssetBinding:
    """A permanent binding between an entity and an asset.

    Once bound, an asset is permanently associated with an entity_id.
    The asset is removed from the available pool and cannot be reused.
    """
    entity_id: str
    category_id: str
    asset_id: str
    bound_at_event_index: int  # Event stream index for determinism

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "category_id": self.category_id,
            "asset_id": self.asset_id,
            "bound_at_event_index": self.bound_at_event_index,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AssetBinding":
        return cls(
            entity_id=data["entity_id"],
            category_id=data["category_id"],
            asset_id=data["asset_id"],
            bound_at_event_index=data.get("bound_at_event_index", 0),
        )


# ---------------------------------------------------------------------------
# Replenishment Job Request
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReplenishmentRequest:
    """A request to generate more assets for a depleted pool.

    This is a stub interface — actual generation is NOT implemented here.
    The job queue records requests; a separate system fulfills them.
    """
    category_id: str
    count: int
    priority: int = 0  # Higher = more urgent

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category_id": self.category_id,
            "count": self.count,
            "priority": self.priority,
        }


# ---------------------------------------------------------------------------
# Binding Registry (aggregate state)
# ---------------------------------------------------------------------------

@dataclass
class BindingRegistry:
    """Registry of all entity→asset bindings.

    Tracks which assets are bound to which entities, ensuring no reuse.
    """
    bindings: List[AssetBinding] = field(default_factory=list)
    """Ordered list of all bindings (append-only)."""

    _entity_bindings: Dict[Tuple[str, str], AssetBinding] = field(
        default_factory=dict, repr=False
    )
    """Index: (entity_id, category_id) → binding. For O(1) lookup."""

    _bound_assets: Dict[str, str] = field(
        default_factory=dict, repr=False
    )
    """Index: asset_id → entity_id. Ensures no asset is bound twice."""

    def get_binding(self, entity_id: str, category_id: str) -> Optional[AssetBinding]:
        """Look up an existing binding."""
        return self._entity_bindings.get((entity_id, category_id))

    def is_asset_bound(self, asset_id: str) -> bool:
        """Check if an asset is already bound to any entity."""
        return asset_id in self._bound_assets

    def add_binding(self, binding: AssetBinding) -> None:
        """Record a new binding. Raises if asset already bound."""
        if binding.asset_id in self._bound_assets:
            raise ValueError(
                f"Asset {binding.asset_id} already bound to "
                f"{self._bound_assets[binding.asset_id]}"
            )
        key = (binding.entity_id, binding.category_id)
        if key in self._entity_bindings:
            raise ValueError(
                f"Entity {binding.entity_id} already has a binding "
                f"for category {binding.category_id}"
            )
        self.bindings.append(binding)
        self._entity_bindings[key] = binding
        self._bound_assets[binding.asset_id] = binding.entity_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bindings": [b.to_dict() for b in self.bindings],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BindingRegistry":
        registry = cls()
        for b_data in data.get("bindings", []):
            binding = AssetBinding.from_dict(b_data)
            registry.add_binding(binding)
        return registry


def compute_binding_id(entity_id: str, category_id: str, seed: int) -> str:
    """Compute a deterministic binding selection key.

    Used to select which available asset to bind when multiple are available.
    Same entity + category + seed → same key → same selection (given same pool).
    """
    raw = f"{seed}:{entity_id}:{category_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

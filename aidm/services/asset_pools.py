"""Asset Pools service — category pool management and deterministic binding.

Manages asset pools with target sizes, deterministic binding of assets to
entities, and replenishment job enqueueing. No actual generation — only state.

Deterministic: given the same seed + same pool contents + same binding
sequence, produces identical bindings.

Binding selection rule: when an entity needs an asset from a category,
compute a deterministic index into the available pool:
    index = int(sha256(seed:entity_id:category_id), 16) % len(available)
This ensures the same entity always gets the same asset from the same pool.

WO-CODE-DISCOVERY-001: Bestiary Knowledge Mask + Asset Binding Pools
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Mapping, Optional

from aidm.schemas.asset_binding import (
    AssetBinding,
    AssetPoolCategory,
    BindingRegistry,
    ReplenishmentRequest,
)
from aidm.services.job_queue_stub import JobQueueStub


class AssetPoolService:
    """Manages asset category pools and permanent entity bindings.

    Usage:
        service = AssetPoolService(seed=42)
        service.add_category(AssetPoolCategory("goblin_portrait", "portrait", 5,
                             available=["gob_a", "gob_b", "gob_c"]))
        asset_id = service.bind("goblin_01", "goblin_portrait")
        # asset_id is deterministic for the same seed + pool state
    """

    def __init__(self, seed: int, job_queue: Optional[JobQueueStub] = None) -> None:
        """Initialize the asset pool service.

        Args:
            seed: Master seed for deterministic asset selection.
            job_queue: Optional job queue for replenishment requests.
                       If None, a stub is created.
        """
        self._seed = seed
        self._categories: Dict[str, AssetPoolCategory] = {}
        self._registry = BindingRegistry()
        self._job_queue = job_queue or JobQueueStub()
        self._event_index = 0  # Monotonic counter for binding events

    @property
    def seed(self) -> int:
        return self._seed

    @property
    def registry(self) -> BindingRegistry:
        return self._registry

    @property
    def job_queue(self) -> JobQueueStub:
        return self._job_queue

    def add_category(self, category: AssetPoolCategory) -> None:
        """Register an asset category pool."""
        self._categories[category.category_id] = category

    def get_category(self, category_id: str) -> Optional[AssetPoolCategory]:
        """Look up a category by ID."""
        return self._categories.get(category_id)

    def list_categories(self) -> List[str]:
        """List all registered category IDs (sorted)."""
        return sorted(self._categories.keys())

    def bind(self, entity_id: str, category_id: str) -> Optional[str]:
        """Bind an asset to an entity from the specified category pool.

        If the entity already has a binding for this category, returns
        the existing binding's asset_id (idempotent).

        If the pool is empty, returns None and enqueues a replenishment job.

        The selection is deterministic:
            index = int(sha256(seed:entity_id:category_id), 16) % len(available)

        Args:
            entity_id: The entity to bind an asset to.
            category_id: The category pool to draw from.

        Returns:
            The bound asset_id, or None if pool is empty.
        """
        # Check for existing binding (idempotent)
        existing = self._registry.get_binding(entity_id, category_id)
        if existing is not None:
            return existing.asset_id

        # Look up category
        category = self._categories.get(category_id)
        if category is None:
            raise ValueError(f"Unknown category: {category_id}")

        # Pool empty?
        if not category.available:
            self._enqueue_replenishment(category_id, category.target_size)
            return None

        # Deterministic selection
        selection_key = f"{self._seed}:{entity_id}:{category_id}"
        selection_hash = hashlib.sha256(selection_key.encode("utf-8")).hexdigest()
        index = int(selection_hash, 16) % len(category.available)

        asset_id = category.available[index]

        # Create binding
        binding = AssetBinding(
            entity_id=entity_id,
            category_id=category_id,
            asset_id=asset_id,
            bound_at_event_index=self._event_index,
        )
        self._event_index += 1

        # Record binding and remove asset from pool
        self._registry.add_binding(binding)
        category.available.pop(index)

        # Check if pool needs replenishment
        if category.deficit > 0:
            self._enqueue_replenishment(category_id, category.deficit)

        return asset_id

    def get_binding(self, entity_id: str, category_id: str) -> Optional[AssetBinding]:
        """Look up an existing binding."""
        return self._registry.get_binding(entity_id, category_id)

    def get_entity_assets(self, entity_id: str) -> Dict[str, str]:
        """Get all asset bindings for an entity.

        Returns:
            Dict of category_id → asset_id.
        """
        result: Dict[str, str] = {}
        for binding in self._registry.bindings:
            if binding.entity_id == entity_id:
                result[binding.category_id] = binding.asset_id
        return result

    def add_asset_to_pool(self, category_id: str, asset_id: str) -> None:
        """Add a generated asset to a category pool.

        Called when a replenishment job completes.

        Args:
            category_id: The category to add to.
            asset_id: The new asset's ID.

        Raises:
            ValueError: If category doesn't exist or asset is already bound.
        """
        category = self._categories.get(category_id)
        if category is None:
            raise ValueError(f"Unknown category: {category_id}")
        if self._registry.is_asset_bound(asset_id):
            raise ValueError(f"Asset {asset_id} is already bound")
        if asset_id in category.available:
            raise ValueError(f"Asset {asset_id} already in pool")
        category.available.append(asset_id)

    def pool_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics for all pools."""
        stats: Dict[str, Dict[str, int]] = {}
        for cat_id, cat in sorted(self._categories.items()):
            bound_count = sum(
                1 for b in self._registry.bindings
                if b.category_id == cat_id
            )
            stats[cat_id] = {
                "target_size": cat.target_size,
                "available": len(cat.available),
                "bound": bound_count,
                "deficit": cat.deficit,
            }
        return stats

    def _enqueue_replenishment(self, category_id: str, count: int) -> None:
        """Enqueue a job to generate more assets for a pool."""
        # Don't duplicate pending requests for the same category
        existing = self._job_queue.get_pending_for_category(category_id)
        if existing:
            return
        self._job_queue.enqueue(ReplenishmentRequest(
            category_id=category_id,
            count=count,
            priority=1,
        ))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire service state."""
        return {
            "seed": self._seed,
            "categories": {
                k: v.to_dict() for k, v in sorted(self._categories.items())
            },
            "registry": self._registry.to_dict(),
            "job_queue": self._job_queue.to_dict(),
            "event_index": self._event_index,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AssetPoolService":
        """Restore from serialized state."""
        job_queue = JobQueueStub.from_dict(data.get("job_queue", {}))
        service = cls(seed=data["seed"], job_queue=job_queue)
        for cat_data in data.get("categories", {}).values():
            service.add_category(AssetPoolCategory.from_dict(cat_data))
        service._registry = BindingRegistry.from_dict(data.get("registry", {}))
        service._event_index = data.get("event_index", 0)
        return service

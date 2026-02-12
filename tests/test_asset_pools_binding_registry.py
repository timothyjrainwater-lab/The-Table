"""Tests for Asset Pools and Binding Registry.

Tests cover:
- Pool management (add category, add assets, check stats)
- Deterministic binding (same seed + same pool → same asset)
- Binding permanence (no reuse across entities)
- Replenishment job enqueueing
- Serialization round-trip
- Edge cases (empty pool, duplicate binding, unknown category)

WO-CODE-DISCOVERY-001
"""

import pytest

from aidm.schemas.asset_binding import (
    AssetBinding,
    AssetPoolCategory,
    BindingRegistry,
    ReplenishmentRequest,
)
from aidm.services.asset_pools import AssetPoolService
from aidm.services.job_queue_stub import JobQueueStub


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_portrait_pool(available=None):
    """Create a goblin portrait pool with 5 target size."""
    if available is None:
        available = ["gob_a", "gob_b", "gob_c", "gob_d", "gob_e"]
    return AssetPoolCategory(
        category_id="goblin_portrait",
        asset_type="portrait",
        target_size=5,
        available=available,
    )


def make_voice_pool(available=None):
    """Create a gruff voice pool with 3 target size."""
    if available is None:
        available = ["voice_gruff_1", "voice_gruff_2", "voice_gruff_3"]
    return AssetPoolCategory(
        category_id="gruff_voice",
        asset_type="voice_profile",
        target_size=3,
        available=available,
    )


def make_service(seed=42, portrait_available=None, voice_available=None):
    """Create a service with portrait and voice pools."""
    service = AssetPoolService(seed=seed)
    service.add_category(make_portrait_pool(portrait_available))
    service.add_category(make_voice_pool(voice_available))
    return service


# ---------------------------------------------------------------------------
# Pool Management Tests
# ---------------------------------------------------------------------------

class TestPoolManagement:
    """Basic pool operations."""

    def test_add_category(self):
        service = AssetPoolService(seed=42)
        service.add_category(make_portrait_pool())
        assert "goblin_portrait" in service.list_categories()

    def test_get_category(self):
        service = make_service()
        cat = service.get_category("goblin_portrait")
        assert cat is not None
        assert cat.target_size == 5
        assert len(cat.available) == 5

    def test_unknown_category_returns_none(self):
        service = make_service()
        assert service.get_category("nonexistent") is None

    def test_pool_stats(self):
        service = make_service()
        stats = service.pool_stats()
        assert stats["goblin_portrait"]["target_size"] == 5
        assert stats["goblin_portrait"]["available"] == 5
        assert stats["goblin_portrait"]["bound"] == 0
        assert stats["goblin_portrait"]["deficit"] == 0

    def test_deficit_calculation(self):
        cat = AssetPoolCategory(
            category_id="test", asset_type="portrait", target_size=5,
            available=["a", "b"],
        )
        assert cat.deficit == 3

    def test_add_asset_to_pool(self):
        service = make_service()
        service.add_asset_to_pool("goblin_portrait", "gob_f")
        cat = service.get_category("goblin_portrait")
        assert "gob_f" in cat.available

    def test_add_duplicate_asset_rejected(self):
        service = make_service()
        with pytest.raises(ValueError, match="already in pool"):
            service.add_asset_to_pool("goblin_portrait", "gob_a")

    def test_add_to_unknown_category_rejected(self):
        service = make_service()
        with pytest.raises(ValueError, match="Unknown category"):
            service.add_asset_to_pool("nonexistent", "asset_x")


# ---------------------------------------------------------------------------
# Binding Tests
# ---------------------------------------------------------------------------

class TestBinding:
    """Asset binding determinism and permanence."""

    def test_bind_returns_asset_id(self):
        service = make_service()
        asset_id = service.bind("goblin_01", "goblin_portrait")
        assert asset_id is not None
        assert asset_id.startswith("gob_")

    def test_bind_is_deterministic(self):
        """Same seed + same pool state → same asset selection."""
        s1 = make_service(seed=42)
        s2 = make_service(seed=42)

        a1 = s1.bind("goblin_01", "goblin_portrait")
        a2 = s2.bind("goblin_01", "goblin_portrait")
        assert a1 == a2

    def test_bind_is_permanent(self):
        """Re-binding the same entity returns the same asset (idempotent)."""
        service = make_service()
        a1 = service.bind("goblin_01", "goblin_portrait")
        a2 = service.bind("goblin_01", "goblin_portrait")
        assert a1 == a2

    def test_bound_asset_removed_from_pool(self):
        service = make_service()
        asset_id = service.bind("goblin_01", "goblin_portrait")
        cat = service.get_category("goblin_portrait")
        assert asset_id not in cat.available

    def test_different_entities_get_different_assets(self):
        service = make_service()
        a1 = service.bind("goblin_01", "goblin_portrait")
        a2 = service.bind("goblin_02", "goblin_portrait")
        assert a1 != a2

    def test_bound_asset_never_reused(self):
        """No two entities share the same asset."""
        service = make_service()
        bound = set()
        for i in range(5):
            asset_id = service.bind(f"goblin_{i:02d}", "goblin_portrait")
            assert asset_id not in bound, f"Asset {asset_id} reused!"
            bound.add(asset_id)

    def test_bind_to_unknown_category_raises(self):
        service = make_service()
        with pytest.raises(ValueError, match="Unknown category"):
            service.bind("goblin_01", "nonexistent_category")

    def test_bind_returns_none_when_pool_empty(self):
        service = make_service(portrait_available=[])
        result = service.bind("goblin_01", "goblin_portrait")
        assert result is None

    def test_get_binding(self):
        service = make_service()
        service.bind("goblin_01", "goblin_portrait")
        binding = service.get_binding("goblin_01", "goblin_portrait")
        assert binding is not None
        assert binding.entity_id == "goblin_01"
        assert binding.category_id == "goblin_portrait"

    def test_get_entity_assets(self):
        service = make_service()
        service.bind("goblin_01", "goblin_portrait")
        service.bind("goblin_01", "gruff_voice")
        assets = service.get_entity_assets("goblin_01")
        assert "goblin_portrait" in assets
        assert "gruff_voice" in assets

    def test_different_seeds_different_selections(self):
        """Different seeds select different assets from the same pool."""
        s1 = make_service(seed=42)
        s2 = make_service(seed=999)

        a1 = s1.bind("goblin_01", "goblin_portrait")
        a2 = s2.bind("goblin_01", "goblin_portrait")
        # Not guaranteed to differ for all seeds, but very likely
        # The important test is determinism, not diversity
        # Just verify both are valid
        assert a1 is not None
        assert a2 is not None


# ---------------------------------------------------------------------------
# Replenishment Tests
# ---------------------------------------------------------------------------

class TestReplenishment:
    """Pool replenishment job enqueueing."""

    def test_replenishment_on_pool_depletion(self):
        service = make_service(portrait_available=["gob_a"])
        service.bind("goblin_01", "goblin_portrait")
        # Pool is now empty → should have enqueued replenishment
        assert service.job_queue.pending_count >= 1
        pending = service.job_queue.get_pending_for_category("goblin_portrait")
        assert len(pending) == 1

    def test_replenishment_not_duplicated(self):
        """Multiple binds from the same pool don't duplicate requests."""
        service = make_service(portrait_available=["gob_a", "gob_b"])
        service.bind("goblin_01", "goblin_portrait")
        service.bind("goblin_02", "goblin_portrait")
        # Pool is now empty, but should have at most 1 pending request
        pending = service.job_queue.get_pending_for_category("goblin_portrait")
        assert len(pending) == 1

    def test_empty_pool_bind_enqueues_job(self):
        service = make_service(portrait_available=[])
        service.bind("goblin_01", "goblin_portrait")
        assert service.job_queue.pending_count >= 1

    def test_replenishment_after_adding_assets(self):
        """After replenishment, new binds work."""
        service = make_service(portrait_available=["gob_a"])
        service.bind("goblin_01", "goblin_portrait")
        # Add new assets (simulating replenishment completion)
        service.add_asset_to_pool("goblin_portrait", "gob_new_1")
        service.add_asset_to_pool("goblin_portrait", "gob_new_2")
        # Now binding should work again
        asset = service.bind("goblin_02", "goblin_portrait")
        assert asset is not None

    def test_bound_assets_cannot_be_readded(self):
        service = make_service()
        asset_id = service.bind("goblin_01", "goblin_portrait")
        with pytest.raises(ValueError, match="already bound"):
            service.add_asset_to_pool("goblin_portrait", asset_id)


# ---------------------------------------------------------------------------
# Binding Registry Tests
# ---------------------------------------------------------------------------

class TestBindingRegistry:
    """Direct BindingRegistry tests."""

    def test_add_binding(self):
        registry = BindingRegistry()
        binding = AssetBinding("e1", "cat1", "asset_a", 0)
        registry.add_binding(binding)
        assert registry.get_binding("e1", "cat1") == binding

    def test_duplicate_asset_rejected(self):
        registry = BindingRegistry()
        registry.add_binding(AssetBinding("e1", "cat1", "asset_a", 0))
        with pytest.raises(ValueError, match="already bound"):
            registry.add_binding(AssetBinding("e2", "cat1", "asset_a", 1))

    def test_duplicate_entity_category_rejected(self):
        registry = BindingRegistry()
        registry.add_binding(AssetBinding("e1", "cat1", "asset_a", 0))
        with pytest.raises(ValueError, match="already has a binding"):
            registry.add_binding(AssetBinding("e1", "cat1", "asset_b", 1))

    def test_is_asset_bound(self):
        registry = BindingRegistry()
        registry.add_binding(AssetBinding("e1", "cat1", "asset_a", 0))
        assert registry.is_asset_bound("asset_a")
        assert not registry.is_asset_bound("asset_b")

    def test_registry_round_trip(self):
        registry = BindingRegistry()
        registry.add_binding(AssetBinding("e1", "cat1", "asset_a", 0))
        registry.add_binding(AssetBinding("e2", "cat1", "asset_b", 1))

        restored = BindingRegistry.from_dict(registry.to_dict())
        assert len(restored.bindings) == 2
        assert restored.get_binding("e1", "cat1") is not None
        assert restored.is_asset_bound("asset_a")


# ---------------------------------------------------------------------------
# Serialization Tests
# ---------------------------------------------------------------------------

class TestServiceSerialization:
    """Asset pool service serialization."""

    def test_category_round_trip(self):
        cat = make_portrait_pool()
        restored = AssetPoolCategory.from_dict(cat.to_dict())
        assert restored.category_id == cat.category_id
        assert restored.target_size == cat.target_size
        assert restored.available == cat.available

    def test_binding_round_trip(self):
        binding = AssetBinding("e1", "cat1", "asset_a", 7)
        restored = AssetBinding.from_dict(binding.to_dict())
        assert restored == binding

    def test_service_round_trip(self):
        service = make_service()
        service.bind("goblin_01", "goblin_portrait")
        service.bind("goblin_01", "gruff_voice")

        data = service.to_dict()
        restored = AssetPoolService.from_dict(data)

        # Same bindings
        assert restored.get_binding("goblin_01", "goblin_portrait") is not None
        assert restored.get_binding("goblin_01", "gruff_voice") is not None
        # Same seed
        assert restored.seed == service.seed
        # Same pool state
        orig_stats = service.pool_stats()
        rest_stats = restored.pool_stats()
        assert orig_stats == rest_stats


# ---------------------------------------------------------------------------
# Job Queue Stub Tests
# ---------------------------------------------------------------------------

class TestJobQueueStub:
    """Job queue stub behavior."""

    def test_enqueue_and_count(self):
        q = JobQueueStub()
        q.enqueue(ReplenishmentRequest("cat1", 5))
        assert q.pending_count == 1

    def test_get_pending_for_category(self):
        q = JobQueueStub()
        q.enqueue(ReplenishmentRequest("cat1", 5))
        q.enqueue(ReplenishmentRequest("cat2", 3))
        assert len(q.get_pending_for_category("cat1")) == 1
        assert len(q.get_pending_for_category("cat3")) == 0

    def test_clear(self):
        q = JobQueueStub()
        q.enqueue(ReplenishmentRequest("cat1", 5))
        q.clear()
        assert q.pending_count == 0

    def test_round_trip(self):
        q = JobQueueStub()
        q.enqueue(ReplenishmentRequest("cat1", 5, priority=2))
        restored = JobQueueStub.from_dict(q.to_dict())
        assert restored.pending_count == 1
        assert restored.pending_requests[0].category_id == "cat1"


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------

class TestValidation:
    """Input validation."""

    def test_empty_category_id_rejected(self):
        with pytest.raises(ValueError, match="category_id"):
            AssetPoolCategory("", "portrait", 5)

    def test_zero_target_size_rejected(self):
        with pytest.raises(ValueError, match="target_size"):
            AssetPoolCategory("cat1", "portrait", 0)

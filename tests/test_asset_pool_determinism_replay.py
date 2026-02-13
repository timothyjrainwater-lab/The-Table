"""Determinism replay tests for asset pools + knowledge mask.

Runs the same event stream 50+ times with identical seeds and verifies
byte-identical outputs for:
- Asset bindings (same entity → same asset)
- Knowledge tier states (same events → same tiers)
- Masked views (same tier → same fields)

WO-CODE-DISCOVERY-001: Acceptance criterion — replay tests show byte-identical
outputs for bindings + masked views given identical inputs.
"""

import json

import pytest

from aidm.schemas.knowledge_mask import (
    DiscoveryEvent,
    DiscoveryEventType,
    KnowledgeTier,
)
from aidm.schemas.asset_binding import AssetPoolCategory
from aidm.services.discovery_log import DiscoveryLog
from aidm.services.asset_pools import AssetPoolService


# ---------------------------------------------------------------------------
# Test Data (deterministic event streams)
# ---------------------------------------------------------------------------

ENTITY_DATA = {
    "entity_type": "beast",
    "display_name": "Ashenmoor Wyvern",
    "size_category": "large",
    "rumor_text": "A great winged beast.",
    "appearance": "Leathery wings, barbed tail.",
    "speed": {"walk": 20, "fly": 60},
    "senses": {"darkvision": 60},
    "natural_armor": True,
    "observed_weapons": ["bite", "tail_sting"],
    "habitat": "Mountain crags",
    "ac_estimate": "heavily armored",
    "hp_estimate": "very tough",
    "attack_pattern": "Dive, then melee",
    "save_estimates": {"fort": "strong", "ref": "average", "will": "weak"},
    "observed_abilities": ["poison_sting"],
    "resistances_observed": [],
    "morale_behavior": "aggressive",
    "ac": 18,
    "hp_max": 59,
    "hit_dice": "7d12+14",
    "base_attack_bonus": 7,
    "attack_details": [{"name": "bite", "bonus": 10, "damage": "2d6+4"}],
    "saves_exact": {"fort": 7, "ref": 5, "will": 5},
    "special_abilities": ["poison_sting"],
    "special_qualities": ["darkvision_60"],
    "damage_reduction": None,
    "spell_resistance": None,
    "vulnerabilities": [],
    "skill_ranks": {"spot": 10},
    "feats": ["alertness"],
    "challenge_rating": 6,
    "lore_text": "A territorial predator.",
}

# A repeatable sequence of discovery events
DISCOVERY_EVENTS = [
    DiscoveryEvent(DiscoveryEventType.NPC_TOLD_YOU, "p1", "wyvern_01"),
    DiscoveryEvent(DiscoveryEventType.NPC_TOLD_YOU, "p2", "wyvern_01"),
    DiscoveryEvent(DiscoveryEventType.ENCOUNTER_SEEN, "p1", "wyvern_01"),
    DiscoveryEvent(DiscoveryEventType.ENCOUNTER_SEEN, "p1", "goblin_01"),
    DiscoveryEvent(DiscoveryEventType.COMBAT_OBSERVED, "p1", "wyvern_01",
                   observed_facts=("ac_estimate=heavily armored",)),
    DiscoveryEvent(DiscoveryEventType.COMBAT_OBSERVED, "p2", "goblin_01"),
    DiscoveryEvent(DiscoveryEventType.STUDY_SUCCESS, "p1", "wyvern_01"),
    DiscoveryEvent(DiscoveryEventType.ENCOUNTER_SEEN, "p2", "wyvern_01"),
    DiscoveryEvent(DiscoveryEventType.NPC_TOLD_YOU, "p1", "troll_01"),
    DiscoveryEvent(DiscoveryEventType.COMBAT_OBSERVED, "p1", "troll_01"),
]

# A repeatable sequence of binding events
BINDING_ENTITIES = [
    ("goblin_01", "goblin_portrait"),
    ("goblin_02", "goblin_portrait"),
    ("goblin_03", "goblin_portrait"),
    ("merchant_01", "human_portrait"),
    ("merchant_02", "human_portrait"),
    ("goblin_01", "gruff_voice"),
    ("goblin_02", "gruff_voice"),
    ("merchant_01", "smooth_voice"),
]

SEED = 42
POOL_DATA = {
    "goblin_portrait": ["gob_p_001", "gob_p_002", "gob_p_003", "gob_p_004", "gob_p_005"],
    "human_portrait": ["hum_p_001", "hum_p_002", "hum_p_003"],
    "gruff_voice": ["vg_001", "vg_002", "vg_003"],
    "smooth_voice": ["vs_001", "vs_002"],
}


def build_discovery_log():
    """Build a discovery log from the standard event stream."""
    log = DiscoveryLog()
    for event in DISCOVERY_EVENTS:
        log.apply_event(event)
    return log


def build_asset_service():
    """Build an asset pool service from the standard pool data."""
    service = AssetPoolService(seed=SEED)
    for cat_id, assets in sorted(POOL_DATA.items()):
        service.add_category(AssetPoolCategory(
            category_id=cat_id,
            asset_type="portrait" if "portrait" in cat_id else "voice_profile",
            target_size=len(assets),
            available=list(assets),  # Fresh copy each time
        ))
    return service


def run_binding_sequence(service):
    """Execute the standard binding sequence, return results."""
    results = []
    for entity_id, category_id in BINDING_ENTITIES:
        asset_id = service.bind(entity_id, category_id)
        results.append((entity_id, category_id, asset_id))
    return results


# ---------------------------------------------------------------------------
# Determinism: Discovery Log (50 replays)
# ---------------------------------------------------------------------------

class TestDiscoveryLogDeterminism:
    """Same event stream → identical knowledge state across 50 runs."""

    REPLAY_COUNT = 50

    def test_tier_determinism_50_replays(self):
        """Tiers are identical across 50 replays of the same event stream."""
        reference_tiers = None

        for i in range(self.REPLAY_COUNT):
            log = build_discovery_log()

            tiers = {}
            for event in DISCOVERY_EVENTS:
                key = f"{event.player_id}:{event.entity_id}"
                tiers[key] = log.get_tier(event.player_id, event.entity_id).name

            if reference_tiers is None:
                reference_tiers = tiers
            else:
                assert tiers == reference_tiers, (
                    f"Tier mismatch at replay {i}: {tiers} != {reference_tiers}"
                )

    def test_masked_view_determinism_50_replays(self):
        """Masked views are identical across 50 replays."""
        reference_views = None

        for i in range(self.REPLAY_COUNT):
            log = build_discovery_log()

            views = {}
            for event in DISCOVERY_EVENTS:
                view = log.get_entry_view(
                    event.player_id, event.entity_id, ENTITY_DATA
                )
                views[f"{event.player_id}:{event.entity_id}"] = view.to_dict()

            if reference_views is None:
                reference_views = views
            else:
                assert views == reference_views, (
                    f"View mismatch at replay {i}"
                )

    def test_serialization_determinism_50_replays(self):
        """Serialized log is identical across 50 replays."""
        reference_json = None

        for i in range(self.REPLAY_COUNT):
            log = build_discovery_log()
            serialized = json.dumps(log.to_dict(), sort_keys=True)

            if reference_json is None:
                reference_json = serialized
            else:
                assert serialized == reference_json, (
                    f"Serialization mismatch at replay {i}"
                )


# ---------------------------------------------------------------------------
# Determinism: Asset Pools (50 replays)
# ---------------------------------------------------------------------------

class TestAssetPoolDeterminism:
    """Same seed + same pool + same sequence → identical bindings across 50 runs."""

    REPLAY_COUNT = 50

    def test_binding_determinism_50_replays(self):
        """Bindings are identical across 50 replays."""
        reference_bindings = None

        for i in range(self.REPLAY_COUNT):
            service = build_asset_service()
            results = run_binding_sequence(service)

            binding_snapshot = [
                (entity_id, cat_id, asset_id)
                for entity_id, cat_id, asset_id in results
            ]

            if reference_bindings is None:
                reference_bindings = binding_snapshot
            else:
                assert binding_snapshot == reference_bindings, (
                    f"Binding mismatch at replay {i}: "
                    f"{binding_snapshot} != {reference_bindings}"
                )

    def test_pool_state_determinism_50_replays(self):
        """Pool stats are identical across 50 replays."""
        reference_stats = None

        for i in range(self.REPLAY_COUNT):
            service = build_asset_service()
            run_binding_sequence(service)
            stats = service.pool_stats()

            if reference_stats is None:
                reference_stats = stats
            else:
                assert stats == reference_stats, (
                    f"Pool stats mismatch at replay {i}"
                )

    def test_serialization_determinism_50_replays(self):
        """Serialized service state is identical across 50 replays."""
        reference_json = None

        for i in range(self.REPLAY_COUNT):
            service = build_asset_service()
            run_binding_sequence(service)
            serialized = json.dumps(service.to_dict(), sort_keys=True)

            if reference_json is None:
                reference_json = serialized
            else:
                assert serialized == reference_json, (
                    f"Serialization mismatch at replay {i}"
                )

    def test_job_queue_determinism_50_replays(self):
        """Job queue state is identical across 50 replays."""
        reference_jobs = None

        for i in range(self.REPLAY_COUNT):
            service = build_asset_service()
            run_binding_sequence(service)
            jobs = json.dumps(service.job_queue.to_dict(), sort_keys=True)

            if reference_jobs is None:
                reference_jobs = jobs
            else:
                assert jobs == reference_jobs, (
                    f"Job queue mismatch at replay {i}"
                )


# ---------------------------------------------------------------------------
# Combined Determinism (Discovery + Asset Pools)
# ---------------------------------------------------------------------------

class TestCombinedDeterminism:
    """Full system: discovery events + asset bindings across 50 replays."""

    REPLAY_COUNT = 50

    def test_full_system_determinism_50_replays(self):
        """Everything together: events + bindings + views → identical."""
        reference_snapshot = None

        for i in range(self.REPLAY_COUNT):
            # Build both systems
            discovery = build_discovery_log()
            assets = build_asset_service()
            binding_results = run_binding_sequence(assets)

            # Snapshot everything
            snapshot = {
                "discovery_log": json.dumps(discovery.to_dict(), sort_keys=True),
                "asset_service": json.dumps(assets.to_dict(), sort_keys=True),
                "bindings": [
                    (e, c, a) for e, c, a in binding_results
                ],
                "views": {
                    f"{ev.player_id}:{ev.entity_id}": discovery.get_entry_view(
                        ev.player_id, ev.entity_id, ENTITY_DATA
                    ).to_dict()
                    for ev in DISCOVERY_EVENTS
                },
            }

            snapshot_json = json.dumps(snapshot, sort_keys=True, default=str)

            if reference_snapshot is None:
                reference_snapshot = snapshot_json
            else:
                assert snapshot_json == reference_snapshot, (
                    f"Full system mismatch at replay {i}"
                )


# ---------------------------------------------------------------------------
# No Time-Based or System-Clock Dependence
# ---------------------------------------------------------------------------

class TestNoTimeDependence:
    """Verify no time-based randomness affects results."""

    def test_no_timestamp_in_binding(self):
        """AssetBinding uses event_index, not timestamps."""
        service = build_asset_service()
        service.bind("goblin_01", "goblin_portrait")
        binding = service.get_binding("goblin_01", "goblin_portrait")
        d = binding.to_dict()
        assert "timestamp" not in d
        assert "bound_at_event_index" in d

    def test_no_timestamp_in_knowledge_entry(self):
        """KnowledgeEntry tier doesn't depend on time."""
        log = build_discovery_log()
        entry = log.get_entry("p1", "wyvern_01")
        d = entry.to_dict()
        assert "timestamp" not in d
        assert "tier" in d

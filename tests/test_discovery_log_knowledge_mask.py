"""Tests for Discovery Log knowledge mask.

Tests cover:
- Tier transition rules (heard→seen→fought→studied)
- Field-leak tests (assert forbidden fields absent)
- Masked view correctness per tier
- Tier never decreases
- Event log integrity
- Serialization round-trip

WO-CODE-DISCOVERY-001
"""

import pytest

from aidm.schemas.knowledge_mask import (
    DiscoveryEvent,
    DiscoveryEventType,
    KnowledgeEntry,
    KnowledgeTier,
    MaskedEntityView,
    REVEAL_SPEC,
    TIER_TRANSITIONS,
)
from aidm.services.discovery_log import DiscoveryLog


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FULL_ENTITY_DATA = {
    # HEARD_OF fields
    "entity_type": "beast",
    "display_name": "Ashenmoor Wyvern",
    "size_category": "large",
    "rumor_text": "Peasants speak of a great winged beast in the crags.",
    # SEEN fields
    "appearance": "Leathery wings, barbed tail, mottled grey scales.",
    "speed": {"walk": 20, "fly": 60},
    "senses": {"darkvision": 60, "scent": True},
    "natural_armor": True,
    "observed_weapons": ["bite", "tail_sting"],
    "habitat": "Mountain crags",
    # FOUGHT fields
    "ac_estimate": "heavily armored",
    "hp_estimate": "very tough",
    "attack_pattern": "Dive attack, then bite and sting in melee",
    "save_estimates": {"fortitude": "strong", "reflex": "average", "will": "weak"},
    "observed_abilities": ["poison_sting"],
    "resistances_observed": [],
    "morale_behavior": "fights aggressively, retreats when badly wounded",
    # STUDIED fields
    "ac": 18,
    "hp_max": 59,
    "hit_dice": "7d12+14",
    "base_attack_bonus": 7,
    "attack_details": [
        {"name": "bite", "bonus": 10, "damage": "2d6+4"},
        {"name": "tail_sting", "bonus": 5, "damage": "1d6+2", "special": "poison"},
    ],
    "saves_exact": {"fort": 7, "ref": 5, "will": 5},
    "special_abilities": ["poison_sting", "improved_grab"],
    "special_qualities": ["darkvision_60", "scent"],
    "damage_reduction": None,
    "spell_resistance": None,
    "vulnerabilities": [],
    "skill_ranks": {"spot": 10, "listen": 8},
    "feats": ["alertness", "flyby_attack"],
    "challenge_rating": 6,
    "lore_text": "The Ashenmoor Wyvern is a territorial predator...",
}


def make_event(event_type, player_id="player_1", entity_id="wyvern_01",
               observed_facts=(), metadata=()):
    return DiscoveryEvent(
        event_type=event_type,
        player_id=player_id,
        entity_id=entity_id,
        observed_facts=observed_facts,
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Tier Transition Tests
# ---------------------------------------------------------------------------

class TestTierTransitions:
    """Tier transitions follow explicit event rules."""

    def test_starts_at_unknown(self):
        log = DiscoveryLog()
        assert log.get_tier("player_1", "wyvern_01") == KnowledgeTier.UNKNOWN

    def test_npc_told_you_sets_heard_of(self):
        log = DiscoveryLog()
        tier = log.apply_event(make_event(DiscoveryEventType.NPC_TOLD_YOU))
        assert tier == KnowledgeTier.HEARD_OF

    def test_encounter_seen_sets_seen(self):
        log = DiscoveryLog()
        tier = log.apply_event(make_event(DiscoveryEventType.ENCOUNTER_SEEN))
        assert tier == KnowledgeTier.SEEN

    def test_combat_observed_sets_fought(self):
        log = DiscoveryLog()
        tier = log.apply_event(make_event(DiscoveryEventType.COMBAT_OBSERVED))
        assert tier == KnowledgeTier.FOUGHT

    def test_study_success_sets_studied(self):
        log = DiscoveryLog()
        tier = log.apply_event(make_event(DiscoveryEventType.STUDY_SUCCESS))
        assert tier == KnowledgeTier.STUDIED

    def test_progressive_advancement(self):
        """Advance through all tiers in order."""
        log = DiscoveryLog()

        t1 = log.apply_event(make_event(DiscoveryEventType.NPC_TOLD_YOU))
        assert t1 == KnowledgeTier.HEARD_OF

        t2 = log.apply_event(make_event(DiscoveryEventType.ENCOUNTER_SEEN))
        assert t2 == KnowledgeTier.SEEN

        t3 = log.apply_event(make_event(DiscoveryEventType.COMBAT_OBSERVED))
        assert t3 == KnowledgeTier.FOUGHT

        t4 = log.apply_event(make_event(DiscoveryEventType.STUDY_SUCCESS))
        assert t4 == KnowledgeTier.STUDIED

    def test_tier_never_decreases(self):
        """A lower-tier event cannot reduce the tier."""
        log = DiscoveryLog()

        log.apply_event(make_event(DiscoveryEventType.STUDY_SUCCESS))
        assert log.get_tier("player_1", "wyvern_01") == KnowledgeTier.STUDIED

        # NPC_TOLD_YOU (heard_of) should NOT reduce tier
        log.apply_event(make_event(DiscoveryEventType.NPC_TOLD_YOU))
        assert log.get_tier("player_1", "wyvern_01") == KnowledgeTier.STUDIED

    def test_skip_tiers(self):
        """Can jump directly to higher tiers (e.g., study without seeing)."""
        log = DiscoveryLog()
        tier = log.apply_event(make_event(DiscoveryEventType.STUDY_SUCCESS))
        assert tier == KnowledgeTier.STUDIED

    def test_duplicate_event_is_idempotent(self):
        """Applying the same event twice doesn't change tier."""
        log = DiscoveryLog()
        t1 = log.apply_event(make_event(DiscoveryEventType.ENCOUNTER_SEEN))
        t2 = log.apply_event(make_event(DiscoveryEventType.ENCOUNTER_SEEN))
        assert t1 == t2 == KnowledgeTier.SEEN

    def test_independent_players(self):
        """Different players have independent knowledge."""
        log = DiscoveryLog()

        log.apply_event(make_event(
            DiscoveryEventType.STUDY_SUCCESS, player_id="player_1"
        ))
        log.apply_event(make_event(
            DiscoveryEventType.ENCOUNTER_SEEN, player_id="player_2"
        ))

        assert log.get_tier("player_1", "wyvern_01") == KnowledgeTier.STUDIED
        assert log.get_tier("player_2", "wyvern_01") == KnowledgeTier.SEEN

    def test_independent_entities(self):
        """Knowledge about different entities is independent."""
        log = DiscoveryLog()

        log.apply_event(make_event(
            DiscoveryEventType.STUDY_SUCCESS, entity_id="wyvern_01"
        ))
        log.apply_event(make_event(
            DiscoveryEventType.NPC_TOLD_YOU, entity_id="goblin_01"
        ))

        assert log.get_tier("player_1", "wyvern_01") == KnowledgeTier.STUDIED
        assert log.get_tier("player_1", "goblin_01") == KnowledgeTier.HEARD_OF


# ---------------------------------------------------------------------------
# Masked View Tests
# ---------------------------------------------------------------------------

class TestMaskedView:
    """Masked views expose only fields allowed at the current tier."""

    def test_unknown_reveals_nothing(self):
        log = DiscoveryLog()
        view = log.get_entry_view("player_1", "wyvern_01", FULL_ENTITY_DATA)
        assert view.tier == KnowledgeTier.UNKNOWN
        assert view.fields == ()
        assert view.field_names == frozenset()

    def test_heard_of_reveals_only_heard_of_fields(self):
        log = DiscoveryLog()
        log.apply_event(make_event(DiscoveryEventType.NPC_TOLD_YOU))
        view = log.get_entry_view("player_1", "wyvern_01", FULL_ENTITY_DATA)

        assert view.tier == KnowledgeTier.HEARD_OF
        expected = REVEAL_SPEC[KnowledgeTier.HEARD_OF]
        assert view.field_names == expected & set(FULL_ENTITY_DATA.keys())

    def test_seen_reveals_seen_fields(self):
        log = DiscoveryLog()
        log.apply_event(make_event(DiscoveryEventType.ENCOUNTER_SEEN))
        view = log.get_entry_view("player_1", "wyvern_01", FULL_ENTITY_DATA)

        assert view.tier == KnowledgeTier.SEEN
        # Must include heard_of fields + seen fields
        assert "display_name" in view.field_names
        assert "appearance" in view.field_names
        assert "speed" in view.field_names

    def test_fought_reveals_fought_fields(self):
        log = DiscoveryLog()
        log.apply_event(make_event(DiscoveryEventType.COMBAT_OBSERVED))
        view = log.get_entry_view("player_1", "wyvern_01", FULL_ENTITY_DATA)

        assert view.tier == KnowledgeTier.FOUGHT
        assert "ac_estimate" in view.field_names
        assert "attack_pattern" in view.field_names

    def test_studied_reveals_all(self):
        log = DiscoveryLog()
        log.apply_event(make_event(DiscoveryEventType.STUDY_SUCCESS))
        view = log.get_entry_view("player_1", "wyvern_01", FULL_ENTITY_DATA)

        assert view.tier == KnowledgeTier.STUDIED
        assert "ac" in view.field_names
        assert "hp_max" in view.field_names
        assert "challenge_rating" in view.field_names

    def test_get_field_returns_value(self):
        log = DiscoveryLog()
        log.apply_event(make_event(DiscoveryEventType.ENCOUNTER_SEEN))
        view = log.get_entry_view("player_1", "wyvern_01", FULL_ENTITY_DATA)

        assert view.get_field("display_name") == "Ashenmoor Wyvern"
        assert view.get_field("ac") is None  # Not visible at SEEN tier

    def test_missing_entity_data_fields_not_fabricated(self):
        """If entity_data lacks a field that the tier allows, it's still absent."""
        log = DiscoveryLog()
        log.apply_event(make_event(DiscoveryEventType.NPC_TOLD_YOU))

        sparse_data = {"entity_type": "beast", "display_name": "Wyvern"}
        view = log.get_entry_view("player_1", "wyvern_01", sparse_data)

        assert "entity_type" in view.field_names
        assert "display_name" in view.field_names
        # rumor_text is allowed but not in sparse_data → absent
        assert "rumor_text" not in view.field_names


# ---------------------------------------------------------------------------
# Field Leakage Tests
# ---------------------------------------------------------------------------

class TestFieldLeakage:
    """Ensure forbidden fields are ABSENT at lower tiers."""

    COMBAT_STATS = {"ac", "hp_max", "hit_dice", "base_attack_bonus",
                    "attack_details", "saves_exact", "challenge_rating"}
    SPECIAL_FIELDS = {"special_abilities", "special_qualities",
                      "damage_reduction", "spell_resistance", "vulnerabilities"}

    def test_heard_of_no_combat_stats(self):
        log = DiscoveryLog()
        log.apply_event(make_event(DiscoveryEventType.NPC_TOLD_YOU))
        view = log.get_entry_view("player_1", "wyvern_01", FULL_ENTITY_DATA)

        for field in self.COMBAT_STATS | self.SPECIAL_FIELDS:
            assert field not in view.field_names, f"Leaked field: {field}"

    def test_seen_no_combat_stats(self):
        log = DiscoveryLog()
        log.apply_event(make_event(DiscoveryEventType.ENCOUNTER_SEEN))
        view = log.get_entry_view("player_1", "wyvern_01", FULL_ENTITY_DATA)

        for field in self.COMBAT_STATS | self.SPECIAL_FIELDS:
            assert field not in view.field_names, f"Leaked field: {field}"

    def test_fought_no_exact_stats(self):
        """FOUGHT reveals estimates, not exact values."""
        log = DiscoveryLog()
        log.apply_event(make_event(DiscoveryEventType.COMBAT_OBSERVED))
        view = log.get_entry_view("player_1", "wyvern_01", FULL_ENTITY_DATA)

        # Exact stats should NOT be present
        assert "ac" not in view.field_names
        assert "hp_max" not in view.field_names
        assert "saves_exact" not in view.field_names

        # Estimates SHOULD be present
        assert "ac_estimate" in view.field_names
        assert "hp_estimate" in view.field_names

    def test_studied_reveals_exact_stats(self):
        """STUDIED reveals everything including exact stats."""
        log = DiscoveryLog()
        log.apply_event(make_event(DiscoveryEventType.STUDY_SUCCESS))
        view = log.get_entry_view("player_1", "wyvern_01", FULL_ENTITY_DATA)

        for field in self.COMBAT_STATS:
            assert field in view.field_names, f"Missing field at STUDIED: {field}"


# ---------------------------------------------------------------------------
# Reveal Spec Consistency Tests
# ---------------------------------------------------------------------------

class TestRevealSpec:
    """Verify reveal spec invariants."""

    def test_tiers_are_monotonically_increasing(self):
        """Each tier reveals a superset of the previous tier's fields."""
        tiers = [KnowledgeTier.UNKNOWN, KnowledgeTier.HEARD_OF,
                 KnowledgeTier.SEEN, KnowledgeTier.FOUGHT, KnowledgeTier.STUDIED]
        for i in range(len(tiers) - 1):
            lower = REVEAL_SPEC[tiers[i]]
            higher = REVEAL_SPEC[tiers[i + 1]]
            assert lower <= higher, (
                f"Tier {tiers[i+1].name} does not include all fields "
                f"from {tiers[i].name}: missing {lower - higher}"
            )

    def test_unknown_reveals_nothing(self):
        assert REVEAL_SPEC[KnowledgeTier.UNKNOWN] == frozenset()

    def test_studied_is_superset_of_all(self):
        studied = REVEAL_SPEC[KnowledgeTier.STUDIED]
        for tier in KnowledgeTier:
            assert REVEAL_SPEC[tier] <= studied


# ---------------------------------------------------------------------------
# Observed Facts Tests
# ---------------------------------------------------------------------------

class TestObservedFacts:
    """Observed facts are recorded from combat events."""

    def test_observed_facts_from_combat(self):
        log = DiscoveryLog()
        event = make_event(
            DiscoveryEventType.COMBAT_OBSERVED,
            observed_facts=("ac_estimate=heavily armored", "hp_estimate=very tough"),
        )
        log.apply_event(event)

        entry = log.get_entry("player_1", "wyvern_01")
        assert entry is not None
        assert entry.observed_facts["ac_estimate"] == "heavily armored"
        assert entry.observed_facts["hp_estimate"] == "very tough"

    def test_observed_facts_accumulate(self):
        log = DiscoveryLog()
        log.apply_event(make_event(
            DiscoveryEventType.COMBAT_OBSERVED,
            observed_facts=("ac_estimate=heavily armored",),
        ))
        log.apply_event(make_event(
            DiscoveryEventType.COMBAT_OBSERVED,
            observed_facts=("hp_estimate=very tough",),
        ))

        entry = log.get_entry("player_1", "wyvern_01")
        assert "ac_estimate" in entry.observed_facts
        assert "hp_estimate" in entry.observed_facts


# ---------------------------------------------------------------------------
# Serialization Tests
# ---------------------------------------------------------------------------

class TestSerialization:
    """Discovery log can be serialized and restored."""

    def test_knowledge_entry_round_trip(self):
        entry = KnowledgeEntry(
            player_id="p1",
            entity_id="e1",
            tier=KnowledgeTier.FOUGHT,
            observed_facts={"ac_estimate": "high"},
        )
        restored = KnowledgeEntry.from_dict(entry.to_dict())
        assert restored.player_id == entry.player_id
        assert restored.entity_id == entry.entity_id
        assert restored.tier == entry.tier
        assert restored.observed_facts == entry.observed_facts

    def test_discovery_event_round_trip(self):
        event = DiscoveryEvent(
            event_type=DiscoveryEventType.COMBAT_OBSERVED,
            player_id="p1",
            entity_id="e1",
            observed_facts=("ac_estimate=high",),
            metadata=(("source", "combat_turn_3"),),
        )
        restored = DiscoveryEvent.from_dict(event.to_dict())
        assert restored.event_type == event.event_type
        assert restored.player_id == event.player_id
        assert restored.entity_id == event.entity_id
        assert restored.observed_facts == event.observed_facts

    def test_discovery_log_round_trip(self):
        log = DiscoveryLog()
        log.apply_event(make_event(DiscoveryEventType.ENCOUNTER_SEEN))
        log.apply_event(make_event(
            DiscoveryEventType.COMBAT_OBSERVED,
            observed_facts=("ac_estimate=high",),
        ))

        data = log.to_dict()
        restored = DiscoveryLog.from_dict(data)

        assert restored.get_tier("player_1", "wyvern_01") == KnowledgeTier.FOUGHT
        entry = restored.get_entry("player_1", "wyvern_01")
        assert entry.observed_facts["ac_estimate"] == "high"

    def test_masked_view_to_dict(self):
        log = DiscoveryLog()
        log.apply_event(make_event(DiscoveryEventType.NPC_TOLD_YOU))
        view = log.get_entry_view("player_1", "wyvern_01", FULL_ENTITY_DATA)

        d = view.to_dict()
        assert d["tier"] == "HEARD_OF"
        assert "display_name" in d["fields"]


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------

class TestValidation:
    """Input validation for discovery events."""

    def test_empty_player_id_rejected(self):
        with pytest.raises(ValueError, match="player_id"):
            DiscoveryEvent(
                event_type=DiscoveryEventType.ENCOUNTER_SEEN,
                player_id="",
                entity_id="e1",
            )

    def test_empty_entity_id_rejected(self):
        with pytest.raises(ValueError, match="entity_id"):
            DiscoveryEvent(
                event_type=DiscoveryEventType.ENCOUNTER_SEEN,
                player_id="p1",
                entity_id="",
            )


# ---------------------------------------------------------------------------
# Event Count / Multi-Entity Tests
# ---------------------------------------------------------------------------

class TestMultiEntity:
    """Tests across multiple entities and players."""

    def test_get_all_entries(self):
        log = DiscoveryLog()
        log.apply_event(make_event(
            DiscoveryEventType.ENCOUNTER_SEEN, entity_id="alpha"
        ))
        log.apply_event(make_event(
            DiscoveryEventType.COMBAT_OBSERVED, entity_id="beta"
        ))
        log.apply_event(make_event(
            DiscoveryEventType.NPC_TOLD_YOU, entity_id="gamma"
        ))

        entries = log.get_all_entries("player_1")
        assert len(entries) == 3
        # Sorted by entity_id
        assert entries[0].entity_id == "alpha"
        assert entries[1].entity_id == "beta"
        assert entries[2].entity_id == "gamma"

    def test_event_count(self):
        log = DiscoveryLog()
        log.apply_event(make_event(DiscoveryEventType.ENCOUNTER_SEEN))
        log.apply_event(make_event(DiscoveryEventType.COMBAT_OBSERVED))
        assert log.event_count == 2

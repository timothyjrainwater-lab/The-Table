"""Tests for Lens-tier Discovery Log state machine.

Tests cover:
- New player has no knowledge (UNKNOWN for all creatures)
- Recording knowledge levels and querying them back
- Tier upgrades (lower → higher)
- Tier never downgrades (higher → lower attempt is no-op)
- Skip levels (UNKNOWN → FOUGHT)
- Field gating per tier (HEARD_OF, SEEN, FOUGHT, STUDIED)
- Multiple players have independent knowledge states
- Serialization round-trip preserves all state
- get_all_known returns all creatures for a player
- KnowledgeEvent processing triggers correct transitions
- KnowledgeEvent validation

WO-DISCOVERY-BACKEND-001: Discovery Log Backend
"""

import pytest

from aidm.schemas.knowledge_mask import (
    KnowledgeTier,
    REVEAL_SPEC,
)
from aidm.lens.discovery_log import (
    DiscoveryLog,
    KnowledgeEvent,
    KnowledgeSource,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_log() -> DiscoveryLog:
    return DiscoveryLog()


def make_event(
    player_id: str = "player_1",
    creature_type: str = "wyvern",
    source: KnowledgeSource = KnowledgeSource.ENCOUNTER,
    resulting_level: KnowledgeTier = KnowledgeTier.SEEN,
    timestamp: str = "2026-02-13T10:00:00Z",
) -> KnowledgeEvent:
    return KnowledgeEvent(
        player_id=player_id,
        creature_type=creature_type,
        source=source,
        resulting_level=resulting_level,
        timestamp=timestamp,
    )


# ---------------------------------------------------------------------------
# Tier Transition Tests
# ---------------------------------------------------------------------------

class TestTierTransitions:
    """Knowledge tier transitions follow monotonic advancement rules."""

    def test_new_player_has_no_knowledge(self):
        """New player returns UNKNOWN for all creatures."""
        log = make_log()
        assert log.get_knowledge("player_1", "wyvern") == KnowledgeTier.UNKNOWN
        assert log.get_knowledge("player_1", "goblin") == KnowledgeTier.UNKNOWN

    def test_record_heard_of(self):
        """Recording HEARD_OF → query returns HEARD_OF."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.HEARD_OF)
        assert log.get_knowledge("player_1", "wyvern") == KnowledgeTier.HEARD_OF

    def test_record_seen(self):
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.SEEN)
        assert log.get_knowledge("player_1", "wyvern") == KnowledgeTier.SEEN

    def test_record_fought(self):
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.FOUGHT)
        assert log.get_knowledge("player_1", "wyvern") == KnowledgeTier.FOUGHT

    def test_record_studied(self):
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.STUDIED)
        assert log.get_knowledge("player_1", "wyvern") == KnowledgeTier.STUDIED

    def test_upgrade_heard_of_to_fought(self):
        """Recording FOUGHT after HEARD_OF → level upgrades to FOUGHT."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.HEARD_OF)
        log.record_encounter("player_1", "wyvern", KnowledgeTier.FOUGHT)
        assert log.get_knowledge("player_1", "wyvern") == KnowledgeTier.FOUGHT

    def test_no_downgrade(self):
        """Recording HEARD_OF after FOUGHT → level stays at FOUGHT."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.FOUGHT)
        log.record_encounter("player_1", "wyvern", KnowledgeTier.HEARD_OF)
        assert log.get_knowledge("player_1", "wyvern") == KnowledgeTier.FOUGHT

    def test_skip_level_unknown_to_fought(self):
        """Skip level: UNKNOWN → FOUGHT is valid."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.FOUGHT)
        assert log.get_knowledge("player_1", "wyvern") == KnowledgeTier.FOUGHT

    def test_skip_level_unknown_to_studied(self):
        """Skip level: UNKNOWN → STUDIED is valid."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.STUDIED)
        assert log.get_knowledge("player_1", "wyvern") == KnowledgeTier.STUDIED

    def test_progressive_advancement(self):
        """Advance through all tiers in order."""
        log = make_log()
        for tier in [KnowledgeTier.HEARD_OF, KnowledgeTier.SEEN,
                     KnowledgeTier.FOUGHT, KnowledgeTier.STUDIED]:
            log.record_encounter("player_1", "wyvern", tier)
            assert log.get_knowledge("player_1", "wyvern") == tier

    def test_duplicate_record_is_idempotent(self):
        """Recording the same tier twice doesn't change state."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.SEEN)
        log.record_encounter("player_1", "wyvern", KnowledgeTier.SEEN)
        assert log.get_knowledge("player_1", "wyvern") == KnowledgeTier.SEEN


# ---------------------------------------------------------------------------
# Field Gating Tests
# ---------------------------------------------------------------------------

class TestFieldGating:
    """Visible fields match the REVEAL_SPEC for each tier."""

    def test_unknown_reveals_nothing(self):
        log = make_log()
        fields = log.get_visible_fields("player_1", "wyvern")
        assert fields == frozenset()

    def test_heard_of_shows_name_and_type(self):
        """HEARD_OF shows only name + type + size_category + rumor_text."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.HEARD_OF)
        fields = log.get_visible_fields("player_1", "wyvern")
        assert fields == REVEAL_SPEC[KnowledgeTier.HEARD_OF]
        assert "display_name" in fields
        assert "entity_type" in fields
        # Should NOT contain combat stats
        assert "ac" not in fields
        assert "hp_max" not in fields

    def test_seen_adds_appearance_fields(self):
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.SEEN)
        fields = log.get_visible_fields("player_1", "wyvern")
        assert fields == REVEAL_SPEC[KnowledgeTier.SEEN]
        assert "appearance" in fields
        assert "speed" in fields
        assert "senses" in fields
        # Still no exact combat stats
        assert "ac" not in fields

    def test_fought_adds_estimates(self):
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.FOUGHT)
        fields = log.get_visible_fields("player_1", "wyvern")
        assert fields == REVEAL_SPEC[KnowledgeTier.FOUGHT]
        assert "ac_estimate" in fields
        assert "hp_estimate" in fields
        assert "attack_pattern" in fields
        # Exact stats still hidden
        assert "ac" not in fields
        assert "hp_max" not in fields

    def test_studied_shows_full_stat_block(self):
        """STUDIED shows full stat block including exact values."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.STUDIED)
        fields = log.get_visible_fields("player_1", "wyvern")
        assert fields == REVEAL_SPEC[KnowledgeTier.STUDIED]
        assert "ac" in fields
        assert "hp_max" in fields
        assert "hit_dice" in fields
        assert "challenge_rating" in fields
        assert "lore_text" in fields
        assert "special_abilities" in fields
        assert "vulnerabilities" in fields

    def test_each_tier_is_superset_of_previous(self):
        """Higher tiers include all fields from lower tiers."""
        tiers = [KnowledgeTier.UNKNOWN, KnowledgeTier.HEARD_OF,
                 KnowledgeTier.SEEN, KnowledgeTier.FOUGHT, KnowledgeTier.STUDIED]
        log = make_log()
        for i in range(len(tiers) - 1):
            log_lower = make_log()
            log_lower.record_encounter("p", "c", tiers[i])
            log_higher = make_log()
            log_higher.record_encounter("p", "c", tiers[i + 1])
            lower_fields = log_lower.get_visible_fields("p", "c")
            higher_fields = log_higher.get_visible_fields("p", "c")
            assert lower_fields <= higher_fields, (
                f"{tiers[i+1].name} should include all fields from "
                f"{tiers[i].name}: missing {lower_fields - higher_fields}"
            )


# ---------------------------------------------------------------------------
# Independent State Tests
# ---------------------------------------------------------------------------

class TestIndependentState:
    """Multiple players and creatures have independent knowledge."""

    def test_independent_players(self):
        """Different players have independent knowledge states."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.STUDIED)
        log.record_encounter("player_2", "wyvern", KnowledgeTier.HEARD_OF)

        assert log.get_knowledge("player_1", "wyvern") == KnowledgeTier.STUDIED
        assert log.get_knowledge("player_2", "wyvern") == KnowledgeTier.HEARD_OF

    def test_independent_creatures(self):
        """Knowledge about different creatures is independent."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.STUDIED)
        log.record_encounter("player_1", "goblin", KnowledgeTier.HEARD_OF)

        assert log.get_knowledge("player_1", "wyvern") == KnowledgeTier.STUDIED
        assert log.get_knowledge("player_1", "goblin") == KnowledgeTier.HEARD_OF

    def test_player_2_unaffected_by_player_1(self):
        """Player 2 has UNKNOWN even when player 1 has STUDIED."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.STUDIED)
        assert log.get_knowledge("player_2", "wyvern") == KnowledgeTier.UNKNOWN


# ---------------------------------------------------------------------------
# get_all_known Tests
# ---------------------------------------------------------------------------

class TestGetAllKnown:
    """get_all_known returns all creatures a player knows about."""

    def test_empty_for_new_player(self):
        log = make_log()
        assert log.get_all_known("player_1") == {}

    def test_returns_all_known_creatures(self):
        """get_all_known returns all creatures for a player."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.SEEN)
        log.record_encounter("player_1", "goblin", KnowledgeTier.HEARD_OF)
        log.record_encounter("player_1", "dragon", KnowledgeTier.STUDIED)

        known = log.get_all_known("player_1")
        assert len(known) == 3
        assert known["wyvern"] == KnowledgeTier.SEEN
        assert known["goblin"] == KnowledgeTier.HEARD_OF
        assert known["dragon"] == KnowledgeTier.STUDIED

    def test_excludes_other_players(self):
        """get_all_known does not include other players' creatures."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.SEEN)
        log.record_encounter("player_2", "goblin", KnowledgeTier.FOUGHT)

        known_p1 = log.get_all_known("player_1")
        assert "goblin" not in known_p1

        known_p2 = log.get_all_known("player_2")
        assert "wyvern" not in known_p2

    def test_sorted_by_creature_type(self):
        """Returned dict keys are sorted."""
        log = make_log()
        log.record_encounter("player_1", "zombie", KnowledgeTier.SEEN)
        log.record_encounter("player_1", "alpha", KnowledgeTier.HEARD_OF)
        log.record_encounter("player_1", "minotaur", KnowledgeTier.FOUGHT)

        known = log.get_all_known("player_1")
        assert list(known.keys()) == ["alpha", "minotaur", "zombie"]


# ---------------------------------------------------------------------------
# KnowledgeEvent Tests
# ---------------------------------------------------------------------------

class TestKnowledgeEvent:
    """KnowledgeEvent processing and validation."""

    def test_process_event_updates_state(self):
        """Knowledge events correctly trigger level transitions."""
        log = make_log()
        event = make_event(resulting_level=KnowledgeTier.SEEN)
        tier = log.process_event(event)
        assert tier == KnowledgeTier.SEEN
        assert log.get_knowledge("player_1", "wyvern") == KnowledgeTier.SEEN

    def test_process_event_advances_tier(self):
        log = make_log()
        log.process_event(make_event(resulting_level=KnowledgeTier.HEARD_OF))
        tier = log.process_event(make_event(resulting_level=KnowledgeTier.FOUGHT))
        assert tier == KnowledgeTier.FOUGHT

    def test_process_event_no_downgrade(self):
        log = make_log()
        log.process_event(make_event(resulting_level=KnowledgeTier.FOUGHT))
        tier = log.process_event(make_event(resulting_level=KnowledgeTier.HEARD_OF))
        assert tier == KnowledgeTier.FOUGHT

    def test_process_event_appends_to_ledger(self):
        log = make_log()
        log.process_event(make_event(resulting_level=KnowledgeTier.SEEN))
        log.process_event(make_event(resulting_level=KnowledgeTier.FOUGHT))
        assert log.event_count == 2

    def test_event_sources(self):
        """Different source types are recorded correctly."""
        log = make_log()
        for source in KnowledgeSource:
            event = make_event(
                source=source,
                creature_type=f"creature_{source.name}",
                resulting_level=KnowledgeTier.HEARD_OF,
            )
            log.process_event(event)
        assert log.event_count == len(KnowledgeSource)

    def test_event_validation_empty_player_id(self):
        with pytest.raises(ValueError, match="player_id"):
            KnowledgeEvent(
                player_id="",
                creature_type="wyvern",
                source=KnowledgeSource.ENCOUNTER,
                resulting_level=KnowledgeTier.SEEN,
                timestamp="2026-02-13T10:00:00Z",
            )

    def test_event_validation_empty_creature_type(self):
        with pytest.raises(ValueError, match="creature_type"):
            KnowledgeEvent(
                player_id="player_1",
                creature_type="",
                source=KnowledgeSource.ENCOUNTER,
                resulting_level=KnowledgeTier.SEEN,
                timestamp="2026-02-13T10:00:00Z",
            )

    def test_event_validation_empty_timestamp(self):
        with pytest.raises(ValueError, match="timestamp"):
            KnowledgeEvent(
                player_id="player_1",
                creature_type="wyvern",
                source=KnowledgeSource.ENCOUNTER,
                resulting_level=KnowledgeTier.SEEN,
                timestamp="",
            )

    def test_event_is_frozen(self):
        """KnowledgeEvent is immutable."""
        event = make_event()
        with pytest.raises(AttributeError):
            event.player_id = "modified"


# ---------------------------------------------------------------------------
# Serialization Tests
# ---------------------------------------------------------------------------

class TestSerialization:
    """Discovery log can be serialized and restored."""

    def test_empty_log_round_trip(self):
        log = make_log()
        data = log.to_dict()
        restored = DiscoveryLog.from_dict(data)
        assert restored.get_knowledge("anyone", "anything") == KnowledgeTier.UNKNOWN

    def test_state_round_trip(self):
        """Serialization round-trip preserves all state."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.FOUGHT)
        log.record_encounter("player_1", "goblin", KnowledgeTier.HEARD_OF)
        log.record_encounter("player_2", "wyvern", KnowledgeTier.SEEN)

        data = log.to_dict()
        restored = DiscoveryLog.from_dict(data)

        assert restored.get_knowledge("player_1", "wyvern") == KnowledgeTier.FOUGHT
        assert restored.get_knowledge("player_1", "goblin") == KnowledgeTier.HEARD_OF
        assert restored.get_knowledge("player_2", "wyvern") == KnowledgeTier.SEEN

    def test_event_round_trip(self):
        """Events survive serialization round-trip."""
        log = make_log()
        log.process_event(make_event(
            resulting_level=KnowledgeTier.SEEN,
            timestamp="2026-02-13T10:00:00Z",
        ))
        log.process_event(make_event(
            resulting_level=KnowledgeTier.FOUGHT,
            timestamp="2026-02-13T11:00:00Z",
        ))

        data = log.to_dict()
        restored = DiscoveryLog.from_dict(data)

        assert restored.event_count == 2
        assert restored.get_knowledge("player_1", "wyvern") == KnowledgeTier.FOUGHT

    def test_knowledge_event_round_trip(self):
        """KnowledgeEvent to_dict/from_dict preserves all fields."""
        event = KnowledgeEvent(
            player_id="player_1",
            creature_type="wyvern",
            source=KnowledgeSource.SKILL_CHECK,
            resulting_level=KnowledgeTier.STUDIED,
            timestamp="2026-02-13T12:00:00Z",
        )
        restored = KnowledgeEvent.from_dict(event.to_dict())
        assert restored.player_id == event.player_id
        assert restored.creature_type == event.creature_type
        assert restored.source == event.source
        assert restored.resulting_level == event.resulting_level
        assert restored.timestamp == event.timestamp

    def test_get_all_known_after_round_trip(self):
        """get_all_known works correctly after restoration."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.SEEN)
        log.record_encounter("player_1", "goblin", KnowledgeTier.FOUGHT)

        restored = DiscoveryLog.from_dict(log.to_dict())
        known = restored.get_all_known("player_1")
        assert len(known) == 2
        assert known["wyvern"] == KnowledgeTier.SEEN
        assert known["goblin"] == KnowledgeTier.FOUGHT

    def test_visible_fields_after_round_trip(self):
        """Field gating works correctly after restoration."""
        log = make_log()
        log.record_encounter("player_1", "wyvern", KnowledgeTier.STUDIED)

        restored = DiscoveryLog.from_dict(log.to_dict())
        fields = restored.get_visible_fields("player_1", "wyvern")
        assert fields == REVEAL_SPEC[KnowledgeTier.STUDIED]

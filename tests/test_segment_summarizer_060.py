"""Tests for WO-060: Summarization Stability Protocol — Segment Summaries and Drift Detection

Validates:
- SessionSegmentSummary frozen dataclass (immutability, content hash)
- SegmentSummarizer template-based summarization from NarrativeBrief history
- Hit/miss counting, severity tracking, defeat tracking
- Drift detection: entity state consistency and fact monotonicity
- Rebuild-from-sources (deterministic)
- SegmentTracker: turn counting, auto-trigger, forced segments
- Edge cases: empty briefs, single brief, large segments

Evidence:
- RQ-LENS-SPARK-001: Context Orchestration Sprint (Deliverable 3)
- WO-060: Summarization Stability Protocol
"""

import pytest

from aidm.lens.segment_summarizer import (
    DriftResult,
    SEGMENT_SIZE,
    SegmentSummarizer,
    SegmentTracker,
    SessionSegmentSummary,
)


# ==============================================================================
# HELPERS
# ==============================================================================


class MockBrief:
    """Lightweight NarrativeBrief stand-in for testing."""
    def __init__(self, **kwargs):
        self.action_type = kwargs.get('action_type', 'attack_hit')
        self.actor_name = kwargs.get('actor_name', 'Kael')
        self.target_name = kwargs.get('target_name', 'Goblin Scout')
        self.outcome_summary = kwargs.get('outcome_summary', '')
        self.severity = kwargs.get('severity', 'minor')
        self.weapon_name = kwargs.get('weapon_name', None)
        self.damage_type = kwargs.get('damage_type', None)
        self.condition_applied = kwargs.get('condition_applied', None)
        self.target_defeated = kwargs.get('target_defeated', False)
        self.scene_description = kwargs.get('scene_description', None)
        self.previous_narrations = kwargs.get('previous_narrations', [])


def make_combat_briefs(count: int = 10, actor: str = "Kael",
                        target: str = "Goblin") -> list:
    """Generate a sequence of combat briefs for testing."""
    briefs = []
    for i in range(count):
        action = 'attack_hit' if i % 3 != 0 else 'attack_miss'
        severity = ['minor', 'moderate', 'severe'][i % 3]
        briefs.append(MockBrief(
            action_type=action,
            actor_name=actor,
            target_name=target,
            severity=severity,
        ))
    return briefs


# ==============================================================================
# SESSION SEGMENT SUMMARY
# ==============================================================================


class TestSessionSegmentSummary:
    """SessionSegmentSummary frozen dataclass behavior."""

    def test_summary_is_frozen(self):
        """SessionSegmentSummary is immutable."""
        summary = SessionSegmentSummary(
            segment_id="seg_001",
            turn_range=(1, 10),
            summary_text="Turns 1-10: combat occurred.",
            key_facts=("Goblin was defeated",),
            entity_states=(("Kael", "active"), ("Goblin", "defeated")),
            defeated_entities=frozenset({"Goblin"}),
            content_hash="abc123",
        )

        with pytest.raises(AttributeError):
            summary.summary_text = "Modified"

    def test_entity_state_dict(self):
        """entity_state_dict returns mutable dict."""
        summary = SessionSegmentSummary(
            segment_id="seg_001",
            turn_range=(1, 10),
            summary_text="Test",
            key_facts=(),
            entity_states=(("Kael", "active"), ("Goblin", "defeated")),
            defeated_entities=frozenset({"Goblin"}),
            content_hash="abc123",
        )

        states = summary.entity_state_dict
        assert states["Kael"] == "active"
        assert states["Goblin"] == "defeated"

    def test_schema_version(self):
        """Schema version defaults to 1.0.0."""
        summary = SessionSegmentSummary(
            segment_id="seg_001", turn_range=(1, 10),
            summary_text="Test", key_facts=(),
            entity_states=(), defeated_entities=frozenset(),
            content_hash="abc123",
        )
        assert summary.schema_version == "1.0.0"


# ==============================================================================
# SEGMENT SUMMARIZER
# ==============================================================================


class TestSegmentSummarizer:
    """SegmentSummarizer template-based summarization."""

    def test_basic_combat_summary(self):
        """Summarize 10 combat turns."""
        summarizer = SegmentSummarizer()
        briefs = make_combat_briefs(10)

        summary = summarizer.summarize(
            briefs=briefs, segment_id="seg_001", turn_range=(1, 10),
        )

        assert summary.segment_id == "seg_001"
        assert summary.turn_range == (1, 10)
        assert "Turns 1-10:" in summary.summary_text
        assert "Kael" in summary.summary_text
        assert "Goblin" in summary.summary_text
        assert "hit" in summary.summary_text.lower()
        assert "miss" in summary.summary_text.lower()

    def test_hit_miss_counting(self):
        """Correct hit and miss counts in summary."""
        summarizer = SegmentSummarizer()
        briefs = [
            MockBrief(action_type='attack_hit'),
            MockBrief(action_type='attack_hit'),
            MockBrief(action_type='attack_miss'),
            MockBrief(action_type='critical'),
            MockBrief(action_type='concealment_miss'),
        ]

        summary = summarizer.summarize(
            briefs=briefs, segment_id="seg_001", turn_range=(1, 5),
        )

        # 3 hits (2 attack_hit + 1 critical), 2 misses
        assert "3 hits" in summary.summary_text
        assert "2 misses" in summary.summary_text

    def test_defeat_tracking(self):
        """Defeated entities tracked in summary."""
        summarizer = SegmentSummarizer()
        briefs = [
            MockBrief(action_type='attack_hit', target_name='Goblin A'),
            MockBrief(action_type='attack_hit', target_name='Goblin B',
                      target_defeated=True, severity='lethal'),
        ]

        summary = summarizer.summarize(
            briefs=briefs, segment_id="seg_001", turn_range=(1, 2),
        )

        assert "Goblin B" in summary.defeated_entities
        assert "Goblin A" not in summary.defeated_entities
        assert "Goblin B was defeated" in summary.key_facts
        assert "Defeated: Goblin B" in summary.summary_text

    def test_max_severity_tracked(self):
        """Max severity from all briefs is reported."""
        summarizer = SegmentSummarizer()
        briefs = [
            MockBrief(severity='minor'),
            MockBrief(severity='devastating'),
            MockBrief(severity='moderate'),
        ]

        summary = summarizer.summarize(
            briefs=briefs, segment_id="seg_001", turn_range=(1, 3),
        )

        assert "devastating" in summary.summary_text.lower()

    def test_condition_tracking(self):
        """Conditions tracked in key facts."""
        summarizer = SegmentSummarizer()
        briefs = [
            MockBrief(
                action_type='trip_success',
                target_name='Ogre',
                condition_applied='prone',
            ),
        ]

        summary = summarizer.summarize(
            briefs=briefs, segment_id="seg_001", turn_range=(1, 1),
        )

        assert "Ogre became prone" in summary.key_facts

    def test_scene_description_included(self):
        """Last scene description included in summary."""
        summarizer = SegmentSummarizer()
        briefs = [
            MockBrief(scene_description='a dark dungeon corridor'),
            MockBrief(scene_description='a vast cavern'),
        ]

        summary = summarizer.summarize(
            briefs=briefs, segment_id="seg_001", turn_range=(1, 2),
        )

        assert "cavern" in summary.summary_text.lower()

    def test_empty_briefs(self):
        """Empty brief list produces minimal summary."""
        summarizer = SegmentSummarizer()

        summary = summarizer.summarize(
            briefs=[], segment_id="seg_001", turn_range=(1, 10),
        )

        assert "No significant events" in summary.summary_text

    def test_content_hash_deterministic(self):
        """Same inputs produce same content hash."""
        summarizer = SegmentSummarizer()
        briefs = make_combat_briefs(5)

        summary_a = summarizer.summarize(
            briefs=briefs, segment_id="seg_001", turn_range=(1, 5),
        )
        summary_b = summarizer.summarize(
            briefs=briefs, segment_id="seg_001", turn_range=(1, 5),
        )

        assert summary_a.content_hash == summary_b.content_hash

    def test_different_inputs_different_hash(self):
        """Different inputs produce different content hash."""
        summarizer = SegmentSummarizer()
        briefs_a = make_combat_briefs(5, actor="Kael")
        briefs_b = make_combat_briefs(5, actor="Wizard")

        summary_a = summarizer.summarize(
            briefs=briefs_a, segment_id="seg_001", turn_range=(1, 5),
        )
        summary_b = summarizer.summarize(
            briefs=briefs_b, segment_id="seg_001", turn_range=(1, 5),
        )

        assert summary_a.content_hash != summary_b.content_hash

    def test_entity_states_tracked(self):
        """Entity states reflect end-of-segment status."""
        summarizer = SegmentSummarizer()
        briefs = [
            MockBrief(actor_name='Kael', target_name='Goblin',
                      target_defeated=True, severity='lethal'),
            MockBrief(actor_name='Kael', target_name='Orc'),
        ]

        summary = summarizer.summarize(
            briefs=briefs, segment_id="seg_001", turn_range=(1, 2),
        )

        states = summary.entity_state_dict
        assert states["Goblin"] == "defeated"
        assert states["Kael"] == "active"

    def test_single_brief_summary(self):
        """Single brief produces valid summary."""
        summarizer = SegmentSummarizer()
        briefs = [MockBrief(action_type='attack_hit', severity='moderate')]

        summary = summarizer.summarize(
            briefs=briefs, segment_id="seg_001", turn_range=(5, 5),
        )

        assert summary.turn_range == (5, 5)
        assert summary.segment_id == "seg_001"
        assert len(summary.summary_text) > 0

    def test_multiple_defeated_sorted(self):
        """Multiple defeated entities sorted alphabetically."""
        summarizer = SegmentSummarizer()
        briefs = [
            MockBrief(target_name='Zombie', target_defeated=True),
            MockBrief(target_name='Goblin', target_defeated=True),
            MockBrief(target_name='Orc', target_defeated=True),
        ]

        summary = summarizer.summarize(
            briefs=briefs, segment_id="seg_001", turn_range=(1, 3),
        )

        assert "Defeated: Goblin, Orc, Zombie" in summary.summary_text

    def test_deduplicated_key_facts(self):
        """Duplicate key facts are removed."""
        summarizer = SegmentSummarizer()
        briefs = [
            MockBrief(target_name='Goblin', condition_applied='prone'),
            MockBrief(target_name='Goblin', condition_applied='prone'),
        ]

        summary = summarizer.summarize(
            briefs=briefs, segment_id="seg_001", turn_range=(1, 2),
        )

        # Should have exactly one "Goblin became prone"
        assert summary.key_facts.count("Goblin became prone") == 1


# ==============================================================================
# DRIFT DETECTION
# ==============================================================================


class TestDriftDetection:
    """SegmentSummarizer.detect_drift() checks."""

    def test_no_drift_when_consistent(self):
        """No drift between consistent segments."""
        summarizer = SegmentSummarizer()
        earlier = SessionSegmentSummary(
            segment_id="seg_001", turn_range=(1, 10),
            summary_text="Combat.", key_facts=(),
            entity_states=(("Kael", "active"), ("Goblin", "defeated")),
            defeated_entities=frozenset({"Goblin"}),
            content_hash="abc",
        )
        later = SessionSegmentSummary(
            segment_id="seg_002", turn_range=(11, 20),
            summary_text="More combat.", key_facts=(),
            entity_states=(("Kael", "active"),),
            defeated_entities=frozenset({"Goblin"}),
            content_hash="def",
        )

        result = summarizer.detect_drift(earlier, later)
        assert not result.has_drift

    def test_drift_defeated_entity_active(self):
        """Drift: defeated entity appears active in later segment."""
        summarizer = SegmentSummarizer()
        earlier = SessionSegmentSummary(
            segment_id="seg_001", turn_range=(1, 10),
            summary_text="Combat.", key_facts=(),
            entity_states=(("Goblin", "defeated"),),
            defeated_entities=frozenset({"Goblin"}),
            content_hash="abc",
        )
        later = SessionSegmentSummary(
            segment_id="seg_002", turn_range=(11, 20),
            summary_text="More combat.", key_facts=(),
            entity_states=(("Goblin", "active"),),
            defeated_entities=frozenset(),
            content_hash="def",
        )

        result = summarizer.detect_drift(earlier, later)
        assert result.has_drift
        assert "Goblin" in result.drifted_entities
        assert len(result.details) > 0

    def test_drift_defeat_not_carried_forward(self):
        """Drift: defeat fact not monotonically carried forward."""
        summarizer = SegmentSummarizer()
        earlier = SessionSegmentSummary(
            segment_id="seg_001", turn_range=(1, 10),
            summary_text="Combat.", key_facts=(),
            entity_states=(("Goblin", "defeated"),),
            defeated_entities=frozenset({"Goblin"}),
            content_hash="abc",
        )
        later = SessionSegmentSummary(
            segment_id="seg_002", turn_range=(11, 20),
            summary_text="More combat.", key_facts=(),
            entity_states=(("Goblin", "prone"),),  # Goblin appears but not defeated
            defeated_entities=frozenset(),
            content_hash="def",
        )

        result = summarizer.detect_drift(earlier, later)
        assert result.has_drift
        assert "Goblin" in result.drifted_entities

    def test_no_drift_entity_absent_from_later(self):
        """No drift if defeated entity simply doesn't appear in later segment."""
        summarizer = SegmentSummarizer()
        earlier = SessionSegmentSummary(
            segment_id="seg_001", turn_range=(1, 10),
            summary_text="Combat.", key_facts=(),
            entity_states=(("Goblin", "defeated"),),
            defeated_entities=frozenset({"Goblin"}),
            content_hash="abc",
        )
        later = SessionSegmentSummary(
            segment_id="seg_002", turn_range=(11, 20),
            summary_text="Exploration.", key_facts=(),
            entity_states=(("Kael", "active"),),  # Goblin not mentioned at all
            defeated_entities=frozenset(),
            content_hash="def",
        )

        result = summarizer.detect_drift(earlier, later)
        assert not result.has_drift

    def test_drift_result_frozen(self):
        """DriftResult is immutable."""
        result = DriftResult(
            has_drift=False, drifted_entities=(), details=(),
        )
        with pytest.raises(AttributeError):
            result.has_drift = True


# ==============================================================================
# REBUILD FROM SOURCES
# ==============================================================================


class TestRebuildFromSources:
    """rebuild_from_sources() deterministic rebuild."""

    def test_rebuild_matches_original(self):
        """Rebuild produces identical summary to original."""
        summarizer = SegmentSummarizer()
        briefs = make_combat_briefs(10)

        original = summarizer.summarize(
            briefs=briefs, segment_id="seg_001", turn_range=(1, 10),
        )
        rebuilt = summarizer.rebuild_from_sources(
            briefs=briefs, segment_id="seg_001", turn_range=(1, 10),
        )

        assert original.summary_text == rebuilt.summary_text
        assert original.content_hash == rebuilt.content_hash
        assert original.key_facts == rebuilt.key_facts
        assert original.entity_states == rebuilt.entity_states


# ==============================================================================
# SEGMENT TRACKER
# ==============================================================================


class TestSegmentTracker:
    """SegmentTracker turn counting and auto-trigger."""

    def test_auto_trigger_at_segment_size(self):
        """Summary auto-generated at SEGMENT_SIZE turns."""
        tracker = SegmentTracker()
        result = None

        for i in range(1, SEGMENT_SIZE + 1):
            brief = MockBrief(action_type='attack_hit')
            result = tracker.record_turn(brief, turn_number=i)

        assert result is not None
        assert isinstance(result, SessionSegmentSummary)
        assert result.turn_range == (1, SEGMENT_SIZE)

    def test_no_trigger_before_segment_size(self):
        """No summary generated before SEGMENT_SIZE turns."""
        tracker = SegmentTracker()

        for i in range(1, SEGMENT_SIZE):
            brief = MockBrief(action_type='attack_hit')
            result = tracker.record_turn(brief, turn_number=i)
            assert result is None

    def test_multiple_segments(self):
        """Multiple segment summaries generated over 30 turns."""
        tracker = SegmentTracker()
        summaries = []

        for i in range(1, 31):
            brief = MockBrief(action_type='attack_hit')
            result = tracker.record_turn(brief, turn_number=i)
            if result:
                summaries.append(result)

        assert len(summaries) == 3
        assert summaries[0].turn_range == (1, 10)
        assert summaries[1].turn_range == (11, 20)
        assert summaries[2].turn_range == (21, 30)

    def test_force_segment(self):
        """Forced segment summary at arbitrary turn."""
        tracker = SegmentTracker()

        for i in range(1, 6):
            tracker.record_turn(MockBrief(), turn_number=i)

        result = tracker.force_segment(turn_number=5, reason="scene_transition")

        assert result is not None
        assert result.turn_range == (1, 5)

    def test_force_segment_empty(self):
        """Force segment with no briefs returns None."""
        tracker = SegmentTracker()
        result = tracker.force_segment(turn_number=1)
        assert result is None

    def test_get_summaries_newest_first(self):
        """get_summaries() returns newest-first order."""
        tracker = SegmentTracker()

        for i in range(1, 21):
            tracker.record_turn(MockBrief(), turn_number=i)

        summaries = tracker.get_summaries()
        assert len(summaries) == 2
        # Newest first
        assert summaries[0].turn_range == (11, 20)
        assert summaries[1].turn_range == (1, 10)

    def test_defeated_entity_tracking(self):
        """Cumulative defeated entity tracking across segments."""
        tracker = SegmentTracker()

        # Segment 1: Goblin defeated
        for i in range(1, 11):
            brief = MockBrief(
                target_name='Goblin' if i == 5 else 'Orc',
                target_defeated=(i == 5),
            )
            tracker.record_turn(brief, turn_number=i)

        # Segment 2: Orc defeated
        for i in range(11, 21):
            brief = MockBrief(
                target_name='Orc',
                target_defeated=(i == 15),
            )
            tracker.record_turn(brief, turn_number=i)

        all_defeated = tracker.get_all_defeated()
        assert "Goblin" in all_defeated
        assert "Orc" in all_defeated

    def test_drift_check(self):
        """check_drift() detects cross-segment drift."""
        tracker = SegmentTracker()

        # Segment 1: Goblin defeated
        for i in range(1, 11):
            brief = MockBrief(
                target_name='Goblin',
                target_defeated=(i == 5),
                severity='lethal' if i == 5 else 'minor',
            )
            tracker.record_turn(brief, turn_number=i)

        # Segment 2: Goblin appears active (drift!)
        for i in range(11, 21):
            brief = MockBrief(
                actor_name='Goblin',  # Goblin acting — but was defeated
                target_name='Kael',
            )
            tracker.record_turn(brief, turn_number=i)

        drift = tracker.check_drift()
        assert drift is not None
        assert drift.has_drift
        assert "Goblin" in drift.drifted_entities

    def test_no_drift_with_single_segment(self):
        """check_drift() returns None with only one segment."""
        tracker = SegmentTracker()

        for i in range(1, 11):
            tracker.record_turn(MockBrief(), turn_number=i)

        drift = tracker.check_drift()
        assert drift is None

    def test_segment_counter_increments(self):
        """Segment IDs increment correctly."""
        tracker = SegmentTracker()

        for i in range(1, 31):
            tracker.record_turn(MockBrief(), turn_number=i)

        summaries = tracker.get_summaries()  # newest first
        assert summaries[0].segment_id == "seg_003"
        assert summaries[1].segment_id == "seg_002"
        assert summaries[2].segment_id == "seg_001"

    def test_segment_size_constant(self):
        """SEGMENT_SIZE is 10."""
        assert SEGMENT_SIZE == 10

    def test_next_segment_starts_after_previous(self):
        """After a segment closes, next segment starts at end_turn + 1."""
        tracker = SegmentTracker()

        # First segment: turns 1-10
        for i in range(1, 11):
            tracker.record_turn(MockBrief(), turn_number=i)

        # Force next segment at turn 15
        for i in range(11, 16):
            tracker.record_turn(MockBrief(), turn_number=i)

        result = tracker.force_segment(turn_number=15, reason="test")

        assert result is not None
        assert result.turn_range == (11, 15)

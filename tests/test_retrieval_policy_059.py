"""Tests for WO-059: Memory Retrieval Policy — RetrievedItem Provenance and Salience Ranking

Validates:
- RetrievedItem provenance tracking (source, turn_number, relevance_score)
- Salience ranking function (recency * 0.5 + actor_match * 0.3 + severity * 0.2)
- Hard caps: 3 narrations, 5 session summaries
- Drop order: summaries first (oldest), narrations (oldest), scene
- Budget enforcement with dropped=True and drop_reason
- Backward-compatible assemble() API unchanged

Evidence:
- RQ-LENS-SPARK-001: Context Orchestration Sprint (Deliverable 2)
- WO-059: Memory Retrieval Policy
- WO-032: ContextAssembler (backward compatibility)
"""

import pytest

from aidm.lens.context_assembler import (
    ContextAssembler,
    RetrievedItem,
    compute_relevance_score,
    MAX_RECENT_NARRATIONS,
    MAX_SESSION_SUMMARIES,
)
from aidm.lens.narrative_brief import NarrativeBrief


# ==============================================================================
# HELPERS
# ==============================================================================


class MockNarration:
    """Lightweight narration record for retrieval testing."""
    def __init__(self, **kwargs):
        self.text = kwargs.get('text', 'A blade strikes true.')
        self.actor_name = kwargs.get('actor_name', 'Kael')
        self.target_name = kwargs.get('target_name', 'Goblin')
        self.severity = kwargs.get('severity', 'minor')
        self.turn_number = kwargs.get('turn_number', 0)


class MockSummary:
    """Lightweight SessionSegmentSummary for retrieval testing."""
    def __init__(self, **kwargs):
        self.summary_text = kwargs.get('summary_text', 'Turns 1-10: combat occurred.')
        self.turn_range = kwargs.get('turn_range', (1, 10))


# ==============================================================================
# RELEVANCE SCORE TESTS
# ==============================================================================


class TestRelevanceScore:
    """compute_relevance_score() deterministic ranking function."""

    def test_most_recent_highest_recency(self):
        """Most recent item (rank 0) gets recency_weight=1.0."""
        score = compute_relevance_score(
            recency_rank=0, total_items=5,
            actor_match=False, severity='minor',
        )
        # 1.0 * 0.5 + 0.0 * 0.3 + 0.2 * 0.2 = 0.5 + 0.04 = 0.54
        assert abs(score - 0.54) < 0.01

    def test_oldest_lowest_recency(self):
        """Oldest item gets recency_weight=0.0."""
        score = compute_relevance_score(
            recency_rank=4, total_items=5,
            actor_match=False, severity='minor',
        )
        # 0.0 * 0.5 + 0.0 * 0.3 + 0.2 * 0.2 = 0.04
        assert abs(score - 0.04) < 0.01

    def test_actor_match_boost(self):
        """Actor match adds 0.3 to score."""
        without = compute_relevance_score(
            recency_rank=0, total_items=1,
            actor_match=False, severity='minor',
        )
        with_match = compute_relevance_score(
            recency_rank=0, total_items=1,
            actor_match=True, severity='minor',
        )
        assert abs(with_match - without - 0.3) < 0.01

    def test_severity_weight_lethal(self):
        """Lethal severity gets severity_weight=1.0."""
        score = compute_relevance_score(
            recency_rank=0, total_items=1,
            actor_match=False, severity='lethal',
        )
        # 1.0 * 0.5 + 0.0 * 0.3 + 1.0 * 0.2 = 0.7
        assert abs(score - 0.7) < 0.01

    def test_severity_weight_minor(self):
        """Minor severity gets severity_weight=0.2."""
        score = compute_relevance_score(
            recency_rank=0, total_items=1,
            actor_match=False, severity='minor',
        )
        # 1.0 * 0.5 + 0.0 * 0.3 + 0.2 * 0.2 = 0.54
        assert abs(score - 0.54) < 0.01

    def test_maximum_score(self):
        """Maximum score: most recent + actor match + lethal."""
        score = compute_relevance_score(
            recency_rank=0, total_items=1,
            actor_match=True, severity='lethal',
        )
        # 1.0 * 0.5 + 1.0 * 0.3 + 1.0 * 0.2 = 1.0
        assert abs(score - 1.0) < 0.01

    def test_deterministic(self):
        """Same inputs produce same score (determinism contract)."""
        kwargs = dict(recency_rank=2, total_items=5, actor_match=True, severity='severe')
        score_a = compute_relevance_score(**kwargs)
        score_b = compute_relevance_score(**kwargs)
        assert score_a == score_b

    def test_single_item_max_recency(self):
        """Single item always gets recency_weight=1.0."""
        score = compute_relevance_score(
            recency_rank=0, total_items=1,
            actor_match=False, severity='minor',
        )
        assert score > 0.5  # Must have recency boost

    def test_unknown_severity_defaults_to_minor(self):
        """Unknown severity treated as minor (0.2)."""
        score = compute_relevance_score(
            recency_rank=0, total_items=1,
            actor_match=False, severity='unknown_severity',
        )
        expected = compute_relevance_score(
            recency_rank=0, total_items=1,
            actor_match=False, severity='minor',
        )
        assert score == expected


# ==============================================================================
# RETRIEVED ITEM TESTS
# ==============================================================================


class TestRetrievedItem:
    """RetrievedItem frozen dataclass behavior."""

    def test_item_is_frozen(self):
        """RetrievedItem is immutable."""
        item = RetrievedItem(
            text="Test", source="narration",
            turn_number=1, relevance_score=0.5,
        )
        with pytest.raises(AttributeError):
            item.text = "Modified"

    def test_default_not_dropped(self):
        """Items are not dropped by default."""
        item = RetrievedItem(
            text="Test", source="narration",
            turn_number=1, relevance_score=0.5,
        )
        assert not item.dropped
        assert item.drop_reason == ""

    def test_dropped_item(self):
        """Dropped item carries reason."""
        item = RetrievedItem(
            text="Test", source="narration",
            turn_number=1, relevance_score=0.5,
            dropped=True, drop_reason="budget_exceeded",
        )
        assert item.dropped
        assert item.drop_reason == "budget_exceeded"

    def test_source_types(self):
        """All four source types work."""
        for source in ("brief", "scene", "narration", "session_summary"):
            item = RetrievedItem(
                text="Test", source=source,
                turn_number=0, relevance_score=0.5,
            )
            assert item.source == source


# ==============================================================================
# RETRIEVE() METHOD TESTS
# ==============================================================================


class TestRetrieve:
    """ContextAssembler.retrieve() with provenance tracking."""

    def test_brief_always_included(self):
        """Current brief is always the first retrieved item."""
        assembler = ContextAssembler(token_budget=800)
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Kael",
            outcome_summary="Kael strikes the goblin.",
        )

        items = assembler.retrieve(brief=brief, current_turn=5)

        assert len(items) >= 1
        assert items[0].source == "brief"
        assert items[0].relevance_score == 1.0
        assert items[0].turn_number == 5
        assert not items[0].dropped

    def test_scene_included_when_present(self):
        """Scene description is included as second item."""
        assembler = ContextAssembler(token_budget=800)
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Kael",
            outcome_summary="Kael strikes.",
            scene_description="A dark dungeon corridor",
        )

        items = assembler.retrieve(brief=brief)
        scene_items = [i for i in items if i.source == "scene"]

        assert len(scene_items) == 1
        assert "dungeon" in scene_items[0].text.lower()
        assert not scene_items[0].dropped

    def test_narrations_ranked_by_relevance(self):
        """Narrations are sorted by relevance score, not insertion order."""
        assembler = ContextAssembler(token_budget=800)
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Kael",
            target_name="Goblin",
            outcome_summary="Kael strikes.",
        )

        # Narrations ordered oldest-to-newest (chronological order)
        narrations = [
            MockNarration(text="Old event.", actor_name="Wizard", severity='minor', turn_number=1),
            MockNarration(text="Mid event.", actor_name="Cleric", severity='moderate', turn_number=2),
            MockNarration(text="Recent match.", actor_name="Kael", severity='devastating', turn_number=3),
        ]

        items = assembler.retrieve(
            brief=brief, previous_narrations=narrations, current_turn=4,
        )
        narr_items = [i for i in items if i.source == "narration" and not i.dropped]

        # The actor-matched, highest-severity narration should rank highest
        assert narr_items[0].text == "Recent match."

    def test_narration_hard_cap(self):
        """Only MAX_RECENT_NARRATIONS narrations are kept, rest dropped."""
        assembler = ContextAssembler(token_budget=2000)  # Large budget
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Kael",
            outcome_summary="Kael strikes.",
        )

        # 6 narrations, but cap is 3
        narrations = [
            MockNarration(text=f"Event {i}.", turn_number=i) for i in range(6)
        ]

        items = assembler.retrieve(brief=brief, previous_narrations=narrations)

        narr_kept = [i for i in items if i.source == "narration" and not i.dropped]
        narr_dropped = [i for i in items if i.source == "narration" and i.dropped]

        assert len(narr_kept) == MAX_RECENT_NARRATIONS
        assert len(narr_dropped) == 3
        for dropped in narr_dropped:
            assert dropped.drop_reason == "cap_exceeded"

    def test_summary_hard_cap(self):
        """Only MAX_SESSION_SUMMARIES summaries are kept."""
        assembler = ContextAssembler(token_budget=5000)
        brief = NarrativeBrief(
            action_type="attack_hit", actor_name="Kael",
            outcome_summary="Kael strikes.",
        )

        # 7 summaries, but cap is 5
        summaries = [
            MockSummary(summary_text=f"Summary {i}.", turn_range=(i*10+1, (i+1)*10))
            for i in range(7)
        ]

        items = assembler.retrieve(
            brief=brief, segment_summaries=summaries,
        )

        sum_kept = [i for i in items if i.source == "session_summary" and not i.dropped]
        sum_dropped = [i for i in items if i.source == "session_summary" and i.dropped]

        assert len(sum_kept) == MAX_SESSION_SUMMARIES
        assert len(sum_dropped) == 2
        for dropped in sum_dropped:
            assert dropped.drop_reason == "cap_exceeded"

    def test_budget_drops_narrations(self):
        """Token budget enforcement drops narrations when exceeded."""
        assembler = ContextAssembler(token_budget=15)  # Only enough for brief
        brief = NarrativeBrief(
            action_type="attack_hit", actor_name="Kael",
            outcome_summary="Kael strikes the goblin warrior with devastating force.",
        )

        narrations = [
            MockNarration(
                text="A long narration with many words that should definitely "
                     "exceed the remaining budget after the brief is included.",
                turn_number=1,
            ),
        ]

        items = assembler.retrieve(brief=brief, previous_narrations=narrations)

        narr_items = [i for i in items if i.source == "narration"]
        assert len(narr_items) == 1
        assert narr_items[0].dropped
        assert narr_items[0].drop_reason == "budget_exceeded"

    def test_budget_drops_summaries(self):
        """Summaries dropped when budget exceeded."""
        assembler = ContextAssembler(token_budget=15)  # Only enough for brief
        brief = NarrativeBrief(
            action_type="attack_hit", actor_name="Kael",
            outcome_summary="Kael strikes the goblin warrior with devastating force.",
        )

        summaries = [
            MockSummary(
                summary_text="A very long summary that takes many many tokens "
                             "to represent and should exceed the remaining budget.",
            ),
        ]

        items = assembler.retrieve(brief=brief, segment_summaries=summaries)

        sum_items = [i for i in items if i.source == "session_summary"]
        assert len(sum_items) == 1
        assert sum_items[0].dropped
        assert sum_items[0].drop_reason == "budget_exceeded"

    def test_string_narrations_supported(self):
        """Plain string narrations work (backward compat)."""
        assembler = ContextAssembler(token_budget=800)
        brief = NarrativeBrief(
            action_type="attack_hit", actor_name="Kael",
            outcome_summary="Kael strikes.",
        )

        items = assembler.retrieve(
            brief=brief,
            previous_narrations=["The blade flashes.", "A grunt of pain."],
        )

        narr_items = [i for i in items if i.source == "narration" and not i.dropped]
        assert len(narr_items) == 2

    def test_dict_narrations_supported(self):
        """Dict narrations work with field extraction."""
        assembler = ContextAssembler(token_budget=800)
        brief = NarrativeBrief(
            action_type="attack_hit", actor_name="Kael",
            outcome_summary="Kael strikes.",
        )

        items = assembler.retrieve(
            brief=brief,
            previous_narrations=[{
                'text': 'The blade flashes.',
                'actor_name': 'Kael',
                'severity': 'devastating',
                'turn_number': 3,
            }],
        )

        narr_items = [i for i in items if i.source == "narration"]
        assert len(narr_items) == 1
        assert narr_items[0].text == "The blade flashes."

    def test_empty_retrieval(self):
        """Retrieval with only brief returns one item."""
        assembler = ContextAssembler(token_budget=800)
        brief = NarrativeBrief(
            action_type="attack_hit", actor_name="Kael",
            outcome_summary="Kael strikes.",
        )

        items = assembler.retrieve(brief=brief)
        assert len(items) == 1
        assert items[0].source == "brief"

    def test_provenance_metadata_complete(self):
        """Every retrieved item has complete provenance metadata."""
        assembler = ContextAssembler(token_budget=800)
        brief = NarrativeBrief(
            action_type="attack_hit", actor_name="Kael",
            outcome_summary="Kael strikes.",
            scene_description="A dungeon corridor",
            previous_narrations=["The battle rages."],
        )

        items = assembler.retrieve(
            brief=brief,
            previous_narrations=[MockNarration(text="Event.")],
            segment_summaries=[MockSummary()],
            current_turn=42,
        )

        for item in items:
            assert isinstance(item.text, str)
            assert item.source in ("brief", "scene", "narration", "session_summary")
            assert isinstance(item.turn_number, int)
            assert 0.0 <= item.relevance_score <= 1.0
            assert isinstance(item.dropped, bool)
            assert isinstance(item.drop_reason, str)


# ==============================================================================
# BACKWARD COMPATIBILITY TESTS
# ==============================================================================


class TestAssembleBackwardCompat:
    """assemble() backward compatibility with WO-032 API."""

    def test_basic_assembly(self):
        """assemble() returns context string with brief."""
        assembler = ContextAssembler(token_budget=1000)
        brief = NarrativeBrief(
            action_type="attack_hit",
            actor_name="Aldric",
            target_name="Goblin",
            outcome_summary="Aldric hits Goblin with longsword",
            severity="moderate",
            weapon_name="longsword",
            damage_type="slashing",
        )

        context = assembler.assemble(brief=brief)

        assert "Current Action: Aldric hits Goblin with longsword" in context
        assert "Weapon: longsword" in context
        assert "Severity: moderate" in context

    def test_assembly_with_scene(self):
        """assemble() includes scene description."""
        assembler = ContextAssembler(token_budget=1000)
        brief = NarrativeBrief(
            action_type="attack_hit", actor_name="Kael",
            outcome_summary="Kael strikes.",
            scene_description="A dark dungeon corridor",
        )

        context = assembler.assemble(brief=brief)
        assert "Location: A dark dungeon corridor" in context

    def test_assembly_with_narrations(self):
        """assemble() includes previous narrations."""
        assembler = ContextAssembler(token_budget=1000)
        brief = NarrativeBrief(
            action_type="attack_hit", actor_name="Kael",
            outcome_summary="Kael strikes.",
            previous_narrations=["The troll roars!", "Steel clashes."],
        )

        context = assembler.assemble(brief=brief)
        assert "Recent Events:" in context
        assert "The troll roars!" in context

    def test_budget_enforcement(self):
        """assemble() respects token budget."""
        assembler = ContextAssembler(token_budget=200)
        brief = NarrativeBrief(
            action_type="attack_hit", actor_name="Fighter",
            target_name="Dragon", outcome_summary="Fighter strikes Dragon",
            severity="devastating",
            scene_description="A volcanic lair filled with smoke",
            previous_narrations=["The dragon breathes fire!"] * 10,
        )

        context = assembler.assemble(brief=brief)
        tokens = assembler._estimate_tokens(context)
        assert tokens <= assembler.token_budget

    def test_target_defeated_flag(self):
        """assemble() includes defeat flag."""
        assembler = ContextAssembler(token_budget=1000)
        brief = NarrativeBrief(
            action_type="attack_hit", actor_name="Fighter",
            target_name="Goblin", outcome_summary="Fighter defeats Goblin",
            target_defeated=True, severity="lethal",
        )

        context = assembler.assemble(brief=brief)
        assert "Target Defeated: Yes" in context


# ==============================================================================
# HARD CAP CONSTANTS
# ==============================================================================


class TestHardCaps:
    """Hard cap values from RQ-LENS-SPARK-001 Deliverable 2."""

    def test_narration_cap_is_three(self):
        """MAX_RECENT_NARRATIONS is 3."""
        assert MAX_RECENT_NARRATIONS == 3

    def test_summary_cap_is_five(self):
        """MAX_SESSION_SUMMARIES is 5."""
        assert MAX_SESSION_SUMMARIES == 5

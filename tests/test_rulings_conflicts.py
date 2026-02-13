"""Tests for rulings and conflicts record schemas."""

import pytest
import json
from aidm.schemas.rulings_conflicts import (
    RulesQuestion,
    RulingConflict,
    RulingDecision
)


def test_rules_question_basic():
    """RulesQuestion should store basic question data."""
    question = RulesQuestion(
        question_text="Does grapple provoke attack of opportunity?",
        context_refs=["goblin_1", "pc_fighter"],
        citations=[{"source_id": "681f92bc94ff", "page": 156}]
    )

    assert question.question_text == "Does grapple provoke attack of opportunity?"
    assert len(question.context_refs) == 2
    assert len(question.citations) == 1


def test_rules_question_empty_text_rejected():
    """RulesQuestion should reject empty question_text."""
    with pytest.raises(ValueError, match="question_text cannot be empty"):
        RulesQuestion(question_text="")


def test_rules_question_serialization():
    """RulesQuestion should serialize deterministically."""
    question = RulesQuestion(
        question_text="How does invisibility interact with AOO?",
        context_refs=["spell_invisibility", "event_42"],
        citations=[
            {"source_id": "681f92bc94ff", "page": 245},
            {"source_id": "fed77f68501d", "page": 198}
        ]
    )

    data = question.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = RulesQuestion.from_dict(json.loads(json_str))

    assert restored.question_text == question.question_text
    assert restored.context_refs == question.context_refs
    assert restored.citations == question.citations


def test_ruling_conflict_basic():
    """RulingConflict should store conflict data."""
    question = RulesQuestion(
        question_text="Does spell X stack with spell Y?",
        context_refs=["pc_wizard"]
    )

    conflict = RulingConflict(
        question=question,
        conflict_notes="PHB p.171 says yes, DMG p.82 says no",
        conflicting_citations=[
            {"source_id": "681f92bc94ff", "page": 171},
            {"source_id": "fed77f68501d", "page": 82}
        ]
    )

    assert conflict.question.question_text == question.question_text
    assert "PHB p.171" in conflict.conflict_notes
    assert len(conflict.conflicting_citations) == 2


def test_ruling_conflict_empty_notes_rejected():
    """RulingConflict should reject empty conflict_notes."""
    question = RulesQuestion(question_text="test question")

    with pytest.raises(ValueError, match="conflict_notes cannot be empty"):
        RulingConflict(
            question=question,
            conflict_notes=""
        )


def test_ruling_conflict_serialization():
    """RulingConflict should serialize deterministically."""
    question = RulesQuestion(
        question_text="Does flanking apply to ranged attacks?",
        context_refs=["goblin_1", "pc_rogue"]
    )

    conflict = RulingConflict(
        question=question,
        conflict_notes="Conflicting interpretations in community",
        conflicting_citations=[
            {"source_id": "681f92bc94ff", "page": 154},
            {"source_id": "fed77f68501d", "page": 63}
        ]
    )

    data = conflict.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = RulingConflict.from_dict(json.loads(json_str))

    assert restored.question.question_text == conflict.question.question_text
    assert restored.conflict_notes == conflict.conflict_notes
    assert restored.conflicting_citations == conflict.conflicting_citations


def test_ruling_decision_basic():
    """RulingDecision should store resolution data."""
    decision = RulingDecision(
        resolution_text="Grapple does provoke AOO per PHB p.156",
        precedence_rationale="PHB is primary source for combat rules",
        citations_used=[{"source_id": "681f92bc94ff", "page": 156}],
        timestamp="2025-01-15T10:00:00Z",
        event_link=42
    )

    assert "Grapple does provoke AOO" in decision.resolution_text
    assert "PHB is primary source" in decision.precedence_rationale
    assert len(decision.citations_used) == 1
    assert decision.timestamp == "2025-01-15T10:00:00Z"
    assert decision.event_link == 42


def test_ruling_decision_empty_resolution_rejected():
    """RulingDecision should reject empty resolution_text."""
    with pytest.raises(ValueError, match="resolution_text cannot be empty"):
        RulingDecision(
            resolution_text="",
            precedence_rationale="test rationale"
        )


def test_ruling_decision_empty_rationale_rejected():
    """RulingDecision should reject empty precedence_rationale."""
    with pytest.raises(ValueError, match="precedence_rationale cannot be empty"):
        RulingDecision(
            resolution_text="test resolution",
            precedence_rationale=""
        )


def test_ruling_decision_citations_sorted():
    """RulingDecision should sort citations deterministically."""
    decision = RulingDecision(
        resolution_text="Ruling text",
        precedence_rationale="Specific beats general",
        citations_used=[
            {"source_id": "fed77f68501d", "page": 100},
            {"source_id": "681f92bc94ff", "page": 50},
            {"source_id": "681f92bc94ff", "page": 10}
        ]
    )

    data = decision.to_dict()
    citations = data["citations_used"]

    # Should be sorted by (source_id, page)
    assert citations[0]["source_id"] == "681f92bc94ff"
    assert citations[0]["page"] == 10
    assert citations[1]["source_id"] == "681f92bc94ff"
    assert citations[1]["page"] == 50
    assert citations[2]["source_id"] == "fed77f68501d"
    assert citations[2]["page"] == 100


def test_ruling_decision_serialization():
    """RulingDecision should serialize deterministically."""
    decision = RulingDecision(
        resolution_text="Invisibility does not prevent AOO if attacker has blindsight",
        precedence_rationale="DMG p.198 clarifies special senses",
        citations_used=[
            {"source_id": "fed77f68501d", "page": 198},
            {"source_id": "681f92bc94ff", "page": 245}
        ],
        timestamp="2025-01-15T12:00:00Z",
        event_link=99
    )

    data = decision.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = RulingDecision.from_dict(json.loads(json_str))

    assert restored.resolution_text == decision.resolution_text
    assert restored.precedence_rationale == decision.precedence_rationale
    assert restored.timestamp == decision.timestamp
    assert restored.event_link == decision.event_link


def test_ruling_decision_optional_fields():
    """RulingDecision should allow optional timestamp and event_link."""
    decision = RulingDecision(
        resolution_text="Use RAW interpretation",
        precedence_rationale="PHB text is clear",
        citations_used=[{"source_id": "681f92bc94ff", "page": 42}]
    )

    assert decision.timestamp is None
    assert decision.event_link is None

    data = decision.to_dict()
    assert "timestamp" not in data
    assert "event_link" not in data


def test_ruling_decision_roundtrip():
    """RulingDecision should roundtrip correctly."""
    original = RulingDecision(
        resolution_text="Flanking requires melee positioning",
        precedence_rationale="PHB p.154 defines flanking requirements",
        citations_used=[
            {"source_id": "681f92bc94ff", "page": 154},
            {"source_id": "fed77f68501d", "page": 63}
        ],
        timestamp="2025-01-15T15:30:00Z",
        event_link=123
    )

    data = original.to_dict()
    restored = RulingDecision.from_dict(data)

    assert restored.resolution_text == original.resolution_text
    assert restored.precedence_rationale == original.precedence_rationale
    assert restored.timestamp == original.timestamp
    assert restored.event_link == original.event_link
    # Citations should be sorted in to_dict()
    assert len(restored.citations_used) == len(original.citations_used)

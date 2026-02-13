"""Tests for tactical policy schemas."""

import pytest
import json
from aidm.schemas.policy import (
    TacticCandidate,
    ScoredTactic,
    TacticalPolicyTrace,
    TacticalPolicyResult
)


def test_tactic_candidate_basic():
    """TacticCandidate should store basic tactic data."""
    candidate = TacticCandidate(
        tactic_class="focus_fire",
        target_ids=["enemy_1"],
        notes="Focus fire on wizard"
    )

    assert candidate.tactic_class == "focus_fire"
    assert candidate.target_ids == ["enemy_1"]
    assert candidate.notes == "Focus fire on wizard"
    assert candidate.position_ref is None


def test_tactic_candidate_empty_tactic_class_rejected():
    """TacticCandidate should reject empty tactic_class."""
    with pytest.raises(ValueError, match="tactic_class cannot be empty"):
        TacticCandidate(tactic_class="")


def test_tactic_candidate_with_position():
    """TacticCandidate should support position reference."""
    candidate = TacticCandidate(
        tactic_class="retreat_regroup",
        position_ref={"x": 10, "y": 15}
    )

    assert candidate.position_ref == {"x": 10, "y": 15}


def test_tactic_candidate_serialization():
    """TacticCandidate should serialize deterministically."""
    candidate = TacticCandidate(
        tactic_class="setup_flank",
        target_ids=["enemy_1", "enemy_2"],
        position_ref={"x": 5, "y": 7},
        notes="Flank the caster"
    )

    data = candidate.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = TacticCandidate.from_dict(json.loads(json_str))

    assert restored.tactic_class == candidate.tactic_class
    assert restored.target_ids == candidate.target_ids
    assert restored.position_ref == candidate.position_ref
    assert restored.notes == candidate.notes


def test_tactic_candidate_serialization_omits_none_position():
    """TacticCandidate serialization should omit None position_ref."""
    candidate = TacticCandidate(tactic_class="attack_nearest")

    data = candidate.to_dict()

    assert "tactic_class" in data
    assert "target_ids" in data
    assert "notes" in data
    assert "position_ref" not in data


def test_scored_tactic_basic():
    """ScoredTactic should store candidate with score and reasons."""
    candidate = TacticCandidate(tactic_class="focus_fire")
    scored = ScoredTactic(
        candidate=candidate,
        score=5000,
        reasons=["base_score: 1000", "focus_fire_bonus: 4000"]
    )

    assert scored.candidate.tactic_class == "focus_fire"
    assert scored.score == 5000
    assert len(scored.reasons) == 2


def test_scored_tactic_negative_score_allowed():
    """ScoredTactic should allow negative scores."""
    candidate = TacticCandidate(tactic_class="retreat_regroup")
    scored = ScoredTactic(
        candidate=candidate,
        score=-2000,
        reasons=["penalty: -3000", "base: 1000"]
    )

    assert scored.score == -2000


def test_scored_tactic_non_integer_score_rejected():
    """ScoredTactic should reject non-integer scores."""
    candidate = TacticCandidate(tactic_class="focus_fire")

    with pytest.raises(ValueError, match="score must be an integer"):
        ScoredTactic(candidate=candidate, score=1.5)


def test_scored_tactic_serialization():
    """ScoredTactic should serialize deterministically."""
    candidate = TacticCandidate(
        tactic_class="use_cover",
        target_ids=[],
        notes="Find cover"
    )
    scored = ScoredTactic(
        candidate=candidate,
        score=3500,
        reasons=["base: 1000", "cover_bonus: 2500"]
    )

    data = scored.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = ScoredTactic.from_dict(json.loads(json_str))

    assert restored.candidate.tactic_class == scored.candidate.tactic_class
    assert restored.score == scored.score
    assert restored.reasons == scored.reasons


def test_tactical_policy_trace_basic():
    """TacticalPolicyTrace should store evaluation trace."""
    trace = TacticalPolicyTrace(
        actor_id="monster_1",
        doctrine_snapshot={"monster_id": "goblin", "allowed_tactics": ["focus_fire"]},
        extracted_features={"actor_hp_band": "healthy", "enemies_in_engagement": 2},
        candidates_before_filtering=["focus_fire", "retreat_regroup"],
        candidates_after_filtering=["focus_fire"],
        scoring_breakdown=[{"tactic": "focus_fire", "score": 5000}],
        final_selection_rationale="Selected focus_fire with score 5000"
    )

    assert trace.actor_id == "monster_1"
    assert trace.doctrine_snapshot["monster_id"] == "goblin"
    assert trace.extracted_features["actor_hp_band"] == "healthy"
    assert len(trace.candidates_after_filtering) == 1


def test_tactical_policy_trace_with_rng_draw():
    """TacticalPolicyTrace should support RNG draw details."""
    trace = TacticalPolicyTrace(
        actor_id="monster_1",
        doctrine_snapshot={},
        extracted_features={},
        rng_draw={"top_k": 3, "selected_index": 1, "method": "uniform_top_k"}
    )

    assert trace.rng_draw is not None
    assert trace.rng_draw["top_k"] == 3
    assert trace.rng_draw["selected_index"] == 1


def test_tactical_policy_trace_serialization():
    """TacticalPolicyTrace should serialize deterministically."""
    trace = TacticalPolicyTrace(
        actor_id="monster_1",
        doctrine_snapshot={"monster_id": "orc"},
        extracted_features={"actor_hp_band": "bloodied"},
        candidates_before_filtering=["focus_fire", "retreat_regroup"],
        candidates_after_filtering=["retreat_regroup"],
        scoring_breakdown=[],
        rng_draw={"top_k": 2, "selected_index": 0},
        final_selection_rationale="Greedy selection"
    )

    data = trace.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = TacticalPolicyTrace.from_dict(json.loads(json_str))

    assert restored.actor_id == trace.actor_id
    assert restored.doctrine_snapshot == trace.doctrine_snapshot
    assert restored.extracted_features == trace.extracted_features
    assert restored.rng_draw == trace.rng_draw


def test_tactical_policy_result_ok_status():
    """TacticalPolicyResult should store OK status with ranked tactics."""
    candidate1 = TacticCandidate(tactic_class="focus_fire")
    candidate2 = TacticCandidate(tactic_class="retreat_regroup")

    scored1 = ScoredTactic(candidate=candidate1, score=5000, reasons=[])
    scored2 = ScoredTactic(candidate=candidate2, score=3000, reasons=[])

    result = TacticalPolicyResult(
        status="ok",
        ranked=[scored1, scored2],
        selected=scored1
    )

    assert result.status == "ok"
    assert len(result.ranked) == 2
    assert result.selected.score == 5000


def test_tactical_policy_result_requires_clarification():
    """TacticalPolicyResult should support requires_clarification status."""
    result = TacticalPolicyResult(
        status="requires_clarification",
        ranked=[],
        selected=None,
        missing_fields=["actor_id"]
    )

    assert result.status == "requires_clarification"
    assert len(result.missing_fields) == 1
    assert "actor_id" in result.missing_fields


def test_tactical_policy_result_no_legal_tactics():
    """TacticalPolicyResult should support no_legal_tactics status."""
    trace = TacticalPolicyTrace(
        actor_id="monster_1",
        doctrine_snapshot={},
        extracted_features={},
        final_selection_rationale="No allowed tactics"
    )

    result = TacticalPolicyResult(
        status="no_legal_tactics",
        ranked=[],
        selected=None,
        trace=trace
    )

    assert result.status == "no_legal_tactics"
    assert len(result.ranked) == 0
    assert result.trace is not None


def test_tactical_policy_result_selected_must_be_in_ranked():
    """TacticalPolicyResult should reject selected not in ranked."""
    candidate1 = TacticCandidate(tactic_class="focus_fire")
    candidate2 = TacticCandidate(tactic_class="retreat_regroup")

    scored1 = ScoredTactic(candidate=candidate1, score=5000, reasons=[])
    scored2 = ScoredTactic(candidate=candidate2, score=3000, reasons=[])

    with pytest.raises(ValueError, match="selected tactic must appear in ranked list"):
        TacticalPolicyResult(
            status="ok",
            ranked=[scored1],
            selected=scored2  # Not in ranked
        )


def test_tactical_policy_result_serialization():
    """TacticalPolicyResult should serialize deterministically."""
    candidate = TacticCandidate(tactic_class="focus_fire")
    scored = ScoredTactic(candidate=candidate, score=5000, reasons=["base: 1000"])

    trace = TacticalPolicyTrace(
        actor_id="monster_1",
        doctrine_snapshot={},
        extracted_features={}
    )

    result = TacticalPolicyResult(
        status="ok",
        ranked=[scored],
        selected=scored,
        trace=trace
    )

    data = result.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = TacticalPolicyResult.from_dict(json.loads(json_str))

    assert restored.status == result.status
    assert len(restored.ranked) == len(result.ranked)
    assert restored.selected.score == result.selected.score
    assert restored.trace.actor_id == result.trace.actor_id


def test_tactical_policy_result_roundtrip():
    """TacticalPolicyResult should roundtrip correctly."""
    candidate1 = TacticCandidate(tactic_class="focus_fire", target_ids=["enemy_1"])
    candidate2 = TacticCandidate(tactic_class="use_cover")

    scored1 = ScoredTactic(candidate=candidate1, score=6000, reasons=["high_priority"])
    scored2 = ScoredTactic(candidate=candidate2, score=4000, reasons=["defensive"])

    trace = TacticalPolicyTrace(
        actor_id="monster_1",
        doctrine_snapshot={"monster_id": "goblin"},
        extracted_features={"actor_hp_band": "healthy"},
        candidates_before_filtering=["focus_fire", "use_cover"],
        candidates_after_filtering=["focus_fire", "use_cover"],
        scoring_breakdown=[scored1.to_dict(), scored2.to_dict()],
        final_selection_rationale="Max score selection"
    )

    original = TacticalPolicyResult(
        status="ok",
        ranked=[scored1, scored2],
        selected=scored1,
        trace=trace,
        missing_fields=[]
    )

    data = original.to_dict()
    restored = TacticalPolicyResult.from_dict(data)

    assert restored.status == original.status
    assert len(restored.ranked) == len(original.ranked)
    assert restored.ranked[0].score == original.ranked[0].score
    assert restored.selected.score == original.selected.score
    assert restored.trace.actor_id == original.trace.actor_id
    assert restored.missing_fields == original.missing_fields

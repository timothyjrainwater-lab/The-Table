"""Tests for tactical policy engine."""

import pytest
import json
from aidm.schemas.doctrine import MonsterDoctrine
from aidm.schemas.policy_config import PolicyVarietyConfig
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager
from aidm.core.tactical_policy import (
    extract_features,
    generate_candidates,
    score_candidate,
    select_tactic,
    evaluate_tactics
)
from aidm.schemas.policy import TacticCandidate, ScoredTactic
from aidm.core.doctrine_rules import derive_tactical_envelope


def test_extract_features_actor_not_found():
    """extract_features should detect missing actor."""
    world_state = WorldState(ruleset_version="3.5e", entities={})
    features = extract_features(world_state, "nonexistent")

    assert features["actor_found"] is False


def test_extract_features_actor_found():
    """extract_features should extract basic actor features."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 10, "y": 10},
                "team": "monsters"
            }
        }
    )

    features = extract_features(world_state, "goblin_1")

    assert features["actor_found"] is True
    assert features["actor_hp_band"] == "healthy"
    assert features["actor_stunned"] is False
    assert features["actor_prone"] is False


def test_extract_features_hp_bands():
    """extract_features should correctly classify HP bands."""
    # Healthy (>=75%)
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={"actor": {"hp_current": 80, "hp_max": 100, "conditions": [], "position": {"x": 0, "y": 0}, "team": "monsters"}}
    )
    features = extract_features(world_state, "actor")
    assert features["actor_hp_band"] == "healthy"

    # Wounded (50-74%)
    world_state.entities["actor"]["hp_current"] = 60
    features = extract_features(world_state, "actor")
    assert features["actor_hp_band"] == "wounded"

    # Bloodied (25-49%)
    world_state.entities["actor"]["hp_current"] = 30
    features = extract_features(world_state, "actor")
    assert features["actor_hp_band"] == "bloodied"

    # Critical (<25%)
    world_state.entities["actor"]["hp_current"] = 10
    features = extract_features(world_state, "actor")
    assert features["actor_hp_band"] == "critical"


def test_extract_features_conditions():
    """extract_features should detect actor conditions."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": ["stunned", "prone"],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            }
        }
    )

    features = extract_features(world_state, "goblin_1")

    assert features["actor_stunned"] is True
    assert features["actor_prone"] is True
    assert features["actor_frightened"] is False
    assert features["actor_grappled"] is False


def test_extract_features_nearby_enemies():
    """extract_features should count nearby enemies by distance band."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            },
            "pc_1": {  # In engagement (5 feet)
                "position": {"x": 5, "y": 0},
                "team": "party"
            },
            "pc_2": {  # Close range (30 feet)
                "position": {"x": 20, "y": 0},
                "team": "party"
            },
            "pc_3": {  # Medium range (60 feet)
                "position": {"x": 50, "y": 0},
                "team": "party"
            }
        }
    )

    features = extract_features(world_state, "goblin_1")

    assert features["enemies_in_engagement"] == 1
    assert features["enemies_close_range"] == 1
    assert features["enemies_medium_range"] == 1


def test_extract_features_nearby_allies():
    """extract_features should count nearby allies."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            },
            "goblin_2": {  # In engagement
                "position": {"x": 5, "y": 0},
                "team": "monsters"
            },
            "goblin_3": {  # Close range
                "position": {"x": 20, "y": 0},
                "team": "monsters"
            }
        }
    )

    features = extract_features(world_state, "goblin_1")

    assert features["allies_in_engagement"] == 1
    assert features["allies_close_range"] == 1


def test_generate_candidates_respects_doctrine():
    """generate_candidates should only create candidates for allowed tactics."""
    doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        allowed_tactics=["focus_fire", "use_cover"]
    )

    features = {"actor_found": True}
    candidates = generate_candidates(doctrine, features)

    assert len(candidates) == 2
    tactic_classes = {c.tactic_class for c in candidates}
    assert tactic_classes == {"focus_fire", "use_cover"}


def test_generate_candidates_deterministic_ordering():
    """generate_candidates should produce deterministic ordering."""
    doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        allowed_tactics=["retreat_regroup", "focus_fire", "attack_nearest"]
    )

    features = {"actor_found": True}

    # Generate twice
    candidates1 = generate_candidates(doctrine, features)
    candidates2 = generate_candidates(doctrine, features)

    # Should be identical order
    assert len(candidates1) == len(candidates2)
    for i in range(len(candidates1)):
        assert candidates1[i].tactic_class == candidates2[i].tactic_class


def test_score_candidate_base_score():
    """score_candidate should apply base score to all tactics."""
    candidate = TacticCandidate(tactic_class="attack_nearest")
    features = {"actor_hp_band": "healthy"}

    scored = score_candidate(candidate, features)

    assert scored.score >= 1000  # Base score
    assert "base_score: 1000" in scored.reasons


def test_score_candidate_retreat_regroup_critical_hp():
    """score_candidate should boost retreat_regroup for critical HP."""
    candidate = TacticCandidate(tactic_class="retreat_regroup")
    features = {"actor_hp_band": "critical"}

    scored = score_candidate(candidate, features)

    assert scored.score >= 6000  # Base + critical retreat bonus
    assert "critical_hp_retreat_bonus: 5000" in scored.reasons


def test_score_candidate_use_cover_multiple_enemies():
    """score_candidate should boost use_cover when outnumbered."""
    candidate = TacticCandidate(tactic_class="use_cover")
    features = {"actor_hp_band": "healthy", "enemies_in_engagement": 3}

    scored = score_candidate(candidate, features)

    assert any("multiple_enemies_cover_bonus" in r for r in scored.reasons)


def test_score_candidate_setup_flank_with_allies():
    """score_candidate should boost setup_flank when allies nearby."""
    candidate = TacticCandidate(tactic_class="setup_flank")
    features = {"actor_hp_band": "healthy", "allies_close_range": 2}

    scored = score_candidate(candidate, features)

    assert any("allies_nearby_flank_bonus" in r for r in scored.reasons)


def test_score_candidate_stunned_penalty():
    """score_candidate should apply heavy penalty for stunned condition."""
    candidate = TacticCandidate(tactic_class="focus_fire")
    features = {"actor_hp_band": "healthy", "actor_stunned": True}

    scored = score_candidate(candidate, features)

    assert scored.score < 0  # Should be negative due to penalty
    assert "stunned_penalty: -9000" in scored.reasons


def test_score_candidate_frightened_penalty():
    """score_candidate should penalize aggressive tactics when frightened."""
    candidate = TacticCandidate(tactic_class="focus_fire")
    features = {"actor_hp_band": "healthy", "actor_frightened": True}

    scored = score_candidate(candidate, features)

    assert "frightened_aggressive_penalty: -3000" in scored.reasons


def test_score_candidate_grappled_penalty():
    """score_candidate should penalize mobility tactics when grappled."""
    candidate = TacticCandidate(tactic_class="retreat_regroup")
    features = {"actor_hp_band": "healthy", "actor_grappled": True}

    scored = score_candidate(candidate, features)

    assert "grappled_mobility_penalty: -4000" in scored.reasons


def test_select_tactic_greedy_default():
    """select_tactic should select max score by default."""
    candidate1 = TacticCandidate(tactic_class="focus_fire")
    candidate2 = TacticCandidate(tactic_class="retreat_regroup")

    scored1 = ScoredTactic(candidate=candidate1, score=5000, reasons=[])
    scored2 = ScoredTactic(candidate=candidate2, score=3000, reasons=[])

    ranked = [scored1, scored2]

    selected, rng_draw = select_tactic(ranked, None, None)

    assert selected.candidate.tactic_class == "focus_fire"
    assert selected.score == 5000
    assert rng_draw is None


def test_select_tactic_variety_requires_rng():
    """select_tactic should require RNG for variety selection."""
    candidate = TacticCandidate(tactic_class="focus_fire")
    scored = ScoredTactic(candidate=candidate, score=5000, reasons=[])

    policy_config = PolicyVarietyConfig(top_k=3, temperature=1.0)

    with pytest.raises(ValueError, match="policy_rng required"):
        select_tactic([scored], policy_config, None)


def test_select_tactic_variety_with_rng():
    """select_tactic should use RNG for variety selection."""
    rng_manager = RNGManager(master_seed=42)
    policy_rng = rng_manager.stream("policy")

    candidate1 = TacticCandidate(tactic_class="focus_fire")
    candidate2 = TacticCandidate(tactic_class="use_cover")
    candidate3 = TacticCandidate(tactic_class="retreat_regroup")

    scored1 = ScoredTactic(candidate=candidate1, score=5000, reasons=[])
    scored2 = ScoredTactic(candidate=candidate2, score=4500, reasons=[])
    scored3 = ScoredTactic(candidate=candidate3, score=4000, reasons=[])

    ranked = [scored1, scored2, scored3]
    policy_config = PolicyVarietyConfig(top_k=3)

    selected, rng_draw = select_tactic(ranked, policy_config, policy_rng)

    assert selected is not None
    assert selected in ranked
    assert rng_draw is not None
    assert rng_draw["top_k"] == 3
    assert 0 <= rng_draw["selected_index"] < 3


def test_evaluate_tactics_missing_actor():
    """evaluate_tactics should return requires_clarification for missing actor."""
    world_state = WorldState(ruleset_version="3.5e", entities={})

    doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        allowed_tactics=["focus_fire"]
    )

    result = evaluate_tactics(doctrine, world_state, "nonexistent")

    assert result.status == "requires_clarification"
    assert "actor_id" in result.missing_fields
    assert len(result.ranked) == 0


def test_evaluate_tactics_no_allowed_tactics():
    """evaluate_tactics should return no_legal_tactics when doctrine forbids all."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "zombie": {
                "hp_current": 10,
                "hp_max": 10,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            }
        }
    )

    doctrine = MonsterDoctrine(
        monster_id="zombie",
        source="MM",
        int_score=None,
        wis_score=10,
        creature_type="undead",
        allowed_tactics=[]  # No tactics allowed
    )

    result = evaluate_tactics(doctrine, world_state, "zombie")

    assert result.status == "no_legal_tactics"
    assert len(result.ranked) == 0
    assert result.trace is not None


def test_evaluate_tactics_ok_status():
    """evaluate_tactics should return ok status with ranked tactics."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            }
        }
    )

    doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        allowed_tactics=["focus_fire", "use_cover", "retreat_regroup"]
    )

    result = evaluate_tactics(doctrine, world_state, "goblin_1")

    assert result.status == "ok"
    assert len(result.ranked) == 3
    assert result.selected is not None
    assert result.trace is not None


def test_evaluate_tactics_determinism():
    """evaluate_tactics should produce identical results for same inputs."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            }
        }
    )

    doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        allowed_tactics=["focus_fire", "use_cover"]
    )

    result1 = evaluate_tactics(doctrine, world_state, "goblin_1")
    result2 = evaluate_tactics(doctrine, world_state, "goblin_1")

    # Results should be identical
    assert result1.status == result2.status
    assert len(result1.ranked) == len(result2.ranked)
    assert result1.selected.candidate.tactic_class == result2.selected.candidate.tactic_class
    assert result1.selected.score == result2.selected.score


def test_evaluate_tactics_rng_isolation():
    """evaluate_tactics policy RNG should not affect combat RNG."""
    rng_manager = RNGManager(master_seed=42)
    combat_rng = rng_manager.stream("combat")
    policy_rng = rng_manager.stream("policy")

    # Capture initial combat RNG state
    initial_combat_count = combat_rng.call_count

    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            }
        }
    )

    doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        allowed_tactics=["focus_fire", "use_cover", "retreat_regroup"]
    )

    policy_config = PolicyVarietyConfig(top_k=3)

    # Evaluate with variety (should use policy RNG)
    result = evaluate_tactics(doctrine, world_state, "goblin_1", policy_config, policy_rng)

    # Combat RNG should be untouched
    assert combat_rng.call_count == initial_combat_count
    # Policy RNG should have been used
    assert policy_rng.call_count > 0


def test_evaluate_tactics_trace_completeness():
    """evaluate_tactics should produce complete trace."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            }
        }
    )

    doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        allowed_tactics=["focus_fire", "use_cover"]
    )

    result = evaluate_tactics(doctrine, world_state, "goblin_1")

    trace = result.trace
    assert trace.actor_id == "goblin_1"
    assert trace.doctrine_snapshot is not None
    assert trace.extracted_features is not None
    assert len(trace.candidates_after_filtering) == 2
    assert len(trace.scoring_breakdown) == 2
    assert trace.final_selection_rationale != ""


def test_evaluate_tactics_trace_serialization():
    """evaluate_tactics trace should serialize deterministically."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            }
        }
    )

    doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        allowed_tactics=["focus_fire"]
    )

    result = evaluate_tactics(doctrine, world_state, "goblin_1")

    # Serialize trace
    data = result.to_dict()
    json_str = json.dumps(data, sort_keys=True)

    # Should not raise
    parsed = json.loads(json_str)
    assert "trace" in parsed


def test_evaluate_tactics_selected_in_ranked():
    """evaluate_tactics selected tactic must appear in ranked."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            }
        }
    )

    doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        allowed_tactics=["focus_fire", "use_cover"]
    )

    result = evaluate_tactics(doctrine, world_state, "goblin_1")

    # Selected must be in ranked
    selected_tactic = result.selected.candidate.tactic_class
    ranked_tactics = {r.candidate.tactic_class for r in result.ranked}

    assert selected_tactic in ranked_tactics


def test_evaluate_tactics_integration_with_doctrine_derivation():
    """evaluate_tactics should work with derived doctrine envelope."""
    world_state = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 4,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            },
            "pc_1": {
                "position": {"x": 5, "y": 0},
                "team": "party"
            },
            "pc_2": {
                "position": {"x": 5, "y": 5},
                "team": "party"
            }
        }
    )

    # Create doctrine and derive tactical envelope
    doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid"
    )

    doctrine = derive_tactical_envelope(doctrine)

    # Evaluate tactics
    result = evaluate_tactics(doctrine, world_state, "goblin_1")

    assert result.status == "ok"
    assert len(result.ranked) > 0
    assert result.selected is not None


def test_evaluate_tactics_hp_affects_scoring():
    """evaluate_tactics should score retreat_regroup higher for low HP."""
    # Create two identical world states except HP
    world_state_healthy = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            }
        }
    )

    world_state_critical = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 1,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            }
        }
    )

    doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        allowed_tactics=["focus_fire", "retreat_regroup"]
    )

    result_healthy = evaluate_tactics(doctrine, world_state_healthy, "goblin_1")
    result_critical = evaluate_tactics(doctrine, world_state_critical, "goblin_1")

    # Find retreat_regroup scores
    retreat_score_healthy = next(
        r.score for r in result_healthy.ranked if r.candidate.tactic_class == "retreat_regroup"
    )
    retreat_score_critical = next(
        r.score for r in result_critical.ranked if r.candidate.tactic_class == "retreat_regroup"
    )

    # Critical HP should boost retreat score significantly
    assert retreat_score_critical > retreat_score_healthy


def test_evaluate_tactics_conditions_affect_scoring():
    """evaluate_tactics should score differently based on conditions."""
    # Healthy goblin
    world_state_healthy = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": [],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            }
        }
    )

    # Frightened goblin
    world_state_frightened = WorldState(
        ruleset_version="3.5e",
        entities={
            "goblin_1": {
                "hp_current": 6,
                "hp_max": 6,
                "conditions": ["frightened"],
                "position": {"x": 0, "y": 0},
                "team": "monsters"
            }
        }
    )

    doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=11,
        creature_type="humanoid",
        allowed_tactics=["focus_fire", "retreat_regroup"]
    )

    result_healthy = evaluate_tactics(doctrine, world_state_healthy, "goblin_1")
    result_frightened = evaluate_tactics(doctrine, world_state_frightened, "goblin_1")

    # Find focus_fire scores
    focus_score_healthy = next(
        r.score for r in result_healthy.ranked if r.candidate.tactic_class == "focus_fire"
    )
    focus_score_frightened = next(
        r.score for r in result_frightened.ranked if r.candidate.tactic_class == "focus_fire"
    )

    # Frightened should heavily penalize aggressive tactics
    assert focus_score_frightened < focus_score_healthy

"""Tactical policy engine for deterministic tactic evaluation and selection.

Evaluates and scores tactics within MonsterDoctrine constraints.
NO RESOLUTION LOGIC - produces scored choices only.
"""

from typing import Dict, Any, List, Optional
from aidm.schemas.doctrine import MonsterDoctrine, TacticClass
from aidm.schemas.policy import (
    TacticCandidate,
    ScoredTactic,
    TacticalPolicyResult,
    TacticalPolicyTrace,
    PolicyStatus
)
from aidm.schemas.policy_config import PolicyVarietyConfig
from aidm.core.state import WorldState
from aidm.core.rng_manager import DeterministicRNG
from aidm.schemas.entity_fields import EF


# Feature extraction constants (distance bands in feet, assuming 5ft grid)
ENGAGEMENT_RADIUS_FEET = 5
CLOSE_RANGE_FEET = 30
MEDIUM_RANGE_FEET = 60


def extract_features(world_state: WorldState, actor_id: str) -> Dict[str, Any]:
    """
    Extract features from WorldState for policy evaluation.

    Minimal initial feature set:
    - Actor exists
    - Nearby threats (distance bands)
    - Ally/enemy count
    - Actor HP band (internal DM-only)
    - Actor conditions restricting actions

    Args:
        world_state: Current world state
        actor_id: Entity ID of the acting creature

    Returns:
        Dictionary of extracted features (primitives only)
    """
    features: Dict[str, Any] = {}

    # Check actor exists
    if actor_id not in world_state.entities:
        features["actor_found"] = False
        return features

    features["actor_found"] = True
    actor = world_state.entities[actor_id]

    # Actor HP band (internal DM-only)
    hp_current = actor.get(EF.HP_CURRENT, 0)
    hp_max = actor.get(EF.HP_MAX, 1)
    hp_ratio = hp_current / hp_max if hp_max > 0 else 0

    if hp_ratio >= 0.75:
        features["actor_hp_band"] = "healthy"
    elif hp_ratio >= 0.5:
        features["actor_hp_band"] = "wounded"
    elif hp_ratio >= 0.25:
        features["actor_hp_band"] = "bloodied"
    else:
        features["actor_hp_band"] = "critical"

    # Actor conditions restricting actions
    conditions = actor.get(EF.CONDITIONS, [])
    features["actor_stunned"] = "stunned" in conditions
    features["actor_prone"] = "prone" in conditions
    features["actor_frightened"] = "frightened" in conditions
    features["actor_grappled"] = "grappled" in conditions

    # Actor position
    actor_pos = actor.get(EF.POSITION, {})
    actor_x = actor_pos.get("x", 0)
    actor_y = actor_pos.get("y", 0)

    # Count nearby entities by distance band
    features["enemies_in_engagement"] = 0
    features["enemies_close_range"] = 0
    features["enemies_medium_range"] = 0
    features["allies_in_engagement"] = 0
    features["allies_close_range"] = 0

    actor_team = actor.get(EF.TEAM, "unknown")

    for entity_id, entity in world_state.entities.items():
        if entity_id == actor_id:
            continue

        entity_pos = entity.get(EF.POSITION, {})
        entity_x = entity_pos.get("x", 0)
        entity_y = entity_pos.get("y", 0)

        # Simple Euclidean distance (for now)
        dx = entity_x - actor_x
        dy = entity_y - actor_y
        distance_feet = ((dx * dx) + (dy * dy)) ** 0.5

        entity_team = entity.get(EF.TEAM, "unknown")
        is_enemy = entity_team != actor_team and entity_team != "unknown"
        is_ally = entity_team == actor_team and entity_team != "unknown"

        # Count by distance band
        if distance_feet <= ENGAGEMENT_RADIUS_FEET:
            if is_enemy:
                features["enemies_in_engagement"] += 1
            if is_ally:
                features["allies_in_engagement"] += 1
        elif distance_feet <= CLOSE_RANGE_FEET:
            if is_enemy:
                features["enemies_close_range"] += 1
            if is_ally:
                features["allies_close_range"] += 1
        elif distance_feet <= MEDIUM_RANGE_FEET:
            if is_enemy:
                features["enemies_medium_range"] += 1

    return features


def generate_candidates(doctrine: MonsterDoctrine, features: Dict[str, Any]) -> List[TacticCandidate]:
    """
    Generate tactic candidates allowed by doctrine.

    Deterministic iteration order (sorted by tactic class name).

    Args:
        doctrine: MonsterDoctrine with allowed_tactics populated
        features: Extracted features from WorldState

    Returns:
        List of TacticCandidate objects
    """
    candidates = []

    # Sort allowed tactics for deterministic ordering
    allowed = sorted(doctrine.allowed_tactics)

    for tactic_class in allowed:
        # For now, generate one candidate per tactic class
        # In future packets, this could generate multiple candidates
        # (e.g., focus_fire with different targets)
        candidate = TacticCandidate(
            tactic_class=tactic_class,
            target_ids=[],  # Populated in future packets with targeting logic
            position_ref=None,
            notes=f"Candidate for {tactic_class}"
        )
        candidates.append(candidate)

    return candidates


def score_candidate(candidate: TacticCandidate, features: Dict[str, Any]) -> ScoredTactic:
    """
    Score a single tactic candidate using heuristic scoring.

    Integer math only (basis points scale: 10000 = 100%).
    Deterministic scoring based on features.

    Args:
        candidate: TacticCandidate to score
        features: Extracted features from WorldState

    Returns:
        ScoredTactic with score and reasons
    """
    score = 0
    reasons = []

    tactic = candidate.tactic_class

    # Base score for all tactics
    BASE_SCORE = 1000
    score += BASE_SCORE
    reasons.append(f"base_score: {BASE_SCORE}")

    # HP-based modifiers
    hp_band = features.get("actor_hp_band", "healthy")

    if tactic == "retreat_regroup":
        if hp_band == "critical":
            score += 5000
            reasons.append("critical_hp_retreat_bonus: 5000")
        elif hp_band == "bloodied":
            score += 2000
            reasons.append("bloodied_hp_retreat_bonus: 2000")

    if tactic == "fight_to_the_death":
        # Ignores HP (no penalties)
        reasons.append("fight_to_death_ignores_hp: 0")

    # Engagement pressure modifiers
    enemies_engaged = features.get("enemies_in_engagement", 0)

    if tactic == "use_cover":
        if enemies_engaged >= 2:
            score += 2000
            reasons.append("multiple_enemies_cover_bonus: 2000")

    if tactic == "retreat_regroup":
        if enemies_engaged >= 2:
            score += 1500
            reasons.append("outnumbered_retreat_bonus: 1500")

    if tactic == "setup_flank":
        allies_close = features.get("allies_close_range", 0)
        if allies_close >= 1:
            score += 1000
            reasons.append("allies_nearby_flank_bonus: 1000")

    if tactic == "focus_fire":
        # Always good baseline
        score += 500
        reasons.append("focus_fire_baseline_bonus: 500")

    if tactic == "attack_nearest":
        # Simple fallback
        score += 100
        reasons.append("attack_nearest_fallback_bonus: 100")

    # Condition penalties
    if features.get("actor_stunned", False):
        # Stunned creatures can't act tactically
        score -= 9000
        reasons.append("stunned_penalty: -9000")

    if features.get("actor_prone", False):
        if tactic not in ["use_cover", "retreat_regroup"]:
            score -= 1000
            reasons.append("prone_penalty: -1000")

    if features.get("actor_frightened", False):
        if tactic in ["focus_fire", "setup_flank", "fight_to_the_death"]:
            score -= 3000
            reasons.append("frightened_aggressive_penalty: -3000")

    if features.get("actor_grappled", False):
        if tactic in ["retreat_regroup", "setup_flank", "use_cover"]:
            score -= 4000
            reasons.append("grappled_mobility_penalty: -4000")

    return ScoredTactic(
        candidate=candidate,
        score=score,
        reasons=reasons
    )


def select_tactic(
    ranked: List[ScoredTactic],
    policy_config: Optional[PolicyVarietyConfig],
    policy_rng: Optional[DeterministicRNG]
) -> tuple[Optional[ScoredTactic], Optional[Dict[str, Any]]]:
    """
    Select a tactic from ranked candidates.

    Default: choose max score (greedy).
    Optional: weighted choice using policy RNG stream.

    Args:
        ranked: List of ScoredTactic in descending score order
        policy_config: Optional variety configuration
        policy_rng: Optional policy RNG stream (required if variety enabled)

    Returns:
        Tuple of (selected ScoredTactic or None, RNG draw details or None)
    """
    if not ranked:
        return None, None

    # Default greedy selection
    if policy_config is None or policy_config.top_k == 1:
        return ranked[0], None

    # Variety selection
    top_k = min(policy_config.top_k, len(ranked))
    candidates = ranked[:top_k]

    if policy_rng is None:
        raise ValueError("policy_rng required for variety selection")

    # For now: uniform random choice among top-k
    # Future: temperature-scaled weights
    selected_idx = policy_rng.randint(0, len(candidates) - 1)
    selected = candidates[selected_idx]

    rng_draw = {
        "top_k": top_k,
        "selected_index": selected_idx,
        "method": "uniform_top_k"
    }

    return selected, rng_draw


def evaluate_tactics(
    doctrine: MonsterDoctrine,
    world_state: WorldState,
    actor_id: str,
    policy_config: Optional[PolicyVarietyConfig] = None,
    policy_rng: Optional[DeterministicRNG] = None
) -> TacticalPolicyResult:
    """
    Evaluate and score tactics for an actor within doctrine constraints.

    Main entrypoint for tactical policy evaluation.

    Args:
        doctrine: MonsterDoctrine with allowed_tactics populated
        world_state: Current world state
        actor_id: Entity ID of the acting creature
        policy_config: Optional variety configuration
        policy_rng: Optional policy RNG stream (required if variety enabled)

    Returns:
        TacticalPolicyResult with status, ranked tactics, selection, and trace
    """
    # Extract features
    features = extract_features(world_state, actor_id)

    # Fail-closed: missing actor
    if not features.get("actor_found", False):
        return TacticalPolicyResult(
            status="requires_clarification",
            ranked=[],
            selected=None,
            trace=None,
            missing_fields=["actor_id"]
        )

    # Check allowed tactics
    if not doctrine.allowed_tactics:
        return TacticalPolicyResult(
            status="no_legal_tactics",
            ranked=[],
            selected=None,
            trace=TacticalPolicyTrace(
                actor_id=actor_id,
                doctrine_snapshot=doctrine.to_dict(),
                extracted_features=features,
                candidates_before_filtering=[],
                candidates_after_filtering=[],
                scoring_breakdown=[],
                final_selection_rationale="No allowed tactics in doctrine"
            ),
            missing_fields=[]
        )

    # Generate candidates
    candidates = generate_candidates(doctrine, features)

    # Score candidates
    scored = [score_candidate(c, features) for c in candidates]

    # Sort by score descending (deterministic: stable sort, already deterministic order)
    ranked = sorted(scored, key=lambda x: x.score, reverse=True)

    # Select tactic
    selected, rng_draw = select_tactic(ranked, policy_config, policy_rng)

    # Build trace
    trace = TacticalPolicyTrace(
        actor_id=actor_id,
        doctrine_snapshot=doctrine.to_dict(),
        extracted_features=features,
        candidates_before_filtering=[c.tactic_class for c in candidates],
        candidates_after_filtering=[c.tactic_class for c in candidates],
        scoring_breakdown=[s.to_dict() for s in ranked],
        rng_draw=rng_draw,
        final_selection_rationale=(
            f"Selected {selected.candidate.tactic_class} with score {selected.score}"
            if selected else "No selection"
        )
    )

    return TacticalPolicyResult(
        status="ok",
        ranked=ranked,
        selected=selected,
        trace=trace,
        missing_fields=[]
    )

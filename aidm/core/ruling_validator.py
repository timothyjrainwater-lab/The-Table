# WO-JUDGMENT-SHADOW-001: Phase 0 validator shell
from typing import List, Tuple
from aidm.schemas.ruling_artifact import RulingArtifactShadow

_DC_MIN = 5
_DC_MAX = 40


def validate_ruling_artifact(artifact: RulingArtifactShadow) -> Tuple[str, List[str]]:
    """
    Phase 0 validation: schema completeness + DC bounds only.
    Returns (validator_verdict, validator_reasons).
    Phase 1 adds: mechanic legality, modifier source checking, rationale quality.
    """
    reasons = []

    # Schema completeness
    if not artifact.player_action_raw:
        reasons.append("player_action_raw is empty")
    if not artifact.route_class:
        reasons.append("route_class is missing")
    if not artifact.routing_confidence:
        reasons.append("routing_confidence is missing")

    # DC bounds (only checked if dc is provided)
    if artifact.dc is not None:
        if artifact.dc < _DC_MIN:
            reasons.append(f"dc={artifact.dc} is below minimum ({_DC_MIN})")
        elif artifact.dc > _DC_MAX:
            reasons.append(f"dc={artifact.dc} exceeds maximum ({_DC_MAX}); flag for DM review")
            # DC > 40 is needs_clarification, not hard fail
            return "needs_clarification", reasons

    if reasons:
        return "fail", reasons
    return "pass", []

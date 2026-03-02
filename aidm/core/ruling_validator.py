# WO-JUDGMENT-SHADOW-001: Phase 0 validator shell
# WO-JUDGMENT-VALIDATOR-001: Phase 1 — mechanic legality + data-driven DC bounds
import json
import os
from typing import List, Tuple

from aidm.schemas.ruling_artifact import RulingArtifactShadow

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

with open(os.path.join(_DATA_DIR, "srd_dc_ranges.json"), encoding="utf-8") as _f:
    _dc_data = json.load(_f)
_DC_MIN: int = _dc_data["dc_min"]   # 5 — PHB p.65
_DC_MAX: int = _dc_data["dc_max"]   # 40 — PHB p.65

with open(os.path.join(_DATA_DIR, "srd_skills.json"), encoding="utf-8") as _f:
    _srd_skills = json.load(_f)

_VALID_MECHANICS: frozenset = frozenset(
    {s["name"] for s in _srd_skills}
    | {
        # PHB p.7 ability scores — full names and abbreviations
        "strength", "dexterity", "constitution",
        "intelligence", "wisdom", "charisma",
        "str", "dex", "con", "int", "wis", "cha",
        # No-roll outcome sentinel (SPEC-RULING-CONTRACT-001)
        "none",
    }
)


def validate_ruling_artifact(artifact: RulingArtifactShadow) -> Tuple[str, List[str]]:
    """
    Phase 0 validation: schema completeness + DC bounds only.
    Returns (validator_verdict, validator_reasons).
    Phase 1 adds: mechanic legality [IMPLEMENTED — WO-JUDGMENT-VALIDATOR-001].
    Remaining: modifier source checking, rationale quality.
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

    # Mechanic legality (Phase 1: WO-JUDGMENT-VALIDATOR-001)
    if artifact.ability_or_skill is not None:
        normalized = artifact.ability_or_skill.lower().strip().replace(" ", "_")
        if normalized not in _VALID_MECHANICS:
            reasons.append(
                f"unrecognized mechanic: {artifact.ability_or_skill!r} — "
                "not in SRD skill list or ability score set (srd_skills.json, PHB p.7)"
            )

    if reasons:
        return "fail", reasons
    return "pass", []

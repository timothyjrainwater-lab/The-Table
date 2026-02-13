"""Tests for WO-CONTENT-EXTRACT-003 — Feat Extraction Pipeline.

Validates:
1. Recognition: no original feat names in feats.json
2. Schema validity: every entry matches MechanicalFeatTemplate
3. Prerequisite chains: all FEAT_XXX references exist
4. Spot-check: 10 feats verified against known mechanics
5. No prose leakage: no field > 100 characters
6. Fighter bonus feat flag correctness
"""

import json
import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
FEATS_JSON = PROJECT_ROOT / "aidm" / "data" / "content_pack" / "feats.json"
PROVENANCE_JSON = PROJECT_ROOT / "tools" / "data" / "feat_provenance.json"
GAPS_JSON = PROJECT_ROOT / "tools" / "data" / "feat_extraction_gaps.json"


@pytest.fixture(scope="module")
def feats_data():
    """Load feats.json."""
    assert FEATS_JSON.exists(), f"feats.json not found at {FEATS_JSON}"
    with open(FEATS_JSON, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def feats_list(feats_data):
    """Return list of feat dicts."""
    return feats_data["feats"]


@pytest.fixture(scope="module")
def feats_by_id(feats_list):
    """Return feats indexed by template_id."""
    return {f["template_id"]: f for f in feats_list}


@pytest.fixture(scope="module")
def provenance():
    """Load provenance data."""
    assert PROVENANCE_JSON.exists(), f"provenance not found at {PROVENANCE_JSON}"
    with open(PROVENANCE_JSON, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def name_to_id(provenance):
    """Return name->template_id mapping."""
    return provenance["name_to_id"]


# ---------------------------------------------------------------------------
# 1. Recognition Test — no original feat names in feats.json
# ---------------------------------------------------------------------------

# A sample of well-known feat names that must NOT appear in the output
KNOWN_FEAT_NAMES = [
    "Power Attack",
    "Cleave",
    "Great Cleave",
    "Dodge",
    "Mobility",
    "Spring Attack",
    "Point Blank Shot",
    "Precise Shot",
    "Rapid Shot",
    "Weapon Focus",
    "Weapon Specialization",
    "Two-Weapon Fighting",
    "Improved Initiative",
    "Improved Critical",
    "Combat Expertise",
    "Improved Grapple",
    "Stunning Fist",
    "Deflect Arrows",
    "Whirlwind Attack",
    "Brew Potion",
    "Empower Spell",
    "Quicken Spell",
    "Blind-Fight",
    "Leadership",
    "Toughness",
    "Iron Will",
    "Lightning Reflexes",
    "Great Fortitude",
    "Spell Focus",
    "Spell Penetration",
]


class TestRecognition:
    """No original feat names may appear in feats.json."""

    def test_no_feat_names_in_json(self, feats_list):
        feats_json_str = json.dumps(feats_list)
        for name in KNOWN_FEAT_NAMES:
            assert name not in feats_json_str, (
                f"Original feat name '{name}' found in feats.json — IP firewall breach"
            )

    def test_template_ids_use_feat_prefix(self, feats_list):
        for feat in feats_list:
            assert feat["template_id"].startswith("FEAT_"), (
                f"Template ID {feat['template_id']} does not use FEAT_ prefix"
            )

    def test_template_ids_are_unique(self, feats_list):
        ids = [f["template_id"] for f in feats_list]
        assert len(ids) == len(set(ids)), "Duplicate template IDs found"


# ---------------------------------------------------------------------------
# 2. Schema Validity
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {
    "template_id": str,
    "feat_type": str,
    "prereq_ability_scores": dict,
    "prereq_bab": (int, type(None)),
    "prereq_feat_refs": list,
    "prereq_class_features": list,
    "prereq_caster_level": (int, type(None)),
    "prereq_other": list,
    "effect_type": str,
    "bonus_value": (int, type(None)),
    "bonus_type": (str, type(None)),
    "bonus_applies_to": (str, type(None)),
    "trigger": (str, type(None)),
    "replaces_normal": (str, type(None)),
    "grants_action": (str, type(None)),
    "removes_penalty": (str, type(None)),
    "stacks_with": list,
    "limited_to": (str, type(None)),
    "fighter_bonus_eligible": bool,
    "can_take_multiple": bool,
    "effects_stack": bool,
    "metamagic_slot_increase": (int, type(None)),
    "source_page": str,
    "source_id": str,
}

VALID_FEAT_TYPES = {"general", "metamagic", "item_creation"}
VALID_EFFECT_TYPES = {
    "attack_modifier", "ac_modifier", "save_modifier", "damage_modifier",
    "action_economy", "special_action", "passive_defense", "skill_modifier",
    "metamagic_modifier", "item_creation", "initiative_modifier",
    "proficiency", "movement_modifier", "hp_modifier", "caster_level_modifier",
    "save_dc_modifier", "critical_modifier", "summoning_modifier",
    "class_feature_modifier",
}


class TestSchema:
    """Every feat entry has valid schema."""

    def test_all_required_fields_present(self, feats_list):
        for feat in feats_list:
            for field, expected_type in REQUIRED_FIELDS.items():
                assert field in feat, (
                    f"{feat['template_id']} missing field '{field}'"
                )

    def test_field_types_correct(self, feats_list):
        for feat in feats_list:
            for field, expected_type in REQUIRED_FIELDS.items():
                val = feat[field]
                assert isinstance(val, expected_type), (
                    f"{feat['template_id']}.{field}: expected {expected_type}, "
                    f"got {type(val).__name__} = {val!r}"
                )

    def test_feat_type_valid(self, feats_list):
        for feat in feats_list:
            assert feat["feat_type"] in VALID_FEAT_TYPES, (
                f"{feat['template_id']}: invalid feat_type '{feat['feat_type']}'"
            )

    def test_effect_type_valid(self, feats_list):
        for feat in feats_list:
            assert feat["effect_type"] in VALID_EFFECT_TYPES, (
                f"{feat['template_id']}: invalid effect_type '{feat['effect_type']}'"
            )

    def test_source_id_set(self, feats_list):
        for feat in feats_list:
            assert feat["source_id"] == "681f92bc94ff", (
                f"{feat['template_id']}: wrong source_id"
            )

    def test_schema_version(self, feats_data):
        assert feats_data["schema_version"] == "1.0.0"
        assert feats_data["extraction_version"] == "WO-CONTENT-EXTRACT-003"


# ---------------------------------------------------------------------------
# 3. Prerequisite Chain Validity
# ---------------------------------------------------------------------------

class TestPrerequisiteChains:
    """All FEAT_XXX prerequisite references point to existing feats."""

    def test_all_prereq_refs_exist(self, feats_list, feats_by_id):
        for feat in feats_list:
            for ref in feat["prereq_feat_refs"]:
                assert ref in feats_by_id, (
                    f"{feat['template_id']} references nonexistent prereq {ref}"
                )

    def test_no_self_referencing_prereqs(self, feats_list):
        for feat in feats_list:
            assert feat["template_id"] not in feat["prereq_feat_refs"], (
                f"{feat['template_id']} references itself as prerequisite"
            )

    def test_no_circular_prereqs(self, feats_list, feats_by_id):
        """Check for circular prerequisite chains."""
        for feat in feats_list:
            visited = set()
            queue = list(feat["prereq_feat_refs"])
            while queue:
                ref = queue.pop(0)
                if ref == feat["template_id"]:
                    pytest.fail(
                        f"Circular prerequisite chain detected for {feat['template_id']}"
                    )
                if ref not in visited:
                    visited.add(ref)
                    ref_feat = feats_by_id.get(ref, {})
                    queue.extend(ref_feat.get("prereq_feat_refs", []))

    def test_ability_score_prereqs_valid(self, feats_list):
        valid_abilities = {"str", "dex", "con", "int", "wis", "cha"}
        for feat in feats_list:
            for ability, score in feat["prereq_ability_scores"].items():
                assert ability in valid_abilities, (
                    f"{feat['template_id']}: invalid ability '{ability}'"
                )
                assert isinstance(score, int) and 1 <= score <= 30, (
                    f"{feat['template_id']}: invalid score {score} for {ability}"
                )


# ---------------------------------------------------------------------------
# 4. Spot-Check — 10 feats verified against known mechanics
# ---------------------------------------------------------------------------

class TestSpotCheck:
    """Verify specific feats against known PHB mechanics."""

    def test_improved_initiative_bonus(self, feats_by_id, name_to_id):
        fid = name_to_id["IMPROVED INITIATIVE"]
        feat = feats_by_id[fid]
        assert feat["effect_type"] == "initiative_modifier"
        assert feat["bonus_value"] == 4
        assert feat["bonus_type"] == "initiative"
        assert feat["fighter_bonus_eligible"] is True
        assert feat["prereq_ability_scores"] == {}
        assert feat["prereq_bab"] is None

    def test_dodge_ac_bonus(self, feats_by_id, name_to_id):
        fid = name_to_id["DODGE"]
        feat = feats_by_id[fid]
        assert feat["effect_type"] == "ac_modifier"
        assert feat["bonus_value"] == 1
        assert feat["prereq_ability_scores"] == {"dex": 13}
        assert feat["fighter_bonus_eligible"] is True

    def test_cleave_prereqs_and_effect(self, feats_by_id, name_to_id):
        fid = name_to_id["CLEAVE"]
        feat = feats_by_id[fid]
        pa_id = name_to_id["POWER ATTACK"]
        assert pa_id in feat["prereq_feat_refs"]
        assert feat["prereq_ability_scores"] == {"str": 13}
        assert feat["effect_type"] == "action_economy"
        assert feat["trigger"] == "on_kill"

    def test_weapon_focus_attack_bonus(self, feats_by_id, name_to_id):
        fid = name_to_id["WEAPON FOCUS"]
        feat = feats_by_id[fid]
        assert feat["effect_type"] == "attack_modifier"
        assert feat["bonus_value"] == 1
        assert feat["bonus_type"] == "attack_roll"
        assert feat["bonus_applies_to"] == "selected_weapon"
        assert feat["can_take_multiple"] is True

    def test_weapon_specialization_damage_bonus(self, feats_by_id, name_to_id):
        fid = name_to_id["WEAPON SPECIALIZATION"]
        feat = feats_by_id[fid]
        wf_id = name_to_id["WEAPON FOCUS"]
        assert wf_id in feat["prereq_feat_refs"]
        assert feat["effect_type"] == "damage_modifier"
        assert feat["bonus_value"] == 2
        assert "fighter_level_4" in feat["prereq_other"]

    def test_point_blank_shot_range_bonus(self, feats_by_id, name_to_id):
        fid = name_to_id["POINT BLANK SHOT"]
        feat = feats_by_id[fid]
        assert feat["effect_type"] == "attack_modifier"
        assert feat["bonus_value"] == 1
        assert feat["bonus_applies_to"] == "ranged_30ft"
        assert feat["prereq_feat_refs"] == []

    def test_toughness_hp_bonus(self, feats_by_id, name_to_id):
        fid = name_to_id["TOUGHNESS"]
        feat = feats_by_id[fid]
        assert feat["effect_type"] == "hp_modifier"
        assert feat["bonus_value"] == 3
        assert feat["can_take_multiple"] is True
        assert feat["effects_stack"] is True

    def test_iron_will_save_bonus(self, feats_by_id, name_to_id):
        fid = name_to_id["IRON WILL"]
        feat = feats_by_id[fid]
        assert feat["effect_type"] == "save_modifier"
        assert feat["bonus_value"] == 2
        assert feat["bonus_applies_to"] == "will"

    def test_brew_potion_item_creation(self, feats_by_id, name_to_id):
        fid = name_to_id["BREW POTION"]
        feat = feats_by_id[fid]
        assert feat["feat_type"] == "item_creation"
        assert feat["effect_type"] == "item_creation"
        assert feat["prereq_caster_level"] == 3

    def test_empower_spell_metamagic(self, feats_by_id, name_to_id):
        fid = name_to_id["EMPOWER SPELL"]
        feat = feats_by_id[fid]
        assert feat["feat_type"] == "metamagic"
        assert feat["effect_type"] == "metamagic_modifier"
        assert feat["metamagic_slot_increase"] == 2


# ---------------------------------------------------------------------------
# 5. No Prose Leakage
# ---------------------------------------------------------------------------

class TestNoProseLeakage:
    """Content pack must not contain descriptive prose."""

    def test_no_field_over_100_chars(self, feats_list):
        for feat in feats_list:
            for key, val in feat.items():
                if isinstance(val, str):
                    assert len(val) <= 100, (
                        f"{feat['template_id']}.{key}: string field is "
                        f"{len(val)} chars (max 100): {val[:80]}..."
                    )

    def test_no_prose_sentences(self, feats_list):
        """Fields should not contain full prose sentences."""
        prose_patterns = [
            r"^You (can|are|get|have|gain|may)\b",
            r"^When you\b",
            r"^If you\b",
            r"^A character\b",
        ]
        # Only check mechanical fields (not replaces_normal which is a summary)
        check_fields = [
            "effect_type", "bonus_type", "bonus_applies_to",
            "trigger", "grants_action", "removes_penalty",
            "limited_to",
        ]
        for feat in feats_list:
            for field in check_fields:
                val = feat.get(field)
                if val is None:
                    continue
                for pattern in prose_patterns:
                    assert not re.match(pattern, val), (
                        f"{feat['template_id']}.{field} contains prose: {val}"
                    )


# ---------------------------------------------------------------------------
# 6. Fighter Bonus Feat Flag
# ---------------------------------------------------------------------------

# These feats are explicitly listed as fighter bonus feats in the PHB
KNOWN_FIGHTER_BONUS_FEATS = [
    "BLIND-FIGHT",
    "CLEAVE",
    "COMBAT EXPERTISE",
    "COMBAT REFLEXES",
    "DEFLECT ARROWS",
    "DODGE",
    "EXOTIC WEAPON PROFICIENCY",
    "FAR SHOT",
    "GREAT CLEAVE",
    "IMPROVED BULL RUSH",
    "IMPROVED CRITICAL",
    "IMPROVED DISARM",
    "IMPROVED FEINT",
    "IMPROVED GRAPPLE",
    "IMPROVED INITIATIVE",
    "IMPROVED OVERRUN",
    "IMPROVED PRECISE SHOT",
    "IMPROVED SHIELD BASH",
    "IMPROVED SUNDER",
    "IMPROVED TRIP",
    "IMPROVED TWO-WEAPON FIGHTING",
    "IMPROVED UNARMED STRIKE",
    "MANYSHOT",
    "MOBILITY",
    "MOUNTED ARCHERY",
    "MOUNTED COMBAT",
    "POINT BLANK SHOT",
    "POWER ATTACK",
    "PRECISE SHOT",
    "QUICK DRAW",
    "RAPID RELOAD",
    "RAPID SHOT",
    "RIDE-BY ATTACK",
    "SHOT ON THE RUN",
    "SNATCH ARROWS",
    "SPRING ATTACK",
    "STUNNING FIST",
    "TRAMPLE",
    "TWO-WEAPON DEFENSE",
    "TWO-WEAPON FIGHTING",
    "WEAPON FINESSE",
    "WEAPON FOCUS",
    "WEAPON SPECIALIZATION",
    "WHIRLWIND ATTACK",
    "GREATER TWO-WEAPON FIGHTING",
    "GREATER WEAPON FOCUS",
    "GREATER WEAPON SPECIALIZATION",
]


class TestFighterBonusFeat:
    """Fighter bonus feat flag must be set correctly."""

    def test_known_fighter_feats_are_flagged(self, feats_by_id, name_to_id):
        for name in KNOWN_FIGHTER_BONUS_FEATS:
            fid = name_to_id.get(name)
            if fid is None:
                pytest.skip(f"Feat '{name}' not found in provenance")
            feat = feats_by_id.get(fid)
            assert feat is not None, f"Feat {fid} not in feats.json"
            assert feat["fighter_bonus_eligible"] is True, (
                f"{name} ({fid}): fighter_bonus_eligible should be True"
            )

    def test_metamagic_feats_not_fighter_bonus(self, feats_list):
        """Metamagic feats are not fighter bonus feats."""
        for feat in feats_list:
            if feat["feat_type"] == "metamagic":
                assert feat["fighter_bonus_eligible"] is False, (
                    f"{feat['template_id']}: metamagic feat should not be "
                    f"fighter_bonus_eligible"
                )

    def test_item_creation_feats_not_fighter_bonus(self, feats_list):
        """Item creation feats are not fighter bonus feats."""
        for feat in feats_list:
            if feat["feat_type"] == "item_creation":
                assert feat["fighter_bonus_eligible"] is False, (
                    f"{feat['template_id']}: item creation feat should not be "
                    f"fighter_bonus_eligible"
                )


# ---------------------------------------------------------------------------
# 7. Provenance File Integrity
# ---------------------------------------------------------------------------

class TestProvenance:
    """Provenance file must be complete and consistent."""

    def test_provenance_has_all_feats(self, feats_list, provenance):
        prov_ids = {e["template_id"] for e in provenance["entries"]}
        feat_ids = {f["template_id"] for f in feats_list}
        assert feat_ids == prov_ids, (
            f"Provenance/feats mismatch: "
            f"in feats but not prov: {feat_ids - prov_ids}, "
            f"in prov but not feats: {prov_ids - feat_ids}"
        )

    def test_name_to_id_mapping_complete(self, provenance):
        name_to_id = provenance["name_to_id"]
        entries = provenance["entries"]
        for entry in entries:
            name = entry["original_name"]
            assert name in name_to_id, (
                f"Name '{name}' not in name_to_id mapping"
            )
            assert name_to_id[name] == entry["template_id"]

    def test_provenance_has_page_info(self, provenance):
        for entry in provenance["entries"]:
            assert entry.get("page"), (
                f"{entry['template_id']}: missing page in provenance"
            )


# ---------------------------------------------------------------------------
# 8. Completeness vs Existing Registry
# ---------------------------------------------------------------------------

class TestExistingRegistryCoverage:
    """All 15 feats in the existing FEAT_REGISTRY should have provenance."""

    EXISTING_FEATS = [
        "POWER ATTACK",
        "CLEAVE",
        "GREAT CLEAVE",
        "DODGE",
        "MOBILITY",
        "SPRING ATTACK",
        "POINT BLANK SHOT",
        "PRECISE SHOT",
        "RAPID SHOT",
        "WEAPON FOCUS",
        "WEAPON SPECIALIZATION",
        "TWO-WEAPON FIGHTING",
        "IMPROVED TWO-WEAPON FIGHTING",
        "GREATER TWO-WEAPON FIGHTING",
        "IMPROVED INITIATIVE",
    ]

    def test_all_existing_feats_extracted(self, name_to_id):
        for name in self.EXISTING_FEATS:
            assert name in name_to_id, (
                f"Existing registry feat '{name}' not found in extraction"
            )


# ---------------------------------------------------------------------------
# 9. Feat Count Sanity
# ---------------------------------------------------------------------------

class TestFeatCount:
    """PHB Chapter 5 contains approximately 87-120 feats."""

    def test_minimum_feat_count(self, feats_data):
        assert feats_data["feat_count"] >= 80, (
            f"Only {feats_data['feat_count']} feats extracted — expected at least 80"
        )

    def test_feat_count_matches_list(self, feats_data):
        assert feats_data["feat_count"] == len(feats_data["feats"])

    def test_feat_type_distribution(self, feats_list):
        """Verify rough distribution of feat types."""
        from collections import Counter
        types = Counter(f["feat_type"] for f in feats_list)
        assert types["general"] >= 70, f"Only {types['general']} general feats"
        assert types["metamagic"] >= 7, f"Only {types['metamagic']} metamagic feats"
        assert types["item_creation"] >= 7, f"Only {types['item_creation']} item creation feats"

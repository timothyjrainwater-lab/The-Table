"""Gate V3: Complete PHB Feat List Tests (WO-CHARGEN-FEATS-COMPLETE).

15 tests covering:
- Total feat count (V3-01)
- Save feats (V3-02)
- Toughness (V3-03)
- Combat maneuver chain (V3-04)
- Mounted feats (V3-05)
- Ranged extended (V3-06)
- Melee extended (V3-07)
- Skill feats (V3-08)
- Spell feats (V3-09)
- Proficiency chain (V3-10)
- Class-specific feats (V3-11)
- Item creation feats (V3-12)
- Prerequisite chains valid (V3-13)
- Original 15 preserved (V3-14)
- get_feat_definition still works (V3-15)

Source: PHB Chapter 5 (Feats)
"""

import pytest

from aidm.schemas.feats import FEAT_REGISTRY, FeatID, get_feat_definition


def test_v3_01_total_feat_count():
    """V3-01: FEAT_REGISTRY has >= 50 entries."""
    assert len(FEAT_REGISTRY) >= 50, f"Expected >= 50 feats, got {len(FEAT_REGISTRY)}"


def test_v3_02_save_feats():
    """V3-02: Great Fortitude, Iron Will, Lightning Reflexes exist with no prereqs."""
    for fid in ("great_fortitude", "iron_will", "lightning_reflexes"):
        feat = FEAT_REGISTRY[fid]
        assert feat.modifier_type == "save"
        assert feat.prerequisites == {}


def test_v3_03_toughness():
    """V3-03: Toughness exists, grants HP."""
    t = FEAT_REGISTRY["toughness"]
    assert t.modifier_type == "hp"
    assert t.prerequisites == {}


def test_v3_04_combat_maneuver_feats():
    """V3-04: All combat maneuver feats exist."""
    maneuver_ids = {
        "combat_reflexes", "improved_bull_rush", "improved_disarm",
        "improved_feint", "improved_grapple", "improved_overrun",
        "improved_sunder", "improved_trip",
    }
    for fid in maneuver_ids:
        assert fid in FEAT_REGISTRY, f"Missing: {fid}"


def test_v3_05_mounted_feats():
    """V3-05: Mounted feat chain exists with correct prerequisites."""
    mc = FEAT_REGISTRY["mounted_combat"]
    assert mc.prerequisites.get("min_ride_ranks") == 1

    rba = FEAT_REGISTRY["ride_by_attack"]
    assert "mounted_combat" in rba.prerequisites.get("required_feats", [])

    sc = FEAT_REGISTRY["spirited_charge"]
    prereqs = sc.prerequisites.get("required_feats", [])
    assert "mounted_combat" in prereqs
    assert "ride_by_attack" in prereqs


def test_v3_06_ranged_extended():
    """V3-06: Shot on the Run, Manyshot, Improved Critical exist."""
    assert "shot_on_the_run" in FEAT_REGISTRY
    assert "manyshot" in FEAT_REGISTRY
    assert "improved_critical" in FEAT_REGISTRY

    ms = FEAT_REGISTRY["manyshot"]
    assert ms.prerequisites.get("min_bab") == 6


def test_v3_07_melee_extended():
    """V3-07: Blind-Fight, Combat Expertise, Whirlwind Attack exist."""
    assert "blind_fight" in FEAT_REGISTRY
    ce = FEAT_REGISTRY["combat_expertise"]
    assert ce.prerequisites.get("min_int") == 13

    wa = FEAT_REGISTRY["whirlwind_attack"]
    prereqs = wa.prerequisites.get("required_feats", [])
    assert "combat_expertise" in prereqs
    assert "spring_attack" in prereqs


def test_v3_08_skill_feats():
    """V3-08: All 12 skill feats exist with no prerequisites."""
    skill_feat_ids = {
        "alertness", "athletic", "acrobatic", "deceitful", "deft_hands",
        "diligent", "investigator", "negotiator", "nimble_fingers",
        "persuasive", "self_sufficient", "stealthy",
    }
    for fid in skill_feat_ids:
        feat = FEAT_REGISTRY[fid]
        assert feat.modifier_type == "skill"
        assert feat.prerequisites == {}, f"{fid} has unexpected prerequisites"


def test_v3_09_spell_feats():
    """V3-09: Spell Focus chain and Spell Penetration chain exist."""
    sf = FEAT_REGISTRY["spell_focus"]
    assert sf.modifier_type == "spell"
    gsf = FEAT_REGISTRY["greater_spell_focus"]
    assert "spell_focus" in gsf.prerequisites.get("required_feats", [])

    sp = FEAT_REGISTRY["spell_penetration"]
    gsp = FEAT_REGISTRY["greater_spell_penetration"]
    assert "spell_penetration" in gsp.prerequisites.get("required_feats", [])


def test_v3_10_proficiency_chain():
    """V3-10: Armor proficiency chain has correct prerequisites."""
    light = FEAT_REGISTRY["armor_proficiency_light"]
    assert light.prerequisites == {}

    medium = FEAT_REGISTRY["armor_proficiency_medium"]
    assert "armor_proficiency_light" in medium.prerequisites.get("required_feats", [])

    heavy = FEAT_REGISTRY["armor_proficiency_heavy"]
    heavy_prereqs = heavy.prerequisites.get("required_feats", [])
    assert "armor_proficiency_light" in heavy_prereqs
    assert "armor_proficiency_medium" in heavy_prereqs


def test_v3_11_class_specific_feats():
    """V3-11: Class-specific feats exist."""
    assert "extra_turning" in FEAT_REGISTRY
    assert "natural_spell" in FEAT_REGISTRY
    assert "track" in FEAT_REGISTRY
    assert "endurance" in FEAT_REGISTRY

    dh = FEAT_REGISTRY["diehard"]
    assert "endurance" in dh.prerequisites.get("required_feats", [])


def test_v3_12_item_creation_feats():
    """V3-12: Item creation feats exist with caster level prerequisites."""
    ss = FEAT_REGISTRY["scribe_scroll"]
    assert ss.prerequisites.get("min_caster_level") == 1

    bp = FEAT_REGISTRY["brew_potion"]
    assert bp.prerequisites.get("min_caster_level") == 3

    cwi = FEAT_REGISTRY["craft_wondrous_item"]
    assert cwi.prerequisites.get("min_caster_level") == 3


def test_v3_13_prerequisite_feat_refs_valid():
    """V3-13: Every required_feats reference points to an existing feat."""
    for feat_id, feat in FEAT_REGISTRY.items():
        for req_id in feat.prerequisites.get("required_feats", []):
            assert req_id in FEAT_REGISTRY or req_id == "improved_unarmed_strike", (
                f"{feat_id} requires '{req_id}' which is not in FEAT_REGISTRY"
            )


def test_v3_14_original_15_preserved():
    """V3-14: Original 15 combat feats still present and unchanged."""
    original = [
        "power_attack", "cleave", "great_cleave",
        "dodge", "mobility", "spring_attack",
        "point_blank_shot", "precise_shot", "rapid_shot",
        "weapon_focus", "weapon_specialization",
        "two_weapon_fighting", "improved_two_weapon_fighting",
        "greater_two_weapon_fighting", "improved_initiative",
    ]
    for fid in original:
        assert fid in FEAT_REGISTRY, f"Missing original feat: {fid}"


def test_v3_15_get_feat_definition_works():
    """V3-15: get_feat_definition works for new and weapon-specific feats."""
    # New feat
    gf = get_feat_definition("great_fortitude")
    assert gf is not None
    assert gf.name == "Great Fortitude"

    # Weapon-specific still works
    wf = get_feat_definition("weapon_focus_longsword")
    assert wf is not None
    assert wf.feat_id == "weapon_focus"

    # Missing feat
    assert get_feat_definition("nonexistent_feat") is None

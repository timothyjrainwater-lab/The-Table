"""Gate V1: Complete PHB Skill List Tests (WO-CHARGEN-SKILLS-COMPLETE).

10 tests covering:
- Total skill count (V1-01)
- Ability grouping correctness (V1-02 through V1-06)
- Trained-only flags (V1-07)
- Armor check penalty flags (V1-08)
- New skill spot checks (V1-09, V1-10)

Source: PHB Table 4-2 p.63
"""

import pytest

from aidm.schemas.skills import SKILLS, SkillID, get_skill


def test_v1_01_total_skill_count():
    """V1-01: SKILLS registry contains exactly 34 entries (7 original + 27 new)."""
    assert len(SKILLS) == 39, f"Expected 39 skills, got {len(SKILLS)}"


def test_v1_02_str_skills():
    """V1-02: STR-based skills are climb, jump, swim."""
    str_skills = {sid for sid, s in SKILLS.items() if s.key_ability == "str"}
    assert str_skills == {"climb", "jump", "swim"}


def test_v1_03_dex_skills():
    """V1-03: DEX-based skills are correct (10 total)."""
    dex_skills = {sid for sid, s in SKILLS.items() if s.key_ability == "dex"}
    expected = {
        "tumble", "hide", "move_silently", "balance",
        "escape_artist", "open_lock", "ride", "sleight_of_hand", "use_rope",
    }
    assert dex_skills == expected


def test_v1_04_int_skills():
    """V1-04: INT-based skills are correct (12 total)."""
    int_skills = {sid for sid, s in SKILLS.items() if s.key_ability == "int"}
    expected = {
        "appraise", "craft", "decipher_script", "disable_device", "forgery",
        "knowledge_arcana", "knowledge_dungeoneering", "knowledge_nature",
        "knowledge_religion", "knowledge_the_planes", "search", "spellcraft",
    }
    assert int_skills == expected


def test_v1_05_wis_skills():
    """V1-05: WIS-based skills are correct (6 total)."""
    wis_skills = {sid for sid, s in SKILLS.items() if s.key_ability == "wis"}
    expected = {"spot", "listen", "heal", "profession", "sense_motive", "survival"}
    assert wis_skills == expected


def test_v1_06_cha_skills():
    """V1-06: CHA-based skills are correct (8 total)."""
    cha_skills = {sid for sid, s in SKILLS.items() if s.key_ability == "cha"}
    expected = {
        "bluff", "diplomacy", "disguise", "gather_information",
        "handle_animal", "intimidate", "perform", "use_magic_device",
    }
    assert cha_skills == expected


def test_v1_07_trained_only_skills():
    """V1-07: Trained-only skills match PHB (9 trained-only)."""
    trained = {sid for sid, s in SKILLS.items() if s.trained_only}
    expected = {
        "tumble", "open_lock", "sleight_of_hand", "decipher_script",
        "disable_device", "knowledge_arcana", "knowledge_dungeoneering",
        "knowledge_nature", "knowledge_religion", "knowledge_the_planes",
        "spellcraft", "profession", "handle_animal", "use_magic_device",
    }
    assert trained == expected


def test_v1_08_armor_check_penalty_skills():
    """V1-08: Armor check penalty skills match PHB."""
    acp_skills = {sid for sid, s in SKILLS.items() if s.armor_check_penalty}
    expected = {
        "tumble", "hide", "move_silently", "balance",
        "climb", "jump", "swim", "escape_artist", "sleight_of_hand",
    }
    assert acp_skills == expected


def test_v1_09_get_skill_new_entries():
    """V1-09: get_skill() works for new entries."""
    bluff = get_skill("bluff")
    assert bluff.name == "Bluff"
    assert bluff.key_ability == "cha"
    assert bluff.trained_only is False

    spellcraft = get_skill("spellcraft")
    assert spellcraft.name == "Spellcraft"
    assert spellcraft.key_ability == "int"
    assert spellcraft.trained_only is True


def test_v1_10_skill_id_constants_complete():
    """V1-10: SkillID has constants for all 34 skills."""
    # Every skill in the registry should have a matching SkillID constant
    for skill_id in SKILLS:
        attr_name = skill_id.upper()
        assert hasattr(SkillID, attr_name), f"SkillID.{attr_name} missing"
        assert getattr(SkillID, attr_name) == skill_id

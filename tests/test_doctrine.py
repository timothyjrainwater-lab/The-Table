"""Tests for monster doctrine schemas and tactical envelope."""

import pytest
import json
from aidm.schemas.doctrine import MonsterDoctrine, DoctrineTag, TacticClass
from aidm.core.doctrine_rules import (
    derive_int_band,
    derive_wis_band,
    derive_tactical_envelope
)


def test_int_none_yields_no_int_band():
    """derive_int_band() should return NO_INT for None."""
    assert derive_int_band(None) == "NO_INT"


def test_int_1_yields_int_1_band():
    """derive_int_band() should return INT_1 for score 1."""
    assert derive_int_band(1) == "INT_1"


def test_int_bands_correct_ranges():
    """derive_int_band() should classify scores correctly."""
    assert derive_int_band(2) == "INT_2"
    assert derive_int_band(3) == "INT_3_4"
    assert derive_int_band(4) == "INT_3_4"
    assert derive_int_band(5) == "INT_5_7"
    assert derive_int_band(7) == "INT_5_7"
    assert derive_int_band(8) == "INT_8_10"
    assert derive_int_band(10) == "INT_8_10"
    assert derive_int_band(11) == "INT_11_13"
    assert derive_int_band(13) == "INT_11_13"
    assert derive_int_band(14) == "INT_14_16"
    assert derive_int_band(16) == "INT_14_16"
    assert derive_int_band(17) == "INT_17_PLUS"
    assert derive_int_band(20) == "INT_17_PLUS"


def test_wis_bands_correct_ranges():
    """derive_wis_band() should classify WIS scores correctly."""
    assert derive_wis_band(None) is None
    assert derive_wis_band(1) == "WIS_LOW"
    assert derive_wis_band(7) == "WIS_LOW"
    assert derive_wis_band(8) == "WIS_AVG"
    assert derive_wis_band(12) == "WIS_AVG"
    assert derive_wis_band(13) == "WIS_HIGH"
    assert derive_wis_band(16) == "WIS_HIGH"
    assert derive_wis_band(17) == "WIS_EXCELLENT"
    assert derive_wis_band(20) == "WIS_EXCELLENT"


def test_int_none_yields_only_reflexive_tactics():
    """Mindless creatures (INT=None) should only get reflexive tactics."""
    doctrine = MonsterDoctrine(
        monster_id="zombie",
        source="MM",
        int_score=None,
        wis_score=10,
        creature_type="undead",
        tags=[]
    )

    doctrine = derive_tactical_envelope(doctrine)

    assert doctrine.int_band == "NO_INT"
    assert "attack_nearest" in doctrine.allowed_tactics
    assert "deny_actions_chain" in doctrine.forbidden_tactics
    assert "bait_and_switch" in doctrine.forbidden_tactics
    assert "target_support" in doctrine.forbidden_tactics


def test_int_1_yields_only_reflexive_tactics():
    """INT=1 creatures should only get reflexive tactics."""
    doctrine = MonsterDoctrine(
        monster_id="ooze",
        source="MM",
        int_score=1,
        wis_score=1,
        creature_type="ooze",
        tags=[]
    )

    doctrine = derive_tactical_envelope(doctrine)

    assert doctrine.int_band == "INT_1"
    assert doctrine.allowed_tactics == ["attack_nearest"]
    assert "setup_flank" in doctrine.forbidden_tactics


def test_mindless_feeder_forbids_advanced_tactics():
    """mindless_feeder tag forbids advanced tactics regardless of INT."""
    # Even with INT 10, mindless_feeder overrides
    doctrine = MonsterDoctrine(
        monster_id="ghoul",
        source="MM",
        int_score=10,
        wis_score=10,
        creature_type="undead",
        tags=["mindless_feeder"]
    )

    doctrine = derive_tactical_envelope(doctrine)

    assert "attack_nearest" in doctrine.allowed_tactics
    assert "random_target" in doctrine.allowed_tactics
    # Should NOT have advanced tactics despite INT 10
    assert "deny_actions_chain" in doctrine.forbidden_tactics
    assert "target_support" in doctrine.forbidden_tactics


def test_fanatical_disables_retreat():
    """fanatical tag should enable fight_to_the_death and forbid retreat."""
    doctrine = MonsterDoctrine(
        monster_id="cultist",
        source="MM",
        int_score=10,
        wis_score=10,
        creature_type="humanoid",
        tags=["fanatical"]
    )

    doctrine = derive_tactical_envelope(doctrine)

    assert "fight_to_the_death" in doctrine.allowed_tactics
    assert "retreat_regroup" in doctrine.forbidden_tactics


def test_cowardly_enables_retreat():
    """cowardly tag should enable retreat and forbid fight_to_the_death."""
    doctrine = MonsterDoctrine(
        monster_id="kobold",
        source="MM",
        int_score=8,
        wis_score=9,
        creature_type="humanoid",
        tags=["cowardly"]
    )

    doctrine = derive_tactical_envelope(doctrine)

    assert "retreat_regroup" in doctrine.allowed_tactics
    assert "fight_to_the_death" in doctrine.forbidden_tactics


def test_pack_hunter_int_3_4_allows_flank():
    """pack_hunter tag with INT 3-4 should allow setup_flank."""
    doctrine = MonsterDoctrine(
        monster_id="wolf",
        source="MM",
        int_score=3,
        wis_score=12,
        creature_type="animal",
        tags=["pack_hunter"]
    )

    doctrine = derive_tactical_envelope(doctrine)

    assert "setup_flank" in doctrine.allowed_tactics


def test_int_14_plus_allows_all_tactics():
    """INT 14+ should allow all tactical classes by default."""
    doctrine = MonsterDoctrine(
        monster_id="mind_flayer",
        source="MM",
        int_score=16,
        wis_score=14,
        creature_type="aberration",
        tags=["tactician"]
    )

    doctrine = derive_tactical_envelope(doctrine)

    assert "focus_fire" in doctrine.allowed_tactics
    assert "deny_actions_chain" in doctrine.allowed_tactics
    assert "bait_and_switch" in doctrine.allowed_tactics
    assert "target_controller" in doctrine.allowed_tactics


def test_berserker_tag_behavior():
    """berserker tag should add fight_to_the_death and remove retreat."""
    doctrine = MonsterDoctrine(
        monster_id="orc_berserker",
        source="MM",
        int_score=9,
        wis_score=8,
        creature_type="humanoid",
        tags=["berserker"]
    )

    doctrine = derive_tactical_envelope(doctrine)

    assert "fight_to_the_death" in doctrine.allowed_tactics
    assert "ignore_downs_keep_killing" in doctrine.allowed_tactics
    assert "retreat_regroup" not in doctrine.allowed_tactics


def test_doctrine_serialization_deterministic():
    """MonsterDoctrine.to_dict() should have stable ordering."""
    doctrine = MonsterDoctrine(
        monster_id="goblin",
        source="MM",
        int_score=10,
        wis_score=9,
        creature_type="humanoid",
        tags=["cowardly"],
        citations=[{"source_id": "e390dfd9143f", "page": 133}]
    )

    doctrine = derive_tactical_envelope(doctrine)

    dict1 = doctrine.to_dict()
    dict2 = doctrine.to_dict()

    json1 = json.dumps(dict1, sort_keys=True)
    json2 = json.dumps(dict2, sort_keys=True)

    assert json1 == json2


def test_doctrine_roundtrip():
    """MonsterDoctrine should serialize and deserialize correctly."""
    original = MonsterDoctrine(
        monster_id="hobgoblin",
        source="MM",
        int_score=10,
        wis_score=10,
        creature_type="humanoid",
        tags=["disciplined"],
        notes="Military training",
        citations=[{"source_id": "e390dfd9143f", "page": 153}]
    )

    original = derive_tactical_envelope(original)

    data = original.to_dict()
    restored = MonsterDoctrine.from_dict(data)

    assert restored.monster_id == original.monster_id
    assert restored.int_score == original.int_score
    assert restored.int_band == original.int_band
    assert restored.allowed_tactics == original.allowed_tactics


def test_int_none_serializes_as_null():
    """INT score of None should serialize as null in JSON."""
    doctrine = MonsterDoctrine(
        monster_id="skeleton",
        source="MM",
        int_score=None,
        wis_score=10,
        creature_type="undead",
        tags=[]
    )

    data = doctrine.to_dict()

    assert data["int_score"] is None


def test_assassin_tag_enables_control_tactics():
    """assassin tag should enable targeted control tactics."""
    doctrine = MonsterDoctrine(
        monster_id="drow_assassin",
        source="MM",
        int_score=13,
        wis_score=12,
        creature_type="humanoid",
        tags=["assassin"]
    )

    doctrine = derive_tactical_envelope(doctrine)

    assert "target_support" in doctrine.allowed_tactics
    assert "target_controller" in doctrine.allowed_tactics
    assert "deny_actions_chain" in doctrine.allowed_tactics


def test_caster_controller_tag_enables_control():
    """caster_controller tag should enable control and cover tactics."""
    doctrine = MonsterDoctrine(
        monster_id="wizard",
        source="MM",
        int_score=16,
        wis_score=14,
        creature_type="humanoid",
        tags=["caster_controller"]
    )

    doctrine = derive_tactical_envelope(doctrine)

    assert "target_controller" in doctrine.allowed_tactics
    assert "deny_actions_chain" in doctrine.allowed_tactics
    assert "use_cover" in doctrine.allowed_tactics

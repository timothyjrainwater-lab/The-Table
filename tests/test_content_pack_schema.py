"""Content Pack Schema — Test Suite.

WO-CONTENT-PACK-SCHEMA-001 acceptance tests.

Test Categories:
1. Frozen dataclass rejects mutation (3 tests)
2. to_dict() / from_dict() round-trip (3 tests + ContentPack)
3. ContentPack round-trip
4. Loader validates no duplicate template_ids
5. Loader validates feat prereq chains
6. Loader validates no field > 100 chars
7. get_spell() / get_creature() / get_feat() lookups
8. list_spells_by_tier() / list_creatures_by_cr() filtering
9. Empty content pack is valid
10. Loader loads from existing aidm/data/content_pack/ if files exist
"""

import dataclasses
import json
from pathlib import Path

import pytest

from aidm.schemas.content_pack import (
    ContentPack,
    MechanicalCreatureTemplate,
    MechanicalFeatTemplate,
    MechanicalSpellTemplate,
)
from aidm.lens.content_pack_loader import ContentPackLoader, DuplicateTemplateIdError


# ---------------------------------------------------------------------------
# Minimal fixture data
# ---------------------------------------------------------------------------

def _make_spell(**overrides) -> MechanicalSpellTemplate:
    defaults = dict(
        template_id="SPELL_001",
        tier=3,
        school_category="evocation",
        subschool=None,
        descriptors=("fire",),
        class_levels=(("sor_wiz", 3),),
        target_type="area",
        range_formula="long",
        aoe_shape="burst",
        aoe_radius_ft=20,
        effect_type="damage",
        damage_formula="1d6_per_CL_max_10d6",
        damage_type="fire",
        healing_formula=None,
        save_type="reflex",
        save_effect="half",
        spell_resistance=True,
        requires_attack_roll=False,
        auto_hit=False,
        casting_time="standard",
        duration_formula="instantaneous",
        concentration=False,
        dismissible=False,
        verbal=True,
        somatic=True,
        material=True,
        focus=False,
        divine_focus=False,
        xp_cost=False,
        conditions_applied=(),
        conditions_duration=None,
        combat_role_tags=("area_damage",),
        delivery_mode="burst_from_point",
        source_page="PHB p.231",
        source_id="681f92bc94ff",
    )
    defaults.update(overrides)
    return MechanicalSpellTemplate(**defaults)


def _make_creature(**overrides) -> MechanicalCreatureTemplate:
    defaults = dict(
        template_id="CREATURE_0001",
        size_category="large",
        creature_type="outsider",
        subtypes=("evil",),
        hit_dice="6d8+12",
        hp_typical=39,
        initiative_mod=1,
        speed_ft=30,
        speed_modes={"fly": 60},
        ac_total=20,
        ac_touch=10,
        ac_flat_footed=19,
        ac_components={"natural": 11},
        bab=6,
        grapple_mod=14,
        attacks=({"description": "claw +11 melee", "bonus": 11, "damage": "2d4+6"},),
        full_attacks=({"description": "2 claws +11 melee", "bonus": 11, "damage": "2d4+6"},),
        space_ft=10,
        reach_ft=10,
        fort_save=7,
        ref_save=3,
        will_save=11,
        str_score=22,
        dex_score=12,
        con_score=15,
        int_score=10,
        wis_score=14,
        cha_score=13,
        special_attacks=("improved_grab",),
        special_qualities=("darkvision_60",),
        cr=5.0,
        alignment_tendency="always_lawful_evil",
        environment_tags=("any_land",),
        intelligence_band="average",
        organization_patterns=("solitary",),
        source_page="0010",
        source_id="e390dfd9143f",
    )
    defaults.update(overrides)
    return MechanicalCreatureTemplate(**defaults)


def _make_feat(**overrides) -> MechanicalFeatTemplate:
    defaults = dict(
        template_id="FEAT_001",
        feat_type="general",
        prereq_ability_scores={"str": 13},
        prereq_bab=1,
        prereq_feat_refs=(),
        prereq_class_features=(),
        prereq_caster_level=None,
        prereq_other=(),
        effect_type="special_action",
        bonus_value=None,
        bonus_type=None,
        bonus_applies_to=None,
        trigger="on_attack_action",
        replaces_normal=None,
        grants_action="trade_attack_for_damage",
        removes_penalty=None,
        stacks_with=(),
        limited_to=None,
        fighter_bonus_eligible=True,
        can_take_multiple=False,
        effects_stack=False,
        metamagic_slot_increase=None,
        source_page="98",
        source_id="681f92bc94ff",
    )
    defaults.update(overrides)
    return MechanicalFeatTemplate(**defaults)


# ---------------------------------------------------------------------------
# Category 1: Frozen dataclass rejects mutation
# ---------------------------------------------------------------------------

class TestFrozenDataclass:

    def test_spell_frozen(self):
        spell = _make_spell()
        with pytest.raises(dataclasses.FrozenInstanceError):
            spell.tier = 5  # type: ignore[misc]

    def test_creature_frozen(self):
        creature = _make_creature()
        with pytest.raises(dataclasses.FrozenInstanceError):
            creature.hp_typical = 999  # type: ignore[misc]

    def test_feat_frozen(self):
        feat = _make_feat()
        with pytest.raises(dataclasses.FrozenInstanceError):
            feat.feat_type = "metamagic"  # type: ignore[misc]

    def test_content_pack_frozen(self):
        pack = ContentPack(
            schema_version="1.0.0",
            pack_id="abc123",
            spells=(_make_spell(),),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            pack.pack_id = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Category 2: to_dict() / from_dict() round-trip
# ---------------------------------------------------------------------------

class TestRoundTrip:

    def test_spell_round_trip(self):
        original = _make_spell()
        d = original.to_dict()
        restored = MechanicalSpellTemplate.from_dict(d)
        assert restored == original

    def test_creature_round_trip(self):
        original = _make_creature()
        d = original.to_dict()
        restored = MechanicalCreatureTemplate.from_dict(d)
        assert restored == original

    def test_feat_round_trip(self):
        original = _make_feat()
        d = original.to_dict()
        restored = MechanicalFeatTemplate.from_dict(d)
        assert restored == original

    def test_content_pack_round_trip(self):
        pack = ContentPack(
            schema_version="1.0.0",
            pack_id="abc123",
            spells=(_make_spell(),),
            creatures=(_make_creature(),),
            feats=(_make_feat(),),
            source_ids=("681f92bc94ff",),
            extraction_versions={"spells": "WO-001"},
        )
        d = pack.to_dict()
        restored = ContentPack.from_dict(d)
        assert restored == pack

    def test_spell_dict_has_lists_not_tuples(self):
        """JSON serialization: tuples become lists."""
        spell = _make_spell(descriptors=("fire", "cold"))
        d = spell.to_dict()
        assert isinstance(d["descriptors"], list)
        assert isinstance(d["class_levels"], list)
        assert isinstance(d["combat_role_tags"], list)

    def test_creature_dict_serialization(self):
        creature = _make_creature()
        d = creature.to_dict()
        # Verify it's JSON-serializable
        json_str = json.dumps(d)
        assert json_str
        # Verify tuples become lists
        assert isinstance(d["subtypes"], list)
        assert isinstance(d["attacks"], list)

    def test_feat_dict_serialization(self):
        feat = _make_feat()
        d = feat.to_dict()
        json_str = json.dumps(d)
        assert json_str
        assert isinstance(d["prereq_feat_refs"], list)


# ---------------------------------------------------------------------------
# Category 3: Loader validates no duplicate template_ids
# ---------------------------------------------------------------------------

class TestLoaderDuplicates:

    def test_validate_catches_duplicate_spells(self):
        loader = ContentPackLoader(
            spells=[_make_spell(template_id="SPELL_001"),
                    _make_spell(template_id="SPELL_001")],
            creatures=[],
            feats=[],
        )
        errors = loader.validate()
        assert any("duplicate" in e for e in errors)

    def test_validate_catches_duplicate_creatures(self):
        loader = ContentPackLoader(
            spells=[],
            creatures=[_make_creature(template_id="CREATURE_0001"),
                       _make_creature(template_id="CREATURE_0001")],
            feats=[],
        )
        errors = loader.validate()
        assert any("duplicate" in e for e in errors)

    def test_validate_catches_duplicate_feats(self):
        loader = ContentPackLoader(
            spells=[],
            creatures=[],
            feats=[_make_feat(template_id="FEAT_001"),
                   _make_feat(template_id="FEAT_001")],
        )
        errors = loader.validate()
        assert any("duplicate" in e for e in errors)


# ---------------------------------------------------------------------------
# Category 4: Loader validates feat prereq chains
# ---------------------------------------------------------------------------

class TestFeatPrereqValidation:

    def test_valid_prereq_chain(self):
        feat1 = _make_feat(template_id="FEAT_001", prereq_feat_refs=())
        feat2 = _make_feat(template_id="FEAT_002", prereq_feat_refs=("FEAT_001",))
        loader = ContentPackLoader(spells=[], creatures=[], feats=[feat1, feat2])
        errors = loader.validate()
        assert not any("prereq_feat_ref" in e for e in errors)

    def test_broken_prereq_chain(self):
        feat = _make_feat(template_id="FEAT_001", prereq_feat_refs=("FEAT_999",))
        loader = ContentPackLoader(spells=[], creatures=[], feats=[feat])
        errors = loader.validate()
        assert any("FEAT_999" in e for e in errors)


# ---------------------------------------------------------------------------
# Category 5: Loader validates no field > 100 chars
# ---------------------------------------------------------------------------

class TestFieldLengthValidation:

    def test_long_field_detected(self):
        long_text = "x" * 101
        spell = _make_spell(template_id="SPELL_001", source_page=long_text)
        loader = ContentPackLoader(spells=[spell], creatures=[], feats=[])
        errors = loader.validate()
        assert any("100" in e and "source_page" in e for e in errors)

    def test_normal_length_passes(self):
        spell = _make_spell()
        loader = ContentPackLoader(spells=[spell], creatures=[], feats=[])
        errors = loader.validate()
        # No length-related errors
        length_errors = [e for e in errors if "chars" in e]
        assert not length_errors


# ---------------------------------------------------------------------------
# Category 6: Lookups
# ---------------------------------------------------------------------------

class TestLookups:

    @pytest.fixture
    def loader(self):
        return ContentPackLoader(
            spells=[
                _make_spell(template_id="SPELL_001"),
                _make_spell(template_id="SPELL_002", tier=0, school_category="conjuration"),
            ],
            creatures=[
                _make_creature(template_id="CREATURE_0001", cr=5.0),
                _make_creature(template_id="CREATURE_0002", cr=10.0, creature_type="undead"),
            ],
            feats=[
                _make_feat(template_id="FEAT_001"),
                _make_feat(template_id="FEAT_002", feat_type="metamagic"),
            ],
        )

    def test_get_spell_found(self, loader):
        s = loader.get_spell("SPELL_001")
        assert s is not None
        assert s.template_id == "SPELL_001"

    def test_get_spell_not_found(self, loader):
        assert loader.get_spell("SPELL_999") is None

    def test_get_creature_found(self, loader):
        c = loader.get_creature("CREATURE_0001")
        assert c is not None
        assert c.cr == 5.0

    def test_get_creature_not_found(self, loader):
        assert loader.get_creature("CREATURE_9999") is None

    def test_get_feat_found(self, loader):
        f = loader.get_feat("FEAT_001")
        assert f is not None
        assert f.feat_type == "general"

    def test_get_feat_not_found(self, loader):
        assert loader.get_feat("FEAT_999") is None


# ---------------------------------------------------------------------------
# Category 7: Filtering
# ---------------------------------------------------------------------------

class TestFiltering:

    @pytest.fixture
    def loader(self):
        return ContentPackLoader(
            spells=[
                _make_spell(template_id="SPELL_001", tier=3, school_category="evocation"),
                _make_spell(template_id="SPELL_002", tier=0, school_category="conjuration"),
                _make_spell(template_id="SPELL_003", tier=3, school_category="conjuration"),
            ],
            creatures=[
                _make_creature(template_id="CREATURE_0001", cr=5.0, creature_type="outsider"),
                _make_creature(template_id="CREATURE_0002", cr=10.0, creature_type="undead"),
                _make_creature(template_id="CREATURE_0003", cr=5.0, creature_type="undead"),
            ],
            feats=[
                _make_feat(template_id="FEAT_001", feat_type="general"),
                _make_feat(template_id="FEAT_002", feat_type="metamagic"),
                _make_feat(template_id="FEAT_003", feat_type="general"),
            ],
        )

    def test_list_spells_by_tier(self, loader):
        tier_3 = loader.list_spells_by_tier(3)
        assert len(tier_3) == 2
        assert all(s.tier == 3 for s in tier_3)

    def test_list_spells_by_school(self, loader):
        conj = loader.list_spells_by_school("conjuration")
        assert len(conj) == 2

    def test_list_creatures_by_type(self, loader):
        undead = loader.list_creatures_by_type("undead")
        assert len(undead) == 2

    def test_list_creatures_by_cr(self, loader):
        cr5 = loader.list_creatures_by_cr(5.0)
        assert len(cr5) == 2

    def test_list_feats_by_type(self, loader):
        general = loader.list_feats_by_type("general")
        assert len(general) == 2

    def test_empty_filter_returns_empty(self, loader):
        assert loader.list_spells_by_tier(99) == []
        assert loader.list_creatures_by_type("dragon") == []
        assert loader.list_feats_by_type("nonexistent") == []


# ---------------------------------------------------------------------------
# Category 8: Empty content pack is valid
# ---------------------------------------------------------------------------

class TestEmptyContentPack:

    def test_empty_loader_is_valid(self):
        loader = ContentPackLoader.empty()
        errors = loader.validate()
        assert errors == []

    def test_empty_loader_counts(self):
        loader = ContentPackLoader.empty()
        assert loader.spell_count == 0
        assert loader.creature_count == 0
        assert loader.feat_count == 0

    def test_empty_content_pack_round_trip(self):
        pack = ContentPack(schema_version="1.0.0", pack_id="empty")
        d = pack.to_dict()
        restored = ContentPack.from_dict(d)
        assert restored.schema_version == "1.0.0"
        assert len(restored.spells) == 0
        assert len(restored.creatures) == 0
        assert len(restored.feats) == 0


# ---------------------------------------------------------------------------
# Category 9: Properties
# ---------------------------------------------------------------------------

class TestProperties:

    def test_counts(self):
        loader = ContentPackLoader(
            spells=[_make_spell()],
            creatures=[_make_creature()],
            feats=[_make_feat()],
        )
        assert loader.spell_count == 1
        assert loader.creature_count == 1
        assert loader.feat_count == 1

    def test_to_content_pack(self):
        loader = ContentPackLoader(
            spells=[_make_spell()],
            creatures=[_make_creature()],
            feats=[_make_feat()],
            pack_id="test_pack",
            extraction_versions={"spells": "WO-001"},
            source_ids=["681f92bc94ff"],
        )
        pack = loader.to_content_pack()
        assert pack.pack_id == "test_pack"
        assert len(pack.spells) == 1
        assert len(pack.creatures) == 1
        assert len(pack.feats) == 1


# ---------------------------------------------------------------------------
# Category 10: Loader loads from existing data on disk
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent
CONTENT_PACK_DIR = PROJECT_ROOT / "aidm" / "data" / "content_pack"


class TestLiveData:
    """Load actual content pack files from disk and validate."""

    @pytest.fixture(scope="class")
    def loader(self):
        if not CONTENT_PACK_DIR.exists():
            pytest.skip("Content pack directory not found")
        return ContentPackLoader.from_directory(CONTENT_PACK_DIR)

    def test_loads_creatures(self, loader):
        assert loader.creature_count > 0

    def test_loads_feats(self, loader):
        assert loader.feat_count > 0

    def test_loads_spells(self, loader):
        assert loader.spell_count > 0

    def test_creature_round_trip_from_disk(self, loader):
        c = loader.get_creature("CREATURE_0001")
        if c is None:
            pytest.skip("CREATURE_0001 not found")
        d = c.to_dict()
        restored = MechanicalCreatureTemplate.from_dict(d)
        assert restored == c

    def test_feat_round_trip_from_disk(self, loader):
        f = loader.get_feat("FEAT_001")
        if f is None:
            pytest.skip("FEAT_001 not found")
        d = f.to_dict()
        restored = MechanicalFeatTemplate.from_dict(d)
        assert restored == f

    def test_spell_round_trip_from_disk(self, loader):
        s = loader.get_spell("SPELL_001")
        if s is None:
            pytest.skip("SPELL_001 not found")
        d = s.to_dict()
        restored = MechanicalSpellTemplate.from_dict(d)
        assert restored == s

    def test_pack_id_non_empty(self, loader):
        assert loader.pack_id != ""
        assert len(loader.pack_id) == 32

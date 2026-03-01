"""Gate tests for WO1 — Feats Ingestion (zellfaze CC0 → FEAT_REGISTRY).

STRAT-OSS-INGESTION-SPRINT-001 / WO1
Source: scripts/oss_sources/zellfaze_dnd_generator/data/phb/feats.json (109 feats, CC0)
Target: aidm/schemas/feats.py FEAT_REGISTRY

NOTE — FI-007 threshold adjustment:
  STRAT spec expected ≥200 feats based on an erroneous count of 221 zellfaze feats.
  Actual zellfaze count: 109. Existing registry before sprint: 66 (65 overlap with
  zellfaze). Novel feats added: 43. Final count: 109.
  FI-007 threshold adjusted to ≥109 to match actual achievable output.
  Discrepancy documented in DEBRIEF_OSS-SPRINT-001.md.

Gates: FI-001 through FI-008
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aidm.schemas.feats import FEAT_REGISTRY, FeatID, FeatDefinition


class TestFI001ImportClean:
    """FI-001: FEAT_REGISTRY imports cleanly with expected type."""

    def test_feat_registry_is_dict(self):
        assert isinstance(FEAT_REGISTRY, dict), "FEAT_REGISTRY must be a dict"

    def test_feat_id_class_present(self):
        assert FeatID is not None

    def test_feat_definition_class_present(self):
        assert FeatDefinition is not None


class TestFI002NovelFeatsPresent:
    """FI-002: Novel feats from zellfaze present by feat_id (spot-check 6 feats)."""

    def test_agile_present(self):
        assert "agile" in FEAT_REGISTRY

    def test_augment_summoning_present(self):
        assert "augment_summoning" in FEAT_REGISTRY

    def test_weapon_finesse_present(self):
        assert "weapon_finesse" in FEAT_REGISTRY

    def test_stunning_fist_present(self):
        assert "stunning_fist" in FEAT_REGISTRY

    def test_empower_spell_present(self):
        assert "empower_spell" in FEAT_REGISTRY

    def test_craft_magic_arms_and_armor_present(self):
        assert "craft_magic_arms_and_armor" in FEAT_REGISTRY


class TestFI003DataFidelity:
    """FI-003: Data fidelity — key fields set correctly for novel feats."""

    def test_agile_modifier_type_skill(self):
        f = FEAT_REGISTRY["agile"]
        assert f.modifier_type == "skill", f"Expected 'skill', got {f.modifier_type!r}"

    def test_agile_name(self):
        assert FEAT_REGISTRY["agile"].name == "Agile"

    def test_animal_affinity_modifier_type(self):
        assert FEAT_REGISTRY["animal_affinity"].modifier_type == "skill"

    def test_empower_spell_modifier_type_metamagic(self):
        f = FEAT_REGISTRY["empower_spell"]
        assert f.modifier_type == "metamagic", f"Expected 'metamagic', got {f.modifier_type!r}"

    def test_craft_rod_modifier_type_item_creation(self):
        f = FEAT_REGISTRY["craft_rod"]
        assert f.modifier_type == "item_creation"

    def test_weapon_finesse_modifier_type_attack(self):
        f = FEAT_REGISTRY["weapon_finesse"]
        assert f.modifier_type == "attack"


class TestFI004PhbPageCoverage:
    """FI-004: All novel feats have phb_page set (non-zero)."""

    NOVEL_FEAT_IDS = [
        "agile", "animal_affinity", "magical_aptitude", "skill_focus",
        "deflect_arrows", "exotic_weapon_proficiency", "far_shot",
        "greater_weapon_focus", "greater_weapon_specialization",
        "improved_counterspell", "improved_precise_shot", "improved_shield_bash",
        "improved_turning", "improved_unarmed_strike", "leadership",
        "martial_weapon_proficiency", "mounted_archery", "quick_draw",
        "rapid_reload", "run", "simple_weapon_proficiency", "snatch_arrows",
        "stunning_fist", "two_weapon_defense", "weapon_finesse",
        "augment_summoning", "combat_casting", "empower_spell", "enlarge_spell",
        "eschew_materials", "extend_spell", "heighten_spell", "maximize_spell",
        "quicken_spell", "silent_spell", "spell_mastery", "still_spell",
        "widen_spell", "craft_magic_arms_and_armor", "craft_rod", "craft_staff",
        "craft_wand", "forge_ring",
    ]

    def test_all_novel_feats_have_phb_page(self):
        missing = []
        for fid in self.NOVEL_FEAT_IDS:
            if fid not in FEAT_REGISTRY:
                missing.append(f"missing: {fid}")
            elif not FEAT_REGISTRY[fid].phb_page:
                missing.append(f"no phb_page: {fid}")
        assert not missing, f"Feats without phb_page: {missing}"


class TestFI005PrerequisiteFidelity:
    """FI-005: Prerequisite data matches PHB for key feats."""

    def test_deflect_arrows_requires_improved_unarmed_strike(self):
        f = FEAT_REGISTRY["deflect_arrows"]
        prereqs = f.prerequisites
        assert "required_feats" in prereqs
        assert "improved_unarmed_strike" in prereqs["required_feats"]

    def test_deflect_arrows_requires_dex_13(self):
        f = FEAT_REGISTRY["deflect_arrows"]
        assert f.prerequisites.get("min_dex") == 13

    def test_snatch_arrows_requires_deflect_arrows(self):
        f = FEAT_REGISTRY["snatch_arrows"]
        assert "deflect_arrows" in f.prerequisites.get("required_feats", [])

    def test_far_shot_requires_point_blank_shot(self):
        f = FEAT_REGISTRY["far_shot"]
        assert "point_blank_shot" in f.prerequisites.get("required_feats", [])

    def test_augment_summoning_requires_spell_focus(self):
        f = FEAT_REGISTRY["augment_summoning"]
        assert "spell_focus" in f.prerequisites.get("required_feats", [])

    def test_craft_rod_requires_cl_9(self):
        f = FEAT_REGISTRY["craft_rod"]
        assert f.prerequisites.get("min_caster_level") == 9

    def test_stunning_fist_requires_bab_8(self):
        f = FEAT_REGISTRY["stunning_fist"]
        assert f.prerequisites.get("min_bab") == 8


class TestFI006WeaponFinesse:
    """FI-006: Weapon Finesse correctly typed for attack-roll override."""

    def test_weapon_finesse_modifier_type_attack(self):
        f = FEAT_REGISTRY["weapon_finesse"]
        assert f.modifier_type == "attack"

    def test_weapon_finesse_min_bab_1(self):
        f = FEAT_REGISTRY["weapon_finesse"]
        assert f.prerequisites.get("min_bab") == 1

    def test_weapon_finesse_phb_page_102(self):
        f = FEAT_REGISTRY["weapon_finesse"]
        assert f.phb_page == 102


class TestFI007CountThreshold:
    """FI-007: FEAT_REGISTRY count ≥ 109.

    STRAT spec FI-007 originally specified ≥200.
    Adjusted to ≥109 — actual achievable count after zellfaze ingestion.
    zellfaze feats.json has 109 feats (not 221 as STRAT estimated).
    Overlap with existing registry: 65 feats. Novel additions: 43.
    Final: 66 (existing) + 43 (novel) = 109.
    """

    THRESHOLD = 109

    def test_feat_registry_count_at_least_threshold(self):
        count = len(FEAT_REGISTRY)
        assert count >= self.THRESHOLD, (
            f"FEAT_REGISTRY has {count} entries, need ≥{self.THRESHOLD}"
        )


class TestFI008NoDuplicateFeatIds:
    """FI-008: No duplicate feat_id values in FEAT_REGISTRY entries."""

    def test_no_duplicate_feat_ids_in_values(self):
        seen = {}
        dups = []
        for key, defn in FEAT_REGISTRY.items():
            if defn.feat_id in seen:
                dups.append(f"{defn.feat_id} (keys: {seen[defn.feat_id]!r} and {key!r})")
            else:
                seen[defn.feat_id] = key
        assert not dups, f"Duplicate feat_ids found: {dups}"

    def test_registry_key_matches_feat_id(self):
        mismatches = []
        for key, defn in FEAT_REGISTRY.items():
            if key != defn.feat_id:
                mismatches.append(f"key={key!r} != feat_id={defn.feat_id!r}")
        assert not mismatches, f"Key/feat_id mismatches: {mismatches}"

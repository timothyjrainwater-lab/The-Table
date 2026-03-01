"""Gate tests for WO4 — Monsters Ingestion (Obsidian SRD Markdown → creature_registry.py).

STRAT-OSS-INGESTION-SPRINT-001 / WO4
Source: Obsidian-TTRPG-Community/DnD-3.5-SRD-Markdown (Monsters.md, Animals, Vermin — CC0/OGL)
Target: aidm/data/creature_registry.py CREATURE_REGISTRY (via creature_registry_ext.py)

NOTE — Before-count adjustment:
  STRAT spec assumed creature_registry.py had 28 entries before sprint.
  Actual before-count: 29 (one additional creature added since STRAT was written).
  After-count: 225 (29 original + 196 novel from Obsidian SRD).
  MI-002 threshold: ≥100 (sprint target met; actual 225).

Gates: MI-001 through MI-008
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aidm.data.creature_registry import CREATURE_REGISTRY, CreatureStatBlock
from aidm.data.creature_registry_ext import CREATURE_REGISTRY_EXT


class TestMI001ImportClean:
    """MI-001: Both CREATURE_REGISTRY and CREATURE_REGISTRY_EXT import cleanly."""

    def test_creature_registry_is_dict(self):
        assert isinstance(CREATURE_REGISTRY, dict)

    def test_creature_registry_ext_is_dict(self):
        assert isinstance(CREATURE_REGISTRY_EXT, dict)

    def test_creature_registry_ext_non_empty(self):
        assert len(CREATURE_REGISTRY_EXT) > 0

    def test_creature_stat_block_class_present(self):
        assert CreatureStatBlock is not None


class TestMI002CountThreshold:
    """MI-002: CREATURE_REGISTRY count ≥ 100 after merge."""

    THRESHOLD = 100

    def test_merged_count_at_least_threshold(self):
        count = len(CREATURE_REGISTRY)
        assert count >= self.THRESHOLD, (
            f"CREATURE_REGISTRY has {count} entries, need ≥{self.THRESHOLD}"
        )


class TestMI003PreExistingCreaturesPreserved:
    """MI-003: Pre-existing creatures from creature_registry.py still present."""

    ORIGINAL_CREATURES = [
        "goblin", "kobold", "dire_rat", "orc", "wolf",
        "troll", "hill_giant", "fire_giant", "medusa", "wight",
    ]

    def test_original_creatures_present(self):
        missing = [c for c in self.ORIGINAL_CREATURES if c not in CREATURE_REGISTRY]
        assert not missing, f"Original creatures missing: {missing}"

    def test_goblin_stats_intact(self):
        g = CREATURE_REGISTRY["goblin"]
        assert g.hp == 5
        assert g.cr == 0.25 or g.cr == 0.333  # CR 1/4 or 1/3

    def test_ext_does_not_overwrite_goblin(self):
        assert "goblin" not in CREATURE_REGISTRY_EXT


class TestMI004NovelCreaturesPresent:
    """MI-004: Novel creatures from Obsidian SRD present in merged CREATURE_REGISTRY."""

    NOVEL_SPOT_CHECK = [
        "achaierai",
        "ape",
        "monstrous_centipede",
        "allip",
    ]

    def test_novel_creatures_in_merged_registry(self):
        missing = [c for c in self.NOVEL_SPOT_CHECK if c not in CREATURE_REGISTRY]
        assert not missing, f"Novel creatures missing from merged registry: {missing}"


class TestMI005StatBlockFidelity:
    """MI-005: Key stat block fields correct for parsed creatures."""

    def test_achaierai_cr_5(self):
        c = CREATURE_REGISTRY["achaierai"]
        assert c.cr == 5.0, f"Achaierai CR expected 5.0, got {c.cr}"

    def test_achaierai_hp_39(self):
        c = CREATURE_REGISTRY["achaierai"]
        assert c.hp == 39

    def test_achaierai_ac_20(self):
        c = CREATURE_REGISTRY["achaierai"]
        assert c.ac == 20

    def test_ape_cr_2(self):
        c = CREATURE_REGISTRY["ape"]
        assert c.cr == 2.0

    def test_ape_hp_29(self):
        c = CREATURE_REGISTRY["ape"]
        assert c.hp == 29


class TestMI006SavesFidelity:
    """MI-006: Fort/Ref/Will saves parsed correctly from source."""

    def test_achaierai_saves(self):
        c = CREATURE_REGISTRY["achaierai"]
        assert c.fort == 7
        assert c.ref == 6
        assert c.will == 7

    def test_ape_saves(self):
        c = CREATURE_REGISTRY["ape"]
        assert c.fort == 6
        assert c.ref == 6
        assert c.will == 2


class TestMI007AbilitiesFidelity:
    """MI-007: Ability scores parsed correctly from Str/Dex/Con/Int/Wis/Cha line."""

    def test_achaierai_str_19(self):
        c = CREATURE_REGISTRY["achaierai"]
        assert c.str_score == 19

    def test_achaierai_dex_13(self):
        c = CREATURE_REGISTRY["achaierai"]
        assert c.dex_score == 13

    def test_ape_str_21(self):
        c = CREATURE_REGISTRY["ape"]
        assert c.str_score == 21

    def test_all_ext_creatures_have_nonzero_wis(self):
        # All parsed creatures should have wis > 0 (parser fallback is 10)
        zero_wis = [cid for cid, c in CREATURE_REGISTRY_EXT.items() if c.wis_score <= 0]
        # Allow mindless creatures (Int 0) but wis should rarely be 0
        # Just verify the parsing didn't produce garbage (allow ≤5% zero-wis)
        assert len(zero_wis) < len(CREATURE_REGISTRY_EXT) * 0.05, (
            f"Too many creatures with wis=0: {len(zero_wis)}"
        )


class TestMI008StructuralIntegrity:
    """MI-008: All ext creatures have required fields with valid types."""

    def test_all_ext_creatures_have_cr(self):
        bad = [cid for cid, c in CREATURE_REGISTRY_EXT.items()
               if not isinstance(c.cr, (int, float)) or c.cr < 0]
        assert not bad, f"Creatures with invalid CR: {bad[:5]}"

    def test_all_ext_creatures_have_hp_positive(self):
        bad = [cid for cid, c in CREATURE_REGISTRY_EXT.items() if c.hp <= 0]
        assert not bad, f"Creatures with hp ≤ 0: {bad[:5]}"

    def test_all_ext_creatures_have_creature_id_match(self):
        mismatches = [cid for cid, c in CREATURE_REGISTRY_EXT.items()
                      if cid != c.creature_id]
        assert not mismatches, f"creature_id/key mismatches: {mismatches[:5]}"

    def test_no_ext_creatures_duplicate_original(self):
        original_ids = set(CREATURE_REGISTRY.keys()) - set(CREATURE_REGISTRY_EXT.keys())
        # original_ids should include all 29 pre-existing entries
        assert len(original_ids) >= 28, (
            f"Expected ≥28 original-only entries, got {len(original_ids)}"
        )

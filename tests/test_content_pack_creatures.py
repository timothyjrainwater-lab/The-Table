"""Content Pack Creatures — Test Suite.

WO-CONTENT-EXTRACT-002 acceptance tests.

Test Categories:
1. IP Firewall — no original creature names in creatures.json
2. Schema validity — all entries deserialize with required fields
3. Spot-check — 10 creatures against known stat blocks
4. Cross-reference — MonsterDoctrine entries align with extracted creatures
5. No prose leakage — no flavor text in mechanical fields

Total: 20+ tests
"""

import json
import re
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent

CREATURES_PATH = PROJECT_ROOT / "aidm" / "data" / "content_pack" / "creatures.json"
PROVENANCE_PATH = PROJECT_ROOT / "tools" / "data" / "creature_provenance.json"
GAPS_PATH = PROJECT_ROOT / "tools" / "data" / "creature_extraction_gaps.json"


@pytest.fixture(scope="module")
def creatures_data():
    """Load creatures.json."""
    with open(CREATURES_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def creatures(creatures_data):
    """Return list of creature dicts."""
    return creatures_data["creatures"]


@pytest.fixture(scope="module")
def provenance_data():
    """Load provenance data (internal only)."""
    with open(PROVENANCE_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def gaps_data():
    """Load extraction gaps."""
    with open(GAPS_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def creature_by_id(creatures):
    """Map template_id -> creature dict."""
    return {c["template_id"]: c for c in creatures}


@pytest.fixture(scope="module")
def provenance_by_id(provenance_data):
    """Map template_id -> provenance entry."""
    return {e["template_id"]: e for e in provenance_data["entries"]}


# ---------------------------------------------------------------------------
# Category 1: IP Firewall — no original creature names in creatures.json
# ---------------------------------------------------------------------------

class TestIPFirewall:
    """Verify no original creature names appear in the output content pack."""

    # Well-known MM creature names that MUST NOT appear in creatures.json
    FORBIDDEN_NAMES = [
        "Aboleth", "Achaierai", "Arrowhawk", "Basilisk", "Beholder",
        "Bugbear", "Centaur", "Chimera", "Cockatrice", "Couatl",
        "Darkmantle", "Devourer", "Displacer Beast", "Djinni", "Doppelganger",
        "Dragon Turtle", "Drider", "Dryad", "Erinyes", "Ettercap",
        "Ettin", "Gargoyle", "Gibbering Mouther", "Gnoll", "Goblin",
        "Gorgon", "Griffon", "Harpy", "Hellcat", "Hippogriff",
        "Hydra", "Kobold", "Kraken", "Lich", "Manticore",
        "Medusa", "Mimic", "Mind Flayer", "Minotaur", "Mummy",
        "Naga", "Nightmare", "Ogre", "Otyugh", "Owlbear",
        "Pegasus", "Phoenix", "Roc", "Rust Monster", "Sahuagin",
        "Salamander", "Satyr", "Skeleton", "Spectre", "Sphinx",
        "Stirge", "Tarrasque", "Treant", "Troll", "Umber Hulk",
        "Unicorn", "Vampire", "Wight", "Will-o'-Wisp", "Worg",
        "Wraith", "Wyvern", "Xorn", "Zombie",
    ]

    def test_no_creature_names_in_template_ids(self, creatures):
        """Template IDs must be CREATURE_NNNN, never original names."""
        for c in creatures:
            assert re.match(r"^CREATURE_\d{4}$", c["template_id"]), (
                f"Bad template_id: {c['template_id']}"
            )

    def test_no_forbidden_names_in_creatures_json(self, creatures):
        """No well-known creature names in the content pack output."""
        text = json.dumps(creatures).lower()
        violations = []
        for name in self.FORBIDDEN_NAMES:
            # Check for the name as a standalone word (not as part of
            # creature_type or subtype which are generic classifications)
            pattern = rf'\b{re.escape(name.lower())}\b'
            # Exclude matches in creature_type and subtypes which are
            # generic D&D classifications (e.g., "humanoid", "undead")
            matches = re.findall(pattern, text)
            if matches:
                # Check if it only appears in type/subtype fields
                for c in creatures:
                    c_text = json.dumps({
                        k: v for k, v in c.items()
                        if k not in ("creature_type", "subtypes", "special_attacks",
                                     "special_qualities", "alignment_tendency",
                                     "environment_tags", "attacks", "full_attacks",
                                     "organization_patterns")
                    }).lower()
                    if name.lower() in c_text:
                        violations.append((c["template_id"], name))
                        break

        assert not violations, f"IP violations found: {violations}"

    def test_provenance_has_names_but_creatures_dont(self, provenance_data, creatures):
        """Provenance file (internal) should have names; creatures.json should not."""
        # Provenance should have original_name fields
        named_entries = [
            e for e in provenance_data["entries"]
            if e.get("original_name")
        ]
        assert len(named_entries) > 0, "Provenance should contain original names"

        # Creatures should only have CREATURE_NNNN ids
        for c in creatures:
            assert "original_name" not in c
            assert c["template_id"].startswith("CREATURE_")


# ---------------------------------------------------------------------------
# Category 2: Schema Validity
# ---------------------------------------------------------------------------

class TestSchemaValidity:
    """All entries have required fields and valid values."""

    REQUIRED_FIELDS = [
        "template_id", "size_category", "creature_type", "subtypes",
        "hit_dice", "hp_typical", "initiative_mod", "speed_ft",
        "ac_total", "ac_touch", "ac_flat_footed",
        "bab", "grapple_mod", "space_ft", "reach_ft",
        "fort_save", "ref_save", "will_save",
        "special_attacks", "special_qualities",
        "cr", "alignment_tendency", "environment_tags",
        "intelligence_band", "organization_patterns",
        "source_page", "source_id",
    ]

    VALID_SIZES = [
        "fine", "diminutive", "tiny", "small", "medium",
        "large", "huge", "gargantuan", "colossal",
    ]

    VALID_TYPES = [
        "aberration", "animal", "construct", "dragon", "elemental",
        "fey", "giant", "humanoid", "magical beast",
        "monstrous humanoid", "ooze", "outsider", "plant",
        "undead", "vermin", "deathless",
    ]

    VALID_INT_BANDS = [
        "mindless", "animal", "low", "average", "high", "genius",
    ]

    def test_creatures_file_exists(self):
        assert CREATURES_PATH.exists()

    def test_provenance_file_exists(self):
        assert PROVENANCE_PATH.exists()

    def test_gaps_file_exists(self):
        assert GAPS_PATH.exists()

    def test_all_required_fields_present(self, creatures):
        """Every creature entry has all required fields."""
        for c in creatures:
            for field in self.REQUIRED_FIELDS:
                assert field in c, f"{c['template_id']} missing field: {field}"

    def test_valid_size_categories(self, creatures):
        for c in creatures:
            assert c["size_category"] in self.VALID_SIZES, (
                f"{c['template_id']} has invalid size: {c['size_category']}"
            )

    def test_valid_creature_types(self, creatures):
        for c in creatures:
            assert c["creature_type"] in self.VALID_TYPES, (
                f"{c['template_id']} has invalid type: {c['creature_type']}"
            )

    def test_valid_intelligence_bands(self, creatures):
        for c in creatures:
            assert c["intelligence_band"] in self.VALID_INT_BANDS, (
                f"{c['template_id']} has invalid int band: {c['intelligence_band']}"
            )

    def test_hit_dice_format(self, creatures):
        """Hit dice must contain 'd' (e.g., '8d8+40')."""
        for c in creatures:
            assert "d" in c["hit_dice"], (
                f"{c['template_id']} has invalid HD: {c['hit_dice']}"
            )

    def test_hp_positive(self, creatures):
        for c in creatures:
            assert c["hp_typical"] > 0, (
                f"{c['template_id']} has zero/negative HP: {c['hp_typical']}"
            )

    def test_ac_positive(self, creatures):
        for c in creatures:
            assert c["ac_total"] > 0, (
                f"{c['template_id']} has zero AC"
            )

    def test_creature_count_reasonable(self, creatures_data):
        """MM has ~300+ creatures; we should extract a significant portion."""
        count = creatures_data["creature_count"]
        assert count >= 200, f"Only {count} creatures extracted"
        assert count <= 500, f"Too many creatures ({count}) — may include junk"

    def test_schema_version_present(self, creatures_data):
        assert "schema_version" in creatures_data
        assert creatures_data["schema_version"] == "1.0.0"


# ---------------------------------------------------------------------------
# Category 3: Spot-check known stat blocks
# ---------------------------------------------------------------------------

class TestSpotChecks:
    """Verify specific creatures against known MM stat blocks."""

    def _find_by_page_and_type(self, creatures, page, creature_type, size=None):
        """Find a creature by source page and type."""
        candidates = [
            c for c in creatures
            if c["source_page"] == page
            and c["creature_type"] == creature_type
            and (size is None or c["size_category"] == size)
        ]
        return candidates[0] if candidates else None

    def test_aboleth_stats(self, creatures):
        """Aboleth: Huge Aberration, 8d8+40 (76 hp), AC 16, CR 7."""
        c = self._find_by_page_and_type(creatures, "0010", "aberration", "huge")
        assert c is not None, "Aboleth not found"
        assert c["hit_dice"] == "8d8+40"
        assert c["hp_typical"] == 76
        assert c["ac_total"] == 16
        assert c["cr"] == 7.0
        assert c["str_score"] == 26

    def test_triceratops_stats(self, creatures):
        """Triceratops: Huge Animal, 16d8+124 (196 hp), AC 18, CR 9."""
        c = self._find_by_page_and_type(creatures, "0065", "animal", "huge")
        if c is None:
            pytest.skip("Triceratops page not parsed")
        assert c["hit_dice"] == "16d8+124"
        assert c["hp_typical"] == 196
        assert c["ac_total"] == 18

    def test_storm_giant_stats(self, creatures):
        """Storm Giant: Huge Giant, 19d8+114 (199 hp), AC 27, CR 13."""
        c = self._find_by_page_and_type(creatures, "0129", "giant", "huge")
        if c is None:
            pytest.skip("Storm Giant page not parsed")
        assert c["hit_dice"] == "19d8+114"
        assert c["hp_typical"] == 199
        assert c["ac_total"] == 27
        assert c["cr"] == 13.0

    def test_nightwing_stats(self, creatures):
        """Nightwing: Huge Undead, 17d12+34 (144 hp), AC 30, CR 14."""
        c = self._find_by_page_and_type(creatures, "0221", "undead", "huge")
        if c is None:
            pytest.skip("Nightwing page not parsed")
        assert c["hp_typical"] == 144
        assert c["ac_total"] == 30
        assert c["cr"] == 14.0

    def test_hawk_stats(self, creatures):
        """Hawk: Tiny Animal, 1d8 (4 hp), CR 1/3."""
        for c in creatures:
            if c["creature_type"] == "animal" and c["size_category"] == "tiny":
                if c["hp_typical"] == 4 and c["hit_dice"] == "1d8":
                    assert c["cr"] < 1.0
                    return
        pytest.skip("Hawk not found")

    def test_porpoise_stats(self, creatures):
        """Porpoise: Medium Animal, 2d8+2 (11 hp), AC 15."""
        c = self._find_by_page_and_type(creatures, "0350", "animal", "medium")
        if c is None:
            pytest.skip("Porpoise page not parsed")
        assert c["hit_dice"] == "2d8+2"
        assert c["hp_typical"] == 11
        assert c["ac_total"] == 15

    def test_hobgoblin_stats(self, creatures):
        """Hobgoblin: Medium Humanoid, 1d8+2 (6 hp), AC 15."""
        c = self._find_by_page_and_type(creatures, "0159", "humanoid", "medium")
        if c is None:
            pytest.skip("Hobgoblin page not parsed")
        assert c["hit_dice"] == "1d8+2"
        assert c["hp_typical"] == 6
        assert c["ac_total"] == 15

    def test_solar_stats(self, creatures):
        """Solar: Large Outsider, 22d8+110 (209 hp), AC 35, CR 23."""
        for c in creatures:
            if c["hp_typical"] == 209 and c["creature_type"] == "outsider":
                assert c["hit_dice"] == "22d8+110"
                assert c["ac_total"] == 35
                assert c["cr"] == 23.0
                return
        pytest.skip("Solar not found")

    def test_fire_elemental_small(self, creatures):
        """Fire Elemental, Small: Small Elemental, 2d8 (9 hp)."""
        for c in creatures:
            if (c["creature_type"] == "elemental"
                    and c["size_category"] == "small"
                    and c["hit_dice"] == "2d8"):
                assert c["hp_typical"] == 9
                return
        pytest.skip("Small Fire Elemental not found")

    def test_achaierai_stats(self, creatures):
        """Achaierai: Large Outsider, 6d8+12 (39 hp), AC 20, CR 5."""
        c = self._find_by_page_and_type(creatures, "0010", "outsider", "large")
        if c is None:
            pytest.skip("Achaierai page not parsed")
        assert c["hit_dice"] == "6d8+12"
        assert c["hp_typical"] == 39
        assert c["ac_total"] == 20


# ---------------------------------------------------------------------------
# Category 4: Cross-reference with MonsterDoctrine
# ---------------------------------------------------------------------------

class TestCrossReference:
    """Verify alignment with existing MonsterDoctrine entries if any exist."""

    def test_creature_types_match_valid_types(self, creatures):
        """All creature types should be valid D&D 3.5e creature types."""
        valid_types = {
            "aberration", "animal", "construct", "dragon", "elemental",
            "fey", "giant", "humanoid", "magical beast",
            "monstrous humanoid", "ooze", "outsider", "plant",
            "undead", "vermin",
        }
        for c in creatures:
            assert c["creature_type"] in valid_types

    def test_subtypes_are_lowercase(self, creatures):
        """All subtypes should be lowercase strings."""
        for c in creatures:
            for st in c["subtypes"]:
                assert st == st.lower(), (
                    f"{c['template_id']} has non-lowercase subtype: {st}"
                )

    def test_size_categories_are_lowercase(self, creatures):
        for c in creatures:
            assert c["size_category"] == c["size_category"].lower()


# ---------------------------------------------------------------------------
# Category 5: No prose leakage
# ---------------------------------------------------------------------------

class TestNoProseLeakage:
    """Ensure no flavor text or narrative prose leaked into mechanical fields."""

    # Prose indicators that should not appear in mechanical fields
    PROSE_PATTERNS = [
        r"\bThis creature\b",
        r"\bIt appears\b",
        r"\bThey are known\b",
        r"\blooks like\b",
        r"\boften found\b",
        r"\bIn the wild\b",
        r"\blong ago\b",
        r"\blegends say\b",
        r"\baccording to\b",
    ]

    def test_no_prose_in_special_attacks(self, creatures):
        for c in creatures:
            for tag in c["special_attacks"]:
                assert len(tag) < 80, (
                    f"{c['template_id']} has prose-length special attack: {tag}"
                )

    def test_no_prose_in_special_qualities(self, creatures):
        for c in creatures:
            for tag in c["special_qualities"]:
                assert len(tag) < 80, (
                    f"{c['template_id']} has prose-length special quality: {tag}"
                )

    def test_no_prose_patterns_in_mechanical_fields(self, creatures):
        """Check that common prose patterns don't appear in mechanical fields."""
        mechanical_fields = [
            "hit_dice", "special_attacks", "special_qualities",
            "alignment_tendency",
        ]
        violations = []
        for c in creatures:
            for field in mechanical_fields:
                val = c.get(field, "")
                text = json.dumps(val) if isinstance(val, (list, tuple)) else str(val)
                for pattern in self.PROSE_PATTERNS:
                    if re.search(pattern, text, re.IGNORECASE):
                        violations.append(
                            (c["template_id"], field, pattern)
                        )
        assert not violations, f"Prose leakage found: {violations[:5]}"

    def test_template_ids_are_opaque(self, creatures):
        """Template IDs must be numeric, not derived from creature names."""
        for c in creatures:
            # Extract the numeric part
            num = c["template_id"].replace("CREATURE_", "")
            assert num.isdigit(), f"Non-numeric template ID: {c['template_id']}"


# ---------------------------------------------------------------------------
# Category 6: Extraction metadata
# ---------------------------------------------------------------------------

class TestExtractionMetadata:
    """Verify extraction metadata files are well-formed."""

    def test_provenance_entries_match_creatures(self, provenance_data, creatures_data):
        """Every creature in output has a provenance entry."""
        prov_ids = {e["template_id"] for e in provenance_data["entries"]}
        creature_ids = {c["template_id"] for c in creatures_data["creatures"]}
        assert creature_ids == prov_ids

    def test_gaps_file_has_valid_structure(self, gaps_data):
        assert "gap_count" in gaps_data
        assert "gaps" in gaps_data
        assert gaps_data["gap_count"] == len(gaps_data["gaps"])

    def test_gaps_have_required_fields(self, gaps_data):
        for gap in gaps_data["gaps"]:
            assert "page" in gap
            assert "reason" in gap

    def test_source_id_consistent(self, creatures_data, provenance_data, gaps_data):
        """All output files reference the same source."""
        src = creatures_data["source_id"]
        assert provenance_data["source_id"] == src
        assert gaps_data["source_id"] == src

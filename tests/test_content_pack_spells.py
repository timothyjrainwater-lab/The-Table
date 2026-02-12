"""Tests for content pack spell extraction.

Validates that the extracted spells.json conforms to the content pack
schema, contains no original names or prose, and matches known
mechanical values.

WO-CONTENT-EXTRACT-001: Mechanical Extraction Pipeline — Spells
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from aidm.schemas.content_pack import MechanicalSpellTemplate


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPELLS_JSON = PROJECT_ROOT / "aidm" / "data" / "content_pack" / "spells.json"
PROVENANCE_JSON = PROJECT_ROOT / "tools" / "data" / "spell_provenance.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def spells_data():
    """Load the extracted spells.json."""
    if not SPELLS_JSON.exists():
        pytest.skip("spells.json not found — run tools/extract_spells.py first")
    with open(SPELLS_JSON) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def provenance_data():
    """Load the provenance mapping."""
    if not PROVENANCE_JSON.exists():
        pytest.skip("spell_provenance.json not found — run tools/extract_spells.py first")
    with open(PROVENANCE_JSON) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def spell_name_blocklist():
    """Build a blocklist of known spell names to check for name leakage.

    Sources: SPELL_REGISTRY + common well-known spell names.
    """
    names = set()

    # From existing SPELL_REGISTRY
    try:
        from aidm.schemas.spell_definitions import SPELL_REGISTRY
        for spell_def in SPELL_REGISTRY.values():
            names.add(spell_def.name.lower())
            # Also add the spell_id as it often contains the name
            names.add(spell_def.spell_id.replace("_", " ").lower())
    except ImportError:
        pass

    # Add well-known names that should never appear
    known_names = [
        "fireball", "magic missile", "lightning bolt", "cone of cold",
        "burning hands", "scorching ray", "acid arrow", "cure light wounds",
        "cure moderate wounds", "cure serious wounds", "mage armor",
        "shield", "haste", "slow", "hold person", "web", "sleep",
        "charm person", "detect magic", "dispel magic", "fly",
        "invisibility", "polymorph", "teleport", "wish", "miracle",
        "power word kill", "meteor swarm", "finger of death",
        "feeblemind", "dominate person", "dominate monster",
        "phantasmal killer", "cloudkill", "wall of fire", "wall of stone",
        "raise dead", "resurrection", "true resurrection",
        "bull's strength", "cat's grace", "bear's endurance",
        "owl's wisdom", "fox's cunning", "eagle's splendor",
    ]
    for name in known_names:
        names.add(name.lower())

    return names


# ---------------------------------------------------------------------------
# Schema Validity Tests
# ---------------------------------------------------------------------------

class TestSchemaValidity:
    """Every entry deserializes into a valid MechanicalSpellTemplate."""

    def test_all_entries_deserialize(self, spells_data):
        """Every entry in spells.json can be deserialized."""
        for entry in spells_data:
            template = MechanicalSpellTemplate.from_dict(entry)
            assert template.template_id.startswith("SPELL_")

    def test_template_ids_are_sequential(self, spells_data):
        """Template IDs follow SPELL_NNN pattern with no gaps."""
        ids = [s["template_id"] for s in spells_data]
        for i, tid in enumerate(ids):
            expected = f"SPELL_{i + 1:03d}"
            assert tid == expected, f"Expected {expected}, got {tid}"

    def test_tier_in_range(self, spells_data):
        """All tiers are between 0 and 9."""
        for s in spells_data:
            assert 0 <= s["tier"] <= 9, (
                f"{s['template_id']}: tier {s['tier']} out of range"
            )

    def test_school_not_empty(self, spells_data):
        """school_category is never empty."""
        for s in spells_data:
            assert s["school_category"], (
                f"{s['template_id']}: empty school_category"
            )

    def test_source_page_not_empty(self, spells_data):
        """source_page is never empty."""
        for s in spells_data:
            assert s["source_page"], (
                f"{s['template_id']}: empty source_page"
            )

    def test_valid_school_values(self, spells_data):
        """School categories are from the known set."""
        valid_schools = {
            "abjuration", "conjuration", "divination", "enchantment",
            "evocation", "illusion", "necromancy", "transmutation",
            "universal",
        }
        for s in spells_data:
            assert s["school_category"] in valid_schools, (
                f"{s['template_id']}: unknown school {s['school_category']}"
            )

    def test_round_trip_preserves_data(self, spells_data):
        """to_dict()/from_dict() round-trip preserves all fields."""
        for entry in spells_data[:20]:  # Spot check first 20
            template = MechanicalSpellTemplate.from_dict(entry)
            restored = template.to_dict()
            # Compare key fields
            assert restored["template_id"] == entry["template_id"]
            assert restored["tier"] == entry["tier"]
            assert restored["school_category"] == entry["school_category"]
            assert restored["effect_type"] == entry["effect_type"]


# ---------------------------------------------------------------------------
# IP Firewall Tests — No Name Leakage
# ---------------------------------------------------------------------------

class TestNoNameLeakage:
    """Verify NO field contains an original spell name."""

    def test_no_name_in_string_fields(self, spells_data, spell_name_blocklist):
        """No string field contains a known spell name.

        Allows legitimate mechanical terms that happen to share names
        with spells (e.g., 'entangled' is a condition, 'teleportation'
        is a subschool).
        """
        # Terms that are legitimate bone/muscle vocabulary, not skin
        mechanical_allowlist = {
            "entangle",    # 'entangled' is a game condition
            "teleport",    # 'teleportation' is a subschool
            "silence",     # 'silenced' can be a condition
            "sleep",       # 'sleep' is a condition effect
            "invisibility",  # 'invisible' is a condition
        }
        violations = []
        for s in spells_data:
            for key, value in s.items():
                if isinstance(value, str):
                    for name in spell_name_blocklist:
                        if len(name) > 5 and name in value.lower():
                            if name not in mechanical_allowlist:
                                violations.append(
                                    f"{s['template_id']}.{key}: contains '{name}'"
                                )
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            for name in spell_name_blocklist:
                                if len(name) > 5 and name in item.lower():
                                    if name not in mechanical_allowlist:
                                        violations.append(
                                            f"{s['template_id']}.{key}: contains '{name}'"
                                        )
        assert not violations, (
            f"Name leakage found in {len(violations)} fields:\n"
            + "\n".join(violations[:20])
        )

    def test_no_template_id_contains_name(self, spells_data):
        """Template IDs are SPELL_NNN, not descriptive names."""
        for s in spells_data:
            assert re.match(r"^SPELL_\d{3,}$", s["template_id"]), (
                f"Bad template_id format: {s['template_id']}"
            )


# ---------------------------------------------------------------------------
# No Prose Leakage Tests
# ---------------------------------------------------------------------------

class TestNoProseLeakage:
    """No field should contain prose descriptions."""

    def test_no_long_strings(self, spells_data):
        """No string field exceeds 100 characters (formulas are short)."""
        violations = []
        for s in spells_data:
            for key, value in s.items():
                if isinstance(value, str) and len(value) > 100:
                    violations.append(
                        f"{s['template_id']}.{key}: {len(value)} chars"
                    )
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and len(item) > 100:
                            violations.append(
                                f"{s['template_id']}.{key}: item {len(item)} chars"
                            )
        assert not violations, (
            f"Prose leakage found:\n" + "\n".join(violations[:20])
        )

    def test_no_sentences_in_fields(self, spells_data):
        """No field contains what looks like a prose sentence."""
        sentence_re = re.compile(r"[A-Z][a-z]{3,}\s+\w+\s+\w+\s+\w+\s+\w+\.")
        violations = []
        for s in spells_data:
            for key, value in s.items():
                if isinstance(value, str) and sentence_re.search(value):
                    violations.append(
                        f"{s['template_id']}.{key}: '{value[:60]}...'"
                    )
        assert not violations, (
            f"Sentence-like prose found:\n" + "\n".join(violations[:10])
        )


# ---------------------------------------------------------------------------
# Completeness Tests
# ---------------------------------------------------------------------------

class TestCompleteness:
    """Verify coverage of known spells."""

    def test_minimum_spell_count(self, spells_data):
        """At least 250 spells extracted (PHB has ~300+)."""
        assert len(spells_data) >= 250, (
            f"Only {len(spells_data)} spells extracted, expected 250+"
        )

    def test_all_tiers_represented(self, spells_data):
        """Every spell level 0-9 has at least one entry."""
        tiers = {s["tier"] for s in spells_data}
        for tier in range(10):
            assert tier in tiers, f"No spells at tier {tier}"

    def test_all_schools_represented(self, spells_data):
        """Every spell school has entries."""
        schools = {s["school_category"] for s in spells_data}
        expected_schools = {
            "abjuration", "conjuration", "divination", "enchantment",
            "evocation", "illusion", "necromancy", "transmutation",
        }
        for school in expected_schools:
            assert school in schools, f"No spells in {school}"

    def test_provenance_matches_templates(self, spells_data, provenance_data):
        """Every template has a provenance entry."""
        template_ids = {s["template_id"] for s in spells_data}
        prov_ids = set(provenance_data.keys())
        missing = template_ids - prov_ids
        assert not missing, (
            f"Templates missing provenance: {missing}"
        )


# ---------------------------------------------------------------------------
# Formula Spot-Check Tests
# ---------------------------------------------------------------------------

class TestFormulaSpotChecks:
    """Spot-check extracted values against known PHB mechanics."""

    def _find_by_criteria(self, spells_data, **criteria):
        """Find templates matching criteria."""
        matches = []
        for s in spells_data:
            if all(s.get(k) == v for k, v in criteria.items()):
                matches.append(s)
        return matches

    def test_evocation_fire_area_damage_exists(self, spells_data):
        """At least one evocation fire area damage spell exists (fireball-like)."""
        matches = [
            s for s in spells_data
            if s["school_category"] == "evocation"
            and s.get("damage_type") == "fire"
            and s["tier"] == 3
        ]
        assert len(matches) >= 1, "No evocation tier-3 fire damage spell found"

    def test_healing_spells_exist(self, spells_data):
        """Healing spells have healing formulas."""
        healing = [s for s in spells_data if s["effect_type"] == "healing"]
        assert len(healing) >= 3, (
            f"Expected at least 3 healing spells, found {len(healing)}"
        )
        for h in healing:
            assert h.get("healing_formula") or h.get("inherits_from_template"), (
                f"{h['template_id']}: healing spell without formula"
            )

    def test_touch_spells_have_touch_range(self, spells_data):
        """Touch target spells have touch range."""
        touch_spells = [
            s for s in spells_data
            if s["target_type"] == "touch"
        ]
        assert len(touch_spells) >= 5, "Expected at least 5 touch spells"
        for s in touch_spells:
            assert s.get("range_formula") in ("touch", "personal_or_touch", None), (
                f"{s['template_id']}: touch spell with range {s.get('range_formula')}"
            )

    def test_ray_spells_require_attack_roll(self, spells_data):
        """Ray spells should require attack rolls."""
        ray_spells = [
            s for s in spells_data if s["target_type"] == "ray"
        ]
        assert len(ray_spells) >= 3, "Expected at least 3 ray spells"
        for s in ray_spells:
            assert s["requires_attack_roll"], (
                f"{s['template_id']}: ray without attack roll"
            )

    def test_cantrips_are_tier_zero(self, spells_data):
        """Level-0 spells (cantrips) exist."""
        cantrips = [s for s in spells_data if s["tier"] == 0]
        assert len(cantrips) >= 10, (
            f"Expected at least 10 cantrips, found {len(cantrips)}"
        )

    def test_ninth_level_spells_exist(self, spells_data):
        """9th-level spells exist."""
        nines = [s for s in spells_data if s["tier"] == 9]
        assert len(nines) >= 10, (
            f"Expected at least 10 9th-level spells, found {len(nines)}"
        )

    def test_component_flags_reasonable(self, spells_data):
        """Most spells have V or S components."""
        v_count = sum(1 for s in spells_data if s["verbal"])
        s_count = sum(1 for s in spells_data if s["somatic"])
        total = len(spells_data)
        # Most D&D spells have V and/or S
        assert v_count > total * 0.3, (
            f"Only {v_count}/{total} spells have V component — seems low"
        )
        assert s_count > total * 0.3, (
            f"Only {s_count}/{total} spells have S component — seems low"
        )

    def test_save_types_distributed(self, spells_data):
        """Save types are distributed across fort/ref/will."""
        save_counts = {}
        for s in spells_data:
            st = s.get("save_type")
            if st:
                save_counts[st] = save_counts.get(st, 0) + 1
        assert "will" in save_counts, "No Will saves found"
        assert "reflex" in save_counts, "No Reflex saves found"
        assert "fortitude" in save_counts, "No Fortitude saves found"

    def test_spell_resistance_distribution(self, spells_data):
        """Some spells have SR and some don't."""
        sr_yes = sum(1 for s in spells_data if s["spell_resistance"])
        sr_no = sum(1 for s in spells_data if not s["spell_resistance"])
        assert sr_yes > 50, f"Only {sr_yes} spells have SR=Yes"
        assert sr_no > 50, f"Only {sr_no} spells have SR=No"


# ---------------------------------------------------------------------------
# Gold Standard Bridge Tests
# ---------------------------------------------------------------------------

class TestGoldStandardBridge:
    """Cross-reference extracted templates against SPELL_REGISTRY."""

    @pytest.fixture(scope="class")
    def gold_spells(self):
        """Load the 53 gold-standard spells."""
        try:
            from aidm.schemas.spell_definitions import SPELL_REGISTRY
            return SPELL_REGISTRY
        except ImportError:
            pytest.skip("SPELL_REGISTRY not available")

    def test_gold_standard_count_coverage(
        self, spells_data, provenance_data, gold_spells,
    ):
        """Extracted set covers the pages of the 53 gold-standard spells."""
        # Get source pages from gold standard
        gold_pages = set()
        for spell_def in gold_spells.values():
            for citation in spell_def.rule_citations:
                # Extract page number from "PHB p.231"
                m = re.search(r"p\.(\d+)", citation)
                if m:
                    gold_pages.add(int(m.group(1)))

        # Check that we have templates from those pages
        extracted_pages = set()
        for s in spells_data:
            m = re.search(r"p\.(\d+)", s["source_page"])
            if m:
                extracted_pages.add(int(m.group(1)))

        missing_pages = gold_pages - extracted_pages
        assert len(missing_pages) <= 5, (
            f"Missing pages from gold standard: {missing_pages}"
        )

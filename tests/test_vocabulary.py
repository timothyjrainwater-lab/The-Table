"""Tests for WO-VOCAB-REGISTRY-001: Vocabulary Registry.

Covers:
1. Frozen dataclass rejects mutation
2. to_dict() / from_dict() round-trip preserves all fields
3. Registry rejects duplicate content_ids
4. Registry rejects duplicate lexicon_ids
5. get_world_name() returns correct name
6. get_world_name() returns None for unknown ID
7. search_by_name() finds entries by substring
8. search_by_name() is case-insensitive
9. get_content_id() reverse lookup works
10. list_by_category() returns sorted results
11. Empty registry is valid
"""

import json
from pathlib import Path

import pytest

from aidm.schemas.vocabulary import (
    LocalizationHooks,
    TaxonomyCategory,
    TaxonomySubcategory,
    VocabularyEntry,
    VocabularyProvenance,
    VocabularyRegistry,
    WorldTaxonomy,
)
from aidm.lens.vocabulary_registry import (
    DuplicateContentIdError,
    DuplicateLexiconIdError,
    VocabularyRegistryLoader,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_provenance(**overrides):
    defaults = {
        "source": "world_compiler",
        "compiler_version": "0.1.0",
        "seed_used": 42,
        "content_pack_id": "base_3.5e_v1",
    }
    defaults.update(overrides)
    return VocabularyProvenance(**defaults)


def _make_entry(
    content_id: str,
    world_name: str,
    lexicon_id: str,
    domain: str = "spell",
    category: str = "destruction_magic",
    **kwargs,
) -> VocabularyEntry:
    defaults = {
        "content_id": content_id,
        "lexicon_id": lexicon_id,
        "domain": domain,
        "world_name": world_name,
        "category": category,
        "aliases": (),
        "subcategory": None,
        "short_description": f"A {domain} called {world_name}.",
        "article": None,
        "plural_form": None,
        "localization_hooks": LocalizationHooks(
            semantic_root=f"{domain}_entry",
            tone_register="formal",
        ),
        "ip_clean": True,
        "provenance": _make_provenance(),
    }
    defaults.update(kwargs)
    return VocabularyEntry(**defaults)


FIXTURE_ENTRIES = [
    _make_entry(
        content_id="spell.fire_burst_003",
        world_name="Searing Detonation",
        lexicon_id="a1b2c3d4e5f6g7h8",
        domain="spell",
        category="destruction_magic",
        subcategory="fire_domain",
        aliases=("Fire Burst", "Searing Blast"),
        short_description="Explosive fire burst at range.",
        article="a",
        localization_hooks=LocalizationHooks(
            semantic_root="fire_burst_projectile",
            tone_register="formal",
            syllable_count=5,
        ),
    ),
    _make_entry(
        content_id="spell.glacial_barrier",
        world_name="Glacial Barrier",
        lexicon_id="b2c3d4e5f6g7h8i9",
        domain="spell",
        category="destruction_magic",
        subcategory="ice_domain",
        short_description="Create a wall of ice.",
        article="a",
        plural_form="Glacial Barriers",
        localization_hooks=LocalizationHooks(
            semantic_root="ice_wall_barrier",
            tone_register="formal",
            syllable_count=5,
        ),
    ),
    _make_entry(
        content_id="feat.iron_stance",
        world_name="Iron Stance",
        lexicon_id="c3d4e5f6g7h8i9j0",
        domain="feat",
        category="martial_technique",
        short_description="Bonus to AC when stationary.",
        localization_hooks=LocalizationHooks(
            semantic_root="defensive_stance",
            tone_register="technical",
        ),
    ),
    _make_entry(
        content_id="creature.shadow_stalker",
        world_name="Shadow Stalker",
        lexicon_id="d4e5f6g7h8i9j0k1",
        domain="creature",
        category="undead_horrors",
        short_description="An undead predator from the shadow plane.",
        article="a",
        localization_hooks=LocalizationHooks(
            semantic_root="undead_shadow_predator",
            tone_register="mythic",
            gender_class="neuter",
        ),
    ),
    _make_entry(
        content_id="creature.bone_sentinel",
        world_name="Bone Sentinel",
        lexicon_id="e5f6g7h8i9j0k1l2",
        domain="creature",
        category="undead_horrors",
        subcategory="skeletal",
        short_description="A skeletal guardian bound to protect.",
        article="a",
        plural_form="Bone Sentinels",
    ),
    _make_entry(
        content_id="skill.shadow_step",
        world_name="Shadow Step",
        lexicon_id="f6g7h8i9j0k1l2m3",
        domain="skill",
        category="stealth_arts",
        short_description="Move through shadows.",
        aliases=("Shadow Walk", "Umbral Step"),
    ),
]


def _fixture_loader() -> VocabularyRegistryLoader:
    return VocabularyRegistryLoader(
        entries=list(FIXTURE_ENTRIES),
        schema_version="1.0",
        world_id="a" * 32,
        locale="en",
    )


def _fixture_registry_dict():
    return {
        "schema_version": "1.0",
        "world_id": "a" * 32,
        "locale": "en",
        "entry_count": len(FIXTURE_ENTRIES),
        "entries": [e.to_dict() for e in FIXTURE_ENTRIES],
    }


# ---------------------------------------------------------------------------
# Test 1: Frozen dataclass rejects mutation
# ---------------------------------------------------------------------------

class TestFrozenDataclasses:
    def test_vocabulary_entry_rejects_mutation(self):
        entry = FIXTURE_ENTRIES[0]
        with pytest.raises(AttributeError):
            entry.world_name = "Hacked Name"

    def test_localization_hooks_rejects_mutation(self):
        hooks = LocalizationHooks(semantic_root="test", tone_register="formal")
        with pytest.raises(AttributeError):
            hooks.semantic_root = "hacked"

    def test_vocabulary_provenance_rejects_mutation(self):
        prov = _make_provenance()
        with pytest.raises(AttributeError):
            prov.source = "hacked"

    def test_taxonomy_category_rejects_mutation(self):
        cat = TaxonomyCategory(
            category_id="test", display_name="Test", domain="spell",
        )
        with pytest.raises(AttributeError):
            cat.category_id = "hacked"

    def test_taxonomy_subcategory_rejects_mutation(self):
        sub = TaxonomySubcategory(subcategory_id="test", display_name="Test")
        with pytest.raises(AttributeError):
            sub.subcategory_id = "hacked"

    def test_vocabulary_registry_rejects_mutation(self):
        reg = VocabularyRegistry(
            schema_version="1.0",
            world_id="a" * 32,
            locale="en",
            entries=(),
        )
        with pytest.raises(AttributeError):
            reg.schema_version = "hacked"


# ---------------------------------------------------------------------------
# Test 2: to_dict() / from_dict() round-trip
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_vocabulary_entry_round_trip(self):
        for entry in FIXTURE_ENTRIES:
            d = entry.to_dict()
            restored = VocabularyEntry.from_dict(d)
            assert restored.content_id == entry.content_id
            assert restored.lexicon_id == entry.lexicon_id
            assert restored.domain == entry.domain
            assert restored.world_name == entry.world_name
            assert restored.category == entry.category
            assert restored.aliases == entry.aliases
            assert restored.subcategory == entry.subcategory
            assert restored.short_description == entry.short_description
            assert restored.article == entry.article
            assert restored.plural_form == entry.plural_form
            assert restored.ip_clean == entry.ip_clean
            # Nested round-trip
            assert (
                restored.localization_hooks.semantic_root
                == entry.localization_hooks.semantic_root
            )
            assert (
                restored.localization_hooks.tone_register
                == entry.localization_hooks.tone_register
            )

    def test_provenance_round_trip(self):
        prov = _make_provenance(
            template_ids=("tmpl_001", "tmpl_002"),
            llm_output_hash="abc123def456",
        )
        d = prov.to_dict()
        restored = VocabularyProvenance.from_dict(d)
        assert restored.source == prov.source
        assert restored.compiler_version == prov.compiler_version
        assert restored.seed_used == prov.seed_used
        assert restored.content_pack_id == prov.content_pack_id
        assert restored.template_ids == prov.template_ids
        assert restored.llm_output_hash == prov.llm_output_hash

    def test_localization_hooks_round_trip(self):
        hooks = LocalizationHooks(
            semantic_root="fire_burst",
            tone_register="archaic",
            gender_class="masculine",
            syllable_count=3,
        )
        d = hooks.to_dict()
        restored = LocalizationHooks.from_dict(d)
        assert restored.semantic_root == hooks.semantic_root
        assert restored.tone_register == hooks.tone_register
        assert restored.gender_class == hooks.gender_class
        assert restored.syllable_count == hooks.syllable_count

    def test_taxonomy_round_trip(self):
        taxonomy = WorldTaxonomy(
            categories=(
                TaxonomyCategory(
                    category_id="destruction_magic",
                    display_name="Destruction Magic",
                    domain="spell",
                    subcategories=(
                        TaxonomySubcategory(
                            subcategory_id="fire_domain",
                            display_name="Fire Domain",
                        ),
                    ),
                ),
            ),
        )
        d = taxonomy.to_dict()
        restored = WorldTaxonomy.from_dict(d)
        assert len(restored.categories) == 1
        assert restored.categories[0].category_id == "destruction_magic"
        assert len(restored.categories[0].subcategories) == 1
        assert (
            restored.categories[0].subcategories[0].subcategory_id == "fire_domain"
        )

    def test_registry_dataclass_round_trip(self):
        reg = VocabularyRegistry(
            schema_version="1.0",
            world_id="a" * 32,
            locale="en",
            entries=tuple(FIXTURE_ENTRIES),
            naming_style="anglo_saxon_with_elvish",
            entry_count=len(FIXTURE_ENTRIES),
        )
        d = reg.to_dict()
        restored = VocabularyRegistry.from_dict(d)
        assert restored.schema_version == reg.schema_version
        assert restored.world_id == reg.world_id
        assert restored.locale == reg.locale
        assert restored.naming_style == reg.naming_style
        assert len(restored.entries) == len(reg.entries)

    def test_registry_dict_round_trip(self):
        reg_dict = _fixture_registry_dict()
        loader = VocabularyRegistryLoader.from_dict(reg_dict)
        assert loader.entry_count == len(FIXTURE_ENTRIES)
        assert loader.schema_version == "1.0"
        assert loader.world_id == "a" * 32


# ---------------------------------------------------------------------------
# Test 3: Registry rejects duplicate content_ids
# ---------------------------------------------------------------------------

class TestDuplicateContentIdRejection:
    def test_duplicate_content_id_raises(self):
        duplicate = _make_entry(
            content_id="spell.fire_burst_003",
            world_name="Duplicate Entry",
            lexicon_id="zzzzzzzzzzzzzzzz",
        )
        with pytest.raises(DuplicateContentIdError, match="Duplicate content_id"):
            VocabularyRegistryLoader(entries=[FIXTURE_ENTRIES[0], duplicate])


# ---------------------------------------------------------------------------
# Test 4: Registry rejects duplicate lexicon_ids
# ---------------------------------------------------------------------------

class TestDuplicateLexiconIdRejection:
    def test_duplicate_lexicon_id_raises(self):
        duplicate = _make_entry(
            content_id="spell.totally_different",
            world_name="Different Name",
            lexicon_id="a1b2c3d4e5f6g7h8",  # same as fire_burst_003
        )
        with pytest.raises(DuplicateLexiconIdError, match="Duplicate lexicon_id"):
            VocabularyRegistryLoader(entries=[FIXTURE_ENTRIES[0], duplicate])


# ---------------------------------------------------------------------------
# Test 5: get_world_name() returns correct name
# ---------------------------------------------------------------------------

class TestGetWorldName:
    def test_get_existing_name(self):
        loader = _fixture_loader()
        assert loader.get_world_name("spell.fire_burst_003") == "Searing Detonation"

    def test_get_another_entry(self):
        loader = _fixture_loader()
        assert loader.get_world_name("creature.shadow_stalker") == "Shadow Stalker"


# ---------------------------------------------------------------------------
# Test 6: get_world_name() returns None for unknown ID
# ---------------------------------------------------------------------------

class TestGetWorldNameMissing:
    def test_unknown_id_returns_none(self):
        loader = _fixture_loader()
        assert loader.get_world_name("spell.nonexistent") is None

    def test_empty_string_returns_none(self):
        loader = _fixture_loader()
        assert loader.get_world_name("") is None


# ---------------------------------------------------------------------------
# Test 7: search_by_name() finds entries by substring
# ---------------------------------------------------------------------------

class TestSearchByName:
    def test_search_finds_by_substring(self):
        loader = _fixture_loader()
        results = loader.search_by_name("Searing")
        assert len(results) == 1
        assert results[0].content_id == "spell.fire_burst_003"

    def test_search_finds_multiple(self):
        loader = _fixture_loader()
        results = loader.search_by_name("Shadow")
        assert len(results) == 2
        content_ids = {e.content_id for e in results}
        assert content_ids == {"creature.shadow_stalker", "skill.shadow_step"}

    def test_search_no_results(self):
        loader = _fixture_loader()
        results = loader.search_by_name("nonexistent_xyz")
        assert len(results) == 0


# ---------------------------------------------------------------------------
# Test 8: search_by_name() is case-insensitive
# ---------------------------------------------------------------------------

class TestSearchCaseInsensitive:
    def test_lowercase_query(self):
        loader = _fixture_loader()
        results = loader.search_by_name("searing")
        assert len(results) == 1

    def test_uppercase_query(self):
        loader = _fixture_loader()
        results = loader.search_by_name("SEARING")
        assert len(results) == 1

    def test_mixed_case_query(self):
        loader = _fixture_loader()
        results = loader.search_by_name("sEaRiNg")
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Test 9: get_content_id() reverse lookup works
# ---------------------------------------------------------------------------

class TestGetContentId:
    def test_reverse_lookup(self):
        loader = _fixture_loader()
        assert loader.get_content_id("Searing Detonation") == "spell.fire_burst_003"

    def test_reverse_lookup_creature(self):
        loader = _fixture_loader()
        assert loader.get_content_id("Shadow Stalker") == "creature.shadow_stalker"

    def test_reverse_lookup_unknown(self):
        loader = _fixture_loader()
        assert loader.get_content_id("Nonexistent Name") is None


# ---------------------------------------------------------------------------
# Test 10: list_by_category() returns sorted results
# ---------------------------------------------------------------------------

class TestListByCategory:
    def test_list_category_sorted_by_world_name(self):
        loader = _fixture_loader()
        entries = loader.list_by_category("destruction_magic")
        assert len(entries) == 2
        # Glacial Barrier < Searing Detonation alphabetically
        assert entries[0].world_name == "Glacial Barrier"
        assert entries[1].world_name == "Searing Detonation"

    def test_list_undead_horrors(self):
        loader = _fixture_loader()
        entries = loader.list_by_category("undead_horrors")
        assert len(entries) == 2
        # Bone Sentinel < Shadow Stalker alphabetically
        assert entries[0].world_name == "Bone Sentinel"
        assert entries[1].world_name == "Shadow Stalker"

    def test_list_empty_category(self):
        loader = _fixture_loader()
        results = loader.list_by_category("nonexistent_category")
        assert results == []


# ---------------------------------------------------------------------------
# Test 11: Empty registry is valid
# ---------------------------------------------------------------------------

class TestEmptyRegistry:
    def test_empty_registry(self):
        loader = VocabularyRegistryLoader.empty()
        assert loader.entry_count == 0
        assert loader.list_all() == []
        assert loader.get_entry("anything") is None
        assert loader.get_world_name("anything") is None
        assert loader.search_by_name("anything") == []
        assert loader.list_by_category("spell") == []
        assert loader.get_content_id("anything") is None

    def test_empty_registry_from_dict(self):
        loader = VocabularyRegistryLoader.from_dict({"entries": []})
        assert loader.entry_count == 0


# ---------------------------------------------------------------------------
# Test 12: JSON file round-trip
# ---------------------------------------------------------------------------

class TestJsonFileRoundTrip:
    def test_load_from_json_file(self, tmp_path):
        reg_dict = _fixture_registry_dict()
        json_path = tmp_path / "vocabulary_registry.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(reg_dict, f)

        loader = VocabularyRegistryLoader.from_json_file(json_path)
        assert loader.entry_count == 6
        assert loader.get_entry("spell.fire_burst_003") is not None

    def test_load_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            VocabularyRegistryLoader.from_json_file(tmp_path / "missing.json")


# ---------------------------------------------------------------------------
# Test 13: list_all() returns all entries sorted by content_id
# ---------------------------------------------------------------------------

class TestListAll:
    def test_all_entries_sorted(self):
        loader = _fixture_loader()
        all_entries = loader.list_all()
        assert len(all_entries) == 6
        ids = [e.content_id for e in all_entries]
        assert ids == sorted(ids)

    def test_all_entries_present(self):
        loader = _fixture_loader()
        all_entries = loader.list_all()
        all_ids = {e.content_id for e in all_entries}
        expected_ids = {e.content_id for e in FIXTURE_ENTRIES}
        assert all_ids == expected_ids

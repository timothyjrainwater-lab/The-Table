"""Gate tests: WO-ENGINE-SPELL-DEF-DEDUP-001 (Batch AT)

SDD-001..008 — Spell definition deduplication:
  SDD-001: No duplicate keys across spell_definitions.py
  SDD-002: grease — verbose PHB fields preserved (save_type, aoe_shape, conditions_on_fail)
  SDD-003: stinking_cloud — verbose PHB fields preserved (save_type, duration)
  SDD-004: All entries have spell_school != None
  SDD-005: SPELL_REGISTRY count >= 730 (no spells deleted)
  SDD-006: cause_fear still present with correct fields
  SDD-007: bless still present in SPELL_REGISTRY
  SDD-008: Existing SE gates intact (spell data wiring unbroken)

Python dicts with duplicate keys silently keep the last value. OSS compact entries
were overwriting verbose hand-typed entries. This WO removes the compact duplicates,
keeping the verbose PHB-accurate entries.
"""

import ast
import pytest

from aidm.data.spell_definitions import SPELL_REGISTRY


# ---------------------------------------------------------------------------
# SDD-001: No duplicate keys in spell_definitions.py
# ---------------------------------------------------------------------------

def test_SDD001_no_duplicate_keys_in_definitions_file():
    """SDD-001: spell_definitions.py has no duplicate dict keys."""
    filepath = "aidm/data/spell_definitions.py"
    with open(filepath, "r", encoding="utf-8") as f:
        src = f.read()

    tree = ast.parse(src)

    class DictFinder(ast.NodeVisitor):
        def __init__(self):
            self.dicts = []
        def visit_Dict(self, node):
            self.dicts.append(node)

    finder = DictFinder()
    finder.visit(tree)
    main_dict = max(finder.dicts, key=lambda d: len(d.keys))

    seen = {}
    duplicates = []
    for k in main_dict.keys:
        if isinstance(k, ast.Constant) and isinstance(k.value, str):
            key = k.value
            if key in seen:
                duplicates.append((key, seen[key], k.lineno))
            else:
                seen[key] = k.lineno

    assert duplicates == [], (
        f"SDD-001: Found {len(duplicates)} duplicate keys in spell_definitions.py: "
        f"{[(d[0], d[1], d[2]) for d in duplicates[:5]]}"
    )


# ---------------------------------------------------------------------------
# SDD-002: grease — verbose PHB fields preserved
# ---------------------------------------------------------------------------

def test_SDD002_grease_verbose_fields_preserved():
    """SDD-002: grease entry has verbose PHB fields — not compact OSS overwrite."""
    grease = SPELL_REGISTRY.get("grease")
    assert grease is not None, "SDD-002: 'grease' missing from SPELL_REGISTRY"
    assert grease.save_type is not None, (
        "SDD-002: grease.save_type must not be None (PHB p.237: Ref half)"
    )
    assert grease.save_type.value == "reflex", (
        f"SDD-002: grease.save_type must be REF (reflex); got {grease.save_type}"
    )
    assert grease.aoe_shape is not None, (
        "SDD-002: grease.aoe_shape must not be None (verbose entry has BURST)"
    )
    assert grease.conditions_on_fail is not None and len(grease.conditions_on_fail) > 0, (
        f"SDD-002: grease.conditions_on_fail must be non-empty ('prone'); "
        f"got {grease.conditions_on_fail}"
    )
    assert "prone" in grease.conditions_on_fail, (
        f"SDD-002: grease.conditions_on_fail must include 'prone'; "
        f"got {grease.conditions_on_fail}"
    )


# ---------------------------------------------------------------------------
# SDD-003: stinking_cloud — verbose PHB fields preserved
# ---------------------------------------------------------------------------

def test_SDD003_stinking_cloud_verbose_fields_preserved():
    """SDD-003: stinking_cloud entry has verbose PHB fields — save_type and duration."""
    sc = SPELL_REGISTRY.get("stinking_cloud")
    assert sc is not None, "SDD-003: 'stinking_cloud' missing from SPELL_REGISTRY"
    assert sc.save_type is not None, (
        "SDD-003: stinking_cloud.save_type must not be None (PHB: Fort save)"
    )
    assert sc.save_type.value == "fortitude", (
        f"SDD-003: stinking_cloud.save_type must be FORT; got {sc.save_type}"
    )
    assert sc.duration_rounds is not None and sc.duration_rounds > 0, (
        f"SDD-003: stinking_cloud.duration_rounds must be > 0; got {sc.duration_rounds}"
    )


# ---------------------------------------------------------------------------
# SDD-004: All entries have spell_school != None
# ---------------------------------------------------------------------------

def test_SDD004_all_entries_have_spell_school():
    """SDD-004: All SPELL_REGISTRY entries have school field non-None."""
    none_school = [
        k for k, v in SPELL_REGISTRY.items()
        if getattr(v, "school", None) is None
    ]
    assert none_school == [], (
        f"SDD-004: {len(none_school)} entries have school=None after dedup: "
        f"{none_school[:10]}"
    )


# ---------------------------------------------------------------------------
# SDD-005: SPELL_REGISTRY count >= 730 (no spells deleted)
# ---------------------------------------------------------------------------

def test_SDD005_spell_registry_count_preserved():
    """SDD-005: SPELL_REGISTRY count >= 730 — dedup removed duplicates only, not spells."""
    count = len(SPELL_REGISTRY)
    assert count >= 730, (
        f"SDD-005: SPELL_REGISTRY has {count} entries — expected >= 730. "
        f"Deduplication must not delete any spells."
    )


# ---------------------------------------------------------------------------
# SDD-006: cause_fear still present with correct fields
# ---------------------------------------------------------------------------

def test_SDD006_cause_fear_still_present():
    """SDD-006: cause_fear (engine test staple) still in SPELL_REGISTRY with correct fields."""
    cf = SPELL_REGISTRY.get("cause_fear")
    assert cf is not None, "SDD-006: 'cause_fear' missing from SPELL_REGISTRY"
    assert cf.school == "necromancy", (
        f"SDD-006: cause_fear.school must be 'necromancy'; got {cf.school!r}"
    )
    assert cf.save_type is not None, (
        "SDD-006: cause_fear.save_type must not be None (Will save)"
    )
    assert cf.save_type.value == "will", (
        f"SDD-006: cause_fear.save_type must be 'will'; got {cf.save_type}"
    )


# ---------------------------------------------------------------------------
# SDD-007: bless still present in SPELL_REGISTRY
# ---------------------------------------------------------------------------

def test_SDD007_bless_still_present():
    """SDD-007: bless (Divine Grace / save bonus test staple) still in SPELL_REGISTRY."""
    bless = SPELL_REGISTRY.get("bless")
    assert bless is not None, "SDD-007: 'bless' missing from SPELL_REGISTRY after dedup"


# ---------------------------------------------------------------------------
# SDD-008: Existing spell resolution unbroken (SE regression guard)
# ---------------------------------------------------------------------------

def test_SDD008_spell_data_wiring_unbroken():
    """SDD-008: Core spells used by existing engine tests still have required fields."""
    required_spells = [
        ("fireball", "evocation"),
        ("magic_missile", "evocation"),
        ("cure_light_wounds", "conjuration"),
        ("cause_fear", "necromancy"),
        ("sleep", "enchantment"),
        ("bless", "enchantment"),
        ("hold_person", "enchantment"),
    ]
    missing = []
    wrong_school = []
    for spell_id, expected_school in required_spells:
        entry = SPELL_REGISTRY.get(spell_id)
        if entry is None:
            missing.append(spell_id)
        elif entry.school != expected_school:
            wrong_school.append((spell_id, entry.school, expected_school))

    assert not missing, (
        f"SDD-008: Engine staple spells missing from SPELL_REGISTRY: {missing}"
    )
    assert not wrong_school, (
        f"SDD-008: School field corrupted for spells: "
        f"{[(s, got, exp) for s, got, exp in wrong_school]}"
    )

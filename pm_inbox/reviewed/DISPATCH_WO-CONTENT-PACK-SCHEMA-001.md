# Instruction Packet: Content Pack Schema Agent

**Work Order:** WO-CONTENT-PACK-SCHEMA-001 (Content Pack Shared Dataclasses)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 1 (Blocks World Compiler + unifies extraction agent output)
**Deliverable Type:** Code implementation + tests
**Parallelization:** Independent — runs in parallel with everything

---

## READ FIRST

The content pack is the database of mechanical templates (bone + muscle, zero skin) that the World Compiler consumes. Three extraction agents are currently producing JSON output for spells, creatures, and feats. This WO creates the **shared Python schema** that:

1. Defines the canonical dataclasses for all content types
2. Provides validation (schema conformance, no-prose-leakage checks)
3. Provides a unified loader that reads `aidm/data/content_pack/*.json`
4. Is consumed by the World Compiler pipeline

---

## YOUR TASK

### Deliverable 1: Content Pack Dataclasses

**File:** `aidm/schemas/content_pack.py` (NEW)

Frozen dataclasses for the three content types currently being extracted:

**1. `MechanicalSpellTemplate`** — Matches the schema in `pm_inbox/DISPATCH_WO-CONTENT-EXTRACT-001.md` lines 93-150. Key fields:
- `template_id` (str, "SPELL_003")
- `tier` (int, 0-9)
- `school_category` (str)
- `descriptors` (tuple)
- `target_type`, `range_formula`, `aoe_shape`, `aoe_radius_ft`
- `effect_type`, `damage_formula`, `damage_type`, `healing_formula`
- `save_type`, `save_effect`, `spell_resistance`, `requires_attack_roll`, `auto_hit`
- `casting_time`, `duration_formula`, `concentration`, `dismissible`
- `verbal`, `somatic`, `material`, `focus`, `divine_focus`, `xp_cost`
- `conditions_applied`, `conditions_duration`
- `combat_role_tags`, `delivery_mode`
- `source_page`, `source_id`

**2. `MechanicalCreatureTemplate`** — Matches the schema in `pm_inbox/DISPATCH_WO-CONTENT-EXTRACT-002.md` lines 60-116. Key fields:
- `template_id` (str, "CREATURE_0042")
- `size_category`, `creature_type`, `subtypes`
- `hit_dice`, `hp_typical`, `initiative_mod`, `speed_ft`, `speed_modes`
- `ac_total`, `ac_touch`, `ac_flat_footed`, `ac_components`
- `bab`, `grapple_mod`, `attacks`, `full_attacks`, `space_ft`, `reach_ft`
- `fort_save`, `ref_save`, `will_save`
- `str_score` through `cha_score` (Optional[int])
- `special_attacks`, `special_qualities`
- `cr`, `alignment_tendency`, `environment_tags`
- `intelligence_band`, `organization_patterns`
- `source_page`, `source_id`

**3. `MechanicalFeatTemplate`** — Matches the schema in `pm_inbox/DISPATCH_WO-CONTENT-EXTRACT-003.md` lines 43-81 PLUS the agent's additions (`can_take_multiple`, `effects_stack`, `metamagic_slot_increase`). Key fields:
- `template_id` (str, "FEAT_017")
- `feat_type` (str)
- `prereq_ability_scores`, `prereq_bab`, `prereq_feat_refs`, `prereq_class_features`, `prereq_caster_level`, `prereq_other`
- `effect_type`, `bonus_value`, `bonus_type`, `bonus_applies_to`
- `trigger`, `replaces_normal`, `grants_action`, `removes_penalty`
- `stacks_with`, `limited_to`
- `fighter_bonus_eligible`, `can_take_multiple`, `effects_stack`
- `metamagic_slot_increase`
- `source_page`, `source_id`

**4. `ContentPack`** — Top-level container:
```python
@dataclass(frozen=True)
class ContentPack:
    schema_version: str
    pack_id: str                    # Deterministic: sha256(sorted file hashes)[:32]
    spells: tuple                   # Tuple of MechanicalSpellTemplate
    creatures: tuple                # Tuple of MechanicalCreatureTemplate
    feats: tuple                    # Tuple of MechanicalFeatTemplate
    source_ids: tuple               # Source book IDs used
    extraction_versions: dict       # {"spells": "WO-...", "creatures": "WO-...", ...}
```

All dataclasses must:
- Be `frozen=True`
- Support `to_dict()` / `from_dict()` (match existing patterns in `aidm/schemas/vocabulary.py`)
- Serialize tuples as lists in JSON, deserialize lists back to tuples

### Deliverable 2: Content Pack Loader

**File:** `aidm/lens/content_pack_loader.py` (NEW)

```python
class ContentPackLoader:
    """Loads and validates the content pack from aidm/data/content_pack/*.json."""

    @classmethod
    def from_directory(cls, path: Path) -> "ContentPackLoader":
        """Load all content pack JSON files from a directory."""

    @classmethod
    def from_content_pack(cls, pack: ContentPack) -> "ContentPackLoader":
        """Load from a ContentPack dataclass."""

    def get_spell(self, template_id: str) -> Optional[MechanicalSpellTemplate]: ...
    def get_creature(self, template_id: str) -> Optional[MechanicalCreatureTemplate]: ...
    def get_feat(self, template_id: str) -> Optional[MechanicalFeatTemplate]: ...

    def list_spells_by_tier(self, tier: int) -> list: ...
    def list_spells_by_school(self, school: str) -> list: ...
    def list_creatures_by_type(self, creature_type: str) -> list: ...
    def list_creatures_by_cr(self, cr: float) -> list: ...
    def list_feats_by_type(self, feat_type: str) -> list: ...

    def validate(self) -> list[str]:
        """Run validation checks. Returns list of error strings (empty = valid)."""
        # 1. No duplicate template_ids within a category
        # 2. All feat prereq_feat_refs resolve to existing feat template_ids
        # 3. No field value longer than 100 chars (prose leakage check)
        # 4. All required fields present

    @property
    def spell_count(self) -> int: ...
    @property
    def creature_count(self) -> int: ...
    @property
    def feat_count(self) -> int: ...
    @property
    def pack_id(self) -> str: ...
```

### Deliverable 3: Tests

**File:** `tests/test_content_pack_schema.py` (NEW)

1. Frozen dataclass rejects mutation (3 tests — one per type)
2. `to_dict()` / `from_dict()` round-trip (3 tests — one per type)
3. ContentPack round-trip
4. Loader validates no duplicate template_ids
5. Loader validates feat prereq chains
6. Loader validates no field > 100 chars
7. `get_spell()` / `get_creature()` / `get_feat()` lookups
8. `list_spells_by_tier()` / `list_creatures_by_cr()` filtering
9. Empty content pack is valid
10. Loader loads from existing `aidm/data/content_pack/` if files exist

Create fixtures with 3-5 entries per type. Use minimal but valid data.

---

## WHAT EXISTS (DO NOT MODIFY)

| Component | Location | Status |
|-----------|----------|--------|
| Extracted feats JSON | `aidm/data/content_pack/feats.json` | 110 feats — READ ONLY |
| Extracted creatures JSON | `aidm/data/content_pack/creatures.json` | 373 creatures — READ ONLY |
| Vocabulary dataclasses (pattern) | `aidm/schemas/vocabulary.py` | Reference for frozen dataclass pattern |
| Vocabulary registry (pattern) | `aidm/lens/vocabulary_registry.py` | Reference for loader pattern |
| Rulebook dataclasses (pattern) | `aidm/schemas/rulebook.py` | Reference for frozen dataclass pattern |
| Rulebook registry (pattern) | `aidm/lens/rulebook_registry.py` | Reference for loader pattern |

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `aidm/data/content_pack/feats.json` | Live extracted feat data — match this schema |
| 1 | `aidm/data/content_pack/creatures.json` | Live extracted creature data — match this schema |
| 1 | `pm_inbox/DISPATCH_WO-CONTENT-EXTRACT-001.md` | MechanicalSpellTemplate spec (lines 93-150) |
| 2 | `aidm/schemas/vocabulary.py` | Frozen dataclass + to_dict/from_dict pattern |
| 2 | `aidm/lens/vocabulary_registry.py` | Loader pattern with validation |
| 3 | `docs/contracts/WORLD_COMPILER.md` | Content pack is input to Stage 0 |

## STOP CONDITIONS

- If `feats.json` or `creatures.json` field names don't match the WO specs, match the ACTUAL JSON on disk (the extraction agents may have deviated slightly). Log any deviations in your completion report.
- If `spells.json` doesn't exist yet, define `MechanicalSpellTemplate` from the spec and note that validation against live data is deferred.

## DELIVERY

- New files: `aidm/schemas/content_pack.py`, `aidm/lens/content_pack_loader.py`, `tests/test_content_pack_schema.py`
- Full test suite run at end — report total pass/fail count
- Completion report: `pm_inbox/AGENT_WO-CONTENT-PACK-SCHEMA-001_completion.md`

## RULES

- All dataclasses MUST be frozen
- No imports from `aidm/core/`
- Follow existing patterns from `aidm/schemas/vocabulary.py` and `aidm/lens/vocabulary_registry.py`
- The loader is READ-ONLY at runtime
- Match field names from the actual extracted JSON on disk, not just the WO specs

---

END OF INSTRUCTION PACKET

# Instruction Packet: Content Extraction Agent

**Work Order:** WO-CONTENT-EXTRACT-001 (Mechanical Extraction Pipeline — Spells)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 1 (Populates the content pack database — required for World Compiler)
**Deliverable Type:** Code implementation + extracted data + tests
**Parallelization:** This WO covers SPELLS only. Separate WOs will cover monsters, feats, and items. All can run in parallel.

---

## READ FIRST — THE BONE/MUSCLE/SKIN PHILOSOPHY

**This is the most important context for this work order.**

The product separates game content into three layers:

- **Bone:** Abstract math — formulas, dice expressions, numeric parameters, timing, constraints. Uncopyrightable.
- **Muscle:** Behavioral contracts — how effects operate in space and time (projectile vs beam vs burst, duration, targeting rules). Technical specification.
- **Skin:** Names, prose, flavor text, lore. Copyrighted. **NEVER SHIPPED.**

The Vault contains OCR'd source text (PHB, MM, DMG). This text contains all three layers mixed together in natural language. The extraction pipeline reads the source text, strips the skin, and outputs structured mechanical templates containing only bone + muscle.

**The content pack is the database that the World Compiler will consume.** At world compile time, Spark generates new skin (world-flavored names, descriptions, presentation semantics) for each mechanical template. The original names and descriptions are NEVER stored in the content pack.

### What Goes INTO the Content Pack Entry

- Mechanical template ID (e.g., `SPELL_003`, NOT "fireball")
- Level, school (as category tags, not names)
- Numeric parameters: range formula, area dimensions, damage dice formula, save type, duration
- Targeting rules: target type, AoE shape
- Effect type: damage, healing, buff, debuff, utility
- Components: V, S, M, F, DF, XP (as flags)
- Scaling formula: how parameters change with caster level
- Condition effects: what conditions are applied, durations
- Rule citations: PHB page reference (internal provenance only)

### What Does NOT Go INTO the Content Pack Entry

- The spell's original name
- Any prose description
- Flavor text
- Lore or world context
- Material component descriptions (just the flag that M is required)
- "Skin" category labels that are IP-identifiable

---

## YOUR TASK

### Phase 1: Extraction Script

**File:** `tools/extract_spells.py` (NEW)

Build a script that:

1. Reads OCR text files from `sources/text/681f92bc94ff/` (PHB, 322 pages)
2. Identifies spell entries by their structured format:
   - Spell name line (title case, standalone)
   - School line (school name + optional descriptors)
   - Level line (`Level: Clr 1, Sor/Wiz 1`)
   - Components line (`Components: V, S, M`)
   - Casting Time line
   - Range line
   - Target/Area/Effect line
   - Duration line
   - Saving Throw line
   - Spell Resistance line
   - Prose description (STRIP THIS — extract only embedded formulas)
3. Parses each spell into a structured mechanical template
4. Outputs JSON conforming to the content pack schema (Deliverable 2)

**Parsing rules for formula extraction from prose:**
- Damage: look for patterns like `Xd6`, `1d6 per caster level (maximum Xd6)`, `Xd6 points of [type] damage`
- Range formulas: `Long (400 ft. + 40 ft./level)`, `Medium (100 ft. + 10 ft./level)`, `Close (25 ft. + 5 ft./2 levels)`
- Duration: `1 round/level`, `10 min./level`, `Instantaneous`, `Concentration`
- Area: `X-ft. radius`, `X-ft. cone`, `X-ft. line`
- Conditions: `blinded`, `deafened`, `paralyzed`, `stunned`, `nauseated`, `frightened`, etc.

**ID assignment:**
- Each spell gets a sequential ID: `SPELL_001`, `SPELL_002`, etc.
- The original name is stored ONLY in a separate provenance mapping file (NOT in the content pack)
- The provenance mapping file is internal-only, never shipped

### Phase 2: Content Pack Schema

**File:** `aidm/schemas/content_pack.py` (NEW)

Define the content pack entry schema for spells:

```python
@dataclass(frozen=True)
class MechanicalSpellTemplate:
    """A single spell's bone + muscle, with all skin stripped.

    This is the content pack entry format. The World Compiler
    consumes these to generate world-flavored spell entries.
    """
    template_id: str          # "SPELL_003" — no original name
    tier: int                 # Spell level (0-9)
    school_category: str      # "evocation", "necromancy", etc.
    descriptors: tuple[str, ...] # ("fire",), ("cold", "water"), etc.

    # Targeting (bone)
    target_type: str          # "area", "single", "ray", "touch", "self"
    range_formula: str        # "400 + (40 * caster_tier)" or "0" for touch
    aoe_shape: Optional[str]  # "burst", "cone", "line", "emanation", None
    aoe_radius_ft: Optional[int]

    # Effect (bone)
    effect_type: str          # "damage", "healing", "buff", "debuff", "utility"
    damage_formula: Optional[str]     # "min(10, caster_tier)d6"
    damage_type: Optional[str]        # "fire", "cold", "electricity", etc.
    healing_formula: Optional[str]    # "1d8 + min(5, caster_tier)"

    # Resolution (bone)
    save_type: Optional[str]          # "reflex", "will", "fortitude", None
    save_effect: Optional[str]        # "half", "negates", "partial", None
    spell_resistance: bool
    requires_attack_roll: bool
    auto_hit: bool

    # Timing (bone)
    casting_time: str                 # "1_standard", "1_full_round", "3_rounds"
    duration_formula: str             # "instantaneous", "1_round_per_tier", "10_min_per_tier"
    concentration: bool
    dismissible: bool

    # Components (bone — flags only, no material descriptions)
    verbal: bool
    somatic: bool
    material: bool
    focus: bool
    divine_focus: bool
    xp_cost: bool

    # Conditions (muscle)
    conditions_applied: tuple[str, ...] # ("blinded", "paralyzed", etc.)
    conditions_duration: Optional[str]  # "save_ends", "1_round", "duration"

    # Classification tags (muscle)
    combat_role_tags: tuple[str, ...]  # ("damage_dealer", "controller", "support")

    # Behavioral contract (muscle)
    delivery_mode: str        # "projectile", "ray", "burst_from_point", "touch", etc.

    # Provenance (internal only, never shipped to players)
    source_page: str          # "PHB p.231"
    source_id: str            # "681f92bc94ff"
```

### Phase 3: Provenance Mapping

**File:** `tools/data/spell_provenance.json` (NEW, INTERNAL ONLY)

A mapping from template_id to original source name, used ONLY for:
- Developer cross-reference ("which spell is SPELL_003?")
- Evidence map maintenance (AD-004)
- Verification against existing SPELL_REGISTRY

```json
{
  "SPELL_001": {"original_ref": "page_reference_only", "source_page": "PHB p.207", "source_id": "681f92bc94ff"},
  "SPELL_002": {"original_ref": "page_reference_only", "source_page": "PHB p.213", "source_id": "681f92bc94ff"}
}
```

**This file is gitignored or marked internal. It NEVER ships.**

### Phase 4: Extracted Data Output

**File:** `aidm/data/content_pack/spells.json` (NEW)

The extracted spell database in JSON format. Every entry is a `MechanicalSpellTemplate` serialized to JSON. Zero original names, zero prose, zero flavor.

### Phase 5: Validation

**File:** `tests/test_content_pack_spells.py` (NEW)

Tests:
1. **Recognition Test:** For every entry in spells.json, verify that NO field contains an original spell name. Regex check against a blocklist of known spell names.
2. **Completeness:** Verify the 53 already-implemented spells in SPELL_REGISTRY have corresponding content pack entries (cross-reference via provenance mapping)
3. **Schema validity:** Every entry deserializes into a valid `MechanicalSpellTemplate`
4. **Formula parsing:** Spot-check 10 entries against known PHB values (damage dice, range, etc.)
5. **No prose leakage:** No field longer than 100 characters (formulas are short; prose is long)

### Phase 6: Bridge to Existing SPELL_REGISTRY

**File:** `tools/verify_spell_bridge.py` (NEW)

A verification script (not shipped) that:
1. Loads existing `SPELL_REGISTRY` (53 spells with original names)
2. Loads extracted `spells.json` (all spells with template IDs)
3. Uses `spell_provenance.json` to cross-reference
4. Reports: matching fields, mismatched fields, missing entries
5. This validates extraction accuracy against the hand-authored gold standard

---

## SCOPE

### In Scope (PHB Chapter 11: Spells)
- All spells from PHB pages ~196-303 (approximately 300+ spells)
- OCR text files: `sources/text/681f92bc94ff/0196.txt` through `sources/text/681f92bc94ff/0303.txt` (approximate — find the actual spell chapter boundaries)

### Out of Scope (separate WOs)
- Monster stat blocks (MM) — WO-CONTENT-EXTRACT-002
- Feats (PHB Chapter 5) — WO-CONTENT-EXTRACT-003
- Magic items (DMG) — WO-CONTENT-EXTRACT-004
- Class progressions — WO-CONTENT-EXTRACT-005
- Skills — future WO

---

## WHAT EXISTS (DO NOT MODIFY)

| Component | Location | Status |
|-----------|----------|--------|
| SPELL_REGISTRY (53 spells) | `aidm/schemas/spell_definitions.py` | Working — do NOT modify |
| SpellDefinition class | `aidm/core/spell_resolver.py` | Working — do NOT modify |
| OCR text files (PHB) | `sources/text/681f92bc94ff/` | 322 pages — READ ONLY |
| Provenance registry | `sources/provenance.json` | Metadata — READ ONLY |

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `sources/text/681f92bc94ff/0231.txt` | Sample spell page (OCR format) |
| 1 | `aidm/schemas/spell_definitions.py` | Existing 53-spell registry (gold standard) |
| 1 | `aidm/core/spell_resolver.py` | SpellDefinition class + enums |
| 2 | `docs/specs/RQ-PRODUCT-001_CONTENT_INDEPENDENCE_ARCHITECTURE.md` | Three-layer model |
| 2 | `docs/contracts/WORLD_COMPILER.md` | Content pack input format |
| 3 | `MANIFESTO.md` | Creation stack philosophy |

## STOP CONDITIONS

- If OCR quality is too poor on a page to extract reliable numbers, SKIP that spell and log it as "manual review needed" in a separate `tools/data/extraction_gaps.json` file.
- If a spell has no clear mechanical formula (purely narrative effect), log it as "no_mechanical_content" and skip.
- If the extraction would require copying prose descriptions to capture the mechanic (e.g., complex conditional effects described only in natural language), extract what you can as structured fields and flag the rest as "complex_effect_requires_manual_authoring."
- NEVER store original spell names in `spells.json`. If you need them for cross-reference, they go in `spell_provenance.json` only.

## DELIVERY

- New files: `tools/extract_spells.py`, `aidm/schemas/content_pack.py`, `aidm/data/content_pack/spells.json`, `tools/data/spell_provenance.json`, `tools/data/extraction_gaps.json`, `tests/test_content_pack_spells.py`, `tools/verify_spell_bridge.py`
- Extraction report: how many spells extracted, how many skipped, how many flagged
- Full test suite run at end — report total pass/fail count
- Completion report: `pm_inbox/AGENT_WO-CONTENT-EXTRACT-001_completion.md`

## RULES

- **IP FIREWALL:** No original names in `spells.json`. Period.
- **No prose:** No field in the content pack may contain descriptive text. Formulas, enums, numbers, flags only.
- **Provenance mapping is internal-only.** Mark it clearly.
- **Recognition Test:** If a D&D player could look at a content pack entry and say "that's fireball," the entry has too much skin. Strip harder.
- **Match existing schemas:** The `MechanicalSpellTemplate` must be convertible to the existing `SpellDefinition` class (possibly with field mapping). The engine already knows how to resolve spells — the content pack feeds it.
- Follow existing code style and test patterns.

---

END OF INSTRUCTION PACKET

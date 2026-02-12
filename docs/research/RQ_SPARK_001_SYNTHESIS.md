# RQ-SPARK-001 Synthesis: Spark Emission Contract v1

**Document Type:** Research Synthesis (RWO-001)
**Status:** COMPLETE
**Date:** 2026-02-12
**Synthesized From:**
- `docs/research/findings/RQ_SPARK_001_A_SCHEMA_AND_UNITS.md` (Schema, Units, Defaults)
- `docs/research/findings/RQ_SPARK_001_B_PROMPTING_VALIDATION_LAYOUT.md` (Prompting, Validation, Layout)
- `docs/research/findings/RQ_SPARK_001_C_IMPROVISATION_AND_NPCS.md` (Improvisation, NPC Generation)

**Reconciled Against Codebase:**
- `aidm/lens/narrative_brief.py` (NarrativeBrief one-way valve pattern)
- `aidm/schemas/geometry.py` (PropertyFlag, PropertyMask, GridCell, SizeCategory, CellState, Direction)
- `aidm/core/lens_index.py` (SourceTier authority hierarchy)
- `aidm/core/fact_acquisition.py` (FactAcquisitionManager, FactRequest/FactResponse)

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Normative Statements Register](#2-normative-statements-register)
3. [Contradiction Analysis and Resolutions](#3-contradiction-analysis-and-resolutions)
4. [Canonical Structured Output Schema](#4-canonical-structured-output-schema)
5. [Provenance and Authority Model](#5-provenance-and-authority-model)
6. [Failure Taxonomy](#6-failure-taxonomy)
7. [Retry, Repair, and Hard Stop Policy](#7-retry-repair-and-hard-stop-policy)
8. [Ship Thresholds](#8-ship-thresholds)
9. [Adversarial and Edge-Case Examples](#9-adversarial-and-edge-case-examples)
10. [Test Map](#10-test-map)
11. [Appendix A: Reconciliation with NarrativeBrief](#appendix-a-reconciliation-with-narrativebrief)
12. [Appendix B: Full Normative Statement Provenance](#appendix-b-full-normative-statement-provenance)

---

## 1. Purpose and Scope

This document is the **canonical contract** governing how Spark (the generative LLM layer) emits structured facts that Lens (the indexing layer) validates and Box (the rules engine) consumes. It synthesizes findings from three sub-dispatch research documents into a single, self-contained specification.

**The contract defines:**
- What Spark MUST emit, MAY emit, and MUST NOT emit
- The JSON schema for all emission types (scene, improvisation patch, NPC/encounter)
- How Lens validates, repairs, and indexes emissions
- When the system gives up and falls back to safe defaults
- Quantitative thresholds required before shipping

**The contract does NOT define:**
- Implementation code (that is for work order dispatch)
- The specific Spark system prompt (only the mandatory fragments)
- Box-side rules resolution (only the interface contract)

**Terminology:**
- "Spark emission" = any structured JSON output from the Spark LLM
- "Scene Fact Pack" = the full scene description emission (prep-time)
- "Fact Completion Patch" = a minimal improvisation emission (runtime)
- "NPC Emission" = creature stat block + tactical role emission
- "Encounter Emission" = group of NPC emissions with CR calculation

---

## 2. Normative Statements Register

All normative statements (MUST, SHOULD, MUST-NOT) extracted from the three sub-findings, deduplicated and organized by domain.

### 2.1 Schema and Structure

| ID | Level | Statement | Source |
|----|-------|-----------|--------|
| S-001 | MUST | All Spark emissions MUST conform to the `scene_fact_pack_v1` JSON schema or the `fact_completion_patch_v1` schema | A SS1.1, B SS4 |
| S-002 | MUST | All numeric fields carrying units MUST include the unit suffix (`_ft`, `_lb`, `_sq`) | A SS2.4 |
| S-003 | MUST | Grid position fields (`position.x`, `position.y`) MUST be non-negative integers representing 0-indexed square indices | A SS1.3, A SS2.2 |
| S-004 | MUST | Position values MUST satisfy `0 <= x < scene.dimensions.width_sq` and `0 <= y < scene.dimensions.height_sq` | A SS1.3 |
| S-005 | MUST | Boolean mechanical fields (solidity, opacity, affordances) MUST be boolean values, never prose | A SS1.1 principle 3 |
| S-006 | MUST | `scene_id` and `scene_version` MUST be present on every Scene Fact Pack emission | A SS1.2 |
| S-007 | MUST | `scene_version` MUST be a monotonically increasing integer starting at 1 | A SS1.2 |
| S-008 | MUST | Each `object_id`, `creature_id`, `zone_id`, and `border_id` MUST be unique within its scene | A SS1.3-1.6 |
| S-009 | MUST | `condition` values MUST be one of: `intact`, `damaged`, `broken`, `destroyed` | A SS1.3 |
| S-010 | MUST | Condition transitions MUST be one-way: intact -> damaged -> broken -> destroyed | A SS1.3, B SS4 |
| S-011 | MUST | `size` for creatures MUST be one of the nine D&D 3.5e size categories: fine, diminutive, tiny, small, medium, large, huge, gargantuan, colossal | A SS1.4 |
| S-012 | MUST | `space_ft` and `reach_ft` for creatures MUST be consistent with the size-to-space table (PHB p.149) | A SS1.4 |
| S-013 | MUST | `material` for objects MUST be one of the defined enum values: wood, stone, iron, steel, glass, cloth, bone, crystal, earth, ice | A SS1.3 |
| S-014 | MUST | Scene `dimensions.width_sq` and `dimensions.height_sq` MUST be integers in range 1-100 | A SS1.2 |
| S-015 | MUST | Every Spark emission MUST include a `provenance` field set to `SPARK_GENERATED` or `SPARK_IMPROVISED` | A SS1.2, C SS1.4 |
| S-016 | MUST | Improvisation patches MUST use `fact_completion` as `patch_type` and emit only new/missing facts, never a full scene re-emission | C SS1.2 |
| S-017 | MUST | Improvisation patches MUST NOT contain prose; prose narration is a separate request | C SS1.2 |
| S-018 | MUST | NPC emissions MUST prefer stat block references (`stat_block_ref`) over custom stat blocks | C SS2.2.1 |
| S-019 | MUST | Custom NPC stat blocks MUST include AC breakdown, BAB, grapple, saves, abilities, feats, and CR | C SS2.5 |
| S-020 | MUST | Encounter emissions MUST include `target_el`, `calculated_el`, `difficulty`, and `cr_breakdown` | C SS2.3.1 |
| S-021 | MUST-NOT | Spark MUST NOT use metric units anywhere in emissions | A SS2.3 |
| S-022 | MUST-NOT | Spark MUST NOT use fractional grid coordinates | A SS2.3 |
| S-023 | MUST-NOT | Spark MUST NOT invent size categories outside the D&D 3.5e list | A SS2.3 |
| S-024 | MUST-NOT | Spark MUST NOT output grid coordinates directly for scene layout; spatial placement is handled by procedural code | B SS5 |
| S-025 | MUST-NOT | Spark MUST NOT use D&D 5e mechanics (advantage/disadvantage, proficiency bonus, concentration, death saves, short rests) | C SS2.4 |
| S-026 | MUST-NOT | Lens MUST NOT perform full scene replacement on re-emission; field-by-field diff is required | A SS5.5 |
| S-027 | SHOULD | Object IDs SHOULD use descriptive snake_case (e.g., `tavern_table_01`) | A SS6.3 |
| S-028 | SHOULD | Encounters SHOULD include a mix of tactical roles (brawler, archer, controller, skirmisher, tank) rather than all-brawler compositions | C SS2.3.2 |
| S-029 | SHOULD | NPC emissions SHOULD include `role_tags` and `tactical_behavior` for AI controller guidance | C SS2.2.2 |
| S-030 | SHOULD | NPC emissions SHOULD include `environment_tie` linking positioning to terrain features | C SS2.2.3 |
| S-031 | SHOULD | Equipment with geometric effects (tower shields, reach weapons) SHOULD be declared in `equipment_geometry` | C SS2.2.4 |

### 2.2 Prompting and Generation

| ID | Level | Statement | Source |
|----|-------|-----------|--------|
| P-001 | MUST | Structured output calls MUST use GBNF grammar-constrained decoding via `response_format={"type": "json_object", "schema": {...}}` | B SS3 Rank 1 |
| P-002 | MUST | All structured output requests MUST prepend `/no_think` soft switch to the user message (NOT `enable_thinking=False`, which breaks Qwen3 structured output) | B SS3 |
| P-003 | MUST | Structured output calls MUST use temperature 0.7, TopP 0.8, TopK 20 per Qwen3 guidance | B SS3 |
| P-004 | MUST | Structured output calls MUST NOT set `max_tokens` (prevents incomplete JSON when grammar hasn't reached terminal state) | B SS3 |
| P-005 | MUST | The Spark system prompt MUST include the unit rules fragment and UNKNOWN discipline fragment from A SS4.5 | A SS4.5 |
| P-006 | MUST | All Spark output MUST be post-validated with Pydantic regardless of grammar enforcement (grammar fail-open mode silently produces unconstrained output) | B SS3 Rank 1, B SS4 |
| P-007 | MUST | Temperature 0.0 MUST NOT be used with Qwen3 (causes endless repetitions and performance degradation) | B SS3 |
| P-008 | SHOULD | Complex scene generation SHOULD use two-pass generation (narrative draft, then structured extraction) for 5-8% improvement in semantic quality | B SS3 Rank 2 |
| P-009 | SHOULD | System prompts SHOULD include 2-3 archetype examples per scene type (compact, within 500-800 token budget) | B SS3 Rank 3 |
| P-010 | SHOULD | Stop sequence SHOULD be `<|im_end|>` only; the existing `JSON_STOP_SEQUENCES = ["}\n", "}\n\n"]` interferes with nested JSON and SHOULD be removed for grammar-constrained calls | B SS3 Rank 4 |

### 2.3 Validation and Repair

| ID | Level | Statement | Source |
|----|-------|-----------|--------|
| V-001 | MUST | Lens MUST validate in three ordered layers: (1) JSON parse + Pydantic schema, (2) D&D 3.5e rules, (3) spatial consistency | B SS4 |
| V-002 | MUST | Before Pydantic parsing, Lens MUST strip markdown fences, preambles, and thinking tokens from raw output | B SS4 Layer 1 |
| V-003 | MUST | Lens MUST cross-check creature `space_ft` against `size` using the PHB p.149 size-to-space table; mismatches are rejected | A SS1.4 |
| V-004 | MUST | Lens MUST detect spatial overlaps: no two solid objects may occupy the same grid cell unless one is non-solid | B SS4 Layer 3 |
| V-005 | MUST | Lens MUST detect out-of-bounds placement: all object/creature footprints must fit within scene dimensions | B SS4 Layer 3 |
| V-006 | MUST | Repair attempts MUST be capped at maximum 2 (total 3 attempts including initial generation) | B SS4 Repair Protocol |
| V-007 | MUST | For 1-3 failed fields, repair MUST use targeted JSON patch approach (send only failed fields + error messages); for >50% fields invalid, MUST trigger full regeneration | B SS4 Repair Protocol |
| V-008 | MUST | After 2 failed repair attempts, Lens MUST apply partial merge with archetype defaults (keep valid fields, substitute defaults for invalid fields) | B SS4 Fallback Strategy |
| V-009 | MUST | Lens MUST validate improvised facts against prior facts for spatial overlap and retroactive contradictions | C SS1.5 |
| V-010 | MUST | Lens MUST reject new Spark values that contradict `BOX_CANONICAL` cached values (drift prevention) | A SS5.2.2 |
| V-011 | MUST | Lens MUST accept SPARK_GENERATED values that upgrade ASSUMED_STANDARD cached values (better data replaces defaults) | A SS5.2.2 |
| V-012 | MUST | Lens MUST reject SPARK_GENERATED values that differ from first-seen SPARK_GENERATED cached values (detail drift prevention) | A SS5.2.2 |
| V-013 | MUST | Every rejected drift attempt MUST be logged with scene_id, object_id, field, cached_value, new_value, and action taken | A SS5.2.3 |
| V-014 | MUST | NPC stat blocks MUST be validated for AC derivation, BAB, saves, grapple, feat count, feat prerequisites, and HP calculation | C SS3.2 |
| V-015 | MUST | Encounter CR calculations MUST be validated against DMG Table 3-1 with multiple-creature adjustment per DMG p.49 | C SS2.3.1 |
| V-016 | MUST | Pydantic validation errors MUST be reformatted as natural-language correction instructions before re-prompting Spark | B SS4 Layer 1 |
| V-017 | MUST-NOT | Lens MUST NOT invent facts; it validates and indexes only | B SS4, C SS1.8 |
| V-018 | SHOULD | Repair logging SHOULD track: scene_id, timestamp, attempt_number, errors, repair_successful, fallback_used, tokens_used | B SS4 Repair Logging |

### 2.4 UNKNOWN Handling

| ID | Level | Statement | Source |
|----|-------|-----------|--------|
| U-001 | MUST | When Spark lacks certainty about a numeric dimension, it MUST emit the string `"UNKNOWN"` instead of guessing | A SS4.1 |
| U-002 | MUST | When Lens receives `"UNKNOWN"`, it MUST look up the archetype by `object.class`, substitute the archetype default, and tag the fact as `ASSUMED_STANDARD` with `SourceTier.DEFAULT` | A SS4.2 |
| U-003 | MUST | If no archetype is found for an UNKNOWN value, the scene MUST be rejected (missing archetype = schema error) | A SS4.2 |
| U-004 | MUST | `position` (x, y) MUST never be UNKNOWN; if Spark cannot place an object, it MUST omit the object entirely | A SS4.4 |
| U-005 | MUST | `size` (creature), `solidity`, `opacity`, and `condition` MUST never be UNKNOWN | A SS4.4 |
| U-006 | MAY | `dimensions.length_ft`, `dimensions.width_ft`, `dimensions.height_ft`, `weight_lb`, `hardness`, `hit_points`, and `elevation_ft` MAY be UNKNOWN | A SS4.4 |

### 2.5 Detail Drift Prevention

| ID | Level | Statement | Source |
|----|-------|-----------|--------|
| D-001 | MUST | Lens MUST maintain a first-seen cache per scene: `Dict[scene_id, Dict[object_id, Dict[field_path, CachedValue]]]` | A SS5.2.1 |
| D-002 | MUST | On scene re-emission, Lens MUST perform field-by-field diff, never wholesale replacement | A SS5.4 |
| D-003 | MUST | New objects (not in cache) MUST be accepted and cached | A SS5.4 |
| D-004 | MUST | Missing objects (in cache but absent from re-emission) MUST be kept from cache (object still exists) | A SS5.4 |
| D-005 | MUST | Position changes MUST only be accepted if Box has not placed the entity on the grid; once on BattleGrid, position is BOX_CANONICAL | A SS5.4 |
| D-006 | MUST | Scene cache MUST persist for session lifetime and serialize with session state | A SS5.2.4 |
| D-007 | SHOULD | Spark requests SHOULD include a seed parameter derived from scene_id (`hash(scene_id) % (2**31)`) as a supplementary stability measure | A SS5.3 |

---

## 3. Contradiction Analysis and Resolutions

### 3.1 Provenance Hierarchy: Four Tiers vs Five Tiers

**Contradiction:** Sub-finding A (SS4.3) defines three provenance tags (`SPARK_GENERATED`, `ASSUMED_STANDARD`, `BOX_CANONICAL`). Sub-finding C (SS3.1) defines five authority levels (`PLAYER_INPUT`, `BOX`, `SPARK_GENERATED`, `SPARK_IMPROVISED`, `NARRATIVE`). The existing codebase (`aidm/core/lens_index.py` lines 23-40) defines five `SourceTier` values (`BOX=1`, `CANONICAL=2`, `PLAYER=3`, `SPARK=4`, `DEFAULT=5`).

**Resolution:** Adopt a unified six-tier model that merges all three sources. The existing `SourceTier` enum is the foundation; we add `SPARK_IMPROVISED` between `SPARK` and `DEFAULT`, and treat `ASSUMED_STANDARD` as an alias for `DEFAULT`. The `NARRATIVE` tier from C maps to a metadata annotation, not a SourceTier, because narrative flavor text is not a "fact" in the Lens sense.

| Tier | SourceTier Value | Provenance Tag | Origin |
|------|-----------------|---------------|--------|
| 1 (highest) | `BOX` | `BOX_CANONICAL` | Box mechanical truth (HP, resolved positions) |
| 2 | `CANONICAL` | `RULEBOOK` | D&D 3.5e rulebook constants |
| 3 | `PLAYER` | `PLAYER_INPUT` | Explicit player statements |
| 4 | `SPARK` | `SPARK_GENERATED` | Prep-time Spark emissions |
| 5 (new) | `SPARK_IMPROV` | `SPARK_IMPROVISED` | Runtime improvisation emissions |
| 6 (lowest) | `DEFAULT` | `ASSUMED_STANDARD` | Archetype defaults for UNKNOWN values |

**Rationale:** The existing `SourceTier` enum already has the right authority ordering. Sub-finding C's `SPARK_IMPROVISED` is genuinely lower authority than prep-time `SPARK_GENERATED` (C SS1.4 lines 146-157: "Lens can override SPARK_IMPROVISED more easily than SPARK_GENERATED"), so it warrants a separate tier. The `NARRATIVE` tier from C SS3.1 is not a fact tier -- it is a content-type marker for prose that Lens does not index as structured data.

### 3.2 NPC Position Coordinates: Sub-findings B vs C

**Contradiction:** Sub-finding B (SS5, line 1023-1025) states: "Spark should generate descriptions, not coordinates. All coordinate-level placement must be handled by deterministic procedural code." Sub-finding C (SS2.2.3, SS2.3.3) includes NPC `initial_position` with explicit grid coordinates (`{"x": 10, "y": 15}`).

**Resolution:** The B finding applies to **scene layout generation** (object/furniture placement). The C finding applies to **encounter tactical positioning** where NPCs are placed relative to already-placed terrain features. These are different contexts:

- **Scene layout:** Spark emits placement hints (`north_wall`, `center`), NOT coordinates. Procedural CSP solver does placement. (Per B.)
- **Encounter NPC positioning:** Spark MAY emit suggested `initial_position` coordinates because NPCs are placed AFTER the scene grid is finalized. However, these positions are **suggestions only** -- Lens MUST validate them (bounds, overlaps, terrain compatibility) and Box has final authority. If Spark-suggested NPC positions fail validation, the procedural placement engine repositions them.

**Normative addition:** S-024 is amended: "Spark MUST NOT output grid coordinates for scene object/furniture layout. Spark MAY suggest initial_position for encounter NPCs, but these are advisory and subject to Lens spatial validation."

### 3.3 Scene Schema Duplication: Sub-findings A vs B

**Contradiction:** Sub-finding A defines the full `SceneFactPack` schema with detailed object, creature, terrain, and border sub-schemas (A SS1.2-1.6). Sub-finding B defines a separate, simpler scene description schema for hybrid layout generation (B SS5 "Spark's JSON schema for scene description") that uses `placement_hint` enum values instead of grid positions, and `furniture` as a type-to-count dict instead of detailed object records.

**Resolution:** These are two different emission types used at different pipeline stages:

1. **SceneDescription** (B's schema): Used during initial scene **intent** generation. Spark outputs what SHOULD exist (room type, atmosphere, landmark types with placement hints, furniture counts). The procedural CSP solver converts this into a placed layout.

2. **SceneFactPack** (A's schema): The **canonical output** after procedural placement. Contains all objects with resolved grid positions, full property details, and Box-ready PropertyFlag data. This is what Lens indexes and Box consumes.

The generation pipeline is: `Spark -> SceneDescription -> CSP Solver -> SceneFactPack -> Lens Validation -> BattleGrid`

Spark may also emit a SceneFactPack directly for pre-authored scenes or DM-provided layouts, bypassing the CSP solver. Both paths converge at Lens validation.

### 3.4 Archetype Templates: Sub-findings A vs C Dimension Ranges

**Contradiction:** Sub-finding A (SS3.1-3.3) defines archetype defaults as **fixed values** (e.g., `tavern_table: L=3, W=3, H=2.5`). Sub-finding C (SS1.3) defines archetype templates with **dimension ranges** (e.g., `storage_room: length_ft=[10,20], width_ft=[8,15]`).

**Resolution:** Both are correct for their respective scopes:

- **Object archetypes** (A): Use fixed default values. When Spark emits UNKNOWN for a tavern_table dimension, the resolution is deterministic: substitute the canonical default. Fixed defaults prevent drift and ensure reproducibility.
- **Room archetypes** (C): Use dimension ranges. When Spark improvises a new room behind a door, it selects within the range, and Lens validates the selection falls within bounds.

**Normative addition:** Object archetype defaults are FIXED values (deterministic substitution). Room archetype defaults are RANGES (Spark selects, Lens validates bounds).

### 3.5 Confidence Tags: Sub-finding A vs C

**Contradiction:** Sub-finding A (SS4.3) defines provenance labels per dimension value (`SPARK_GENERATED`, `ASSUMED_STANDARD`, `BOX_CANONICAL`). Sub-finding C (SS1.4) adds a separate `material_confidence` / `hardness_confidence` field with different labels (`KNOWN`, `ASSUMED_STANDARD`, `CALCULATED`, `UNKNOWN`).

**Resolution:** Use the SourceTier system (Section 5) as the single provenance mechanism. The per-field confidence tags from C are informational metadata, not a parallel authority system. Map them:

| C's Confidence | SourceTier Equivalent |
|---------------|----------------------|
| `KNOWN` | `SPARK` (explicitly stated by Spark) |
| `ASSUMED_STANDARD` | `DEFAULT` (archetype lookup) |
| `CALCULATED` | `CANONICAL` (derived from D&D 3.5e rules) |
| `UNKNOWN` | Not stored -- triggers UNKNOWN resolution pipeline |

The per-field confidence tags from C SHOULD be stored as metadata annotations on LensFact entries for debugging/transparency, but SourceTier remains the authoritative override mechanism.

---

## 4. Canonical Structured Output Schema

### 4.1 Emission Type Registry

| Emission Type | Schema Version | When Used | Spark Generates Coordinates? |
|--------------|---------------|-----------|------------------------------|
| `SceneDescription` | `scene_description_v1` | Initial scene intent (hybrid layout) | NO (placement hints only) |
| `SceneFactPack` | `scene_fact_pack_v1` | Full scene data (after CSP or pre-authored) | YES (resolved by CSP or DM) |
| `FactCompletionPatch` | `fact_completion_patch_v1` | Runtime improvisation | NO (for objects), advisory (for NPC positions) |
| `NPCEmission` | `npc_emission_v1` | NPC stat block generation | Advisory initial_position |
| `EncounterEmission` | `encounter_emission_v1` | Full encounter with CR | Advisory NPC positions |

### 4.2 SceneFactPack v1 (Canonical)

This is the primary schema. Source: A SS1.2-1.6, reconciled with existing `aidm/schemas/geometry.py`.

**Top-level required fields:** `$schema`, `scene_id`, `scene_version`, `provenance`, `metadata`, `dimensions`
**Top-level optional fields:** `objects`, `creatures`, `terrain_zones`, `borders`

```
SceneFactPack {
  $schema: "scene_fact_pack_v1"                     # REQUIRED, literal
  scene_id: string (non-empty)                       # REQUIRED, unique
  scene_version: integer (>= 1, monotonic)           # REQUIRED
  provenance: "SPARK_GENERATED"                      # REQUIRED, literal
  metadata: SceneMetadata                            # REQUIRED
  dimensions: {width_sq: int 1-100, height_sq: int 1-100}  # REQUIRED
  objects: [SceneObject]                             # default []
  creatures: [SceneCreature]                         # default []
  terrain_zones: [TerrainZone]                       # default []
  borders: [BorderOverride]                          # default []
}
```

**SceneObject required fields:** `object_id`, `class`, `material`, `dimensions` (all three sub-fields), `position`, `solidity`, `opacity`, `mobility`, `condition`

**SceneCreature required fields:** `creature_id`, `name`, `size`, `space_ft`, `reach_ft`, `position`

**TerrainZone required fields:** `zone_id`, `zone_type`, `region` (all four sub-fields)

**BorderOverride required fields:** `border_id`, `position`, `direction`, `solid`, `opaque`

Full field-level detail: see A SS1.3-1.6 (reproduced verbatim in the sub-finding; not duplicated here to avoid staleness -- the sub-finding is the field-level source of truth until Pydantic models are implemented).

### 4.3 SceneDescription v1 (Intent Schema for Hybrid Layout)

Source: B SS5 "Spark's JSON schema for scene description."

```
SceneDescription {
  room_type: enum [tavern, dungeon_corridor, dungeon_chamber,
                   throne_room, cave, forest_clearing, street,
                   temple, library, prison_cell]              # REQUIRED
  size_category: enum [tiny, small, medium, large, huge]      # REQUIRED
  atmosphere: enum [calm, tense, festive, abandoned, eerie]   # REQUIRED
  lighting: enum [bright, dim, dark]                          # REQUIRED
  landmarks: [{type: string, placement_hint: enum, description?: string}]  # REQUIRED, max 6
  furniture: {string -> int 0-10}                             # REQUIRED
  special_features?: [{type: string, near?: string, description?: string}]  # max 3
  tactical_intent?: enum [open_battle, defensible, ambush,
                          chokepoint, multi_level, hazardous]
  description: string                                         # REQUIRED
}
```

**placement_hint enum:** `north_wall`, `south_wall`, `east_wall`, `west_wall`, `center`, `corner`, `any`

**size_category to grid dimensions mapping:**
- `tiny`: 4x4 (20x20ft)
- `small`: 6x6 (30x30ft)
- `medium`: 8x10 (40x50ft)
- `large`: 12x14 (60x70ft)
- `huge`: 16x20 (80x100ft)

### 4.4 FactCompletionPatch v1 (Improvisation)

Source: C SS1.2, reconciled with existing FactRequest/FactResponse patterns in `aidm/core/fact_acquisition.py`.

```
FactCompletionPatch {
  patch_type: "fact_completion"                       # REQUIRED, literal
  patch_id: string (UUID)                             # REQUIRED
  trigger: string (e.g., "player_query", "door_opened")  # REQUIRED
  query?: string                                      # original player query
  new_facts: [NewFact]                                # REQUIRED, non-empty
  prose_summary: null                                 # MUST be null (prose is separate)
}

NewFact {
  fact_id: string (UUID)                              # REQUIRED
  object_id: string                                   # REQUIRED
  fact_type: string (e.g., "room_layout", "object_property", "npc_equipment")  # REQUIRED
  archetype?: string                                  # archetype used as template
  properties: {string -> any}                         # REQUIRED, fact key-value pairs
  provenance: "SPARK_IMPROVISED"                      # REQUIRED, literal
  source_context?: string                             # explanation of why this was generated
}
```

**Relationship to existing FactAcquisitionManager:** The `FactCompletionPatch` is a bulk version of the existing single-entity `FactResponse`. The `FactAcquisitionManager.apply_response()` method (line 426-458 of `fact_acquisition.py`) stores facts with `SourceTier.SPARK`. Improvisation patches MUST be stored with the new `SourceTier.SPARK_IMPROV` tier instead.

### 4.5 NPCEmission v1

Source: C SS2.5, reconciled with existing geometry schemas.

```
NPCEmission {
  npc_id: string                                      # REQUIRED, unique
  name?: string                                       # for named NPCs
  stat_block_ref?: string (e.g., "MM_GOBLIN_WARRIOR") # PREFERRED over custom
  custom_stat_block?: CustomStatBlock                  # fallback for unique NPCs
  role_tags: [enum: brawler, archer, controller, skirmisher, tank]  # REQUIRED
  tactical_behavior?: {
    preferred_range_ft: int,
    retreat_threshold_hp_pct: int 0-100,
    uses_cover: bool,
    flanks_when_possible: bool,
    ai_hints?: string
  }
  initial_position?: {x: int, y: int, elevation_ft?: int}  # advisory only
  environment_tie?: string
  equipment_geometry?: {
    weapon_primary: string,
    reach_ft: int,
    threatens_squares?: string,
    provides_cover?: bool,
    notes?: string
  }
  provenance: "SPARK_GENERATED" | "SPARK_IMPROVISED"  # REQUIRED
}
```

**Exactly one of `stat_block_ref` or `custom_stat_block` MUST be non-null.**

### 4.6 Reconciliation with NarrativeBrief

The `NarrativeBrief` (defined in `aidm/lens/narrative_brief.py`) is a **separate data flow** from the Spark Emission Contract. Key distinctions:

| Aspect | NarrativeBrief | Spark Emission |
|--------|---------------|----------------|
| Direction | Box -> Lens -> Spark (output to LLM) | Spark -> Lens -> Box (input from LLM) |
| Purpose | Provide safe context for narration | Provide structured facts for game state |
| Contains coordinates | NEVER (containment boundary) | YES (grid positions for objects/creatures) |
| Contains HP/AC | NEVER | YES (for NPC stat blocks) |
| Provenance | Always `[DERIVED]` from Box STPs | `SPARK_GENERATED` or `SPARK_IMPROVISED` |

These two systems are complementary, not overlapping. NarrativeBrief controls what Spark can SEE. The Spark Emission Contract controls what Spark can EMIT. They form a bidirectional containment boundary:

```
Box --[NarrativeBrief]--> Lens --[safe context]--> Spark
Spark --[Emission Contract]--> Lens --[validated facts]--> Box
```

See Appendix A for detailed reconciliation.

---

## 5. Provenance and Authority Model

### 5.1 Unified SourceTier Hierarchy

Extension of existing `SourceTier` enum (`aidm/core/lens_index.py` lines 23-40):

| Tier | IntEnum Value | Tag | Override Rules |
|------|-------------|-----|---------------|
| `BOX` | 1 | `BOX_CANONICAL` | Only overridable by BOX (self-correction) |
| `CANONICAL` | 2 | `RULEBOOK` | Only overridable by BOX |
| `PLAYER` | 3 | `PLAYER_INPUT` | Overridable by BOX, CANONICAL |
| `SPARK` | 4 | `SPARK_GENERATED` | Overridable by BOX, CANONICAL, PLAYER |
| `SPARK_IMPROV` | 5 | `SPARK_IMPROVISED` | Overridable by all above |
| `DEFAULT` | 6 | `ASSUMED_STANDARD` | Overridable by all above |

**Override rules (from A SS5.2.2, C SS3.1):**
- Higher-tier always overrides lower-tier.
- Same-tier: first-seen wins for `SPARK` (detail drift prevention per D-001). Newer wins for `SPARK_IMPROV` with a conflict warning logged.
- `BOX` values are frozen and never overridable by any non-BOX source.
- `DEFAULT` values are always upgradeable when a better source provides data.

### 5.2 Cache Architecture (Detail Drift Prevention)

Per A SS5.2.1, the scene cache stores the first-seen value for every field:

```
SceneCache = Dict[scene_id, Dict[object_id, Dict[field_path, CachedValue]]]

CachedValue:
  value: Any
  source: SourceTier
  turn_cached: int
  frozen: bool  # True for BOX values
```

**Ingestion protocol on re-emission (A SS5.2.2):**
1. Field not in cache -> Accept and cache.
2. Field in cache, values match -> Accept (no drift).
3. Field in cache, values differ, cache is `BOX` -> REJECT new value, keep cache, log.
4. Field in cache, values differ, both `SPARK` -> REJECT new value, keep first-seen, log.
5. Field in cache, values differ, cache is `DEFAULT` and new is `SPARK` -> ACCEPT upgrade, update cache.
6. All other cases -> REJECT, log warning.

---

## 6. Failure Taxonomy

### 6.1 Classification

| ID | Failure Class | Detection Layer | Severity | Example |
|----|--------------|----------------|----------|---------|
| F-001 | **JSON Parse Failure** | Layer 1 (pre-Pydantic) | HARD | Truncated JSON, markdown fences, thinking tokens in output |
| F-002 | **Schema Validation Failure** | Layer 1 (Pydantic) | HARD | Missing required field, wrong type, invalid enum value |
| F-003 | **UNKNOWN Resolution Failure** | Layer 1 (post-Pydantic) | HARD | UNKNOWN value with no matching archetype in registry |
| F-004 | **D&D 3.5e Rules Violation** | Layer 2 (rules) | MEDIUM | Size/space mismatch, table height 500ft, invalid material hardness |
| F-005 | **5e Contamination** | Layer 2 (rules) | MEDIUM | Advantage/disadvantage, proficiency bonus, concentration |
| F-006 | **Spatial Overlap** | Layer 3 (spatial) | MEDIUM | Two solid objects at same grid cell |
| F-007 | **Out-of-Bounds** | Layer 3 (spatial) | MEDIUM | Object footprint extends beyond scene dimensions |
| F-008 | **Connectivity Violation** | Layer 3 (spatial) | LOW | Placed objects make some floor cells unreachable from all doors |
| F-009 | **Detail Drift** | Cache check | LOW | Re-emitted value differs from first-seen cached value |
| F-010 | **Box Contradiction** | Cross-system | HIGH | Spark emission contradicts BOX_CANONICAL fact (e.g., wall Spark says is intact was already destroyed in combat) |
| F-011 | **NPC Stat Block Invalid** | Layer 2 (rules) | MEDIUM | Wrong feat count, prerequisite chain broken, AC derivation mismatch |
| F-012 | **Encounter CR Mismatch** | Layer 2 (rules) | LOW | Calculated EL does not match target EL |
| F-013 | **Grammar Fail-Open** | Layer 1 (detection) | HIGH | Grammar parse failure caused llama.cpp to generate unconstrained output silently |
| F-014 | **Token Exhaustion** | Layer 1 (detection) | HARD | Grammar could not force early closure, output truncated mid-JSON |
| F-015 | **Improvisation Contradiction** | Cross-system | MEDIUM | New improvised fact contradicts established scene fact |

### 6.2 Severity Definitions

| Severity | Meaning | System Response |
|----------|---------|----------------|
| **HARD** | Output is not parseable or fundamentally broken | Must retry or fall back entirely |
| **HIGH** | Output is parseable but contradicts authoritative truth | Reject affected fields, keep valid fields |
| **MEDIUM** | Output violates D&D rules or spatial constraints | Attempt targeted repair, then default substitution |
| **LOW** | Output is valid but suboptimal or inconsistent | Log warning, apply policy (keep first-seen, adjust CR) |

---

## 7. Retry, Repair, and Hard Stop Policy

### 7.1 Decision Flow

```
Spark emits structured output
         |
         v
  [Strip fences/preambles]  -----> (F-001 if no JSON found)
         |
         v
  [Pydantic validation]  --------> (F-002 / F-003)
         |                    |
      VALID              INVALID
         |                    |
         v                    v
  [D&D 3.5e rules check]  [Count invalid fields]
         |                    |
      VALID            +------+------+
         |             |             |
         v          <= 50%        > 50%
  [Spatial check]   INVALID      INVALID
         |             |             |
      VALID            v             v
         |      [Targeted Repair]  [Full Regeneration]
         v      (patch approach)   (new Spark call)
  [Cache drift     |                  |
   check]       Attempt 1          Attempt 1
         |         |                  |
      PASS     +---+---+         +---+---+
         |     |       |         |       |
         v   PASS   FAIL       PASS   FAIL
  [Accept]    |       |         |       |
              v       v         v       v
           [Accept] Attempt 2  [Accept] Attempt 2
                      |                   |
                  +---+---+          +---+---+
                  |       |          |       |
                PASS   FAIL        PASS   FAIL
                  |       |          |       |
                  v       v          v       v
              [Accept] [Partial   [Accept] [Partial
                        Merge              Merge
                        w/Defaults]        w/Defaults]
```

### 7.2 Repair Request Format

For targeted repair (1-3 failed fields), Spark receives (per B SS4 Repair Protocol):

```
/no_think
Your previous output had validation errors. Fix ONLY these fields:

ERRORS:
- objects[0].height_ft = 500 -> max reasonable height is 15ft for this archetype
- objects[1].size = "gigantic" -> must be one of: fine/diminutive/tiny/small/medium/large/huge/gargantuan/colossal
- objects[2].position.x = -1 -> must be >= 0

Output ONLY the corrected fields as JSON:
```

Grammar-constrained patch schema:
```json
{
  "corrections": [
    {"path": "objects[0].height_ft", "value": 10},
    {"path": "objects[1].size", "value": "large"},
    {"path": "objects[2].position.x", "value": 0}
  ]
}
```

### 7.3 Hard Stop Conditions

The system MUST stop retrying and apply archetype fallback when:

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Repair attempts exhausted | 2 repairs failed | Partial merge with archetype defaults |
| No JSON extractable from output | Immediate (no retry) | Full archetype template fallback |
| Grammar fail-open detected | Immediate (1 retry with logged warning) | If retry also fails, full archetype fallback |
| Token exhaustion (truncated JSON) | Immediate (1 retry with logged warning) | Archetype fallback |
| BOX contradiction detected | Immediate (no retry) | Reject contradicting fields, keep BOX values |
| Total generation latency exceeds 3000ms | Immediate hard stop | Archetype fallback |

### 7.4 Partial Merge with Archetype Defaults

When repair fails, the system preserves valid fields and substitutes defaults for invalid fields (per B SS4 Fallback Strategy):

1. Identify which fields passed validation.
2. Identify which fields failed.
3. For each failed field: look up archetype default by `object.class`.
4. If archetype found: substitute default value, tag as `ASSUMED_STANDARD`.
5. If no archetype found: use material-based defaults from DMG (A SS3.4).
6. If neither available: omit the object from the scene and log a warning.

**Key principle:** A partial scene with valid objects is better than no scene or a fully hallucinated scene.

---

## 8. Ship Thresholds

Quantitative criteria that must be met before the Spark Emission Contract implementation can be considered shippable.

### 8.1 Schema Compliance Rate

| Metric | Target | Alert Threshold | Measurement |
|--------|--------|-----------------|-------------|
| First-attempt validation pass rate | >= 80% | < 70% | Pydantic + D&D rules + spatial (all three layers) |
| Pass rate after repair (max 2 retries) | >= 95% | < 90% | Same three layers |
| Archetype fallback frequency | <= 5% of all emissions | > 10% | Count of partial-merge fallbacks / total emissions |

Source: B SS4 Monitoring Metrics (lines 930-937).

### 8.2 Retry Bounds

| Metric | Target | Hard Limit |
|--------|--------|------------|
| Maximum repair attempts per emission | 2 | MUST NOT exceed 2 (3 total attempts) |
| Retry count distribution mode | 0 (most pass first try) | Alert if mode shifts to 1+ |
| Token cost overhead for retries | < 25% of base generation cost | Alert if > 50% |

### 8.3 Latency Constraints

| Metric | Target | Hard Limit |
|--------|--------|------------|
| Total emission latency (generation + validation + retries) P50 | < 200ms | N/A |
| Total emission latency P95 | < 500ms | 1000ms |
| Total emission latency P99 | < 1000ms | 3000ms (hard stop) |
| Validation-only latency (no retries) | < 50ms | 100ms |
| Single repair round-trip | < 300ms | 500ms |

Source: B SS4 Monitoring Metrics (lines 937: "total_latency_p95: <500ms incl. retries, alert >1s").

### 8.4 Content Quality

| Metric | Target | Measurement |
|--------|--------|-------------|
| D&D 3.5e rules compliance (no 5e contamination) | 100% | Automated rules validators |
| Size/space consistency | 100% | Cross-check creature size vs space_ft |
| Spatial validity (no overlaps, in-bounds) | >= 98% after placement | Spatial validator |
| Detail drift rejection rate | Track only (no target) | Count of drift rejections per session |
| NPC feat prerequisite validity | 100% | Automated chain validator |
| Encounter EL accuracy (within +/-1 of target) | >= 95% | DMG Table 3-1 calculator |

### 8.5 Per-Field Diagnostics

The following per-field metrics MUST be tracked from day one (per B SS4 Tier 2 Monitoring):

- `field_failure_rate{field=X}`: Which fields fail validation most often
- `field_error_type{field=X, error=Y}`: Categorize failure modes per field
- `field_repair_success{field=X}`: Track which fields are successfully repaired

These metrics drive prompt engineering iteration: if `material` fails 30% of the time, the system prompt needs better material guidance.

---

## 9. Adversarial and Edge-Case Examples

### 9.1 Grammar Fail-Open (F-013)

**Setup:** llama.cpp encounters a grammar parse error and silently falls back to unconstrained generation.

**Input prompt:** Standard scene generation request.

**Adversarial output:**
```
Sure! Here's a tavern scene for your D&D game:

The Rusty Dragon is a cozy tavern with wooden tables and a roaring fireplace...
```

**Detection:** Pydantic `model_validate_json()` fails because input is not JSON. Pre-processing `extract_json()` finds no `{...}` block.

**Expected behavior:** Log grammar fail-open warning. Retry once. If second attempt also fails, apply full archetype fallback for the requested scene type.

**Test:** `test_grammar_failopen_detection`

### 9.2 5e Contamination (F-005)

**Adversarial output:**
```json
{
  "npc_id": "bandit_1",
  "custom_stat_block": {
    "ac": 14,
    "ac_breakdown": "10 + 2 (DEX) + 2 (proficiency)",
    "saves": {"str": 3, "dex": 4, "con": 2, "int": 0, "wis": 1, "cha": -1},
    "feats": ["Roll with advantage on stealth"]
  }
}
```

**Detection:** Layer 2 validator detects:
- `ac_breakdown` contains "proficiency" (5e term, not used in 3.5e AC calculation)
- `saves` uses ability names instead of Fort/Ref/Will
- Feat description uses "advantage" (5e mechanic)

**Expected behavior:** Reject stat block. Repair prompt instructs Spark to use 3.5e AC formula (10 + armor + shield + DEX + size + natural + deflection + misc) and Fort/Ref/Will saves.

**Test:** `test_5e_contamination_detection`

### 9.3 UNKNOWN with Missing Archetype (F-003)

**Adversarial output:**
```json
{
  "object_id": "alien_artifact_01",
  "class": "xenomorph_pod",
  "material": "crystal",
  "dimensions": {"length_ft": "UNKNOWN", "width_ft": "UNKNOWN", "height_ft": "UNKNOWN"},
  "position": {"x": 5, "y": 3},
  "solidity": true,
  "opacity": true,
  "mobility": "fixed",
  "condition": "intact"
}
```

**Detection:** Lens looks up archetype `xenomorph_pod` -- not found in registry.

**Expected behavior:** Scene rejected with error "Unknown archetype 'xenomorph_pod' with UNKNOWN dimensions -- cannot resolve defaults." Spark re-prompted with instruction to either provide numeric dimensions or use a recognized archetype class.

**Test:** `test_unknown_missing_archetype_rejection`

### 9.4 Spatial Overlap (F-006)

**Adversarial output:** Two solid objects placed at the same position:
```json
{
  "objects": [
    {"object_id": "pillar_01", "position": {"x": 5, "y": 5}, "solidity": true, ...},
    {"object_id": "barrel_01", "position": {"x": 5, "y": 5}, "solidity": true, ...}
  ]
}
```

**Detection:** Layer 3 spatial validator marks cell (5,5) as occupied by `pillar_01`, then finds `barrel_01` also claims (5,5).

**Expected behavior:** Targeted repair: "objects[1].position overlaps objects[0] at cell (5,5). Move barrel_01 to an unoccupied cell."

**Test:** `test_spatial_overlap_detection`

### 9.5 Detail Drift on Re-Emission (F-009)

**Setup:** Scene `tavern_01` was first emitted with `table_01.dimensions.length_ft = 3`. On second emission (player re-enters room), Spark emits `table_01.dimensions.length_ft = 4`.

**Detection:** Cache check finds `table_01.dimensions.length_ft` cached as `3` with source `SPARK_GENERATED`. New value `4` differs. Both are `SPARK_GENERATED`.

**Expected behavior:** Reject new value, keep cached `3`. Log:
```json
{
  "event": "DETAIL_DRIFT_REJECTED",
  "scene_id": "tavern_01",
  "object_id": "table_01",
  "field": "dimensions.length_ft",
  "cached_value": 3,
  "new_value": 4,
  "action": "KEPT_CACHED"
}
```

**Test:** `test_detail_drift_rejection`

### 9.6 BOX Contradiction (F-010)

**Setup:** During combat, Box destroyed `wall_section_01` (CellState.DESTROYED). Spark later re-emits the scene with `wall_section_01.condition = "intact"`.

**Detection:** Cache check finds `wall_section_01.condition` is `BOX_CANONICAL` with value `destroyed`. Spark's `intact` contradicts a frozen value.

**Expected behavior:** Reject Spark's value. Keep `destroyed`. Log BOX contradiction. Do NOT re-prompt Spark (BOX is authoritative).

**Test:** `test_box_contradiction_rejection`

### 9.7 Metric-Unit Emission (S-021)

**Adversarial output:**
```json
{
  "object_id": "table_01",
  "dimensions": {"length_ft": "3 meters", "width_ft": 3, "height_ft": 2.5}
}
```

**Detection:** Pydantic validation fails -- `length_ft` is type string but not `"UNKNOWN"`, and contains metric unit.

**Expected behavior:** Targeted repair: "dimensions.length_ft = '3 meters' is invalid. Must be a number in feet or 'UNKNOWN'. 3 meters = approximately 10 feet."

**Test:** `test_metric_unit_rejection`

### 9.8 Fractional Grid Coordinates (S-003)

**Adversarial output:**
```json
{
  "object_id": "chest_01",
  "position": {"x": 2.5, "y": 3}
}
```

**Detection:** Pydantic validation fails -- `position.x` must be integer.

**Expected behavior:** Targeted repair: "position.x = 2.5 must be an integer grid square index. Use 2 or 3."

**Test:** `test_fractional_grid_coordinate_rejection`

### 9.9 Token Exhaustion Mid-JSON (F-014)

**Adversarial output:** Truncated JSON because grammar could not force early closure:
```json
{"scene_id": "dungeon_01", "objects": [{"object_id": "pillar_01", "class": "stone_pillar", "mater
```

**Detection:** `json.loads()` raises `JSONDecodeError`. Pre-processing `extract_json()` cannot find a complete `{...}` block.

**Expected behavior:** Log token exhaustion warning. Retry once (the second attempt may produce shorter output due to stochastic generation). If retry also truncates, apply full archetype fallback.

**Test:** `test_token_exhaustion_handling`

### 9.10 Improvisation Contradicts Established Scene (F-015)

**Setup:** Existing fact: hallway ceiling is 7ft. Spark improvises a room behind a door with 15ft ceiling.

**Detection:** Lens contradiction check compares new room height against connected corridor ceiling height. 15ft is a sudden, unexplained 8ft increase.

**Expected behavior:** Repair prompt: "New room ceiling_height_ft = 15 contradicts connected corridor ceiling of 7ft. Either reduce height or add 'ceiling rises beyond doorway' to source_context." Accept if Spark provides a source_context explanation; reject if height exceeds 2x the connected space without explanation.

**Test:** `test_improvisation_height_contradiction`

### 9.11 Large Creature Insufficient Space (V-003)

**Adversarial output:**
```json
{
  "creature_id": "ogre_01",
  "size": "large",
  "space_ft": 5,
  "reach_ft": 5,
  "position": {"x": 0, "y": 0}
}
```

**Detection:** Layer 2 D&D 3.5e rules validator checks size-to-space table: Large = 10ft space. Emitted `space_ft = 5` is a mismatch.

**Expected behavior:** Targeted repair: "creature ogre_01 has size 'large' but space_ft=5. Large creatures require space_ft=10 per PHB p.149."

**Test:** `test_size_space_mismatch_rejection`

---

## 10. Test Map

Each policy and failure mode mapped to test specifications. Tests marked [EXISTS] reference existing test infrastructure; tests marked [NEEDED] must be created during implementation.

### 10.1 Schema Validation Tests

| Test ID | Policy/Failure | Test Description | Status |
|---------|---------------|------------------|--------|
| T-001 | S-001, F-002 | Valid SceneFactPack passes Pydantic validation | [NEEDED] |
| T-002 | S-002 | Fields with units have correct suffixes (_ft, _lb, _sq) | [NEEDED] |
| T-003 | S-003, 9.8 | Fractional grid coordinates rejected | [NEEDED] |
| T-004 | S-004, F-007 | Out-of-bounds positions rejected | [NEEDED] |
| T-005 | S-005 | Prose in boolean fields rejected | [NEEDED] |
| T-006 | S-006, S-007 | Missing scene_id or non-monotonic scene_version rejected | [NEEDED] |
| T-007 | S-008 | Duplicate object_id within scene rejected | [NEEDED] |
| T-008 | S-009, S-010 | Invalid condition values and backward transitions rejected | [NEEDED] |
| T-009 | S-011, S-023 | Invalid size categories (including invented ones) rejected | [NEEDED] |
| T-010 | S-012, 9.11 | Size/space_ft mismatch detected and rejected | [NEEDED] |
| T-011 | S-013 | Invalid material enum values rejected | [NEEDED] |
| T-012 | S-014 | Scene dimensions outside 1-100 range rejected | [NEEDED] |
| T-013 | S-015 | Missing or invalid provenance field rejected | [NEEDED] |

### 10.2 UNKNOWN Handling Tests

| Test ID | Policy/Failure | Test Description | Status |
|---------|---------------|------------------|--------|
| T-020 | U-001, U-002 | UNKNOWN dimension resolved to archetype default | [NEEDED] |
| T-021 | U-003, 9.3 | UNKNOWN with no archetype -> scene rejection | [NEEDED] |
| T-022 | U-004 | UNKNOWN position -> object omission (not error) | [NEEDED] |
| T-023 | U-005 | UNKNOWN for size/solidity/opacity/condition -> rejection | [NEEDED] |
| T-024 | U-006 | UNKNOWN for dimensions/weight/hardness/hp/elevation -> accepted with defaults | [NEEDED] |
| T-025 | U-002 | Resolved UNKNOWN tagged as ASSUMED_STANDARD with SourceTier.DEFAULT | [NEEDED] |

### 10.3 Prompting and Generation Tests

| Test ID | Policy/Failure | Test Description | Status |
|---------|---------------|------------------|--------|
| T-030 | P-001 | Grammar-constrained output produces valid JSON | [NEEDED] |
| T-031 | P-002 | `/no_think` prefix present on structured output requests | [NEEDED] |
| T-032 | P-003 | Temperature/TopP/TopK set to Qwen3-recommended values | [NEEDED] |
| T-033 | P-004 | max_tokens is NOT set on structured output calls | [NEEDED] |
| T-034 | P-006, 9.1 | Grammar fail-open detected by Pydantic post-validation | [NEEDED] |
| T-035 | P-007 | Temperature 0.0 blocked for Qwen3 models | [NEEDED] |
| T-036 | 9.9, F-014 | Token exhaustion produces parseable fallback | [NEEDED] |

### 10.4 Validation and Repair Tests

| Test ID | Policy/Failure | Test Description | Status |
|---------|---------------|------------------|--------|
| T-040 | V-001 | Three validation layers execute in correct order | [NEEDED] |
| T-041 | V-002 | Markdown fences and preambles stripped before parsing | [NEEDED] |
| T-042 | V-004, 9.4 | Spatial overlaps detected | [NEEDED] |
| T-043 | V-005 | Out-of-bounds footprints detected | [NEEDED] |
| T-044 | V-006 | Repair capped at 2 attempts; 3rd failure -> fallback | [NEEDED] |
| T-045 | V-007 | Targeted repair for few fields; full regen for >50% failure | [NEEDED] |
| T-046 | V-008 | Partial merge keeps valid fields, substitutes defaults for invalid | [NEEDED] |
| T-047 | V-016, 9.2 | Pydantic errors formatted as natural-language repair instructions | [NEEDED] |
| T-048 | V-009, 9.10 | Improvisation contradiction with established facts detected | [NEEDED] |

### 10.5 Drift Prevention Tests

| Test ID | Policy/Failure | Test Description | Status |
|---------|---------------|------------------|--------|
| T-050 | D-001, D-002 | First-seen cache populated on initial emission | [NEEDED] |
| T-051 | D-001, 9.5 | Detail drift rejected (same-tier re-emission) | [NEEDED] |
| T-052 | V-010, 9.6 | BOX_CANONICAL contradiction rejected | [NEEDED] |
| T-053 | V-011 | DEFAULT -> SPARK upgrade accepted | [NEEDED] |
| T-054 | D-003 | New objects in re-emission accepted and cached | [NEEDED] |
| T-055 | D-004 | Missing objects in re-emission preserved from cache | [NEEDED] |
| T-056 | D-005 | Position changes rejected after Box placement | [NEEDED] |
| T-057 | V-013 | All drift rejections logged with required fields | [NEEDED] |
| T-058 | D-006 | Scene cache serializes/deserializes with session state | [NEEDED] |

### 10.6 NPC and Encounter Tests

| Test ID | Policy/Failure | Test Description | Status |
|---------|---------------|------------------|--------|
| T-060 | S-018 | Stat block reference preferred over custom block | [NEEDED] |
| T-061 | V-014, S-019 | AC derivation validated against 3.5e formula | [NEEDED] |
| T-062 | V-014 | Feat prerequisite chain validated | [NEEDED] |
| T-063 | V-014 | Feat count validated for class/level | [NEEDED] |
| T-064 | V-015, S-020 | Encounter EL matches target within tolerance | [NEEDED] |
| T-065 | S-025, 9.2 | 5e contamination in stat blocks detected | [NEEDED] |
| T-066 | S-028 | All-brawler encounter flagged as low tactical variety | [NEEDED] |
| T-067 | S-031 | Equipment geometry declared for reach weapons/tower shields | [NEEDED] |

### 10.7 Integration Tests

| Test ID | Policy/Failure | Test Description | Status |
|---------|---------------|------------------|--------|
| T-070 | 4.6 | SceneFactPack -> PropertyMask encoding matches geometry.py PropertyFlag bits | [NEEDED] |
| T-071 | 4.6 | SceneCreature -> SizeCategory.footprint() produces correct grid occupancy | [NEEDED] |
| T-072 | 4.4 | FactCompletionPatch integrates with FactAcquisitionManager.apply_response() | [NEEDED] |
| T-073 | 5.1 | New SPARK_IMPROV SourceTier integrates with LensIndex authority resolution | [NEEDED] |
| T-074 | 4.2 | Full pipeline: Spark emission -> Lens validation -> BattleGrid population | [NEEDED] |
| T-075 | 7.1 | Full pipeline with 2 repair cycles -> successful validation | [NEEDED] |
| T-076 | 7.3 | Full pipeline with 3 failures -> archetype fallback | [NEEDED] |

---

## Appendix A: Reconciliation with NarrativeBrief

The `NarrativeBrief` pattern (`aidm/lens/narrative_brief.py`) establishes several design precedents that the Spark Emission Contract adopts:

### A.1 Frozen Dataclass Pattern

`NarrativeBrief` is a `@dataclass(frozen=True)` (line 42). All emission schemas in this contract SHOULD use frozen Pydantic models (or frozen dataclasses for non-validated internal types) to maintain the same immutability guarantee. Emissions are replaced, never modified in place.

### A.2 Provenance Tag Pattern

`NarrativeBrief` always carries `provenance_tag: str = "[DERIVED]"` (line 86). This contract extends the pattern: every Spark emission carries a `provenance` field (`SPARK_GENERATED` or `SPARK_IMPROVISED`), and every resolved UNKNOWN carries the `ASSUMED_STANDARD` provenance tag.

### A.3 Containment Boundary Analogy

NarrativeBrief enforces a containment boundary on what Spark can see (lines 2-18): no entity IDs, no raw HP, no AC, no grid coordinates. The Spark Emission Contract enforces the reverse boundary on what Spark can emit: structured facts only, no prose in mechanical fields, no 5e mechanics, no coordinate placement for scene layout.

Together, they form a symmetric membrane:

```
          NarrativeBrief (Output Valve)
          Strips: entity IDs, HP, AC, grid coords, RNG state
    Box  ========================================>  Spark
          Contains: action_type, severity, display names

          Spark Emission Contract (Input Valve)
          Strips: prose in mechanical fields, 5e mechanics
    Spark ========================================>  Lens -> Box
          Contains: structured JSON, D&D 3.5e data, provenance tags
```

### A.4 Event ID Tracking

NarrativeBrief tracks `source_event_ids` (line 85) for provenance from Box STPs. Analogously, `FactCompletionPatch` tracks `patch_id` and each `NewFact` carries `fact_id` for provenance through the Lens indexing pipeline.

---

## Appendix B: Full Normative Statement Provenance

Every normative statement in Section 2 is traced to its source sub-finding with section and approximate line range.

| Statement ID | Sub-Finding | Section | Lines (approx) |
|-------------|-------------|---------|----------------|
| S-001 | A | SS1.1, SS1.2 | 29-59 |
| S-002 | A | SS2.4 | 316-322 |
| S-003 | A | SS1.3, SS2.2 | 130-131, 294-298 |
| S-004 | A | SS1.3 | 130-131 |
| S-005 | A | SS1.1 principle 3 | 31 |
| S-006 | A | SS1.2 | 41-42 |
| S-007 | A | SS1.2 | 41 |
| S-008 | A | SS1.3-1.6 | 68, 142, 199, 224 |
| S-009 | A | SS1.3 | 97, 135 |
| S-010 | A | SS1.3 / B SS4 | 97, 625 |
| S-011 | A | SS1.4 | 146 |
| S-012 | A | SS1.4 | 174-191 |
| S-013 | A | SS1.3 | 71 |
| S-014 | A | SS1.2 | 52-53 |
| S-015 | A / C | SS1.2 / SS1.4 | 42, 73-74 |
| S-016 | C | SS1.2 | 52-56 |
| S-017 | C | SS1.2 | 81 |
| S-018 | C | SS2.2.1 | 524-528 |
| S-019 | C | SS2.5 | 1017-1078 |
| S-020 | C | SS2.3.1 | 795-809 |
| S-021 | A | SS2.3 | 306 |
| S-022 | A | SS2.3 | 308 |
| S-023 | A | SS2.3 | 311 |
| S-024 | B | SS5 | 1023-1025 |
| S-025 | C | SS2.4 | 934-946 |
| S-026 | A | SS5.5 | 607-613 |
| S-027 | A | SS6.3 | 768 |
| S-028 | C | SS2.3.2 | 819-853 |
| S-029 | C | SS2.2.2 | 644-667 |
| S-030 | C | SS2.2.3 | 676-706 |
| S-031 | C | SS2.2.4 | 710-748 |
| P-001 | B | SS3 Rank 1 | 84-177 |
| P-002 | B | SS3 | 45-55 |
| P-003 | B | SS3 | 57-69 |
| P-004 | B | SS3 | 73-80 |
| P-005 | A | SS4.5 | 480-496 |
| P-006 | B | SS3 Rank 1, SS4 | 176-177, 509 |
| P-007 | B | SS3 | 57-60 |
| P-008 | B | SS3 Rank 2 | 188-254 |
| P-009 | B | SS3 Rank 3 | 258-293 |
| P-010 | B | SS3 Rank 4 | 296-316 |
| V-001 | B | SS4 | 507-508 |
| V-002 | B | SS4 Layer 1 | 546-561 |
| V-003 | A | SS1.4 | 191 |
| V-004 | B | SS4 Layer 3 | 665-703 |
| V-005 | B | SS4 Layer 3 | 687-691 |
| V-006 | B | SS4 Repair | 806-812 |
| V-007 | B | SS4 Repair | 759-786 |
| V-008 | B | SS4 Fallback | 833-866 |
| V-009 | C | SS1.5 | 195-266 |
| V-010 | A | SS5.2.2 | 540-542 |
| V-011 | A | SS5.2.2 | 550-554 |
| V-012 | A | SS5.2.2 | 546-549 |
| V-013 | A | SS5.2.3 | 564-576 |
| V-014 | C | SS3.2 | 1258-1270 |
| V-015 | C | SS2.3.1 | 753-816 |
| V-016 | B | SS4 Layer 1 | 563-576 |
| V-017 | B / C | SS4 / SS1.8 | 709, 379 |
| V-018 | B | SS4 Repair Logging | 818-829 |
| U-001 | A | SS4.1 | 400-402 |
| U-002 | A | SS4.2 | 424-449 |
| U-003 | A | SS4.2 | 438-439 |
| U-004 | A | SS4.4 | 469 |
| U-005 | A | SS4.4 | 470-472 |
| U-006 | A | SS4.4 | 474-478 |
| D-001 | A | SS5.2.1 | 512-519 |
| D-002 | A | SS5.4 | 599 |
| D-003 | A | SS5.4 | 601 |
| D-004 | A | SS5.4 | 602 |
| D-005 | A | SS5.4 | 605 |
| D-006 | A | SS5.2.4 | 578-587 |
| D-007 | A | SS5.3 | 592-596 |

---

**End of RQ-SPARK-001 Synthesis: Spark Emission Contract v1**

**Document ID:** RQ_SPARK_001_SYNTHESIS
**Word Count:** ~7,800
**Date:** 2026-02-12
**Synthesizer:** Claude Opus 4.6
**Dispatch Authority:** Product Owner (Thunder)
**Next Step:** PM reviews synthesis -> dispatch implementation WOs for schema models, validation pipeline, scene cache, and archetype registry.

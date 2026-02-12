# World Compiler Contract v1
## Frozen World Bundle Specification

**Document ID:** RQ-WORLD-001
**Version:** 1.0
**Date:** 2026-02-12
**Status:** DRAFT — Awaiting PM + PO Approval
**Authority:** This document is the canonical contract for world compilation and the Frozen World Bundle.
**Scope:** Compile inputs, compile stages, bundle output format, determinism policy, failure modes, versioning.

**References:**
- `MANIFESTO.md` — Creation Stack (§"The Creation Stack: How Meaning Freezes")
- `docs/specs/RQ-PRODUCT-001_CONTENT_INDEPENDENCE_ARCHITECTURE.md` — Three-layer model, Layered World Authority Model (§8)
- `docs/decisions/AD-007_PRESENTATION_SEMANTICS_CONTRACT.md` — Presentation semantics schema (Layer B)
- `docs/decisions/DEC-WORLD-001.md` — "World skin freezes at compile; runtime cannot rewrite world truth"
- `docs/governance/BL-020_WORLDSTATE_IMMUTABILITY_AT_NON_ENGINE_BOUNDARIES.md` — Immutability enforcement pattern
- `docs/planning/RQ-TABLE-FOUNDATIONS-001.md` — Research Topic C (World Compiler spec requirements)
- `aidm/schemas/campaign.py` — CampaignManifest, PrepJob, AssetRecord (existing campaign-level schemas)
- `aidm/core/provenance.py` — W3C PROV-DM provenance tracking

**Companion Schemas (canonical JSON definitions for bundle registries):**
- `docs/schemas/world_bundle.schema.json` — WorldManifest, BundleHashes, AssetPools, CompileReport, LexiconEntry
- `docs/schemas/rule_registry.schema.json` — RuleEntry, RuleParameters, RuleTextSlots, RuleProvenance
- `docs/schemas/vocabulary_registry.schema.json` — VocabularyEntry, LocalizationHooks, WorldTaxonomy, VocabularyProvenance
- `docs/schemas/presentation_semantics_registry.schema.json` — AbilityPresentationEntry, EventPresentationEntry, SemanticsProvenance

**Existing Infrastructure (this spec builds on, does not replace):**

| Component | File | Relationship |
|-----------|------|-------------|
| Campaign manifest | `aidm/schemas/campaign.py` | Campaign is downstream of world; inherits world bundle |
| Prep orchestrator | `aidm/core/prep_orchestrator.py` | Campaign-level prep; world compile precedes this |
| Prep pipeline | `aidm/core/prep_pipeline.py` | Asset generation for campaigns; world assets are upstream |
| Provenance tracking | `aidm/core/provenance.py` | World compile must produce provenance records |
| FrozenWorldStateView | `aidm/core/state.py` | Runtime immutability pattern; world bundle uses same principle |

---

## Contract Summary (1-Page)

The World Compiler is an offline pipeline that takes system-agnostic
mechanics (the content pack) + a world theme + seeds + pinned tooling and
produces a **Frozen World Bundle**: a read-only artifact containing
everything needed to run campaigns in that world.

The world bundle is the product's **Level 1** in the creation stack
(RQ-PRODUCT-001 §8). It sits between the immutable engine substrate
(Level 0) and the lightweight campaign selection (Level 2). World compilation
is **expensive and rare** — the PO's design: "come back in hours." Campaign
creation is cheap — the world already exists.

**The bundle contains:**
- The world's rulebook (generated ability/spell/feat descriptions)
- The world's lexicon (canonical names for all mechanical IDs)
- The world's bestiary (creature entries with names, lore, doctrine profiles)
- The world's map seeds (regions, countries, cities, governments, geography)
- Presentation semantics for all abilities/events (AD-007 Layer B)
- NPC archetypes and doctrine profiles
- Asset pool definitions and binding rules
- Provenance labels and compile certificate
- File-level hashes and a root bundle hash

**Invariants:**
1. **Deterministic:** Same inputs + same seeds + same pinned toolchain → identical bundle bytes (or explicit failure). No silent variation.
2. **Frozen:** Once compiled, the bundle is read-only. Runtime cannot mutate it. Campaigns inherit it unchanged.
3. **Authority boundary:** The compiler authors vocabulary, presentation semantics, and world geography. It does NOT decide runtime mechanics, resolve actions, or narrate sessions.
4. **No coaching:** Bundle content encodes rules and lore only. No tactical advice, no "player tips," no strategy guidance.
5. **Local-first:** The bundle is a local artifact. No service dependency to play.
6. **IP-clean:** The bundle ships zero D&D/WotC content. Vault references are scaffolding only, never bundle inputs.

---

## 1. Inputs Contract

### 1.1 Required Inputs

| Input | Type | Description | Validation |
|-------|------|-------------|------------|
| `content_pack_id` | string | Identifies the content pack (Level 0b data: mechanics, behavioral contracts, category tags) | Must resolve to a valid content pack directory |
| `world_theme_brief` | object | Structured theme descriptor: genre, tone, technology level, magic level, cosmology notes, naming style, environmental palette | Must contain at minimum: `genre`, `tone`, `naming_style` |
| `world_seed` | integer | Primary seed for all world generation RNG | Must be non-negative 64-bit integer |
| `compile_config` | object | Compilation parameters: output directory, log level, stage enables, content filters | Must pass schema validation |
| `toolchain_pins` | object | Pinned versions of all tools used during compilation (LLM model ID, image gen model ID, hash algorithm, schema version) | All pins required; no "latest" |

### 1.2 Optional Inputs

| Input | Type | Description | Default |
|-------|------|-------------|---------|
| `asset_pool_targets` | object | Target sizes for asset pools (portraits per category, voice profiles, etc.) | Minimum viable defaults |
| `locale` | string | Language/locale for generated text | `"en"` |
| `tone_profile` | object | DM persona parameters for generated rulebook text | Neutral/encyclopedic |
| `content_filters` | object | World-appropriate content constraints (violence level, horror elements, etc.) | No filters (full range) |
| `map_config` | object | Map generation parameters (region count, city density, geographic features) | Genre-appropriate defaults |
| `derived_seeds` | object | Override derived seeds for specific stages (see §4.1) | Derived from `world_seed` |

### 1.3 Input Validation Rules

```
REJECT if:
  IV-001: content_pack_id does not resolve to a valid content pack
  IV-002: world_theme_brief is missing required fields (genre, tone, naming_style)
  IV-003: world_seed is negative or exceeds 64-bit range
  IV-004: toolchain_pins is missing any required pin (llm_model_id, hash_algorithm, schema_version)
  IV-005: toolchain_pins contains "latest" or unresolved version references
  IV-006: compile_config fails schema validation
  IV-007: content_pack_id version is incompatible with schema_version in toolchain_pins
```

Validation is **fail-closed**: any validation failure halts compilation before
Stage 0 begins. No partial compilation proceeds.

---

## 2. Compile Stages

### 2.0 Stage 0: Validate Inputs + Pins

**Purpose:** Verify all inputs are present, valid, and compatible.

**Actions:**
1. Validate all required inputs against schemas (§1.3)
2. Verify content pack integrity (hash check against known manifest)
3. Verify toolchain pins resolve to available tools
4. Derive child seeds from `world_seed` (§4.1)
5. Create compile workspace directory
6. Write `compile_inputs.json` (frozen snapshot of all inputs for reproducibility)

**Output:** `compile_inputs.json` + workspace directory
**Failure:** Any validation failure → halt, write `compile_report.json` with error details

### 2.1 Stage 1: Generate Lexicon + IDs

**Purpose:** Assign canonical names to all mechanical IDs in the content pack
for this world's theme.

**Actions:**
1. Read all ability IDs, spell IDs, feat IDs, skill IDs, class IDs, creature IDs from content pack
2. Generate world-flavored names for each ID using the world theme brief and naming style
3. Generate taxonomy (how abilities/creatures are categorized in this world)
4. Generate cosmology labels (schools of magic, creature types, damage types — all world-flavored)
5. Assign stable `lexicon_id` to each entry (deterministic: `sha256(world_seed + content_id)[:16]`)

**Output:** `lexicon.json`
**Determinism:** Same world_seed + same content_pack + same naming_style → same lexicon
**Constraint:** Names must pass the Recognition Test (RQ-PRODUCT-001 §3): no name recognizable as originating from a specific copyrighted source

### 2.2 Stage 2: Generate Rulebook Pages + Index

**Purpose:** Produce the world's player-inspectable rulebook. Each ability,
spell, feat, and class gets a stable entry.

**Actions:**
1. For each mechanical ID:
   - Combine Layer A (mechanics from content pack) + Layer B (presentation semantics from Stage 3) + lexicon name (from Stage 1)
   - Generate a stable rulebook entry: name, type, range, area, effect description, mechanical summary
2. Generate rulebook index (searchable by name, category, tier, school)
3. Generate table of contents

**Output:** `rulebook/` directory with per-entry files + `rulebook/index.json`
**Dependency:** Requires Stage 1 (lexicon) and Stage 3 (presentation semantics).
Stages 1 and 3 may run before Stage 2; Stage 2 is a join point.
**Determinism:** Same inputs → identical rulebook text
**Constraint:** Rulebook text is **generated at compile time and frozen**. It is
never regenerated during play. It is the canonical reference the player sees
when they "open the rulebook."

### 2.3 Stage 3: Generate Presentation Semantics Bindings

**Purpose:** Assign AD-007 presentation semantics (Layer B) to every ability
and event category.

**Actions:**
1. For each ability ID in the content pack:
   - Read behavioral contract (Layer 2 from content pack)
   - Generate presentation semantics: `delivery_mode`, `staging`, `origin_rule`, `vfx_tags`, `sfx_tags`, `scale`, `residue`
   - Generate `ui_description` (canonical short description for rulebook)
2. For each event category (combat events, environmental effects, social interactions):
   - Generate default presentation semantics

**Output:** `presentation_semantics.json`
**Determinism:** Same theme + same behavioral contract → same semantics
**Reference:** AD-007 fields and enums are authoritative

### 2.4 Stage 4: Generate NPC Archetypes + Doctrine Profiles

**Purpose:** Define the world's NPC behavioral archetypes and tactical
doctrine profiles.

**Actions:**
1. Generate NPC archetype templates (shopkeeper, guard, noble, peasant, scholar, criminal, etc.)
   - Each archetype: personality traits, speech patterns, knowledge domains, behavioral constraints
2. Generate tactical doctrine profiles for creature types
   - Each doctrine: aggression level, retreat threshold, pack behavior, preferred tactics, morale
3. Bind archetypes and doctrines to world theme (a space pirate world's "guard" differs from a fantasy "guard")

**Output:** `npc_archetypes.json` + `doctrine_profiles.json`
**Determinism:** Same world theme + same creature types → same profiles
**Constraint:** Doctrine profiles are behavioral (how creatures fight), not narrative (how to describe them fighting). No coaching content.

### 2.5 Stage 5: Generate Bestiary Canonical Entries

**Purpose:** Produce the world's canonical creature catalog.

**Actions:**
1. For each creature ID in the content pack:
   - Assign world-flavored name (from lexicon, Stage 1)
   - Generate appearance description, habitat, behavior summary
   - Assign presentation semantics for creature-specific abilities
   - Generate bestiary entry (combines: Layer 1 mechanical stats + Layer 2 behavioral contract + Layer 3 world skin)
2. Generate creature type taxonomy for this world
3. Generate habitat distribution (which creatures appear where in the world)

**Output:** `bestiary.json`
**Determinism:** Same world_seed + same content_pack → same bestiary
**Constraint:** Bestiary entries are the **canonical truth**. They contain full
information (not player-masked). Player-visible masks (progressive revelation)
are applied at runtime by the Knowledge Mask system (RQ-TABLE-FOUNDATIONS-001,
Topic B). The compiled bestiary is DM-side truth.

### 2.6 Stage 6: Generate Map Seeds + Symbolic Placements

**Purpose:** Define the world's geography: regions, countries, cities,
governments, major landmarks. Not rendered maps — symbolic placements.

**Actions:**
1. Determine region count, geographic features, climate zones from world theme + map_config
2. Generate region definitions: name, terrain type, climate, dominant species, government type
3. Generate country/nation definitions within regions: government structure, culture traits, major cities
4. Generate city definitions: name, size, notable features, district layout (symbolic)
5. Generate governmental baseline: what types of governance exist, where they are
6. Generate major landmark definitions: name, type, significance
7. Assign map seeds for procedural detail generation (runtime can generate local maps from these seeds)

**Output:** `maps/` directory + `map_seeds.json`
**Determinism:** Same world_seed + same map_config → same geography
**Constraint:** Map data is symbolic (names, relationships, types, seeds), not
rendered (no images). Image rendering is deferred to the asset pipeline.
All regions, countries, cities, and governments are generated here —
campaigns select from this geography, they do not create new geography.

### 2.7 Stage 7: Initialize Asset Pools + Binding Registry

**Purpose:** Define the asset categories, pool sizes, and binding rules for
this world.

**Actions:**
1. Define asset categories appropriate to this world (creature portraits, NPC portraits, voice profiles, environment tiles, ambient tracks)
2. Set target pool sizes per category (from `asset_pool_targets` or defaults)
3. Define binding rules: permanent binding (NPC → portrait), category binding (creature type → token style)
4. Initialize empty binding registry (populated at campaign/runtime)
5. Define fallback representations for empty pools (placeholder assets)

**Output:** `asset_pools.json`
**Determinism:** Same world theme + same targets → same pool definitions
**Constraint:** Asset pools define categories and rules. Actual asset generation
is deferred to the campaign-level prep pipeline (`aidm/core/prep_pipeline.py`).
The world compiler defines *what* assets are needed, not the assets themselves.

### 2.8 Stage 8: Finalize Hashes + Write Manifest + Compile Report

**Purpose:** Seal the bundle with integrity hashes and write the compile
certificate.

**Actions:**
1. Compute SHA-256 hash of every file in the bundle
2. Write `bundle_hashes.json` (file path → hash mapping)
3. Compute root bundle hash: `sha256(sorted(all_file_hashes))` → single deterministic hash
4. Write `world_manifest.json`:
   - `world_id`: `sha256(world_seed + content_pack_id + toolchain_pins_hash)[:32]`
   - `world_name`: from lexicon (generated world name)
   - `version`: schema version
   - `compile_timestamp`: ISO-8601 (recorded for UX only, excluded from determinism checks)
   - `toolchain_pins`: frozen copy of all tool versions
   - `seeds`: all seeds used (world, lexicon, map, asset, bestiary)
   - `content_pack_id`: input content pack
   - `content_pack_hash`: hash of the input content pack
   - `root_hash`: the bundle's root hash
   - `file_count`: total files in bundle
5. Write `compile_report.json`:
   - Status: `"success"` or `"failure"`
   - Stage timings
   - Warnings (non-fatal issues)
   - Validation results
   - Input snapshot hash
6. Write `provenance_policy.json`:
   - Required provenance labels for this world
   - Label definitions (what each label means in this world)
   - Provenance chain requirements per artifact type

**Output:** `world_manifest.json` + `bundle_hashes.json` + `compile_report.json` + `provenance_policy.json`
**Determinism:** All hashes are deterministic for the same inputs. `compile_timestamp` is the only non-deterministic field and is excluded from hash computation.

### 2.9 Stage Dependency Graph

```
Stage 0 (Validate)
    │
    ├──→ Stage 1 (Lexicon) ──────────────────────────┐
    │                                                 │
    ├──→ Stage 3 (Presentation Semantics) ───────────│──→ Stage 2 (Rulebook)
    │                                                 │
    ├──→ Stage 4 (NPC Archetypes + Doctrine) ────────│
    │                                                 │
    ├──→ Stage 5 (Bestiary) ─────────────────────────│
    │       (depends on Stage 1 for names)           │
    │       (depends on Stage 3 for creature semantics)
    │                                                 │
    ├──→ Stage 6 (Maps) ────────────────────────────│
    │                                                 │
    ├──→ Stage 7 (Asset Pools) ──────────────────────│
    │                                                 │
    └──→ ─ ─ ─ ─ (all stages complete) ─ ─ ─ ─ ──→ Stage 8 (Finalize)
```

Stages 1, 3, 4, 6, 7 can run in parallel after Stage 0.
Stage 5 depends on Stages 1 and 3.
Stage 2 depends on Stages 1 and 3.
Stage 8 depends on all prior stages.

---

## 3. Canonical Bundle File Tree

```
world_bundle/
├── world_manifest.json          # World identity, seeds, pins, root hash
├── bundle_hashes.json           # Per-file SHA-256 hashes + root hash
├── compile_report.json          # Compile status, timings, warnings
├── compile_inputs.json          # Frozen snapshot of all inputs
├── provenance_policy.json       # Provenance labels and chain requirements
├── lexicon.json                 # Canonical name mappings (vocabulary_registry.schema.json)
├── rule_registry.json           # World-authored rule entries (rule_registry.schema.json)
├── presentation_semantics.json  # AD-007 Layer B bindings (presentation_semantics_registry.schema.json)
├── npc_archetypes.json          # NPC behavioral templates
├── doctrine_profiles.json       # Creature tactical doctrine
├── bestiary.json                # Full canonical creature catalog
├── asset_pools.json             # Asset category definitions + binding rules
├── rulebook/
│   ├── index.json               # Searchable rulebook index
│   ├── toc.json                 # Table of contents
│   ├── abilities/               # Per-ability rulebook entries
│   │   ├── ABILITY_001.json
│   │   ├── ABILITY_002.json
│   │   └── ...
│   ├── classes/                  # Per-class entries
│   ├── skills/                   # Per-skill entries
│   └── feats/                    # Per-feat entries
└── maps/
    ├── map_seeds.json            # Procedural seeds + symbolic placements
    ├── regions/                   # Per-region definitions
    │   ├── region_001.json
    │   └── ...
    ├── countries/                 # Per-country definitions
    ├── cities/                    # Per-city definitions
    └── landmarks/                 # Per-landmark definitions
```

### 3.1 Required Files

Every valid world bundle MUST contain these files:

| File | Purpose | Validation |
|------|---------|------------|
| `world_manifest.json` | Bundle identity and certificate | Schema-valid, root_hash matches |
| `bundle_hashes.json` | Integrity verification | Every listed file exists; hashes match |
| `compile_report.json` | Compile provenance | Status is `"success"` |
| `compile_inputs.json` | Reproducibility | Input snapshot present |
| `provenance_policy.json` | Provenance rules | Schema-valid |
| `lexicon.json` | Name bindings | Every content pack ID has a mapping |
| `rule_registry.json` | Rule entries | Every content pack rule has an entry; validates against `rule_registry.schema.json` |
| `presentation_semantics.json` | AD-007 Layer B | Every ability ID has semantics; validates against `presentation_semantics_registry.schema.json` |
| `bestiary.json` | Creature catalog | At least 1 creature entry |
| `asset_pools.json` | Asset definitions | Schema-valid |
| `rulebook/index.json` | Rulebook index | Schema-valid, entries reference existing files |
| `maps/map_seeds.json` | Map seeds | At least 1 region defined |

Optional files that may be absent in minimal bundles:
- `npc_archetypes.json` (may be empty in minimal bundles)
- `doctrine_profiles.json` (may be empty in minimal bundles)
- Individual rulebook entries (index may reference placeholders)

---

## 4. Determinism + Reproducibility

### 4.1 Seed Strategy

All randomness during compilation derives from the `world_seed` via
deterministic key derivation:

| Derived Seed | Derivation | Purpose |
|-------------|-----------|---------|
| `lexicon_seed` | `sha256("lexicon:" + str(world_seed))` → int | Name generation RNG |
| `map_seed` | `sha256("map:" + str(world_seed))` → int | Map/geography generation |
| `bestiary_seed` | `sha256("bestiary:" + str(world_seed))` → int | Creature detail generation |
| `asset_seed` | `sha256("asset:" + str(world_seed))` → int | Asset pool initialization |
| `doctrine_seed` | `sha256("doctrine:" + str(world_seed))` → int | Doctrine profile generation |
| `rulebook_seed` | `sha256("rulebook:" + str(world_seed))` → int | Rulebook text generation |

Derived seeds can be overridden via `derived_seeds` in the compile config
(for debugging/testing). If overridden, the override is recorded in
`compile_inputs.json` and affects the `world_id`.

### 4.2 Idempotency Rules

**Strong idempotency:** Re-running the compiler with identical inputs (same
content_pack + same world_seed + same toolchain_pins + same compile_config)
MUST produce a byte-identical bundle, with one exception:

- `compile_report.json` → `compile_timestamp` field may differ (timestamps
  are recorded for UX, not for identity)

**Hash idempotency:** The `root_hash` in `bundle_hashes.json` MUST be
identical across re-runs with the same inputs. The `compile_timestamp` in
`world_manifest.json` is excluded from hash computation.

**LLM determinism caveat:** If an LLM is used during compilation (for name
generation, description generation, etc.), the toolchain pin MUST include the
exact model ID and any temperature/sampling parameters. If the LLM provider
does not guarantee deterministic output for the same inputs, the compiler
MUST:
1. Run the LLM once
2. Cache the output
3. Hash the output
4. Include the hash in the bundle
5. On re-run: check cache → if cache hit with matching input hash, use cached output
6. If no cache: re-run LLM, verify output hash matches → if mismatch, **fail with explicit error** (the toolchain is not deterministic)

This is the "compile once, freeze forever" model. The LLM is a compiler,
not a runtime service. Its output is frozen into the bundle.

### 4.3 Allowed Nondeterminism

**None.** All outputs are deterministic for the same inputs, or the compile
fails. There is no "best effort" determinism. Specific rules:

| Source of Nondeterminism | Mitigation |
|--------------------------|------------|
| Timestamps | Excluded from hash computation; recorded for UX only |
| Unordered collections | All collections are sorted before hashing (sort_keys=True) |
| Float precision | All floats are rounded to 6 decimal places before hashing |
| File system ordering | Files are processed in sorted(path) order |
| LLM output variation | Compile-once-cache model (§4.2). Mismatch = hard failure |
| Thread scheduling | Parallel stages produce deterministic outputs independently; final join is ordered |

### 4.4 Reproducibility Certificate

The `world_manifest.json` serves as the compile certificate. It contains
everything needed to reproduce the bundle:

```
To reproduce this bundle:
1. Obtain content_pack matching content_pack_hash
2. Obtain toolchain matching toolchain_pins
3. Set world_seed to recorded value
4. Run compiler with compile_inputs.json
5. Verify root_hash matches
```

If root_hash matches, the bundle is identical. If it doesn't, the toolchain
has changed behavior and the bundle cannot be reproduced — this is an error,
not an expected outcome.

---

## 5. Failure Modes

### 5.1 Fail-Closed Policy

The compiler **never** produces a partial bundle and promotes it as playable.
Every failure results in:

1. `compile_report.json` with `status: "failure"`
2. Detailed error information (which stage, what input, what went wrong)
3. The bundle directory exists but is explicitly marked as invalid
4. No `world_manifest.json` is written (absence = bundle is not valid)

### 5.2 Failure Taxonomy

| Failure Mode | Stage | Behavior | Recovery |
|-------------|-------|----------|----------|
| Missing content pack | 0 | Halt, report | Provide valid content pack |
| Invalid theme brief | 0 | Halt, report | Fix theme brief |
| Missing toolchain pin | 0 | Halt, report | Pin all tools |
| Unpinned tool used | Any | Halt, report | Add missing pin |
| LLM generation failure | 1-5 | Halt, report | Retry with same pins |
| LLM output nondeterminism | 1-5 (re-run) | Halt, report hash mismatch | Investigate LLM, pin tighter |
| Schema validation failure | 8 | Halt, report | Fix generator output |
| Hash integrity failure | 8 | Halt, report | Recompile from clean state |
| Insufficient content | 1-5 | Halt, report | Expand content pack or theme |
| Content filter conflict | 1-5 | Halt, report | Relax filters or expand theme |

### 5.3 No Partial Bundles

A bundle is either complete and valid, or it does not exist as a playable
artifact. There is no "90% compiled" state that can be loaded by the runtime.

The `compile_report.json` is always written (even on failure) to provide
diagnostic information. But the `world_manifest.json` is only written on
success — its presence is the bundle validity signal.

---

## 6. Versioning + Incremental Updates

### 6.1 Decision: No Post-Freeze Patching

**World bundles are immutable once compiled.** There is no patch mechanism.

**Rationale:**
- Patching creates version skew between campaigns using the same world
- Patching makes determinism verification harder (which version of the bundle?)
- Patching creates audit complexity (provenance chains across patch versions)
- The "recompile to new world" model is cleaner and already expected by the PO
  ("come back in hours" is the accepted cost)

**Consequence:**
- If a bug is found in a compiled world, the fix is: compile a new world (new `world_id`)
- Existing campaigns in the old world are unaffected (they reference the old `world_id`)
- The old world remains valid and playable — it just won't receive fixes
- Migrating a campaign to a new world is a manual decision by the player

### 6.2 Schema Versioning

The `schema_version` in `toolchain_pins` determines what files are expected
and what schemas apply. Schema changes are:

| Change Type | Version Bump | Bundle Compatibility |
|------------|-------------|---------------------|
| New optional file added | Minor | Old bundles still valid |
| New required file added | Major | Old bundles invalid unless migrated |
| Field added to existing file | Minor | Old bundles still valid (missing field = default) |
| Field removed from existing file | Major | Old bundles may have orphaned data |
| Field type changed | Major | Old bundles invalid |

**Migration:** When schema versions are incompatible, the old bundle remains
valid for its schema version. The runtime must support loading bundles with
older (compatible) schema versions, or refuse with an explicit error.

### 6.3 World Identity

`world_id` is a deterministic hash:
```
world_id = sha256(str(world_seed) + content_pack_id + canonical(toolchain_pins))[:32]
```

Same inputs → same `world_id`. Different inputs → different `world_id`.
This means:
- Changing the world_seed creates a new world
- Changing the content pack creates a new world
- Changing the toolchain creates a new world
- Re-running with identical inputs produces the same `world_id`

---

## 7. Runtime Integration

### 7.1 Loading a World Bundle

Runtime loads a world bundle by:
1. Verify `world_manifest.json` exists (bundle validity signal)
2. Read `bundle_hashes.json`
3. Verify root_hash (single hash check)
4. Optionally verify individual file hashes (deep integrity check)
5. Load required files into memory (lexicon, presentation semantics, bestiary, etc.)

### 7.2 Runtime Immutability

The loaded world bundle is **read-only**. Runtime code MUST NOT:
- Modify any loaded bundle data
- Write to the bundle directory
- Add, remove, or rename files in the bundle
- Overwrite cached LLM outputs in the bundle

This extends the BL-020 immutability principle (FrozenWorldStateView) to the
world bundle level. The enforcement mechanism is:
- Bundle directory is opened read-only
- Loaded data structures use frozen/immutable types where possible
- Any mutation attempt is a hard failure (same as BL-020 STOP conditions)

### 7.3 Campaign → World Relationship

```
WorldBundle (Level 1, frozen)
    │
    ├── Campaign A (Level 2, selects region_003)
    │   ├── Storyline 1
    │   └── Storyline 2
    │
    ├── Campaign B (Level 2, selects region_007)
    │   └── Storyline 1
    │
    └── Campaign C (Level 2, selects region_001)
        └── Storyline 1
```

Every campaign references a `world_id`. On load, the campaign verifies the
world bundle's `root_hash` matches what was recorded at campaign creation.
If the hash doesn't match, the campaign refuses to load (bundle was tampered
with or replaced).

### 7.4 What Campaigns Add (Not Modify)

Campaigns may add:
- Local NPC instances (bound to world archetypes from `npc_archetypes.json`)
- Local plot hooks and quest definitions
- Session logs and event history
- Asset bindings (NPC → portrait from world's asset pool)

Campaigns may NOT:
- Modify the lexicon (rename abilities)
- Modify the bestiary (change creature stats or appearance)
- Modify the rulebook (change ability descriptions)
- Modify the map (create new regions or countries)
- Modify presentation semantics (change how abilities behave visually)

---

## 8. Example Configs

### 8.1 Minimal Viable World ("Ashenmoor" — MVP)

```json
{
  "content_pack_id": "base_3.5e_v1",
  "world_theme_brief": {
    "genre": "dark_fantasy",
    "tone": "grim",
    "naming_style": "anglo_saxon_with_elvish",
    "technology_level": "medieval",
    "magic_level": "moderate",
    "cosmology_notes": "single_continent, ancient_ruins, fallen_empire"
  },
  "world_seed": 42,
  "compile_config": {
    "output_dir": "./worlds/ashenmoor",
    "log_level": "info",
    "stages_enabled": ["all"]
  },
  "toolchain_pins": {
    "llm_model_id": "llama-3.1-70b-instruct",
    "llm_temperature": 0.0,
    "llm_top_p": 1.0,
    "hash_algorithm": "sha256",
    "schema_version": "1.0"
  }
}
```

**Expected output tree:**
```
worlds/ashenmoor/
├── world_manifest.json
├── bundle_hashes.json
├── compile_report.json
├── compile_inputs.json
├── provenance_policy.json
├── lexicon.json
├── presentation_semantics.json
├── npc_archetypes.json
├── doctrine_profiles.json
├── bestiary.json
├── asset_pools.json
├── rulebook/
│   ├── index.json
│   ├── toc.json
│   ├── abilities/ (20+ entries)
│   ├── classes/ (4+ entries)
│   ├── skills/ (10+ entries)
│   └── feats/ (10+ entries)
└── maps/
    ├── map_seeds.json
    ├── regions/ (3+ entries)
    ├── countries/ (5+ entries)
    ├── cities/ (10+ entries)
    └── landmarks/ (5+ entries)
```

### 8.2 Sci-Fi World

```json
{
  "content_pack_id": "base_3.5e_v1",
  "world_theme_brief": {
    "genre": "space_opera",
    "tone": "adventurous",
    "naming_style": "latin_technical",
    "technology_level": "interstellar",
    "magic_level": "none_replaced_by_technology",
    "cosmology_notes": "multiple_star_systems, ancient_alien_ruins, corporate_factions"
  },
  "world_seed": 7777,
  "compile_config": {
    "output_dir": "./worlds/nova_reach",
    "log_level": "info"
  },
  "toolchain_pins": {
    "llm_model_id": "llama-3.1-70b-instruct",
    "llm_temperature": 0.0,
    "llm_top_p": 1.0,
    "hash_algorithm": "sha256",
    "schema_version": "1.0"
  }
}
```

### 8.3 Undersea World

```json
{
  "content_pack_id": "base_3.5e_v1",
  "world_theme_brief": {
    "genre": "aquatic_fantasy",
    "tone": "mysterious",
    "naming_style": "polynesian_mythological",
    "technology_level": "bronze_age_with_magic",
    "magic_level": "high",
    "cosmology_notes": "ocean_world, sunken_cities, deep_trenches, bioluminescent"
  },
  "world_seed": 2048,
  "compile_config": {
    "output_dir": "./worlds/deepholm"
  },
  "toolchain_pins": {
    "llm_model_id": "llama-3.1-70b-instruct",
    "llm_temperature": 0.0,
    "llm_top_p": 1.0,
    "hash_algorithm": "sha256",
    "schema_version": "1.0"
  }
}
```

### 8.4 Horror World

```json
{
  "content_pack_id": "base_3.5e_v1",
  "world_theme_brief": {
    "genre": "cosmic_horror",
    "tone": "dread",
    "naming_style": "lovecraftian_with_germanic",
    "technology_level": "victorian",
    "magic_level": "forbidden_and_costly",
    "cosmology_notes": "reality_is_fragile, things_from_beyond, sanity_is_currency"
  },
  "world_seed": 1313,
  "compile_config": {
    "output_dir": "./worlds/bleakshire"
  },
  "toolchain_pins": {
    "llm_model_id": "llama-3.1-70b-instruct",
    "llm_temperature": 0.0,
    "llm_top_p": 1.0,
    "hash_algorithm": "sha256",
    "schema_version": "1.0"
  },
  "content_filters": {
    "violence_level": "graphic",
    "horror_elements": "unrestricted"
  }
}
```

### 8.5 Minimal Test World (Unit Testing)

```json
{
  "content_pack_id": "test_pack_minimal",
  "world_theme_brief": {
    "genre": "generic_fantasy",
    "tone": "neutral",
    "naming_style": "simple_english"
  },
  "world_seed": 1,
  "compile_config": {
    "output_dir": "./test_worlds/minimal",
    "log_level": "debug",
    "stages_enabled": ["0", "1", "8"]
  },
  "toolchain_pins": {
    "llm_model_id": "test_stub",
    "hash_algorithm": "sha256",
    "schema_version": "1.0"
  }
}
```

---

## 9. Doctrine Alignment Cross-Check

| Doctrine | How This Spec Aligns |
|----------|---------------------|
| **No-Opaque-DM** | Bundle is fully inspectable. Every fact traces to compile inputs via provenance. No hidden discretion. |
| **No coaching** | Bundle contains rules and lore only. Rulebook entries describe mechanics and behavior, never tactics or advice. Compliance checklist includes coaching scan. |
| **Authority split** | Compiler authors vocabulary/skin (Level 1). It does not resolve actions (Box), assemble briefs (Lens), or narrate (Spark). |
| **Local-first** | Bundle is a local directory. No network dependency to load or use it. |
| **No IP shipping** | Bundle contains generated names and descriptions. Recognition Test (RQ-PRODUCT-001 §3) applies to all generated text. Compliance checklist includes IP scan. |
| **Determinism** | Same inputs → same bundle bytes (§4). LLM outputs are compiled and frozen, not regenerated. |
| **Fail-closed** | No partial bundles. Failure → no world_manifest.json → runtime refuses to load. |
| **FREEZE-001 / BL-020** | Bundle is read-only at runtime. Same immutability principle as FrozenWorldStateView, extended to the file level. |
| **AD-007** | Presentation semantics are generated at Stage 3 and frozen in the bundle. Runtime reads them, never modifies them. |

---

## 10. Deltas from Existing Infrastructure

| # | Delta | Current State | Contract Requirement | Severity |
|---|-------|--------------|---------------------|----------|
| D-01 | No world-level schema | `CampaignManifest` exists; no `WorldManifest` | World manifest schema needed | High |
| D-02 | No world_id concept | `campaign_id` exists; campaigns don't reference worlds | World_id + campaign→world binding needed | High |
| D-03 | PrepJob is campaign-level | `PrepJob` types: INIT_SCAFFOLD, SEED_ASSETS, etc. | World compile stages are distinct from campaign prep | Medium |
| D-04 | No lexicon storage | Names are inline in code/test fixtures | Lexicon.json as canonical name source | High |
| D-05 | No presentation semantics storage | AD-007 defines schema but no persistence format | presentation_semantics.json needed | High |
| D-06 | No bestiary persistence | Creature data is in code | bestiary.json as canonical creature catalog | Medium |
| D-07 | No map/geography system | No geographic data structures exist | maps/ directory + region/country/city schemas | High |
| D-08 | AssetRecord is campaign-level | Assets bound to campaign_id | World-level asset pool definitions needed | Low |
| D-09 | No compile certificate | No world_manifest.json equivalent | New artifact type | Medium |
| D-10 | Provenance is runtime-only | W3C PROV-DM tracks runtime facts | Compile-time provenance needed | Low |

---

## END OF WORLD COMPILER CONTRACT v1

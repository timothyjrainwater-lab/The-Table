# RQ-SPRINT-010: Community Mechanical Literacy -- Cross-World Communication

**Domain:** Product Architecture -- Community Knowledge Transfer & Cross-World UX
**Status:** COMPLETE
**Date:** 2026-02-14
**Depends on:** RQ-PRODUCT-001 (Content Independence Architecture)
**Informs:** World Compiler UX, Community Tools, Build Planner, Cross-World Gallery

---

## 1. Core Question

> How do players build expertise around a system where everyone has different
> words for everything?

The Content Independence Architecture (RQ-PRODUCT-001) deliberately separates
mechanical truth from narrative skin. Every world compiled from the same content
pack shares identical bone-layer procedures but assigns entirely different
names, categories, and visual presentations. ABILITY_003 is "Void Flare" in one
world and "Plasma Grenade" in another. The mechanical definition -- tier 3,
`min(10, caster_tier)d6` fire damage, 20-ft-radius sphere, Reflex save for
half -- is identical in both.

This creates a novel literacy problem. Players who master the system in one
world carry deep procedural knowledge but zero transferable vocabulary. Community
discussion, strategy guides, build advice, and cross-table communication all
break down when every participant uses different words for the same procedures.

This research examines the codebase structures that make cross-world
communication possible and proposes concrete mechanisms for building community
mechanical literacy across worlds.

---

## 2. Files Examined

| File | Key Structures | Relevance |
|------|---------------|-----------|
| `aidm/schemas/content_pack.py` | `MechanicalSpellTemplate` (30+ fields), `MechanicalCreatureTemplate`, `MechanicalFeatTemplate`, `ContentPack` | Defines the bone-layer data that is identical across all worlds. The `template_id` (e.g., `SPELL_003`) is the stable anchor. |
| `aidm/schemas/canonical_ids.py` | 7-namespace ID system (`mechanical_id`, `entity_id`, `asset_id`, `session_id`, `event_id`, `campaign_id`, `prepjob_id`) | The `mechanical_id` namespace (`spell.fireball`, `feat.power_attack`) is the universal translator between worlds. |
| `aidm/schemas/vocabulary.py` | `VocabularyRegistry`, `VocabularyEntry`, `WorldTaxonomy`, `LocalizationHooks` | The skin layer: maps `content_id` to `world_name`. This is the per-world translation table. |
| `aidm/schemas/presentation_semantics.py` | `AbilityPresentationEntry` with `DeliveryMode`, `Staging`, `OriginRule`, `Scale` enums | Defines how abilities behave visually. Shareable across worlds as part of the skin bundle. |
| `aidm/schemas/world_compile.py` | `CompileInputs`, `WorldThemeBrief`, `ToolchainPins`, `CompileReport` | The compile pipeline that produces per-world vocabulary and presentation registries. |
| `aidm/schemas/bundles.py` | `CampaignBundle`, `SessionBundle`, `SceneCard`, `NpcCard`, `EncounterSpec` | Contains campaign secrets, entity states, event logs. NOT shareable. |
| `aidm/data/content_pack/spells.json` | 605 spell templates | The full mechanical spell database. |
| `aidm/data/content_pack/creatures.json` | 273 creature templates | The full mechanical creature database. |
| `aidm/data/content_pack/feats.json` | 109 feat templates | The full mechanical feat database. |
| `aidm/schemas/feats.py` | 15 core combat feat definitions (`FeatDefinition`, `FEAT_REGISTRY`) | Runtime feat resolution with `feat_id` as stable identifier. |
| `docs/specs/RQ-PRODUCT-001_CONTENT_INDEPENDENCE_ARCHITECTURE.md` | Three-layer content model, Layered World Authority Model, Provenance Firewall | The foundational architecture that creates the cross-world communication problem. |

---

## 3. Mechanical Fingerprint Design

### 3.1 The Problem

`MechanicalSpellTemplate` has 30+ fields. Two abilities in different worlds that
share identical bone-layer procedures are the "same spell" from a mechanical
standpoint, but players have no way to recognize this at a glance. The
`template_id` (`SPELL_003`) is stable but opaque -- it tells you nothing about
what the spell does.

Players need a compact, human-recognizable summary of what a procedure does
mechanically. This is the **mechanical fingerprint**.

### 3.2 Fingerprint Hash Construction

A mechanical fingerprint is a deterministic hash derived from the subset of
`MechanicalSpellTemplate` fields that define the spell's mechanical identity.
Two spells with the same fingerprint are mechanically identical in all ways that
matter for tactical decision-making.

**Fingerprint input fields** (from `content_pack.py`):

```
target_type      : str    -- "single", "area", "self", "touch", "ray"
damage_type      : str?   -- "fire", "cold", "force", etc.
effect_type      : str    -- "damage", "healing", "buff", "debuff", "utility"
aoe_shape        : str?   -- "burst", "cone", "line", "emanation", etc.
save_type        : str?   -- "fortitude", "reflex", "will"
save_effect      : str?   -- "half", "negates", "partial"
tier             : int    -- 0-9
delivery_mode    : str    -- "projectile", "ray", "burst_from_point", etc.
auto_hit         : bool   -- True for auto-hit effects
requires_attack_roll : bool
damage_formula   : str?   -- "8d6", "1d6_per_CL_max_10d6", etc.
conditions_applied : tuple -- ("blinded", "stunned", etc.)
```

**Fingerprint algorithm:**

```python
import hashlib

def mechanical_fingerprint(template: MechanicalSpellTemplate) -> str:
    """Generate a compact mechanical fingerprint for cross-world identification.

    Returns a 12-character hex string (48 bits). Two templates with the
    same fingerprint are mechanically identical for tactical purposes.
    """
    canonical = "|".join([
        template.target_type,
        str(template.damage_type or ""),
        template.effect_type,
        str(template.aoe_shape or ""),
        str(template.save_type or ""),
        str(template.save_effect or ""),
        str(template.tier),
        template.delivery_mode,
        str(template.auto_hit),
        str(template.requires_attack_roll),
        str(template.damage_formula or ""),
        ",".join(sorted(template.conditions_applied)),
    ])
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]
```

### 3.3 Fingerprint as Parallel Namespace

The fingerprint occupies a distinct namespace from the 7 canonical ID namespaces
defined in `canonical_ids.py`. It is NOT a replacement for `mechanical_id` or
`template_id`. The relationship:

```
template_id   : SPELL_003             -- Stable content pack identity
mechanical_id : spell.fire_burst_003  -- Canonical rules-domain identity
fingerprint   : a7c3f2e8b1d4         -- Mechanical behavior hash
world_name    : "Void Flare"          -- Per-world display name (VocabularyEntry)
```

The `template_id` is the primary key. The `mechanical_id` is the canonical
cross-domain reference (used in `canonical_ids.py`). The fingerprint is a
**derived, lossy summary** -- two different spells could theoretically share a
fingerprint if their tactical profiles are identical but their exact formulas
differ in edge cases.

This is by design. The fingerprint answers the question "Is this spell
tactically similar to that one?" not "Are these the exact same content pack
entry?"

### 3.4 Fingerprint Collision Policy

Because the fingerprint is derived from a subset of fields (not all 30+), hash
collisions represent **mechanical similarity, not identity**. Two spells with
the same fingerprint are:

- Same tier
- Same target type, AoE shape, delivery mode
- Same damage type, save type, save effect
- Same conditions applied

They may differ in: range_formula, aoe_radius_ft, duration_formula, casting_time,
component requirements, spell_resistance, school_category. These are secondary
tactical distinctions that matter for detailed play but not for the "what kind
of spell is this?" question.

Community tools should display fingerprints with a "similar spells" caveat, not
an "identical spells" guarantee.

---

## 4. World Bundle Sharing Format

### 4.1 The Privacy Boundary

The Content Independence Architecture creates a clean separation between data
that defines a world's aesthetic (the skin) and data that records what happened
in a specific campaign (the state). The sharing boundary aligns with this
separation.

**SHAREABLE** (the skin -- defines how the world looks and sounds):

| Data | Schema | Why Shareable |
|------|--------|---------------|
| Vocabulary Registry | `VocabularyRegistry` (vocabulary.py) | Maps `content_id` to `world_name`. Contains no campaign state. Defines the world's lexicon. |
| Presentation Semantics | `PresentationSemanticsRegistry` (presentation_semantics.py) | `AbilityPresentationEntry` with `DeliveryMode`, `Staging`, `OriginRule`, `Scale`. Defines how abilities look and sound. No campaign state. |
| World Taxonomy | `WorldTaxonomy` (vocabulary.py) | How abilities/creatures are categorized in this world. `TaxonomyCategory` and `TaxonomySubcategory` entries. |
| World Theme Brief | `WorldThemeBrief` (world_compile.py) | Genre, tone, naming_style, technology_level, magic_level, cosmology_notes, environmental_palette. Defines the world's aesthetic parameters. |
| Compile Report (metadata only) | `CompileReport` (world_compile.py) | `world_id`, `root_hash`, compiler version. Integrity verification. |

**NOT SHAREABLE** (campaign state -- contains secrets and player data):

| Data | Schema | Why Private |
|------|--------|-------------|
| Campaign Bundle | `CampaignBundle` (bundles.py) | Contains `world_facts`, `factions`, `npc_index`, `session_ledger`, `evidence_ledger`, `thread_registry`. All campaign secrets. |
| Session Bundle | `SessionBundle` (bundles.py) | Contains `SceneCard` (with `secrets` field), `NpcCard` (with personality/goals), `EncounterSpec` (with trigger conditions and monster doctrines). Active campaign state. |
| Entity States | Entity ID namespace (canonical_ids.py) | Runtime entity data scoped to `campaign_id`. Contains character sheets, HP, conditions, inventories. |
| Event Logs | Event ID namespace (canonical_ids.py) | Session-scoped event records. Contain the complete play history. |

### 4.2 Minimum Shareable Bundle

The minimum data required to "preview" another world's skin:

```
shareable_world_bundle/
  vocabulary_registry.json     -- VocabularyRegistry (all VocabularyEntry records)
  presentation_semantics.json  -- PresentationSemanticsRegistry (all AbilityPresentationEntry records)
  world_theme_brief.json       -- WorldThemeBrief (genre, tone, naming_style, etc.)
  compile_metadata.json        -- world_id, root_hash, schema_version, compiler_version
```

This bundle is sufficient for:
- Browsing another world's spell/creature/feat names
- Viewing how abilities are categorized in another world's taxonomy
- Comparing presentation semantics (DeliveryMode, Staging, Scale) across worlds
- Understanding the world's genre, tone, and naming conventions

This bundle is NOT sufficient for:
- Playing in the world (requires full compile output + content pack)
- Viewing campaign-specific content (NPCs, plot, encounters)
- Accessing any player or session data

### 4.3 Sharing Protocol

The shareable bundle is generated at compile time as a side artifact. The
`CompileReport` already tracks all output files per stage (`StageResult.output_files`).
A new compile stage can produce the shareable bundle by extracting only the
skin-layer registries.

Export flow:
```
World Compile (existing pipeline)
  --> Stage N: Generate Shareable Bundle
      --> Extract VocabularyRegistry  (entries only, no campaign refs)
      --> Extract PresentationSemanticsRegistry (ability + event entries)
      --> Copy WorldThemeBrief (from CompileInputs)
      --> Write compile_metadata.json (world_id, root_hash, versions)
      --> Package as shareable_world_bundle.zip
```

The bundle is signed with the `world_id` hash from `CompileReport` for
integrity verification. Any consumer can verify that the bundle was produced by
a legitimate compile run.

---

## 5. Community Vocabulary Emergence

### 5.1 The Natural Shorthand Problem

Players will inevitably develop shorthand for mechanical archetypes. Without
guidance, this shorthand will be inconsistent, fragmented, and world-specific.
The system can facilitate convergence by providing canonical mechanical
vocabulary alongside world-specific names.

### 5.2 Mechanical Class Taxonomy

Based on the `MechanicalSpellTemplate` fields, abilities naturally cluster into
recognizable mechanical archetypes. These archetypes can be named using the
template's own field vocabulary:

| Mechanical Class | Defining Fields | Example Template | Description |
|-----------------|----------------|------------------|-------------|
| **Auto-hit projectile** | `auto_hit=True`, `delivery_mode="projectile"`, `effect_type="damage"` | `SPELL_025` (force missiles) | Guaranteed-hit ranged damage. No save, no attack roll. |
| **Area burst save-for-half** | `aoe_shape="burst"`, `save_effect="half"`, `effect_type="damage"` | `SPELL_003` (fire burst) | Point-targeted AoE with Reflex save reducing damage by half. |
| **Single-target save-or-suck** | `target_type="single"`, `save_effect="negates"`, `effect_type="debuff"` | `SPELL_044` (paralysis effect) | One target, save or suffer full condition. |
| **Touch healing** | `target_type="touch"`, `effect_type="healing"` | `SPELL_017` (restorative touch) | Touch-range HP restoration. |
| **Self-buff** | `target_type="self"`, `effect_type="buff"` | `SPELL_051` (personal enhancement) | Caster-only beneficial effect. |
| **Area denial** | `aoe_shape != None`, `effect_type="utility"`, `duration_formula != "instantaneous"` | `SPELL_082` (persistent zone) | Ongoing area that creates tactical terrain. |
| **Ray debuff** | `target_type="ray"`, `effect_type="debuff"`, `requires_attack_roll=True` | `SPELL_033` (weakening ray) | Ranged touch attack delivering a condition. |
| **Cone blast** | `aoe_shape="cone"`, `effect_type="damage"` | `SPELL_060` (cone of cold/fire/etc.) | Forward-facing AoE from caster position. |
| **Summon** | `delivery_mode="summon"` | `SPELL_095` (creature conjuration) | Creates an ally entity at a designated point. |
| **Mass buff** | `aoe_shape != None`, `effect_type="buff"` | `SPELL_112` (group enhancement) | Area-targeted beneficial effect on multiple allies. |

### 5.3 Facilitating Convergence

The system can help community vocabulary converge by:

1. **Displaying mechanical class alongside world name.** In the rulebook UI,
   each ability entry shows its world name prominently, with the mechanical
   class visible as a subtitle or tag:

   ```
   VOID FLARE
   [Area Burst Save-for-Half | Tier 3 | Fire]
   ```

2. **Showing template_id and fingerprint on hover/inspection.** Players who want
   to discuss specific abilities across worlds can reference the stable
   identifiers:

   ```
   Tooltip: SPELL_003 | Fingerprint: a7c3f2e8b1d4
   ```

3. **Tagging abilities with combat_role_tags.** The `combat_role_tags` field on
   `MechanicalSpellTemplate` already supports this: `direct_damage`,
   `area_control`, `single_target_damage`, `healing`, `buff`, `debuff`,
   `battlefield_control`, `support`, `utility`. These tags are identical across
   all worlds.

### 5.4 Expected Community Language Evolution

Phase 1 (early adoption): Players use world-specific names exclusively. "My
wizard has Void Flare, Thread of Unmaking, and Aetheric Shield."

Phase 2 (cross-world contact): Players discover that others use different
names for the same procedures. Confusion arises. "What's your Void Flare
equivalent?"

Phase 3 (mechanical shorthand): Players develop shorthand based on mechanical
classes. "I need a tier 3 area burst save-for-half." The system's mechanical
class labels accelerate this phase.

Phase 4 (mature community): Players fluently switch between world-specific
names (for in-character discussion) and mechanical class names (for strategy
discussion). Builds are discussed using mechanical archetypes: "I want an
auto-hit projectile at tier 1, area burst save-for-half at tier 3, and a
self-buff at tier 2."

---

## 6. Educational UX Concepts

### 6.1 Progressive Revelation Through the Discovery Log

The discovery log already teaches mechanics through play. As players encounter
abilities (used by them or against them), the log records what they observed.
Cross-world literacy builds naturally through this system:

- **First encounter:** Player sees the world name, effect description, and
  outcome. "You are struck by Void Flare. 24 fire damage."
- **Repeated encounters:** The discovery log shows pattern recognition.
  "Void Flare: Tier 3 Area Burst. Save: Reflex for half. Damage: fire."
- **Mechanical view unlocked:** After sufficient encounters, the player can
  toggle a "mechanical view" showing the bone-layer structure alongside the
  skin.

### 6.2 Mechanical View Toggle

A UI toggle that shows the bone-layer structure alongside the world-flavored
presentation. Available in:

- **Rulebook entries:** Show `MechanicalSpellTemplate` fields alongside the
  world-flavored spell description.
- **Character sheets:** Show mechanical class tags next to ability names.
- **Combat log:** Show template_id and fingerprint alongside narrated outcomes.
- **Build planner:** Toggle between world-specific names and mechanical
  archetype names.

Example -- Rulebook entry with mechanical view ON:

```
VOID FLARE                                  SPELL_003
"A searing orb of annihilation..."          template_id: SPELL_003
                                            fingerprint: a7c3f2e8b1d4
Tier: 3                                     tier: 3
School: Destruction Magic                   school_category: evocation
Range: Medium (400 + 40/level ft)           range_formula: medium
Area: 20-ft sphere                          aoe_shape: burst, aoe_radius_ft: 20
Save: Reflex for half                       save_type: reflex, save_effect: half
Damage: 1d6/level (max 10d6) fire           damage_formula: 1d6_per_CL_max_10d6
                                            damage_type: fire
Delivery: Projectile                        delivery_mode: projectile
                                            auto_hit: false
                                            requires_attack_roll: false
                                            spell_resistance: true
```

The left column is the world-flavored presentation (from `VocabularyRegistry`
and `PresentationSemanticsRegistry`). The right column is the raw bone-layer
data (from `MechanicalSpellTemplate`). Players learning the system can compare
the two and build intuition for what the mechanical fields mean.

### 6.3 Cross-World Comparison Tool

Given two worlds compiled from the same content pack, display the same
mechanical procedure with both worlds' skins side by side:

```
SPELL_003 | Fingerprint: a7c3f2e8b1d4

World: "Ashenveil" (Dark Fantasy)     World: "Neon Horizon" (Sci-Fi)
Name:  Void Flare                     Name:  Plasma Grenade
School: Destruction Magic             School: Thermal Weaponry
Delivery: Projectile (dark orb)       Delivery: Projectile (plasma canister)
Scale: Dramatic                       Scale: Dramatic
VFX: [dark_fire, void_energy]         VFX: [plasma_burst, heat_shimmer]
SFX: [deep_rumble, void_crack]        SFX: [explosion, static_hiss]

                    SHARED MECHANICS
            Tier 3 | Area Burst 20ft | Reflex Half
            1d6/CL fire (max 10d6) | SR: Yes
```

This tool uses the `VocabularyEntry.content_id` field as the join key. Both
worlds' `VocabularyRegistry` entries for `content_id = "spell.fire_burst_003"`
are loaded, and the shared `MechanicalSpellTemplate` is displayed in the center.
The `AbilityPresentationEntry` from each world's `PresentationSemanticsRegistry`
provides the vfx_tags, sfx_tags, delivery_mode, staging, and scale.

### 6.4 Fingerprint Display in UI Elements

Fingerprints appear in the following UI contexts:

| Context | Display Format | Purpose |
|---------|---------------|---------|
| Rulebook entry header | `[a7c3f2e8b1d4]` as small monospace tag | Allows cross-world reference |
| Character sheet ability list | Tooltip on hover | Quick identification without cluttering the sheet |
| Combat log entries | Optional column (toggled by mechanical view) | Post-combat analysis |
| Build planner ability cards | Always visible as subtitle | Primary use case for cross-world builds |
| Forum/community tools | Copyable badge | Pasting into discussion threads |

---

## 7. Cross-World Communication Tools

### 7.1 Build Planner Using Mechanical Archetypes

The build planner operates at two levels:

**Level 1: Mechanical Archetype Selection** (world-independent)

The player selects desired mechanical archetypes without reference to any
world's vocabulary:

```
Build: "Control Caster" (Tier 5)
  Slot 1: Auto-hit projectile (Tier 1)        -- guaranteed damage
  Slot 2: Area burst save-for-half (Tier 3)    -- AoE damage
  Slot 3: Single-target save-or-suck (Tier 4)  -- hard disable
  Slot 4: Self-buff (Tier 2)                   -- defense layer
  Slot 5: Area denial (Tier 5)                 -- battlefield control
```

**Level 2: World-Specific Resolution** (per-world)

Once the player selects their world, each archetype slot resolves to the
world-specific abilities that match:

```
Build: "Control Caster" in World "Ashenveil"
  Slot 1: Void Needles (SPELL_025)             -- auto-hit projectile
  Slot 2: Void Flare (SPELL_003)               -- area burst save-for-half
  Slot 3: Thread of Unmaking (SPELL_044)        -- save-or-suck
  Slot 4: Aetheric Shell (SPELL_051)            -- self-buff
  Slot 5: Entropic Field (SPELL_082)            -- area denial
```

The same build in World "Neon Horizon":

```
Build: "Control Caster" in World "Neon Horizon"
  Slot 1: Homing Darts (SPELL_025)             -- auto-hit projectile
  Slot 2: Plasma Grenade (SPELL_003)           -- area burst save-for-half
  Slot 3: Neural Scrambler (SPELL_044)          -- save-or-suck
  Slot 4: Reactive Plating (SPELL_051)          -- self-buff
  Slot 5: Graviton Sink (SPELL_082)             -- area denial
```

The build planner queries the `MechanicalSpellTemplate` fields to find
abilities matching each archetype, then resolves world names through the
`VocabularyRegistry`.

### 7.2 Strategy Forums with Fingerprint-Based Ability References

Community discussion tools support fingerprint-based ability references that
automatically resolve to the reader's world:

**Author writes (in World "Ashenveil"):**
```
For this encounter, I recommend opening with [Void Flare](fp:a7c3f2e8b1d4)
to soften the group, then using [Thread of Unmaking](fp:b2d4e6f8a0c1) on the
leader. Keep [Aetheric Shell](fp:c3e5d7f9b1a2) active throughout.
```

**Reader sees (in World "Neon Horizon"):**
```
For this encounter, I recommend opening with Plasma Grenade (your world:
"Plasma Grenade") to soften the group, then using Neural Scrambler (your
world: "Neural Scrambler") on the leader. Keep Reactive Plating (your world:
"Reactive Plating") active throughout.
```

The fingerprint link `fp:a7c3f2e8b1d4` is resolved against the reader's
`VocabularyRegistry` to display the reader's world name. If no vocabulary
is loaded, the fingerprint and mechanical class are shown as fallback:

```
For this encounter, I recommend opening with [Area Burst Save-for-Half, Tier 3,
Fire | fp:a7c3f2e8b1d4] to soften the group...
```

### 7.3 World Gallery

A community-facing gallery where players browse worlds compiled from the shared
content pack. Each world entry shows:

- **WorldThemeBrief summary:** Genre, tone, naming_style, technology_level,
  magic_level
- **Sample vocabulary:** 10-20 representative spell/creature/feat names from
  the `VocabularyRegistry` with their `content_id` mappings
- **Presentation preview:** Sample `AbilityPresentationEntry` data showing
  vfx_tags, sfx_tags, and scale for signature abilities
- **Taxonomy overview:** The `WorldTaxonomy` categories and subcategories,
  showing how abilities are organized in that world

The gallery operates entirely on shareable bundle data. No campaign data is
exposed.

Players can browse the gallery to:
- Find aesthetic inspiration for their own world creation
- Understand how the same mechanics are re-skinned across settings
- Discover naming patterns they want to use or avoid

### 7.4 The "Translate" Feature

Given a world-specific name, find the equivalent in another world:

```
Translate: "Void Flare" (Ashenveil) --> ? (Neon Horizon)

Step 1: Look up "Void Flare" in Ashenveil's VocabularyRegistry
        --> content_id: spell.fire_burst_003
Step 2: Look up content_id "spell.fire_burst_003" in Neon Horizon's VocabularyRegistry
        --> world_name: "Plasma Grenade"

Result: "Void Flare" (Ashenveil) = "Plasma Grenade" (Neon Horizon)
```

The `content_id` field on `VocabularyEntry` is the join key. Every world's
`VocabularyRegistry` maps the same set of `content_id` values to different
`world_name` values. Translation is a two-step lookup: source world name to
`content_id`, then `content_id` to target world name.

The translate feature also supports:
- **Alias resolution:** `VocabularyEntry.aliases` are searched if the primary
  `world_name` does not match
- **Fuzzy matching:** If no exact match, suggest entries with similar
  `world_name` strings
- **Batch translation:** Translate an entire spell list or character sheet
  from one world to another

---

## 8. The Rosetta Stone Problem

### 8.1 The content_id Layer as Universal Translator

The entire cross-world communication system rests on one architectural fact:
**every world maps the same `content_id` values to different `world_name`
values.**

From `vocabulary.py`, the `VocabularyEntry` dataclass:

```python
@dataclass(frozen=True)
class VocabularyEntry:
    content_id: str      # "spell.fire_burst_003" -- same in every world
    lexicon_id: str      # sha256(world_seed + content_id)[:16] -- unique per world
    domain: str          # "spell" -- same in every world
    world_name: str      # "Void Flare" / "Plasma Grenade" -- unique per world
    category: str        # world-specific taxonomy category
    aliases: tuple       # alternative names within this world
    localization_hooks: LocalizationHooks  # semantic_root, tone_register, etc.
```

The `content_id` is the Rosetta Stone. It is:
- **Derived from `mechanical_id`** in the canonical ID system (`canonical_ids.py`)
- **Stable across all worlds** using the same content pack
- **Human-readable:** `spell.fire_burst_003` tells you the domain (spell) and
  gives a semantic hint (fire_burst), unlike an opaque UUID
- **The join key** for all cross-world operations (translate, compare, build plan)

### 8.2 How the Layers Connect

```
Content Pack (Level 0b)
  MechanicalSpellTemplate.template_id = "SPELL_003"
       |
       v
Canonical ID System
  mechanical_id("spell", "fire_burst_003") = "spell.fire_burst_003"
       |
       v
Vocabulary Registry (per world, Level 1)
  VocabularyEntry.content_id = "spell.fire_burst_003"
  VocabularyEntry.world_name = "Void Flare"  (World A)
  VocabularyEntry.world_name = "Plasma Grenade" (World B)
       |
       v
Presentation Semantics (per world, Level 1)
  AbilityPresentationEntry.content_id = "spell.fire_burst_003"
  AbilityPresentationEntry.delivery_mode = DeliveryMode.PROJECTILE
  AbilityPresentationEntry.scale = Scale.DRAMATIC
  AbilityPresentationEntry.vfx_tags = ("dark_fire",)  (World A)
  AbilityPresentationEntry.vfx_tags = ("plasma_burst",)  (World B)
       |
       v
Mechanical Fingerprint (derived, world-independent)
  fingerprint("SPELL_003") = "a7c3f2e8b1d4"
```

### 8.3 UI Interaction Model

The default UI shows the world-flavored name (`world_name`). The universal
identifiers are available on demand:

| UI State | What the Player Sees |
|----------|---------------------|
| Default | "Void Flare" |
| Hover | "Void Flare" + tooltip: `spell.fire_burst_003` |
| Mechanical view ON | "Void Flare" + full bone-layer fields |
| Cross-world mode | "Void Flare (Ashenveil) = Plasma Grenade (Neon Horizon)" |
| Forum post | `[Void Flare](fp:a7c3f2e8b1d4)` -- auto-resolves for reader |

Players never need to learn `content_id` values by rote. The system handles
translation transparently. But for players who want to discuss mechanics
precisely across worlds, the `content_id` and fingerprint are always accessible.

### 8.4 The "Same Spell, Different Skin" Invariant

The architecture guarantees that for any two worlds compiled from the same
content pack:

1. The set of `content_id` values in both `VocabularyRegistry` entries is
   identical (same content pack = same mechanical catalog)
2. The `MechanicalSpellTemplate` for each `content_id` is byte-identical
   (frozen at Level 0b)
3. The `world_name`, `category`, `aliases`, `localization_hooks`, and
   `AbilityPresentationEntry` may differ (generated at Level 1, per-world)
4. The fingerprint for each `content_id` is identical across worlds
   (derived from Level 0b data only)

This invariant is what makes all cross-world tools possible. It is enforced
by the compile pipeline: the content pack is an input to the World Compiler,
not an output. The compiler generates skin; it does not modify bone.

---

## 9. Content Scale Context

The cross-world communication problem scales with content pack size. The
current content pack contains:

| Content Type | Count | Schema |
|-------------|-------|--------|
| Spell templates | 605 | `MechanicalSpellTemplate` |
| Creature templates | 273 | `MechanicalCreatureTemplate` |
| Feat templates | 109 | `MechanicalFeatTemplate` |
| **Total mechanical entries** | **987** | -- |

Each of these 987 entries has a unique `template_id`, a unique `content_id`
in the canonical ID system, and a unique `world_name` in every world. A player
who masters one world's vocabulary has learned 987 world-specific names. Moving
to a new world means learning 987 new names for the same procedures.

The mechanical fingerprint and class taxonomy reduce this 987-name problem to
a much smaller set of recognizable archetypes. The 605 spells likely cluster
into 20-30 distinct mechanical classes based on the combination of
`target_type`, `effect_type`, `delivery_mode`, and `aoe_shape`. Players who
learn the mechanical classes can rapidly orient themselves in any new world.

---

## 10. Creature and Feat Fingerprints

### 10.1 Creature Fingerprints

The `MechanicalCreatureTemplate` can be fingerprinted similarly, using tactical
identity fields:

```python
def creature_fingerprint(template: MechanicalCreatureTemplate) -> str:
    canonical = "|".join([
        template.size_category,
        template.creature_type,
        str(template.cr),
        template.intelligence_band,
        str(template.speed_ft),
        ",".join(sorted(template.speed_modes.keys())),
        ",".join(sorted(template.special_attacks)),
        ",".join(sorted(template.special_qualities)),
    ])
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]
```

This allows players to recognize that "Ashveil Stalker" (dark fantasy) and
"Phase Raptor" (sci-fi) are the same CR 3 large beast with fly speed, ambush
behavior, and poison special attack.

### 10.2 Feat Fingerprints

The `MechanicalFeatTemplate` fingerprint uses:

```python
def feat_fingerprint(template: MechanicalFeatTemplate) -> str:
    canonical = "|".join([
        template.feat_type,
        template.effect_type,
        str(template.bonus_value or ""),
        str(template.bonus_type or ""),
        str(template.bonus_applies_to or ""),
        str(template.trigger or ""),
        str(template.fighter_bonus_eligible),
    ])
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]
```

The 15 core combat feats from `feats.py` (Power Attack chain, Dodge chain,
Point Blank Shot chain, Weapon Focus chain, TWF chain, Improved Initiative)
form well-known mechanical archetypes. Players will quickly recognize
"trade attack for damage" (Power Attack archetype) regardless of what the
world calls it.

---

## 11. Implementation Considerations

### 11.1 Compile-Time vs. Runtime Fingerprints

Fingerprints should be computed at compile time and stored alongside the
vocabulary and presentation registries. This avoids runtime hash computation
and ensures fingerprints are available in the shareable bundle.

The `CompileReport.stage_results` (from `world_compile.py`) already tracks
per-stage output files. A fingerprint generation stage would produce:

```
fingerprints.json:
  {
    "SPELL_003": "a7c3f2e8b1d4",
    "SPELL_025": "d4f6a8c2e0b3",
    ...
    "CREATURE_014": "f1a3c5e7b9d2",
    ...
    "FEAT_007": "b2d4f6a8c0e1",
    ...
  }
```

### 11.2 Backward Compatibility with Canonical IDs

The fingerprint system does not modify the 7-namespace canonical ID system
from `canonical_ids.py`. It is a parallel, derived namespace that exists
purely for community communication. The `IDCollisionRegistry` does not need
to track fingerprints because they are not used for entity resolution.

### 11.3 VocabularyEntry Extension

The `VocabularyEntry` dataclass could be extended with an optional
`fingerprint` field:

```python
@dataclass(frozen=True)
class VocabularyEntry:
    # ... existing fields ...
    fingerprint: Optional[str] = None
    """Mechanical fingerprint hash (12 hex chars). Derived from bone-layer
    fields at compile time. Used for cross-world identification."""
```

This keeps the fingerprint co-located with the vocabulary mapping, making
it available in the shareable bundle without a separate file.

---

## 12. Recommendations

### P0: Critical Path (Required for Cross-World Communication)

- **Expose mechanical fingerprints in rulebook entries.** Compute fingerprints
  at compile time from `MechanicalSpellTemplate`, `MechanicalCreatureTemplate`,
  and `MechanicalFeatTemplate` fields. Store in the vocabulary registry
  alongside `content_id` and `world_name`. Display as a subtle tag in the
  rulebook UI.

### P1: High Priority (Enables Community Tools)

- **Define shareable world bundle subset.** Formalize the shareable bundle
  format: `VocabularyRegistry` + `PresentationSemanticsRegistry` +
  `WorldThemeBrief` + compile metadata. No `CampaignBundle` or `SessionBundle`
  data. Add a compile stage to produce this bundle automatically.

- **Build cross-world comparison prototype.** Given two shareable bundles,
  display side-by-side comparisons of the same `content_id` across both
  worlds. Use `VocabularyEntry.content_id` as the join key. Show shared
  mechanics in the center, world-specific skin on the sides.

### P2: Valuable (Enhances Community Experience)

- **Community theme gallery with preview system.** A browsable gallery of
  shareable world bundles. Shows `WorldThemeBrief` summary, sample vocabulary
  entries, taxonomy overview, and presentation semantic previews. Operates
  entirely on shareable bundle data.

- **Build planner operating on mechanical archetypes.** Two-tier build
  planner: first select mechanical archetypes (world-independent), then
  resolve to world-specific abilities. Supports exporting/importing builds
  across worlds via archetype descriptions.

### P3: Future (Community Scale Features)

- **Forum integration with fingerprint auto-resolution.** Inline fingerprint
  links in community discussion tools that auto-resolve to the reader's
  world vocabulary.

- **Translate feature.** Given a world-specific name and a target world,
  resolve the equivalent name via `content_id` lookup in both worlds'
  vocabulary registries.

- **Mechanical class auto-tagging.** Automatically classify all 605 spells,
  273 creatures, and 109 feats into mechanical archetype classes based on
  their template fields. Display these classes in the UI alongside world
  names.

---

## 13. Relationship to Other Work

| Relationship | Target | Notes |
|-------------|--------|-------|
| **Depends on** | RQ-PRODUCT-001 (Content Independence Architecture) | The three-layer content model and Layered World Authority Model are prerequisites for all cross-world communication. |
| **Depends on** | World Compiler pipeline | Fingerprints and shareable bundles are compile-time artifacts. |
| **Informs** | Rulebook UI design | Mechanical view toggle, fingerprint display, cross-world comparison tools. |
| **Informs** | Community platform design | Gallery, forums, translate feature, build planner. |
| **Independent of** | RQ-BOX-002, RQ-BOX-003 | Mechanical literacy is orthogonal to RAW silence handling and object identity. |
| **Extends** | Canonical ID system (`canonical_ids.py`) | Fingerprints are a parallel derived namespace, not a replacement for the 7 canonical namespaces. |
| **Constrained by** | Privacy boundary (CampaignBundle/SessionBundle) | Community tools must never expose campaign state. Only skin-layer data is shareable. |

---

## 14. Success Criteria

This research is complete when:

- [x] **Mechanical fingerprint algorithm defined** -- Deterministic hash from
  `MechanicalSpellTemplate` tactical identity fields (`target_type`,
  `damage_type`, `effect_type`, `aoe_shape`, `save_type`, `tier`,
  `delivery_mode`, `auto_hit`, `requires_attack_roll`, `damage_formula`,
  `conditions_applied`). Extended to creatures and feats.
- [x] **Shareable bundle boundary defined** -- `VocabularyRegistry` +
  `PresentationSemanticsRegistry` + `WorldThemeBrief` are shareable.
  `CampaignBundle` + `SessionBundle` are not.
- [x] **Community vocabulary emergence path documented** -- Mechanical class
  taxonomy, four-phase community language evolution, system facilitation
  mechanisms.
- [x] **Educational UX concepts specified** -- Discovery log progressive
  revelation, mechanical view toggle, cross-world comparison tool, fingerprint
  display locations.
- [x] **Cross-world communication tools designed** -- Build planner with
  two-tier resolution, strategy forums with fingerprint links, world gallery,
  translate feature.
- [x] **Rosetta Stone architecture documented** -- `content_id` as universal
  translator, layer connection diagram, UI interaction model, "same spell
  different skin" invariant.
- [x] **Prioritized recommendation list produced** -- P0 through P3 with
  clear dependencies and implementation scope.

---

*End of RQ-SPRINT-010.*

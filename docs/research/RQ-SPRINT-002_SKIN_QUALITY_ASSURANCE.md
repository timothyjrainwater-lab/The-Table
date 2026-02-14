# RQ-SPRINT-002: Skin Quality Assurance -- Presentation Semantics Generation

## Metadata

```
Sprint:     RQ-SPRINT-002
Scope:      Layer B (Presentation Semantics) generation feasibility & quality criteria
Status:     COMPLETE
Date:       2026-02-14
Governing:  AD-007 Presentation Semantics Contract (RATIFIED 2026-02-12)
```

## 1 -- Current Layer B Schema Analysis

### 1.1 Schema location and structure

The canonical Layer B schema lives in two files:

| File | Role |
|------|------|
| `aidm/schemas/presentation_semantics.py` (342 lines) | Frozen Python dataclasses: enums, `AbilityPresentationEntry`, `EventPresentationEntry`, `PresentationSemanticsRegistry` |
| `docs/schemas/presentation_semantics_registry.schema.json` | Machine-readable JSON Schema (enums, validation, defaults) |

The Python module declares three frozen dataclasses and six enums. Every field name and every enum value must match between the Python classes and the JSON schema; a test in `tests/test_presentation_semantics.py` enforces that invariant.

### 1.2 AbilityPresentationEntry -- the core skin record

Eight required fields, five optional:

| # | Field | Python type | Enum cardinality | Populated by SemanticsStage today? |
|---|-------|------------|-------------------|------------------------------------|
| 1 | `content_id` | `str` | -- | Yes |
| 2 | `delivery_mode` | `DeliveryMode` | 12 values | Yes |
| 3 | `staging` | `Staging` | 8 values | Yes |
| 4 | `origin_rule` | `OriginRule` | 6 values | Yes |
| 5 | `vfx_tags` | `tuple[str, ...]` | open (tags) | Yes |
| 6 | `sfx_tags` | `tuple[str, ...]` | open (tags) | Yes |
| 7 | `scale` | `Scale` | 4 values | Yes |
| 8 | `provenance` | `SemanticsProvenance` | -- | Yes |
| 9 | `residue` | `tuple[str, ...]` | open (tags) | **No** -- always `()` |
| 10 | `ui_description` | `Optional[str]` | free text | **No** -- always `None` |
| 11 | `token_style` | `Optional[str]` | free text | **No** -- always `None` |
| 12 | `handout_style` | `Optional[str]` | free text | **No** -- always `None` |
| 13 | `contraindications` | `tuple[str, ...]` | open (tags) | **No** -- always `()` |

**Summary**: 8 of 13 fields are populated. The two most important gaps are `ui_description` (the rulebook blurb a player reads) and `residue` (what the scene looks like after the effect).

### 1.3 Enum spaces

**DeliveryMode** (12 values):

```
projectile  beam  burst_from_point  aura  cone  line
touch  self  summon  teleport  emanation  gaze
```

**Staging** (8 values):

```
travel_then_detonate  instant  linger  pulses
channeled  delayed  expanding  fading
```

**OriginRule** (6 values):

```
from_caster  from_chosen_point  from_object
from_target  from_ground  ambient
```

**Scale** (4 values):

```
subtle  moderate  dramatic  catastrophic
```

### 1.4 EventPresentationEntry -- fallback semantics for generic events

18 event categories, each with `default_scale`, `default_vfx_tags`, `default_sfx_tags`, and `narration_priority`. All 18 are already populated in the `EVENT_DEFAULTS` dict in `semantics.py` (lines 91-200). Examples:

- `MELEE_ATTACK`: scale=MODERATE, vfx=`(impact, sparks)`, sfx=`(clang, thud)`, priority=ALWAYS_NARRATE
- `ENTITY_DEFEATED`: scale=DRAMATIC, vfx=`(collapse, fade)`, sfx=`(thud, silence)`, priority=ALWAYS_NARRATE
- `TURN_BOUNDARY`: scale=SUBTLE, vfx=`()`, sfx=`()`, priority=NEVER_NARRATE

### 1.5 Integration plumbing that already exists

**NarrativeBrief** (`aidm/lens/narrative_brief.py`, line 103):

```python
presentation_semantics: Optional[AbilityPresentationEntry] = None
```

The Lens assembler (`assemble_narrative_brief`, line 322) accepts a `presentation_semantics` parameter and threads it through to Spark. Round-trip serialization (`to_dict` / `from_dict`) is implemented and tested.

**PresentationRegistryLoader** (`aidm/lens/presentation_registry.py`):

Provides O(1) lookup by `content_id` or `EventCategory`. Validates entry counts and rejects duplicates on load.

**SemanticsStage** (`aidm/core/compile_stages/semantics.py`, 561 lines):

Stage 3 of the world compiler. Loads spells.json + feats.json, applies rule-based mappers, writes `presentation_semantics.json` to the world bundle.

### 1.6 What is NOT yet wired

| Gap | Impact |
|-----|--------|
| `Narrator` does not read `presentation_semantics` from `NarrativeBrief` | Spark templates ignore staging, vfx_tags, sfx_tags -- narration is unconstrained by Layer B |
| `ContradictionChecker` has no staging-constraint rule class | No automated detection when narration contradicts delivery_mode or staging |
| `ui_description` is never generated | Rulebook entries cannot be produced; worlds feel generic |
| `residue` is never generated | No post-effect scene state (scorch marks, frost, etc.) |
| Content pack `delivery_mode` field contains stale duration values (`"instantaneous"` for 352 of 605 spells) | SemanticsStage correctly ignores this field and re-derives from `target_type`/`aoe_shape`; the content pack field is vestigial |

### 1.7 Content pack inventory

```
Spells:       605
Feats:        109 total, 30 active (with trigger or grants_action)
Creatures:    (separate bestiary stage, out of scope for this sprint)

Spell target_type distribution:
  single:  316   (52%)
  touch:   128   (21%)
  area:     99   (16%)
  self:     45    (7%)
  ray:      17    (3%)

Spell effect_type distribution:
  utility: 304   (50%)
  debuff:  109   (18%)
  buff:     94   (16%)
  damage:   89   (15%)
  healing:   9    (1%)

Spell AoE shape distribution (of the 64 AoE spells):
  cone: 17   spread: 16   emanation: 15   burst: 13   line: 3

Spell tier distribution:
  0: 28   1: 87   2: 89   3: 80   4: 68   5: 64   6: 64   7: 51   8: 43   9: 31
```

---

## 2 -- Derivability Matrix

### 2.1 The 10 representative abilities

For each of the 10 archetypal mechanics specified in the research task, I traced the derivation path through the existing mapper functions in `semantics.py` and the bone-layer fields present in `spells.json`, `attack_resolver.py`, `maneuver_resolver.py`, and `environmental_damage_resolver.py`.

**Legend:**
- **D** = deterministic from bone-layer metadata (rule or lookup table)
- **C** = requires creative / world-aware generation (LLM or human authoring)
- **H** = hybrid: a sensible template default exists, but creative enrichment raises quality

### 2.2 Matrix

```
                             delivery   staging    origin    scale    vfx_      sfx_      ui_          residue
                             _mode                 _rule              tags      tags      description
-----------------------------+----------+----------+---------+--------+---------+---------+------------+---------
1  Ranged touch / auto-hit   | D        | D        | D       | D      | D       | D       | C          | H
   (Magic Missile)           | BEAM     | INSTANT  | CASTER  | SUBTLE | shimmer | hum     | --         | --
   via: target_type=ray      |          |          |         | tier=1 | pulse   | pulse   |            |
                             |          |          |         |        | energy  |         |            |
                             |          |          |         |        | blast   |         |            |
-----------------------------+----------+----------+---------+--------+---------+---------+------------+---------
2  Area burst damage         | D        | D        | D       | D      | D       | D       | C          | H
   (Fireball)                | BURST_   | TRAVEL_  | CHOSEN  | DRAMA  | fire    | whoosh  | --         | scorch
   via: aoe_shape=burst,     | FROM_PT  | THEN_DET | _POINT  | TIC    | glow    | crackle |            | smoke
   damage_type=fire, tier=3  |          |          |         |        | heat_d  |         |            |
                             |          |          |         |        | energy  |         |            |
                             |          |          |         |        | blast   |         |            |
-----------------------------+----------+----------+---------+--------+---------+---------+------------+---------
3  Melee full attack         | D        | D        | D       | D      | H       | H       | C          | C
   (iterative weapon atks)   | TOUCH    | INSTANT  | CASTER  | MODER  | generic | generic | --         | weapon-
   via: event defaults for   |          |          |         | ATE    | _magic  | _cast   |            | depend-
   MELEE_ATTACK category     |          |          |         |        | (impact | (clang  |            | ent
                             |          |          |         |        | sparks) | thud)   |            |
-----------------------------+----------+----------+---------+--------+---------+---------+------------+---------
4  Save-or-suck              | D        | D        | D       | D      | D       | D       | C          | H
   (Hold Person: Will,       | PROJECT  | LINGER   | CASTER  | MODER  | glow    | drone   | --         | --
   condition)                | ILE      | (dur has | (single | ATE    | mesmer  | fade    |            |
   via: target=single,       |          | round)   | target) | tier=2 | ize     |         |            |
   range=medium,dur=rounds   |          |          |         |        |         |         |            |
-----------------------------+----------+----------+---------+--------+---------+---------+------------+---------
5  Buff / enhancement        | D        | D        | D       | D      | D       | D       | C          | H
   (Bull's Strength)         | TOUCH    | LINGER   | CASTER  | SUBTLE | glow    | chime   | --         | aura
   via: target=touch,        |          | (dur has | (touch  | tier=2 | aura    | hum     |            | fade
   effect=buff,dur=rounds    |          | round)   | target) |        | morph   |         |            |
                             |          |          |         |        | shift   |         |            |
-----------------------------+----------+----------+---------+--------+---------+---------+------------+---------
6  Healing                   | D        | D        | D       | D      | D       | D       | C          | H
   (Cure Light Wounds)       | TOUCH    | INSTANT  | CASTER  | SUBTLE | radianc | chime   | --         | light
   via: target=touch,        |          |          |         | tier=1 | warmth  | swell   |            | wisps
   effect=healing,           |          |          |         |        | materi  |         |            | (fade)
   dur=instantaneous         |          |          |         |        | portal  |         |            |
-----------------------------+----------+----------+---------+--------+---------+---------+------------+---------
7  Condition application     | D        | D        | D       | D      | H       | H       | C          | H
   (Stinking Cloud:          | BURST_   | LINGER   | CHOSEN  | DRAMA  | materi  | generic | --         | fog
   area, Fort, nauseate)     | FROM_PT  | (dur has | _POINT  | TIC    | portal  | _cast   |            | residue
   via: aoe_shape=spread,    |          | round)   | (spread | tier=3 | dim     |         |            |
   target=area, effect=debuf |          |          | shape)  |        | weaken  |         |            |
-----------------------------+----------+----------+---------+--------+---------+---------+------------+---------
8  Movement effect           | D        | D        | D       | D      | H       | H       | C          | H
   (Bull Rush maneuver)      | TOUCH    | INSTANT  | CASTER  | MODER  | motion  | grunt   | --         | impact
   via: event defaults for   |          |          |         | ATE    | _blur   | impact  |            | marks
   COMBAT_MANEUVER category  |          |          |         |        |         |         |            |
-----------------------------+----------+----------+---------+--------+---------+---------+------------+---------
9  Environmental hazard      | D        | D        | D       | D      | H       | H       | C          | H
   (falling / lava)          | EMANAT   | INSTANT  | GROUND  | MODER  | hazard  | crackle | --         | hazard-
   via: event defaults for   | ION      |          | (env    | ATE    | _glow   |         |            | persist
   ENVIRONMENTAL_DAMAGE cat  |          |          | source) |        |         |         |            |
-----------------------------+----------+----------+---------+--------+---------+---------+------------+---------
10 Progression milestone     | D        | D        | D       | D      | C       | C       | C          | C
   (level up / stat gain)    | SELF     | INSTANT  | CASTER  | DRAMA  | (no     | (no     | --         | --
   via: no content pack      |          |          |         | TIC    | table)  | table)  |            |
   entry; must be authored   |          |          |         |        |         |         |            |
```

### 2.3 Field-level determinism summary

| Field | % Deterministic | Current mapper | Gaps |
|-------|-----------------|----------------|------|
| `delivery_mode` | **95%** | `map_delivery_mode()` lines 208-242 | GAZE, TELEPORT, AURA not yet reachable from any bone-layer path |
| `staging` | **90%** | `map_staging()` lines 245-264 | DELAYED, EXPANDING, PULSES not reachable (need new duration formulas or effect subtypes) |
| `origin_rule` | **85%** | `map_origin_rule()` lines 281-295 | FROM_OBJECT, FROM_GROUND, AMBIENT never produced (no bone-layer trigger) |
| `scale` | **80%** | `map_scale()` lines 267-278 | Weapons and environmental hazards lack `tier`; falling damage is context-dependent |
| `vfx_tags` | **60%** | `map_vfx_tags()` lines 298-319 via 3 lookup tables | 304 utility spells have no damage_type, so they fall through to school table only; tag overlap (e.g. "glow" in 3 tables) reduces distinctiveness |
| `sfx_tags` | **60%** | `map_sfx_tags()` lines 322-340 via 2 lookup tables | Same gap as vfx_tags; utility/debuff spells often get `("generic_cast",)` |
| `ui_description` | **0%** | Not implemented | Critical gap; requires either template or LLM |
| `residue` | **0%** | Not implemented | Sensible defaults derivable from damage_type for ~40% of abilities |
| `contraindications` | **0%** | Not implemented | Requires manual curation per delivery_mode family |

### 2.4 Key observation: utility spells

304 of 605 spells (50%) have `effect_type=utility`. These spells typically have:
- No `damage_type` (so VFX_BY_DAMAGE_TYPE yields nothing)
- No `healing_formula` (so VFX_BY_EFFECT_TYPE yields nothing)
- Only the school table contributes tags

This means half the spell catalogue gets only 2 vfx_tags (the school pair) and falls back to `("generic_cast",)` for sfx_tags. Distinctiveness is weakest in this segment.

---

## 3 -- Quality Criteria

### 3.1 Consistency

**Definition:** Within a compiled world, abilities with the same mechanical template produce identical Layer B values.

**Measurable test:** For every pair of spells sharing `(target_type, aoe_shape, effect_type, damage_type, tier)`, assert identical `(delivery_mode, staging, origin_rule, scale)`.

**Current status:** PASS. The rule-based mappers are pure functions of their inputs with no randomness.

**Risk if we add LLM:** High. LLM outputs vary with temperature, seed, and model version. Mitigation: LLM-generated fields must be cached and keyed by `(content_id, world_seed, compiler_version)`. Core enum fields (delivery_mode, staging, origin_rule, scale) must remain deterministic.

### 3.2 Distinctiveness

**Definition:** Abilities with different Layer A mechanics produce noticeably different Layer B entries.

**Measurable test:** For two spells with different `(aoe_shape, damage_type, effect_type)`, assert that they differ on at least 2 of `{delivery_mode, staging, vfx_tags, scale}`.

**Current status:** PASS for damage spells (damage_type drives vfx separation). WEAK for utility spells (304 spells collapsing onto school-only tags). A transmutation utility spell and a transmutation buff spell currently produce identical `vfx_tags=("morph", "shift", "glow", "aura")`.

**Remedy:** Add a VFX_BY_SUBSCHOOL table (e.g., `polymorph -> ("body_warp", "stretch")`, `teleportation -> ("blink", "afterimage")`) or promote `descriptors` from the content pack (already present; e.g., `["fire"]`, `["mind-affecting"]`) into vfx derivation.

### 3.3 Learnability

**Definition:** After seeing 3-5 abilities with the same delivery_mode, a player can predict the delivery_mode of the next similar ability.

**Measurable test:** Present a test subject with 5 cone spells, all labeled `delivery_mode=CONE`. Present a 6th cone spell unlabeled. Predict CONE.

**Current status:** Structurally achievable because the mapping rule is: `aoe_shape=cone -> delivery_mode=CONE`. The rule has zero exceptions. The concern is that the player never sees the word "CONE" directly -- they see it through narration and VFX, which currently do not reference delivery_mode.

**Remedy:** The Narrator must use `presentation_semantics.staging` to structure narration timing, and `delivery_mode` to select narration verbs. This is a Spark-layer change, not a Layer B schema change.

### 3.4 Evocativeness

**Definition:** The combination of `vfx_tags + sfx_tags + ui_description` creates a mental image of the ability.

**Measurable test:** Given only `vfx_tags`, `sfx_tags`, and `ui_description`, a reader can identify the damage type and approximate area.

**Current status:** FAIL. `ui_description` is always `None`. Without it, the tags alone (`fire, glow, heat_distortion, energy, blast`) suggest fire but do not paint a picture of a streaking projectile detonating at range. A player looking at a rulebook entry sees nothing.

**Remedy:** This is the critical gap. Template fallback gets the field from `None` to something; LLM enrichment gets it from something to evocative.

### 3.5 Tonal coherence

**Definition:** All abilities in a world share a consistent aesthetic vocabulary.

**Measurable test:** Run a sentiment/style classifier across all `ui_description` values in a compiled world. Standard deviation of "tone score" should be below threshold.

**Current status:** Vacuously true (no descriptions exist). Once descriptions are generated, the risk is that template descriptions feel flat and uniform while LLM descriptions drift tonally between entries.

**Remedy:** If using LLM, include a "World Voice Guide" (3-5 sentences of tone direction) in every prompt. If using templates, ensure the template vocabulary is drawn from a single register.

---

## 4 -- Generation Strategy Assessment

### 4.1 Strategy A: Pure Template

**Approach:** All Layer B fields derived from bone-layer metadata using deterministic rule functions. `ui_description` and `residue` added via template strings.

**Quality ceiling:**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Consistency | Excellent | Pure functions; zero variance |
| Distinctiveness | Good | Driven by damage_type + school; weak for 304 utility spells |
| Learnability | Excellent | Patterns are absolute rules |
| Evocativeness | Weak | "A dramatic burst dealing fire damage." is accurate but lifeless |
| Tonal coherence | Neutral | Uniformly flat; no tone drift but no tone at all |

**Consistency risk:** None.

**Computational cost:** Under 1 second for all 605 spells + 30 feats. No external calls.

### 4.2 Strategy B: Pure LLM

**Approach:** Send bone-layer data + world theme description to an LLM for every ability. LLM returns a JSON object with all Layer B fields.

**Quality ceiling:**

| Criterion | Rating | Notes |
|-----------|--------|-------|
| Consistency | Medium | LLM may assign BEAM to one ray spell and PROJECTILE to another |
| Distinctiveness | Excellent | LLM creates unique descriptions and tags per ability |
| Learnability | Medium | Pattern varies by LLM reasoning; hard for player to predict |
| Evocativeness | Excellent | LLM produces vivid, world-aware prose |
| Tonal coherence | Good-to-Excellent | LLM can follow a voice guide if prompted well |

**Consistency risk:** HIGH.

**Computational cost:** ~1-2 seconds per LLM call. Sequential: 605 calls = 10-20 minutes. Parallel with rate limits: 2-5 minutes.

### 4.3 Strategy C: Hybrid (Template Core + Optional LLM Creative Layer)

**Approach:** Deterministic rules populate all enum fields (delivery_mode, staging, origin_rule, scale) and baseline tags (vfx_tags, sfx_tags). A separate, optional LLM pass generates only the creative fields: `ui_description`, enriched `vfx_tags`, and `residue`.

**Why this is the right architecture:**

1. The enum fields (4 of 8 required) have mechanical meaning. A fireball with `delivery_mode=BURST_FROM_POINT` and `staging=TRAVEL_THEN_DETONATE` constrains how the Narrator describes it, how the battle map animates it, and how the ContradictionChecker validates it. These fields must be deterministic. The existing mapper functions already handle them correctly.

2. The tag fields (vfx_tags, sfx_tags) have sensible deterministic baselines from the 3 VFX tables and 2 SFX tables. A world theme layer can optionally replace or extend these tags, but the baseline is functional.

3. The prose field (ui_description) has no deterministic path to quality. A template can produce a non-null placeholder. Only an LLM or human author can make it evocative. This field is the correct place for LLM investment.

4. The residue field is partially deterministic (fire damage = scorch_marks) and partially creative (what does enchantment residue look like in a crystal world?).

**Quality ceiling:**

| Criterion | Without LLM | With LLM |
|-----------|------------|----------|
| Consistency | Excellent | Excellent (core is still deterministic) |
| Distinctiveness | Good | Excellent |
| Learnability | Excellent | Excellent |
| Evocativeness | Weak (template ui_description) | Excellent |
| Tonal coherence | Neutral | Excellent (voice guide in prompt) |

**Consistency risk:** Low. Enum fields never touch the LLM. LLM outputs are cached by `(content_id, world_seed, compiler_version)` and hashed via `provenance.llm_output_hash`. Same seed = same output.

**Computational cost:**
- Without LLM: under 1 second for 635 abilities.
- With LLM (first compile): 2-5 minutes for 635 calls (parallelized, only generating ui_description + residue, ~100 tokens per call).
- With LLM (cached): under 1 second (read from disk).

---

## 5 -- Generation Strategy Recommendation

### 5.1 Recommendation: Hybrid (Strategy C)

**Rationale in three sentences:**

The four enum fields are mechanically meaningful, must be deterministic, and are already implemented correctly. The prose field (`ui_description`) is the only field that materially affects whether a world feels authored vs. generic, and it requires creative generation. Splitting the problem into "deterministic core + optional creative layer" eliminates the consistency risk of pure LLM while preserving the quality ceiling.

### 5.2 Phase plan

**Phase 1 -- Template MVP (this sprint):**

Add `ui_description` and `residue` generation to `map_spell_to_entry()` using template functions. No LLM, no external dependencies. Deliverables:

1. `generate_ui_description(spell, entry) -> str` -- template based on effect_type, delivery_mode, scale, damage_type.
2. `generate_residue(spell) -> tuple[str, ...]` -- lookup table keyed on damage_type with sensible defaults.
3. Wire both into `map_spell_to_entry()` and `map_feat_to_entry()`.
4. All 605 + 30 entries get non-null `ui_description` and (where applicable) non-empty `residue`.
5. Tests: round-trip serialization, template coverage for all 5 effect_types, residue for all 8 damage_types.

**Phase 2 -- Narrator integration (next sprint):**

Teach the Narrator to consume `presentation_semantics` from NarrativeBrief:

1. Use `staging` to structure narration timing (e.g., two-sentence narration for `TRAVEL_THEN_DETONATE`: travel clause + impact clause).
2. Use `vfx_tags` as vocabulary seeds for descriptive adjectives.
3. Use `scale` to modulate narration intensity.
4. Add `staging` constraint to ContradictionChecker: if `delivery_mode=PROJECTILE`, narration must not say "erupting from the ground."

**Phase 3 -- Optional LLM enrichment (future sprint):**

Add an LLM enrichment pass gated behind `--use-llm` and `--world-theme`:

1. For each ability, send the deterministic baseline + world theme to LLM.
2. LLM returns only `ui_description`, optionally customized `vfx_tags`, and `residue`.
3. LLM output is hashed and stored in `provenance.llm_output_hash`.
4. Cached per `(content_id, world_seed, compiler_version)`.
5. Deterministic core (delivery_mode, staging, origin_rule, scale) is NEVER LLM-generated.

---

## 6 -- MVP Minimum: What Makes a World Feel Authored?

### 6.1 The 6-field floor

A world feels authored -- not generated -- when every ability has at least these 6 fields populated:

| Field | Why it matters | Source |
|-------|---------------|--------|
| `delivery_mode` | Tells the player HOW the effect reaches them. | Deterministic mapper (implemented) |
| `staging` | Tells the player WHEN things happen. | Deterministic mapper (implemented) |
| `scale` | Tells the player HOW BIG the moment is. | Deterministic mapper (implemented) |
| `vfx_tags` | Tells the battle map WHAT TO SHOW and gives Spark vocabulary. | Lookup tables (implemented) |
| `sfx_tags` | Gives Spark audio vocabulary. | Lookup tables (implemented) |
| `ui_description` | The rulebook blurb a player reads when they look up an ability. This is the single field that separates "engine" from "game." | **NOT YET IMPLEMENTED -- critical gap** |

### 6.2 The quality gap at the floor

With template `ui_description`, examples:

| Ability | Template output |
|---------|-----------------|
| Fireball (fire, burst, tier 3) | "A dramatic burst from point dealing fire damage." |
| Magic Missile (force, ray, tier 1) | "A subtle beam dealing force damage." |
| Cure Light Wounds (healing, touch, tier 1) | "A subtle touch that restores vitality." |
| Hold Person (debuff, single, tier 2) | "A moderate projectile that inflicts a harmful condition." |
| Bull's Strength (buff, touch, tier 2) | "A moderate touch that enhances the recipient." |

These are accurate but lifeless. They are enough for an MVP because:
1. The field is non-null (rulebook can display something).
2. The content is correct (delivery_mode and scale are accurate).
3. The player can distinguish abilities (different delivery, different damage type).
4. The template can be replaced wholesale by LLM output in Phase 3 without schema changes.

### 6.3 Immediate blockers for MVP

There is exactly one blocker: the `ui_description` field must be generated. It requires:

1. A `generate_ui_description(spell: dict, entry: AbilityPresentationEntry) -> str` function (~30 lines).
2. A `generate_residue(spell: dict) -> tuple[str, ...]` function (~20 lines, optional but trivial).
3. Wiring both into `map_spell_to_entry()` (3 lines changed).
4. Wiring both into `map_feat_to_entry()` (3 lines changed).
5. Test coverage for all effect_types and a round-trip serialization check.

---

## Appendix A -- File Reference

| File | Lines | Role in Layer B |
|------|-------|-----------------|
| `aidm/schemas/presentation_semantics.py` | 342 | Schema: 6 enums, 3 frozen dataclasses |
| `aidm/core/compile_stages/semantics.py` | 561 | SemanticsStage: rule mappers, lookup tables, stage execution |
| `aidm/lens/presentation_registry.py` | 155 | Registry loader: O(1) lookup by content_id or EventCategory |
| `aidm/lens/narrative_brief.py` | 824 | NarrativeBrief: carries Layer B from Lens to Spark (line 103) |
| `aidm/narration/narrator.py` | 413 | Narrator: template-based, does NOT consume Layer B |
| `aidm/core/spell_resolver.py` | ~600 | Spell resolution: SpellDefinition, SpellTarget, SpellEffect, DamageType enums |
| `aidm/core/attack_resolver.py` | ~400 | Attack resolution: weapon attacks, crits, DR, sneak attack |
| `aidm/core/maneuver_resolver.py` | ~400 | Maneuver resolution: bull rush, trip, overrun, sunder, disarm, grapple |
| `aidm/core/environmental_damage_resolver.py` | ~200 | Environmental: fire, acid, lava, spiked pit |
| `aidm/data/content_pack/spells.json` | 30594 | 605 spell definitions (bone-layer data) |
| `aidm/data/content_pack/feats.json` | ~3000 | 109 feat definitions (30 active) |
| `docs/decisions/AD-007_PRESENTATION_SEMANTICS_CONTRACT.md` | 229 | Architecture decision: three-layer model ratified |
| `docs/schemas/presentation_semantics_registry.schema.json` | ~300 | JSON Schema: canonical field names and enum values |
| `tests/test_presentation_semantics.py` | ~200 | Tests: enum match, freeze enforcement, round-trip, registry validation |
| `tests/test_compile_semantics.py` | ~300 | Tests: mapper rules, output validity, no duplicates, stage registration |

## Appendix B -- Existing Mapping Rules (Exact)

These are the deterministic rules currently implemented in `aidm/core/compile_stages/semantics.py`.

### delivery_mode (lines 208-242)

```
target_type == "ray"                                -> BEAM
target_type == "touch"                              -> TOUCH
target_type == "self"                               -> SELF
aoe_shape == "burst"                                -> BURST_FROM_POINT
aoe_shape == "cone"                                 -> CONE
aoe_shape == "line"                                 -> LINE
aoe_shape == "emanation"                            -> EMANATION
aoe_shape == "spread"                               -> BURST_FROM_POINT
effect_type == "summoning"                          -> SUMMON
target_type == "area" (no shape)                    -> BURST_FROM_POINT
target_type == "single" and range not touch/personal -> PROJECTILE
[default]                                           -> PROJECTILE
```

Unreachable enum values: AURA, GAZE, TELEPORT (no bone-layer path produces them).

### staging (lines 245-264)

```
aoe_shape == "burst" and duration == "instantaneous" -> TRAVEL_THEN_DETONATE
duration == "instantaneous"                          -> INSTANT
concentration == True                                -> CHANNELED
"round" in duration string                           -> LINGER
[default]                                            -> INSTANT
```

Unreachable: DELAYED, EXPANDING, PULSES, FADING (no bone-layer duration formula triggers them).

### origin_rule (lines 281-295)

```
target_type in (self, touch, ray)                    -> FROM_CASTER
aoe_shape in (burst, spread)                         -> FROM_CHOSEN_POINT
aoe_shape in (emanation, cone)                       -> FROM_CASTER
effect_type == "summoning"                           -> FROM_CHOSEN_POINT
[default]                                            -> FROM_CASTER
```

Unreachable: FROM_OBJECT, FROM_GROUND, AMBIENT.

### scale (lines 267-278)

```
aoe_radius >= 40 or tier >= 7                        -> CATASTROPHIC
aoe_radius >= 20 or tier >= 5                        -> DRAMATIC
aoe_radius >= 10 or tier >= 3                        -> MODERATE
[default]                                            -> SUBTLE
```

### VFX lookup tables (lines 41-70)

```
VFX_BY_DAMAGE_TYPE:
  fire            -> (fire, glow, heat_distortion)
  cold            -> (frost, ice_crystals, mist)
  electricity     -> (lightning, spark, arc)
  acid            -> (acid, dissolve, hiss)
  sonic           -> (shockwave, ripple)
  force           -> (shimmer, pulse)
  positive energy -> (radiance, warmth)
  negative energy -> (shadow, drain)

VFX_BY_SCHOOL:
  necromancy      -> (shadow, decay)
  illusion        -> (shimmer, distortion)
  enchantment     -> (glow, mesmerize)
  divination      -> (glow, reveal)
  abjuration      -> (shield, ward)
  transmutation   -> (morph, shift)
  conjuration     -> (materialize, portal)
  evocation       -> (energy, blast)

VFX_BY_EFFECT_TYPE:
  healing         -> (radiance, warmth)
  summoning       -> (portal, materialize)
  buff            -> (glow, aura)
  debuff          -> (dim, weaken)
```

### SFX lookup tables (lines 72-88)

```
SFX_BY_DAMAGE_TYPE:
  fire            -> (whoosh, crackle)
  cold            -> (crystallize, shatter)
  electricity     -> (zap, thunder)
  acid            -> (sizzle, bubble)
  sonic           -> (boom, rumble)
  force           -> (hum, pulse)

SFX_BY_EFFECT_TYPE:
  healing         -> (chime, swell)
  summoning       -> (whoosh, materialize)
  buff            -> (chime, hum)
  debuff          -> (drone, fade)
```

## Appendix C -- Content Pack delivery_mode Caveat

The content pack `spells.json` has a `delivery_mode` field on every spell, but its values do NOT match the `DeliveryMode` enum. Distribution:

```
instantaneous:    352  (not a valid DeliveryMode)
touch:            128  (valid)
self:              44  (valid)
burst_from_point:  29  (valid)
cone:              17  (valid)
ray:               15  (valid)
emanation:         15  (valid)
line:               3  (valid)
projectile:         2  (valid)
```

The SemanticsStage mapper correctly ignores this field and re-derives `delivery_mode` from `target_type` and `aoe_shape`. The content pack field appears to be a vestigial artifact from an earlier extraction pass.

---

*End of RQ-SPRINT-002 report.*

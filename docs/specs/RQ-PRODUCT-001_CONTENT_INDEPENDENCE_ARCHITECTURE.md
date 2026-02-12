# RQ-PRODUCT-001: Content Independence Architecture

**Domain:** Product Architecture — IP Separation & Content Pack Design
**Status:** DRAFT
**Filed:** 2026-02-12
**Gate:** Must be reviewed before any content ships externally
**Prerequisite:** PO design session (2026-02-12), House Policy Governance Doctrine

---

## 1. Thesis

The engine (Box/Lens/Spark) implements mathematical procedures. The content
(spells, feats, skills, classes, creatures) is data that feeds those procedures.
The narrative (what the player hears and reads) is generated fresh each session
by Spark, constrained by the mechanical truth and a behavioral contract.

For the product to be independently marketable, the content layer must contain
**zero copyrightable text**. Game mechanics — mathematical formulas, resolution
procedures, state machines — are not copyrightable. The engine code is original
work. The only IP risk is in static text that could be traced to a source
rulebook.

The PO's design insight: **there should be no static flavor text at all.**
Content pack entries consist of:

1. **Mechanical definitions** — pure math (formulas, parameters, thresholds)
2. **Behavioral contracts** — how abilities operate in space and time (delivery
   model, origin, travel, detonation, phases)
3. **Category tags** — semantic labels Spark uses to generate appropriate
   narration (school, element, scale, intensity)

Flavor text does not exist as a static artifact. Spark generates narration from
the behavioral contract and category tags, adapted to the campaign's skin and
the current scene context. The "player handbook" shows mechanics and behavior,
not prose.

This architecture produces:

- **Zero copyrightable text in the content pack** (math + technical specs)
- **Consistent player experience** (behavioral contracts are static and
  inspectable)
- **Infinite narrative variety** (Spark generates fresh narration every session)
- **Multi-skin support** (same mechanics, different settings, no content changes)
- **Full IP independence** (nothing in the shipped product traces to any
  third-party rulebook)

---

## 2. The Three-Layer Content Model

### Layer 1: Mechanical Definition (Box Truth)

What the ability **does** mathematically. Box consumes this for resolution.
Players inspect this for tactical decisions about numbers.

```yaml
ABILITY_003:
  tier: 3
  cost: [ability_slot_tier_3]
  range_formula: 400 + (40 * caster_tier)
  area: {shape: sphere, radius_ft: 20}
  targeting: designated_point
  save: {type: reflex, effect: half_damage}
  damage: {dice: "min(10, caster_tier)d6", type: fire}
  duration: instantaneous
  components: [verbal, somatic, material]
  prerequisites: [caster_tier >= 5]
```

**IP status:** Pure mathematics. Uncopyrightable. The formula
`min(10, caster_tier) * d6` is a mathematical expression. The fact that
a well-known spell uses this formula is irrelevant — you cannot own a
damage curve.

### Layer 2: Behavioral Contract (Lens Constraint)

How the ability **operates in space and time**. Lens consumes this to constrain
Spark's narration. Players inspect this for tactical decisions about spatial
behavior.

This is the layer that D&D "spell descriptions" encode implicitly in prose.
We extract it as structured data.

```yaml
ABILITY_003:
  behavior:
    delivery: projectile
    origin: caster_hand
    target: designated_point_in_range
    travel_path: straight_line
    travel_speed: instant_arrival
    detonation_trigger: on_reach_target
    detonation_shape: sphere
    line_of_effect: required
    blocked_by: [total_cover, solid_obstruction]
    spreads_around_corners: true
    visual_phases:
      - phase: launch
        description: "Effect originates from caster"
      - phase: travel
        description: "Projectile traverses to target point"
      - phase: detonation
        description: "Area effect activates at target point"
      - phase: aftermath
        description: "Residual effects dissipate"
    sensory_tags: [bright, loud, thermal]
```

**IP status:** Technical specification of spatial behavior. Describing that an
effect is "a projectile that detonates at a target point in a spherical area"
is not copyrightable expression. It is a functional description of behavior,
equivalent to an engineering specification.

**Key property:** This is STATIC. Same every time. Same for every player. This
is what the "rulebook" displays when a player looks up an ability. It tells
them how it works, not what it looks like.

### Layer 3: Narrative Realization (Spark Output)

How the ability **is described this time**. Spark generates this fresh for each
use, constrained by:

- The behavioral contract (must match phases, delivery model, spatial behavior)
- The campaign skin (fantasy/sci-fi/horror/etc.)
- The scene context (dungeon/forest/spaceship/etc.)
- The DM persona (gritty/theatrical/humorous/terse)
- The NarrativeBrief (mechanical outcome — hit/miss, damage, defeat)

**IP status:** Ephemeral, generated text. Never static. Never stored as
content. Cannot be traced to any source because it is created fresh by the LLM
for each specific context.

**Key property:** This is VARIABLE. Different every time. Different for every
campaign. This is what the player *hears* during play. It must be consistent
with the behavioral contract but is otherwise free.

---

## 3. The Provenance Firewall

### What the Vault Is

The Vault (~23,750 files of extracted D&D 3.5e rulebook text) is a **human-
readable research library**. It exists so that developers can understand what
mechanics exist, how they interact, and what behavioral patterns the rules
describe.

### What the Vault Is Not

The Vault is **not a build input**. No automated tool reads Vault files to
produce content pack entries. No script transforms Vault text into shipping
content. No algorithmic process derives descriptions from Vault prose.

### The Firewall

```
VAULT (research reference)          CONTENT PACK (ships)
========================           ====================
  D&D 3.5e text                      Mechanical definitions (math)
  Flavor descriptions                Behavioral contracts (specs)
  Page citations                     Category tags (labels)
  Creative expression                NO TEXT DESCRIPTIONS
                                     NO FLAVOR PROSE
        │                                    │
        │   HUMAN UNDERSTANDING              │
        │   (read, comprehend,               │
        │    extract formula,                │
        │    close Vault,                    │
        │    write specification)            │
        │                                    │
        └──── NO AUTOMATED PATH ─────────────┘
```

The content authoring workflow:

1. Developer reads Vault entry to understand what a mechanic does
2. Developer closes the Vault
3. Developer writes mechanical definition as pure math
4. Developer writes behavioral contract as technical specification
5. Developer assigns category tags
6. **At no point is Vault text copied, paraphrased, or transformed**

### The Recognition Test

For every piece of static content in the product, apply this test:

> "Could a D&D player recognize this as coming from the PHB without being
> told?"

If yes → the content is too close to the source. Rewrite as pure specification.
If no → the content is safe.

This test applies to:
- Behavioral contract descriptions
- Category tag names
- UI labels
- Any static text visible to the player

This test does NOT apply to:
- Mathematical formulas (uncopyrightable regardless)
- Spark-generated narration (ephemeral, never stored)
- Engine code (original work)

---

## 4. Content Pack Schema (v1 Draft)

### Entry Structure

Every content pack entry follows the three-layer model:

```yaml
content_pack:
  schema_version: "1.0.0"
  pack_id: "core_v1"

abilities:
  - id: ABILITY_003
    category: [offensive, area, ranged, elemental]
    tier: 3
    mechanical:
      range: "400 + (40 * caster_tier)"
      area: {shape: sphere, radius_ft: 20}
      save: {type: reflex, effect: half_damage}
      damage: {formula: "min(10, caster_tier)d6", type: fire}
      duration: instantaneous
      components: [verbal, somatic, material]
    behavioral:
      delivery: projectile
      origin: caster
      target: designated_point
      travel: straight_line
      detonation: on_arrival
      line_of_effect: required
      blocked_by: [total_cover]
      spreads_around_corners: true
      phases: [launch, travel, detonation, aftermath]
      sensory: [bright, loud, thermal]
    tags:
      school: evocation
      element: fire
      scale: area_burst
      intensity: destructive
      combat_role: damage_dealer
```

### Content Categories

| Category | Count (v1 scope) | Entry Type |
|----------|-------------------|------------|
| Abilities (spells) | 53 | Mechanical + Behavioral + Tags |
| Talents (feats) | 15 | Mechanical + Tags |
| Skills | 7 | Mechanical + Tags |
| Class progressions | 4 | Mechanical (BAB/save/ability tables) |
| Conditions | 8 | Mechanical + Behavioral |
| Combat maneuvers | 6 | Mechanical + Behavioral |
| Equipment | ~100 | Mechanical + Tags |
| Creatures | ~20 | Mechanical + Behavioral + Tags |

### Delivery Model Vocabulary (Behavioral Contract)

Abilities need a standardized vocabulary for delivery models:

| Delivery Model | Description | Examples |
|---------------|-------------|---------|
| `projectile` | Originates from caster, travels to target | Ranged attack abilities |
| `ray` | Line from caster to single target | Targeted ranged effects |
| `emanation` | Radiates outward from a point | Aura effects |
| `burst` | Instantaneous area at designated point | Area detonations |
| `cone` | Expands from caster in a cone shape | Breath-style effects |
| `line` | Extends from caster in a line | Line-area effects |
| `touch` | Requires physical contact | Melee-range effects |
| `self` | Affects caster only | Self-buffs |
| `summoning` | Creates entity at designated point | Conjuration effects |

### Visual Phase Vocabulary

| Phase | When | Spark Narration Focus |
|-------|------|----------------------|
| `launch` | Effect originates | How it begins |
| `travel` | Effect moves through space | Movement description |
| `impact` | Effect hits target | Contact moment |
| `detonation` | Area effect activates | Expansion/spread |
| `duration` | Ongoing effect persists | Sustained description |
| `aftermath` | Effect concludes | Residual state |

Not all abilities use all phases. A touch ability uses [launch, impact].
A self-buff uses [launch, duration]. The phase list tells Spark what narrative
beats to hit.

### Creature Three-Layer Model

The same skeleton/muscle/skin separation applies to creatures. The monster
manual is not a single document — it is three layers, just like abilities.

**Layer 1: Mechanical Definition (Skeleton) — Substrate Level**

Pure math. Same across all worlds. Uncopyrightable.

```yaml
CREATURE_014:
  cr: 3
  type: beast
  size: large
  hit_dice: 4d10+8
  ac: 15
  speed: {walk: 30, fly: 60}
  bab: +4
  attacks:
    - {name: bite, bonus: +6, damage: "1d6+3", type: piercing}
    - {name: tail_sting, bonus: +1, damage: "1d4+1", type: piercing,
       special: ABILITY_047}  # poison
  saves: {fort: +6, ref: +4, will: +1}
  abilities: [ABILITY_047, ABILITY_048]  # poison, breath_weapon
  senses: {darkvision: 60, scent: true}
  skills: {SKILL_003: +5, SKILL_006: +8}  # spot, listen equivalents
```

**Layer 2: Behavioral Contract (Muscle) — Substrate Level**

How the creature fights, moves, and reacts. Static across all worlds.
Constrains Spark's narration of creature behavior.

```yaml
CREATURE_014:
  behavior:
    combat_doctrine: ambush_predator
    engagement_range: medium  # prefers 30-60 ft opening
    opening_tactic: breath_weapon_then_close
    melee_preference: bite_primary_sting_secondary
    retreat_threshold: 0.25  # retreats below 25% HP
    morale: aggressive_but_not_suicidal
    pack_behavior: solitary_or_mated_pair
    lair_behavior: territorial_within_1_mile
    movement_pattern: aerial_circling_before_dive
    sensory_profile: [keen_smell, good_vision, poor_hearing]
    threat_display: true  # warns before attacking
```

**Layer 3: Narrative Skin — World Level (Generated at World Creation)**

What the creature looks like, what it's called, its lore. Different per
world. Frozen at world creation. This is what appears in the world's
"monster manual."

| World | CREATURE_014 Name | Appearance | Habitat |
|-------|------------------|------------|---------|
| High Fantasy | Wyvern | Leathery wings, barbed tail | Mountain crags |
| Sci-Fi | Phase Raptor | Shimmering scales, plasma tail | Asteroid nests |
| Undersea | Abyssal Eel | Bioluminescent, venomous spines | Deep trenches |
| Horror | Nightwing | Membranous wings, necrotic sting | Abandoned cathedrals |

Same CR 3. Same 22 HP. Same ambush-then-dive behavior. Different skin.

**Why This Matters for IP**

The D&D Monster Manual is three things mixed together:
1. Statistics (math — uncopyrightable)
2. Combat behavior (functional specification — uncopyrightable)
3. Appearance, name, lore (creative expression — copyrightable)

We separate them. The content pack ships (1) and (2). The world generation
produces (3) fresh, themed to the world. Zero copyrightable text in the
shipped product. The same skeleton/muscle/skin principle that makes abilities
IP-clean makes creatures IP-clean.

---

## 5. Extraction Surface Audit

### Files Requiring Content Extraction

These files currently contain D&D-specific names and descriptions that would
become content pack entries:

| File | Current State | Extraction Target |
|------|--------------|-------------------|
| `aidm/core/spell_definitions.py` | 53 SpellDefinition entries with D&D names | Content pack ability entries |
| `aidm/core/feat_resolver.py` | FEAT_REGISTRY with 15 D&D feat names | Content pack talent entries |
| `aidm/core/skill_resolver.py` | 7 skill names hardcoded | Content pack skill entries |
| `aidm/core/experience_resolver.py` | CLASS_PROGRESSIONS with 4 class names | Content pack progression entries |
| `aidm/core/conditions.py` | 8 condition names | Content pack condition entries |
| `aidm/core/maneuver_resolver.py` | 6 maneuver names | Content pack maneuver entries |
| `aidm/core/doctrine_rules.py` | Monster doctrine with D&D creature types | Content pack creature behavioral tags |
| `aidm/narration/narrator.py` | 55 templates with some D&D-flavored language | Parameterized templates or Spark-generated |
| `aidm/spark/dm_persona.py` | "Dungeon Master" terminology | Neutral term ("Game Master" or branded) |
| `aidm/core/source_registry.py` | PHB/DMG/MM page citations | Internal rule ID citations |

### Files Already Clean (No Extraction Needed)

| File | Why It's Clean |
|------|---------------|
| `aidm/core/attack_resolver.py` | Pure math — d20 + bonus vs threshold |
| `aidm/core/spell_resolver.py` | Generic resolver — processes SpellDefinition data |
| `aidm/core/full_attack_resolver.py` | Iterative attack math |
| `aidm/core/save_resolver.py` | d20 + save bonus vs DC |
| `aidm/core/initiative.py` | d20 + modifier, ordering |
| `aidm/core/aoo.py` | Reaction trigger logic |
| `aidm/core/combat_controller.py` | Turn sequencing |
| `aidm/core/event_log.py` | Append-only event sourcing |
| `aidm/core/rng_manager.py` | Deterministic RNG |
| `aidm/core/state.py` | World state hashing |
| `aidm/core/replay_runner.py` | Deterministic replay |
| `aidm/lens/narrative_brief.py` | Data transformation (ID-based) |
| `aidm/lens/context_assembler.py` | Token-budgeted assembly |
| `aidm/runtime/session_orchestrator.py` | Pipeline conductor |
| `aidm/immersion/*` | Protocol-based adapters |

### Estimated Extraction Scope

- ~10 files need content extraction
- ~15 files are already clean
- The extraction is data migration, not code rewrite
- Resolver algorithms do not change
- Test assertions change only in name strings, not in math

---

## 6. The Behavioral Contract as Narration Guardrail

### The Problem Behavioral Contracts Solve

Without behavioral contracts, Spark receives:

```
ability used, fire damage, area effect, 3 targets hit
```

Spark generates narration that is mechanically correct but behaviorally wrong:
- "Fire erupts from the ground beneath them" (wrong — it's a projectile)
- "A slow-burning flame spreads across the room" (wrong — it's instantaneous)
- "The target bursts into flame" (wrong — it's an area, not single-target)

Players who know how the ability works lose trust. The narration contradicts
their tactical understanding even though the math is correct.

### How Behavioral Contracts Fix This

With behavioral contracts, Lens passes to Spark:

```
ability used: projectile delivery, launch from caster, straight-line travel,
detonation at target point, spherical burst, fire damage, instantaneous,
3 targets hit, sensory: bright + loud + thermal
```

Spark must narrate:
- Something launching from the caster (launch phase)
- Something traveling to the target point (travel phase)
- An explosion at that point (detonation phase)
- Fire damage to multiple targets in an area (aftermath phase)

The specific imagery is Spark's creative choice. But the narrative structure
matches the behavioral structure. A player hearing the narration recognizes
the ability they chose to use.

### Relationship to Existing Systems

| System | How Behavioral Contracts Interact |
|--------|-----------------------------------|
| **NarrativeBrief** (WO-032) | Brief carries mechanical outcome. Behavioral contract adds spatial/temporal structure. Both feed Spark. |
| **ContradictionChecker** (RQ-LENS-SPARK-001) | Checker validates mechanical claims. Behavioral contracts enable future validation of spatial/temporal claims. |
| **GrammarShield** | Catches numeric leaks. Behavioral contracts catch behavioral contradictions (wrong delivery model, wrong phase ordering). |
| **DMPersona** (WO-041) | Persona controls tone. Behavioral contract controls structure. Orthogonal. |

---

## 7. Multi-Skin Support

### How Skins Work

A "skin" is a terminology mapping + narrative style that Spark applies to the
abstract content pack. The content pack does not change. The mechanical
definitions do not change. The behavioral contracts do not change. Only the
names and narrative flavor change.

| Abstract ID | Fantasy Skin | Sci-Fi Skin | Horror Skin |
|------------|-------------|------------|------------|
| ABILITY_003 | Fireball | Plasma Grenade | Hellfire Eruption |
| TALENT_007 | Power Strike | Overcharge | Berserker Frenzy |
| SKILL_004 | Tumble | Zero-G Maneuver | Desperate Dodge |
| CLASS_01 | Warrior | Marine | Survivor |

The skin is a JSON file mapping IDs to display names. Spark receives the
display name and generates narration appropriate to the setting. The engine
receives the ID and resolves math.

### Campaign-Level Skin Selection

At session zero (campaign creation), the player or campaign designer selects:
- A skin (terminology mapping)
- A DM persona (tone, verbosity, drama level)
- A setting description (for Spark's scene generation)

These three inputs, combined with the content pack's behavioral contracts,
give Spark everything it needs to generate consistent, thematic narration
without any static flavor text in the content pack.

---

## 8. Layered World Authority Model (Creation Stack)

### The Problem

The three-layer content model (mechanical / behavioral / narrative) defines
**what** content is made of. It does not define **when** each layer gets frozen
or **where** stability is enforced across the product lifecycle.

Without a creation hierarchy, questions arise:
- Does the rulebook change every session? (No.)
- Does the rulebook change every campaign? (Only if you switch worlds.)
- If Spark writes the codex, when does it write it? (Once, at campaign compile.)
- Can two campaigns share monster families? (Yes — they share a world.)

The Layered World Authority Model answers all of these by defining a stratified
creation stack where stability increases as you go down the stack and variation
is constrained by the layer above.

### The Creation Stack

```
Level 0: Mechanical Substrate (Immutable)
  │  Pure math, resolvers, state machines, IDs only
  │  Never changes. This is the physics engine.
  │
Level 1: World Generation (Rare, High-Cost)
  │  Cosmology, magic/technology level, species taxonomy
  │  Material properties, core reality assumptions
  │  THE RULEBOOK — generated once, frozen, player-inspectable
  │  ABILITY_003 → "Void Flare" for this entire world
  │  Monster catalog, spell list, ability names — all world-level
  │  Governmental baseline (types of governance that exist in this world)
  │  THE MAP — all regions, countries, cities, governments, geography
  │  Defines what is POSSIBLE, how it is NAMED, and where it EXISTS
  │  All campaigns inside this world inherit these rules, names, AND geography
  │
Level 2: Campaign Generation (Deliberate, Region-Scoped)
  │  SELECTS a region of the world to play in (doesn't create new geography)
  │  May add local detail: specific NPCs, plot hooks, local flavor
  │  But the cities, countries, and governments already exist at world level
  │  Same rulebook, same monsters, same spells as the world
  │  New campaign = play in a different region of the same world
  │
Level 3: Storyline (Cheap, Multiple Per Campaign)
  │  Characters, plot arcs, NPCs, adventures
  │  Operates within a campaign's region — same cities, same factions
  │  New characters can start; old characters can retire
  │  Multiple storylines can run in the same campaign region
  │  Nothing above this layer changes
  │
Level 4: Session (Ephemeral)
     Dice rolls, narration, event logs
     Nothing permanent is authored here except logs
```

### What Gets Frozen Where

| Level | What Freezes | When | Stability |
|-------|-------------|------|-----------|
| 0 — Substrate | Math, resolvers, condition logic | At build time | Immutable across all worlds |
| 1 — World | **Rulebook**, reality rules, species, materials, magic level, ability names, monster catalog, spell list, **all regions/countries/cities/governments/geography** | At world creation | Fixed for all campaigns in this world |
| 2 — Campaign | **Selects a region** of the world to play in; may add local NPCs, plot hooks, local detail | At campaign creation | Fixed for all storylines in this campaign |
| 3 — Storyline | Character sheets, plot state, NPC relationships | At storyline start | Evolves within storyline only |
| 4 — Session | Narration text, dice outcomes, event log entries | During play | Ephemeral — logs only |

### The Rulebook Belongs to the World Layer

When a player says "I want to play a space pirate adventure," the system:

1. Selects a content pack (Level 0 — math + behavioral contracts)
2. **Generates the world** (Level 1):
   - Determines cosmology, magic/technology level, species taxonomy
   - Generates the **rulebook**: ability names, spell descriptions, monster
     catalog, all flavored to match the world theme
   - ABILITY_003 becomes "Void Flare" in this world — and stays "Void Flare"
     for every campaign, every storyline, every session in this world
   - The rulebook is frozen. It never changes after world creation.
3. **Selects a campaign region** (Level 2) — picks one of the world's
   existing regions to play in. The campaign inherits everything: rulebook,
   geography, governments, cities. May add local detail (specific NPCs,
   plot hooks) but does not create new regions or redefine existing ones.
4. Creates a storyline (Level 3) — characters, plot, adventure. The storyline
   inherits the campaign's geography and the world's rules.

**This is a deliberate creation process.** The PO's design: when you say "start
a new world," the system needs time to compile. The DM says "come back in
hours" — because the entire rulebook, codex, map, regions, governments, and
world context are being generated and frozen. Starting a new campaign within
an existing world is cheap — the world already exists, you're just selecting
which region to play in.

### Why the Rulebook Is World-Level, Not Campaign-Level

The PO's key insight: the **world flavor** determines the rulebook flavor.

- "Space pirate adventure" → space-flavored ability names, alien monster types,
  technology-themed spell descriptions
- "Undersea kingdom" → aquatic ability names, sea creature catalog,
  water-themed spell descriptions
- "Classic fantasy" → traditional fantasy naming, standard monster catalog

If the rulebook were campaign-level, switching campaigns within the same world
would change the rules — confusing players who expect the same spells and
monsters across the world. That's wrong. A new campaign is a new *region*,
not a new *ruleset*.

### Cross-Campaign Familiarity

Because campaigns are just different regions of the same world, **everything
except location is shared**:

- **Monster catalog is identical** — the world defines all species; campaigns
  determine which monsters appear in that region
- **Spell list is identical** — same abilities, same names, same behavioral
  contracts in every region of the world
- **Mechanics stay identical** — the substrate never changes
- **Geography already exists** — the world generated all regions, countries,
  cities, and governments; the campaign just scopes into one
- **Only your location changes** — switch campaigns to play in a different
  part of the same world

Switching campaigns within a world is like traveling to a different country.
Different peoples, different politics, same physics, same magic system, same
monster ecology. The world already built all of it.

### Controlled Novelty Hierarchy

| Action | Cost | What Changes | What Stays |
|--------|------|-------------|------------|
| New session | Free | Just play | Everything |
| New storyline | Low | New characters, new plot | Campaign, world, rules |
| New campaign | Low-Medium | Select a different region of the world | World, rulebook, monsters, spells, all geography |
| New world | High | New reality, new rulebook, new everything above Level 0 | Substrate only |

This prevents cognitive overload. Players never face "what does this ability do
again?" within a campaign. Experienced players recognize ability patterns across
campaigns within the same world.

### Replay Provenance

Every outcome can be traced to its layer of origin:

```
World: W-01 (High Fantasy)
  Campaign: C-07 (Astral Corsairs — northern continent)
    Storyline: S-14 (The Void Cartographer)
      Session: T-221
        Event: ABILITY_003 used by entity_047 at grid (12,8)
        Resolved by: Box (Level 0 substrate)
        Named by: World W-01 rulebook ("Void Flare")
        Narrated by: Spark (Level 4 ephemeral)
```

This is gold for debugging, trust, and deterministic replay.

### Mapping to Three-Layer Content Model

| Content Layer | Authored At | Frozen At | Referenced By |
|--------------|------------|-----------|---------------|
| Mechanical Definition (math) | Level 0 — Substrate | Build time | Box resolvers |
| Behavioral Contract (spatial/temporal) | Level 0 — Substrate | Build time | Lens constraints, world rulebook |
| World Rules + Rulebook (reality + names) | Level 1 — World | World creation | All campaigns, player handbook UI, Spark narration anchor |
| Campaign Context (geography, factions) | Level 2 — Campaign | Campaign creation | Storyline generation, Lens scene context |
| Narrative Realization (prose) | Level 4 — Session | Never (ephemeral) | Player-facing output only |

The behavioral contract (Level 0) is the **anchor**. The world rulebook
(Level 1) is the **presentation**. The narration (Level 4) is the **experience**.

---

## 9. Sequencing

### When This Work Happens

**Not now.** The content extraction pass is release preparation, not
development work. The current D&D 3.5e-named implementation is the development
scaffold — it allows verification against known rules by name.

**Recommended sequence:**

1. **Current phase:** Continue developing with D&D names as scaffolding.
   All mechanical verification happens against named spells/feats/skills
   because that's how humans think about the rules.

2. **Pre-release phase:** Execute the content extraction pass.
   - Define content pack schema (this document)
   - Extract mechanical definitions from hardcoded entries
   - Write behavioral contracts for all abilities
   - Define category tag taxonomy
   - Build skin system (terminology mapping)
   - Migrate tests to use IDs instead of names

3. **Release:** Ship engine + content pack + default skin.
   The Vault stays behind. The D&D-named scaffold stays behind.
   The product contains only math, behavioral specs, and category tags.

### What This Research Does NOT Do

- **Does not implement the content pack system.** This research defines the
  schema and extraction plan. Implementation is a separate work order.
- **Does not perform the extraction.** The extraction is a per-file migration
  task executed during pre-release.
- **Does not design the skin system UI.** How players select and customize
  skins is a UX concern deferred to Phase 4+.
- **Does not resolve any RAW questions.** Content independence is orthogonal to
  RAW silence handling (RQ-BOX-002) and object identity (RQ-BOX-003).
- **Does not provide legal advice.** The IP analysis in this document reflects
  general understanding of game mechanics copyright law. Formal legal review
  is recommended before commercial release.

---

## 10. Success Criteria

This research is complete when:

- [ ] **Three-layer content model defined** (mechanical, behavioral, narrative)
  with clear ownership (Box, Lens, Spark) and static/dynamic classification
- [ ] **Content pack schema v1 specified** with entry structure for all content
  categories (abilities, talents, skills, progressions, conditions, maneuvers,
  equipment, creatures)
- [ ] **Behavioral contract vocabulary defined** (delivery models, visual
  phases, sensory tags) sufficient for v1 scope abilities
- [ ] **Extraction surface audit complete** — every file with D&D-specific
  content identified, extraction target documented
- [ ] **Provenance firewall specified** — Vault isolation rules, recognition
  test, content authoring workflow
- [ ] **Layered World Authority Model defined** — creation stack (substrate →
  world → campaign → storyline → session) with freeze points and stability
  guarantees documented. Rulebook freezes at world level, not campaign level.
- [ ] **World compile process specified** — when the rulebook is generated,
  what freezes, what remains variable, provenance tracing per layer
- [ ] **At least one complete example** — one ability fully specified in all
  three layers (mechanical + behavioral + category tags) to validate the schema

---

## 11. Relationship to Other Work

| Relationship | Target | Notes |
|-------------|--------|-------|
| **Independent of** | RQ-LENS-SPARK-001 | Context orchestration is engine work. Content independence is data work. No blocking. |
| **Independent of** | RQ-BOX-002, RQ-BOX-003 | RAW silence handling and object identity are mechanical concerns. Content independence is a product concern. |
| **Informed by** | House Policy Governance Doctrine | The two-source authority model (rules + house policy) applies regardless of whether the rules are named "D&D" or abstracted to IDs. |
| **Constrains** | Future content authoring | All new content entries must follow the three-layer model. No static flavor text. |
| **Constrains** | Campaign compile pipeline | Campaigns inherit their world's rulebook unchanged. Codex generation happens at world creation, not campaign creation. |
| **Enables** | Multi-skin support, campaign theming, Spark narrative flexibility | The ID-based content pack is the prerequisite for setting-agnostic gameplay. |
| **Enables** | World/campaign/storyline hierarchy | The creation stack enables shared worlds with multiple campaigns, each with frozen rulebooks. |
| **Feeds into** | Commercial release preparation | This research defines what must be done before the product can ship independently. |

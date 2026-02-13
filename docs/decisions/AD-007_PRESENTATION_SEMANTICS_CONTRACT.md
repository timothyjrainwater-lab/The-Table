# AD-007: Presentation Semantics Contract

**Status:** RATIFIED
**Author:** PO (Thunder) + PM (Opus) + Third-party review
**Date:** 2026-02-12
**Source:** Whiteboard session + external PM/Design/Engineering analysis

---

## Summary

This decision formalizes the **Presentation Semantics** layer as a first-class architectural component between Box (deterministic mechanics) and Spark (ephemeral narration). This is the missing contract that ensures stable player mental models without static copyrighted prose.

---

## The Problem

Box produces pure math: range, area, targets, damage, saves, conditions, timing.
Spark produces free prose: varied descriptions of what happened.

Neither layer alone gives the player a **stable understanding of how things behave**. A fireball should always travel as a projectile and detonate on impact — that's not mechanical truth (Box doesn't care about visual staging) and it's not narration (it must be consistent, not varied). It's a third thing.

Without this layer:
- Narration can drift (fireball described as a beam one turn, an explosion the next)
- Players can't build reliable mental models of abilities
- The world-owned rulebook has no stable "how it looks/acts" entries
- Spark has no staging constraints beyond "don't contradict the math"

---

## The Three-Layer Description Model

### Layer A: Behavior (Box / Mechanics) — DETERMINISTIC

What the ability *does* mathematically.

- Range, area, targeting rules
- Save type and DC
- Damage dice, damage type
- Conditions applied, durations
- Timing in rounds/actions
- All state transitions

Owned by: Box (deterministic resolvers)
Mutability: Immutable (rules procedures)
Example: `range=20ft_burst, area=20ft_radius, damage=6d6_fire, save=reflex_half`

### Layer B: Presentation Semantics (World Model) — FROZEN AT WORLD COMPILE

What the ability *behaves like* in this world. Not prose — structured semantic tags.

Required fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `delivery_mode` | enum | How the effect reaches its target | `projectile`, `beam`, `burst_from_point`, `aura`, `cone`, `line`, `touch`, `self` |
| `staging` | enum | Temporal sequence of the effect | `travel_then_detonate`, `instant`, `linger`, `pulses`, `channeled` |
| `origin_rule` | enum | Where the effect originates | `from_caster`, `from_chosen_point`, `from_object`, `from_target` |
| `vfx_tags` | list[str] | Visual descriptors | `["fire", "expanding_ring", "scorch", "bright"]` |
| `sfx_tags` | list[str] | Audio descriptors | `["boom", "crackle", "whoosh"]` |
| `scale` | enum | Perceived size/impact | `subtle`, `moderate`, `dramatic`, `catastrophic` |
| `residue` | list[str] | What remains after the effect | `["scorch_marks", "smoke", "heated_air"]` |
| `ui_description` | str | Canonical short description for the world's rulebook entry | Generated at world compile, stable |

Owned by: World Model (authored at world compile, then frozen)
Mutability: Frozen within a world. Different worlds may assign different presentation semantics to the same mechanical ability.
Example: Ability FIRE_BURST_003 in World "Ashenmoor" might have `delivery_mode=projectile, staging=travel_then_detonate, vfx_tags=["fire", "expanding_ring"]` while the same mechanical template in World "Crystaldeep" might have `delivery_mode=projectile, staging=travel_then_detonate, vfx_tags=["crystal_shards", "prismatic_flash"]`.

### Layer C: Narration (Spark) — EPHEMERAL

Free prose that describes the moment. May vary every time.

Constraints:
- MUST NOT contradict Layer A (mechanical outcome)
- MUST NOT contradict Layer B (presentation semantics)
- MAY vary phrasing, metaphor, tone, detail level
- MAY reference residue, staging, and vfx/sfx tags creatively

Owned by: Spark (generative narrator)
Mutability: Varies per narration instance

---

## How It Works in the Pipeline

```
Box resolves ability
    → produces: mechanical outcome (damage, saves, conditions)

Lens assembles NarrativeBrief
    → includes: outcome summary + presentation semantics tags from world model

Spark receives brief
    → generates narration that respects both mechanical outcome AND staging semantics

ContradictionChecker validates
    → checks narration against mechanical truth AND semantic constraints
```

### What Lens Passes to Spark

The NarrativeBrief already contains outcome data. With this contract, it also includes:

```
presentation_semantics:
  delivery_mode: "projectile"
  staging: "travel_then_detonate"
  vfx_tags: ["fire", "expanding_ring", "scorch"]
  sfx_tags: ["boom", "crackle"]
  scale: "dramatic"
  residue: ["scorch_marks", "smoke"]
```

Spark uses these tags to generate narration that is consistent with the world's established visual language.

---

## How It Enables the World-Owned Rulebook

Each ability's rulebook entry is generated from Layer A + Layer B:

```
ABILITY: Searing Burst (Ashenmoor name for FIRE_BURST_003)
TYPE: Projectile burst
RANGE: 20 feet
AREA: 20-foot radius
EFFECT: Launches a streaking projectile of fire that detonates
        on impact, engulfing the target area in expanding flames.
DAMAGE: Significant fire damage (Reflex save for half)
RESIDUE: Leaves scorch marks and lingering smoke.
```

This entry is:
- Generated at world compile (not hand-written)
- Stable within the world (frozen)
- Free of copyrighted language
- Mechanically accurate (derived from Layer A)
- Visually consistent (derived from Layer B)

---

## How It Enables the Battle Map

Presentation semantics drive visual effects on the battle map:

- `delivery_mode=projectile` → animated projectile travels from caster to target point
- `staging=travel_then_detonate` → projectile animation followed by burst animation
- `vfx_tags=["fire", "expanding_ring"]` → fire-colored expanding circle overlay
- `residue=["scorch_marks"]` → after effect resolves, affected tiles get scorch overlay

All of this is cosmetic. The mechanical effect (which squares are hit, what damage is dealt) is computed by Box. The presentation semantics tell the visual layer *how to display* what Box computed.

---

## How It Enables the Discovery Log

When a player encounters an ability for the first time:

- **Seen it:** Bestiary entry records: "Uses a fire projectile ability"
- **Studied it:** Entry updates with mechanical details + full presentation semantics
- **Rulebook entry generated:** Player can look up the ability in their world rulebook

Knowledge level determines how much of the presentation semantics are revealed to the player.

---

## Validation Rules

1. Every ability in the world model MUST have both Layer A (behavior) and Layer B (presentation semantics) defined
2. Layer B is generated at world compile and frozen — it cannot be modified during play
3. Spark narration is validated against Layer B staging constraints (new ContradictionChecker rule class)
4. If Layer B is missing for an ability, the system fails closed (no narration generated, template fallback used, gap logged)
5. Different worlds MAY assign different Layer B values to the same Layer A mechanical template
6. Layer B fields are structured data (enums, tag lists), not free prose

---

## Relationship to Existing Architecture

| Component | Role with Presentation Semantics |
|-----------|----------------------------------|
| Box (core resolvers) | Produces Layer A output. Unaware of Layer B. |
| World Model (new) | Owns and stores Layer B. Generated at world compile. Frozen. |
| Lens (NarrativeBrief) | Includes Layer B tags in brief passed to Spark. |
| Spark (narrator) | Consumes Layer B tags. Constrained by them. |
| ContradictionChecker | Validates Spark output against Layer A + Layer B. |
| Rulebook Generator (new) | Generates stable rulebook entries from Layer A + Layer B. |
| Battle Map Renderer (new) | Drives visual effects from Layer B tags. |
| Discovery Log | Progressive revelation of Layer B information to players. |

---

## Implications for Content Independence

This contract is what makes content independence real. The same Layer A template (projectile burst, 6d6 damage, Reflex half) can exist in any world with any skin:

- Fantasy world: "Searing Burst" — fire projectile, boom, scorch marks
- Sci-fi world: "Plasma Grenade" — energy projectile, electric crackle, burn marks
- Horror world: "Bile Eruption" — organic projectile, wet splatter, acid residue

The mechanics are identical. The presentation semantics are world-authored. The narration is moment-specific. No copyrighted material is required at any layer.

---

## Work Required

### WO-A: Presentation Semantics Schema
- Define frozen dataclass schema with all required fields
- Define enum types for delivery_mode, staging, origin_rule, scale
- Define validation rules
- Define how it's stored in the world model
- Define what Lens passes to Spark
- Write tests: schema validation, freeze enforcement, Lens integration

### WO-B: Rulebook Object Model
- Rulebook storage format and indexing
- "Open to page" / "show me ability X" query API
- Entry generation from Layer A + Layer B
- Integration with notebook (player can look up rules)

### WO-C: ContradictionChecker Extension
- New rule class: staging constraint violation
- Tests: Spark output may vary phrasing but must preserve staging invariants
- Example: if delivery_mode=projectile, narration cannot describe it as "erupting from the ground beneath them"

---

*This decision supersedes any prior assumption that narration is the only creative layer. There are three layers of description: Behavior (deterministic), Presentation Semantics (world-frozen), and Narration (ephemeral). The middle layer is the keystone.*

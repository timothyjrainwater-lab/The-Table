# RQ-BOX-003: Object Identity Model — When One Object Becomes Many

**Domain:** Box Layer — Object State Tracking
**Status:** DRAFT
**Filed:** 2026-02-12
**Gate:** Prerequisite for correct spell targeting, sunder resolution, and House Policy trigger families
**Prerequisite:** House Policy Governance Doctrine (PO session 2026-02-12, AD-006)

---

## 1. Thesis

Box tracks creatures as first-class entities with full state: entity_id, HP,
conditions, position, equipment. There is no equivalent for objects. A longsword
in a creature's inventory is a string label, not a stateful thing. A door on the
battlefield grid is a hardcoded obstacle, not an object with HP and integrity.

This absence was invisible until the PO design session on 2026-02-12 surfaced a
concrete edge case:

> **Can the _mending_ cantrip join two fully severed rope halves?**
>
> PO ruling: **NO.** Mending repairs damage to ONE object. Two severed halves
> are TWO objects. Mending cannot merge objects.

This ruling is correct under RAW. But Box cannot enforce it, because Box has no
concept of object identity. Without it:

- **Mending** cannot distinguish "one damaged rope" from "two rope pieces."
  The spell description says "repairs small breaks or tears in objects" —
  singular. If the rope is in two pieces, those are two objects, and mending
  targets one object at a time. It does not fuse separate objects.

- **Sunder** cannot determine when an item transitions from "damaged" to
  "destroyed" to "fragments." A sundered shield with 1 HP remaining is still
  one shield (damaged). A shield reduced to 0 HP is destroyed — but is it
  one broken shield or several pieces of wood and metal? RAW is silent on
  the physical outcome, but the mechanical distinction matters for follow-up
  actions.

- **Container rules** cannot track nested items. CONTAINMENT_PLAUSIBILITY
  (AD-006 family #1) needs to know what objects are inside a container, and
  those objects need identities to be individually retrievable, damageable,
  and targetable.

- **Structural load-bearing** cannot track object integrity over time. A
  bridge at full HP and a bridge at half HP should have different load
  capacities, but this requires the bridge to be a persistent, stateful
  object — not a narrative prop.

This is a **data model gap**, not a rules gap. RAW implies object identity
through its spell descriptions, sunder rules, and item tracking conventions
but never formalizes it. The system needs an explicit ObjectState schema that
makes identity, integrity, and parentage machine-queryable.

---

## 2. What RAW Implies

RAW never defines an "object identity model" in those terms. But object
identity is implicit throughout the core rulebooks. The following rules only
make sense if objects have persistent, distinguishable identity:

### Objects Have HP and Hardness (DMG p.166, PHB p.165-166)

Every object has hit points determined by its material and thickness, and
hardness that reduces incoming damage. This implies that an object persists
across damage events — it is the same object at 10 HP as it was at 15 HP.

| Material       | Hardness | HP per inch of thickness |
|----------------|----------|--------------------------|
| Paper/Cloth    | 0        | 2                        |
| Rope           | 0        | 2                        |
| Glass          | 1        | 1                        |
| Ice            | 0        | 3                        |
| Wood           | 5        | 10                       |
| Stone           | 8        | 15                       |
| Iron/Steel     | 10       | 30                       |
| Mithral        | 15       | 30                       |
| Adamantine     | 20       | 40                       |

### Objects Can Be Damaged or Destroyed (DMG p.166)

Objects reduced to 0 HP are "destroyed." RAW uses the word "destroyed" but
does not specify the physical outcome. Does a destroyed wooden door vanish?
Collapse into rubble? Splinter into fragments? The mechanical answer is that
it no longer functions as a door. The physical answer is unstated.

### Sunder Attacks Target Specific Objects (PHB p.158)

The sunder combat maneuver targets a specific object held or worn by an
opponent: a weapon, a shield, a piece of armor. This requires that the object
be individually identifiable and distinguishable from other objects the target
carries. You sunder _this_ longsword, not "a longsword somewhere on the
creature."

### Mending Repairs One Object (PHB p.253)

> "Mending repairs small breaks or tears in objects."

The spell targets one object. It repairs damage to that object. It does not
assemble multiple objects into one. A rope with a cut halfway through (one
object, damaged) is a valid target. Two rope halves (two objects, each intact
as a "piece of rope") are not a single valid target — you could mend damage
to one half, but that half is already intact. The repair the caster wants
(joining the halves) requires treating them as one object, which they are not.

### Make Whole Operates on One Object (PHB p.252)

> "This spell functions like mending, except that make whole completely
> repairs an object made of any substance."

Same identity constraint. One object. More thorough repair, but still one
target.

### Fabricate Creates New Objects (PHB p.229)

Fabricate transforms raw materials into a finished product. The output is a
new object — it did not exist before the spell was cast. This implies object
creation: a new identity comes into existence.

### Items in Inventory Are Tracked Individually

Every character sheet tracks items individually. "Longsword," "50 ft. hemp
rope," "backpack." Each is a distinct thing with a name and properties. RAW
does not assign IDs, but the implicit model is that each item is separately
identifiable.

### RAW Never Defines Destruction Outcomes

This is the critical silence. When an object reaches 0 HP:
- Does it cease to exist entirely?
- Does it become one non-functional wreck?
- Does it split into multiple fragments?
- Do the fragments have HP of their own?

RAW says "destroyed." It does not say what "destroyed" looks like physically.
This silence must be resolved by the object identity model, because downstream
systems (mending, make whole, fabricate, sunder, container tracking) need to
know what exists after destruction.

---

## 3. The Minimal Model

The following schema proposes the minimum viable object identity model. It
uses frozen dataclasses consistent with the project's existing schema patterns
(see `aidm/schemas/box_events.py`, `aidm/schemas/entity_state.py`).

### ObjectIntegrity States

```python
from typing import Literal

ObjectIntegrity = Literal[
    "intact",       # Full HP, fully functional
    "damaged",      # HP reduced but > 0, functional (possibly degraded)
    "broken",       # HP = 0, non-functional but physically one piece
    "destroyed",    # HP below negative threshold, object splits into fragments
    "fragments",    # This entry IS a fragment of a formerly whole object
]
```

### ObjectState Schema

```python
from dataclasses import dataclass, field
from typing import Dict, Optional, Literal

@dataclass(frozen=True)
class ObjectState:
    """Minimal object identity record for Box-layer object tracking.

    Every physical object in the game world that Box needs to reason about
    gets an ObjectState. Creatures are NOT ObjectStates — they have
    EntityState. Objects held by creatures reference the creature via
    holder_entity_id.

    Frozen: state transitions produce new ObjectState instances, never
    mutation. The old instance is the audit trail.
    """

    object_id: str
    """Unique, immutable identifier. Format: 'obj_<uuid_short>'."""

    object_type: str
    """Canonical type label: 'rope', 'longsword', 'door', 'chest', etc."""

    material: str
    """Primary material: 'hemp', 'iron', 'wood', 'stone', 'steel', etc.
    Determines hardness and HP-per-inch via DMG p.166 table."""

    integrity: str  # Must match ObjectIntegrity values
    """Current integrity state. See state transition graph."""

    hp_current: int
    """Current hit points. Non-negative for intact/damaged. Zero for broken.
    Negative values only valid transiently during destruction threshold check."""

    hp_max: int
    """Maximum hit points. Derived from material + thickness (DMG p.166)."""

    hardness: int
    """Material hardness. Damage below hardness is ignored (DMG p.166)."""

    parent_object_id: Optional[str] = None
    """If this object is inside a container, the container's object_id.
    Used by CONTAINMENT_PLAUSIBILITY and STACKING_NESTING_LIMITS families.
    None if the object is not inside another object."""

    holder_entity_id: Optional[str] = None
    """If a creature holds/wears/carries this object, the creature's
    entity_id. None for environmental objects (doors, walls, bridges)."""

    fragment_of: Optional[str] = None
    """If this object is a fragment, the object_id of the original whole
    object before destruction. None for non-fragment objects."""

    fragment_index: Optional[int] = None
    """Ordering index among sibling fragments (0-indexed). Deterministic
    fragment generation requires stable ordering."""

    size_category: Optional[str] = None
    """Size category: 'Fine', 'Diminutive', 'Tiny', 'Small', 'Medium',
    'Large', 'Huge', 'Gargantuan', 'Colossal'. From DMG p.166 object size."""

    thickness_inches: Optional[float] = None
    """Thickness in inches. Combined with material, determines HP
    (DMG p.166: HP = hp_per_inch * thickness)."""

    display_name: Optional[str] = None
    """Human-readable name for Lens/Spark narration. If None, derived from
    object_type + material (e.g., 'hemp rope', 'iron door'). The object_id
    is never exposed to Spark."""
```

### State Transition Graph

```
                    HP reduced
    intact ──────────────────────► damaged
      ▲                              │
      │  mending / make_whole        │  HP reaches 0
      │  (restores HP,               ▼
      │   resets integrity)        broken
      │                              │
      │  make_whole only             │  HP below destruction
      │  (from broken)               │  threshold (see Open
      └──────────────────────────────┘  Questions §5.1)
                                     │
                                     ▼
                                 destroyed
                                     │
                                     │  System generates N new
                                     │  ObjectState entries with
                                     │  fragment_of = original.object_id
                                     ▼
                              ┌─────────────┐
                              │  fragment 0  │
                              │  fragment 1  │
                              │  fragment …  │
                              └─────────────┘
```

**Transition rules:**

| From       | To         | Trigger                                      |
|------------|------------|----------------------------------------------|
| intact     | damaged    | HP reduced below hp_max but remains > 0      |
| damaged    | intact     | Repaired to full HP (mending, make_whole)     |
| damaged    | broken     | HP reaches 0                                 |
| broken     | intact     | make_whole restores to full HP                |
| broken     | destroyed  | Further damage below destruction threshold    |
| destroyed  | fragments  | System spawns fragment ObjectState entries    |

**Irreversible transitions:**

- `destroyed` and `fragments` are terminal for the original object_id. The
  original object ceases to exist as a targetable entity.
- Fragments are new objects with their own object_ids. They can be individually
  intact, damaged, broken, or destroyed.
- `fabricate` can consume fragments as raw material inputs and produce a new
  ObjectState with a new object_id. This is creation, not repair.

### Spell Interaction Rules

| Spell       | Valid integrity targets       | Effect                                     |
|-------------|------------------------------|--------------------------------------------|
| mending     | damaged, broken              | Restores HP (up to 1 per casting for 0-level). Target must be ONE object. |
| make_whole  | damaged, broken              | Restores to intact (full HP). Target must be ONE object. |
| mending     | fragments                    | **INVALID** — each fragment is a separate object. Mending one fragment repairs that fragment, not the original whole. |
| make_whole  | fragments                    | **INVALID** — same constraint. Cannot reassemble. |
| fabricate   | any (consumes as material)   | Creates new object_id from raw materials. Fragments may serve as material input. |

---

## 4. Consumers

The following systems require ObjectState to function correctly:

### 4.1 SpellResolver

- **Mending / Make Whole target validation:** Before resolving the spell, the
  resolver must look up the target's ObjectState and confirm `integrity` is in
  the valid set. If the target is a fragment, the spell resolves against that
  fragment (not the original whole object).

- **Fabricate material input:** The spell consumes objects (raw materials or
  fragments) and produces a new object. The resolver must deduct consumed
  ObjectStates and create a new ObjectState with a fresh object_id.

- **General spell targeting:** Any spell that targets "an object" (as opposed
  to "a creature") needs to validate that the target is a single ObjectState
  with an identity, not a narrative description.

### 4.2 Sunder Resolution

The sunder combat maneuver (`aidm/core/maneuver_resolver.py`) targets a
specific held or worn object. The resolver must:

1. Identify the target ObjectState by object_id
2. Apply damage (reduced by hardness)
3. Transition integrity if HP thresholds are crossed
4. If destroyed, generate fragment ObjectStates
5. If the object was a weapon/shield/armor, update the holder's equipment state

Currently, sunder resolution tracks ad-hoc HP on objects. ObjectState
formalizes this into a proper state machine with auditable transitions.

### 4.3 House Policy Trigger Families (AD-006)

| Family ID                  | ObjectState dependency                                     |
|----------------------------|------------------------------------------------------------|
| CONTAINMENT_PLAUSIBILITY   | `parent_object_id` — what is inside this container? Can this object fit? |
| FRAGILITY_BREAKAGE         | `integrity`, `material`, `hardness` — does rough handling damage this object? |
| STRUCTURAL_LOAD_BEARING    | `integrity`, `hp_current`, `hp_max`, `material`, `thickness_inches` — what load can this object bear given its current state? |
| STACKING_NESTING_LIMITS    | `parent_object_id` chain depth — containers inside containers inside containers |
| RETRIEVAL_ACCESSIBILITY    | `parent_object_id`, `holder_entity_id` — action cost to access a stored item |
| READINESS_STATE            | `holder_entity_id` — is this item "at hand" vs "stowed"    |

### 4.4 Inventory System

Objects inside other objects form a tree via `parent_object_id`. Objects on
creatures link via `holder_entity_id`. The inventory system needs ObjectState
to:

- Track gear slot assignments (creature holds/wears specific object_ids)
- Enforce container capacity (CONTAINMENT_PLAUSIBILITY consumes ObjectState)
- Handle item transfer (change holder_entity_id, preserve object_id)
- Handle item drop/pickup (set/clear holder_entity_id)

### 4.5 NarrativeBrief (Lens → Spark)

When Lens builds a NarrativeBrief for Spark, it must refer to objects by
`display_name`, never by `object_id`. The object_id is a Box-internal
identifier. Spark sees "the hemp rope" or "the broken iron door" — names
derived from ObjectState fields but stripped of mechanical internals.

This follows the existing Lens containment pattern: Spark describes outcomes
but never sees entity_ids, HP values, or object_ids.

---

## 5. Open Questions

These questions must be resolved before ObjectState can be implemented. Each
is a design decision that requires PO input or RAW analysis.

### 5.1 Destruction Threshold

At what HP threshold does "broken" become "destroyed"?

RAW says HP 0 = "destroyed" for objects. But does "destroyed" mean
non-functional (one broken piece) or physically disintegrated (multiple
fragments)? The proposed model separates these into `broken` (HP = 0,
one piece, non-functional) and `destroyed` (further damage, fragments).

Options:
- **A)** HP = 0 → broken. Any further damage → destroyed/fragments.
- **B)** HP = 0 → destroyed/fragments immediately. No "broken" state.
- **C)** HP = 0 → broken. HP below -(hp_max / 2) → destroyed/fragments
  (mirroring the creature death threshold logic, though RAW does not
  specify this for objects).

PO decision required.

### 5.2 Fragment Inheritance

Do fragments inherit material and hardness from the parent object?

Almost certainly yes — a fragment of an iron door is still iron. But do
fragments inherit thickness? A fragment is likely thinner/smaller than the
whole. Fragment HP would need to be computed from fragment dimensions, not
inherited from the parent's hp_max.

### 5.3 Dimension Granularity

How granular do dimensions need to be? Options:

- **Size category only** (Fine through Colossal). Coarse but simple.
  Sufficient for spell targeting (mending has a size limit).
- **Size category + thickness.** Sufficient for HP derivation and
  STRUCTURAL_LOAD_BEARING calculations.
- **Full dimensions** (length, width, height, thickness). Needed for
  CONTAINMENT_PLAUSIBILITY and SPATIAL_CLEARANCE, but significantly
  increases schema complexity.

Recommendation: start with size category + thickness. Add full dimensions
only when a consumer (trigger family or spell) requires them.

### 5.4 Broken vs. Destroyed Collapse

Should "broken" be a distinct state from "destroyed," or should they collapse
into a single post-zero-HP state?

Arguments for distinct states:
- Mending / make_whole can target broken objects (one piece) but not
  fragments (multiple pieces). The distinction is mechanically meaningful.
- A broken sword is still one object (you can mend it). A shattered sword is
  fragments (you cannot mend the original).

Arguments for collapsing:
- RAW says HP 0 = destroyed, full stop. Adding "broken" as an intermediate
  state is a House Policy addition, not RAW.

Recommendation: keep them distinct. The mending edge case that motivated this
research requires the distinction. Document it as House Policy, not RAW.

### 5.5 Magic Item Destruction

Magic items have special destruction rules (many require specific conditions
to be destroyed, are immune to certain damage types, or cannot be destroyed
by mundane means at all). The ObjectState model must accommodate magic items
but this research does not design the magic item destruction subsystem.

Open: does ObjectState need an `is_magical` flag, or is that tracked
elsewhere and queried at resolution time?

### 5.6 Fragment Count

When an object is destroyed, how many fragments are generated? Options:

- **Fixed:** Always 2 fragments (simplest).
- **Material-dependent:** Brittle materials (glass, ceramic) produce more
  fragments; ductile materials (iron, rope) produce fewer.
- **Damage-dependent:** The amount of overkill damage determines fragment
  count.

This affects determinism — fragment generation must be reproducible given the
same inputs. Whatever rule is chosen, it must be a pure function of
ObjectState + damage event, with no randomness.

---

## 6. What This Research Does NOT Do

To bound scope and prevent feature creep:

- **Does not implement the model in code.** This research defines the schema
  and state machine. Implementation is a separate work order.

- **Does not design the full inventory system.** ObjectState is a prerequisite
  for inventory, but inventory includes gear slots, encumbrance integration,
  container capacity calculations, and equipment swap action economy — all
  out of scope here.

- **Does not resolve all RAW ambiguities about object destruction.** Open
  Questions (section 5) catalogs the ambiguities. Resolution requires PO
  rulings and may spawn additional House Policy entries.

- **Does not cover magic item special destruction rules.** Artifacts,
  intelligent items, and items with specific destruction conditions are
  deferred.

- **Does not design the FAIL_CLOSED behavior for missing object data.** If
  a spell targets an object that has no ObjectState (legacy data, migration
  gap), the system should FAIL_CLOSED per AD-006. The specific FAIL_CLOSED
  record format for object identity gaps is not designed here.

- **Does not define the object registry or storage layer.** Where ObjectStates
  are stored (in-memory dict, session log, campaign persistence) is an
  implementation concern.

---

## 7. Success Criteria

This research is complete when:

- [ ] **Minimal ObjectState schema defined** with clear field semantics,
  types, and invariants. Every field has a documented purpose and consumer.

- [ ] **State transition graph documented** (intact -> damaged -> broken ->
  destroyed -> fragments) with explicit transition triggers, spell
  interaction rules, and irreversibility constraints.

- [ ] **All known consumer use cases validated against the model.** Each
  consumer (SpellResolver, sunder, trigger families, inventory,
  NarrativeBrief) has been checked against the schema to confirm it
  provides the data they need.

- [ ] **Open questions cataloged for future resolution.** Each open question
  has options enumerated, tradeoffs described, and a recommendation where
  possible.

- [ ] **PO ruling on mending/object-identity captured as test case.** The
  motivating edge case — mending cannot join two severed rope halves — is
  documented as a concrete validation scenario with expected inputs and
  outputs:

  ```
  GIVEN: two ObjectState entries, each with fragment_of = "obj_rope_001"
  WHEN:  player casts mending targeting "the rope"
  THEN:  spell targeting fails — no single ObjectState matches "the rope"
         as a whole object. Each fragment is a valid individual target,
         but mending on an intact fragment is a no-op (nothing to repair).
  ```

---

## 8. Relationship to Other Work

### Feeds Into

- **SpellResolver** — target validation for mending, make_whole, fabricate,
  and any future spell that targets "an object" or "an item."

- **Sunder resolution** (`aidm/core/maneuver_resolver.py`) — formalized
  integrity state transitions replace ad-hoc HP tracking on sundered items.

- **House Policy trigger families** (AD-006 registry):
  - FRAGILITY_BREAKAGE (#7) — requires `integrity`, `material`, `hardness`
  - STRUCTURAL_LOAD_BEARING (candidate #10) — requires `integrity`,
    `hp_current`, `hp_max`, `material`, `thickness_inches`
  - CONTAINMENT_PLAUSIBILITY (#1) — requires `parent_object_id`
  - STACKING_NESTING_LIMITS (#6) — requires `parent_object_id` chain depth

### Related

- **RQ-BOX-001** (Grid-Based Geometric Engine) — object representation on
  the grid. RQ-BOX-001 sub-question (5) addresses destructibility as state
  transitions, which is the grid-level counterpart to ObjectState.

- **RQ-BOX-002** (RAW Silence Catalog, if filed) — the object identity gap
  was discovered through RAW silence analysis. Object destruction outcomes
  are a prime example of RAW silence.

- **RQ-LENS-SPARK-001** (Context Orchestration Sprint) — independent track.
  ObjectState's `display_name` feeds into NarrativeBrief construction, but
  the two research tracks do not block each other.

- **AD-006** (House Policy Governance Doctrine) — the governance framework
  that motivated this research. The mending edge case (section B of AD-006)
  is the direct trigger.

### Does NOT Require

- Any Tier 2+ capability gates
- Spark/LLM involvement (this is pure Box-layer data modeling)
- Campaign persistence layer (ObjectState can be session-scoped initially)
- Grid/geometry engine (ObjectState is identity, not position)

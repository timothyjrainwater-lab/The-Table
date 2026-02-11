# Battle Map & Environmental Physics Specification
## Box-Layer Battlefield Authority, Cover Geometry, and Object Simulation

**Document Type:** Design Specification
**Document ID:** BM-ENV-001
**Version:** 1.0.0
**Status:** BINDING
**Date:** 2026-02-11
**Authority:** Thunder (Product Owner) + Opus (Acting PM)
**Source:** Whiteboard Session 002 (WHITEBOARD_SESSION_002_DECISIONS.md)
**Layer:** BOX (The battle map is Box territory — all mechanics enforced deterministically)

---

## 1. Foundational Principle

**"The battle map is fundamentally without equivocal doubt a part of the box layer."**
— Thunder (Product Owner)

The battle map is the physical manifestation of the Box's mechanical authority. Every distance, every cover calculation, every line of sight determination, every AoE placement is Box-computed. The Spark narrates what happens on the map. The Box owns what IS on the map.

**Trust dependency:** One failed distance calculation. One spell radius off by a square. One AoO that should have triggered but didn't. The player thinks: "If it got that wrong, what else is wrong?" The entire trust layer collapses.

**Therefore:** The battle map must be audited, triple-checked, and tested to a higher standard than any other system component. M3.5 RAW Compliance Gate applies specifically to battle map mechanics.

---

## 2. Map Presentation

### 2.1 The Scroll Metaphor

- The battle map is a scroll the DM unrolls
- "Roll initiative" is the trigger — the scroll unfurls, the battlefield appears
- Matt Mercer moment: dramatic reveal, then tactical play

### 2.2 Visual Style: Minimal

- **Circles** for creatures (sized by size category)
- **Grid squares** (5-foot increments, standard D&D grid)
- **Simple shapes** for environmental objects (rectangles for tables, circles for pillars, triangles for trees)
- **Labels** on objects (type, condition)
- **Elevation markers** (topographic notation — see Section 5)
- **Fog of war overlay** (unexplored/unseen areas obscured)

**NOT a 3D render. NOT a detailed illustration.** Just enough to be functional and accurate. Low graphical overhead by design.

### 2.3 Dynamic Updates

The map is not static. During combat:
- Objects can be added (Spark describes a new element → Lens indexes → map updates)
- Objects can be destroyed (Box resolves destruction → map removes/replaces object)
- Objects can be moved (player flips a table → new position and facing)
- Terrain can change (tree falls → difficult terrain in those squares)
- The Spark can modify the map when the battlefield changes

When the Spark needs time to generate a visual for an unexpected change:
- DM says: "Hold on, wasn't expecting that. Give me a moment."
- Natural pacing — no loading spinners on the battle map
- DM can narrate while the visual updates process

---

## 3. Object Property System

### 3.1 Required Properties Per Object

Every object on the battle map MUST have the following properties tracked by the Box:

| Property | Type | Description | Source |
|----------|------|-------------|--------|
| `object_id` | string | Unique identifier | Box (assigned) |
| `object_type` | enum | CREATURE, FURNITURE, STRUCTURE, TERRAIN, VEGETATION, ITEM | Box (classified) |
| `position` | (x, y) | Grid coordinates (5-ft squares) | Box (tracked) |
| `elevation` | float | Feet above ground level | Lens (from Spark world-knowledge) |
| `size_category` | enum | Fine, Diminutive, Tiny, Small, Medium, Large, Huge, Gargantuan, Colossal | Box (per 3.5e rules) |
| `height` | float | Exact height in feet | Lens (from Spark world-knowledge) |
| `width` | float | Width in feet | Lens (from Spark world-knowledge) |
| `depth` | float | Depth in feet | Lens (from Spark world-knowledge) |
| `material` | enum | WOOD, STONE, IRON, STEEL, EARTH, ICE, CLOTH, BONE, etc. | Lens (from Spark world-knowledge) |
| `hardness` | int | Per 3.5e material table (PHB/DMG) | Box (looked up from material) |
| `hit_points` | int | Based on material and thickness (DMG 165-167) | Box (calculated) |
| `current_hp` | int | Current HP (may be damaged) | Box (tracked) |
| `condition` | enum | INTACT, DAMAGED, DESTROYED, PRONE, UPRIGHT | Box (tracked) |
| `facing` | degrees | Direction the object faces (for directional cover) | Box (tracked) |
| `opacity` | bool | Does it block line of sight? | Box (derived from material/condition) |
| `solidity` | bool | Does it block line of effect? | Box (derived from material/condition) |
| `mobility` | enum | FIXED, MOVEABLE, DESTROYED_TERRAIN | Box (classified) |

### 3.2 Data Population Flow

1. **During prep:** Spark generates scene → writes world-knowledge to Lens → Lens indexes physical properties → Box reads from Lens when combat starts
2. **During play (new objects):** Spark introduces new elements → Lens captures properties → Box registers the object
3. **On demand (missing data):** Box queries Lens for object properties → if Lens doesn't have them → Lens queries Spark → Spark provides common-sense knowledge → Lens indexes → Box receives data

**Example:** Player flips a table during combat.
- Box knows: table exists at position (4,7), currently UPRIGHT
- Box updates: table now PRONE at (4,7), facing changed
- If Box needs dimensions for cover calc and doesn't have them → queries Lens
- Lens checks index → has it (from scene generation) → returns: height 3.5ft, width 4ft, material OAK
- Box calculates: oak table, prone, 3.5ft height provides X cover from direction Y

### 3.3 Material Property Table (3.5e RAW)

Per DMG Chapter 9 (pp. 165-167):

| Material | Hardness | HP per inch of thickness |
|----------|----------|--------------------------|
| Paper/Cloth | 0 | 2 |
| Rope | 0 | 2 |
| Glass | 1 | 1 |
| Ice | 0 | 3 |
| Leather/Hide | 2 | 5 |
| Wood | 5 | 10 |
| Stone | 8 | 15 |
| Iron/Steel | 10 | 30 |
| Mithral | 15 | 30 |
| Adamantine | 20 | 40 |

**Box MUST use these exact values.** Any deviation must be documented in the RAW Deviation Register.

---

## 4. Cover System

### 4.1 Cover Types (3.5e RAW — PHB 150-152)

| Cover Type | AC Bonus | Reflex Save Bonus | Determination |
|------------|----------|-------------------|---------------|
| No Cover | +0 | +0 | Clear line from attacker to defender |
| Cover (+4) | +4 | +2 | Obstacle between attacker and defender blocks some lines |
| Improved Cover (+8) | +8 | +4 | Very little exposure (arrow slit, peering around corner) |
| Total Cover | N/A (can't be targeted) | N/A | No line from attacker to any part of defender |

### 4.2 Geometric Cover Calculation

**The Box MUST calculate cover geometrically, not abstractly.**

Inputs to cover calculation:
- **Attacker position** (grid coordinates + elevation)
- **Defender position** (grid coordinates + elevation)
- **Defender height** (exact — 3ft for halfling, 5-6ft for human, 8ft for half-orc in some cases)
- **Defender stance** (standing, crouching, prone — affects effective height)
- **Intervening objects** (position, height, width, facing, condition)
- **Relative angles** (is the defender behind the object from the attacker's perspective?)

**The system measures every single vector that is truly present.** This is what makes it more accurate than a physical table.

### 4.3 Size-Relative Cover

**Critical rule:** A halfling (3ft tall) behind a standard chair (seat height ~1.5ft, back height ~3.5ft) has cover. A human (6ft tall) behind the same chair has no meaningful cover.

The Box must:
1. Know the character's exact height (from race + modifiers)
2. Know the object's exact height (from Lens environmental data)
3. Compare heights relative to the attacker's line of fire
4. Determine what percentage of the defender's body is obscured

**Prone calculations:** A prone character's effective height is approximately half their standing height. A prone halfling (~1.5ft) can fit under furniture that a standing halfling cannot hide behind.

### 4.4 Directional Cover

Cover is directional. An overturned table provides cover FROM one direction, not all directions.

- The table has a facing (the direction it was flipped toward)
- Cover applies to attacks from the direction the table faces
- Attacks from the side or behind the table ignore it
- The Box tracks facing for all cover-providing objects

---

## 5. Elevation System

### 5.1 The Problem

The battle map is 2D. The world has elevation. Elevation affects:
- Cover (high ground, low ground)
- Line of sight (can you see over that wall?)
- Movement (climbing costs, jumping)
- Size-relative positioning ("I hide under the table")
- Spell geometry (vertical component of AoE)

### 5.2 Elevation Notation

The map displays elevation using topographic-style markers:
- Contour-style lines or shading showing elevation changes
- Numeric elevation labels on terrain features ("+10ft", "+20ft")
- Object height labels where relevant (tree: 30ft tall)
- Below-ground notation (pits, basements, tunnels)

### 5.3 Vertical Space Tracking

The Box tracks vertical position for all objects and creatures:
- Ground level = 0ft (default)
- Elevated positions (on a ledge, climbing a wall, flying)
- Below-ground positions (in a pit, prone in a depression)
- "Under" positions (halfling under a table — position is at table's grid square, elevation is 0, and the object above provides total cover from ranged attacks)

### 5.4 Elevation and Combat

Per 3.5e RAW:
- **Higher ground:** +1 bonus on melee attack rolls (PHB 151)
- **Charging downhill:** +1 per 10ft of elevation advantage (for lance charges, etc.)
- **Cover from elevation:** A character below a ledge may have cover from characters above
- **Line of sight:** Elevation affects whether you can see over obstacles
- **Spell geometry:** Fireball is a sphere — if cast at ground level, it expands upward too. Characters on elevated positions may or may not be within the radius.

---

## 6. Line of Sight & Line of Effect

### 6.1 Line of Sight (LoS)

Per 3.5e RAW (PHB 150):
- Draw a line from any corner of the attacker's square to any corner of the defender's square
- If any such line is not blocked by a solid, opaque obstacle → attacker has line of sight
- The Box must check LoS for every attack, spell targeting, and perception check

**Blocked by:** Walls, solid objects (opacity = true), fog (magical or mundane), darkness (without darkvision)

**Not blocked by:** Creatures (provide cover, not concealment), transparent objects, objects shorter than the line of fire (elevation-dependent)

### 6.2 Line of Effect (LoE)

Per 3.5e RAW (PHB 175-176):
- Required for most spells and abilities
- Blocked by solid barriers (solidity = true) — wall of force, solid stone, etc.
- A window (glass) blocks line of effect but not line of sight
- The Box must check LoE for every spell that requires it

### 6.3 Fog of War (Player Visibility)

Per 3.5e RAW (PHB 164-165):
- Characters can see based on: light sources, darkvision, low-light vision
- Standard vision: bright light = normal sight, shadowy = 20% miss chance, darkness = blind
- Darkvision: 60ft (standard for dwarves, etc.) — see in black-and-white
- Low-light vision: see twice as far in dim conditions

**The fog of war on the battle map is Box-enforced.** The player sees only what their character can see. This is not optional — it is a fundamental 3.5e rule.

**Implementation benefit:** Fog of war IS the loading strategy. Content behind the fog doesn't need to be rendered until revealed. Progressive loading as exploration continues.

---

## 7. Area of Effect (AoE) System

### 7.1 AoE Templates (3.5e RAW — PHB 175-176)

| Shape | Measurement | Example |
|-------|-------------|---------|
| **Burst** | Radius from point of origin | Fireball (20ft radius) |
| **Emanation** | Radius from caster | Bless (50ft radius from caster) |
| **Spread** | Radius from point, flows around corners | Cloudkill |
| **Cone** | Quarter-circle from caster | Cone of Cold (60ft cone) |
| **Line** | Straight line from caster | Lightning Bolt (120ft line) |
| **Cylinder** | Radius + height from point | Flame Strike (10ft radius, 40ft high) |

### 7.2 AoE Display

During targeting:
- The AoE shape is shown as an overlay on the grid
- Creatures within the area are highlighted
- Creatures on the edge are clearly indicated (in or out?)
- The DM coordinates: "This covers goblins 1, 2, and 3. Goblin 4 is just outside."

### 7.3 AoE Accuracy Requirements

- The Box determines EXACTLY which squares are in the AoE
- For spheres/bursts: count squares from point of origin per 3.5e grid rules
- For cones: use the 3.5e cone template (PHB 176)
- For lines: trace the line through grid squares per 3.5e rules
- **Spell geometry is never approximate.** If the fireball is 20ft radius, the Box knows exactly which squares that covers.

### 7.4 AoE and Elevation

- Fireball is a sphere — it extends vertically
- A character on a 15ft ledge IS within a 20ft radius fireball centered at ground level (distance = 15ft < 20ft radius)
- A character in a 25ft deep pit is NOT within the same fireball (distance = 25ft > 20ft radius)
- The Box must calculate 3D distance for AoE effects

---

## 8. Movement System

### 8.1 Standard Movement (3.5e RAW — PHB 147-148)

| Terrain | Cost | Rule |
|---------|------|------|
| Normal | 5ft per square | Standard movement |
| Difficult terrain | 10ft per square | Rubble, undergrowth, uneven ground |
| Diagonal (first) | 5ft | First diagonal in a sequence |
| Diagonal (second) | 10ft | Alternating 5/10 for diagonals |
| Climbing (wall) | 10ft per 5ft vertical | Half speed, Climb check may be required |
| Swimming | 10ft per 5ft | Half speed, Swim check required |
| Crawling (prone) | 10ft per 5ft | Half speed while prone |

### 8.2 Movement Validation

The Box MUST validate every movement action:
- Does the character have enough movement remaining?
- Does the path cross difficult terrain? (Cost is doubled)
- Does the path cross threatened squares? (May trigger AoO)
- Can the character fit? (Size category vs. passage width)
- Is the character climbing, swimming, or otherwise specially moving?
- Is charging legal? (Straight line, no obstacles, within charge distance)

### 8.3 Attacks of Opportunity (AoO)

Per 3.5e RAW (PHB 137-138):
- Moving OUT of a threatened square provokes AoO
- Moving WITHIN a threatened square does not (usually)
- The Box must track all threatened squares for all creatures
- The Box must detect AoO triggers during movement
- The Box must prompt: "This movement provokes an AoO from [creature]. Continue?"

### 8.4 Special Movement

- **5-foot step:** Free 5ft movement that doesn't provoke AoO. Only if you haven't moved this turn.
- **Charge:** Double move in straight line, +2 attack, -2 AC. Must have clear path.
- **Bull Rush:** Opposed Strength check. May push target back.
- **Overrun:** Opposed Strength check. May move through opponent's square.
- **Tumble:** Move through threatened squares without provoking AoO (skill check required).
- **Withdraw:** Full-round action, no AoO from initial square.

All of these are Box-resolved with full rules citations.

---

## 9. Destructible Environment

### 9.1 Object Destruction

When a player or effect targets an object:
1. Box checks: Is the attack type effective against this material? (Fire vs wood = yes, bludgeoning vs iron = limited)
2. Box applies damage: damage - hardness = HP reduction
3. Box tracks HP: if current_hp ≤ 0, object is DESTROYED
4. Box determines consequences: what happens when this object breaks?

### 9.2 Destruction Consequences

When an object is destroyed:
- **Falls/collapses:** Determine direction, affected squares → new DESTROYED_TERRAIN in those squares
- **Creates difficult terrain:** Rubble, debris, fallen objects
- **May provide new cover:** A fallen tree can be used as cover from certain directions
- **May cause damage:** Falling object/debris may deal damage to creatures underneath (improvised falling damage rules)
- **May change LoS/LoE:** A destroyed wall opens new sightlines

### 9.3 Improvised Actions

Players will do unexpected things: flip tables, break chair legs for weapons, pull down shelving.

The Box + Lens + Spark symbiosis handles this:
1. Player declares action: "I flip the table"
2. Spark interprets → Lens translates → Box resolves: Strength check DC [based on table weight]
3. If success: Box updates table position, condition (PRONE), facing
4. Spark narrates the flip
5. Box recalculates cover from the new table position

For improvised weapons (broken chair leg, thrown bottle, etc.):
1. Spark provides world-knowledge: "chair leg, wood, ~2ft, ~3 lbs"
2. Lens indexes the improvised weapon properties
3. Box applies improvised weapon rules: 1d4 bludgeoning (or 1d3 for tiny), -4 attack penalty (not proficient)

---

## 10. Flanking

Per 3.5e RAW (PHB 153):
- Two allies on opposite sides of an enemy → both get +2 flanking bonus on melee attacks
- "Opposite sides" means: draw a line between the two allies' centers; if it passes through any two opposite sides or corners of the enemy's space, flanking is achieved
- The Box must calculate flanking geometry for all melee attacks
- Flanking status must be displayed/communicated to the player

---

## 11. Testing & Compliance Requirements

### 11.1 Testing Standard

Every mechanical system in this specification MUST have:
- Unit tests with PHB/DMG page number citations
- Edge case tests (minimum 3 per mechanic)
- Regression tests tagged with `@pytest.mark.raw_compliance`
- Integration tests with multi-object, multi-creature scenarios

### 11.2 Priority Test Scenarios

| Scenario | Tests Required | Why Critical |
|----------|---------------|--------------|
| Halfling behind chair | Cover calc with size-relative geometry | Core selling point — accuracy beyond physical table |
| Fireball in a room with elevation | AoE + vertical distance + multiple targets | Complex AoE with 3D component |
| Character under furniture | Height check + prone + cover | Player expectation of physical consistency |
| Tree hit by fireball → falls → difficult terrain | Destruction chain + terrain generation | Dynamic environment integrity |
| AoO during movement through multiple threatened squares | Sequential AoO triggers | High-frequency combat scenario |
| Diagonal movement + difficult terrain | Movement cost alternation + terrain multiplier | Common calculation error |
| Directional cover from overturned table | Cover from facing vs flanking around | Directional cover is unusual and must work |

### 11.3 M3.5 RAW Compliance Gate

This specification's mechanics are subject to M3.5 RAW Compliance Gate (see `M3_5_RAW_COMPLIANCE_GATE_PROPOSAL.md`). All mechanics listed here must pass the compliance gate before M4.

---

## 12. Non-Goals

This specification does NOT cover:
- Spell effect resolution (separate rules engine concern — effects are diverse)
- Creature AI / tactical behavior (Spark concern, not Box)
- Visual rendering technology (implementation detail)
- Network synchronization (solo-first, future milestone)
- Character sheet mechanics (separate Box concern)

---

## 13. Relationship to Spark/Lens/Box Architecture

| Concern | Layer | Authority |
|---------|-------|-----------|
| Object positions on the grid | **Box** | SOLE |
| Movement validation | **Box** | SOLE |
| Cover calculation | **Box** | SOLE |
| AoE determination | **Box** | SOLE |
| Line of sight / line of effect | **Box** | SOLE |
| Flanking geometry | **Box** | SOLE |
| Object destruction resolution | **Box** | SOLE |
| Object physical dimensions | **Lens** (sourced from Spark) | DATA |
| Object material classification | **Lens** (sourced from Spark) | DATA |
| Scene generation / description | **Spark** | NARRATIVE |
| Combat narration | **Spark** | NARRATIVE |
| DM coordination ("Drop fireball here?") | **Spark** via **Lens** | PRESENTATION |

**The Box is sovereign over the battle map. The Lens serves data. The Spark narrates.**

---

## END OF BATTLE MAP & ENVIRONMENTAL PHYSICS SPECIFICATION

**Date:** 2026-02-11
**Authors:** Thunder (Product Owner), Opus (Acting PM)
**Status:** BINDING
**Layer:** BOX

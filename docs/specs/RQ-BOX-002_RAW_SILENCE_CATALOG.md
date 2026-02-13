# RQ-BOX-002: RAW Silence Catalog — Systematic Audit of 3.5e Underspecification

**Domain:** Box Layer — House Policy Governance
**Status:** DRAFT
**Filed:** 2026-02-12
**Gate:** Must complete before Template Family Registry can be finalized
**Prerequisite:** House Policy Governance Doctrine (PO session 2026-02-12)

---

## 1. Thesis

The House Policy Governance Doctrine establishes that the system has exactly two authority sources: Rules As Written (RAW) and explicit House Policies. House Policies are instantiated at runtime only within pre-declared trigger families. The system has zero authority to create new categories of judgment at runtime. If no trigger family covers a situation, RAW applies or the system fails closed.

This architecture requires that the set of trigger families be **complete before deployment**. A trigger family that doesn't exist cannot catch silences that fall within its domain. A silence that no family covers produces a FAIL_CLOSED event — correct behavior, but a degraded player experience if it happens frequently.

The Template Family Registry cannot be finalized by guessing which problems will arise. It must be built from a systematic inventory of where RAW is silent, where RAW is ambiguous, and where RAW is contradictory. This research question exists to produce that inventory.

The alternative — building trigger families reactively as FAIL_CLOSED events accumulate during play — violates the doctrine itself, because it means the system's coverage is being shaped by runtime encounters rather than offline human research. The trigger family list must be designed, not discovered.

---

## 2. Methodology

### 2.1 Audit Structure

The audit proceeds domain by domain through the mechanical systems relevant to Box's v1 scope:

1. **Equipment & Inventory**
2. **Movement & Terrain**
3. **Spellcasting & Targeting**
4. **Combat Interactions**
5. **Environmental & Physics**
6. **Social & NPC** (deferred — see Scope Boundaries)

Within each domain, the auditor examines the 3.5e core rulebooks (PHB, DMG, MM) for situations where a deterministic rules engine must make a decision but the text does not provide a deterministic answer.

### 2.2 Silence Classification

Every identified silence is classified into one of three types:

| Type | Definition | Example |
|------|-----------|---------|
| **SILENT** | No rule exists. RAW says nothing. | "Can a 10-foot ladder fit inside a backpack?" |
| **AMBIGUOUS** | A rule exists but admits multiple valid interpretations. | "Does a tanglefoot bag work underwater?" |
| **CONTRADICTORY** | Two or more rules conflict. | Grapple size restrictions vs. spell targeting rules for enlarge effects mid-grapple. |

### 2.3 Data Availability Assessment

For each silence, determine:

- **(a) Partial RAW data exists** — RAW provides some inputs that a template could consume (e.g., material hardness, weight, size category). The template needs to supply the missing formula or threshold.
- **(b) Pure gap** — RAW provides no relevant data at all. The template must supply both the inputs and the formula.

Category (a) silences are strong candidates for template families because the templates can lean on existing RAW data. Category (b) silences require more opinionated house policy and carry higher design risk.

### 2.4 Trigger Family Mapping

Every silence is mapped to one of the declared trigger families, or flagged as `NEW_FAMILY_NEEDED` with a justification for why no existing family covers it.

The current trigger family candidates:

| # | Family | Scope |
|---|--------|-------|
| 1 | CONTAINMENT_PLAUSIBILITY | Does item fit in container |
| 2 | RETRIEVAL_ACCESSIBILITY | Action cost to access stored item |
| 3 | CONCEALMENT_PLAUSIBILITY | Can item be hidden on person |
| 4 | ENVIRONMENTAL_INTERACTION | Can tool/weapon affect object (hardness/material) |
| 5 | SPATIAL_CLEARANCE | Can creature/item fit in space |
| 6 | STACKING_NESTING_LIMITS | Bags inside bags |
| 7 | FRAGILITY_BREAKAGE | Does rough handling damage item |
| 8 | READINESS_STATE | "At hand" vs "stowed" and action cost |
| 9 | MOUNT_COMPATIBILITY | Can creature serve as mount for rider |
| 10 | STRUCTURAL_LOAD_BEARING | Can object support weight across span |

---

## 3. Known Silences (Initial Catalog)

These silences have already been identified through prior work and PO sessions. They seed the audit but do not replace it.

### SIL-001: Container Capacity (Volume/Shape)

- **Domain:** Equipment & Inventory
- **Description:** RAW defines container capacity by weight only. A backpack holds 60 lbs. RAW does not address volume or shape. A 10-foot ladder weighs 20 lbs — well under the limit — but obviously does not fit in a backpack.
- **RAW data available:** Weight capacity per container, item weights.
- **RAW data missing:** Volume capacity, item dimensions, shape constraints.
- **Silence type:** SILENT
- **Trigger family:** CONTAINMENT_PLAUSIBILITY
- **Frequency:** Often
- **Exploit severity if unaddressed:** Major — players can carry arbitrary objects by weight-gaming.

### SIL-002: Structural Load-Bearing

- **Domain:** Environmental & Physics
- **Description:** RAW provides object hit points and hardness by material and thickness. It does not provide load-bearing capacity. "Can a wooden door support an ogre standing on it?" has no RAW answer. HP tells you how much damage an object can absorb, not how much static weight it can bear.
- **RAW data available:** Material hardness, HP by thickness, break DCs.
- **RAW data missing:** Load-bearing formula, span limits, distributed vs. point load distinction.
- **Silence type:** SILENT
- **Trigger family:** STRUCTURAL_LOAD_BEARING
- **Frequency:** Sometimes
- **Exploit severity if unaddressed:** Mild — creative but niche exploit vector.

### SIL-003: Item Retrieval Action Cost

- **Domain:** Equipment & Inventory
- **Description:** RAW specifies that drawing a weapon is a move action (free with BAB +1). RAW does not specify the action cost of retrieving an item from a backpack vs. a belt pouch vs. an item stowed inside a bag inside a backpack. The rules assume "retrieve a stored item" is a move action, but nested storage and varying accessibility are unaddressed.
- **RAW data available:** "Retrieve a stored item" = move action (PHB Table 8-2).
- **RAW data missing:** Action cost gradient by storage depth, container type, encumbrance interaction.
- **Silence type:** SILENT
- **Trigger family:** RETRIEVAL_ACCESSIBILITY
- **Frequency:** Often
- **Exploit severity if unaddressed:** Mild — players may argue everything is always "at hand."

### SIL-004: Object Identity Under Damage

- **Domain:** Combat Interactions / Environmental & Physics
- **Description:** When a table is sundered in half, is it still "one object" or "two objects"? This matters for spells like *mending* and *make whole*, for size category, for HP tracking, and for further sunder attempts. RAW does not define when a damaged object becomes multiple objects.
- **RAW data available:** Object HP, sunder rules, hardness.
- **RAW data missing:** Identity model — threshold for one-object-to-many transition, size recalculation.
- **Silence type:** SILENT
- **Trigger family:** Deferred to **RQ-BOX-003** (Object Identity Model) — this silence is complex enough to warrant its own research question.
- **Frequency:** Sometimes
- **Exploit severity if unaddressed:** Major — affects spell targeting, HP tracking, and downstream mechanics.

### SIL-005: Concealment of Oversized Items

- **Domain:** Equipment & Inventory
- **Description:** The Sleight of Hand skill allows concealing objects on one's person, opposed by Spot. RAW does not specify size or shape limits for concealment beyond a -20 penalty for "large" items. A halfling concealing a greatsword and a human concealing a dagger use the same mechanic.
- **RAW data available:** Sleight of Hand rules, size penalties (vague), Spot opposition.
- **RAW data missing:** Object-to-creature size ratio thresholds, shape constraints, location-on-body limits.
- **Silence type:** AMBIGUOUS — a rule exists but "large" is undefined in this context.
- **Trigger family:** CONCEALMENT_PLAUSIBILITY
- **Frequency:** Sometimes
- **Exploit severity if unaddressed:** Mild — mostly comical edge cases, but can affect stealth gameplay.

### SIL-006: Mount Weight Limits

- **Domain:** Movement & Terrain
- **Description:** RAW states a mount must be at least one size category larger than the rider and "suitable" for mounting. RAW provides carrying capacity by Strength score. RAW does not provide explicit weight thresholds for when a mount's performance degrades or when mounting is refused — carrying capacity and mount suitability are two separate systems that don't cross-reference each other.
- **RAW data available:** Size category rules, mount carrying capacity by Strength, encumbrance thresholds.
- **RAW data missing:** Explicit "mount refuses" threshold, performance degradation rules for overloaded mounts, interaction between rider gear weight and mount encumbrance.
- **Silence type:** AMBIGUOUS — rules exist in both systems but their interaction is unspecified.
- **Trigger family:** MOUNT_COMPATIBILITY
- **Frequency:** Sometimes
- **Exploit severity if unaddressed:** Mild — mostly arises with unusual mount/rider combinations.

### SIL-007: Magic Item Enhancement Bonus to Hardness/HP (PHB vs DMG Contradiction)

- **Domain:** Combat Interactions
- **Description:** PHB p.165 states each +1 enhancement bonus adds +2 hardness and +10 HP to weapons, armor, and shields. DMG p.222 states each +1 adds +1 hardness and +1 HP. These are directly contradictory. The system must pick one formula and document the choice as a House Policy.
- **RAW data available:** Both formulas exist in print, both in core rulebooks.
- **RAW data missing:** Authoritative resolution of the contradiction. No errata resolves it.
- **Silence type:** CONTRADICTORY
- **Trigger family:** ENVIRONMENTAL_INTERACTION — prerequisite for entire sunder subsystem.
- **Frequency:** Always (every magic weapon, armor, and shield in the game)
- **Exploit severity:** Major — wrong interpretation makes sunder either useless or game-breakingly powerful.
- **Source:** Community research (EN World sunder threads, RQ-BOX-002-A survey)

### SIL-008: Armor Enhancement Bonus Exclusion from Hardness/HP Table

- **Domain:** Combat Interactions
- **Description:** The DMG enhancement bonus table (p.222) explicitly covers weapons and shields but omits armor. Under strict RAW, a +5 full plate has base hardness 10 and ~20 HP with no enhancement bonus contribution, making it trivially destroyable by a single Power Attack. The PHB table includes armor, further deepening the SIL-007 contradiction.
- **RAW data available:** Armor base hardness and HP (DMG p.61). Enhancement bonus rules for weapons and shields (DMG p.222).
- **RAW data missing:** Whether armor is intentionally excluded or accidentally omitted from the DMG table.
- **Silence type:** SILENT (armor simply not mentioned in the DMG enhancement table)
- **Trigger family:** ENVIRONMENTAL_INTERACTION
- **Frequency:** Rare (few players attempt armor sunder)
- **Exploit severity:** Major (if exploited, trivializes armored opponents)
- **Source:** Community research (EN World sunder threads, RQ-BOX-002-A survey)

### SIL-009: Grapple Square Threatening

- **Domain:** Combat Interactions
- **Description:** Do grappled creatures threaten adjacent squares? If not, they cannot make AoO against bystanders or the grappler. If yes, grappling restricts movement but not threat range. RAW grapple rules (PHB p.156) list action restrictions but do not explicitly address whether the grappled condition removes square threatening. Threatening rules (PHB p.137) require a melee weapon to be wielded, which a grappled creature arguably still holds.
- **RAW data available:** Grapple action restrictions (PHB p.156), threatening definition (PHB p.137).
- **RAW data missing:** Explicit statement on whether grappled creatures threaten adjacent squares.
- **Silence type:** AMBIGUOUS
- **Trigger family:** None — combat rules interpretation. Box resolver picks one reading and documents it.
- **Frequency:** Often (grapple is a common combat interaction)
- **Exploit severity:** Mild
- **Source:** Community research (Giant in the Playground grapple threads, RQ-BOX-002-A survey)

### SIL-010: Object Physical State After HP Reaches Zero

- **Domain:** Environmental & Physics / Combat Interactions
- **Description:** When an object's HP reaches 0, RAW says it is "ruined" (DMG p.61). RAW does not define what "ruined" means physically — two pieces? Bent metal? Pile of fragments? This affects mending/make whole targeting (SIL-004), salvage, material reuse for crafting, and whether the remains count as one object or many.
- **RAW data available:** Object HP thresholds, sunder rules, "ruined" keyword.
- **RAW data missing:** Physical description of destruction states, fragment count, salvage rules, material recovery.
- **Silence type:** SILENT
- **Trigger family:** Deferred to **RQ-BOX-003** (Object Identity Model) — complements SIL-004 (identity under damage) with the "identity after destruction" question.
- **Frequency:** Sometimes
- **Exploit severity:** Mild (mainly affects repair spells and salvage)
- **Source:** Community research (EN World sunder threads, RQ-BOX-002-A survey)

---

## 4. Audit Domains

### 4.1 Equipment & Inventory

The highest-density silence domain. RAW equipment rules are built around weight, gold piece cost, and single-sentence descriptions. Likely silences:

- Container volume and shape constraints (SIL-001)
- Item nesting limits (bag inside bag inside bag)
- Liquid container interactions (potion in open flask vs. sealed vial, spillage)
- Item dimensions (RAW rarely specifies length, width, or thickness)
- Ammunition storage and retrieval while moving
- Shield stowage and readiness transitions
- Equipment degradation from environmental exposure (wet bowstrings, rusted armor)

### 4.2 Movement & Terrain

RAW movement rules specify speed, difficult terrain multipliers, and some climbing/swimming DCs. Likely silences:

- Climbing surfaces without a stated DC (brick wall vs. rough cave wall vs. ice)
- Swimming while wearing armor beyond "check penalty applies"
- Squeezing through gaps for creatures with gear (armor width, weapon length)
- Jump distance with heavy load or bulky equipment
- Movement across unstable surfaces (ice, wet stone, loose rubble)
- Mounted movement through terrain the mount can traverse but the rider cannot reach (low ceilings)

### 4.3 Spellcasting & Targeting

RAW spell descriptions are generally precise about targeting, but interactions with the physical environment are often unaddressed. Likely silences:

- Object identity for repair spells (*mending*, *make whole*) — deferred to RQ-BOX-003
- Area effect interaction with terrain features (does a *fireball* go around corners? RAW says yes. Does it go through arrow slits? Unclear.)
- Spell component availability (does the caster have bat guano if they haven't explicitly purchased it?)
- Line of effect through partial cover (window, portcullis, curtain)
- Targeting objects held by creatures vs. unattended objects (clear in some spells, silent in others)

### 4.4 Combat Interactions

RAW combat is the most thoroughly specified domain, but edge cases remain. Likely silences:

- Improvised weapons from environment (table leg, chair, rock) — damage, proficiency, and properties
- Cover from objects of varying size (does a barrel provide cover? A crate? A corpse?)
- Attacking objects at different scales (striking a rope, hitting a keyhole, breaking a chain)
- Sunder interactions with natural weapons and unarmed strikes
- Combat in unusual environments (underwater is specified; waist-deep water is not)
- Falling onto objects or creatures (damage distribution, both directions)
- **PHB vs DMG enhancement bonus contradiction** (SIL-007) — affects all magic item durability
- **Armor excluded from enhancement HP/hardness table** (SIL-008) — makes armor sunder trivial
- **Grappled creature threatening** (SIL-009) — affects AoO during grapple
- **Object physical state after destruction** (SIL-010) — "ruined" is undefined physically

### 4.5 Environmental & Physics

RAW provides some environmental rules (fire, falling, drowning) but assumes a DM will adjudicate physical interactions. Likely silences:

- Fire spread between objects and across surfaces
- Water depth effects on movement and combat at granularities below "fully submerged"
- Falling onto objects vs. falling onto ground (does a hay bale reduce fall damage?)
- Temperature effects on materials (frozen rope, heated metal)
- Structural integrity of constructed features under load (SIL-002)
- Smoke, fog, and gas interactions with wind and enclosed spaces

### 4.6 Social & NPC

**Deferred to future work.** Social mechanics (Diplomacy, Intimidate, Bluff, Sense Motive) interact with Spark's narrative domain and are out of scope for the v1 Box layer. NPC behavioral responses to house-policy situations (e.g., a shopkeeper's reaction to an absurd Diplomacy check) are a Spark concern, not a Box concern.

---

## 5. Output Format

Each silence entry in the final catalog must capture the following fields:

| Field | Description | Example |
|-------|-------------|---------|
| **Silence ID** | Unique identifier | SIL-001 |
| **Domain** | Audit domain | Equipment & Inventory |
| **Description** | The specific question RAW doesn't answer | "Can a 10-foot ladder fit in a backpack?" |
| **RAW data available** | What inputs exist in the written rules | Weight capacity, item weight |
| **RAW data missing** | What inputs would be needed for a deterministic answer | Volume, dimensions, shape constraints |
| **Silence type** | SILENT / AMBIGUOUS / CONTRADICTORY | SILENT |
| **Trigger family** | Mapped family or NEW_FAMILY_NEEDED | CONTAINMENT_PLAUSIBILITY |
| **Frequency estimate** | Rare / Sometimes / Often | Often |
| **Exploit severity** | None / Mild / Major | Major |

Entries flagged as `NEW_FAMILY_NEEDED` must include a one-sentence justification for why no existing family covers the silence. These entries are candidates for expanding the trigger family list.

---

## 6. Success Criteria

The audit is complete when:

1. All six audit domains have been surveyed (Social & NPC surveyed and explicitly deferred with rationale).
2. Every identified silence has a complete entry in the output format above.
3. Every silence is classified by type (SILENT / AMBIGUOUS / CONTRADICTORY).
4. Every silence is mapped to a trigger family or flagged as `NEW_FAMILY_NEEDED`.
5. The trigger family list is either **confirmed sufficient** (all silences map to existing families) or **expanded with justified additions** (new families added with documented rationale).
6. No silence is left unmapped — every entry has a family assignment or a NEW_FAMILY_NEEDED flag.
7. Frequency and exploit severity estimates are provided for prioritization of Template Family Registry work.

---

## 7. Scope Boundaries

This research question does **not**:

- **Design template implementations.** That is the Template Family Registry's job. This research identifies *what* needs templates, not *how* those templates work.
- **Implement any code.** This is a research artifact, not a development task.
- **Evaluate RAW ambiguities for the "correct" interpretation.** Where RAW is ambiguous, this research notes the ambiguity and classifies it. Choosing the correct interpretation is rules research, not silence cataloging.
- **Cover Tier 2+ mechanics.** Spells above level 5, prestige classes, epic-level rules, and supplement material are locked behind capability gates and are excluded from this audit.
- **Address Social & NPC domain.** Deferred to future work as noted in Section 4.6. The v1 Box layer does not adjudicate social mechanics.
- **Produce a complete catalog in one pass.** The initial catalog will be expanded as implementation work surfaces additional silences. The methodology is designed to be repeatable, not exhaustive on first execution.

---

## 8. Relationship to Other Work

| Relationship | Target | Notes |
|-------------|--------|-------|
| **Feeds into** | Template Family Registry (not yet created) | The silence catalog defines the problem space; the registry defines the solution space. |
| **Feeds into** | FAIL_CLOSED Logging Schema (not yet created) | Silences not covered by trigger families produce FAIL_CLOSED events. The logging schema must capture enough context to retroactively classify the silence. |
| **Related** | RQ-BOX-003 (Object Identity Model) | Discovered through this research (SIL-004). Object identity is a cross-cutting concern that affects multiple silence entries and warrants its own research question. |
| **Related** | RQ-LENS-SPARK-001 (Context Orchestration Sprint) | Independent track. Lens/Spark work does not depend on this research, but the FAIL_CLOSED surface area identified here will inform Lens's error-handling contract. |
| **Prerequisite** | House Policy Governance Doctrine (PO session 2026-02-12) | This research exists to operationalize the doctrine. The doctrine defines the rules; this research identifies the terrain those rules must cover. |

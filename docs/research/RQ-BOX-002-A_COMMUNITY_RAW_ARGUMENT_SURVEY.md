# RQ-BOX-002-A: Community RAW Argument Survey

**Domain:** Box Layer — House Policy Governance
**Status:** DRAFT
**Filed:** 2026-02-12
**Parent:** RQ-BOX-002 (RAW Silence Catalog)
**Purpose:** Mine community debates to identify RAW silences, ambiguities, and contradictions that real tables encounter

---

## 1. Methodology

This survey examines community debates from EN World, Giant in the Playground,
RPGnet, MinMaxForum, and general D&D discussion spaces to identify the RAW
gaps that cause the most table friction in 3.5e. The goal is not to resolve
these debates but to **catalog the questions being asked** — each unresolvable
argument signals a silence, ambiguity, or contradiction that the system must
handle.

**Selection criteria:** Only debates where RAW genuinely fails to provide a
deterministic answer are cataloged. "Player misread the rules" and "DM
disagrees with RAW" are excluded. The focus is on cases where two competent
readers of the same text reach different conclusions, or where the text
provides no answer at all.

---

## 2. Category A: Object Hardness, HP, and Sunder

**Community heat level:** Very High — one of the most debated subsystems in 3.5e.

### Finding A-1: PHB vs DMG Enhancement Bonus Contradiction

**The contradiction:**
- PHB p.165: Each +1 enhancement bonus adds **+2 hardness** and **+10 HP** to weapons, armor, and shields.
- DMG p.222: Each +1 enhancement bonus adds **+1 hardness** and **+1 HP** to weapons and shields.

This is not ambiguity — it is a direct numerical contradiction between two core books on the same mechanic. No errata resolved it definitively.

**Silence type:** CONTRADICTORY
**Impact:** Determines whether sunder is viable at mid-to-high levels. Under PHB numbers, a +5 weapon gains +10 hardness and +50 HP (extremely durable). Under DMG numbers, +5 hardness and +5 HP (trivially destroyed).
**Trigger family mapping:** ENVIRONMENTAL_INTERACTION (#4) — but this is really a prerequisite for the entire sunder subsystem, not just a house policy edge case.
**Frequency:** Always (affects every magic weapon and armor in the game).
**Exploit severity:** Major — wrong interpretation makes sunder either useless or game-breakingly powerful.

**Catalog entry:** SIL-007 (new)

### Finding A-2: Armor Does Not Benefit From Enhancement Bonus (RAW)

The DMG enhancement bonus table applies to weapons and shields but NOT to armor. A +5 full plate has no additional hardness or HP beyond base values (hardness 10, ~20 HP). A 12th-level fighter can destroy +5 full plate in a single Power Attack.

**Silence type:** SILENT (armor excluded from the enhancement table)
**Impact:** Makes armor sunder trivially easy. A greatsword with Power Attack deals 2d6+25 vs hardness 10, 20 HP. One hit destroys the best armor in the game.
**Trigger family mapping:** ENVIRONMENTAL_INTERACTION (#4)
**Frequency:** Rare in practice (few players attempt armor sunder because it feels wrong)
**Exploit severity:** Major — if the system allows it RAW, a sunder-focused build trivializes armored opponents.

**Catalog entry:** SIL-008 (new)

### Finding A-3: Double Weapon Enhancement Stacking

RAW allows the enhancement bonuses on both ends of a double weapon to stack for hardness/HP purposes. A +2/+1 Dwarven Urgrosh would gain +6 hardness and +30 HP total (both ends contribute). This was almost certainly unintended.

**Silence type:** AMBIGUOUS (rule as written produces an absurd result)
**Trigger family mapping:** ENVIRONMENTAL_INTERACTION (#4)
**Frequency:** Rare
**Exploit severity:** Mild

**Catalog entry:** Not cataloged separately — subsumes under SIL-007.

### Finding A-4: Adamantine Ignoring Hardness

Adamantine weapons ignore hardness up to 20, making sunder trivially easy against non-adamantine objects. Combined with the low base HP of most objects, adamantine weapons can destroy nearly anything in one hit. Community consensus: "the first thing a PC should get is a +1 adamantine weapon."

**Silence type:** Not truly silent — RAW is clear. But the interaction produces balance problems that RAW doesn't address.
**Impact:** Sunder becomes a dominant strategy for adamantine-equipped characters.
**Trigger family mapping:** No trigger family needed — this is a RAW-as-designed interaction, not a silence. The system should implement it faithfully. If PO decides it needs adjustment, that's a conscious House Policy decision, not a silence fill.
**Catalog entry:** Not cataloged — RAW is unambiguous. Note for future design reference only.

### Finding A-5: Object HP Values Are Too Low

Community consensus: "Iron/Steel have Hardness 10, Wood Hardness 5, and this just isn't enough to stop most normal damage. Their HP is even more pathetic, only 2-10 for most weapons." A +5 bow has ~7 HP (wood, thin), making it trivially destroyed.

**Silence type:** Not a silence — RAW provides the numbers. The problem is that the numbers produce unsatisfying gameplay.
**Trigger family mapping:** FRAGILITY_BREAKAGE (#7) — but only if the system needs to adjudicate incidental damage (dropping, environmental exposure). Intentional sunder uses RAW directly.
**Catalog entry:** Not cataloged as a silence. Design note for FRAGILITY_BREAKAGE family.

---

## 3. Category B: Polymorph, Wild Shape, and Form Change

**Community heat level:** Extreme — the polymorph subsystem was officially declared broken by WotC.

### Finding B-1: Equipment Melding Rules

When a character polymorphs, equipment either stays (if the new form can wear it) or melds into the new form. RAW for which items meld and which don't is ambiguous:
- Armor and shield bonuses cease when melded.
- Constant-effect items continue to function when melded.
- Activation items cannot be used when melded.

**Silence type:** AMBIGUOUS — the categories exist but edge cases are legion (ring worn on a tentacle? boots on a quadruped?)
**Trigger family mapping:** Does not map to current families. **NEW_FAMILY_NEEDED: FORM_CHANGE_EQUIPMENT** — What happens to equipment when a creature's form changes. However, this is deep in Tier 2+ territory (polymorph is not in v1 scope). Deferred.
**Catalog entry:** Not cataloged — out of v1 scope (polymorph not implemented).

### Finding B-2: Spell Component Pouch and Polymorphed Casters

A polymorphed caster's spell component pouch melds into the new form, making material component casting impossible without Eschew Materials. RAW provides no clean solution.

**Silence type:** AMBIGUOUS
**Trigger family mapping:** Out of v1 scope.
**Catalog entry:** Not cataloged — out of v1 scope.

### Finding B-3: Form Stacking / Template Inheritance

Whether a polymorphed creature retains templates from its original form is hotly debated. Designer (Skip Williams) said no, but RAW text doesn't explicitly prohibit it. This created the "Polymorph → Assume template → Stack" exploit chain.

**Silence type:** AMBIGUOUS (RAW silent on template interaction)
**Trigger family mapping:** Out of v1 scope.
**Catalog entry:** Not cataloged — out of v1 scope.

**Note for future work:** When polymorph enters scope, this entire subsystem will need its own research question. The volume of RAW problems is large enough that WotC abandoned the spell entirely in favor of the PHB II "Polymorph Subschool" replacement.

---

## 4. Category C: Grapple, Unarmed Strikes, and AoO

**Community heat level:** Very High — "one of the most complex attacks in the game with tons of confusing rules."

### Finding C-1: Unarmed Attacks in Grapple and AoO Provocation

Does making an unarmed attack while grappling provoke an AoO? RAW says unarmed attacks provoke AoO unless you have Improved Unarmed Strike. Grapple rules say you can damage an opponent with an unarmed strike. The interaction is ambiguous:
- You can't provoke AoO from the person you're grappling (they don't threaten squares while grappled — debated).
- Bystanders adjacent to the grapple may get AoO.

**Silence type:** AMBIGUOUS
**Trigger family mapping:** No trigger family needed — this is a combat rules interpretation, not a physics/plausibility judgment. The system must pick one interpretation and implement it deterministically.
**Catalog entry:** Not cataloged as a silence — this is a rules interpretation that Box resolves by choosing one reading. Document the choice in Box's resolver comments.

### Finding C-2: Flurry of Blows in Grapple

Whether a monk can use Flurry of Blows while grappling is "contested." It depends on whether Flurry is a "full attack action" (grapple allows full attack) or a "special full round action" (grapple only allows standard full attack). RAW is genuinely ambiguous on the classification of Flurry.

**Silence type:** AMBIGUOUS
**Trigger family mapping:** No trigger family — combat rules interpretation.
**Catalog entry:** Not cataloged — Box combat resolver decision. When monks are implemented, document the ruling.

### Finding C-3: Monk Unarmed Strike — Manufactured vs Natural Weapon

A monk's unarmed strike is "treated as both a manufactured weapon and a natural weapon for the purpose of spells and effects." This dual classification creates edge cases with feats (Improved Natural Attack), magic item enhancement, and iterative attack calculations.

**Silence type:** AMBIGUOUS (intentional dual classification creates unintended interactions)
**Trigger family mapping:** No trigger family — combat rules interpretation.
**Catalog entry:** Not cataloged — Box combat resolver decision.

---

## 5. Category D: Simulacrum and Spell Ontology

**Community heat level:** High — one of the most debated single spells in D&D history.

### Finding D-1: "51-60% of Level" Definition

Simulacrum gives the copy 51-60% of the original's hit points, knowledge, level, skills, and personality. What does "51-60% of level" mean? A level 20 wizard's simulacrum at 55% has level 11. But what about a level 15 wizard at 55%? Level 8.25 — half a level of "loose XP." RAW provides no rounding rule.

**Silence type:** AMBIGUOUS
**Trigger family mapping:** No trigger family — spell resolution rules. This is a Box spell resolver question, not a physics/plausibility judgment.
**Catalog entry:** Not cataloged — spell implementation decision (Simulacrum is level 7, currently out of v1 scope).

### Finding D-2: Simulacrum Spellcasting Ability

Does a simulacrum of a wizard get spellcasting? The spell says it gets "knowledge" and "level" at reduced percentage, but spellcasting and class features are not explicitly listed. Community is deeply split.

**Silence type:** AMBIGUOUS
**Catalog entry:** Not cataloged — out of v1 scope.

### Finding D-3: Simulacrum Army / Infinite Loop

A simulacrum can cast spells (if interpretation D-2 allows it). Can it cast simulacrum? If yes, can the simulacrum's simulacrum cast simulacrum? This produces an infinite army. 2024 revision explicitly closed this loop.

**Silence type:** AMBIGUOUS (3.5e), RESOLVED (2024)
**Catalog entry:** Not cataloged — out of v1 scope. When simulacrum enters scope, the infinite-loop case must be explicitly addressed in the spell definition.

### Finding D-4: Simulacrum Object Identity

Is a simulacrum of a creature a "creature" for spell targeting purposes? Can it be healed? Can it be raised if destroyed? This is a variant of the object identity problem (RQ-BOX-003) applied to spell-created entities.

**Silence type:** AMBIGUOUS
**Trigger family mapping:** Feeds into RQ-BOX-003 (Object Identity Model) — spell-created entity identity is a subcase of the general object identity problem.
**Catalog entry:** Deferred to RQ-BOX-003.

---

## 6. Category E: Famous RAW Exploits (Physics Abuse)

**Community heat level:** Legendary — these are cultural touchstones of the 3.5e community.

### Finding E-1: The Locate City Nuke

A harmless 1st-level divination (Locate City) with a 10-mile/level AoE is combined with feat chains (Snowcasting → Flash Frost → Lord of the Uttercold → Fell Drain) to deal negative energy damage across an area the size of a country, killing every commoner and raising them as wights.

**Relevance to AIDM:** Low for v1 (requires feats and spells not in scope). However, it demonstrates a systemic problem: RAW provides no "sanity check" on feat/spell interaction chains. The system must either:
(a) Implement every interaction faithfully (and accept exploits), or
(b) Have a gate that catches degenerate combinations.

**AIDM position:** (a) — implement RAW faithfully. The No-Opaque-DM doctrine forbids the system from exercising judgment about whether a legal combination "should" work. If the feats and spells are implemented and the prerequisites are met, the interaction fires. If PO decides to ban specific feat chains, that's a House Policy decision (a banned-combination list), not a runtime judgment.

**Catalog entry:** Not cataloged — out of v1 scope. Design principle noted.

### Finding E-2: The Peasant Railgun

2,280 peasants in a line pass a 10-foot pole hand-to-hand in a single round, propelling it to Mach 1.5. The final peasant throws it.

**Relevance to AIDM:** None mechanically (D&D has no momentum rules). The exploit fails RAW because there is no "velocity damage" mechanic. The pole arrives at the final peasant at zero velocity and is thrown normally.

**Significance:** Demonstrates that RAW is not physics. The system should never attempt to simulate real physics — it should implement RAW mechanics. When RAW is silent on a physical interaction, the system uses trigger families (bounded templates), not physics simulation.

**Catalog entry:** Not cataloged — illustrative only. Reinforces design principle.

### Finding E-3: Bag of Holding + Portable Hole Void Bomb

Placing one extradimensional container inside another produces a catastrophic planar rupture. Players weaponize this as a "void bomb" — move within 10 feet of target, combine containers, plane shift away.

**Relevance to AIDM:** The containers and their interaction are well-defined RAW. The system implements it faithfully. No silence — RAW is explicit about the result.

**Catalog entry:** Not cataloged — RAW is unambiguous.

---

## 7. New Silence Catalog Entries (Derived from Community Research)

The following new entries are recommended for addition to the RQ-BOX-002 catalog:

### SIL-007: Magic Item Enhancement Bonus to Hardness/HP (PHB vs DMG)

- **Domain:** Combat Interactions
- **Description:** PHB p.165 says +2 hardness/+10 HP per enhancement bonus. DMG p.222 says +1 hardness/+1 HP. These are contradictory. The system must pick one.
- **RAW data available:** Both formulas exist.
- **RAW data missing:** Authoritative resolution of the contradiction.
- **Silence type:** CONTRADICTORY
- **Trigger family:** ENVIRONMENTAL_INTERACTION (#4) — but really a sunder-subsystem prerequisite.
- **Frequency:** Always (every magic weapon/armor/shield)
- **Exploit severity:** Major

### SIL-008: Armor Enhancement Bonus Exclusion from Hardness/HP Table

- **Domain:** Combat Interactions
- **Description:** The DMG enhancement bonus table explicitly covers weapons and shields but omits armor. A +5 full plate has base hardness 10 and ~20 HP with no enhancement bonus contribution. Destroyed in one Power Attack hit.
- **RAW data available:** Armor base hardness and HP. Enhancement bonus rules for weapons and shields.
- **RAW data missing:** Whether armor is intentionally excluded or accidentally omitted.
- **Silence type:** SILENT (armor simply not mentioned in the enhancement table)
- **Trigger family:** ENVIRONMENTAL_INTERACTION (#4)
- **Frequency:** Rare (few attempt armor sunder)
- **Exploit severity:** Major (if exploited, trivially destroys armored opponents)

### SIL-009: Grapple Square Threatening

- **Domain:** Combat Interactions
- **Description:** Do grappled creatures threaten adjacent squares? If not, they cannot make AoO against bystanders. If yes, grappling only restricts movement but not threat range. RAW is ambiguous — grapple imposes restrictions on actions but doesn't explicitly address threatening.
- **RAW data available:** Grapple action restrictions (PHB p.156), threatening rules (PHB p.137).
- **RAW data missing:** Explicit statement on whether grappled creatures threaten.
- **Silence type:** AMBIGUOUS
- **Trigger family:** None — combat rules interpretation, not physics/plausibility. Box resolver decision.
- **Frequency:** Often (grapple is common)
- **Exploit severity:** Mild

### SIL-010: Object State After HP Reaches Zero

- **Domain:** Environmental & Physics / Combat Interactions
- **Description:** When an object's HP reaches 0, it is "ruined" (DMG p.61). RAW does not define what "ruined" means physically. Is a "ruined" sword in two pieces? A bent hunk of metal? A pile of fragments? This affects mending/make whole targeting, salvage, and whether the material can be reused for crafting.
- **RAW data available:** Object HP thresholds, sunder rules, "ruined" keyword.
- **RAW data missing:** Physical description of destruction state, fragment count, salvage rules.
- **Silence type:** SILENT
- **Trigger family:** Deferred to **RQ-BOX-003** (Object Identity Model) — this is the "what happens after destruction" complement to SIL-004 (identity under damage).
- **Frequency:** Sometimes
- **Exploit severity:** Mild (mainly affects repair spells and salvage)

---

## 8. Design Principles Reinforced by Community Research

### Principle 1: RAW is Not Physics

The Peasant Railgun and similar exploits demonstrate that D&D's action economy is not a physics simulation. The system must never attempt to derive physical consequences from game mechanics. When RAW is silent on a physical interaction, trigger families provide bounded answers — they do not simulate physics.

### Principle 2: Contradictions Require a Choice, Not a Judgment

The PHB vs DMG sunder numbers are a direct contradiction. The system cannot resolve this at runtime by "picking the more reasonable one" — that would be opaque DM behavior. The system must:
1. Pick one interpretation at design time.
2. Document the choice with citations to both sources.
3. Log the choice as a House Policy instance within the appropriate trigger family.
4. Make the choice player-inspectable.

### Principle 3: "Broken" Interactions Are RAW

The Locate City Nuke, simulacrum army, and other exploit chains are legal under RAW (debatably). The No-Opaque-DM doctrine means the system cannot refuse to execute a legal combination because it "seems wrong." If an interaction is truly problematic, the PO creates a House Policy banning it — explicitly, logged, and inspectable. The system never silently refuses.

### Principle 4: Scope Discipline Protects Against Complexity Explosion

Polymorph alone generates more RAW ambiguity than all other subsystems combined. The decision to keep polymorph out of v1 scope (spells levels 0-5, no polymorph) was correct. When polymorph enters scope, it will need its own dedicated research question equivalent to RQ-BOX-002.

---

## 9. Recommendations

### For RQ-BOX-002 (RAW Silence Catalog)

Add SIL-007 through SIL-010 to the catalog. SIL-007 (PHB vs DMG sunder contradiction) is the highest-priority finding because it affects every magic item in the game and has no clean RAW resolution.

### For RQ-BOX-003 (Object Identity Model)

Community debates on object destruction state ("ruined" = what?) reinforce the need for the Object Identity Model. SIL-010 should be cross-referenced as a second data point alongside SIL-004 (object identity under damage).

### For Template Family Registry (future)

The sunder subsystem will require a design-time decision on the PHB vs DMG contradiction before any trigger family involving object damage can be finalized. Recommend: adopt PHB numbers (+2 hardness/+10 HP per enhancement) as the more internally consistent and better-playtested values. Document as a House Policy with citations to both sources.

### For Future Scope Expansion

When the following enter scope, they each warrant dedicated research:
- **Polymorph/Wild Shape** — equipment melding, form stacking, component access
- **Simulacrum** — level percentage, spellcasting, infinite loop, entity identity
- **Grapple edge cases** — square threatening, Flurry in grapple, TWF in grapple

---

## 10. Sources

Community discussions surveyed:
- EN World: [Magic Item Hardness/HP](https://www.enworld.org/threads/3-5-so-just-what-is-the-hardness-hp-of-a-magic-item.58475/)
- EN World: [GMW and Sunder](https://www.enworld.org/threads/3-0-3-5-gmw-and-sunder.59619/)
- EN World: [Thoughts on Sunder](https://www.enworld.org/threads/3-5-thoughts-on-sunder.58618/)
- EN World: [Polymorph Item Melding](https://www.enworld.org/threads/3-5-alter-self-polymorph-wild-shape-confusion-which-items-meld-which-dont.58022/)
- EN World: [Simulacrum Spellcasting](https://www.enworld.org/threads/can-a-simulacrum-cast-spells.43111/)
- EN World: [Simulacrum Crafting](https://www.enworld.org/threads/can-a-simulacrum-craft-for-you.307150/)
- Giant in the Playground: [Grapple Confusion](https://forums.giantitp.com/archive/index.php/t-203379.html)
- D&D Wiki: [Better Sunder Rules Variant](https://broken.dnd-wiki.org/w/index.php?title=Better_Sunder_Rules_(3.5e_Variant_Rule))
- D&D Wiki: [SRD Sunder](https://www.dandwiki.com/wiki/SRD:Sunder)
- D&D Wiki: [SRD Breaking and Entering](https://www.dandwiki.com/wiki/SRD:Breaking_and_Entering)
- MinMaxForum: [Monk Unarmed Strike](https://minmaxforum.com/index.php?topic=84.0)
- MinMaxForum: [Complete Polymorph Thread](https://minmaxforum.com/index.php?topic=519.0)
- D&D Wiki: [3.5e Exploits Variant Rule](https://dnd-wiki.org/wiki/Exploits_(3.5e_Variant_Rule))
- TV Tropes: [GameBreaker D&D 3rd Edition](https://tvtropes.org/pmwiki/pmwiki.php/GameBreaker/DungeonsAndDragonsThirdEdition)

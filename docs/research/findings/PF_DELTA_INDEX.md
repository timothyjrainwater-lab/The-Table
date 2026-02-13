# Pathfinder 1e Delta Index: 3.5e Mechanics Changed by Paizo

**Document ID:** RQ-BOX-002-PF
**Domain:** Box Layer -- House Policy Governance
**Status:** V1 COMPLETE
**Filed:** 2026-02-12
**Author:** Research Agent (Opus)
**Authority:** Pathfinder 1e Core Rulebook (2009), Pathfinder SRD
**Source Authority Level:** EXTERNAL_EVIDENCE (Priority 7 per RESEARCH_FINDING_SCHEMA)

---

## Purpose

Pathfinder 1e was a direct revision of D&D 3.5e's System Reference Document. Every mechanical change Paizo made is evidence of a failure mode in 3.5e -- a silence, an ambiguity, a contradiction, or a balance issue that caused enough table-level pain that Paizo invested design effort to fix it.

This index catalogs those changes within the AIDM v1 scope and maps each to the 3.5e problem it evidences. The resulting catalog serves as a prioritized roadmap for House Policy template design: if Paizo thought it was worth fixing, AIDM's deterministic engine almost certainly needs a policy for it.

**Scope constraints:** Core combat, equipment, spells 0-5, environment/objects, mounted combat, grid movement, combat maneuvers. Excludes polymorph, wild shape, prestige classes, epic levels, spells 6+, class redesigns (unless they affect core combat).

---

## Methodology

This analysis draws on the Pathfinder 1e Core Rulebook and its SRD, compared against the D&D 3.5e PHB, DMG, and MM. Where web search was unavailable, findings are drawn from the author's training knowledge of both systems. All mechanical claims are verifiable against the Pathfinder SRD (d20pfsrd.com) and the D&D 3.5e SRD (d20srd.org).

Each delta is cross-referenced against the existing AIDM silence catalog (RQ-BOX-002) where applicable.

---

## Delta Catalog

---

### PF-DELTA-0001: Unified Combat Maneuver System (CMB/CMD)

**3.5e Mechanic:**
Grapple, trip, bull rush, disarm, overrun, and sunder each use a different resolution mechanic. Grapple uses a special "grapple check" (BAB + Str + special size modifier). Trip uses a touch attack followed by an opposed Strength/Dex check. Disarm uses opposed attack rolls with weapon-dependent modifiers. Bull rush uses opposed Strength checks. Sunder uses opposed attack rolls. Each maneuver has its own unique size modifier scale, its own AoO provocation rules, and its own counter-attack mechanic. PHB p.154-160.

**Pathfinder Change:**
All combat maneuvers resolve through a single unified system. Combat Maneuver Bonus (CMB) = BAB + Str modifier + size modifier. Combat Maneuver Defense (CMD) = 10 + BAB + Str modifier + Dex modifier + size modifier + miscellaneous modifiers. To perform any combat maneuver, roll d20 + CMB against the target's CMD. Success means the maneuver works; failure by 10 or more on a trip or overrun means the attacker is knocked prone. One formula, one defense value, consistent across all maneuvers.

**Category:** MANEUVERS

**3.5e Problem Evidenced:**
Six different resolution subsystems for conceptually similar actions created enormous cognitive load, inconsistent balance, and frequent rules errors at the table. The grapple flowchart alone was a notorious source of confusion. Different size modifier scales for grapple vs. other maneuvers created silent inconsistency. The lack of a unified "defense against maneuvers" value meant that some creatures were accidentally immune to certain maneuvers while trivially vulnerable to others.

**Silence Type:** AMBIGUOUS + BALANCE_ISSUE
The individual systems each work, but their inconsistency means a DM must memorize six separate resolution paths, and the balance between them is uneven (grapple was far more powerful than disarm at most levels).

**Relevant SIL:** SIL-009 (Grapple Square Threatening) -- Pathfinder's unified system also clarifies that grappled creatures do not threaten.

**Relevance to AIDM:**
CP-18 already documents the complexity of implementing six separate maneuver subsystems. The Pathfinder delta confirms that the 3.5e approach is problematic enough to warrant redesign. AIDM should consider whether its House Policy layer needs a unifying principle for maneuver resolution even while implementing RAW 3.5e, particularly for edge cases where the six subsystems interact (e.g., can you trip someone you're grappling?). The CMB/CMD model also demonstrates that a single defense value against maneuvers is viable.

---

### PF-DELTA-0002: Grapple Simplified to Non-Relational Model

**3.5e Mechanic:**
Grapple creates a bidirectional state: both attacker and defender gain the "grappled" condition. The grappler must maintain the grapple each round with opposed checks. The grappled creature can attempt escape (opposed grapple or Escape Artist), deal damage, pin the opponent, draw a light weapon, or attempt to cast a spell (Concentration DC 20 + spell level). Moving while grappling requires a grapple check. Multiple creatures can join a grapple. PHB p.155-157.

**Pathfinder Change:**
Grapple still creates conditions on both parties, but the resolution is dramatically simplified. Initiating a grapple is a standard CMB check vs CMD. Maintaining is a CMB check (at +5 bonus) as a standard action. The grappled condition gives -4 Dex and -2 to attack rolls and CMB checks (except to maintain or escape). Moving a grappled foe requires a second CMB check. The pin is a separate CMB check (not an automatic progression). Escape is a CMB or Escape Artist check vs the grappler's CMD. Critically, the condition effects are explicit and enumerated rather than scattered across half a page of nested rules.

**Category:** MANEUVERS

**3.5e Problem Evidenced:**
The 3.5e grapple system is the single most complained-about subsystem in the edition. Its multi-round state machine creates cascading complexity: who threatens whom, what actions are available, how movement works, how third parties interact with the grapple, what happens when sizes change mid-grapple. The bidirectional state dependency (attacker's condition depends on defender's state and vice versa) is the architectural pattern the AIDM project has formally identified as G-T3C (Relational Conditions).

**Silence Type:** AMBIGUOUS
RAW provides rules for grapple, but the rules are so dense and interrelated that community consensus was never achieved on several key interactions (e.g., can a grappled creature make AoOs? Does a grappled creature threaten?).

**Relevant SIL:** SIL-009 (Grapple Square Threatening)

**Relevance to AIDM:**
CP-18 already implements "Grapple-Lite" (unidirectional, no pin, no escape loop) specifically because full grapple crosses G-T3C. The Pathfinder delta confirms this was the right architectural call -- even Paizo, with unlimited design resources, significantly simplified grapple. When AIDM eventually opens G-T3C for full grapple, the Pathfinder model should be studied as a reference for how to implement bidirectional grapple state without the 3.5e complexity.

---

### PF-DELTA-0003: Sunder as Damage-Dealing Maneuver with Broken Condition

**3.5e Mechanic:**
Sunder uses opposed attack rolls (attacker vs. defender). If the attacker wins, they roll damage against the item. Item takes damage minus hardness. If the item reaches 0 HP, it is "destroyed" (DMG p.61 says "ruined"). There is no intermediate state between "fully functional" and "destroyed." PHB p.158-159, DMG p.61.

**Pathfinder Change:**
Sunder is now a CMB check vs CMD. Damage is dealt to the item directly (no opposed roll for whether you "hit" the item -- you always deal damage if CMB beats CMD). Critically, Pathfinder introduces the **Broken condition**: when an object reaches half its total HP, it gains the broken condition. Broken weapons take a -2 penalty to attack and damage rolls and their critical threat range is halved. Broken armor has its AC bonus halved. Broken tools have a -2 penalty to checks. Broken wands/staves use twice as many charges per use. This creates a meaningful intermediate state between "works perfectly" and "destroyed."

**Category:** EQUIPMENT + COMBAT

**3.5e Problem Evidenced:**
The binary functional/destroyed model for objects means sunder is either completely useless (can't get through hardness in time to matter) or instantly devastating (destroyed the enemy's primary weapon). There is no middle ground for tactical play. Additionally, the lack of an intermediate state means there is no mechanical incentive for partial damage to objects -- you either commit to full destruction or the damage means nothing.

**Silence Type:** SILENT + BALANCE_ISSUE
3.5e is SILENT on what happens between "undamaged" and "destroyed." It is also a BALANCE_ISSUE because the all-or-nothing model makes sunder a rarely-used gamble.

**Relevant SIL:** SIL-004 (Object Identity Under Damage), SIL-010 (Object Physical State After HP Reaches Zero)

**Relevance to AIDM:**
CP-18 already identifies sunder as DEGRADED (narrative only, no persistent item state). The Pathfinder Broken condition provides a tested design pattern for the intermediate state AIDM will eventually need. When the item HP kernel is implemented, adopting a Broken-equivalent condition is strongly recommended. This also informs RQ-BOX-003 (Object Identity Model) -- the Broken condition is evidence that objects need states beyond binary.

---

### PF-DELTA-0004: Enhancement Bonus to Object Hardness and HP (Unified Formula)

**3.5e Mechanic:**
PHB p.165 states each +1 enhancement bonus adds +2 hardness and +10 HP. DMG p.222 states each +1 adds +2 hardness and +10 HP for weapons and shields, but the text on the same page is interpreted by some as +1 hardness and +1 HP. Armor is potentially excluded from the DMG table entirely. These two books contradict each other or, at minimum, create enough ambiguity that community consensus never formed.

**Pathfinder Change:**
Pathfinder establishes a clear, unified rule: each +1 enhancement bonus adds +2 hardness and +10 HP to the item. This applies to weapons, armor, and shields equally. No exceptions, no contradictions between sourcebooks.

**Category:** EQUIPMENT + OBJECTS

**3.5e Problem Evidenced:**
This is a documented CONTRADICTORY silence in the AIDM catalog. The PHB and DMG give different numbers, and armor is arguably omitted from the DMG table entirely. This contradiction affects every single magic weapon, armor, and shield in the game and has massive downstream effects on the viability of sunder as a combat tactic.

**Silence Type:** CONTRADICTORY

**Relevant SIL:** SIL-007 (Magic Item Enhancement Bonus to Hardness/HP), SIL-008 (Armor Enhancement Bonus Exclusion)

**Relevance to AIDM:**
SIL-007 and SIL-008 are already cataloged as needing House Policy resolution. The Pathfinder delta provides strong evidence for adopting the PHB formula (+2 hardness, +10 HP per +1) as the House Policy, since Paizo's playtest confirmed this was the intended and balanced interpretation. This should be documented as a HIGH-PRIORITY House Policy decision because it affects the entire sunder subsystem.

---

### PF-DELTA-0005: AoO Provocation Consolidated and Clarified

**3.5e Mechanic:**
AoO provocation is defined in a table (PHB Table 8-2) plus scattered text throughout the combat chapter. Different maneuvers provoke from different sources: bull rush provokes from "everyone" including the target; grapple provokes from the target only; trip provokes from the target only. The table and the maneuver-specific text occasionally diverge. Whether ranged attacks provoke when you're not threatening anyone is debatable. Whether "moving through" a threatened square provokes once or per square is unclear in edge cases.

**Pathfinder Change:**
Pathfinder consolidates AoO provocation into a clearer structure. All combat maneuvers provoke AoOs from the target of the maneuver (unless you have the relevant Improved feat). Movement provokes when you leave a threatened square (not when you enter one -- Pathfinder's language is more precise on this point). The Improved [Maneuver] feats are unified: each one prevents the AoO that the base maneuver would provoke from the defender AND grants a +2 bonus to the CMB check.

**Category:** COMBAT

**3.5e Problem Evidenced:**
The inconsistency in which maneuvers provoke from whom, combined with Table 8-2's occasionally ambiguous entries, creates frequent table disputes. "Does bull rush provoke from everyone or just the target?" is a common argument. The answer (everyone, including the target) is RAW but counterintuitive and easily missed.

**Silence Type:** AMBIGUOUS
Rules exist but their distribution across table, paragraph text, and individual maneuver descriptions makes consistent application difficult.

**Relevant SIL:** NONE (CP-15 already handles AoO resolution correctly, but the provocation trigger list is a known maintenance burden)

**Relevance to AIDM:**
CP-15's AoO trigger detection layer must correctly encode which maneuvers provoke and from whom. The Pathfinder delta provides evidence that the 3.5e trigger list is confusing enough to warrant a clear, centralized provocation table in AIDM's implementation. Consider documenting the provocation rules as a single truth table rather than distributing them across maneuver-specific code.

---

### PF-DELTA-0006: Attacks of Opportunity -- Combat Reflexes and Flat-Footed Clarification

**3.5e Mechanic:**
A flat-footed creature cannot make attacks of opportunity (PHB p.137). Combat Reflexes allows additional AoOs per round equal to Dex modifier. Whether a flat-footed creature with Combat Reflexes can make AoOs is debated: the feat says "you may also make attacks of opportunity while flat-footed," but the core rule says flat-footed creatures cannot make AoOs. Interaction is unclear.

**Pathfinder Change:**
Pathfinder explicitly states in the Combat Reflexes feat description: "This feat also allows you to make attacks of opportunity while flat-footed." The base rule still prohibits flat-footed AoOs, but the feat creates an explicit exception. No ambiguity.

**Category:** COMBAT

**3.5e Problem Evidenced:**
The interaction between a general prohibition (flat-footed = no AoOs) and a feat-granted exception (Combat Reflexes implies flat-footed AoOs are possible) is a classic "specific beats general" case, but the 3.5e text is ambiguous enough that community debate existed.

**Silence Type:** AMBIGUOUS

**Relevant SIL:** NONE

**Relevance to AIDM:**
CP-15 defers Combat Reflexes to future work. When implementing it, AIDM must decide the flat-footed AoO interaction. The Pathfinder delta confirms the intended design: Combat Reflexes grants flat-footed AoO capability. This should be documented as a preemptive House Policy decision.

---

### PF-DELTA-0007: Standing from Prone Provokes AoO

**3.5e Mechanic:**
PHB Table 8-2 lists "Move" as provoking an AoO. Standing from prone is described as a move action (PHB p.142). Whether standing from prone provokes an AoO is technically derivable from the table (it's a "move" action in a threatened area) but is not explicitly listed in the table's examples. Community disagreement existed.

**Pathfinder Change:**
Pathfinder explicitly lists "Stand up from prone" in its AoO provocation table as a provoking action. No ambiguity. This makes the trip maneuver more powerful because a tripped creature must risk an AoO to stand back up.

**Category:** COMBAT + MOVEMENT

**3.5e Problem Evidenced:**
The omission of "stand from prone" from the explicit provocation list, while it's technically implied by the broader "move action in threatened area" rule, creates a gap that tables disagree on. This directly affects the tactical value of the Trip maneuver.

**Silence Type:** AMBIGUOUS (implied but not explicit)

**Relevant SIL:** NONE

**Relevance to AIDM:**
CP-18 implements Trip, which applies the Prone condition. The action economy of recovering from Prone (and whether it provokes) directly affects Trip's tactical value. AIDM should explicitly encode standing-from-prone as an AoO-provoking action in the CP-15 trigger table, matching both RAW interpretation and Pathfinder's explicit confirmation.

---

### PF-DELTA-0008: Cantrips (0-Level Spells) Become At-Will

**3.5e Mechanic:**
Cantrips (0-level spells) consume spell slots like any other spell. A 1st-level wizard has three 0-level slots per day. Once used, cantrips are expended until rest. This makes cantrips a limited resource that must be carefully allocated.

**Pathfinder Change:**
Cantrips can be cast an unlimited number of times per day. Prepared casters prepare their cantrips as normal but do not expend them when cast. Spontaneous casters know a fixed number of cantrips and can cast them at will.

**Category:** SPELLS

**3.5e Problem Evidenced:**
The scarcity of 0-level spell slots meant that trivial utility magic (detect magic, light, prestidigitation, mending) competed with each other for limited daily resources. At low levels, a wizard who cast light and detect magic had already spent 2 of 3 cantrip slots. This pushed casters toward mundane solutions for trivial problems (carrying a torch instead of casting light), which undermined the class fantasy and created unnecessary bookkeeping.

**Silence Type:** BALANCE_ISSUE

**Relevant SIL:** NONE

**Relevance to AIDM:**
AIDM implements 3.5e RAW, so cantrips remain limited. However, the Pathfinder delta highlights that cantrip slot tracking is a pain point. The AIDM engine must correctly track 0-level slot expenditure, but the Session Zero configuration might offer a House Policy option for "unlimited cantrips" as a common variant rule. The mending cantrip is particularly relevant because unlimited mending would fundamentally change the object repair economy (see SIL-004, SIL-010).

---

### PF-DELTA-0009: Mending Repairs More Damage

**3.5e Mechanic:**
Mending (0-level transmutation) repairs 1d4 points of damage to an object. It can repair one break in a metallic object (like a ring, chain link, or sword) as long as the break is no larger than 1 foot. It cannot restore magic to a magic item. PHB p.253.

**Pathfinder Change:**
Mending repairs 1d4 points of damage to an object. However, combined with the at-will cantrip change (PF-DELTA-0008), mending can now be cast unlimited times. Pathfinder also adds the clause: "If the object has the broken condition, this condition is removed if the object is restored to at least half its original hit points." This ties mending directly into the Broken condition (PF-DELTA-0003).

**Category:** SPELLS + OBJECTS

**3.5e Problem Evidenced:**
In 3.5e, mending's 1d4 repair is so small that it's nearly useless for combat-relevant repair (a longsword has 5 HP and 10 hardness). Combined with limited cantrip slots, mending is a waste of a spell slot. Conversely, if mending were unlimited and objects had an intermediate "broken" state, it would become a meaningful out-of-combat repair tool. The 3.5e version falls into a dead zone: too weak to matter but consuming a resource that could be used for something better.

**Silence Type:** BALANCE_ISSUE

**Relevant SIL:** SIL-004 (Object Identity Under Damage), SIL-010 (Object Physical State After HP Reaches Zero)

**Relevance to AIDM:**
When AIDM implements the object HP kernel, the interaction between mending and object state must be carefully designed. The Pathfinder model (unlimited mending + Broken condition threshold) provides a tested framework. Under 3.5e RAW, mending is limited and there's no broken condition, so repair magic is mostly irrelevant to gameplay. House Policy may need to address: "How many times can mending be cast on the same object? Can mending restore a 'destroyed' object?"

---

### PF-DELTA-0010: Object Hardness and HP Table Revised

**3.5e Mechanic:**
Object hardness and HP are defined in DMG p.61 (Table 9-11 for substance hardness, Table 9-12 for object HP by size/material). Specific object examples have hardness and HP scattered across the DMG. The tables are adequate but sparse -- many common objects (rope, glass, ceramic, leather) have ambiguous or missing entries.

**Pathfinder Change:**
Pathfinder provides a significantly expanded object hardness and HP table. Key additions and changes:
- Glass: Hardness 1 (was unlisted in 3.5e DMG table)
- Rope: Hardness 0, 2 HP per inch (3.5e only listed it in the "special" section)
- Ice: Hardness 0, 3 HP per inch (not in 3.5e)
- Leather/hide: Hardness 2 (not in 3.5e object table)
- Common objects table expanded with doors, chests, manacles, etc.
- Energy attacks deal half damage to most objects (explicit rule)

**Category:** OBJECTS + ENVIRONMENT

**3.5e Problem Evidenced:**
The sparse 3.5e table forces DMs to improvise hardness and HP for common objects. "What's the hardness of a rope?" is a question that arises frequently (cutting bonds, destroying a bridge rope, etc.) but has no clear entry in the DMG table. The lack of explicit rules for energy damage vs. objects creates ambiguity about fireball vs. wooden door.

**Silence Type:** SILENT (missing entries) + AMBIGUOUS (energy damage)

**Relevant SIL:** SIL-002 (Structural Load-Bearing -- related to object property gaps)

**Relevance to AIDM:**
The AIDM engine needs deterministic hardness and HP values for any object that might be targeted by sunder, spells, or environmental damage. The expanded Pathfinder table should be used as a reference when building AIDM's object property database. House Policy should explicitly adopt hardness/HP values for the objects Pathfinder added (rope, glass, leather, ice) rather than leaving them to ad-hoc DM fiat.

---

### PF-DELTA-0011: Energy Damage vs. Objects Explicitly Halved

**3.5e Mechanic:**
The 3.5e rules state that energy attacks (fire, cold, etc.) deal damage to objects, but the rules for how much are scattered and inconsistent. DMG p.61 says objects take half damage from ranged attacks and most energy attacks. But the exact list of which energy types deal half damage and which deal full damage is not clearly enumerated. Fire vs. flammable objects is addressed but fire vs. stone is not explicit.

**Pathfinder Change:**
Pathfinder states explicitly: "Energy attacks deal half damage to most objects. Divide the damage dealt by 2 before applying the object's hardness." It then lists exceptions: fire deals full damage to paper, cloth, and similar flammable materials. Cold deals full damage to objects made of ice. Acid deals full damage to objects that are vulnerable to acid (DM discretion on what qualifies).

**Category:** ENVIRONMENT + OBJECTS

**3.5e Problem Evidenced:**
The 3.5e rule that objects take half damage from "most energy attacks" is vague. Does a fireball deal half damage to a wooden door? Full damage because wood is flammable? The interaction between energy types and material vulnerabilities is left almost entirely to DM adjudication.

**Silence Type:** AMBIGUOUS

**Relevant SIL:** NONE (but related to the ENVIRONMENTAL_INTERACTION trigger family)

**Relevance to AIDM:**
CP-20 (Environmental Damage) and future spell implementations will need clear rules for energy damage vs. objects. The Pathfinder "half damage, divide before hardness" rule is a clean, deterministic formula that AIDM should consider adopting as a House Policy. The exception list (flammable = full fire damage, ice = full cold damage) is straightforward and covers the common cases.

---

### PF-DELTA-0012: Damage Reduction Unified Notation (DR X/Type)

**3.5e Mechanic:**
Damage Reduction in 3.5e uses the notation DR X/material-or-alignment (e.g., DR 10/cold iron, DR 5/magic, DR 10/evil). The rules for what overcomes DR are distributed across the Monster Manual entries. DR X/-- means nothing overcomes it. The interaction between multiple DR types (e.g., a creature with DR 10/cold iron and DR 5/magic) and weapons that satisfy one or both conditions is not clearly specified.

**Pathfinder Change:**
Pathfinder keeps the same notation but adds explicit stacking/overlap rules: "If a creature has damage reduction from more than one source, the two forms of damage reduction do not stack. Instead, the creature gets the benefit of the best damage reduction in a given situation." This explicit non-stacking rule resolves the most common source of DR confusion.

**Category:** COMBAT

**3.5e Problem Evidenced:**
When a creature has multiple DR entries (common for outsiders and high-level monsters), the interaction is unclear. Does a Pit Fiend with DR 15/good and silver take 15 less from a +5 holy cold iron weapon, or does each DR apply separately? The rules do not clearly specify, and community interpretations varied.

**Silence Type:** AMBIGUOUS

**Relevant SIL:** NONE

**Relevance to AIDM:**
AIDM's damage computation pipeline must handle DR correctly. When multiple DR values apply, the engine needs a deterministic rule for which applies. The Pathfinder "best in situation" rule is the most common community interpretation of 3.5e as well, and should be adopted as the Box resolver decision.

---

### PF-DELTA-0013: Conditions Enumerated as Formal Game Terms

**3.5e Mechanic:**
The 3.5e PHB has an appendix of conditions (PHB p.306-310), but the conditions are not always consistently referenced in the combat rules. The grappled condition's effects are primarily described within the grapple section (PHB p.155-157) rather than in the conditions appendix. Some conditions have effects distributed across multiple rule sections. The "flat-footed" condition's interaction with various abilities is implied rather than enumerated.

**Pathfinder Change:**
Pathfinder provides a significantly expanded and formalized conditions appendix. Each condition has a complete, self-contained description of all its mechanical effects. The grappled condition explicitly lists: cannot move, -4 Dex, -2 attack rolls, -2 CMB (except to grapple), concentration check to cast spells, cannot take AoOs. Flat-footed explicitly lists: cannot take AoOs, loses Dex bonus to AC and CMD. No cross-referencing required.

**Category:** COMBAT + MANEUVERS

**3.5e Problem Evidenced:**
The distributed nature of condition effects in 3.5e means that looking up "what does grappled do?" requires reading the grapple section, the conditions appendix, and potentially the AoO rules. This distribution creates inconsistency and makes it easy to miss effects.

**Silence Type:** AMBIGUOUS (effects exist but are scattered, making complete enumeration error-prone)

**Relevant SIL:** SIL-009 (Grapple Square Threatening -- a direct consequence of scattered condition effects)

**Relevance to AIDM:**
CP-16 implements the conditions system. The Pathfinder model of self-contained condition definitions is the correct architectural pattern for AIDM's deterministic engine. Each condition should enumerate ALL its mechanical effects in one place, with no implicit effects derived from other rule sections. This is already the design intent in CP-16 but the Pathfinder delta provides external validation.

---

### PF-DELTA-0014: Charge Action Clarified (Path and AoO)

**3.5e Mechanic:**
A charge requires moving at least 10 feet in a straight line toward the target. The charger must have a clear path (no difficult terrain, no obstacles, no allies blocking). The charge provokes AoOs from threatened squares moved through (not from the target, who is the recipient of the attack). PHB p.154. Whether "straight line" means exact diagonal/straight or within certain angular tolerance is debated. Whether the charger can take a 5-foot step before charging is unclear.

**Pathfinder Change:**
Pathfinder clarifies that the charge must be in a "straight line" but allows the charger to move through squares occupied by allies (with the ally's consent, treating them as non-blocking). The path must still be clear of obstacles and difficult terrain. Pathfinder explicitly states you cannot take a 5-foot step in the same round you charge. The charge provokes AoOs normally from movement through threatened squares.

**Category:** COMBAT + MOVEMENT

**3.5e Problem Evidenced:**
The "straight line" requirement and the interaction with allies in the path created arguments at tables. A fighter trying to charge past an allied rogue to reach the enemy wizard was a common scenario with no clear RAW answer. Whether 5-foot step + charge was legal was another frequent debate (it's not, but the rules don't say so directly).

**Silence Type:** AMBIGUOUS

**Relevant SIL:** NONE

**Relevance to AIDM:**
When AIDM implements charge mechanics (part of bull rush integration and general melee), the path legality check must have clear, deterministic rules for what constitutes a valid charge path. The Pathfinder clarifications on ally pass-through and 5-foot step prohibition should inform AIDM's implementation or House Policy.

---

### PF-DELTA-0015: Diagonal Movement Cost Clarified

**3.5e Mechanic:**
Diagonal movement alternates between 5-foot cost and 10-foot cost (first diagonal = 5 ft, second diagonal = 10 ft, repeating). PHB p.147. However, the rules for how this alternation interacts with difficult terrain, multiple movement modes in a single turn, and movement across round boundaries are not fully specified. Does the alternation reset between rounds? Between movement modes?

**Pathfinder Change:**
Pathfinder keeps the alternating 5/10 diagonal cost but clarifies that the count resets at the start of each turn. It also explicitly states that in difficult terrain, the diagonal cost doubles (so the alternation becomes 10/20 instead of 5/10). This removes the ambiguity about persistent diagonal counting.

**Category:** MOVEMENT

**3.5e Problem Evidenced:**
The alternating diagonal cost is a source of minor but persistent confusion. Does a creature that moved one diagonal last round start this round with the "expensive" diagonal? Most tables assume the count resets per round, but RAW doesn't explicitly say so.

**Silence Type:** SILENT (on reset behavior)

**Relevant SIL:** NONE

**Relevance to AIDM:**
The AIDM movement system must implement diagonal costing. The Pathfinder per-turn reset rule should be adopted (it matches the most common interpretation of 3.5e RAW). The difficult terrain interaction (doubled diagonal cost) should also be explicitly encoded.

---

### PF-DELTA-0016: Cover and Concealment from Creatures Formalized

**3.5e Mechanic:**
Creatures can provide cover to other creatures ("soft cover"). PHB p.150-151 describes cover generally but does not clearly define when a creature provides cover vs. concealment to an adjacent ally. The rules for shooting through occupied squares are addressed, but the mechanical distinction between a creature providing cover (+4 AC) vs. just being in the way is fuzzy.

**Pathfinder Change:**
Pathfinder explicitly defines "soft cover": a creature between you and an enemy provides soft cover to the enemy (+4 AC bonus). Soft cover does NOT allow you to attempt a Stealth check (unlike regular cover). This distinction clarifies that creatures provide the AC bonus of cover but not the hiding benefit, resolving a common table dispute.

**Category:** COMBAT

**3.5e Problem Evidenced:**
The interaction between creature positioning and cover/concealment is a frequent tactical question. Can a halfling hide behind a human ally? Does the human ally provide cover for Reflex saves? The 3.5e rules don't clearly distinguish "creature-provided cover" from "object-provided cover."

**Silence Type:** AMBIGUOUS

**Relevant SIL:** NONE

**Relevance to AIDM:**
CP-19 implements the cover system. The soft cover distinction (AC bonus but no hiding) should be encoded as a separate cover type in AIDM's cover resolution. This is a deterministic question: given creature positions, what cover exists? The Pathfinder model provides a clean answer.

---

### PF-DELTA-0017: Trip No Longer Requires Touch Attack

**3.5e Mechanic:**
Trip requires a melee touch attack to initiate, followed by an opposed Strength/Dexterity check. This two-step process means trip has two failure points: miss the touch attack, or lose the opposed check. PHB p.158-160.

**Pathfinder Change:**
Trip is now a single CMB check vs CMD. No touch attack required. This means trip has exactly one roll that determines success or failure, dramatically simplifying the resolution.

**Category:** MANEUVERS

**3.5e Problem Evidenced:**
The two-step trip resolution (touch attack + opposed check) creates awkward probability curves. A high-BAB fighter can reliably hit the touch attack but might lose the opposed check; a low-BAB rogue might miss the touch attack entirely. The touch attack step adds mechanical overhead without adding meaningful tactical depth -- it's just an extra failure point.

**Silence Type:** BALANCE_ISSUE

**Relevant SIL:** NONE

**Relevance to AIDM:**
CP-18 implements trip with the 3.5e two-step resolution (touch attack + opposed check). The Pathfinder delta suggests this is a balance pain point. AIDM must implement 3.5e RAW, but this is a candidate for a House Policy variant (single-check trip) if the PO decides the balance cost is unacceptable.

---

### PF-DELTA-0018: Bull Rush No Longer Provokes from Everyone

**3.5e Mechanic:**
Bull rush provokes AoOs from ALL threatening creatures, including the defender (PHB p.154). This means a bull rush attempt through a crowd can trigger multiple AoOs before the bull rush even resolves, making it extremely dangerous in melee-heavy situations.

**Pathfinder Change:**
Bull rush (like all combat maneuvers) provokes an AoO from the defender only, and this AoO is suppressed by the Improved Bull Rush feat. The change to CMB/CMD means bull rush no longer provokes from bystanders -- only from the target.

**Category:** MANEUVERS + COMBAT

**3.5e Problem Evidenced:**
The "provokes from everyone" rule for bull rush makes it unusable in most real combat scenarios where multiple enemies are adjacent. A fighter trying to bull rush an orc off a cliff while two other orcs are in melee range takes 2-3 AoOs before the bull rush even resolves. This makes bull rush a trap option in the most common combat configurations.

**Silence Type:** BALANCE_ISSUE

**Relevant SIL:** NONE

**Relevance to AIDM:**
CP-18 currently implements bull rush with AoOs from all threatening enemies (3.5e RAW). The Pathfinder change is evidence that this makes bull rush too risky. AIDM implements RAW, but this should be flagged as a potential House Policy candidate if playtesting reveals that bull rush is never used.

---

### PF-DELTA-0019: Disarm Counter-Attack Cannot Escalate

**3.5e Mechanic:**
If a disarm attempt fails, the defender may immediately attempt to disarm the attacker as a free action. If THAT fails, the rules do not explicitly say whether the original attacker gets another counter-disarm attempt, creating a potential infinite loop. PHB p.155.

**Pathfinder Change:**
Pathfinder explicitly states that if you fail a disarm attempt, the target cannot attempt to disarm you in return. The counter-disarm mechanic is entirely removed. Failure simply means the attempt failed with no retaliation (beyond the standard AoO).

**Category:** MANEUVERS

**3.5e Problem Evidenced:**
The counter-disarm mechanic in 3.5e creates a potential infinite recursion problem. While most tables interpret it as "one counter only," the RAW text does not explicitly limit the chain. Additionally, the counter-disarm is a free action with no limit on the number of free actions per round (see Community Debates Catalog entry #43 on free action limits).

**Silence Type:** AMBIGUOUS (recursion not explicitly bounded)

**Relevant SIL:** NONE (but related to "free action limits" debate, Entry #43 in Community Debates Catalog)

**Relevance to AIDM:**
CP-18 implements disarm with a single counter-disarm (no follow-up). The Pathfinder delta confirms this is the right call -- even removing the counter entirely. AIDM's implementation should hard-code a maximum recursion depth of 1 for counter-maneuvers (apply to both disarm and trip counter-trip).

---

### PF-DELTA-0020: Overrun Defender Avoidance Simplified

**3.5e Mechanic:**
When you attempt to overrun, the defender can choose to "avoid" you (step aside) or "block" you (force the opposed check). This requires player/NPC input during another creature's turn, creating an interactive prompt in a system that otherwise resolves sequentially. PHB p.157-158.

**Pathfinder Change:**
Pathfinder removes the defender's choice to avoid. Overrun always resolves with a CMB vs CMD check. If the attacker has Improved Overrun, the defender additionally cannot avoid (redundant since avoidance is already removed, but the feat remains for the +2 CMB bonus and AoO suppression).

**Category:** MANEUVERS

**3.5e Problem Evidenced:**
The defender avoidance choice creates an out-of-turn decision point that requires either player input (breaking the sequential action model) or AI/DM adjudication. This is the exact "interactive input during resolution" anti-pattern that AIDM's deterministic architecture seeks to avoid.

**Silence Type:** BALANCE_ISSUE (not a RAW failure, but a design pattern that conflicts with deterministic resolution)

**Relevant SIL:** NONE

**Relevance to AIDM:**
CP-18 already flags overrun defender avoidance as DEGRADED (controlled by AI/doctrine rather than player input). The Pathfinder delta confirms this is a known problem -- Paizo removed the mechanic entirely. AIDM should document this as a Box resolver decision: overrun always resolves with an opposed check, no avoidance option.

---

### PF-DELTA-0021: Shield Bonus to Touch AC Against Combat Maneuvers

**3.5e Mechanic:**
Touch AC excludes armor and shield bonuses (PHB p.136). Combat maneuvers that target touch AC (grapple's touch attack, trip's touch attack) therefore ignore the defender's shield entirely. A fighter with a tower shield is just as easy to grab as a wizard in robes, as far as the touch attack step is concerned.

**Pathfinder Change:**
CMD (Combat Maneuver Defense) includes shield bonus, armor bonus, and all other AC modifiers. Since CMB checks replace touch attacks for combat maneuvers, shields now contribute to resisting grapple, trip, and other maneuvers. A fighter with a shield is harder to grab than a wizard without one.

**Category:** EQUIPMENT + MANEUVERS

**3.5e Problem Evidenced:**
The exclusion of shield from touch AC for maneuver resolution creates a counterintuitive result: a shield -- a defensive tool specifically designed to deflect and block -- provides zero benefit against being grabbed, tripped, or bull rushed. This makes heavy shield investment strategically questionable against maneuver-focused opponents.

**Silence Type:** BALANCE_ISSUE

**Relevant SIL:** NONE

**Relevance to AIDM:**
When AIDM resolves combat maneuvers, the touch AC step excludes shield bonus per 3.5e RAW. The Pathfinder delta is evidence that this feels wrong to players and DMs. A House Policy variant that includes shield bonus in maneuver defense could be offered at Session Zero. This is low-priority but worth documenting for completeness.

---

### PF-DELTA-0022: Aid Another in Combat Standardized

**3.5e Mechanic:**
The Aid Another action in combat allows you to make a melee attack roll against AC 10. If you succeed, you grant an adjacent ally either +2 to their next attack roll or +2 to their AC against one attack. PHB p.154. The rules do not specify whether you must threaten the same enemy your ally is fighting, whether the bonus stacks with multiple aids, or how long the bonus lasts (one round? one attack?).

**Pathfinder Change:**
Pathfinder keeps the same basic mechanic but clarifies: the +2 attack bonus applies to the aided ally's next attack roll against the specific opponent you threaten. The +2 AC bonus applies against the next attack from the specific opponent. Multiple Aid Another bonuses from different allies stack. The bonus lasts until the start of your next turn.

**Category:** COMBAT

**3.5e Problem Evidenced:**
The 3.5e Aid Another rules are functional but underspecified for edge cases. How many allies can aid the same target? Does the bonus stack? How long does it persist? These questions arise in any combat with more than two participants per side.

**Silence Type:** AMBIGUOUS (on stacking, duration, and targeting)

**Relevant SIL:** NONE

**Relevance to AIDM:**
When AIDM implements Aid Another, the engine needs deterministic answers to: do aid bonuses stack? How long do they persist? Who must be threatened? The Pathfinder model provides clean answers to all three. These should inform either RAW interpretation (most 3.5e tables already play it the Pathfinder way) or explicit House Policy.

---

### PF-DELTA-0023: Mounted Combat -- Targeting Rider vs. Mount Clarified

**3.5e Mechanic:**
Attacks against a mounted combatant can target either the rider or the mount. PHB p.157 states that an attacker can choose to attack either. However, the rules for cover (rider has cover from the mount) and the interaction between the rider's AC and the mount's AC when the attacker doesn't specify a target are unclear. If an area effect hits the mounted pair, damage application to each is not fully specified.

**Pathfinder Change:**
Pathfinder explicitly states: the rider gains a +4 cover bonus to AC from the mount (no change from 3.5e), but adds that if the mount is not in combat (carrying rider only), attacks target the rider by default. Area effects affect both mount and rider independently. The Mounted Combat feat allows the rider to make a Ride check to negate a hit on the mount (same as 3.5e, but more clearly stated).

**Category:** COMBAT + MOVEMENT

**3.5e Problem Evidenced:**
The 3.5e mounted combat rules leave gaps in default targeting (who gets attacked when the attacker doesn't specify?), area effect damage distribution, and the interaction between the rider's and mount's defensive statistics.

**Silence Type:** AMBIGUOUS

**Relevant SIL:** SIL-006 (Mount Weight Limits -- related mounted combat gap)

**Relevance to AIDM:**
CP-18A (Mounted Combat) already implements basic mounted mechanics. The rider/mount targeting question must have a deterministic default answer in AIDM's engine. The Pathfinder "default target is rider" rule should be adopted or documented as a Box resolver decision.

---

### PF-DELTA-0024: Stabilization at Negative HP Simplified

**3.5e Mechanic:**
A dying character (between -1 and -9 HP) must make a DC 10 Constitution check each round to stabilize. If they fail, they lose 1 HP. At -10, they die. If they stabilize, they stop losing HP but remain unconscious. Natural healing begins after stabilization. PHB p.145.

**Pathfinder Change:**
Pathfinder changes the death threshold from -10 to -(Constitution score). A character with 14 Con dies at -14 HP instead of -10. The stabilization check is now a DC 10 Constitution check each round (same mechanic), but the larger negative HP buffer means characters have more time to be rescued. Additionally, Pathfinder introduces the concept that a stable character has a 10% chance per hour of becoming conscious (rather than remaining unconscious indefinitely without healing).

**Category:** COMBAT

**3.5e Problem Evidenced:**
The fixed -10 death threshold is widely considered too harsh, especially at higher levels where a single hit can deal 20+ damage, meaning a character can go from positive HP to instant death in one attack. The flat -10 threshold means Constitution investment has no bearing on death resistance (beyond providing more HP to stay above -10).

**Silence Type:** BALANCE_ISSUE

**Relevant SIL:** NONE

**Relevance to AIDM:**
AIDM implements the 3.5e -10 death threshold per RAW. The Pathfinder delta is evidence that the fixed threshold is a known pain point. Session Zero might offer a House Policy variant for "death at negative Constitution score" since it's the most common house rule even in 3.5e games. The engine should make this threshold configurable.

---

### PF-DELTA-0025: Power Attack Scaling Changed

**3.5e Mechanic:**
Power Attack allows trading attack bonus for damage bonus on a 1-for-1 basis (up to BAB). With a two-handed weapon, the damage bonus is doubled. A level 20 fighter can trade -20 to attack for +40 damage with a two-handed weapon. PHB p.98.

**Pathfinder Change:**
Power Attack is no longer a variable trade-off. Instead, it provides a fixed penalty and bonus that scales with BAB: -1 attack/+2 damage at BAB +1, -2/+4 at BAB +4, -3/+6 at BAB +8, etc. Two-handed weapons get 50% more damage bonus (not double). The player no longer chooses how much to trade -- the trade is automatic based on BAB.

**Category:** COMBAT

**3.5e Problem Evidenced:**
The variable Power Attack in 3.5e creates a massive damage spike with two-handed weapons at high levels. A 20th-level fighter with a greatsword can swing for +0 to attack and +40 damage, which trivializes many encounters. The 1-for-2 ratio with two-handed weapons is the primary balance problem. Additionally, the variable nature means the "optimal" power attack value depends on the target's AC, which requires either metagaming or complex probability reasoning.

**Silence Type:** BALANCE_ISSUE

**Relevant SIL:** NONE

**Relevance to AIDM:**
AIDM implements 3.5e's variable Power Attack. The Pathfinder delta is evidence that the 1-for-2 two-handed ratio is a balance problem. This is relevant for AIDM's AI DM monster tactics -- an AI that optimally calculates Power Attack values could exploit this harder than a human player. House Policy might cap the maximum Power Attack trade or use the Pathfinder scaling formula as a variant option.

---

## Summary Matrix

| Delta ID | Category | Silence Type | Relevant SIL | AIDM Priority |
|----------|----------|-------------|--------------|---------------|
| PF-DELTA-0001 | MANEUVERS | AMBIGUOUS + BALANCE | SIL-009 | HIGH |
| PF-DELTA-0002 | MANEUVERS | AMBIGUOUS | SIL-009 | HIGH |
| PF-DELTA-0003 | EQUIPMENT + COMBAT | SILENT + BALANCE | SIL-004, SIL-010 | HIGH |
| PF-DELTA-0004 | EQUIPMENT + OBJECTS | CONTRADICTORY | SIL-007, SIL-008 | CRITICAL |
| PF-DELTA-0005 | COMBAT | AMBIGUOUS | NONE | MEDIUM |
| PF-DELTA-0006 | COMBAT | AMBIGUOUS | NONE | LOW |
| PF-DELTA-0007 | COMBAT + MOVEMENT | AMBIGUOUS | NONE | MEDIUM |
| PF-DELTA-0008 | SPELLS | BALANCE | NONE | LOW |
| PF-DELTA-0009 | SPELLS + OBJECTS | BALANCE | SIL-004, SIL-010 | MEDIUM |
| PF-DELTA-0010 | OBJECTS + ENVIRONMENT | SILENT + AMBIGUOUS | SIL-002 | MEDIUM |
| PF-DELTA-0011 | ENVIRONMENT + OBJECTS | AMBIGUOUS | NONE | MEDIUM |
| PF-DELTA-0012 | COMBAT | AMBIGUOUS | NONE | LOW |
| PF-DELTA-0013 | COMBAT + MANEUVERS | AMBIGUOUS | SIL-009 | HIGH |
| PF-DELTA-0014 | COMBAT + MOVEMENT | AMBIGUOUS | NONE | MEDIUM |
| PF-DELTA-0015 | MOVEMENT | SILENT | NONE | MEDIUM |
| PF-DELTA-0016 | COMBAT | AMBIGUOUS | NONE | LOW |
| PF-DELTA-0017 | MANEUVERS | BALANCE | NONE | LOW |
| PF-DELTA-0018 | MANEUVERS + COMBAT | BALANCE | NONE | LOW |
| PF-DELTA-0019 | MANEUVERS | AMBIGUOUS | NONE | MEDIUM |
| PF-DELTA-0020 | MANEUVERS | BALANCE | NONE | HIGH |
| PF-DELTA-0021 | EQUIPMENT + MANEUVERS | BALANCE | NONE | LOW |
| PF-DELTA-0022 | COMBAT | AMBIGUOUS | NONE | LOW |
| PF-DELTA-0023 | COMBAT + MOVEMENT | AMBIGUOUS | SIL-006 | MEDIUM |
| PF-DELTA-0024 | COMBAT | BALANCE | NONE | LOW |
| PF-DELTA-0025 | COMBAT | BALANCE | NONE | LOW |

---

## Cross-Reference to Existing Silence Catalog

| SIL ID | Description | Deltas That Provide Evidence |
|--------|-------------|------------------------------|
| SIL-002 | Structural Load-Bearing | PF-DELTA-0010 |
| SIL-004 | Object Identity Under Damage | PF-DELTA-0003, PF-DELTA-0009 |
| SIL-006 | Mount Weight Limits | PF-DELTA-0023 |
| SIL-007 | Enhancement Bonus Hardness/HP Contradiction | PF-DELTA-0004 |
| SIL-008 | Armor Enhancement Bonus Exclusion | PF-DELTA-0004 |
| SIL-009 | Grapple Square Threatening | PF-DELTA-0001, PF-DELTA-0002, PF-DELTA-0013 |
| SIL-010 | Object Physical State After HP=0 | PF-DELTA-0003, PF-DELTA-0009 |

---

## Actionable Recommendations

### Immediate (Informs Current Design)

1. **PF-DELTA-0004**: Resolve SIL-007/SIL-008 by adopting the PHB/Pathfinder formula (+2 hardness, +10 HP per +1 enhancement). Pathfinder confirms this was the intended design.

2. **PF-DELTA-0013**: Validate that CP-16 condition definitions are self-contained. Each condition must enumerate ALL its effects without requiring cross-reference to other rule sections.

3. **PF-DELTA-0019**: Hard-code recursion depth of 1 for counter-maneuvers in CP-18. No counter-counter-disarm, no counter-counter-trip.

4. **PF-DELTA-0020**: Codify overrun as always-opposed-check (no defender avoidance) as a Box resolver decision. Pathfinder confirms the avoidance mechanic is problematic.

### Near-Term (Informs Upcoming Design)

5. **PF-DELTA-0003**: When designing the item HP kernel, include a "Broken" intermediate condition. Binary functional/destroyed is confirmed as a design failure by Pathfinder.

6. **PF-DELTA-0010**: Build the AIDM object property database using the expanded Pathfinder hardness/HP table as a supplementary reference for materials 3.5e omits (rope, glass, leather, ice).

7. **PF-DELTA-0011**: Adopt "energy damage halved before hardness" as a House Policy for CP-20 environmental damage against objects.

8. **PF-DELTA-0005/0007**: Build a centralized AoO provocation truth table rather than distributing provocation rules across individual maneuver implementations.

### Session Zero Variant Options

9. **PF-DELTA-0008**: Offer "unlimited cantrips" as a Session Zero option. Flag the mending interaction with object repair economy.

10. **PF-DELTA-0024**: Offer "death at negative Con score" as a Session Zero option (configurable death threshold).

11. **PF-DELTA-0025**: Flag Power Attack 1-for-2 two-handed ratio as a known balance concern. Consider a House Policy cap on maximum Power Attack trade.

---

## Provenance and Limitations

**Source authority:** EXTERNAL_EVIDENCE (Priority 7 per RESEARCH_FINDING_SCHEMA.md). Pathfinder deltas do not determine AIDM House Policy -- they inform it. All findings must be validated against 3.5e RAW before being promoted to House Policy decisions.

**Completeness:** This index covers 25 deltas within the v1 scope. Additional deltas exist in areas excluded from v1 (polymorph, class features, skill consolidation, spells 6+). These may be added in future revisions when scope expands.

**Verification:** Web search and web fetch were unavailable during compilation. All findings are drawn from the author's training knowledge of both systems. Each claim is verifiable against the Pathfinder SRD (d20pfsrd.com) and the D&D 3.5e SRD (d20srd.org). A verification pass against live SRD sources is recommended before promoting any finding to House Policy status.

---

**Document Version:** 1.0
**Filed:** 2026-02-12
**Status:** V1 COMPLETE -- Pending PO review and SRD verification pass

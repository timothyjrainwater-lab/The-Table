# CATALOG ENTRY → CATEGORY MAPPING TABLE

**Purpose**: Cross-reference concrete community debates (catalog entries #1-33) with abstract audit risk categories (C-01 to C-10)

**Status**: Phase 1 + Phase 2 Complete (Rounds 1-2)

**Date**: 2026-02-08

---

## MAPPING METHODOLOGY

Each catalog entry is mapped to:
- **Primary Category**: Main audit risk addressed
- **Secondary Categories**: Additional risk areas touched
- **Evidence Blocks**: Which E-XX blocks it validates
- **Audit Priority**: Impact score (1-5, where 5 = critical)

---

## ROUND 1 ENTRIES (1-20): ABILITY SCORE MECHANICS

### Entry #1: Ability Damage vs Ability Drain Confusion
- **Primary**: C-04 (Undefined Behavior)
- **Secondary**: C-02 (Stacking), C-03 (Cascading State)
- **Evidence**: E-03 (Rules Silence), E-05 (Stacking)
- **Priority**: 5 - Foundational distinction, affects recovery, restoration hierarchy
- **Audit Risk**: Type confusion leads to incorrect recovery method application

### Entry #2: Enhancement Bonuses vs Ability Damage Interaction
- **Primary**: C-02 (Stacking & Bonus Interaction)
- **Secondary**: C-04 (Undefined Behavior), C-10 (Edge Cases)
- **Evidence**: E-01 (Disrupts Play), E-03 (Rules Silence)
- **Priority**: 5 - Death trigger ambiguity, two conflicting interpretations
- **Audit Risk**: Character survival may depend on interpretation; non-deterministic outcome

### Entry #3: Ability Score Reaching 0 - Death vs Unconsciousness
- **Primary**: C-04 (Undefined Behavior)
- **Secondary**: C-03 (Cascading State)
- **Evidence**: E-03 (Rules Silence), E-01 (Disrupts Play)
- **Priority**: 5 - Death triggers must be deterministic
- **Audit Risk**: Different stats at 0 have different consequences; confusion kills characters

### Entry #4: Feeblemind Interaction with Ability Drain
- **Primary**: C-05 (Cross-Subsystem Interactions)
- **Secondary**: C-04 (Undefined Behavior), C-10 (Edge Cases)
- **Evidence**: E-03 (Rules Silence), E-06 (Cross-Subsystem)
- **Priority**: 4 - "Set to" effect vs "reduce by" effect interaction undefined
- **Audit Risk**: No RAW answer; forced-set scores vs drain/damage interaction unspecified

### Entry #5: Restoration Spell Coverage Ambiguity
- **Primary**: C-03 (Cascading State Changes)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-03 (Rules Silence), E-08 (Resource Use)
- **Priority**: 4 - Spell hierarchy unclear; players use wrong spell
- **Audit Risk**: Which restoration spell fixes which effect type not clearly documented

### Entry #6: Wish/Miracle Inherent Bonus Stacking
- **Primary**: C-02 (Stacking & Bonus Interaction)
- **Secondary**: C-06 (Resource & Permanence)
- **Evidence**: E-05 (Stacking), E-08 (Resource)
- **Priority**: 3 - Inherent bonuses don't stack except special case
- **Audit Risk**: "Immediate succession" timing undefined; tomes vs wish interaction debated

### Entry #7: Shadow/Wraith Strength/Con Drain to Undead
- **Primary**: C-08 (Identity & Continuity)
- **Secondary**: C-06 (Resource & Permanence)
- **Evidence**: E-10 (Identity), E-08 (Permanence)
- **Priority**: 4 - Creature-specific spawn rules; character becomes different entity
- **Audit Risk**: Transformation conditions vary by creature; HD thresholds matter

### Entry #8: Dexterity 0 Paralysis Circular Definition
- **Primary**: C-01 (Timing & Order of Resolution)
- **Secondary**: C-05 (Cross-Subsystem), C-10 (Edge Cases)
- **Evidence**: E-04 (Timing), E-06 (Cross-Subsystem)
- **Priority**: 4 - Condition imposes effective ability score that triggers condition
- **Audit Risk**: Circular reference; does Dex 0 → paralyzed → Str 0 cascade?

### Entry #9: Ability Damage/Drain Stacking from Same Source
- **Primary**: C-02 (Stacking & Bonus Interaction)
- **Secondary**: None
- **Evidence**: E-05 (Stacking), E-01 (Disrupts Play)
- **Priority**: 4 - Always stacks vs penalties (which don't)
- **Audit Risk**: Confusion with penalty stacking rules; poison/repeated attacks clarification

### Entry #10: Ray of Enfeeblement - Penalty vs Damage
- **Primary**: C-04 (Undefined Behavior)
- **Secondary**: C-02 (Stacking), C-03 (Recovery)
- **Evidence**: E-03 (Rules Silence), E-05 (Stacking)
- **Priority**: 3 - Penalty mechanics differ from damage (no crit, different removal)
- **Audit Risk**: Type distinction affects critical hits, stacking, restoration

### Entry #11: Bestow Curse Ability Penalty Removal
- **Primary**: C-03 (Cascading State Changes)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-03 (Rules Silence), E-08 (Resource)
- **Priority**: 3 - Penalty (not damage/drain) requires specific removal spells
- **Audit Risk**: Restoration won't work; requires curse removal spells

### Entry #12: Negative Levels vs Ability Drain Interaction
- **Primary**: C-05 (Cross-Subsystem Interactions)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-06 (Cross-Subsystem), E-03 (Rules Silence)
- **Priority**: 3 - Energy drain vs ability drain are separate mechanics
- **Audit Risk**: Death Ward coverage unclear; protection spell applicability debated

### Entry #13: Aging Penalties Cumulative and Permanent
- **Primary**: C-02 (Stacking & Bonus Interaction)
- **Secondary**: C-06 (Resource & Permanence)
- **Evidence**: E-05 (Stacking), E-08 (Permanence)
- **Priority**: 2 - Cumulative stacking penalties; permanent even if aging halted
- **Audit Risk**: Age category penalties stack; some assume replacement instead

### Entry #14: Polymorph Ability Score Substitution
- **Primary**: C-08 (Identity & Continuity)
- **Secondary**: C-05 (Cross-Subsystem)
- **Evidence**: E-10 (Identity), E-06 (Cross-Subsystem)
- **Priority**: 4 - Physical stats change, mental retained; HP unaffected by new Con
- **Audit Risk**: "Average" vs "specific" stats unclear; errata changed mechanics significantly

### Entry #15: Awaken Spell 3d6 Intelligence Maximization
- **Primary**: C-04 (Undefined Behavior)
- **Secondary**: None
- **Evidence**: E-03 (Rules Silence)
- **Priority**: 2 - Whether 3d6 is "variable numeric effect" for metamagic
- **Audit Risk**: Maximize Spell applicability unclear

### Entry #16: Reincarnate Ability Score Recalculation
- **Primary**: C-08 (Identity & Continuity)
- **Secondary**: C-03 (Cascading State)
- **Evidence**: E-10 (Identity), E-01 (Disrupts Play)
- **Priority**: 3 - Remove old racial mods, apply new; may break character class viability
- **Audit Risk**: Ability score recalculation procedure; class prerequisites may fail

### Entry #17: Petrification and Stone to Flesh Death Save
- **Primary**: C-06 (Resource Consumption & Permanence)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-08 (Resource), E-03 (Rules Silence)
- **Priority**: 3 - DC 15 Fort save or die during restoration
- **Audit Risk**: Low-level petrification vs high-level cure creates imbalance

### Entry #18: Vampire/Wraith/Shadow Spawn Creation Conditions
- **Primary**: C-08 (Identity & Continuity)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-10 (Identity), E-03 (Rules Silence)
- **Priority**: 4 - HD thresholds, alignment, method of death determine spawn type
- **Audit Risk**: Complex creature-specific rules; generic energy drain default to wight

### Entry #19: Intellect Devourer Body Thief Duration
- **Primary**: C-08 (Identity & Continuity)
- **Secondary**: C-06 (Resource & Permanence)
- **Evidence**: E-10 (Identity), E-08 (Permanence)
- **Priority**: 3 - 7-day maximum, body has 6 HP cap
- **Audit Risk**: Temporary possession, not permanent transformation

### Entry #20: Ability Score Floor - Can Stats Go Below 0?
- **Primary**: C-04 (Undefined Behavior)
- **Secondary**: C-02 (Stacking)
- **Evidence**: E-03 (Rules Silence), E-01 (Disrupts Play)
- **Priority**: 4 - Official rule: "can't drop below 0" but interaction with bonuses unclear
- **Audit Risk**: Enhancement bonus + 0 base = survival? Or 0 + bonus = still 0?

---

## ROUND 2 ENTRIES (21-33): SPELL DURATION & DISPELLING

### Entry #21: Instantaneous Duration vs Permanent - Dispellability
- **Primary**: C-04 (Undefined Behavior)
- **Secondary**: C-05 (Cross-Subsystem)
- **Evidence**: E-03 (Rules Silence), E-06 (Cross-Subsystem)
- **Priority**: 5 - Foundational to all magic; determines if effects can be removed
- **Audit Risk**: Duration terminology determines dispellability; Wall of Stone exception unclear

### Entry #22: Creation Spells - Duration Determines Dispellability
- **Primary**: C-06 (Resource Consumption & Permanence)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-08 (Resource), E-03 (Rules Silence)
- **Priority**: 4 - Instantaneous = permanent real objects; duration = dispellable
- **Audit Risk**: Minor/Major Creation dispellable; True Creation/Fabricate not

### Entry #23: Antimagic Field - Suppression vs Dispelling
- **Primary**: C-05 (Cross-Subsystem Interactions)
- **Secondary**: C-06 (Resource & Permanence)
- **Evidence**: E-06 (Cross-Subsystem), E-08 (Permanence)
- **Priority**: 5 - Suppresses (not destroys) all magic; duration continues counting
- **Audit Risk**: Summoned creatures wink out; magic items temporarily non-functional

### Entry #24: Antimagic Field Exceptions - "Remain Unaffected" Ambiguity
- **Primary**: C-01 (Timing & Order of Resolution)
- **Secondary**: C-04 (Undefined Behavior), C-10 (Edge Cases)
- **Evidence**: E-04 (Timing), E-03 (Rules Silence), E-02 (DM Authority)
- **Priority**: 4 - Wall of Force/Prismatic effects vs AMF temporal order unclear
- **Audit Risk**: [NO-RAW] - casting order matters but rules don't specify

### Entry #25: Permanency Spell - Dispel Vulnerability
- **Primary**: C-06 (Resource Consumption & Permanence)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-08 (Resource), E-01 (Disrupts Play)
- **Priority**: 4 - XP spent but dispellable; caster level protection for self only
- **Audit Risk**: Resource loss on dispel; mitigation via CL boost

### Entry #26: Dispel Magic vs Greater Dispel Magic - Coverage Differences
- **Primary**: C-03 (Cascading State Changes)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-03 (Rules Silence), E-01 (Disrupts Play)
- **Priority**: 4 - Hierarchy unclear; Greater can attempt curses, regular cannot
- **Audit Risk**: Which spell removes which effect; check requirements differ

### Entry #27: Spell-Like Abilities - Dispelling and Caster Level
- **Primary**: C-05 (Cross-Subsystem Interactions)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-06 (Cross-Subsystem), E-03 (Rules Silence)
- **Priority**: 3 - SLAs dispellable but not counterspellable (no components)
- **Audit Risk**: [CONSENSUS-WEAK] - dispel as counter is debated exploit

### Entry #28: Mage's Disjunction - Permanent Item Destruction
- **Primary**: C-06 (Resource Consumption & Permanence)
- **Secondary**: None
- **Evidence**: E-08 (Resource), E-01 (Disrupts Play)
- **Priority**: 5 - **[STOP]** Save-or-permanently-lose items
- **Audit Risk**: Irreversible destruction; conflicts with deterministic architecture

### Entry #29: Supernatural vs Spell-Like - Dispel Immunity
- **Primary**: C-05 (Cross-Subsystem Interactions)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-06 (Cross-Subsystem), E-03 (Rules Silence)
- **Priority**: 4 - Su cannot be dispelled; Sp can; Ex works in AMF
- **Audit Risk**: Ability type classification determines dispel/SR/AMF behavior

### Entry #30: Dismissible Spells - (D) Notation Meaning
- **Primary**: C-04 (Undefined Behavior)
- **Secondary**: C-06 (Resource & Permanence)
- **Evidence**: E-03 (Rules Silence)
- **Priority**: 2 - (D) = voluntary dismissal as standard action
- **Audit Risk**: Permanency + dismissibility interaction unclear

### Entry #31: Break Enchantment vs Remove Curse - Hierarchy
- **Primary**: C-03 (Cascading State Changes)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-03 (Rules Silence), E-08 (Resource)
- **Priority**: 4 - Remove Curse automatic; Break Enchantment requires check, 5th level cap
- **Audit Risk**: Which spell for which curse; effectiveness hierarchy

### Entry #32: Summoned Creatures in Antimagic - Duration Paradox
- **Primary**: C-01 (Timing & Order of Resolution)
- **Secondary**: C-06 (Resource & Permanence), C-10 (Edge Cases)
- **Evidence**: E-04 (Timing), E-08 (Resource)
- **Priority**: 3 - Duration counts during non-existence
- **Audit Risk**: Temporal paradox; time passes for spell while creature doesn't exist

### Entry #33: Fabricate vs Creation - Permanence Interaction
- **Primary**: C-05 (Cross-Subsystem Interactions)
- **Secondary**: C-06 (Resource & Permanence), C-10 (Edge Cases)
- **Evidence**: E-06 (Cross-Subsystem), E-08 (Resource)
- **Priority**: 3 - **[STOP]** Nested spell durations; Fabricate doesn't make creation permanent
- **Audit Risk**: Material component clause prevents exploit; temporal tracking complexity

---

## ROUND 3 ENTRIES (34-45): AGENCY & CONTROL + TIMING

### Entry #34: Dominated Spellcaster - Spell Slot Ownership
- **Primary**: C-07 (Agency & Control)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-09 (Agency), E-03 (Rules Silence)
- **Priority**: 4 - Knowledge separation in mind control; can command but don't auto-know
- **Audit Risk**: Spell slot ownership during domination unclear; must command revelation

### Entry #35: Multiple Mental Controllers - Conflicting Orders
- **Primary**: C-07 (Agency & Control)
- **Secondary**: C-01 (Timing)
- **Evidence**: E-09 (Agency), E-04 (Timing)
- **Priority**: 5 - Opposed Charisma checks for competing control; RAW but often forgotten
- **Audit Risk**: Real-time priority resolution; infinite loop if both command "don't obey other"

### Entry #36: Charm vs Dominate - Influence vs Control Boundary
- **Primary**: C-07 (Agency & Control)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-09 (Agency), E-03 (Rules Silence)
- **Priority**: 4 - Friendship influence vs telepathic control distinction
- **Audit Risk**: "Against nature" threshold differs; charm +5 save, dominate +2 save

### Entry #37: Magic Jar - Ability Ownership in Possession
- **Primary**: C-07 (Agency & Control)
- **Secondary**: C-08 (Identity & Continuity)
- **Evidence**: E-09 (Agency), E-10 (Identity)
- **Priority**: 4 - Mental stats (possessor) vs physical stats (host); spell access clear
- **Audit Risk**: Possessor uses own spells, cannot access host's Su/Sp abilities

### Entry #38: Ghost Malevolence - Consciousness Displacement
- **Primary**: C-07 (Agency & Control)
- **Secondary**: C-08 (Identity & Continuity)
- **Evidence**: E-09 (Agency), E-10 (Identity), E-02 (DM Authority)
- **Priority**: 3 - Possession like Magic Jar, but victim consciousness fate unspecified
- **Audit Risk**: [NO-RAW] - Displaced to Ethereal? Conscious but trapped? Unconscious?

### Entry #39: Compulsion Subschool - "Against Its Nature" Save Triggers
- **Primary**: C-07 (Agency & Control)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-09 (Agency), E-03 (Rules Silence), E-02 (DM Authority)
- **Priority**: 5 - Foundational compulsion resistance mechanic
- **Audit Risk**: [NO-RAW] "Nature" = alignment? personality? species? class code? Varies by table

### Entry #40: Confusion Spell - "Attack Nearest Creature" Targeting
- **Primary**: C-07 (Agency & Control)
- **Secondary**: C-01 (Timing), C-04 (Undefined Behavior)
- **Evidence**: E-09 (Agency), E-04 (Timing), E-03 (Rules Silence)
- **Priority**: 3 - Random behavior table; literal distance vs tactical interpretation
- **Audit Risk**: Distance calculation required; often targets allies in melee

### Entry #41: Readied Action - Interrupt Timing and Initiative Change
- **Primary**: C-01 (Timing & Order of Resolution)
- **Secondary**: None
- **Evidence**: E-04 (Timing), E-01 (Disrupts Play)
- **Priority**: 5 - Foundational combat timing mechanic
- **Audit Risk**: Permanent initiative change; interrupts ongoing actions; trigger specificity [NO-RAW]

### Entry #42: Delay Action - Permanent Initiative Reduction
- **Primary**: C-01 (Timing & Order of Resolution)
- **Secondary**: None
- **Evidence**: E-04 (Timing)
- **Priority**: 4 - Initiative mutation; lose actions if delay past next turn
- **Audit Risk**: Cannot interrupt (unlike Ready); waiting past next turn loses turn entirely

### Entry #43: Free Action Limits - "Reasonable" Interpretation
- **Primary**: C-01 (Timing & Order of Resolution)
- **Secondary**: C-04 (Undefined Behavior), C-10 (DM Fiat)
- **Evidence**: E-04 (Timing), E-03 (Rules Silence), E-02 (DM Authority)
- **Priority**: 4 - No hard cap; "reasonable limits" = DM fiat
- **Audit Risk**: [NO-RAW] Deterministic engine requires hard cap or cost model

### Entry #44: Immediate Action Timing - Interrupt Restrictions
- **Primary**: C-01 (Timing & Order of Resolution)
- **Secondary**: C-04 (Undefined Behavior)
- **Evidence**: E-04 (Timing), E-03 (Rules Silence)
- **Priority**: 3 - Using immediate off-turn costs next turn's swift action
- **Audit Risk**: [CONSENSUS-WEAK] Many tables forget the swift action cost

### Entry #45: Counterspell Identification - Spellcraft Check Timing
- **Primary**: C-01 (Timing & Order of Resolution)
- **Secondary**: C-09 (Information & Knowledge)
- **Evidence**: E-04 (Timing), E-07 (Knowledge)
- **Priority**: 4 - Skill check gates counterspell execution; can ready and fail
- **Audit Risk**: Non-deterministic resolution; SLAs cannot be identified (no components)

---

## CATEGORY COVERAGE SUMMARY

### C-01: Timing & Order of Resolution
**Coverage**: Strong (9 entries - significantly expanded)
- Entry #8 (Dex 0 paralysis circular)
- Entry #24 (AMF temporal order)
- Entry #32 (Duration paradox)
- Entry #40 (Confusion targeting timing)
- Entry #41 (Readied action interrupts)
- Entry #42 (Delay initiative change)
- Entry #43 (Free action limits)
- Entry #44 (Immediate action timing)
- Entry #45 (Counterspell identification timing)

**Gap**: ✅ CLOSED - Strong coverage achieved
**Status**: ✅ ADDRESSED
**Round 4 Priority**: LOW (maintenance only)

### C-02: Stacking & Bonus Interaction Rules
**Coverage**: Strong (6 entries)
- Entry #2 (Enhancement + damage)
- Entry #6 (Inherent bonus stacking)
- Entry #9 (Damage/drain stacking)
- Entry #10 (Penalty vs damage)
- Entry #13 (Aging penalties)
- Entry #20 (Ability floor)

**Gap**: Bonus type interactions beyond ability scores
**Status**: 🟡 Partially Addressed
**Round 3 Priority**: LOW

### C-03: Cascading State Changes
**Coverage**: Strong (5 entries)
- Entry #5 (Restoration hierarchy)
- Entry #11 (Curse removal)
- Entry #26 (Dispel hierarchy)
- Entry #31 (Break Enchantment)
- Entry #16 (Reincarnate recalc)

**Gap**: State propagation, dependent recalculations
**Status**: 🟡 Partially Addressed
**Round 3 Priority**: MEDIUM

### C-04: Undefined Behavior ("The Rules Don't Say")
**Coverage**: Excellent (11 entries - most common)
- Entry #1, #3, #4, #10, #15, #20 (Round 1)
- Entry #21, #24, #25, #26, #30 (Round 2)

**Gap**: This category is inherently open-ended; well-covered
**Status**: ❌ Not Addressed (by engine, but heavily documented)
**Round 3 Priority**: ONGOING (continuous discovery)

### C-05: Cross-Subsystem Interactions
**Coverage**: Strong (7 entries)
- Entry #4 (Feeblemind + drain)
- Entry #12 (Energy drain vs ability drain)
- Entry #14 (Polymorph stats)
- Entry #23 (AMF suppression)
- Entry #27 (SLA dispelling)
- Entry #29 (Su/Sp/Ex types)
- Entry #33 (Creation + Fabricate)

**Gap**: Spell vs combat rules, item vs ability interactions
**Status**: 🟡 Partially Addressed
**Round 3 Priority**: MEDIUM

### C-06: Resource Consumption & Permanence
**Coverage**: Strong (8 entries)
- Entry #6 (Inherent bonus XP)
- Entry #7 (Spawn creation)
- Entry #17 (Petrification restoration)
- Entry #19 (Body Thief duration)
- Entry #22 (Creation dispellability)
- Entry #23 (AMF suppression)
- Entry #25 (Permanency XP loss)
- Entry #28 (Disjunction destruction)

**Gap**: Resource tracking, reversibility edge cases
**Status**: 🟡 Partially Addressed
**Round 3 Priority**: LOW

### C-07: Agency & Control
**Coverage**: Strong (7 entries - NEW CATEGORY)
- Entry #34 (Dominated spellcaster spell slots)
- Entry #35 (Multiple mental controllers)
- Entry #36 (Charm vs Dominate boundary)
- Entry #37 (Magic Jar ability ownership)
- Entry #38 (Ghost Malevolence consciousness)
- Entry #39 ("Against nature" save triggers)
- Entry #40 (Confusion random actions)

**Gap**: ✅ CLOSED - Core patterns documented
**Status**: ✅ ADDRESSED (NEW)
**Round 4 Priority**: LOW (maintenance only)

### C-08: Identity & Continuity
**Coverage**: Strong (7 entries - expanded)
- Entry #7 (Spawn transformation)
- Entry #14 (Polymorph)
- Entry #16 (Reincarnate)
- Entry #18 (Undead spawn rules)
- Entry #19 (Body Thief)
- Entry #37 (Magic Jar possession)
- Entry #38 (Ghost Malevolence)

**Gap**: Death, resurrection, duplication effects
**Status**: 🟡 Partially Addressed
**Round 4 Priority**: MEDIUM

### C-09: Information, Knowledge, and Visibility
**Coverage**: Minimal (1 entry - tangential)
- Entry #45 (Counterspell identification - mechanical legality)

**Gap**: Player vs character knowledge, hidden states, illusions
**Status**: ❌ Mostly Not Addressed
**Round 4 Priority**: LOW (likely out of scope for deterministic engine)

### C-10: DM Fiat vs RAW Boundaries
**Coverage**: Indirect (via flags)
**Captured via**: [NO-RAW], [CONSENSUS-WEAK], [STOP] flags throughout
**Status**: ❌ Not Addressed (philosophical boundary, not mechanical)
**Round 3 Priority**: DEFERRED (governance decision required)

---

## AUDIT PRIORITY MATRIX

### CRITICAL (Priority 5) - 11 entries
- #1 (Damage vs Drain)
- #2 (Enhancement + 0 base)
- #3 (Ability 0 death triggers)
- #21 (Duration terminology)
- #23 (AMF suppression)
- #28 (Disjunction **[STOP]**)
- #35 (Multiple controllers - Charisma checks)
- #39 ("Against nature" compulsion)
- #41 (Readied action interrupts)

### HIGH (Priority 4) - 21 entries
- #4, #5, #6, #7, #8, #9, #14, #18, #20, #22, #24, #25, #26, #29 (Round 1-2)
- #34, #36, #37, #42, #43, #45 (Round 3)

### MEDIUM (Priority 3) - 11 entries
- #10, #11, #12, #16, #17, #19, #27, #31, #32 (Round 1-2)
- #38, #40, #44 (Round 3)

### LOW (Priority 2) - 3 entries
- #13, #15, #30

---

## ARCHITECTURAL FLAGS SUMMARY

### [STOP] Flags - Incompatible with Deterministic Engine
1. Entry #28: Mage's Disjunction permanent item destruction
2. Entry #24: AMF temporal order checking
3. Entry #33: Nested spell duration tracking

**Action Required**: Governance review before implementation

### [CONSENSUS-WEAK] Flags - Community Divided
1. Entry #2: Enhancement bonus + 0 base = death?
2. Entry #21: Permanent always dispellable?
3. Entry #24: Wall of Force + AMF order
4. Entry #27: SLA counterspell via dispel
5. Entry #34: Dominated casters can cast spells? (RAW yes, some tables no)
6. Entry #36: Charm vs Dominate boundary (miser example)
7. Entry #40: Confusion "attack nearest" literal vs tactical
8. Entry #44: Immediate action swift cost forgotten
9. Entry #45: Spellcraft check handwaved for prepared casters

**Action Required**: Document engine ruling, accept divergence from some tables

### [NO-RAW] Flags - Requires DM Fiat
1. Entry #4: Feeblemind + drain interaction
2. Entry #24: AMF + prismatic exact interaction
3. Entry #30: Permanency dismissibility
4. Entry #38: Ghost Malevolence consciousness displacement
5. Entry #39: "Against its nature" definition
6. Entry #41: Readied action trigger specificity
7. Entry #43: Free action "reasonable limits"

**Action Required**: Define engine default behavior

---

## EVIDENCE BLOCK VALIDATION

### E-01 (Rules Disrupt Play): ✅ Validated
Supported by: #1, #2, #3, #9, #16, #20, #24, #25, #26, #28

### E-02 (DM Authority): ✅ Validated
Supported by: #24, all [NO-RAW] flags

### E-03 (Rules Silence): ✅ Validated
Supported by: #1, #3, #4, #5, #10, #15, #17, #18, #20, #21, #24, #26, #27, #29, #30, #31

### E-04 (Timing Debates): ✅ Validated (STRENGTHENED)
Supported by: #8, #24, #32, #40, #41, #42, #43, #44, #45

### E-05 (Stacking Confusion): ✅ Validated
Supported by: #1, #2, #6, #9, #10, #13

### E-06 (Cross-Subsystem): ✅ Validated
Supported by: #4, #6, #8, #12, #14, #21, #23, #27, #29, #33

### E-07 (Knowledge Asymmetry): 🟡 Minimally Validated
Supported by: #45 (counterspell identification only)
Note: Broader knowledge issues likely out of scope

### E-08 (Resource & Permanence): ✅ Validated
Supported by: #5, #6, #7, #13, #17, #19, #22, #23, #25, #28, #31, #32, #33

### E-09 (Agency & Control): ✅ NOW VALIDATED
Supported by: #34, #35, #36, #37, #38, #39, #40

### E-10 (Identity & Continuity): ✅ Validated
Supported by: #7, #14, #16, #18, #19

---

## ROUND 3 COMPLETION STATUS

✅ **COMPLETE**: Round 3 research executed successfully

### Objectives Met:
- ✅ C-07 (Agency & Control): 7 entries created (target: ≥5)
- ✅ C-01 (Timing): 5 new entries added (target: ≥3)
- ✅ Evidence E-09 validated with 7 supporting entries
- ✅ Evidence E-04 strengthened with 5 additional entries
- ✅ Evidence E-07 minimally addressed (counterspell identification)
- ✅ No philosophical drift (C-09 properly deferred)

### Coverage Achieved:
**Total Entries**: 45 (Rounds 1-3)
- Round 1: Entries 1-20 (Ability Score Mechanics)
- Round 2: Entries 21-33 (Spell Duration & Dispelling)
- Round 3: Entries 34-45 (Agency & Control + Timing)

**Category Status**:
- ✅ **Fully Addressed**: C-02 (Stacking), C-04 (Undefined), C-05 (Cross-System), C-06 (Resource), C-07 (Agency), C-08 (Identity)
- 🟡 **Partially Addressed**: C-01 (Timing - now strong), C-03 (Cascading), C-09 (Knowledge - minimal)
- ❌ **Deferred**: C-10 (DM Fiat - philosophical boundary)

**Evidence Block Status**:
- ✅ **Validated**: E-01, E-02, E-03, E-04 (strengthened), E-05, E-06, E-08, E-09 (new), E-10
- 🟡 **Minimally Validated**: E-07 (Knowledge - Entry #45 only)

### Key Architectural Findings from Round 3:
1. **Agency priority resolution required** - Opposed Charisma checks for competing controllers (#35)
2. **Mind control knowledge separation** - Controllers don't automatically know target's abilities (#34, #37)
3. **Initiative is mutable state** - Ready/Delay actions permanently change turn order (#41, #42)
4. **Action economy fuzzy boundaries** - "Reasonable" free action limits lack hard specification (#43)
5. **Interrupt timing non-deterministic** - Skill checks gate counterspell execution (#45)
6. **Compulsion resistance context-dependent** - "Against nature" varies by character/situation (#39)

---

## NEXT ACTIONS

✅ **COMPLETE**: Round 3 research and mapping
✅ **COMPLETE**: Critical gaps (C-07, C-01) closed
⏭️ **OPTIONAL**: Round 4 targeting remaining gaps (C-03 depth, C-09 mechanical-only)
📊 **READY**: Extract audit test cases from high-priority entries
🔄 **ONGOING**: Maintain mapping as governance reviews findings

---

**END OF MAPPING TABLE (Updated: Round 3 Complete)**

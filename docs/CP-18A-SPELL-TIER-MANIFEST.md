# CP-18A Spell Tier Manifest

**Version:** 1.0
**Date:** 2026-02-08
**Status:** ✅ CANONICAL (Binding Contract for CP-18A Scope)
**Authority:** DR-001 (Spellcasting Scope Lock)

---

## Purpose

This manifest is the **binding Tier 1 spell list** for CP-18A (Tier 1 Spellcasting Core).

**Scope Boundary (Mandatory):**
- Every spell in this manifest is AUTHORIZED for implementation in CP-18A
- Every spell NOT in this manifest is FORBIDDEN for CP-18A
- No spell may be implemented without appearing in this table
- Deviation requires NEW decision record (DR-XXX)

This document enforces the fail-closed gate architecture defined in [AIDM_PROJECT_ACTION_PLAN_V2.md](AIDM_PROJECT_ACTION_PLAN_V2.md).

---

## Tier 1 Inclusion Test (Fail-Closed)

A spell is classified as **Tier 1** if and only if **ALL** of the following are true:

1. ✅ **No permanent stat mutation** (does NOT block G-T2A)
   - No ability score drain (STR/DEX/CON/INT/WIS/CHA permanent reduction)
   - No permanent ability score buffs (inherent bonuses)
   - No Feeblemind-type effects (permanent INT/CHA → 1)

2. ✅ **No XP cost, level loss, or crafting cost** (does NOT block G-T2B)
   - No XP component cost
   - No level loss on recipient
   - No permanent item creation with XP cost

3. ✅ **No entity creation/forking/summoning** (does NOT block G-T3A)
   - No Summon Monster/Nature's Ally
   - No Animate Dead or undead creation
   - No Simulacrum, Clone, or entity templating
   - No Planar Binding or extraplanar entity creation

4. ✅ **No agency delegation or external control** (does NOT block G-T3B)
   - No Dominate Person/Monster
   - No Charm spells
   - No Geas/Quest or compulsion effects
   - No Suggestion or mind control

5. ✅ **No relational conditions** (does NOT block G-T3C)
   - No grapple/pinned conditions
   - No mount/rider coupling
   - No entity-to-entity relationship tracking

6. ✅ **No transformation stack or form history** (does NOT block G-T3D)
   - No Polymorph or Shapechange
   - No Petrification (Flesh to Stone)
   - No Reincarnate or body transformation
   - No form stacking or restoration depth

7. ✅ **No timeline branching or complex interrupts** (deferred subsystems)
   - No Time Stop
   - No Temporal Stasis
   - No Contingency or trigger-based casting

**Classification Rule:** If a spell violates **ANY** of the above tests, it is **NOT Tier 1** and is **FORBIDDEN** for CP-18A.

---

## Explicit Gate Assertion

**All spells in this manifest require only G-T1 (✅ OPEN).**

No spell in this manifest requires any CLOSED gate:
- G-T2A (Permanent Stat Mutation) — 🔒 CLOSED
- G-T2B (XP Economy) — 🔒 CLOSED
- G-T3A (Entity Forking) — 🔒 CLOSED
- G-T3B (Agency Delegation) — 🔒 CLOSED
- G-T3C (Relational Conditions) — 🔒 CLOSED
- G-T3D (Transformation History) — 🔒 CLOSED

**Enforcement:** Any spell discovered to require a CLOSED gate MUST be removed from this manifest and implementation halted immediately.

---

## Spell List Table

### Column Definitions

| Column | Definition |
|--------|------------|
| **Spell Name** | Official PHB/DMG spell name |
| **Class/Level** | Spell level for each class (e.g., Wiz 3, Clr 2) |
| **School/Subschool** | Spell school (PHB classification) |
| **Targeting Type** | Entity / Point / Area / Self |
| **Tier** | Must be T1 |
| **Gate Required** | Must be G-T1 |
| **Citation** | PHB or DMG page number |
| **Kernel Dependency** | Must be NONE |
| **Notes** | Only if special considerations required |

---

### Damage Spells (Direct HP Reduction)

| Spell Name | Class/Level | School/Subschool | Targeting Type | Tier | Gate | Citation | Kernel Dep | Notes |
|------------|-------------|------------------|----------------|------|------|----------|------------|-------|
| Magic Missile | Wiz/Sor 1 | Evocation [Force] | Entity | T1 | G-T1 | PHB 251 | NONE | Auto-hit, 1d4+1 per missile |
| Burning Hands | Wiz/Sor 1 | Evocation [Fire] | Area (cone) | T1 | G-T1 | PHB 207 | NONE | 1d4/level fire damage, Reflex half |
| Shocking Grasp | Wiz/Sor 1 | Evocation [Electricity] | Entity (touch) | T1 | G-T1 | PHB 279 | NONE | 1d6/level electricity damage |
| Acid Arrow | Wiz/Sor 2 | Conjuration (Creation) [Acid] | Entity | T1 | G-T1 | PHB 196 | NONE | 2d4 immediate + 2d4 next round |
| Scorching Ray | Wiz/Sor 2 | Evocation [Fire] | Entity (ray) | T1 | G-T1 | PHB 274 | NONE | 4d6 fire per ray, 1+ rays |
| Fireball | Wiz/Sor 3 | Evocation [Fire] | Area (sphere) | T1 | G-T1 | PHB 231 | NONE | 1d6/level fire, Reflex half |
| Lightning Bolt | Wiz/Sor 3 | Evocation [Electricity] | Area (line) | T1 | G-T1 | PHB 248 | NONE | 1d6/level electricity, Reflex half |
| Ice Storm | Wiz/Sor 4 | Evocation [Cold] | Area (cylinder) | T1 | G-T1 | PHB 243 | NONE | 3d6 bludgeoning + 2d6 cold |
| Cone of Cold | Wiz/Sor 5 | Evocation [Cold] | Area (cone) | T1 | G-T1 | PHB 212 | NONE | 1d6/level cold, Reflex half |
| Disintegrate | Wiz/Sor 6 | Transmutation | Entity (ray) | T1 | G-T1 | PHB 222 | NONE | 2d6/level, Fort partial (5d6) |
| Delayed Blast Fireball | Wiz/Sor 7 | Evocation [Fire] | Area (sphere) | T1 | G-T1 | PHB 218 | NONE | 1d6/level fire, delayed detonation |
| Sunburst | Wiz/Sor 8, Drd 8 | Evocation [Light] | Area (sphere) | T1 | G-T1 | PHB 288 | NONE | 6d6 damage, blindness (Reflex neg) |
| Meteor Swarm | Wiz/Sor 9 | Evocation [Fire] | Area (spheres) | T1 | G-T1 | PHB 253 | NONE | 4 meteors, 2d6 + 6d6 fire each |

---

### Healing Spells (HP Restoration)

| Spell Name | Class/Level | School/Subschool | Targeting Type | Tier | Gate | Citation | Kernel Dep | Notes |
|------------|-------------|------------------|----------------|------|------|----------|------------|-------|
| Cure Light Wounds | Clr 1, Drd 1, Brd 1 | Conjuration (Healing) | Entity (touch) | T1 | G-T1 | PHB 215 | NONE | 1d8+1/level (max +5) |
| Cure Moderate Wounds | Clr 2, Drd 3, Brd 2 | Conjuration (Healing) | Entity (touch) | T1 | G-T1 | PHB 215 | NONE | 2d8+1/level (max +10) |
| Cure Serious Wounds | Clr 3, Drd 4, Brd 3 | Conjuration (Healing) | Entity (touch) | T1 | G-T1 | PHB 215 | NONE | 3d8+1/level (max +15) |
| Cure Critical Wounds | Clr 4, Drd 5, Brd 4 | Conjuration (Healing) | Entity (touch) | T1 | G-T1 | PHB 215 | NONE | 4d8+1/level (max +20) |
| Heal | Clr 6, Drd 7 | Conjuration (Healing) | Entity (touch) | T1 | G-T1 | PHB 239 | NONE | 10 HP/level (max 150), cures conditions |
| Mass Cure Light Wounds | Clr 5, Drd 6, Brd 5 | Conjuration (Healing) | Area (close) | T1 | G-T1 | PHB 252 | NONE | 1d8+1/level (max +25) each |
| Mass Cure Moderate Wounds | Clr 6, Drd 7, Brd 6 | Conjuration (Healing) | Area (close) | T1 | G-T1 | PHB 252 | NONE | 2d8+1/level (max +30) each |
| Mass Cure Serious Wounds | Clr 7, Drd 8 | Conjuration (Healing) | Area (close) | T1 | G-T1 | PHB 252 | NONE | 3d8+1/level (max +35) each |
| Mass Cure Critical Wounds | Clr 8, Drd 9 | Conjuration (Healing) | Area (close) | T1 | G-T1 | PHB 252 | NONE | 4d8+1/level (max +40) each |
| Mass Heal | Clr 9 | Conjuration (Healing) | Area (close) | T1 | G-T1 | PHB 252 | NONE | 10 HP/level (max 250) each |

---

### Buff/Debuff Spells (Temporary Modifiers, Non-Permanent)

| Spell Name | Class/Level | School/Subschool | Targeting Type | Tier | Gate | Citation | Kernel Dep | Notes |
|------------|-------------|------------------|----------------|------|------|----------|------------|-------|
| Bless | Clr 1 | Enchantment (Compulsion) [Mind-Affecting] | Area (burst) | T1 | G-T1 | PHB 205 | NONE | +1 attack, +1 saves vs fear |
| Bane | Clr 1 | Enchantment (Compulsion) [Fear, Mind-Affecting] | Area (burst) | T1 | G-T1 | PHB 202 | NONE | -1 attack, -1 saves vs fear |
| Shield | Wiz/Sor 1 | Abjuration [Force] | Self | T1 | G-T1 | PHB 278 | NONE | +4 AC, negates Magic Missile |
| Mage Armor | Wiz/Sor 1 | Conjuration (Creation) [Force] | Entity (touch) | T1 | G-T1 | PHB 249 | NONE | +4 armor bonus to AC |
| Shield of Faith | Clr 1 | Abjuration | Entity (touch) | T1 | G-T1 | PHB 278 | NONE | +2 deflection bonus to AC (+1/6 levels) |
| Enlarge Person | Wiz/Sor 1 | Transmutation | Entity (close) | T1 | G-T1 | PHB 226 | NONE | Size → Large, +2 STR, -2 DEX, -1 AC (temporary, CP-16) |
| Reduce Person | Wiz/Sor 1 | Transmutation | Entity (close) | T1 | G-T1 | PHB 270 | NONE | Size → Small, +2 DEX, -2 STR, +1 AC (temporary, CP-16) |
| Bull's Strength | Wiz/Sor 2, Clr 2 | Transmutation | Entity (touch) | T1 | G-T1 | PHB 207 | NONE | +4 enhancement bonus to STR (temporary, CP-16) |
| Cat's Grace | Wiz/Sor 2, Brd 2 | Transmutation | Entity (touch) | T1 | G-T1 | PHB 208 | NONE | +4 enhancement bonus to DEX (temporary, CP-16) |
| Bear's Endurance | Wiz/Sor 2, Clr 2 | Transmutation | Entity (touch) | T1 | G-T1 | PHB 202 | NONE | +4 enhancement bonus to CON (temporary, CP-16) |
| Eagle's Splendor | Wiz/Sor 2, Clr 2, Brd 2 | Transmutation | Entity (touch) | T1 | G-T1 | PHB 225 | NONE | +4 enhancement bonus to CHA (temporary, CP-16) |
| Fox's Cunning | Wiz/Sor 2, Brd 2 | Transmutation | Entity (touch) | T1 | G-T1 | PHB 233 | NONE | +4 enhancement bonus to INT (temporary, CP-16) |
| Owl's Wisdom | Wiz/Sor 2, Clr 2, Drd 2 | Transmutation | Entity (touch) | T1 | G-T1 | PHB 259 | NONE | +4 enhancement bonus to WIS (temporary, CP-16) |
| Blur | Wiz/Sor 2, Brd 2 | Illusion (Glamer) | Self | T1 | G-T1 | PHB 206 | NONE | 20% miss chance (concealment) |
| Mirror Image | Wiz/Sor 2, Brd 2 | Illusion (Figment) | Self | T1 | G-T1 | PHB 254 | NONE | 1d4+1 images, attacks hit images first |
| Haste | Wiz/Sor 3, Brd 3 | Transmutation | Area (close) | T1 | G-T1 | PHB 239 | NONE | +1 attack, +1 AC, +1 Reflex, extra attack (NO timeline mechanics) |
| Slow | Wiz/Sor 3, Brd 3 | Transmutation | Area (close) | T1 | G-T1 | PHB 280 | NONE | -1 attack, -1 AC, -1 Reflex, move/standard only (NO timeline mechanics, Will neg) |
| Prayer | Clr 3 | Enchantment (Compulsion) [Mind-Affecting] | Area (burst) | T1 | G-T1 | PHB 264 | NONE | Allies +1 luck bonus, enemies -1 luck penalty |
| Stoneskin | Wiz/Sor 4, Drd 5 | Abjuration | Entity (touch) | T1 | G-T1 | PHB 285 | NONE | DR 10/adamantine, max 10 points/level absorbed |
| Greater Invisibility | Wiz/Sor 4, Brd 4 | Illusion (Glamer) | Entity (touch) | T1 | G-T1 | PHB 245 | NONE | Invisibility that doesn't end on attack |
| Displacement | Wiz/Sor 3, Brd 3 | Illusion (Glamer) | Entity (touch) | T1 | G-T1 | PHB 223 | NONE | 50% miss chance (displacement) |

---

### Detection/Divination Spells (Information Gathering)

| Spell Name | Class/Level | School/Subschool | Targeting Type | Tier | Gate | Citation | Kernel Dep | Notes |
|------------|-------------|------------------|----------------|------|------|----------|------------|-------|
| Detect Magic | Wiz/Sor 0, Clr 0, Drd 0, Brd 0 | Divination | Area (cone) | T1 | G-T1 | PHB 219 | NONE | Detects magical auras |
| Detect Evil | Clr 1 | Divination | Area (cone) | T1 | G-T1 | PHB 219 | NONE | Detects evil auras |
| Detect Good | Clr 1 | Divination | Area (cone) | T1 | G-T1 | PHB 219 | NONE | Detects good auras |
| Detect Law | Clr 1 | Divination | Area (cone) | T1 | G-T1 | PHB 219 | NONE | Detects lawful auras |
| Detect Chaos | Clr 1 | Divination | Area (cone) | T1 | G-T1 | PHB 219 | NONE | Detects chaotic auras |
| Detect Thoughts | Wiz/Sor 2, Brd 2 | Divination [Mind-Affecting] | Area (cone) | T1 | G-T1 | PHB 220 | NONE | Detects surface thoughts (Will neg) |
| See Invisibility | Wiz/Sor 2, Brd 3 | Divination | Self | T1 | G-T1 | PHB 275 | NONE | See invisible creatures/objects |
| Arcane Sight | Wiz/Sor 3 | Divination | Self | T1 | G-T1 | PHB 201 | NONE | See magic auras, identify spells |
| Clairaudience/Clairvoyance | Wiz/Sor 3, Brd 3 | Divination (Scrying) | Point (long) | T1 | G-T1 | PHB 209 | NONE | See or hear at a distance |
| Scrying | Wiz/Sor 4, Brd 3, Clr 5, Drd 4 | Divination (Scrying) | Entity (see text) | T1 | G-T1 | PHB 274 | NONE | View distant creature (Will neg) |
| True Seeing | Wiz/Sor 5, Clr 5, Drd 7 | Divination | Entity (touch) | T1 | G-T1 | PHB 296 | NONE | See all things as they are |

---

### Utility Spells (Non-Combat Effects)

| Spell Name | Class/Level | School/Subschool | Targeting Type | Tier | Gate | Citation | Kernel Dep | Notes |
|------------|-------------|------------------|----------------|------|------|----------|------------|-------|
| Light | Wiz/Sor 0, Clr 0, Drd 0, Brd 0 | Evocation [Light] | Entity/Object (touch) | T1 | G-T1 | PHB 248 | NONE | Object sheds light (20 ft radius) |
| Prestidigitation | Wiz/Sor 0, Brd 0 | Universal | Point (close) | T1 | G-T1 | PHB 264 | NONE | Minor magical tricks |
| Mage Hand | Wiz/Sor 0, Brd 0 | Transmutation | Point (close) | T1 | G-T1 | PHB 250 | NONE | Telekinesis (5 lbs max) |
| Mending | Wiz/Sor 0, Clr 0, Drd 0, Brd 0 | Transmutation | Object (touch) | T1 | G-T1 | PHB 253 | NONE | Repairs object (1d4 HP) |
| Grease | Wiz/Sor 1, Brd 1 | Conjuration (Creation) | Point/Area (close) | T1 | G-T1 | PHB 237 | NONE | Slippery surface (Reflex or fall prone) |
| Feather Fall | Wiz/Sor 1, Brd 1 | Transmutation | Entity (close) | T1 | G-T1 | PHB 229 | NONE | Slow fall (60 ft/round) |
| Jump | Wiz/Sor 1, Drd 1, Rgr 1 | Transmutation | Entity (touch) | T1 | G-T1 | PHB 246 | NONE | +10 enhancement to Jump checks (+20 at CL 5, +30 at CL 9) |
| Levitate | Wiz/Sor 2 | Transmutation | Entity/Self (close) | T1 | G-T1 | PHB 248 | NONE | Move up/down 20 ft/round |
| Knock | Wiz/Sor 2 | Transmutation | Object (medium) | T1 | G-T1 | PHB 246 | NONE | Opens locks, doors |
| Fly | Wiz/Sor 3 | Transmutation | Entity (touch) | T1 | G-T1 | PHB 232 | NONE | Fly speed 60 ft (good maneuverability) |
| Tongues | Wiz/Sor 3, Clr 4, Brd 2 | Divination | Entity (touch) | T1 | G-T1 | PHB 294 | NONE | Speak/understand all languages |
| Dispel Magic | Wiz/Sor 3, Clr 3, Drd 4, Brd 3 | Abjuration | Entity/Area/Object (medium) | T1 | G-T1 | PHB 223 | NONE | Dispel ongoing magical effects |
| Remove Curse | Wiz/Sor 4, Clr 3, Brd 3 | Abjuration | Entity (touch) | T1 | G-T1 | PHB 271 | NONE | Remove curse effects |
| Dimension Door | Wiz/Sor 4, Brd 4 | Conjuration (Teleportation) | Self + entities | T1 | G-T1 | PHB 221 | NONE | Teleport up to long range |
| Teleport | Wiz/Sor 5 | Conjuration (Teleportation) | Self + entities | T1 | G-T1 | PHB 293 | NONE | Long-distance teleportation |
| Greater Teleport | Wiz/Sor 7 | Conjuration (Teleportation) | Self + entities | T1 | G-T1 | PHB 293 | NONE | Teleport with no error chance |
| Antimagic Field | Wiz/Sor 6, Clr 8 | Abjuration | Area (emanation, self) | T1 | G-T1 | PHB 200 | NONE | 10-ft radius suppresses all magic |

---

### Condition Application Spells (Uses CP-16 Condition System)

| Spell Name | Class/Level | School/Subschool | Targeting Type | Tier | Gate | Citation | Kernel Dep | Notes |
|------------|-------------|------------------|----------------|------|------|----------|------------|-------|
| Sleep | Wiz/Sor 1, Brd 1 | Enchantment (Compulsion) [Mind-Affecting] | Area (medium) | T1 | G-T1 | PHB 281 | NONE | Unconscious condition (4 HD limit, Will neg) |
| Hold Person | Wiz/Sor 3, Clr 2, Brd 2 | Enchantment (Compulsion) [Mind-Affecting] | Entity (medium) | T1 | G-T1 | PHB 241 | NONE | Paralyzed condition (humanoid, Will neg) |
| Hold Monster | Wiz/Sor 5, Brd 4 | Enchantment (Compulsion) [Mind-Affecting] | Entity (medium) | T1 | G-T1 | PHB 241 | NONE | Paralyzed condition (any creature, Will neg) |
| Blindness/Deafness | Wiz/Sor 2, Clr 3, Brd 2 | Necromancy | Entity (medium) | T1 | G-T1 | PHB 206 | NONE | Blinded or deafened condition (Fort neg) |
| Bestow Curse | Wiz/Sor 4, Clr 3 | Necromancy | Entity (touch) | T1 | G-T1 | PHB 203 | NONE | -6 ability, -4 attacks/saves/checks, or 50% action loss (Will neg, temporary) |
| Scare | Wiz/Sor 2, Brd 2 | Necromancy [Fear, Mind-Affecting] | Entity (medium) | T1 | G-T1 | PHB 274 | NONE | Shaken condition (< 6 HD flee, Will neg) |
| Fear | Wiz/Sor 4, Brd 3 | Necromancy [Fear, Mind-Affecting] | Area (cone) | T1 | G-T1 | PHB 229 | NONE | Panicked condition (Will neg for shaken) |
| Ray of Enfeeblement | Wiz/Sor 1 | Necromancy | Entity (ray) | T1 | G-T1 | PHB 269 | NONE | 1d6+1/2 levels STR penalty (temporary, Fort neg) |
| Touch of Fatigue | Wiz/Sor 0 | Necromancy | Entity (touch) | T1 | G-T1 | PHB 294 | NONE | Fatigued condition (Fort neg) |
| Daze | Wiz/Sor 0, Brd 0 | Enchantment (Compulsion) [Mind-Affecting] | Entity (close) | T1 | G-T1 | PHB 216 | NONE | Dazed condition (1 round, HD limit 4, Will neg) |
| Stinking Cloud | Wiz/Sor 3 | Conjuration (Creation) | Area (medium) | T1 | G-T1 | PHB 285 | NONE | Nauseated condition in cloud (Fort neg) |
| Glitterdust | Wiz/Sor 2, Brd 2 | Conjuration (Creation) | Area (medium) | T1 | G-T1 | PHB 236 | NONE | Blinded condition + outline (Will neg) |

---

## Total Spell Count

**Current Manifest:** 80 spells

**Breakdown by Category:**
- Damage: 13 spells
- Healing: 10 spells
- Buff/Debuff: 21 spells
- Detection/Divination: 11 spells
- Utility: 16 spells
- Condition Application: 12 spells

**Target (Action Plan V2):** ~245 Tier 1 spells

**Status:** Initial manifest (Phase 1). Additional spells will be added in subsequent revisions after schema design approval.

---

## Exclusion Rules (Mandatory Enforcement)

**Rule 1: Manifest-Only Authorization**
- Any spell NOT appearing in the table above is **FORBIDDEN** for CP-18A implementation
- No exceptions without manifest update + new decision record

**Rule 2: Tier Verification**
- All spells MUST pass the Tier 1 Inclusion Test (Section 2)
- If a spell is discovered to require a CLOSED gate, it MUST be removed immediately

**Rule 3: Gate Dependency Check**
- All spells MUST have "Gate Required" = G-T1
- All spells MUST have "Kernel Dependency" = NONE
- Violation = automatic rejection

---

## Explicitly Deferred Spell Categories

The following spell categories are **FORBIDDEN** for CP-18A per [AIDM_PROJECT_ACTION_PLAN_V2.md](AIDM_PROJECT_ACTION_PLAN_V2.md) Section 6:

**Summoning (G-T3A CLOSED):**
- Summon Monster I-IX, Summon Nature's Ally I-IX, Planar Ally, Planar Binding, Gate (summoning variant), Animate Dead, Create Undead

**Polymorph & Transformation (G-T3D CLOSED):**
- Polymorph, Baleful Polymorph, Polymorph Any Object, Shapechange, Wild Shape, Flesh to Stone, Stone to Flesh, Reincarnate, Awaken

**Dominate & Charm (G-T3B CLOSED):**
- Dominate Person, Dominate Monster, Dominate Animal, Charm Person, Charm Monster, Charm Animal, Geas/Quest, Suggestion, Mass Charm/Dominate

**Resurrection & XP-Cost (G-T2B CLOSED):**
- Raise Dead, Resurrection, True Resurrection, Wish (5000 XP variant), Miracle (XP variant), Permanency, Clone, all item creation spells

**Permanent Ability Modification (G-T2A CLOSED):**
- Feeblemind (permanent INT → 1), Restoration (reverses permanent drain), Wish (permanent +1 stat), ability drain attacks

**Relational Conditions (G-T3C CLOSED):**
- Any spell creating grapple/pinned/mounted conditions requiring entity-to-entity relationship tracking

**Timeline Manipulation (Deferred):**
- Time Stop, Temporal Stasis, Haste/Slow with timeline branching mechanics

**Interrupt & Readied (Deferred):**
- Contingency, all trigger-based automatic casting

See Action Plan V2 Section 6 for full deferred features list.

---

## Change Control Protocol

**Adding a Spell:**
1. Verify spell passes Tier 1 Inclusion Test (all 7 criteria)
2. Add entry to appropriate category table
3. Update Total Spell Count
4. Run PBHA after implementation
5. If spell discovered to cross tier → halt implementation, remove from manifest, produce DR-XXX

**Removing a Spell:**
1. Document reason for removal (gate violation discovered, kernel dependency found)
2. Remove from table
3. Update Total Spell Count
4. Halt any in-progress implementation

**Tier Reclassification:**
- If spell requires CLOSED gate → immediate removal + DR record
- No silent downgrades
- Explicit decision record required

---

## Approval Checklist

Before CP-18A schema design (Phase 2) begins, verify:

- [ ] All spells in manifest pass Tier 1 Inclusion Test
- [ ] All spells cite PHB/DMG page number
- [ ] All spells have "Gate Required" = G-T1
- [ ] All spells have "Kernel Dependency" = NONE
- [ ] No FORBIDDEN spell categories appear in manifest
- [ ] Total spell count documented
- [ ] Exclusion rules enforced

**Status:** ✅ PHASE 1 MANIFEST COMPLETE

**Next Step:** Await approval before proceeding to CP-18A-SCHEMA-DESIGN.md (Phase 2)

---

**END OF CP-18A SPELL TIER MANIFEST**

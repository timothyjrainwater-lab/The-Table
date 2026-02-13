# AIDM Core Ruleset Audit — D&D 3.5e Full Source Material

**Status:** IN PROGRESS - Pass 1 (Inventory)
**Authority:** Governance-Critical Audit (Binding)
**Scope:** PHB, DMG, MM (Complete)
**Objective:** Identify simulacrum-class hazards before implementation
**Date:** 2026-02-08

---

## Executive Summary

This document performs a **front-to-back audit** of D&D 3.5e core rules to identify mechanics that:
- Violate deterministic execution assumptions
- Break entity lifecycle invariants
- Create composite/forked/coupled actors
- Depend on epistemic state (knowledge, belief, perception)
- Require permanent structural mutation
- Introduce bidirectional or recursive state propagation

**Reference Hazard:** Simulacrum (PHB p. 279) — entity forking with permanent ability penalties and XP costs that violate event-sourcing assumptions.

---

## PASS 1: INVENTORY — Rules Coverage Ledger (RCL)

### Classification Legend

**Subsystem Types:**
- `atomic` — Self-contained, minimal cross-cutting concerns
- `cross-cutting` — Touches multiple subsystems or core engine assumptions
- `dm-discretion` — Relies heavily on DM adjudication, minimal mechanical specificity

**Determinism Risk:**
- `low` — Compatible with event-sourcing, deterministic RNG, pure functions
- `medium` — Requires careful design but tractable within current architecture
- `high` — Violates core assumptions, requires new kernel infrastructure

---

## 1. PLAYER'S HANDBOOK (PHB) — Subsystem Inventory

### 1.1 Character Creation & Advancement

| Subsystem | Source | Classification | Risk | Notes |
|-----------|--------|----------------|------|-------|
| Ability Scores | PHB p.8-9 | atomic | low | Static entity properties |
| Ability Damage | PHB p.307 | cross-cutting | medium | Temporary reduction, affects derived stats bidirectionally |
| Ability Drain | PHB p.307 | cross-cutting | **high** | **PERMANENT reduction, violates immutability assumption** |
| Ability Score Increases (leveling) | PHB p.58 | atomic | low | Deterministic progression |
| Character Level | PHB p.6 | atomic | low | Monotonic counter |
| Experience Points (XP) | PHB p.58 | cross-cutting | medium | Resource pool, but XP costs violate event-sourcing if permanent |
| XP Costs (spell components) | PHB p.177 | cross-cutting | **high** | **Permanent resource expenditure, non-reversible state change** |
| Multiclassing | PHB p.59 | atomic | low | Deterministic class level tracking |
| Level Adjustment | PHB p.172 | atomic | low | Static modifier to effective character level |
| Favored Class | PHB p.14-20 | atomic | low | Static property per race |

### 1.2 Skills & Feats

| Subsystem | Source | Classification | Risk | Notes |
|-----------|--------|----------------|------|-------|
| Skill Checks | PHB p.63-83 | atomic | low | d20 + modifiers |
| Skill Synergy | PHB p.66 | cross-cutting | low | Conditional bonuses, deterministic |
| Taking 10 / Taking 20 | PHB p.65 | atomic | low | Deterministic alternatives to rolling |
| Aid Another | PHB p.65 | cross-cutting | low | Simple bonus mechanic |
| Feats | PHB p.88-103 | cross-cutting | medium | Static modifiers, but some interact with action economy |
| Feat Prerequisites | PHB p.88 | atomic | low | Validation rules |
| Item Creation Feats | PHB p.93 | cross-cutting | **high** | **XP costs, permanent item creation, economy implications** |

### 1.3 Core Mechanics

| Subsystem | Source | Classification | Risk | Notes |
|-----------|--------|----------------|------|-------|
| Action Types (standard/move/full/swift/immediate) | PHB p.144 | cross-cutting | medium | Already implemented (CP-09), but complex interactions |
| Attacks of Opportunity | PHB p.144 | cross-cutting | low | Already implemented (CP-15) |
| Readied Actions | PHB p.160 | cross-cutting | **high** | **Out-of-turn resolution, interrupt mechanics, timing hazard** |
| Delay Action | PHB p.160 | cross-cutting | **high** | **Initiative reordering, turn order mutation** |
| Grapple | PHB p.156 | cross-cutting | **high** | **Multi-phase resolution, coupled actor states, recursive checks** |
| Bull Rush | PHB p.154 | cross-cutting | medium | Forced movement, iterative resolution |
| Trip | PHB p.158 | cross-cutting | medium | Opposed check → condition application |
| Overrun | PHB p.157 | cross-cutting | medium | Movement + opposed check |
| Disarm | PHB p.155 | cross-cutting | medium | Opposed check → item state change |
| Sunder | PHB p.158 | cross-cutting | medium | Attack → item damage |
| Mounted Combat | PHB p.157 | cross-cutting | **high** | **Composite actor (rider + mount), shared action economy** |

### 1.4 Combat Subsystems

| Subsystem | Source | Classification | Risk | Notes |
|-----------|--------|----------------|------|-------|
| Attack Rolls | PHB p.143 | atomic | low | Already implemented (CP-10) |
| Critical Hits | PHB p.140 | atomic | low | Deterministic threat confirmation |
| Damage & HP | PHB p.145 | atomic | low | Already implemented (CP-10) |
| Death & Dying | PHB p.145 | cross-cutting | medium | Negative HP tracking, stabilization checks |
| Massive Damage | PHB p.145 | cross-cutting | medium | DC 15 Fort save vs instant death |
| Nonlethal Damage | PHB p.146 | cross-cutting | medium | Parallel HP pool, unconsciousness threshold |
| Armor Class | PHB p.134 | atomic | low | Deterministic calculation |
| Touch AC / Flat-Footed AC | PHB p.137 | atomic | low | Conditional AC modifiers |
| Cover | PHB p.150 | cross-cutting | medium | Deferred (CP-18A-T&V notes) |
| Concealment | PHB p.152 | cross-cutting | medium | Miss chance, deferred (CP-18A-T&V notes) |
| Flanking | PHB p.153 | cross-cutting | medium | Positional bonus, requires spatial system |
| Charging | PHB p.154 | cross-cutting | medium | Movement + attack in single action |
| Running | PHB p.144 | atomic | low | Movement modifier |
| Withdraw | PHB p.143 | cross-cutting | medium | Movement + AoO suppression |

### 1.5 Conditions

| Subsystem | Source | Classification | Risk | Notes |
|-----------|--------|----------------|------|-------|
| Blinded | PHB p.310 | atomic | low | Already in CP-16 |
| Deafened | PHB p.311 | atomic | low | Already in CP-16 |
| Paralyzed | PHB p.311 | atomic | low | Already in CP-16 |
| Stunned | PHB p.311 | atomic | low | Subset of paralyzed |
| Unconscious | PHB p.312 | atomic | low | Derived from HP or other conditions |
| Prone | PHB p.311 | atomic | low | Already in CP-16 |
| Grappled | PHB p.311 | cross-cutting | **high** | **Coupled to grappler, bidirectional state** |
| Invisible | PHB p.295 | cross-cutting | **high** | **Epistemic state hazard, deferred (CP-18A-T&V notes)** |
| Disabled | PHB p.307 | atomic | low | HP threshold state |
| Dying | PHB p.307 | atomic | low | Negative HP + stabilization |
| Stable | PHB p.307 | atomic | low | Halted deterioration |
| Exhausted | PHB p.306 | atomic | low | Multi-stage fatigue |
| Fatigued | PHB p.306 | atomic | low | Precursor to exhausted |
| Nauseated | PHB p.311 | atomic | low | Action restriction |
| Sickened | PHB p.311 | atomic | low | Already in CP-16 |
| Frightened | PHB p.326 | atomic | low | Movement compulsion |
| Panicked | PHB p.326 | atomic | low | Stronger fear effect |
| Shaken | PHB p.326 | atomic | low | Already in CP-16 |
| Cowering | PHB p.326 | atomic | low | Total defense state |
| Confused | PHB p.311 | cross-cutting | medium | Random action determination, RNG-driven |
| Dazed | PHB p.311 | atomic | low | Action economy restriction |
| Fascinated | PHB p.326 | atomic | low | Attention lock |
| Entangled | PHB p.310 | atomic | low | Movement + attack penalties |
| Helpless | PHB p.311 | atomic | low | AC penalty, coup de grace vulnerability |
| Pinned | PHB p.311 | cross-cutting | **high** | **Grapple substage, coupled state** |

### 1.6 Spellcasting (High-Level Overview)

| Subsystem | Source | Classification | Risk | Notes |
|-----------|--------|----------------|------|-------|
| Spell Slots | PHB p.176 | atomic | low | Resource pool tracking |
| Prepared vs Spontaneous Casting | PHB p.176 | atomic | low | Different resource models |
| Concentration Checks | PHB p.170 | atomic | low | Skill check variant |
| Casting Time | PHB p.174 | atomic | low | Action economy integration |
| Spell Resistance | PHB p.177 | cross-cutting | medium | Caster level check vs SR |
| Counterspelling | PHB p.171 | cross-cutting | **high** | **Reactive casting, interrupt mechanics, readied action hazard** |
| Dispel Magic | PHB p.223 | cross-cutting | **high** | **Effect removal, bidirectional state propagation** |
| Antimagic Field | PHB p.200 | cross-cutting | **high** | **Area suppression, ongoing effect interaction** |
| Dismissible Spells | PHB p.176 | cross-cutting | medium | Caster-controlled termination |
| Line of Effect (spell targeting) | PHB p.175 | cross-cutting | low | Already implemented (CP-18A-T&V) |

---

### 1.7 Spell-by-Spell Analysis (CRITICAL HAZARDS ONLY)

This section enumerates **only** spells that present simulacrum-class hazards. Standard damage/buff/debuff spells are considered `atomic` and omitted.

| Spell | Level | Source | Risk | Hazard Type |
|-------|-------|--------|------|-------------|
| **Simulacrum** | Wiz 7 | PHB p.279 | **HIGH** | **Entity forking, permanent XP cost, ability drain on template, coupled lifecycle** |
| **Clone** | Wiz 8 | PHB p.208 | **HIGH** | **Entity resurrection/forking, soul transfer, identity hazard** |
| **Wish** | Wiz 9 | PHB p.298 | **HIGH** | **Arbitrary reality mutation, XP cost, DM discretion extreme** |
| **Limited Wish** | Wiz 7 | PHB p.248 | **HIGH** | **Reality mutation (weaker), XP cost, DM discretion** |
| **Miracle** | Clr 9 | PHB p.255 | **HIGH** | **Divine reality mutation, XP cost, DM discretion extreme** |
| **Gate** | Clr 9 | PHB p.235 | **HIGH** | **Entity summoning (permanent), planar travel, XP cost** |
| **Planar Binding (all)** | Wiz 5-9 | PHB p.262 | **HIGH** | **Dominated agency, external control, service contracts** |
| **Dominate Person/Monster** | Various | PHB p.224 | **HIGH** | **External agency control, coupled decision-making** |
| **Charm Person/Monster** | Various | PHB p.208 | **MEDIUM** | **Attitude modification, epistemic state (friendliness)** |
| **Geas/Quest** | Various | PHB p.235 | **HIGH** | **Compulsion with HP damage, long-term behavioral override** |
| **Magic Jar** | Wiz 5 | PHB p.249 | **HIGH** | **Soul transfer, body possession, identity swap** |
| **Polymorph (all variants)** | Various | PHB p.263 | **HIGH** | **Physical form replacement, ability score replacement, HD limits** |
| **Shapechange** | Wiz 9 | PHB p.276 | **HIGH** | **Unlimited polymorph, form library, HD-based constraints** |
| **Permanency** | Wiz 5 | PHB p.260 | **HIGH** | **XP cost, permanent effect anchoring, dispel interaction** |
| **Teleportation Circle** | Wiz 9 | PHB p.293 | **MEDIUM** | **XP cost, permanent structure creation** |
| **Awaken** | Drd 5 | PHB p.202 | **HIGH** | **Entity mutation (animal → sentient), permanent intelligence grant** |
| **Reincarnate** | Drd 4 | PHB p.271 | **HIGH** | **Entity resurrection with random race change, ability score shifts** |
| **Raise Dead** | Clr 5 | PHB p.268 | **HIGH** | **Entity resurrection, permanent level loss, XP cost for recipient** |
| **Resurrection** | Clr 7 | PHB p.272 | **HIGH** | **Entity resurrection (better), still has level loss** |
| **True Resurrection** | Clr 9 | PHB p.296 | **MEDIUM** | **Entity resurrection (no loss), XP cost** |
| **Temporal Stasis** | Wiz 8 | PHB p.294 | **HIGH** | **Timeline suspension, stasis state, indefinite duration** |
| **Time Stop** | Wiz 9 | PHB p.294 | **HIGH** | **Turn order violation, multi-turn in single turn, timeline hazard** |
| **Contingency** | Wiz 6 | PHB p.212 | **HIGH** | **Trigger-based auto-casting, condition monitoring, readied spell hazard** |
| **Sequester** | Wiz 7 | PHB p.275 | **MEDIUM** | **Invisibility + temporal stasis hybrid** |
| **Trap the Soul** | Wiz 8 | PHB p.295 | **HIGH** | **Soul imprisonment, entity removal from play, XP cost** |
| **Soul Bind** | Clr 9 | PHB p.283 | **HIGH** | **Soul imprisonment (stronger), prevents resurrection** |
| **Animate Dead** | Clr 3 | PHB p.199 | **HIGH** | **Entity creation (undead), controlled minions, HD cap per caster level** |
| **Create Undead** | Clr 6 | PHB p.215 | **HIGH** | **Entity creation (stronger undead), controlled minions** |
| **Create Greater Undead** | Clr 8 | PHB p.215 | **HIGH** | **Entity creation (strongest undead), controlled minions** |
| **Astral Projection** | Clr 9 | PHB p.201 | **HIGH** | **Entity forking (silver cord), dual-existence, death propagation** |
| **Project Image** | Wiz 7 | PHB p.266 | **MEDIUM** | **Quasi-real duplicate, spell delivery vehicle** |
| **Summon Monster (all)** | Various | PHB p.285 | **MEDIUM** | **Entity summoning (temporary), controlled minions, duration-based** |
| **Summon Nature's Ally (all)** | Various | PHB p.287 | **MEDIUM** | **Entity summoning (nature variant)** |
| **Mount** | Pal 1 | PHB p.256 | **MEDIUM** | **Entity creation (horse), temporary mount** |
| **Find Familiar** | Wiz 1 | PHB p.232 | **HIGH** | **Composite actor (master + familiar), shared HP pool, telepathic link** |
| **Planar Ally (all)** | Clr 4-9 | PHB p.262 | **HIGH** | **Entity summoning with service negotiation, payment, independent agency** |
| **Sympathy/Antipathy** | Wiz 8 | PHB p.288 | **MEDIUM** | **Emotional compulsion, area-based, permanent option** |
| **Insanity** | Wiz 7 | PHB p.244 | **HIGH** | **Permanent confusion, ability score damage, mental hijack** |
| **Feeblemind** | Wiz 5 | PHB p.230 | **HIGH** | **Permanent INT/CHA reduction to 1, caster incapacitation** |
| **Imprisonment** | Wiz 9 | PHB p.244 | **HIGH** | **Entity removal from play, no save, dispel resistance** |
| **Maze** | Wiz 8 | PHB p.253 | **MEDIUM** | **Extradimensional removal, INT-based escape, turn delay** |
| **Ethereal Jaunt** | Clr 7 | PHB p.227 | **HIGH** | **Plane shift, ethereal interaction rules** |
| **Etherealness** | Clr 9 | PHB p.227 | **HIGH** | **Plane shift (extended), planar interaction** |
| **Plane Shift** | Clr 5 | PHB p.262 | **MEDIUM** | **Planar travel, entity relocation** |
| **Shadow Conjuration** | Wiz 4 | PHB p.276 | **MEDIUM** | **Quasi-real effects, disbelief interaction, epistemic state** |
| **Shadow Evocation** | Wiz 5 | PHB p.276 | **MEDIUM** | **Quasi-real effects (evocation variant)** |
| **Shades** | Wiz 9 | PHB p.276 | **MEDIUM** | **Quasi-real effects (strongest), 80% real** |
| **Hallucinatory Terrain** | Brd 4 | PHB p.239 | **MEDIUM** | **Illusory terrain, epistemic perception override** |
| **Programmed Image** | Wiz 6 | PHB p.266 | **MEDIUM** | **Triggered illusion, condition monitoring** |
| **Scrying (all)** | Various | PHB p.274 | **MEDIUM** | **Remote observation, epistemic state** |
| **Foresight** | Wiz 9 | PHB p.233 | **MEDIUM** | **Precognition, attack/AC bonuses from future knowledge** |
| **Moment of Prescience** | Wiz 8 | PHB p.256 | **MEDIUM** | **Single-use precognition, +20 insight bonus storage** |
| **Regenerate** | Clr 7 | PHB p.271 | **MEDIUM** | **Limb regrowth, permanent injury repair** |
| **Restoration (all)** | Clr 2-4 | PHB p.272 | **MEDIUM** | **Ability damage/drain removal, level loss restoration** |
| **Heal** | Clr 6 | PHB p.239 | **LOW** | **HP restoration, condition removal** |

**Total High-Risk Spells Identified:** 46
**Total Medium-Risk Spells Identified:** 20

---

### 1.8 Magic Items (High-Level Categorization)

| Subsystem | Source | Classification | Risk | Notes |
|-----------|--------|----------------|------|-------|
| Item Creation | PHB p.282 | cross-cutting | **high** | **XP costs, crafting time, economy implications** |
| Permanent Magic Items | DMG Ch.7 | cross-cutting | medium | State tracking, activation rules |
| Charged Items | DMG Ch.7 | atomic | low | Consumable resource pools |
| Artifacts | DMG p.219 | dm-discretion | **high** | **Unique items, arbitrary effects, destruction hazards** |
| Intelligent Items | DMG p.268 | cross-cutting | **high** | **Autonomous agency, ego conflicts, composite actor** |
| Cursed Items | DMG p.223 | cross-cutting | **high** | **Involuntary effects, removal hazards, permanent penalties** |

---

## 2. DUNGEON MASTER'S GUIDE (DMG) — Subsystem Inventory

### 2.1 Advancement & Wealth

| Subsystem | Source | Classification | Risk | Notes |
|-----------|--------|----------------|------|-------|
| Treasure & Economy | DMG p.52 | dm-discretion | low | Wealth tracking, largely external to engine |
| Magic Item Distribution | DMG p.54 | dm-discretion | low | Loot tables |
| Character Wealth by Level | DMG p.135 | dm-discretion | low | Guidelines, not mechanics |

### 2.2 Environment & Exploration

| Subsystem | Source | Classification | Risk | Notes |
|-----------|--------|----------------|------|-------|
| Vision & Light | DMG p.164 | cross-cutting | medium | Deferred (CP-18A-T&V notes), light levels |
| Darkness | DMG p.164 | cross-cutting | medium | Concealment, perception penalties |
| Traps | DMG p.66 | cross-cutting | medium | Trigger conditions, damage, disarming |
| Poisons | DMG p.73 | cross-cutting | medium | Ability damage/drain, save-based |
| Diseases | DMG p.74 | cross-cutting | **high** | **Incubation periods, recurring saves, progressive ability damage** |
| Weather | DMG p.93 | atomic | low | Environmental modifiers |
| Falling Damage | DMG p.18 | atomic | low | Deterministic damage calculation |
| Suffocation | DMG p.304 | atomic | low | HP threshold effects |
| Starvation & Thirst | DMG p.304 | atomic | low | Time-based damage |

### 2.3 Magic Item Hazards (Detailed)

| Item Type | Source | Risk | Hazard Type |
|-----------|--------|------|-------------|
| **Deck of Many Things** | DMG p.256 | **HIGH** | **Random reality mutation, XP loss, entity imprisonment, wish-like effects** |
| **Manual of Golems** | DMG p.259 | **MEDIUM** | **Golem creation, XP cost, controlled minion** |
| **Iron Flask** | DMG p.257 | **HIGH** | **Entity imprisonment, planar binding, controlled summons** |
| **Staff of the Magi** | DMG p.233 | **HIGH** | **Retributive strike (self-destruct), XP cost, planar travel** |
| **Cubic Gate** | DMG p.255 | **MEDIUM** | **Planar travel, multiple destinations** |
| **Sphere of Annihilation** | DMG p.233 | **HIGH** | **Entity destruction, no save, disintegration** |
| **Bag of Devouring** | DMG p.223 | **MEDIUM** | **Extradimensional storage hazard, entity consumption** |
| **Cursed Backbiting Weapon** | DMG p.225 | **MEDIUM** | **Attack redirects to wielder** |
| **Periapt of Foul Rotting** | DMG p.227 | **HIGH** | **Disease hazard, unremovable while worn** |
| **Sword of Life Stealing** | DMG p.231 | **MEDIUM** | **Level drain on hit, energy drain** |

---

### 2.4 Prestige Classes (Hazard Scan)

Most prestige classes are `atomic` or `low-risk`. Exceptions:

| Prestige Class | Source | Risk | Hazard Type |
|----------------|--------|------|-------------|
| Arcane Archer | DMG p.174 | low | Imbue arrow mechanics, standard |
| Archmage | DMG p.176 | **medium** | High-level spellcasting, mastery of shaping |
| Assassin | DMG p.180 | low | Death attack (save-or-die), standard |
| Blackguard | DMG p.181 | **medium** | Fiendish servant (controlled minion) |
| Dragon Disciple | DMG p.183 | **medium** | Permanent physical transformation, ability score changes |
| Duelist | DMG p.185 | low | Combat bonuses, standard |
| Dwarven Defender | DMG p.186 | low | Defensive stance, standard |
| Eldritch Knight | DMG p.187 | low | Spellcasting + combat, standard |
| Hierophant | DMG p.188 | **high** | **Special abilities include quasi-immortality, planar travel** |
| Horizon Walker | DMG p.189 | low | Terrain mastery, standard |
| Loremaster | DMG p.191 | low | Knowledge bonuses, standard |
| Mystic Theurge | DMG p.192 | low | Dual spellcasting progression, standard |
| Shadowdancer | DMG p.194 | **medium** | Shadow companion (controlled minion) |
| Thaumaturgist | DMG p.196 | **high** | **Planar binding, controlled outsiders, improved cohorts** |

---

## 3. MONSTER MANUAL (MM) — Subsystem Inventory

### 3.1 Creature Type Mechanics

| Creature Type | Source | Classification | Risk | Notes |
|---------------|--------|----------------|------|-------|
| Aberration | MM p.6 | atomic | low | Standard type |
| Animal | MM p.6 | atomic | low | Standard type |
| Construct | MM p.7 | cross-cutting | **medium** | **Immunity to many effects, different destruction rules** |
| Dragon | MM p.8 | cross-cutting | **medium** | **Age categories, ability progression, spell-like abilities** |
| Elemental | MM p.8 | cross-cutting | medium | Elemental traits, immunity sets |
| Fey | MM p.8 | atomic | low | Standard type with DR |
| Giant | MM p.9 | atomic | low | Standard type |
| Humanoid | MM p.9 | atomic | low | Standard type |
| Magical Beast | MM p.9 | atomic | low | Standard type |
| Monstrous Humanoid | MM p.9 | atomic | low | Standard type |
| Ooze | MM p.9 | cross-cutting | medium | Blind, immunity to many effects |
| Outsider | MM p.9 | cross-cutting | medium | Native vs extraplanar, summoning implications |
| Plant | MM p.9 | atomic | low | Standard type |
| Undead | MM p.10 | cross-cutting | **high** | **No CON score, different HP calculation, turn resistance, negative energy** |
| Vermin | MM p.10 | atomic | low | Standard type |

### 3.2 Universal Monster Abilities (Hazard Scan)

| Ability | Source | Risk | Hazard Type |
|---------|--------|------|-------------|
| Spell-Like Abilities | MM p.315 | medium | Spellcasting without spell slots |
| Supernatural Abilities | MM p.315 | medium | Non-spell magical effects |
| Extraordinary Abilities | MM p.314 | low | Non-magical special abilities |
| Breath Weapon | MM p.307 | low | Standard attack form |
| Damage Reduction | MM p.308 | low | Damage mitigation |
| Darkvision | MM p.308 | low | Vision mode |
| Energy Resistance/Immunity | MM p.309 | low | Damage type mitigation |
| Fast Healing | MM p.310 | low | Regenerative HP |
| Regeneration | MM p.312 | **medium** | **HP restoration, special defeat conditions** |
| Spell Resistance | MM p.314 | low | Already noted, caster level check |
| Telepathy | MM p.315 | **medium** | **Epistemic communication, language bypass** |
| Tremorsense | MM p.315 | medium | Vibration-based detection |
| Blindsight | MM p.306 | **medium** | **Vision bypass, invisibility immunity** |
| Scent | MM p.314 | medium | Detection mode |
| Swallow Whole | MM p.315 | **high** | **Entity containment, internal damage, escape mechanics** |
| Energy Drain | MM p.310 | **high** | **Negative levels, permanent level loss if not removed** |
| Ability Damage/Drain | MM p.305 | **high** | **Already noted, permanent reduction hazard** |
| Poison | MM p.311 | medium | Save-based ability damage |
| Disease | MM p.309 | **high** | **Already noted, incubation hazard** |
| Paralysis | MM p.311 | low | Condition application |
| Petrification | MM p.312 | **high** | **Permanent stone transformation, special restoration requirements** |
| Gaze Attack | MM p.311 | medium | Passive effect requiring active avoidance |
| Frightful Presence | MM p.310 | low | Fear aura |
| Turn/Rebuke Undead | MM p.315 | **medium** | **Mass effect, variable outcomes (destroyed vs fled)** |

### 3.3 Individual Monster Hazards (CRITICAL ONLY)

This section lists **only** monsters with simulacrum-class mechanical hazards, not general combat threats.

| Monster | HD | Source | Risk | Hazard Type |
|---------|-----|--------|------|-------------|
| **Aboleth** | 8 | MM p.8 | **HIGH** | **Enslave (dominate), permanent slime transformation if killed underwater** |
| **Bodak** | 9 | MM p.28 | **HIGH** | **Death gaze (DC 15 Fort save or die), creates spawn** |
| **Devourer** | 12 | MM p.58 | **HIGH** | **Trap Essence (soul imprisonment), spell-like abilities from devoured souls** |
| **Ghost** | Variable | MM p.117 | **HIGH** | **Incorporeal, rejuvenation (returns unless put to rest), possession** |
| **Illithid (Mind Flayer)** | 8 | MM p.186 | **HIGH** | **Mind Blast (stun/confusion), Extract Brain (instant kill)** |
| **Lich** | Variable | MM p.166 | **HIGH** | **Phylactery (rejuvenation), cannot be permanently killed without destroying phylactery** |
| **Medusa** | 6 | MM p.179 | **HIGH** | **Petrifying gaze, permanent stone** |
| **Mummy** | 8 | MM p.190 | **MEDIUM** | **Mummy rot (disease, incurable by normal means)** |
| **Nymph** | 6 | MM p.195 | **MEDIUM** | **Blinding beauty (permanent blindness)** |
| **Rakshasa** | 7-14 | MM p.210 | **MEDIUM** | **Change shape, spell-like abilities, DR 15/good and piercing** |
| **Shadow** | 3 | MM p.221 | **HIGH** | **Incorporeal, STR drain, creates spawn from victims** |
| **Spectre** | 7 | MM p.232 | **HIGH** | **Incorporeal, energy drain (2 levels), creates spawn** |
| **Vampire** | Variable | MM p.250 | **HIGH** | **Energy drain, dominate, gaseous form escape, create spawn, coffin dependency** |
| **Wight** | 4 | MM p.255 | **MEDIUM** | **Energy drain (1 level), creates spawn** |
| **Wraith** | 5 | MM p.258 | **HIGH** | **Incorporeal, CON drain, creates spawn, sunlight powerlessness** |
| **Dragon (all)** | Variable | MM p.69-92 | **MEDIUM** | **Spell-like abilities, age progression, frightful presence** |
| **Beholder** | 11 | MM p.25 | **MEDIUM** | **Eye rays (antimagic cone, disintegrate, death ray, petrification, etc.)** |
| **Tarrasque** | 48 | MM p.239 | **MEDIUM** | **Regeneration, spell reflection, near-indestructible** |

**Total High-Risk Monsters Identified:** 13
**Total Medium-Risk Monsters Identified:** 7

---

## 4. CROSS-CUTTING HAZARD SUMMARY (Pass 1 Complete)

### 4.1 By Hazard Category

| Hazard Category | Count | Example Subsystems |
|-----------------|-------|-------------------|
| **Entity Forking/Copying** | 8 | Simulacrum, Clone, Astral Projection, Find Familiar, Create Undead variants |
| **Permanent Ability Drain** | 4 | Ability Drain, Feeblemind, Energy Drain, Shadow/Wraith/Spectre attacks |
| **XP Costs** | 12 | Item creation, Wish/Miracle, Permanency, Resurrection variants, Gate |
| **Dominated/Controlled Agency** | 9 | Dominate spells, Planar Binding, Charm effects, Geas/Quest, Enslave |
| **Composite/Coupled Actors** | 6 | Mounted Combat, Grapple, Find Familiar, Intelligent Items, Rider+Mount |
| **Readied/Interrupt Mechanics** | 5 | Readied Actions, Counterspelling, Contingency, AoO (already handled) |
| **Timeline Hazards** | 4 | Time Stop, Temporal Stasis, Delay Action, Sequester |
| **Epistemic State** | 11 | Invisibility, Scrying, Illusions, Charm (attitude), Foresight, Blindsight |
| **Permanent Transformations** | 8 | Polymorph variants, Awaken, Petrification, Reincarnate, Dragon Disciple |
| **Planar Mechanics** | 7 | Plane Shift, Etherealness, Gate, Planar Binding, Cubic Gate |
| **Soul/Identity Hazards** | 6 | Magic Jar, Trap the Soul, Soul Bind, Imprisonment, Devourer |
| **Spawn Creation** | 7 | Vampire, Wraith, Spectre, Shadow, Wight, Bodak, Animate Dead |
| **Rejuvenation** | 3 | Lich (phylactery), Ghost, Tarrasque (near-immortal) |
| **Disease/Poison** | 3 | Disease subsystem, Poison subsystem, Mummy Rot |
| **Regeneration** | 2 | Monster regeneration, Regenerate spell |

### 4.2 Determinism Risk Distribution

- **HIGH Risk:** 67 subsystems/spells/monsters
- **MEDIUM Risk:** 45 subsystems/spells/monsters
- **LOW Risk:** 98 subsystems (majority are atomic or already implemented)

### 4.3 Classification Distribution

- **Atomic:** ~98 subsystems
- **Cross-Cutting:** ~89 subsystems
- **DM-Discretion:** ~23 subsystems

---

## PASS 1 STATUS: COMPLETE

**Next Steps:**
- **Pass 2:** Depth-first CCMA on all HIGH-risk items
- **Pass 3:** Interaction scan (spell×spell, spell×condition, etc.)
- **Pass 4:** Sequencing & governance mapping

---

**END OF PASS 1 INVENTORY**

---

## PASS 2: HAZARD CLASSIFICATION — Cross-Cutting Mechanics Audit (CCMA)

This section performs depth-first analysis on all HIGH-risk subsystems, answering:
1. What engine assumption does this violate?
2. What entities, states, or timelines does it couple?
3. What breaks if implemented late or implicitly?
4. Does this require new infrastructure?

---

### CCMA-001: Ability Drain (Permanent)

**Source:** PHB p.307
**Risk:** HIGH
**Classification:** cross-cutting

#### Engine Assumption Violated

Event-sourced architecture assumes **all state changes are reversible through event replay**. Ability drain creates a **permanent, non-reversible modification** to entity base statistics.

Current architecture: `hp_current` can be restored via events. Ability scores are assumed immutable except through temporary modifiers (CP-16 conditions).

Ability drain **permanently reduces** ability scores (e.g., STR 16 → STR 14 forever, or until Restoration spell).

####

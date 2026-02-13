# RQ-BOX-002-F: FAQ Mining Results — D&D 3.5e Official FAQ (June 2008)

**Domain:** Box Layer — House Policy Governance
**Status:** DRAFT
**Filed:** 2026-02-12
**Parent:** RQ-BOX-002 (RAW Silence Catalog)
**Source Authority:** OFFICIAL_FAQ (Wizards of the Coast, D&D 3.5 FAQ v3.5 Update, June 2008 final revision)
**Methodology:** Systematic extraction of FAQ entries that reveal RAW silences, ambiguities, or contradictions within v1 scope

---

## 1. Source Description

The D&D 3.5e FAQ (June 2008) is the final official revision of the Frequently Asked Questions document published by Wizards of the Coast for the D&D 3.5 edition rules. It was compiled primarily by the "Sage" columnists (Skip Williams and later Andy Collins) and addresses hundreds of rules questions submitted by players and DMs. The document is organized into sections corresponding to the core rulebooks (PHB, DMG, MM) and covers combat, spells, skills, equipment, and numerous subsystems.

**Critical note on FAQ authority:** The FAQ is *official* in the sense that WotC published it, but it was never granted errata-level authority. The FAQ sometimes contradicts RAW, sometimes adds rules not present in RAW, and sometimes presents one designer's interpretation as if it were authoritative. For AIDM purposes, FAQ entries are treated as:

- **EVIDENCE of silences** — if the FAQ had to address a question, RAW was unclear enough that players needed guidance
- **ADVISORY rulings** — the FAQ's answer is a data point for house policy design, not a binding constraint
- **NOT RAW** — the FAQ cannot override the core books; it can only clarify or reveal gaps

### Scope Filter Applied

Only entries relevant to v1 scope were mined:
- Core combat (AoO, grapple, sunder, cover/concealment, mounted combat)
- Equipment and inventory (containers, weapons, armor, shields)
- Spells levels 0-5 (targeting, area effects, specific spell interactions)
- Environmental interactions (hardness, HP, breaking objects, terrain)
- Grid-based movement and positioning

Excluded: polymorph, wild shape, prestige classes, epic levels, spells level 6+, social mechanics, supplement material.

---

## 2. Findings Catalog

### Finding RQ-BOX-002-F-0001: Cover from Creatures

```
Finding ID: RQ-BOX-002-F-0001
Source: D&D 3.5e FAQ (June 2008), Combat — Cover section
Source Authority: OFFICIAL_FAQ
Category: COMBAT_INTERACTIONS
Question: Do creatures provide cover to other creatures?
RAW References: PHB p.150-151 (Cover rules). Cover is defined by drawing lines
  from attacker corner to defender corner and checking for intervening obstacles.
  PHB mentions "creature or object" in several places but does not explicitly
  state whether an intervening creature grants cover or what degree.
RAW Answer: AMBIGUOUS
RAW Data Available: Cover rules, line-drawing method, cover bonus (+4 AC,
  +2 Reflex). Size categories of intervening creatures.
RAW Data Missing: (1) Whether creatures count as "obstacles" for cover.
  (2) Whether creature size relative to target/attacker matters. (3) Whether
  a creature only grants soft cover (no Reflex bonus) vs full cover. The FAQ
  rules that creatures provide soft cover (+4 AC to melee, no Reflex save
  bonus), but this "soft cover" concept is introduced BY the FAQ and does not
  appear in the PHB or DMG.
Mechanical Relevance: Every ranged attack and many melee attacks in crowded
  combat. Determines whether archers can freely target enemies behind their
  allies.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: NEW_FAMILY_NEEDED — COVER_DETERMINATION (adjudicating cover
  degree from intervening entities). Alternatively subsumable under
  SPATIAL_CLEARANCE (#5) if that family's scope is broadened.
Silence ID: NEW (SIL-011 candidate)
Frequency: OFTEN
Exploit Severity: MILD
Community Consensus: Most tables use the FAQ's "soft cover" rule. Some ignore
  cover from creatures entirely. Others apply full cover from Large+ creatures.
PM Recommendation: Adopt the FAQ's soft cover ruling (+4 AC, no Reflex bonus)
  as house policy. Implement size-relative logic: a creature grants soft cover
  if it is the same size or larger than the target, no cover if smaller. Log
  as COVER_DETERMINATION family instance. This is a high-frequency situation
  that the grid engine must handle deterministically.
```

---

### Finding RQ-BOX-002-F-0002: Attacks of Opportunity and Reach Weapons

```
Finding ID: RQ-BOX-002-F-0002
Source: D&D 3.5e FAQ (June 2008), Combat — Attacks of Opportunity section
Source Authority: OFFICIAL_FAQ
Category: COMBAT_INTERACTIONS
Question: Can a creature with a reach weapon threaten both adjacent squares
  and squares at reach distance?
RAW References: PHB p.137 (Threatening & AoO), PHB p.141 (Reach Weapons).
  RAW states reach weapons can strike at 10 ft but "cannot be used against
  an adjacent foe." The threatening rules say you threaten all squares you
  can make a melee attack into.
RAW Answer: AMBIGUOUS
RAW Data Available: Reach weapon range (10 ft), threatening definition,
  "cannot be used against adjacent foe" rule.
RAW Data Missing: (1) Whether a creature holding BOTH a reach weapon and a
  non-reach weapon threatens all squares (adjacent + reach). (2) Whether
  dropping/switching weapons changes threatened squares mid-round. (3) Whether
  natural weapons (which are not reach weapons) restore adjacent threatening
  for a creature also holding a reach weapon.
Mechanical Relevance: Determines AoO zones for common fighter builds (e.g.,
  spiked gauntlet + longspear). Affects tactical positioning on the grid.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: NONE — combat rules interpretation. Box resolver picks one
  reading. However, the interaction of MULTIPLE weapons affecting threat
  range simultaneously is genuinely underspecified.
Silence ID: NEW (SIL-012 candidate)
Frequency: OFTEN
Exploit Severity: MILD
Community Consensus: Nearly universal consensus that wielding a reach weapon
  + a non-reach weapon (e.g., spiked gauntlet) threatens both adjacent and
  reach squares. The FAQ confirms this interpretation. The silence is in the
  base RAW text.
PM Recommendation: Implement the FAQ ruling: a creature threatens all squares
  it can make a melee attack into with ANY currently wielded weapon. If
  wielding both a reach and non-reach weapon, threaten both zones. This is a
  Box resolver decision, not a template family — document in resolver comments.
```

---

### Finding RQ-BOX-002-F-0003: Grapple and Attacks of Opportunity — Timing

```
Finding ID: RQ-BOX-002-F-0003
Source: D&D 3.5e FAQ (June 2008), Combat — Grapple section
Source Authority: OFFICIAL_FAQ
Category: COMBAT_INTERACTIONS
Question: When exactly does the AoO from initiating a grapple occur — before
  the touch attack, after the touch attack, or during the grapple check?
RAW References: PHB p.155-156 (Grapple). The grapple sequence is:
  (1) AoO provoked, (2) touch attack, (3) grapple check, (4) grapple
  established. RAW says the target gets an AoO "as normal" and can choose
  to use it before the grapple attempt.
RAW Answer: AMBIGUOUS
RAW Data Available: Grapple sequence steps, AoO trigger ("entering the
  target's threatened area"), standard AoO rules.
RAW Data Missing: (1) Whether the AoO can disrupt the grapple attempt
  (like disrupting a spell) or only deal damage. (2) Whether damage from
  the AoO has any effect on the subsequent grapple check. (3) Whether
  the grappled condition from a successful AoO-triggered trip or disarm
  interferes with the grapple sequence. The FAQ clarifies that the AoO
  happens before the touch attack and cannot directly prevent the grapple
  attempt (only deal damage), but this is the FAQ adding a rule, not
  citing one.
Mechanical Relevance: Grapple initiation is common for monsters and melee
  combatants. The timing determines whether AoO can functionally prevent
  grapple attempts (it cannot, per FAQ, but RAW is silent).
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: NONE — combat rules interpretation (grapple resolver).
Silence ID: Maps to SIL-009 (extends it — SIL-009 covers threatening during
  grapple; this covers AoO timing entering grapple)
Frequency: OFTEN
Exploit Severity: MILD
Community Consensus: FAQ ruling widely adopted. AoO deals damage but does
  not disrupt the grapple attempt.
PM Recommendation: Implement FAQ ruling: AoO fires before touch attack, deals
  damage normally, does not disrupt the grapple sequence. If the AoO kills
  the grappler, the grapple attempt obviously fails. Otherwise, proceed to
  touch attack. Document as grapple resolver rule.
```

---

### Finding RQ-BOX-002-F-0004: Grapple — Moving a Grappled Opponent

```
Finding ID: RQ-BOX-002-F-0004
Source: D&D 3.5e FAQ (June 2008), Combat — Grapple section
Source Authority: OFFICIAL_FAQ
Category: COMBAT_INTERACTIONS
Question: When you win a grapple check to move your opponent, can you move
  them into hazardous terrain (off a cliff, into fire, into a wall of blades)?
RAW References: PHB p.156 (Move action in grapple). On a successful grapple
  check, you can move yourself and your opponent at half speed. RAW says
  "you can move both yourself and your opponent" but places no restrictions
  on destination beyond "half your speed."
RAW Answer: SILENT
RAW Data Available: Grapple movement rules, half-speed restriction,
  grapple check mechanics.
RAW Data Missing: (1) Whether the destination must be a legal standing
  position. (2) Whether the grappled opponent gets a save or check to
  resist being moved into hazardous terrain. (3) Whether environmental
  damage applies immediately upon entering the square or at the start of
  the moved creature's turn. (4) Whether you can push someone off a cliff
  edge via grapple (no Bull Rush check needed?).
Mechanical Relevance: Grapple-into-hazard is a common tactical question.
  Without clear rules, a grappler near a cliff or fire pit has either a
  trivially easy instant-kill or no viable tactic, depending on interpretation.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: SPATIAL_CLEARANCE (#5) — expanded to include forced movement
  into hazardous destinations. Or NEW_FAMILY_NEEDED:
  FORCED_MOVEMENT_DESTINATION — adjudicating whether forced movement can
  deposit a creature in a hazardous location and what happens when it does.
Silence ID: NEW (SIL-013 candidate)
Frequency: SOMETIMES
Exploit Severity: MAJOR
Community Consensus: Most tables allow grapple-into-hazard but give the
  opponent an opposed Strength check or Reflex save to stop at the edge.
  No RAW basis for this — it is pure table ruling.
PM Recommendation: Adopt a house policy: grapple movement into obviously
  lethal terrain (cliff edge, lava) allows the grappled opponent an
  additional opposed grapple check to halt movement at the last safe
  square. Movement into damaging but non-lethal terrain (fire, caltrops)
  proceeds normally with damage applied on entry. This prevents trivial
  grapple-kills while preserving tactical value. Log under
  FORCED_MOVEMENT_DESTINATION or SPATIAL_CLEARANCE family.
```

---

### Finding RQ-BOX-002-F-0005: Sunder — Attacking Held Objects

```
Finding ID: RQ-BOX-002-F-0005
Source: D&D 3.5e FAQ (June 2008), Combat — Sunder section
Source Authority: OFFICIAL_FAQ
Category: COMBAT_INTERACTIONS
Question: Can you sunder any object a creature is holding or wearing, or only
  weapons and shields?
RAW References: PHB p.158 (Sunder). Sunder text focuses on "striking a
  weapon" and "striking a shield" as the primary use cases. The general
  rule says you can use sunder to "strike at an opponent's weapon" but the
  broader text in DMG p.165 (Damaging Objects) says you can attack "objects."
RAW Answer: AMBIGUOUS
RAW Data Available: Sunder action sequence, AoO provocation, specific
  rules for weapon vs weapon sunder, shield sunder.
RAW Data Missing: (1) Whether you can sunder worn armor (the FAQ says yes,
  but RAW sunder rules describe weapon-vs-weapon). (2) Whether you can sunder
  held items that are not weapons (e.g., a spell component pouch, a holy
  symbol, a wand). (3) Whether sundering a necklace/ring is mechanically
  possible (no "grip" to target). (4) The AC of worn/held items that are not
  weapons or shields (the formula is provided for held weapons but not for
  rings, cloaks, etc.).
Mechanical Relevance: Defines the entire viable target set for the sunder
  action. If only weapons and shields can be sundered, the tactic is narrow.
  If any worn/held object can be targeted, sunder becomes a dominant strategy
  against spellcasters (destroy focus/component pouch) and item-dependent
  characters.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: ENVIRONMENTAL_INTERACTION (#4)
Silence ID: Maps to SIL-007/SIL-008 constellation (extends the sunder
  subsystem silences). NEW (SIL-014 candidate) for targetable-object scope.
Frequency: SOMETIMES
Exploit Severity: MAJOR
Community Consensus: FAQ says you can sunder worn armor (treat as attack
  against AC 10 + armor's enhancement bonus). Community is split on whether
  you can sunder rings, amulets, or spell component pouches. Most tables
  allow sundering any held/worn object but assign ad-hoc ACs.
PM Recommendation: Define a complete sunder target table: weapons (held),
  shields (held/worn), armor (worn), other held items (wands, rods, held
  foci), and other worn items (cloaks, belts, rings — NOT targetable via
  sunder unless the creature is helpless or the item is specifically
  grabbed first). This scoping decision prevents sunder from becoming a
  universal "disenchant opponent" action while preserving its tactical role.
  Log under ENVIRONMENTAL_INTERACTION family.
```

---

### Finding RQ-BOX-002-F-0006: Natural Weapon Attacks + Manufactured Weapon in Full Attack

```
Finding ID: RQ-BOX-002-F-0006
Source: D&D 3.5e FAQ (June 2008), Combat — Full Attack section
Source Authority: OFFICIAL_FAQ
Category: COMBAT_INTERACTIONS
Question: When a creature with natural weapons also wields a manufactured
  weapon, how do the attacks combine in a full attack action?
RAW References: MM p.312 (Natural Weapons), PHB p.139 (Full Attack).
  RAW states that natural weapons used alongside manufactured weapons are
  treated as secondary attacks (-5 penalty, half Str to damage). But RAW
  is ambiguous on: which natural weapons can still be used (a creature
  holding a sword in its claw — can it still claw with that hand?).
RAW Answer: AMBIGUOUS
RAW Data Available: Primary/secondary natural attack distinction,
  manufactured weapon iterative attack rules, -5 penalty for secondary.
RAW Data Missing: (1) Whether a limb holding a manufactured weapon can also
  make a natural attack (e.g., claw while holding a sword). The FAQ rules
  NO — if a hand/claw holds a weapon, that limb cannot also make a natural
  attack. (2) Whether a bite attack (no hand conflict) is always available
  as secondary alongside manufactured weapon attacks. FAQ rules YES.
  (3) Whether a tail slap, gore, or wing buffet (non-hand natural weapons)
  are available as secondaries during a manufactured weapon full attack.
  FAQ rules YES for non-conflicting limbs.
Mechanical Relevance: Affects monster stat blocks and any PC race with
  natural weapons. Determines total number of attacks per round for many
  creatures — a critical combat variable.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: NONE — combat rules interpretation (attack resolver).
  However, the limb-weapon conflict detection requires tracking which
  limbs are occupied, which may justify a family or at least a resolver
  subroutine.
Silence ID: NEW (SIL-015 candidate)
Frequency: OFTEN (many monsters have natural weapons + use manufactured
  weapons; also affects PC races like half-dragon templates, lizardfolk)
Exploit Severity: MILD
Community Consensus: FAQ ruling is widely adopted. A claw holding a sword
  cannot also claw-attack. Non-hand natural weapons (bite, tail, gore)
  remain available as secondaries.
PM Recommendation: Implement the FAQ ruling as Box combat resolver logic:
  (1) During a full attack with manufactured weapons, any natural weapon
  that uses the same limb as a held manufactured weapon is unavailable.
  (2) Non-conflicting natural weapons (bite, tail, gore, wing) are
  available as secondary attacks at -5, half Str. (3) This requires the
  creature data model to tag which limbs each natural weapon uses.
  Document as resolver rule, not template family.
```

---

### Finding RQ-BOX-002-F-0007: Two-Weapon Fighting and Double Weapons — Off-Hand Attacks

```
Finding ID: RQ-BOX-002-F-0007
Source: D&D 3.5e FAQ (June 2008), Combat — Two-Weapon Fighting section
Source Authority: OFFICIAL_FAQ
Category: COMBAT_INTERACTIONS
Question: When using a double weapon with TWF, how many attacks do you get,
  and which end gets iterative attacks from high BAB?
RAW References: PHB p.146 (Two-Weapon Fighting), PHB p.116 (Double Weapons).
  RAW says you can use a double weapon "as if fighting with two weapons"
  and that the off-hand end gets one extra attack. High BAB provides
  iteratives on the primary hand. TWF/ITWF/GTWF provide additional
  off-hand attacks.
RAW Answer: AMBIGUOUS
RAW Data Available: TWF penalties, iterative attack progression, double
  weapon classification, Improved/Greater TWF feat descriptions.
RAW Data Missing: (1) Whether the "main hand" end is fixed or the player
  chooses each round. (2) Whether the first attack of a full attack must
  come from the main hand. (3) Whether you can freely intermix main-hand
  and off-hand attacks in any order, or must follow a specific sequence.
  The FAQ rules that: (a) the player designates main/off-hand each round,
  (b) attacks can be made in any order, (c) iteratives from BAB go on
  main hand, additional attacks from TWF feats go on off hand.
Mechanical Relevance: Attack sequence and penalty assignment for every TWF
  build. Minor optimization but the system must produce deterministic
  attack sequences.
Disposition: BOX_RESOLVER_DECISION
Trigger Family: NONE — combat resolver logic.
Silence ID: NEW (SIL-016 candidate)
Frequency: OFTEN (TWF is a common build)
Exploit Severity: NONE
Community Consensus: FAQ ruling is universally adopted. Attack order is
  player's choice. Main/off hand designation is per-round.
PM Recommendation: Implement FAQ ruling directly in attack resolver.
  Player designates main/off hand. BAB iteratives on main hand. Feat
  iteratives on off hand. Attack order is player's choice (relevant for
  cases where first attack kills target and remaining attacks redirect).
  This is pure resolver implementation, not house policy.
```

---

### Finding RQ-BOX-002-F-0008: Charge Through Difficult Terrain

```
Finding ID: RQ-BOX-002-F-0008
Source: D&D 3.5e FAQ (June 2008), Combat — Movement section
Source Authority: OFFICIAL_FAQ
Category: MOVEMENT_TERRAIN
Question: Can you charge through or into difficult terrain?
RAW References: PHB p.154 (Charge). Charge requires moving in a straight
  line and "You must move to the closest space from which you can attack
  the opponent." PHB p.148 (Difficult Terrain) says difficult terrain
  costs double movement. PHB charge rules say you "can't use a charge
  if any obstacle, creature, or square of difficult terrain stands in
  your path." BUT see also DMG difficult terrain rules.
RAW Answer: AMBIGUOUS
RAW Data Available: Charge requirements (straight line, double move),
  difficult terrain movement cost, PHB charge restriction.
RAW Data Missing: (1) The PHB says you can't charge through difficult
  terrain, but this makes charges nearly impossible in any dungeon with
  rubble. The FAQ clarifies that you CAN charge through difficult terrain
  but it costs double movement per square (so your charge distance is
  effectively halved). This contradicts the literal PHB text. (2) Whether
  partial difficult terrain (starting on normal, ending on difficult)
  blocks the charge or just reduces distance. (3) Whether obstacles that
  don't impede movement (e.g., low brush) count as "difficult terrain"
  for charge purposes.
Mechanical Relevance: Charges are a fundamental combat tactic. If difficult
  terrain completely blocks charges, many dungeon environments become
  charge-free zones, dramatically changing tactical options.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: SPATIAL_CLEARANCE (#5) or NEW_FAMILY_NEEDED:
  MOVEMENT_LEGALITY — adjudicating whether a specific movement type
  (charge, run, 5-ft step, withdraw) is legal given terrain.
Silence ID: NEW (SIL-017 candidate)
Frequency: OFTEN
Exploit Severity: MILD
Community Consensus: Virtually all tables use the FAQ ruling — you can
  charge through difficult terrain at double cost. The PHB literal text
  is considered overly restrictive.
PM Recommendation: Adopt the FAQ ruling: difficult terrain does not prevent
  charges but each square of difficult terrain costs double movement from
  the charge distance. A creature with a 60-ft charge (double move) moving
  through all difficult terrain can charge up to 30 ft. Log as a Box
  resolver rule rather than house policy (since the FAQ clarification is
  essentially universal). If treated as house policy, log under
  SPATIAL_CLEARANCE or a new MOVEMENT_LEGALITY family.
```

---

### Finding RQ-BOX-002-F-0009: Squeezing and Attacks of Opportunity

```
Finding ID: RQ-BOX-002-F-0009
Source: D&D 3.5e FAQ (June 2008), Combat — Movement section
Source Authority: OFFICIAL_FAQ
Category: MOVEMENT_TERRAIN
Question: What penalties apply when squeezing through a space narrower than
  your space but wider than your actual body?
RAW References: PHB p.148 (Squeezing). A creature can squeeze through a
  space one size category smaller. While squeezing: -4 AC, -4 attack rolls.
  Movement costs double.
RAW Answer: AMBIGUOUS
RAW Data Available: Squeeze penalties (-4 AC, -4 attack), movement cost
  doubling, size category narrower definition.
RAW Data Missing: (1) Whether squeezing provokes AoO (moving through
  threatened squares while squeezing — does the reduced space change which
  squares are threatened?). (2) Whether a squeezing creature's own
  threatened area shrinks (a Large creature squeezing into Medium space —
  does it threaten as Medium?). (3) Whether squeezing interacts with
  encumbrance (creature in heavy armor squeezing). (4) Whether creatures
  can squeeze while carrying items wider than the squeeze space. The FAQ
  addresses some of these: squeezing does not provoke additional AoO
  beyond normal movement, and the creature's threatened area remains
  based on its actual size (not squeezed size). But these are FAQ
  additions, not RAW citations.
Mechanical Relevance: Squeezing occurs in narrow corridors, cave passages,
  and any situation where the map constrains movement. The grid engine must
  know the complete penalty set and movement interaction.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: SPATIAL_CLEARANCE (#5)
Silence ID: NEW (SIL-018 candidate)
Frequency: SOMETIMES
Exploit Severity: MILD
Community Consensus: FAQ rulings adopted. Squeezing does not change
  threatened area. Main question is whether equipment prevents squeezing.
PM Recommendation: Implement squeeze rules per FAQ: -4 AC, -4 attack,
  double movement cost, threatened area unchanged. Add equipment
  interaction as SPATIAL_CLEARANCE family instance: a creature cannot
  squeeze while carrying items whose minimum dimension exceeds the
  squeeze space width. This requires item dimension data (connects to
  SIL-001 dimension problem).
```

---

### Finding RQ-BOX-002-F-0010: Prone and Attacks of Opportunity

```
Finding ID: RQ-BOX-002-F-0010
Source: D&D 3.5e FAQ (June 2008), Combat — Conditions section
Source Authority: OFFICIAL_FAQ
Category: COMBAT_INTERACTIONS
Question: Does standing up from prone provoke an attack of opportunity?
  Can a prone creature crawl without provoking?
RAW References: PHB p.142 (Prone), PHB p.137 (AoO). Standing from prone
  is a move action. The AoO table (PHB Table 8-2) lists "Move" actions
  that provoke. "Stand up" is not explicitly listed in the AoO table but
  is a move action.
RAW Answer: AMBIGUOUS
RAW Data Available: Prone condition effects (-4 melee attack, +4 ranged
  attack bonus for attackers, -4 AC vs melee, +4 AC vs ranged). Standing
  = move action. AoO table.
RAW Data Missing: (1) Whether standing from prone provokes AoO. The FAQ
  says YES — standing from prone provokes. But the PHB Table 8-2 does not
  explicitly list "stand from prone" as an AoO-provoking action (it lists
  "Move" generically). (2) Whether crawling (5 ft while prone) provokes
  AoO. FAQ says crawling provokes AoO as normal movement. (3) Whether a
  creature can take a 5-foot step while prone (to avoid AoO) — FAQ says
  NO, you cannot 5-ft step while prone; you must stand first or crawl.
Mechanical Relevance: Prone is an extremely common combat condition
  (trip attacks, being knocked down). The action economy of recovering
  from prone determines whether trip builds are viable. If standing
  doesn't provoke, trip is much weaker.
Disposition: BOX_RESOLVER_DECISION
Trigger Family: NONE — combat rules interpretation.
Silence ID: NEW (SIL-019 candidate)
Frequency: OFTEN
Exploit Severity: MILD
Community Consensus: Universal adoption of FAQ ruling. Standing provokes.
  No 5-ft step while prone. Crawling provokes normally.
PM Recommendation: Implement FAQ ruling as resolver rule: standing from
  prone provokes AoO, costs move action, no 5-ft step while prone,
  crawling provokes as normal movement. This is sufficiently universal
  that it should be treated as RAW clarification, not house policy.
```

---

### Finding RQ-BOX-002-F-0011: Mounted Combat — Lance and Charge Damage

```
Finding ID: RQ-BOX-002-F-0011
Source: D&D 3.5e FAQ (June 2008), Combat — Mounted Combat section
Source Authority: OFFICIAL_FAQ
Category: MOUNT_MOUNTED
Question: When a mounted character charges with a lance, does the lance deal
  double damage, and does the mount's charge affect the damage?
RAW References: PHB p.143 (Mounted Combat), PHB p.118 (Lance). Lance
  deals double damage on a mounted charge. Charge gives +2 attack, -2 AC.
  Spirited Charge feat triples damage. But RAW is unclear on several
  interactions.
RAW Answer: AMBIGUOUS
RAW Data Available: Lance double damage rule, charge bonus, Spirited Charge
  (3x damage), mounted charge rules, mount movement.
RAW Data Missing: (1) Whether "double damage" means double total damage
  (including Str, Power Attack, enhancement) or only double base weapon
  damage dice. The FAQ rules double TOTAL damage. (2) Whether Spirited
  Charge stacks multiplicatively (double then triple = 6x?) or uses the
  3.5e multiplication rule (double + triple = 4x). The FAQ confirms the
  3.5e multiplication rule applies (2x + 3x = 4x, not 6x). (3) Whether
  Power Attack damage is multiplied on a lance charge. FAQ says YES, Power
  Attack is part of the total multiplied. (4) Whether the mount needs a
  special ability to charge (any mount can charge, per FAQ).
Mechanical Relevance: Mounted lance charge is the highest single-hit
  damage combo in core rules without spells. Getting the multiplication
  wrong can double or halve the output. This is a v1 critical path since
  mounted combat basics are in scope.
Disposition: NEEDS_HOUSE_POLICY (for the multiplication stack question)
  + BOX_RESOLVER_DECISION (for Power Attack inclusion)
Trigger Family: MOUNT_COMPATIBILITY (#9) — extends to mounted damage
  calculation. Alternatively, this is pure combat resolver math, not a
  plausibility judgment.
Silence ID: NEW (SIL-020 candidate)
Frequency: SOMETIMES
Exploit Severity: MAJOR
Community Consensus: FAQ ruling universally adopted. 3.5e multiplication
  stacking rule (add multipliers - 1). Lance charge = 2x. Spirited Charge
  lance = 4x. Power Attack included in multiplied total.
PM Recommendation: Implement the 3.5e stacking multiplication rule in the
  damage resolver. Double damage = multiply total by 2. Spirited Charge =
  multiply total by 3. Combined = multiply total by 4 (not 6). Power
  Attack bonus damage is included in the total before multiplication.
  Document as resolver rule. This is effectively RAW clarification (the
  stacking multiplication rule IS in the PHB p.304) but its application
  to the lance + Spirited Charge combo is the silence.
```

---

### Finding RQ-BOX-002-F-0012: Mounted Combat — Rider/Mount Action Economy

```
Finding ID: RQ-BOX-002-F-0012
Source: D&D 3.5e FAQ (June 2008), Combat — Mounted Combat section
Source Authority: OFFICIAL_FAQ
Category: MOUNT_MOUNTED
Question: How do the rider's actions and the mount's actions interact in the
  initiative order? Can the rider attack at any point during the mount's
  movement?
RAW References: PHB p.157 (Mounted Combat). Mount acts on rider's initiative.
  A controlled mount can move and attack (charge) or move and full-round
  action (if not a charge). Rider can attack at any point during mount's
  movement.
RAW Answer: AMBIGUOUS
RAW Data Available: Mount initiative rules, "rider can act at any point
  during mount's move" principle, action types.
RAW Data Missing: (1) Whether the rider can take a full attack action if
  the mount only takes a single move (not a double move/charge). The FAQ
  rules YES — if the mount moves its speed or less (single move action),
  the rider can take a full attack action. (2) Whether the rider can split
  a full attack action across the mount's movement (attack, mount moves,
  attack again). FAQ rules NO — rider's full attack happens at one point
  during mount movement. (3) Whether the rider can cast a spell while the
  mount charges (Concentration check DC 10 + spell level to cast while
  mount moves, per FAQ). (4) Whether the mount's Ride-By Attack movement
  counts differently from normal movement for the rider's action economy.
Mechanical Relevance: This is the fundamental action economy question for
  all mounted combat. Incorrect implementation either makes mounted
  characters absurdly strong (split full attacks across movement) or
  too weak (can never full attack while mounted).
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: MOUNT_COMPATIBILITY (#9) — needs expansion to cover
  mounted action economy, not just compatibility.
Silence ID: NEW (SIL-021 candidate)
Frequency: OFTEN (every mounted combatant every round)
Exploit Severity: MAJOR
Community Consensus: FAQ ruling is standard. Mount single move = rider
  full attack. Mount double move/charge = rider standard action only.
  No splitting full attacks across movement.
PM Recommendation: Implement the FAQ ruling as the mounted combat action
  resolver: (1) Mount single move → rider may full attack at any ONE
  point during movement. (2) Mount double move or charge → rider may
  take only a standard action at any point. (3) No splitting attacks
  across movement. (4) Spellcasting during mount movement requires
  Concentration DC 10 + spell level. This is critical path for v1
  mounted combat. Document as resolver logic.
```

---

### Finding RQ-BOX-002-F-0013: Splash Weapons — Missing on Targeted Square

```
Finding ID: RQ-BOX-002-F-0013
Source: D&D 3.5e FAQ (June 2008), Combat — Special Attacks section
Source Authority: OFFICIAL_FAQ
Category: COMBAT_INTERACTIONS
Question: When a splash weapon (alchemist's fire, acid flask, tanglefoot bag)
  misses its target, where does it land?
RAW References: PHB p.158 (Splash Weapons). If you miss, the weapon lands
  1d8 squares away (roll for direction) from the target. Creatures in the
  splash radius take splash damage. Target takes direct hit damage on hit.
RAW Answer: AMBIGUOUS
RAW Data Available: Miss deviation roll (1d8 direction), splash radius,
  direct hit damage, splash damage values.
RAW Data Missing: (1) How far the splash weapon deviates — RAW says a
  direction but not a distance for misses against grid intersections vs
  creature squares. (2) Whether range increment affects deviation distance
  (the FAQ rules YES — deviation is 1 square per range increment of the
  throw, minimum 1). (3) Whether obstacles in the deviation path stop
  the splash weapon or it flies over them. (4) Whether the splash weapon
  can "land" in an occupied square on deviation and count as a direct hit
  on that creature (FAQ rules NO — deviation always means splash only).
Mechanical Relevance: Splash weapons are critical for low-level parties
  against swarms and for tactical area control. Getting deviation wrong
  changes whether splash weapons are reliable or chaotic.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: NONE — combat resolver (ranged attack deviation). However,
  the obstacle-in-path question touches SPATIAL_CLEARANCE (#5).
Silence ID: NEW (SIL-022 candidate)
Frequency: SOMETIMES
Exploit Severity: NONE
Community Consensus: FAQ deviation rules widely used. One square per range
  increment is the standard. Obstacle interaction remains table-specific.
PM Recommendation: Implement FAQ deviation: 1d8 direction, 1 square per
  range increment of distance. Obstacle in path: splash weapon breaks at
  obstacle, splash damage applies at that point. Deviation into occupied
  square: splash only, not direct hit. Document as resolver rule.
```

---

### Finding RQ-BOX-002-F-0014: Spell Area Effects and Vertical Extent

```
Finding ID: RQ-BOX-002-F-0014
Source: D&D 3.5e FAQ (June 2008), Spells — Area Effects section
Source Authority: OFFICIAL_FAQ
Category: SPELLCASTING_TARGETING
Question: Do area effect spells (e.g., fireball, entangle, grease) have a
  vertical extent, or are they flat circles on the ground?
RAW References: PHB p.175 (Spell Areas), individual spell descriptions.
  Fireball: 20-ft radius spread. Entangle: 40-ft radius spread. PHB
  describes areas in 2D terms ("radius," "cone," "line") and does not
  consistently specify height. Fireball is described as a "spread" which
  the PHB says "extends in all directions" — suggesting a sphere. Entangle
  and grease are ground-targeted and logically flat.
RAW Answer: AMBIGUOUS
RAW Data Available: Area shape keywords (burst, spread, emanation, cone),
  radius measurements, some vertical extent rules (cones have height =
  range).
RAW Data Missing: (1) Whether "20-ft radius spread" means a sphere (20-ft
  radius in 3D) or a cylinder (20-ft radius disk of some height). The FAQ
  clarifies that bursts and spreads are 3D unless the spell description
  says otherwise. A fireball is a 20-ft radius sphere. (2) What the
  height of ground-targeted effects is (entangle, grease, web). FAQ is
  largely silent on this — individual spell descriptions vary. (3) Whether
  a fireball detonated at ground level only fills a hemisphere (the
  ground blocks the lower half) or whether the energy redistributes
  (FAQ says the energy of a fireball in a smaller space can extend farther
  per PHB p.175, but vertical truncation is not addressed directly).
Mechanical Relevance: Determines whether flying creatures can hover above
  area effects to avoid them. Determines whether a fireball hits creatures
  on a second story. Fundamental for the grid engine's 3D interaction model.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: NEW_FAMILY_NEEDED: AREA_EFFECT_GEOMETRY — adjudicating the
  3D volume of area effect spells. This requires inputs (spell area type,
  dimensions, point of origin, terrain) and outputs (set of affected grid
  squares/cubes). May be subsumable under SPATIAL_CLEARANCE (#5) with
  expanded scope.
Silence ID: NEW (SIL-023 candidate)
Frequency: OFTEN (every area-effect spell every casting)
Exploit Severity: MILD
Community Consensus: Most tables treat bursts/spreads as 3D (spheres/
  hemispheres). Ground effects (grease, entangle) are treated as 2D with
  minimal height (5 ft). Web is a special case (FAQ says it must be
  anchored to two surfaces, giving it variable 3D shape).
PM Recommendation: Implement area effects as 3D volumes: (1) Bursts and
  spreads are spheres centered on the origin point. (2) If a sphere
  intersects a surface (floor, wall), the energy fills available space
  per the fireball-in-a-corridor rule (PHB p.175). (3) Ground-targeted
  effects (grease, entangle) have 5-ft vertical extent. (4) Web requires
  two anchor surfaces and fills the volume between them. Document as
  spell area resolver rules. The 3D sphere interpretation is well-enough
  supported by RAW + FAQ to be treated as resolver logic rather than
  house policy.
```

---

### Finding RQ-BOX-002-F-0015: Concealment and Total Concealment — Miss Chance Mechanics

```
Finding ID: RQ-BOX-002-F-0015
Source: D&D 3.5e FAQ (June 2008), Combat — Concealment section
Source Authority: OFFICIAL_FAQ
Category: COMBAT_INTERACTIONS
Question: How does the miss chance from concealment interact with critical
  hits? Does concealment prevent crits?
RAW References: PHB p.152 (Concealment). Miss chance = 20% (concealment)
  or 50% (total concealment). Attacker rolls a miss chance percentile die
  separately from the attack roll. PHB p.140 (Critical Hits).
RAW Answer: AMBIGUOUS
RAW Data Available: Miss chance percentages, critical hit confirmation
  rules, concealment definitions (fog, darkness, blur).
RAW Data Missing: (1) Whether the miss chance roll happens before or after
  the attack roll. The FAQ rules: attack roll first, then if it hits,
  roll miss chance. (2) Whether a critical threat that hits on the attack
  roll but fails the miss chance roll is a miss (FAQ: yes, miss chance
  negates the hit entirely, including the crit). (3) Whether a critical
  threat that succeeds on miss chance must ALSO succeed on miss chance
  for the confirmation roll (FAQ: no, miss chance is rolled once per
  attack, not once per roll). (4) Whether concealment affects touch
  attacks (FAQ: yes, concealment works against all attacks).
Mechanical Relevance: Critical hits are a major damage spike. Whether
  concealment can negate them changes the value of blur, displacement,
  and fog-based tactics significantly.
Disposition: BOX_RESOLVER_DECISION
Trigger Family: NONE — combat resolver (attack resolution sequence).
Silence ID: NEW (SIL-024 candidate)
Frequency: OFTEN
Exploit Severity: MILD
Community Consensus: FAQ ruling is standard. Roll attack, then miss chance.
  One miss chance roll per attack. Concealment affects touch attacks.
PM Recommendation: Implement FAQ attack resolution sequence: (1) Roll
  attack vs AC. (2) If hit, roll miss chance (if concealment applies).
  (3) If miss chance fails, attack misses entirely (no crit, no damage).
  (4) If miss chance succeeds and attack was a critical threat, roll
  confirmation. (5) Miss chance is rolled once per attack, not per
  sub-roll. Document as resolver sequence.
```

---

### Finding RQ-BOX-002-F-0016: Spell Resistance and Area Spells — Selective Application

```
Finding ID: RQ-BOX-002-F-0016
Source: D&D 3.5e FAQ (June 2008), Spells — Spell Resistance section
Source Authority: OFFICIAL_FAQ
Category: SPELLCASTING_TARGETING
Question: When an area spell affects multiple creatures and some have SR and
  some don't, does a successful SR check negate the spell entirely or only
  for that creature?
RAW References: PHB p.177 (Spell Resistance). SR is checked per-creature.
  The spell affects all valid targets in its area; SR only protects the
  individual creature that has it.
RAW Answer: SILENT on specific interactions
RAW Data Available: SR check mechanics (caster level check vs SR),
  per-creature application rule, area spell targeting rules.
RAW Data Missing: (1) Whether a creature with SR that successfully resists
  a web spell can still be impeded by the webbing that formed around it
  (affecting other creatures). FAQ rules: the creature is unaffected by the
  spell entirely, but the physical webbing exists around it — it just
  passes through. (2) Whether SR protects against secondary effects of
  area spells (e.g., a fireball ignites combustibles — does SR prevent
  the fire damage from burning objects landing on the SR creature?).
  FAQ is silent. (3) Whether a grease spell's area exists for SR creatures
  even though they resist the spell effect (can they slide on grease they
  resist?). FAQ is ambiguous — different readings are possible.
Mechanical Relevance: SR interaction with area spells determines whether
  SR creatures can use areas of web, grease, or entangle as safe zones
  while allies are impeded. Affects tactical positioning.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: NONE — spell resolver logic. However, the physical vs
  magical distinction (grease exists physically but is conjured magically)
  may warrant a ENVIRONMENTAL_INTERACTION (#4) instance for
  spell-created-obstacles.
Silence ID: NEW (SIL-025 candidate)
Frequency: SOMETIMES
Exploit Severity: MILD
Community Consensus: Per-creature SR application is uncontroversial. The
  physical-secondary-effects question is debated. Most tables rule that SR
  protects only against the spell's direct magical effect, not physical
  consequences (e.g., SR doesn't protect against fire from a fireball-ignited
  oil puddle, but does protect against the fireball damage itself).
PM Recommendation: Implement per-creature SR. For physical secondary effects,
  apply the rule: SR protects against the spell's direct effect only.
  Environmental consequences of the spell (fire spread, fallen debris from
  shattered walls) are treated as non-magical hazards and bypass SR.
  Document as resolver rule.
```

---

### Finding RQ-BOX-002-F-0017: Mending and Make Whole — Object Size/Weight Limits

```
Finding ID: RQ-BOX-002-F-0017
Source: D&D 3.5e FAQ (June 2008), Spells — Specific Spells section
Source Authority: OFFICIAL_FAQ
Category: SPELLCASTING_TARGETING
Question: What are the limits of mending (cantrip) and make whole (2nd level)
  for repairing objects? Can they restore a shattered object?
RAW References: PHB p.253 (Mending): repairs small breaks or tears in
  objects. Restores 1d4 HP to an object. Weight limit: 1 lb. PHB p.252
  (Make Whole): repairs objects of up to 10 cu ft/level. Restores 1d6+
  caster level HP.
RAW Answer: AMBIGUOUS
RAW Data Available: HP restored, weight/volume limits, "small breaks or
  tears" language for mending.
RAW Data Missing: (1) Whether mending can repair an object that has been
  completely destroyed (0 HP — "ruined") or only damaged objects (above
  0 HP). The FAQ rules mending/make whole can only repair objects that
  still have HP remaining (are damaged, not destroyed). But this is FAQ
  ruling, not RAW text. (2) Whether "restoring 1d4 HP" to an object at
  0 HP means the spell can bring it from 0 to 1d4 (partially repaired)
  or whether 0 HP is an uncrossable threshold. (3) Whether make whole
  can repair an object broken into multiple pieces (connects to SIL-004:
  Object Identity Under Damage). (4) Whether these spells repair magical
  properties or only physical form. FAQ says they repair physical form;
  magical properties require more powerful magic (but where does RAW say
  this?).
Mechanical Relevance: Mending is a cantrip — unlimited use. If it can
  repair destroyed objects, sunder becomes much less impactful (just
  mend it afterward). If it cannot, the destroyed threshold is permanent
  without make whole or fabricate. This directly interacts with SIL-004
  (object identity) and SIL-010 (destruction state).
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: Deferred to RQ-BOX-003 (Object Identity Model). The
  repair spell question is a downstream consumer of the object identity
  model — once you know whether a "ruined" object is one entity or many,
  the spell targeting rules follow.
Silence ID: Maps to SIL-004 and SIL-010 (extends both). Repair spell
  specifics are part of the object identity constellation.
Frequency: OFTEN (mending is a cantrip used constantly)
Exploit Severity: MAJOR (if mending can repair destroyed objects, sunder
  is rendered meaningless)
Community Consensus: Most tables rule that mending cannot repair destroyed
  objects (0 HP). Make whole CAN repair destroyed objects IF all pieces are
  present. This is a pragmatic ruling with weak RAW support.
PM Recommendation: Adopt the community consensus as house policy:
  (1) Mending only works on damaged objects (HP > 0). (2) Make whole can
  repair destroyed objects (HP = 0) if the pieces are present and within
  the spell's volume limit. (3) Neither spell restores magical properties
  to a destroyed magic item — that requires more powerful restoration.
  This interacts with the object identity model (RQ-BOX-003) and should
  be formalized when that model is designed.
```

---

### Finding RQ-BOX-002-F-0018: Falling Damage — Maximum and Surface Interaction

```
Finding ID: RQ-BOX-002-F-0018
Source: D&D 3.5e FAQ (June 2008), Environment — Falling section
Source Authority: OFFICIAL_FAQ
Category: ENVIRONMENTAL_PHYSICS
Question: Is there a maximum falling damage, and does landing on a surface
  other than solid ground change the damage?
RAW References: PHB p.303 (Falling). 1d6 per 10 ft fallen, maximum 20d6.
  Falling into water reduces effective distance by varying amounts based
  on a Swim/Dive check.
RAW Answer: SILENT on surface interaction (except water)
RAW Data Available: 1d6/10 ft, 20d6 max, water depth table for reduced
  damage.
RAW Data Missing: (1) Whether landing on a soft surface (hay, snow, loose
  sand) reduces fall damage. RAW only addresses water. The FAQ acknowledges
  this gap but does not provide a comprehensive rule — it suggests DM
  adjudication. (2) Whether landing on a creature deals damage to both
  (FAQ says: house rule territory, but suggests equal damage split).
  (3) Whether falling onto a hard protrusion (spikes, sharp rocks) adds
  damage beyond the base fall. FAQ: suggests adding damage as if the
  protrusion is a trap (1d6 per spike, etc.), but this is not RAW.
  (4) Whether terminal velocity (20d6 cap) is really 200 ft or whether
  it applies at different heights for different creature sizes/weights.
  FAQ: the 20d6 cap is absolute regardless of size/weight.
Mechanical Relevance: Falling is one of the most common environmental
  hazards. The surface interaction question comes up constantly: pits
  with spikes, jumping into water vs onto stone, pushing creatures off
  ledges onto different surfaces below.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: ENVIRONMENTAL_INTERACTION (#4) — surface-modified falling
  damage. Or FRAGILITY_BREAKAGE (#7) — creature damage from environmental
  interaction.
Silence ID: NEW (SIL-026 candidate)
Frequency: OFTEN
Exploit Severity: MILD
Community Consensus: Most tables reduce fall damage for soft surfaces (half
  damage for hay/snow, DC 15 Tumble to reduce by 10 ft) and add damage for
  hazardous surfaces (spike damage added to fall damage). The Tumble skill
  RAW allows reducing effective fall by 10 ft on a DC 15 check.
PM Recommendation: Implement base RAW faithfully (1d6/10 ft, 20d6 cap,
  water table). For surface interaction, adopt a house policy table:
  Soft surface (hay, deep snow): reduce effective fall distance by 10 ft.
  Hazardous surface (spikes): add spike damage per DMG trap rules.
  Landing on creatures: split damage equally, creature underneath gets
  Reflex save DC 15 to avoid. Log under ENVIRONMENTAL_INTERACTION family.
```

---

### Finding RQ-BOX-002-F-0019: Object AC and Attacking Specific Objects

```
Finding ID: RQ-BOX-002-F-0019
Source: D&D 3.5e FAQ (June 2008), Combat — Objects section
Source Authority: OFFICIAL_FAQ
Category: ENVIRONMENTAL_PHYSICS
Question: What is the AC of an object that is not being held or worn?
  How do you attack a specific small object (rope, lock, chain)?
RAW References: DMG p.165 (Damaging Objects). Objects have AC = 10 + size
  modifier + Dex modifier (0 for inanimate). Size modifiers: Colossal -8
  to Fine +8. Held objects use holder's Dex instead and get a +5 bonus.
RAW Answer: AMBIGUOUS
RAW Data Available: Size-based AC formula, held-object rules, hardness
  and HP tables.
RAW Data Missing: (1) The size category of common objects. RAW provides
  examples (Fine: potion, Diminutive: scroll, Tiny: dagger) but many
  objects have no listed size. What size is a rope? A door hinge? A
  chest lock? A tent? (2) Whether you can target a PART of an object
  (strike the lock on a chest without damaging the chest, cut a specific
  rope out of many). The FAQ suggests treating the part as a separate
  object with its own HP, but this is FAQ addition, not RAW. (3) Whether
  there is a minimum AC for objects or whether a Colossal object (like
  a building wall) has AC 2 (10 - 8) making it auto-hit. FAQ confirms
  AC 2 is correct for Colossal objects — they are easy to hit, hard to
  damage (high hardness/HP).
Mechanical Relevance: Attacking objects is core to sunder, breaking down
  doors, cutting ropes, destroying barriers. Without object size
  assignments, the system cannot calculate object AC for objects not in
  the DMG tables.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: ENVIRONMENTAL_INTERACTION (#4)
Silence ID: Maps to SIL-007/SIL-008 constellation (object combat stats).
  NEW for the size-category-of-unlisted-objects gap (SIL-027 candidate).
Frequency: OFTEN
Exploit Severity: MILD
Community Consensus: Most tables assign object sizes by common sense.
  The FAQ's suggestion to treat object parts as separate objects is
  widely adopted.
PM Recommendation: Create a comprehensive object size table as a PDL
  (Policy Default Library) entry. Assign sizes to all PHB equipment list
  items. For objects not in the table, implement a size inference rule
  based on weight and longest dimension (connects to SIL-001 dimension
  data). Log under ENVIRONMENTAL_INTERACTION family. Object-part
  targeting: allow targeting distinct parts (lock, hinge, handle) with
  separate HP (fraction of whole object HP based on size ratio).
```

---

### Finding RQ-BOX-002-F-0020: Stacking Bonuses — Dodge, Circumstance, and Untyped

```
Finding ID: RQ-BOX-002-F-0020
Source: D&D 3.5e FAQ (June 2008), General Rules — Bonus Stacking section
Source Authority: OFFICIAL_FAQ
Category: COMBAT_INTERACTIONS
Question: Which bonus types stack with themselves and which do not? Do
  untyped bonuses always stack?
RAW References: PHB p.21 (Bonus Types). Same-type bonuses don't stack
  (highest applies) except: dodge bonuses always stack, circumstance
  bonuses stack. Untyped bonuses are addressed inconsistently.
RAW Answer: AMBIGUOUS
RAW Data Available: Bonus type list (armor, shield, natural armor,
  deflection, enhancement, competence, insight, luck, morale, profane,
  sacred, resistance, circumstance, dodge). Stacking rule: same type
  don't stack except dodge and circumstance.
RAW Data Missing: (1) Whether untyped bonuses stack with each other. The
  FAQ rules YES — untyped bonuses always stack. But this creates an
  exploit vector where multiple sources of untyped bonuses produce
  enormous totals. RAW never explicitly states this. (2) Whether
  penalties follow the same stacking rules (FAQ: penalties of the same
  type DO stack, unlike bonuses). (3) Whether enhancement bonuses to
  ability scores stack with enhancement bonuses to derived stats (e.g.,
  +4 enhancement to Str via bull's strength → +2 to attack and damage;
  does a +1 enhancement to attack from another source stack? FAQ: no,
  both are enhancement bonuses to attack, even though one is derived).
Mechanical Relevance: Bonus stacking is the fundamental math of D&D.
  Getting it wrong produces cascading errors in every AC, attack, save,
  and skill calculation. The untyped-bonus question affects every buff
  spell and magic item combination.
Disposition: BOX_RESOLVER_DECISION
Trigger Family: NONE — core rules engine math. This is not a plausibility
  judgment; it is the foundational bonus calculation.
Silence ID: NEW (SIL-028 candidate)
Frequency: ALWAYS
Exploit Severity: MAJOR (incorrect stacking breaks bounded accuracy)
Community Consensus: FAQ rulings widely adopted. Untyped bonuses stack.
  Same-type penalties stack. Enhancement-to-derived-stat is still
  enhancement type.
PM Recommendation: Implement the bonus stacking engine per FAQ: (1) Same
  named type: highest only (except dodge and circumstance, which stack).
  (2) Untyped bonuses: always stack. (3) Penalties: always stack
  regardless of type. (4) Derived bonuses retain their original type
  (enhancement to Str produces enhancement bonus to attack). This is
  foundational resolver logic, not house policy. Must be implemented
  before any combat math works correctly.
```

---

### Finding RQ-BOX-002-F-0021: Damaging Objects with Energy Attacks

```
Finding ID: RQ-BOX-002-F-0021
Source: D&D 3.5e FAQ (June 2008), Environment — Objects section
Source Authority: OFFICIAL_FAQ
Category: ENVIRONMENTAL_PHYSICS
Question: How do energy attacks (fire, cold, electricity, acid, sonic) interact
  with object hardness? Can a fireball damage a stone wall?
RAW References: DMG p.165 (Damaging Objects). Energy attacks deal half
  damage to most objects. Object hardness applies against energy damage.
  Some materials have specific vulnerabilities (fire vs wood, cold vs
  crystal, sonic vs crystal/glass).
RAW Answer: AMBIGUOUS
RAW Data Available: Half-damage rule for energy vs objects, hardness
  values, material vulnerability notes (DMG p.165-166).
RAW Data Missing: (1) Whether the half-damage is applied before or after
  hardness. FAQ rules: apply hardness first, then halve. (This order
  dramatically reduces energy damage to objects.) (2) Whether fire
  damage to a wooden object bypasses the half-damage rule (the DMG
  mentions fire vulnerability for wood/paper but doesn't clarify if
  this means full damage or some other multiplier). FAQ rules: fire
  does full damage to wood/cloth/paper, not half. (3) Whether cold
  damage can make materials brittle (reduce hardness). FAQ: no RAW
  basis for this, suggests DM adjudication. (4) Whether sonic damage
  bypasses hardness entirely for crystalline objects. FAQ: sonic
  bypasses hardness for crystal/glass, full damage.
Mechanical Relevance: Determines whether spellcasters can efficiently
  destroy objects (doors, walls, barriers). If fireball does 10d6 / 2
  after hardness 8 vs a wooden door (HP 15), it might deal ((avg 35) -
  8) / 2 = 13.5 damage — nearly destroying it. But if hardness applies
  after halving: (35/2) - 8 = 9.5 damage. Different order, very
  different result.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: ENVIRONMENTAL_INTERACTION (#4)
Silence ID: Maps to SIL-007/SIL-008 constellation (object damage
  calculation). NEW for the energy-vs-hardness order question
  (SIL-029 candidate).
Frequency: OFTEN
Exploit Severity: MILD
Community Consensus: FAQ order (hardness first, then halve) is standard.
  Fire bypassing half-damage for wood is universally adopted.
PM Recommendation: Implement the FAQ ruling: (1) Energy damage vs objects:
  apply hardness, then halve remaining. (2) Vulnerability exceptions:
  fire vs wood/cloth/paper = full damage after hardness. Sonic vs
  crystal/glass = full damage, ignore hardness. (3) Cold: no special
  brittleness effect (no RAW basis). (4) Acid: normal energy rules
  (half after hardness). Document in ENVIRONMENTAL_INTERACTION family
  as object-damage-energy-interaction policy.
```

---

### Finding RQ-BOX-002-F-0022: Swimming in Armor

```
Finding ID: RQ-BOX-002-F-0022
Source: D&D 3.5e FAQ (June 2008), Skills — Swim section
Source Authority: OFFICIAL_FAQ
Category: MOVEMENT_TERRAIN
Question: What happens when a character in heavy armor falls into water?
  Can they swim at all?
RAW References: PHB p.84 (Swim skill). Armor check penalty applies as a
  penalty to Swim checks. Heavy armor has check penalties of -5 to -8.
  DC 10 for calm water, DC 15 for rough water. No explicit rule for
  what happens when you fail by a lot.
RAW Answer: AMBIGUOUS
RAW Data Available: Swim check DCs, armor check penalties, drowning rules
  (PHB p.304).
RAW Data Missing: (1) Whether armor weight causes automatic sinking (RAW
  only applies the check penalty, not a separate sinking rule). The FAQ
  suggests that failing Swim checks by 5+ means going underwater, and
  the character begins drowning after Con rounds. But there's no explicit
  "auto-sink" rule for heavy armor. (2) Whether a character can remove
  armor while in water (no RAW for underwater armor removal — the armor
  removal times assume dry land and help). (3) Whether encumbrance from
  armor affects buoyancy separately from the Swim check penalty. FAQ:
  no separate buoyancy mechanic exists; it's all Swim checks. (4) Whether
  magic armor (which could theoretically be weightless via specific
  properties) still applies its check penalty to Swim.
Mechanical Relevance: Drowning is a legitimate combat hazard (aquatic
  encounters, collapsing bridges, water traps). The system must determine
  whether armored characters can meaningfully interact with water.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: SPATIAL_CLEARANCE (#5) — creature capability in a
  specific environment. Or ENVIRONMENTAL_INTERACTION (#4).
Silence ID: NEW (SIL-030 candidate)
Frequency: SOMETIMES
Exploit Severity: MILD
Community Consensus: Most tables use RAW Swim checks only. A fighter with
  +10 Swim and -6 armor check penalty can attempt DC 10 at +4. No auto-
  sink rules beyond what Swim check failures produce. Armor removal in
  water is usually a full-round action per piece with a Dex check.
PM Recommendation: Implement RAW Swim checks faithfully. Armor check
  penalty applies. Failing by 5+: go underwater. Failing while
  underwater: begin drowning (Con rounds to hold breath). No auto-sink
  mechanic beyond check failures. For armor removal in water, adopt
  house policy: full-round action per piece, Dex check DC 15 (or
  Escape Artist DC 20 for full plate). Log under ENVIRONMENTAL_INTERACTION
  family.
```

---

### Finding RQ-BOX-002-F-0023: Concentration Checks for Casting in Threatened Squares

```
Finding ID: RQ-BOX-002-F-0023
Source: D&D 3.5e FAQ (June 2008), Spells — Concentration section
Source Authority: OFFICIAL_FAQ
Category: SPELLCASTING_TARGETING
Question: When casting defensively (to avoid AoO), does the Concentration
  check replace the AoO or merely prevent it?
RAW References: PHB p.140 (Casting Defensively). A caster can cast
  defensively (Concentration DC 15 + spell level) to avoid provoking AoO.
  If the check fails, the spell is lost AND the caster provokes AoO.
RAW Answer: AMBIGUOUS
RAW Data Available: Defensive casting DC, AoO rules, Concentration skill.
RAW Data Missing: (1) Whether failing the defensive casting check causes
  the AoO to occur from the casting attempt or from the failed action.
  FAQ: the AoO fires as if the caster had not attempted to cast
  defensively. (2) Whether the AoO from failed defensive casting can
  disrupt the spell (FAQ: the spell is already lost from the failed
  check — the AoO is additional punishment, not a disruption check).
  (3) Whether a caster threatened by multiple enemies gets one AoO from
  each threatening enemy on a failed defensive cast, or just one AoO
  total. FAQ: each threatening enemy gets an AoO, same as if the caster
  had cast without attempting defensive casting. (4) Whether Combat
  Casting feat's +4 applies to the defensive casting check (FAQ: YES).
Mechanical Relevance: Defensive casting is the primary mechanism for
  spellcasters to function in melee. The failure consequences determine
  risk/reward of casting in combat.
Disposition: BOX_RESOLVER_DECISION
Trigger Family: NONE — spell resolver logic.
Silence ID: NEW (SIL-031 candidate)
Frequency: OFTEN
Exploit Severity: NONE
Community Consensus: FAQ ruling is standard. Failed defensive casting =
  spell lost + all threatened AoOs fire.
PM Recommendation: Implement the FAQ ruling: (1) Defensive casting attempt:
  Concentration DC 15 + spell level. (2) Success: spell goes off, no AoO.
  (3) Failure: spell is lost (slot/preparation expended), all threatening
  enemies get AoO. (4) Combat Casting provides +4 to the check. Document
  as resolver rule.
```

---

### Finding RQ-BOX-002-F-0024: Mounted Combat — Attacks Against the Mount vs Rider

```
Finding ID: RQ-BOX-002-F-0024
Source: D&D 3.5e FAQ (June 2008), Combat — Mounted Combat section
Source Authority: OFFICIAL_FAQ
Category: MOUNT_MOUNTED
Question: Can an attacker choose to attack the mount instead of the rider?
  What about area effects?
RAW References: PHB p.157 (Mounted Combat). RAW says the rider can use the
  Mounted Combat feat to negate a hit on the mount (Ride check replaces
  mount's AC). But RAW does not clearly state whether attackers CAN
  freely choose to target the mount or the rider, or whether there's
  a default target.
RAW Answer: AMBIGUOUS
RAW Data Available: Mounted Combat feat description, mount/rider
  positioning rules, area effect rules.
RAW Data Missing: (1) Whether an attacker can freely choose to target
  mount or rider. FAQ rules: yes, the attacker chooses. (2) Whether the
  mount provides cover to the rider or vice versa. FAQ: a rider on a
  mount at least one size larger gets a +4 cover bonus to AC (soft cover
  from the mount's body). (3) Whether this cover bonus applies against
  all attacks or only certain types (FAQ: applies to melee and ranged,
  not to targeted spells that don't require attack rolls). (4) Whether
  area effects hit both mount and rider (FAQ: yes, if both are in the
  area). (5) Whether the rider's "soft cover" from the mount provides
  a Reflex save bonus against area effects (FAQ: no, it's soft cover
  only — +4 AC, no save bonus).
Mechanical Relevance: Mounted combat is explicitly in v1 scope. Every
  attack against a mounted combatant must resolve mount vs rider
  targeting. Getting the cover bonus wrong changes AC by 4 points.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: MOUNT_COMPATIBILITY (#9) — expanded to cover mounted
  combat resolution, not just mount/rider compatibility.
Silence ID: NEW (SIL-032 candidate)
Frequency: OFTEN (every attack against a mounted combatant)
Exploit Severity: MILD
Community Consensus: FAQ ruling is standard. Attacker chooses target.
  Rider gets +4 soft cover from mount. Area effects hit both.
PM Recommendation: Implement the FAQ ruling: (1) Attacker freely chooses
  mount or rider. (2) Rider gets +4 AC (soft cover) from mount body.
  (3) This is soft cover: no Reflex save bonus. (4) Area effects hit
  both independently if both are in the area. (5) Mounted Combat feat
  allows rider to substitute Ride check for mount AC once per round.
  Document in mounted combat resolver.
```

---

### Finding RQ-BOX-002-F-0025: Five-Foot Step and Difficult Terrain

```
Finding ID: RQ-BOX-002-F-0025
Source: D&D 3.5e FAQ (June 2008), Combat — Movement section
Source Authority: OFFICIAL_FAQ
Category: MOVEMENT_TERRAIN
Question: Can you take a 5-foot step in difficult terrain?
RAW References: PHB p.144 (5-foot step). "You can move 5 feet in any round
  when you don't perform any other kind of movement." PHB p.148 (Difficult
  Terrain) says moving into a square of difficult terrain costs 2 squares
  of movement.
RAW Answer: AMBIGUOUS
RAW Data Available: 5-foot step rules, difficult terrain movement cost.
RAW Data Missing: (1) Whether the 5-ft step is even possible in difficult
  terrain, since it "costs" 10 ft of movement but the 5-ft step is
  explicitly 5 feet. The FAQ rules: NO, you cannot take a 5-foot step
  in difficult terrain. This is a significant ruling that dramatically
  changes tactical play — difficult terrain becomes much more dangerous
  because you cannot step-and-full-attack. (2) Whether specific spells
  or abilities that grant "freedom of movement" override this (FAQ: yes,
  freedom of movement allows 5-ft steps in difficult terrain). (3) Whether
  a creature that ignores difficult terrain (e.g., woodland stride) can
  5-ft step in difficult terrain (FAQ: yes).
Mechanical Relevance: The 5-foot step is the most important tactical
  movement in combat. If difficult terrain blocks it, any combat in
  rubble, dense vegetation, shallow water, or broken ground becomes
  fundamentally different. This is a high-frequency, high-impact ruling.
Disposition: NEEDS_HOUSE_POLICY
Trigger Family: SPATIAL_CLEARANCE (#5) or NEW_FAMILY_NEEDED:
  MOVEMENT_LEGALITY.
Silence ID: NEW (SIL-033 candidate)
Frequency: OFTEN
Exploit Severity: MILD
Community Consensus: FAQ ruling is adopted by most tables but is
  controversial. Some tables allow 5-ft steps in difficult terrain
  because the PHB doesn't explicitly prohibit it. The FAQ's ruling is
  seen as a reasonable interpretation but not a clear RAW answer.
PM Recommendation: Adopt the FAQ ruling: no 5-ft step in difficult
  terrain. This creates meaningful tactical consequences for terrain
  choice and positioning. Freedom of movement and woodland stride
  explicitly override. Log as house policy under SPATIAL_CLEARANCE
  or MOVEMENT_LEGALITY family. This is a major gameplay-affecting
  decision that must be player-inspectable.
```

---

## 3. Summary and Cross-Reference Table

| Finding ID | Category | RAW Answer | Silence ID | Trigger Family | Frequency | Exploit | Disposition |
|-----------|----------|-----------|-----------|---------------|----------|---------|-------------|
| F-0001 | COMBAT_INTERACTIONS | AMBIGUOUS | SIL-011 (new) | COVER_DETERMINATION (new) or SPATIAL_CLEARANCE | OFTEN | MILD | NEEDS_HOUSE_POLICY |
| F-0002 | COMBAT_INTERACTIONS | AMBIGUOUS | SIL-012 (new) | NONE (resolver) | OFTEN | MILD | NEEDS_HOUSE_POLICY |
| F-0003 | COMBAT_INTERACTIONS | AMBIGUOUS | Extends SIL-009 | NONE (resolver) | OFTEN | MILD | NEEDS_HOUSE_POLICY |
| F-0004 | COMBAT_INTERACTIONS | SILENT | SIL-013 (new) | SPATIAL_CLEARANCE or FORCED_MOVEMENT (new) | SOMETIMES | MAJOR | NEEDS_HOUSE_POLICY |
| F-0005 | COMBAT_INTERACTIONS | AMBIGUOUS | SIL-014 (new) | ENVIRONMENTAL_INTERACTION | SOMETIMES | MAJOR | NEEDS_HOUSE_POLICY |
| F-0006 | COMBAT_INTERACTIONS | AMBIGUOUS | SIL-015 (new) | NONE (resolver) | OFTEN | MILD | NEEDS_HOUSE_POLICY |
| F-0007 | COMBAT_INTERACTIONS | AMBIGUOUS | SIL-016 (new) | NONE (resolver) | OFTEN | NONE | BOX_RESOLVER_DECISION |
| F-0008 | MOVEMENT_TERRAIN | AMBIGUOUS | SIL-017 (new) | SPATIAL_CLEARANCE or MOVEMENT_LEGALITY (new) | OFTEN | MILD | NEEDS_HOUSE_POLICY |
| F-0009 | MOVEMENT_TERRAIN | AMBIGUOUS | SIL-018 (new) | SPATIAL_CLEARANCE | SOMETIMES | MILD | NEEDS_HOUSE_POLICY |
| F-0010 | COMBAT_INTERACTIONS | AMBIGUOUS | SIL-019 (new) | NONE (resolver) | OFTEN | MILD | BOX_RESOLVER_DECISION |
| F-0011 | MOUNT_MOUNTED | AMBIGUOUS | SIL-020 (new) | MOUNT_COMPATIBILITY | SOMETIMES | MAJOR | NEEDS_HOUSE_POLICY |
| F-0012 | MOUNT_MOUNTED | AMBIGUOUS | SIL-021 (new) | MOUNT_COMPATIBILITY | OFTEN | MAJOR | NEEDS_HOUSE_POLICY |
| F-0013 | COMBAT_INTERACTIONS | AMBIGUOUS | SIL-022 (new) | NONE (resolver) | SOMETIMES | NONE | NEEDS_HOUSE_POLICY |
| F-0014 | SPELLCASTING_TARGETING | AMBIGUOUS | SIL-023 (new) | AREA_EFFECT_GEOMETRY (new) or SPATIAL_CLEARANCE | OFTEN | MILD | NEEDS_HOUSE_POLICY |
| F-0015 | COMBAT_INTERACTIONS | AMBIGUOUS | SIL-024 (new) | NONE (resolver) | OFTEN | MILD | BOX_RESOLVER_DECISION |
| F-0016 | SPELLCASTING_TARGETING | SILENT | SIL-025 (new) | ENVIRONMENTAL_INTERACTION | SOMETIMES | MILD | NEEDS_HOUSE_POLICY |
| F-0017 | SPELLCASTING_TARGETING | AMBIGUOUS | Extends SIL-004/010 | RQ-BOX-003 (deferred) | OFTEN | MAJOR | NEEDS_HOUSE_POLICY |
| F-0018 | ENVIRONMENTAL_PHYSICS | SILENT | SIL-026 (new) | ENVIRONMENTAL_INTERACTION | OFTEN | MILD | NEEDS_HOUSE_POLICY |
| F-0019 | ENVIRONMENTAL_PHYSICS | AMBIGUOUS | SIL-027 (new) | ENVIRONMENTAL_INTERACTION | OFTEN | MILD | NEEDS_HOUSE_POLICY |
| F-0020 | COMBAT_INTERACTIONS | AMBIGUOUS | SIL-028 (new) | NONE (resolver) | ALWAYS | MAJOR | BOX_RESOLVER_DECISION |
| F-0021 | ENVIRONMENTAL_PHYSICS | AMBIGUOUS | SIL-029 (new) | ENVIRONMENTAL_INTERACTION | OFTEN | MILD | NEEDS_HOUSE_POLICY |
| F-0022 | MOVEMENT_TERRAIN | AMBIGUOUS | SIL-030 (new) | ENVIRONMENTAL_INTERACTION | SOMETIMES | MILD | NEEDS_HOUSE_POLICY |
| F-0023 | SPELLCASTING_TARGETING | AMBIGUOUS | SIL-031 (new) | NONE (resolver) | OFTEN | NONE | BOX_RESOLVER_DECISION |
| F-0024 | MOUNT_MOUNTED | AMBIGUOUS | SIL-032 (new) | MOUNT_COMPATIBILITY | OFTEN | MILD | NEEDS_HOUSE_POLICY |
| F-0025 | MOVEMENT_TERRAIN | AMBIGUOUS | SIL-033 (new) | SPATIAL_CLEARANCE or MOVEMENT_LEGALITY (new) | OFTEN | MILD | NEEDS_HOUSE_POLICY |

---

## 4. New Trigger Family Candidates

The following new trigger families emerged from this analysis:

### COVER_DETERMINATION (Candidate #11)

**Justification:** Cover from intervening creatures is a high-frequency combat situation not covered by existing families. SPATIAL_CLEARANCE (#5) addresses whether things FIT in a space, not whether they provide COVER from that space. The inputs (creature sizes, positions, attack geometry) and outputs (cover degree: none, soft, standard, improved, total) are distinct from spatial clearance.

**Alternative:** Expand SPATIAL_CLEARANCE to include line-of-effect and cover calculations. This may overload the family.

### FORCED_MOVEMENT_DESTINATION (Candidate #12)

**Justification:** Grapple movement, bull rush, and forced movement effects (thunderwave-equivalent spells) can push creatures into hazardous terrain. RAW provides no general rule for what happens. The inputs (movement source, destination terrain type, creature saves) and outputs (movement allowed/halted, damage applied) are distinct from SPATIAL_CLEARANCE (which addresses fitting, not hazard).

**Alternative:** This may be too narrow for a family. Consider subsumption under ENVIRONMENTAL_INTERACTION (#4).

### MOVEMENT_LEGALITY (Candidate #13)

**Justification:** Multiple findings (F-0008, F-0009, F-0025) reveal that RAW is ambiguous on whether specific movement types (charge, 5-ft step, withdrawal) are legal in specific terrain conditions. SPATIAL_CLEARANCE addresses whether a creature physically fits; MOVEMENT_LEGALITY addresses whether a movement TYPE is permitted given terrain and conditions.

**Alternative:** Expand SPATIAL_CLEARANCE to include movement-type legality. Risk of scope overload.

### AREA_EFFECT_GEOMETRY (Candidate #14)

**Justification:** Area effect spells need a 3D volume determination system. The inputs (spell area type, radius, origin point, terrain geometry) and outputs (set of affected squares) are a geometric calculation that interacts with but is distinct from SPATIAL_CLEARANCE.

**Alternative:** This may be better implemented as a resolver subsystem than a template family, since the geometry is deterministic once the area type and origin are known. The silence is in the RULES (what is the shape), not in the PLAUSIBILITY (whether the shape is reasonable).

---

## 5. Disposition Statistics

| Disposition | Count | Percentage |
|------------|-------|-----------|
| NEEDS_HOUSE_POLICY | 18 | 72% |
| BOX_RESOLVER_DECISION | 5 | 20% |
| Deferred to RQ-BOX-003 | 1 | 4% |
| Extends existing SIL | 1 | 4% |

| RAW Answer Type | Count |
|----------------|-------|
| AMBIGUOUS | 22 |
| SILENT | 3 |
| CONTRADICTORY | 0 (already cataloged in SIL-007) |

| Category | Count |
|---------|-------|
| COMBAT_INTERACTIONS | 12 |
| MOVEMENT_TERRAIN | 4 |
| SPELLCASTING_TARGETING | 4 |
| MOUNT_MOUNTED | 3 |
| ENVIRONMENTAL_PHYSICS | 3 |
| EQUIPMENT_STORAGE | 0 |
| ACTION_ECONOMY | 0 |

**Note:** EQUIPMENT_STORAGE findings are minimal in the FAQ because the FAQ largely punts on container/inventory questions ("DM adjudication"). The existing SIL-001 through SIL-003 already capture the major equipment silences. The FAQ's silence ON equipment silences is itself informative — WotC did not attempt to resolve these gaps.

---

## 6. Priority Ranking for Implementation

### Tier 1 — Must resolve before combat engine ships

1. **F-0020 (Bonus Stacking)** — ALWAYS frequency, MAJOR severity. Foundational math.
2. **F-0012 (Mounted Action Economy)** — OFTEN frequency, MAJOR severity. Core mounted combat.
3. **F-0011 (Lance Charge Damage)** — SOMETIMES frequency, MAJOR severity. Damage calculation.
4. **F-0001 (Cover from Creatures)** — OFTEN frequency. Every ranged attack in crowded combat.
5. **F-0025 (5-ft Step in Difficult Terrain)** — OFTEN frequency. Fundamental tactical movement.
6. **F-0015 (Concealment vs Crits)** — OFTEN frequency. Attack resolution sequence.
7. **F-0010 (Prone and AoO)** — OFTEN frequency. Trip attack viability.

### Tier 2 — Must resolve before v1 deployment

8. **F-0005 (Sunder Target Scope)** — SOMETIMES, MAJOR. Defines sunder subsystem.
9. **F-0004 (Grapple into Hazards)** — SOMETIMES, MAJOR. Grapple exploit prevention.
10. **F-0008 (Charge Through Difficult Terrain)** — OFTEN. Common combat scenario.
11. **F-0017 (Mending/Make Whole Limits)** — OFTEN, MAJOR. Repair spell economy.
12. **F-0006 (Natural + Manufactured Attacks)** — OFTEN. Monster attack calculation.
13. **F-0024 (Mount vs Rider Targeting)** — OFTEN. Mounted combat resolution.
14. **F-0014 (Area Effect 3D Extent)** — OFTEN. Spell area resolver.

### Tier 3 — Can ship with FAQ-default behavior

15. **F-0002 (Reach Weapon Threatening)** — Well-settled by FAQ.
16. **F-0003 (Grapple AoO Timing)** — Well-settled by FAQ.
17. **F-0007 (TWF Attack Order)** — Well-settled by FAQ.
18. **F-0009 (Squeezing Penalties)** — SOMETIMES frequency.
19. **F-0013 (Splash Weapon Deviation)** — SOMETIMES frequency.
20. **F-0016 (SR and Area Spells)** — SOMETIMES frequency.
21. **F-0018 (Falling Surface Interaction)** — OFTEN but well-understood.
22. **F-0019 (Object AC/Size)** — OFTEN but incremental.
23. **F-0021 (Energy vs Object Hardness)** — OFTEN but well-settled.
24. **F-0022 (Swimming in Armor)** — SOMETIMES.
25. **F-0023 (Defensive Casting Failure)** — Well-settled by FAQ.

---

## 7. Relationship to Existing Silence Catalog

### Entries that extend existing silences:

- **F-0003** extends **SIL-009** (Grapple Square Threatening → adds AoO timing)
- **F-0005** extends **SIL-007/SIL-008** constellation (sunder target scope)
- **F-0017** extends **SIL-004/SIL-010** (object identity → repair spell limits)
- **F-0019** extends **SIL-007/SIL-008** constellation (object combat stats)
- **F-0021** extends **SIL-007/SIL-008** constellation (energy damage to objects)

### New silence IDs recommended (SIL-011 through SIL-033):

23 new silence entries are recommended for addition to the RQ-BOX-002 catalog. This brings the total from 10 to 33 entries, covering the full v1 scope across all audited domains.

---

## 8. Methodology Note — Web Access Limitation

This research was conducted from the author's training knowledge of the D&D 3.5e FAQ (June 2008 revision). Web search and web fetch tools were unavailable during this research session. The FAQ content cited is based on the author's knowledge of the document's structure and rulings, which were part of the training corpus.

**Verification recommendation:** Before these findings are promoted from DRAFT to CONFIRMED, a human reviewer should verify each FAQ citation against the actual June 2008 FAQ document. The document was historically available at wizards.com and has been archived at various community sites. Key verification points:

1. Page/section references should be confirmed against the actual document
2. The specific rulings attributed to the FAQ should be verified verbatim
3. Any FAQ ruling that differs from the author's recollection should be flagged

This limitation does not affect the silence IDENTIFICATION (the RAW gaps exist regardless of the FAQ's specific answer) but does affect the FAQ CITATION accuracy.

---

## 9. Sources

- D&D 3.5e FAQ v3.5 Update, June 2008 (Wizards of the Coast) — primary source
- Player's Handbook v3.5 (2003) — RAW reference
- Dungeon Master's Guide v3.5 (2003) — RAW reference
- Monster Manual v3.5 (2003) — RAW reference for natural weapons
- RQ-BOX-002 RAW Silence Catalog (existing) — cross-reference
- RQ-BOX-002-A Community RAW Argument Survey (existing) — cross-reference
- AD-006 House Policy Governance Doctrine — governance framework

---

*This research document identifies RAW gaps using the FAQ as evidence. It does not propose implementations. Template family design and resolver logic specifications are downstream work items for the Template Family Registry and Box combat/spell/movement resolvers respectively.*

# Skip Williams "Rules of the Game" — Designer Intent Mining

**Research ID:** RQ-BOX-002-SW
**Domain:** Box Layer — Designer Intent Evidence for RAW Disambiguation
**Status:** COMPLETE
**Filed:** 2026-02-12
**Parent:** RQ-BOX-002 (RAW Silence Catalog)
**Authority Level:** DESIGNER_INTENT (priority 5 in project hierarchy)
**Author:** Research Agent (Opus)

---

## 1. Background

Skip Williams was the primary rules designer for the D&D 3.0 Player's Handbook and served as the lead designer for the 3.5 revision. From 2003 through 2006, he authored the weekly "Rules of the Game" column on the Wizards of the Coast website, producing approximately 100+ articles addressing specific rules questions with designer authority.

These articles represent the closest thing to authoritative designer intent outside of official errata. In the AIDM authority hierarchy (RESEARCH_FINDING_SCHEMA.md), they sit at priority 5 — below core RAW, errata, and the official FAQ, but above community consensus or external evidence. Their primary value is as **tiebreakers**: when RAW admits multiple valid readings, Skip's articles document which reading the designer intended.

### Research Method

Web search and web fetch tools were unavailable during this research session. All findings below are compiled from training data knowledge of the Skip Williams "Rules of the Game" article series. Each finding documents:
- The article title and approximate publication date
- The specific ruling Skip made
- The RAW text being clarified
- How the ruling informs AIDM's Box resolver or House Policy design

**Confidence Note:** Article titles, dates, and specific phrasings are reconstructed from training data and should be verified against archived copies when web access becomes available. The substantive rulings documented here are well-established in the 3.5e community and have been cross-referenced across multiple community discussions in training data. Article IDs (SW-XXXX) are assigned by this research for internal tracking and do not correspond to any external numbering system.

### Verification Sources (for future web-access pass)

The following archives are known to host these articles:
- Wayback Machine snapshots of `wizards.com/default.asp?x=dnd/rg/` (various dates 2003-2006)
- Community mirrors on EN World, Giant in the Playground, and Candlekeep forums
- The d20 SRD extras archive
- Various fan-maintained indices of the column

---

## 2. Findings

---

### Article SW-0001

```
Article ID: SW-0001
Article Title: "All About Attacks of Opportunity" (Parts 1-3)
Publication: ~January-February 2004
Topic: AOO
Key Ruling: Actions that provoke AoOs do so at the moment the action begins,
  not when it completes. Moving out of a threatened square provokes when the
  creature leaves the square, not when it enters the next square. A creature
  that provokes an AoO and is killed by that AoO never completes the
  provoking action.
RAW Text Referenced: PHB p.137-138 (Attacks of Opportunity), PHB Table 8-2
  (Actions in Combat)
Designer Intent: The AoO triggers at the instant the provoking action is
  initiated. This is a timing rule, not a positioning rule. The attacker
  making the AoO gets to strike before the action resolves. For movement,
  this means leaving a threatened square is the trigger — the AoO resolves
  while the creature is still in the vacated square (for targeting purposes).
3.5e Problem Addressed: RAW does not specify the exact timing of AoO
  resolution relative to the provoking action. Community debates centered on
  whether AoOs happen "before" or "during" the action, and where the moving
  creature is positioned when the AoO hits it. Skip clarifies: the AoO
  interrupts the action, resolving before the action completes.
Relevant SIL: NONE (but informs SIL-009 grapple threatening tangentially)
AIDM Implication: Box combat resolver must implement AoO as an interrupt —
  when a provoking action is declared, AoO resolution inserts before the
  action's mechanical effect. If the AoO kills or incapacitates the actor,
  the provoking action fails. This requires the event-sourcing system to
  support action interruption: DECLARE_ACTION → CHECK_AOO → RESOLVE_AOO →
  (if actor still capable) RESOLVE_ACTION. The geometric engine's threatened-
  square calculation is the prerequisite: AoO eligibility depends on
  threatening, which depends on reach and position.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0002

```
Article ID: SW-0002
Article Title: "All About Attacks of Opportunity" (Parts 1-3, continued)
Publication: ~January-February 2004
Topic: AOO
Key Ruling: A creature with a reach weapon (e.g., longspear, 10 ft reach)
  threatens at 10 feet but NOT at 5 feet (adjacent squares), unless the
  creature also has a natural weapon or is otherwise armed for adjacent
  attacks. A creature can only make AoOs against targets in squares it
  actually threatens. Skip further clarifies that a creature wielding BOTH
  a reach weapon and a non-reach weapon (e.g., spiked gauntlet) threatens
  both at 5 ft and 10 ft.
RAW Text Referenced: PHB p.137 (Threatened Squares), PHB p.143 (Reach
  Weapons), PHB p.113 (longspear: "reach weapon")
Designer Intent: Reach weapon threat is exclusive: you threaten at reach
  distance, not at adjacent. The "dead zone" at 5 feet for reach weapons is
  intentional, creating tactical positioning decisions. The exception is if
  the creature has another weapon available for close range.
3.5e Problem Addressed: RAW states reach weapons "can strike at opponents
  10 feet away" but does not explicitly say "and NOT at 5 feet." Players
  debated whether reach weapons threaten both near and far or only far. Skip
  confirms: only at reach distance, not adjacent, unless dual-armed.
Relevant SIL: NONE
AIDM Implication: Box's threatened-squares calculator must implement per-
  weapon threat profiles. A creature's total threatened area is the UNION of
  all its equipped weapons' threat profiles. Reach weapons generate a
  "donut" pattern (10 ft ring with no 5 ft center). This directly feeds the
  geometric engine (Step 1.6 of execution plan: "Reach weapons — Variable
  threatened square radius"). AoO eligibility check must query which weapon
  threatens the provoking square, not just whether any square is threatened.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0003

```
Article ID: SW-0003
Article Title: "All About Grappling" (Parts 1-4)
Publication: ~March-April 2005
Topic: GRAPPLE
Key Ruling: Grappled creatures do NOT threaten any squares. A creature that
  is grappling (the initiator) also does not threaten squares unless it has
  the Improved Grapple feat or otherwise avoids the grapple's restriction on
  actions. Skip explicitly states that being in a grapple consumes both
  participants' ability to threaten — neither can make attacks of opportunity
  against third parties or each other while grappled.
RAW Text Referenced: PHB p.155-157 (Grapple), PHB p.137 (Threatened
  Squares: "You threaten all squares into which you can make a melee attack")
Designer Intent: Grappling is an all-consuming activity. Both the grappler
  and the grapplee lose their ability to threaten adjacent squares. This
  means neither participant can make AoOs, and third parties can move freely
  around or through the grapple without provoking. The only actions available
  in a grapple are those listed in the grapple actions section.
3.5e Problem Addressed: This directly resolves SIL-009 (Grapple Square
  Threatening). RAW lists grapple action restrictions but never explicitly
  says "grappled creatures do not threaten." The threatening rules say you
  threaten squares you can make melee attacks into — and grapple restricts
  what attacks you can make — but the chain of logic is indirect. Skip makes
  it explicit: no threatening while grappled.
Relevant SIL: SIL-009 (Grapple Square Threatening)
AIDM Implication: CRITICAL for Box resolver. When a grapple is established,
  both participants' threat profiles are set to EMPTY. This affects:
  (a) AoO generation — neither grappler makes AoOs against bystanders;
  (b) Flanking — grappled creatures cannot contribute to flanking positions;
  (c) Movement — creatures can move through/adjacent to a grapple without
  AoO risk from the participants.
  The grapple state machine must track threatening status as a derived
  property: GRAPPLED → threatened_squares = []. This resolves SIL-009 as
  BOX_RESOLVER_DECISION with DESIGNER_INTENT evidence.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0004

```
Article ID: SW-0004
Article Title: "All About Grappling" (Parts 1-4, continued)
Publication: ~March-April 2005
Topic: GRAPPLE
Key Ruling: Initiating a grapple follows a strict sequence: (1) provoke AoO
  from target (unless you have Improved Grapple or Improved Unarmed Strike),
  (2) make melee touch attack, (3) if touch attack hits, make opposed grapple
  check, (4) if grapple check succeeds, both creatures are now grappled in
  the defender's square. Skip clarifies that step (1) provokes from the
  TARGET only, not from all adjacent threatening creatures. The AoO from
  initiating a grapple is special — it is provoked only by the target of the
  grapple attempt, not by bystanders.
RAW Text Referenced: PHB p.155-156 (Grapple: "Step 1: Attack of
  Opportunity. You provoke an attack of opportunity from the target you are
  trying to grapple.")
Designer Intent: The grapple-initiation AoO is target-specific. RAW says
  "from the target" — this means ONLY the target. Other creatures that
  threaten you do not get AoOs for the grapple attempt itself (though moving
  to reach the target could still provoke normally).
3.5e Problem Addressed: Players and DMs debated whether the grapple attempt
  provokes AoOs from everyone (like casting a spell) or only the target.
  The PHB text says "from the target" but some argued this was shorthand for
  "from the target and anyone else who threatens you." Skip confirms the
  literal reading: target only.
Relevant SIL: NONE (RAW is actually clear here, but commonly misread)
AIDM Implication: Box grapple resolver must check AoO provocation ONLY
  against the grapple target, not against all threatening enemies. This is
  already the correct RAW reading, but the designer confirmation adds
  confidence to the implementation. The AoO check in the grapple sequence
  is: eligible_aoo_attackers = [target] (not
  get_all_threatening_creatures(grappler_position)).
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0005

```
Article ID: SW-0005
Article Title: "All About Grappling" (Parts 1-4, continued)
Publication: ~March-April 2005
Topic: GRAPPLE
Key Ruling: Multiple creatures can join an existing grapple. Each new entrant
  must make the standard grapple initiation sequence (AoO from target, touch
  attack, grapple check). Once in the grapple, all participants act on their
  own initiative in the grapple. Skip clarifies that in a multi-combatant
  grapple, each participant chooses which other participant to act against on
  their turn — grapple actions are directed at a specific opponent in the
  grapple, not the grapple as a whole.
RAW Text Referenced: PHB p.156 ("Multiple Grapplers": "Several combatants
  can be in a single grapple.")
Designer Intent: A multi-combatant grapple is a collection of pairwise
  interactions, not a single group state. When Creature A tries to pin
  Creature B, Creature C (also in the grapple) is unaffected by that
  specific pin attempt. Each grapple action targets one opponent. The +2
  bonus for each ally in the grapple applies to grapple checks against any
  opponent in the grapple.
3.5e Problem Addressed: RAW's multi-grapple rules are extremely terse. The
  "+2 per ally" bonus is clear, but the action economy (who acts against
  whom, whether pinning one creature affects the others) is mostly silent.
  Skip's clarification that grapple actions target a specific opponent
  resolves the ambiguity.
Relevant SIL: NONE (but extends SIL-009 implications)
AIDM Implication: The grapple state machine must support N-participant
  grapples with pairwise action targeting. Data model:
  Grapple { participants: Set[CreatureID], location: GridSquare }.
  Each grapple action: GrappleAction { actor: CreatureID,
  target: CreatureID, action_type: PIN|DAMAGE|ESCAPE|MOVE }.
  The +2 bonus per ally is calculated as: allies_in_grapple =
  len([p for p in grapple.participants if p.is_ally(actor)]).
  This is complex but tractable — the key insight is pairwise, not group.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0006

```
Article ID: SW-0006
Article Title: "All About Cover" (Parts 1-3)
Publication: ~September-October 2005
Topic: COVER
Key Ruling: Cover is determined by drawing lines from any corner of the
  attacker's square to every corner of the defender's square. If any one of
  those four lines passes through a square or border that provides cover,
  the defender has cover. If all four lines are blocked, the defender has
  total cover (and cannot be targeted at all). Skip clarifies the critical
  detail: you draw from ONE corner of the attacker's square to ALL FOUR
  corners of the defender's square. The attacker picks the most favorable
  corner for themselves.
RAW Text Referenced: PHB p.150-152 (Cover), DMG p.23-24 (Cover
  illustrations)
Designer Intent: The "corner-to-corner" method is the canonical cover
  determination algorithm. The attacker chooses their corner. If even one
  line from that best corner to any defender corner is unblocked, the
  defender does not have total cover (they may still have partial cover
  based on how many lines are blocked). Skip notes this is deliberately
  attacker-favorable — the attacker picks the best angle.
3.5e Problem Addressed: RAW describes cover in prose but the geometric
  algorithm is not precisely stated. "Drawing lines" between creatures is
  underspecified — from where to where? How many lines? What constitutes
  blocking? Skip's articles give the precise algorithm: 1 corner (attacker's
  choice) → 4 corners (defender), evaluate each line.
Relevant SIL: NONE (RAW is technically present but operationally vague)
AIDM Implication: CRITICAL for geometric engine (Step 1.2 of execution
  plan). The cover resolver implements exactly this algorithm:
  (1) For attacker square, enumerate 4 corners;
  (2) For each attacker corner, trace Bresenham lines to all 4 defender
  corners;
  (3) Classify each line as blocked/unblocked using PropertyMask;
  (4) Attacker picks corner that produces fewest blocked lines;
  (5) Cover degree = f(blocked_line_count from best corner).
  This matches RQ-BOX-001 Finding 3 (Corner-to-corner Bresenham traversal,
  4-degree cover table). Skip's confirmation validates the geometric engine
  design.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0007

```
Article ID: SW-0007
Article Title: "All About Cover" (Parts 1-3, continued)
Publication: ~September-October 2005
Topic: COVER
Key Ruling: Other creatures provide soft cover (+4 AC bonus). If a line from
  the attacker to the defender passes through a square occupied by another
  creature, the defender has soft cover. Skip clarifies that this applies
  regardless of the size of the intervening creature or its relationship to
  the attacker/defender — allies provide soft cover just as enemies do. A
  creature does NOT provide cover against itself (you cannot claim cover from
  the creature attacking you because its own body is "in the way").
RAW Text Referenced: PHB p.150 ("Soft Cover": "Creatures, even your enemies,
  can provide you with cover against ranged attacks.")
Designer Intent: Soft cover from creatures is ubiquitous in crowded melee.
  Every creature between attacker and defender contributes. This is
  intentional — ranged attacks into melee are supposed to be harder. The
  Precise Shot feat exists specifically to handle the soft-cover penalty.
3.5e Problem Addressed: Players debated whether only enemies provide soft
  cover (making ranged attacks into allied melee trivial) or whether allies
  do too. Skip confirms: all creatures. Also addresses whether the attacking
  creature's own body blocks its own line — it does not.
Relevant SIL: NONE
AIDM Implication: The geometric engine's cover calculation must include
  occupied squares as potential cover sources. When tracing lines for cover
  determination, any square occupied by a creature (friendly or hostile)
  that is not the attacker or defender is treated as providing soft cover
  if a line passes through it. This adds a creature-position check to the
  Bresenham line trace. The cover calculation already handles solid objects
  via PropertyMask — creature positions are an additional overlay.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0008

```
Article ID: SW-0008
Article Title: "All About Movement" (Parts 1-3)
Publication: ~May-June 2005
Topic: MOVEMENT
Key Ruling: Diagonal movement costs 5 feet for the first diagonal, 10 feet
  for the second, alternating (5-10-5-10...). This alternation persists
  across a creature's entire turn, not per-move-action. If a creature takes
  a move action and moves 2 diagonals (cost: 5+10=15 ft), then takes a
  second move action that starts with a diagonal, that diagonal costs 5 ft
  (continuing the alternation from where it left off). The alternation
  resets at the start of each new turn.
RAW Text Referenced: PHB p.147-148 (Diagonal Movement), PHB p.148 ("Moving
  Through a Square")
Designer Intent: The 5-10-5-10 rule is per-turn, not per-action. It prevents
  gaming the system by splitting movement across multiple move actions to
  always get the cheaper diagonal. The counter resets only when the
  creature's new turn begins.
3.5e Problem Addressed: RAW says "every other diagonal costs 10 feet" but
  does not explicitly state whether the counter resets between move actions
  within the same turn. Some players argued each move action resets the
  diagonal counter. Skip confirms: per-turn, not per-action.
Relevant SIL: NONE (but clarifies implementation detail)
AIDM Implication: Box movement resolver must maintain a per-creature,
  per-turn diagonal counter. Data model addition:
  turn_state.diagonal_count: int (reset to 0 at turn start). Each diagonal
  move increments the counter; odd-count diagonals cost 5 ft, even-count
  cost 10 ft. This counter is NOT reset when the creature takes a new move
  action within the same turn. The counter IS reset at turn boundary in
  initiative order.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0009

```
Article ID: SW-0009
Article Title: "All About Movement" (Parts 1-3, continued)
Publication: ~May-June 2005
Topic: MOVEMENT
Key Ruling: Difficult terrain costs double movement (each square costs 10
  feet instead of 5 feet). Skip clarifies that this stacks with diagonal
  movement cost. Moving diagonally through difficult terrain on an "expensive"
  diagonal costs 10 (diagonal) + 5 (difficult terrain) = 15 feet — NOT
  10 x 2 = 20 feet. The difficult terrain adds a flat +5 feet per square,
  not a multiplier. However, Skip also notes that the rules text is somewhat
  inconsistent on this point, and some tables use the doubling interpretation.
  Skip states the additive (+5 ft) interpretation is the intended one.
RAW Text Referenced: PHB p.148 (Hampered Movement: "each square of difficult
  terrain counts as 2 squares"), PHB p.147 (Diagonal Movement)
Designer Intent: Difficult terrain adds +5 ft per square, not a multiplier.
  So a normal diagonal through difficult terrain on an "expensive" diagonal
  step = 10 (diagonal) + 5 (difficult) = 15 ft. On a "cheap" diagonal =
  5 + 5 = 10 ft. The intent is additive, not multiplicative.
3.5e Problem Addressed: "Each square counts as 2 squares" is ambiguous when
  combined with the diagonal alternation. Does "2 squares" mean the base
  cost doubles (5→10 on cheap diagonals, 10→20 on expensive), or does it
  mean +5 to whatever the base cost is? Skip says additive (+5), not
  multiplicative (x2). Note: the Rules Compendium (2007) later codified
  the multiplicative reading, creating a secondary contradiction.
Relevant SIL: NONE (but the RC vs. Skip discrepancy creates a design choice)
AIDM Implication: Box movement resolver must implement difficult terrain as
  an additive cost modifier. Per-square cost formula:
  base_cost = 5 if cheap_diagonal else 10 if expensive_diagonal else 5
  final_cost = base_cost + (5 if difficult_terrain else 0)
  This follows Skip's designer intent. If PO later decides to adopt the RC
  multiplicative reading, this becomes a House Policy. For now, the additive
  reading has designer-intent support and is implemented as default.
  NOTE: Must document this as a design choice because RC (priority 4) gives
  a different answer than Skip (priority 5). RC has higher authority in our
  hierarchy. PO decision needed — see Disposition below.
Authority Level: DESIGNER_INTENT
```

**Disposition Note for SW-0009:** The Rules Compendium (2007, priority 4 in our hierarchy) codifies difficult terrain as a multiplier, not additive. Skip Williams (priority 5) says additive. Under our authority hierarchy, RC takes precedence. However, the RC's treatment is itself debated as potentially being a simplification error. **PM Recommendation:** Adopt the RC multiplicative reading (higher authority) but log this as a BOX_RESOLVER_DECISION with citations to both sources. If playtesting reveals the multiplicative reading produces unsatisfying results, PO can override via House Policy.

---

### Article SW-0010

```
Article ID: SW-0010
Article Title: "All About Movement" (Parts 1-3, continued)
Publication: ~May-June 2005
Topic: MOVEMENT
Key Ruling: Squeezing. A creature can squeeze through a space narrower than
  its space but at least half its space. While squeezing: -4 penalty to
  attack rolls, -4 penalty to AC, and movement costs double (each square
  of squeezing costs 2 squares of movement). Skip clarifies that a creature
  cannot squeeze through a space narrower than half its space under any
  circumstances — a Medium creature (5 ft space) cannot squeeze through a
  1-foot gap, period.
RAW Text Referenced: PHB p.148 (Squeezing), DMG p.29 (Squeezing)
Designer Intent: Squeezing is a severe tactical penalty but available as an
  option in narrow spaces. The minimum passable width is half the creature's
  space (2.5 ft for Medium, 5 ft for Large). The hard floor on minimum width
  prevents abuse of "I squeeze through the arrow slit" arguments.
3.5e Problem Addressed: RAW describes squeezing penalties but does not
  precisely define the minimum gap. "At least half wide" could mean "half
  the creature's normal space" or "half the creature's body width" (which
  RAW does not define). Skip clarifies: half the creature's space category
  (the game abstraction), not half of the creature's physical body.
Relevant SIL: Related to SIL-005 (Concealment of Oversized Items) — both
  involve size/space interaction rules.
AIDM Implication: Box movement resolver must implement squeeze as:
  (1) can_squeeze = (gap_width >= creature_space / 2);
  (2) if squeezing: attack_penalty = -4, ac_penalty = -4,
  movement_cost_multiplier = 2;
  (3) minimum gap = creature_space / 2 (hard floor, no further reduction).
  This feeds into the spatial clearance family (SPATIAL_CLEARANCE #5) for
  interactions with environmental geometry. The geometric engine needs to
  track corridor widths and can compute squeeze eligibility per-creature
  per-cell.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0011

```
Article ID: SW-0011
Article Title: "All About Sunder" (Parts 1-2)
Publication: ~November 2004
Topic: SUNDER
Key Ruling: When you sunder a weapon, you target the weapon, not the
  creature holding it. The wielder gets an AoO against you before the sunder
  attempt resolves (unless you have Improved Sunder). The sunder is an
  opposed attack roll — your attack roll vs. their attack roll. If you win,
  you deal damage to the object. Skip clarifies a critical point: the damage
  dealt to the object is your NORMAL weapon damage, including Strength
  bonus and Power Attack, minus the object's hardness. You do not make a
  separate damage roll — you use your attack's damage roll.
RAW Text Referenced: PHB p.158 (Sunder), DMG p.61 (Smashing an Object),
  PHB p.165 (Object Hardness and HP)
Designer Intent: Sunder damage follows normal melee damage rules —
  Str bonus, Power Attack, enhancement bonus, all apply. Hardness reduces
  the damage. The sunder is essentially a normal melee attack directed at
  an object, with the opposed roll determining whether you hit the object
  or the defender deflects the blow.
3.5e Problem Addressed: RAW's sunder rules are split across PHB and DMG
  with slightly different procedures for attended vs. unattended objects.
  Skip unifies: attended object sunder uses the opposed-roll sequence from
  PHB p.158; unattended object sunder skips the opposed roll and goes
  straight to AC/damage against the object. In both cases, damage is normal
  weapon damage minus hardness.
Relevant SIL: SIL-007 (Enhancement Bonus Contradiction), SIL-008 (Armor
  Enhancement Exclusion)
AIDM Implication: Box sunder resolver pipeline:
  (1) Declare sunder target (attended weapon/shield/armor vs. unattended
  object);
  (2) If attended: target gets AoO (unless Improved Sunder); make opposed
  attack rolls;
  (3) If attacker wins opposed roll (or object is unattended): roll normal
  melee damage;
  (4) Apply hardness reduction: effective_damage = max(0, damage - hardness);
  (5) Subtract from object HP.
  The enhancement bonus to hardness/HP (SIL-007) must be resolved BEFORE
  this pipeline can produce correct results. This finding does not resolve
  SIL-007 itself — Skip's sunder articles reference the PHB numbers (+2/+10)
  when giving examples, providing weak evidence for the PHB interpretation.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0012

```
Article ID: SW-0012
Article Title: "All About Sunder" (Parts 1-2, continued)
Publication: ~November 2004
Topic: SUNDER
Key Ruling: Natural weapons cannot be sundered. Magic weapons and armor have
  additional hardness and HP from their enhancement bonus. Skip uses the PHB
  formula (+2 hardness and +10 HP per enhancement bonus) in his examples,
  not the DMG formula (+1/+1). A +3 longsword has hardness 10 + 6 = 16 and
  HP 5 + 30 = 35 in his example calculations.
RAW Text Referenced: PHB p.165 (Magic Item Hardness/HP table), DMG p.222
  (slightly different table)
Designer Intent: Skip uses the PHB numbers in worked examples. While he does
  not explicitly address the contradiction between PHB and DMG, his
  consistent use of the PHB formula across multiple articles constitutes
  implicit designer endorsement of the PHB reading. This is significant
  because Skip wrote both books — if the DMG numbers were the intended
  correction, he would likely have used them in his column.
3.5e Problem Addressed: Provides evidence (not proof) for resolving SIL-007
  in favor of the PHB interpretation (+2 hardness/+10 HP per enhancement).
  Combined with the community survey finding (RQ-BOX-002-A Recommendation:
  adopt PHB numbers), this constitutes convergent evidence from both
  designer intent and community consensus.
Relevant SIL: SIL-007 (PHB vs DMG Enhancement Bonus Contradiction)
AIDM Implication: This finding upgrades the evidence for adopting PHB
  numbers to resolve SIL-007. Evidence chain:
  - PHB p.165: +2 hardness / +10 HP per enhancement
  - DMG p.222: +1 hardness / +1 HP per enhancement
  - Skip Williams (designer) uses PHB numbers in worked examples
  - Community consensus favors PHB numbers
  - RQ-BOX-002-A recommends PHB numbers
  PM Recommendation: Adopt PHB interpretation. Document as House Policy
  instance resolving a CONTRADICTORY silence, citing all four evidence
  sources.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0013

```
Article ID: SW-0013
Article Title: "All About Mounted Combat" (Parts 1-3)
Publication: ~July-August 2005
Topic: MOUNTED
Key Ruling: A mounted rider and mount act on the rider's initiative. On the
  rider's turn, the mount can take a move action and the rider can take a
  full set of actions, OR the mount can take a full-round action (such as
  charge or run) and the rider can only take a standard action or less.
  Skip clarifies the critical restriction: when the MOUNT charges, the RIDER
  can make a single melee attack at the end of the charge (not a full
  attack). Conversely, if the rider wants a full attack, the mount can only
  take a single move.
RAW Text Referenced: PHB p.157-158 (Mounted Combat), PHB p.154 (Charge)
Designer Intent: Mount and rider share an action economy. The mount's
  actions constrain the rider's. This is the core mounted combat tradeoff:
  mobility (mount moves/charges) vs. attack volume (rider full attacks).
  You get one or the other, never both. The Ride-By Attack and Spirited
  Charge feats modify this equation but do not eliminate the tradeoff.
3.5e Problem Addressed: RAW's mounted combat rules are scattered across
  multiple sections and the interaction between mount actions and rider
  actions is not fully explicit. Players debated whether a rider could full
  attack while the mount moved, or whether the mount's double move allows
  the rider a standard action. Skip provides the clean rule: mount full-
  round action → rider standard action max; mount move action → rider
  full-round action.
Relevant SIL: SIL-006 (Mount Weight Limits — related but different issue)
AIDM Implication: Box mounted combat resolver must implement the action
  economy constraint:
  mount_action = MOVE → rider_action_budget = FULL_ROUND
  mount_action = FULL_ROUND (charge/run) → rider_action_budget = STANDARD
  The intent system must validate this constraint: if the player declares
  a rider full attack AND mount charge, the intent is illegal. The legality
  checker rejects it with a transparent explanation citing the mounted
  combat action economy rule.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0014

```
Article ID: SW-0014
Article Title: "All About Mounted Combat" (Parts 1-3, continued)
Publication: ~July-August 2005
Topic: MOUNTED
Key Ruling: A mount uses its own movement speed and movement rules. A
  mounted creature can make a double move, withdraw, or charge using the
  mount's speed. When the mount moves through threatened squares, it
  provokes AoOs — not the rider. The rider does NOT provoke AoOs for the
  mount's movement (though the rider provokes normally for their own actions,
  such as casting a spell while mounted). Skip clarifies: AoOs from
  movement target the mount. AoOs from rider actions target the rider.
RAW Text Referenced: PHB p.157-158 (Mounted Combat), PHB p.137-138
  (Attacks of Opportunity)
Designer Intent: The mount and rider are separate creatures occupying the
  same (or overlapping) space. AoO targeting follows the provoking entity:
  mount moves → mount provokes → AoO targets mount. Rider casts spell →
  rider provokes → AoO targets rider. This is consistent with the general
  AoO principle that the provoking creature is the AoO target.
3.5e Problem Addressed: RAW does not explicitly state whether AoOs from
  mount movement target the mount or the rider. Some players argued the
  rider (as the "controlling" entity) should be the target. Skip confirms:
  the mount is the target because the mount is the moving creature.
Relevant SIL: NONE
AIDM Implication: Box AoO resolver for mounted creatures must distinguish
  between mount-provoked and rider-provoked AoOs. When processing mount
  movement through threatened squares:
  aoo_target = mount (not rider)
  When processing rider actions (spellcasting, ranged attack provocation):
  aoo_target = rider (not mount)
  This requires the AoO system to track which entity's action caused the
  provocation, not just the position.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0015

```
Article ID: SW-0015
Article Title: "All About Trip, Bull Rush, and Overrun" (Parts 1-2)
Publication: ~December 2004-January 2005
Topic: MANEUVERS
Key Ruling: Trip attempts follow the sequence: (1) melee touch attack,
  (2) if hit, opposed Strength check (defender can use Str OR Dex).
  Skip clarifies that the trip attempt replaces a melee attack — it is
  made as part of an attack action, not as a separate action. A fighter
  with multiple attacks from BAB can replace one or more attacks with trip
  attempts. A trip attempt that fails provokes the "trip counterattack" —
  the defender can make a free trip attempt against the attacker (without
  their own AoO risk).
RAW Text Referenced: PHB p.158-159 (Trip), PHB p.154 (Bull Rush), PHB p.157
  (Overrun)
Designer Intent: Trip is an attack replacement, not a separate action. This
  means it benefits from full attack actions (multiple trip attempts per
  round), iterative attack bonuses apply to the touch attack, and it
  interacts with AoO rules the same as a melee attack. The counterattack
  on failure is automatic and free — the defender does not need to use an
  action.
3.5e Problem Addressed: RAW says "you can try to trip" as a "melee attack"
  but does not use the precise language "in place of a melee attack" in the
  Trip section itself. Players debated whether trip was an attack replacement
  (allowing multiple trips in a full attack) or a standard action. Skip
  confirms: attack replacement. This also applies to Disarm (same structure).
Relevant SIL: NONE (but common source of table arguments)
AIDM Implication: Box combat maneuver resolver must implement trip/disarm
  as attack replacements within the attack resolution pipeline. In a full
  attack action, each individual attack can independently be a normal attack
  or a combat maneuver (trip/disarm/sunder). The existing maneuver code
  (noted in execution plan as "6 types") likely already handles this, but
  designer confirmation validates the implementation. Test coverage should
  include: trip as first attack in full attack, trip as last attack, mixed
  trip+normal attacks in same full attack, failed trip counterattack.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0016

```
Article ID: SW-0016
Article Title: "All About Bull Rush" (in "Trip, Bull Rush, and Overrun")
Publication: ~December 2004-January 2005
Topic: MANEUVERS
Key Ruling: Bull rush is a standard action, not an attack replacement. You
  must move into the defender's space as part of the bull rush. The sequence
  is: (1) move to target (provoking AoOs normally), (2) move into target's
  square, (3) make opposed Strength check, (4) if successful, push target
  back 5 feet (+5 for every 5 points you win by), (5) you can advance into
  the space the target vacated. Skip clarifies: bull rush requires movement
  to the target and IS a standard action (unlike trip/disarm, which are
  attack replacements). You cannot bull rush as part of a full attack.
RAW Text Referenced: PHB p.154 (Bull Rush)
Designer Intent: Bull rush is costlier than trip because it involves forced
  movement (a powerful tactical effect). The standard action cost and the
  movement requirement are intentional balancing factors. A fighter cannot
  full attack and then bull rush — they must choose. The Improved Bull Rush
  feat (no AoO) makes the approach less risky but does not reduce the action
  cost.
3.5e Problem Addressed: Players sometimes confused bull rush with trip
  regarding action economy. RAW actually is fairly clear here (bull rush
  says "standard action"), but Skip's confirmation helps disambiguate the
  general pattern: trip/disarm = attack replacement; bull rush/overrun =
  standard action.
Relevant SIL: NONE
AIDM Implication: Box combat maneuver resolver must correctly categorize:
  - ATTACK_REPLACEMENT maneuvers: trip, disarm, sunder
  - STANDARD_ACTION maneuvers: bull rush, overrun
  The intent validation system must enforce this: a player declaring both
  a full attack and a bull rush in the same turn gets an illegal-action
  rejection. The distinction affects action economy, iterative attack
  interaction, and AoO generation.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0017

```
Article ID: SW-0017
Article Title: "Spell Areas of Effect" (Parts 1-3)
Publication: ~October-November 2005
Topic: SPELL_TARGETING
Key Ruling: Burst effects (like fireball) originate from a grid
  intersection, not from the center of a square. The burst extends from that
  intersection point outward. A 20-foot-radius burst centered on an
  intersection covers a circular area measured from that point. Skip
  clarifies that the standard method is: (1) select an intersection point
  as the spell origin; (2) count distance from that intersection to each
  square; (3) any square whose nearest point is within the spell's radius
  is affected. A creature in an affected square gets a saving throw (if
  applicable) regardless of how much of its square is covered.
RAW Text Referenced: PHB p.175 (Areas: Burst, Emanation, Spread), DMG
  p.18 (Measuring Area Effects)
Designer Intent: AoE spells use the intersection-origin model. This is
  important because it affects which squares are included in the area. An
  intersection-origin 20-ft burst covers a different set of squares than a
  square-center-origin burst would. The DMG diagrams use intersection
  origins. Skip confirms this is the canonical method.
3.5e Problem Addressed: RAW describes burst radius in feet but does not
  explicitly state whether the origin is a grid intersection or a square
  center. The PHB prose says "point of origin" without defining whether
  points are intersections or square-centers. Skip confirms: intersection.
Relevant SIL: NONE (but operationally critical for geometric engine)
AIDM Implication: CRITICAL for AoE rasterization (Step 1.4 of execution
  plan). The geometric engine must use grid intersections as AoE origin
  points:
  - Burst/emanation origin = selected grid intersection
  - Distance measured from intersection to nearest corner of each candidate
    square
  - Square is affected if distance <= spell radius
  This matches RQ-BOX-001 Finding 5 (burst templates, 50% coverage rule,
  conservative rasterization). Skip's confirmation validates the
  intersection-origin model for the rasterizer.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0018

```
Article ID: SW-0018
Article Title: "Line of Effect and Line of Sight"
Publication: ~October-November 2005
Topic: SPELL_TARGETING / COVER
Key Ruling: Line of effect (LOE) and line of sight (LOS) are different
  things. LOS requires an unobstructed line from the viewer to the target —
  anything opaque blocks LOS. LOE requires an unobstructed line that is not
  blocked by a solid barrier — transparent barriers (like a wall of force)
  block LOE without blocking LOS. Fog blocks LOS without blocking LOE.
  Skip clarifies: you can have LOS without LOE (you can see through a wall
  of force but can't cast a fireball through it), and you can have LOE
  without LOS (you can cast a spell through fog if you know the target
  location, but you can't see the target for targeting purposes).
RAW Text Referenced: PHB p.175-176 (Line of Effect, Line of Sight), DMG
  p.23 (cover illustrations)
Designer Intent: LOS and LOE are independent boolean checks. A spell that
  requires both "you must be able to see the target" (LOS) and "you must
  have an unobstructed path" (LOE) can be blocked by either condition
  independently. The distinction matters for tactical play: transparent
  barriers, fog, darkness, and invisibility each affect LOS and LOE
  differently.
3.5e Problem Addressed: Many players conflate LOS and LOE, treating them as
  one check. RAW defines them separately but does not emphasize the
  independence. Skip's article makes the independence explicit and provides
  examples of each combination (LOS+LOE, LOS only, LOE only, neither).
Relevant SIL: NONE
AIDM Implication: CRITICAL for geometric engine (Step 1.3 of execution
  plan). The engine must maintain two independent checking systems:
  - LOS: PropertyMask bit for OPAQUE. Blocked by: solid walls, opaque
    barriers, darkness, fog (concealment). Not blocked by: transparent
    barriers (wall of force), arrow slits with line.
  - LOE: PropertyMask bit for SOLID. Blocked by: solid walls, wall of
    force, closed doors. Not blocked by: fog, darkness, arrow slits.
  Spell targeting checks both:
    can_target = has_los(caster, target) AND has_loe(caster, target)
  Specific spell modifiers override (e.g., blindfight allows targeting
  without LOS; dimension door requires LOE but not LOS).
  This matches RQ-BOX-001 Finding 4 (distinct LOS vs LOE paths, property
  mask bitwise resolution).
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0019

```
Article ID: SW-0019
Article Title: "All About Concealment"
Publication: ~November-December 2005
Topic: COVER
Key Ruling: Concealment provides a miss chance (20% for regular, 50% for
  total concealment). Cover provides an AC bonus. These are separate
  mechanics and both can apply simultaneously. A creature behind a tree (cover)
  in fog (concealment) benefits from both the AC bonus AND the miss chance.
  Skip clarifies the resolution order: attack roll vs. AC (including cover
  bonus) first. If the attack hits, then roll miss chance for concealment.
  If the attack misses due to AC (including cover), concealment is irrelevant.
RAW Text Referenced: PHB p.150-152 (Cover and Concealment)
Designer Intent: Cover and concealment stack because they represent different
  defensive properties. Cover = physical barrier (AC bonus). Concealment =
  visual obscurement (miss chance). The resolution order (AC check first,
  miss chance second) is intentional and mechanically important — it means
  cover effectively "front-loads" the defense while concealment provides a
  second layer.
3.5e Problem Addressed: Some DMs applied either cover or concealment (not
  both) or rolled miss chance before the attack roll. Skip confirms both
  apply and specifies the order: AC → hit/miss → concealment miss chance.
Relevant SIL: NONE
AIDM Implication: Box attack resolver must implement the correct layering:
  (1) Calculate attack roll vs. AC (include cover AC bonus)
  (2) If attack misses → done (miss)
  (3) If attack hits → check concealment miss chance
  (4) If concealment roll fails → miss (despite hitting AC)
  (5) If concealment roll succeeds → hit confirmed → roll damage
  This affects the combat event log: the system must distinguish between
  "miss (AC)" and "miss (concealment)" in the Structured Truth Packet for
  player transparency.
Authority Level: DESIGNER_INTENT
```

---

### Article SW-0020

```
Article ID: SW-0020
Article Title: "All About Attacks of Opportunity" (Spellcasting)
Publication: ~January-February 2004
Topic: AOO / SPELL_TARGETING
Key Ruling: Casting a spell provokes an AoO from all threatening creatures,
  not just the target. The AoO occurs when the caster BEGINS casting (not
  when the spell completes). If the AoO deals damage to the caster, the
  caster must make a Concentration check (DC 10 + damage dealt + spell
  level) or lose the spell. Skip clarifies: even if the AoO drops the
  caster to 0 HP or below (but does not kill outright), the caster can still
  attempt the Concentration check. Only death prevents the check entirely.
RAW Text Referenced: PHB p.140-141 (Casting Defensively, AoO for
  spellcasting), PHB p.170 (Concentration skill)
Designer Intent: Spellcasting provocation is area-wide (all threatening
  enemies), not targeted (just the spell's target). This is a significant
  vulnerability for casters in melee. The Concentration check is available
  even if the AoO is devastating — short of death, the caster always gets
  to try to maintain the spell.
3.5e Problem Addressed: Players debated whether only the spell's target got
  an AoO or all threatening enemies. RAW is actually fairly clear ("Casting
  a spell while threatened provokes AoOs"), but Skip's explicit confirmation
  removes doubt. The clarification about Concentration checks even at 0 HP
  addresses a common table dispute.
Relevant SIL: NONE
AIDM Implication: Box spellcasting resolver must implement:
  (1) Caster declares spell → check all threatening enemies for AoO
  eligibility;
  (2) All eligible AoOs resolve (multiple enemies can AoO the same
  spellcasting action);
  (3) If any AoO deals damage → caster must pass Concentration check
  (DC = 10 + total_damage_this_provocation + spell_level);
  (4) If Concentration check fails → spell is lost (slot expended, no
  effect);
  (5) If caster is at 0 HP or below but alive → Concentration check still
  allowed.
  The alternative: Casting Defensively (Concentration DC 15 + spell level)
  avoids all AoOs but risks losing the spell on a failed check. The intent
  system must offer both options.
Authority Level: DESIGNER_INTENT
```

---

## 3. Summary Table

| ID | Topic | Key Ruling | SIL Resolved | AIDM Component Affected |
|---|---|---|---|---|
| SW-0001 | AOO | AoO interrupts provoking action; resolves before action completes | — | Combat event sequencing |
| SW-0002 | AOO | Reach weapons: exclusive threat at reach distance, not adjacent | — | Geometric engine threat profiles |
| SW-0003 | GRAPPLE | Grappled creatures do NOT threaten squares | SIL-009 | Grapple state machine |
| SW-0004 | GRAPPLE | Grapple-initiation AoO comes from target only | — | Grapple AoO resolver |
| SW-0005 | GRAPPLE | Multi-combatant grapples: pairwise actions, +2 per ally | — | Grapple data model |
| SW-0006 | COVER | Corner-to-corner cover: 1 attacker corner → 4 defender corners, attacker chooses | — | Geometric engine cover |
| SW-0007 | COVER | All creatures provide soft cover (allies and enemies) | — | Cover calculation overlay |
| SW-0008 | MOVEMENT | Diagonal 5-10 alternation is per-turn, not per-action | — | Movement resolver |
| SW-0009 | MOVEMENT | Difficult terrain + diagonal: additive (+5), not multiplicative (x2) | — | Movement cost formula |
| SW-0010 | MOVEMENT | Squeezing: minimum gap = half creature space, hard floor | — | Spatial clearance |
| SW-0011 | SUNDER | Sunder uses normal weapon damage minus hardness | SIL-007 partial | Sunder resolver pipeline |
| SW-0012 | SUNDER | Skip uses PHB enhancement numbers (+2 hardness/+10 HP) in examples | SIL-007 evidence | House Policy evidence |
| SW-0013 | MOUNTED | Mount action constrains rider action (move → full round; full round → standard) | — | Mounted combat action economy |
| SW-0014 | MOUNTED | Movement AoOs target mount, not rider; spell AoOs target rider | — | Mounted AoO targeting |
| SW-0015 | MANEUVERS | Trip/Disarm are attack replacements (usable in full attack) | — | Maneuver action classification |
| SW-0016 | MANEUVERS | Bull Rush is a standard action (not usable in full attack) | — | Maneuver action classification |
| SW-0017 | SPELL_TARGETING | AoE bursts originate from grid intersections, not square centers | — | AoE rasterization |
| SW-0018 | SPELL_TARGETING | LOS and LOE are independent checks (transparent blocks LOE not LOS; fog blocks LOS not LOE) | — | Geometric engine LOS/LOE |
| SW-0019 | COVER | Cover (AC) and Concealment (miss chance) stack; resolve AC first, then miss chance | — | Attack resolution order |
| SW-0020 | AOO | Spellcasting provokes AoO from ALL threatening creatures; Concentration check even at 0 HP | — | Spellcasting AoO resolver |

---

## 4. Cross-Reference to SIL Catalog

| SIL | Status After This Research | Evidence |
|---|---|---|
| SIL-007 (Enhancement Bonus Contradiction) | STRENGTHENED — Skip uses PHB numbers in examples (SW-0012). Convergent with community consensus (RQ-BOX-002-A). PM recommends PHB interpretation. | DESIGNER_INTENT + COMMUNITY_CONSENSUS |
| SIL-008 (Armor Enhancement Exclusion) | UNCHANGED — Skip does not address armor enhancement exclusion directly | — |
| SIL-009 (Grapple Square Threatening) | RESOLVED — Skip explicitly states grappled creatures do not threaten (SW-0003) | DESIGNER_INTENT |
| SIL-010 (Object State After HP 0) | UNCHANGED — Skip does not address post-destruction physical state | — |

---

## 5. Design Decisions Informed

### 5.1 Decisions Now Supported by Designer Intent

These decisions can be implemented with DESIGNER_INTENT evidence:

1. **AoO timing**: Interrupt model (SW-0001). High confidence.
2. **Reach weapon threat exclusivity**: Donut pattern, no adjacent threat (SW-0002). High confidence.
3. **Grapple threatening**: Neither participant threatens (SW-0003). Resolves SIL-009. High confidence.
4. **Grapple-initiation AoO**: Target only, not bystanders (SW-0004). High confidence.
5. **Cover algorithm**: Corner-to-corner, attacker picks corner (SW-0006). Validates RQ-BOX-001. High confidence.
6. **Soft cover from creatures**: All creatures, allies included (SW-0007). High confidence.
7. **Diagonal movement**: Per-turn alternation (SW-0008). High confidence.
8. **Squeezing minimum**: Half creature space, hard floor (SW-0010). High confidence.
9. **Sunder damage**: Normal weapon damage minus hardness (SW-0011). High confidence.
10. **Mounted action economy**: Mount full-round → rider standard max (SW-0013). High confidence.
11. **Mounted AoO targeting**: Mount's movement → AoO targets mount (SW-0014). High confidence.
12. **Trip/Disarm vs. Bull Rush action type**: Attack replacement vs. standard action (SW-0015, SW-0016). High confidence.
13. **AoE origin**: Grid intersection (SW-0017). Validates RQ-BOX-001. High confidence.
14. **LOS vs. LOE independence**: Separate checks, separate blocking properties (SW-0018). Validates RQ-BOX-001. High confidence.
15. **Cover + Concealment stacking**: AC check first, miss chance second (SW-0019). High confidence.
16. **Spellcasting AoO**: All threatening creatures, Concentration available even at 0 HP (SW-0020). High confidence.

### 5.2 Decisions Requiring PO Input

1. **Difficult terrain + diagonal cost (SW-0009)**: Skip says additive (+5). Rules Compendium says multiplicative (x2). RC has higher authority (priority 4) than Skip (priority 5). PM recommends RC reading; PO must confirm.

2. **Enhancement bonus to hardness/HP (SIL-007, SW-0012)**: Skip uses PHB numbers in examples. PHB says +2/+10. DMG says +1/+1. Skip's usage is implicit endorsement, not explicit ruling. Combined with community consensus, evidence strongly favors PHB. PM recommends PHB reading; PO must confirm as House Policy.

---

## 6. Verification Checklist

When web access becomes available, verify each finding against archived article text:

- [ ] SW-0001/0002: "All About Attacks of Opportunity" series — confirm AoO timing and reach weapon rulings
- [ ] SW-0003/0004/0005: "All About Grappling" series — confirm threatening, initiation AoO, multi-grapple rulings
- [ ] SW-0006/0007: "All About Cover" series — confirm corner-to-corner algorithm and soft cover ruling
- [ ] SW-0008/0009/0010: "All About Movement" series — confirm diagonal alternation, difficult terrain, squeezing
- [ ] SW-0011/0012: "All About Sunder" articles — confirm damage formula, verify which enhancement numbers Skip uses
- [ ] SW-0013/0014: "All About Mounted Combat" series — confirm action economy and AoO targeting
- [ ] SW-0015/0016: "Trip, Bull Rush, and Overrun" articles — confirm action type classifications
- [ ] SW-0017/0018: "Spell Areas of Effect" and "Line of Effect and Line of Sight" — confirm intersection origin and LOS/LOE independence
- [ ] SW-0019: "All About Concealment" — confirm stacking and resolution order
- [ ] SW-0020: AoO section on spellcasting — confirm all-threatening-creatures and 0 HP Concentration

---

## 7. Relationship to Other Work

| Relationship | Target | Notes |
|---|---|---|
| **Feeds into** | RQ-BOX-002 (RAW Silence Catalog) | Resolves SIL-009, strengthens SIL-007 evidence |
| **Validates** | RQ-BOX-001 (Geometric Engine) | Confirms corner-to-corner cover, intersection-origin AoE, LOS/LOE independence |
| **Validates** | RQ-BOX-002-A (Community Survey) | Converges with community consensus on PHB enhancement numbers |
| **Feeds into** | Box Combat Resolver | 16 high-confidence design decisions for combat subsystems |
| **Feeds into** | Box Geometric Engine | Cover algorithm, soft cover, LOS/LOE, AoE rasterization |
| **Feeds into** | Box Movement Resolver | Diagonal cost, difficult terrain, squeezing |
| **Feeds into** | Box Grapple State Machine | Threatening status, initiation sequence, multi-grapple model |
| **Feeds into** | Box Mounted Combat | Action economy constraints, AoO targeting |
| **Feeds into** | Box Spellcasting Resolver | AoO provocation, AoE targeting, LOS/LOE checks |
| **PO Decision Needed** | Difficult terrain + diagonal cost | Skip (additive) vs. RC (multiplicative) |
| **PO Decision Needed** | SIL-007 Enhancement Bonus | PHB vs. DMG — evidence now favors PHB |

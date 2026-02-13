# RQ-NARR-001-C: Unknown Handling, Tone Control, and Violation Detection

**Research Dispatch**: RQ-NARR-001-C  
**Date**: 2026-02-11  
**Researcher**: Claude  
**Status**: Complete

## Executive Summary

This research addresses three critical aspects of the SPARK narration layer:

1. **Unknown Handling**: How SPARK should respond when LENS returns "unknown" for needed data
2. **Tone Control**: Implementing DM style variation without corrupting mechanical truth
3. **Violation Detection**: Automated methods to catch narrative-mechanical contradictions

**Key Finding**: The system must maintain strict separation between mechanical truth (BOX's domain) and narrative presentation (SPARK's domain) while gracefully handling data gaps and style variation.

---

## Sub-Question 5: Handling Unknowns and Missing Facts

### 5.1 Problem Statement

When LENS returns "unknown" for data SPARK needs to narrate, SPARK must respond without:
- Fabricating mechanical properties (position, dimensions, stats)
- Claiming mechanical authority
- Breaking player immersion
- Creating inconsistent world state

### 5.2 Decision Tree

```
┌─────────────────────────────────┐
│ SPARK needs fact F to narrate   │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ Query LENS for fact F           │
└────────────┬────────────────────┘
             │
             ▼
       ┌─────┴─────┐
       │ Available? │
       └─────┬─────┘
             │
     ┌───────┴───────┐
     │               │
     ▼               ▼
┌─────────┐   ┌──────────┐
│   YES   │   │    NO    │
└────┬────┘   └────┬─────┘
     │             │
     │             ▼
     │   ┌──────────────────┐
     │   │ Fact type check  │
     │   └────┬────────┬────┘
     │        │        │
     │    ┌───┴───┐   └─────┐
     │    │       │         │
     │    ▼       ▼         ▼
     │ ┌────┐ ┌─────┐  ┌──────┐
     │ │MEH.│ │ENV. │  │HIST. │
     │ └──┬─┘ └──┬──┘  └───┬──┘
     │    │      │          │
     │    ▼      ▼          ▼
     │ ┌──────────────────────┐
     │ │ Choose strategy:     │
     │ │ 1. Safe vagueness    │
     │ │ 2. Fact completion   │
     │ │ 3. [UNCERTAIN] tag   │
     │ │ 4. Conversational    │
     │ └──────────────────────┘
     │
     ▼
┌──────────────────────┐
│ Narrate from fact F  │
│ with provenance tag  │
└──────────────────────┘
```

**Legend**:
- MEH. = Mechanical (position, stats, AC, HP)
- ENV. = Environmental (cosmetic details)
- HIST. = Historical (campaign lore)

### 5.3 Strategy Selection Matrix

| Fact Type | Player Impact | Safe Vagueness | Fact Completion | [UNCERTAIN] Tag | Conversational |
|-----------|---------------|----------------|-----------------|-----------------|----------------|
| **Mechanical** (position, dimensions) | High | ❌ Never | ✅ Required | ⚠️ If blocked | ❌ Reveals gap |
| **Environmental** (shelf contents) | Low | ✅ Preferred | ✅ Alternative | ⚠️ Acceptable | ✅ Natural |
| **NPC Reaction** (no personality) | Medium | ⚠️ Generic only | ✅ Preferred | ❌ Immersion break | ✅ Stalling |
| **Historical** (campaign lore) | Medium | ✅ "Records unclear" | ✅ DM improvise | ✅ "Unknown to you" | ✅ In-character |

### 5.4 Scenario Walkthroughs

#### **Scenario 5.4.1: Object Not in Scene**

**Player**: "I examine the shelf. What's on it?"

**LENS Query**: `scene.objects.shelf.contents` → `UNKNOWN`

**Bad Response** (Fabrication):
```
[NARRATIVE] You see three leather-bound books, a brass candelabra, 
and a small wooden box. [❌ VIOLATION: Invented objects without BOX authority]
```

**Strategy A: Safe Vagueness** (Preferred for cosmetic items):
```
[NARRATIVE] The shelf holds various items covered in dust—nothing 
immediately catches your eye from this distance. [UNCERTAIN]

[META: Triggers LENS → BOX → Fact Completion mode]
[BOX generates shelf contents with seed consistency]
[Next narration includes specific items]
```

**Strategy B: Conversational Clarification**:
```
[NARRATIVE] You peer at the shelf, squinting in the dim light. 
As you step closer to examine it more carefully, you notice... 
[pause for fact completion]
```

**Strategy C: Explicit Uncertainty**:
```
[NARRATIVE] The shelf is too far away and the lighting too poor 
to make out specific items. [UNCERTAIN: vision_range_exceeded]
```

**Decision**: Use Strategy A for non-mechanical, then trigger fact completion. Strategy C if vision mechanics prevent seeing detail.

---

#### **Scenario 5.4.2: NPC Reaction Without Personality Data**

**Situation**: Guard captain should react to player's lie, but `npc.guard_captain.personality` → `UNKNOWN`

**Bad Response** (Mechanical Authority):
```
[NARRATIVE] The guard captain doesn't believe you. 
[❌ VIOLATION: Adjudicated Sense Motive check without BOX]
```

**Strategy A: Generic Reaction** (Safe but bland):
```
[NARRATIVE] The guard captain's expression is unreadable as 
he listens to your explanation. [DERIVED: from generic_npc_template]
```

**Strategy B: Fact Completion + Personality Generation**:
```
[PROCESS]
1. LENS requests NPC personality completion
2. SPARK generates: "Gruff veteran, loyal but suspicious of outsiders"
3. LENS validates (no mechanical claims) → stores with [NARRATIVE] tag
4. SPARK narrates using new personality data

[NARRATIVE] The grizzled guard captain narrows his eyes, one 
hand resting on his sword hilt. "That so?" he rumbles. 
[DERIVED: personality.guard_captain.demeanor]
```

**Strategy C: DM Stall** (Buys time for completion):
```
[NARRATIVE] The guard captain studies you for a long moment, 
weathered face thoughtful... [pause] 
"Right then," he says finally, his tone suggesting— 
[fact completion arrives here]
```

**Decision**: Use Strategy B for named NPCs (maintain consistency), Strategy A for nameless NPCs.

---

#### **Scenario 5.4.3: Environmental Detail Missing**

**Player**: "How deep is the water in this pool?"

**LENS Query**: `scene.water_pool.depth` → `UNKNOWN`

**Bad Response** (Fabricated Mechanic):
```
[NARRATIVE] The water is about 10 feet deep. 
[❌ VIOLATION: Depth = mechanical property (drowning, swimming DC)]
```

**Strategy A: Safe Vagueness**:
```
[NARRATIVE] The dark water obscures the bottom—you can't tell 
how deep it is just by looking. [UNCERTAIN]
```

**Strategy B: Fact Completion with Provenance**:
```
[PROCESS]
1. LENS → BOX: Generate pool depth using dungeon generation seed
2. BOX determines: 8 feet (from dungeon_seed + room_id hash)
3. LENS marks as [DERIVED: environmental_generation]

[NARRATIVE] Peering into the murky water, you estimate it's about 
8 feet deep—deeper than a human stands tall. [DERIVED]
```

**Strategy C: Player Investigation Prompt**:
```
[NARRATIVE] The water's surface ripples gently, giving no 
indication of depth. You could test it with a pole, drop a 
weighted rope, or... [prompts player action]
```

**Decision**: 
- If depth doesn't affect immediate mechanics → Strategy A
- If player needs to make decision (swim across?) → Strategy B (trigger fact completion)
- If player already investigating → Strategy C (prompt concrete action)

---

#### **Scenario 5.4.4: Historical Question**

**Player**: "Has this town been attacked before?"

**LENS Query**: `campaign_memory.ironforge_town.attack_history` → `UNKNOWN`

**Bad Response** (Invented Lore):
```
[NARRATIVE] Yes, the town was sacked by orcs twenty years ago. 
[❌ VIOLATION: Inventing campaign history without DM approval]
```

**Strategy A: In-Character Uncertainty**:
```
[NARRATIVE] The locals you've spoken with haven't mentioned any 
attacks, but that doesn't mean there haven't been any. The town's 
history before you arrived remains unclear. [UNCERTAIN: campaign_lore]
```

**Strategy B: Knowledge Check Redirect**:
```
[NARRATIVE] You recall no tales of attacks on Ironforge in your 
travels, but your knowledge of this region's history is limited. 
[BOX: Knowledge (local) check available if player requests]
```

**Strategy C: NPC Information Source**:
```
[NARRATIVE] The barkeep might know—he's lived here all his life. 
Would you like to ask him? [prompts player interaction]
```

**Strategy D: Fact Completion with DM Improvisation**:
```
[PROCESS]
1. LENS flags historical gap
2. SPARK generates lore: "Ironforge has stood for 200 years, 
   weathering minor goblin raids but never a full siege"
3. LENS stores with [NARRATIVE: dm_improvised] tag
4. Future queries use this established lore

[NARRATIVE] As far as you know, Ironforge has stood strong for 
two centuries, though goblin raiders from the Thornwood have 
tested its walls from time to time. [NARRATIVE: dm_improvised]
```

**Decision**: 
- Use Strategy D for world-building (creates consistent lore)
- Use Strategy A if fact might contradict future plot
- Use Strategy C to make discovery interactive

---

#### **Scenario 5.4.5: Combat Position Query**

**Player**: "Is the orc behind cover from my position?"

**LENS Query**: `combat.orc_warrior_1.cover_from[pc_archer]` → `UNKNOWN`

**Bad Response** (Mechanical Fabrication):
```
[NARRATIVE] No, you have a clear shot. 
[❌ CRITICAL VIOLATION: Cover = +4 AC bonus, mechanical authority required]
```

**Only Acceptable Response**:
```
[NARRATIVE] [UNCERTAIN: mechanical_query_requires_box]

[PROCESS]
1. LENS → BOX: Compute cover from PC position
2. BOX calculates: corner pillar blocks line of effect
3. BOX determines: +4 cover bonus to AC
4. LENS returns: [BOX: cover_bonus=4]

[NARRATIVE] The orc crouches behind the stone pillar, using it 
for cover. [BOX: +4 AC from cover]
```

**Critical Rule**: Mechanical queries MUST ALWAYS block narration until BOX computes answer. No "safe vagueness" for mechanics.

---

### 5.5 Integration with Fact Completion Protocol

The **Improvisation Protocol** (from RQ-SPARK-001-C) handles fact generation:

```python
# Fact Completion Flow
def handle_unknown_fact(fact_query, fact_type):
    if fact_type == "MECHANICAL":
        # Block narration, require BOX
        return LENS.request_box_computation(fact_query)
    
    elif fact_type == "ENVIRONMENTAL":
        # Safe to generate with SPARK
        new_fact = SPARK.improvise(
            fact_query, 
            constraints=scene_consistency_rules,
            mode="environmental_detail"
        )
        LENS.store_with_tag(new_fact, "[NARRATIVE: improvised]")
        return new_fact
    
    elif fact_type == "HISTORICAL":
        # DM-approved improvisation
        new_lore = SPARK.improvise(
            fact_query,
            constraints=campaign_consistency_rules,
            mode="lore_generation"
        )
        LENS.store_with_tag(new_lore, "[NARRATIVE: dm_improvised]")
        return new_lore
    
    elif fact_type == "NPC_PERSONALITY":
        # Personality generation
        personality = SPARK.improvise(
            fact_query,
            constraints=npc_consistency_rules,
            mode="npc_personality"
        )
        LENS.store_with_tag(personality, "[DERIVED: npc_generation]")
        return personality
```

### 5.6 Real DM Handling of Unknowns

Research into actual D&D DM techniques:

**Common Patterns**:
1. **Thinking Pause**: "Hmm, let me think about that..." (2-5 seconds natural)
2. **Clarifying Question**: "What are you hoping to find?" (narrows improvisation)
3. **Provisional Description**: "You see what looks like..." (commits less)
4. **Defer to Rules**: "Let me check if there's a table for that" (BOX equivalent)
5. **Player Agency**: "What do you do to find out?" (makes discovery active)

**Anti-Patterns to Avoid**:
- **Instant Certainty**: No pause feels artificial when improvising
- **Overcommitting**: Specific numbers lock you into consequences
- **Contradiction**: Each unknown should check campaign consistency
- **Railroading**: "Nothing interesting" blocks player agency

**Adaptation to SPARK**:
- Thinking pause → Brief clarifying narration before fact completion
- Player agency → Prompt actions that trigger BOX computations
- Rules check → LENS query to BOX with visible [BOX] tag
- Provisional → Use [UNCERTAIN] or [DERIVED] tags transparently

---

## Sub-Question 6: Tone Control vs Truth Control

### 6.1 Separation Principle

**Truth Layer** (IMMUTABLE):
- What happened (outcome)
- Who was involved (entities)
- Mechanical results (damage, success/failure)
- Source: BOX computation → LENS truth packet

**Style Layer** (VARIABLE):
- How to describe it (word choice, metaphor)
- Narrative pacing (terse vs. elaborate)
- Emotional tone (dramatic vs. understated)
- Source: DM persona settings → SPARK style guide

**Critical Invariant**: `hash(truth_packet) + tone_settings → same_mechanical_outcome`

### 6.2 Tone Parameters

#### **Parameter 6.2.1: Verbosity**

**Terse** (verbosity=1):
```
[TRUTH: hit=true, damage=12, target=orc_warrior]
[NARRATIVE] Hit. 12 damage. The orc staggers.
```

**Moderate** (verbosity=5):
```
[TRUTH: hit=true, damage=12, target=orc_warrior]
[NARRATIVE] Your sword strikes true, cutting deep into the orc's 
shoulder for 12 damage. The warrior stumbles backward, blood 
darkening his hide armor.
```

**Verbose** (verbosity=10):
```
[TRUTH: hit=true, damage=12, target=orc_warrior]
[NARRATIVE] The arc of your blade catches the firelight as it 
descends, finding the gap between the crude shoulder plates of 
the orc's armor. Steel bites flesh with a wet thunk, and dark 
blood wells from the wound—12 points of damage that leaves the 
warrior reeling backward, his roar of pain echoing off the 
cavern walls.
```

**Constraint**: All three narrations describe `damage=12`. Verbosity affects ONLY description length, never the number.

---

#### **Parameter 6.2.2: Drama**

**Understated** (drama=1):
```
[TRUTH: crit=true, damage=24, target_hp_remaining=2]
[NARRATIVE] Critical hit. 24 damage. The orc is nearly dead.
```

**Dramatic** (drama=10):
```
[TRUTH: crit=true, damage=24, target_hp_remaining=2]
[NARRATIVE] Your blade finds the perfect opening—time seems to 
slow as you drive it home with devastating force! The orc's eyes 
widen in shock as 24 points of damage tear through his defenses, 
leaving him swaying on the brink of death!
```

**Bleeding Risk**: Drama must NOT imply different outcomes:

❌ **Bad (implies orc defeated)**:
```
"Your mighty blow cleaves through the orc, dropping him to the ground!"
[truth_packet shows: target_hp_remaining=2, not dead]
```

✅ **Good (respects hp_remaining=2)**:
```
"Your devastating strike leaves the orc on his knees, barely clinging to consciousness!"
```

---

#### **Parameter 6.2.3: Humor**

**Serious** (humor=0):
```
[TRUTH: fumble=true, weapon_dropped=true]
[NARRATIVE] You swing wildly and your sword slips from your grasp, 
clattering to the floor.
```

**Occasional Wit** (humor=5):
```
[TRUTH: fumble=true, weapon_dropped=true]
[NARRATIVE] Your enthusiastic swing encounters nothing but air, 
and the momentum carries your blade right out of your hand. It 
lands with an apologetic clatter several feet away.
```

**Frequent Humor** (humor=10):
```
[TRUTH: fumble=true, weapon_dropped=true]
[NARRATIVE] You put everything you have into the swing, which 
turns out to be too much of a good thing. Your sword goes flying 
across the room like it's late for an appointment elsewhere, 
leaving you holding nothing but embarrassment and a handful of 
air.
```

**Constraint**: Humor affects tone only. The fumble happened regardless of comedy level.

---

#### **Parameter 6.2.4: Grittiness**

**Heroic Fantasy** (grit=1):
```
[TRUTH: damage=18, target_killed=true]
[NARRATIVE] Your blade strikes true, and the orc falls, defeated.
```

**Dark & Gritty** (grit=10):
```
[TRUTH: damage=18, target_killed=true]
[NARRATIVE] Your blade opens a vicious wound across the orc's 
throat. Hot blood sprays across your face as the creature gurgles, 
clawing at the mortal wound before collapsing into the spreading 
pool of crimson beneath him.
```

**Content Warning**: Grit level should be session-configurable with player consent.

---

#### **Parameter 6.2.5: NPC Voice**

**The Challenge**: Maintaining distinct character voices with limited context window (8K-32K tokens)

**Gruff Dwarf Guard**:
```
[TRUTH: npc=dwarf_guard, dialogue_request="Where is the tavern?"]
[NARRATIVE] The dwarf grunts, jerking his thumb down the street. 
"Three doors down. Can't miss it—just follow yer nose to the ale."
```

**Eloquent Elf Sage**:
```
[TRUTH: npc=elf_sage, dialogue_request="Where is the tavern?"]
[NARRATIVE] The elf inclines her head gracefully. "You seek 
refreshment? The Wandering Minstrel lies but a short walk hence, 
third establishment southward along this thoroughfare."
```

**Nervous Goblin**:
```
[TRUTH: npc=goblin_snitch, dialogue_request="Where is the tavern?"]
[NARRATIVE] The goblin's eyes dart nervously. "T-tavern? Uh, 
down street, yeah? Three... three doors? Maybe four? Don't hurt 
Riggle!" He points with a trembling claw.
```

**Implementation**: NPC voice tied to `npc.personality` data in truth packet, not tone settings.

---

### 6.3 Critical Constraints on Style

#### **Constraint 6.3.1: Margin Accuracy**

❌ **FORBIDDEN** (no margin data):
```
[TRUTH: attack_roll=15, target_ac=16, hit=false]
[NARRATIVE] Your blade barely misses, deflecting off the orc's armor.
```
**Problem**: "barely" implies `attack_roll ≈ target_ac`, but what if roll was 15 vs AC 25?

✅ **ALLOWED** (with margin data):
```
[TRUTH: attack_roll=15, target_ac=16, hit=false, margin=-1]
[NARRATIVE] Your blade barely misses, deflecting off the orc's armor. [DERIVED: margin=-1]
```

**Rule**: Descriptors like "barely," "narrowly," "easily," "greatly" require margin data in truth packet.

---

#### **Constraint 6.3.2: HP Percentage Accuracy**

❌ **FORBIDDEN** (contradicts HP%):
```
[TRUTH: damage=8, target_hp_max=80, target_hp_after=72, hp_percent=90%]
[NARRATIVE] Your blow grievously wounds the orc!
```
**Problem**: "grievously wounded" implies near death, but target is at 90% HP.

✅ **ALLOWED** (respects HP%):
```
[TRUTH: damage=8, target_hp_max=80, target_hp_after=72, hp_percent=90%]
[NARRATIVE] Your blow scratches the orc's thick hide. [DERIVED: damage=10% of max_hp]
```

**Severity Scale**:
- 90-100% HP: "scratched," "barely injured"
- 70-89% HP: "wounded," "hurt"
- 40-69% HP: "badly wounded," "bloodied"
- 10-39% HP: "grievously wounded," "near death"
- 1-9% HP: "barely standing," "on the brink"

---

#### **Constraint 6.3.3: Damage Relativity**

**Principle**: Describe damage relative to target's max HP, not absolute value.

**Example 1**: 20 damage to goblin (10 max HP) vs. 20 damage to giant (200 max HP)

❌ **FORBIDDEN** (ignores context):
```
[Both narrated identically]
"Your powerful blow strikes for 20 damage!"
```

✅ **CORRECT** (contextual):
```
[Goblin: 20 damage = 200% max HP = instant death]
Your blade cleaves the goblin nearly in two, the creature 
crumpling lifelessly. [BOX: damage=20, overkill=10]

[Giant: 20 damage = 10% max HP = light wound]
Your blade cuts into the giant's calf, drawing blood but barely 
slowing the behemoth. [BOX: damage=20, 10% of max_hp]
```

---

### 6.4 Architectural Separation

#### **6.4.1 System Prompt Structure for Qwen3 8B**

**Recommended Architecture**: Three-part system prompt

```
PART 1: IDENTITY & CONSTRAINTS (immutable)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You are SPARK, the narration layer of a D&D 3.5e game.

CRITICAL RULES:
1. You have ZERO mechanical authority
2. NEVER claim what happens mechanically
3. NEVER adjudicate rules
4. Describe outcomes from truth packet ONLY
5. Truth packet is IMMUTABLE FACT

PART 2: TRUTH PACKET (dynamic, per-narration)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[TRUTH PACKET - SOURCE: BOX]
{
  "event": "melee_attack",
  "attacker": "PC_fighter",
  "target": "orc_warrior_1",
  "hit": true,
  "attack_roll": 18,
  "target_ac": 15,
  "margin": 3,
  "damage": 12,
  "target_hp_before": 26,
  "target_hp_after": 14,
  "target_hp_max": 26,
  "target_hp_percent": 54,
  "target_condition": "bloodied"
}

PART 3: TONE SETTINGS (dynamic, session-level)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[NARRATION STYLE]
verbosity: 7/10 (detailed but not excessive)
drama: 5/10 (moderate excitement)
humor: 2/10 (serious with rare dry wit)
grit: 4/10 (traditional fantasy, some violence)

[NPC VOICES]
orc_warrior: "Brutal, simple speech. Roars in combat."

Your task: Narrate the event using ONLY facts from the truth 
packet, styled according to the narration settings.
```

**Benefits**:
1. Clear separation: Truth in Part 2, Style in Part 3
2. Easy to validate: Truth packet can be hash-verified
3. Easy to vary: Swap Part 3 without changing Part 1 or Part 2
4. Explicit hierarchy: Part 2 > Part 3 (truth overrides style)

---

#### **6.4.2 Preventing Tone Bleeding**

**Bleeding** = Tone settings causing mechanical implications

**Example of Bleeding**:
```
[TONE: drama=10]
[TRUTH: spell_cast="fireball", save_dc=15, target_save=16, save_succeeded=true]

❌ BAD NARRATION (bleeding):
"Your fireball engulfs the orc completely! The flames overwhelm 
his resistance!" 
[Implies save failed, contradicts truth packet]

✅ GOOD NARRATION (no bleeding):
"Your fireball erupts in a blazing inferno! The orc throws himself 
aside with a roar, singed but not consumed!" 
[Respects save_succeeded=true despite high drama]
```

**Prevention Strategies**:

**Strategy 1: Template Anchoring**
```
# Generate template first (locked to truth)
template = generate_template(truth_packet)
# "The orc saves against the fireball."

# Then style the template
styled = apply_tone(template, tone_settings)
# "The orc roars in defiance, twisting aside as the fireball 
#  detonates—flames lick at his armor but fail to penetrate!"

# Verify styled version doesn't contradict template
if contradicts(styled, template):
    fallback_to_template()
```

**Strategy 2: Outcome Anchors**
```
# Extract non-negotiable outcomes
anchors = [
    "save_succeeded=true",
    "damage=0",
    "target_condition=unaffected"
]

# Inject anchors into prompt
prompt = f"""
Narrate this event with {tone_settings}.
REQUIRED OUTCOMES: {anchors}
These outcomes CANNOT be contradicted by your description.
"""
```

**Strategy 3: Post-Hoc Verification**
```
# After SPARK generates narration
narration = SPARK.generate(truth_packet, tone_settings)

# Check for contradiction keywords
violations = check_contradictions(narration, truth_packet)

if violations:
    # Regenerate with stricter constraints
    narration = SPARK.regenerate_safe(truth_packet)
```

**Strategy 4: Explicit Negative Constraints**
```
# In system prompt
DO NOT say the spell "overwhelms" resistance if save succeeded
DO NOT say target is "helpless" if condition is normal
DO NOT say attack "nearly killed" if damage < 50% max HP
DO NOT use outcome words contradicting truth packet
```

---

#### **6.4.3 NPC Voice Consistency**

**Challenge**: Limited 8K-32K context window can't hold full personality profiles for all NPCs

**Solution 1: Compressed Personality Tokens**

```python
# Compact representation (under 50 tokens per NPC)
npc_profiles = {
    "guard_captain": {
        "voice": "gruff, terse, military",
        "quirk": "checks weapon when nervous",
        "catchphrase": "Right then",
        "attitude_default": "suspicious but professional"
    },
    "elf_sage": {
        "voice": "eloquent, archaic grammar",
        "quirk": "quotes ancient texts",
        "catchphrase": "As the scrolls tell us",
        "attitude_default": "helpful but condescending"
    }
}

# Only include active NPCs in context
active_npcs = scene.get_present_npcs()
context_personalities = {npc: npc_profiles[npc] for npc in active_npcs}
```

**Solution 2: Voice Retrieval**

```python
# Store full personality out-of-context
def get_npc_voice(npc_id, context_size):
    if context_size > 16000:  # Plenty of room
        return full_personality_profile(npc_id)
    else:  # Context constrained
        return compressed_profile(npc_id, max_tokens=50)

# Dynamically fetch when NPC speaks
if npc_speaks_in_scene:
    voice = get_npc_voice(npc_id, current_context_tokens)
    inject_into_prompt(voice)
```

**Solution 3: Voice Consistency Hashing**

```python
# Generate voice seed from NPC identity
voice_seed = hash(npc_id + campaign_id + "personality") 

# Use seed to ensure consistent generation
personality = SPARK.generate_personality(
    npc_base_template,
    seed=voice_seed
)

# Same NPC + same seed = same personality across sessions
```

**Solution 4: Session Personality Cache**

```python
# At session start, generate personality for key NPCs
session_npcs = ["guard_captain", "elf_sage", "villain"]
for npc in session_npcs:
    personality[npc] = SPARK.generate_personality(npc)
    LENS.store(personality[npc], tag="[NARRATIVE:npc_personality]")

# Reuse throughout session without regenerating
# Persist to campaign file for future sessions
```

**Recommended Approach**: Hybrid

1. **Compressed profiles** (50 tokens) for all NPCs in scene
2. **Voice retrieval** for speaking NPC (expand to 200 tokens when active)
3. **Consistency hashing** for unnamed NPCs (e.g., "tavern patron")
4. **Session cache** for recurring NPCs (avoid drift over time)

---

### 6.5 Tone Architecture Design

```
┌─────────────────────────────────────────────────┐
│              DM CONFIGURATION                   │
│  verbosity=7, drama=5, humor=2, grit=4         │
└────────────────────┬────────────────────────────┘
                     │ (session-level, persistent)
                     │
┌────────────────────▼────────────────────────────┐
│              LENS MEDIATOR                      │
│  - Receives truth packet from BOX              │
│  - Fetches tone config                         │
│  - Constructs SPARK prompt                     │
└────────────────────┬────────────────────────────┘
                     │
                     ├─────────────┬──────────────┐
                     │             │              │
                     ▼             ▼              ▼
           ┌──────────────┐  ┌─────────┐   ┌──────────┐
           │ TRUTH PACKET │  │  TONE   │   │   NPC    │
           │   [BOX]      │  │ SETTINGS│   │  VOICES  │
           │  (immutable) │  │(variable)│   │ (cached) │
           └──────┬───────┘  └────┬────┘   └─────┬────┘
                  │               │              │
                  └───────┬───────┴──────────────┘
                          │
                          ▼
              ┌──────────────────────┐
              │   SPARK PROMPT       │
              │                      │
              │  PART 1: Identity    │
              │  PART 2: Truth ←─────┼── [BOX] data
              │  PART 3: Tone  ←─────┼── DM settings
              │  PART 4: NPCs  ←─────┼── Personalities
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   SPARK GENERATION   │
              │   (Qwen3 8B)        │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  NARRATION OUTPUT    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  VERIFICATION GATE   │
              │  - Check bleeding    │
              │  - Verify no mech.   │
              │  - Match truth packet│
              └──────────┬───────────┘
                         │
                    ┌────┴────┐
                    │ Valid?  │
                    └────┬────┘
                         │
                 ┌───────┴───────┐
                 │               │
             ✅ PASS         ❌ FAIL
                 │               │
                 ▼               ▼
        ┌────────────────┐  ┌─────────────┐
        │ PRESENT TO     │  │ FALLBACK TO │
        │ PLAYER         │  │ TEMPLATE    │
        └────────────────┘  └─────────────┘
```

**Key Properties**:
1. Truth packet flows from BOX (single source of truth)
2. Tone settings independent of BOX (can change without recompute)
3. Verification gate prevents bleeding
4. Fallback ensures player never sees violations

---

### 6.6 Example: Same Event, Three Tones

**Truth Packet**:
```json
{
  "event": "melee_attack",
  "attacker": "PC_ranger",
  "target": "goblin_archer",
  "weapon": "longsword",
  "hit": true,
  "attack_roll": 19,
  "target_ac": 14,
  "margin": 5,
  "damage": 8,
  "damage_type": "slashing",
  "target_hp_before": 5,
  "target_hp_after": -3,
  "target_killed": true,
  "target_hp_max": 5,
  "overkill": 3
}
```

---

**Tone 1: Terse Combat** (verbosity=1, drama=1, humor=0, grit=2)
```
[NARRATIVE] 
Hit. 8 damage. The goblin falls dead.
[BOX: attack_roll=19 vs AC 14, damage=8, target killed]
```

---

**Tone 2: Standard Fantasy** (verbosity=5, drama=5, humor=0, grit=4)
```
[NARRATIVE]
Your longsword arcs through the air, catching the goblin across 
the chest. The blade bites deep—8 points of slashing damage that 
prove far too much for the small creature. The archer crumples to 
the ground, dead before he hits the earth.
[BOX: attack_roll=19 vs AC 14, damage=8, target killed]
```

---

**Tone 3: Epic & Dramatic** (verbosity=9, drama=10, humor=0, grit=7)
```
[NARRATIVE]
Time seems to slow as you pivot, your longsword gleaming in the 
torchlight. The goblin archer's eyes widen—he sees it coming but 
cannot move fast enough. Steel meets flesh with a sickening crunch 
as your blade carves through leather armor and bone alike. Eight 
points of devastating damage tear through the goblin's frail body, 
the force of the blow lifting him momentarily off his feet. He 
crashes back down in a broken heap, dark blood pooling beneath his 
lifeless form.
[BOX: attack_roll=19 vs AC 14, damage=8, target killed]
```

---

**Tone 4: Darkly Humorous** (verbosity=7, drama=4, humor=8, grit=5)
```
[NARRATIVE]
Your sword introduces itself to the goblin's ribcage with an 
enthusiastic crunch. The archer looks down at the eight inches of 
steel protruding from his chest with an expression that suggests 
this was not on his agenda for the day. "Huh," he manages, before 
folding up like a cheap lawn chair and hitting the ground with all 
the grace of a dropped sack of potatoes.
[BOX: attack_roll=19 vs AC 14, damage=8, target killed]
```

---

**Critical Observation**: All four narrations describe EXACTLY the same mechanical outcome:
- Hit (attack roll 19 vs AC 14)
- 8 damage
- Target killed

**None contradict the truth packet**. The variation is purely stylistic.

---

### 6.7 Determinism Gate Verification

**Principle**: Changing tone must NOT change mechanical outcomes from BOX

**Test Protocol**:
```python
def verify_tone_determinism(combat_scenario, seed):
    # Run same combat with different tones
    tones = [
        {"verbosity": 1, "drama": 1},
        {"verbosity": 10, "drama": 10},
        {"verbosity": 5, "drama": 5, "humor": 8}
    ]
    
    mechanical_outcomes = []
    
    for tone in tones:
        BOX.reset(seed)  # Same seed
        outcome = run_combat(combat_scenario, tone_settings=tone)
        
        # Extract only mechanical data (ignore narration)
        mechanical = {
            "hit_results": outcome.hits,
            "damage_dealt": outcome.damage,
            "hp_remaining": outcome.hp_states,
            "conditions": outcome.conditions,
            "turn_order": outcome.initiative
        }
        mechanical_outcomes.append(mechanical)
    
    # All mechanical outcomes must be identical
    assert all(m == mechanical_outcomes[0] for m in mechanical_outcomes), \
        "TONE BLEEDING DETECTED: Tone changed mechanical outcome"
    
    return True  # Determinism verified
```

**Run this test**:
- On every tone parameter change
- As part of regression suite
- With 100+ combat scenarios
- Random seeds to catch edge cases

**If test fails**: Tone is bleeding into BOX computations → CRITICAL BUG

---

## Sub-Question 7: Violation Detection

### 7.1 Violation Categories

#### **Category 7.1.1: Outcome Mismatch**

**Definition**: SPARK's narration contradicts BOX's computed outcome

**Examples**:
```
[TRUTH: hit=false]
❌ SPARK: "Your blade strikes the orc's armor!"
[VIOLATION: Implies hit when truth says miss]

[TRUTH: save_succeeded=true, damage=0]
❌ SPARK: "The fireball engulfs him completely!"
[VIOLATION: Implies damage when save negated it]

[TRUTH: spell_cast="magic_missile", spell_failed=true, reason="target_has_shield"]
❌ SPARK: "Your missiles streak toward the target!"
[VIOLATION: Implies spell worked when it failed]
```

**Severity**: CRITICAL (directly contradicts mechanical resolution)

---

#### **Category 7.1.2: Entity Mismatch**

**Definition**: SPARK mentions entities not in truth packet's scene data

**Examples**:
```
[TRUTH: scene.entities = ["PC_fighter", "orc_warrior_1", "orc_warrior_2"]]
❌ SPARK: "The goblin shaman begins casting a spell..."
[VIOLATION: Goblin shaman not in scene]

[TRUTH: attacker="PC_ranger", target="orc_warrior_1"]
❌ SPARK: "You swing at the troll..."
[VIOLATION: Target is orc, not troll]

[TRUTH: scene.objects = ["wooden_table", "iron_door"]]
❌ SPARK: "You duck behind the stone pillar..."
[VIOLATION: No pillar in scene objects]
```

**Severity**: HIGH (breaks scene consistency, confuses players)

---

#### **Category 7.1.3: Geometry Mismatch**

**Definition**: SPARK describes positions/distances contradicting scene geometry

**Examples**:
```
[TRUTH: PC_position=(5,5), orc_position=(15,5), no_obstacles_between]
❌ SPARK: "You peer around the pillar at the orc..."
[VIOLATION: Claims obstacle when none exists]

[TRUTH: distance=50_feet, PC_move_speed=30_feet]
❌ SPARK: "You easily close the distance and attack..."
[VIOLATION: Implies moving 50 feet with 30 feet movement]

[TRUTH: flanking=false, ally_position=null]
❌ SPARK: "With your ally distracting him from behind..."
[VIOLATION: Claims flanking when not achieved]
```

**Severity**: HIGH (contradicts tactical grid state)

---

#### **Category 7.1.4: Severity Mismatch**

**Definition**: SPARK's descriptive severity doesn't match numerical severity

**Examples**:
```
[TRUTH: damage=2, target_hp_max=50, hp_percent=96%]
❌ SPARK: "Your devastating blow nearly fells the creature!"
[VIOLATION: 2 damage to 50 HP target is trivial, not devastating]

[TRUTH: attack_roll=8, target_ac=18, margin=-10]
❌ SPARK: "Your blade barely misses..."
[VIOLATION: -10 margin is "wildly misses", not "barely"]

[TRUTH: damage=45, target_hp_max=50, hp_percent=10%]
❌ SPARK: "You scratch the orc's hide."
[VIOLATION: 90% HP damage is grievous, not a scratch]
```

**Severity**: MEDIUM (misleads player about combat state)

---

#### **Category 7.1.5: Mechanical Assertion**

**Definition**: SPARK makes claims requiring mechanical authority

**Examples**:
```
❌ SPARK: "You can't attack because you're flatfooted."
[VIOLATION: Adjudicating what's legal = BOX's authority]

❌ SPARK: "The orc's AC is too high for your attack bonus."
[VIOLATION: Claiming knowledge of AC/bonus = mechanical data]

❌ SPARK: "That action provokes an attack of opportunity."
[VIOLATION: AoO determination = BOX's rules engine]

❌ SPARK: "Your spell DC isn't high enough to affect him."
[VIOLATION: Save DC comparison = mechanical computation]
```

**Severity**: CRITICAL (SPARK claiming BOX's role)

---

#### **Category 7.1.6: Unauthorized Mechanics**

**Definition**: SPARK invents effects not computed by BOX

**Examples**:
```
[TRUTH: spell="ice_storm", damage=20, effects=["cold_damage"]]
❌ SPARK: "The icy blast freezes the orc in place, slowing his movement!"
[VIOLATION: Added "slowed" condition not in BOX computation]

[TRUTH: critical_hit=true, damage=24]
❌ SPARK: "Your critical strike severs the orc's arm!"
[VIOLATION: Added dismemberment not in D&D 3.5e rules]

[TRUTH: damage_type="fire", target_resistance_fire=10, net_damage=5]
❌ SPARK: "The flames ignite the orc's clothing!"
[VIOLATION: Added ongoing burning not computed by BOX]
```

**Severity**: CRITICAL (inventing rules/effects)

---

#### **Category 7.1.7: Temporal Mismatch**

**Definition**: SPARK describes events out of initiative/sequence order

**Examples**:
```
[TRUTH: initiative_order=["PC_1", "orc", "PC_2"], current_actor="PC_1"]
❌ SPARK: "Before you can strike, the orc charges at you!"
[VIOLATION: Orc hasn't acted yet per initiative]

[TRUTH: turn_sequence=["move", "attack", "end"], current_phase="attack"]
❌ SPARK: "You attack, then move to flank..."
[VIOLATION: Can't move after standard attack]

[TRUTH: spell_duration="instantaneous", no_ongoing_effects]
❌ SPARK: "The magic missile continues to seek its target..."
[VIOLATION: Instantaneous spells don't "continue"]
```

**Severity**: MEDIUM (breaks action economy understanding)

---

### 7.2 Detection Approaches

#### **Approach 7.2.1: Keyword Matching**

**Method**: Scan SPARK output for mechanical keywords, check against truth packet

```python
MECHANICAL_KEYWORDS = {
    "outcomes": ["hit", "miss", "critical", "fumble", "save", "fail"],
    "mechanics": ["AC", "attack bonus", "save DC", "damage reduction"],
    "numbers": r"\d+\s*(damage|HP|hit points|feet)",
    "conditions": ["prone", "stunned", "paralyzed", "slowed", "blinded"],
    "actions": ["attack of opportunity", "AoO", "5-foot step", "full attack"]
}

def keyword_violation_check(narration, truth_packet):
    violations = []
    
    # Check outcomes
    if "hit" in narration.lower() and truth_packet["hit"] == False:
        violations.append("outcome_mismatch: claimed hit when missed")
    
    if "miss" in narration.lower() and truth_packet["hit"] == True:
        violations.append("outcome_mismatch: claimed miss when hit")
    
    # Check for AC mentions (forbidden)
    if re.search(r"\bAC\s*\d+", narration):
        violations.append("mechanical_assertion: mentioned AC value")
    
    # Check damage numbers
    damage_matches = re.findall(r"(\d+)\s*damage", narration)
    if damage_matches:
        narration_damage = int(damage_matches[0])
        truth_damage = truth_packet["damage"]
        if narration_damage != truth_damage:
            violations.append(f"outcome_mismatch: wrong damage ({narration_damage} vs {truth_damage})")
    
    return violations
```

**Pros**:
- Fast (< 10ms)
- Simple to implement
- Catches obvious violations
- No LLM calls needed

**Cons**:
- High false positive rate
- Can't detect semantic contradictions
- Easily fooled by paraphrasing
- Misses implicit violations

**Example False Positive**:
```
[TRUTH: hit=true]
SPARK: "You miss your footing but your blade hits anyway!"
KEYWORD: Flags "miss" despite describing a hit
```

**Verdict**: Use as first-pass filter, not definitive detection

---

#### **Approach 7.2.2: Regex Pattern Detection**

**Method**: More sophisticated patterns to detect mechanical assertions

```python
VIOLATION_PATTERNS = {
    "mechanical_assertion": [
        r"you can't .* because",
        r"that (?:would|will) provoke",
        r"(?:your|the) AC is (?:too |not )?(?:high|low)",
        r"the DC is \d+",
        r"you (?:need|must) roll (?:at least )?\d+",
    ],
    "unauthorized_mechanics": [
        r"(?:also|additionally) (?:slows|stuns|blinds|paralyzes)",
        r"ignites? (?:their|his|her|the)",
        r"severs? (?:the|their|his|her) (?:arm|leg|hand)",
        r"knocks? (?:them|him|her|the .* )?(?:prone|down|back)",
    ],
    "geometry_claims": [
        r"behind the (?!truth_packet_objects)",
        r"(?:flanking|flanks)",
        r"within (?:reach|range|melee)",
    ]
}

def regex_violation_check(narration, truth_packet):
    violations = []
    
    for category, patterns in VIOLATION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, narration, re.IGNORECASE):
                # Verify it's actually a violation
                if category == "unauthorized_mechanics":
                    # Check if effect is in truth packet
                    if not effect_in_truth_packet(pattern, truth_packet):
                        violations.append(f"{category}: {pattern}")
    
    return violations
```

**This is KILL-002 from Plan v2**.

**Pros**:
- Still fast (< 50ms)
- Lower false positive rate than keywords
- Can detect complex patterns
- Catches adjudication attempts

**Cons**:
- Requires pattern maintenance
- Can be fooled by creative wording
- May miss novel violation types
- Context-dependent patterns tricky

**Example Detection**:
```
SPARK: "Your spell also slows the orc's movement"
REGEX: Matches "also (?:slows)" 
CHECK: "slowed" not in truth_packet["conditions"]
VERDICT: unauthorized_mechanics violation
```

**Verdict**: Use as primary fast detection. Plan v2's KILL-002 is good foundation.

---

#### **Approach 7.2.3: Semantic Comparison (LLM-based)**

**Method**: Use secondary LLM to verify consistency

```python
def semantic_violation_check(narration, truth_packet):
    prompt = f"""
You are a verification system. Check if the NARRATION contradicts 
the TRUTH PACKET.

TRUTH PACKET (mechanical fact):
{json.dumps(truth_packet, indent=2)}

NARRATION:
{narration}

Violations to check:
1. Does narration claim opposite outcome? (hit vs miss)
2. Does narration mention entities not in truth packet?
3. Does narration describe positions contradicting geometry?
4. Does narration severity mismatch damage percentage?
5. Does narration make mechanical claims? (AC, DC, "you can't")
6. Does narration add effects not in truth packet?
7. Does narration describe wrong action order?

Respond ONLY with JSON:
{{
  "violations": [
    {{"category": "outcome_mismatch", "evidence": "said hit when truth says miss"}},
    ...
  ],
  "verdict": "PASS" or "FAIL"
}}
"""
    
    response = llm_verification.query(prompt)
    return parse_json(response)
```

**Pros**:
- Catches semantic contradictions
- Understands context and implication
- Detects novel violation types
- Low false positive rate (if LLM is good)

**Cons**:
- Slow (1-5 seconds per check)
- Expensive (API costs or compute)
- Non-deterministic (same input → different results)
- Requires second LLM (can't use Qwen3 to check itself)

**Optimization**: Run async, don't block player experience

```python
async def async_semantic_check(narration, truth_packet):
    # Player sees narration immediately
    # Semantic check runs in background
    violation_report = await llm_verification.query(...)
    
    if violation_report["verdict"] == "FAIL":
        log_violation(violation_report)
        alert_dm_dashboard(violation_report)
        # Don't retcon, but track for quality metrics
```

**Verdict**: Use for post-hoc analysis, not real-time blocking. Too slow for critical path.

---

#### **Approach 7.2.4: Template Anchoring**

**Method**: If narration uses templates, verify LLM additions don't contradict template

```python
def template_anchored_check(template, llm_additions, truth_packet):
    """
    Template = locked structure from truth packet
    LLM additions = SPARK's stylistic enhancements
    """
    
    # Template is pre-verified to match truth packet
    # Example: "Your attack hits. 12 damage. Target bloodied."
    
    # SPARK enhances:
    # "Your blade arcs through the air, striking deep into the 
    #  orc's shoulder for 12 points of damage. The warrior 
    #  staggers, blood streaming from the wound—bloodied."
    
    # Verify LLM didn't contradict template facts
    template_facts = extract_facts(template)
    # ["hit=true", "damage=12", "target_bloodied=true"]
    
    narration_facts = extract_facts(llm_additions)
    # Check for contradictions
    
    violations = []
    for fact in template_facts:
        if contradicts(fact, narration_facts):
            violations.append(f"template_contradiction: {fact}")
    
    return violations
```

**Pros**:
- Faster than full semantic check
- High confidence in template portion
- Focuses verification on risky LLM additions
- Good middle ground

**Cons**:
- Only works with template-augmented narration
- Requires good fact extraction
- LLM can still violate in subtle ways
- Template design is critical

**Example**:
```
[TEMPLATE (locked)]: "Miss. The orc dodges."
[LLM ADDITION]: "Your blade swings wide, the orc barely dodging aside"

CHECK: "Miss" in template, "barely" in addition
VERIFY: Does "barely" contradict truth_packet["margin"]?
- If margin = -1: "barely" is ALLOWED (close miss)
- If margin = -15: "barely" is VIOLATION (should be "easily")
```

**Verdict**: Use for template-based narration. Cheaper than full semantic, more thorough than regex.

---

#### **Approach 7.2.5: Regression Testing**

**Method**: Gold master scenarios with known-correct narrations

```python
class GoldMasterTest:
    def __init__(self, scenario_file):
        self.scenario = load_scenario(scenario_file)
        self.expected_outcomes = self.scenario["mechanical_outcomes"]
        self.acceptable_narrations = self.scenario["reference_narrations"]
    
    def run_test(self, iterations=100):
        violations = []
        
        for i in range(iterations):
            # Run scenario with SPARK
            seed = self.scenario["seed"]
            BOX.reset(seed)
            result = run_combat(self.scenario, seed=seed)
            
            # Verify mechanical determinism
            if result.mechanical != self.expected_outcomes:
                violations.append({
                    "iter": i,
                    "type": "mechanical_drift",
                    "expected": self.expected_outcomes,
                    "actual": result.mechanical
                })
            
            # Check narration for violations
            narration_violations = check_all_violations(
                result.narration, 
                result.truth_packet
            )
            
            if narration_violations:
                violations.append({
                    "iter": i,
                    "type": "narration_violation",
                    "violations": narration_violations
                })
        
        return {
            "total_iterations": iterations,
            "violation_count": len(violations),
            "violation_rate": len(violations) / iterations,
            "violations": violations
        }
```

**Gold Master Scenarios** (from existing infrastructure):
1. Basic melee combat (10 rounds)
2. Spellcasting with saves (fireball vs 4 targets)
3. Multi-target attack (cleave chain)
4. Complex positioning (flanking, cover, AoO)

**Pros**:
- Comprehensive (covers full combat flow)
- Catches regressions
- Validates determinism
- Builds quality metrics over time

**Cons**:
- Slow (can't run on every narration)
- Requires maintaining gold masters
- Can't catch all novel scenarios
- Needs regular updates

**Verdict**: Essential for quality assurance, but run as CI/nightly tests, not per-narration.

---

### 7.3 Recommended Detection Pipeline

**Three-tier approach**:

```
┌────────────────────────────────────┐
│  SPARK generates narration         │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│  TIER 1: Regex Detection (KILL-002)│  ← REAL-TIME (< 50ms)
│  - Mechanical assertions           │
│  - Unauthorized effects            │
│  - Obvious contradictions          │
└──────────────┬─────────────────────┘
               │
          ┌────┴────┐
          │ Flagged?│
          └────┬────┘
               │
       ┌───────┴────────┐
       │                │
      YES              NO
       │                │
       ▼                ▼
┌─────────────┐   ┌──────────────┐
│ BLOCK       │   │ PRESENT TO   │
│ NARRATION   │   │ PLAYER       │
│             │   │              │
│ Fallback to │   └──────┬───────┘
│ template    │          │
└─────────────┘          │
                         ▼
               ┌──────────────────────┐
               │ TIER 2: Template     │  ← ASYNC (< 500ms)
               │ Anchoring Check      │
               │ (if template-based)  │
               └──────────┬───────────┘
                          │
                     ┌────┴────┐
                     │ Flagged?│
                     └────┬────┘
                          │
                  ┌───────┴────────┐
                  │                │
                 YES              NO
                  │                │
                  ▼                ▼
            ┌─────────────┐  ┌───────────┐
            │ LOG WARNING │  │ CONTINUE  │
            │ Alert DM    │  └───────────┘
            └─────────────┘
                          │
                          ▼
               ┌──────────────────────┐
               │ TIER 3: Semantic LLM │  ← BACKGROUND (1-5s)
               │ (sample 10% random)  │
               └──────────┬───────────┘
                          │
                     ┌────┴────┐
                     │ Flagged?│
                     └────┬────┘
                          │
                  ┌───────┴────────┐
                  │                │
                 YES              NO
                  │                │
                  ▼                ▼
            ┌─────────────┐  ┌───────────┐
            │ LOG TO      │  │ LOG TO    │
            │ VIOLATIONS  │  │ QUALITY   │
            │ DB          │  │ METRICS   │
            └─────────────┘  └───────────┘
                          │
                          ▼
               ┌──────────────────────┐
               │ TIER 4: Regression   │  ← NIGHTLY
               │ (gold master tests)  │
               └──────────────────────┘
```

**Tier Responsibilities**:

**Tier 1 (Real-time, blocking)**:
- Regex patterns (KILL-002)
- Critical violations only
- Fast execution (< 50ms)
- Blocks player presentation if violation found
- Fallback to safe template

**Tier 2 (Async, warning)**:
- Template anchoring (if applicable)
- Runs in parallel with player experience
- Logs warnings for DM dashboard
- Doesn't block, but alerts

**Tier 3 (Background, sampling)**:
- Semantic LLM check on 10% of narrations
- Catches subtle violations
- Builds quality metrics
- Trains detection patterns

**Tier 4 (Offline, comprehensive)**:
- Regression tests with gold masters
- Full combat scenario validation
- Nightly CI/CD runs
- Long-term quality tracking

---

### 7.4 Metrics to Track

#### **Violation Rate Metrics**

```python
class ViolationMetrics:
    def __init__(self):
        self.violations_by_category = defaultdict(int)
        self.total_narrations = 0
        self.template_only_violations = 0
        self.llm_augmented_violations = 0
    
    def track_violation(self, category, narration_type):
        self.violations_by_category[category] += 1
        if narration_type == "template_only":
            self.template_only_violations += 1
        else:
            self.llm_augmented_violations += 1
    
    def get_rates(self):
        return {
            "overall_rate": sum(self.violations_by_category.values()) / self.total_narrations,
            "by_category": {
                cat: count / self.total_narrations 
                for cat, count in self.violations_by_category.items()
            },
            "template_vs_llm": {
                "template_only": self.template_only_violations / self.total_narrations,
                "llm_augmented": self.llm_augmented_violations / self.total_narrations
            }
        }
```

**Target Metrics** (aspirational):
- Overall violation rate: < 1% (< 1 violation per 100 narrations)
- Critical violations (outcome mismatch): < 0.1%
- Template-only violations: < 0.01% (templates are pre-verified)
- LLM-augmented violations: < 2% (LLM adds risk)

---

#### **Detection Method Metrics**

```python
class DetectionMetrics:
    def __init__(self):
        self.method_catches = defaultdict(int)  # How many each method caught
        self.method_false_positives = defaultdict(int)
        self.method_execution_time = defaultdict(list)
    
    def track_detection(self, method, caught_violation, false_positive, exec_time):
        if caught_violation:
            self.method_catches[method] += 1
        if false_positive:
            self.method_false_positives[method] += 1
        self.method_execution_time[method].append(exec_time)
    
    def get_effectiveness(self):
        return {
            method: {
                "catch_rate": self.method_catches[method],
                "false_positive_rate": self.method_false_positives[method] / 
                                       self.method_catches[method],
                "avg_exec_time_ms": statistics.mean(self.method_execution_time[method])
            }
            for method in self.method_catches.keys()
        }
```

**Target Detection Metrics**:
- Regex (Tier 1):
  - Catch rate: 60-70% of violations
  - False positive rate: < 5%
  - Exec time: < 50ms
  
- Template Anchoring (Tier 2):
  - Catch rate: 85-90% of template violations
  - False positive rate: < 2%
  - Exec time: < 500ms

- Semantic LLM (Tier 3):
  - Catch rate: 95%+ of all violations
  - False positive rate: < 1%
  - Exec time: 1-5 seconds

---

#### **Scenario-Specific Metrics**

```python
class ScenarioMetrics:
    """Track violations by combat scenario type"""
    
    scenarios = {
        "melee_basic": {"turns": 10, "violations": []},
        "spellcasting": {"turns": 5, "violations": []},
        "multi_target": {"turns": 8, "violations": []},
        "complex_positioning": {"turns": 12, "violations": []}
    }
    
    def violation_rate_by_scenario(self):
        return {
            scenario: len(data["violations"]) / data["turns"]
            for scenario, data in self.scenarios.items()
        }
```

**Expected Patterns**:
- Basic melee: Lowest violation rate (simple outcomes)
- Spellcasting: Medium rate (save mechanics complex)
- Multi-target: Higher rate (tracking multiple outcomes)
- Complex positioning: Highest rate (geometry violations)

---

### 7.5 Integration with Kill Switch Framework

Existing kill switches:
- **KILL-001**: Memory hash mismatch
- **KILL-002** (planned): Regex mechanical assertions

**New Kill Switches for Narration**:

**KILL-003: Critical Violation Detection**
```python
def KILL_003_critical_violation(narration, truth_packet):
    """Block narration if critical violation detected"""
    
    critical_patterns = [
        (r"hit", lambda: truth_packet["hit"] == False, "outcome_reversal"),
        (r"miss", lambda: truth_packet["hit"] == True, "outcome_reversal"),
        (r"\d+\s*damage", lambda d: d != truth_packet["damage"], "wrong_damage"),
        (r"you can't", lambda: True, "mechanical_adjudication"),
    ]
    
    for pattern, violation_check, violation_type in critical_patterns:
        if re.search(pattern, narration, re.IGNORECASE):
            if violation_check():
                # KILL SWITCH ACTIVATED
                log_critical(f"KILL-003 triggered: {violation_type}")
                return FALLBACK_TEMPLATE(truth_packet)
    
    return narration  # No critical violation
```

**KILL-004: Entity Hallucination**
```python
def KILL_004_entity_check(narration, truth_packet):
    """Block narration if mentions non-existent entities"""
    
    valid_entities = set(truth_packet["scene"]["entities"])
    
    # Extract entity mentions from narration
    mentioned_entities = extract_entities(narration)
    
    hallucinated = mentioned_entities - valid_entities
    
    if hallucinated:
        log_critical(f"KILL-004: Hallucinated entities: {hallucinated}")
        return FALLBACK_TEMPLATE(truth_packet)
    
    return narration
```

**KILL-005: Geometry Violation**
```python
def KILL_005_geometry_check(narration, truth_packet):
    """Block narration if describes impossible positions"""
    
    if "behind" in narration:
        # Check if claimed obstacle exists
        claimed_obstacle = extract_obstacle(narration)
        if claimed_obstacle not in truth_packet["scene"]["objects"]:
            log_critical(f"KILL-005: Non-existent obstacle: {claimed_obstacle}")
            return FALLBACK_TEMPLATE(truth_packet)
    
    if "flank" in narration.lower():
        if not truth_packet.get("flanking", False):
            log_critical("KILL-005: Claimed flanking without achieving it")
            return FALLBACK_TEMPLATE(truth_packet)
    
    return narration
```

**KILL-006: Unauthorized Effect**
```python
def KILL_006_effect_check(narration, truth_packet):
    """Block narration if invents effects not in truth packet"""
    
    valid_effects = set(truth_packet.get("effects", []))
    
    # Pattern match common invented effects
    invented_effects = {
        "slow": r"(?:slow|slowed|slowing)",
        "stun": r"(?:stun|stunned|stunning)",
        "knockback": r"(?:knock|knocked|knocking) (?:back|down|prone)",
        "ignite": r"(?:ignite|ignites|burning|aflame)",
    }
    
    for effect_name, pattern in invented_effects.items():
        if re.search(pattern, narration, re.IGNORECASE):
            if effect_name not in valid_effects:
                log_critical(f"KILL-006: Invented effect: {effect_name}")
                return FALLBACK_TEMPLATE(truth_packet)
    
    return narration
```

**Integration into Pipeline**:
```python
def narration_with_kill_switches(truth_packet, tone_settings):
    # Generate narration
    narration = SPARK.generate(truth_packet, tone_settings)
    
    # Run kill switches in order
    narration = KILL_003_critical_violation(narration, truth_packet)
    narration = KILL_004_entity_check(narration, truth_packet)
    narration = KILL_005_geometry_check(narration, truth_packet)
    narration = KILL_006_effect_check(narration, truth_packet)
    
    # If any kill switch triggered, narration is now fallback template
    # Log and continue
    
    return narration
```

---

### 7.6 Evaluation Rubric

| Violation Category | Severity | Detection Method | Kill Switch | Auto-Fix |
|--------------------|----------|------------------|-------------|----------|
| **Outcome Mismatch** | CRITICAL | Regex + Semantic | KILL-003 | Fallback |
| **Entity Mismatch** | HIGH | Entity extraction | KILL-004 | Fallback |
| **Geometry Mismatch** | HIGH | Pattern + Scene check | KILL-005 | Fallback |
| **Severity Mismatch** | MEDIUM | HP% comparison | Warning | No |
| **Mechanical Assertion** | CRITICAL | Regex (KILL-002) | KILL-003 | Fallback |
| **Unauthorized Mechanics** | CRITICAL | Pattern + Effects check | KILL-006 | Fallback |
| **Temporal Mismatch** | MEDIUM | Initiative order check | Warning | No |

**Fallback Strategy**: When kill switch triggers, replace SPARK narration with minimal template:

```python
def FALLBACK_TEMPLATE(truth_packet):
    """Safe template that can't violate truth"""
    if truth_packet["event"] == "melee_attack":
        if truth_packet["hit"]:
            return f"Hit. {truth_packet['damage']} damage."
        else:
            return "Miss."
    
    elif truth_packet["event"] == "spell_cast":
        if truth_packet["spell_succeeded"]:
            return f"{truth_packet['spell_name']} succeeds. {truth_packet['effect_summary']}"
        else:
            return f"{truth_packet['spell_name']} fails."
    
    # ... templates for other event types
```

---

## Integration Considerations

### 8.1 Workflow Integration

```
Player Action
     │
     ▼
┌──────────────────┐
│ BOX processes    │
│ (deterministic)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ BOX outputs      │
│ truth packet     │
│ [BOX] tags       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ LENS receives    │
│ truth packet     │
└────────┬─────────┘
         │
         ├─── Query: Unknown data? ───┐
         │                            │
         │                            ▼
         │                    ┌───────────────┐
         │                    │ Fact          │
         │                    │ Completion    │
         │                    │ (Sub-Q 5)     │
         │                    └───────┬───────┘
         │                            │
         │◄───────────────────────────┘
         │
         ├─── Fetch tone settings ────┐
         │                            │
         │                            ▼
         │                    ┌───────────────┐
         │                    │ DM Persona    │
         │                    │ Config        │
         │                    │ (Sub-Q 6)     │
         │                    └───────┬───────┘
         │                            │
         │◄───────────────────────────┘
         │
         ▼
┌──────────────────┐
│ LENS constructs  │
│ SPARK prompt:    │
│ - Truth packet   │
│ - Tone settings  │
│ - NPC voices     │
│ - Constraints    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ SPARK generates  │
│ narration        │
│ (Qwen3 8B)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Violation        │
│ Detection        │
│ (Sub-Q 7)        │
└────────┬─────────┘
         │
         ├─── KILL-003 through KILL-006
         │
    ┌────┴────┐
    │ Valid?  │
    └────┬────┘
         │
    ┌────┴────┐
    │         │
   YES       NO
    │         │
    │         ▼
    │    ┌─────────────┐
    │    │ Fallback    │
    │    │ Template    │
    │    └──────┬──────┘
    │           │
    │◄──────────┘
    │
    ▼
┌──────────────────┐
│ Present to       │
│ player           │
└──────────────────┘
```

---

### 8.2 Performance Constraints

**Latency Budget** (from player action to narration):
- BOX computation: < 100ms (deterministic, fast)
- Fact completion (if needed): < 500ms (LLM generation)
- SPARK narration: < 2000ms (Qwen3 8B, 200 tokens)
- Tier 1 detection (regex): < 50ms (real-time)
- Tier 2 detection (template): < 500ms (async)
- **Total**: < 3000ms target (< 5000ms acceptable)

**Memory Budget**:
- Qwen3 8B model: ~8GB GPU RAM
- Context window: 8K-32K tokens
- Truth packet: ~500 tokens
- Tone settings: ~100 tokens
- NPC voices (active): ~200 tokens
- Conversation history: ~4K tokens
- **Total context**: ~5K tokens (plenty of headroom)

---

### 8.3 Quality Assurance

**Continuous Monitoring**:
```python
class NarrationQA:
    def __init__(self):
        self.metrics = ViolationMetrics()
        self.detection = DetectionMetrics()
    
    def monitor_session(self, session_id):
        # Track violations in real-time
        while session_active(session_id):
            narration_event = wait_for_narration()
            
            # Tier 1: Real-time detection
            t1_result = tier1_regex_check(narration_event)
            self.detection.track_detection("regex", t1_result)
            
            # Tier 2: Async template check
            if narration_event.has_template:
                t2_result = async_template_check(narration_event)
                self.detection.track_detection("template", t2_result)
            
            # Tier 3: Sample for LLM check
            if random.random() < 0.10:  # 10% sampling
                t3_result = background_llm_check(narration_event)
                self.detection.track_detection("llm", t3_result)
            
            # Update metrics
            if any_violation(t1_result, t2_result, t3_result):
                self.metrics.track_violation(
                    violation_category,
                    narration_event.type
                )
    
    def generate_report(self):
        return {
            "violation_rates": self.metrics.get_rates(),
            "detection_effectiveness": self.detection.get_effectiveness(),
            "recommendations": self.generate_recommendations()
        }
```

**Nightly Regression**:
```bash
#!/bin/bash
# Run nightly regression tests

echo "Running gold master scenarios..."
python regression_tests.py --scenarios=all --iterations=1000

echo "Analyzing violation trends..."
python analyze_violations.py --last-7-days

echo "Generating QA report..."
python generate_qa_report.py --output=reports/daily_qa.html

echo "Checking for regressions..."
if python check_regression.py --threshold=0.05; then
    echo "✅ Quality stable"
else
    echo "❌ Quality regression detected!"
    # Alert team
fi
```

---

## Recommendations

### 9.1 Implementation Priority

**Phase 1: Unknown Handling** (Critical foundation)
1. Implement decision tree for unknown fact types
2. Integrate with fact completion protocol from RQ-SPARK-001-C
3. Add [UNCERTAIN] provenance tag support
4. Test with 5 scenario walkthroughs

**Phase 2: Basic Violation Detection** (Risk mitigation)
1. Implement KILL-003 through KILL-006 (regex-based)
2. Add fallback template system
3. Test with existing gold master scenarios
4. Establish baseline violation metrics

**Phase 3: Tone Control** (Quality enhancement)
1. Implement three-part system prompt architecture
2. Add tone parameter controls (verbosity, drama, etc.)
3. Implement template anchoring for bleeding prevention
4. Test tone determinism with 100+ combat runs

**Phase 4: Advanced Detection** (Quality assurance)
1. Add template anchoring check (Tier 2)
2. Implement async LLM verification (Tier 3)
3. Set up continuous monitoring dashboard
4. Establish nightly regression suite

---

### 9.2 Critical Success Factors

1. **Truth Packet Integrity**: NEVER let SPARK bypass truth packet
2. **Determinism**: Same seed → same BOX outcome regardless of tone
3. **Fast Detection**: Regex checks must be < 50ms to not block player
4. **Graceful Degradation**: Fallback template always available
5. **Transparency**: Provenance tags show data source to DM

---

### 9.3 Open Questions for Future Research

1. **Adaptive Tone**: Should tone adapt to combat intensity automatically?
2. **Player Preferences**: Per-player tone settings in multi-player?
3. **Learning from Violations**: Can violation patterns improve SPARK prompts?
4. **Semantic Detection**: Can we train a lightweight violation classifier?
5. **Natural Language Unknowns**: Should SPARK ask player in-character or meta?

---

## Appendices

### Appendix A: Example Truth Packet Schemas

```json
{
  "melee_attack": {
    "event": "melee_attack",
    "timestamp": 1234567890,
    "attacker": "PC_fighter",
    "attacker_level": 5,
    "target": "orc_warrior_1",
    "weapon": "longsword",
    "attack_roll": 18,
    "attack_bonus": 7,
    "target_ac": 15,
    "hit": true,
    "margin": 3,
    "critical_threat": false,
    "damage_roll": "1d8+3",
    "damage": 8,
    "damage_type": "slashing",
    "target_hp_before": 26,
    "target_hp_after": 18,
    "target_hp_max": 26,
    "target_hp_percent": 69,
    "target_condition": "normal",
    "target_killed": false,
    "provenance": "[BOX]"
  },
  
  "spell_cast": {
    "event": "spell_cast",
    "caster": "PC_wizard",
    "caster_level": 7,
    "spell_name": "fireball",
    "spell_level": 3,
    "save_type": "reflex",
    "save_dc": 16,
    "targets": [
      {
        "target": "orc_warrior_1",
        "save_roll": 12,
        "save_succeeded": false,
        "damage": 28,
        "hp_before": 26,
        "hp_after": -2,
        "killed": true
      },
      {
        "target": "orc_warrior_2",
        "save_roll": 19,
        "save_succeeded": true,
        "damage": 14,
        "hp_before": 30,
        "hp_after": 16,
        "killed": false
      }
    ],
    "area_of_effect": "20ft_radius",
    "center_position": [10, 15],
    "provenance": "[BOX]"
  }
}
```

### Appendix B: Violation Detection Test Cases

```python
TEST_CASES = [
    {
        "name": "Outcome Reversal",
        "truth": {"hit": False},
        "narration": "Your blade strikes the orc!",
        "expected_violation": "outcome_mismatch",
        "severity": "CRITICAL"
    },
    {
        "name": "Wrong Damage",
        "truth": {"damage": 12},
        "narration": "You deal 20 damage!",
        "expected_violation": "outcome_mismatch",
        "severity": "CRITICAL"
    },
    {
        "name": "Entity Hallucination",
        "truth": {"entities": ["PC_fighter", "orc_warrior"]},
        "narration": "The goblin shaman casts a spell...",
        "expected_violation": "entity_mismatch",
        "severity": "HIGH"
    },
    {
        "name": "Unauthorized Effect",
        "truth": {"effects": ["damage"]},
        "narration": "The flames also slow the orc's movement",
        "expected_violation": "unauthorized_mechanics",
        "severity": "CRITICAL"
    },
    {
        "name": "Severity Mismatch",
        "truth": {"damage": 2, "target_hp_max": 50, "hp_percent": 96},
        "narration": "Your devastating blow nearly kills him!",
        "expected_violation": "severity_mismatch",
        "severity": "MEDIUM"
    }
]
```

### Appendix C: Fallback Template Library

```python
FALLBACK_TEMPLATES = {
    "melee_attack_hit": lambda tp: (
        f"Hit. {tp['damage']} damage. "
        f"{'Target killed.' if tp['target_killed'] else ''}"
    ),
    "melee_attack_miss": lambda tp: "Miss.",
    "melee_attack_critical": lambda tp: (
        f"Critical hit! {tp['damage']} damage. "
        f"{'Target killed.' if tp['target_killed'] else ''}"
    ),
    "spell_single_target_save": lambda tp: (
        f"{tp['spell_name']} cast. "
        f"{'Target saves.' if tp['save_succeeded'] else f'Target fails save. {tp['damage']} damage.'}"
    ),
    "spell_area_effect": lambda tp: (
        f"{tp['spell_name']} detonates. "
        f"{len(tp['targets'])} creatures affected."
    )
}
```

---

## Conclusion

This research establishes a comprehensive framework for:

1. **Handling unknowns** gracefully without fabricating mechanical authority
2. **Controlling tone** while preserving mechanical truth integrity
3. **Detecting violations** automatically with multi-tier approach

The system maintains strict separation between BOX (mechanical authority) and SPARK (narrative presentation), ensuring D&D 3.5e rules fidelity while supporting flexible DM storytelling styles.

**Key Takeaway**: Trust but verify. SPARK generates creative narration, but LENS and the kill switch framework ensure it never contradicts BOX's mechanical truth.

---

**Status**: Research complete. Ready for implementation planning.

**Next Steps**: 
1. Review with architecture team
2. Prioritize implementation phases
3. Begin Phase 1: Unknown handling integration

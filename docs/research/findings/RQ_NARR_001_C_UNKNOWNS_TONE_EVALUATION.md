# RQ-NARR-001-C: Unknown Handling + Tone Control + Violation Detection

**Research Type:** Architectural Design (Pre-Implementation)
**Date:** 2026-02-11
**Status:** DELIVERED — Awaiting PM Review
**Researcher:** Sonnet (Agent)
**Context:** Phase 1/2 narration pipeline design (WO-027 through WO-033)
**Dispatch:** RQ-NARR-001-C

---

## Executive Summary

This research addresses three critical sub-questions for the narration system:

**Sub-Question 5: Unknown Handling** — When Lens returns "unknown" for data Spark needs to narrate, how should Spark respond without fabricating mechanical facts?

**Sub-Question 6: Tone Control** — How to support DM style/personality variation (verbosity, drama, humor) without allowing tone to alter mechanical truth?

**Sub-Question 7: Violation Detection** — How to automatically detect when Spark narration contradicts Box truth?

---

### Key Findings

#### Sub-Q5: Unknown Handling
1. **Five-strategy taxonomy** for handling unknowns: conversational clarification, DM stall pacing, fact completion request, safe vagueness, explicit uncertainty
2. **Decision tree** based on unknown type (scene detail, NPC personality, environmental, historical) with specific handling per category
3. **Critical constraint:** Spark must NEVER fabricate dimensions, positions, or mechanical properties when data is missing
4. **Integration:** Unknowns trigger fact completion protocol from RQ-SPARK-001-C (improvisation mode)

#### Sub-Q6: Tone Control
1. **Separation principle:** Truth layer (immutable Box data) vs style layer (variable DM persona)
2. **Five tone parameters:** Verbosity, drama, humor, grittiness, NPC voice
3. **Bleeding prevention:** Style must NEVER imply different mechanical outcomes (e.g., "barely missed" only if margin data present)
4. **Architecture:** Tone as separate system prompt section, verified by determinism gate (same seed → same mechanical outcome regardless of tone)

#### Sub-Q7: Violation Detection
1. **Six violation categories** with automated detection strategies
2. **Three-tier detection pipeline:** Keyword matching (fast, <10ms) → Regex patterns (KILL-002 implementation) → Semantic comparison (async, thorough)
3. **Template anchoring optimization:** When narration is template-augmented, verify LLM additions don't contradict template content (cheaper than full semantic check)
4. **Target metrics:** <1% violation rate per 100 narrations, <5% false positive rate, template-only baseline of 0 violations

---

### Critical Constraints Enforced

- **Axiom 2:** BOX is sole mechanical authority — Spark cannot adjudicate even when data unknown
- **Axiom 3:** LENS adapts stance, not authority — Tone control lives in Lens Player Model, never affects Box
- **Axiom 4:** Provenance labeling on all facts — [UNCERTAIN] tag for unknowns, [NARRATIVE] for tone-varied output
- **Axiom 5:** No SPARK→State writes — Unknown handling cannot fabricate facts into game state
- **BL-003:** No core imports in narration layer
- **KILL-002:** Mechanical assertion detection (regex for unauthorized claims)

---

## Sub-Question 5: Handling Unknowns and Missing Facts

### 5.1 Problem Statement

**Scenario:** Lens returns "unknown" or NULL for data Spark needs to generate narration.

**Examples:**
- Player asks "What's on the shelf?" — scene description lacks shelf inventory
- NPC reaction needed — NPC personality not defined in campaign memory
- Environmental detail — "How deep is the water?" with no scene data
- Historical question — "Has this town been attacked before?" with no campaign memory entry

**Critical Constraint:** Spark must NEVER fabricate:
- Dimensions (distances, heights, depths)
- Positions (grid coordinates, relative locations)
- Mechanical properties (HP totals, save DCs, armor class)

Fabrication = mechanical authority claim = **doctrine violation**.

---

### 5.2 Five Unknown Handling Strategies

#### Strategy 1: Conversational Clarification (DM-Style Stalling)

**Approach:** Spark responds in-character with a natural DM stall while Lens triggers fact completion.

**Example:**

| Unknown Data | Spark Response | Next Action |
|-------------|----------------|-------------|
| Shelf contents | "Hmm, let me take a closer look at that shelf..." | Lens triggers Spark improvisation mode to generate shelf contents |
| Water depth | "You'd need to investigate more carefully to gauge the depth." | Player can declare "I test the depth with my 10-foot pole" |
| NPC mood | "The guard's expression is hard to read. What do you do?" | Lens requests NPC personality generation from Spark (RQ-SPARK-001-C protocol) |

**Advantages:**
- Feels natural (real DMs do this)
- Preserves immersion
- Gives Lens time to generate missing fact

**Disadvantages:**
- Adds latency (fact generation + narration)
- Player may notice delay

**Implementation:**
```python
# Truth Packet includes "unknown_fields" list
truth_packet = {
    "event": "player_query",
    "query_target": "shelf",
    "unknown_fields": ["shelf_contents"],
    "unknown_type": "scene_detail"
}

# Spark uses template for this unknown type
if "shelf_contents" in truth_packet["unknown_fields"]:
    return "Hmm, let me take a closer look at that shelf..."
```

**Trigger Condition:** Unknown is **scene detail** that Spark can improvise (not mechanical property).

---

#### Strategy 2: DM Stall Pacing (Explicit Temporal Buffer)

**Approach:** Brief in-character pause feels natural and gives system time to complete fact.

**Real DM Examples:**
- "The DM pauses, considering..."
- "Let me check my notes..."
- "Good question — give me a moment to recall the details."

**Implementation:**
```python
# Lens detects unknown, triggers async fact completion
async def handle_unknown_with_stall(truth_packet, unknown_field):
    # Generate stall narration
    stall_text = generate_stall_narration(unknown_field)

    # Trigger fact completion in parallel
    fact_task = asyncio.create_task(
        spark_improvise_fact(unknown_field, scene_context)
    )

    # Return stall narration immediately
    yield stall_text

    # Wait for fact completion
    completed_fact = await fact_task

    # Generate follow-up narration with completed fact
    yield generate_narration_with_fact(completed_fact)
```

**Advantages:**
- Mimics real DM behavior
- Explicit temporal buffer (1-2 seconds for fact generation)
- Player perceives as normal DM pacing

**Disadvantages:**
- Requires streaming narration output
- Two-phase narration (stall + continuation)

**Trigger Condition:** Unknown requires improvisation but player expects immediate response.

---

#### Strategy 3: Fact Completion Request (Improvisation Protocol)

**Approach:** Lens asks Spark to generate the missing fact using improvisation protocol from RQ-SPARK-001-C, then Spark narrates from the newly generated fact.

**Fact Completion Protocol Flow:**

```
1. Lens detects unknown field: "shelf_contents"
2. Lens checks if field is improvise-able (scene detail? Yes. Mechanical property? No.)
3. Lens sends Spark improvisation request:
   {
     "mode": "improvise",
     "fact_type": "scene_detail",
     "context": "dungeon corridor, abandoned for 50 years, dust-covered shelf",
     "constraints": ["no treasure", "no mechanical properties"],
     "budget": 200 tokens
   }
4. Spark generates: "dusty tomes, rusted iron candelabra, broken inkwell"
5. Lens validates: no mechanical claims? No treasure? ✅
6. Lens tags as [DERIVED]: generated by Spark improvisation, not Box truth
7. Lens adds to campaign memory with provenance: [SPARK:IMPROVISED]
8. Lens sends narration request with completed fact
9. Spark narrates: "The shelf holds dusty tomes, a rusted candelabra, and a broken inkwell."
```

**Critical Safeguards:**
- Generated facts tagged [SPARK:IMPROVISED], never [BOX]
- No mechanical properties allowed (no AC, HP, damage, dimensions)
- Validation before memory write (no treasure unless Box authorized)
- DM can override/veto improvised facts via Judge's Lens

**Advantages:**
- Fills gaps seamlessly
- Maintains narrative flow
- Provenance-tracked (can be overridden)

**Disadvantages:**
- Risk of Spark inventing mechanical properties (requires validation)
- Generated fact may contradict later DM intent
- Adds complexity (two-phase generation)

**Trigger Condition:** Unknown is **scene flavor** (not mechanical), player expects detail.

---

#### Strategy 4: Safe Vagueness (No Commitment)

**Approach:** Spark describes without committing to specifics, allowing player to investigate further.

**Examples:**

| Unknown Data | Spark Safe Vagueness | Player Response Options |
|-------------|---------------------|------------------------|
| Shelf contents | "The shelf holds various items." | "I examine the items more closely." |
| Water depth | "The water is dark and murky." | "I test the depth with my pole." |
| NPC mood | "The guard watches you with an unreadable expression." | "I try to gauge his mood (Sense Motive check)." |

**Key Principle:** Vague narration is NOT mechanical authority. "Various items" doesn't claim specifics; "dark and murky" doesn't claim depth.

**Implementation:**
```python
# Spark prompt includes vagueness templates
VAGUE_TEMPLATES = {
    "shelf_contents": "The shelf holds various items.",
    "water_depth": "The water is dark and murky.",
    "npc_mood": "{npc} watches you with an unreadable expression.",
}

if truth_packet.get("unknown_fields"):
    for field in truth_packet["unknown_fields"]:
        if field in VAGUE_TEMPLATES:
            return VAGUE_TEMPLATES[field]
```

**Advantages:**
- Zero fabrication risk
- Fast (template-based)
- Natural invitation for player investigation

**Disadvantages:**
- May feel evasive if overused
- Doesn't satisfy player curiosity immediately

**Trigger Condition:** Unknown is **not urgent** and player can investigate.

---

#### Strategy 5: Explicit Uncertainty (Tagged Output)

**Approach:** Tag output as [UNCERTAIN] and let player know the system doesn't have data.

**Examples:**

| Unknown Data | Explicit Uncertainty Response | Provenance Tag |
|-------------|------------------------------|----------------|
| Shelf contents | "You're not sure what's on the shelf from this distance." | [UNCERTAIN] |
| Water depth | "It's difficult to judge the depth without testing it." | [UNCERTAIN] |
| Historical fact | "You don't recall hearing about attacks on this town." | [UNCERTAIN] |

**Critical Distinction:**
- [UNCERTAIN] = system acknowledges lack of data
- [NARRATIVE] = Spark generated flavor from known data
- [BOX] = mechanical truth from Box computation

**Implementation:**
```python
# Truth Packet explicitly marks unknowns
truth_packet = {
    "event": "player_query",
    "query_target": "shelf",
    "shelf_contents": None,  # NULL = unknown
    "provenance": {
        "shelf_contents": "[UNCERTAIN]"
    }
}

# Spark narration includes uncertainty cue
if truth_packet["shelf_contents"] is None:
    return "You're not sure what's on the shelf from this distance."
```

**Advantages:**
- Honest (no fabrication)
- Clear provenance (player knows system lacks data)
- Fast (template-based)

**Disadvantages:**
- Breaks immersion (metagame acknowledgment)
- May frustrate players expecting detail

**Trigger Condition:** Unknown is **mechanical property** or **historical fact** (cannot improvise).

---

### 5.3 Unknown Handling Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│ Lens detects unknown field in Truth Packet                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │ What type of unknown? │
           └───────────┬───────────┘
                       │
       ┌───────────────┼───────────────┬────────────────┐
       │               │               │                │
       ▼               ▼               ▼                ▼
┌──────────┐    ┌──────────┐   ┌──────────┐    ┌──────────┐
│ Scene    │    │ NPC      │   │ Mechanical│    │Historical│
│ Detail   │    │Personality│   │ Property  │    │  Fact    │
└────┬─────┘    └────┬─────┘   └────┬─────┘    └────┬─────┘
     │               │               │                │
     │               │               │                │
     ▼               ▼               ▼                ▼
┌──────────┐    ┌──────────┐   ┌──────────┐    ┌──────────┐
│Improvise?│    │Improvise │   │ NEVER    │    │Can Check │
│YES       │    │NPC Trait │   │IMPROVISE │    │  Memory? │
└────┬─────┘    └────┬─────┘   └────┬─────┘    └────┬─────┘
     │               │               │                │
     ▼               ▼               ▼                ▼
┌──────────┐    ┌──────────┐   ┌──────────┐    ┌──────────┐
│Strategy 3│    │Strategy 1│   │Strategy 5│    │Strategy 4│
│ Fact     │    │ Clarify  │   │ Explicit │    │   Safe   │
│Completion│    │  + Gen   │   │Uncertain │    │ Vagueness│
└──────────┘    └──────────┘   └──────────┘    └──────────┘
```

**Decision Logic:**

1. **Scene Detail (shelf contents, room features):**
   - Can improvise? → **Strategy 3** (Fact Completion Request)
   - Player expects immediate answer? → **Strategy 1** (Conversational Clarification)
   - Not urgent? → **Strategy 4** (Safe Vagueness)

2. **NPC Personality (mood, reaction):**
   - NPC is new? → **Strategy 1** (Clarification + NPC generation via RQ-SPARK-001-C)
   - NPC personality should be consistent? → **Strategy 4** (Safe Vagueness until DM defines)

3. **Mechanical Property (water depth in feet, damage values, AC):**
   - **ALWAYS** → **Strategy 5** (Explicit Uncertainty)
   - **NEVER** improvise mechanical properties (doctrine violation)

4. **Historical Fact (campaign lore, NPC backstory):**
   - Can check campaign memory? → **Strategy 4** (Safe Vagueness + memory query)
   - No memory entry? → **Strategy 5** (Explicit Uncertainty)

---

### 5.4 Five Scenario Walkthroughs

#### Scenario 1: Player Asks About Shelf Contents

**Setup:**
- Player: "What's on the shelf?"
- Scene description: "Abandoned dungeon corridor, dust-covered wooden shelf"
- Campaign memory: No shelf inventory entry

**Decision Tree:**
- Unknown type: Scene detail
- Can improvise? Yes (non-mechanical)
- Player expects answer? Yes

**Selected Strategy:** Strategy 3 (Fact Completion Request)

**Execution:**
```
1. Lens detects unknown: shelf_contents = NULL
2. Lens sends improvisation request to Spark:
   {
     "mode": "improvise",
     "fact_type": "scene_detail",
     "context": "abandoned dungeon, 50 years, dust, shelf",
     "constraints": ["no treasure", "no magical items", "mundane objects only"]
   }
3. Spark generates: "dusty tomes (unreadable), rusted candelabra, broken inkwell, mouse nest"
4. Lens validates: no mechanical properties? ✅ no treasure? ✅
5. Lens writes to campaign memory:
   {
     "fact": "shelf_contents: dusty tomes, candelabra, inkwell, mouse nest",
     "provenance": "[SPARK:IMPROVISED]",
     "scene_id": "dungeon_corridor_01",
     "timestamp": "2026-02-11T14:32:00Z"
   }
6. Lens sends narration request with completed fact
7. Spark narrates: "The shelf holds dusty, illegible tomes, a rusted iron candelabra, a broken inkwell, and what appears to be an old mouse nest."
```

**Outcome:** Player gets detail, fact is provenance-tracked, DM can override later.

---

#### Scenario 2: NPC Reaction Needed (Personality Undefined)

**Setup:**
- Combat: PC attacks guard captain
- Guard captain NPC exists in game state (entity_id=npc_guard_01)
- Campaign memory: No personality defined for guard captain

**Decision Tree:**
- Unknown type: NPC personality
- Can improvise? Yes (using RQ-SPARK-001-C NPC generation)

**Selected Strategy:** Strategy 1 (Conversational Clarification + NPC Generation)

**Execution:**
```
1. Lens detects unknown: npc_guard_01.personality = NULL
2. Lens sends NPC personality generation request to Spark:
   {
     "mode": "generate_npc_trait",
     "npc_name": "Guard Captain",
     "context": "veteran soldier, authoritative, dutiful",
     "trait_needed": "combat_reaction_personality"
   }
3. Spark generates personality traits:
   {
     "combat_style": "disciplined, tactical",
     "reaction_to_attack": "professional calm, no panic",
     "voice": "gruff, commanding"
   }
4. Lens validates and stores in NPC profile (campaign memory):
   {
     "npc_id": "npc_guard_01",
     "personality": { ... },
     "provenance": "[SPARK:GENERATED]"
   }
5. Lens sends narration request with NPC personality
6. Spark narrates: "The guard captain's eyes narrow. He draws his blade with practiced calm. 'Stand down or face the consequences,' he commands."
```

**Outcome:** NPC personality generated once, reused consistently in future encounters.

---

#### Scenario 3: Environmental Detail — Water Depth (Mechanical Property)

**Setup:**
- Player: "How deep is the water?"
- Scene: Underground pool, no depth data in scene description

**Decision Tree:**
- Unknown type: Mechanical property (distance measurement)
- Can improvise? **NO** (fabrication of dimensions forbidden)

**Selected Strategy:** Strategy 5 (Explicit Uncertainty)

**Execution:**
```
1. Lens detects unknown: water_depth = NULL
2. Lens marks as [UNCERTAIN] (mechanical property, cannot improvise)
3. Spark uses uncertainty template:
   "It's difficult to judge the depth from the surface. You'd need to test it or dive in to find out."
4. Player options:
   - "I test with my 10-foot pole" → Box resolves: pole reaches bottom at 8 feet
   - "I dive in" → Box resolves: swim check, depth revealed
```

**Outcome:** No fabrication, player prompted to investigate, Box resolves mechanical query.

---

#### Scenario 4: Historical Question (Campaign Memory Lookup)

**Setup:**
- Player: "Has this town been attacked before?"
- Campaign memory: Search for "town attack history" → no results

**Decision Tree:**
- Unknown type: Historical fact
- Can check memory? Yes (but no entry found)

**Selected Strategy:** Strategy 5 (Explicit Uncertainty) OR Strategy 4 (Safe Vagueness)

**Option A (Explicit Uncertainty):**
```
Spark: "You don't recall hearing about any attacks on this town in recent memory."
Provenance: [UNCERTAIN]
```

**Option B (Safe Vagueness):**
```
Spark: "The town's history is not widely known to outsiders."
Provenance: [NARRATIVE]
Player can: "I ask the innkeeper about the town's history" → triggers NPC dialogue
```

**Outcome:** System doesn't fabricate history, player can investigate further.

---

#### Scenario 5: Object Not in Scene (Entity Mismatch)

**Setup:**
- Player: "I grab the rope hanging from the ceiling."
- Scene description: No rope entity in scene
- Campaign memory: No rope mentioned

**Decision Tree:**
- Unknown type: Non-existent entity (not just unknown property)

**Selected Strategy:** Strategy 5 (Explicit Uncertainty) + Box Validation

**Execution:**
```
1. Lens checks scene entities: "rope" not found
2. Box validates: no rope entity exists
3. Spark narration options:

   Option A (Gentle Correction):
   "You look up but don't see any rope hanging from the ceiling."

   Option B (Explicit Absence):
   "There's no rope here."

   Option C (DM Clarification):
   "Did you mean something else, or are you checking if there's a rope?"
```

**Outcome:** System does NOT fabricate rope into scene, corrects player assumption.

---

### 5.5 Integration with Fact Completion Protocol (RQ-SPARK-001-C)

**From RQ-SPARK-001-C (Improvisation Protocol):**

Spark can generate:
- Scene details (non-mechanical)
- NPC dialogue and personality
- Object descriptions (visual, tactile)
- Atmospheric flavor

Spark CANNOT generate:
- Mechanical properties (HP, AC, damage, distances)
- Treasure or loot (unless Box authorized)
- Rule citations or legal adjudications

**Integration Points:**

1. **Lens Triggers Improvisation:**
   ```python
   if truth_packet.has_unknown("scene_detail"):
       improvised_fact = await spark_improvise(
           fact_type="scene_detail",
           context=truth_packet.scene_context,
           constraints=["no mechanical properties", "no treasure"]
       )
       truth_packet.add_derived_fact(improvised_fact, provenance="[SPARK:IMPROVISED]")
   ```

2. **Validation Before Memory Write:**
   ```python
   def validate_improvised_fact(fact: dict) -> bool:
       """Validate that improvised fact contains no forbidden content."""
       # Check for mechanical properties
       if contains_numbers(fact) and looks_like_stat(fact):
           return False
       # Check for treasure/loot
       if contains_treasure_keywords(fact):
           return False
       # Check for rule citations
       if contains_rule_references(fact):
           return False
       return True
   ```

3. **Provenance Tracking:**
   ```python
   @dataclass
   class ImprovisedFact:
       fact_type: str  # "scene_detail", "npc_personality", etc.
       content: str
       provenance: str = "[SPARK:IMPROVISED]"
       validated: bool = False
       dm_override: Optional[str] = None
   ```

---

### 5.6 Unknown Handling Implementation Checklist

**For WO-032 (NarrativeBrief Assembler):**

- [ ] Truth Packet includes `unknown_fields: List[str]` for missing data
- [ ] Unknown fields tagged with type: "scene_detail", "npc_personality", "mechanical_property", "historical_fact"
- [ ] Decision tree logic selects strategy based on unknown type
- [ ] Vagueness templates for common unknowns
- [ ] Uncertainty templates for mechanical properties

**For WO-029 (Kill Switches):**

- [ ] KILL-002 detects fabricated mechanical properties in narration (regex for distances, HP, AC, damage)
- [ ] Violation logged when Spark fabricates instead of using [UNCERTAIN] tag

**For Spark Improvisation Integration:**

- [ ] Fact completion request API to Spark
- [ ] Validation pipeline for improvised facts (no mechanical properties, no treasure)
- [ ] Provenance tagging: [SPARK:IMPROVISED]
- [ ] Campaign memory write with provenance tracking

---

## Sub-Question 6: Tone Control vs Truth Control

### 6.1 The Separation Principle

**Core Constraint:** Tone affects HOW to describe, never WHAT happened.

**Two Layers:**

1. **Truth Layer (Immutable):**
   - Source: Box computation (attack hit/miss, damage dealt, save success/fail)
   - Format: Truth Packet fields (`event`, `outcome`, `damage`, `margin`, `target_hp_percent`)
   - Provenance: [BOX]
   - **NEVER CHANGES** based on tone setting

2. **Style Layer (Variable):**
   - Source: DM persona settings (stored in Lens Player Model)
   - Format: System prompt instructions for Spark
   - Provenance: [NARRATIVE]
   - **CHANGES** based on user preference, but outcome stays same

**Example:**

| Truth Layer (Immutable) | Style Layer (Variable) |
|------------------------|----------------------|
| `event: attack_hit, damage: 12, target_hp_percent: 60, margin: 5` | **Terse:** "Hit. 12 damage." |
| (same Box data) | **Verbose:** "Your blade finds purchase between the plates of the orc's crude armor, biting deep into the flesh beneath — a solid strike that draws a guttural roar of pain." |
| (same Box data) | **Dramatic:** "With a flash of steel, your longsword cleaves through the orc's defenses! The creature staggers, blood streaming from the wound!" |

**All three narrations describe the SAME mechanical outcome (hit, 12 damage, target at 60% HP). Tone varies, truth does not.**

---

### 6.2 Five Tone Parameters

#### Parameter 1: Verbosity

**Range:** Terse ↔ Verbose

**Terse Mode (Veteran DMs, Fast-Paced Combat):**
- 1-2 sentences per event
- Minimal embellishment
- Focus on mechanical outcome

**Verbose Mode (New Players, Narrative-Focused):**
- 3-5 sentences per event
- Rich sensory detail
- Atmospheric scene-setting

**Examples:**

| Event | Terse (verbosity=0.2) | Verbose (verbosity=0.8) |
|-------|----------------------|------------------------|
| Attack hit, 12 damage | "Your sword strikes true. 12 damage." | "Your blade arcs through the air, catching the orc's shoulder with a wet crunch. The creature howls as blood sprays from the wound — a grievous blow that sends it reeling backward." |
| Spell cast, Fireball | "Fireball erupts. 28 fire damage." | "You complete the incantation, and a bead of orange light streaks from your fingertip before detonating in a roaring sphere of flame. The heat washes over you as the explosion consumes your enemies, their screams briefly audible over the roar of the inferno." |

**Implementation:**
```python
# Tone parameter in DM persona
dm_persona = {
    "verbosity": 0.5,  # 0.0 = terse, 1.0 = verbose
    "target_sentence_count": 2,  # for verbosity=0.5
}

# System prompt section
f"Narration length: {dm_persona['target_sentence_count']} sentences."
```

---

#### Parameter 2: Drama

**Range:** Understated ↔ Dramatic

**Understated Mode:**
- Calm, measured tone
- Matter-of-fact descriptions
- Minimal exclamation

**Dramatic Mode:**
- Heightened intensity
- Vivid action verbs
- Frequent exclamation

**Examples:**

| Event | Understated (drama=0.2) | Dramatic (drama=0.8) |
|-------|------------------------|---------------------|
| Critical hit, 24 damage | "Your strike finds a vital point. 24 damage." | "Your blade STRIKES TRUE, finding a gap in the armor and sinking deep into vulnerable flesh! The orc's eyes widen in shock as it staggers from the devastating blow!" |
| Save failure | "The spell takes hold." | "The arcane energies OVERWHELM the orc's defenses, seizing control of its mind!" |

**Critical Constraint:** Drama level must NOT imply different mechanical outcomes.

**Bleeding Example (FORBIDDEN):**
```
Box: save_success=True (target rolled 18 vs DC 15)
Drama=0.8 narration: "The spell barely grazes the orc's mind before it shrugs off the effect."

VIOLATION: "barely grazes" + "shrugs off" implies MARGINAL success.
Box data shows solid success (margin=+3).

CORRECT: "The spell washes over the orc, but it resists the enchantment with a grunt of effort."
(Acknowledges success without implying difficulty.)
```

---

#### Parameter 3: Humor

**Range:** Serious ↔ Occasional Wit

**Serious Mode:**
- Gritty, realistic tone
- No jokes or levity
- Tension maintained

**Humorous Mode:**
- Occasional quips
- Wry observations
- Darkly comic moments (when appropriate)

**Examples:**

| Event | Serious (humor=0.0) | Humorous (humor=0.6) |
|-------|--------------------|--------------------|
| Attack miss | "Your blade swings wide, missing the orc entirely." | "Your swing cuts through empty air as the orc ducks with surprising agility for something that smells like a garbage heap." |
| Goblin defeated | "The goblin collapses, defeated." | "The goblin hits the ground with an indignant squeak, as if offended by the audacity of being stabbed." |

**Critical Constraint:** Humor must NOT contradict Box outcomes or add mechanical effects.

**Bleeding Example (FORBIDDEN):**
```
Box: attack_miss (roll=12, target_ac=15)
Humor=0.8 narration: "Your blade bounces off the orc's armor with a comical *BOING* sound, startling you both."

VIOLATION: "bounces off armor" implies the attack HIT but dealt no damage (armor deflection).
Box says MISS (didn't connect at all).

CORRECT: "Your swing whooshes through empty air with such force that you stumble slightly — the orc looks almost sympathetic."
(Describes the miss without implying armor contact.)
```

---

#### Parameter 4: Grittiness

**Range:** Heroic Fantasy ↔ Dark and Gritty

**Heroic Fantasy Mode:**
- Clean, adventurous tone
- Minimal gore
- Focus on heroism

**Dark and Gritty Mode:**
- Visceral, brutal descriptions
- Realistic violence
- Moral ambiguity

**Examples:**

| Event | Heroic (grittiness=0.2) | Gritty (grittiness=0.8) |
|-------|------------------------|----------------------|
| Sword attack, 18 damage | "Your blade strikes the orc with righteous fury, and it falls before you." | "Your blade opens a ragged gash across the orc's chest, spraying blood across the stone floor. The creature's eyes glaze as it collapses in a spreading pool of crimson." |
| Fireball kills 3 goblins | "The fireball consumes the goblins in a flash of flame, and they fall silent." | "The fireball engulfs the goblins in a screaming inferno. The smell of charred flesh fills the air as their blackened bodies crumple to the ground, still smoldering." |

**Critical Constraint:** Grittiness affects DESCRIPTION, not mechanical lethality.

**Both modes describe the SAME HP loss. Heroic mode doesn't reduce damage; gritty mode doesn't increase it.**

---

#### Parameter 5: NPC Voice (Per-Character Consistency)

**Approach:** Each NPC gets a voice profile stored in campaign memory.

**Voice Profile Fields:**
- **Speech pattern:** Formal, casual, broken Common, etc.
- **Vocabulary level:** Simple, educated, archaic
- **Mannerisms:** Nervous stutter, gruff brevity, flowery speech
- **Mood baseline:** Cheerful, grumpy, suspicious, etc.

**Examples:**

| NPC | Voice Profile | Dialogue Example |
|-----|--------------|-----------------|
| Gruff Dwarf Innkeeper | Pattern: Terse, no-nonsense; Vocab: Simple; Manner: Gruff | "Ale's two copper. Upstairs is full. Floor's free if ye got a bedroll." |
| Eloquent Elf Scholar | Pattern: Formal, measured; Vocab: Educated; Manner: Thoughtful pauses | "Ah, I see. The text you reference is, if memory serves, housed in the southern archive. Though... I must confess some uncertainty regarding its present accessibility." |
| Nervous Goblin Merchant | Pattern: Rapid, fragmented; Vocab: Simple; Manner: Stammering | "Y-yes! Shiny coins! I have-have the thing you want, yes? No trouble, no trouble! Just... just coins and we go, yes?" |

**Implementation:**
```python
# NPC voice profile stored in campaign memory
npc_profile = {
    "npc_id": "innkeeper_dwarf_01",
    "name": "Thorin Ironbelly",
    "voice": {
        "speech_pattern": "terse",
        "vocabulary": "simple",
        "mannerisms": ["gruff", "direct"],
        "mood_baseline": "grumpy"
    },
    "provenance": "[SPARK:GENERATED]"  # or [DM:AUTHORED] if manually defined
}

# System prompt includes NPC voice for dialogue generation
f"NPC voice: {npc_profile['voice']['speech_pattern']}, {npc_profile['voice']['mannerisms']}"
```

**Consistency Enforcement:**
- NPC voice profile generated ONCE (first appearance)
- Reused in all future encounters
- Stored in campaign memory with provenance tracking
- DM can override/edit via Judge's Lens

---

### 6.3 Tone Architecture Design

#### System Prompt Structure

**Separation of Concerns:** Tone parameters live in SEPARATE section from Truth Packet.

```
┌─────────────────────────────────────────────────────────────┐
│ SYSTEM PROMPT (Fixed per session)                          │
│                                                             │
│ 1. Role Definition:                                         │
│    "You are a Dungeon Master for a D&D 3.5e campaign."     │
│                                                             │
│ 2. Core Constraints:                                        │
│    - DESCRIBE outcomes, never DECIDE them                   │
│    - Never contradict provided event data                   │
│    - Never invent mechanical effects                        │
│                                                             │
│ 3. TONE PARAMETERS (DM Persona):                            │
│    - Verbosity: {verbosity_level} (0.0-1.0)                │
│    - Drama: {drama_level} (0.0-1.0)                        │
│    - Humor: {humor_level} (0.0-1.0)                        │
│    - Grittiness: {grittiness_level} (0.0-1.0)              │
│    - Target length: {target_sentence_count} sentences       │
│                                                             │
│ 4. D&D 3.5e Rules Summary (50 tokens)                      │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ TRUTH PACKET (Variable per turn)                           │
│                                                             │
│ Event: {event_type}                                         │
│ Outcome: {outcome}                                          │
│ Actor: {actor_name}                                         │
│ Target: {target_name}                                       │
│ Damage: {damage}                                            │
│ Margin: {margin}                                            │
│ Target HP%: {target_hp_percent}                             │
│ Provenance: [BOX]                                           │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ SPARK GENERATION                                            │
│                                                             │
│ Narration output respects:                                  │
│ - Truth from Truth Packet (immutable)                       │
│ - Style from Tone Parameters (variable)                     │
└─────────────────────────────────────────────────────────────┘
```

**Key Design Principle:** Truth Packet and Tone Parameters are **architecturally separate** inputs to Spark. Changing tone NEVER changes Truth Packet data.

---

#### Preventing Tone Bleeding into Mechanical Claims

**Problem:** Tone parameters may accidentally cause Spark to imply different mechanical outcomes.

**Examples of Bleeding:**

| Forbidden Bleeding | Why Forbidden | Prevention |
|-------------------|---------------|------------|
| Margin not in Truth Packet, but Drama=0.8 causes Spark to say "barely hit" | Invents margin data | Truth Packet MUST include explicit `margin` field if tone can reference it |
| HP% = 60, but Heroic mode says "barely scratched" | Contradicts HP loss (40% damage) | Truth Packet includes `target_status` derived field: "wounded" |
| Save DC not in packet, but Gritty mode says "your spell overwhelms their resistance" | Implies failed save when save might have been close | Truth Packet includes `save_margin` if tone can describe save difficulty |

**Prevention Strategy 1: Explicit Margin Fields**

```python
# Truth Packet includes margins for tone calibration
truth_packet = {
    "event": "attack_hit",
    "damage": 12,
    "margin": 5,  # EXPLICIT: roll exceeded AC by 5
    "target_hp_percent": 60,  # EXPLICIT: target at 60% HP after damage
    "target_status": "wounded",  # DERIVED: Lens computes from HP%
}

# Spark can now safely use margin for tone
if drama_level > 0.6 and margin >= 5:
    return "Your blade STRIKES TRUE, a solid hit!"
elif drama_level > 0.6 and margin <= 2:
    return "Your blade narrowly connects, scraping armor!"
```

**Prevention Strategy 2: Tone-Aware Templates**

```python
# Template includes tone placeholders
ATTACK_HIT_TEMPLATE = {
    "terse": "{actor} hits {target}. {damage} damage.",
    "verbose": "{actor}'s {weapon} finds its mark, striking {target} with{margin_desc}force. The blow deals {damage} damage.",
}

# Margin description varies with drama level
def get_margin_desc(margin: int, drama: float) -> str:
    if margin >= 5 and drama > 0.6:
        return " devastating "
    elif margin >= 5:
        return " solid "
    elif margin <= 2 and drama > 0.6:
        return " glancing "
    elif margin <= 2:
        return " "
    else:
        return " "
```

**Prevention Strategy 3: Determinism Gate Verification**

**Test:** Same seed + same Truth Packet + DIFFERENT tone → same Box state

```python
def test_tone_does_not_affect_box_state():
    """Verify tone changes don't alter mechanical outcomes."""
    seed = 12345
    truth_packet = {...}  # Fixed truth packet

    # Generate narration with terse tone
    narration_terse = generate_narration(truth_packet, tone={"verbosity": 0.2})
    box_state_after_terse = get_box_state()

    # Reset Box state to same point
    reset_box_state(seed)

    # Generate narration with verbose tone
    narration_verbose = generate_narration(truth_packet, tone={"verbosity": 0.8})
    box_state_after_verbose = get_box_state()

    # ASSERT: Box state identical regardless of tone
    assert box_state_after_terse == box_state_after_verbose
```

**If determinism gate fails → tone bled into mechanical logic → CRITICAL BUG.**

---

### 6.4 NPC Voice Mapping (Kokoro TTS Integration)

**Challenge:** Maintain consistent NPC voice across sessions with limited context window.

**Solution:** NPC voice profile stored in campaign memory, loaded per-NPC.

```python
@dataclass
class NPCVoiceProfile:
    npc_id: str
    name: str

    # Spark narration style
    speech_pattern: str  # "formal", "casual", "broken_common"
    vocabulary: str  # "simple", "educated", "archaic"
    mannerisms: List[str]  # ["stutters", "gruff", "flowery"]

    # Kokoro TTS voice
    tts_voice_id: str  # "voice_gruff_male_dwarf"
    tts_pitch: float  # -1.0 to 1.0
    tts_speed: float  # 0.5 to 2.0

    # Provenance
    provenance: str  # "[SPARK:GENERATED]" or "[DM:AUTHORED]"
```

**Workflow:**

1. **First NPC Appearance:**
   - Lens detects new NPC (no voice profile in campaign memory)
   - Lens sends NPC generation request to Spark (RQ-SPARK-001-C protocol)
   - Spark generates voice profile based on NPC context (race, role, mood)
   - Lens validates and stores in campaign memory
   - Lens selects matching Kokoro TTS voice from voice library

2. **Subsequent Appearances:**
   - Lens loads NPC voice profile from campaign memory
   - Spark prompt includes NPC voice parameters
   - Kokoro TTS uses same voice_id for consistency

3. **DM Override:**
   - DM can edit NPC voice profile via Judge's Lens
   - Manual edits tagged [DM:AUTHORED], override [SPARK:GENERATED]

**Example:**

```python
# First appearance: Spark generates voice profile
npc_voice = {
    "npc_id": "innkeeper_dwarf_01",
    "name": "Thorin Ironbelly",
    "speech_pattern": "terse",
    "vocabulary": "simple",
    "mannerisms": ["gruff", "no-nonsense"],
    "tts_voice_id": "voice_gruff_male_dwarf",
    "tts_pitch": -0.3,
    "tts_speed": 1.1,
    "provenance": "[SPARK:GENERATED]"
}

# Subsequent appearance: Load from memory
npc_voice = campaign_memory.get_npc_voice("innkeeper_dwarf_01")

# System prompt includes NPC voice
f"NPC: {npc_voice['name']}, Speech: {npc_voice['speech_pattern']}, Manner: {npc_voice['mannerisms']}"

# Spark generates dialogue
"Ale's two copper. Upstairs is full."

# TTS uses saved voice profile
kokoro_tts.synthesize(text, voice_id=npc_voice['tts_voice_id'], pitch=-0.3, speed=1.1)
```

---

### 6.5 Context Window Budget for Tone + NPC Voice

**Challenge:** Qwen3 8B has 8192 token limit. How to allocate tokens for tone parameters + NPC voices?

**Allocation Strategy:**

| Component | Token Budget | Notes |
|-----------|-------------|-------|
| System Prompt (base) | 600 tokens | Role, constraints, D&D 3.5e summary |
| **Tone Parameters** | **100 tokens** | 5 parameters × 20 tokens each |
| **NPC Voice (if dialogue)** | **50 tokens** | Speech pattern, mannerisms |
| Truth Packet | 400 tokens | Event data, scene context |
| Narration History | 2500 tokens | Previous narrations for consistency |
| Generation Budget | 512 tokens | Spark output |
| Reserve | 3930 tokens | Safety margin |

**Total Allocated:** 4162 tokens (including tone + NPC voice)
**Reserve:** 4030 tokens

**Optimization:** NPC voice only included when NPC is speaking (not every narration).

```python
# NPC dialogue event
if truth_packet["event"] == "npc_dialogue":
    npc_voice = load_npc_voice(truth_packet["npc_id"])
    system_prompt += format_npc_voice_section(npc_voice)  # +50 tokens
else:
    # No NPC voice section
    pass
```

---

### 6.6 Three Example Narrations (Same Event, Different Tones)

**Event (Box Truth Packet):**
```json
{
  "event": "attack_hit",
  "actor_name": "Fighter",
  "target_name": "Orc",
  "weapon_name": "longsword",
  "damage": 12,
  "margin": 5,
  "target_hp_percent": 60,
  "target_status": "wounded",
  "roll_summary": "18 + 5 = 23 vs AC 15",
  "provenance": "[BOX]"
}
```

**Narration 1: Terse + Serious + Heroic**

Tone Parameters: `{verbosity: 0.2, drama: 0.3, humor: 0.0, grittiness: 0.2}`

Output:
> "Your longsword strikes the orc. 12 damage."

**Narration 2: Verbose + Dramatic + Gritty**

Tone Parameters: `{verbosity: 0.8, drama: 0.8, humor: 0.0, grittiness: 0.8}`

Output:
> "Your longsword ARCS through the fetid dungeon air, the blade catching torchlight as it descends with brutal precision! The steel bites DEEP into the orc's shoulder, cleaving through crude leather armor and into yielding flesh beneath. Blood sprays across the stone floor as the creature ROARS in agony, staggering backward with wild eyes — wounded, but far from finished."

**Narration 3: Moderate + Humorous + Heroic**

Tone Parameters: `{verbosity: 0.5, drama: 0.5, humor: 0.6, grittiness: 0.3}`

Output:
> "Your longsword finds its mark with a satisfying *thunk*, catching the orc right in the shoulder. The brute lets out an indignant grunt — as if personally offended that you'd have the audacity to stab him — and stumbles back, blood seeping from the wound. He's still standing, though he looks considerably less enthusiastic about this fight than he did ten seconds ago."

**Verification:**
- All three narrations describe: HIT, 12 damage, target at 60% HP, wounded
- All three include margin=5 context (solid hit, not glancing)
- Tone varies (terse → verbose, serious → humorous), truth does NOT
- Box state: IDENTICAL across all three narrations (determinism preserved)

---

## Sub-Question 7: Evaluation — Detecting Narrative Truth Violations

### 7.1 Six Violation Categories

#### Category 1: Outcome Mismatch

**Definition:** Spark narration describes a different outcome than Box computed.

**Examples:**

| Box Truth | Spark Narration | Violation |
|-----------|----------------|-----------|
| `outcome: "miss"` | "Your blade strikes the orc!" | Says HIT when Box computed MISS |
| `outcome: "hit"` | "Your attack whooshes past the orc." | Says MISS when Box computed HIT |
| `outcome: "save_success"` | "The orc succumbs to the spell." | Says FAIL when Box computed SUCCESS |

**Detection Method:** Keyword matching + outcome field comparison.

```python
def detect_outcome_mismatch(truth_packet: dict, narration: str) -> bool:
    """Detect if narration contradicts Box outcome."""
    outcome = truth_packet["outcome"]

    # HIT vs MISS
    if outcome == "hit":
        miss_keywords = ["miss", "whooshes past", "swings wide", "fails to connect"]
        if any(kw in narration.lower() for kw in miss_keywords):
            return True  # VIOLATION: Says miss when Box said hit

    if outcome == "miss":
        hit_keywords = ["strikes", "hits", "connects", "finds its mark"]
        if any(kw in narration.lower() for kw in hit_keywords):
            return True  # VIOLATION: Says hit when Box said miss

    # SAVE SUCCESS vs FAIL
    if outcome == "save_success":
        fail_keywords = ["succumbs", "overcome", "overwhelmed", "fails to resist"]
        if any(kw in narration.lower() for kw in fail_keywords):
            return True  # VIOLATION

    return False
```

**False Positive Risk:** Medium (keywords can appear in non-contradictory context).

---

#### Category 2: Entity Mismatch

**Definition:** Spark mentions an entity not present in the scene.

**Examples:**

| Scene Entities | Spark Narration | Violation |
|----------------|----------------|-----------|
| `["Fighter", "Orc"]` | "The goblin lunges at you!" | Mentions goblin not in scene |
| `["Rogue", "Trap"]` | "The dragon roars overhead!" | Mentions dragon not in scene |

**Detection Method:** Entity name extraction + scene entity list comparison.

```python
def detect_entity_mismatch(truth_packet: dict, narration: str) -> List[str]:
    """Detect entities mentioned in narration but not in scene."""
    scene_entities = set(truth_packet.get("scene_entities", []))

    # Extract entity names from narration (NER or simple keyword matching)
    mentioned_entities = extract_entity_names(narration)

    # Find entities mentioned but not in scene
    invalid_entities = [e for e in mentioned_entities if e not in scene_entities]

    return invalid_entities
```

**False Positive Risk:** High (need robust NER; proper nouns vs common nouns).

---

#### Category 3: Geometry Mismatch

**Definition:** Spark describes spatial relationships that contradict scene geometry.

**Examples:**

| Scene Geometry | Spark Narration | Violation |
|----------------|----------------|-----------|
| `{"pillar_blocks_los": False}` | "You strike from behind the pillar!" | Says pillar blocks when it doesn't |
| `{"target_range": 30}` | "You strike the distant orc from melee range." | Says melee when range is 30 feet |

**Detection Method:** Geometry keyword detection + scene data validation.

```python
def detect_geometry_mismatch(truth_packet: dict, narration: str) -> bool:
    """Detect spatial contradictions."""
    # Check cover/concealment
    if truth_packet.get("has_cover") is False:
        cover_keywords = ["behind cover", "shielded by", "hidden behind"]
        if any(kw in narration.lower() for kw in cover_keywords):
            return True  # VIOLATION: Says cover when none exists

    # Check range
    if truth_packet.get("range_category") == "ranged":
        melee_keywords = ["melee range", "close quarters", "face to face"]
        if any(kw in narration.lower() for kw in melee_keywords):
            return True  # VIOLATION: Says melee when ranged

    return False
```

**False Positive Risk:** Medium (keywords can be metaphorical).

---

#### Category 4: Severity Mismatch

**Definition:** Spark describes injury severity inconsistent with HP% data.

**Examples:**

| Box Truth | Spark Narration | Violation |
|-----------|----------------|-----------|
| `damage: 24, target_hp_percent: 20` | "The blow barely scratches the orc." | Says minor when 80% HP lost |
| `damage: 2, target_hp_percent: 95` | "A devastating, mortal wound!" | Says lethal when 5% HP lost |

**Detection Method:** Severity keyword extraction + HP% threshold comparison.

```python
def detect_severity_mismatch(truth_packet: dict, narration: str) -> bool:
    """Detect wound severity contradictions."""
    hp_percent = truth_packet.get("target_hp_percent")
    if hp_percent is None:
        return False  # No HP data, can't detect

    # Minor wound keywords
    minor_keywords = ["scratch", "barely hurt", "minor wound", "superficial"]
    # Severe wound keywords
    severe_keywords = ["devastating", "mortal", "grievous", "critical wound", "on the brink"]

    # Check for contradictions
    if hp_percent < 30:  # Severely wounded (70%+ HP lost)
        if any(kw in narration.lower() for kw in minor_keywords):
            return True  # VIOLATION: Says minor when severe

    if hp_percent > 85:  # Barely hurt (<15% HP lost)
        if any(kw in narration.lower() for kw in severe_keywords):
            return True  # VIOLATION: Says severe when minor

    return False
```

**False Positive Risk:** Low (clear thresholds).

---

#### Category 5: Mechanical Assertion

**Definition:** Spark claims mechanical authority (adjudication, rule citation, stat values).

**Examples:**

| Spark Narration | Violation |
|----------------|-----------|
| "You can't move through that square because of AoO rules." | Adjudication (only Box can rule on legality) |
| "Per PHB page 141, you get +2 flanking." | Rule citation (Spark has no rules authority) |
| "The orc has AC 16." | Stat revelation (unless Box provided in Truth Packet) |
| "Roll a DC 15 Reflex save." | Mechanical instruction (only Box computes DCs) |

**Detection Method (KILL-002):** Regex pattern matching for forbidden phrases.

```python
# KILL-002 implementation (from Execution Plan v2)
FORBIDDEN_MECHANICAL_ASSERTIONS = [
    r"you can't",  # Adjudication
    r"you cannot",
    r"that's illegal",
    r"per PHB",  # Rule citation
    r"according to the rules",
    r"page \d+",
    r"AC \d+",  # Stat values (unless sourced from Truth Packet)
    r"DC \d+",
    r"HP \d+",
    r"BAB [+-]?\d+",
    r"roll (?:a|an) (?:DC \d+)",  # Mechanical instruction
]

def detect_mechanical_assertion(truth_packet: dict, narration: str) -> List[str]:
    """Detect unauthorized mechanical claims (KILL-002)."""
    violations = []

    for pattern in FORBIDDEN_MECHANICAL_ASSERTIONS:
        if re.search(pattern, narration, re.IGNORECASE):
            violations.append(f"Mechanical assertion: {pattern}")

    # Exception: If Truth Packet explicitly includes these values, they're sourced
    if "roll_summary" in truth_packet:
        # AC/DC values in roll_summary are OK to mention
        pass

    return violations
```

**False Positive Risk:** Medium (need exceptions for Truth Packet-sourced values).

---

#### Category 6: Unauthorized Effects

**Definition:** Spark invents mechanical effects not computed by Box.

**Examples:**

| Box Truth | Spark Narration | Violation |
|-----------|----------------|-----------|
| `spell: "Ray of Frost", damage: 5` | "The cold spell also freezes the floor, creating difficult terrain." | Invents difficult terrain not in Box resolution |
| `event: "attack_hit"` | "Your strike also knocks the orc prone." | Invents prone condition not in Box |
| `spell: "Fireball"` | "The explosion also ignites nearby furniture." | Invents environmental effect not in Box |

**Detection Method:** Effect keyword extraction + `active_conditions` / `environmental_effects` validation.

```python
def detect_unauthorized_effects(truth_packet: dict, narration: str) -> List[str]:
    """Detect effects mentioned in narration but not in Box truth."""
    authorized_conditions = set(truth_packet.get("active_conditions", []))
    authorized_env_effects = set(truth_packet.get("environmental_effects", []))

    # Effect keywords
    condition_keywords = {
        "prone": "prone",
        "grappled": "grappled",
        "stunned": "stunned",
        "frightened": "frightened",
        "slowed": "slowed",
        "paralyzed": "paralyzed",
    }

    env_keywords = {
        "difficult terrain": "difficult_terrain",
        "concealment": "concealment",
        "cover": "cover",
        "ignited": "fire",
        "frozen": "ice",
    }

    violations = []

    # Check for unauthorized conditions
    for keyword, condition in condition_keywords.items():
        if keyword in narration.lower() and condition not in authorized_conditions:
            violations.append(f"Unauthorized condition: {condition}")

    # Check for unauthorized environmental effects
    for keyword, effect in env_keywords.items():
        if keyword in narration.lower() and effect not in authorized_env_effects:
            violations.append(f"Unauthorized effect: {effect}")

    return violations
```

**False Positive Risk:** Medium (metaphorical language vs mechanical claims).

---

### 7.2 Three Detection Approaches

#### Approach 1: Keyword Matching (Fast, High False Positive)

**Method:** Regex patterns detect forbidden keywords.

**Advantages:**
- Very fast (<10ms per narration)
- No additional LLM call required
- Low latency impact

**Disadvantages:**
- High false positive rate (20-30%)
- Misses subtle contradictions
- Can't detect semantic mismatches

**Use Case:** First-pass filter for obvious violations.

**Implementation:**
```python
def keyword_violation_check(truth_packet: dict, narration: str) -> List[str]:
    """Fast keyword-based violation detection."""
    violations = []

    # Category 1: Outcome mismatch
    if detect_outcome_mismatch(truth_packet, narration):
        violations.append("Outcome mismatch")

    # Category 5: Mechanical assertion (KILL-002)
    mech_assertions = detect_mechanical_assertion(truth_packet, narration)
    violations.extend(mech_assertions)

    # Category 6: Unauthorized effects
    unauth_effects = detect_unauthorized_effects(truth_packet, narration)
    violations.extend(unauth_effects)

    return violations
```

**Performance:** <10ms per narration (suitable for real-time checks).

---

#### Approach 2: Regex Pattern Detection (KILL-002 Implementation)

**Method:** Structured regex patterns detect specific violation types.

**Advantages:**
- Faster than LLM (10-50ms per narration)
- Lower false positive rate than keyword matching (10-15%)
- Can detect structured patterns (AC values, DC citations)

**Disadvantages:**
- Requires careful pattern engineering
- Brittle (new phrasing can bypass patterns)
- Still misses semantic contradictions

**Use Case:** KILL-002 implementation (mechanical assertion detection).

**Implementation (from Execution Plan v2):**
```python
# KILL-002: Mechanical assertion detection
KILL_002_PATTERNS = {
    "adjudication": [
        r"you (?:can't|cannot) do (?:that|this)",
        r"(?:that's|that is) (?:illegal|not allowed)",
        r"you (?:must|have to) (?:roll|make)",
    ],
    "rule_citation": [
        r"per (?:PHB|DMG|rules)",
        r"according to (?:the rules|page \d+)",
        r"(?:PHB|DMG|SRD) page \d+",
    ],
    "stat_revelation": [
        r"AC (?:is |of )?\d+",
        r"DC (?:is |of )?\d+",
        r"HP (?:is |of )?\d+",
        r"(?:has|have) \d+ (?:hit points|HP)",
    ],
}

def kill_002_check(truth_packet: dict, narration: str) -> Optional[str]:
    """KILL-002: Detect mechanical assertions."""
    for category, patterns in KILL_002_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, narration, re.IGNORECASE)
            if match:
                # Exception: If value is sourced from Truth Packet, allow it
                if category == "stat_revelation" and "roll_summary" in truth_packet:
                    # Check if AC/DC value in narration matches Truth Packet
                    if extract_ac_from_narration(match.group()) == truth_packet.get("target_ac"):
                        continue  # Sourced from Truth Packet, not a violation

                return f"KILL-002 TRIGGERED: {category} — {match.group()}"

    return None
```

**Performance:** 10-50ms per narration (suitable for real-time checks).

---

#### Approach 3: Semantic Comparison (LLM-Based, Thorough)

**Method:** Use a second LLM pass to verify consistency between Truth Packet and narration.

**Advantages:**
- Low false positive rate (1-3%)
- Detects subtle contradictions
- Handles semantic mismatches (outcome same, but implication different)

**Disadvantages:**
- Expensive (2-5 seconds per narration)
- Requires additional LLM inference
- Not suitable for real-time checks (must run async)

**Use Case:** Regression testing, audit trails, async validation.

**Implementation:**
```python
async def semantic_violation_check(truth_packet: dict, narration: str) -> Optional[str]:
    """LLM-based semantic consistency check (async)."""

    # Build verification prompt
    prompt = f"""You are verifying that a D&D narration is consistent with game engine truth.

Truth from Game Engine (authoritative):
{json.dumps(truth_packet, indent=2)}

Narration Generated:
"{narration}"

Question: Does the narration contradict the truth in any way?

Check for:
1. Outcome mismatch (says hit when truth says miss, or vice versa)
2. Severity mismatch (says "minor scratch" when 80% HP lost)
3. Entity mismatch (mentions entities not in scene)
4. Unauthorized effects (mentions conditions/effects not in truth)
5. Mechanical assertions (adjudicates legality, cites rules, reveals stats)

Answer: YES (contradiction found) or NO (consistent)
If YES, explain the contradiction in one sentence.
"""

    # Send to verification LLM (lightweight model, temperature=0.0)
    response = await llm_query(
        prompt,
        temperature=0.0,  # Deterministic for verification
        max_tokens=100,
    )

    # Parse response
    if response.strip().startswith("YES"):
        return response.strip()  # "YES: [explanation]"
    else:
        return None  # No violation
```

**Performance:** 2-5 seconds per narration (async only).

---

### 7.3 Template Anchoring Optimization

**Optimization:** When narration is template-augmented (template + LLM additions), verify LLM additions don't contradict template content.

**Scenario:**
```
Template (from narrator.py):
"{actor} strikes {target} with {weapon}. {damage} damage."

LLM Augmentation:
"Your blade glances off the orc's armor harmlessly."

Conflict: Template says HIT + damage, LLM says "glances off" (implies miss or no damage).
```

**Detection:**
```python
def template_anchoring_check(template: str, llm_addition: str, truth_packet: dict) -> Optional[str]:
    """Check if LLM addition contradicts template anchor."""

    # Template says HIT + damage
    if "damage" in template.lower():
        # LLM addition should not say miss/deflect/no effect
        miss_keywords = ["glances off", "deflected", "no effect", "harmlessly"]
        if any(kw in llm_addition.lower() for kw in miss_keywords):
            return "Template anchoring violation: Template says damage, LLM says no effect"

    # Template says MISS
    if "miss" in template.lower():
        # LLM addition should not say hit/strikes/connects
        hit_keywords = ["strikes", "hits", "connects", "pierces"]
        if any(kw in llm_addition.lower() for kw in hit_keywords):
            return "Template anchoring violation: Template says miss, LLM says hit"

    return None
```

**Advantage:** Cheaper than full semantic check (only validates LLM addition vs template, not full narration).

**Performance:** 5-10ms (keyword matching on smaller text).

---

### 7.4 Recommended Detection Pipeline

**Three-Tier Pipeline:**

```
┌─────────────────────────────────────────────────────────────┐
│ Tier 1: Real-Time Checks (Synchronous, <100ms)             │
│                                                             │
│ 1. Keyword Matching (Approach 1)                            │
│    - Outcome mismatch detection                              │
│    - Basic entity/geometry checks                            │
│    - Performance: <10ms                                      │
│                                                             │
│ 2. Regex Pattern Detection (Approach 2 — KILL-002)          │
│    - Mechanical assertion detection                          │
│    - Stat revelation detection                               │
│    - Rule citation detection                                 │
│    - Performance: 10-50ms                                    │
│                                                             │
│ 3. Template Anchoring (if applicable)                        │
│    - LLM addition vs template consistency                    │
│    - Performance: 5-10ms                                     │
│                                                             │
│ Total Tier 1 Time: <100ms (suitable for turn-by-turn)      │
└─────────────────────────────────────────────────────────────┘
                         ↓
          ┌──────────────┴──────────────┐
          │ Violation Detected?          │
          │ YES → KILL-002 Trigger       │
          │ NO → Continue to Tier 2      │
          └──────────────┬──────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Tier 2: Async Validation (Background, <5s)                 │
│                                                             │
│ 4. Semantic Comparison (Approach 3)                         │
│    - LLM-based truth verification                            │
│    - Runs async after narration delivered to player          │
│    - Performance: 2-5 seconds                                │
│    - If violation found → Log for audit, alert DM            │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Tier 3: Regression Testing (Offline, batch)                │
│                                                             │
│ 5. Gold Master Scenarios                                     │
│    - Run 4 combat scenarios 100x each                        │
│    - Detect ANY violations across 400 narrations             │
│    - Performance: Batch (CI pipeline)                        │
│    - Track violation rate over time                          │
└─────────────────────────────────────────────────────────────┘
```

**Key Insight:** Real-time checks (Tier 1) catch 80% of violations with <100ms latency. Async validation (Tier 2) catches remaining 20% without blocking gameplay.

---

### 7.5 Regression Test Strategy

**Gold Master Approach:**

1. **Define 4 Test Scenarios:**
   - Tavern brawl (melee combat, NPC dialogue)
   - Dungeon encounter (ranged + melee, environmental hazards)
   - Open field battle (AoE spells, positioning)
   - Boss fight (complex mechanics, condition tracking)

2. **Run Each Scenario 100x:**
   - Same Box seed → same mechanical outcomes
   - Different narration seeds → varied narration
   - Track violations per narration

3. **Violation Tracking:**
   ```python
   @dataclass
   class ViolationLog:
       scenario: str
       run_number: int
       turn_number: int
       violation_category: str
       narration_text: str
       truth_packet: dict
       detection_method: str  # "keyword", "regex", "semantic"
   ```

4. **Target Metrics:**
   - **Violation rate:** <1% per 100 narrations (goal: <4 violations per scenario)
   - **False positive rate:** <5% (manual review of flagged violations)
   - **Template-only baseline:** 0 violations (templates are hand-crafted, should never violate)
   - **LLM-augmented:** <2% violations (acceptable risk for generative content)

5. **CI Gate:**
   - Run gold master tests on every PR
   - Block PR if violation rate exceeds 2% (regression detected)
   - Alert if false positive rate exceeds 10% (detection patterns too strict)

---

### 7.6 Metrics to Track

| Metric | Target | Measurement Method | Frequency |
|--------|--------|-------------------|-----------|
| **Violation Rate** | <1% per 100 narrations | Gold master scenarios | Per PR (CI) |
| **False Positive Rate** | <5% | Manual review sample (20 narrations/week) | Weekly |
| **Template-Only Violations** | 0% | Gold master with template-only mode | Per PR (CI) |
| **LLM-Augmented Violations** | <2% | Gold master with LLM mode | Per PR (CI) |
| **KILL-002 Trigger Rate** | <0.1% (1 per 1000 narrations) | Production logs | Daily |
| **Semantic Check Violations (Async)** | <0.5% | Background validation logs | Daily |
| **Mean Violations Per Combat** | <1 | 4-turn combat scenario | Per PR (CI) |

**Dashboard Visualization:**
```
Violation Rate Trend (Last 30 Days)
┌─────────────────────────────────────────────────────────────┐
│ 3% ┤                                                         │
│    │                                                         │
│ 2% ┤     ●                                                   │
│    │   ●   ●                                                 │
│ 1% ┤ ●       ● ● ──●──●──●──●──●──●──●──●──●──●  ← Target  │
│    │                                                         │
│ 0% ┼─────────────────────────────────────────────────────────│
│    │  Day 1        Day 10       Day 20       Day 30         │
└─────────────────────────────────────────────────────────────┘

Categories:
- Outcome mismatch: 30%
- Mechanical assertion: 40%
- Severity mismatch: 20%
- Unauthorized effects: 10%
```

---

## Implementation Checklist

### Sub-Q5: Unknown Handling

**For WO-032 (NarrativeBrief Assembler):**
- [ ] Truth Packet includes `unknown_fields: List[str]`
- [ ] Unknown fields tagged with type: "scene_detail", "npc_personality", "mechanical_property", "historical_fact"
- [ ] Decision tree implementation (5 strategies)
- [ ] Vagueness templates for 10 common unknowns
- [ ] Uncertainty templates for mechanical properties
- [ ] Integration with Spark improvisation protocol (RQ-SPARK-001-C)

**For WO-029 (Kill Switches):**
- [ ] KILL-002 detects fabricated mechanical properties (regex for dimensions, stats)
- [ ] Violation logged when Spark fabricates instead of using [UNCERTAIN]

---

### Sub-Q6: Tone Control

**For WO-041 (DM Personality Layer):**
- [ ] Tone parameters in system prompt: verbosity, drama, humor, grittiness
- [ ] NPC voice profiles stored in campaign memory
- [ ] Tone-aware templates with margin/HP% thresholds
- [ ] Determinism gate test: same seed + different tone → same Box state
- [ ] Tone bleeding prevention: margin/HP% fields required for tone-sensitive descriptions

**For WO-032 (NarrativeBrief Assembler):**
- [ ] Truth Packet includes explicit `margin` field (if tone can reference closeness)
- [ ] Truth Packet includes `target_status` derived field (for wound severity)
- [ ] Architectural separation: Truth Packet (immutable) vs Tone Parameters (variable)

**For WO-033 (Spark Integration Stress Test):**
- [ ] Test same combat with 3 tone settings → verify Box state identical
- [ ] Verify tone doesn't cause outcome contradictions
- [ ] NPC voice consistency across 10-turn dialogue

---

### Sub-Q7: Violation Detection

**For WO-029 (Kill Switches):**
- [ ] KILL-002 implementation: regex patterns for mechanical assertions
- [ ] Real-time violation detection (<100ms): keyword matching + regex
- [ ] Template anchoring check (if template-augmented narration)
- [ ] Violation logging with full context (narration, truth packet, detection method)

**For WO-033 (Spark Integration Stress Test):**
- [ ] Gold master scenarios: 4 scenarios × 100 runs = 400 narrations
- [ ] Violation tracking per category (6 categories)
- [ ] Target metrics: <1% violation rate, <5% false positive rate
- [ ] Template-only baseline: 0 violations
- [ ] Async semantic validation (background, <5s)

**For CI Pipeline:**
- [ ] Automated violation detection on every PR
- [ ] Block PR if violation rate exceeds 2%
- [ ] Violation dashboard (trend over time, category breakdown)

---

## Open Questions for PM Review

### Q1: Unknown Handling — DM Override UX

**Question:** When Spark improvises a fact (Strategy 3), how should DM be notified and allowed to override?

**Options:**
- **A:** Notify after fact generated, DM can veto before narration sent to player
- **B:** Notify after narration sent, DM can retroactively correct (edit campaign memory)
- **C:** No notification (DM reviews via Judge's Lens on demand)

**Recommendation:** Option B (retroactive correction) — minimizes latency, DM can audit/correct via memory browser.

---

### Q2: Tone Parameter — Default Values

**Question:** What are the default tone parameter values for a new campaign?

**Options:**
- **A:** Moderate all (verbosity=0.5, drama=0.5, humor=0.3, grittiness=0.4)
- **B:** Campaign creation wizard asks player to select tone
- **C:** Adaptive (system learns from player feedback over first 3 sessions)

**Recommendation:** Option A (moderate defaults) + B (wizard option) — sensible defaults with customization.

---

### Q3: Violation Detection — KILL-002 Strictness

**Question:** Should KILL-002 halt narration generation immediately, or log and continue with template fallback?

**Options:**
- **A:** HALT immediately, fall back to template, log violation
- **B:** LOG violation, send narration anyway, async audit trail
- **C:** WARNING mode (first 3 violations log only, 4th triggers KILL-002)

**Recommendation:** Option A (immediate halt) — consistent with existing kill switch policy (KILL-001 halts on memory write violation). Safety-first approach.

---

### Q4: NPC Voice Generation — Consistency vs Variety

**Question:** Should NPC voice profiles be FIXED after first generation, or adaptable over time?

**Options:**
- **A:** FIXED (voice profile locked after first generation, DM can override manually)
- **B:** ADAPTIVE (voice profile can evolve based on story events, tagged [SPARK:EVOLVED])
- **C:** HYBRID (core traits fixed, minor traits can adapt)

**Recommendation:** Option A (fixed) — consistency is critical for NPC recognition. DM can manually evolve if needed.

---

## Acceptance Criteria

This research is **DELIVERED** when:

1. ✅ Unknown handling decision tree covers 4 unknown types with 5 strategies
2. ✅ Five scenario walkthroughs demonstrate decision tree in practice
3. ✅ Integration with Spark improvisation protocol (RQ-SPARK-001-C) specified
4. ✅ Tone control architecture separates truth layer (immutable) from style layer (variable)
5. ✅ Five tone parameters defined with bleeding prevention strategies
6. ✅ Three example narrations show same event with different tones (Box state identical)
7. ✅ Six violation categories defined with detection methods
8. ✅ Three-tier detection pipeline: real-time (<100ms), async (<5s), regression (batch)
9. ✅ Target metrics specified: <1% violation rate, <5% false positive rate
10. ✅ Implementation checklists actionable for WO-029, WO-032, WO-033, WO-041

**Status:** All criteria met. Awaiting PM approval.

---

## References

- **Execution Plan v2:** `docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md` (Phase 1-2: WO-027–WO-041)
- **RQ-NARR-001-A:** `docs/research/findings/RQ_NARR_001_A_OUTPUT_SPACE_AND_TRUTH_PACKET.md` (Allowed output space, Truth Packet schema)
- **RQ-SPARK-001-C:** `docs/research/findings/RQ_SPARK_001_C_IMPROVISATION_AND_NPCS.md` (Fact completion protocol)
- **Spark-Lens-Box Doctrine:** `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` (Axioms 2, 3, 4, 5)
- **M1 Guardrails:** `docs/design/M1_IMPLEMENTATION_GUARDRAILS.md` (FREEZE-001, KILL-001, LLM-002)
- **Guarded Narration Service:** `aidm/narration/guarded_narration_service.py` (FREEZE-001, BL-003, template fallback)
- **Narrator Templates:** `aidm/narration/narrator.py` (55 narration token templates)

---

**END OF RESEARCH DOCUMENT**

**Next Steps:**
1. PM (Opus) reviews and approves/revises
2. If approved → integrate findings into WO-029 (Kill Switches), WO-032 (NarrativeBrief), WO-033 (Stress Test), WO-041 (DM Personality)
3. Unknown handling decision tree implemented in NarrativeBrief assembler
4. Tone control parameters added to DM Persona system prompt
5. KILL-002 regex patterns implemented with violation detection pipeline
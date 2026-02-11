# Spark/Lens/Box Operational Architecture
## Interface Contracts, Data Flow, and the Lens as Focus System

**Document Type:** Architecture Specification (Binding Amendment)
**Document ID:** SLB-ARCH-001
**Version:** 1.0.0
**Status:** BINDING
**Date:** 2026-02-11
**Authority:** Thunder (Product Owner) + Opus (Acting PM)
**Parent Doctrine:** `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` (conceptual constitution)
**Amends:** Lens definition — upgrades from "stateless presentation logic" to "stateful focus system"
**Preserves:** All trust, authority, provenance, and separation axioms from parent doctrine

---

## 1. Purpose

This specification defines the **operational architecture** of the Spark/Lens/Box system — how the three layers communicate, what data flows between them, and the contracts governing each interface.

The parent doctrine (`SPARK_LENS_BOX_DOCTRINE.md`) establishes the conceptual constitution: who has authority, what each layer may and may not do, and how trust is preserved. This document builds on that foundation with the engineering details necessary for implementation.

### 1.1 Critical Amendment: The Lens Is Stateful

The parent doctrine defines the Lens as "stateless presentation logic." This was a first-draft simplification. Product Owner whiteboarding (Session 002, 2026-02-11) established that the Lens is significantly more:

> "That lens system is what's like keeping track of the campaign. It's keeping track of the session notes. It's keeping track of what happened yesterday, a year ago, 10 years ago. It needs to have a very structured and rigorous logging documenting indexing and searchable record history so that the LLM is never overpowered."
> — Thunder (Product Owner)

**The Lens is a stateful focus system.** It holds campaign memory, player model, alignment evidence, environmental data, and session continuity. It is the shared data membrane that both the Spark and the Box interact with — but never each other.

**What this does NOT change:**
- The Lens still cannot invent mechanical authority (Box-exclusive)
- The Lens still cannot refuse Spark generation (Spark is pre-law)
- The Lens still preserves provenance labels
- All trust/authority axioms from the parent doctrine remain binding

**What this DOES change:**
- The Lens is no longer "stateless" — it maintains persistent, indexed, queryable state
- The Lens is the data layer between Spark and Box — neither talks to the other directly
- The Lens assembles context windows for the Spark (focus function)
- The Lens serves environmental/world data to the Box on demand (data function)

---

## 2. The Three Systems

### 2.1 The Box (D&D 3.5e Engine)

**What it is:** The deterministic rules engine. Already built. 2003+ tests passing.

**What it owns:**
- All game rules (RAW D&D 3.5e)
- All dice resolution
- All game state (WorldState, initiative, HP, conditions, positions)
- All mechanical validation (action legality, prerequisite checks)
- The battle map (positions, movement, cover, line of sight, AoE)

**What it does:**
- Validates actions against RAW
- Resolves combat (attack rolls, saves, damage)
- Enforces movement rules, threatened squares, AoO triggers
- Calculates cover geometry (character height vs object height vs attacker angle)
- Tracks object properties (material, hardness, HP, destructibility)
- Emits events for everything it does (event-sourced)
- Presents go/no-go options (valid actions available to a character)

**What it reads from the Lens:**
- Environmental data (object dimensions, materials, positions)
- Character physical properties (height, size category)
- Scene composition (what objects exist in the current area)

**What it writes to the Lens:**
- Event stream (every mechanical resolution, with full provenance)
- Go/no-go option sets (valid actions for the current game state)
- State snapshots (current WorldState for context assembly)

**What it NEVER does:**
- Generate narration (Spark does that)
- Talk to the Spark directly (always through the Lens)
- Make rulings without RAW citation
- Adapt tone or presentation

---

### 2.2 The Spark (LLM)

**What it is:** Raw generative intelligence. A commodity. Rented, configured, swappable.

**What it owns:** Nothing. It generates, it doesn't own.

**What it does:**
- Generates narration for game events
- Interprets player intent (natural language → structured intent)
- Creates world-knowledge (scene descriptions with physical properties)
- Produces NPC dialogue, atmospheric descriptions, story beats
- Generates images (via image pipeline) and audio (via audio pipeline)
- Provides common-sense world knowledge (a table is ~3.5 feet tall, wood burns)

**What it reads from the Lens:**
- Focused context windows (assembled by the Lens for each call)
- Player model parameters (verbosity preference, experience level, tone)
- Campaign memory slices (relevant history for the current moment)
- Box go/no-go options (what actions are mechanically available)

**What it writes to the Lens:**
- Narration text (for delivery to the player)
- Intent interpretations (player said X, Spark thinks they mean Y)
- World-knowledge (scene objects with dimensions, materials, positions)
- Generated assets (images, audio) for indexing

**What it NEVER does:**
- Assert mechanical authority (only the Box does that)
- Mutate game state (only the Box does that through event-sourcing)
- Talk to the Box directly (always through the Lens)
- Refuse generation based on policy (refusal is LENS post-generation gating)

---

### 2.3 The Lens (Focus System)

**What it is:** The crystal ball. The glass membrane. The product we're building.

> "Think of this as a crystal ball. A magical crystal ball where the intelligence lives beneath the glass."
> — Thunder (Product Owner)

The Lens is the only system that talks to both the Spark and the Box. It is the membrane through which they interact. Neither reaches through to the other.

**What it owns:**
- Campaign Memory Index (entities, events, locations, NPCs, timelines)
- Player Model (5 dimensions: experience, pacing, explanation depth, tone, modality)
- Alignment Tracker (continuous 2-axis tracking with evidence chains)
- Environmental Data Index (scene objects with physical properties, indexed and queryable)
- Session Continuity (where we left off, what happened last time)
- Context Assembler (builds minimum-necessary context windows for Spark calls)

**What it does:**

**Focus function (Lens → Spark):**
- Assembles focused context windows for each Spark call
- Injects player model parameters into prompts
- Queries campaign memory and feeds relevant slices to Spark
- Translates Box go/no-go options into Spark-readable context
- Prevents Spark overload by filtering irrelevant information

**Data function (Lens → Box):**
- Stores and indexes world-knowledge from the Spark
- Serves environmental data to the Box on demand (object dimensions, materials)
- Translates Spark-generated scene descriptions into structured data the Box can query
- Points the Box to indexed data locations when the Spark identifies relevant information

**Membrane function (between both):**
- Captures Spark world-knowledge, structures it, catalogs it
- Captures Box events, formats them for Spark narration requests
- Ensures Spark and Box never communicate directly
- Maintains the data layer both systems read from and write to

**What it reads:**
- From Spark: narration output, intent interpretations, world-knowledge, generated assets
- From Box: event streams, go/no-go options, state snapshots

**What it writes:**
- To Spark: focused context windows, player model parameters, memory slices
- To Box: structured environmental data (dimensions, materials, positions)
- To Player: final output (narration + mechanical results, with provenance labels)

**What it NEVER does:**
- Invent mechanical authority (Box-exclusive)
- Override Box rulings
- Block Spark generation (only post-generation gating)
- Strip provenance labels

---

## 3. Interface Contracts

### 3.1 Box → Lens Interface

The Box writes to the Lens. The Lens stores, indexes, and serves.

**Events (Box → Lens):**
```
BoxEvent {
    event_id: UUID
    event_type: enum (ATTACK_ROLL, SAVE, DAMAGE, MOVEMENT, STATE_CHANGE, ...)
    timestamp: datetime
    inputs: dict          # What went into the computation
    outputs: dict         # What came out
    rule_citations: list  # PHB/DMG page references
    provenance: [BOX]     # Always BOX for events
}
```

**Go/No-Go Options (Box → Lens):**
```
ActionOptions {
    character_id: canonical_id
    available_actions: list[Action]  # What this character CAN do right now
    constraints: list[Constraint]    # Why certain actions are unavailable
    movement_remaining: int          # Feet of movement left
    attacks_remaining: int           # Attacks left in full attack
    spells_available: list[Spell]    # Prepared spells with slots remaining
}
```

The Lens uses these options to build context for the Spark: "The fighter can move 30 feet, take a full attack (3 attacks), or charge. The wizard has fireball prepared (20-ft radius, 3 goblins in potential range)."

**Data Requests (Box → Lens):**
```
EnvironmentQuery {
    query_type: enum (OBJECT_DIMENSIONS, MATERIAL_PROPERTIES, COVER_GEOMETRY, ...)
    target_id: str        # ID of the object/location being queried
    context: dict         # Additional context (attacker position, character height, etc.)
}
```

The Box queries the Lens for environmental data that the Spark generated: "What are the dimensions of the table at grid position (4,7)?" The Lens returns structured data from its index.

---

### 3.2 Lens → Box Interface

The Lens serves data to the Box. The Lens does not command the Box.

**Canonical Intents (Lens → Box):**
```
CanonicalIntent {
    intent_id: UUID
    character_id: canonical_id
    action_type: canonical_action    # ATTACK, CAST_SPELL, MOVE, USE_SKILL, ...
    target: canonical_id or position
    parameters: dict                 # Spell level, weapon choice, movement path, etc.
    source: enum (PLAYER_VOICE, PLAYER_CLICK, DM_AUTOMATED)
}
```

The Lens translates player input (via Spark interpretation) into canonical intents the Box can resolve. The Box validates and executes or rejects.

**Environmental Data (Lens → Box):**
```
EnvironmentData {
    object_id: str
    position: grid_coordinates
    elevation: float              # Feet above ground level
    size: enum (Fine..Colossal)
    height: float                 # Exact measurement in feet
    width: float
    depth: float
    material: enum (WOOD, STONE, IRON, EARTH, ...)
    hardness: int                 # Per 3.5e material tables
    hit_points: int               # Per material and thickness
    condition: enum (INTACT, DAMAGED, DESTROYED, ...)
    facing: degrees               # For directional cover
    opacity: bool                 # Blocks line of sight?
    solidity: bool                # Blocks line of effect?
    mobility: enum (FIXED, MOVEABLE, DESTROYED_TERRAIN)
    notes: str                    # Additional context
}
```

---

### 3.3 Lens → Spark Interface

The Lens assembles focused context and sends it to the Spark.

**Context Window (Lens → Spark):**
```
SparkContext {
    # Core request
    request_type: enum (NARRATE_EVENT, INTERPRET_INTENT, GENERATE_SCENE,
                        GENERATE_IMAGE, DM_DIALOGUE, ...)

    # Player model (affects tone, verbosity, explanation depth)
    player_model: {
        experience_level: float    # 0.0 (brand new) to 1.0 (veteran DM)
        pacing_preference: float   # 0.0 (slow/detailed) to 1.0 (fast/terse)
        explanation_depth: float   # 0.0 (minimal) to 1.0 (teach me everything)
        tone_preference: str       # "dramatic", "humorous", "gritty", "classic"
        modality_preference: str   # "voice", "text", "mixed"
    }

    # Relevant campaign memory (minimum necessary slice)
    memory_slice: {
        recent_events: list[Event]         # Last N relevant events
        active_npcs: list[NPC]             # NPCs in current scene
        open_threads: list[Thread]         # Active quest/story threads
        location_context: LocationCard     # Where we are right now
        alignment_state: AlignmentRecord   # Current alignment + recent evidence
    }

    # Box state (go/no-go options, current mechanical reality)
    mechanical_context: {
        action_options: ActionOptions       # What the character can do
        combat_state: CombatState or None   # Initiative, positions, HP if in combat
        environmental_objects: list[EnvironmentData]  # Scene objects with properties
    }

    # Session continuity
    session_context: {
        session_number: int
        time_in_session: duration
        last_player_action: str
        current_phase: enum (PRE_SESSION, EXPLORATION, COMBAT, DIALOGUE, PREP)
    }
}
```

This is the Lens's primary function: assembling the minimum context window that gives the Spark everything it needs and nothing it doesn't.

---

### 3.4 Spark → Lens Interface

The Spark writes output to the Lens. The Lens indexes, structures, and routes it.

**Narration Output (Spark → Lens):**
```
SparkNarration {
    narration_id: UUID
    text: str                     # The generated narration
    provenance: [NARRATIVE]       # Always NARRATIVE for Spark output
    intent_interpretation: str    # If interpreting player input
    world_knowledge: list[WorldFact]  # Any new facts about the scene
}
```

**World Knowledge (Spark → Lens):**
```
WorldFact {
    fact_id: UUID
    fact_type: enum (OBJECT_PROPERTY, NPC_DETAIL, SCENE_DESCRIPTION, ...)
    subject: str                  # What this fact is about
    properties: dict              # Structured data (dimensions, material, etc.)
    confidence: float             # How confident the Spark is (for common-sense facts)
    source_context: str           # What prompted this knowledge generation
}
```

When the Spark generates a tavern scene and mentions "four heavy oak tables," the Lens captures:
- 4x WorldFact entries, each with: material=WOOD(OAK), estimated dimensions, standard furniture height
- These are indexed and available for the Box when combat starts in the tavern

---

## 4. Data Flow Diagrams

### 4.1 Standard Game Loop

```
Player speaks: "I want to attack the goblin"
         │
         ▼
    ┌─────────┐
    │  LENS   │ ← Captures player input
    │ (Focus) │ ← Queries campaign memory: who is the goblin? where?
    │         │ ← Gets Box go/no-go: can this character attack?
    │         │ ← Assembles context window for Spark
    └────┬────┘
         │ Focused context window
         ▼
    ┌─────────┐
    │  SPARK  │ ← Interprets: player wants to melee attack goblin #1
    │  (LLM)  │ ← Returns structured intent interpretation
    └────┬────┘
         │ Intent interpretation
         ▼
    ┌─────────┐
    │  LENS   │ ← Receives interpretation
    │ (Trans) │ ← Translates to canonical intent: ATTACK(fighter, goblin_1, longsword)
    └────┬────┘
         │ Canonical intent
         ▼
    ┌─────────┐
    │   BOX   │ ← Validates: legal action? Yes.
    │(Engine) │ ← Resolves: d20+8=22 vs AC 15 → HIT
    │         │ ← Computes: 1d8+4=9 slashing damage
    │         │ ← Emits event: ATTACK_HIT {roll:22, ac:15, damage:9, type:slashing}
    └────┬────┘
         │ BoxEvent
         ▼
    ┌─────────┐
    │  LENS   │ ← Receives event
    │ (Focus) │ ← Indexes event in campaign memory
    │         │ ← Assembles narration context for Spark
    └────┬────┘
         │ Narration context
         ▼
    ┌─────────┐
    │  SPARK  │ ← Generates: "Your longsword bites deep into the goblin's shoulder..."
    │  (LLM)  │ ← Returns narration tagged [NARRATIVE]
    └────┬────┘
         │ Narration
         ▼
    ┌─────────┐
    │  LENS   │ ← Combines: [BOX] Attack hits (22 vs AC 15, 9 slashing)
    │(Deliver)│ ←          [NARRATIVE] "Your longsword bites deep..."
    │         │ ← Applies player model (verbosity, tone)
    │         │ ← Delivers to player
    └─────────┘
```

### 4.2 Environmental Query Flow

```
Combat starts in a tavern. Halfling dives under a table.
         │
         ▼
    ┌─────────┐
    │   BOX   │ ← Needs table dimensions for cover calculation
    │(Engine) │ ← Queries Lens: OBJECT_DIMENSIONS(table_at_4_7)
    └────┬────┘
         │ EnvironmentQuery
         ▼
    ┌─────────┐
    │  LENS   │ ← Checks index: was this table registered?
    │  (Data) │
    │         │──── IF YES: Returns stored EnvironmentData
    │         │              (height: 3.5ft, material: OAK, etc.)
    │         │
    │         │──── IF NO: Queries Spark for world-knowledge
    └────┬────┘
         │ (If data missing)
         ▼
    ┌─────────┐
    │  SPARK  │ ← "What are the physical properties of a standard tavern table?"
    │  (LLM)  │ ← Returns: oak, ~3.5ft tall, ~4ft wide, ~2in thick
    └────┬────┘
         │ WorldFact
         ▼
    ┌─────────┐
    │  LENS   │ ← Indexes the new WorldFact
    │  (Data) │ ← Serves EnvironmentData to Box
    └────┬────┘
         │ EnvironmentData
         ▼
    ┌─────────┐
    │   BOX   │ ← Table height 3.5ft, halfling height 3.0ft (prone ~1.5ft)
    │(Engine) │ ← Halfling fits under table: YES
    │         │ ← Cover from table: TOTAL (from one direction)
    │         │ ← Condition: PRONE
    │         │ ← Emits event: TAKE_COVER {type:TOTAL, source:table, condition:PRONE}
    └─────────┘
```

### 4.3 Prep Time Flow

```
Player says "yes" to starting a new campaign.
         │
         ▼
    ┌─────────┐
    │  LENS   │ ← Assembles campaign generation context
    │ (Focus) │ ← Player model, preferences, past campaigns
    └────┬────┘
         │ Campaign context
         ▼
    ┌─────────┐
    │  SPARK  │ ← Generates adventure structure
    │  (LLM)  │ ← Creates NPCs (names, descriptions, stats framework)
    │         │ ← Generates scene descriptions with world-knowledge
    │         │ ← Produces encounter designs
    │         │ ← Generates NPC portraits (image pipeline)
    │         │ ← Periodically teases player: "Hey, want to see this?"
    └────┬────┘
         │ Adventure content + WorldFacts + images
         ▼
    ┌─────────┐
    │  LENS   │ ← Indexes everything:
    │ (Index) │   - NPC cards (name, description, stats, portrait)
    │         │   - Location cards (description, environmental objects)
    │         │   - Encounter data (creatures, terrain, objects)
    │         │   - Environmental objects (dimensions, materials)
    │         │   - Images (categorized, filed into Tome/Bestiary)
    └────┬────┘
         │ Structured stat blocks
         ▼
    ┌─────────┐
    │   BOX   │ ← Validates NPC stat blocks against RAW
    │(Engine) │ ← Confirms encounter CR math
    │         │ ← Registers environmental objects for future combat
    │         │ ← Stamps: VALIDATED or REJECTED (with reason)
    └─────────┘
```

---

## 5. The Lens Subsystems

### 5.1 Campaign Memory Index

**Purpose:** Structured, queryable record of everything that has happened.

**Contents:**
- Entity Cards (NPCs, creatures, locations, items)
- Event Timeline (chronological record of all events)
- Open Threads (active quests, unresolved plot points)
- Consequence Chains (action A led to event B which caused state C)
- Session Summaries (condensed records of each session)
- Relationship Map (who knows whom, faction standings)

**Query interface:** The Lens queries campaign memory when assembling context for the Spark. "What does the player know about this NPC?" "What happened last time they were in this location?" "What open threads are relevant to the current scene?"

**Write interface:** Events from the Box and narration from the Spark both contribute to campaign memory, but through different channels:
- Box events are indexed as authoritative facts (tagged [BOX])
- Spark narration may generate new world-facts, which are indexed as [NARRATIVE] until validated

---

### 5.2 Player Model

**Purpose:** Track player preferences and behavior to focus the Spark's output.

**Five Dimensions:**
1. **Experience Level** (0.0–1.0): How well the player knows D&D 3.5e rules
2. **Pacing Preference** (0.0–1.0): Slow/detailed vs fast/action-oriented
3. **Explanation Depth** (0.0–1.0): How much rule explanation to include
4. **Tone Preference** (categorical): dramatic, humorous, gritty, classic, etc.
5. **Communication Modality** (categorical): voice-primary, text-primary, mixed

**Inference:** Based on player behavior, tracked over time with confidence weighting and decay. A player who frequently asks "why?" gets higher explanation depth. A player who says "skip this" gets higher pacing preference.

**Usage:** Injected into every Spark context window. Affects how the Spark generates narration, how verbose it is, how much it explains, what tone it uses. Never affects mechanics.

---

### 5.3 Alignment Tracker

**Purpose:** Continuous tracking of character alignment with evidence chains.

**Model:** Two continuous axes:
- Law ↔ Chaos (-1.0 to +1.0)
- Good ↔ Evil (-1.0 to +1.0)

**Tracking:**
- Actions tagged with alignment deltas: {event_id, delta_law: -0.1, delta_good: +0.2, evidence: "freed prisoners"}
- Evidence chain maintained: every shift has a reason and an event reference
- Threshold-based label quantization: the floating-point position maps to the 9 standard alignments
- Confidence weighting: recent actions weigh more than old ones
- Decay: very old actions contribute less to current position

**Mechanical enforcement lives in the Box:** Paladin falls if alignment shifts beyond threshold. Detect Evil reads current alignment state. Protection from Evil checks alignment. These are Box computations that query alignment state from the Lens.

**Conversational evidence lives in the Lens:** When the player asks "Hey DM, why did my alignment change?" the DM (Spark) queries the Lens for the evidence chain and presents it: "Well, you executed that prisoner in session 12, you lied to the temple priest in session 14..."

---

### 5.4 Environmental Data Index

**Purpose:** Structured storage of physical world-knowledge for Box queries.

**Contents:** Every object in the game world with physical properties:
- Dimensions (height, width, depth)
- Material and hardness
- Hit points
- Position and elevation
- Condition (intact, damaged, destroyed)
- Facing (for directional cover)
- Opacity and solidity (line of sight/effect)

**Population:**
- During prep: Spark generates scene descriptions → Lens extracts and indexes object properties
- During play: Spark generates new world-knowledge in real-time as players interact with the environment
- On demand: Box queries Lens for missing data → Lens queries Spark → Spark provides common-sense knowledge → Lens indexes and serves

**This is the symbiosis:** The Spark creates the world. The Box enforces the rules within it. The Lens makes sure the Box has the data it needs to do its job.

---

### 5.5 Context Assembler

**Purpose:** Build the minimum-necessary context window for each Spark call.

**Principle:** The Spark doesn't need to see everything. It needs to see exactly what's relevant to this moment. The Context Assembler's job is aggressive but intelligent filtering.

**Assembly process:**
1. Determine request type (narrate event, interpret intent, generate scene, etc.)
2. Query campaign memory for relevant slices
3. Get Box go/no-go options for current game state
4. Get player model parameters
5. Get session continuity context
6. Compose context window with minimum information for maximum coherence
7. Respect token limits — if context exceeds window, prioritize by relevance

**This is what prevents Spark overload.** The Box might know about 200 objects in the dungeon. The player can only see 15 in their current room. The Spark only needs to know about the 3 that are relevant to this action. The Context Assembler makes that determination.

---

### 5.6 Session Continuity

**Purpose:** Maintain coherent experience across sessions.

**Contents:**
- Where we left off (scene, game state, active dialogue)
- Session-start recap data (for the DM to offer a recap)
- Player's last emotional state (were they mid-combat? mid-conversation? exploring?)
- Time elapsed since last session (affects DM greeting tone)
- Unresolved cliffhangers or pending decisions

**Usage:** When the player opens the application, the Lens provides session continuity to the Spark so the DM can greet appropriately: "Welcome back! It's been a while. Last time, you were about to enter the goblin cave. Want me to recap what happened?" vs. "Hey, we just left off — your sword is still drawn, the orc is 10 feet away. Ready?"

---

## 6. The Separation Guarantee

### 6.1 Communication Matrix

| From → To | Box | Lens | Spark | Player |
|-----------|-----|------|-------|--------|
| **Box** | Self (internal) | Events, go/no-go options, queries | NEVER DIRECTLY | NEVER DIRECTLY |
| **Lens** | Canonical intents, environment data | Self (internal) | Context windows, prompts | Final output (labeled) |
| **Spark** | NEVER DIRECTLY | Narration, intents, world-knowledge | Self (internal) | NEVER DIRECTLY |
| **Player** | NEVER DIRECTLY | Input (voice/text/clicks) | NEVER DIRECTLY | N/A |

**The Lens is the only system that talks to both.** The Spark and Box are isolated from each other. The player interacts only with the Lens (through the table surface).

### 6.2 What Each System Guards

| System | Guards | Does NOT Guard |
|--------|--------|----------------|
| **Box** | Mechanics, rules, dice, game state, battle map | Narration, tone, player experience |
| **Lens** | Spark coherence, context quality, data integrity, provenance | Mechanics (Box does that), generation (Spark does that) |
| **Spark** | Nothing | Everything is guarded by Box or Lens |

### 6.3 Enforcement

This architecture is enforced via:
1. **Parent doctrine:** `SPARK_LENS_BOX_DOCTRINE.md` (conceptual axioms)
2. **PR gate:** `M1_PR_GATE_CHECKLIST.md` CHECK-007 (separation verification)
3. **Monitoring:** `M1_MONITORING_PROTOCOL.md` INV-TRUST-001 (runtime invariant)
4. **This document:** Interface contracts define the ONLY permitted communication paths

Any communication path not defined in this document is prohibited.

---

## 7. Relationship to Existing Documents

| Document | Relationship |
|----------|-------------|
| `SPARK_LENS_BOX_DOCTRINE.md` | Parent doctrine. This spec implements and amends (Lens definition). All axioms preserved. |
| `SPARK_LENS_BOX_DEFINITIONS.md` | Definitions addendum. Lens definition requires update to reflect statefulness. |
| `SPARK_PROVIDER_CONTRACT.md` | Spark interface contract. Compatible — SparkRequest/SparkResponse maps to Spark↔Lens interface. |
| `M1_LLM_SAFEGUARD_ARCHITECTURE.md` | Safeguards for narration boundary. Compatible — safeguards operate at Lens layer. |
| `SPARK_ADAPTER_ARCHITECTURE.md` | Model selection/loading. Compatible — hardware-aware selection is a Spark-internal concern. |
| `TABLE_METAPHOR_AND_PLAYER_ARTIFACTS.md` | Table surface is the player-facing side of the Lens. |
| `WHITEBOARD_SESSION_002_DECISIONS.md` | Source decisions for this spec. |

---

## 8. Open Engineering Questions

These require resolution before implementation:

1. **Lens persistence format:** What is the storage format for the Campaign Memory Index? (Candidates: SQLite, append-only log, hybrid)
2. **Context window budgeting:** How do we allocate tokens across memory slices, mechanical context, player model, and session continuity?
3. **Environmental data latency:** When the Box queries the Lens for missing data and the Lens must query the Spark, what is the acceptable latency? How does this affect combat pacing?
4. **World-knowledge validation:** Should the Lens validate Spark-generated world-knowledge (e.g., "Is 3.5 feet a reasonable height for a tavern table?") or accept it as common-sense truth?
5. **Alignment decay function:** What mathematical function governs how old alignment evidence decays? Linear? Exponential? Session-based?
6. **Player model cold start:** How does the system behave before it has enough data to infer player preferences?

---

## 9. Governance

- This document is **BINDING** as of 2026-02-11
- Amendments require Product Owner (Thunder) approval
- This document amends the Lens definition in the parent doctrine; all other doctrine axioms remain unchanged
- Implementation must conform to both this spec and the parent doctrine
- In case of conflict between this spec and the parent doctrine's trust/authority axioms, the parent doctrine prevails

---

## END OF SPARK/LENS/BOX OPERATIONAL ARCHITECTURE

**Date:** 2026-02-11
**Authors:** Thunder (Product Owner), Opus (Acting PM)
**Status:** BINDING
**Parent:** `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md`

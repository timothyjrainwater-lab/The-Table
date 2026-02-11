# RQ-INTERACT-001: Voice-First, Click-Second Interaction

**Research Track:** 5 of 7
**Domain:** Player Interaction
**Status:** FINDINGS RECEIVED
**Filed:** 2026-02-11
**Source:** Thunder (Product Owner) — Deep Research prompt

---

## Problem Statement

Player intent should be expressed primarily in natural language to the DM. Direct map manipulation exists, but as a secondary path. The system must translate ambiguous human intent into precise mechanical actions without forcing the player into UI workflows, and without letting misinterpretation corrupt Box resolution.

**This is not a speech-to-command problem.**
This is an intent interpretation → confirmation → mechanical execution pipeline that preserves the feeling of talking to a DM.

---

## Research Objective

Design an interaction model where:

1. Player speaks/types intent in natural language
2. System interprets it into structured "Action Intents"
3. DM confirms interpretation visually and conversationally
4. Box executes only after confirmation
5. Direct map interaction remains available but never primary

Provide concrete strategies for intent parsing, ambiguity handling, confirmation UX, and map interaction that preserve immersion and mechanical precision.

---

## Research Sub-Questions

### (1) Intent → Structured Action Translation

Research how to reliably convert:

> "I want to cast fireball and try to catch all three goblins"

into:

```
action: CAST_SPELL
spell: FIREBALL
targeting_mode: AREA
desired_targets: [goblin1, goblin2, goblin3]
```

Focus on:
- Semantic parsing techniques for tabletop commands
- Handling vague phrases ("around them", "near the door", "behind the table")
- Maintaining context across turns

Deliverable: intent schema + parsing strategy.

### (2) Ambiguity Resolution via DM Confirmation

Research how to design a loop where:
- System proposes a geometric interpretation
- Highlights it on the map
- Asks for confirmation in natural language

Example: "Here? Or here?"

This is critical for trust.

Deliverable: confirmation loop pattern + examples.

### (3) Lean-Up Map Interaction Model

Research how to design a minimal interaction pattern where:
- Player "leans up" to the map
- Cursor becomes a geometric tool (radius, ray, movement path)
- No UI overlays or toolbars are needed
- Returning to seat restores prior state

Deliverable: interaction grammar for map mode.

### (4) Character Sheet as Action Surface

Research how to make the character sheet serve as:
- Spell/ability trigger surface
- Contextual info display
- Alternative to voice input

Without becoming an MMO hotbar.

Deliverable: interaction principles + examples.

### (5) Error Handling Without Breaking Immersion

Research how to handle mis-parses:
- DM asks clarification questions
- Avoid system error messages
- Keep interaction conversational

Deliverable: recovery patterns.

### (6) Timing and Responsiveness Expectations

Research acceptable latency for:
- Intent parsing
- Confirmation rendering
- Box resolution

So the conversation feels natural.

Deliverable: timing targets + pacing rules.

### (7) Accessibility and Fallback Paths

Research:
- When players prefer clicking vs speaking
- How to support both without UI creep
- How to maintain metaphor consistency

Deliverable: dual-mode design rules.

### (8) Output: Interaction Playbook

Synthesize into:
- Intent schema
- Confirmation loop model
- Map interaction grammar
- Character sheet interaction rules
- Error recovery patterns
- Latency targets

---

## Research Findings

### Preamble

This creates a high-stakes UX challenge: mediating between the messiness of human speech and the rigid logic of game rules without breaking the "magic circle" of the table. The following Interaction Playbook is designed to keep the technology invisible and the conversation central.

---

### Finding 1: Intent → Structured Action Translation

**Objective:** Convert natural language into a machine-readable payload (JSON) that describes *intent*, not just mechanics.

#### The Parsing Strategy: Context-Aware Semantic Slot Filling

Standard "Speech-to-Text" is insufficient. We need "Speech-to-Context." The parser must utilize a **Short-Term Memory (STM) buffer** that retains the last 3 turns of context to resolve pronouns ("Attack *him* again").

#### The Intent Schema

The system translates speech into an `ActionIntent` object:

```json
{
  "actor_id": "player_wizard_01",
  "intent_type": "CAST_SPELL",
  "primary_object": "FIREBALL",
  "spatial_constraint": {
    "type": "AREA_OPTIMIZATION",
    "target_descriptors": ["goblin_1", "goblin_2", "goblin_3"],
    "avoid_descriptors": ["player_fighter_01"],
    "anchor_hint": "cluster_centroid"
  },
  "parameters": {
    "spell_level": "default",
    "meta_magic": null
  }
}
```

#### Handling Vague Phrases

- **"Near the door":** System queries map metadata for objects tagged "door" within actor's line of sight, sets a proximity anchor.
- **"Try to get them all":** Translated to an optimization request. Box calculates geometric solution maximizing targets within radius.
- **"Behind the table":** Interpreted as a pathfinding constraint (Move *to* coordinate X *via* cover).

---

### Finding 2: Ambiguity Resolution — The "Ghost" State

**Objective:** Confirm intent without pop-up dialog boxes.

#### The Confirmation Loop Pattern

1. **Player Speaks:** "I cast Fireball to hit those three goblins."
2. **The Phantom Render:** Before Box resolves damage, the system renders a **translucent "Phantom" template** (a glowing orange sphere) on the map at the calculated optimal point.
3. **The DM Inquiry:** The DM persona asks a confirmation question based on confidence level:
   - *High Confidence:* "Here?" (Visual pulse of the phantom).
   - *Low Confidence:* "I can hit two of them, but the third is out of range. Is this okay?"
4. **Player Confirmation:**
   - *Voice:* "Yes" / "Perfect."
   - *Refinement:* "Nudge it left... okay, there." (Visual updates in real-time).

**Why this works:** It mimics a real tabletop moment where a player hovers their hand over the map and looks at the DM for a nod.

---

### Finding 3: Lean-Up Map Interaction Model

**Objective:** Make direct input feel like physical posturing, not switching apps.

#### The "Lean-Up" Metaphor

In real life, when a player needs precision, they stand up and lean over the table.

- **Trigger:** Zooming in past a certain threshold or holding a "Focus" key (e.g., Spacebar).
- **Visual Shift:** Camera creates a "tilt-shift" effect, blurring the character sheet/background and sharpening the map. POV moves closer to a top-down tactical view.

#### Context-Sensitive Interaction Grammar (No Toolbars)

When in "Lean-Up" mode, the cursor changes function based on what it is hovering over:

| Cursor Context | Action (Click + Drag) | Visual Feedback |
|---|---|---|
| **Hover Self** | Plot Movement Path | Dashed line showing path + distance counter |
| **Hover Enemy** | Declare Attack/Target | Red reticle appears under enemy |
| **Empty Space** | Ping / Area Measurement | Ray or Radius measurement tool appears automatically |
| **Active Spell** | Fine-tune Placement | Moves the "Phantom" spell template |

**Returning to Seat:** Releasing the Focus key or zooming out instantly snaps the view back to the atmospheric, lower-angle "Player View," signifying the end of the tactical moment.

---

### Finding 4: Character Sheet as Action Surface

**Objective:** The sheet is a diegetic object, not a UI menu.

#### Interaction Principles

- **Drag-to-World:** To cast a spell manually, the player drags the spell name *off* the sheet and *onto* the map. This creates a physical connection between the ability and the world.
- **Touch-to-Query:** Clicking/tapping a stat (e.g., Strength) doesn't roll it immediately. It highlights it and prompts the DM: "Do you want to make a Strength check?"
- **Dynamic Ink:** Values shouldn't just change; they should look like they are being erased and rewritten. If HP drops, the paper texture might darken or look blood-spattered (subtle immersive feedback).

#### The "Focus" State

When the player mentions "Inventory," the camera shifts to look down at the sheet. When they say "Look at the map," the sheet slides off-screen or blurs.

---

### Finding 5: Error Handling — Conversational Recovery

**Objective:** Never say "Error: Invalid Command."

#### Recovery Patterns

Instead of system alerts, the DM persona handles misunderstandings using **Reflective Questioning**:

- **Scenario A: Ambiguous Target**
  - Bad: "Error: Multiple targets found."
  - Good (DM Voice): "Did you mean the Goblin Archer or the Worg next to him?" (System highlights both alternately).

- **Scenario B: Illegal Move (rules violation)**
  - Bad: "Action prevented. Movement limited to 30ft."
  - Good (DM Voice): "That's a bit too far for one turn. You can get to *here* (ghost marker), or you'd need to Dash."

- **Scenario C: Total Hallucination (Parser fail)**
  - Bad: "Command not recognized."
  - Good (DM Voice): "I didn't quite catch that. What are you trying to do?"

---

### Finding 6: Timing and Responsiveness Expectations

**Objective:** Maintain the illusion of conversation.

| Interaction Phase | Target Latency | Design Note |
|---|---|---|
| **Intent Parsing** ("The 'Uh-huh' window") | < **600ms** | System must acknowledge input (a nod from the avatar, a "thinking" sound) almost instantly while processing logic |
| **Phantom Rendering** (Visual Confirmation) | < **200ms** | As soon as semantic intent (e.g., "Fireball") is identified, the template should appear, even if targets aren't fully locked yet |
| **Box Resolution** (The Dice Roll) | **Variable (1s - 3s)** | Instant resolution feels anticlimactic. Deliberately delay high-stakes rolls with rolling animation for tension. Low-stakes rolls (opening a door) should be instant |

---

### Finding 7: Accessibility and Fallback Paths

**Objective:** Ensure the game is playable in a noisy room or by non-verbal players.

#### Dual-Mode Design Rules

1. **Redundancy:** Every voice command must have a mouse/keyboard equivalent.
   - *Voice:* "Cast Magic Missile on the wizard."
   - *Click:* Drag "Magic Missile" from sheet → Drop on Wizard token.

2. **Seamless Handoff:** The system listens to both simultaneously. A player can start a sentence "I want to move..." and finish it by clicking a destination on the map. The parser fuses the audio "Move" with the coordinate data from the click.

3. **Chat Fallback:** A text input box exists (hidden until active). Typing "Cast Fireball" triggers the exact same semantic parser as the voice input.

---

## Cross-References

- `docs/design/TABLE_SURFACE_UI_SPECIFICATION.md` — Table interaction model, lean-up mechanic
- `docs/design/SPARK_LENS_BOX_ARCHITECTURE.md` — Intent processing flow
- `docs/research/RQ_VOICE_001_BENCHMARK_RESULTS.md` — Voice pipeline benchmarks

# M1.5 Runtime Experience — Solo Vertical Slice Flow

**Status:** Design-Only (No Implementation)
**Agent:** SONNET C
**Work Order:** WO-M1.5-UX-01
**Date:** 2026-02-10

---

## Executive Summary

This document defines the **minimal end-to-end experience** for a solo user running AIDM from disk → play → exit. This is a **design-only specification** with no UI implementation, no SPARK integration, and no content generation.

**Goal:** Define what the user sees and does when resuming a campaign, making choices, and seeing consequences.

**Scope:** Text-only, single-player, minimal interaction flow.

---

## 1. Resume Flow (Disk → First Prompt)

### 1.1 Entry Point

User runs:
```bash
python -m aidm.runtime.runner --campaign my_campaign_id
```

### 1.2 Bootstrap Sequence

**Step 1: Campaign Load**
```
[AIDM] Loading campaign: my_campaign_id
[AIDM] Found campaign directory: ~/.aidm/campaigns/my_campaign_id/
[AIDM] Loading manifest...
[AIDM]   Campaign: "Rise of the Cult"
[AIDM]   Seed: 42
[AIDM]   Created: 2025-01-15
```

**Step 2: State Reconstruction**
```
[AIDM] Loading initial state from start_state.json...
[AIDM] Loading event log from events.jsonl...
[AIDM]   Found 127 events (22 complete turns)
[AIDM] Replaying event log...
[AIDM]   Turn 1 (goblin_1) ✓
[AIDM]   Turn 2 (pc_fighter) ✓
[AIDM]   Turn 3 (pc_wizard) ✓
[AIDM]   ...
[AIDM]   Turn 22 (pc_fighter) ✓
[AIDM] Replay complete.
[AIDM] Final state hash: a3f8d9e7c2b1...
```

**Step 3: Partial Write Recovery (if needed)**
```
[AIDM] Partial write detected: 3 events after last turn_end
[AIDM] Discarding incomplete turn (events 125-127)
[AIDM] Resuming from turn 22 (event_id 124)
```

**Step 4: Log Sync Check**
```
[AIDM] Verifying log synchronization...
[AIDM]   Event log: 22 complete turns
[AIDM]   Session log: 22 resolved intents
[AIDM]   ✓ Logs synchronized
```

**Step 5: Session Ready**
```
[AIDM] Session ready.
[AIDM] Next turn: pc_wizard (Turn 23)
```

### 1.3 Error Cases

**Missing Campaign**
```
[AIDM] ERROR: Campaign 'unknown_campaign' not found
[AIDM] Available campaigns:
[AIDM]   - my_campaign_id
[AIDM]   - test_campaign
```

**Corrupted Event Log**
```
[AIDM] ERROR: Failed to load event log (invalid JSON on line 45)
[AIDM] Campaign cannot be resumed.
[AIDM] Restore from backup or contact support.
```

**Log Desync**
```
[AIDM] ERROR: Log desynchronization detected
[AIDM]   Event log: 22 complete turns
[AIDM]   Session log: 21 resolved intents
[AIDM] This indicates a runtime bug. Campaign cannot be resumed.
```

---

## 2. Session Start Moment (What User Sees)

### 2.1 Initial Prompt

After bootstrap completes, the user sees:

```
================================================================================
AIDM — AI Dungeon Master for D&D 3.5e
================================================================================

Campaign: Rise of the Cult
Session: 5 (Turn 23)

Current Scene: Trapped Chamber
  A stone chamber with a locked door to the north and suspicious
  floor tiles. The air is thick with dust.

Active Combat: Round 4 of 6
Initiative Order:
  1. Goblin Warrior (6/6 HP) — READY
  2. Kael (Fighter, 10/12 HP)
  3. Lyra (Wizard, 6/6 HP) — YOUR TURN
  4. Goblin Archer (4/6 HP)

Your Status:
  Lyra (Wizard 3)
  HP: 6/6
  Position: (15, 5) — 20ft from goblin warrior
  Conditions: None
  Spells Remaining: 2nd-level (1), 1st-level (2), 0-level (3)

================================================================================
What do you do?
> _
```

### 2.2 Context Display Components

**Minimal required context:**
1. **Campaign name** — "Rise of the Cult"
2. **Turn counter** — "Turn 23"
3. **Active scene** — "Trapped Chamber" with description
4. **Active combat status** — Initiative order, current round
5. **PC status** — HP, position, conditions, resources
6. **Prompt** — "What do you do?"

**Optional context (not M1):**
- Recent events summary
- Known enemies and their status
- Available actions menu
- Narration layer output

---

## 3. Turn Loop UX (Text-Only Interaction)

### 3.1 Basic Input Flow

**User Input:**
```
> I cast Magic Missile at the goblin warrior
```

**System Response (Intent Creation):**
```
[INTENT] Parsing action...
[INTENT] Detected: CAST_SPELL
[INTENT]   Spell: Magic Missile
[INTENT]   Target: goblin_warrior
[INTENT] Status: PENDING
```

### 3.2 Clarification Flow

**Scenario: Missing Required Field**

User input:
```
> I attack
```

System detects missing target:
```
[INTENT] Detected: ATTACK
[INTENT] Missing required field: target_id

Which target?
  1. goblin_warrior (6/6 HP, 20ft away)
  2. goblin_archer (4/6 HP, 35ft away)

Enter number or name:
> 1
```

System confirms:
```
[INTENT] Target selected: goblin_warrior
[INTENT] Status: CONFIRMED
```

### 3.3 Resolution Flow

**After intent confirmation:**
```
[RESOLVE] Processing attack...
[RESOLVE] Rolling attack: 1d20+5 → [12]+5 = 17
[RESOLVE]   vs AC 15 → HIT
[RESOLVE] Rolling damage: 1d8+3 → [6]+3 = 9
[RESOLVE] Result: goblin_warrior takes 9 damage (0/6 HP)
[RESOLVE]   Status: DYING

[EVENT] Intent resolved (event_id 128)
[EVENT] State updated (hash: b4e7a1f9...)
[LOG] Logged to intents.jsonl
```

### 3.4 Narration Layer (Optional, Not M1)

**If narration layer is enabled:**
```
[NARRATE] Lyra's magical bolt streaks across the chamber,
          striking the goblin warrior squarely in the chest.
          The creature collapses with a gurgling cry.
```

**If narration layer is disabled:**
```
[Skip narration — narration layer not configured]
```

### 3.5 Turn End

**System advances turn:**
```
================================================================================
Turn 24: Goblin Archer

[POLICY] Evaluating tactics for goblin_archer...
[POLICY]   Selected: retreat_regroup (score: 6000)
[POLICY]   Rationale: ally_down, outnumbered, critical_hp

The goblin archer flees toward the exit.

[RESOLVE] Processing move...
[RESOLVE] Target position: (0, 10) — exit corridor
[RESOLVE] Movement provokes AoO from Kael
[RESOLVE]   Kael attacks: 1d20+6 → [15]+6 = 21 vs AC 15 → HIT
[RESOLVE]   Damage: 1d8+4 → [5]+4 = 9 (goblin_archer at 0/6 HP)
[RESOLVE]   Status: DYING

[EVENT] Combat ended (all enemies defeated)
[EVENT] Turn 24 complete

================================================================================
What do you do?
> _
```

---

## 4. Exit and Save Semantics

### 4.1 Graceful Exit (Mid-Session)

**User input:**
```
> /exit
```

**System response:**
```
[AIDM] Saving session state...
[AIDM]   Events written: events.jsonl (128 events)
[AIDM]   Intents written: intents.jsonl (24 entries)
[AIDM]   State hash: b4e7a1f9...
[AIDM] Session saved.
[AIDM] Goodbye!
```

**On next resume:**
```
[AIDM] Loading campaign: my_campaign_id
[AIDM] Loading event log from events.jsonl...
[AIDM]   Found 128 events (24 complete turns)
[AIDM] Replaying event log...
[AIDM] Replay complete.
[AIDM] Session ready.
[AIDM] Next turn: pc_wizard (Turn 25)
```

### 4.2 Emergency Exit (Ctrl+C)

**User presses Ctrl+C:**
```
^C
[AIDM] Interrupt detected.
[AIDM] Saving session state...
[AIDM]   Events written: events.jsonl (127 events)
[AIDM]   Intents written: intents.jsonl (23 entries)
[AIDM]   WARNING: Turn 24 incomplete — will be discarded on resume
[AIDM] Session saved (partial write).
[AIDM] Goodbye!
```

**On next resume:**
```
[AIDM] Loading campaign: my_campaign_id
[AIDM] Partial write detected: 2 events after last turn_end
[AIDM] Discarding incomplete turn (events 126-127)
[AIDM] Resuming from turn 23 (event_id 125)
[AIDM] Session ready.
[AIDM] Next turn: pc_wizard (Turn 24)
```

### 4.3 Auto-Save Policy

**Auto-save trigger points:**
1. After every turn_end event
2. Every 5 minutes (wall-clock time)
3. On graceful exit

**Auto-save output:**
```
[AIDM] Auto-saving... (128 events, 24 intents)
[AIDM] ✓ Saved
```

---

## 5. Concrete Walkthrough (Single Session)

### 5.1 Scenario Setup

- **Campaign:** test_campaign (fresh, no events)
- **Scene:** Forest Clearing
- **Entities:** 1 goblin, 2 PCs (fighter, wizard)
- **Goal:** 3 turns total (demonstration only)

### 5.2 Full Transcript

```
$ python -m aidm.runtime.runner --campaign test_campaign

[AIDM] Loading campaign: test_campaign
[AIDM] Found campaign directory: ~/.aidm/campaigns/test_campaign/
[AIDM] Loading manifest...
[AIDM]   Campaign: "Test Campaign"
[AIDM]   Seed: 42
[AIDM]   Created: 2026-02-10
[AIDM] Loading initial state from start_state.json...
[AIDM] Loading event log from events.jsonl...
[AIDM]   Found 0 events (new campaign)
[AIDM] Session ready.
[AIDM] Next turn: goblin_1 (Turn 1)

================================================================================
AIDM — AI Dungeon Master for D&D 3.5e
================================================================================

Campaign: Test Campaign
Session: 1 (Turn 1)

Current Scene: Forest Clearing
  A small clearing with a single goblin and two adventurers.

Active Combat: Round 1
Initiative Order:
  1. Goblin (6/6 HP) — READY
  2. Kael (Fighter, 10/10 HP)
  3. Lyra (Wizard, 6/6 HP)

================================================================================

[POLICY] Evaluating tactics for goblin_1...
[POLICY]   Ranked tactics:
[POLICY]     1. focus_fire (score: 5000)
[POLICY]     2. attack_nearest (score: 2000)
[POLICY]   Selected: focus_fire
[POLICY]   Rationale: base_score=1000, focus_fire_bonus=4000

The goblin charges toward the fighter.

[RESOLVE] Processing attack...
[RESOLVE] Rolling attack: 1d20+2 → [14]+2 = 16
[RESOLVE]   vs AC 16 → HIT
[RESOLVE] Rolling damage: 1d6+1 → [3]+1 = 4
[RESOLVE] Result: pc_fighter takes 4 damage (6/10 HP)

[EVENT] Turn 1 complete (event_id 0-2)

================================================================================
Turn 2: Kael (Fighter)

Your Status:
  Kael (Fighter 1)
  HP: 6/10
  Position: (10, 0) — 5ft from goblin
  Conditions: None

What do you do?
> I attack the goblin with my longsword

[INTENT] Parsing action...
[INTENT] Detected: ATTACK
[INTENT]   Target: goblin_1
[INTENT]   Weapon: longsword
[INTENT] Status: CONFIRMED

[RESOLVE] Processing attack...
[RESOLVE] Rolling attack: 1d20+3 → [18]+3 = 21
[RESOLVE]   vs AC 15 → HIT
[RESOLVE] Rolling damage: 1d8+3 → [7]+3 = 10
[RESOLVE] Result: goblin_1 takes 10 damage (0/6 HP)
[RESOLVE]   Status: DYING

[EVENT] Combat ended (all enemies defeated)
[EVENT] Turn 2 complete (event_id 3-5)

================================================================================
Combat Summary:
  Rounds: 1
  Duration: 6 seconds (game time)
  Enemies defeated: 1
  Party casualties: 0

What do you do?
> /exit

[AIDM] Saving session state...
[AIDM]   Events written: events.jsonl (6 events)
[AIDM]   Intents written: intents.jsonl (1 entry)
[AIDM]   State hash: c9d4e2f1...
[AIDM] Session saved.
[AIDM] Goodbye!
```

---

## 6. Boundary Between Engine and Presentation

### 6.1 Engine Responsibilities

**What the engine provides:**
- WorldState after resolution
- EngineResult with rolls, modifiers, outcome
- Event log with citations
- Deterministic replay

**What the engine does NOT provide:**
- Formatted text descriptions
- Combat log formatting
- Narration/flavor text
- UI layout decisions

### 6.2 Presentation Layer Responsibilities

**What the presentation layer does:**
- Format WorldState into human-readable text
- Display initiative order
- Show HP changes
- Generate combat log
- Format dice roll output
- Handle user input parsing
- Call narration layer (if configured)

**What the presentation layer does NOT do:**
- Modify WorldState directly
- Make mechanical decisions
- Bypass intent lifecycle
- Cache state outside event log

### 6.3 Interface Contract

**Engine → Presentation:**
```python
@dataclass
class TurnResult:
    """Output from engine after turn resolution."""
    world_state: WorldState
    events: List[Event]
    engine_result: EngineResult
    narration_token: str  # For narration layer (optional)
```

**Presentation → Engine:**
```python
@dataclass
class UserInput:
    """Parsed user input for engine processing."""
    actor_id: str
    source_text: str
    action_type: ActionType
    initial_fields: Dict[str, Any]
```

**No shared mutable state** — all communication through immutable data structures.

---

## 7. What This Does NOT Cover

**Explicitly out of scope for M1.5:**

1. **Graphics/UI** — Text-only, no grid visualization
2. **SPARK Integration** — No session prep, no content generation
3. **Multi-player** — Solo player only
4. **Campaign Creation Flow** — Assumes campaign already exists
5. **Character Creation** — Assumes PCs already defined
6. **Narration LLM** — Narration layer is optional, not required
7. **Voice Input** — Text input only
8. **Streaming Output** — Synchronous, blocking resolution
9. **Undo/Redo** — No rewind capability
10. **State Inspection Tools** — No debug commands (future work)

---

## 8. Design Decisions

### 8.1 Text-Only First

**Why:** Proves the architecture without UI complexity. Graphics can be added later without changing the engine contract.

### 8.2 Synchronous Resolution

**Why:** Simplest possible implementation. Async/streaming can be added later as optimization.

### 8.3 No Undo

**Why:** Event sourcing makes undo *possible*, but M1 doesn't require it. Future work.

### 8.4 Explicit Save Points

**Why:** Auto-save after turn_end ensures clean resume. No mid-turn saves prevents partial-write complexity.

### 8.5 Fail-Fast on Corruption

**Why:** No automatic repair. If logs are corrupted, fail immediately and alert user. Repair is a manual process.

---

## 9. Implementation Notes (For Future Work)

**When implementing this design:**

1. **Create `aidm/runtime/runner.py`** — Entry point for CLI
2. **Create `aidm/runtime/display.py`** — Presentation layer formatting
3. **Wire `SessionBootstrap` to `RuntimeSession`** — Bootstrap → session initialization
4. **Add input parser** — Parse text input into `UserInput` structs
5. **Add output formatter** — Format `TurnResult` into readable text
6. **Add signal handler** — Catch Ctrl+C for graceful exit
7. **Test with vertical_slice_v1 data** — Use existing test scenario

**Do NOT:**
- Add graphics
- Add networking
- Add LLM integration
- Add complex UI state management
- Optimize prematurely

---

## 10. Success Criteria

**M1.5 is complete when:**

1. ✅ User can resume an existing campaign from disk
2. ✅ User can see current game state (text-only)
3. ✅ User can input an action (text command)
4. ✅ System resolves action and updates state
5. ✅ System displays outcome (text output)
6. ✅ User can exit and resume later
7. ✅ Partial writes are automatically recovered
8. ✅ Full replay verification passes on every resume

---

## 11. Summary

**M1.5 Runtime Experience defines:**

- **Resume flow:** Campaign load → replay → ready prompt
- **Session start:** Text display of game state and active turn
- **Turn loop:** Input → clarify → confirm → resolve → display → next turn
- **Exit semantics:** Graceful exit, emergency exit, auto-save policy
- **Engine/presentation boundary:** Clear interface, no shared mutable state

**Next steps after M1.5 design approval:**
1. Implement `aidm/runtime/runner.py` (CLI entry point)
2. Implement `aidm/runtime/display.py` (text formatting)
3. Add input parser and output formatter
4. Test with vertical_slice_v1 scenario
5. Iterate based on user feedback

---

**Document Status:** Design Complete
**Implementation Status:** Not Started
**Last Updated:** 2026-02-10

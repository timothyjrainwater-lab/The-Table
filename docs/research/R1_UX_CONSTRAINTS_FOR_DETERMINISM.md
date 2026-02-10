# R1: UX Constraints for Determinism

**Status:** R0 / RESEARCH / NON-BINDING
**Type:** Safety Specification (NOT Design)
**Authority:** Advisory only (requires PM validation)
**Last Updated:** 2026-02-10
**Research Lead:** Agent C (UX Constraints)

---

## ⚠️ RESEARCH NOTICE

This document enumerates **UX safety constraints** required to prevent player confusion when deterministic recall and generative narration coexist.

**This is NOT:**
- ❌ A UX design specification
- ❌ A mockup or wireframe
- ❌ An interaction flow diagram
- ❌ A feature proposal

**This IS:**
- ✅ A list of required UX signals to prevent confusion
- ✅ A catalog of negative cases (what UX must NOT do)
- ✅ Player failure scenarios where clarity breaks
- ✅ Clarity risk enumeration

**Do not implement UX solutions** based on this document. This defines constraints only.

---

## Research Question

**What UX signals are required to prevent player confusion if deterministic recall and generative narration coexist?**

**Context:**
- AIDM uses deterministic replay (same seed → identical outcomes)
- AIDM uses generative narration (LLM produces text from event log)
- **Tension:** Narration text may vary even when events are identical
- **Risk:** Players may confuse "different narration" with "different outcome"

**Example Scenario:**
```
Session 1 (original play):
  Event: player_attack_hit (damage=12, target=goblin_1)
  Narration: "Your blade cuts deep into the goblin's shoulder."

Session 2 (replay from save):
  Event: player_attack_hit (damage=12, target=goblin_1)  [IDENTICAL]
  Narration: "You strike the goblin's torso with precision."  [DIFFERENT TEXT]
```

**Player Question:** "Did something change? Why is the text different?"

**Required UX Signal:** Player must understand that **events are deterministic, narration is cosmetic**.

---

## Critical Constraints

### Constraint 1: Events vs Narration Distinction

**Requirement:** UX must make it clear that **events** are the source of truth, **narration** is presentation.

**Player Confusion Risk:**
- Player sees different narration text on replay
- Player assumes game state changed ("This feels different")
- Player loses trust in determinism ("Is replay broken?")

**UX Signal Required:**
- ✅ Player must be able to distinguish "what happened" (event) from "how it was described" (narration)
- ✅ Player must be able to inspect raw events if narration is unclear

**UX Must NOT:**
- ❌ Present narration as the sole representation of game state
- ❌ Hide event log entirely (opacity creates distrust)
- ❌ Use narration variation to imply mechanical differences

**Negative Case:**
```
BAD: Only show narration text with no event visibility
Player: "I got 12 damage last time, this time it says '10 damage' - is this a bug?"
Reality: Event shows damage=12 both times, narration generator rounded differently
Problem: Player can't verify events, assumes narration is ground truth
```

**Required Signal (enumerated, NOT designed):**
1. Event log must be inspectable by player (at minimum: toggle to show raw events)
2. Narration must be visually distinct from events (not interchangeable)
3. Replay must indicate "same events, possibly different narration"

---

### Constraint 2: Determinism Boundary Visibility

**Requirement:** UX must make it clear **what is deterministic** and **what is not**.

**Deterministic (same seed → same result):**
- Dice rolls
- Damage calculations
- Hit/miss outcomes
- Initiative order
- RNG-driven events

**Non-Deterministic (may vary):**
- Narration text (LLM-generated)
- Audio TTS voice variance (if stochastic model)
- Image generation results (if using generative model)

**Player Confusion Risk:**
- Player expects replay to be **byte-for-byte identical**
- Player sees narration variation, assumes "replay is broken"
- Player reports false bugs ("Replay doesn't match!")

**UX Signal Required:**
- ✅ Player must know what "deterministic replay" means (events identical, presentation may vary)
- ✅ Player must be warned if presentation layer is non-deterministic

**UX Must NOT:**
- ❌ Claim "perfect replay" if narration/audio/image can vary
- ❌ Use term "replay" without clarifying scope (events vs presentation)
- ❌ Show narration differences without explanation

**Negative Case:**
```
BAD: "Replay Session" with no clarification
Player: "I replayed from turn 5, but the DM said something different. Is my save corrupted?"
Reality: Events are identical, LLM narration varied (allowed)
Problem: Player doesn't know narration is non-deterministic
```

**Required Signal (enumerated, NOT designed):**
1. "Replay" feature must clarify scope: "Events will be identical, narration may vary"
2. If narration varies during replay, explain why (one-time notice acceptable)
3. Do NOT use language implying total identity ("exact replay", "perfect match")

---

### Constraint 3: Generative Content Labeling

**Requirement:** UX must distinguish **deterministic content** from **generated content**.

**Sources of Content:**
- **Deterministic:** Event log, dice rolls, damage calculations, rulebook data
- **Generated:** Narration text, NPC dialogue, scene descriptions, image/audio

**Player Confusion Risk:**
- Player treats generated narration as "what actually happened"
- Player disputes mechanical outcome based on narration interpretation
- Player assumes narration text is canonical (contradicts event log)

**UX Signal Required:**
- ✅ Player must know when content is generated (narration, NPC dialogue)
- ✅ Player must know when content is deterministic (dice rolls, damage)

**UX Must NOT:**
- ❌ Present generated narration without indication of source
- ❌ Allow narration to contradict events (if damage=12, narration must not say "minor scratch")
- ❌ Use generated content as authoritative source for disputes

**Negative Case:**
```
BAD: Narration says "You miss the goblin completely"
Event log shows: attack_roll=18, goblin_ac=15, hit=true, damage=12
Player: "But the narration said I missed!"
Problem: Generated narration contradicted deterministic event
```

**Required Signal (enumerated, NOT designed):**
1. Generated narration must align with events (damage=12 cannot be narrated as "miss")
2. If narration contradicts events, events take precedence (player can inspect log)
3. Generated content should be visually distinct (e.g., different formatting, icon, color)

---

### Constraint 4: RNG Transparency

**Requirement:** UX must clarify **when randomness was used** and **from which seed**.

**Player Confusion Risk:**
- Player sees same input, different output (doesn't realize RNG was involved)
- Player assumes "broken determinism" when actually RNG seed changed
- Player can't debug "why did this happen differently?"

**UX Signal Required:**
- ✅ Player must know when RNG affected outcome (dice roll, random event)
- ✅ Player must be able to identify RNG seed for debugging (if different seed → different outcome)

**UX Must NOT:**
- ❌ Hide RNG usage entirely (player assumes deterministic when it's not)
- ❌ Use RNG without attribution (player can't trace why outcome occurred)
- ❌ Change RNG seed without player awareness (silent re-roll breaks determinism)

**Negative Case:**
```
BAD: Replay from save, but RNG seed is different
Player: "I loaded my save at turn 5, but the goblin hit me this time. Last time it missed. Is my save corrupted?"
Reality: Save file had different RNG seed (intentional or bug)
Problem: Player doesn't know RNG seed controls outcome
```

**Required Signal (enumerated, NOT designed):**
1. RNG usage must be visible (e.g., "rolled 1d20: result 14")
2. RNG seed must be inspectable (advanced users can verify determinism)
3. If RNG seed changes, explain why ("New game started" vs "Loaded save from different timeline")

---

### Constraint 5: Save/Load Determinism Clarity

**Requirement:** UX must clarify **what is preserved** in save files and **what is regenerated**.

**Preserved (in save file):**
- Event log (all events up to save point)
- RNG seed (or sequence state)
- World state (entities, HP, conditions)

**Regenerated (on load):**
- Narration text (re-generated from events)
- Audio TTS (re-synthesized)
- Images (re-generated or cached)

**Player Confusion Risk:**
- Player expects save file to store "everything they saw" (including exact narration text)
- Player loads save, sees different narration, assumes "save is corrupted"
- Player doesn't understand why images regenerate (assumes they should be cached)

**UX Signal Required:**
- ✅ Player must know what save files contain (events + seed, NOT narration text)
- ✅ Player must know narration will regenerate on load (may differ from original)

**UX Must NOT:**
- ❌ Imply save files store full presentation layer (narration, audio, images)
- ❌ Show regeneration progress without explanation ("Why is it loading narration?")
- ❌ Fail silently if regeneration produces different result (player should know it's expected)

**Negative Case:**
```
BAD: Save file loads, narration regenerates silently
Player: "I saved at turn 10, but when I loaded, the DM said something different. Did I lose my save?"
Reality: Save file only stores events, narration regenerates on load (expected)
Problem: Player doesn't know regeneration is normal
```

**Required Signal (enumerated, NOT designed):**
1. Save file description must clarify scope: "Saves game state and events, narration regenerates on load"
2. On load, indicate regeneration is happening ("Generating narration from event log...")
3. If regeneration fails, explain fallback ("Narration unavailable, showing event log")

---

### Constraint 6: Event Log as Ground Truth

**Requirement:** UX must establish **event log** as authoritative source for game state.

**Hierarchy of Truth:**
1. **Event log** (what actually happened, deterministic)
2. **World state** (derived from event log via reducer)
3. **Narration** (cosmetic presentation of events, may vary)

**Player Confusion Risk:**
- Player treats narration as authoritative ("But the DM said...")
- Player disputes event log ("That's not what happened!")
- Player doesn't understand event log is source of truth

**UX Signal Required:**
- ✅ Player must know event log is authoritative
- ✅ Player must be able to inspect event log to resolve disputes

**UX Must NOT:**
- ❌ Hide event log entirely (creates opacity, breeds distrust)
- ❌ Present narration as equal authority to events
- ❌ Allow player to modify narration but not events (creates divergence)

**Negative Case:**
```
BAD: Player disputes damage calculation
Player: "The DM said 'You take 15 damage' but my HP only went down by 12. Is this a bug?"
Reality: Event log shows damage=12, narration generator mistakenly said 15
Problem: Player can't verify event log, assumes narration is correct
```

**Required Signal (enumerated, NOT designed):**
1. Event log must be inspectable (toggle, advanced view, debug mode)
2. If narration contradicts events, event log takes precedence (player can verify)
3. Disputes resolved by checking event log, not narration

---

### Constraint 7: Abstention Signaling

**Requirement:** UX must clarify when **AI abstains** vs **when outcome is determined**.

**Abstention Cases (from CP-18):**
- Ruling too complex for AI to resolve (defers to human DM)
- Insufficient information to make ruling
- Ambiguous player intent

**Player Confusion Risk:**
- Player sees "AI cannot resolve this" and assumes "system is broken"
- Player doesn't know whether outcome is delayed or impossible
- Player expects AI to retry, but AI has permanently abstained

**UX Signal Required:**
- ✅ Player must know AI has abstained (not crashed, not stuck)
- ✅ Player must know why AI abstained (too complex, ambiguous intent, missing info)
- ✅ Player must know what happens next (human DM steps in, or re-prompt)

**UX Must NOT:**
- ❌ Present abstention as failure ("Error: cannot process")
- ❌ Retry indefinitely without explaining abstention
- ❌ Hide abstention reason (player needs to know why)

**Negative Case:**
```
BAD: AI abstains silently, narration says "..."
Player: "Why isn't anything happening? Is the game frozen?"
Reality: AI abstained due to complex ruling, waiting for human DM
Problem: Player doesn't know AI abstained, assumes system crashed
```

**Required Signal (enumerated, NOT designed):**
1. Abstention must be explicit: "AI cannot resolve this ruling, human DM required"
2. Abstention reason must be shown: "Ruling is too complex for current AI capabilities"
3. Next steps must be clear: "Waiting for DM input" or "Re-prompt with more detail"

---

### Constraint 8: Ledger Visibility vs Immersion

**Requirement:** UX must balance **mechanical transparency** (showing attribution, citations) with **narrative immersion** (staying in story).

**Tension:**
- High transparency: Show all citations, attributions, rule lookups → breaks immersion
- High immersion: Hide all mechanics → breeds distrust, no way to verify rulings

**Player Confusion Risk:**
- Too much transparency: "Why am I seeing PHB page numbers during combat?"
- Too little transparency: "How did the AI decide this? I don't trust it."

**UX Signal Required:**
- ✅ Player must be able to toggle transparency level (show/hide citations)
- ✅ Default transparency level must not break immersion
- ✅ Advanced users can inspect full attribution ledger

**UX Must NOT:**
- ❌ Force citations into narration ("As per PHB p.157, you take 12 damage")
- ❌ Hide citations entirely (no way to verify rulings)
- ❌ Present one transparency mode as "correct" (player preference varies)

**Negative Case:**
```
BAD: Narration includes inline citations
Narration: "The goblin attacks you (PHB p.154) and rolls a 14 (1d20+2, Monster Manual p.133). It hits your AC 15 (PHB p.119)."
Player: "This reads like a rulebook, not a story. I can't stay immersed."
```

**Required Signal (enumerated, NOT designed):**
1. Citations must be available but not forced into narration (toggle, tooltip, sidebar)
2. Default mode should prioritize immersion (hide citations unless requested)
3. Advanced mode should show full ledger (attributions, rule lookups, event provenance)

---

## Player Failure Scenarios

### Scenario 1: Player Confuses Narration Variation with Game State Change

**Setup:**
- Player saves game at turn 10
- Player loads save, replays turn 10
- Events are identical, narration text differs

**Player Expectation:** "Replay should be identical"
**Reality:** Events identical, narration regenerated (may vary)
**Failure:** Player assumes game state changed, reports bug

**Required UX Signal:**
- Explain "Events are deterministic, narration may vary"
- Show event log to prove events are identical

---

### Scenario 2: Player Disputes Mechanical Outcome Based on Narration

**Setup:**
- Event log shows: damage=12
- Narration says: "You barely scratch the goblin" (LLM interpretation)
- Player reads narration, assumes damage was low

**Player Expectation:** Narration accurately describes damage magnitude
**Reality:** Narration is cosmetic, may misrepresent magnitude
**Failure:** Player disputes damage calculation based on narration text

**Required UX Signal:**
- Event log must be inspectable (player verifies damage=12)
- Narration must not contradict events (if damage=12, don't say "scratch")

---

### Scenario 3: Player Doesn't Understand AI Abstention

**Setup:**
- Player attempts complex maneuver (grapple + disarm combo)
- AI abstains (too complex to resolve)
- No clear UX signal, player waits

**Player Expectation:** AI will resolve ruling
**Reality:** AI has abstained, waiting for human DM
**Failure:** Player assumes system is frozen, quits game

**Required UX Signal:**
- Explicit abstention message: "AI cannot resolve this, human DM required"
- Next steps: "Waiting for DM" or "Simplify action and retry"

---

### Scenario 4: Player Can't Verify RNG Determinism

**Setup:**
- Player loads save, rolls same attack, gets different result
- Player doesn't know RNG seed controls outcome

**Player Expectation:** Same input → same output
**Reality:** RNG seed changed (new timeline)
**Failure:** Player assumes "broken determinism", loses trust

**Required UX Signal:**
- RNG seed must be visible (advanced view)
- Explain "Different RNG seed = different outcomes (expected)"

---

### Scenario 5: Player Expects Save File to Store Narration Text

**Setup:**
- Player saves game, closes session
- Player loads save, narration regenerates (different text)
- Player assumes save file is corrupted

**Player Expectation:** Save file stores "everything I saw"
**Reality:** Save file stores events, narration regenerates
**Failure:** Player reports "save corruption"

**Required UX Signal:**
- Save file description: "Saves events and game state, narration regenerates on load"
- On load: "Regenerating narration..." (indicates expected behavior)

---

## Clarity Risks

### Risk 1: Overloading "Determinism" Term

**Risk:** Players assume "deterministic" means "byte-for-byte identical replay"

**Reality:** Deterministic means "events identical", presentation may vary

**Mitigation Required:**
- Use precise language: "Deterministic events" NOT "deterministic replay"
- Clarify scope: "Events are deterministic, narration may vary"

---

### Risk 2: Hidden Event Log Creates Distrust

**Risk:** Players can't verify AI rulings, assume system is arbitrary

**Reality:** Event log is authoritative, but hidden from player

**Mitigation Required:**
- Event log must be inspectable (at minimum: advanced mode toggle)
- Do NOT hide event log entirely

---

### Risk 3: Narration Contradicts Events

**Risk:** LLM narration misrepresents event magnitude (damage=12 → "barely a scratch")

**Reality:** Narration is cosmetic, may diverge from events

**Mitigation Required:**
- Narration must align with events (damage=12 cannot be narrated as "miss")
- If contradiction occurs, event log takes precedence

---

### Risk 4: Abstention Interpreted as Failure

**Risk:** Players see AI abstention as "system broken"

**Reality:** Abstention is intentional design (defer complex rulings to human)

**Mitigation Required:**
- Abstention must be framed as feature, not bug
- Explain why AI abstained (complexity, ambiguity, missing info)

---

### Risk 5: RNG Seed Changes Without Explanation

**Risk:** Players load save, outcomes differ, assume "broken determinism"

**Reality:** RNG seed changed (new timeline, intentional or bug)

**Mitigation Required:**
- RNG seed must be inspectable
- If seed changes, explain why

---

## Required UX Signals (Enumerated)

**Signal 1: Event Log Inspectability**
- Player must be able to toggle event log visibility (show raw events)
- Event log must be visually distinct from narration
- Event log must show authoritative game state (damage, HP, conditions)

**Signal 2: Determinism Scope Clarification**
- "Replay" feature must clarify: "Events identical, narration may vary"
- Do NOT use language implying total identity ("exact replay")

**Signal 3: Generated Content Labeling**
- Narration, NPC dialogue, images must be visually distinct from events
- Generated content must align with events (no contradictions)

**Signal 4: RNG Transparency**
- RNG usage must be visible (dice rolls, random events)
- RNG seed must be inspectable (advanced view)

**Signal 5: Save/Load Regeneration Notice**
- Save file description: "Saves events, narration regenerates on load"
- On load: "Regenerating narration..." (indicates expected behavior)

**Signal 6: Abstention Explicit Notice**
- Abstention must be framed as feature: "AI cannot resolve this, human DM required"
- Abstention reason must be shown: "Too complex" or "Ambiguous intent"

**Signal 7: Ledger Transparency Toggle**
- Player must be able to toggle citations/attributions visibility
- Default mode: immersion (hide citations)
- Advanced mode: full ledger (show all attributions)

---

## UX Must NOT Do (Negative Constraints)

**Must NOT 1:** Present narration as sole representation of game state
**Must NOT 2:** Hide event log entirely (creates opacity)
**Must NOT 3:** Use "replay" without clarifying scope (events vs presentation)
**Must NOT 4:** Allow narration to contradict events (if damage=12, don't say "miss")
**Must NOT 5:** Present abstention as failure ("Error: cannot process")
**Must NOT 6:** Force citations into narration (breaks immersion)
**Must NOT 7:** Hide RNG seed (prevents determinism verification)
**Must NOT 8:** Imply save files store full presentation layer (narration, audio, images)

---

## Deferred to M1 (Solutions, Not Constraints)

**This document does NOT specify:**
- ❌ How to implement event log toggle (UI design)
- ❌ Where to show citations (sidebar, tooltip, modal)
- ❌ What transparency toggle looks like (button, slider, menu)
- ❌ How to visualize RNG seed (text field, hex display, debug panel)
- ❌ What "regenerating narration" indicator looks like (spinner, progress bar)

**Solutions deferred to M1 implementation phase.**

---

## Stop Condition Met

**Question:** "What UX solutions are necessary?"
**Answer:** STOP. Solutions are M1 work, not R0 research.

This document enumerates **constraints only**. Implementation deferred.

---

## Document Governance

**Status:** R0 / RESEARCH / NON-BINDING
**Type:** Safety Specification (NOT Design)
**Approval Required From:** PM (human project owner)
**Depends On:** CP-18 (Abstention), M1 Narrator design
**Unblocks:** M1 UX implementation (when authorized)
**Future Work:** UX design (solutions, mockups, flows) deferred to M1

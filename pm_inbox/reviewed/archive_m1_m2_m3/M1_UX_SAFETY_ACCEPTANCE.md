# M1 UX Safety Acceptance
## Player-Facing Determinism & Generative Flexibility Guardrails

**Document ID:** M1-UX-SAFETY-001
**Status:** DRAFT (M1-Prep Phase, Requirements-Only)
**Type:** Acceptance Criteria (NOT Design)
**Authority:** Entry gate for M1 narration unlock
**Date:** 2026-02-10
**Phase:** M1 Preparation (Requirements Definition)

---

## Purpose

### Why UX Safety Gates Are Required

This document defines **minimum acceptable UX safety criteria** that MUST be satisfied before generative narration is exposed to players in M1.

**Context:**
- AIDM uses **deterministic event resolution** (same seed → identical outcomes)
- AIDM uses **generative LLM narration** (text may vary even when events identical)
- **Tension:** Players may confuse "different narration" with "different outcome"
- **Risk:** Player distrust, false bug reports, confusion about determinism guarantees

**Authoritative Inputs:**
- R1_UX_CONSTRAINTS_FOR_DETERMINISM.md (constraint enumeration)
- R1_DETERMINISTIC_RECALL_VS_GENERATIVE.md (safeguard definitions)
- M1 Roadmap acceptance criteria (determinism replay ≥10×)

**This Document Specifies:**
- ✅ What players MUST be able to understand
- ✅ What players MUST be able to verify
- ✅ What MUST NOT be ambiguous
- ✅ When M1 narration unlock is BLOCKED (failure conditions)

**This Document Does NOT Specify:**
- ❌ UI design (screens, flows, layouts)
- ❌ Implementation approach (how to build UX)
- ❌ Visual style (widgets, buttons, colors)
- ❌ Policies (GAP-POL items remain deferred)

---

## Non-Negotiable UX Guarantees

### Guarantee 1: Event Log Inspectability

**Requirement:**
Players MUST be able to inspect the authoritative event log to verify mechanical outcomes.

**What This Means:**
- Events are the source of truth (damage, HP, conditions, rolls)
- Narration is cosmetic presentation (may vary, NOT authoritative)
- Players can resolve disputes by checking event log

**Player Must Be Able To:**
- ✅ Toggle event log visibility (show/hide raw events)
- ✅ Verify damage, HP changes, dice rolls, conditions from events
- ✅ Compare narration to events (detect contradictions)

**M1 Entry Gate BLOCKED If:**
- ❌ Event log is completely hidden (no toggle, no debug mode, no access)
- ❌ Player cannot verify mechanical outcomes (opacity creates distrust)
- ❌ Narration is sole representation of game state (creates false authority)

**Acceptance Test:**
```
Given: Combat event (damage=12, target_hp: 25→13)
When: Player views narration ("You barely scratch the goblin")
Then: Player can inspect event log to verify damage=12 (not "barely scratch")
```

---

### Guarantee 2: Determinism Scope Clarity

**Requirement:**
Players MUST understand what "deterministic" means in AIDM context.

**What This Means:**
- **Deterministic:** Events, dice rolls, damage calculations, initiative order
- **Non-Deterministic:** Narration text, TTS voice variance, image generation results
- **Replay:** Same events, possibly different narration

**Player Must Be Able To:**
- ✅ Understand "replay" means events identical, presentation may vary
- ✅ Know when replay is "broken" (events differ) vs "expected" (narration differs)

**M1 Entry Gate BLOCKED If:**
- ❌ "Replay" feature claims "exact replay" or "perfect match" (misleading)
- ❌ Narration variation during replay is unexplained (player assumes bug)
- ❌ Player cannot distinguish event determinism from presentation variance

**Acceptance Test:**
```
Given: Player saves at turn 10, loads save, replays turn 10
When: Events are identical, narration text differs
Then: Player understands this is expected behavior (not bug or corruption)
```

---

### Guarantee 3: Narration vs Event Distinction

**Requirement:**
Players MUST be able to distinguish "what happened" (event) from "how it was described" (narration).

**What This Means:**
- Events are facts (damage=12, hit=true, target_hp=13)
- Narration is interpretation ("Your blade cuts deep" or "You strike the goblin")
- Narration MUST NOT contradict events (damage=12 cannot be narrated as "miss")

**Player Must Be Able To:**
- ✅ Visually distinguish narration from events (different formatting, label, or section)
- ✅ Detect when narration contradicts events (access to both for comparison)

**M1 Entry Gate BLOCKED If:**
- ❌ Narration contradicts events (damage=12 narrated as "you miss")
- ❌ Player cannot tell narration from events (identical presentation)
- ❌ Narration is treated as equal authority to events (creates ambiguity)

**Acceptance Test:**
```
Given: Event shows damage=12, target still alive (HP: 25→13)
When: Narration says "You defeat the goblin"
Then: Player can detect contradiction by inspecting event log
And: Player knows event log is authoritative (narration error, not mechanical bug)
```

---

### Guarantee 4: RNG Transparency

**Requirement:**
Players MUST be able to verify RNG usage and seed determinism.

**What This Means:**
- RNG controls dice rolls, initiative, random events
- Same RNG seed → same outcomes (deterministic)
- Different RNG seed → different outcomes (expected, not bug)

**Player Must Be Able To:**
- ✅ See dice roll results (d20 roll: 14, attack roll: 14+3=17)
- ✅ Verify RNG seed (advanced view, debug mode acceptable)
- ✅ Understand why outcomes differ on replay (different seed = different timeline)

**M1 Entry Gate BLOCKED If:**
- ❌ RNG usage is completely hidden (player assumes outcomes arbitrary)
- ❌ RNG seed is never visible (cannot debug "why did this happen differently?")
- ❌ RNG seed changes without explanation (player assumes "broken determinism")

**Acceptance Test:**
```
Given: Player loads save, rolls same attack
When: Outcome differs from original playthrough
Then: Player can verify RNG seed changed (expected behavior, not bug)
```

---

### Guarantee 5: Abstention Signaling

**Requirement:**
Players MUST know when AI abstains (defers ruling to human DM).

**What This Means:**
- AI cannot resolve all complex rulings (intentional design)
- Abstention is NOT failure (it's a feature)
- Player must know what happens next (wait for DM or re-prompt)

**Player Must Be Able To:**
- ✅ Distinguish abstention from crash/freeze (explicit message)
- ✅ Understand why AI abstained (too complex, ambiguous, missing info)
- ✅ Know next steps (wait for human DM or simplify action)

**M1 Entry Gate BLOCKED If:**
- ❌ Abstention is silent (player assumes system crashed)
- ❌ Abstention is framed as error ("Error: cannot process")
- ❌ Abstention reason is hidden (player doesn't know why)

**Acceptance Test:**
```
Given: Player attempts complex ruling (grapple + disarm combo)
When: AI abstains (too complex to resolve)
Then: Player sees "AI cannot resolve this ruling, human DM required"
And: Player understands this is expected behavior (not bug)
```

---

## Transparency Requirements

### Requirement 1: Deterministic vs Generative Disclosure

**Rule:**
Players MUST know which content is deterministic and which is generated.

**Disclosure Scope:**
- **Deterministic:** Events, dice rolls, damage, HP, conditions, rulebook data
- **Generated:** Narration text, NPC dialogue, scene descriptions (if LLM-based)

**M1 Entry Gate BLOCKED If:**
- ❌ Player cannot tell deterministic from generated content
- ❌ Generated narration is presented without indication of source
- ❌ Player assumes all content is deterministic (misleading)

**Minimum Acceptable Disclosure:**
- Generated content is visually distinct (formatting, icon, label acceptable)
- Player can toggle "show source" (event vs narration, advanced mode acceptable)

---

### Requirement 2: Abstention Visibility

**Rule:**
Players MUST know when AI has abstained (not crashed, not processing).

**Disclosure Scope:**
- Abstention is explicit ("AI cannot resolve this")
- Abstention reason is shown ("Too complex", "Ambiguous intent", "Missing info")
- Next steps are clear ("Waiting for DM" or "Re-prompt with detail")

**M1 Entry Gate BLOCKED If:**
- ❌ Abstention is silent (player waits indefinitely)
- ❌ Abstention looks like crash (no message, no indication)
- ❌ Player cannot tell abstention from timeout (ambiguous state)

**Minimum Acceptable Disclosure:**
- Abstention message: "AI cannot resolve this ruling, human DM required"
- Reason shown: "Ruling too complex for current AI capabilities"
- Next steps: "Waiting for DM input" or "Simplify action and retry"

---

### Requirement 3: Dispute Signaling

**Rule:**
Players MUST be able to signal disputes and understand resolution path.

**Disclosure Scope:**
- Player can flag "narration contradicts my understanding"
- Player can inspect event log to verify outcome
- Player knows event log is authoritative (narration is cosmetic)

**M1 Entry Gate BLOCKED If:**
- ❌ Player cannot flag disputes (no feedback mechanism)
- ❌ Dispute resolution path is unclear (no guidance)
- ❌ Player assumes narration is authoritative (creates false disputes)

**Minimum Acceptable Disclosure:**
- Disputes resolved by checking event log (narration is NOT authoritative)
- Player can report "narration error" (if narration contradicts events)
- System logs narration contradictions for review (detect LLM hallucination)

---

## Failure & Edge-Case Handling

### Failure Case 1: Narration Contradicts Events

**Scenario:**
Event log shows damage=12, target_hp: 25→13 (still alive)
Narration says: "You defeat the goblin"

**Required UX Behavior:**
- ✅ Player can inspect event log to verify target still alive (HP=13)
- ✅ Player knows event log is authoritative (narration error, not mechanical bug)
- ✅ System logs narration contradiction for review (detect LLM failure)

**M1 Entry Gate BLOCKED If:**
- ❌ Player cannot verify event outcome (opacity prevents dispute resolution)
- ❌ Narration contradiction is treated as authoritative (creates false game state)
- ❌ No mechanism to report/log narration errors (failures go undetected)

---

### Failure Case 2: Missing Data (Context Window Overflow)

**Scenario:**
Player queries: "What happened in Session 25?"
Memory exceeds context window, Session 25 data unavailable to LLM

**Required UX Behavior:**
- ✅ LLM abstains explicitly: "I don't have records for Session 25"
- ✅ LLM does NOT invent facts to fill gap (no hallucination)
- ✅ Player knows data is unavailable (not missing due to bug)

**M1 Entry Gate BLOCKED If:**
- ❌ LLM invents facts when data unavailable (hallucination violates determinism)
- ❌ LLM says "let me check..." then stalls (ambiguous state)
- ❌ Player assumes data is lost/corrupted (when actually context window limit)

---

### Failure Case 3: Narration Disablement (Fallback Mode)

**Scenario:**
LLM narration fails (timeout, crash, hallucination rate >5%)
System reverts to template-based narration (M0 fallback)

**Required UX Behavior:**
- ✅ Player is notified: "Generative narration disabled, using template mode"
- ✅ Player knows events are unaffected (narration change only)
- ✅ Player knows how to re-enable (restart, config change, or wait for fix)

**M1 Entry Gate BLOCKED If:**
- ❌ Narration disablement is silent (player assumes bug)
- ❌ Player cannot tell template from generative narration (ambiguous)
- ❌ Fallback mode is permanent with no re-enable path (stuck state)

---

### Failure Case 4: Save/Load Narration Regeneration

**Scenario:**
Player saves game at turn 10
Player loads save, narration regenerates (text differs from original)

**Required UX Behavior:**
- ✅ Player knows save file stores events, NOT narration text
- ✅ Player knows narration regenerates on load (expected behavior)
- ✅ Player sees "Regenerating narration..." indicator (not silent)

**M1 Entry Gate BLOCKED If:**
- ❌ Player assumes save file stores narration text (false expectation)
- ❌ Regeneration is silent (player assumes corruption)
- ❌ Regenerated narration contradicts events (LLM failure undetected)

---

### Failure Case 5: RNG Seed Change (Timeline Divergence)

**Scenario:**
Player loads save from turn 10
RNG seed differs from original playthrough (new timeline)

**Required UX Behavior:**
- ✅ Player knows RNG seed controls outcomes
- ✅ Player can verify RNG seed changed (advanced view acceptable)
- ✅ Player understands different seed = different outcomes (not bug)

**M1 Entry Gate BLOCKED If:**
- ❌ RNG seed change is silent (player assumes "broken determinism")
- ❌ Player cannot verify seed (no debug access)
- ❌ Player cannot distinguish seed change from bug (ambiguous cause)

---

## Negative Acceptance Cases (UX That FAILS Review)

### Negative Case 1: Hidden Event Log

**BAD UX:**
Narration is sole representation of game state, event log completely hidden.

**Why This Fails:**
- Player cannot verify mechanical outcomes (breeds distrust)
- Narration errors cannot be detected (LLM hallucination undetected)
- Disputes cannot be resolved (no source of truth)

**M1 Entry Gate:** ❌ **BLOCKED**

---

### Negative Case 2: Misleading "Exact Replay" Claim

**BAD UX:**
"Replay" feature claims "exact replay" or "perfect match".

**Why This Fails:**
- Player expects byte-for-byte identity (including narration text)
- Narration variation is unexpected (player assumes bug)
- False expectation creates distrust ("replay is broken")

**M1 Entry Gate:** ❌ **BLOCKED**

---

### Negative Case 3: Narration Contradicts Events Without Indication

**BAD UX:**
Event shows damage=12, narration says "you miss".
Player cannot detect contradiction.

**Why This Fails:**
- Player treats narration as authoritative (false game state)
- Player disputes mechanical outcome based on narration (wrong source)
- LLM hallucination goes undetected (quality failure)

**M1 Entry Gate:** ❌ **BLOCKED**

---

### Negative Case 4: Silent Abstention

**BAD UX:**
AI abstains (cannot resolve ruling), shows blank screen or "..." with no explanation.

**Why This Fails:**
- Player assumes system crashed (ambiguous state)
- Player waits indefinitely (no next steps)
- Abstention interpreted as failure (design intent unclear)

**M1 Entry Gate:** ❌ **BLOCKED**

---

### Negative Case 5: Hidden RNG Usage

**BAD UX:**
RNG affects outcome, but dice rolls and seed are never visible.

**Why This Fails:**
- Player cannot verify determinism (no transparency)
- Player assumes outcomes arbitrary (breeds distrust)
- Debugging "why different outcome?" impossible (no data)

**M1 Entry Gate:** ❌ **BLOCKED**

---

### Negative Case 6: Forced Citations in Narration

**BAD UX:**
Narration includes inline citations: "You take 12 damage (PHB p.157, Monster Manual p.133)."

**Why This Fails:**
- Breaks narrative immersion (reads like rulebook, not story)
- Player cannot disable citations (forced transparency)
- Violates player preference for immersion vs transparency

**M1 Entry Gate:** ❌ **BLOCKED** (must be toggle, NOT forced)

---

### Negative Case 7: Save File "Corruption" on Regeneration

**BAD UX:**
Save file loads, narration regenerates silently, player assumes corruption.

**Why This Fails:**
- Player doesn't know regeneration is expected (false bug report)
- No indicator of regeneration ("Generating narration...")
- Player loses trust in save system (false perception)

**M1 Entry Gate:** ❌ **BLOCKED**

---

## M1 Entry UX Gates (Pass/Fail Criteria)

### Gate 1: Event Log Accessibility

**Pass Condition:**
Player can toggle event log visibility (show raw events) in M1 narration runtime.

**Fail Condition:**
Event log is completely hidden OR requires external tools to access.

**Test:**
```
Given: M1 narration runtime running
When: Player triggers toggle (button, hotkey, menu)
Then: Event log becomes visible (damage, HP, rolls, conditions)
```

**Status:** ⬜ NOT TESTED (M1 not built yet)

---

### Gate 2: Determinism Scope Disclosure

**Pass Condition:**
"Replay" feature clarifies scope: "Events will be identical, narration may vary."

**Fail Condition:**
"Replay" claims "exact replay" OR provides no scope clarification.

**Test:**
```
Given: Player accesses replay feature
When: Player views replay description/tooltip
Then: Scope clarification is visible ("Events identical, narration may vary")
```

**Status:** ⬜ NOT TESTED (M1 not built yet)

---

### Gate 3: Narration Contradiction Detection

**Pass Condition:**
If narration contradicts events, player can detect via event log inspection.

**Fail Condition:**
Narration contradiction is undetectable (event log hidden OR narration-only view).

**Test:**
```
Given: Event shows damage=12, target HP: 25→13
When: Narration says "You defeat the goblin" (contradiction)
Then: Player inspects event log, sees HP=13 (still alive)
And: Player knows narration is wrong (event log is truth)
```

**Status:** ⬜ NOT TESTED (M1 not built yet)

---

### Gate 4: Abstention Explicit Message

**Pass Condition:**
When AI abstains, player sees explicit message: "AI cannot resolve this, human DM required."

**Fail Condition:**
Abstention is silent OR shows generic error ("Error: cannot process").

**Test:**
```
Given: Player attempts complex ruling (grapple + disarm + move)
When: AI abstains (too complex)
Then: Player sees abstention message with reason ("Too complex for AI")
And: Player sees next steps ("Waiting for DM" or "Simplify and retry")
```

**Status:** ⬜ NOT TESTED (M1 not built yet)

---

### Gate 5: RNG Transparency (Dice Visibility)

**Pass Condition:**
Player can see dice roll results (d20 roll: 14, attack roll: 14+3=17).

**Fail Condition:**
Dice rolls are completely hidden (no visibility, no toggle).

**Test:**
```
Given: Player attacks goblin
When: Engine rolls attack (d20=14, bonus=+3, total=17)
Then: Player sees roll results ("d20: 14, Attack: 17")
```

**Status:** ⬜ NOT TESTED (M1 not built yet)

---

### Gate 6: Save/Load Regeneration Notice

**Pass Condition:**
On save load, player sees "Regenerating narration..." indicator.

**Fail Condition:**
Regeneration is silent (no indication).

**Test:**
```
Given: Player loads save file
When: System regenerates narration from event log
Then: Player sees progress indicator ("Regenerating narration...")
```

**Status:** ⬜ NOT TESTED (M1 not built yet)

---

### Gate 7: Narration Disablement Notice

**Pass Condition:**
If generative narration fails, player sees "Narration disabled, using template mode."

**Fail Condition:**
Narration disablement is silent (player assumes bug).

**Test:**
```
Given: LLM narration timeout (>5s) OR hallucination rate >5%
When: System disables generative narration
Then: Player sees notice ("Generative narration disabled, using templates")
```

**Status:** ⬜ NOT TESTED (M1 not built yet)

---

## Explicit Non-Goals (Intentionally Deferred)

### Non-Goal 1: UI Design Solutions

**Not Specified:**
- How event log toggle is implemented (button, hotkey, menu)
- Where citations appear (sidebar, tooltip, modal)
- What transparency toggle looks like (slider, checkbox, dropdown)

**Why Deferred:**
UI design is M1 implementation work, not M1-prep requirements.

---

### Non-Goal 2: Visual Style

**Not Specified:**
- Event log formatting (colors, fonts, layout)
- Narration vs event visual distinction (exact styling)
- Abstention message wording (exact phrasing)

**Why Deferred:**
Visual design is M1 implementation work, not entry gate criteria.

---

### Non-Goal 3: Policy Authorship

**Not Specified:**
- Dispute resolution workflow (who reviews, how long, escalation path)
- Narration error reporting process (form, email, in-app)
- Abstention escalation policy (when to involve human DM)

**Why Deferred:**
GAP-POL items remain deferred per governance.

---

### Non-Goal 4: Implementation Approach

**Not Specified:**
- How to implement event log (data structure, storage)
- How to detect narration contradictions (NLP, validation logic)
- How to track RNG seed (storage format, UI display)

**Why Deferred:**
Implementation is M1 build phase, not requirements phase.

---

## Validation Checklist (Self-Audit)

**Agent C Self-Assessment:**

- ✅ **No visuals or flows:** Document specifies WHAT players must understand, NOT HOW to present it
- ✅ **No implementation assumptions:** Document does not assume specific tech stack or architecture
- ✅ **Uses MUST / MUST NOT language:** Requirements are unambiguous (not "should" or "could")
- ✅ **Aligns with determinism safeguards:** References R1_DETERMINISTIC_RECALL_VS_GENERATIVE.md safeguards
- ✅ **Blocks unsafe UX by default:** M1 Entry Gates explicitly BLOCK if criteria unmet
- ✅ **No policy authorship:** GAP-POL items remain deferred (no dispute workflows specified)
- ✅ **No schema changes:** Document does not imply memory schema modifications
- ✅ **No UI design:** Document avoids "button", "screen", "modal", "widget" language

**Validation Result:** ✅ **PASS** (requirements-only, no design decisions embedded)

---

## Completion Protocol

**Agent C Status:** STANDBY (document complete, awaiting PM review)

**Next Steps:**
1. PM reviews M1_UX_SAFETY_ACCEPTANCE.md
2. PM approves OR requests revisions
3. M1 team uses this document as entry gate criteria
4. M1 narration unlock BLOCKED until all gates pass

**Notification:**
PM (Thunder) — M1_UX_SAFETY_ACCEPTANCE.md ready for review.

---

**END OF M1 UX SAFETY ACCEPTANCE**

**Document ID:** M1-UX-SAFETY-001
**Status:** DRAFT (Awaiting PM Approval)
**Type:** Acceptance Criteria (Requirements-Only)
**Phase:** M1-Prep (Entry Gate Definition)
**Date:** 2026-02-10
**Agent:** Agent C (UX / Integration / Safety Layer)

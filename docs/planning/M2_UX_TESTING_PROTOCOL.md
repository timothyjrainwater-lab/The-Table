# M2 UX Testing Protocol — LLM-Driven Interactions

**Status:** M2 / PLANNING / NON-BINDING
**Purpose:** Define UX testing scenarios and feedback protocols for M2 LLM integration
**Authority:** Planning only (requires PM approval before execution)
**Last Updated:** 2026-02-10
**Lead:** Agent C (UX Testing)

---

## ⚠️ PLANNING NOTICE

This document defines **UX testing protocols** for M2 LLM-driven interactions.

**Execution Prerequisites:**
1. Agent A confirms LLM integration operational
2. M2 system deployed and accessible
3. Test users/environment available
4. PM approves testing protocol

**Do not execute tests** until all prerequisites met.

---

## Testing Objectives

### Primary Goals
1. **Validate narrative flow** - Does LLM narration feel natural and coherent?
2. **Assess player input handling** - Does system understand player intent correctly?
3. **Measure clarity** - Do players understand what's happening and why?
4. **Evaluate engagement** - Do players stay immersed or get frustrated?

### Success Criteria
- ✅ Players can complete basic scenarios without confusion
- ✅ LLM narration aligns with deterministic events (no contradictions)
- ✅ Players understand when AI abstains vs when it rules
- ✅ Players can verify outcomes via event log

### Failure Indicators
- ❌ Players report "I don't know what happened"
- ❌ Players dispute outcomes based on narration mismatches
- ❌ Players assume system is broken when AI abstains
- ❌ Players cannot find event log or verify outcomes

---

## Test Scenarios

### Scenario 1: Basic Combat Flow
**Objective:** Test LLM narration of deterministic combat events

**Setup:**
- PC (fighter, level 5) vs Goblin (MM p.133)
- Simple attack sequence (3 rounds)
- Mix of hits, misses, critical hit

**Test Flow:**
1. Player declares attack: "I attack the goblin with my sword"
2. System rolls attack (1d20+8), compares to goblin AC 15
3. LLM generates narration from event
4. Player reads narration, verifies outcome makes sense

**Success Criteria:**
- Narration accurately reflects hit/miss outcome
- Damage narration aligns with actual damage rolled (e.g., 12 damage → "significant blow", not "scratch")
- Critical hit narration feels impactful (not understated)

**Failure Criteria:**
- Narration says "miss" when event shows hit=true
- Damage magnitude misrepresented (12 damage → "barely hurts")
- Critical hit narrated as normal hit

**Metrics:**
- Time to complete: <5 minutes expected
- Player confusion incidents: 0 expected
- Narration-event alignment: 100% expected

---

### Scenario 2: Ambiguous Player Intent
**Objective:** Test AI abstention and clarification flow

**Setup:**
- PC attempts complex action: "I want to grapple the goblin and disarm him at the same time"
- This requires clarification (grapple first, then disarm? Or simultaneous?)

**Test Flow:**
1. Player declares ambiguous action
2. System detects ambiguity, AI abstains
3. System requests clarification: "Do you want to grapple first, then disarm? Or attempt both simultaneously?"
4. Player clarifies intent
5. System resolves action

**Success Criteria:**
- AI abstention is clear and helpful (not error-like)
- Clarification request is specific (not generic "error")
- Player understands why clarification needed
- Player can proceed after clarifying

**Failure Criteria:**
- System attempts to guess intent (leads to wrong outcome)
- Abstention message is generic error: "Cannot process"
- No guidance on how to clarify
- Player assumes system is broken

**Metrics:**
- Abstention clarity: Player rates "helpful" vs "confusing"
- Time to resolution: <2 minutes from abstention to clarification
- Player frustration: Low (abstention explained well)

---

### Scenario 3: Event Log Verification
**Objective:** Test player ability to verify outcomes via event log

**Setup:**
- PC takes 12 damage from goblin attack
- LLM narration may vary in interpretation
- Player wants to verify exact damage

**Test Flow:**
1. Combat event occurs (goblin hits, damage=12)
2. Player reads narration: "The goblin's blade cuts into your shoulder"
3. Player wants exact damage number
4. Player toggles event log view
5. Event log shows: `damage_dealt: 12, hp_before: 45, hp_after: 33`

**Success Criteria:**
- Event log accessible within 2 clicks (toggle, menu, keybind)
- Event log shows critical fields: event_type, damage, HP change
- Event log is visually distinct from narration
- Player can verify narration aligns with events

**Failure Criteria:**
- Event log hidden with no access method
- Event log missing critical fields (damage not shown)
- Event log looks identical to narration (indistinguishable)
- Player cannot verify outcome

**Metrics:**
- Event log access time: <5 seconds
- Event log comprehension: Player can find damage value within 10 seconds
- Visual distinction: Player correctly identifies event log vs narration

---

### Scenario 4: Narration Variation on Replay
**Objective:** Test player understanding of determinism scope

**Setup:**
- Player saves game at turn 5
- Player loads save, replays turn 5
- Events identical, narration text differs

**Test Flow:**
1. Original playthrough: Goblin attack hits, narration: "The goblin's rusty blade slashes your arm"
2. Save game
3. Load save, replay turn 5
4. Replay: Same event (hit=true, damage=12), different narration: "The goblin strikes your shoulder with precision"
5. Player notices narration difference

**Success Criteria:**
- Player sees explanation: "Events are identical, narration may vary"
- Player can verify events match (same damage, same HP change)
- Player understands variation is cosmetic (not mechanical)
- Player does not report "replay broken"

**Failure Criteria:**
- No explanation of narration variation
- Player assumes replay is bugged
- Player cannot verify events match
- Player loses trust in determinism

**Metrics:**
- Player understanding: "Do you think replay is working correctly?" (Yes expected)
- Confusion incidents: 0 expected
- False bug reports: 0 expected

---

### Scenario 5: Ledger Transparency Toggle
**Objective:** Test citation visibility without breaking immersion

**Setup:**
- Player in combat, wants to verify rules
- Player toggles citation view

**Test Flow:**
1. Default mode: Narration only, no citations
2. Player toggles citations ON (settings, keybind)
3. Citations appear: "Goblin attack: PHB p.154, damage: PHB p.145"
4. Player verifies rules
5. Player toggles citations OFF
6. Citations disappear, narration returns to immersive mode

**Success Criteria:**
- Citations accessible but not forced
- Default mode hides citations (immersion priority)
- Advanced mode shows citations clearly
- Toggle is easy to find (settings, keybind, menu)

**Failure Criteria:**
- Citations forced into narration (cannot hide)
- Citations completely hidden (cannot access)
- No toggle exists
- Toggle is obscure (buried in menus)

**Metrics:**
- Toggle access time: <10 seconds to find
- Immersion preservation: Narration readable without citations
- Citation usefulness: Player can verify rules when needed

---

## Feedback Collection Framework

### Quantitative Metrics

**Completion Metrics:**
- Time to complete each scenario
- Number of clarification requests needed
- Number of event log accesses
- Number of failed attempts

**Error Metrics:**
- Narration-event misalignment incidents
- False bug reports (player thinks system broken)
- Confusion incidents (player says "I don't understand")

**Engagement Metrics:**
- Session length before player disengages
- Player-reported immersion rating (1-10 scale)
- Player-reported trust rating (1-10 scale)

### Qualitative Feedback

**Post-Scenario Questions:**
1. "What just happened in that scenario?" (comprehension check)
2. "Did the narration match what you expected?" (alignment check)
3. "Did you feel confused at any point? When?" (clarity check)
4. "Did you trust the system's rulings?" (trust check)
5. "Would you prefer text-only or LLM narration?" (preference check)

**Exit Interview:**
1. "What worked well?"
2. "What was frustrating?"
3. "What would you change?"
4. "Would you use this system for a real D&D game?"

### Observation Protocol

**Observer watches for:**
- **Confusion signals:** Furrowed brow, re-reading, saying "wait, what?"
- **Frustration signals:** Sighing, clicking rapidly, saying "this is broken"
- **Engagement signals:** Leaning forward, smiling, narrating along
- **Distrust signals:** Checking event log repeatedly, disputing outcomes

**Observer notes:**
- When confusion/frustration occurs (timestamp, context)
- What triggered it (narration mismatch, abstention, etc.)
- How player resolved it (event log, retry, give up)

---

## Test Environment Requirements

### Technical Requirements
- M2 system operational (LLM integration complete)
- Test scenarios pre-configured (combat setups, saved games)
- Event log accessible (toggle implemented)
- Citation toggle implemented (if in scope)

### User Requirements
- 5-10 test participants (D&D players, varying experience levels)
- 30-60 minutes per participant
- Screen recording enabled (for playback analysis)
- Observer present (live or remote)

### Data Collection Tools
- Screen recording software
- Observation notes template
- Post-scenario questionnaire
- Exit interview script

---

## Coordination with Agent A & B

### Agent A (LLM Integration)
**Needed from Agent A:**
- LLM model selection confirmed (which model?)
- Narration generation working (can produce text from events?)
- Abstention cases identified (when does LLM abstain?)
- Schema alignment verified (LLM output matches event schema?)

**Feedback to Agent A:**
- Narration quality issues (misalignments, contradictions)
- Abstention clarity feedback (was it helpful?)
- LLM performance metrics (latency, coherence)

### Agent B (Schema Validation)
**Needed from Agent B:**
- Event schema stable (no changes during testing)
- Event log serialization working (can inspect events?)
- Citation schema ready (if ledger toggle in scope)

**Feedback to Agent B:**
- Schema usability (is event log readable by players?)
- Missing fields (what should be in event log but isn't?)
- Serialization issues (event log formatting problems)

---

## Risk Mitigation

### Risk 1: LLM Narration Quality Too Low
**Risk:** LLM produces incoherent or contradictory narration
**Mitigation:** Test with text-only fallback available (player can disable LLM)
**Escalation:** If >30% of narration is contradictory, flag for Agent A

### Risk 2: Players Don't Understand Abstention
**Risk:** Players interpret abstention as "system broken"
**Mitigation:** Pre-test abstention messaging (adjust wording based on feedback)
**Escalation:** If >50% of players confused by abstention, redesign messaging

### Risk 3: Event Log Too Technical
**Risk:** Event log is unreadable by non-technical players
**Mitigation:** Test with mixed experience levels (novice + expert D&D players)
**Escalation:** If novice players cannot use event log, simplify presentation

### Risk 4: Test Environment Not Ready
**Risk:** M2 system crashes, LLM unavailable, test scenarios broken
**Mitigation:** Pre-test all scenarios before live user testing
**Escalation:** If environment unstable, pause testing until fixed

---

## Execution Checklist

**Pre-Testing (Agent C):**
- [ ] Confirm Agent A LLM integration ready
- [ ] Verify M2 system operational
- [ ] Prepare test scenarios (combat setups, saves)
- [ ] Recruit 5-10 test participants
- [ ] Set up screen recording + observation tools
- [ ] Pre-test scenarios (dry run)

**During Testing (Agent C):**
- [ ] Run each participant through 5 scenarios
- [ ] Observe and take notes (confusion, frustration, engagement)
- [ ] Collect post-scenario feedback
- [ ] Conduct exit interview

**Post-Testing (Agent C):**
- [ ] Analyze quantitative metrics (completion time, errors)
- [ ] Analyze qualitative feedback (common themes)
- [ ] Identify pain points (what frustrated users most?)
- [ ] Provide feedback to Agent A (LLM quality) and Agent B (schema usability)
- [ ] Document recommendations (M2 UX improvements)

---

## Deliverables

**Testing Report:**
- Summary of findings (what worked, what didn't)
- Quantitative metrics (completion times, error rates)
- Qualitative themes (common feedback patterns)
- Pain point analysis (top 3 frustrations)
- Recommendations (prioritized UX improvements)

**Feedback to Agents:**
- Agent A: LLM narration quality report
- Agent B: Schema usability report
- PM: M2 UX readiness assessment (go/no-go)

---

## Status

**Current State:** READY FOR EXECUTION (pending Agent A confirmation)

**Blocking On:**
- Agent A LLM integration confirmation
- M2 system deployment
- Test participant recruitment

**Next Step:** Await Agent A signal "M2 LLM integration ready for UX testing"

---

## Document Governance

**Status:** M2 / PLANNING / NON-BINDING
**Purpose:** UX testing protocol for M2 LLM integration
**Approval Required From:** PM + Agent A (LLM ready) + Agent B (schema stable)
**Depends On:** Agent A LLM integration completion
**Blocks:** M2 UX feedback delivery, M2 go/no-go decision
**Future Work:** Execute tests (when M2 ready), analyze results, provide feedback

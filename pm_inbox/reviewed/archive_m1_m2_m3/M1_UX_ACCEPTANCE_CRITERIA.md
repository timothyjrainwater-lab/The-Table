# M1 UX Acceptance Criteria

**Status:** M0 / PLANNING / NON-BINDING
**Purpose:** Define testable UX requirements for M1 implementation
**Authority:** Planning only (requires PM approval before M1 gates)
**Last Updated:** 2026-02-10
**Source:** R1_UX_CONSTRAINTS_FOR_DETERMINISM.md

---

## ⚠️ PLANNING NOTICE

This document converts R0 UX constraints into **testable acceptance criteria** for M1.

**This is NOT:**
- ❌ A UX design specification
- ❌ A wireframe or mockup
- ❌ An interaction flow diagram
- ❌ A visual design guide

**This IS:**
- ✅ Pass/fail statements for UX review
- ✅ Negative acceptance cases (what fails review)
- ✅ Testable requirements (observable, verifiable)

**Purpose:** Block bad UX implementations, NOT design good UX.

---

## How to Use This Document

### For Reviewers
Each criterion has:
- **Criterion ID:** Unique identifier (AC-UX-001, etc.)
- **Pass Condition:** What must be true for acceptance
- **Fail Condition:** What causes rejection
- **Test Method:** How to verify

### Review Protocol
1. Implement UX (designer/developer)
2. Test against criteria (QA/reviewer)
3. If ANY criterion fails → reject implementation
4. If ALL criteria pass → accept for M1

### Failure Response
- **Minor fail:** Fix and re-test
- **Major fail:** Redesign and re-test
- **Blocker fail:** Escalate to PM (acceptance criteria may be wrong)

---

## Acceptance Criteria

### AC-UX-001: Event Log Inspectability

**Pass Condition:**
- Player can view raw event log at any time during session
- Event log shows: event_type, timestamp, event_id, payload
- Event log is visually distinct from narration (different formatting)

**Fail Condition:**
- Event log hidden with no way to access
- Event log mixed with narration (indistinguishable)
- Event log missing critical fields (event_type, payload)

**Test Method:**
1. Start session
2. Trigger event (attack, move, spell cast)
3. Attempt to view event log (toggle, menu, keybind)
4. Verify event appears with type, ID, timestamp, payload
5. Verify event log is visually distinct from narration

**Priority:** CRITICAL (blocks player verification of game state)

---

### AC-UX-002: Determinism Scope Clarification

**Pass Condition:**
- "Replay" feature includes explanation: "Events are identical, narration may vary"
- Language does NOT use "exact replay", "perfect match", "identical session"
- First-time replay shows one-time notice explaining scope

**Fail Condition:**
- "Replay" feature has no explanation of scope
- Language implies byte-for-byte identity ("exact replay")
- Player discovers narration variation with no warning

**Test Method:**
1. Save game at turn 10
2. Load save and trigger replay
3. Verify explanation appears (inline, tooltip, modal)
4. Verify language is precise ("events identical, narration may vary")
5. Trigger narration variation, verify no confusion signal

**Priority:** HIGH (prevents false "replay broken" bug reports)

---

### AC-UX-003: Generated Content Labeling

**Pass Condition:**
- Narration text is visually distinct from events (font, color, icon, formatting)
- Generated content (narration, NPC dialogue) has visual indicator (e.g., quotation marks, italics, border)
- Event log and generated content cannot be confused

**Fail Condition:**
- Narration appears identical to events (same formatting)
- No visual distinction between deterministic and generated content
- Player cannot tell which content is authoritative

**Test Method:**
1. Trigger event with narration (attack hit, damage dealt)
2. View event log entry
3. View narration text
4. Verify visual distinction exists (different font, color, icon, formatting)
5. Verify player can identify which is authoritative (should be event log)

**Priority:** HIGH (prevents narration being treated as ground truth)

---

### AC-UX-004: Narration-Event Alignment

**Pass Condition:**
- Narration accurately reflects event payload (damage=12 → narration mentions ~12 damage)
- Narration does NOT contradict events (damage=12 → narration cannot say "miss")
- If narration contradicts event, event log is correct (player can verify)

**Fail Condition:**
- Narration contradicts events (damage=12 → narration says "you miss")
- Narration misrepresents magnitude (damage=12 → "barely a scratch")
- No way to verify contradiction (event log hidden)

**Test Method:**
1. Trigger event with quantifiable outcome (attack damage=12)
2. Read narration text
3. Verify narration aligns with event ("12 damage", "significant hit", etc.)
4. Check event log shows damage=12
5. If contradiction found, verify event log takes precedence

**Priority:** CRITICAL (narration contradictions break trust)

---

### AC-UX-005: RNG Transparency

**Pass Condition:**
- RNG usage is visible (dice roll results shown: "Rolled 1d20: 14")
- RNG seed is inspectable (advanced view, debug panel)
- If outcome is RNG-driven, player can see roll result

**Fail Condition:**
- RNG usage hidden (player sees outcome but not roll)
- RNG seed not inspectable (cannot verify determinism)
- No indication that outcome was random

**Test Method:**
1. Trigger RNG event (attack roll, saving throw)
2. Verify roll result is shown ("Rolled 1d20+2: 16")
3. Access advanced view (settings, debug panel)
4. Verify RNG seed is visible (hex string, integer)
5. Verify same seed → same roll (determinism check)

**Priority:** HIGH (enables determinism verification)

---

### AC-UX-006: Save/Load Regeneration Notice

**Pass Condition:**
- Save file description clarifies scope: "Saves events and game state, narration regenerates on load"
- On load, regeneration indicator appears: "Regenerating narration from event log..."
- Player knows regeneration is expected (not a bug)

**Fail Condition:**
- Save file description implies full presentation storage ("Saves everything")
- Load happens silently with no regeneration indicator
- Player discovers narration variation with no warning

**Test Method:**
1. View save file description (save dialog, help text)
2. Verify scope clarification: "narration regenerates on load"
3. Save game, close session
4. Load save file
5. Verify regeneration indicator appears
6. Verify narration may differ from original (expected)

**Priority:** MEDIUM (prevents "save corruption" false reports)

---

### AC-UX-007: Abstention Explicit Notice

**Pass Condition:**
- Abstention shows explicit message: "AI cannot resolve this ruling, human DM required"
- Abstention reason is shown: "Ruling too complex" or "Ambiguous player intent"
- Next steps are clear: "Waiting for DM input" or "Simplify action and retry"

**Fail Condition:**
- Abstention is silent (player waits indefinitely)
- Abstention message is generic error ("Error: cannot process")
- No next steps shown (player doesn't know what to do)

**Test Method:**
1. Trigger abstention case (complex maneuver, ambiguous intent)
2. Verify explicit abstention message appears
3. Verify reason is shown ("Too complex for AI")
4. Verify next steps are clear ("Waiting for DM" or "Retry with simpler action")
5. Verify abstention is NOT framed as error/bug

**Priority:** CRITICAL (abstention is feature, not bug)

---

### AC-UX-008: Ledger Transparency Toggle

**Pass Condition:**
- Player can toggle citation visibility (show/hide attributions)
- Default mode hides citations (prioritizes immersion)
- Advanced mode shows citations (PHB p.157, MM p.133, etc.)
- Toggle is accessible (settings, keybind, menu)

**Fail Condition:**
- Citations forced into narration (cannot hide)
- Citations completely hidden (cannot access)
- No toggle exists (single transparency level only)

**Test Method:**
1. View narration with default settings
2. Verify citations are hidden (immersive mode)
3. Toggle citations on (settings, keybind, menu)
4. Verify citations appear (PHB p.157, event provenance)
5. Toggle citations off, verify they disappear

**Priority:** MEDIUM (balances transparency and immersion)

---

### AC-UX-009: No Forced Citations in Narration

**Pass Condition:**
- Narration text does NOT include inline citations ("As per PHB p.157, you take 12 damage")
- Citations are available separately (tooltip, sidebar, ledger view)
- Narration reads like story, not rulebook

**Fail Condition:**
- Narration includes citations inline (breaks immersion)
- No way to access citations separately (forced choice: citations or no citations)

**Test Method:**
1. Read narration text in default mode
2. Verify no inline citations appear
3. Hover/click/inspect to view citations separately
4. Verify narration maintains narrative tone (not rulebook tone)

**Priority:** HIGH (forced citations break immersion)

---

### AC-UX-010: RNG Seed Change Warning

**Pass Condition:**
- If RNG seed changes between saves, player is warned: "Different RNG seed detected, outcomes may differ"
- Seed change reason is shown if known: "New game started" vs "Loaded from different timeline"
- Player can inspect current RNG seed (advanced view)

**Fail Condition:**
- RNG seed changes silently (no warning)
- Player discovers different outcomes with no explanation
- No way to identify seed change

**Test Method:**
1. Save game with RNG seed A
2. Start new game (RNG seed B)
3. Load save from seed A
4. Verify warning appears: "RNG seed changed, outcomes may differ"
5. Verify player can inspect both seeds (advanced view)

**Priority:** MEDIUM (prevents "broken determinism" false reports)

---

### AC-UX-011: Event Log as Ground Truth

**Pass Condition:**
- Documentation states: "Event log is authoritative, narration is cosmetic"
- If dispute arises, event log resolution is clear: "Check event log to verify"
- Player can resolve mechanical disputes by inspecting event log

**Fail Condition:**
- No guidance on which source is authoritative
- Narration treated as equal authority to events
- No way to resolve disputes

**Test Method:**
1. Create scenario where narration and event log could diverge (damage calculation)
2. Check documentation/help text
3. Verify event log is stated as authoritative
4. Simulate dispute, verify player knows to check event log
5. Verify event log resolves dispute

**Priority:** HIGH (establishes hierarchy of truth)

---

### AC-UX-012: No "Exact Replay" Language

**Pass Condition:**
- Replay feature does NOT use language: "exact replay", "perfect match", "identical session"
- Language is precise: "same events", "same outcomes", "deterministic events"
- Player expectations are calibrated correctly

**Fail Condition:**
- "Exact replay" language used
- Player expects byte-for-byte identity
- No clarification of scope

**Test Method:**
1. View replay feature description (UI text, help text)
2. Verify language does NOT include "exact", "perfect", "identical"
3. Verify language IS precise: "same events, possibly different narration"
4. Survey users: "What do you expect from replay?" (should NOT say "byte-for-byte identical")

**Priority:** HIGH (manages player expectations)

---

### AC-UX-013: Regeneration Failure Fallback

**Pass Condition:**
- If narration regeneration fails, fallback is clear: "Narration unavailable, showing event log"
- Player can continue playing with event log only (no blocking error)
- Failure is explained: "Narration generation failed (LLM unavailable)"

**Fail Condition:**
- Regeneration failure blocks play (modal error, cannot proceed)
- No fallback to event log
- Failure is silent (player sees nothing)

**Test Method:**
1. Simulate narration regeneration failure (disable LLM, corrupt cache)
2. Load save file
3. Verify fallback message appears: "Narration unavailable, showing event log"
4. Verify player can continue playing (view event log only)
5. Verify failure reason is shown

**Priority:** MEDIUM (graceful degradation)

---

### AC-UX-014: Abstention Reason Enumeration

**Pass Condition:**
- Abstention reasons are specific, not generic:
  - "Ruling too complex for AI (requires human DM)"
  - "Ambiguous player intent (clarify action)"
  - "Insufficient information (provide missing details)"
- Player knows exactly why AI abstained

**Fail Condition:**
- Abstention reason is generic: "Error: cannot process"
- No reason shown (player must guess why)
- Reason is technical jargon (player doesn't understand)

**Test Method:**
1. Trigger each abstention category (complex ruling, ambiguous intent, missing info)
2. Verify specific reason appears
3. Verify reason is human-readable (not error code)
4. Verify reason guides player to resolution

**Priority:** HIGH (abstention must be understandable)

---

### AC-UX-015: No Hidden Regeneration

**Pass Condition:**
- If content regenerates (narration, images), player is notified: "Regenerating..."
- Regeneration progress is visible (spinner, progress bar, status text)
- Player knows system is working (not frozen)

**Fail Condition:**
- Regeneration happens silently (long pause with no feedback)
- Player assumes system crashed
- No indication of progress

**Test Method:**
1. Load save file (triggers narration regeneration)
2. Verify regeneration indicator appears within 500ms
3. Verify indicator updates (progress, status text)
4. Verify player can distinguish "working" from "frozen"

**Priority:** MEDIUM (prevents "system frozen" false reports)

---

## Negative Acceptance Cases (Auto-Fail)

### NAC-001: Event Log Completely Hidden
**If:** Event log has no access method (toggle, menu, keybind)
**Then:** REJECT immediately (violates AC-UX-001)

### NAC-002: Narration Contradicts Events
**If:** Narration says "miss" but event shows hit=true
**Then:** REJECT immediately (violates AC-UX-004)

### NAC-003: Forced Citations in Narration
**If:** Narration includes "(PHB p.157)" inline
**Then:** REJECT immediately (violates AC-UX-009)

### NAC-004: Silent Abstention
**If:** AI abstains with no message (player waits indefinitely)
**Then:** REJECT immediately (violates AC-UX-007)

### NAC-005: "Exact Replay" Language
**If:** UI text says "exact replay" or "perfect match"
**Then:** REJECT immediately (violates AC-UX-012)

### NAC-006: RNG Seed Completely Hidden
**If:** No way to inspect RNG seed (even in advanced view)
**Then:** REJECT immediately (violates AC-UX-005)

### NAC-007: No Determinism Scope Clarification
**If:** "Replay" feature has no explanation of what is deterministic
**Then:** REJECT immediately (violates AC-UX-002)

### NAC-008: Regeneration Blocks Play
**If:** Narration regeneration failure prevents player from continuing
**Then:** REJECT immediately (violates AC-UX-013)

---

## Test Protocol

### Phase 1: Smoke Test (5 Critical Criteria)
**Must pass before detailed review:**
1. AC-UX-001: Event log inspectable
2. AC-UX-004: Narration aligns with events
3. AC-UX-007: Abstention explicit
4. AC-UX-009: No forced citations
5. AC-UX-011: Event log as ground truth

**If any fail:** STOP, fix critical issues before continuing.

### Phase 2: Functional Test (7 High-Priority Criteria)
**Must pass for M1 acceptance:**
1. AC-UX-002: Determinism scope clarified
2. AC-UX-003: Generated content labeled
3. AC-UX-005: RNG transparency
4. AC-UX-012: No "exact replay" language
5. AC-UX-014: Abstention reasons specific

**If any fail:** Redesign and re-test.

### Phase 3: Polish Test (3 Medium-Priority Criteria)
**Should pass for quality:**
1. AC-UX-006: Save/load regeneration notice
2. AC-UX-008: Ledger transparency toggle
3. AC-UX-010: RNG seed change warning
4. AC-UX-013: Regeneration failure fallback
5. AC-UX-015: No hidden regeneration

**If any fail:** Fix if time allows, else document as known issue.

---

## Acceptance Matrix

| Criterion ID | Priority | Phase | Pass Required |
|--------------|----------|-------|---------------|
| AC-UX-001 | CRITICAL | Phase 1 | YES (blocking) |
| AC-UX-002 | HIGH | Phase 2 | YES (blocking) |
| AC-UX-003 | HIGH | Phase 2 | YES (blocking) |
| AC-UX-004 | CRITICAL | Phase 1 | YES (blocking) |
| AC-UX-005 | HIGH | Phase 2 | YES (blocking) |
| AC-UX-006 | MEDIUM | Phase 3 | NO (nice-to-have) |
| AC-UX-007 | CRITICAL | Phase 1 | YES (blocking) |
| AC-UX-008 | MEDIUM | Phase 3 | NO (nice-to-have) |
| AC-UX-009 | CRITICAL | Phase 1 | YES (blocking) |
| AC-UX-010 | MEDIUM | Phase 3 | NO (nice-to-have) |
| AC-UX-011 | CRITICAL | Phase 1 | YES (blocking) |
| AC-UX-012 | HIGH | Phase 2 | YES (blocking) |
| AC-UX-013 | MEDIUM | Phase 3 | NO (nice-to-have) |
| AC-UX-014 | HIGH | Phase 2 | YES (blocking) |
| AC-UX-015 | MEDIUM | Phase 3 | NO (nice-to-have) |

**M1 Gate:** 10 blocking criteria must pass (5 CRITICAL + 5 HIGH)

---

## Review Checklist

**For UX Implementer:**
- [ ] Read R1_UX_CONSTRAINTS_FOR_DETERMINISM.md (source document)
- [ ] Implement UX (design + code)
- [ ] Self-test against 15 acceptance criteria
- [ ] Fix failures, re-test
- [ ] Submit for review when all CRITICAL criteria pass

**For Reviewer:**
- [ ] Run Phase 1 smoke test (5 CRITICAL criteria)
- [ ] If Phase 1 fails → REJECT, return to implementer
- [ ] If Phase 1 passes → proceed to Phase 2
- [ ] Run Phase 2 functional test (5 HIGH criteria)
- [ ] If Phase 2 fails → REJECT, return to implementer
- [ ] If Phase 2 passes → proceed to Phase 3
- [ ] Run Phase 3 polish test (5 MEDIUM criteria)
- [ ] Document Phase 3 failures as known issues (if time-constrained)
- [ ] If all blocking criteria pass → ACCEPT for M1

---

## Failure Resolution

**Minor Fail (1-2 MEDIUM criteria):**
- Document as known issue
- Plan fix for M2
- Accept M1 if all CRITICAL and HIGH criteria pass

**Major Fail (1+ HIGH criteria OR 3+ MEDIUM criteria):**
- Return to implementer
- Require fix before M1 acceptance
- Re-test after fix

**Blocker Fail (1+ CRITICAL criteria):**
- STOP M1 review immediately
- Escalate to PM (acceptance criteria may be wrong, or UX fundamentally flawed)
- Do NOT proceed until blocker resolved

---

## Document Governance

**Status:** M0 / PLANNING / NON-BINDING
**Purpose:** Define testable UX requirements for M1
**Approval Required From:** PM (human project owner)
**Depends On:** R1_UX_CONSTRAINTS_FOR_DETERMINISM.md
**Blocks:** M1 UX implementation review
**Future Work:** UX implementation (M1), UX testing (M1), UX refinement (M2+)

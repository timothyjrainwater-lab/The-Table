# Rehydration Kernel

Compact restore block for Aegis (Opus/PM) after context resets. Derived from STANDING_OPS_CONTRACT.md, PROJECT_STATE_DIGEST.md, and verify_session_start.py.

## Identity and Roles

Product Owner (PO): Thunder. Design decisions, vision, dispatch authority.
Project Manager (PM): Opus. WO creation, coding direction, agent coordination, principal engineering. Full PM authority delegated 2026-02-11.
Agents execute within WO scope only. PM confirms rehydration before any work.

## Two-Force Parallel Execution Protocol (effective 2026-02-13)

**Relay model:** Operator Intent → PM drafts Research WO → Operator executes research → PM normalizes into Brick → PM drafts Builder WO → Builders implement.

**Roles:**
- Operator = Research execution, builder dispatch. Does not draft WOs. Physically passes WOs to builder agents.
- PM = WO authorship (research + build), normalization, sequencing. Does not execute research or implementation. Does not dispatch to builders directly — outputs WO documents for Operator to dispatch.
- Builders = Implementation only. Never see upstream research artifacts. Receive only READY Brick packets via Operator.

**Brick format (READY when all 4 present):** (1) Target Lock, (2) Binary Decisions, (3) Contract Spec, (4) Implementation Plan.

**Tracking surface:** `pm_inbox/BURST_INTAKE_QUEUE.md` — single intake + staging surface for all bursts.

**WIP limit:** 1-2 READY Bricks ahead. No BURST-003+ until BURST-001/002 resolved.

## Session Start Sensor

Run `python scripts/verify_session_start.py` and paste output verbatim. No work begins until bootstrap confirmed. If RED warnings appear, resolve before proceeding. Read PROJECT_STATE_DIGEST.md for current state.

## Stoplight Policy

GREEN: Bootstrap passes, tests pass, tree clean. Normal operations.
YELLOW: Minor warnings, non-blocking issues. Proceed with caution, flag concerns.
RED: Test failures, dirty tracked files, stale processes, crash state. Full stop. Fix before any feature work.

## Escalation Ladder

Apply in order. Stop at the first layer that solves the problem.
1. Tool fix (script, CLI guard, bootstrap warning)
2. Process tweak (WO structure, execution flow)
3. Documentation (only if layers 1-2 cannot encode the rule)
4. Doctrine (only after two repeated failures that docs could not prevent)

## Classification Before Response

Before responding to any operator input, classify it:
BUG: Repro test first, then fix.
FEATURE: WO with file scope, then build.
OPS-FRICTION: Tool or process fix only (escalation ladder).
PLAYTEST: Forensics with command sequence, friction points, repro test.
DOC: Apply escalation ladder. Probably reject.
STRATEGY: Discussion only. No file changes.
BURST: Create/append entry in BURST_INTAKE_QUEUE.md. No WO, no dispatch.

## Mandatory Dual-Channel Comms

Every substantive response includes both:
SYSTEM STATUS: What is the current state (stoplight, test count, branch, last commit).
OPERATOR ACTION REQUIRED: What Thunder needs to do next, if anything. If nothing, state IDLE explicitly.

## Context Drift Tripwire

CONTEXT DRIFT WARNING. I may be missing prior agreements.
Action: paste REHYDRATION KERNEL or latest verify_session_start output.

Trigger conditions:
- Aegis asks for something already provided in-session.
- Aegis contradicts a locked protocol (WO packet format, stoplight, escalation order).
- Aegis responds in the wrong mode after a strong signal (e.g., pasted WO but conversational output).
- Aegis references repo state or files inconsistently with prior verified facts.
- Aegis produces generic advice where project-specific truth existed.

Behavior on trigger:
- Stoplight downgrades to YELLOW (or RED if tests, crash, or dirty tree involved).
- Aegis must request the sensor and halt feature planning until rehydrated.

## Current Repo Snapshot

Branch: master
Last commit: e521288 — chore: update kernel for PM handoff — all 13 fix WOs resolved
Tests passed: 5,532 (24 skipped) — **GREEN. 0 failures.**
Stoplight: **YELLOW — All fix WOs COMPLETE, 7 AMBIGUOUS Operator decisions pending, PSD update + RED block lift remain**

**Verification COMPLETE:** 338 formulas verified across 9 domains. 255 CORRECT, 30 WRONG, 28 AMBIGUOUS, 25 UNCITED. All domains marked COMPLETE in checklist. Domain A re-verified with research cross-reference — 4 verdicts reclassified WRONG→AMBIGUOUS (cover design decision in RQ-BOX-001).

**Fix WO status — ALL 13 WOs RESOLVED (11 commits covering all 13 WOs):**
- `ca76c8e` WO-FIX-13: Colossal footprint 36 (6x6)
- `acf88bb` WO-FIX-10 partial: SIZE_ORDER 9 categories
- `16f24f7` WO-FIX-10 partial: soft cover inversion + water fall damage
- `d293242` WO-FIX-07/08/09: maneuver touch attacks, overrun, sunder damage
- `23d4f4d` WO-FIX-12 partial: level 1 feat fix
- `a386b81` WO-FIX-01/02: STR grip multiplier + min-1 damage + full attack early termination
- `df3a958` WO-FIX-03/04: condition AC melee/ranged + Panicked/Fatigued/Exhausted
- `cb05060` WO-FIX-06: concentration DC includes spell level
- `1da6377` WO-FIX-14: TWF penalties respect off-hand weapon weight
- `fcf712e` WO-FIX-11: trip/disarm/grapple action type = varies (was marked RETIRED, then implemented)
- `b52d8d8` WO-FIX-12 F2/F3: hardcoded XP table levels 11-20 from DMG

**Fix WO status — RETIRED:**
- WO-FIX-05 (cover values): Retired — design decision, not a bug. Documented in RQ-BOX-001.

**Additional fix commits:**
- `f581d44` fix: test isolation — sys.modules torch mock + TTS skip guard

**Fix phase artifacts:**
- `docs/verification/WRONG_VERDICTS_MASTER.md` — 30 WRONG verdicts in 12 active fix WOs (FIX-WO-05 retired)
- `docs/verification/AMBIGUOUS_VERDICTS_DECISION_LOG.md` — 28 AMBIGUOUS verdicts, 7 need Operator decision
- `pm_inbox/FIX_WO_DISPATCH_PACKET.md` — full dispatch packet with all 13 WOs

**OPEN QUESTION (Operator decisions still pending):**
- 7 AMBIGUOUS verdicts need Operator decision (see AMBIGUOUS_VERDICTS_DECISION_LOG.md)

**Lessons learned (fix phase):**
- 3 of 7 builder agents reported completion without persisting code changes. Operator caught during commit review. **Mitigation:** `git diff <target_files>` verification step in WO completion protocol.
- Schema WOs must trace the full path: definition → aggregation → serialization → consumer. WO-FIX-03 missed `aidm/core/conditions.py` and serialization methods.
- WO-FIX-11 was initially RETIRED (action cost table doesn't exist as described), but then successfully implemented by changing action type classification in `play.py`. Lesson: "no code target" may mean the WO spec was wrong, not that no fix is possible.

**Schema note:** `ActiveSpellEffect` gained `spell_level: int = 0` field (cb05060). Callers creating concentration effects should pass spell_level for correct DC calculation.

**Context window discipline:** PM context is reserved for coordination only. All fix implementation dispatched to builder agents via WOs. **Hard boundary — see PM Execution Boundary section below.**

**Process gap identified:** `pm_inbox/` has no triage protocol, lifecycle management, or cleanup enforcement. See `pm_inbox/HANDOFF_PM_INBOX_HYGIENE.md`. Related to WO-GOV-03 and WO-GOV-04.

**Untracked files (not committed):**
- 4 voice research docs in `docs/research/VOICE_*.md`
- `pm_inbox/research/` directory

## PM Execution Boundary (HARD CONSTRAINT)

The PM agent MUST NOT perform any of the following actions. These are builder-only activities. Violations waste irreplaceable PM context window and risk coordination failures.

**NEVER do (draft a WO for the Operator to dispatch to a builder instead):**
- Run pytest, test suites, or any test commands
- Read source code files (`.py` in `aidm/` or `tests/`)
- Debug test failures (binary search, isolation runs, traceback analysis)
- Write or edit source code or test files
- Run git diff on source files
- Regenerate gold masters or fixtures
- Execute any `python` command against the codebase

**PM MAY do:**
- Read/write tracking surfaces (PSD, kernel, checklist, WO docs, verification docs)
- Run `git status`, `git log`, `git show --stat` (metadata only)
- Run `python scripts/verify_session_start.py` (bootstrap sensor)
- Draft WOs, Bricks, and dispatch packets
- Review builder completion reports (when Operator pastes them)
- Coordinate and sequence work

**When tempted to "just quickly check":** Draft a WO instead. The PM's value is coordination, not execution. Every line of source code read in PM context is a line of coordination capacity lost.

**Dispatch chain:** PM drafts WO → PM presents WO to Operator → **Operator dispatches WO to builder agent.** The PM never directly spawns, manages, or communicates with builder agents. The Operator is the physical dispatch layer — the PM's output is always a document (WO, Brick, memo), never an agent invocation.

**Incident trigger:** If the PM executes a builder action, Operator should invoke CONTEXT DRIFT WARNING and downgrade stoplight to YELLOW. PM must acknowledge the boundary violation and return to coordination posture.

---

## Active Work Surfaces

**BONE-LAYER VERIFICATION — FIX PHASE (YELLOW — all WOs resolved, gate items remain):**
Verification complete. 13 fix WOs drafted. **All 13 resolved** — 12 implemented and committed (11 original commits + 2 new), 1 retired (WO-FIX-05 cover values). Test suite GREEN (5,532 passed, 0 failures). Test isolation fixed (f581d44).

**Fix WO progress — ALL COMPLETE:**
- [x] WO-FIX-01 (BUG-1/8/9) — COMMITTED (a386b81)
- [x] WO-FIX-02 (BUG-2) — COMMITTED (a386b81)
- [x] WO-FIX-03 (BUG-3/4) — COMMITTED (df3a958)
- [x] WO-FIX-04 (BUG-5/6/7) — COMMITTED (df3a958)
- [x] WO-FIX-06 (BUG-C-002) — COMMITTED (cb05060)
- [x] WO-FIX-07 (B-BUG-1/3/5) — COMMITTED (d293242)
- [x] WO-FIX-08 (B-BUG-2) — COMMITTED (d293242)
- [x] WO-FIX-09 (B-BUG-4) — COMMITTED (d293242)
- [x] WO-FIX-10 (E-BUG-01/02/03) — COMMITTED (16f24f7 + acf88bb)
- [x] WO-FIX-11 (G-PLAY-71-86) — COMMITTED (fcf712e). Initially marked RETIRED, then implemented: action type = varies for trip/disarm/grapple.
- [x] WO-FIX-12 (BUG-F1/F2/F3) — F1 COMMITTED (23d4f4d). F2/F3 COMMITTED (b52d8d8): hardcoded XP table levels 11-20 from DMG.
- [x] WO-FIX-13 (I-GEOM-291) — COMMITTED (ca76c8e)
- [x] WO-FIX-14 (I-AMB-02) — COMMITTED (1da6377)

**Remaining completion gate items:**
- [x] All fix WO code changes committed and tested
- [x] Test suite confirmed GREEN (5,532 passed, 24 skipped, 0 failures)
- [x] WO-FIX-11 — COMMITTED (fcf712e)
- [x] WO-FIX-12 F2/F3 — COMMITTED (b52d8d8)
- [x] Test isolation fixed (f581d44)
- [ ] Operator reviews and approves 7 AMBIGUOUS decisions
- [ ] PSD updated to reflect fix phase completion
- [ ] RED block lifted by Operator

**ALL OF THE FOLLOWING ARE BLOCKED behind completion gate (3 items remain):**

- Phase 4C Wave C (3 WOs) — BLOCKED
- BURST-001/002/003 — BLOCKED
- All feature work — BLOCKED
- All playtesting — BLOCKED
- WO_SET_METHODOLOGY_REFINEMENT (6 governance WOs, commit f1013ba) — BLOCKED

**PM posture:** ACTIVE. Fix phase code COMPLETE. Tests GREEN. **Remaining gate items:** (1) 7 AMBIGUOUS Operator decisions, (2) PSD update, (3) RED block lift by Operator.

**Post-fix forward path (PM-assessed, see `pm_inbox/MEMO_POST_FIX_PHASE_ACTION_PLAN.md`):**
- Wave 1 (immediate, parallel-safe): P1-A sunder grip multiplier, P1-C register narration marker, P1-D fix TestPerformance tests. All micro-WOs.
- Wave 2 (operator-gated): P1-B XP table spot-check (Operator action), P2-A AMBIGUOUS decisions (completion gate).
- Wave 3 (after RED block lift): P2-C UNCITED triage, P3-A conftest hooks, P3-C .gitignore.
- Backlog (milestone-level): P4-A circular imports, P4-B god modules, P4-C attack dedup, P4-D weapon stubs (highest impact).
- **Key risk flagged:** P4-D `is_ranged` hardcoded `False` means WO-FIX-03 Prone/Helpless AC differentiation is correct but dormant for ranged attacks. Known limitation, not a blocker.

**pm_inbox hygiene:** Triage complete. 20 files archived to `pm_inbox/reviewed/`. Inbox at 4 active files (cap 15). See `pm_inbox/PM_BRIEFING_CURRENT.md`.

---

## PM Context Window Handover Protocol

When a PM context window expires and a new PM agent is initialized, the Operator follows this exact sequence. The goal is **minimal context consumption** — the new PM reads only what it needs to resume, in the right order, and nothing else.

### Step 1: Identity Paste (Operator action)
Paste this exact block into the new session as the first message:

```
You are the PM agent (Aegis/Opus) for a D&D 3.5e combat engine project. Product Owner is Thunder. Your context window is a critical finite resource — do NOT use it for implementation work. You coordinate only.

Read these files in this exact order, then report SYSTEM STATUS:
1. pm_inbox/REHYDRATION_KERNEL_LATEST.md (this file — your operating rules)
2. docs/verification/BONE_LAYER_CHECKLIST.md (progress tracker — tells you where work stands)
3. docs/verification/BONE_LAYER_VERIFICATION_PLAN.md (execution plan — Sections 1-2 and 7-9 only, skip the rest unless needed)

Do NOT read: PROJECT_STATE_DIGEST.md (too long for rehydration), FORMULA_INVENTORY.md (builder reference only), any source code files, any completion reports you haven't been asked to review.

After reading, report: stoplight, last commit, verification progress, and next PM action.
```

### Step 2: New PM Self-Orients (Agent action)
The new PM reads the 3 files in order (kernel = ~200 lines, checklist = ~50 lines, plan Sections 1-2 + 7-9 = ~80 lines). Total context consumed: ~330 lines. This gives the PM:
- Operating rules + PM boundary + dispatch chain (kernel)
- What's done and what's not (checklist)
- How to execute the next iteration (plan)

### Step 3: PM Reports Status (Agent action)
The new PM must report:
```
SYSTEM STATUS: [stoplight], [last commit], [test count], [verification X/9 domains complete]
NEXT PM ACTION: [what to do next based on checklist state]
OPERATOR ACTION REQUIRED: [what Thunder needs to do, or IDLE]
```

### Step 4: Resume Work (Agent action)
Based on current state (fix phase code COMPLETE, gate items remain):
- All 13 fix WOs are resolved (12 committed, 1 retired). Tests GREEN. No code work remains.
- If 7 AMBIGUOUS decisions still pending: ask Operator to review them (see `docs/verification/AMBIGUOUS_VERDICTS_DECISION_LOG.md`)
- If AMBIGUOUS decisions resolved: update PSD, request RED block lift from Operator
- If RED block lifted: unblock Phase 4C Wave C, BURST-001/002/003, governance WOs, feature work, playtesting
- If pm_inbox hygiene WO needed: scope `pm_inbox/HANDOFF_PM_INBOX_HYGIENE.md` into a governance WO

### What NOT To Do During Handover
- Do NOT re-read the formula inventory (builder reference, not PM reference)
- Do NOT explore the codebase
- Do NOT read source files
- Do NOT re-derive anything that's already in the checklist or plan
- Do NOT update the kernel until you have new information to add
- Do NOT read completion reports proactively — wait for Operator to paste them

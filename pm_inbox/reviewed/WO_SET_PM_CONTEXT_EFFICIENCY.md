# WO Set: PM Context Efficiency Overhaul

**Authority:** Builder (Opus 4.6), advisory session
**Date:** 2026-02-14
**Lifecycle:** NEW
**For:** PM verdict and dispatch sequencing
**Supersedes:** None
**Resolves:** PM self-diagnosed context waste (tracking surface redundancy, memo sprawl, commit ceremony overhead)

---

## Problem Statement

The PM's context window is the most expensive resource in the system. Current tracking surface architecture burns PM context on mechanical operations (reading overlapping state across 4 files, updating 4 files per event, reading 3 memos that cover the same findings). The PM identified 6 categories of waste. This WO set addresses all 6 with concrete, dispatchable work orders.

**Measured waste:**
- Kernel: 260 lines, ~120 of which are resolved fix-phase state that will never change
- Briefing: 52 lines, 19 of which are archived items already checked off
- Per-event update cost: 4 file reads + 4 edits + staging + commit = ~800 tokens per state change
- Builder memo intake: 698 lines across 3 memos for one session's findings

---

## WO-GOV-CE-01: Kernel Rotation

**Scope:** Archive current kernel, write phase-appropriate replacement
**Files:** `pm_inbox/REHYDRATION_KERNEL_LATEST.md`, new `pm_inbox/aegis_rehydration/REHYDRATION_KERNEL_FIX_PHASE_ARCHIVE.md`
**Effort:** Medium (rewrite, not just trim)

**Steps:**

1. Copy current `REHYDRATION_KERNEL_LATEST.md` verbatim to `pm_inbox/aegis_rehydration/REHYDRATION_KERNEL_FIX_PHASE_ARCHIVE.md`

2. Rewrite `REHYDRATION_KERNEL_LATEST.md` with this structure (~100 lines target):

   **Keep as-is (no changes):**
   - Identity and Roles (8 lines)
   - Two-Force Parallel Execution Protocol (12 lines)
   - Session Start Sensor (3 lines)
   - Stoplight Policy (4 lines)
   - Escalation Ladder (6 lines)
   - Classification Before Response (8 lines)
   - Mandatory Dual-Channel Comms (4 lines)
   - Context Drift Tripwire (12 lines)
   - PM Execution Boundary (25 lines)
   - PM Context Window Handover Protocol (20 lines)

   **Replace "Current Repo Snapshot" + "Active Work Surfaces" (~130 lines) with compressed version (~15 lines):**
   ```
   ## Current Repo Snapshot

   Branch: master
   Last commit: [hash] — [msg]
   Tests: 5,532 passed, 24 skipped — GREEN
   Stoplight: [state]

   Fix phase: COMPLETE. 13 WOs resolved (12 committed, 1 retired). 28 AMBIGUOUS all resolved.
   Full fix-phase details: pm_inbox/aegis_rehydration/REHYDRATION_KERNEL_FIX_PHASE_ARCHIVE.md

   Lessons (carry forward):
   - Silent agent completion: 43% failure rate. Gate: git diff before accepting.
   - Schema cascade: trace definition → serialization → aggregation → consumer → tests.
   - is_ranged hardcoded False: 3 rules dormant until weapon plumbing (P4-D).

   Remaining gate: RED block lift by Operator.
   Blocked behind gate: Phase 4C Wave C, BURST-001/002/003, governance WOs, feature work, playtesting.
   Forward path: see PM_BRIEFING_CURRENT.md action queue.
   ```

   **Cut entirely:**
   - Per-WO commit hash list (13 lines)
   - AMBIGUOUS verdict details (3 lines)
   - Fix phase artifacts list (3 lines)
   - Additional fix commits list (2 lines)
   - Per-WO progress checkboxes (14 lines)
   - Remaining completion gate checkboxes (9 lines → 1 line)
   - Active Work Surfaces narrative block (46 lines → 3 lines)
   - Post-fix forward path details (5 lines → reference briefing)
   - Process gap / untracked files notes (4 lines → resolved or archived)

3. Update Handover Protocol Step 2 line count estimate: "kernel = ~100 lines" (was ~200)

**Acceptance:** New kernel < 110 lines. All protocol sections preserved. Phase-specific state archived, not deleted. Handover protocol updated.

**PM Decision Required:** Does the PM want any additional state carried forward beyond the 3 compressed lessons?

---

## WO-GOV-CE-02: Briefing Archive Split

**Scope:** Separate action queue from audit trail
**Files:** `pm_inbox/PM_BRIEFING_CURRENT.md`, new `pm_inbox/PM_BRIEFING_ARCHIVE.md`
**Effort:** Low (file split + convention change)

**Steps:**

1. Create `pm_inbox/PM_BRIEFING_ARCHIVE.md` with header:
   ```
   # PM Briefing — Archive
   Historical record of completed/archived items. Builder-maintained.
   PM does not read this file during normal operations.
   ```

2. Move all `[x]` items from "PM Review Completed / Archived This Session" into the archive file. Organize by date.

3. Briefing shrinks to action-only format (~15 lines):
   ```
   # PM Briefing — Current
   **Last updated:** [date]

   ## Requires PM Action
   - [ ] [items needing PM verdict]

   ## Requires Operator Action
   - [ ] [items needing operator action]

   ## Awaiting Dispatch (BLOCKED behind [gate])
   - [ ] [queued WOs]

   ## Active Operational Files
   - [list]

   ## Persistent Files
   - README.md, PM_BRIEFING_CURRENT.md, REHYDRATION_KERNEL_LATEST.md
   ```

4. Add to pm_inbox README under Builder Intake Protocol: "When PM sets lifecycle to ARCHIVE, builder moves the one-line entry from briefing action queue to `PM_BRIEFING_ARCHIVE.md`."

5. Add `PM_BRIEFING_ARCHIVE.md` to the persistent files list in both the README and the briefing itself.

**Acceptance:** Briefing < 20 lines. Archive file contains all historical items. README updated with archive flow.

---

## WO-GOV-CE-03: Builder Memo Consolidation Protocol

**Scope:** Enforce one-memo-per-session rule and Supersedes/Resolves fields
**Files:** `pm_inbox/README.md`, `templates/SESSION_MEMO_TEMPLATE.md` (framework repo, optional)
**Effort:** Low (text edits)

**Steps:**

1. Add to pm_inbox README under "Builder Intake Protocol" (after item 5):
   ```
   6. **One memo per session.** If a session produces findings spanning multiple
      concerns (debrief, action items, recommendations), merge them into one memo
      with sections. Do NOT create separate memos for related findings.
   7. **Pass 1 goes straight to archive.** The full context dump (DEBRIEF_ prefix)
      goes directly to `pm_inbox/reviewed/` on creation. PM reads Pass 2 only.
      The DEBRIEF is the artifact of record if a future agent needs session details.
   8. **Supersedes/Resolves fields are mandatory.** Every memo header includes:
      - **Supersedes:** [list of prior documents this replaces, or "None"]
      - **Resolves:** [list of WOs/issues this completes, or "None"]
      PM uses these fields to archive without reading superseded documents.
   ```

2. Update the lifecycle header example block to include:
   ```
   **Supersedes:** None
   **Resolves:** None
   ```

3. (Optional, framework repo) Update `templates/SESSION_MEMO_TEMPLATE.md` to include Supersedes/Resolves fields.

**Acceptance:** README contains consolidation rules. Next builder session produces one memo, not multiple.

**PM Decision Required:** Should the DEBRIEF (Pass 1) still route through pm_inbox briefly for the PM to see the filename, or go directly to `reviewed/` without ever appearing in the briefing?

---

## WO-GOV-CE-04: Checklist Phase Transition

**Scope:** Transition bone-layer checklist from active tracking surface to completed-phase artifact
**Files:** `docs/verification/BONE_LAYER_CHECKLIST.md`
**Effort:** Trivial (text edit)

**Steps:**

1. Once RED block is lifted, mark the final gate item `[x]`.

2. Add status line at top of file:
   ```
   **Phase Status:** COMPLETE (all gate items resolved). This file is now a
   historical record. Active tracking has moved to PM_BRIEFING_CURRENT.md.
   ```

3. Remove checklist from PM rehydration reading list. The kernel's compressed "Fix phase: COMPLETE" line replaces it. If a future agent needs verification details, the checklist is still here — it just isn't part of the standard rehydration path.

4. Update kernel Handover Protocol Step 1 to remove checklist from required reading:
   ```
   Read these files in this exact order:
   1. pm_inbox/REHYDRATION_KERNEL_LATEST.md (operating rules + state)
   2. pm_inbox/PM_BRIEFING_CURRENT.md (action queue — what needs doing)
   ```
   Checklist becomes optional reference, not mandatory onboarding.

**Acceptance:** Checklist has COMPLETE header. Handover protocol references 2 files instead of 3. PM rehydration cost drops from ~330 lines to ~115 lines.

**PM Decision Required:** Should the verification plan (third rehydration file) also drop from mandatory to optional? It served the verification phase, which is over.

---

## WO-GOV-CE-05: Batch Commit Convention

**Scope:** Process convention change, no file modifications required
**Files:** None (convention only; optionally document in pm_inbox README)
**Effort:** None (behavioral change)

**Convention:**

1. **One "PM action cycle" = one commit.** PM reads inbox, writes verdicts. Builder executes all resulting actions (file moves, briefing updates, kernel edits). All actions from one cycle go into one commit.

2. **Commit message format:** `chore: PM cycle — [summary]`
   Example: `chore: PM cycle — archive 3 memos, update briefing, rotate kernel`

3. **Safety valve:** If VPN drop risk is high, commit at natural checkpoints (after each verdict batch). Never defer everything to end-of-session.

4. **Maximum 2 commits per cycle:** One for PM verdict edits (if PM is writing to files), one for builder execution of those verdicts. Combine if possible.

**Acceptance:** Next PM cycle produces 1-2 commits instead of 6-8.

---

## WO-GOV-CE-06: Aggressive Archive via Supersedes Protocol

**Scope:** Convention change + README update
**Files:** `pm_inbox/README.md`
**Effort:** Trivial (text addition)

**Steps:**

1. Add to pm_inbox README under "PM Verdict Protocol — What the PM does":
   ```
   4. When triaging a memo with a Supersedes field, archive all listed
      documents without reading them. The superseding memo contains
      everything the PM needs.
   ```

2. Add to "Builder Intake Protocol":
   ```
   9. **Builder completion reports include:** If your deliverable resolves
      prior WOs or supersedes prior memos, list them in the header fields.
      This saves PM context on triage — the PM archives superseded docs
      on sight without reading them.
   ```

**Acceptance:** README contains archive-on-supersede protocol. PM skips reading obsolete documents.

---

## Dispatch Sequence

```
Wave 1 (parallel-safe, builder can execute immediately):
  WO-GOV-CE-01  Kernel rotation           — highest impact, ~100 line savings
  WO-GOV-CE-02  Briefing archive split    — ~35 line savings per PM read

Wave 2 (after Wave 1 committed):
  WO-GOV-CE-03  Memo consolidation rules  — README update
  WO-GOV-CE-06  Supersedes protocol       — README update
  (These two touch the same file — combine into one edit/commit)

Wave 3 (after RED block lift):
  WO-GOV-CE-04  Checklist phase transition — depends on RED block

Wave 0 (immediate, no files):
  WO-GOV-CE-05  Batch commit convention   — takes effect now
```

---

## PM Decisions Required (3)

1. **WO-GOV-CE-01:** Any additional fix-phase state to carry forward in the new kernel beyond the 3 compressed lessons?
2. **WO-GOV-CE-03:** Should DEBRIEF (Pass 1) briefly appear in the briefing before archival, or go directly to `reviewed/`?
3. **WO-GOV-CE-04:** Should the verification plan also drop from mandatory rehydration reading to optional reference?

---

## Expected Impact

| Metric | Before | After |
|--------|--------|-------|
| Kernel size | ~260 lines | ~100 lines |
| Briefing size | ~52 lines | ~15 lines |
| PM rehydration read | ~330 lines (3 files) | ~115 lines (2 files) |
| Files updated per event | 4 (kernel + briefing + checklist + PSD) | 1-2 (briefing + kernel on rotation) |
| Builder memos per session | 1-3 | 1 (enforced) |
| PM reads per memo intake | 600+ lines | 100-150 lines |
| Commits per PM cycle | 6-8 | 1-2 |

---

*End of WO set.*

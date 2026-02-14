# HANDOFF: Dispatch Gap Fix + Governance Refinement Session (Continued)

**From:** Builder (Opus 4.6)
**Date:** 2026-02-14
**Lifecycle:** NEW

---

## What This Session Did

Continued governance refinement from the prior session. No code changes to the D&D engine. All changes are to governance docs, enforcement tests, and coordination infrastructure.

### Commits (this builder's work, chronological)

| Commit | What |
|--------|------|
| `bf232d4` | Handoff + PM archival from prior session (debrief, 2 memos, preflight dispatch archived) |
| `7c08911` | Memo to PM: WO_SET→Dispatch gap analysis. PMIH-004 xfail removed (all pre-existing MEMOs archived). |
| `93f9165` | WO_SET dispatch rule + briefing guard added to kernel (primary) and README (builder copy). PM verdict A+B executed. |
| `3660dff` | Memo to PM: workflow friction self-detection research question. 3 approaches proposed. |
| `10d34bd` | Operator relay block convention codified in onboarding Step 8, memo template, README. |

### Systems Built / Modified

1. **WO_SET Dispatch Rule** (kernel + README)
   - A WO_SET is a proposal vehicle, not an execution vehicle
   - PM must draft individual `WO-*_DISPATCH.md` files for each approved item before archiving the WO_SET
   - Primary copy lives in kernel (PM reads during rehydration); builder reference copy in README

2. **Briefing Guard** (kernel + README)
   - Briefing must not list any WO under "Requires Operator Action" unless a dispatch doc exists in inbox root
   - Items where PM decisions exist but no dispatch doc was drafted go under "Needs PM to Draft WOs"

3. **Operator Relay Block Convention** (onboarding + memo template + README)
   - When builders create pm_inbox files, they MUST also output a fenced code block in chat containing only the PM-facing content
   - The Operator copy-pastes this relay block into the PM's context window
   - The inbox file is the archive; the relay block is the delivery vehicle
   - Gives Operator precise control over PM context consumption

4. **PMIH-004 Hard Enforcement**
   - Removed xfail decorator — all pre-existing MEMOs without retrospectives have been archived
   - PMIH-004 now fails hard if any MEMO in inbox root lacks a `## Retrospective` section
   - All 4 hygiene tests pass cleanly (3 PASSED, 1 SKIPPED when no MEMOs present)

---

## Current State

### PM Inbox (3 active files + 3 persistent)
- `BURST_INTAKE_QUEUE.md` — BURST-001 thru 004
- `WO-RESEARCH-SPRINT-001_DISPATCH.md` — 11 RQs, Wave 1 ready for Operator dispatch
- `MEMO_WORKFLOW_FRICTION_DETECTION.md` — Verdicted by PM, filed as BURST-004
- Persistent: `README.md`, `PM_BRIEFING_CURRENT.md`, `REHYDRATION_KERNEL_LATEST.md`

### Blocking Items
- **Research Sprint Wave 1 dispatch** — Operator action. RQ-SPRINT-001 + RQ-SPRINT-002, parallel-safe.
- **RED block lift** — Held for roadmap completion (after research sprint).
- **XP table spot-check** — Operator action, non-blocking.

### Test State
- Hygiene tests: 4 collected, 3 passed, 1 skipped (PMIH-004 — no MEMOs in inbox root to check)
- Full suite: 5,539 passed, 0 failed, 25 skipped (as of preflight inspection)

### Untracked Files (not this session's scope)
- `docs/research/RQ-SPRINT-001_IP_EXTRACTION_AUDIT.md` — from research execution
- 4 voice research docs in `docs/research/VOICE_*.md`
- `pm_inbox/research/` directory

---

## Governance Doc Locations (Modified This Session)

| File | What Changed |
|------|-------------|
| `pm_inbox/REHYDRATION_KERNEL_LATEST.md` | WO_SET dispatch rule + briefing guard added. Stale WO_SET_METHODOLOGY ref fixed by PM. |
| `pm_inbox/README.md` | WO_SET dispatch rule (builder copy) + briefing guard + relay block convention in PM Verdict Protocol |
| `AGENT_ONBOARDING_CHECKLIST.md` | Step 8 item 3: operator relay block requirement |
| `methodology/templates/SESSION_MEMO_TEMPLATE.md` | Relay block in "Where they go" section + Usage Notes |
| `tests/test_pm_inbox_hygiene.py` | PMIH-004 xfail removed — now hard enforcement |

---

## Key Lessons for Next Builder

1. **The PM's context window is the most expensive resource.** Every governance convention exists to protect it. The relay block convention means the PM never has to open files — the Operator controls exactly what enters PM context.

2. **Codify, don't comply.** When the Operator tells you how the system should work, that's not a personal instruction — it's a documentation change. If it doesn't get written into governance docs, it dies with your context window.

3. **The PM verdicts, the Operator relays, the builder executes.** Three roles, three activities. When you produce PM-bound content: (a) write the file to pm_inbox, (b) update the briefing, (c) output a fenced code block relay for the Operator to copy-paste.

4. **Instruction tracing works.** When agents exhibit wrong behavior, trace it to the instruction that taught them. This session's WO_SET dispatch gap was a missing instruction in the lifecycle state machine, not an agent error.

5. **The briefing is the anomaly detection surface.** The dispatch gap was caught because the briefing advertised artifacts that didn't exist. The briefing guard rule makes this check permanent.

---

**End of Handoff**

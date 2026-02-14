# DEBRIEF: PM Inbox Hygiene System & Three-Pass Debrief Protocol

**From:** Builder (Opus 4.6)
**Date:** 2026-02-14
**Session scope:** Design and implement Tier 1 enforcement for pm_inbox lifecycle management; upgrade debrief protocol from two-pass to three-pass with mandatory retrospective.
**Lifecycle:** NEW

---

## Pass 1 — Full Context Dump

### Phase 1: PM Inbox Hygiene System

**Problem identified:** The pm_inbox had a 10-item cap in README (Tier 3 prose, never enforced) that was violated 2.3x over — 23 files in the inbox root with no lifecycle tracking, no naming convention enforcement, and no centralized triage entry point. The PM had to open every file to determine its status.

**Root cause:** The cap was aspirational prose with zero enforcement. There was no structural mechanism (test, hook, or gate) that prevented file accumulation. There was also no "drain" — no centralized file that told the PM which items needed action vs. which were informational.

**Solution designed (3-tier model):**
- Tier 1 (test-enforced, ~100% stickiness): `tests/test_pm_inbox_hygiene.py` with 4 test classes
- Tier 2 (process-enforced, ~70-80%): Templates, onboarding checklist, Section 15.5 updates
- Tier 3 (prose-enforced, ~40-60%): README conventions (still useful as documentation)

**Files created:**
- `tests/test_pm_inbox_hygiene.py` — 4 test classes:
  - PMIH-001: Active file count <= 15 (was xfail, now hard pass after PM triage)
  - PMIH-002: All non-persistent files use valid prefix
  - PMIH-003: All non-persistent files have `**Lifecycle:**` header in first 15 lines
  - PMIH-004: All MEMO_ files contain `## Retrospective` section (currently xfail)
- `pm_inbox/PM_BRIEFING_CURRENT.md` — Rolling PM entry point. Every agent adding a file must add a one-line entry here.
- `pm_inbox/MEMO_PM_INBOX_TRIAGE_TABLE.md` — PM guidance for initial triage (now archived by PM)

**Files modified:**
- `pm_inbox/README.md` — Rewritten from 34 to 92 lines with:
  - File type prefix table (WO-, MEMO_, DEBRIEF_, HANDOFF_, PO_REVIEW, BURST_, FIX_WO, WO_SET, WO_INSTITUTIONALIZE — both underscore and hyphen variants)
  - Lifecycle state machine (NEW -> TRIAGED -> ACTIONED -> ARCHIVE)
  - Builder intake protocol (4 steps)
  - PM triage protocol (5 steps)
  - Persistent files list
  - Subdirectory documentation
- `AGENT_ONBOARDING_CHECKLIST.md` — Steps 4, 6, 8 updated with hygiene rules
- 22 existing pm_inbox files received `**Lifecycle:** NEW` headers (bulk operation via subagent)

### Phase 2: Three-Pass Debrief Protocol

**Problem identified:** PO (Thunder) observed that operational judgment was being lost at context window boundaries. Agents completed work orders and closed sessions without reflecting on the process. The two-pass protocol (dump + summary) captured facts but not meta-observations about what went well, what broke, what should change.

**User quote:** "I want this to happen every single time. Any work order is completed automatically."

**Solution designed:**
- Pass 1 = Full Dump (raw knowledge capture) → `DEBRIEF_*.md`
- Pass 2 = PM Summary (compressed for PM context budget) → `MEMO_*.md`
- Pass 3 = Operational Retrospective (judgment about the process) → `## Retrospective` section in MEMO file

**Files modified:**
- `AGENT_DEVELOPMENT_GUIDELINES.md` — Section 15.5 upgraded from "two-pass" to "three-pass"
  - Added Pass 3 description with 4 required categories: Fragility, Process feedback, Methodology, Concerns
  - Added lifecycle header template
  - Added briefing update instruction
  - LAST UPDATED header updated
- `pm_inbox/aegis_rehydration/AGENT_DEVELOPMENT_GUIDELINES.md` — Synced with root copy
- `methodology/templates/SESSION_MEMO_TEMPLATE.md` — Template updated:
  - Added `## Retrospective (Pass 3 — Operational judgment)` section
  - Changed process description from "Two-Pass" to "Three-Pass Writing Process: Dump, Distill, Reflect"
  - References PMIH-004 enforcement
- `AGENT_ONBOARDING_CHECKLIST.md` — Step 6 updated with three-pass references
- `tests/test_pm_inbox_hygiene.py` — Added PMIH-004 test class

### Phase 3: Cross-File Consistency Audit

**Triggered by:** PO asked "Just take a second and double check and see what you think."

**Findings (9 inconsistencies, 3 critical):**

1. **CRITICAL — CF-001 Partial Update:** `pm_inbox/aegis_rehydration/AGENT_DEVELOPMENT_GUIDELINES.md` still said "two-pass" after root copy was updated to "three-pass". This is exactly the failure mode the project's own coordination failure taxonomy (CF-001) describes. Fixed by syncing Section 15.5 and LAST UPDATED header.

2. **CRITICAL — PMIH-002 violation:** `ACTION_PLAN_POST_FIX_PHASE.md` appeared in pm_inbox without a valid prefix (created by another session that didn't follow the new rules). Renamed to `MEMO_POST_FIX_PHASE_ACTION_PLAN.md`. Added lifecycle header.

3. **CRITICAL — WO_INSTITUTIONALIZE stale references:** 4 occurrences of "two-pass" in `WO_INSTITUTIONALIZE_DEBRIEF_PROTOCOL.md`. Updated all to "three-pass". Lifecycle set to ARCHIVE. Status set to COMPLETED.

4. **MODERATE — README prefix table incomplete:** Only documented hyphen variants while tests accepted underscore variants. Expanded table to document both forms.

5. **MODERATE — Triage table test count wrong:** Referenced "3 tests" after PMIH-004 was added. Fixed to "4 tests".

6-9. **MINOR — Various documentation references** updated for consistency.

### Phase 4: PM Triage (Performed by PM During Session)

While I was preparing the handover, the PM performed triage:
- Active file count dropped from 22 to 4 (well under 15-file cap)
- ~18 files moved to `pm_inbox/reviewed/`
- PMIH-001 test changed from XFAIL to XPASS (test passes but xfail decorator still present)
- PM updated `PM_BRIEFING_CURRENT.md` to reflect post-triage state

**Action taken this session:** Removed the `@pytest.mark.xfail` decorator from PMIH-001, making it a hard enforcement test.

### Errors and Recovery

1. **Edit tool requires prior file read:** Attempted batch-edit of 22 files without reading them first. Tool blocked. Recovered by dispatching a subagent to read-then-edit each file individually.

2. **PowerShell command syntax:** Initial `dir /B` command failed in shell environment. Switched to Glob tool.

3. **CF-001 rehydration copy desync:** Root file's own comment says "REHYDRATION COPY: After editing this file, also update pm_inbox/aegis_rehydration/AGENT_DEVELOPMENT_GUIDELINES.md" — I didn't follow this instruction during initial edits. Caught by consistency audit, fixed.

4. **Prefix violation from external session:** Another builder session created `ACTION_PLAN_POST_FIX_PHASE.md` while the hygiene system was being built. PMIH-002 test caught it. Renamed and added lifecycle header.

---

**End of Pass 1 Dump**

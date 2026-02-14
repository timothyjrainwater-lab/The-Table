# Handoff: PM Inbox Hygiene — Process Gap Identified

**From:** Builder (Opus 4.6)
**To:** Next agent
**Date:** 2026-02-14
**Status:** NOT STARTED — needs scoping and WO

---

## Problem

`pm_inbox/` has no triage protocol, no lifecycle management, and no hygiene enforcement. Files accumulate indefinitely. The folder currently contains:

- Session memos (MEMO_*)
- Work order sets (WO_SET_*, WO_INSTITUTIONALIZE_*)
- Handoff documents (HANDOFF_*)
- Verification dispatches (WO-VERIFY-*)
- Research subfolder (research/)
- Agent notes (SONNET_AGENT_NOTES.md)
- Reviewed subfolder (reviewed/) — PM-only
- Rehydration subfolder (aegis_rehydration/) — PM-only

There is no defined lifecycle for these files: when do they get triaged? When do they move to reviewed/? When do they get deleted? What's actionable vs archived vs stale?

The PM (Aegis) has a limited context window. Opening pm_inbox/ and seeing 20+ files with no priority ordering is the PM equivalent of context starvation.

## What Needs to Happen

1. **Define file lifecycle states** — new → triaged → actioned → archived
2. **Define triage protocol** — who triages, when, what the output is
3. **Consider a rolling briefing file** (PM_BRIEFING_CURRENT.md) as proposed in WO-GOV-03
4. **Consider naming conventions** that encode priority or type
5. **Consider a test** (Tier 1 enforcement) that warns when pm_inbox/ exceeds a threshold — already proposed in WO-GOV-04 (`test_document_budget.py`)

## Files to Read

- `pm_inbox/WO_SET_METHODOLOGY_REFINEMENT.md` — WO-GOV-03 (PM Context Compression) and WO-GOV-04 (Document Budget Test) both address parts of this
- `AGENT_ONBOARDING_CHECKLIST.md` Step 8 — current PM inbox routing rules
- `AGENT_DEVELOPMENT_GUIDELINES.md` Section 15.5 — debrief protocol adds more files to pm_inbox/

## What NOT to Do

- Do NOT delete or move files in pm_inbox/ without PM approval
- Do NOT restructure pm_inbox/ without a WO — it affects the PM's workflow

---

**End of Handoff**

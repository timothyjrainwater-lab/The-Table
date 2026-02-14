# Work Order: Institutionalize Builder Debrief Protocol

**From:** Builder (Opus 4.6)
**To:** PM (Aegis)
**Date:** 2026-02-14
**Priority:** HIGH — process gap, affects all future WO batches
**Status:** PROPOSAL — requires PM review before enforcement

---

## Context

Builder agents complete work orders and close their context windows. The knowledge accumulated during execution — cascading impacts, schema additions, agent failures, test changes, WO mismatches, loose ends — is lost unless explicitly captured. Currently, some sessions write memos, some write handoff files, some write nothing. There is no mandatory post-WO debrief process.

Section 15.5 has been added to `AGENT_DEVELOPMENT_GUIDELINES.md` (commit `61b8b91`) defining a two-pass debrief protocol. This WO makes it institutional — embedded in dispatch templates, onboarding, and enforcement.

---

## What Section 15.5 Says (Already Committed)

After completing a WO or WO batch, the builder agent MUST produce:

**Pass 1 — Full Dump** (`pm_inbox/DEBRIEF_[SESSION_ID].md`):
Everything from context — cascading impacts, agent failures, schema additions, WO mismatches, test changes, loose ends. No filtering. Raw knowledge capture.

**Pass 2 — PM Summary** (`pm_inbox/MEMO_[SHORT_TITLE].md`):
Compressed memo: Action Items (PM must act), Status Updates (informational), Deferred Items (not blocking).

---

## What Needs to Happen to Make This Institutional

### Action 1: Add Debrief Requirement to Dispatch Template

All future WO dispatches must include this block at the end, after "What NOT to Do":

```markdown
## Post-Completion Debrief (MANDATORY)

Before closing your session, produce a two-pass debrief per Section 15.5
of AGENT_DEVELOPMENT_GUIDELINES.md:

1. **Full Dump** → `pm_inbox/DEBRIEF_[WO-ID].md`
   Write everything: cascading impacts, failures, schema additions,
   WO mismatches, test changes, loose ends. No filtering.

2. **PM Summary** → `pm_inbox/MEMO_[WO-ID]_SUMMARY.md`
   Compress into: Action Items / Status Updates / Deferred Items.

Both files must be committed before session close.
```

### Action 2: Add to Onboarding Checklist

Add to `AGENT_ONBOARDING_CHECKLIST.md` Step 6 (CP Workflow), after step 8:

```markdown
9. Write post-completion debrief (Section 15.5 — two-pass: dump then distill)
```

Also add to Step 4 (Quick-Reference "DO NOT" List):

```markdown
6. **DO NOT** close a session after WO completion without writing a debrief — knowledge dies with your context window
```

### Action 3: Add to FIX_WO_DISPATCH_PACKET Universal Builder Instructions

If a future dispatch packet is created (similar to `FIX_WO_DISPATCH_PACKET.md`), the Universal Builder Instructions section must include:

```markdown
### Post-Completion
After all fixes are committed and tests pass:
1. Write full debrief to pm_inbox/DEBRIEF_[WO-ID].md
2. Write PM summary to pm_inbox/MEMO_[WO-ID]_SUMMARY.md
3. Commit both files
4. Do NOT close session until debrief is committed
```

### Action 4: Enforcement Mechanism

The PM should check for debrief files when processing completed WOs:
- WO marked COMPLETE but no `DEBRIEF_*.md` in pm_inbox → flag as process violation
- WO marked COMPLETE but no `MEMO_*.md` in pm_inbox → flag as process violation
- Both present → process compliant, proceed with review

This is a PM-side check, not a test. You can't unit-test "did the agent write a memo" — but you can make it a PM triage step.

---

## Why This Matters

The proving-ground project has consumed dozens of context windows. Each one accumulated unique knowledge — which files interact, which tests broke unexpectedly, which WO instructions were ambiguous, which assumptions were wrong. Without a debrief protocol, all of that knowledge dies when the session closes. The next agent starts from scratch, hits the same issues, and wastes another context window discovering the same things.

The debrief protocol captures that knowledge in two forms:
- **Full dump** — preserves everything for reference (future agents, thesis data, retrospectives)
- **PM summary** — gives the coordinator actionable intelligence without overwhelming their context window

This is the "artifact primacy" principle applied to session output, not just session state.

---

## Files Already Modified

- `AGENT_DEVELOPMENT_GUIDELINES.md` — Section 15.5 added (commit `61b8b91`)
- `methodology/templates/SESSION_MEMO_TEMPLATE.md` — Template with two-pass process documented

## Files Requiring PM Action

- `AGENT_ONBOARDING_CHECKLIST.md` — Steps 4 and 6 need updates (Actions 2)
- Future dispatch templates — Need debrief block added (Actions 1, 3)
- PM triage process — Need debrief check added (Action 4)

---

**End of Work Order**

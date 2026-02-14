# MEMO: WO_SET → Dispatch Gap — Process Fix Proposals

**From:** Builder (Opus 4.6)
**Date:** 2026-02-14
**Session scope:** Analyze the process gap where PM-verdicted WO sets were advertised as operator-dispatchable without individual dispatch documents being drafted.
**Lifecycle:** NEW

---

## Action Items (PM decides, builder executes)

1. **Choose a fix tier for the WO_SET→Dispatch gap.** Three options below (A, B, C). PM selects one or a combination. Builder executes: edits the governance docs per the selected option. Blocks: future WO_SET processing correctness.

2. **Decide whether the kernel relay model needs updating.** The relay model currently describes only the research→build pipeline. Governance WOs follow a different path that isn't articulated. Builder executes: adds governance WO pipeline to kernel if approved. Blocks: nothing immediately — informational accuracy.

## Root Cause Analysis

The PM processed two WO sets (`WO_SET_PM_CONTEXT_EFFICIENCY.md`, `WO_SET_METHODOLOGY_REFINEMENT.md`), wrote decisions on proposals within them, and archived the sets to `reviewed/`. The briefing then listed items like "Dispatch WO-GOV-CE-01/02 (Wave 1)" under "Requires Operator Action" — implying dispatch-ready documents existed in the inbox.

No individual dispatch documents were ever drafted. The operator had nothing to hand to a builder.

**The gap:** The governance docs define a lifecycle state machine (`NEW → TRIAGED → ACTIONED → ARCHIVE`) that treats all inbox files uniformly. A MEMO and a WO_SET go through the same states. But a WO_SET has a **downstream obligation** that MEMOs don't — it must produce individual dispatch documents. The lifecycle doesn't distinguish "decisions captured" from "dispatches drafted." When the PM set ARCHIVE on the WO_SET, the system treated it as complete. For a WO_SET, it wasn't.

**Why nothing caught it:** No test, naming convention, or process rule checks whether a verdicted WO_SET produced corresponding dispatches. The briefing was the only surface where the gap became visible — and only because the operator noticed the referenced documents didn't exist.

## Proposed Fixes

### Option A: Prose fix (Tier 3 — ~50-60% stickiness)

Add a WO_SET processing rule to the PM Verdict Protocol in `pm_inbox/README.md`:

> **WO_SET-specific rule:** When a WO_SET receives a verdict, the PM must draft individual `WO-*_DISPATCH.md` files for each approved item before setting the WO_SET lifecycle to ARCHIVE. A WO_SET with ARCHIVE lifecycle and no corresponding dispatch documents in the inbox is an incomplete action. The WO_SET is a proposal vehicle; the dispatch document is the execution vehicle.

**Pros:** Low cost, directly addresses the gap, fits existing doc structure.
**Cons:** Prose enforcement — same tier that failed to prevent PM-executes-builder-actions before we had to codify the decision-only principle. Depends on PM reading and remembering the rule across context resets.

### Option B: Briefing guard (Tier 2 — behavioral)

Add a rule to the PM's briefing maintenance protocol:

> The briefing must not list any WO under "Requires Operator Action" unless a corresponding `WO-*_DISPATCH.md` file exists in `pm_inbox/` root. If PM decisions exist but no dispatch doc has been drafted, the item belongs under "Needs PM to Draft WOs."

This is already the corrected briefing structure. The fix is making it a documented rule rather than an ad-hoc correction.

**Pros:** Catches the symptom at the surface the operator reads. Low implementation cost.
**Cons:** Doesn't prevent the underlying error (archiving a WO_SET without producing dispatches) — only prevents the briefing from advertising non-existent artifacts.

### Option C: Lifecycle extension (structural)

Add a `VERDICTED` state to the WO_SET lifecycle:

```
NEW → TRIAGED → VERDICTED → ARCHIVE
```

Where `VERDICTED` means "PM has written decisions but individual dispatch documents have not been drafted." ARCHIVE is only set after dispatches exist. Builder moves to `reviewed/` only on ARCHIVE.

**Pros:** Makes the two-step nature structurally explicit. Prevents premature archival.
**Cons:** Adds complexity to the lifecycle state machine for a case that applies only to WO_SET files. Requires updating README, hygiene tests, and rehydration docs. Over-engineering for a failure mode observed once.

### Recommendation

Option A + B together. Prose rule in README (addresses root cause) plus briefing guard (catches the symptom). If the error recurs after A+B, escalate to Option C. This follows the escalation ladder: tool fix → process tweak → documentation → doctrine.

## Status Updates (Informational only)

- The PM already corrected the briefing structure (splitting "Requires Operator Action" from "Needs PM to Draft WOs") — this memo proposes making that correction permanent via documented rules.
- The kernel at `REHYDRATION_KERNEL_LATEST.md:197` still references `WO_SET_METHODOLOGY_REFINEMENT` as blocked behind RED block lift, but the file is already in `reviewed/`. This is stale — a minor kernel accuracy issue, not the same structural gap.

## Deferred Items (Not blocking, act when convenient)

- The kernel's relay model only describes the research→build pipeline. Governance WOs (proposed internally by PM, not from operator research) follow an undocumented pipeline. Not blocking, but a completeness gap in the PM's operating model.

## Retrospective (Pass 3 — Operational judgment)

- **Fragility:** The WO_SET prefix exists in the naming convention table, but its lifecycle semantics are identical to every other file type. This means the naming convention implies a distinct artifact type (batch of proposals) but the lifecycle treats it as undifferentiated. The naming suggested structure that the process didn't enforce. This is a category of gap worth watching for in other prefix types.

- **Process feedback:** The three-tier enforcement hierarchy predicted this failure mode. The WO_SET lifecycle was Tier 3 (prose-only), and it failed. The briefing correction is effectively a Tier 2 fix (behavioral process rule). The escalation ladder works when applied — the question is whether the PM applies it proactively or only after a failure.

- **Methodology:** This confirms the pattern from the `playtest_log.jsonl` incident: **inherited state is the most common source of unquestioned debt.** The WO_SET files were inherited from a prior PM context window. The new PM context window processed them through the lifecycle without questioning whether the lifecycle was complete for this artifact type. The "audit grandfathered items" rule (builder intake step 5) should have a PM-side equivalent.

- **Concerns:** The PM operates across context resets. Rules that require remembering multi-step obligations across resets are inherently fragile. Option A depends on the PM reading the README rule during rehydration. If the PM's rehydration sequence doesn't include README (it currently reads kernel → checklist → plan), the rule won't load. Either the rule needs to be in the kernel, or the rehydration sequence needs to include README.

---

**End of Memo**

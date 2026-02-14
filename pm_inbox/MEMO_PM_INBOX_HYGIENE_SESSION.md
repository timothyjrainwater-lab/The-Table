# MEMO: PM Inbox Hygiene & Three-Pass Debrief Implementation

**From:** Builder (Opus 4.6)
**Date:** 2026-02-14
**Session scope:** Implement Tier 1 enforcement for pm_inbox lifecycle management and upgrade debrief protocol to three-pass with mandatory retrospective.
**Lifecycle:** NEW

---

## Action Items (PM must act on these)

1. **Add debrief entries to PM_BRIEFING_CURRENT.md** — PM. Two new files were created in pm_inbox this session: `DEBRIEF_PM_INBOX_HYGIENE_AND_DEBRIEF_PROTOCOL.md` (Pass 1 dump) and this memo. The PM was active during file creation, so the builder did not modify the briefing file. Blocks: nothing (PM will see these files during next triage scan).

2. **Resolve PMIH-004 xfail** — PM/Builder. The `MEMO_POST_FIX_PHASE_ACTION_PLAN.md` and `MEMO_BUILDER_DEBRIEF_FIX_PHASE_COMPLETION.md` files lack `## Retrospective` sections (they predate the requirement). Either add retrospective sections to these files or archive them to `reviewed/`, then remove the `@pytest.mark.xfail` from PMIH-004 in `tests/test_pm_inbox_hygiene.py`. Blocks: full GREEN on hygiene tests.

3. **Verify aegis rehydration copy stays synced** — PM. The `pm_inbox/aegis_rehydration/AGENT_DEVELOPMENT_GUIDELINES.md` was out of sync this session (CF-001 failure). It has been fixed. Going forward, any edit to root `AGENT_DEVELOPMENT_GUIDELINES.md` must also be applied to the rehydration copy. The root file has a comment reminding of this, but it was missed once already. Blocks: nothing immediate, but desync causes stale context for rehydrated agents.

## Status Updates (Informational only)

- **PMIH-001 xfail removed** — File count test is now hard enforcement. PM triage brought count from 22 to 4 (cap is 15). The test now passes without xfail.
- **4 test classes active** — PMIH-001 (count, PASS), PMIH-002 (prefix, PASS), PMIH-003 (lifecycle, PASS), PMIH-004 (retrospective, XFAIL).
- **22 files received lifecycle headers** — All existing pm_inbox files now have `**Lifecycle:** NEW|TRIAGED|ARCHIVE` in their first 15 lines.
- **Section 15.5 upgraded to three-pass** — Both root and rehydration copies of AGENT_DEVELOPMENT_GUIDELINES.md updated. SESSION_MEMO_TEMPLATE.md updated with `## Retrospective` section.
- **9 cross-file inconsistencies found and fixed** — Most critical was the aegis rehydration desync (CF-001).
- **File renamed:** `ACTION_PLAN_POST_FIX_PHASE.md` -> `MEMO_POST_FIX_PHASE_ACTION_PLAN.md` (prefix violation caught by PMIH-002).

## Deferred Items (Not blocking, act when convenient)

- **Consider a pre-commit hook for PMIH rules** — Currently the hygiene tests run as part of the test suite. A pre-commit hook that checks prefix and lifecycle before allowing commits to pm_inbox would catch violations earlier (Tier 1.5 enforcement). Low priority — the test catches them post-commit, which is sufficient.
- **Template helper for pm_inbox file creation** — PO raised concern that lifecycle headers would be forgotten without template support. Currently handled by documentation in Section 15.5, onboarding Step 8, and the PMIH-003 test as backstop. A helper function or snippet could further reduce friction.

## Retrospective (Pass 3 — Operational judgment)

- **Fragility:** The biggest fragility is the rehydration copy sync. The root `AGENT_DEVELOPMENT_GUIDELINES.md` has a comment saying "also update the rehydration copy" but that comment was missed during my initial edits. The consistency audit caught it, but only because the PO explicitly asked me to double-check. Without that prompt, the desync would have shipped. This is a structural problem — comments inside files are Tier 3 enforcement. The sync should either be automated (a test that diffs the two files) or eliminated (single source of truth with symlink/include). The pm_inbox hygiene system itself worked well — the test caught the `ACTION_PLAN_POST_FIX_PHASE.md` naming violation immediately, proving Tier 1 enforcement works as designed.

- **Process feedback:** The PO's intervention model was effective. Three clear phases: (1) design the plan, (2) execute, (3) consistency check. The PO didn't micromanage implementation but did catch meta-level issues (the retrospective gap, the consistency concern) that I wouldn't have flagged on my own. The "just take a second and double check" instruction was the most valuable single intervention — it caught 9 inconsistencies that would have been shipped otherwise. This suggests a mandatory self-audit step should be part of every WO completion protocol, not just when the PO asks for it.

- **Methodology:** The 3-tier enforcement model is validated by this session. The 10-item cap at Tier 3 was violated 2.3x over. The same cap at Tier 1 (test-enforced) was immediately respected — the PM triaged the inbox within hours of the test being created. Tier 1 enforcement doesn't just catch violations; it motivates compliance. The three-pass debrief protocol is a new pattern. It solves a real problem (operational judgment being lost at context boundaries) with structural enforcement (PMIH-004 test). The risk is that the retrospective section becomes a checkbox exercise — agents writing "everything went fine" to satisfy the test. The test can enforce the section's existence but not its quality. Quality enforcement would require human review (Tier 2).

- **Concerns:** (1) The pm_inbox now has a robust lifecycle system but the system is self-referential — the rules for managing pm_inbox files are themselves pm_inbox files and methodology files. If an agent modifies the rules (README, test, or Section 15.5) without understanding the full dependency graph, they can introduce inconsistencies faster than the tests can catch them. (2) The PMIH-004 xfail on existing MEMOs creates a period where the retrospective requirement is "enforced but not really" — new MEMOs should have retrospectives, but the test won't fail if they don't (because the xfail absorbs the failure). This should be resolved quickly by adding retrospective sections to the 2 remaining MEMOs or archiving them. (3) Two MEMO files in the inbox (`MEMO_POST_FIX_PHASE_ACTION_PLAN.md` and `MEMO_BUILDER_DEBRIEF_FIX_PHASE_COMPLETION.md`) lack retrospective sections and predate the requirement. They shouldn't be modified to add retrospectives after the fact — that would be retroactive compliance, not genuine reflection. Better to archive them and apply the requirement only to future MEMOs.

---

**End of Memo**

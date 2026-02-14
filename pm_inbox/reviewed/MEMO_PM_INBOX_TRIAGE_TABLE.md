# MEMO: PM Inbox Triage Table — File Disposition Recommendations

**From:** Builder (Opus 4.6)
**Date:** 2026-02-14
**Lifecycle:** NEW

---

## Context

The pm_inbox hygiene system has been implemented (README, PM_BRIEFING_CURRENT.md, test_pm_inbox_hygiene.py, lifecycle headers on all files). The inbox currently has **21 active .md files** against a cap of **15**. The PM must triage 6+ files to bring the count under budget.

The test `tests/test_pm_inbox_hygiene.py::TestPMIH001_ActiveFileCount` is marked `xfail` until this triage is complete. Once the count is ≤15, remove the `xfail` decorator to make the cap a hard enforcement.

---

## Triage Table

**Instructions:** For each file, mark your disposition. `KEEP` = stays in inbox. `ARCHIVE` = move to `pm_inbox/reviewed/`. Files you archive reduce the count.

| # | File | Type | Recommendation | PM Decision |
|---|------|------|---------------|-------------|
| 1 | `BURST_INTAKE_QUEUE.md` | Operational | **KEEP** — active parking lot, regularly updated | ☐ Keep / ☐ Archive |
| 2 | `FIX_WO_DISPATCH_PACKET.md` | WO Dispatch | **KEEP** — 12 active fix WOs not yet dispatched | ☐ Keep / ☐ Archive |
| 3 | `HANDOFF_GOVERNANCE_PATCH.md` | Handoff | **ARCHIVE candidate** — governance patch was largely completed in prior session | ☐ Keep / ☐ Archive |
| 4 | `HANDOFF_PM_INBOX_HYGIENE.md` | Handoff | **ARCHIVE** — superseded by this hygiene implementation. Already marked `Lifecycle: ARCHIVE` | ☐ Keep / ☐ Archive |
| 5 | `MEMO_GOVERNANCE_SESSION_FINDINGS.md` | Memo | **ARCHIVE candidate** — action items were captured in WO_SET and subsequent work | ☐ Keep / ☐ Archive |
| 6 | `MEMO_REVERIFY_A_FINDINGS.md` | Memo | **ARCHIVE candidate** — Domain A findings delivered, WO-VERIFY-A exists as dispatch | ☐ Keep / ☐ Archive |
| 7 | `MEMO_SESSION2_METHODOLOGY_EXTRACT.md` | Memo | **ARCHIVE candidate** — methodology was published, debrief WO was written | ☐ Keep / ☐ Archive |
| 8 | `PO_REVIEW_WO-OSS-DICE-001.md` | PO Review | **ARCHIVE** — already reviewed (marked TRIAGED). No pending action. | ☐ Keep / ☐ Archive |
| 9 | `WO_INSTITUTIONALIZE_DEBRIEF_PROTOCOL.md` | WO | **KEEP or ARCHIVE** — debrief protocol is now in Section 15.5 and onboarding. WO may be moot. | ☐ Keep / ☐ Archive |
| 10 | `WO_SET_METHODOLOGY_REFINEMENT.md` | WO Set | **KEEP** — 6 WOs (GOV-01–06) awaiting dispatch decision | ☐ Keep / ☐ Archive |
| 11 | `WO-BUGFIX-TIER0-001_DISPATCH.md` | WO Dispatch | **KEEP** — 4 Tier 0 correctness bugs, not yet dispatched | ☐ Keep / ☐ Archive |
| 12 | `WO-FIX-12-DESKCHECK.md` | WO | **KEEP** — desk check not yet completed | ☐ Keep / ☐ Archive |
| 13 | `WO-FIX-FINALIZE_DISPATCH.md` | WO Dispatch | **KEEP** — finalize phase not yet executed | ☐ Keep / ☐ Archive |
| 14 | `WO-VERIFY-A_DISPATCH.md` | WO Dispatch | **KEEP** — Wave 2, blocked on WO-VERIFY-D | ☐ Keep / ☐ Archive |
| 15 | `WO-VERIFY-B_DISPATCH.md` | WO Dispatch | **KEEP** — Wave 1, not yet dispatched | ☐ Keep / ☐ Archive |
| 16 | `WO-VERIFY-C_DISPATCH.md` | WO Dispatch | **KEEP** — Wave 1, not yet dispatched | ☐ Keep / ☐ Archive |
| 17 | `WO-VERIFY-D_DISPATCH.md` | WO Dispatch | **KEEP** — Wave 1 priority, not yet dispatched | ☐ Keep / ☐ Archive |
| 18 | `WO-VERIFY-E_DISPATCH.md` | WO Dispatch | **KEEP** — Wave 1, not yet dispatched | ☐ Keep / ☐ Archive |
| 19 | `WO-VERIFY-F_DISPATCH.md` | WO Dispatch | **KEEP** — Wave 1, not yet dispatched | ☐ Keep / ☐ Archive |
| 20 | `WO-VERIFY-G_DISPATCH.md` | WO Dispatch | **KEEP** — Wave 1, not yet dispatched | ☐ Keep / ☐ Archive |
| 21 | `WO-VERIFY-H_DISPATCH.md` | WO Dispatch | **KEEP** — Wave 1, not yet dispatched | ☐ Keep / ☐ Archive |
| 22 | `WO-VERIFY-I_DISPATCH.md` | WO Dispatch | **KEEP** — Wave 1, not yet dispatched | ☐ Keep / ☐ Archive |

---

## Recommended Archive Set (Minimum 6 files to reach cap)

If the PM archives these 6 files, the inbox drops from 21 to 15 (exactly at cap):

1. `HANDOFF_PM_INBOX_HYGIENE.md` — superseded
2. `PO_REVIEW_WO-OSS-DICE-001.md` — already reviewed
3. `MEMO_GOVERNANCE_SESSION_FINDINGS.md` — action items captured elsewhere
4. `MEMO_REVERIFY_A_FINDINGS.md` — findings delivered, dispatch exists
5. `MEMO_SESSION2_METHODOLOGY_EXTRACT.md` — methodology published, WOs written
6. `HANDOFF_GOVERNANCE_PATCH.md` — largely completed

If the PM also archives `WO_INSTITUTIONALIZE_DEBRIEF_PROTOCOL.md` (now institutional), that brings it to 14 with one slot of headroom.

---

## After Triage

Once the PM has archived files and the count is ≤15:
1. Remove the `@pytest.mark.xfail` decorator from `TestPMIH001_ActiveFileCount` in `tests/test_pm_inbox_hygiene.py`
2. Remove the `@pytest.mark.xfail` decorator from `TestPMIH004_MemoRetrospective` once existing MEMOs have retrospective sections (or are archived)
3. Run `pytest tests/test_pm_inbox_hygiene.py -v` to confirm all 4 tests pass
4. The cap and retrospective requirement are now hard-enforced — future violations will fail the test suite

---

## Retrospective

- **Fragility:** The biggest fragility is the rehydration copy sync — the root `AGENT_DEVELOPMENT_GUIDELINES.md` was updated to three-pass but the `aegis_rehydration/` copy wasn't. This is CF-001 (Partial Update) in action. The header comment says "sync after editing" but that's Tier 3 enforcement. A future test could cross-check the two files.
- **Process feedback:** The pm_inbox README's 10-item cap existed since the project's early days but was never enforced. Promoting it to Tier 1 with a test is the correct fix. The naming convention table initially only documented hyphen variants while existing files used underscores — the audit caught the mismatch.
- **Methodology:** The three-pass debrief protocol (dump → distill → reflect) is a new pattern that emerged during this session. It extends Artifact Primacy to cover not just facts but judgment. The retrospective section is the feedback loop that makes the governance stack self-correcting.
- **Concerns:** The PM briefing file depends on every agent updating it — Tier 2 enforcement. If agents skip it, files become invisible. A future Tier 1 test could cross-reference the briefing against actual files, but that's complex to implement correctly.

---

**End of Memo**

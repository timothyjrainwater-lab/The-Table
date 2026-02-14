# MEMO: Dispatch Fluidity Fix + Strategic Assessment Pre-RED-Block

**From:** Builder (Opus 4.6)
**Date:** 2026-02-14
**Session scope:** PM inbox hygiene enforcement, three-pass debrief protocol, dispatch fluidity fix, and pre-RED-block strategic assessment.
**Lifecycle:** NEW

---

## Action Items (PM decides, builder executes)

1. **Scope the is_ranged micro-WO wider** — Three dormant fixes (is_ranged, disarm weapon type, sunder grip) all need the same plumbing: weapon/equipment data flowing from entity schema through to combat context. PM decides: bundle all three into one plumbing WO or keep as separate dispatches. Builder executes: drafts the WO after verdict. Blocks: activating 3 already-implemented rules post-RED-block.

2. **Standardize preflight inspections as a phase gate** — WO-PREFLIGHT-001 is the right pattern for catching stale state before it causes downstream confusion. PM decides: should preflight-style audits be a standard gate before every block lift / phase transition, or remain ad-hoc? Builder executes: adds to methodology if approved. Blocks: nothing immediate.

3. **Prioritize resolver deduplication** — attack_resolver / full_attack_resolver duplication caused a missed sync (sunder grip) and will compound with every future combat rule. PM decides: schedule as first P4 WO after plumbing pass, or defer further? Builder executes: drafts the refactor WO. Blocks: nothing immediate, but cost compounds.

## Status Updates (Informational only)

- `0c8d918` — Fixed builder hesitation in onboarding Step 7. "Wait for approval" replaced with "dispatch is authorization, execute immediately." This was the root cause of the PM stalling on WO-PREFLIGHT-001 handoff.
- `e7c0aa8` — PM decision-only principle codified across 5 governance docs (README, memo template, onboarding, Section 15.5, rehydration copy).
- `fa88875` — playtest_log.jsonl moved to project root per PM verdict. PMIH-003 caught missing lifecycle header on WO-AMBFIX-001 (PM-created file without header — validates Tier 1 enforcement catches all sources).
- `09707f1` — PM inbox hygiene system + three-pass debrief protocol. 4 test classes (PMIH-001 through PMIH-004), README rewrite, PM_BRIEFING_CURRENT.md created, lifecycle headers on all files.

## Deferred Items (Not blocking, act when convenient)

- **Pillow deprecation deadline Oct 2026** — 88 test warnings, mostly deprecation. Not urgent but the test suite's signal-to-noise ratio degrades if warnings accumulate.
- **25 UNCITED formulas** — Mostly Geometry and Conditions domains. Low priority until those domains get feature WOs.

## Retrospective

- **Fragility:** The biggest process fragility exposed this session was the "wait for approval" line in Step 7. A single sentence in the onboarding doc was teaching every builder to hesitate on dispatched WOs. The PM then inherited that hesitation — asking the operator "shall I proceed?" on a read-only inspection it should have just dispatched. The fix was one line change in one file. The lesson: when agents exhibit unwanted behavior, trace it to the instruction that taught them to do it. The behavior is always downstream of the documentation.

- **Process feedback:** The PM decision-only principle was already in the REHYDRATION_KERNEL (line 154: "If the PM executes a builder action, Operator should invoke CONTEXT DRIFT WARNING") but wasn't reflected in the operational docs builders actually read. The principle existed at the strategic level but not at the tactical level. This is a recurring pattern — rules in high-level docs don't propagate to the files that agents actually consult during work. The onboarding checklist and README are the tactical docs; the kernel and guidelines are strategic. Both layers need to say the same thing.

- **Methodology:** The 3-tier enforcement model is now validated across two sessions. Tier 3 prose (10-item cap) was violated 2.3x. Tier 1 test enforcement (15-item cap) was respected within hours — the PM triaged immediately. The PMIH-003 test caught a violation from the PM itself (WO-AMBFIX-001 missing lifecycle header), proving that structural enforcement is role-agnostic. This confirms: if a rule matters, it needs a test. If it doesn't have a test, assume it will be violated.

- **Concerns:** The PM is still doing builder work (creating dispatch files, moving files to reviewed/). The decision-only principle is now documented but the PM agent hasn't internalized it yet — it was trained on the old docs. The next PM context window will rehydrate from the updated kernel and guidelines, which should fix the behavior. But there's a lag between codifying a rule and having it take effect across all active agents. This is the same propagation problem as the aegis rehydration copy desync — just at the agent behavior level instead of the file level.

---

**End of Memo**

# Debrief: WO-ORACLE-SURVEY — Oracle v5.2 Overlap Mapping

**From:** Builder
**Date:** 2026-02-18
**Lifecycle:** COMPLETE
**Commit:** `b475b2f`

---

## Scope Accuracy

WO scope was accurate — all 7 survey sections (5 Oracle objects + event sourcing + canonical serialization) are completed with file paths, line ranges, covering tests, and SATISFIED/PARTIAL/GREENFIELD gap assessments.

## Discovery Log

- **Validated all 4 assumptions.** (1) `aidm/` contains 16 subdirectories; core engine is in `aidm/core/` (81 files). (2) Event emission happens in play_loop.py, attack_resolver.py, spell_resolver.py, maneuver_resolver.py, aoo.py, combat_controller.py — 50+ event types total. (3) NarrativeBrief assembly is indeed the closest WorkingSet analog, but PromptPack (five-channel, byte-equal serialization) is the actual WorkingSet. (4) Session/campaign management exists in campaign_store.py, session_log.py, session.py, campaign.py — more extensive than expected.
- **Strongest overlap: WorkingSet and Event Sourcing.** PromptPack's five-channel structure with `json.dumps(sort_keys=True, ensure_ascii=True)` is already byte-equal deterministic (tested 10x in test_prompt_pack.py). EventLog + replay_runner + RNG manager form a mature event sourcing stack with deterministic replay.
- **Weakest overlap: StoryState.** No threads, clocks, or evented pointer mutation. Campaign management is storage-focused, not narrative-position-focused.
- **Surprise find: W3C PROV-DM in provenance.py.** Full entity/activity/agent/relation model with derivation chains, explain(), and content hashing — but not wired into EventLog. Two provenance systems exist in parallel.
- **Surprise find: KnowledgeMask.** Progressive revelation with default-deny and absent-field semantics (not redacted, truly absent) is a strong UnlockState analog, but only for entity stats.
- **All 12 key modules have covering tests** — no untested infrastructure.

## Methodology Challenge

The constraint "Do not read the GT v12 or Oracle v5.2 memo directly" forces the survey to map against PM-summarized contracts rather than the source spec. If the PM's 1-2 sentence summaries omit nuances, the survey will have blind spots. For FactsLedger in particular, the distinction between "append-only facts" and "append-only events" is architecturally significant — the survey identifies this gap, but a direct spec read would let the builder assess whether Oracle truly requires fact extraction or treats events-as-facts.

## Field Manual Entry

**#13 — Parallel Provenance Systems.** The codebase has two provenance mechanisms: EventLog citations (rule references embedded in events) and ProvenanceStore (W3C PROV-DM derivation chains). They serve different purposes (audit trail vs. derivation tracking) but are not connected. Before building Oracle FactsLedger, decide whether to unify them or keep them separate with a bridge. Unifying reduces complexity; bridging preserves separation of concerns.

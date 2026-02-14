# MEMO: Research Sprint Second-Pass Analysis — Supplementary Observations

**From:** Builder (Opus 4.6), advisory session
**Date:** 2026-02-14
**Session scope:** Deep cross-reference of all 11 research deliverables against builder debrief and PM synthesis to surface missed connections and underweighted findings.
**Lifecycle:** NEW

---

## Action Items (PM decides, builder executes)

1. **GAP-B-002 pairing with GAP-B-001 — scope decision needed.** RQ-003 identified TWO gaps: GAP-B-001 (presentation_semantics is None in NarrativeBrief) and GAP-B-002 (TruthChannel has no fields to serialize Layer B data to Spark). The synthesis lists GAP-B-001 as ARCH-001 and GAP-B-002 as ARCH-003 but treats them independently. They are a pair — fixing GAP-B-001 without GAP-B-002 puts data in the brief that Spark can't consume. **Decision:** Should WO-GAP-B-001 scope include both, or should ARCH-003 be a separate WO? Builder executes: whichever scoping the PM decides. Blocks: narration quality improvements in H1.

2. **"Events record results, not formulas" — codify as boundary law or test.** RQ-007 identifies this as the invariant that makes Type A fixes replay-safe. The PM's synthesis (Section 9.5) calls it DOCTRINE. But it's not in the boundary law list (BL-001 through BL-020), not in AGENT_DEVELOPMENT_GUIDELINES, and not enforced by any test. A future builder who stores `{"formula": "str_mod * 1.5", "result": 10}` in an event payload introduces a silent replay divergence risk. **Decision:** Add as BL-021 and/or add a test that asserts event payloads contain no formula fields? Builder executes: doc edit + optional test. Blocks: nothing immediately, but foundational for versioning safety.

3. **Positive validation (RQ-004) has no WO in the roadmap.** RQ-004's containment audit proposes a novel "positive validation" concept — checking narration IS CONSISTENT WITH Layer B (delivery_mode, staging, scale, VFX vocabulary), not just checking it DOESN'T contain forbidden content. The PM synthesis lists ARCH-010 (NarrationValidator) covering RQ-005's negative rules (RV-001/002/008), but positive validation from RQ-004 has no ARCH entry or WO. **Decision:** Fold into WO-NARRATION-VALIDATOR as a P1 extension, or create a separate WO? Builder executes: PM scoping decision. Blocks: nothing in H0/H1.

## Status Updates (Informational only)

- All 11 research deliverables cross-referenced in depth against builder debrief and PM synthesis.
- No factual errors found in the debrief or synthesis — findings are accurate. The gaps below are missed connections and underweighted observations, not corrections.

## Deferred Items (Not blocking, act when convenient)

- **Discovery Log unification:** RQ-005 (Crystal Ball audit drill-down), RQ-006 (5 ability knowledge tiers with 8 knowledge sources), and RQ-010 (progressive revelation via mechanical fingerprints) all touch the DiscoveryLog subsystem independently. No RQ produced a unified design. When H2 WOs are drafted (WO-DISCOVERY-TIERS), the PM should cross-reference all three RQs rather than relying solely on RQ-006.

- **Stress test as regression asset:** RQ-003's 20-scenario stress test (PASS/PARTIAL/FAIL against NarrativeBrief schema) is a reusable regression test template. When WO-BRIEF-WIDTH lands in H1, the same 20 cases should be re-run to verify improvement from 1 PASS / 10 PARTIAL / 9 FAIL to the target distribution. This should be noted in the WO-BRIEF-WIDTH acceptance criteria.

- **Template infrastructure overlap:** RQ-006 defines 5 mechanical archetype template families for rulebook text generation. RQ-004 identifies 62 narration templates (55 flat + 7 severity-branched) with D&D vocabulary that needs parameterization. Both need per-archetype text templates with world-vocabulary substitution. When WO-RULEBOOK-GEN and WO-CONTAIN-PARAM are drafted (H2), they should share a common template infrastructure rather than building two independent systems.

- **RQ-007's "safer path" warning:** The builder notes that adding `bone_engine_version` to WorldState changes `state_hash()` output, breaking ALL existing replay hashes. The safer path is tracking version in CampaignManifest only, not WorldState. The PM synthesis (ARCH-004) says "add `bone_engine_version` to WorldState (with hash-safe default)" but the builder's own deliverable warns this is risky. WO-VERSION-MVP should explicitly resolve this — CampaignManifest or WorldState?

- **Chatterbox truncation (TD-023) is both a TTS bug and a narration design constraint.** RQ-009 identifies TD-023 (silent truncation at ~60-80 words) as an active blocker. The PM roadmap lists WO-TTS-CHUNKING in H1. But RQ-003's stress test results show that compound events (multi-target AoE, causal chains) produce narration that naturally exceeds 60 words. WO-BRIEF-WIDTH (which produces more complex narration) will hit TD-023 harder. These two WOs have an unstated dependency: BRIEF-WIDTH increases narration length, TTS-CHUNKING handles it. Should be parallel or TTS-CHUNKING first.

## Retrospective (Pass 3 — Operational judgment)

- **Fragility:** This analysis was possible because all 11 deliverables exist as standalone files with consistent structure. If they had been conversational outputs instead of archived documents, this cross-referencing would have been impossible. The three-pass debrief protocol (raw dump → PM summary → retrospective) works here too — the raw deliverables are the dump, the PM synthesis is the summary, and this memo is the retrospective pass that catches what the summary compressed away.

- **Process feedback:** The builder's debrief is well-structured (12 sections, priority stack, cross-cutting themes) but it's a summary of individual findings, not a cross-referencing exercise. The PM synthesis is a roadmap derivation, not a gap analysis. Neither document's purpose is to find connections between RQs that the individual research agents missed. This second-pass analysis fills that role. Consider making "cross-RQ gap analysis" a standard step in multi-deliverable sprints.

- **Methodology:** The strongest signal in the entire sprint is the independent convergence of RQ-002, RQ-003, and RQ-005 on GAP-B-001. This validates the methodology of dispatching independent research agents to different facets of the same system — if three agents find the same gap without coordinating, confidence is high. The weakest signal is in areas where only one agent touched a subsystem (e.g., RQ-007 on versioning) — there's no independent confirmation.

- **Concerns:** The PM synthesis is 300+ lines and the builder debrief is 213 lines. This supplementary memo adds another ~100 lines. The Operator's review burden for this sprint is ~600+ lines of analytical text. The relay block convention mitigates this (Operator gets a one-liner per memo), but when the Operator does deep-read, this is a significant context load. Future sprints should consider whether the PM synthesis alone is sufficient, or whether the supplementary analysis adds enough value to justify the Operator's time.

---

**End of Memo**

# MEMO — Roadmap Audit: H1 WO Coverage, Sequencing, and Gap Analysis

**From:** Roadmap Auditor
**To:** PM (Aegis)
**Date:** 2026-02-14
**Lifecycle:** NEW
**Scope:** Cross-reference of dispatch queue, rehydration kernel, 4-horizon roadmap, and 11 research findings

---

## Executive Summary

The H1 WO batch is well-aligned with the roadmap for its core items but has **3 coverage gaps**, **1 sequencing conflict**, and **2 H2 items that research findings suggest should be promoted to H1**. The PM has drafted 7 dispatch-ready WOs covering 5 of the 6 roadmap-specified H1 items. The missing H1 WO is a trivial omission (TruthChannel fields). The sequencing conflict is between WO-NARRATION-VALIDATOR-001 and WO-BRIEF-WIDTH-001 — already identified in the briefing but worth flagging as a hard dependency. Two H2 items (narration-to-event persistence and `content_id` emission in resolver events) have stronger H1 justification than their current placement suggests.

---

## 1. H1 WO Existence vs. Roadmap Specification

### 1.1 Roadmap-Specified H1 Items (from MEMO_RESEARCH_SPRINT_SYNTHESIS.md §5, Horizon 1)

| Roadmap Item | WO Drafted? | Dispatch Doc? | Status |
|-------------|-------------|---------------|--------|
| WO-BRIEF-WIDTH (NarrativeBrief schema extension) | YES | `WO-BRIEF-WIDTH-001_DISPATCH.md` | DISPATCH-READY |
| WO-NARRATION-VALIDATOR (P0 runtime rules RV-001/002/008) | YES | `WO-NARRATION-VALIDATOR-001_DISPATCH.md` | DISPATCH-READY |
| WO-COMPILE-VALIDATE (CT-001/002/003 cross-validation) | YES | `WO-COMPILE-VALIDATE-001_DISPATCH.md` | DISPATCH-READY |
| WO-TTS-CHUNKING (TD-023 sentence-boundary fix) | YES | `WO-TTS-CHUNKING-001_DISPATCH.md` | DISPATCH-READY |
| WO-RNG-PROTOCOL (RNGProvider Protocol extraction) | YES | `WO-RNG-PROTOCOL-001_DISPATCH.md` | DISPATCH-READY |
| WO-WEAPON-PLUMBING-001 (is_ranged + disarm + sunder) | YES | `WO-WEAPON-PLUMBING-001_DISPATCH.md` | DISPATCH-READY |

**Result: 6 of 6 roadmap H1 items have dispatch documents. Full coverage on named items.**

### 1.2 Roadmap-Specified Architectural Changes That Lack WOs

The synthesis memo §3 specifies ARCH-001 through ARCH-009 as "Immediate" and "Foundation" changes. Cross-referencing against the WO batch:

| ARCH ID | Change | Covered By WO? | Notes |
|---------|--------|-----------------|-------|
| ARCH-001 | Populate `NarrativeBrief.presentation_semantics` | **H0 — DONE** (WO-GAP-B-001, commit e9a9371) | Complete |
| ARCH-002 | Widen NarrativeBrief (multi-target + causal chain + conditions) | WO-BRIEF-WIDTH-001 | Covered |
| ARCH-003 | Add `TruthChannel` fields for Layer B serialization to Spark | **NO WO EXISTS** | **GAP — see §3.1** |
| ARCH-004 | Campaign load version gate | **H0 — DONE** (WO-VERSION-MVP, commit eac5061) | Complete |
| ARCH-005 | `event_schema_version` on Event | **H0 — DONE** (WO-VERSION-MVP) | Complete |
| ARCH-006 | EventLog JSONL metadata header | **H0 — DONE** (WO-VERSION-MVP) | Complete |
| ARCH-007 | Version source of truth | **H0 — DONE** (WO-VERSION-MVP) | Complete |
| ARCH-008 | Compile-time validation pass | WO-COMPILE-VALIDATE-001 | Covered |
| ARCH-009 | RNGProvider Protocol extraction | WO-RNG-PROTOCOL-001 | Covered |

### 1.3 Research-Implied Items in Dispatch Queue But NOT in Roadmap H1

| WO | Source | In Roadmap H1? | Notes |
|----|--------|----------------|-------|
| WO-TTS-COLD-START-RESEARCH | RQ-009, voice research | Not listed as H1 WO | Listed in briefing as dispatch-ready. Research WO, not a builder WO. Correct placement — research feeds future TTS WOs. |

### 1.4 Briefing Non-WO Items

| Item | Status | Notes |
|------|--------|-------|
| XP table spot-check (P1-B) | Listed in briefing §1 item 8 | Non-WO operator action. Not a roadmap gap. |
| Resolver deduplication | Listed as P4 in PM Action Queue | Correctly deferred. Roadmap does not specify this for H1. |

---

## 2. Sequencing Conflicts

### 2.1 WO-NARRATION-VALIDATOR-001 depends on WO-BRIEF-WIDTH-001 — KNOWN, CORRECTLY DOCUMENTED

**Dependency:** WO-NARRATION-VALIDATOR-001 needs condition fields (`active_conditions`, `actor_conditions`) from WO-BRIEF-WIDTH-001 to implement RV-004 (Condition Consistency) and enriched `presentation_semantics` consumption for RV-005/006/007.

**Briefing says:** "Dispatch after BRIEF-WIDTH completes, or in parallel if builder can stub the dependency."

**Assessment:** The stub approach is viable for P0 rules (RV-001/002/008 consume only `action_type`, `target_defeated`, and existing `presentation_semantics` — none of which require BRIEF-WIDTH fields). P1 rules (RV-003 through RV-007) DO require BRIEF-WIDTH. The current WO scope (P0 only) is sequencing-safe for parallel dispatch. **No conflict for the current scope.**

### 2.2 WO-COMPILE-VALIDATE-001 and WO-BRIEF-WIDTH-001 — NO CONFLICT

Both touch the narration pipeline but at different layers (compile-time vs. runtime). The briefing correctly notes they are parallel-safe.

### 2.3 POTENTIAL CONFLICT: WO-COMPILE-VALIDATE-001 needs `content_id` in resolver events

RQ-005 §2.3 specifies that compile-time validation requires `content_id` entries in both `RuleEntry` and `AbilityPresentationEntry` registries. The WO-COMPILE-VALIDATE-001 dispatch document (per briefing) "activates GAP-B-001 pipeline" and requires `content_id` emission in resolver events.

**Risk:** If resolver events do not currently emit `content_id`, then the runtime validation rules in WO-NARRATION-VALIDATOR-001 (specifically RV-005 through RV-007 which consume `presentation_semantics` keyed by `content_id`) have no way to look up the correct Layer B entry for a given resolution event.

**Assessment:** This is a latent dependency. The compile-time validation in WO-COMPILE-VALIDATE-001 operates on compile artifacts (registries), not runtime events, so the compile-time path is unblocked. But the runtime path (WO-NARRATION-VALIDATOR-001 P1 rules) depends on `content_id` being threaded through the resolver → brief assembly → validator chain. **This should be flagged as a dependency for the P1 validator expansion (WO-NARRATION-VALIDATOR-P1 in H2).**

### 2.4 BURST-001 (Voice-First Reliability) vs. WO-TTS-CHUNKING-001

BURST-001 specifies 19 WOs across 5 tiers, including Tier 3 parser/grammar work. WO-TTS-CHUNKING-001 is a standalone TTS fix. These are independent — TTS chunking fixes a defect (TD-023) in the adapter layer, while BURST-001 addresses the broader voice control plane.

**No conflict.** TTS chunking can and should land before BURST-001 builder WOs are drafted.

---

## 3. Missing WOs Implied by Research Findings

### 3.1 MISSING: ARCH-003 — TruthChannel Layer B Serialization

**Source:** RQ-003 (Finding 1, GAP-B-002), Synthesis memo §3.1 ARCH-003
**What:** `TruthChannel` has no fields to serialize Layer B data (delivery_mode, staging, scale, contraindications) to Spark. GAP-B-001 connected the `presentation_semantics` field on NarrativeBrief, but Spark's actual consumption path through TruthChannel does not yet carry this data.
**Impact:** Without this, Spark cannot use Layer B data for narration structure (e.g., two-sentence narration for `TRAVEL_THEN_DETONATE` staging). The NarrationValidator rules RV-005/006/007 validate fields that Spark never received.
**Effort:** Low (schema extension + serialization).
**Recommendation:** Draft a WO. This is the missing link between GAP-B-001 (done) and WO-NARRATION-VALIDATOR-001 (P1 rules). Could be bundled into WO-BRIEF-WIDTH-001 or stand alone.

### 3.2 MISSING: Narration-to-Event Persistence (GAP-4 from RQ-005)

**Source:** RQ-005 §1.2, GAP-4
**What:** After Spark generates narration, the narration text is not persisted alongside its `source_event_ids`. There is no reverse index from narration to events. Post-session audit (Replay Journal, Crystal Ball) requires this linkage.
**Impact:** Blocks all H3 audit UX concepts (Transparency Gem drill-down, Replay Journal, Tome Annotations). Also blocks post-session narration quality analysis.
**Current roadmap placement:** Not explicitly placed. RQ-005 §7 rates it P1. The synthesis memo does not assign it to a horizon.
**Effort:** Low (persist narration text + event IDs at NarrationValidator output point).
**Recommendation:** Draft a micro-WO for H1. The persistence hook is natural to add when WO-NARRATION-VALIDATOR-001 lands (the validator already sits at the narration output point). Deferring it to H2/H3 means retrofit.

### 3.3 MISSING: `content_id` Emission in Resolver Events

**Source:** RQ-005 §2.3 (compile-time validation needs `content_id` as join key), RQ-010 §8 (content_id as "Rosetta Stone")
**What:** Resolver events (attack, spell, maneuver) do not currently emit the `content_id` of the ability being used. Without this, there is no way to join a runtime event to its Layer B presentation entry or its RuleEntry.
**Impact:** Blocks: (a) runtime narration validator Layer B rules (RV-005/006/007), (b) `RuleEntry`-to-`EngineResult` citation flow (GAP-5), (c) mechanical fingerprint lookups at runtime. This is a foundational plumbing item.
**Current roadmap placement:** The briefing notes WO-COMPILE-VALIDATE-001 includes "content_id emission in resolver events." If this is already scoped into that WO, the gap is covered. If not, it needs its own WO.
**Recommendation:** Verify that WO-COMPILE-VALIDATE-001 explicitly includes resolver-level `content_id` emission in event payloads, not just compile-time cross-validation. If the WO only covers compile-time checks, a separate micro-WO is needed.

### 3.4 MISSING: `contraindications` Generation in SemanticsStage

**Source:** RQ-002 §1.2 (contraindications always `()` today), RQ-005 §3.2 rule RV-007 (contraindication enforcement)
**What:** The `contraindications` field on `AbilityPresentationEntry` is always empty. The SemanticsStage does not generate it. The compile-time validation rule CT-006 and runtime rule RV-007 both depend on `contraindications` being populated.
**Impact:** CT-006 and RV-007 are dead code until this field is populated. A fire spell with empty `contraindications` will never trigger the "no ice VFX" check.
**Effort:** Low-medium (~50 lines of mapping logic in SemanticsStage, keyed on damage_type).
**Current roadmap placement:** Not assigned to any WO or horizon.
**Recommendation:** Bundle into WO-COMPILE-VALIDATE-001 scope (since CT-006 is one of its rules), or draft a separate micro-WO. Without this, two validation rules are structurally inert.

### 3.5 MISSING: `residue` Generation in SemanticsStage

**Source:** RQ-002 §1.2 (residue always `()` today), §2.3 (0% deterministic for residue)
**What:** The `residue` field is never generated. RQ-002 notes that ~40% of abilities have deterministic residue (fire → scorch_marks, cold → frost, acid → corrosion).
**Impact:** Low for H1. Residue affects visual post-effect state, not narration correctness. CT-007 (residue vs staging consistency) is a WARN-level rule, not a FAIL.
**Recommendation:** Defer to H2 (WO-RULEBOOK-GEN or WO-UI-DESC scope). No H1 urgency.

### 3.6 NOT MISSING BUT WORTH NOTING: RuleTextSlots Extensions

**Source:** RQ-006 §3 (`usage_constraints`, `interaction_notes`, `mechanical_summary_vague`)
**What:** Three schema fields recommended for rulebook generation quality.
**Current roadmap placement:** Correctly in H2 (WO-RULEBOOK-GEN).
**Assessment:** No gap. H2 placement is appropriate.

---

## 4. H2 Items That Should Be Promoted to H1

### 4.1 PROMOTE: Narration-to-Event Persistence → H1

**Current placement:** Unplaced (between H1 and H3 depending on reading of RQ-005 priorities).
**Why promote:**
1. RQ-005 rates it P1, not P2.
2. The natural insertion point is WO-NARRATION-VALIDATOR-001 — the validator sits at exactly the right pipeline position to persist narration text alongside event IDs.
3. Deferring to H2/H3 means the persistence hook must be retrofitted into a pipeline that has already stabilized, increasing risk.
4. It's low effort (~20-30 lines: write `(narration_text, source_event_ids, timestamp)` to a session-scoped JSONL).
5. It enables post-session narration quality analysis, which is valuable for validating that the H1 narration fidelity WOs actually worked.

### 4.2 PROMOTE: `contraindications` Population → H1

**Current placement:** Unplaced.
**Why promote:**
1. WO-COMPILE-VALIDATE-001 includes CT-006 (contraindication enforcement) and WO-NARRATION-VALIDATOR-001 includes RV-007 (runtime contraindication check). Both are dead rules without populated `contraindications`.
2. Shipping validation rules that can never fire is misleading — the validation pass reports PASS for every entry because the field is empty, not because the data is correct.
3. Effort is low (~50 lines of damage_type → contraindication mapping).
4. It should be scoped into WO-COMPILE-VALIDATE-001 to avoid shipping dead validation.

### 4.3 DO NOT PROMOTE: WO-PATHFIND-PROTOCOL

**Current placement:** H2.
**Why keep H2:** RQ-011 rates pathfinding and AoE geometry extraction at P1 (not P0 like RNG). These are mechanical modularity items that do not affect narration fidelity (H1's goal). The current monolithic pathfinding works correctly; the issue is swappability, which is a quality-of-architecture concern for H2.

### 4.4 DO NOT PROMOTE: WO-VERSION-FULL

**Current placement:** H2.
**Why keep H2:** WO-VERSION-MVP landed in H0. The full version infrastructure (YAML contracts, JSONL header, replay --version-check) is valuable but not blocking any H1 work. No H1 WO depends on full version safety.

### 4.5 DO NOT PROMOTE: WO-DISCOVERY-TIERS

**Current placement:** H2.
**Why keep H2:** Discovery tiers depend on WO-RULEBOOK-GEN (template families), which is H2. Promoting tiers without templates creates an empty progressive revelation system with no text to reveal.

---

## 5. Summary of Findings

| Category | Count | Items |
|----------|-------|-------|
| H1 WOs matching roadmap | 6/6 | BRIEF-WIDTH, NARRATION-VALIDATOR, COMPILE-VALIDATE, TTS-CHUNKING, RNG-PROTOCOL, WEAPON-PLUMBING |
| Sequencing conflicts | 0 hard, 1 soft | NARRATION-VALIDATOR→BRIEF-WIDTH (documented, scoped correctly for P0) |
| Missing WOs (H1 scope) | 3 | ARCH-003 TruthChannel, narration persistence, contraindications population |
| Missing WOs (verify scope) | 1 | content_id emission — may be inside COMPILE-VALIDATE, needs confirmation |
| H2→H1 promotions recommended | 2 | Narration-to-event persistence, contraindications population |
| H2 items correctly placed | 5 | PATHFIND-PROTOCOL, VERSION-FULL, DISCOVERY-TIERS, RULEBOOK-GEN, UI-DESC |

---

## 6. Recommended PM Actions

1. **Verify** WO-COMPILE-VALIDATE-001 scope includes `content_id` emission in resolver event payloads (not just compile-time registry validation). If not, draft a micro-WO.

2. **Draft WO-TRUTHCHANNEL-LAYER-B** (ARCH-003) — TruthChannel serialization of Layer B fields to Spark. Low effort. Could be bundled into WO-BRIEF-WIDTH-001 as an additional deliverable.

3. **Add `contraindications` population** to WO-COMPILE-VALIDATE-001 scope (or draft a separate micro-WO). Without it, CT-006 and RV-007 are dead rules.

4. **Draft WO-NARRATION-PERSIST** — narration-to-event persistence. ~20-30 lines. Natural companion to WO-NARRATION-VALIDATOR-001. Can be dispatched simultaneously with a note that the persistence hook lands at the validator output point.

5. **No sequencing changes needed** for the current WO batch. The briefing's dispatch guidance is correct for the current scope.

---

## Appendix: Research Findings Cross-Reference

| RQ | Key Finding Feeding H1 | WO Coverage |
|----|------------------------|-------------|
| RQ-002 | ui_description gap, contraindications empty | ui_desc → H2 (correct), contraindications → **MISSING from H1** |
| RQ-003 | GAP-B-001 (DONE), GAP-B-002 (TruthChannel), brief width | GAP-B-001 ✓, GAP-B-002 **MISSING**, brief width ✓ |
| RQ-005 | 5 verification gaps, CT rules, RV rules, narration persistence | CT → ✓, RV → ✓, persistence **MISSING** |
| RQ-006 | Text pipeline is stub, schema extensions | Correctly H2 |
| RQ-007 | Version infrastructure | H0 DONE (MVP), H2 (FULL) — correct |
| RQ-009 | TD-023 chunking, STT bottleneck | TD-023 → ✓ (WO-TTS-CHUNKING-001) |
| RQ-010 | content_id as Rosetta Stone, fingerprints | content_id emission — **verify in COMPILE-VALIDATE scope** |
| RQ-011 | RNG P0, pathfinding P1 | RNG → ✓, pathfinding → H2 (correct) |

---

*End of roadmap audit memo.*

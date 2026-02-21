# Burst Intake Queue
**Lifecycle:** NEW

Parking lot for research/strategy bursts that need conversion before entering production planning.

**Protocol (Two-Force Model, effective 2026-02-13):**
- **Burst** = raw operator insight, not yet actionable.
- **Brick** = READY when it includes: (1) Target Lock, (2) Binary Decisions, (3) Contract Spec, (4) Implementation Plan.
- Research WOs are **drafted by PM, executed by Operator**. PM does not execute research.
- PM normalizes research outputs into READY Brick packets.
- Builder WOs are drafted by PM from READY Bricks only. Builders never see upstream research.
- Relay: Operator Intent → PM drafts Research WO → Operator executes → PM normalizes Brick → PM drafts Builder WO → Builders implement.
- WIP limit: 1-2 READY Bricks ahead. Do not open BURST-003+ until BURST-001/002 are converted or deprioritized.
- Dispatch authority: operator-only. PM prepares packets but dispatch requires explicit approval.

---

## READY Bricks

### BURST-001: Voice-First Reliability Membrane — SCOPING COMPLETE

**Target Lock:** Speech input becomes deterministic, confirm-gated, and measurable.

**Status:** SCOPING COMPLETE — Binary decisions resolved (Thunder + Aegis, 2026-02-19). PM to draft Tier 1 builder WOs.

**Binary Decisions (RESOLVED):**

| DC | Question | Answer | Authority |
|---|---|---|---|
| DC-01 | BURST-001 focus | **A: Reliability/control-plane** — single-path audio, routing correctness, logging, replayability | Thunder via Aegis proposal, Slate concurrence |
| DC-02 | Runtime posture for voice work | **B: Batch-per-turn** — generate all lines, synthesize in one batch. Aligns with sequential VRAM posture. | Thunder via Aegis proposal, Slate concurrence |
| DC-03 | STT source of truth | **C: Hybrid** — Win+H stays operator UX; local STT (faster-whisper/whisper.cpp+VAD) for product loop | Thunder via Aegis proposal, Slate concurrence |
| DC-04 | Data handling / backflow safety | **B: Sensor events only** — STT produces non-canon sensor events (audio chunk+hash+transcript). Lens may read, Oracle canon protected. No backflow. | Thunder via Aegis proposal, Slate concurrence |
| DC-05 | Gates | **Accept B1-B5** (see below) | Thunder via Aegis proposal, Slate concurrence |

**Gates (B1-B5):**
- **B1: Single-path playback.** No duplicate chimes, no double voice, one emitter per event.
- **B2: Deterministic routing.** Same inputs choose the same persona, register, and reference set.
- **B3: Swap timing instrumentation.** Measure load, unload, TTFT, first-audio; report separately.
- **B4: Soak stability.** 10 cycles without VRAM creep or routing degradation.
- **B5: Sensor log replay.** Same audio chunks produce same transcript and same downstream events.

**Brick Outputs:**

1. **Target Lock:** Speech input becomes deterministic, confirm-gated, and measurable.
2. **Binary Decisions:** RESOLVED (see table above).
3. **Contract Spec:** Voice-First Reliability Playbook (`pm_inbox/reviewed/legacy_pm_inbox/research/VOICE_FIRST_RELIABILITY_PLAYBOOK.md`) — 547 lines covering unified control-plane model, 7 boundary invariants, CLI grammar (G-01..G-07), 2PC protocol, failure policy (11 classes), Spark failure cascade, template fallback guarantees, metrics/observability (15 compliance checks), prosodic control (PAS v0.1), MVVL definition (10 GREEN thresholds).
4. **Implementation Plan:** 19 WOs across 5 tiers (Spec Freeze → Instrumentation → Parser/Grammar → UX Prompts → Evaluation Harness). Critical path: 1.1 → 3.1 → 3.2 → 3.3 → 3.4 → 5.5. Parallel opportunities: Tiers 2 and 4.1-4.2 alongside Tier 3.

**Research Artifacts (complete, do not send to builders):**
- WO-VOICE-RESEARCH-01: Voice Control Plane Contract (`docs/research/VOICE_CONTROL_PLANE_CONTRACT.md`)
- WO-VOICE-RESEARCH-02: Failure Taxonomy & Unknown Policy (`docs/research/VOICE_FAILURE_TAXONOMY_AND_UNKNOWN_POLICY.md`)
- WO-VOICE-RESEARCH-03: Metrics & Telemetry Spec (`docs/research/VOICE_METRICS_AND_TELEMETRY_SPEC.md`)
- WO-VOICE-RESEARCH-04: UX Turn-Taking & Confirmation (`docs/research/VOICE_UX_TURNTAKING_AND_CONFIRMATION.md`)
- WO-VOICE-RESEARCH-05: Synthesis Playbook (`pm_inbox/reviewed/legacy_pm_inbox/research/VOICE_FIRST_RELIABILITY_PLAYBOOK.md`)

**Next action:** **TIER 1 SPEC FREEZE COMPLETE.** All four tiers accepted: 1.1 Grammar (`Gate J`), 1.2 Unknown Handling (`Gate K`), 1.3 Typed Call (`Gate L`, `a65acea`), 1.4 Boundary Pressure (`Gate M`, `c330db1`). 157 BURST-001 gate tests total. Next: Tier 2 (Instrumentation) — PM drafting.

**Aegis audit carry-forwards (Tier 1.3):**
- **Amendment cost:** Frozen 6x7 matrix (6 CallTypes × 7 dimensions). Adding a CallType requires filling all 7 dimensions + Gate L + validator. Future amendment WOs must scope accordingly.
- **Stage 3 gap:** EvidenceValidator slot is empty. Semantic violations (narrating events that didn't happen) pass the pipeline. Priority candidate for Tier 2.
- **outcome_assertions not enforceable yet:** OA-01 through OA-06 in Stage 2 require NarrativeBrief runtime access. Regex-enforceable checks (MV-01..MV-09, RC-01..RC-04) are active; structural checks are specified but dormant. Wiring WO must distinguish.
- **Fallback stubs are placeholders:** TC-INV-03 satisfied structurally. Production-quality authored fallbacks needed in a future narration polish pass.

**Builder Radar carry-forwards (Tier 1.4):**
- **BP-MISSING-FACT drift risk:** Required field list in Section 1.1 is a copy of Tier 1.3's per-CallType input schemas. No cross-reference enforcement — if Tier 1.3 adds/removes a required field, the Tier 1.4 table drifts silently.
- **`"pending"` sentinel in BP-AUTHORITY-PROXIMITY:** Looks like vocabulary scanning but is a Box pipeline sentinel. Cultural enforcement only (BP-INV-03). Future builder might add string checks, sliding toward vocabulary scanning.
- **Confidence field omitted:** Research defines a `confidence` field (0.0-1.0) on BoundaryPressure. Contract omits it for simplicity — all detections are binary within their level. May revisit in Tier 2 instrumentation.

---

## Active Bursts

### BURST-002: Model/Runtime Constraint Envelope (Spark-Side)

**Target Lock:** Lock where models can be used (prep vs runtime), what's allowed/forbidden, and failure behavior (degrade vs fail-closed).

**Status:** NOT STARTED — burst identified but no research WO drafted.

**Expected outputs:** Gating rules, fallback rules, measurable latency/stability criteria.

**Adjacent existing artifacts:**
- WO-RQ-SPARK-BOUNDARYPRESSURE-01 (boundary pressure runtime signal) — COMPLETE
- WO-RQ-LLM-CALL-TYPING-01 (Lens/Spark typed-call schemas) — COMPLETE

**Binary decisions (needed):**
1. Does Spark failure in prep mode degrade (skip asset) or fail-closed (abort prep)?
2. Does Spark failure in runtime mode degrade (template fallback) or fail-closed (halt session)?
3. Is latency SLA enforced per-call or per-turn?

**Next action:** If operator prioritizes, PM drafts research WO for operator execution. Existing RQ artifacts cover partial ground.

### BURST-003: Tactical Snapshot (ASCII Grid + AoE Preview) — PARTIALLY IMPLEMENTED

**Target Lock:** Player can see spatial state and predict AoE impact before committing actions.

**Status:** PARTIALLY IMPLEMENTED — ASCII grid (`show_map()`) and `map` command are live. AoE preview remains unbuilt.

**What's done:**
- ASCII grid with auto-sized bounding box, entity symbols, coordinate labels, legend: `show_map()` in `play.py`
- `map` / `grid` / `tactical` commands in parser
- First-letter-of-name symbols with collision handling (e.g., G, G2 for two goblins)
- Defeated entities excluded from map
- 4 tests covering grid rendering, defeated exclusion, symbol collision, command parsing

**What remains:**
- AoE overlay preview before spell resolution (center square, entities in radius, save DC, confirm prompt)
- Coordinate roster + distance matrix (optional complement)

**Binary decisions — RESOLVED:**
1. ~~Grid size: fixed 20x20, or bounded to active combat region (auto-sized)?~~ **RESOLVED: Auto-sized** (bounded to active entities + 1-cell padding)
2. AoE preview: display-only, or confirm-gated (require "yes" before resolution)? **OPEN**
3. ~~Grid display trigger: automatic every turn, or on-demand (`map` command)?~~ **RESOLVED: On-demand** (`map` command, free action)
4. ~~Entity symbols: single-letter (A/S/E/G), or first-letter-of-name with collision handling?~~ **RESOLVED: First-letter-of-name with collision handling**

**Next action:** Only AoE preview remains. Operator resolves DC-2 (confirm-gated or display-only). PM drafts 1 builder WO for AoE overlay integration.

### BURST-004: Workflow Friction Self-Detection — NOT STARTED

**Target Lock:** Make workflow stutters (dispatch gaps, hesitation loops, scope-restriction evasion) self-identifying rather than operator-dependent.

**Status:** NOT STARTED — research question identified, 3 candidate approaches assessed in memo. PM verdict: defer until 3+ builder cycles confirm whether A+B fix and briefing guard are sufficient.

**Candidate approaches:**
1. Checkpoint assertions at lifecycle transitions (partially implemented via A+B fix)
2. Briefing as anomaly detection surface (implemented via briefing guard rule)
3. Agent friction self-reporting (unproven, needs lightweight pilot to assess feasibility)

**Binary decisions (needed if escalated):**
1. Friction reporting: structured debrief subsection, or real-time flag during execution?
2. Checkpoint scope: per-artifact-type, or generalized transition validator?

**Next action:** Monitor for recurrence. If 3+ new stutter categories appear in next builder cycles, escalate to governance WO with Approach 3 pilot.

---

## Completed Bursts

(None yet — BURST-001 is READY BRICK, first builder WO ACCEPTED. PRS-01 is a parallel contract track, not a burst.)

## Parallel Tracks (Non-Burst)

### PRS-01: Publishing Readiness Spec — DRAFTED

**Contract:** `docs/contracts/PUBLISHING_READINESS_SPEC.md`
**Origin:** Aegis audit memo (2026-02-19), normalized by Slate with Thunder decisions.
**Status:** DRAFTED — awaiting Thunder review. Not a burst (no research WO needed). Spec-to-WO pipeline.
**Builder WO sequence:** ~6 WOs after spec freeze (see PRS-01 Appendix A).
**Relationship:** Parallel to BURST-001. Neither blocks the other.

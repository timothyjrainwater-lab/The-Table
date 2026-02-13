# Burst Intake Queue

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

### BURST-001: Voice-First Reliability Membrane — READY BRICK

**Target Lock:** Speech input becomes deterministic, confirm-gated, and measurable.

**Status:** READY BRICK — All research complete. Playbook synthesized. 5 binary decisions await operator resolution.

**Brick Outputs:**

1. **Target Lock:** Speech input becomes deterministic, confirm-gated, and measurable.
2. **Binary Decisions (5, operator resolution required):**
   - DC-01: Chatterbox-only or Kokoro CPU fallback for operator voice?
   - DC-02: AUTHORITY detector in Phase 1 or deferred to Phase 2?
   - DC-03: Pressure alerts spoken by DM persona or Arbor?
   - DC-04: EvidenceValidator full implementation or defer to Phase 2?
   - DC-05: Golden transcript stability — all non-Spark lines or structural only?
3. **Contract Spec:** Voice-First Reliability Playbook (`pm_inbox/research/VOICE_FIRST_RELIABILITY_PLAYBOOK.md`) — 547 lines covering unified control-plane model, 7 boundary invariants, CLI grammar (G-01..G-07), 2PC protocol, failure policy (11 classes), Spark failure cascade, template fallback guarantees, metrics/observability (15 compliance checks), prosodic control (PAS v0.1), MVVL definition (10 GREEN thresholds).
4. **Implementation Plan:** 19 WOs across 5 tiers (Spec Freeze → Instrumentation → Parser/Grammar → UX Prompts → Evaluation Harness). Critical path: 1.1 → 3.1 → 3.2 → 3.3 → 3.4 → 5.5. Parallel opportunities: Tiers 2 and 4.1-4.2 alongside Tier 3.

**Research Artifacts (complete, do not send to builders):**
- WO-VOICE-RESEARCH-01: Voice Control Plane Contract (`docs/research/VOICE_CONTROL_PLANE_CONTRACT.md`)
- WO-VOICE-RESEARCH-02: Failure Taxonomy & Unknown Policy (`docs/research/VOICE_FAILURE_TAXONOMY_AND_UNKNOWN_POLICY.md`)
- WO-VOICE-RESEARCH-03: Metrics & Telemetry Spec (`docs/research/VOICE_METRICS_AND_TELEMETRY_SPEC.md`)
- WO-VOICE-RESEARCH-04: UX Turn-Taking & Confirmation (`docs/research/VOICE_UX_TURNTAKING_AND_CONFIRMATION.md`)
- WO-VOICE-RESEARCH-05: Synthesis Playbook (`pm_inbox/research/VOICE_FIRST_RELIABILITY_PLAYBOOK.md`)

**Blocking gate:** DC-01 through DC-05 must be resolved by operator before PM drafts Tier 2+ builder WOs.

**Next action:** Operator resolves 5 binary decisions. PM then drafts Tier 1 spec-freeze WOs as first builder packets.

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

---

## Completed Bursts

(None yet — BURST-001 is READY BRICK but not yet dispatched for build.)

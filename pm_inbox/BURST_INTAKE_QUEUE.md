# Burst Intake Queue

Parking lot for research/strategy bursts that need conversion before entering production planning.

**Protocol:** When an insight burst arrives (from operator or fleet), it stays here until converted into the four required outputs: (1) Target Lock, (2) Binary Decisions, (3) Contract Spec, (4) Implementation Sequencing. Only then does it graduate to a WO set.

---

## Active Bursts

### BURST-001: Voice-First Reliability Membrane

**Target Lock:** Speech input becomes deterministic, confirm-gated, and measurable.

**Status:** IN FLIGHT — WO-VOICE-RESEARCH-01..05 dispatched to fleet. Awaiting WO-VOICE-RESEARCH-05 synthesis.

**Expected outputs:** Command grammar, confirmation rules, ambiguity handling, telemetry metrics, UX turn-taking. Consolidated into Voice-First Reliability Playbook.

**Binary decisions (pending synthesis):** TBD from WO-05 delivery.

**Adjacent existing artifacts:**
- WO-RQ-AUDIOFIRST-CLI-CONTRACT-01 (audio-first CLI output grammar) — COMPLETE
- WO-RQ-UNKNOWN-TAXONOMY-01 (unknown handling policy) — DRAFT

**Next action:** Await WO-05 synthesis. PM audits for boundary compliance, extracts binary decisions, issues implementation WOs.

---

### BURST-002: Model/Runtime Constraint Envelope (Spark-Side)

**Target Lock:** Lock where models can be used (prep vs runtime), what's allowed/forbidden, and failure behavior (degrade vs fail-closed).

**Status:** NOT STARTED — burst identified but no fleet dispatch.

**Expected outputs:** Gating rules, fallback rules, measurable latency/stability criteria.

**Adjacent existing artifacts:**
- WO-RQ-SPARK-BOUNDARYPRESSURE-01 (boundary pressure runtime signal) — COMPLETE
- WO-RQ-LLM-CALL-TYPING-01 (Lens/Spark typed-call schemas) — COMPLETE

**Binary decisions (needed):**
1. Does Spark failure in prep mode degrade (skip asset) or fail-closed (abort prep)?
2. Does Spark failure in runtime mode degrade (template fallback) or fail-closed (halt session)?
3. Is latency SLA enforced per-call or per-turn?

**Next action:** Convert to research WO when operator prioritizes. Existing RQ artifacts cover partial ground.

---

## Completed Bursts

(None yet)

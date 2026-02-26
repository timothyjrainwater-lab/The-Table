# WO-BURST-002-RESEARCH-001 — Spark Runtime Constraint Envelope

**Issued:** 2026-02-23
**Authority:** BURST-002 binary decisions RESOLVED (Thunder 2026-02-23). Adjacent research complete: WO-RQ-SPARK-BOUNDARYPRESSURE-01 (pre-generation gating), WO-RQ-LLM-CALL-TYPING-01 (call contracts).
**Gate:** New gate — target 12 tests. Gate letter assigned at acceptance.
**Blocked by:** Nothing.

---

## 1. Target Lock

Define and enforce what Spark is allowed to do at runtime — not what it may *say* (that's WO-RQ-LLM-CALL-TYPING-01) but when it may *run*, how long it may take, what happens when it fails, and how the system degrades gracefully. Three missing constraints: model loading failures have no policy, TTFT/inference latency has no SLA, and the fallback escalation path is unspecified.

**What already exists:**
- Pre-generation gating: `BoundaryPressure` (GREEN/YELLOW/RED) prevents bad calls before they fire (WO-RQ-SPARK-BOUNDARYPRESSURE-01)
- Post-generation validation: GrammarShield + evidence discipline (WO-RQ-LLM-CALL-TYPING-01)
- Latency infrastructure: `performance_profiler.py` tracks BOX and LENS latency (not Spark)
- Fallback chain: `load_model_with_fallback()` retries 3× but no policy after exhaustion
- Stub mode: `_load_model()` / `_unload_model()` in `prep_pipeline.py` are NotImplementedError stubs

**What BURST-002 adds:**
- Failure policy: what happens when all model fallbacks are exhausted (prep and runtime)
- Latency SLA: per-call TTFT and inference time targets, enforcement via timeout
- Degradation states: defined, logged, surfaced to operator
- Runtime constraint gate: tests that enforce these policies

---

## 2. Binary Decisions (RESOLVED)

| # | Decision | Choice | Authority |
|---|---|---|---|
| 1 | Prep-mode Spark failure | **Skip asset, continue prep** — mark `prep_failed`, log, proceed with templates | Thunder 2026-02-23 |
| 2 | Runtime Spark failure | **Template fallback narration** — set `narration_degraded=True`, emit notice, continue gameplay | Thunder 2026-02-23 |
| 3 | Latency SLA scope | **Per individual LLM call** (p95) — turn wall-clock recorded as secondary metric only | Thunder 2026-02-23 |

---

## 3. Contract Spec

### 3.1 Failure taxonomy (new enum)

```python
# aidm/spark/spark_failure.py (new file)
from enum import Enum

class SparkFailureMode(Enum):
    MODEL_LOAD_TIMEOUT    = "model_load_timeout"      # _load_model() exceeded budget
    MODEL_LOAD_OOM        = "model_load_oom"          # VRAM/RAM exhausted at load
    INFERENCE_TIMEOUT     = "inference_timeout"        # Per-call wall-clock exceeded SLA
    INFERENCE_OOM         = "inference_oom"           # OOM during inference (mid-call)
    FALLBACK_EXHAUSTED    = "fallback_exhausted"      # All models in chain failed
    CONTEXT_OVERFLOW      = "context_overflow"        # Input exceeds context window
```

### 3.2 Per-call latency SLA (new constants)

```python
# aidm/spark/spark_sla.py (new file)
# Per-call latency targets (wall-clock seconds, p95 enforcement)
# Source: Thunder binary decision 2026-02-23

SPARK_SLA_PER_CALL = {
    "COMBAT_NARRATION":      {"timeout_s": 8.0,  "p95_target_s": 5.0},
    "OPERATOR_DIRECTIVE":    {"timeout_s": 5.0,  "p95_target_s": 3.0},
    "SUMMARY":               {"timeout_s": 12.0, "p95_target_s": 8.0},
    "RULE_EXPLAINER":        {"timeout_s": 8.0,  "p95_target_s": 5.0},
    "CLARIFICATION_QUESTION":{"timeout_s": 4.0,  "p95_target_s": 2.5},
    "NPC_DIALOGUE":          {"timeout_s": 8.0,  "p95_target_s": 5.0},
}

# Turn wall-clock (secondary — recorded, not enforced)
TURN_WALL_CLOCK_BUDGET_S = 15.0
```

### 3.3 Degradation state

```python
# Add to SparkResponse (aidm/spark/spark_adapter.py):
degraded: bool = False
failure_mode: SparkFailureMode | None = None
fallback_used: bool = False   # True if template narration substituted
```

### 3.4 Prep pipeline failure policy

When a Spark call during prep fails (any `SparkFailureMode`):

```python
# Pseudo-code for prep_pipeline.py:
try:
    result = spark.generate(request)
except SparkFailure as e:
    asset.status = "prep_failed"
    asset.failure_mode = e.mode
    log_evidence_frame(asset_id=asset.id, failure=e)
    continue   # Skip to next asset — do NOT abort prep
```

Template narration placeholder for failed prep assets:
```
"[Narration unavailable — model failure during prep. Template in use.]"
```

### 3.5 Runtime failure policy

When a Spark call during live gameplay fails:

```python
# Pseudo-code for session orchestrator:
try:
    response = spark.generate(request, timeout=SPARK_SLA_PER_CALL[call_type]["timeout_s"])
except SparkFailure as e:
    response = SparkResponse(
        text=TEMPLATE_NARRATION[call_type],   # deterministic fallback
        degraded=True,
        failure_mode=e.mode,
        fallback_used=True,
    )
    emit_sensor_event("SPARK_DEGRADED", failure_mode=e.mode, call_type=call_type)
    print(f"[AIDM] Narration degraded ({e.mode.value}). Gameplay continues.")
```

Template narration strings (one per CallType — deterministic, no inference):
```python
TEMPLATE_NARRATION = {
    "COMBAT_NARRATION":      "The action resolves.",
    "OPERATOR_DIRECTIVE":    "Understood.",
    "SUMMARY":               "Events recorded.",
    "RULE_EXPLAINER":        "See rulebook for details.",
    "CLARIFICATION_QUESTION":"Please clarify your intent.",
    "NPC_DIALOGUE":          "...",
}
```

### 3.6 TTFT measurement (new instrumentation)

Add to `SparkAdapter.generate()`:

```python
import time

t_call_start = time.perf_counter()
# ... inference ...
t_first_token = time.perf_counter()  # record when first token arrives
t_complete = time.perf_counter()

ttft_s = t_first_token - t_call_start
inference_s = t_complete - t_call_start

# Log to performance_profiler bucket "spark_call"
profiler.record("spark_call", {
    "call_type": call_type,
    "ttft_s": ttft_s,
    "inference_s": inference_s,
    "model_id": model_id,
    "degraded": response.degraded,
})
```

---

## 4. Implementation Plan

1. **Read** `aidm/spark/spark_adapter.py` — locate `SparkResponse`, `generate()` method, timeout handling
2. **Read** `aidm/spark/llamacpp_adapter.py` lines 145-265 — `load_model()`, `load_model_with_fallback()`
3. **Read** `aidm/core/prep_pipeline.py` — locate the NotImplementedError stubs and asset iteration loop
4. **Read** `aidm/testing/performance_profiler.py` — confirm bucket API for adding `spark_call` measurements
5. **Create** `aidm/spark/spark_failure.py` — `SparkFailureMode` enum
6. **Create** `aidm/spark/spark_sla.py` — `SPARK_SLA_PER_CALL` + `TEMPLATE_NARRATION` + `TURN_WALL_CLOCK_BUDGET_S`
7. **Extend** `SparkResponse` — add `degraded`, `failure_mode`, `fallback_used` fields
8. **Extend** `SparkAdapter.generate()` — TTFT measurement, timeout enforcement, failure handling → return degraded response instead of raising
9. **Extend** `prep_pipeline.py` — catch `SparkFailure`, mark asset `prep_failed`, continue
10. **Write** `tests/test_spark_runtime_gate.py` — 12 tests
11. **Run** `pytest tests/test_spark_runtime_gate.py -v` — all pass
12. **Run** `pytest tests/ --tb=no -q` — zero regressions

---

## 5. Deliverables Checklist

- [ ] `aidm/spark/spark_failure.py`: `SparkFailureMode` enum (6 modes)
- [ ] `aidm/spark/spark_sla.py`: per-call SLA table, template narration strings, turn budget constant
- [ ] `SparkResponse`: `degraded`, `failure_mode`, `fallback_used` fields added
- [ ] `SparkAdapter.generate()`: TTFT measurement, timeout enforcement, graceful degradation
- [ ] `prep_pipeline.py`: asset-level failure catch, `prep_failed` status, log evidence
- [ ] `tests/test_spark_runtime_gate.py`: 12 tests, all PASS
- [ ] Zero regressions vs 6,536 baseline

---

## 6. Test Spec (12 tests)

| Test | What it checks |
|---|---|
| T-01 | `SparkFailureMode` enum has exactly 6 members |
| T-02 | `SPARK_SLA_PER_CALL` has entries for all 6 CallTypes |
| T-03 | Each SLA entry has `timeout_s` and `p95_target_s` keys, both floats |
| T-04 | `TEMPLATE_NARRATION` has entries for all 6 CallTypes, all non-empty strings |
| T-05 | `SparkResponse` has `degraded` (bool), `failure_mode` (SparkFailureMode or None), `fallback_used` (bool) |
| T-06 | Degraded response with `INFERENCE_TIMEOUT` mode carries correct template for COMBAT_NARRATION |
| T-07 | Degraded response `fallback_used=True` when template substituted |
| T-08 | Prep pipeline: asset marked `prep_failed` when SparkFailure raised, pipeline continues (does not raise) |
| T-09 | Prep pipeline: subsequent asset after failure still processed (skip, not abort) |
| T-10 | TTFT measurement: `spark_call` record contains `ttft_s`, `inference_s`, `call_type`, `degraded` keys |
| T-11 | `TURN_WALL_CLOCK_BUDGET_S` is a float > 0 |
| T-12 | Sensor event `SPARK_DEGRADED` emitted on runtime failure (mock spark, verify event) |

---

## 7. Integration Seams

- Do NOT change `BoundaryPressure` or pre-generation gating (WO-RQ-SPARK-BOUNDARYPRESSURE-01) — this WO adds post-decision failure handling, not pre-call gating
- Do NOT change GrammarShield or CallType contracts (WO-RQ-LLM-CALL-TYPING-01)
- `load_model_with_fallback()` stays unchanged — BURST-002 handles failure *after* that chain exhausts
- `prep_pipeline.py` NotImplementedError stubs remain stubs — do not implement real model loading (that's a future WO)
- `performance_profiler.py`: add `spark_call` bucket only, do not modify existing buckets

---

## 8. Preflight

```bash
pytest tests/test_spark_runtime_gate.py -v   # gate passes
pytest tests/ --tb=no -q                      # zero new failures
```

---

## 9. Debrief Focus

1. **Fallback exhaustion path** — trace through what actually happens when `load_model_with_fallback()` exhausts all 3 retries. Does the new failure policy intercept it? Show the call stack.
2. **TTFT measurement point** — for llama.cpp streaming, exactly where is "first token" measured? Document the code path.

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

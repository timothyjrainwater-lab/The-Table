# M2 Acceptance Criteria — Spark Swappability
## Testable Pass/Fail Requirements for SPARK_SWAPPABLE_INVARIANT

**Document Type:** Governance / Acceptance Criteria
**Status:** ✅ **BINDING** (M2 gate)
**Date:** 2026-02-10
**Authority:** PM (Aegis)
**Parent Documents:**
- `docs/doctrine/SPARK_SWAPPABLE_INVARIANT.md` (invariant definition)
- `docs/specs/SPARK_PROVIDER_CONTRACT.md` (interface contract)

---

## 1. Purpose

**This document defines binary pass/fail acceptance tests for Spark swappability.**

**M2 Completion Criteria:**
- ALL acceptance tests MUST pass before M2 is declared complete
- ANY test failure constitutes M2 incomplete (STOP condition)
- Tests MUST be reproducible (same inputs → same results)

**Scope:**
- Configuration-driven selection
- Hot-swap determinism
- Capability handling
- Fallback behavior
- Code audit (no hard-coded providers)

---

## 2. Test Environment Setup

### 2.1 Required Test Models

**For acceptance testing, MUST have:**

| Model | Purpose | Context Window | RAM Req |
|-------|---------|----------------|---------|
| **Mistral 7B (4-bit)** | Primary SPARK | 8192 | 4-6 GB |
| **Phi-2 (4-bit)** | Fallback SPARK | 2048 | 2-3 GB |

**Registry Configuration (models.yaml):**
```yaml
spark:
  default: "mistral-7b-4bit"
  models:
    - id: "mistral-7b-4bit"
      provider: "llamacpp"
      path: "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
      context_window: 8192
      capabilities: {streaming: true, json_mode: false}
    - id: "phi-2-4bit"
      provider: "llamacpp"
      path: "models/phi-2.Q4_K_M.gguf"
      context_window: 2048
      capabilities: {streaming: true, json_mode: false}
```

---

### 2.2 Test Scenario (Canonical)

**All tests use same scenario for reproducibility:**

**Scenario:** Attack roll hit event
- Attacker: Fighter (BAB +5, STR +3)
- Target: Orc (AC 15)
- Roll: d20 = 12 → Total 20 (12 + 5 + 3)
- Result: HIT (20 ≥ 15)
- Damage: 1d8+3 = 5+3 = 8 damage

**Expected BOX Output:**
```json
{
  "event_type": "attack_roll",
  "result": "hit",
  "attack_roll": 20,
  "target_ac": 15,
  "damage": 8,
  "damage_type": "slashing"
}
```

**Expected SPARK Task:**
Generate narration for this event (SPARK output varies by model, BOX output identical).

---

## 3. Acceptance Tests (6 Required)

### TEST-001: Configuration-Driven Selection

**Requirement:** User MUST be able to select SPARK via config, NOT code.

**Test Procedure:**
1. Load default config (default: "mistral-7b-4bit")
2. Verify SPARK loaded is Mistral 7B
3. Override via environment variable: `AIDM_SPARK_MODEL=phi-2-4bit`
4. Reload AIDM
5. Verify SPARK loaded is Phi-2

**Pass Criteria:**
- ✅ Default SPARK matches config (Mistral 7B)
- ✅ Override via env var succeeds (Phi-2 loaded)
- ✅ No source code modification required

**Fail Criteria:**
- ❌ SPARK selection requires code changes
- ❌ Environment variable override ignored
- ❌ Wrong model loaded (mismatch between config and active SPARK)

**Verification Method:**
```python
# Test code
assert spark.model_id == "mistral-7b-4bit"  # Default

os.environ["AIDM_SPARK_MODEL"] = "phi-2-4bit"
reload_aidm()

assert spark.model_id == "phi-2-4bit"  # Override
```

**Status:** ⏸️ **PENDING M2 IMPLEMENTATION**

---

### TEST-002: Hot-Swap Determinism

**Requirement:** Swapping SPARK MUST NOT change BOX outcomes.

**Test Procedure:**
1. Run canonical scenario with Mistral 7B SPARK
2. Capture BOX output (attack result, damage)
3. Swap to Phi-2 SPARK (reload config)
4. Run SAME scenario (same RNG seed, same inputs)
5. Capture BOX output

**Pass Criteria:**
- ✅ BOX outputs are BYTE-FOR-BYTE IDENTICAL (attack result, damage, hit/miss)
- ✅ SPARK narrations MAY differ (acceptable, expected)
- ✅ Event log mechanics IDENTICAL (only narration field varies)

**Fail Criteria:**
- ❌ BOX outputs differ (attack result changes, damage changes)
- ❌ Hit/miss outcome changes
- ❌ Event log mechanics differ

**Verification Method:**
```python
# Run 1: Mistral SPARK
result_mistral = run_scenario(spark="mistral-7b-4bit", seed=42)

# Run 2: Phi-2 SPARK
result_phi2 = run_scenario(spark="phi-2-4bit", seed=42)

# Verify BOX determinism
assert result_mistral.attack_result == result_phi2.attack_result  # IDENTICAL
assert result_mistral.damage == result_phi2.damage  # IDENTICAL
assert result_mistral.hit == result_phi2.hit  # IDENTICAL

# SPARK narrations MAY differ (acceptable)
# result_mistral.narration != result_phi2.narration  # ALLOWED
```

**Status:** ⏸️ **PENDING M2 IMPLEMENTATION**

---

### TEST-003: Capability Mismatch Handling

**Requirement:** Requesting unsupported capability MUST gracefully degrade or fail-fast.

**Test Procedure:**
1. Load SPARK with `json_mode: false` (e.g., Mistral 7B via llama.cpp)
2. Request generation with `json_mode=True`
3. Verify system uses fallback strategy (guided generation)
4. Verify response is valid (JSON parsed successfully)

**Pass Criteria:**
- ✅ System detects capability mismatch (json_mode not supported)
- ✅ Fallback strategy triggered (guided generation with JSON instructions in prompt)
- ✅ Response is valid JSON (parsed successfully)
- ⚠️ User notified of degraded mode (warning logged)

**Fail Criteria:**
- ❌ System crashes or throws unhandled exception
- ❌ Response is malformed JSON (no fallback applied)
- ❌ No user notification of capability mismatch

**Verification Method:**
```python
# Load SPARK without JSON mode
spark = load_spark("mistral-7b-4bit")
assert not spark.supports_json_mode()

# Request JSON output
response = spark.generate(prompt="...", json_mode=True)

# Verify fallback triggered
assert "JSON" in response.prompt  # Fallback added JSON instructions
assert json.loads(response.text)  # Valid JSON parsed
```

**Status:** ⏸️ **PENDING M2 IMPLEMENTATION**

---

### TEST-004: OOM Fallback

**Requirement:** Out-of-memory MUST trigger fallback to smaller model with user notification.

**Test Procedure:**
1. Simulate OOM condition (mock RAM exhaustion)
2. Attempt to load Mistral 7B (requires 6 GB RAM)
3. Verify system falls back to Phi-2 (requires 3 GB RAM)
4. Verify user notification displayed

**Pass Criteria:**
- ✅ OOM detected (exception caught)
- ✅ Fallback to Phi-2 succeeds
- ✅ User warned: "Using smaller model due to memory constraints"
- ✅ System remains functional (narration continues)

**Fail Criteria:**
- ❌ System crashes on OOM (no fallback)
- ❌ No user notification (silent fallback)
- ❌ Fallback fails (system unusable)

**Verification Method:**
```python
# Mock OOM condition
with mock_oom_on_load("mistral-7b-4bit"):
    spark = load_spark_with_fallback(default="mistral-7b-4bit", fallback="phi-2-4bit")

# Verify fallback succeeded
assert spark.model_id == "phi-2-4bit"
assert "memory constraints" in get_last_warning()
```

**Status:** ⏸️ **PENDING M2 IMPLEMENTATION**

---

### TEST-005: No Hard-Coded Provider Audit

**Requirement:** Source code MUST NOT contain hard-coded model paths or provider names.

**Test Procedure:**
1. Audit codebase for hard-coded model references
2. Run grep checks (see below)
3. Verify 0 violations

**Pass Criteria:**
- ✅ Zero hard-coded model paths found (all paths from config)
- ✅ Zero hard-coded provider names (all providers from registry)
- ✅ All SPARK invocations use registry-loaded providers

**Fail Criteria:**
- ❌ Hard-coded model path detected (e.g., `"models/mistral-7b.gguf"` in source)
- ❌ Hard-coded provider name detected (e.g., `provider = "llamacpp"` in source)
- ❌ Any SPARK invocation bypasses registry

**Verification Commands:**
```bash
# Check for hard-coded model paths
grep -r 'model_path.*=.*".*\.gguf"' aidm/ --include="*.py"
# MUST return 0 results

# Check for hard-coded provider names
grep -r 'provider.*=.*"llamacpp"' aidm/ --include="*.py"
# MUST return 0 results

# Check for model name references in code (should only be in config)
grep -r '"mistral-7b\|"phi-2\|"llama' aidm/ --include="*.py" | grep -v "# comment"
# MUST return 0 results (model names only in models.yaml)
```

**Status:** ⏸️ **PENDING M2 IMPLEMENTATION**

---

### TEST-006: Lens/Box Gating Preserved

**Requirement:** ALL SPARK outputs MUST pass through LENS/BOX validation.

**Test Procedure:**
1. Swap SPARK to different model (Mistral → Phi-2)
2. Generate narration
3. Verify LENS provenance labeling applied
4. Verify BOX mechanics unchanged

**Pass Criteria:**
- ✅ SPARK output tagged `[NARRATIVE]` by LENS (provenance preserved)
- ✅ No mechanical claims from SPARK bypass BOX validation
- ✅ Swapping SPARK does NOT weaken validation

**Fail Criteria:**
- ❌ SPARK output presented without provenance label
- ❌ SPARK mechanical claim (e.g., damage value) used without BOX validation
- ❌ LENS filtering disabled or bypassed

**Verification Method:**
```python
# Generate with Mistral
response_mistral = generate_narration(spark="mistral-7b-4bit", event=attack_event)
assert "[NARRATIVE]" in response_mistral  # LENS provenance

# Generate with Phi-2
response_phi2 = generate_narration(spark="phi-2-4bit", event=attack_event)
assert "[NARRATIVE]" in response_phi2  # LENS provenance

# Verify BOX mechanics unchanged
assert extract_damage(response_mistral) == None  # No mechanical claim from SPARK
assert extract_damage(response_phi2) == None  # No mechanical claim from SPARK
```

**Status:** ⏸️ **PENDING M2 IMPLEMENTATION**

---

## 4. Test Execution Summary

### 4.1 Test Status Table

| Test ID | Requirement | Status | Blocker |
|---------|-------------|--------|---------|
| **TEST-001** | Configuration-driven selection | ⏸️ PENDING | M2 implementation |
| **TEST-002** | Hot-swap determinism | ⏸️ PENDING | M2 implementation |
| **TEST-003** | Capability mismatch handling | ⏸️ PENDING | M2 implementation |
| **TEST-004** | OOM fallback | ⏸️ PENDING | M2 implementation |
| **TEST-005** | No hard-coded provider audit | ⏸️ PENDING | M2 implementation |
| **TEST-006** | Lens/Box gating preserved | ⏸️ PENDING | M2 implementation |

**M2 Completion:** ✅ ALL 6 tests MUST pass

---

### 4.2 Test Execution Workflow

**Phase 1: Pre-Implementation (Now)**
- ✅ Acceptance tests defined (this document)
- ✅ Test scenarios documented (canonical attack roll)
- ⏸️ Implementation pending (M2 execution phase)

**Phase 2: Implementation (M2 Execution)**
- Implement SPARK registry (models.yaml loader)
- Implement SPARK adapters (LlamaCppAdapter)
- Implement capability validation
- Implement fallback logic

**Phase 3: Testing (M2 Validation)**
- Execute TEST-001 through TEST-006
- Document results (PASS/FAIL)
- Fix failures, re-test until all pass

**Phase 4: Certification (M2 Closeout)**
- Agent D reviews test results
- All 6 tests PASS → M2 certified complete
- Any test FAIL → M2 incomplete (STOP condition)

---

## 5. Stop Conditions (Test Failures)

**Any of the following test failures constitutes M2 incomplete:**

### STOP-TEST-001: Configuration Override Fails

**Symptom:** User cannot override SPARK via environment variable or config

**Impact:** Swappability broken (hard-coded model forced)

**Remediation:** Fix registry loader to respect overrides

---

### STOP-TEST-002: Determinism Violation

**Symptom:** Swapping SPARK changes BOX outcomes (attack result differs)

**Impact:** 🔴 **CRITICAL** — Core architectural principle violated

**Remediation:** Ensure BOX never reads SPARK outputs for mechanical decisions

---

### STOP-TEST-003: No Capability Fallback

**Symptom:** Requesting unsupported capability crashes system

**Impact:** System unusable with providers lacking features (e.g., JSON mode)

**Remediation:** Implement graceful degradation (guided generation fallback)

---

### STOP-TEST-004: OOM Crash

**Symptom:** Out-of-memory crashes system instead of falling back

**Impact:** System unusable on minimum spec hardware

**Remediation:** Implement OOM detection + fallback to smaller model

---

### STOP-TEST-005: Hard-Coded Model Found

**Symptom:** Grep audit finds hard-coded model path in source

**Impact:** Swappability violated (code changes required to swap models)

**Remediation:** Move all model references to configuration

---

### STOP-TEST-006: LENS/BOX Bypass

**Symptom:** SPARK output presented without provenance label

**Impact:** Trust violation (cannot distinguish SPARK narrative from BOX truth)

**Remediation:** Ensure all SPARK output routed through LENS

---

## 6. Acceptance Thresholds

### 6.1 Schema Validity

**Requirement:** SPARK responses MUST conform to canonical schema.

**Threshold:** ≥99% schema-valid responses (1% tolerance for edge cases)

**Measurement:**
- Run 100 SPARK requests with various prompts
- Validate each response against SparkResponse schema
- Count malformed responses

**Pass:** ≤1 malformed response in 100 (99%+ valid)

**Fail:** >1 malformed response (schema validation insufficient)

---

### 6.2 Abstention Behavior

**Requirement:** When SPARK cannot generate valid response, MUST abstain (return empty string or error).

**Threshold:** ≥95% valid abstentions (no hallucinated responses when uncertain)

**Measurement:**
- Provide 20 prompts with insufficient context (e.g., "What happened in session 99?" when only session 1-5 exist)
- Verify SPARK abstains (e.g., "I don't have records for session 99") instead of hallucinating

**Pass:** ≥19/20 prompts result in abstention (95%+)

**Fail:** <19/20 prompts result in abstention (hallucination detected)

---

### 6.3 Failure Mode Handling

**Requirement:** SPARK failures MUST degrade gracefully (no crashes).

**Threshold:** 100% graceful degradation (0 crashes on failure)

**Measurement:**
- Simulate 10 failure modes (OOM, timeout, malformed response, etc.)
- Verify system remains functional (falls back to template or smaller model)

**Pass:** 10/10 failures handled gracefully (no crashes)

**Fail:** Any crash on failure (ungraceful degradation)

---

## 7. Test Reporting Template

**When executing tests, use this report format:**

```markdown
# M2 Acceptance Test Report — Spark Swappability

**Date:** YYYY-MM-DD
**Tester:** Agent D / Agent A
**Environment:** [Hardware spec, OS, Python version]

## Test Results

### TEST-001: Configuration-Driven Selection
- **Status:** ✅ PASS / ❌ FAIL
- **Evidence:** [Screenshot/log showing config override]
- **Notes:** [Any deviations from expected behavior]

### TEST-002: Hot-Swap Determinism
- **Status:** ✅ PASS / ❌ FAIL
- **Evidence:** [BOX output comparison, hash verification]
- **Notes:** [Narration differences observed, expected]

### TEST-003: Capability Mismatch Handling
- **Status:** ✅ PASS / ❌ FAIL
- **Evidence:** [Fallback log, JSON parse success]
- **Notes:** [User notification verified]

### TEST-004: OOM Fallback
- **Status:** ✅ PASS / ❌ FAIL
- **Evidence:** [Fallback log, user warning]
- **Notes:** [System remained functional]

### TEST-005: No Hard-Coded Provider Audit
- **Status:** ✅ PASS / ❌ FAIL
- **Evidence:** [Grep output, 0 violations]
- **Notes:** [Audit commands executed]

### TEST-006: Lens/Box Gating Preserved
- **Status:** ✅ PASS / ❌ FAIL
- **Evidence:** [Provenance tags verified]
- **Notes:** [No mechanical claims from SPARK]

## Summary

**Total Tests:** 6
**Passed:** X / 6
**Failed:** Y / 6

**M2 Status:** ✅ COMPLETE (if all pass) / ❌ INCOMPLETE (if any fail)

**Next Actions:**
- [If failures: remediation steps]
- [If all pass: proceed to M2 certification]
```

---

## 8. Compliance Statement

**This document is BINDING for M2 completion.**

**M2 CANNOT be certified complete until:**
- ✅ All 6 acceptance tests PASS
- ✅ Test evidence documented
- ✅ Agent D reviews and approves test results

**Violations:**
- Any test failure → M2 incomplete (STOP condition)
- Skipping tests → M2 incomplete (no bypass allowed)
- Faking test results → Governance violation (immediate escalation to PM)

---

**END OF M2 ACCEPTANCE CRITERIA**

**Date:** 2026-02-10
**Agent:** Agent D (Research Orchestrator)
**Authority:** PM (Aegis)
**Status:** ✅ **BINDING** (M2 gate)
**Signature:** Agent D (Research Orchestrator) — 2026-02-10

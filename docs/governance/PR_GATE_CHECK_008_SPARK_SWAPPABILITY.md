# PR Gate CHECK-008: Spark Swappability Compliance
## Enforcement Mechanism for SPARK_SWAPPABLE_INVARIANT

**Check ID:** CHECK-008
**Authority:** [docs/doctrine/SPARK_SWAPPABLE_INVARIANT.md](../doctrine/SPARK_SWAPPABLE_INVARIANT.md)
**Severity:** 🔴 **CRITICAL** (M2 gate requirement)
**Status:** ✅ **ACTIVE** (M2+)
**Date:** 2026-02-10

---

## 1. Purpose

**This check enforces Spark swappability as a binding M2 invariant.**

**Gate Condition:** ALL PRs modifying SPARK-related code MUST pass this check before merge.

**Scope:**
- Any changes to `aidm/spark/` (when created in M2)
- Any changes to model loading, provider selection, or LLM invocation
- Any changes that introduce new SPARK dependencies or capabilities

---

## 2. Automated Checks

### 2.1 Audit Script Execution

**Requirement:** Run `scripts/audit_spark_swappability.sh` before PR approval.

**Pass Criteria:**
- ✅ Script exits with code 0 (all checks passed)
- ✅ Zero violations detected

**Fail Criteria:**
- ❌ Script exits with code 1 (violations detected)
- ❌ Any hard-coded model path, provider name, or capability assumption

**Verification Command:**
```bash
cd /path/to/repo
bash scripts/audit_spark_swappability.sh
```

**Expected Output (PASS):**
```
============================================
SPARK SWAPPABILITY AUDIT
Authority: SPARK_SWAPPABLE_INVARIANT.md
Date: 2026-02-10
============================================

[CHECK-001] Scanning for hard-coded model paths...
✅ PASS: No hard-coded model paths

[CHECK-002] Scanning for hard-coded provider names...
✅ PASS: No hard-coded provider names

[CHECK-003] Scanning for hard-coded model names in code...
✅ PASS: No model names in source code

[CHECK-004] Scanning for capability assumptions without checks...
✅ PASS: All capability usage properly validated

[CHECK-005] Scanning for direct SPARK output usage...
✅ PASS: No direct SPARK output bypass

[CHECK-006] Scanning for SPARK mechanical claims...
✅ PASS: No SPARK mechanical claims detected

============================================
AUDIT SUMMARY
============================================
✅ ALL CHECKS PASSED
Spark swappability invariant preserved.
```

---

### 2.2 Specific Violation Patterns

**STOP-001: Hard-Coded Model Selection**

**Pattern:**
```python
# ❌ VIOLATION
model = LlamaCpp(model_path="models/mistral-7b.gguf")
provider = "llamacpp"
```

**Compliant:**
```python
# ✅ COMPLIANT
model_config = load_model_config(model_id=config.default_spark_model)
model = create_spark_adapter(model_config)
```

---

**STOP-002: Capability Assumption Without Validation**

**Pattern:**
```python
# ❌ VIOLATION
response = spark.generate(prompt, json_mode=True)
```

**Compliant:**
```python
# ✅ COMPLIANT
if spark.supports_json_mode():
    response = spark.generate(prompt, json_mode=True)
else:
    prompt_with_json = f"{prompt}\n\nRespond in valid JSON format."
    response = spark.generate(prompt_with_json)
```

---

**STOP-003: SPARK Bypasses Lens/Box Validation**

**Pattern:**
```python
# ❌ VIOLATION
def narrate_event(event):
    return spark.generate(event.prompt)  # Direct output
```

**Compliant:**
```python
# ✅ COMPLIANT
def narrate_event(event):
    spark_output = spark.generate(event.prompt)
    filtered_output = lens.filter(spark_output)  # LENS gating
    return filtered_output
```

---

## 3. Manual Review Checklist

**Reviewer MUST verify:**

### 3.1 Configuration-Driven Selection

- [ ] ✅ SPARK provider loaded from `models.yaml` or equivalent registry
- [ ] ✅ Default model specified in configuration (not source code)
- [ ] ✅ User override mechanism supported (env var, CLI param, or runtime config)
- [ ] ✅ No hard-coded model paths in source files

**Evidence Required:**
- Point to registry loading code (e.g., `load_model_registry("models.yaml")`)
- Confirm override mechanism tested (environment variable or config file)

---

### 3.2 Capability Validation

- [ ] ✅ All `json_mode=True` usage gated by `supports_json_mode()` check
- [ ] ✅ All `streaming=True` usage gated by `supports_streaming()` check
- [ ] ✅ Fallback strategy documented for unsupported capabilities
- [ ] ✅ No assumptions that all SPARKs have identical features

**Evidence Required:**
- Search for `json_mode=` and `streaming=` in diff, verify each has capability check

---

### 3.3 Lens/Box Separation Preserved

- [ ] ✅ All SPARK outputs routed through LENS filtering
- [ ] ✅ No SPARK mechanical claims used by BOX (damage, hit/miss, legality)
- [ ] ✅ BOX never reads SPARK outputs for mechanical decisions
- [ ] ✅ Event log stores SPARK outputs for replay (provenance preserved)

**Evidence Required:**
- Trace SPARK output flow: `spark.generate()` → `lens.filter()` → user
- Confirm BOX computes mechanics independently of SPARK

---

### 3.4 Determinism Preservation

- [ ] ✅ Swapping SPARK does not affect BOX RNG (separate seeds)
- [ ] ✅ BOX computations use deterministic rules engine (no SPARK influence)
- [ ] ✅ Event log replay uses recorded SPARK outputs (no regeneration)
- [ ] ✅ Acceptance TEST-002 will verify hot-swap determinism

**Evidence Required:**
- Confirm BOX uses separate `random.Random(seed)` instance from SPARK
- Confirm event log stores `spark_narration` field for replay

---

## 4. Stop Conditions (PR Rejection Criteria)

**Any of the following constitutes automatic PR REJECTION:**

### STOP-001: Hard-Coded Model Found

**Detection:** Audit script CHECK-001, CHECK-002, or CHECK-003 fails

**Symptom:**
```
❌ FAIL: Hard-coded model paths detected (STOP-001 violation)
aidm/spark/loader.py:42:    model = LlamaCpp(model_path="models/mistral-7b.gguf")
```

**Remediation:** Move model path to `models.yaml`, load via registry

---

### STOP-002: Capability Assumption Without Validation

**Detection:** Audit script CHECK-004 fails

**Symptom:**
```
❌ FAIL: Capability usage without validation (STOP-002 violation)
aidm/narration/generator.py:78:    response = spark.generate(prompt, json_mode=True)
```

**Remediation:** Add capability check:
```python
if spark.supports_json_mode():
    response = spark.generate(prompt, json_mode=True)
else:
    # Fallback strategy
```

---

### STOP-003: SPARK Bypasses Lens/Box

**Detection:** Audit script CHECK-005 or CHECK-006 fails

**Symptom:**
```
❌ FAIL: Direct SPARK output without LENS filtering (STOP-003 violation)
aidm/api/narration.py:102:    return spark.generate(event.prompt)
```

**Remediation:** Route through LENS:
```python
spark_output = spark.generate(event.prompt)
return lens.filter(spark_output)
```

---

### STOP-004: Silent Fallback Without Notification

**Detection:** Manual review (no automated check)

**Symptom:** Code switches SPARK provider without user notification

**Remediation:** Add warning log:
```python
if not spark_available:
    logger.warning(f"SPARK '{requested}' unavailable, falling back to '{fallback}'")
    notify_user(f"Using fallback model: {fallback}")
```

---

### STOP-005: Determinism Violation on Swap

**Detection:** Acceptance TEST-002 (deferred to M2 validation)

**Symptom:** Swapping SPARK changes BOX outcomes (attack result differs)

**Remediation:** Ensure BOX never reads SPARK outputs for mechanical decisions

---

## 5. Integration with M2 Acceptance Tests

**CHECK-008 is a prerequisite for acceptance testing.**

**Relationship:**
- **CHECK-008** = Static code analysis (grep audits, manual review)
- **Acceptance Tests** = Dynamic validation (runtime behavior verification)

**M2 Completion Requires BOTH:**
1. ✅ CHECK-008 passes (no violations in source code)
2. ✅ All 6 acceptance tests pass (runtime swappability verified)

**Acceptance Test Reference:** [docs/governance/M2_ACCEPTANCE_SPARK_SWAPPABILITY.md](M2_ACCEPTANCE_SPARK_SWAPPABILITY.md)

---

## 6. Enforcement Workflow

### 6.1 PR Submission

**Submitter (Agent A or external contributor):**
1. Run `scripts/audit_spark_swappability.sh` locally
2. Fix any violations before submitting PR
3. Include audit script output in PR description

---

### 6.2 PR Review

**Reviewer (PM or designated agent):**
1. Re-run audit script on PR branch
2. Verify output shows `✅ ALL CHECKS PASSED`
3. Perform manual checklist review (section 3)
4. Approve if compliant, reject if violations detected

---

### 6.3 Merge Gate

**Before merge:**
- ✅ Audit script passes
- ✅ Manual checklist complete
- ✅ No STOP conditions triggered
- ✅ Reviewer approval documented

---

## 7. Exemptions and Overrides

**PM (Aegis) may grant exemptions in exceptional cases with:**
- Explicit written justification
- Documented alternative enforcement mechanism
- Time-bounded exception (with remediation plan)

**Example Exemption:**
```
Exemption granted for PR #42 (prototype SPARK adapter)
Rationale: Early M2 development, registry not yet implemented
Alternative: Manual verification that prototype uses config file
Remediation: Full compliance required by M2 validation phase
Authority: PM (Aegis) — 2026-02-12
```

**No exemptions for:**
- STOP-003 violations (SPARK bypassing LENS/BOX is never acceptable)
- STOP-005 violations (determinism is sacred, non-negotiable)

---

## 8. Compliance Statement

**This check is BINDING for M2+.**

**All PRs touching SPARK code MUST:**
- ✅ Pass audit script (exit code 0)
- ✅ Pass manual checklist review
- ✅ Preserve configuration-driven swappability
- ✅ Maintain Lens/Box separation
- ✅ Document any fallback strategies

**Violations:**
- Any STOP condition triggered → PR REJECTED (no merge until fixed)
- Repeated violations → Escalation to PM for governance review

---

**END OF PR GATE CHECK-008 SPECIFICATION**

**Date:** 2026-02-10
**Agent:** Agent D (Research Orchestrator)
**Authority:** PM (Aegis)
**Status:** ✅ **ACTIVE** (M2 gate requirement)
**Signature:** Agent D (Research Orchestrator) — 2026-02-10

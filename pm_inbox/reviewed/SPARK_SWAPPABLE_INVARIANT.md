# Spark Swappable Invariant
## Binding Architectural Constraint for M2+

**Document Type:** Doctrine / Core Invariant
**Status:** ✅ **BINDING** (M2+)
**Date:** 2026-02-11 (R1 updated)
**Authority:** PM (Aegis)
**Supersedes:** None (new invariant)

---

## 1. Invariant Statement

**SPARK MUST BE USER-SWAPPABLE VIA CONFIGURATION, NOT HARD-CODED.**

**Definition:**
- **SPARK** = The LLM provider component (generative intelligence core)
- **Swappable** = User-selectable at runtime via configuration/registry, not compiled/hard-coded into application
- **Configuration** = External registry (models.yaml, config file, or runtime parameter), NOT source code constants

**Scope:** All AIDM components that invoke LLM inference (narration generation, memory queries, paraphrasing, fact extraction)

---

## 2. Purpose & Rationale

### 2.1 Why Spark Must Be Swappable

**User Needs:**
1. **Hardware Heterogeneity:** Users have vastly different hardware (8 GB RAM minimum → 32+ GB high-end)
2. **Performance vs Quality Tradeoff:** Users choose speed (small model) vs quality (large model) based on preference
3. **Future Model Upgrades:** New LLMs released frequently → users want access without code changes
4. **Experimentation:** Power users want to test different models for specific use cases

**Technical Needs:**
1. **Graceful Degradation:** System must function on minimum spec (Qwen3 4B) AND high-end spec (Qwen3 8B+)
2. **Provider Diversity:** Local models (llama.cpp, Transformers) vs cloud APIs (OpenAI, Anthropic) vs hybrid
3. **Quantization Flexibility:** 4-bit vs 8-bit vs FP16 based on available VRAM
4. **Context Window Variation:** 2K → 32K context requires different batching strategies

**Architectural Principle:**
- **SPARK** is the ONLY swappable component (LENS and BOX are deterministic, not model-dependent)
- Swapping SPARK MUST NOT break determinism of BOX (mechanics remain identical)
- Swapping SPARK MAY change narration quality but MUST NOT change game state

---

### 2.2 "Spark Cannot Be Trusted" — Lens/Box Gating Required

**Core Principle:** Regardless of which SPARK is active, LENS and BOX MUST gate all outputs.

**Why:**
- Different LLMs have different hallucination rates, adherence to instructions, JSON reliability
- A high-quality SPARK (GPT-4) may be more trustworthy than a low-quality SPARK (GPT-2), but NEITHER is authoritative
- All SPARK outputs MUST pass through validation (LENS filtering, BOX verification) before affecting game state

**Enforcement:**
- **BOX** remains sole mechanical authority (attack rolls, damage, legality) — SPARK cannot override
- **LENS** remains sole presentation authority (tone, filtering, provenance labels) — SPARK generates, LENS gates
- **Swapping SPARK** changes generation quality, NOT enforcement rules

**Example:**
- **SPARK = Qwen3 4B:** Generates "You hit the orc for 10 damage" (hallucinated damage value)
- **BOX:** Ignores SPARK damage claim, computes actual damage (1d8+3 = 7), outputs `[BOX] 7 damage`
- **SPARK = Qwen3 8B:** Generates "Your blade strikes true" (no hallucinated damage)
- **BOX:** Computes same damage (1d8+3 = 7), outputs `[BOX] 7 damage`
- **Result:** Different narration quality, SAME mechanical outcome (determinism preserved)

---

## 3. Non-Negotiable Requirements

### 3.1 Configuration-Driven Selection

**MUST:**
- ✅ SPARK provider MUST be selectable via external configuration (models.yaml, config.json, or CLI parameter)
- ✅ Default SPARK MUST be specified in configuration (e.g., `default_model: qwen3-8b-instruct-4bit`)
- ✅ Users MUST be able to override SPARK without modifying source code
- ✅ SPARK selection MUST be validated at startup (fail-fast if model unavailable)

**MUST NOT:**
- ❌ SPARK provider MUST NOT be hard-coded in source (e.g., `model = "qwen3-8b"` in Python)
- ❌ SPARK selection MUST NOT require recompilation or code changes
- ❌ SPARK fallback MUST NOT silently use different model without user notification

**Example (Compliant Configuration):**
```yaml
# models.yaml
spark:
  default: "qwen3-8b-instruct-4bit"
  available:
    - id: "qwen3-8b-instruct-4bit"
      path: "models/qwen3-8b-instruct.Q4_K_M.gguf"
      context_window: 8192
      quantization: "4-bit"
    - id: "qwen3-4b-instruct-4bit"
      path: "models/qwen3-4b-instruct.Q4_K_M.gguf"
      context_window: 8192
      quantization: "4-bit"
```

**Example (Non-Compliant Hard-Coding):**
```python
# ❌ VIOLATION: Hard-coded model selection
def load_llm():
    return LlamaCpp(model_path="models/qwen3-8b.gguf")  # STOP CONDITION
```

---

### 3.2 Capability Manifest

**MUST:**
- ✅ Each SPARK provider MUST declare capabilities (context window, JSON mode, streaming, tool calling)
- ✅ AIDM MUST validate capability requirements before invoking SPARK (fail-fast if incompatible)
- ✅ SPARK adapters MUST normalize differences (e.g., convert LlamaCpp format → Transformers format)

**MUST NOT:**
- ❌ AIDM MUST NOT assume all SPARKs have identical capabilities (e.g., assume JSON mode available)
- ❌ AIDM MUST NOT silently degrade if capability missing (MUST warn user or fail-fast)

**Example (Capability Manifest):**
```yaml
spark:
  - id: "qwen3-8b-instruct-4bit"
    capabilities:
      context_window: 8192
      json_mode: false  # Qwen3 via llama.cpp lacks native JSON mode
      streaming: true
      tool_calling: false
    constraints:
      max_batch_size: 1  # No batch inference
      requires_stop_tokens: true
```

**Usage:**
```python
# ✅ COMPLIANT: Check capability before use
if not spark.supports_json_mode():
    use_guided_generation_fallback()  # Graceful degradation
```

---

### 3.3 Determinism Preservation

**MUST:**
- ✅ Swapping SPARK MUST NOT change BOX determinism (same event log → same mechanical outcomes)
- ✅ SPARK outputs MUST be recorded in event log (for replay, auditing)
- ✅ Event log replay MUST use RECORDED SPARK outputs, not regenerate (deterministic replay)

**MUST NOT:**
- ❌ Swapping SPARK MUST NOT alter BOX computations (attack rolls, damage, saves remain identical)
- ❌ SPARK randomness MUST NOT affect BOX randomness (separate RNG seeds)

**Determinism Model:**
- **BOX Determinism:** Same event sequence → same game state (REQUIRED, never violated)
- **SPARK Determinism:** Same event sequence → different narrations (ACCEPTABLE, expected with model swap)
- **Replay Determinism:** Replay uses logged SPARK outputs → narration identical (REQUIRED for audit)

**Example:**
```
Event Log (Session 5, Turn 3):
  event_001: {type: "attack_roll", result: "hit", damage: 12, spark_narration: "Your blade strikes the orc's armor."}

Replay (same SPARK):
  BOX recomputes: attack_roll → hit, damage 12 ✅ IDENTICAL
  SPARK output: (uses logged narration, no regeneration) ✅ IDENTICAL

Replay (different SPARK):
  BOX recomputes: attack_roll → hit, damage 12 ✅ IDENTICAL (determinism preserved)
  SPARK output: (uses logged narration from original SPARK) ✅ IDENTICAL (replay fidelity)
```

**Key Insight:** Event log stores SPARK outputs as part of event history → replay uses logged outputs, not regenerated.

---

## 4. Spark / Lens / Box Separation (Compatibility)

**This invariant MUST remain compatible with existing Spark/Lens/Box doctrine.**

### 4.1 Spark Layer (Swappable)

**Unchanged Responsibilities:**
- Generate narrative text (raw LLM output)
- Paraphrase player intent
- Query memory for fact retrieval
- Synthesize responses

**New Requirement:**
- **SPARK provider MUST be swappable** (user-selectable via config)
- **SPARK adapter MUST normalize provider differences** (prompt format, tokenization, stop tokens)

**No Change to Doctrine:**
- SPARK remains non-authoritative (no mechanical claims)
- SPARK never refuses (refusal is LENS/BOX responsibility)
- SPARK outputs require LENS/BOX validation

---

### 4.2 Lens Layer (Fixed)

**Unchanged:**
- LENS is NOT swappable (single implementation, deterministic logic)
- LENS gates SPARK output (tone adaptation, filtering, provenance labeling)
- LENS cannot invent authority

**Compatibility:**
- Swapping SPARK changes input to LENS (different narration text), but LENS logic remains identical
- LENS applies same filtering rules regardless of SPARK provider

---

### 4.3 Box Layer (Fixed)

**Unchanged:**
- BOX is NOT swappable (deterministic RAW rules engine)
- BOX is sole mechanical authority
- BOX never delegates to SPARK

**Compatibility:**
- Swapping SPARK has ZERO effect on BOX (mechanics remain identical)
- BOX may request SPARK narration but always ignores SPARK mechanical claims

---

## 5. Stop Conditions (Enforceable Violations)

**Any of the following constitutes a BINDING VIOLATION:**

### STOP-001: Hard-Coded Model Selection

**Violation:** Source code contains hard-coded model path or provider selection.

**Detection:**
```bash
# Search for hard-coded model paths
grep -r "model_path.*=.*\".*\.gguf\"" aidm/ --include="*.py"
# Should return 0 results (all paths must come from config)

# Search for hard-coded provider names
grep -r "provider.*=.*\"llamacpp\"" aidm/ --include="*.py"
# Should return 0 results (provider must come from config)
```

**Enforcement:** PR gate CHECK-008 (added to M2_PR_GATE_CHECKLIST.md)

**Remediation:** Move model selection to configuration file, load via registry.

---

### STOP-002: Capability Assumption Without Validation

**Violation:** Code assumes SPARK capability (JSON mode, streaming, tool calling) without checking manifest.

**Detection:**
```bash
# Search for JSON mode usage without capability check
grep -r "json_mode=True" aidm/ --include="*.py" | grep -v "if.*supports.*json"
# Should return 0 results (all JSON mode usage must check capability)
```

**Enforcement:** Code review + runtime assertion (capability validation required at SPARK invocation)

**Remediation:** Add capability check before invoking SPARK feature:
```python
if spark.supports_json_mode():
    response = spark.generate(prompt, json_mode=True)
else:
    response = spark.generate(prompt_with_json_instructions)  # Fallback
```

---

### STOP-003: SPARK Bypasses Lens/Box Validation

**Violation:** SPARK output used directly without LENS filtering or BOX verification.

**Detection:**
```bash
# Search for direct SPARK output to user
grep -r "return spark\.generate" aidm/ --include="*.py"
# Should return 0 results (all SPARK output must pass through LENS)

# Search for SPARK mechanical claims used without BOX
grep -r "spark.*damage\|spark.*hit\|spark.*legal" aidm/ --include="*.py"
# Should return 0 results (BOX computes mechanics, not SPARK)
```

**Enforcement:** Architectural review (CHECK-007 Spark/Lens/Box separation)

**Remediation:** Route all SPARK output through LENS → user, route all mechanics through BOX.

---

### STOP-004: Silent SPARK Fallback Without Notification

**Violation:** System silently switches SPARK provider without user notification (e.g., OOM fallback without warning).

**Detection:** Runtime monitoring (capability mismatch or OOM triggers fallback without user alert)

**Enforcement:** Acceptance test (M2_ACCEPTANCE_SPARK_SWAPPABILITY.md TEST-005)

**Remediation:** Log warning + notify user when fallback occurs:
```python
if not spark_available:
    logger.warning(f"SPARK '{requested_model}' unavailable, falling back to '{fallback_model}'")
    notify_user(f"Using fallback model: {fallback_model}")
```

---

### STOP-005: Determinism Violation on SPARK Swap

**Violation:** Swapping SPARK changes BOX outcomes (same event log → different mechanical results).

**Detection:** Determinism test (replay session with different SPARK, verify BOX state identical)

**Enforcement:** Acceptance test (M2_ACCEPTANCE_SPARK_SWAPPABILITY.md TEST-002)

**Remediation:** Ensure BOX never reads SPARK outputs for mechanical decisions, only for narration.

---

## 6. Governance Integration

### 6.1 M2 PR Gate Checklist

**New Check:** CHECK-008 (Spark Swappability)

**Question:** Does this PR preserve Spark swappability?

**Pass Criteria:**
- ✅ No hard-coded model paths or provider names
- ✅ All SPARK invocations use configuration-loaded provider
- ✅ All capability-dependent code checks manifest before use
- ✅ No SPARK output bypasses LENS/BOX validation

**Fail Criteria:**
- ❌ Hard-coded model selection detected (grep finds violations)
- ❌ Capability assumption without validation
- ❌ SPARK output used directly without LENS/BOX

**Verification Command:**
```bash
# Check for hard-coded models
grep -r "model_path.*=.*\"" aidm/ --include="*.py"
# Should return 0 results

# Check for capability assumptions
grep -r "json_mode=True\|streaming=True" aidm/ --include="*.py" | grep -v "if.*supports"
# Should return 0 results (all usage gated by capability check)
```

---

### 6.2 M2 Monitoring Protocol

**New Invariant:** INV-SWAP-001 (Spark Swappability Preserved)

**Requirement:** All SPARK invocations MUST be registry-driven, not hard-coded.

**Verification Method:**
```bash
# Audit codebase for hard-coded model references
grep -r "qwen\|gemma\|llama" aidm/ --include="*.py" | grep -v "# comment\|\"\"\".*\"\"\""
# Should return 0 results (model names only in config, not code)
```

**Evidence Requirement:**
- 100 consecutive SPARK invocations use registry-loaded provider (no hard-coded paths)
- Zero capability mismatches (all features validated before use)

**Severity:** 🔴 **CRITICAL** — Hard-coding SPARK violates M2 architectural principle

---

## 7. Acceptance Criteria Reference

**Full acceptance tests documented in:** `docs/governance/M2_ACCEPTANCE_SPARK_SWAPPABILITY.md`

**Summary:**
- TEST-001: Configuration-driven selection (user overrides default via config)
- TEST-002: Hot-swap determinism (same scenario, different SPARK, BOX unchanged)
- TEST-003: Capability mismatch handling (graceful degradation or fail-fast)
- TEST-004: OOM fallback (graceful fallback with user notification)
- TEST-005: No hard-coded provider audit (grep verification)
- TEST-006: Lens/Box gating preserved (all SPARK output validated)

---

## 8. Implementation Guidance (Specification Only)

**Note:** This section describes WHAT must be implemented, not HOW (code implementation deferred to M2 execution).

### 8.1 Model Registry

**Specification:**
- External configuration file (models.yaml or config.json)
- Schema: model ID, path, quantization, context window, capabilities
- Validation: check file exists, model loadable at startup
- Default model specified, user override supported

**Example Structure:**
```yaml
spark:
  default: "qwen3-8b-instruct-4bit"
  models:
    - id: "qwen3-8b-instruct-4bit"
      path: "models/qwen3-8b-instruct.Q4_K_M.gguf"
      backend: "llamacpp"
      context_window: 8192
      capabilities: {json_mode: false, streaming: true}
    - id: "qwen3-4b-instruct-4bit"
      path: "models/qwen3-4b-instruct.Q4_K_M.gguf"
      backend: "llamacpp"
      context_window: 8192
      capabilities: {json_mode: false, streaming: true}
```

---

### 8.2 SPARK Adapter Interface

**Specification:**
- Abstract interface: `generate(prompt, temperature, max_tokens, **kwargs) -> str`
- Capability query: `supports_json_mode() -> bool`, `supports_streaming() -> bool`
- Normalization: Convert provider-specific formats to canonical AIDM format

**Adapters Required:**
- LlamaCppAdapter (llama.cpp backend, .gguf models)
- TransformersAdapter (HuggingFace Transformers, PyTorch models)
- (Future) OpenAIAdapter, AnthropicAdapter (cloud APIs)

---

### 8.3 Capability-Driven Invocation

**Specification:**
- Before invoking SPARK feature, check capability manifest
- If capability unsupported, use fallback strategy (e.g., guided generation for JSON)
- If fallback unavailable, fail-fast with clear error message

**Example Flow:**
```
1. User requests narration generation
2. AIDM checks: spark.supports_json_mode()?
3. If YES: invoke with json_mode=True (structured output)
4. If NO: invoke with JSON instructions in prompt (guided generation)
5. LENS validates JSON parse (fail gracefully if malformed)
```

---

## 9. Migration Path (M1 → M2)

**M1 Status:** SPARK provider likely hard-coded (template-based narration, no LLM integration yet)

**M2 Transition:**
1. **Create models.yaml** with default SPARK (Qwen3 8B 4-bit)
2. **Implement SPARK registry** (load models from config, validate at startup)
3. **Refactor SPARK invocations** (replace hard-coded paths with registry lookups)
4. **Add capability checks** (validate JSON mode, streaming before use)
5. **Test hot-swap** (verify swapping SPARK doesn't break BOX determinism)

**Backward Compatibility:**
- M1 template-based narration remains functional (no SPARK required for templates)
- M2 adds LLM-based narration as optional upgrade (SPARK registry required)

---

## 10. Compliance Statement

**This invariant is BINDING for M2+.**

**All agents must:**
- ✅ Design SPARK components as swappable (configuration-driven, not hard-coded)
- ✅ Validate capability requirements before invoking SPARK features
- ✅ Preserve Lens/Box separation (SPARK swappability doesn't weaken validation)
- ✅ Maintain determinism (swapping SPARK doesn't change BOX outcomes)

**PM (Aegis) may:**
- Override STOP conditions with explicit justification (rare exception)
- Update this invariant for M3+ with revision record

**Violations:**
- Any hard-coded SPARK provider → PR REJECTED (CHECK-008 failure)
- Any capability assumption without validation → PR REJECTED (architectural review)
- Any SPARK bypass of LENS/BOX → PR REJECTED (CHECK-007 failure)

---

**END OF SPARK SWAPPABLE INVARIANT**

**Date:** 2026-02-10
**Agent:** Agent D (Research Orchestrator)
**Authority:** PM (Aegis)
**Status:** ✅ **BINDING** (M2+)
**Signature:** Agent D (Research Orchestrator) — 2026-02-10

---

> **R1 Update (2026-02-11):** Model references updated to reflect R1 Technology Stack Validation selections. See `pm_inbox/OPUS_R1_TECHNOLOGY_STACK_VALIDATION.md`.

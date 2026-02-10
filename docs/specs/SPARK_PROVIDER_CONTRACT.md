# Spark Provider Contract
## Specification for Swappable LLM Integration

**Document Type:** Specification (Interface Contract)
**Status:** ✅ **BINDING** (M2+)
**Date:** 2026-02-10
**Authority:** PM (Aegis)
**Scope:** All SPARK provider implementations

---

## 1. Purpose

**This document defines the interface contract for SPARK providers.**

**Goal:** Enable user-swappable LLM backends without code changes by establishing:
1. Canonical request/response schema (what AIDM sends/receives)
2. Capability manifest (what features each provider supports)
3. Model registry requirements (how providers are discovered and configured)
4. Adapter responsibility boundaries (what adapters normalize vs what AIDM handles)

**Non-Goal:** Implementation details (HOW adapters work internally) — deferred to M2 execution.

---

## 2. Canonical Request/Response Schema

### 2.1 SparkRequest (AIDM → SPARK)

**Canonical Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt` | string | REQUIRED | The text prompt sent to SPARK (pre-formatted by adapter) |
| `temperature` | float | REQUIRED | Sampling temperature (0.0-2.0, typically 0.7-1.0 for narration) |
| `max_tokens` | int | REQUIRED | Maximum response length in tokens |
| `stop_sequences` | list[string] | OPTIONAL | Token sequences that halt generation (e.g., `["</s>", "\n\n"]`) |
| `context_window` | int | OPTIONAL | Override default context window (for truncation logic) |
| `streaming` | bool | OPTIONAL | Enable streaming response (default: False) |
| `json_mode` | bool | OPTIONAL | Request structured JSON output (requires capability check) |
| `seed` | int | OPTIONAL | RNG seed for reproducibility (if provider supports) |
| `metadata` | dict | OPTIONAL | Provider-specific parameters (passed through adapter) |

**Schema Invariants:**
- `prompt` MUST be non-empty string
- `temperature` MUST be in range [0.0, 2.0]
- `max_tokens` MUST be positive integer ≤ context_window
- If `json_mode=True`, provider MUST support JSON capability (else error)

**Example:**
```python
request = SparkRequest(
    prompt="Generate narration for attack hit event: target=orc, damage=12",
    temperature=0.8,
    max_tokens=100,
    stop_sequences=["</narration>"],
    json_mode=False
)
```

---

### 2.2 SparkResponse (SPARK → AIDM)

**Canonical Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | REQUIRED | Generated text output |
| `finish_reason` | enum | REQUIRED | Why generation stopped: `completed`, `length_limit`, `stop_sequence`, `error` |
| `tokens_used` | int | REQUIRED | Total tokens consumed (prompt + response) |
| `provider_metadata` | dict | OPTIONAL | Provider-specific info (model version, latency, etc.) |
| `error` | string | OPTIONAL | Error message if generation failed |

**Schema Invariants:**
- `text` MUST be string (may be empty if error occurred)
- `finish_reason` MUST be one of: `completed`, `length_limit`, `stop_sequence`, `error`
- If `finish_reason == "error"`, `error` field MUST be populated
- `tokens_used` MUST be non-negative integer

**Example:**
```python
response = SparkResponse(
    text="Your blade strikes the orc's shoulder, dealing 12 points of damage.",
    finish_reason="completed",
    tokens_used=45,
    provider_metadata={"model": "mistral-7b-v0.2", "latency_ms": 1200}
)
```

---

## 3. Capability Manifest

### 3.1 Required Capabilities (All Providers)

**Every SPARK provider MUST declare:**

| Capability | Type | Description |
|------------|------|-------------|
| `provider_id` | string | Unique provider identifier (e.g., "llamacpp", "transformers") |
| `model_id` | string | Specific model identifier (e.g., "mistral-7b-4bit") |
| `context_window` | int | Maximum context window in tokens (e.g., 8192) |
| `max_tokens` | int | Maximum generation length per request |
| `quantization` | string | Model quantization (e.g., "4-bit", "8-bit", "fp16", "none") |

---

### 3.2 Optional Capabilities (Feature Flags)

**Providers SHOULD declare support for:**

| Capability | Type | Default | Description |
|------------|------|---------|-------------|
| `supports_streaming` | bool | False | Incremental token-by-token streaming |
| `supports_json_mode` | bool | False | Native JSON structured output (not prompt-based) |
| `supports_tool_calling` | bool | False | Function calling / tool use (future M3+) |
| `supports_seeded_generation` | bool | False | Reproducible generation via RNG seed |
| `supports_batch_inference` | bool | False | Multiple prompts in single call |
| `supports_stop_sequences` | bool | True | Custom stop tokens |

**Capability Check Example:**
```python
# ✅ COMPLIANT: Check capability before use
if spark.supports_json_mode():
    response = spark.generate(request, json_mode=True)
else:
    # Fallback: Use guided generation (JSON in prompt)
    request.prompt += "\n\nRespond in valid JSON format."
    response = spark.generate(request)
    parsed = parse_json_from_text(response.text)  # LENS validates
```

---

### 3.3 Capability Manifest Schema

**Each provider MUST provide a manifest (YAML or JSON):**

```yaml
provider:
  id: "llamacpp"
  name: "llama.cpp Backend"
  backend: "llama-cpp-python"
  version: "0.2.77"

model:
  id: "mistral-7b-4bit"
  name: "Mistral 7B Instruct v0.2 (4-bit)"
  path: "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
  context_window: 8192
  max_tokens: 2048
  quantization: "4-bit"

capabilities:
  supports_streaming: true
  supports_json_mode: false  # llama.cpp lacks native JSON mode
  supports_tool_calling: false
  supports_seeded_generation: true
  supports_batch_inference: false
  supports_stop_sequences: true

constraints:
  min_ram_gb: 4.0  # Minimum RAM required to load model
  min_vram_gb: 0.0  # Can run CPU-only
  avg_tokens_per_sec: 20  # Expected throughput (median spec)
```

---

## 4. Model Registry Requirements

### 4.1 Registry Schema (models.yaml)

**AIDM MUST load SPARK providers from external configuration file.**

**Required Structure:**
```yaml
spark:
  # Default model (used if user doesn't override)
  default: "mistral-7b-4bit"

  # Available models (user-selectable)
  models:
    - id: "mistral-7b-4bit"
      name: "Mistral 7B (4-bit, fast)"
      provider: "llamacpp"
      path: "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
      context_window: 8192
      capabilities:
        streaming: true
        json_mode: false
      presets:
        narration:
          temperature: 0.8
          max_tokens: 150
        query:
          temperature: 0.3
          max_tokens: 50

    - id: "phi-2-4bit"
      name: "Phi-2 (4-bit, minimum spec)"
      provider: "llamacpp"
      path: "models/phi-2.Q4_K_M.gguf"
      context_window: 2048
      capabilities:
        streaming: true
        json_mode: false
      presets:
        narration:
          temperature: 0.9
          max_tokens: 100
```

---

### 4.2 Registry Validation (Startup)

**AIDM MUST validate registry at startup:**

**Validation Rules:**
1. ✅ Default model MUST exist in `models` list
2. ✅ All model paths MUST be valid files (fail-fast if missing)
3. ✅ All models MUST declare `provider`, `path`, `context_window`
4. ✅ Provider backend MUST be available (e.g., llama-cpp-python installed)
5. ⚠️ WARN if model file >10 GB (user confirmation recommended)

**Validation Errors:**
```python
# Example validation failures
RegistryError: Default model 'mistral-7b-4bit' not found in models list
RegistryError: Model file not found: models/missing.gguf
RegistryError: Provider 'transformers' not installed (pip install transformers)
RegistryWarning: Model 'llama-70b' is 40 GB (confirm before loading)
```

---

### 4.3 User Override Mechanism

**Users MUST be able to override default model via:**

**Option 1: Environment Variable**
```bash
export AIDM_SPARK_MODEL="phi-2-4bit"
./aidm-cli
```

**Option 2: CLI Parameter**
```bash
./aidm-cli --spark-model phi-2-4bit
```

**Option 3: Runtime Config**
```python
# In-game command (if supported)
/settings spark-model phi-2-4bit
```

**Override Validation:**
- If overridden model not in registry → ERROR (fail-fast)
- If overridden model incompatible with current scenario → WARN (e.g., context window too small)

---

## 5. Adapter Responsibility Boundaries

### 5.1 Adapter Responsibilities (Provider-Specific)

**Adapters MUST handle:**

| Responsibility | Description | Example |
|----------------|-------------|---------|
| **Prompt Formatting** | Convert canonical prompt → provider-specific format | Add chat template tags: `<|im_start|>user\n{prompt}<|im_end|>` |
| **Tokenization** | Tokenize prompt, count tokens, enforce context window | llama.cpp: `tokenize(prompt)`, Transformers: `tokenizer.encode(prompt)` |
| **Stop Token Handling** | Convert canonical stop sequences → provider format | LlamaCpp: `stop=["</s>"]`, Transformers: `stopping_criteria=...` |
| **Temperature Normalization** | Map AIDM temperature → provider range | Some providers use [0, 1], others [0, 2] |
| **Response Extraction** | Extract text from provider-specific response format | LlamaCpp: `response['choices'][0]['text']` |
| **Error Handling** | Catch provider exceptions, convert to SparkResponse error | OOM → `SparkResponse(error="Out of memory", finish_reason="error")` |

---

### 5.2 AIDM Responsibilities (Provider-Agnostic)

**AIDM MUST handle:**

| Responsibility | Description |
|----------------|-------------|
| **Capability Validation** | Check manifest before invoking optional features (json_mode, streaming) |
| **Lens/Box Integration** | Route SPARK output through LENS filtering, BOX validation |
| **Provenance Labeling** | Tag SPARK output as `[NARRATIVE]` or `[UNCERTAIN]` |
| **Fallback Logic** | Handle capability mismatch (e.g., no JSON mode → guided generation) |
| **Logging & Metrics** | Track SPARK latency, token usage, error rates |

---

### 5.3 Division of Labor Example

**Scenario:** Generate narration with JSON output

**Adapter (LlamaCppAdapter):**
1. Format prompt with Mistral chat template
2. Tokenize prompt, check fits in context window
3. Call llama.cpp inference: `llama_generate(...)`
4. Extract text from response
5. Return SparkResponse

**AIDM:**
1. Check `spark.supports_json_mode()` → False (Mistral lacks native JSON)
2. Fallback: Add JSON instructions to prompt
3. Invoke adapter: `response = spark.generate(request)`
4. Parse JSON from text (LENS validates structure)
5. If parse fails → retry with corrective prompt OR use template fallback

---

## 6. Fallback Rules

### 6.1 Capability Mismatch Fallback

**Rule:** If requested capability unsupported, use graceful degradation.

| Requested Feature | Fallback Strategy |
|-------------------|-------------------|
| **JSON Mode** | Add JSON instructions to prompt, parse from text |
| **Streaming** | Use batch generation, simulate streaming via chunking |
| **Tool Calling** | Defer to M3+ (not required for M2) |
| **Seeded Generation** | Proceed without seed (non-deterministic SPARK acceptable) |

**Example:**
```python
# User requests JSON output
if spark.supports_json_mode():
    response = spark.generate(request, json_mode=True)
else:
    # Fallback: Guided generation
    request.prompt += "\n\nFormat your response as valid JSON."
    response = spark.generate(request)
    try:
        data = json.loads(response.text)
    except JSONDecodeError:
        # Fallback to template (no SPARK)
        data = template_based_narration(event)
```

---

### 6.2 OOM (Out of Memory) Fallback

**Rule:** If SPARK fails due to insufficient RAM/VRAM, fall back to smaller model with user notification.

**Fallback Sequence:**
1. Attempt primary model (e.g., Mistral 7B)
2. If OOM detected → unload model, try fallback (e.g., Phi-2)
3. If fallback succeeds → WARN user: "Using smaller model due to memory constraints"
4. If fallback fails → ERROR: "Insufficient memory for any SPARK model, reverting to template-based narration"

**User Notification:**
```
⚠️ WARNING: Insufficient memory to load Mistral 7B (requires 6 GB RAM).
Falling back to Phi-2 (requires 3 GB RAM).
Narration quality may be reduced. Consider closing background applications.
```

**Fallback Config:**
```yaml
spark:
  default: "mistral-7b-4bit"
  fallback_chain:
    - "phi-2-4bit"  # First fallback (smaller model)
    - "template"     # Final fallback (no SPARK, templates only)
```

---

### 6.3 Context Window Overflow Fallback

**Rule:** If prompt exceeds context window, truncate or summarize.

**Strategies:**
1. **Truncate Oldest:** Drop oldest messages from conversation history
2. **Summarize:** Use separate SPARK call to summarize history (if context allows)
3. **Switch Model:** Offer to switch to larger context window model (user approval required)

**Example:**
```python
if len(tokens) > spark.context_window:
    # Strategy 1: Truncate
    truncated_prompt = truncate_to_fit(prompt, spark.context_window)
    logger.warning(f"Prompt truncated ({len(tokens)} → {len(truncated_tokens)} tokens)")

    # Strategy 2: Offer model switch
    if user_approves_model_switch():
        switch_to_model("mistral-7b-32k")  # Larger context window
```

---

## 7. Adapter Interface (Specification)

### 7.1 SparkAdapter (Abstract Interface)

**All providers MUST implement this interface:**

```python
class SparkAdapter(ABC):
    """Abstract interface for SPARK providers."""

    @abstractmethod
    def generate(self, request: SparkRequest) -> SparkResponse:
        """Generate text from prompt.

        Args:
            request: Canonical SPARK request

        Returns:
            Canonical SPARK response

        Raises:
            SparkError: If generation fails
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> CapabilityManifest:
        """Return capability manifest for this provider."""
        pass

    @abstractmethod
    def supports_json_mode(self) -> bool:
        """Check if provider supports native JSON output."""
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Check if provider supports streaming."""
        pass

    @abstractmethod
    def get_context_window(self) -> int:
        """Return maximum context window in tokens."""
        pass

    @abstractmethod
    def tokenize(self, text: str) -> list[int]:
        """Tokenize text using provider's tokenizer."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass

    @abstractmethod
    def load_model(self, model_path: str) -> None:
        """Load model from path (called at startup)."""
        pass

    @abstractmethod
    def unload_model(self) -> None:
        """Unload model from memory (for OOM recovery)."""
        pass
```

---

### 7.2 Concrete Adapter Examples (Specification Only)

**LlamaCppAdapter:**
- Backend: llama-cpp-python
- Models: .gguf quantized models (Mistral, LLaMA, Phi-2)
- Capabilities: Streaming ✅, JSON mode ❌, Seeded generation ✅

**TransformersAdapter:**
- Backend: HuggingFace Transformers + PyTorch
- Models: Safetensors, PyTorch checkpoints
- Capabilities: Streaming ✅, JSON mode ❌, Seeded generation ✅

**OpenAIAdapter (Future M3):**
- Backend: OpenAI API
- Models: gpt-4, gpt-3.5-turbo
- Capabilities: Streaming ✅, JSON mode ✅, Tool calling ✅

---

## 8. Normalization Requirements

### 8.1 Prompt Formatting

**Adapters MUST normalize prompts to provider format:**

**Example (Mistral Chat Template):**
```
Input (canonical): "Generate narration for attack hit: damage=12"

Output (Mistral format):
<s>[INST] Generate narration for attack hit: damage=12 [/INST]
```

**Example (ChatML format):**
```
<|im_start|>system
You are a Dungeon Master narrating a D&D game.
<|im_end|>
<|im_start|>user
Generate narration for attack hit: damage=12
<|im_end|>
<|im_start|>assistant
```

**Adapter Responsibility:** Convert canonical prompt → provider-specific template

---

### 8.2 Temperature Scaling

**Some providers use different temperature ranges:**

| Provider | Temperature Range | Normalization |
|----------|-------------------|---------------|
| llama.cpp | [0.0, 2.0] | No normalization (1:1 mapping) |
| Transformers | [0.0, 1.0] | Scale: `provider_temp = aidm_temp / 2.0` |
| OpenAI | [0.0, 2.0] | No normalization (1:1 mapping) |

**Adapter Responsibility:** Map AIDM temperature → provider range

---

### 8.3 Stop Sequence Handling

**Different providers use different stop token formats:**

| Provider | Stop Format | Example |
|----------|-------------|---------|
| llama.cpp | List of strings | `stop=["</s>", "\n\n"]` |
| Transformers | StoppingCriteria object | `stopping_criteria=CustomStoppingCriteria(["</s>"])` |
| OpenAI | List of strings | `stop=["</s>", "\n\n"]` |

**Adapter Responsibility:** Convert canonical stop sequences → provider format

---

## 9. Contract Enforcement

### 9.1 Runtime Validation

**AIDM MUST validate adapter contracts at runtime:**

**Startup Validation:**
- Adapter implements all required methods (generate, get_capabilities, etc.)
- Model file exists and is loadable
- Capability manifest is valid (all required fields present)

**Invocation Validation:**
- Request schema is valid (all required fields present)
- Requested capabilities are supported (json_mode, streaming, etc.)
- Response schema is valid (finish_reason is valid enum, etc.)

---

### 9.2 Contract Violation Handling

**Violation Types:**

| Violation | Severity | Action |
|-----------|----------|--------|
| Missing required method | 🔴 CRITICAL | Fail-fast at startup (adapter unusable) |
| Invalid capability manifest | 🔴 CRITICAL | Fail-fast at startup (adapter unusable) |
| Capability mismatch | 🟡 HIGH | Fall back to alternative strategy (warn user) |
| Malformed response | 🟡 HIGH | Retry with corrective prompt OR template fallback |

**Example:**
```python
# Validation at startup
try:
    adapter.get_capabilities()  # Must return valid manifest
except NotImplementedError:
    raise AdapterError("Adapter missing get_capabilities() method")
```

---

## 10. Specification Status

**This document is SPECIFICATION ONLY (not implementation).**

**Implementation deferred to M2 execution phase.**

**What this spec defines:**
- ✅ Request/response schema (field names, types, invariants)
- ✅ Capability manifest structure (what providers declare)
- ✅ Model registry format (models.yaml structure)
- ✅ Adapter interface (required methods, signatures)
- ✅ Normalization rules (prompt formatting, temperature scaling, stop sequences)

**What this spec does NOT define:**
- ❌ Implementation code (Python classes, functions)
- ❌ Specific adapter implementations (LlamaCppAdapter internals)
- ❌ Model selection algorithm (how AIDM chooses default)
- ❌ UI for model selection (settings screen, CLI commands)

---

## 11. Compliance Statement

**All SPARK providers MUST conform to this contract.**

**Required for M2:**
- ✅ LlamaCppAdapter (primary backend for .gguf models)
- ✅ Model registry (models.yaml with ≥2 models: Mistral 7B + Phi-2)
- ✅ Capability validation (check manifest before invoking features)

**Optional for M2 (deferred to M3):**
- ⏸️ TransformersAdapter (HuggingFace models)
- ⏸️ OpenAIAdapter (cloud API)
- ⏸️ Tool calling support (function calling)

**Violations:**
- Provider missing required methods → Fail-fast at startup
- Provider bypassing capability checks → Runtime error
- Provider returning malformed response → Retry OR template fallback

---

**END OF SPARK PROVIDER CONTRACT**

**Date:** 2026-02-10
**Agent:** Agent D (Research Orchestrator)
**Authority:** PM (Aegis)
**Status:** ✅ **BINDING SPECIFICATION** (M2+)
**Signature:** Agent D (Research Orchestrator) — 2026-02-10

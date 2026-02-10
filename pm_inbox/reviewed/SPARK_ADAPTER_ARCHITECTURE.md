# Spark Adapter Architecture
## Design Specification for Dynamic Model Loading and Tier-Based Selection

**Document Type:** Design / Architecture Specification
**Phase:** M2 Preparation (Design-Only)
**Date:** 2026-02-10
**Status:** DESIGN (Non-binding until M2 implementation approval)
**Agent:** Agent A (LLM & Systems Architect)

---

## Purpose

This document defines the **architecture for the Spark Adapter**, which enables dynamic LLM model loading and tier-based model selection based on hardware capabilities. The Spark Adapter ensures:
- Runtime model swappability (no hardcoded models)
- Hardware-aware model selection (14B/7B/3B based on VRAM/CPU)
- Graceful degradation (fallback to smaller models when resources insufficient)
- Configuration-driven model registry (models.yaml)

**What This Document Defines:**
- Spark Adapter interface contract
- Model registry schema (models.yaml format)
- Model selection strategy (tier-based)
- Fallback logic (VRAM/CPU offload)
- Integration points with GuardedNarrationService

**What This Document Does NOT Define:**
- Implementation details (no code, no model files)
- Model file provisioning strategy
- Inference runtime selection (llama.cpp vs transformers vs vLLM)
- Performance benchmarks (deferred to M2 execution)

---

## 1. Spark Adapter Overview

### 1.1 Purpose

**Problem Statement:**
The LLM narration system must support multiple models (14B, 7B, 3B) based on user hardware, without hardcoding model paths or requiring code changes for model swaps.

**Solution:**
The Spark Adapter provides a **configuration-driven model loading interface** that:
1. Reads model registry (models.yaml)
2. Detects hardware tier (via Agent B's hardware detection)
3. Selects appropriate model (14B/7B/3B)
4. Loads model with correct quantization (4-bit/8-bit)
5. Provides fallback logic (VRAM overflow → smaller model or CPU offload)

---

### 1.2 Design Principles

**Principle 1: Spark Swappability (SPARK_SWAPPABLE_INVARIANT.md)**
- LLM models are **Spark components** (generative, non-deterministic)
- Must be swappable without breaking determinism (Lens/Box layers unaffected)
- Model swap = configuration change only (no code changes)

**Principle 2: Hardware-Aware Selection**
- Model selection based on detected hardware tier (Agent B)
- High tier (≥8 GB VRAM) → 14B model
- Medium tier (6-8 GB VRAM) → 7B model
- Low tier (<6 GB VRAM or CPU-only) → 3B model or CPU offload

**Principle 3: Graceful Degradation**
- If selected model fails to load → fallback to smaller model
- If VRAM exhausted → offload layers to CPU
- If all models fail → template-based narration (M0 fallback)

**Principle 4: Configuration-Driven**
- All model metadata in models.yaml (no hardcoded paths)
- Model registry updatable without code changes
- Model profiles include: path, quantization, context window, VRAM requirements

---

## 2. Spark Adapter Interface Contract

### 2.1 Core Interface

```python
class SparkAdapter:
    """Abstract interface for LLM model loading and selection.

    The Spark Adapter provides a hardware-aware model loading interface
    that selects models based on detected hardware tier and falls back
    gracefully when resources are insufficient.
    """

    def load_model(self, model_id: str) -> LoadedModel:
        """Load model by ID from model registry.

        Args:
            model_id: Model identifier (e.g., "mistral-7b-instruct-4bit")

        Returns:
            LoadedModel instance with inference interface

        Raises:
            ModelLoadError: If model cannot be loaded
            InsufficientResourcesError: If hardware requirements not met
        """
        raise NotImplementedError

    def select_model_for_tier(self, hardware_tier: HardwareTier) -> str:
        """Select appropriate model ID for detected hardware tier.

        Args:
            hardware_tier: Detected hardware tier (HIGH/MEDIUM/LOW)

        Returns:
            model_id: Best model for this hardware tier

        Raises:
            NoSuitableModelError: If no model fits hardware tier
        """
        raise NotImplementedError

    def get_fallback_model(self, failed_model_id: str) -> str:
        """Get fallback model ID if primary model fails to load.

        Args:
            failed_model_id: Model that failed to load

        Returns:
            fallback_model_id: Smaller model to try next

        Raises:
            NoFallbackAvailableError: If no fallback exists
        """
        raise NotImplementedError

    def check_model_compatibility(self, model_id: str) -> CompatibilityReport:
        """Check if model is compatible with current hardware.

        Args:
            model_id: Model to check

        Returns:
            CompatibilityReport with VRAM requirements, context window, etc.
        """
        raise NotImplementedError
```

---

### 2.2 Supporting Data Structures

```python
@dataclass
class HardwareTier:
    """Hardware capability tier detected by Agent B."""
    tier_name: str  # "HIGH", "MEDIUM", "LOW"
    vram_gb: float  # Available VRAM in GB
    cpu_cores: int  # Available CPU cores
    supports_gpu: bool  # GPU available (True/False)

@dataclass
class ModelProfile:
    """Model metadata from model registry."""
    id: str  # "mistral-7b-instruct-4bit"
    path: str  # Path to model file
    quantization: str  # "4bit", "8bit", "fp16"
    max_tokens: int  # Maximum generation length
    max_context_window: int  # Maximum context size (tokens)
    min_vram_gb: float  # Minimum VRAM required
    supports_streaming: bool  # Streaming generation support
    backend: str  # "llama.cpp", "transformers", "vllm"

@dataclass
class LoadedModel:
    """Loaded model instance with inference interface."""
    model_id: str
    profile: ModelProfile
    inference_engine: Any  # Runtime-specific inference engine

@dataclass
class CompatibilityReport:
    """Model compatibility check result."""
    model_id: str
    is_compatible: bool
    vram_required_gb: float
    vram_available_gb: float
    compatibility_issues: List[str]  # Reasons if not compatible
```

---

## 3. Model Registry Schema (models.yaml)

### 3.1 Schema Definition

```yaml
# models.yaml — Model Registry
# This file defines available LLM models and their hardware requirements

models:
  # High-Tier Model (14B, requires ≥8 GB VRAM)
  - id: mistral-14b-instruct-4bit
    path: models/mistral-14b-instruct-Q4_K_M.gguf
    quantization: 4bit
    max_tokens: 2048
    max_context_window: 8192
    min_vram_gb: 8.0
    supports_streaming: true
    backend: llama.cpp
    tier: HIGH
    fallback_model: mistral-7b-instruct-4bit

  # Medium-Tier Model (7B, requires 6-8 GB VRAM)
  - id: mistral-7b-instruct-4bit
    path: models/mistral-7b-instruct-Q4_K_M.gguf
    quantization: 4bit
    max_tokens: 2048
    max_context_window: 8192
    min_vram_gb: 6.0
    supports_streaming: true
    backend: llama.cpp
    tier: MEDIUM
    fallback_model: phi-3b-instruct-4bit

  # Low-Tier Model (3B, CPU-compatible)
  - id: phi-3b-instruct-4bit
    path: models/phi-3b-instruct-Q4_K_M.gguf
    quantization: 4bit
    max_tokens: 1024
    max_context_window: 4096
    min_vram_gb: 3.0
    supports_streaming: true
    backend: llama.cpp
    tier: LOW
    fallback_model: template-narration  # Ultimate fallback (M0 template)

  # Template Narration Fallback (No Model)
  - id: template-narration
    path: null
    quantization: null
    max_tokens: null
    max_context_window: null
    min_vram_gb: 0.0
    supports_streaming: false
    backend: template
    tier: FALLBACK
    fallback_model: null

# Tier Selection Rules
tier_selection:
  HIGH:
    min_vram_gb: 8.0
    preferred_model: mistral-14b-instruct-4bit
  MEDIUM:
    min_vram_gb: 6.0
    preferred_model: mistral-7b-instruct-4bit
  LOW:
    min_vram_gb: 0.0
    preferred_model: phi-3b-instruct-4bit
  FALLBACK:
    min_vram_gb: 0.0
    preferred_model: template-narration
```

---

### 3.2 Schema Field Definitions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique model identifier | `"mistral-7b-instruct-4bit"` |
| `path` | string | File path to model (relative to models/) | `"models/mistral-7b-instruct-Q4_K_M.gguf"` |
| `quantization` | string | Quantization format | `"4bit"`, `"8bit"`, `"fp16"` |
| `max_tokens` | int | Maximum generation length | `2048` |
| `max_context_window` | int | Maximum context size (tokens) | `8192` |
| `min_vram_gb` | float | Minimum VRAM required (GB) | `6.0` |
| `supports_streaming` | bool | Streaming generation support | `true` |
| `backend` | string | Inference runtime | `"llama.cpp"`, `"transformers"`, `"vllm"` |
| `tier` | string | Hardware tier | `"HIGH"`, `"MEDIUM"`, `"LOW"`, `"FALLBACK"` |
| `fallback_model` | string | Next model to try if this fails | `"mistral-7b-instruct-4bit"` |

---

## 4. Model Selection Strategy

### 4.1 Tier-Based Selection Algorithm

```
INPUT: HardwareTier (from Agent B hardware detection)
OUTPUT: model_id (selected model for this hardware)

ALGORITHM:
1. Read models.yaml → parse model registry
2. Extract tier_selection rules
3. Match HardwareTier to tier_selection:
   IF vram_gb >= 8.0 → tier = HIGH
   ELIF vram_gb >= 6.0 → tier = MEDIUM
   ELIF vram_gb >= 3.0 → tier = LOW
   ELSE → tier = FALLBACK
4. Get preferred_model for detected tier
5. Check model compatibility (vram_required <= vram_available)
6. IF compatible → RETURN model_id
   ELSE → RETURN fallback_model (recursive)
```

---

### 4.2 Model Selection Flowchart

```
┌─────────────────────────────────────┐
│ Agent B: Detect Hardware Tier      │
│ (VRAM, CPU, GPU availability)      │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ Spark Adapter: Read models.yaml    │
│ Parse model registry + tier rules  │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ Match HardwareTier → Tier Name     │
│ (HIGH/MEDIUM/LOW/FALLBACK)         │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ Get preferred_model for tier       │
│ (e.g., HIGH → mistral-14b-4bit)    │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ Check Model Compatibility           │
│ (vram_required <= vram_available?)  │
└─────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
   ✅ Compatible      ❌ Incompatible
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────────┐
│ Load Model   │  │ Get Fallback     │
│ Return model │  │ Retry with       │
│ instance     │  │ smaller model    │
└──────────────┘  └──────────────────┘
                         │
                         ▼
                  (Recursive fallback
                   until compatible
                   or template-narration)
```

---

## 5. Fallback Logic Design

### 5.1 Fallback Hierarchy

```
Primary Model (Tier-Based Selection)
    ↓ (If load fails or VRAM insufficient)
Fallback Model (defined in models.yaml)
    ↓ (If fallback fails)
Next Fallback (recursive)
    ↓ (If all models fail)
Template Narration (M0 fallback, no LLM)
```

**Example Fallback Chain:**
```
mistral-14b-instruct-4bit (8 GB VRAM required)
    ↓ VRAM insufficient (only 6 GB available)
mistral-7b-instruct-4bit (6 GB VRAM required)
    ↓ Load successful ✅
```

**Example Extreme Fallback:**
```
mistral-14b-instruct-4bit (8 GB VRAM required)
    ↓ VRAM insufficient (only 4 GB available)
mistral-7b-instruct-4bit (6 GB VRAM required)
    ↓ VRAM insufficient
phi-3b-instruct-4bit (3 GB VRAM required)
    ↓ Load successful ✅
```

**Example Complete Failure:**
```
mistral-14b-instruct-4bit (8 GB VRAM required)
    ↓ VRAM insufficient (CPU-only system)
mistral-7b-instruct-4bit (6 GB VRAM required)
    ↓ VRAM insufficient
phi-3b-instruct-4bit (3 GB VRAM required)
    ↓ VRAM insufficient (CPU fallback attempted, too slow)
template-narration (M0 template fallback)
    ↓ Always succeeds (no model required) ✅
```

---

### 5.2 Offload Logic (VRAM Overflow Handling)

**Scenario:** Model requires more VRAM than available, but CPU has sufficient RAM

**Offload Strategy:**
1. Attempt full GPU loading first
2. If VRAM insufficient → Offload layers to CPU
3. If still insufficient → Switch to smaller model
4. If all fail → Template narration fallback

**Offload Configuration Example:**
```yaml
# models.yaml (offload section)
offload_config:
  mistral-14b-instruct-4bit:
    gpu_layers: 40  # Full model on GPU (if VRAM ≥8 GB)
    offload_layers: 20  # Offload 20 layers to CPU if VRAM <8 GB
    min_gpu_layers: 10  # Minimum 10 layers on GPU (otherwise fallback)

  mistral-7b-instruct-4bit:
    gpu_layers: 32
    offload_layers: 16
    min_gpu_layers: 8
```

**Offload Decision Logic:**
```
IF vram_available >= model.min_vram_gb:
    → Load entire model on GPU (gpu_layers = max)
ELIF vram_available >= (model.min_vram_gb * 0.5):
    → Offload layers to CPU (gpu_layers = reduced, offload_layers = active)
ELSE:
    → Fallback to smaller model (insufficient VRAM for offload)
```

---

### 5.3 Graceful Degradation User Experience

**User Notification Strategy:**

**Case 1: Successful Model Load**
```
✅ "Loading Mistral 14B model... Ready!"
(No user notification needed, system working as expected)
```

**Case 2: Fallback to Smaller Model**
```
⚠️ "Mistral 14B requires 8 GB VRAM (6 GB available).
    Falling back to Mistral 7B for optimal performance."
```

**Case 3: CPU Offload**
```
⚠️ "Offloading 20 model layers to CPU due to VRAM constraints.
    Generation may be slower but quality is preserved."
```

**Case 4: Template Narration Fallback**
```
⚠️ "LLM models require more resources than available.
    Using template-based narration (upgrade recommended for full experience)."
```

---

## 6. Integration Points

### 6.1 Integration with GuardedNarrationService

**Current M1 Implementation:**
```python
# aidm/narration/guarded_narration_service.py (M1)
class GuardedNarrationService:
    def generate_narration(self, request: NarrationRequest) -> str:
        # M1: Template-based (no LLM)
        return self._generate_template_narration(request.engine_result)
```

**M2 Integration with Spark Adapter:**
```python
# aidm/narration/guarded_narration_service.py (M2)
class GuardedNarrationService:
    def __init__(self, spark_adapter: SparkAdapter):
        self.spark_adapter = spark_adapter
        self.loaded_model = None

    def initialize_model(self, hardware_tier: HardwareTier):
        """Load appropriate model for hardware tier."""
        model_id = self.spark_adapter.select_model_for_tier(hardware_tier)
        self.loaded_model = self.spark_adapter.load_model(model_id)

    def generate_narration(self, request: NarrationRequest) -> str:
        # M2: LLM-based (with template fallback)
        if self.loaded_model and self.loaded_model.model_id != "template-narration":
            return self._generate_llm_narration(request, self.loaded_model)
        else:
            return self._generate_template_narration(request.engine_result)
```

---

### 6.2 Integration with Agent B (Hardware Detection)

**Agent B Provides:**
```python
@dataclass
class HardwareTier:
    tier_name: str  # "HIGH", "MEDIUM", "LOW"
    vram_gb: float
    cpu_cores: int
    supports_gpu: bool
```

**Spark Adapter Consumes:**
```python
hardware_tier = agent_b.detect_hardware_tier()
model_id = spark_adapter.select_model_for_tier(hardware_tier)
loaded_model = spark_adapter.load_model(model_id)
```

---

### 6.3 Integration with Agent D (Governance)

**Governance Checks:**
1. **Model Swappability Validation**
   - Verify that swapping models does NOT break determinism (Lens/Box unaffected)
   - Test: Generate narration with Model A, swap to Model B, verify mechanical outcomes identical

2. **Fallback Chain Validation**
   - Verify that fallback chain always terminates (no infinite loops)
   - Test: Force VRAM=0, verify template-narration fallback reached

3. **Configuration Integrity**
   - Verify models.yaml schema compliance
   - Test: Parse models.yaml, validate all required fields present

---

## 7. Error Handling & Edge Cases

### 7.1 Error Scenarios

| Error | Trigger | Response |
|-------|---------|----------|
| **ModelLoadError** | Model file not found | Fallback to next model in chain |
| **InsufficientResourcesError** | VRAM < min_vram_gb | Attempt offload, then fallback |
| **NoSuitableModelError** | No model fits hardware | Fallback to template narration |
| **CorruptedModelFileError** | Model file corrupt/invalid | Fallback to next model in chain |
| **BackendNotAvailableError** | llama.cpp/transformers not installed | Fallback to template narration |

---

### 7.2 Edge Case Handling

**Edge Case 1: All Models Fail to Load**
- **Response:** Fallback to template-narration (M0 fallback)
- **User Notification:** "LLM models unavailable, using template narration"

**Edge Case 2: Model Loads But Inference Fails**
- **Response:** Retry once, then fallback to next model
- **User Notification:** "Model error detected, switching to fallback model"

**Edge Case 3: VRAM Changes Mid-Session (GPU Disconnected)**
- **Response:** Detect VRAM change, reload appropriate model
- **User Notification:** "Hardware change detected, reloading model"

**Edge Case 4: Model Registry File Missing/Corrupt**
- **Response:** Use hardcoded fallback config (minimal model list)
- **User Notification:** "Model registry unavailable, using default configuration"

---

## 8. Configuration Management

### 8.1 Configuration Loading

**Configuration Sources (Priority Order):**
1. User-specific models.yaml (user-editable)
2. Default models.yaml (shipped with AIDM)
3. Hardcoded fallback config (code-embedded minimal config)

**Loading Logic:**
```
1. Attempt to load: ~/.aidm/models.yaml (user config)
   IF exists → LOAD
   ELSE → Continue
2. Attempt to load: /config/models.yaml (default config)
   IF exists → LOAD
   ELSE → Continue
3. Use hardcoded fallback config (minimal: template-narration only)
```

---

### 8.2 Configuration Validation

**Required Validation Checks:**
1. Schema compliance (all required fields present)
2. Model file paths valid (files exist)
3. Fallback chains acyclic (no circular fallbacks)
4. Tier selection rules valid (min_vram_gb values reasonable)
5. Backend availability (llama.cpp installed if backend="llama.cpp")

**Validation Errors:**
- **Schema Error:** Missing required field → Use default config
- **File Path Error:** Model file not found → Skip model, use fallback
- **Circular Fallback:** Model A → Model B → Model A → REJECT, use default chain

---

## 9. Performance Considerations

### 9.1 Model Loading Latency

**Expected Latency (Hardware-Dependent):**
- 14B model (4-bit): 10-30 seconds (initial load)
- 7B model (4-bit): 5-15 seconds (initial load)
- 3B model (4-bit): 2-5 seconds (initial load)
- Template narration: <1 second (no model)

**Mitigation Strategy:**
- Lazy loading (load model on first use, not at startup)
- Loading screen with progress indicator
- Background model preloading (optional, during prep phase)

---

### 9.2 VRAM Monitoring

**Strategy:** Monitor VRAM usage during inference, detect overflow

**Overflow Response:**
1. Detect VRAM allocation failure
2. Unload current model
3. Load fallback model (smaller)
4. Notify user of degradation

---

## 10. Testing Strategy

### 10.1 Unit Tests

**Test Coverage:**
1. Model registry parsing (valid/invalid YAML)
2. Tier selection logic (HIGH/MEDIUM/LOW/FALLBACK)
3. Fallback chain traversal (recursive fallback)
4. Compatibility checking (VRAM requirements)
5. Error handling (missing files, corrupt models)

**Example Test:**
```python
def test_tier_selection_high_vram():
    """Test that HIGH tier selects 14B model."""
    hardware = HardwareTier(tier_name="HIGH", vram_gb=10.0, cpu_cores=8, supports_gpu=True)
    model_id = spark_adapter.select_model_for_tier(hardware)
    assert model_id == "mistral-14b-instruct-4bit"

def test_fallback_chain():
    """Test that fallback chain terminates at template-narration."""
    hardware = HardwareTier(tier_name="FALLBACK", vram_gb=0.0, cpu_cores=4, supports_gpu=False)
    model_id = spark_adapter.select_model_for_tier(hardware)
    assert model_id == "template-narration"
```

---

### 10.2 Integration Tests

**Test Scenarios:**
1. Load model for each tier (HIGH/MEDIUM/LOW)
2. Force fallback (set VRAM=0, verify template-narration reached)
3. Swap models mid-session (verify determinism preserved)
4. Corrupt model file (verify fallback triggered)

---

## 11. Explicit Non-Goals

### 11.1 What This Architecture Does NOT Cover

**Deferred to M2 Implementation:**
- ❌ Model file provisioning (where/how to download models)
- ❌ Inference runtime selection (llama.cpp vs transformers vs vLLM)
- ❌ Model quantization tooling (GPTQ vs GGUF conversion)
- ❌ Performance benchmarks (latency, throughput)
- ❌ Model fine-tuning strategy

**Out of Scope:**
- ❌ Cloud-based model hosting (M0/M1/M2 = local-first)
- ❌ Model licensing compliance (user responsibility)
- ❌ Multi-GPU support (single GPU only for M2)
- ❌ Dynamic quantization (fixed quantization per model)

---

## 12. Dependencies

### 12.1 Blocked on Agent B

**Hardware Detection System:**
- Agent B must provide HardwareTier detection
- Required: VRAM detection, CPU core count, GPU availability

**Integration Point:**
```python
from aidm.hardware import detect_hardware_tier
hardware_tier = detect_hardware_tier()
```

---

### 12.2 Blocked on PM

**Infrastructure Provisioning:**
- Model files (14B/7B/3B) must be provisioned
- Inference runtime (llama.cpp or transformers) must be installed
- Storage allocation (models/ directory)

---

## 13. Acceptance Criteria

### 13.1 Design Acceptance (This Document)

**Pass Criteria:**
- ✅ Interface contract defined
- ✅ Model registry schema specified
- ✅ Tier selection strategy documented
- ✅ Fallback logic designed
- ✅ Integration points identified

**Fail Criteria:**
- ❌ Missing interface methods
- ❌ Ambiguous fallback logic
- ❌ Incomplete model registry schema

---

### 13.2 Implementation Acceptance (M2 Phase)

**Pass Criteria (Future):**
- ✅ Spark Adapter class implemented
- ✅ models.yaml parsing functional
- ✅ Tier selection logic working
- ✅ Fallback chain verified (no infinite loops)
- ✅ Integration tests passing (model swap preserves determinism)

---

## 14. References

- **SPARK_SWAPPABLE_INVARIANT.md:** Spark swappability principle
- **SPARK_LENS_BOX_DOCTRINE.md:** Spark/Lens/Box separation
- **M1_LLM_SAFEGUARD_ARCHITECTURE.md:** LLM integration safeguards
- **GuardedNarrationService:** M1 implementation (template-based)

---

## 15. Validation Checklist

**Agent A Self-Audit:**
- ✅ **No implementation language:** No code written, architecture only
- ✅ **No model provisioning:** No model files referenced (deferred to M2)
- ✅ **No inference runtime selection:** Backend choice deferred
- ✅ **Integration points defined:** Agent B (hardware), Agent D (governance)
- ✅ **Fallback logic complete:** Chain terminates at template-narration
- ✅ **Configuration-driven:** models.yaml schema specified

**Hard Constraints Observed:**
- ❌ NO code written (architecture specification only)
- ❌ NO model files provisioned
- ❌ NO runtime selection (llama.cpp vs transformers deferred)

---

**END OF SPARK ADAPTER ARCHITECTURE**

**Date:** 2026-02-10
**Agent:** Agent A (LLM & Systems Architect)
**Phase:** M2 Preparation (Design-Only)
**Deliverable:** SPARK_ADAPTER_ARCHITECTURE.md
**Status:** COMPLETE (awaiting PM review)
**Authority:** DESIGN (non-binding until M2 implementation approval)

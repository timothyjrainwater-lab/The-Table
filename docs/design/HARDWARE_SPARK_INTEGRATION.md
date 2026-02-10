# Hardware Tier Integration & Spark Adapter Coordination

**Status:** ✅ **COMPLETE**
**Date:** 2026-02-10
**Agent:** Agent B (Systems Validation / Image Research)
**Instruction Packet:** 01 - Hardware Tier Integration & Model Fallback Logic
**Authority:** WRITE-ENABLED

---

## Executive Summary

Successfully integrated Agent B's hardware detection system with Agent A's Spark Adapter Architecture. The integration ensures seamless model selection based on hardware capabilities, with full support for fallback chains and offload strategies defined in the Spark model registry.

**Key Achievements:**
- ✅ Aligned hardware tier thresholds with Spark specification (8GB HIGH, 6GB MEDIUM)
- ✅ Created complete `config/models.yaml` Spark model registry
- ✅ Updated `ModelSelector` to read from Spark registry
- ✅ Implemented fallback chains (model → fallback_model → template-narration)
- ✅ All unit tests passing (12/12 tests)
- ✅ Documentation updated to reflect integration

---

## Integration Architecture

### Component Integration Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Hardware Detection (Agent B)                             │
│    aidm/core/hardware_detector.py                           │
│    - Detects GPU VRAM via PyTorch CUDA                      │
│    - Detects CPU cores/RAM via psutil                       │
│    - Assigns tier: HIGH (≥8GB), MEDIUM (6-8GB), FALLBACK   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Model Selection (Agent B + Spark Registry)               │
│    aidm/core/model_selector.py + config/models.yaml         │
│    - Reads models.yaml for preferred_model per tier         │
│    - Validates VRAM compatibility                           │
│    - Applies fallback chain if incompatible                 │
│    - Configures offload strategy (GPU/CPU layers)           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Model Loading (Agent A - Future M2)                      │
│    aidm/spark/spark_adapter.py (NOT YET IMPLEMENTED)        │
│    - Loads model file from path (e.g., .gguf)               │
│    - Configures llama.cpp backend                           │
│    - Provides inference interface                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Narration Generation (Agent A - Future M2)               │
│    aidm/narration/guarded_narration_service.py              │
│    - Calls Spark adapter for LLM inference                  │
│    - Applies LENS filtering and BOX validation              │
│    - Returns provenance-labeled narration                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Spark Model Registry (`config/models.yaml`)

### Registry Structure

The model registry follows the specification in `SPARK_ADAPTER_ARCHITECTURE.md` and `SPARK_PROVIDER_CONTRACT.md`:

**Key Sections:**
1. **spark.models**: List of available models with metadata
2. **tier_selection**: Preferred model per hardware tier
3. **offload_strategy**: CPU offload configuration rules
4. **providers**: Backend-specific settings (llama.cpp, transformers)

**Example Model Entry:**
```yaml
- id: "mistral-7b-instruct-4bit"
  name: "Mistral 7B Instruct v0.2 (4-bit)"
  provider: "llamacpp"
  path: "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
  quantization: "4bit"
  max_context_window: 8192
  min_vram_gb: 6.0
  tier: "MEDIUM"
  fallback_model: "phi-3b-instruct-4bit"
  presets:
    narration:
      temperature: 0.8
      max_tokens: 150
```

### Model Fallback Chains

**HIGH Tier:**
```
mistral-14b-instruct-4bit → mistral-7b-instruct-4bit → phi-3b-instruct-4bit → template-narration
```

**MEDIUM Tier:**
```
mistral-7b-instruct-4bit → phi-3b-instruct-4bit → template-narration
```

**FALLBACK Tier:**
```
phi-3b-instruct-4bit → qwen2.5-3b-instruct → template-narration
```

**Ultimate Fallback:**
```
template-narration (M0 template-based narration, no model loading required)
```

---

## Hardware Tier Alignment

### Threshold Changes (Spark Alignment)

| Tier | Previous Threshold | Spark-Aligned Threshold | Rationale |
|------|-------------------|------------------------|-----------|
| **HIGH** | ≥12 GB VRAM | ≥8 GB VRAM | Aligns with Spark spec, supports RTX 2080 (8GB) for 14B models |
| **MEDIUM** | 6-12 GB VRAM | 6-8 GB VRAM | Clearer tier boundary, 8GB+ gets HIGH tier |
| **FALLBACK** | <6 GB VRAM | <6 GB VRAM | Unchanged, supports low-VRAM GPUs and CPU-only |

**Impact:**
- RTX 2080 (8GB) now classified as HIGH tier (previously MEDIUM)
- Enables 14B model loading on 8GB GPUs (with 4-bit quantization)
- More consistent with Spark architecture specification

---

## Model Selection Logic

### Selection Algorithm (Updated)

```python
def select_model(capabilities: HardwareCapabilities) -> ModelSelectionResult:
    """Select model based on hardware tier and Spark registry."""

    # Step 1: Get preferred model for tier from models.yaml
    tier_name = capabilities.tier.value.upper()
    preferred_model_id = models_yaml["tier_selection"][tier_name]["preferred_model"]

    # Step 2: Look up model entry in registry
    model_entry = find_model_by_id(preferred_model_id)

    # Step 3: Check VRAM compatibility
    required_vram = model_entry["min_vram_gb"]
    available_vram = capabilities.gpu_info.vram_available_gb

    if available_vram >= required_vram:
        # Compatible - load without offload
        return ModelConfig(
            model_name=preferred_model_id,
            model_path=model_entry["path"],
            enable_offload=False
        )
    else:
        # Incompatible - try fallback model
        fallback_model_id = model_entry["fallback_model"]
        return select_model_recursive(fallback_model_id)  # Recursive fallback
```

### Offload Configuration

**Full GPU (VRAM ≥ requirements):**
```python
ModelConfig(
    enable_offload=False,
    offload_layers=0,
    device_map="auto"
)
```

**Partial Offload (VRAM = 50-100% of requirements):**
```python
ModelConfig(
    enable_offload=True,
    offload_layers=0,  # Auto-determine
    device_map="auto",
    load_in_8bit=True  # 8-bit quantization to reduce VRAM
)
```

**Full CPU Offload (VRAM < 50% or no GPU):**
```python
ModelConfig(
    enable_offload=True,
    offload_layers=999,  # Offload all layers
    device_map="cpu",
    torch_dtype="float32"
)
```

---

## Testing & Validation

### Unit Test Results

**Test Suite:** `tests/test_hardware_detection.py`
**Status:** ✅ **12/12 PASSING**

**Test Coverage:**
1. ✅ High tier assignment (12GB VRAM)
2. ✅ High tier assignment (8GB VRAM, Spark-aligned)
3. ✅ Medium tier assignment (7GB VRAM)
4. ✅ Fallback tier assignment (4GB VRAM)
5. ✅ Fallback tier CPU-only
6. ✅ Marginal VRAM warning
7. ✅ High tier model selection (14B)
8. ✅ Medium tier model selection (7B)
9. ✅ Fallback tier model selection (3B with offload)
10. ✅ CPU-only full offload
11. ✅ CPU detection fallback
12. ✅ Hardware capability caching

**Test Adjustments:**
- Updated `test_medium_tier_assignment_8gb_vram` → `test_medium_tier_assignment_7gb_vram` (7GB now MEDIUM)
- Added `test_high_tier_assignment_8gb_vram` (8GB now HIGH tier)
- All tests aligned with Spark thresholds

---

## Files Modified/Created

### Created Files
1. **`config/models.yaml`** (362 lines)
   - Complete Spark model registry
   - Model definitions per tier (HIGH/MEDIUM/FALLBACK)
   - Tier selection rules
   - Offload configuration strategies
   - Provider settings (llama.cpp, transformers)

### Modified Files
1. **`aidm/schemas/hardware_capability.py`**
   - Updated `VRAM_THRESHOLD_HIGH_TIER` from 12288 (12GB) to 8192 (8GB)
   - Updated `TIER_REQUIREMENTS` to align with Spark
   - Added reference to Spark architecture in docstring

2. **`aidm/core/model_selector.py`**
   - Added `yaml` import for models.yaml parsing
   - Added `DEFAULT_MODEL_REGISTRY_PATH` constant
   - Implemented `_load_model_registry()` to read models.yaml
   - Implemented `_build_fallback_registry()` for graceful degradation
   - Added helper methods: `_get_models_by_tier()`, `_get_preferred_model_id()`, `_get_model_by_id()`
   - Updated model selection methods to read from registry instead of hardcoded dict
   - Added `_select_template_narration()` for ultimate fallback

3. **`docs/design/HARDWARE_DETECTION_SYSTEM.md`**
   - Updated tier thresholds section (8GB HIGH, 6GB MEDIUM)
   - Added Spark integration section
   - Updated model registry section with models.yaml structure
   - Added Spark Adapter coordination examples
   - Updated references to include Spark architecture docs

4. **`pyproject.toml`**
   - Added `psutil>=5.9.0` dependency (hardware detection)
   - Added `pyyaml>=6.0` dependency (models.yaml parsing)

5. **`tests/test_hardware_detection.py`**
   - Updated `test_medium_tier_assignment_8gb_vram` to use 7GB (MEDIUM tier)
   - Added `test_high_tier_assignment_8gb_vram` (8GB = HIGH tier)
   - Updated docstrings to reference Spark alignment

---

## Coordination with Agent A

### Agent B Deliverables (Complete)
- ✅ Hardware detection logic (`hardware_detector.py`)
- ✅ Tier classification aligned with Spark (8GB HIGH, 6GB MEDIUM)
- ✅ Model selection logic reading from Spark registry (`model_selector.py`)
- ✅ Spark model registry (`config/models.yaml`)
- ✅ Fallback chain implementation
- ✅ Offload configuration logic
- ✅ Unit tests passing (12/12)
- ✅ Documentation updated

### Agent A Responsibilities (Pending M2)
- ⏸️ Implement `SparkAdapter` interface
- ⏸️ Implement `LlamaCppAdapter` for .gguf models
- ⏸️ Integrate with `GuardedNarrationService`
- ⏸️ Implement LENS/BOX provenance labeling
- ⏸️ Handle model loading from paths in models.yaml
- ⏸️ Implement inference interface (`generate()`)

### Handoff Points
1. **`ModelConfig` → SparkAdapter**: Agent B provides model configuration, Agent A loads model
2. **`models.yaml` → SparkAdapter**: Agent A reads same registry for model path and settings
3. **Fallback Chain**: Agent A must implement fallback logic when model loading fails
4. **Template Narration**: Agent A falls back to M0 template system when all models fail

---

## Next Steps

### Immediate (M2 Preparation)
1. ✅ **Complete** - Hardware tier integration with Spark
2. ⏸️ **Agent A** - Implement SparkAdapter interface
3. ⏸️ **Agent A** - Implement LlamaCppAdapter (.gguf loading)
4. ⏸️ **Infrastructure** - Provision model files (14B/7B/3B .gguf models)

### Future Enhancements (M3+)
1. **AMD GPU Support (ROCm)**: Detect AMD GPUs, support RX 6000/7000 series
2. **Apple Silicon Support (Metal)**: Detect M1/M2/M3 GPUs, use Metal backend
3. **Dynamic Model Swapping**: Runtime tier changes (14B → 7B if VRAM pressure)
4. **Advanced Offload**: Layer-wise offload optimization, mixed precision
5. **Performance Monitoring**: Track inference latency, auto-downgrade if >2 seconds

---

## Compliance & Validation

### Spark Architecture Compliance
- ✅ Tier thresholds aligned with `SPARK_ADAPTER_ARCHITECTURE.md`
- ✅ Model registry follows `SPARK_PROVIDER_CONTRACT.md` schema
- ✅ Fallback chains terminate at `template-narration` (M0 fallback)
- ✅ Offload configuration per model tier
- ✅ Provider-agnostic interface (llama.cpp, transformers, future OpenAI)

### Testing Compliance
- ✅ All unit tests passing (12/12)
- ✅ Tier assignment tests cover all thresholds
- ✅ Model selection tests cover all tiers
- ✅ Fallback logic tested (GPU marginal, CPU-only)
- ✅ Caching behavior validated

### Documentation Compliance
- ✅ `HARDWARE_DETECTION_SYSTEM.md` updated
- ✅ Integration points documented
- ✅ Spark coordination examples provided
- ✅ Model registry structure documented

---

## Summary

The hardware tier integration with Spark Adapter Architecture is **COMPLETE**. Agent B has successfully:

1. **Aligned tier thresholds** with Spark specification (8GB HIGH, 6GB MEDIUM)
2. **Created complete Spark model registry** (`config/models.yaml`) with fallback chains
3. **Integrated ModelSelector** to read from Spark registry instead of hardcoded models
4. **Validated all changes** with passing unit tests (12/12)
5. **Documented integration** in `HARDWARE_DETECTION_SYSTEM.md`

**Handoff to Agent A:**
- Hardware detection and model selection logic is production-ready
- Agent A can now implement `SparkAdapter` to load models using `ModelConfig`
- Model registry provides all metadata needed for model loading
- Fallback chains ensure graceful degradation to template narration

**Authority:** Agent B work is WRITE-ENABLED and COMPLETE. Ready for Agent A M2 implementation.

---

**Agent:** Agent B (Systems Validation / Image Research)
**Date:** 2026-02-10
**Status:** ✅ **COMPLETE**
**Signature:** Agent B — Hardware Tier Integration & Spark Adapter Coordination

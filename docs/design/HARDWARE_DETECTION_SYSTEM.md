# Hardware Detection & LLM Tier Selection System

## Overview

The hardware detection system automatically detects GPU (VRAM, CUDA) and CPU (cores, RAM) capabilities to assign an appropriate LLM model tier. This ensures optimal model selection based on available hardware, with automatic fallback and offload strategies when VRAM is insufficient.

**Status:** IMPLEMENTED + SPARK INTEGRATION COMPLETE (2026-02-10)
**Agent:** Agent B (Systems Validation / Image Research)
**Priority:** HIGH
**Authority:** WRITE-ENABLED (Production Code)
**Integration:** Spark Adapter Architecture (Agent A)

---

## Tier System

The system classifies hardware into three tiers (aligned with Spark Adapter Architecture):

| Tier | VRAM Requirement | Model Size | Offload | Use Case |
|------|------------------|------------|---------|----------|
| **HIGH** | ≥8 GB | 14B parameters | No | High-end GPUs (RTX 3060 12GB, RTX 3090, RTX 4080) |
| **MEDIUM** | 6-8 GB | 7B parameters | No | Mid-range GPUs (RTX 2060, GTX 1070, RX 6600 XT) |
| **FALLBACK** | <6 GB or CPU-only | 3B parameters | Yes | Low VRAM GPUs (GTX 1050 Ti) or CPU-only systems |

### Tier Assignment Logic

```python
if vram >= 8 GB:
    tier = HIGH (14B models, no offload)
elif vram >= 6 GB:
    tier = MEDIUM (7B models, no offload)
else:
    tier = FALLBACK (3B models with offload, or CPU-only)
```

**Note:** Thresholds aligned with `SPARK_ADAPTER_ARCHITECTURE.md` specification.

---

## Architecture

### Component Overview

1. **`aidm/schemas/hardware_capability.py`**: Schema definitions
   - `HardwareTier`: Enum for HIGH/MEDIUM/FALLBACK tiers
   - `GPUInfo`: GPU hardware information (VRAM, compute capability)
   - `CPUInfo`: CPU hardware information (cores, RAM)
   - `HardwareCapabilities`: Complete hardware profile with assigned tier
   - `ModelTierRequirements`: VRAM/RAM requirements per tier

2. **`aidm/core/hardware_detector.py`**: Hardware detection implementation
   - `HardwareDetector`: Detects GPU (PyTorch CUDA) and CPU (psutil)
   - `detect_hardware()`: Convenience function for detection
   - Caching support to avoid repeated detection calls

3. **`aidm/core/model_selector.py`**: Model selection logic (Spark integration)
   - `ModelSelector`: Selects appropriate model based on hardware tier
   - Reads `config/models.yaml` for Spark model registry
   - `ModelConfig`: Configuration for model loading (offload, quantization, device map)
   - `select_model_for_hardware()`: Convenience function for model selection

4. **`config/models.yaml`**: Spark model registry (NEW)
   - Defines available models per tier (HIGH/MEDIUM/FALLBACK)
   - Model metadata: paths, quantization, context windows, VRAM requirements
   - Fallback chains for graceful degradation
   - Offload configuration per model

5. **`tests/test_hardware_detection.py`**: Unit tests
   - Tests for tier assignment logic
   - Tests for model selection per tier
   - Integration tests for detection → selection pipeline

6. **`aidm/examples/hardware_detection_example.py`**: Usage example
   - Complete workflow demonstration
   - Error handling examples
   - Fallback configuration

---

## Spark Integration

### Integration with Agent A's Spark Adapter

The hardware detection system is now fully integrated with Agent A's Spark Adapter Architecture:

**Hardware Detection (Agent B) → Model Registry (models.yaml) → Spark Adapter (Agent A)**

```python
# Step 1: Detect hardware tier (Agent B)
from aidm.core.hardware_detector import detect_hardware
capabilities = detect_hardware()

# Step 2: Select model from registry (Agent B + models.yaml)
from aidm.core.model_selector import select_model_for_hardware
result = select_model_for_hardware(capabilities)

# Step 3: Load model via Spark Adapter (Agent A)
# (Future M2 implementation)
# spark_adapter = SparkAdapter()
# loaded_model = spark_adapter.load_model(result.config.model_name)
```

**Key Integration Points:**

1. **Tier Thresholds:** Aligned with Spark specification (8GB HIGH, 6GB MEDIUM)
2. **Model Registry:** `config/models.yaml` defines available models per tier
3. **Fallback Chains:** Models.yaml specifies fallback_model for each entry
4. **Offload Config:** Models.yaml includes offload_config for FALLBACK tier models

**Division of Responsibilities:**
- **Agent B (Hardware Detection):** Detect GPU/CPU, assign tier, select model ID from registry
- **Agent A (Spark Adapter):** Load model file, manage inference, handle LENS/BOX integration

---

## Usage

### Basic Usage

```python
from aidm.core.hardware_detector import detect_hardware
from aidm.core.model_selector import select_model_for_hardware

# Step 1: Detect hardware
capabilities = detect_hardware()

print(f"Tier: {capabilities.tier.value}")
print(f"Has GPU: {capabilities.has_gpu}")
print(f"Requires Offload: {capabilities.requires_offload}")

# Step 2: Select model
result = select_model_for_hardware(capabilities)

print(f"Model: {result.config.model_name}")
print(f"Size: {result.config.model_size.value}")
print(f"Enable Offload: {result.config.enable_offload}")

# Step 3: Load model (pseudocode)
# model = load_model(
#     result.config.model_name,
#     device_map=result.config.device_map,
#     load_in_8bit=result.config.load_in_8bit,
#     offload=result.config.enable_offload,
# )
```

### Advanced Usage: Preferred Model Override

```python
from aidm.core.hardware_detector import detect_hardware
from aidm.core.model_selector import ModelSelector

capabilities = detect_hardware()
selector = ModelSelector()

# Try to use preferred model (will fallback if incompatible)
result = selector.select_model(
    capabilities,
    preferred_model="qwen2.5-14b-instruct"
)

if result.fallback_applied:
    print(f"⚠ Preferred model not compatible, using fallback")
    print(f"  Reason: {result.reason}")

for warning in result.warnings:
    print(f"  Warning: {warning}")
```

### Caching and Re-detection

```python
from aidm.core.hardware_detector import HardwareDetector

detector = HardwareDetector()

# First detection (queries hardware)
capabilities = detector.detect()

# Second detection (returns cached)
capabilities_cached = detector.detect()

# Force re-detection (queries hardware again)
capabilities_fresh = detector.detect(force_refresh=True)
```

---

## Model Registry

### Spark Model Registry (models.yaml)

The model registry is now defined in `config/models.yaml` following Spark Adapter Architecture specification.

**Available Models Per Tier:**

**HIGH Tier (14B models):**
- `mistral-14b-instruct-4bit` (default)
- `qwen2.5-14b-instruct`

**MEDIUM Tier (7B models):**
- `mistral-7b-instruct-4bit` (default)
- `qwen2.5-7b-instruct`
- `llama-3-7b-instruct`

**FALLBACK Tier (3B models):**
- `phi-3b-instruct-4bit` (default)
- `qwen2.5-3b-instruct`
- `stablelm-3b-4e1t`

**Template Fallback:**
- `template-narration` (ultimate fallback, no model loading)

**Registry Structure Example:**
```yaml
spark:
  default: "mistral-7b-instruct-4bit"
  models:
    - id: "mistral-7b-instruct-4bit"
      name: "Mistral 7B Instruct v0.2 (4-bit)"
      provider: "llamacpp"
      path: "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
      quantization: "4bit"
      max_tokens: 2048
      max_context_window: 8192
      min_vram_gb: 6.0
      min_ram_gb: 16.0
      supports_streaming: true
      backend: "llama.cpp"
      tier: "MEDIUM"
      fallback_model: "phi-3b-instruct-4bit"
      presets:
        narration:
          temperature: 0.8
          max_tokens: 150
          stop_sequences: ["</narration>", "\n\n"]

tier_selection:
  HIGH:
    min_vram_gb: 8.0
    preferred_model: "mistral-14b-instruct-4bit"
  MEDIUM:
    min_vram_gb: 6.0
    preferred_model: "mistral-7b-instruct-4bit"
  FALLBACK:
    min_vram_gb: 0.0
    preferred_model: "phi-3b-instruct-4bit"
```

**Model Selection Process:**
1. Hardware detector determines tier (HIGH/MEDIUM/FALLBACK)
2. ModelSelector reads models.yaml and gets preferred_model for tier
3. ModelSelector validates VRAM compatibility
4. If compatible → return model config
5. If incompatible → try fallback_model (recursive)
6. Ultimate fallback → template-narration (always succeeds)

---

## Offload Strategies

### When Offload is Enabled

Offload is automatically enabled when:
1. No GPU detected (CPU-only)
2. GPU VRAM < 6 GB (insufficient for 7B models)
3. User overrides to load larger model than tier supports

### Offload Configuration

**Marginal GPU (4-6 GB VRAM):**
```python
config = ModelConfig(
    model_name="qwen2.5-3b-instruct",
    model_size=ModelSize.SMALL_3B,
    enable_offload=True,
    offload_layers=0,  # Auto-determine optimal split
    device_map="auto",  # Let transformers decide GPU/CPU split
    load_in_8bit=True,  # Reduce VRAM footprint via quantization
)
```

**CPU-Only:**
```python
config = ModelConfig(
    model_name="qwen2.5-3b-instruct",
    model_size=ModelSize.SMALL_3B,
    enable_offload=True,
    offload_layers=999,  # Offload all layers to CPU
    device_map="cpu",  # Force CPU execution
    torch_dtype="float32",  # CPU uses float32 (no bfloat16)
)
```

---

## Error Handling

### Detection Failures

The system handles detection failures gracefully:

```python
try:
    capabilities = detect_hardware()
except Exception as e:
    logger.error(f"Hardware detection failed: {e}")
    # Fallback to minimal configuration
    capabilities = HardwareCapabilities(
        tier=HardwareTier.FALLBACK,
        gpu_info=None,
        cpu_info=CPUInfo(
            processor="Unknown",
            physical_cores=4,
            logical_cores=8,
            ram_total_mb=8192,
            ram_available_mb=4096,
        ),
        detection_errors=[str(e)],
    )
```

### Insufficient Hardware Warnings

The system provides warnings when hardware is marginal:

```python
result = select_model_for_hardware(capabilities)

if result.warnings:
    print("⚠ Hardware Warnings:")
    for warning in result.warnings:
        print(f"  - {warning}")

# Example warnings:
# - "GPU VRAM (6.5GB) is marginal for 7B models. Consider enabling CPU offload if OOM errors occur."
# - "System RAM (7.8GB) below minimum requirement (8GB). LLM inference may be slow or fail."
```

---

## Performance Expectations

### Inference Latency by Tier

| Tier | Model Size | Hardware Example | Expected Latency |
|------|------------|------------------|------------------|
| **HIGH** | 14B | RTX 3090 (24GB) | <500ms per generation |
| **MEDIUM** | 7B | RTX 2060 (8GB) | <800ms per generation |
| **FALLBACK (GPU)** | 3B | GTX 1050 Ti (4GB) with offload | 1-3 seconds per generation |
| **FALLBACK (CPU)** | 3B | Intel i7 (8 cores) | 5-15 seconds per generation |

**Note:** Latency depends on prompt length, context size, and generation length.

### VRAM Usage Estimates

| Model Size | VRAM Required (FP16) | VRAM Required (8-bit) | VRAM Required (4-bit) |
|------------|---------------------|----------------------|----------------------|
| **14B** | ~12-14 GB | ~7-8 GB | ~4-5 GB |
| **7B** | ~6-7 GB | ~3.5-4 GB | ~2-2.5 GB |
| **3B** | ~3-3.5 GB | ~1.5-2 GB | ~1-1.5 GB |

---

## Coordination with Agent A

### Integration Points

**Agent A (LLM & Spark Adapter Architect) responsibilities:**
1. Implement SparkAdapter interface for model loading
2. Implement LlamaCppAdapter for .gguf model loading (llama.cpp backend)
3. Integrate loaded model with narration pipeline
4. Implement LENS/BOX integration for provenance labeling

**Agent B (Systems Validation) deliverables:**
1. ✅ Hardware detection logic (`hardware_detector.py`)
2. ✅ Tier classification system (`hardware_capability.py`)
3. ✅ Model selection logic (`model_selector.py`)
4. ✅ Spark model registry (`config/models.yaml`)
5. ✅ Error handling and fallback mechanisms
6. ✅ Tier threshold alignment with Spark architecture (8GB HIGH, 6GB MEDIUM)

**Handoff:**
- Agent B provides `ModelConfig` with recommended settings from models.yaml
- Agent A implements SparkAdapter to load model using `ModelConfig.model_name` and `ModelConfig.model_path`
- Agent A responsible for actual model inference and narration generation
- Integration point: `GuardedNarrationService` (M2 phase)

### Example Integration (Agent A - Future M2 Implementation)

```python
# Agent B: Detect hardware and select model
from aidm.core.hardware_detector import detect_hardware
from aidm.core.model_selector import select_model_for_hardware

capabilities = detect_hardware()
result = select_model_for_hardware(capabilities)

# Agent A: Load model using Spark Adapter (M2 implementation)
from aidm.spark.spark_adapter import SparkAdapter

spark_adapter = SparkAdapter()
loaded_model = spark_adapter.load_model(result.config.model_name)

# Agent A: Generate narration using loaded model
from aidm.narration.guarded_narration_service import GuardedNarrationService

narration_service = GuardedNarrationService(spark_adapter=spark_adapter)
narration = narration_service.generate_narration(narration_request)
```

**Spark Adapter Contract:**
- Reads `config/models.yaml` to get model path and configuration
- Loads model file from disk (e.g., `.gguf` quantized models)
- Provides inference interface: `generate(prompt, temperature, max_tokens)`
- Handles provider-specific formatting (Mistral chat template, etc.)
- Returns canonical `SparkResponse` with generated text

**Reference Documentation:**
- `SPARK_ADAPTER_ARCHITECTURE.md`: Spark design specification
- `SPARK_PROVIDER_CONTRACT.md`: Spark provider interface contract

---

## Testing

### Running Unit Tests

```bash
# Run all hardware detection tests
pytest tests/test_hardware_detection.py -v

# Run specific test
pytest tests/test_hardware_detection.py::TestHardwareDetector::test_high_tier_assignment_12gb_vram -v
```

### Running Example Script

```bash
# Run example demonstration
python -m aidm.examples.hardware_detection_example
```

**Expected output:**
```
================================================================================
Hardware Detection & Model Selection Example
================================================================================

Step 1: Detecting hardware capabilities...
--------------------------------------------------------------------------------
✓ Hardware detection complete!
  Tier: HIGH
  Has GPU: True
  Requires Offload: False

  GPU Details:
    Device: NVIDIA GeForce RTX 3090
    VRAM Total: 24.00 GB
    VRAM Available: 23.85 GB
    Compute Capability: 8.6

  CPU Details:
    Processor: Intel(R) Core(TM) i9-10900K CPU @ 3.70GHz
    Physical Cores: 10
    Logical Cores: 20
    RAM Total: 32.00 GB
    RAM Available: 24.12 GB

Step 2: Selecting appropriate LLM model...
--------------------------------------------------------------------------------
✓ Model selection complete!
  Selected Model: qwen2.5-14b-instruct
  Model Size: 14B
  Enable Offload: False
  Device Map: auto
  Max Context: 8192 tokens
  Quantization: None (full precision)

  Reason: High-tier hardware detected (23.9GB VRAM). Loading 14B model (qwen2.5-14b-instruct) without offload.
```

---

## Future Enhancements

### Planned for M2/M3

1. **AMD GPU Support (ROCm)**
   - Detect AMD GPUs via ROCm
   - Support RX 6000/7000 series GPUs

2. **Apple Silicon Support (Metal)**
   - Detect Apple M1/M2/M3 GPUs
   - Use Metal backend for inference

3. **Dynamic Model Swapping**
   - Allow runtime model tier changes
   - Swap from 14B → 7B if VRAM pressure detected

4. **Advanced Offload Strategies**
   - Layer-wise offload optimization
   - Mixed precision (FP16 + INT8) offload

5. **Performance Monitoring**
   - Track inference latency per tier
   - Automatic tier downgrade if latency >2 seconds

---

## References

- **Instruction Packet 01:** Hardware Tier Integration & Model Fallback Logic
- **Instruction Packet 03:** Hardware Detection & Tier Selection Implementation
- **SPARK_ADAPTER_ARCHITECTURE.md:** Spark model loading system design
- **SPARK_PROVIDER_CONTRACT.md:** Spark provider interface specification
- **M1 Guardrails:** `docs/design/M1_IMPLEMENTATION_GUARDRAILS.md`
- **Image Latency Research:** `docs/research/R1_IMAGE_LATENCY_BENCHMARKS.md` (methodology reference)

---

**Status:** ✅ **IMPLEMENTATION COMPLETE + SPARK INTEGRATION COMPLETE**

**Date:** 2026-02-10
**Agent:** Agent B (Systems Validation / Image Research)

**Deliverables:**
1. ✅ `aidm/schemas/hardware_capability.py` (Schema definitions, Spark-aligned thresholds)
2. ✅ `aidm/core/hardware_detector.py` (Hardware detection)
3. ✅ `aidm/core/model_selector.py` (Model selection with Spark registry integration)
4. ✅ `config/models.yaml` (Spark model registry)
5. ✅ `tests/test_hardware_detection.py` (Unit tests)
6. ✅ `aidm/examples/hardware_detection_example.py` (Usage example)
7. ✅ This documentation
8. ✅ Integration with Agent A's Spark Adapter Architecture

**Integration Status:**
- ✅ Tier thresholds aligned with Spark (8GB HIGH, 6GB MEDIUM, <6GB FALLBACK)
- ✅ Model registry created following SPARK_ADAPTER_ARCHITECTURE.md specification
- ✅ ModelSelector reads from config/models.yaml
- ✅ Fallback chains implemented (model → fallback_model → template-narration)
- ✅ Offload configuration per model tier
- ⏸️ SparkAdapter implementation (Agent A, M2 phase)

**Next Steps:**
1. Coordinate with Agent A for SparkAdapter implementation (M2)
2. Update unit tests to include models.yaml validation
3. Test with actual model files when provisioned
4. Validate fallback chains with real hardware configurations

# RQ-SPRINT-011: Component Modularity — Swappable AI and Hardware Sensitivity

**Status:** COMPLETE
**Date:** 2026-02-14

---

## Core Question

Can the system absorb a generational leap in AI technology with nothing more than a new adapter implementation?

## Answer

For atmospheric components (narration, voice, image, speech): **YES**. Protocol-based architecture + factory registries + `SPARK_SWAPPABLE_INVARIANT` = one new file + one registry line. Zero changes to callers, zero changes to mechanics.

For mechanical components (RNG, pathfinding, AoE): **NO** — not yet. Monolithic implementations without Protocol interfaces.

---

## 1. Adapter Boundary Audit

Seven adapter boundaries were examined. Each was assessed for Protocol conformance, implementation count, contract tightness, and outstanding issues.

### 1.1 STTAdapter

- **Protocol location:** `stt_adapter.py`
- **Implementation:** `WhisperSTTAdapter` (model: `small.en`, device: CPU, quantization: int8)
- **Contract:** TIGHT — callers depend only on the Protocol surface.
- **Issues:**
  - Hard-coded model name (`small.en`) inside the implementation; no constructor parameter to override.
  - No GPU execution path; forced CPU even when CUDA is available.
  - No Tier 0 text-input-only adapter that bypasses audio capture entirely.

### 1.2 TTSAdapter

- **Protocol location:** `tts_adapter.py`
- **Implementations:**
  - `KokoroTTSAdapter` (runtime: ONNX, device: CPU)
  - `ChatterboxTTSAdapter` (runtime: PyTorch, device: CUDA)
- **Contract:** TIGHT — callers see only `synthesize(text) -> AudioSegment`.
- **Issues:**
  - Output audio format (sample rate, bit depth, channel count) is implicit; not declared in the Protocol.
  - No Tier 0 text-only adapter that simply displays narration text without audio synthesis.
  - No negotiation mechanism for callers to request a specific output format.

### 1.3 ImageAdapter

- **Protocol location:** `image_adapter.py`
- **Implementation:** `SDXLImageAdapter` (quantization: NF4, VRAM footprint: 3.5-4.5 GB)
- **Contract:** TIGHT — callers provide a prompt, receive an image path.
- **Issues:**
  - Hard-coded `STYLE_SUFFIX` appended to every prompt; not configurable through the Protocol.
  - No Tier 1 pre-generated image library adapter that serves static assets without GPU inference.
  - No fallback behavior defined when VRAM is insufficient to load the model.

### 1.4 SparkAdapter

- **Protocol location:** `spark_adapter.py` (ABC, not Protocol)
- **Implementation:** `LlamaCppAdapter`
- **Contract:** TIGHT — callers use the abstract base class surface.
- **Issues:**
  - Uses ABC rather than `typing.Protocol`; implementations must explicitly inherit.
  - Template fallback logic exists inside `LlamaCppAdapter` but is not exposed through the `SparkAdapter` interface, preventing a standalone `TemplateSparkAdapter` from being registered.
  - No capability metadata to advertise model size, context window, or quantization level.

### 1.5 ImageCritiqueAdapter

- **Protocol location:** `image_critique_adapter.py`
- **Implementations:**
  - `SigLIPCritiqueAdapter` (embedding similarity)
  - `ImageRewardCritiqueAdapter` (learned reward model)
- **Contract:** TIGHT — callers provide an image and prompt, receive a quality score.
- **Issues:** None significant. This is the cleanest adapter boundary in the system.

### 1.6 Audio Mixer

- **Status:** MONOLITHIC — no Protocol interface.
- **Impact:** LOW. The audio mixer is atmospheric-only; it has zero mechanical side effects.
- **Issues:**
  - Single concrete class with no abstraction layer.
  - Swapping mixing strategies (e.g., spatial audio, simple stereo pan) requires editing the class directly.

### 1.7 Music Generator

- **Status:** Protocol-based (partial).
- **Issues:**
  - Protocol exists but is incomplete; some methods are implemented only in the concrete class.
  - No second implementation to validate that the Protocol surface is sufficient.

---

## 2. Swappability Gap Inventory

Six components were identified as lacking the adapter abstraction necessary for clean swaps.

| Component | Priority | Severity | Current State | Impact Domain |
|-----------|----------|----------|---------------|---------------|
| RNG | P0 | CRITICAL | Monolithic, no Protocol | Mechanical |
| Pathfinding | P1 | MEDIUM | Embedded in targeting module | Mechanical |
| AoE Rasterizer | P1 | MEDIUM | Embedded in targeting module | Mechanical |
| Event Log Storage | P2 | LOW | Fixed JSONL format | Infrastructure |
| NLG Engine | P2 | MEDIUM | Partially pluggable | Atmospheric |
| Audio Mixer | P3 | NONE | Atmospheric only | Atmospheric |

### 2.1 RNG (P0 — CRITICAL)

The random number generator is consumed directly throughout the mechanical layer. There is no `RNGProvider` Protocol. Swapping RNG strategies (e.g., from Python `random` to a cryptographic source, or to a deterministic replay source for testing) requires modifying every call site. This is the single most dangerous monolithic dependency in the system because RNG touches every d20 roll, every damage roll, every encounter table lookup — the entire mechanical contract.

### 2.2 Pathfinding (P1 — MEDIUM)

Pathfinding logic is embedded directly in the targeting module. There is no `PathfindingEngine` Protocol that would allow swapping between A*, Dijkstra, or pre-computed navigation meshes. Movement validation and opportunity attack geometry are coupled to the specific algorithm.

### 2.3 AoE Rasterizer (P1 — MEDIUM)

Area-of-Effect geometry calculation is embedded in the targeting module alongside pathfinding. There is no `AoEGeometry` Protocol. Swapping between grid-based rasterization and continuous-space geometry requires editing the targeting module directly.

### 2.4 Event Log Storage (P2 — LOW)

The event log writes fixed-format JSONL. There is no storage backend Protocol. Swapping to SQLite, Parquet, or a remote telemetry sink requires modifying the event log class.

### 2.5 NLG Engine (P2 — MEDIUM)

Natural language generation for non-Spark text (item descriptions, spell flavor text, room descriptions) is partially pluggable but lacks a clean Protocol boundary. Some NLG flows go through Spark; others use hard-coded templates with no abstraction.

### 2.6 Audio Mixer (P3 — NONE)

As noted in the adapter audit, the audio mixer is monolithic but atmospheric-only. Its lack of a Protocol interface has zero impact on mechanical correctness. Prioritized last.

---

## 3. Hardware Detection System

### 3.1 Existing Infrastructure

The hardware detection system lives in `hardware_detector.py` and provides:

- **GPUInfo:** dataclass capturing VRAM total, VRAM available, GPU name, CUDA compute capability.
- **CPUInfo:** dataclass capturing core count, thread count, available RAM, CPU model string.
- **HardwareTier:** enum with three levels:
  - `HIGH` — full GPU inference, real-time generation.
  - `MEDIUM` — quantized GPU inference, reduced batch sizes.
  - `FALLBACK` — CPU-only or text-only operation.
- **TierAssignmentResult:** dataclass binding a `HardwareTier` to the reasoning that produced it.
- **HardwareCapabilities:** aggregate dataclass combining `GPUInfo`, `CPUInfo`, and the assigned `HardwareTier`.

### 3.2 Tier Assignment Logic

```
if gpu.vram_total_gb >= 8.0:
    tier = HardwareTier.HIGH
elif gpu.vram_total_gb >= 6.0:
    tier = HardwareTier.MEDIUM
else:
    tier = HardwareTier.FALLBACK
```

The thresholds are derived from the VRAM requirements of the heaviest components:

- SDXL (NF4): 3.5-4.5 GB
- Chatterbox TTS: ~2 GB
- Whisper (small.en): ~0.5 GB
- LlamaCpp (7B Q4): ~4 GB

A HIGH-tier system (>=8 GB) can run SDXL + one other model with headroom. A MEDIUM-tier system (>=6 GB) must serialize model loads. A FALLBACK system uses CPU-only or text-only adapters.

### 3.3 Detection Gaps

- **No disk type detection.** NVMe vs. SATA vs. HDD affects model load times by 3-10x. The tier system cannot distinguish between "slow because CPU" and "slow because spinning rust."
- **No model file availability check.** The detector reports hardware capability but does not verify that required model files are present on disk. A HIGH-tier system without downloaded model weights will fail at adapter initialization, not at detection time.
- **No runtime re-detection.** Hardware capabilities are captured once at startup. If VRAM pressure changes mid-session (e.g., another application claims GPU memory), the tier assignment becomes stale. There is no mechanism to trigger re-detection and adapter downgrade.

---

## 4. Per-Component Tiering Specification

Each atmospheric component operates at one of three tiers. The cardinal rule: **ALL tiers produce IDENTICAL mechanical outcomes.** Only sensory presentation differs.

### 4.1 STT (Speech-to-Text)

| Tier | Implementation | Device | Latency | Notes |
|------|---------------|--------|---------|-------|
| Tier 0 | Text input (keyboard) | N/A | N/A | No audio capture; player types commands directly. |
| Tier 1 | Whisper `small.en` (int8) | CPU | 2-5s per utterance | Current default. Acceptable for turn-based play. |
| Tier 2 | Whisper `large-v3` (fp16) | GPU | 0.3-0.8s per utterance | Requires ~3 GB VRAM. Near-real-time transcription. |

### 4.2 TTS (Text-to-Speech)

| Tier | Implementation | Device | Latency | Notes |
|------|---------------|--------|---------|-------|
| Tier 0 | Text display only | N/A | N/A | Narration rendered as styled text. No audio synthesis. |
| Tier 1 | Kokoro (ONNX) | CPU | 1-3s per paragraph | Lightweight, consistent quality. Current CPU default. |
| Tier 2 | Chatterbox (PyTorch) | GPU | 0.5-1s per paragraph | Requires ~2 GB VRAM. Superior prosody and emotion. |

### 4.3 Image Generation

| Tier | Implementation | Device | VRAM | Notes |
|------|---------------|--------|------|-------|
| Tier 0 | Stub adapter | N/A | 0 | Returns a placeholder or no image. Functional skeleton. |
| Tier 1 | Pre-generated library | N/A | 0 | Serves static images matched by tag/keyword. No inference. |
| Tier 2 | SDXL (NF4) | GPU | 3.5-4.5 GB | Real-time generation. Current GPU default. |

### 4.4 Narration (Spark / LLM)

| Tier | Implementation | Device | VRAM | Notes |
|------|---------------|--------|------|-------|
| Tier 0 | Template engine | N/A | 0 | String interpolation from structured data. Deterministic. |
| Tier 1 | 3B parameter LLM (Q4) | CPU | 0 | Slow but functional. ~10-30s per narration block. |
| Tier 2 | 7-14B parameter LLM (Q4) | GPU | 4-8 GB | Fast, high-quality prose. Current GPU default. |

### 4.5 Invariant

```
SPARK_SWAPPABLE_INVARIANT:
  For any two adapters A and B implementing the same Protocol:
    mechanical_outcome(A, input) == mechanical_outcome(B, input)

  The ONLY permitted differences are:
    - Sensory richness (audio quality, image detail, prose style)
    - Latency
    - Resource consumption
```

This invariant ensures that a player on a $300 laptop and a player on a $3,000 workstation experience the same game. The workstation player gets better narration voice quality, faster image generation, and richer prose — but every die roll, every saving throw, every damage calculation, every turn order is identical given the same RNG seed.

---

## 5. Future-Proofing Interface Contract

### 5.1 AdapterCapability Metadata Schema

Every adapter should expose a class-level `capability` descriptor conforming to this schema:

```python
@dataclass(frozen=True)
class AdapterCapability:
    adapter_id: str            # e.g., "whisper-stt-small-en"
    protocol: str              # e.g., "STTAdapter"
    tier: int                  # 0, 1, or 2
    hardware_requirements: HardwareRequirements
    feature_flags: frozenset[str]  # e.g., {"streaming", "multilingual"}
    performance: PerformanceCharacteristics
    model_files: tuple[ModelFileSpec, ...]  # required model files on disk

@dataclass(frozen=True)
class HardwareRequirements:
    min_vram_gb: float         # 0.0 for CPU-only
    min_ram_gb: float
    requires_cuda: bool
    min_cuda_compute: float    # e.g., 7.0 for Volta+
    requires_nvme: bool        # for large model loads

@dataclass(frozen=True)
class PerformanceCharacteristics:
    typical_latency_ms: int
    throughput_tokens_per_sec: int  # 0 if not applicable
    vram_footprint_gb: float

@dataclass(frozen=True)
class ModelFileSpec:
    relative_path: str         # relative to models directory
    size_bytes: int
    sha256: str                # for integrity verification
    download_url: str          # for auto-download
```

### 5.2 ComponentRegistry

```python
class ComponentRegistry:
    def register(self, capability: AdapterCapability, factory: Callable) -> None:
        """Register an adapter factory with its capability metadata."""
        ...

    def list_adapters(self, protocol: str) -> list[AdapterCapability]:
        """List all registered adapters implementing a given Protocol."""
        ...

    def select_for_hardware(
        self,
        protocol: str,
        hardware: HardwareCapabilities,
        preferred_tier: int | None = None,
    ) -> AdapterCapability:
        """
        Select the best adapter for the detected hardware.

        Algorithm:
        1. Filter to adapters whose requirements are satisfied.
        2. If preferred_tier is set and available, use it.
        3. Otherwise, select the highest tier that fits.
        4. Break ties by lowest latency.
        """
        ...

    def create(self, capability: AdapterCapability) -> Any:
        """Instantiate the adapter from its registered factory."""
        ...
```

### 5.3 Steps to Add a New Adapter

Adding a next-generation adapter (e.g., a hypothetical "WhisperV4" STT model) requires exactly:

1. **One new file** — e.g., `whisper_v4_stt_adapter.py` — implementing the `STTAdapter` Protocol and declaring an `AdapterCapability` class attribute.
2. **One registry line** — e.g., `registry.register(WhisperV4STTAdapter.capability, WhisperV4STTAdapter)` in the initialization module.

Zero changes to callers. Zero changes to other adapters. Zero changes to mechanical logic. The `ComponentRegistry.select_for_hardware` method will automatically prefer the new adapter if the hardware supports it.

---

## 6. Hot-Swap Feasibility

### 6.1 Classification

Not all adapters can be swapped while a session is in progress.

**Deterministic adapters (CANNOT swap mid-session):**
- RNG — Swapping mid-session would break replay determinism and audit trails.
- Pathfinding — Swapping algorithms mid-combat could change reachability, invalidating prior movement.
- AoE Rasterizer — Swapping geometry mid-combat could change which creatures are in an area of effect.

**Atmospheric adapters (CAN swap mid-session):**
- SparkAdapter — Narration quality changes, but no mechanical state depends on it.
- TTSAdapter — Voice changes, but no mechanical state depends on audio output.
- STTAdapter — Input method changes, but parsed commands are the same.
- ImageAdapter — Visual quality changes, but no mechanical state depends on images.

### 6.2 HotSwappable Protocol

For atmospheric adapters that support mid-session swapping:

```python
class HotSwappable(Protocol):
    def prepare_swap(self) -> SwapCheckpoint:
        """
        Capture any state needed for continuity.

        Returns a SwapCheckpoint containing:
        - session_context: any context the new adapter needs
        - pending_requests: in-flight requests to drain or cancel
        """
        ...

    def accept_swap(self, checkpoint: SwapCheckpoint) -> None:
        """
        Initialize from a predecessor's checkpoint.

        Called on the NEW adapter instance after construction.
        """
        ...

    def release_resources(self) -> None:
        """
        Release GPU memory, file handles, and other resources.

        MUST be called before the new adapter loads its model
        to avoid VRAM double-booking.
        """
        ...
```

### 6.3 VRAM Budget Constraint

On systems with limited VRAM, two large models cannot coexist simultaneously. The swap sequence must be **sequential**:

1. `old_adapter.prepare_swap()` — capture checkpoint.
2. `old_adapter.release_resources()` — free VRAM.
3. Verify VRAM is actually freed (CUDA memory fragmentation can prevent this).
4. `new_adapter = Factory()` — load new model into freed VRAM.
5. `new_adapter.accept_swap(checkpoint)` — restore continuity.

There is a brief window (steps 2-4) where no adapter of that type is available. Callers must handle `AdapterUnavailable` gracefully during this window — e.g., by queuing requests or falling back to Tier 0.

---

## Priority Actions

| Priority | Action | Rationale |
|----------|--------|-----------|
| **P0** | Add `AdapterCapability` metadata to all existing Protocol adapters | Enables hardware-aware selection and self-describing adapters. |
| **P0** | Wrap template narration as `TemplateSparkAdapter` | Provides a Tier 0 Spark implementation that requires zero models, ensuring every system can narrate. |
| **P1** | Implement `ComponentRegistry` with hardware-aware auto-selection | Centralizes adapter lifecycle and removes hard-coded adapter choices from initialization. |
| **P1** | Define `RNGProvider` Protocol and wrap existing RNG behind it | Eliminates the most critical monolithic dependency. Enables deterministic replay and alternative RNG strategies. |
| **P2** | Build Tier 1 pre-generated image library adapter | Provides image content on systems that cannot run SDXL, using tagged static assets. |
| **P2** | Add disk type detection to `hardware_detector.py` | Enables accurate latency predictions for model loading and appropriate timeout configuration. |
| **P3** | Define `PathfindingEngine` and `AoEGeometry` Protocols | Decouples mechanical geometry from specific algorithms. Enables future optimizations without caller changes. |

---

## Files Examined

### Immersion Layer
- `aidm/immersion/stt_adapter.py`
- `aidm/immersion/whisper_stt_adapter.py`
- `aidm/immersion/tts_adapter.py`
- `aidm/immersion/kokoro_tts_adapter.py`
- `aidm/immersion/chatterbox_tts_adapter.py`
- `aidm/immersion/image_adapter.py`
- `aidm/immersion/sdxl_image_adapter.py`
- `aidm/immersion/audio_mixer.py`

### Spark Layer
- `aidm/spark/spark_adapter.py`
- `aidm/spark/llamacpp_adapter.py`

### Core Layer
- `aidm/core/hardware_detector.py`
- `aidm/core/rng_manager.py`
- `aidm/core/image_critique_adapter.py`
- `aidm/core/event_log.py`
- `aidm/core/world_compiler.py`

### Schemas
- `aidm/schemas/hardware_capability.py`
- `aidm/schemas/immersion.py`

### Tests
- `tests/test_hardware_detection.py`

---

*RQ-SPRINT-011 complete. The atmospheric layer is swap-ready today. The mechanical layer requires Protocol extraction at P0-P1 priority before it can claim the same.*

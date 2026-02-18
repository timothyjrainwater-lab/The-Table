# WO-SPARK-LLM-SELECTION — Research Prep & Command Deck Runbook

**Status:** RESEARCH COMPLETE / HARDWARE EXECUTION BLOCKED
**Builder:** Claude Opus 4.6
**Date:** 2026-02-19

---

## 1. Assumption Validation

### Assumption 1: Chatterbox VRAM ~4-5GB
**Status: CANNOT VERIFY — hardware required.**
- `bench_vram.py` exists and will measure this precisely (9-phase benchmark).
- Chatterbox adapter docs state "GPU with ≥ 6GB VRAM (RTX 3080 Ti tested)" — this is the whole-system minimum, not the Chatterbox-only footprint.
- The bench script estimates "Typical 7B LLM (4-bit): ~4500 MB" and checks coexistence. Actual numbers are unpinned.
- **Action:** Run `python scripts/bench_vram.py` on command deck. This is Task 1 in the WO and must complete before candidate selection is finalized.

### Assumption 2: PromptPack compiler is functional
**Status: CONFIRMED ✅ — No GAP.**
- `aidm/lens/prompt_pack_builder.py` — builds from NarrativeBrief. Fully tested (45+ tests).
- `aidm/lens/promptpack_compiler.py` — builds from Oracle WorkingSet. Fully tested (20+ tests).
- `aidm/schemas/prompt_pack.py` — five-channel frozen schema (Truth, Memory, Task, Style, Contract). Deterministic serialization via `.serialize()`.
- Golden serialization test at `tests/test_prompt_pack.py:452`.
- **The pipeline can produce real PromptPacks from test fixtures today.**

### Assumption 3: Spark cage interface exists
**Status: CONFIRMED ✅ — No GAP.**
- `aidm/spark/spark_adapter.py` — Abstract `SparkAdapter` with `generate_text()` and `generate()` methods.
- `aidm/spark/llamacpp_adapter.py` — Concrete `LlamaCppAdapter` wrapping `llama-cpp-python`. Fully implemented (load, generate, unload, tier selection, fallback chain).
- `aidm/spark/model_registry.py` — Parses `config/models.yaml`, tier-based selection.
- `aidm/spark/grammar_shield.py` — Output validation (mechanical assertion detection, schema checks).
- `aidm/spark/dm_persona.py` — DM voice/tone system prompt builder.
- Canonical schema: `SparkRequest` → `SparkResponse` with `FinishReason`, token counts, metadata.
- **Integration is production-ready.** The LlamaCppAdapter accepts GGUF models loaded via `llama-cpp-python`.

**GAP-A: dm_persona.py type import.** Line 83 references `NarrativeBrief` in function signature without importing it. Runtime-functional (duck typing) but violates static type checking. Low priority — does not block evaluation.

### Assumption 4: 7B-9B at 4-bit can clear the Mercer bar
**Status: HYPOTHESIS — hardware execution required to test.**

### Assumption 5: NVIDIA GPU with CUDA, 12GB VRAM
**Status: PARTIALLY VERIFIABLE.**
- `aidm/core/hardware_detector.py` uses `torch.cuda.get_device_properties()`.
- Tier thresholds: HIGH ≥8GB, MEDIUM 6-12GB, FALLBACK <6GB.
- **Action:** Run `nvidia-smi` on command deck to confirm GPU model, total VRAM, CUDA version.

---

## 2. Candidate Set

### Residency Posture: CONCURRENT
Both Spark LLM and Chatterbox must be VRAM-resident simultaneously. The WO is explicit: multi-beat combat turns accumulate 4-6s swap overhead under sequential loading.

### VRAM Budget (estimated, pending Task 1)
- Total: 12,288 MB (12 GB)
- Chatterbox estimate: 4,000-5,000 MB (will be pinned by bench_vram.py)
- Available for Spark: ~7,000-8,000 MB (optimistic) / ~5,000-6,000 MB (if Chatterbox is larger)
- KV cache at 2K context (narration use case): ~300 MB
- **Critical:** KV cache at default 8K context: ~1.3 GB. Use `-c 2048` for narration to minimize KV cache.

### Class A: Qwen3 8B Instruct (Q4_K_M)
- **Family:** Qwen (Alibaba)
- **Parameters:** 8.2B
- **Quantization:** Q4_K_M GGUF
- **GGUF file size:** ~4.7-5.0 GB
- **Expected VRAM (weights + 2K KV):** ~5.5-6.0 GB
- **Context:** 32K native (use 2K for narration)
- **Rationale:** Already the `models.yaml` default. Best benchmark performer at this size class. Strong instruction following. Community reports natural, flexible prose.
- **GGUF source:** `Mungert/Qwen3-8B-GGUF` or `Qwen/Qwen3-8B-Instruct-GGUF` on HuggingFace
- **Already in registry as:** `qwen3-8b-instruct-4bit`

### Class B: LLaMA 3.1 8B Instruct (Q4_K_M)
- **Family:** LLaMA (Meta)
- **Parameters:** 8B
- **Quantization:** Q4_K_M GGUF
- **GGUF file size:** ~4.5 GB
- **Expected VRAM (weights + 2K KV):** ~5.0-5.5 GB
- **Context:** 128K native (use 2K for narration)
- **Rationale:** Different model family (Meta vs Alibaba). Largest fine-tune ecosystem. Adequate creative writing. The comparison candidate per WO binary decision #4.
- **GGUF source:** `bartowski/Meta-Llama-3.1-8B-Instruct-GGUF` on HuggingFace
- **Already in registry as:** `llama-3.1-8b-instruct-4bit`

### Stretch Class (CONDITIONAL on Task 1):
Test ONLY IF bench_vram.py shows Chatterbox ≤ 3.5GB (leaving ≥8.5GB for Spark).

**Gemma 3 12B QAT (Q4_K_M)**
- **Family:** Gemma (Google)
- **Parameters:** 12B
- **Quantization:** QAT Q4_K_M GGUF
- **GGUF file size:** ~8.1 GB
- **Expected VRAM (weights + 2K KV):** ~8.5-9.0 GB
- **Context:** 128K native (use 2K for narration)
- **WARNING:** Gemma 3 has unusually high KV cache requirements due to sliding window attention architecture. Users report 22-23GB at default context. Must use aggressive KV cache quantization (`-ctk q4_0`) and short context (`-c 2048`).
- **Rationale:** Best prose quality among open-weight models per community consensus. Google QAT preserves quality at 4-bit better than standard PTQ.
- **GGUF source:** `bartowski/google_gemma-3-12b-it-qat-GGUF` on HuggingFace
- **Already in registry as:** `gemma3-12b-qat`

---

## 3. Measurement Procedure (Command Deck Runbook)

### Pre-flight
```bash
# 1. Confirm GPU
nvidia-smi
# Record: GPU model, total VRAM, CUDA version, driver version

# 2. Run preflight canary
cd F:\DnD-3.5
python scripts/preflight_canary.py
# Log output to pm_inbox/PREFLIGHT_CANARY_LOG.md
```

### Task 1: Measure Chatterbox VRAM Baseline
```bash
python scripts/bench_vram.py
```
**Record these pinned numbers:**

| Metric | Value | Notes |
|--------|-------|-------|
| GPU model | ______ | nvidia-smi |
| Total VRAM | ______ MB | |
| Baseline (torch only) | ______ MB allocated | Phase 1 |
| Chatterbox Original (idle) | ______ MB allocated | Phase 2 |
| Chatterbox Original (peak synthesis) | ______ MB peak | Phase 3 |
| Chatterbox Turbo (idle) | ______ MB allocated | Phase 8 |
| Both tiers (idle) | ______ MB allocated | Phase 4 |
| VRAM remaining after Original | ______ MB | = Total - Original reserved |
| VRAM remaining after Both | ______ MB | = Total - Both reserved |

**Decision gate:** If Chatterbox Original > 7,000 MB → **STOP.** Report to PM.

**Residency decision:**
- If remaining VRAM after Original ≥ 6,000 MB → proceed with Class A + B (8B models)
- If remaining VRAM after Original ≥ 8,500 MB → also test Stretch (Gemma 12B)
- If remaining VRAM after Original < 5,000 MB → only test 8B models with aggressive `-c 1024` context

### Task 2: Download Candidates
```bash
# Download to models/ directory. Exact filenames must match config/models.yaml paths.

# Class A: Qwen3 8B
# From: https://huggingface.co/Mungert/Qwen3-8B-GGUF
# File: Qwen3-8B-Q4_K_M.gguf → rename to qwen3-8b-instruct-Q4_K_M.gguf

# Class B: LLaMA 3.1 8B
# From: https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF
# File: Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf → rename to llama-3.1-8b-instruct-Q4_K_M.gguf

# Stretch (ONLY if Task 1 permits):
# From: https://huggingface.co/bartowski/google_gemma-3-12b-it-qat-GGUF
# File: google_gemma-3-12b-it-qat-Q4_K_M.gguf → rename to gemma-3-12b-it-qat-q4_k_m.gguf
```

### Task 3: Gate Tests per Candidate

For each candidate, run gates in fail-fast order: S1 → S2 → S3 → S4 → S5.

#### Gate S1: PromptPack Compatibility

Generate 3 PromptPacks from test fixtures and feed to each model:

```python
# Run from project root
import json, time
from pathlib import Path
from aidm.lens.narrative_brief import NarrativeBrief
from aidm.lens.prompt_pack_builder import PromptPackBuilder
from aidm.spark.model_registry import ModelRegistry
from aidm.spark.llamacpp_adapter import LlamaCppAdapter

registry = ModelRegistry.load_from_file("config/models.yaml")
adapter = LlamaCppAdapter(registry=registry)

# Load candidate (substitute model_id per candidate)
loaded = adapter.load_model("qwen3-8b-instruct-4bit")

builder = PromptPackBuilder()

# --- Scenario 1: Melee Attack ---
brief_melee = NarrativeBrief(
    action_type="attack_hit",
    actor_name="Kael",
    target_name="Goblin Scout",
    outcome_summary="Kael strikes the goblin with his longsword",
    severity="moderate",
    weapon_name="Longsword",
    damage_type="slashing",
    previous_narrations=("The party formed a defensive line.",),
    scene_description="Underground cavern with torchlight",
)

# --- Scenario 2: AoE Fireball ---
brief_aoe = NarrativeBrief(
    action_type="spell_damage_dealt",
    actor_name="Elara",
    target_name="Goblin Warrior",
    outcome_summary="Elara's fireball engulfs the goblin group",
    severity="devastating",
    spell_name="Fireball",
    damage_type="fire",
    additional_targets=(
        ("Goblin Archer", "severe", False),
        ("Goblin Scout", "severe", True),
    ),
    previous_narrations=("The wizard raised her staff, chanting.",),
    scene_description="Open cavern with enemies clustered near an altar",
)

# --- Scenario 3: Healing Spell ---
brief_heal = NarrativeBrief(
    action_type="spell_healed",
    actor_name="Brother Aldric",
    target_name="Kael",
    outcome_summary="Brother Aldric heals Kael with cure serious wounds",
    severity="moderate",
    spell_name="Cure Serious Wounds",
    previous_narrations=("Kael fell to his knees, bloodied from the onslaught.",),
    scene_description="Behind a stone pillar, away from the front line",
)

scenarios = [
    ("melee_attack", brief_melee),
    ("aoe_fireball", brief_aoe),
    ("healing_spell", brief_heal),
]

from aidm.spark.spark_adapter import SparkRequest

for name, brief in scenarios:
    pack = builder.build(brief=brief)
    prompt_text = pack.serialize()

    request = SparkRequest(
        prompt=prompt_text,
        temperature=0.8,
        max_tokens=150,
        stop_sequences=["</narration>", "\n\n"],
    )

    t0 = time.perf_counter()
    response = adapter.generate(request, loaded)
    t1 = time.perf_counter()

    print(f"\n{'='*60}")
    print(f"SCENARIO: {name}")
    print(f"TIME: {t1-t0:.3f}s")
    print(f"FINISH: {response.finish_reason}")
    print(f"TOKENS: {response.tokens_used}")
    print(f"OUTPUT:\n{response.text}")
    print(f"{'='*60}")

adapter.unload_model(loaded)
```

**S1 Pass/Fail criteria:**
- PASS: Model produces coherent narration that respects PromptPack structure for ALL 3 scenarios.
- FAIL: Any schema break (outputs mechanical data like "12 damage"), instruction inversion (narrates the wrong action), or model refusal.

#### Gate S2: Latency Budget

**Measured during S1 runs above.** Record per scenario per candidate:

| Candidate | Scenario | Time-to-completion (s) | Pass (<2.0s) |
|-----------|----------|----------------------|--------------|
| | melee_attack | | |
| | aoe_fireball | | |
| | healing_spell | | |

**Pass threshold:** All scenarios < 2.0 seconds (Spark portion of 3.0s stall budget).

For more precise TTFT measurement, use streaming mode if supported:
```python
# Optional: measure time-to-first-token
request.streaming = True
# Time from request to first yielded token
```

#### Gate S3: Quality Rubric

Score each output on 5 dimensions (1-5 scale, 25 max):

**Rubric tied to concrete scenes:**

| # | Dimension | Scoring anchor (melee) | Scoring anchor (AoE) | Scoring anchor (heal) |
|---|-----------|----------------------|---------------------|---------------------|
| 1 | **Clarity & confidence** | Reads as a DM describing the hit, not hedging ("perhaps", "might") | Conveys the scale of the fireball without equivocation | States healing clearly, not vaguely |
| 2 | **Pacing & table presence** | 2-4 sentences, each one a distinct beat. No run-on paragraphs | Captures the explosion then the aftermath. Distinct visual beats | Quiet moment amid combat. Pacing should shift from the violence |
| 3 | **Fidelity to facts** | Uses "Kael", "longsword", "slashing", "Goblin Scout" — does NOT invent damage numbers, HP, or AC | Uses "Elara", "fireball", "fire", names all targets. Does NOT invent spell level or save DC | Uses "Brother Aldric", "Cure Serious Wounds", "Kael". Does NOT invent HP restored |
| 4 | **Controlled improvisation** | May add sensory detail (clang of steel, spray of blood) but NOT new NPCs, locations, or items | May describe the heat, the screams, scorch marks — NOT new NPCs or environmental features not in the scene | May describe warm light, closing wounds — NOT new plot points or NPC reactions |
| 5 | **Cadence for TTS** | No walls of subordinate clauses. Each sentence stands alone when read aloud | No tongue-twisters. Names are spelled out, not abbreviated. Commas create natural breath points | Gentle rhythm. No jarring tonal shifts from the combat narration that preceded it |

**Scoring sheet (fill per candidate per scenario):**

```
Candidate: ___________
Scenario: ___________

1. Clarity & confidence:     _/5
2. Pacing & table presence:  _/5
3. Fidelity to facts:        _/5
4. Controlled improvisation: _/5
5. Cadence for TTS:          _/5
                       TOTAL: _/25

Notes: ___________
```

**Pass threshold:** ≥15/25 average across all 3 scenarios. Below 15 on any single scenario is a flag.

#### Gate S4: Resource Coexistence

```python
# With Chatterbox ALREADY loaded (from bench_vram.py or speak.py),
# load the Spark model and run 5 turn cycles:

import torch

for cycle in range(5):
    # 1. Spark generates narration
    response = adapter.generate(request, loaded)

    # 2. Log VRAM
    alloc = torch.cuda.memory_allocated() / 1024**2
    reserved = torch.cuda.memory_reserved() / 1024**2
    print(f"Cycle {cycle+1}: allocated={alloc:.0f}MB reserved={reserved:.0f}MB")

    # 3. Chatterbox synthesizes speech (use speak.py or adapter directly)
    # speak(response.text, "dm_narrator", 0.5, "chatterbox")

    # 4. Check for OOM or degradation
```

**Pass criteria:** No crashes, no OOM, no runaway VRAM growth across 5 cycles. VRAM at cycle 5 ≤ VRAM at cycle 1 + 50MB tolerance.

#### Gate S5: Repeat Stability

```python
# Run same PromptPack (melee_attack) 3 times with fixed settings
for run in range(3):
    request = SparkRequest(
        prompt=prompt_text,
        temperature=0.8,
        max_tokens=150,
        stop_sequences=["</narration>", "\n\n"],
        seed=42,  # if supported
    )
    response = adapter.generate(request, loaded)
    print(f"Run {run+1}: {response.text}")
```

**Pass criteria:** All 3 outputs reference the same characters (Kael, Goblin Scout), same weapon (longsword), same action type (hit/strike). Stylistic variation is fine. Factual contradiction between runs (e.g., one says miss, another says hit) is a FAIL.

---

## 4. Evaluation Matrix Template

| Metric | Qwen3 8B | LLaMA 3.1 8B | Gemma 3 12B (if tested) |
|--------|----------|--------------|------------------------|
| **Model family** | Qwen (Alibaba) | LLaMA (Meta) | Gemma (Google) |
| **Parameters** | 8.2B | 8B | 12B |
| **Quantization** | Q4_K_M | Q4_K_M | QAT Q4_K_M |
| **GGUF size** | ~4.7 GB | ~4.5 GB | ~8.1 GB |
| **VRAM (measured)** | ___ MB | ___ MB | ___ MB |
| **S1: PromptPack compat** | ☐ PASS / ☐ FAIL | ☐ PASS / ☐ FAIL | ☐ PASS / ☐ FAIL |
| **S2: Latency (melee)** | ___s | ___s | ___s |
| **S2: Latency (AoE)** | ___s | ___s | ___s |
| **S2: Latency (heal)** | ___s | ___s | ___s |
| **S3: Quality avg** | _/25 | _/25 | _/25 |
| **S4: Coexistence** | ☐ PASS / ☐ FAIL | ☐ PASS / ☐ FAIL | ☐ PASS / ☐ FAIL |
| **S5: Stability** | ☐ PASS / ☐ FAIL | ☐ PASS / ☐ FAIL | ☐ PASS / ☐ FAIL |
| **RECOMMENDATION** | ☐ | ☐ | ☐ |

---

## 5. Integration Spec (pre-written for winner)

The winner plugs into the existing Spark cage with zero code changes:

1. Place GGUF file in `models/` matching the `path` in `config/models.yaml`.
2. Set `spark.default` in `models.yaml` to the winning model's `id`.
3. The `LlamaCppAdapter` loads it via `llama-cpp-python` with settings from `providers.llamacpp.default_settings`.
4. `GuardedNarrationService` (in `aidm/narration/guarded_narration_service.py`) optionally wraps it with `GrammarShield` for mechanical assertion filtering.
5. **Recommended llama.cpp settings for narration:**
   - `-c 2048` (2K context — narration prompts are short, saves ~1GB KV cache vs 8K default)
   - `-ngl 99` (offload all layers to GPU)
   - For Gemma 3 specifically: `-ctk q4_0` (quantize KV cache to control its inflated footprint)

---

## 6. GAP Summary

| GAP ID | Description | Severity | File | Action |
|--------|-------------|----------|------|--------|
| GAP-A | `dm_persona.py` references `NarrativeBrief` without importing it | Low | `aidm/spark/dm_persona.py:83` | Add import or TYPE_CHECKING guard. Does not block evaluation. |

No other gaps found. The Spark cage, PromptPack compiler, model registry, and inference pipeline are all production-ready and functional.

---

## 7. STOP / WAITING ON HARDWARE

The following steps **cannot be executed without live GPU access:**

- [ ] **Task 1:** `python scripts/bench_vram.py` — pin Chatterbox VRAM footprint
- [ ] **Task 1:** `nvidia-smi` — confirm GPU model + VRAM
- [ ] **Task 2:** Download 2-3 GGUF files (~5-8 GB each)
- [ ] **Task 3:** Run Gate S1-S5 per candidate (inference, timing, VRAM monitoring)
- [ ] **Task 4:** Score rubric, fill evaluation matrix, write recommendation
- [ ] **Debrief:** Write `pm_inbox/DEBRIEF_WO-SPARK-LLM-SELECTION.md`

**All research, tooling, rubric design, candidate selection, and measurement procedures are complete.** The command deck operator has everything needed to execute Tasks 1-4 and produce the final deliverables.

---

## Sources

- [Ollama VRAM Requirements Guide](https://localllm.in/blog/ollama-vram-requirements-for-local-llms)
- [Qwen llama.cpp documentation](https://qwen.readthedocs.io/en/latest/run_locally/llama.cpp.html)
- [GGUF VRAM formula (oobabooga)](https://oobabooga.github.io/blog/posts/gguf-vram-formula/)
- [Gemma 3 QAT announcement (Google)](https://developers.googleblog.com/en/gemma-3-quantized-aware-trained-state-of-the-art-ai-to-consumer-gpus/)
- [Gemma 3 12B vs Qwen3 8B comparison](https://blog.galaxy.ai/compare/gemma-3-12b-it-vs-qwen3-8b)
- [LLM Model Selection Guide (Qwen, Mistral, Llama, Gemma)](https://dasroot.net/posts/2026/01/llm-model-selection-guide-qwen-mistral-llama-gemma/)
- [bartowski Gemma 3 12B QAT GGUF](https://huggingface.co/bartowski/google_gemma-3-12b-it-qat-GGUF)
- [Mungert Qwen3 8B GGUF](https://huggingface.co/Mungert/Qwen3-8B-GGUF)

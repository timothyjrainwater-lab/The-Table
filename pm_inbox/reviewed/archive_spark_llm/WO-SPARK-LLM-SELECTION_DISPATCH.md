# WO-SPARK-LLM-SELECTION — Local LLM Selection for Spark Cage

**Status:** DISPATCHED — AMENDED (see Addendum A below)
**Drafted by:** Slate (PM)
**Date:** 2026-02-19
**Priority:** Strategic — blocks vertical slice completion
**Audit input:** Aegis (GPT) adversarial review, 5 gates + red team

---

## Target Lock

Select and validate a local LLM for the Spark cage. The Spark cage generates combat narration, environmental description, and NPC dialogue via PromptPacks. The architecture (`SPARK_SWAPPABLE_INVARIANT`) is model-agnostic — this WO fills the empty seat.

**Product constraint:** Fully local, offline-capable execution. No API dependency. This is doctrine (GT v12, `LOCAL_RUNTIME_PACKAGING_STRATEGY.md`).

**VRAM constraint:** Concurrent residency with Chatterbox TTS on a 12GB GPU. Chatterbox footprint is estimated at ~4-5GB. Builder MUST measure actual Chatterbox VRAM footprint as the first task — all model class decisions depend on this number.

**Stall budget:** 3.0 seconds maximum from intent submission to first audio output (Spark generation + Chatterbox synthesis + playback start). This is the Mercer-bar latency threshold. Set before testing, not after.

---

## Binary Decisions

1. **API or local?** LOCAL. API is ruled out by offline doctrine. Not a variable.

2. **Concurrent or sequential VRAM?** CONCURRENT. Both Spark and Chatterbox must be resident in VRAM simultaneously. Rationale: multi-beat combat turns (attack → damage → condition) would accumulate 4-6s of swap overhead per beat under sequential loading. That kills table flow. If the builder discovers during Task 1 (VRAM measurement) that swap latency is under 1.5s, log it as a finding — but proceed with concurrent constraint for selection.

3. **Model class A (primary)?** 7B–9B instruct, 4-bit quantization, GPU-first. This is the expected sweet spot for concurrent residency on 12GB minus Chatterbox footprint.

4. **Model class B (comparison)?** 7B–9B instruct from a DIFFERENT model family than Class A. Same quantization. Purpose: avoid single-family bias.

5. **Stretch class (conditional)?** 12B–14B class, only tested IF Task 1 reveals more headroom than estimated (e.g., Chatterbox is 3GB, not 5GB). Heavy quant or mixed GPU/CPU offload. Do NOT test this class if headroom doesn't support it.

6. **How many candidates?** 2 minimum (one per class A/B), 3 maximum (if stretch class is viable). Do not test more than 3.

7. **Quality rubric or vibes?** RUBRIC. Five fixed scoring dimensions, scored before model names are revealed if possible. See Gate S3.

8. **What PromptPacks?** Real PromptPacks from existing smoke scenarios. NOT vanilla prompts. See Gate S1.

---

## Contract Spec

### Deliverables

1. **VRAM measurement report** — Actual Chatterbox footprint on target GPU (not estimated). Actual model swap latency (load → first inference). These two numbers are pinned facts for all subsequent decisions.

2. **Model evaluation matrix** — 2-3 candidates tested against Gates S1-S5. Each candidate row includes: model name, family, parameter count, quantization, VRAM footprint (measured), first-token latency (measured), completion latency (measured), quality scores (rubric), coexistence result (pass/fail).

3. **Quality rubric scorecards** — Each candidate scored on 5 dimensions (see Gate S3) across 3+ real PromptPack scenes. Raw scores preserved, not just averages.

4. **Recommendation** — One model, with rationale. If no candidate clears all gates, say so — that's a valid finding.

5. **Integration spec** — How the selected model loads into the Spark cage. What inference engine (llama.cpp, vLLM, transformers, etc.). What config is needed. Enough for a follow-up WO to wire it in.

6. **Debrief** — Standard 5-section format + Radar.

### Gate Tests (S1–S5)

**Gate S1: PromptPack compatibility.**
Run N real PromptPacks (minimum 3, from smoke scenarios — melee attack, fireball AoE, healing spell). Model must produce a valid response that respects the mask and structure in ALL N runs. Fail is any schema break, instruction inversion, or refusal.

**Gate S2: Latency budget.**
Measure time-to-first-token and time-to-completion on the target machine for each PromptPack. Pass threshold: Spark generation must complete in under 2.0 seconds for a typical combat narration prompt (leaving 1.0s for Chatterbox + playback start within the 3.0s stall budget). Log exact numbers per candidate per prompt.

**Gate S3: Quality rubric.**
Score each output on these 5 dimensions (1-5 scale each, 25 max):

| # | Dimension | What it measures |
|---|-----------|-----------------|
| 1 | **Clarity & confidence** | Narration reads as authoritative, not hedging or generic |
| 2 | **Pacing & table presence** | Sentences have rhythm suited to spoken delivery at the table |
| 3 | **Fidelity to provided facts** | Uses the mechanical facts from the PromptPack, invents nothing |
| 4 | **Controlled improvisation** | Adds flavor without minting new canon (no invented NPC names, locations, or facts not in the pack) |
| 5 | **Cadence for TTS** | Text will sound natural when spoken by Chatterbox — no tongue-twisters, no walls of dependent clauses |

Minimum pass: 15/25 average across all prompts. Below 15 on any single prompt is a flag (log it, don't auto-fail).

**Gate S4: Resource coexistence.**
Load both Spark model and Chatterbox in VRAM simultaneously. Run 5 turn cycles: Spark generates narration → Chatterbox synthesizes speech → playback. Pass: no crashes, no OOM, no runaway VRAM growth, no cumulative slowdown across the 5 cycles. Log VRAM at each step.

**Gate S5: Repeat stability.**
Run the same PromptPack 3 times with fixed sampling settings (temperature, seed if supported). Check that outputs are factually consistent (same damage numbers referenced, same character names used) and stylistically within band. Not deterministic — but not drifting into different facts. Fail is factual contradiction between runs.

---

## Implementation Plan

### Task 1: Measure baseline (FIRST — everything depends on this)
- Load Chatterbox with standard reference voice on target GPU
- Measure actual VRAM footprint (nvidia-smi or equivalent)
- Measure model swap latency: unload Chatterbox → load a 7B model → first inference → time
- Record these as pinned numbers in the evaluation report
- Determine actual VRAM headroom for Spark model

### Task 2: Select candidates
- Based on measured headroom, select 2 candidates from different model families (Class A + Class B)
- If headroom permits, add 1 stretch candidate (Class C)
- Candidate selection criteria: strong instruct-following, good prose reputation in community benchmarks, fits in measured headroom at target quantization
- Do NOT spend time on exhaustive model surveys — pick strong representatives from well-known families

### Task 3: Run gate tests
- For each candidate: S1 (PromptPack compat) → S2 (latency) → S3 (quality rubric) → S4 (coexistence) → S5 (stability)
- Gate order is intentional — fail-fast. If a model fails S1, skip remaining gates for that model.
- Use real PromptPacks from `aidm/` (the module that compiles PromptPacks from Oracle WorkingSet — confirm path before running)

### Task 4: Score and recommend
- Fill evaluation matrix
- Recommend one model (or report that none passed)
- Write integration spec for the winner

### Stop Conditions

- **STOP** if no candidate passes Gate S1 (PromptPack compatibility) — report finding, do not force-fit
- **STOP** if measured Chatterbox VRAM exceeds 7GB (leaves less than 5GB, likely insufficient for any 7B model) — report finding, escalate to PM for sequential loading reconsideration
- **STOP** if all candidates fail Gate S3 quality rubric (below 15/25 average) — the model class may be too small for the narration bar
- **STOP** if you find yourself downloading or testing more than 3 models — scope creep

---

## Assumptions to Validate

1. **Chatterbox VRAM is ~4-5GB.** Measure it. If it's significantly different, the candidate pool changes.
2. **PromptPack compiler is functional and produces real packs from smoke scenario data.** Confirm the pipeline works before testing models against it. If it doesn't produce packs, use representative handcrafted prompts and log the deviation.
3. **The Spark cage interface exists and accepts a model + prompt → text output.** Confirm the integration point exists. If it doesn't, document what's needed for the follow-up wiring WO.
4. **A 7B-9B model at 4-bit quantization can produce narration quality that clears the Mercer bar.** This is the core hypothesis. It may be wrong. If it is, that's a valid finding — don't rationalize poor output.
5. **GPU is NVIDIA with CUDA support and 12GB VRAM total.** Confirm before loading anything.

---

## Integration Seams

- **Spark cage** — the module that accepts an LLM and generates text from PromptPacks. This WO selects the model; a follow-up WO wires it in.
- **Chatterbox TTS** — concurrent VRAM resident. This WO validates coexistence; it does NOT modify the TTS pipeline.
- **PromptPack compiler** — consumer of Oracle WorkingSet. This WO uses PromptPacks as test inputs; it does NOT modify the compiler.

No code changes to existing modules. This is a research + evaluation WO. The output is a recommendation + integration spec, not shipped code.

---

## Preflight

Run `python scripts/preflight_canary.py` and log results in `pm_inbox/PREFLIGHT_CANARY_LOG.md` before starting work.

---

## Debrief Focus

1. **Missing assumption** — What assumption in this dispatch turned out to be wrong, and how did it change your approach?
2. **Spec divergence** — Did you deviate from the gate definitions or scoring rubric? If so, why?

---

## Delivery

- Commit evaluation report, rubric scorecards, and integration spec to `pm_inbox/` or `docs/research/` (builder's judgment on location)
- Debrief in `pm_inbox/DEBRIEF_WO-SPARK-LLM-SELECTION.md`
- Standard 5-section format: (0) Scope Accuracy, (1) Discovery Log, (2) Methodology Challenge, (3) Field Manual Entry, (4) Builder Radar
- **Builder Radar (Section 4, mandatory, 3 lines):**
  - Line 1: **Trap.** Hidden dependency or trap.
  - Line 2: **Drift.** Current drift risk.
  - Line 3: **Near stop.** What got close to triggering a stop condition.
- Missing or unlabeled Radar → REJECT debrief. No partial accept.

---

# ADDENDUM A — Sequential VRAM Pivot

**Date:** 2026-02-19
**Trigger:** Hardware measurement (Anvil, RTX 3080 Ti) falsified concurrent residency assumption.
**Authority:** Slate (PM), Thunder (PO) approval, Aegis (GPT) adversarial audit.

**Read this addendum AFTER the main dispatch above. Where this addendum contradicts the main dispatch, the addendum wins.**

---

## A1. OVERRIDE — Binary Decision #2

Binary Decision #2 is amended: **CONCURRENT → SEQUENTIAL** on 12GB hardware.

**Measured facts (Anvil, 2026-02-19):**
- GPU: RTX 3080 Ti, 12,288 MB total VRAM, Driver 591.74, CUDA 13.1
- Chatterbox Original idle: 3,059 MB allocated / 3,088 MB reserved
- Chatterbox Original peak (synthesis): 3,465 MB
- Concurrent headroom after Chatterbox: ~8,800 MB — insufficient for 8B LLM (~4,500 MB) + KV cache + inference spikes on both models simultaneously

**Sequential means:** Spark LLM and Chatterbox are never loaded in VRAM at the same time. The Spark model gets the full ~11 GB VRAM budget (12 GB minus ~1 GB OS overhead). Chatterbox is unloaded before Spark loads, and vice versa.

---

## A2. POSTURE — Batch Per Turn (Path B)

All latency and gate measurements must assume **Path B: batch narration per turn.**

The runtime sequence is:
1. Unload Chatterbox (if loaded)
2. Load Spark LLM
3. Generate ALL narration for the turn (1-3+ beats) in one Spark session
4. Unload Spark LLM
5. Load Chatterbox
6. Synthesize ALL audio for the turn in one Chatterbox session
7. Play audio (no GPU required)

**Do NOT measure per-beat swapping.** The architecture swaps once per turn, not once per beat. Multi-beat turns (attack → damage → condition) batch all narration while Spark is loaded, then batch all synthesis while Chatterbox is loaded.

---

## A3. BUDGET — Revised Stall Threshold

The original 3.0s stall budget assumed concurrent residency and is no longer valid.

**New target: 8.0 seconds** from intent submission to first audio output for a **single-beat turn**, measured end-to-end including one full swap cycle:

| Phase | What | Expected Range |
|-------|------|---------------|
| Unload Chatterbox | Free VRAM | 0.5-1.0s |
| Load Spark LLM | GGUF → GPU | 1.0-3.0s |
| Generate narration | Inference | 0.5-2.0s |
| Unload Spark LLM | Free VRAM | 0.5-1.0s |
| Load Chatterbox | Model → GPU | 1.0-2.0s |
| Synthesize speech | TTS | 1.0-2.0s |
| **Total** | | **4.5-11.0s** |

**Pass threshold (S2):** Single-beat ≤ 8.0 seconds end-to-end.

**Secondary metric (report, not pass/fail):** 3-beat batched turn (e.g., attack + damage + condition) total time from intent to last audio complete. This should scale sub-linearly vs 3× single-beat because swap cost is paid once. If it doesn't scale sub-linearly, that's a finding.

**Record separately for diagnosis:** (a) Spark model load time, (b) Spark TTFT (time-to-first-token), (c) Spark total generation time, (d) Chatterbox load time, (e) Chatterbox time-to-first-audio. Do not bundle load time into TTFT — these are distinct phases with different optimization paths.

---

## A4. CANDIDATES — 12B Promoted

The 12B stretch class (Gemma 3 12B QAT) is promoted to **primary candidate** alongside the two 8B candidates. It is no longer conditional on Chatterbox VRAM being ≤ 3.5 GB — under sequential loading, the full ~11 GB budget accommodates it.

All three candidates are evaluated equally. The rubric decides:
- **Class A:** Qwen3 8B Instruct (Q4_K_M) — ~5.0 GB VRAM
- **Class B:** LLaMA 3.1 8B Instruct (Q4_K_M) — ~4.5 GB VRAM
- **Class C:** Gemma 3 12B QAT (Q4_K_M) — ~8.5 GB VRAM

Selection must satisfy BOTH S2 (latency) AND S3 (quality). No "prose-only" win — a model that produces beautiful narration in 12 seconds fails S2 and is eliminated. No "speed-only" win — a model that generates in 2 seconds but produces flat prose fails S3 and is eliminated.

**12B load time caveat:** The 12B model will have a longer load time (~2-3s vs ~1-2s for 8B). This is acceptable IF the total end-to-end stays within the 8.0s budget. The builder must measure and report actual load times per candidate.

---

## A5. S0 — Concurrent Viability Probe (TIMEBOXED)

**Optional. Maximum 30 minutes. Logged finding only.**

Load Chatterbox + each 8B candidate simultaneously. Run 5 cycles of generate → synthesize. Log VRAM at each step.

- If no OOM: log as finding. Note peak VRAM. This informs future hardware targeting (e.g., 16 GB cards) but does NOT change the current architecture. Sequential remains the default posture regardless of S0 outcome.
- If OOM: log and move on. Expected result.

**Do NOT run S0 for the 12B candidate.** It will not fit alongside Chatterbox. Don't waste time confirming the obvious.

---

## A6. GATE AMENDMENTS

The following gates are redefined. All other gates from the main dispatch remain as specified.

**Gate S2 (REDEFINED): Latency and stall budget under sequential loading.**
Measure end-to-end intent-to-first-audio under Path B (batch per turn). Include full swap cycle in the measurement. Pass threshold: single-beat ≤ 8.0 seconds. Also record 3-beat batched turn total time as secondary metric. Log each phase (unload/load/generate/unload/load/synthesize) individually so we can identify bottlenecks. Diagnostics: record and report (a) Spark load time, (b) Spark TTFT, (c) Spark total generation time, (d) Chatterbox load time, (e) Chatterbox time-to-first-audio. Do not bundle load time into TTFT.

**Gate S4 (REDEFINED): Sequential coexistence stability.**
Run 5 full swap loops: load Spark → batch generate 3 narrations → unload Spark → load Chatterbox → batch synthesize 3 audio clips → unload Chatterbox. Pass: no crashes, no OOM, no runaway VRAM growth, no cumulative slowdown across the 5 loops. Log VRAM at each phase transition. VRAM at loop 5 ≤ VRAM at loop 1 + 100 MB tolerance.

Gates S1, S3, S5 remain as defined in the main dispatch.

---

## A7. STOP CONDITIONS (AMENDED)

Original stop conditions remain in effect, plus:

- **STOP** if ALL candidates fail S2 (no model meets the 8.0s single-beat budget) — report finding with per-phase breakdown. The bottleneck identification (load time? inference? synthesis?) determines whether the budget or the architecture needs revision.
- **STOP** if swap loop shows VRAM leak > 500 MB across 5 iterations in S4 — indicates a resource cleanup bug in the adapter lifecycle, not a model selection issue. Report to PM.

Original stop condition for Chatterbox > 7 GB is no longer relevant (measured at 3.1-3.5 GB). Remove.

---

## A8. ASSUMPTIONS UPDATE

Original Assumption 1 (Chatterbox VRAM ~4-5GB): **RESOLVED.** Measured at 3,059 MB idle, 3,465 MB peak. Lower than estimated.

Original Assumption 5 (GPU is NVIDIA 12GB): **RESOLVED.** RTX 3080 Ti, 12,288 MB, CUDA 13.1.

New assumption to validate:
- **Assumption 6: Model swap latency (unload + load) is ≤ 4.0 seconds for 8B models and ≤ 5.0 seconds for 12B models.** If significantly worse, the 8.0s budget becomes unachievable and the architecture needs a different mitigation (e.g., persistent model server, mmap warm cache).

---

## A9. INTEGRATION SEAM UPDATE

Original seam for Chatterbox TTS is amended:
- ~~Chatterbox TTS — concurrent VRAM resident.~~
- **Chatterbox TTS — sequential VRAM resident.** This WO validates swap lifecycle stability; it does NOT modify the TTS pipeline. The runtime model manager (not yet built — follow-up WO scope) will handle load/unload orchestration.

---

*End of Addendum A.*

# Waypoint Spark Explore Debrief

**Session date time UTC:** 2026-02-21 15:30 to 16:15 UTC
**Session date time local:** 2026-02-21 09:30 to 10:15 CST-CN
**Operator:** Thunder
**Builder:** Anvil (BS Buddy)

---

## Purpose

Prove the Spark cage is operational end to end: DLL loading, model inference, narration generation, and validator enforcement, then stress test it with chaos scenarios and validator fuzzing.

---

## Environment

**Machine:** Desktop workstation (Windows 11 Pro 10.0.22631)
**OS:** Windows 11 Pro
**GPU:** NVIDIA GeForce RTX 3080 Ti, 12288 MiB VRAM
**Driver:** 591.74
**Python:** 3.11.1
**Key libraries:**
- llama-cpp-python 0.3.4
- torch 2.5.1+cu121
- CUDA 12.1
- pynvml 13.0.1 (nvidia-ml-py 13.590.48)

**Model:** Qwen2.5 7B Instruct Q4_K_M (4.4 GB GGUF on disk)
**Context size:** 2048
**GPU layers:** -1 (all layers on GPU)
**Threads:** auto-detect
**Generation settings:** temperature 0.8, max tokens 150
**Stop sequences:** </narration>, double newline, ===

---

## Baseline Behavior

**Cold start model load time:** 34.85 seconds. This is expected. CUDA runtime context initialization happens on first use per process. It allocates device memory, compiles PTX kernels, and builds the execution context. One time cost.

**Warm start model load time:** 3.26 seconds. This is steady state. Model weights loaded into already initialized CUDA context.

**Ratio:** 10.7 times slower on cold start.

**First token time:** Not directly measured. Generation started within the measured generation time window.

**Total generation time:** 0.56 to 0.93 seconds per scenario (single draft, warm). Throughput approximately 33 tokens per second.

**Known expected differences:** Cold start adds approximately 30 seconds. This is not a model problem or a DLL problem. If a builder reports 35 second load times, ask if this is a fresh process. If yes, expected behavior.

---

## Run Log

### Run 1: H-01 Melee Hit (baseline)
**Inputs:** attack_hit, Kael vs Goblin Scout, moderate severity, longsword slashing
**Settings:** temp 0.8, max 150, stop [</narration>, newline newline, ===]
**Raw output saved:** pm_inbox/HOOLIGAN_RUN_001.json, frames[0]
**Validator result:** PASS. No violations.
**Fallback result:** Not triggered.
**Notes:** 47 completion tokens, 0.72 seconds. Clean baseline. Blue light embellishment noted but not a violation.

### Run 2: H-02 Miss (no damage)
**Inputs:** attack_miss, Grunk vs Skeleton Warrior, no severity, battleaxe slashing
**Settings:** same as baseline
**Raw output saved:** pm_inbox/HOOLIGAN_RUN_001.json, frames[1]
**Validator result:** PASS. No violations.
**Fallback result:** Not triggered.
**Notes:** 65 completion tokens, 0.93 seconds. Correctly narrates a whiff with no damage described.

### Run 3: H-03 Kill Shot (target defeated)
**Inputs:** attack_hit, Vex vs Dire Wolf Alpha, devastating severity, longbow piercing, target defeated true
**Settings:** same as baseline
**Raw output saved:** pm_inbox/HOOLIGAN_RUN_001.json, frames[2]
**Validator result:** PASS. No violations.
**Fallback result:** Not triggered.
**Notes:** 41 completion tokens, 0.59 seconds. Ending its reign over the pack. Correct defeat narration.

### Run 4: H-04 Healing Spell
**Inputs:** healing, Brother Aldric on Kael, moderate severity, Cure Wounds
**Settings:** same as baseline
**Raw output saved:** pm_inbox/HOOLIGAN_RUN_001.json, frames[3]
**Validator result:** PASS. No violations.
**Fallback result:** Not triggered.
**Notes:** 53 completion tokens, 0.73 seconds. Non-combat narration works cleanly.

### Run 5: H-05 Condition Removal
**Inputs:** condition_removed, Seraphine on Grunk, moderate severity, Remove Curse, condition removed mummy_rot
**Settings:** same as baseline
**Raw output saved:** pm_inbox/HOOLIGAN_RUN_001.json, frames[4]
**Validator result:** WARN. RV-004: Condition mummy_rot removed but not referenced in narration.
**Fallback result:** Not triggered.
**Notes:** 49 completion tokens, 0.72 seconds. See FINDING-HOOLIGAN-01. The narration says mummy rot with a space. The validator checks for mummy_rot with an underscore. Keyword normalization issue.

### Run 6: H-06 Critical Hit
**Inputs:** attack_hit, Kael vs Orc Warchief, critical severity, longsword slashing
**Settings:** same as baseline
**Raw output saved:** pm_inbox/HOOLIGAN_RUN_001.json, frames[5]
**Validator result:** PASS. No violations.
**Fallback result:** Not triggered.
**Notes:** 54 completion tokens, 0.77 seconds. No critical hit game term used. Respected the contract.

### Run 7: H-07 Save Success (spell fizzles)
**Inputs:** spell_no_effect, Seraphine vs Iron Golem, no severity, Hold Monster, save result success
**Settings:** same as baseline
**Raw output saved:** pm_inbox/HOOLIGAN_RUN_001.json, frames[6]
**Validator result:** PASS. No violations.
**Fallback result:** Not triggered.
**Notes:** 56 completion tokens, 0.81 seconds. Correctly narrates spell failure without save DCs.

### Run 8: H-08 Empty MEMORY Section
**Inputs:** attack_hit, Kael vs Goblin Scout, moderate severity. MEMORY section set to Previous None, Scene Unknown.
**Settings:** same as baseline
**Raw output saved:** pm_inbox/HOOLIGAN_RUN_001.json, frames[7]
**Validator result:** PASS. No violations.
**Fallback result:** Not triggered.
**Notes:** 40 completion tokens, 0.56 seconds. Graceful degradation. Works without context.

### Runs 9 through 18: Determinism Abuse (Axis 1)
**Inputs:** Same as H-01 melee baseline, repeated 10 times
**Settings:** temp 0.0, seed 42, max 150, stop [</narration>, newline newline, ===]
**Raw output saved:** pm_inbox/HOOLIGAN_RUN_001.json, axis_1_determinism.frames[0-9]
**Validator result:** All 10 PASS. No violations.
**Fallback result:** Not triggered on any run.
**Notes:** 34 completion tokens each run, 0.42 to 0.51 seconds. All 10 outputs identical. One unique output in 10 runs. Determinism confirmed with seed plus greedy decoding.

### Runs 19 through 22: Contract Ambiguity (Axis 3)
**Run 19 AMB-01:** Two intents in one line. Kael attacks while Seraphine casts Shield.
**Validator result:** FAIL. RV-001 false positive. See FINDING-HOOLIGAN-03.
**Raw output saved:** pm_inbox/HOOLIGAN_RUN_001.json, axis_3_ambiguity.frames[0]

**Run 20 AMB-02:** Negation in contract. Do not mention the weapon by name.
**Validator result:** PASS. Model used blade and silent shadow instead of longsword. Respected negation.
**Raw output saved:** pm_inbox/HOOLIGAN_RUN_001.json, axis_3_ambiguity.frames[1]

**Run 21 AMB-03:** Roleplay wrapper around a command. Asterisk adjusts DM screen asterisk.
**Validator result:** PASS. Model ignored the roleplay wrapper, wrote clean narration.
**Raw output saved:** pm_inbox/HOOLIGAN_RUN_001.json, axis_3_ambiguity.frames[2]

**Run 22 AMB-04:** Minimal TRUTH section. Bare minimum fields, empty STYLE and MEMORY.
**Validator result:** PASS. Graceful handling of minimal input.
**Raw output saved:** pm_inbox/HOOLIGAN_RUN_001.json, axis_3_ambiguity.frames[3]

---

## Findings

### FINDING-HOOLIGAN-01
**Short name:** Condition keyword underscore mismatch
**Severity:** LOW
**Status:** OPEN

**What happened:** Validator warned that mummy_rot was not referenced in narration, but the narration says mummy rot with a space.

**Why it matters:** Condition names from the engine use underscores. Natural language uses spaces. The validator should normalize before matching.

**Evidence:**
- Input: pm_inbox/HOOLIGAN_RUN_001.json, hooligan.frames[4].prompt
- Settings: same as baseline
- Raw output: pm_inbox/HOOLIGAN_RUN_001.json, hooligan.frames[4].raw_output
- Validator report: verdict WARN, RV-004

**Recommendation:** Normalize condition names by replacing underscores with spaces before keyword matching in RV-004.

---

### FINDING-HOOLIGAN-02
**Short name:** RV-007 forbidden claims not implemented
**Severity:** HIGH
**Status:** OPEN

**What happened:** Validator did not catch damage numbers, HP values, or dice rolls injected into narration text.

**Why it matters:** The model has not produced these violations yet, but the validator would not catch them if it did. Any narration containing explicit game mechanics passes validation unchallenged.

**Evidence:**
- FUZZ-01: Text containing deals 14 damage. Verdict PASS. Expected FAIL.
- FUZZ-02: Text containing 42 HP remaining. Verdict PASS. Expected FAIL.
- FUZZ-03: Text containing rolled a 19. Verdict PASS. Expected FAIL.
- Full fuzzing results: pm_inbox/HOOLIGAN_RUN_001.json, axis_2_fuzzing.mutations[0-2]

**Recommendation:** Implement RV-007 to detect damage numbers, HP references, dice notation, roll results, save DCs, and AC references. Pattern list provided in DEBRIEF_HOOLIGAN_RUN_001.md.

---

### FINDING-HOOLIGAN-03
**Short name:** RV-001 false positive on compound actions
**Severity:** MEDIUM
**Status:** OPEN

**What happened:** Validator fired RV-001 hit miss contradiction on compound narration where deflection language referred to a different action than the hit.

**Why it matters:** RV-001 scans entire text for miss keywords without attributing them to specific actors. Works for single action narration. Produces false positives for simultaneous events.

**Evidence:**
- Input: pm_inbox/HOOLIGAN_RUN_001.json, axis_3_ambiguity.frames[0].prompt
- Raw output: The word deflected from Seraphine Shield spell triggered miss detection on Kael attack hit.
- Validator report: verdict FAIL, RV-001

**Recommendation:** Scope RV-001 per sentence or per actor. Or accept that compound narrations need a different validation path.

---

## Fixes Applied During Session

### Fix 1: Device label logic
**File:** aidm/spark/llamacpp_adapter.py line 234
**What changed:** Replaced n_gpu_layers > 0 with n_gpu_layers != 0 and self.enable_gpu. The old check evaluated -1 > 0 as False, so device reported cpu when model was fully on GPU.
**Commit:** 487ef77
**Risk:** Low. Only affects the device label string in LoadedModel. Does not affect actual GPU layer allocation.

### Fix 2: NVML VRAM reporting
**File:** aidm/spark/llamacpp_adapter.py, _get_available_vram_gb and new _get_vram_used_gb
**What changed:** Added pynvml as primary VRAM reporter, torch as fallback. Added new method _get_vram_used_gb for runtime monitoring.
**Commit:** 487ef77
**Risk:** Low. Falls back to torch if pynvml not available.

### Fix 3: Stop sequence === added (from prior session)
**File:** config/models.yaml, all narration presets
**What changed:** Added === to stop sequences to prevent multi-draft generation.
**Commit:** 076c486
**Risk:** Low. May truncate legitimate output that starts with === but this is unlikely in narration context.

**Important note from Aegis:** Raw before evidence is preserved. Section 8 of DEBRIEF_WO-SPARK-EXPLORE-001.md contains the full raw failure log including all 4 DLL fix attempts, the raw multi-draft output, and the device timing anomaly. AB_FINDING_EXPLORE_01.json contains the before and after stop sequence test with full raw outputs.

---

## Evidence Pack

**Prompt packs:** Stored in scripts/spark_hooligan.py, SCENARIOS dict and AMBIGUOUS_SCENARIOS dict
**Raw outputs:** pm_inbox/HOOLIGAN_RUN_001.json (full capture frames for all runs)
**Validator reports:** Embedded in each capture frame in HOOLIGAN_RUN_001.json
**Run logs:** This debrief plus pm_inbox/DEBRIEF_HOOLIGAN_RUN_001.md
**Hardware metrics:** NVML VRAM readings in each capture frame (vram_before_mb, vram_after_mb)
**AB test artifact:** pm_inbox/AB_FINDING_EXPLORE_01.json
**Raw failure log:** pm_inbox/DEBRIEF_WO-SPARK-EXPLORE-001.md section 8
**Test harnesses:** scripts/spark_explore.py, scripts/spark_ab_stop_sequence.py, scripts/spark_hooligan.py

---

## Next Plan

Pass Zero baseline is locked. Hooligan run is complete. Three findings documented.

Next priorities from findings:
1. Implement RV-007 forbidden claims detection. HIGH priority gap.
2. Fix RV-004 condition keyword normalization. LOW but clean fix.
3. Evaluate RV-001 compound action handling. MEDIUM, needs design decision.

Further testing when fixes land:
- Rerun validator fuzzing after RV-007 implementation to confirm all 8 mutations caught
- Rerun H-05 after RV-004 normalization fix to confirm PASS
- Design compound action test suite for RV-001 evaluation

---

## Closing

The cage holds. The model generates clean prose across 8 combat types. Determinism works. The validator catches structural lies but is blind to forbidden meta-game content. That is the gap.

Story is welcome. Raw record is sacred. Narrative sits on top of evidence, not instead of it.

No patching until the finding is captured. Unless the system is fully blocked and cannot run at all. If it is blocked, fix only the block, then resume logging immediately.

---

*Seven Wisdom energy is undefeated.*

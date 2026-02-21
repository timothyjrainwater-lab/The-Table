# Spark State Digest

**Last updated:** 2026-02-22

## Environment

- **Machine:** Thunder's desktop, Windows 11 Pro
- **GPU:** NVIDIA (VRAM monitored via pynvml, not torch)
- **Python:** 3.11+
- **llama-cpp-python:** 0.3.4 (pre-built wheel — blocks Qwen3/Gemma3 arch)

## Model

- **Active model:** Qwen2.5 7B Instruct (Q4_K_M GGUF)
- **Registry:** `models.yaml`
- **Load time:** ~2.69s
- **VRAM:** ~5,818 MB
- **GPU offload:** Full (`n_gpu_layers=-1`)
- **DLL fix:** importlib.util.find_spec + ctypes pre-load chain (GAP-C resolved)

## Determinism

- **Proven:** 10/10 identical outputs at seed=42, temp=0.0
- **RNG:** Deterministic via `RNGManager(master_seed)`

## Validator

- **Operational rules:** RV-001 (hit/miss), RV-002 (defeat), RV-003 (severity), RV-004 (condition), RV-005 (contraindication), RV-007 (delivery mode), RV-008 (save result)
- **MISSING:** RV-009 (forbidden meta-game claims) + RV-010 (rule citations) — dispatched as WO-SPARK-RV007-001
- **Known issue:** RV-004 underscore normalization (FINDING-HOOLIGAN-01)

## Pipeline

- PromptPack v1.0: 5-channel wire protocol (TRUTH, MEMORY, TASK, STYLE, CONTRACT)
- GuardedNarrationService: FAIL -> template fallback, WARN -> log, PASS -> proceed
- Kill switches: KILL-001 through KILL-006 active
- Contradiction checker: active (WO-058)

## Known Issues

1. **FINDING-HOOLIGAN-02 HIGH** — Validator blind to forbidden meta-game content (damage numbers, HP, dice rolls). WO dispatched.
2. **FINDING-HOOLIGAN-03 MEDIUM** — RV-001 false positive on compound actions. Needs contract decision.
3. **FINDING-HOOLIGAN-01 LOW** — RV-004 underscore normalization. Fix scoped in RV-007 WO.
4. **GAP-A LOW** — `dm_persona.py:83` missing import. Runtime-functional.
5. **GAP-B HIGH** — llama-cpp-python blocks Qwen3/Gemma3. Needs VS Build Tools + compile from source.

# WO-PRS-FIRSTRUN-001 — Fail-Closed First Run
**Lifecycle:** NEW
**Date:** 2026-02-23
**Type:** FEATURE
**Authority:** PRS-01 v1.0 FROZEN (`docs/contracts/PUBLISHING_READINESS_SPEC.md`)
**Gate:** AA (new)

---

## Target Lock

Build the P7 fail-closed first run test: verify that when required runtime assets (model weights, TTS voices) are missing, the application produces a deterministic error message and halts. No silent fallback.

## Binary Decisions

| # | Decision | Resolution |
|---|----------|------------|
| 1 | What assets are required? | **Model weights (Qwen2.5 GGUF)** and **TTS voice models (Kokoro)**. Builder inventories actual required paths by tracing startup. |
| 2 | Test environment? | **Temp directory with clean config** — copy config but not weights/voices. Run startup. Expect error + halt. |
| 3 | Error message format? | **Must name the missing asset and suggest where to obtain it** per PRS-01 §P7. Builder validates message content, not just exit code. |
| 4 | Partial startup allowed? | **No** — per PRS-01 §P7: "No partial output is generated before the error." Script checks for clean halt. |

## Contract Spec

**`scripts/publish_first_run_missing_weights.py`:**
- Create a temporary working environment (temp dir or env vars) where model weight paths resolve to empty/missing locations
- Attempt to start the application's core initialization path
- Verify:
  1. Application exits with non-zero exit code
  2. Error output names the missing asset (e.g., "Model not found: ...")
  3. Error output suggests where to obtain it (e.g., "Download from ...")
  4. No partial output is generated before the error
- Exit 0 if all checks pass (application correctly fails closed), exit 1 if application silently starts or hangs

## Implementation Plan

1. Trace application startup path to identify all required runtime assets
2. Document required asset paths and their expected locations
3. Build test script that removes/redirects asset paths
4. Verify fail-closed behavior: deterministic error + halt
5. Verify error message quality: names asset, suggests resolution

## Gate Spec

**New test file:** `tests/test_publish_firstrun_gate_aa.py` (Gate AA)

| Test ID | What It Checks |
|---------|---------------|
| AA-01 | Script exits 0 when run (meaning: app correctly fails closed) |
| AA-02 | Missing model weights produce actionable error message |
| AA-03 | Missing TTS voices produce actionable error message |
| AA-04 | Error message names the specific missing asset |
| AA-05 | Application exits with non-zero code when assets missing |
| AA-06 | No partial output before error |

**Minimum 6 tests.** Gate letter: AA.

## Files to Read

- `docs/contracts/PUBLISHING_READINESS_SPEC.md` — §P7
- `aidm/runtime/session_orchestrator.py` — Startup path, asset loading
- `aidm/voice/` — TTS initialization, voice model loading
- `config/` — Default config, asset path definitions

## Preflight

```bash
python -m pytest tests/ -x -q --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py --ignore=tests/test_graduated_critique_orchestrator.py --ignore=tests/test_immersion_authority_contract.py --ignore=tests/test_pm_inbox_hygiene.py --ignore=tests/test_speak_signal.py
```

## Integration Seams

- Script logs to `RC_PACKET/p7_first_run.log` (via orchestrator)
- Exit code semantics: 0 = app correctly fails closed (PASS), 1 = app silently starts or hangs (FAIL)
- Note the inverted semantics: the *publish gate* passes when the *application* fails (correctly)

## Assumptions to Validate

1. Application has a clean startup path that can be invoked programmatically
2. Missing weight/voice paths produce errors (not silent fallbacks) — if not, this WO may need to add fail-closed guards to startup

## Delivery Footer

Builder delivers: 1 script + gate tests. Debrief in CODE format (500 words, 5 sections + Radar). Commit message references PRS-01 and gate letter AA.

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "First run work order complete. Awaiting Thunder."
```

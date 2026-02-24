# WO-WORLDGEN-INGESTION-001 — Content Pack Ingestion Stage

**Status:** ACCEPTED — 15/15 Gate INGESTION
**Date:** 2026-02-23
**Gate:** INGESTION (new gate, 15/15)
**Boundary law:** `aidm/core/` only — no imports from `aidm/lens/` or `aidm/immersion/`
**Depends on:** Stage 0 (validate) — ingestion runs immediately after Stage 0 in the compile pipeline

## Verdict

**ACCEPTED.** Gate INGESTION 15/15. Zero regressions (world_compiler 51/51, world_archive 24/24).

`IngestionStage` delivers step 1 of the FINDING-WORLDGEN-IP-001 audit chain.

Key findings during implementation:
- Real content pack (`aidm/data/content_pack/`) has 7 field-length warnings (4 creatures with `environment_tags` > 100 chars, 3 with `alignment_tendency` > 100 chars). These are recorded in `ingestion_report.json` under `validation_warnings` — non-blocking, they are the subject of the double-audit step.
- Structural validation (duplicate IDs, broken prereq chains) remains blocking (IC-002).
- `content_hash` baseline: deterministic SHA-256 over all 273 creatures, 605 spells, 109 feats.

### `ingestion_report.json` output (success path):
```json
{
  "content_hash": "<64-char sha256>",
  "content_pack_dir": "<abs path>",
  "creature_count": 273,
  "feat_count": 109,
  "pack_id": "<32-char hash>",
  "spell_count": 605,
  "stage_id": "ingestion",
  "status": "success",
  "validation_errors": [],
  "validation_warnings": ["creature CREATURE_0102: item in 'environment_tags' is 163 chars (max 100)", ...]
}
```

---

---

## Context

FINDING-WORLDGEN-IP-001 defines a four-step pre-condition chain before World Gen LLM mode can be enabled:

> **ingestion complete → double audit PASS → name strip → IP scan gate → LLM mode enabled**

This WO delivers **step 1**: a formal `IngestionStage` (Stage 0.5 in the pipeline) that loads the `ContentPackLoader` from `aidm/data/content_pack/`, validates it, computes a deterministic content pack hash, and writes an `ingestion_report.json` into the compile workspace. Without a verified ingestion artifact, the downstream audit (step 2) has no stable baseline to compare against.

The content pack already exists (`aidm/data/content_pack/creatures.json` 273 creatures, `spells.json`, `feats.json`). The loader (`aidm/lens/content_pack_loader.py`) already exists. What is missing is a **formal compile-stage wrapper** that:
1. Loads via `ContentPackLoader.from_directory()`
2. Runs `validate()` — duplicate IDs, feat prereq chains, field-length check
3. Counts entities (spells, creatures, feats) and reports them
4. Computes the deterministic `content_hash` and records it
5. Writes `ingestion_report.json` into the workspace
6. Registers itself as a `CompileStage` so the `WorldCompiler` can orchestrate it

---

## Deliverables

### 1. `aidm/core/compile_stages/ingestion.py` (new file)

```python
"""Stage: Content Pack Ingestion.

Loads the content pack from aidm/data/content_pack/, validates it,
and writes ingestion_report.json to the compile workspace.

This stage is the formal entry point for the audit chain:
  ingestion complete → double audit PASS → name strip → IP scan gate → LLM mode

WO-WORLDGEN-INGESTION-001
Reference: docs/contracts/WORLD_COMPILER.md §2.0
Reference: FINDING-WORLDGEN-IP-001 (pm_inbox/PM_BRIEFING_CURRENT.md)

BOUNDARY LAW: No imports from aidm/lens/ at module scope.
aidm/lens/content_pack_loader is imported inside execute() to keep
the core layer boundary clean per BL-003.
"""
```

**Class:** `IngestionStage(CompileStage)`

| Property | Value |
|----------|-------|
| `stage_id` | `"ingestion"` |
| `stage_number` | `0` (runs first among registered stages, after Stage 0 validate) |
| `depends_on` | `()` (no stage dependencies — only needs workspace from Stage 0) |

**Constructor:**
```python
def __init__(self, content_pack_dir: Optional[Path] = None) -> None:
```
- If `content_pack_dir` is `None`, defaults to `Path(__file__).parent.parent.parent / "data" / "content_pack"` (resolves to `aidm/data/content_pack/`)
- Stores as `self._content_pack_dir`

**`execute(context: CompileContext) -> StageResult`:**

Steps (in order):
1. Resolve `pack_dir`: use `self._content_pack_dir` if set, else fall back to `context.content_pack_dir` if it exists, else use the default path.
2. **Import** `ContentPackLoader` from `aidm.lens.content_pack_loader` inside the method (boundary-safe).
3. Call `ContentPackLoader.from_directory(pack_dir)`.
4. Call `loader.validate()`. If errors → return `StageResult(status="failed", error="\n".join(errors))`.
5. Compute counts: `spell_count`, `creature_count`, `feat_count`.
6. Compute `content_hash = loader.content_hash` (already a property on the loader).
7. Build `ingestion_report.json` dict:
   ```json
   {
     "stage_id": "ingestion",
     "status": "success",
     "content_pack_dir": "<abs path>",
     "content_hash": "<64-char sha256>",
     "spell_count": <N>,
     "creature_count": <N>,
     "feat_count": <N>,
     "validation_errors": [],
     "pack_id": "<pack_id>"
   }
   ```
8. Write to `context.workspace_dir / "ingestion_report.json"`.
9. Store `context.stage_outputs["ingestion"] = {"content_hash": content_hash, "spell_count": ..., "creature_count": ..., "feat_count": ...}`.
10. Return `StageResult(stage_id="ingestion", status="success", output_files=("ingestion_report.json",), elapsed_ms=...)`.

**Failure mode:** If `pack_dir` does not exist → `StageResult(status="failed", error=f"IC-001: content_pack_dir not found: {pack_dir}")`. If validation errors → `StageResult(status="failed", error=f"IC-002: content pack validation failed: {'; '.join(errors)}")`.

**Error codes:**
- `IC-001`: pack directory not found
- `IC-002`: content pack validation failed (lists specific errors)

---

### 2. `tests/test_ingestion_gate.py` (new file, Gate INGESTION)

15 tests across 5 classes. All tests use `tmp_path` and real content pack where noted.

#### Class `TestIngestionStageSmoke` (3 tests)

**INGESTION-01** `test_stage_id_and_number`
Assert `IngestionStage().stage_id == "ingestion"`, `.stage_number == 0`, `.depends_on == ()`.

**INGESTION-02** `test_execute_with_real_pack`
Call `IngestionStage(content_pack_dir=REAL_PACK_DIR).execute(context)` where `REAL_PACK_DIR = Path("aidm/data/content_pack")`. Assert `result.status == "success"`. Assert `"ingestion_report.json" in result.output_files`.

**INGESTION-03** `test_ingestion_report_written`
After INGESTION-02 setup, read `workspace / "ingestion_report.json"`. Assert `data["status"] == "success"`. Assert `data["content_hash"]` is 64-char hex. Assert `data["spell_count"] > 0`. Assert `data["creature_count"] > 0`. Assert `data["feat_count"] > 0`.

#### Class `TestIngestionCounts` (3 tests)

**INGESTION-04** `test_creature_count_matches_content_pack`
Load `ContentPackLoader.from_directory(REAL_PACK_DIR)`. Assert `loader.creature_count == 273` (known count).
Then run `IngestionStage`. Assert `ingestion_report["creature_count"] == 273`.

**INGESTION-05** `test_spell_count_positive`
Run `IngestionStage` with real pack. Assert `ingestion_report["spell_count"] > 0`.

**INGESTION-06** `test_feat_count_positive`
Run `IngestionStage` with real pack. Assert `ingestion_report["feat_count"] > 0`.

#### Class `TestIngestionContentHash` (3 tests)

**INGESTION-07** `test_content_hash_is_64_chars`
Assert `len(ingestion_report["content_hash"]) == 64`.

**INGESTION-08** `test_content_hash_is_deterministic`
Run stage twice on same pack dir. Assert both `content_hash` values are equal.

**INGESTION-09** `test_content_hash_stored_in_stage_outputs`
After `execute()`, assert `context.stage_outputs["ingestion"]["content_hash"]` equals the value in `ingestion_report.json`.

#### Class `TestIngestionFailureModes` (3 tests)

**INGESTION-10** `test_missing_pack_dir_returns_failed`
Call `IngestionStage(content_pack_dir=Path("/nonexistent/path")).execute(context)`. Assert `result.status == "failed"`. Assert `"IC-001"` in `result.error`.

**INGESTION-11** `test_empty_pack_dir_succeeds_with_zero_counts`
Create an empty temp dir. Run `IngestionStage(content_pack_dir=empty_dir)`. Assert `result.status == "success"`. Assert `ingestion_report["creature_count"] == 0`. Assert `ingestion_report["spell_count"] == 0`. Assert `ingestion_report["feat_count"] == 0`.

**INGESTION-12** `test_validation_failure_returns_failed`
Create a temp pack dir. Write a `creatures.json` with duplicate `template_id` values:
```json
{"creatures": [{"template_id": "CREATURE_0001", ...}, {"template_id": "CREATURE_0001", ...}]}
```
Assert `result.status == "failed"`. Assert `"IC-002"` in `result.error`.

#### Class `TestIngestionPipelineIntegration` (3 tests)

**INGESTION-13** `test_ingestion_registered_in_world_compiler`
Build `WorldCompiler(inputs, content_pack)`. Register `IngestionStage()`. Call `compile()`. Assert `report.status == "success"` (or "partial" if real pack not present). Assert at least one stage result has `stage_id == "ingestion"`.

**INGESTION-14** `test_ingestion_runs_before_dependent_stages`
Register `IngestionStage()` and a `StubStage("lexicon", 1, depends_on=("ingestion",))`. Assert that in the compile report, the ingestion result appears before the lexicon result.

**INGESTION-15** `test_ingestion_failure_halts_dependents`
Register `IngestionStage(content_pack_dir=Path("/bad/path"))` and a `StubStage("lexicon", 1, depends_on=("ingestion",))`. Assert `lexicon` stage is `"skipped"` and `ingestion` is `"failed"`.

---

## Acceptance Criteria

- Gate INGESTION 15/15 PASS
- `IngestionStage` importable from `aidm.core.compile_stages.ingestion`
- `ingestion_report.json` written with correct schema on success
- `IC-001` error on missing pack dir
- `IC-002` error on validation failure
- Zero regressions on existing gates (world_compiler, world_archive tests pass)
- Boundary law: `ContentPackLoader` import is inside `execute()` method body, not at module scope

---

## Implementation Notes

- The `content_pack_dir` default path in `__init__` should use `Path(__file__).parent.parent.parent / "data" / "content_pack"` — resolving three parents up from `aidm/core/compile_stages/ingestion.py` gives `aidm/`, then `/ "data" / "content_pack"`.
- The 100-char field-length validation in `ContentPackLoader.validate()` skips `replaces_normal` and `organization_patterns` — this is already correct in the loader and does not need to change.
- `elapsed_ms` is `(time.monotonic_ns() // 1_000_000) - start_ms` at return time.
- The `pack_id` field in `ingestion_report.json` comes from `loader.pack_id`.
- Duplicate template_id test (INGESTION-12): write minimal JSON with only the required fields per `MechanicalCreatureTemplate.from_dict()`. Required: `template_id`, `size_category`, `creature_type`.

---

## Files Changed

| File | Action |
|------|--------|
| `aidm/core/compile_stages/ingestion.py` | CREATE |
| `tests/test_ingestion_gate.py` | CREATE |

No existing files are modified.

---

## Relation to FINDING-WORLDGEN-IP-001

This WO closes step 1 of the IP remediation chain. When INGESTION-001 is ACCEPTED:
- `ingestion_report.json` provides the `content_hash` baseline for the double audit (step 2)
- Steps 2-4 (double audit, name strip, IP scan gate) remain OPEN — separate WOs
- FINDING-WORLDGEN-IP-001 remains OPEN until all four steps complete

# WO-M1-02 Delivery Report: Inject-Only IDs & Timestamps

| Field       | Value                                      |
|-------------|-------------------------------------------|
| Agent       | OPUS (Claude Opus 4.6)                    |
| Work Order  | WO-M1-02                                  |
| Date        | 2026-02-10                                |
| Status      | COMPLETE                                  |

---

## Summary

Removed all nondeterministic `default_factory` usage for UUIDs and timestamps from dataclass fields across the codebase. All ID and timestamp fields are now required parameters (inject-only). Callers must explicitly provide values at construction time.

This enforces BL-017 (no `uuid.uuid4()` in defaults) and BL-018 (no `datetime.utcnow()`/`now()` in defaults), ensuring deterministic replay is never poisoned by hidden nondeterminism in schema defaults.

## Changes Made

### Schema Files (source of truth)

1. **`aidm/schemas/intent_lifecycle.py`**
   - Made `intent_id`, `actor_id`, `action_type`, `status`, `source_text`, `created_at`, `updated_at` all required fields with no defaults
   - Removed `import uuid`
   - `create_intent_from_input()` now requires `intent_id` and `created_at` parameters
   - `transition_to()` now requires `timestamp` parameter
   - `from_dict()` requires `intent_id`, `created_at`, `updated_at` in data (no fallback generation)

2. **`aidm/schemas/engine_result.py`**
   - Made `result_id`, `intent_id`, `status`, `resolved_at` all required fields with no defaults
   - Removed `import uuid`
   - `from_dict()` requires `result_id`, `resolved_at`, `status` in data (no fallback generation)
   - `EngineResultBuilder.build()` requires `result_id` and `resolved_at` as parameters
   - `build_failure()` and `build_aborted()` also require `result_id` and `resolved_at`

3. **`aidm/schemas/campaign.py`**
   - Made `campaign_id` a required field (removed `default_factory=lambda: str(uuid.uuid4())`)
   - Removed `import uuid`
   - `from_dict()` requires `campaign_id` in data (no nondeterministic fallback)

### Runtime Files

4. **`aidm/runtime/session.py`**
   - `IntentEntry.logged_at` is now required (no default)
   - All `RuntimeSession` methods (`create_intent`, `update_intent`, `confirm_intent`, `retract_intent`, `resolve`, `process_input`) require explicit `timestamp` parameter
   - `process_input()` requires explicit `intent_id` parameter

5. **`aidm/core/session_log.py`**
   - `create_test_resolver()` now generates `result_id` and `resolved_at` at the call site via local imports

### Test Files

6. **`tests/test_boundary_law.py`** — Added 8 new enforcement tests:
   - `TestBL017_UUIDInjectionOnly` (3 tests): AST scan for uuid in default_factory across all schema files, IntentObject requires intent_id, EngineResult requires result_id
   - `TestBL018_TimestampInjectionOnly` (5 tests): AST scan for datetime in default_factory, IntentObject requires timestamps, EngineResult requires resolved_at, roundtrip preservation for IntentObject and EngineResult

7. **`tests/test_intent_lifecycle.py`** — All ~30 IntentObject() calls updated with explicit `intent_id`, `status`, `created_at`, `updated_at`; all `transition_to()` calls updated with `timestamp`

8. **`tests/test_engine_result.py`** — All EngineResult() and builder.build() calls updated with explicit `result_id` and `resolved_at`

9. **`tests/test_session_log.py`** — All construction calls updated with explicit values

10. **`tests/test_runtime_session.py`** — All construction calls and method calls updated with explicit IDs/timestamps

11. **`tests/test_spark_adapter.py`** — All EngineResult() direct construction calls updated

12. **`tests/test_m1_narration_guardrails.py`** — All EngineResult() construction calls updated

13. **`tests/test_narrator.py`** — All EngineResultBuilder().build() calls updated

14. **`tests/test_campaign_schemas.py`** — All CampaignManifest() calls updated with explicit `campaign_id`; `test_manifest_unique_ids` replaced with `test_manifest_preserves_injected_ids`

## File Touch Map

| File | Type | Changes |
|------|------|---------|
| `aidm/schemas/intent_lifecycle.py` | schema | Required fields, removed uuid import, inject-only factory |
| `aidm/schemas/engine_result.py` | schema | Required fields, removed uuid import, inject-only builder |
| `aidm/schemas/campaign.py` | schema | Required campaign_id, removed uuid import |
| `aidm/runtime/session.py` | runtime | Required timestamps/IDs on all methods |
| `aidm/core/session_log.py` | core | Explicit ID/timestamp in test resolver |
| `tests/test_boundary_law.py` | test | +8 new BL-017/018 enforcement tests |
| `tests/test_intent_lifecycle.py` | test | Updated ~30 call sites |
| `tests/test_engine_result.py` | test | Updated all call sites |
| `tests/test_session_log.py` | test | Updated all call sites |
| `tests/test_runtime_session.py` | test | Updated all call sites |
| `tests/test_spark_adapter.py` | test | Updated EngineResult calls |
| `tests/test_m1_narration_guardrails.py` | test | Updated EngineResult calls |
| `tests/test_narrator.py` | test | Updated builder.build() calls |
| `tests/test_campaign_schemas.py` | test | Updated CampaignManifest calls |

## Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| No `uuid.uuid4()` in any dataclass `default_factory` | PASS (AST scan in BL-017 test) |
| No `datetime.utcnow()`/`now()` in any dataclass `default_factory` | PASS (AST scan in BL-018 test) |
| `IntentObject()` without `intent_id` raises `TypeError` | PASS |
| `EngineResult()` without `result_id` raises `TypeError` | PASS |
| `EngineResult()` without `resolved_at` raises `TypeError` | PASS |
| `IntentObject()` without `created_at`/`updated_at` raises `TypeError` | PASS |
| Roundtrip preserves injected timestamps exactly | PASS |
| Full test suite passes | PASS (1692 passed, 0 failed) |

## Test Results

```
1692 passed, 0 failed, 43 warnings in 6.93s
```

Baseline was 1665 tests. Net gain of +27 tests (8 new BL-017/018 tests + 19 BL-020 tests from prior work).

## Notes

- `campaign.py` was not listed in the original work order's "Files in Scope", but the acceptance criteria ("No uuid.uuid4() in **any** dataclass defaults") required fixing it. The BL-017 AST scan caught the violation.
- `aidm/core/campaign_store.py` already used inject-at-call-site pattern (`campaign_id = str(uuid.uuid4())` before constructing `CampaignManifest`), so no changes were needed there.
- `build_failure()` and `build_aborted()` convenience methods on `EngineResultBuilder` retain `result_id: str = ""` and `resolved_at: Optional[datetime] = None` as parameters (not dataclass defaults), which is acceptable per the work order: "Factories/builders MAY have overridable convenience defaults."

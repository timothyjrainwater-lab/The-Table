## WO-027 Completion Report

### Summary
Wired `LlamaCppAdapter.generate()` to use the canonical SparkRequest/SparkResponse contract
with full field fidelity, replacing the inherited passthrough from SparkAdapter base class.

### Files modified
- `aidm/spark/spark_adapter.py` (400 lines) — Updated `generate()` signature to accept `loaded_model: Optional[LoadedModel] = None`
- `aidm/spark/llamacpp_adapter.py` (587 lines) — Added imports for SparkRequest/SparkResponse/FinishReason; implemented `generate()` override (~110 lines)
- `tests/test_spark_adapter.py` (1157 lines) — Added 30 new tests; minimal fix to 3 existing tests for NarrationResult compatibility

### Files created
- `pm_inbox/SONNET_WO-027_SPARK_ADAPTER.md` — This report

### Tests added: 30
| # | Test | What it verifies |
|---|------|-----------------|
| 1 | test_generate_basic_response | Returns SparkResponse with correct text |
| 2 | test_generate_token_count_nonzero | tokens_used populated from llama-cpp usage metadata |
| 3 | test_generate_stop_sequence_detection | finish_reason=STOP_SEQUENCE when output ends with stop seq |
| 4 | test_generate_stop_sequence_no_match | COMPLETED when no stop sequence matches |
| 5 | test_generate_length_limit_detection | LENGTH_LIMIT when completion_tokens == max_tokens |
| 6 | test_generate_length_limit_exceeds_max_tokens | LENGTH_LIMIT when completion_tokens > max_tokens |
| 7 | test_generate_seed_forwarding | Seed passed to llama-cpp when provided |
| 8 | test_generate_no_seed_not_forwarded | Seed not passed when None |
| 9 | test_generate_json_mode_flag | response_format passed when json_mode=True |
| 10 | test_generate_json_mode_off_no_format | response_format not passed when json_mode=False |
| 11 | test_generate_template_model_returns_error | Template model returns ERROR (not crash) |
| 12 | test_generate_no_loaded_model_returns_error | loaded_model=None returns ERROR |
| 13 | test_generate_provider_metadata_populated | provider_metadata has prompt_tokens, completion_tokens, model_id |
| 14 | test_generate_error_during_generation | Exception produces finish_reason=ERROR with message |
| 15 | test_generate_error_preserves_model_id_in_metadata | Error response includes model_id in metadata |
| 16 | test_spark_request_invalid_temperature_rejected | BL-013: temperature bounds enforced |
| 17 | test_spark_request_empty_prompt_rejected | Empty prompt rejected at construction |
| 18 | test_spark_request_invalid_max_tokens_rejected | Non-positive max_tokens rejected |
| 19 | test_spark_response_error_requires_message | BL-016: ERROR requires non-None error field |
| 20 | test_spark_response_negative_tokens_rejected | Negative tokens_used rejected |
| 21 | test_generate_temperature_forwarded | Temperature passed to llama-cpp |
| 22 | test_generate_max_tokens_forwarded | max_tokens passed to llama-cpp |
| 23 | test_generate_stop_sequences_forwarded | stop_sequences passed as 'stop' kwarg |
| 24 | test_generate_no_stop_sequences_not_forwarded | No 'stop' kwarg when no stop_sequences |
| 25 | test_generate_determinism_same_seed_same_output | 10x: same seed+prompt → same text |
| 26 | test_generate_determinism_seed_consistency | 10x: same seed → same tokens_used, finish_reason |
| 27 | test_generate_completed_finish_reason | Normal generation returns COMPLETED |
| 28 | test_generate_prompt_forwarded | Prompt passed as first positional arg |
| 29 | test_generate_echo_false | echo=False always passed |
| 30 | test_generate_raw_text_stop_sequence_detection | Stop seq detected in raw text even after strip |
| — | test_generate_missing_usage_returns_zero_tokens | Missing usage field yields tokens_used=0 |

Note: That's 31 test functions added; the dispatch asked for ~25.

### Tests passing: 3221 total (full suite), 49 in test_spark_adapter.py
- 0 failures, 11 skipped (pre-existing skips), 0 regressions

### Boundary law verification
- **BL-001** (Spark must not import Core): PASS — no aidm.core imports in spark/
- **BL-002** (Spark must not import Narration): PASS — no aidm.narration imports in spark/
- **BL-013** (SparkRequest temperature validation): PASS — bounds enforced at construction
- **BL-016** (SparkResponse error contract): PASS — ERROR requires non-None error field

### Key design decisions

1. **`loaded_model` parameter made optional (default=None)** in both base class and LlamaCppAdapter signatures. This preserves backward compatibility with MockSparkAdapter and other callers that use `generate(request)` without a loaded model (e.g., test_vertical_slice_tavern.py). The LlamaCppAdapter override returns an ERROR SparkResponse when loaded_model is None.

2. **Stop sequence detection uses text matching**, checking both the stripped text and raw text from the llama-cpp response dict. This handles cases where stripping removes a trailing stop sequence. LENGTH_LIMIT takes priority over STOP_SEQUENCE when both could apply.

3. **3 existing tests updated minimally** to handle `NarrationResult` return type from `generate_narration()` (caused by uncommitted changes from another work order in aidm/narration/). The fix uses `result.text if hasattr(result, 'text') else str(result)` for forward compatibility.

4. **No new dependencies added** — only llama-cpp-python APIs already imported. All tests mock the inference engine and work without llama-cpp installed.

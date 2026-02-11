## WO-031 Completion Report

### Files created/modified

| File | Lines before | Lines after | What changed |
|------|-------------|-------------|--------------|
| `aidm/spark/grammar_shield.py` | — (new) | 478 | New file: `GrammarShield`, `GrammarShieldConfig`, `ValidationResult`, exceptions (`GrammarValidationError`, `MechanicalAssertionError`, `JsonParseError`, `SchemaValidationError`), `MECHANICAL_PATTERNS` compiled at module level |
| `aidm/spark/llamacpp_adapter.py` | 588 | 638 | Added `generate_validated()` method (+50 lines), updated `typing` import to include `Any` |
| `aidm/spark/__init__.py` | 54 | 72 | Added Grammar Shield exports (`GrammarShield`, `GrammarShieldConfig`, `GrammarValidationError`, `MechanicalAssertionError`, `JsonParseError`, `SchemaValidationError`, `ValidationResult`) |
| `tests/test_grammar_shield.py` | — (new) | 591 | 32 new tests across 6 test classes |

### Tests added (32)

**JSON Validation (5):**
1. `test_valid_json_passes` — `{"key": "value"}` passes
2. `test_invalid_json_detected` — `"not json"` fails
3. `test_json_retry_succeeds` — first attempt bad JSON, retry good → passes
4. `test_json_retry_exhausted_raises` — all retries bad → raises `JsonParseError`
5. `test_json_not_checked_without_json_mode` — `json_mode=False` skips check

**Schema Validation (5):**
6. `test_valid_schema_passes` — output matches callable validator
7. `test_schema_mismatch_detected` — missing required field fails
8. `test_schema_retry_succeeds` — first mismatch, retry matches → passes
9. `test_schema_retry_exhausted_raises` — all retries mismatch → raises
10. `test_no_schema_skips_check` — `schema=None` skips validation

**Mechanical Assertion Detection (7):**
11. `test_clean_narration_passes` — "The orc roars in fury" passes
12. `test_damage_number_detected` — "deals 15 damage" detected
13. `test_ac_reference_detected` — "AC 18" detected
14. `test_rule_citation_detected` — "PHB 145" detected
15. `test_dice_notation_detected` — "2d6" detected
16. `test_dc_reference_detected` — "DC 15" detected
17. `test_assertion_retry_still_fails_raises` — all retries contain assertions → raises

**Retry Logic (4):**
18. `test_retry_budget_tracked` — `retries_used` incremented correctly
19. `test_retry_preserves_original_text` — original text stored in result
20. `test_retry_prompt_appends_constraint` — retry includes "Do NOT include specific numbers"
21. `test_no_retry_on_clean_output` — clean output → 0 retries

**Integration (4):**
22. `test_generate_validated_passthrough_no_shield` — `grammar_shield=None` → plain `generate()`
23. `test_generate_validated_with_shield_validates` — shield validates clean output
24. `test_generate_validated_metadata_includes_shield_info` — `provider_metadata` has `grammar_shield` key
25. `test_generate_validated_error_response_skips_validation` — `finish_reason=ERROR` skips validation

**Edge Cases (7):**
26. `test_hit_points_detected` — "25 hp" detected
27. `test_attack_bonus_detected` — "+5 to attack" detected
28. `test_die_roll_result_detected` — "rolled a 17" detected
29. `test_multiple_patterns_in_single_text` — multiple patterns in one text all detected
30. `test_config_disable_assertion_detection` — disabling detection allows mechanical text
31. `test_retry_temperature_caps_at_2_0` — retry temp increase caps at 2.0
32. `test_json_retry_appends_json_constraint` — JSON retry includes "MUST be valid JSON"

### Total test count

**3253 passed, 11 skipped, 0 failures** (full `python -m pytest tests/ -q`)

### Boundary law verification

- **BL-001**: `aidm/spark/` has no imports from `aidm.core` — PASS
- **BL-002**: `aidm/spark/` has no imports from `aidm.narration` — PASS
- Verified by running `test_boundary_law.py` — all 13 spark-related boundary tests pass

### Sample: clean narration passing

```
Input:  "The orc roars in fury, swinging its blade wildly."
Result: validate_only() returns [] (empty errors list)
→ Passes all three checks: JSON (skipped, not json_mode), schema (skipped, no schema), assertions (clean)
```

### Sample: mechanical assertion caught

```
Input:  "The sword deals 15 damage to the goblin."
Result: MechanicalAssertionError(
    matched_patterns=['damage_quantity'],
    matched_text=['15 damage'],
    full_text='The sword deals 15 damage to the goblin.'
)
→ Retry with stricter prompt, or raise to caller for KILL-002 signaling
```

### Key design decisions

1. **Layer independence**: `grammar_shield.py` imports only from `aidm.spark.spark_adapter` (SparkRequest, SparkResponse, FinishReason). No imports from core or narration. The caller in the narration layer catches `MechanicalAssertionError` to trigger KILL-002.

2. **Additive API**: `generate_validated()` added as a new method on `LlamaCppAdapter`. Existing `generate()` completely unchanged — no signature or behavior modifications.

3. **Per-request retry budget**: Each `validate_and_retry()` call starts fresh. No global retry counter or state. The `GrammarShield` instance is stateless.

4. **Module-level pattern compilation**: All 8 mechanical assertion regex patterns compiled once at module import via `re.compile()`. Not per-call. Stored in `MECHANICAL_PATTERNS` list.

5. **Schema validation without Pydantic dependency**: `_check_schema()` supports three modes: Pydantic model classes (via `model_validate`), callables (function validators), and dict-based JSON schemas (key presence). No Pydantic import in `grammar_shield.py`.

6. **Error priority in exhaustion**: When all retries fail, `_raise_final_error()` prioritizes `MechanicalAssertionError` > `JsonParseError` > `SchemaValidationError`. Mechanical assertions are the most critical (KILL-002 signal).

7. **Error response passthrough**: `generate_validated()` skips Grammar Shield validation when the initial `generate()` returns `finish_reason=ERROR` — no point validating an error response.

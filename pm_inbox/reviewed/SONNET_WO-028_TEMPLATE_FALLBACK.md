## WO-028 Completion Report

### Files modified

| File | Lines before | Lines after | What changed |
|------|-------------|-------------|--------------|
| `aidm/narration/guarded_narration_service.py` | 543 | 583 | Added `NarrationResult` dataclass, refactored `_generate_template_narration()` to use `NarrationTemplates` with `format_map` + `defaultdict`, changed `generate_narration()` return type to `NarrationResult` with provenance |
| `aidm/narration/__init__.py` | 24 | 27 | Added `NarrationResult` export |
| `tests/test_m1_narration_guardrails.py` | 547 | 844 | Updated existing tests for `NarrationResult` return type, added 20 new `TestTemplateFallbackChain` tests |

### Tests added: 20

All in `tests/test_m1_narration_guardrails.py::TestTemplateFallbackChain`:

1. `test_all_55_tokens_produce_non_empty_text` — all 58 tokens (>= 55) produce text
2. `test_attack_hit_template_text` — placeholder substitution for attack_hit
3. `test_attack_miss_template_text` — placeholder substitution for attack_miss
4. `test_critical_hit_template_text` — damage in critical_hit
5. `test_combat_maneuver_tokens` — all 18 maneuver tokens produce text
6. `test_unknown_token_falls_back_to_unknown_template` — bogus token → "Something happens..."
7. `test_none_token_falls_back` — None narration_token → "unknown" template
8. `test_placeholder_actor_replaced` — `{actor}` replaced, no raw placeholder in output
9. `test_placeholder_target_replaced` — `{target}` replaced
10. `test_placeholder_weapon_replaced` — `{weapon}` replaced
11. `test_placeholder_damage_replaced` — `{damage}` replaced with numeric value
12. `test_missing_actor_uses_safe_default` — no events → default actor, no crash
13. `test_missing_damage_uses_safe_default` — no damage event → "some damage"
14. `test_missing_all_placeholders_no_crash` — no events at all → safe defaults, no `{` in output
15. `test_template_provenance_tag` — template path → `[NARRATIVE:TEMPLATE]`
16. `test_template_provenance_on_llm_fallback` — LLM failure → provenance still `[NARRATIVE:TEMPLATE]`
17. `test_llm_exception_falls_back_to_template_silently` — no exception to caller
18. `test_kill_switch_blocks_template_narration` — KILL-001 blocks templates too
19. `test_freeze_001_enforced_on_template_path` — hash verification runs on template path
20. `test_narration_module_has_no_core_imports` — BL-003 boundary law check

### Tests passing: 3221 (0 failures, 11 skipped)

- 29 guardrail tests (9 original + 20 new) — all pass
- 21 narrator tests — all pass (unchanged)
- 3171 other tests — all pass (0 regressions)

### Template coverage

All 58 tokens in `NarrationTemplates.TEMPLATES` produce non-empty narration text when no LLM is loaded. The dispatch referenced 55 templates; the actual dictionary has 58 entries (3 additional combat tokens were added in prior work orders). All 58 are wired through the fallback path.

### Provenance tagging

- `[NARRATIVE]` — LLM-generated narration (set only when `_generate_llm_narration()` succeeds)
- `[NARRATIVE:TEMPLATE]` — Template-based narration (default; used when no LLM loaded, or LLM fails/is rejected)

Provenance is returned in `NarrationResult.provenance` — a structured field inspectable by callers, not embedded in the narration text.

### KILL-001 behavior

When the kill switch is active, `generate_narration()` raises `NarrationBoundaryViolation` **unconditionally** — both LLM and template paths are blocked. This is correct behavior: KILL-001 fires when memory mutation is detected, meaning the system integrity is compromised. Allowing template narration to continue would still be operating in a potentially corrupted state. The kill switch requires manual reset via `reset_kill_switch()` after root cause investigation.

### Boundary law verification

BL-003 confirmed passing. The `aidm/narration/` module imports:
- `aidm.narration.narrator` (intra-module)
- `aidm.narration.llm_query_interface` (intra-module, optional)
- `aidm.schemas.campaign_memory` (schemas, allowed)
- `aidm.schemas.engine_result` (schemas, allowed)
- `aidm.spark` (optional, allowed)

No imports from `aidm.core` — BL-003 intact.

### Key design decisions

1. **`NarrationResult` return type**: Changed `generate_narration()` from returning `str` to `NarrationResult(text, provenance)`. This is a breaking API change for callers, but necessary to expose provenance as a structured field. Updated all 9 existing tests that use the return value.

2. **`defaultdict` for safe placeholders**: Used `str.format_map()` with a `defaultdict(lambda: "something")` to handle unknown placeholder keys without crashing. Known keys (`actor`, `target`, `weapon`, `damage`) get domain-appropriate defaults ("someone", "someone", "an attack", "some damage").

3. **`NarrationContext.from_engine_result()` reuse**: Delegated context extraction to the existing `NarrationContext.from_engine_result()` method in `narrator.py` rather than duplicating the event-parsing logic. This keeps the extraction logic in one place.

4. **Template count**: The dispatch said 55 templates but the actual dictionary has 58. The test asserts `>= 55` rather than `== 55` to be forward-compatible with template additions.

5. **No new files**: All changes in existing files per design constraint.

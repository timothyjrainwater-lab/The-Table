# MEMO: WO-COMPILE-VALIDATE-001 / WO-NARRATION-VALIDATOR-001 Builder Findings
**From:** Agent (Opus 4.6), relaying builder debrief
**Date:** 2026-02-14
**Lifecycle:** NEW
**Builder commits:** `fb05aef` (COMPILE-VALIDATE), `2d923ed` (NARRATION-VALIDATOR)

---

## Findings

### 1. Pipeline Registration Gap (Structural)

WorldCompiler requires callers to manually register stages, but `RulebookStage`, `BestiaryStage`, `NPCArchetypeStage`, and now `CrossValidateStage` are all exported from `compile_stages/__init__.py` without being registered in production code. The compiler's stage list in practice is just `LexiconStage` + `SemanticsStage`. If cross-validation is meant to run in real compilations, someone needs to wire it.

**PM decision needed:** Is this intentional (stages only run in test/audit) or a wiring gap that needs a micro-WO?

### 2. content_id Bridge Is Dormant

`SpellDefinition.content_id` field exists and `play_loop` emits it, but actual spell definitions in `SPELL_REGISTRY` don't populate it. The GAP-B-001 pipeline (event → content_id → presentation_semantics lookup) is fully wired but produces `None` for every spell until someone maps runtime spell IDs to compile-time content_ids. This is the same finding the WEAPON-PLUMBING builder reported — the plumbing is wired but data is missing.

**PM decision needed:** Is this already tracked? If not, needs a data-population WO.

### 3. Test Pollution (~47 Phantom Failures)

Running the full suite in one shot produces ~47 failures that don't reproduce in isolation. `test_spark_adapter.py` and `test_template_narration_contract.py` appear to leak state that affects `test_play_loop_narration.py`. Not related to this WO's work, but a reliability concern for CI.

**PM decision needed:** Track as tech debt or draft a test isolation WO?

### 4. Pattern Inconsistency in maneuver_resolver.py (Cosmetic)

Bull rush and trip use explicit `if causal_chain_id is not None:` blocks to inject chain_id into payloads. Overrun, sunder, disarm, grapple use `**({...} if x else {})` dict unpacking. Both work, but two styles in the same file. Cosmetic only — no action needed unless a cleanup WO touches this file.

### 5. pm_inbox Hygiene Failures (Pre-Existing)

`test_pm_inbox_hygiene.py` consistently fails on active file count and lifecycle headers. Untracked files in `pm_inbox/research/` and debrief files push count over budget. This is a known operational issue — the inbox cap test needs to account for the research subdirectory, or the research files need a different home.

---

## Process Validation

Builder confirmed:
- **CompileStage protocol** (depends_on + topological sort) is clean and extensible — zero framework changes needed to add CrossValidateStage.
- **NarrativeBrief assembly pipeline** is purely additive — multi-target, conditions, causal chains landed without restructuring existing logic.
- **Test coverage and fixtures** are strong — `_make_rule_entry` / `_make_ability_entry` helpers are reusable patterns.
- **Boundary law tests** enforce clean layer separation effectively.

## Retrospective

The highest-signal items are #1 (pipeline registration gap) and #3 (test pollution). The registration gap means production compilations don't run cross-validation even though the stage exists — this is either intentional or a silent gap. The test pollution is a CI reliability issue that erodes trust in green test runs. Both are worth PM decisions before they compound.

## Operator-Level Recommendations (Session Review)

The following recommendations synthesize builder findings with operational context:

- **Test isolation WO** — The ~47 phantom failures (#3) need proper setup/teardown to prevent shared state between test files. This is a CI reliability issue that compounds as the test suite grows. Recommend a dedicated WO to identify and fix state leaks in `test_spark_adapter.py` and `test_template_narration_contract.py`.
- **Wire CrossValidateStage in production** — Finding #1 and the builder's "automated gap monitoring" suggestion point to the same thing: the stage exists but doesn't run. Wiring it into the default WorldCompiler stage list would make cross-validation automatic rather than test-only.
- **Resolver pattern unification** — The causal_chain_id inconsistency (#4) could be bundled into the resolver deduplication WO already in the PM action queue (P4). No separate WO needed.

## Builder Post-Commit Findings (Second Pass)

Builder committed both WOs (`fb05aef`, `2d923ed`) and flagged three additional items:

### 6. SPELL_REGISTRY content_id Population (Follow-Up WO)

SPELL_REGISTRY entries in `aidm/schemas/spell_definitions.py` don't set `content_id`. Until someone populates those (e.g., `content_id="spell.fireball_003"`), the runtime pipeline won't activate for actual gameplay. Reinforces finding #2. Builder suggests a dedicated WO to map runtime spell IDs to compile-time content_ids.

### 7. No Full Pipeline Integration Test

CrossValidateStage tests call `stage.execute()` directly with hand-written JSON. No test runs `WorldCompiler.compile()` with RulebookStage + SemanticsStage + CrossValidateStage all registered. If RulebookStage output format drifts from what CrossValidateStage expects, it won't be caught until a real compile.

**Builder suggests:** WO for end-to-end compile with all stages registered, verifying cross-validation catches a deliberately bad entry.

### 8. Fail-Open Behavior on Missing Dependencies

CrossValidateStage depends on `("semantics", "rulebook")`. If a production caller registers CrossValidateStage without RulebookStage, the topological sort runs it but `rule_registry.json` won't exist — the stage gracefully skips, meaning validation silently doesn't happen. Builder flags this as either fine (fail-open for optional stages) or a latent bug (should warn louder).

**PM decision needed:** Fail-open acceptable, or should missing dependency raise a warning?

### Test Results

5,775 tests pass, 14 failures (all pre-existing TTS/torchaudio environment issues). Zero regressions from either WO.

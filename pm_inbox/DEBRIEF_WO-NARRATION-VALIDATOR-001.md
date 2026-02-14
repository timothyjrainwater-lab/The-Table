# DEBRIEF: WO-NARRATION-VALIDATOR-001

**Builder:** Claude Opus 4.6 (Session 2)
**Lifecycle:** NEW
**Commit (source):** 6369806 — `feat: PM review cycle — scope amendments, archive 13 files, builder code stubs`
**Commit (tests):** 2d923ed — `test(WO-NARRATION-VALIDATOR-001): 46 tests for NarrationValidator rules + integration`
**Date:** 2026-02-14
**Verdict:** COMPLETE — all success criteria met

---

## 1. Full Context Dump

### What Was Built

Seven validation rules in a new `NarrationValidator` class that compares Spark narration text against the NarrativeBrief truth frame. Returns PASS/WARN/FAIL with actionable rule IDs.

### Changes Delivered

| Change | Description | File(s) |
|--------|-------------|---------|
| 1 | `ValidationResult` + `RuleViolation` frozen dataclasses | `aidm/narration/narration_validator.py` |
| 2 | P0 negative rules: RV-001, RV-002, RV-008 (FAIL) | `aidm/narration/narration_validator.py` |
| 3 | P1 positive rules: RV-003, RV-004 (WARN), plus Layer B dormant guards RV-005 (FAIL), RV-007 (WARN) | `aidm/narration/narration_validator.py` |
| 4 | Integration into `GuardedNarrationService` (validator call after ContradictionChecker, FAIL → template fallback, WARN → log + emit) | `aidm/narration/guarded_narration_service.py` |
| 5 | Keyword list reuse from `ContradictionChecker` (HIT/MISS/DEFEAT/STANDING/SEVERITY lists imported, not duplicated) | `aidm/narration/narration_validator.py` imports |
| 6 | Narration persistence hook — session JSONL with narration_text, source_event_ids, validation_verdict, violations, timestamp | `aidm/narration/guarded_narration_service.py` (`_persist_narration_log`) |

### Rule Inventory

| Rule | Type | Severity | What It Checks |
|------|------|----------|----------------|
| RV-001 | P0 Negative | FAIL | Hit narration has no miss-language; miss narration has no hit-language |
| RV-002 | P0 Negative | FAIL | Defeat narration has no standing-language; non-defeat has no defeat-language |
| RV-008 | P0 Negative | FAIL | Resisted spell has no full-effect language; spell damage has no shrug-off language |
| RV-005 | P0 Negative (Layer B) | FAIL | Narration contains no contraindicated terms from presentation_semantics |
| RV-003 | P1 Positive | WARN | Minor severity has no inflation language; lethal has no deflation language |
| RV-004 | P1 Positive | WARN | Applied/removed conditions referenced in narration (soft keyword match) |
| RV-007 | P1 Positive (Layer B) | WARN | Delivery mode reflected in narration language (cone → directional, etc.) |

### Integration Pipeline Position

```
Spark generates text
  → KILL-002 mechanical assertion check
  → KILL-003 token overflow check
  → KILL-004 latency check
  → ContradictionChecker (WO-058)
  → NarrationValidator (THIS WO)     ← FAIL triggers template fallback
  → _persist_narration_log()          ← always runs, JSONL append
  → return NarrationResult
```

### Test Coverage

46 tests in `tests/test_narration_validator.py`:

| Test Class | Count | Coverage |
|------------|-------|----------|
| TestRV001HitMiss | 6 | Hit/miss/critical language detection, non-attack skip |
| TestRV002Defeat | 4 | Defeat/standing language consistency |
| TestRV008SaveResult | 4 | Spell resist/damage language |
| TestRV003Severity | 4 | Inflation/deflation alignment, unchecked severity pass |
| TestRV004Condition | 6 | Applied/removed mention, unknown condition fallback |
| TestRV005Contraindications | 4 | Layer B dormant guard, contraindicated term detection |
| TestRV007DeliveryMode | 4 | Layer B dormant guard, delivery mode language |
| TestValidationResult | 5 | Structure, frozen immutability, verdict precedence |
| TestGuardedNarrationServiceIntegration | 4 | Attribute presence, custom validator/log_path injection |
| TestNarrationPersistence | 5 | JSONL write, multiple entries, None brief, disabled path |

Full suite result: **5,775 passed**, 14 pre-existing failures (TTS/inbox hygiene — unrelated).

### Architectural Decisions

1. **NarrationValidator is a separate class from ContradictionChecker.** CC handles Class A/B/C contradictions with response policies (retry, template, annotate). NV handles rule-based structural validation with PASS/WARN/FAIL verdicts. NV *imports* CC's keyword lists but does not call CC methods.

2. **Layer B rules are built but dormant.** RV-005 and RV-007 check `presentation_semantics` and gracefully return empty violation lists when `presentation_semantics is None`. When content_id emission lands (GAP-B-001), these rules activate automatically with zero code changes.

3. **Persistence writes to append-only JSONL.** One JSON line per narration pass, always written (PASS, WARN, or FAIL), even for template fallbacks. Disabled when `narration_log_path is None` (default). This is the prerequisite for H3 Transparency Gem and Replay Journal.

4. **`_compile_keywords()` reused from ContradictionChecker.** Save-result keywords and condition mention maps are new to this module but use the same compilation pattern.

---

## 2. PM Summary

All 6 changes delivered. 7 validation rules implemented (3 P0 FAIL, 4 P1 WARN including 2 Layer B dormant). GuardedNarrationService integration wired after ContradictionChecker — FAIL triggers template fallback, WARN logs + emits. Narration persistence JSONL appends every pass. 46 tests, zero regressions.

---

## 3. Retrospective

### What Went Well

- Keyword list reuse from ContradictionChecker was clean — the `_compile_keywords` function and all constant lists were already module-level, importable without modification.
- The condition mention map (`_CONDITION_MENTION_MAP`) provides 18 D&D 3.5e conditions with synonym lists, giving soft-match coverage that should catch most reasonable narration phrasings.
- The test suite exercises both positive (correct narration passes) and negative (bad narration caught) cases for every rule.

### Observations for PM

- **RV-005 is currently classified as P0 (FAIL) in the dispatch, but it's a Layer B dormant guard.** When content_id emission lands, contraindication violations will immediately trigger template fallback. PM should confirm this is the desired severity — an alternative would be WARN during initial rollout.
- **Condition removal detection (RV-004) uses a hardcoded removal phrase list** ("no longer", "shakes off", "recovers", "breaks free", "gets up", "rises", "stands"). This is pragmatic but may miss creative phrasings. A future WO could expand this with an LLM-assisted synonym pass.
- **Save result keywords (RV-008) are new to this module**, not imported from ContradictionChecker. If CC ever needs the same lists, they should be consolidated to avoid drift.

---

*End of debrief.*

# WO-NARRATION-VALIDATOR-001: Runtime Narration Validation

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 1
**Priority:** P1 — Content trust. Three P0 rules prevent mechanically-wrong narration from reaching players.
**Source:** RQ-SPRINT-005 (Content Trust Verification), RQ-SPRINT-004 (Spark Containment), RQ_NARR_001_SYNTHESIS
**Depends on:** WO-BRIEF-WIDTH-001 (for condition fields). Layer B fields already wired via GAP-B-001 (commit e9a9371, dormant until events emit content_id).

---

## Target Lock

Add a `NarrationValidator` that compares Spark's narration text against the NarrativeBrief truth frame. Currently, `ContradictionChecker` handles Class A/B/C contradictions and `GrammarShield` catches mechanical assertions — but there is no unified validation pass that returns PASS/WARN/FAIL with actionable rule IDs.

This WO builds the P0 negative rules (must-not-violate) and the structural P1 positive rules (must-be-consistent-with).

## Binary Decisions

1. **New class or extend ContradictionChecker?** New class `NarrationValidator` in `aidm/narration/narration_validator.py`. ContradictionChecker stays as-is — NarrationValidator consumes it as one input.
2. **Where in the pipeline?** After Spark generates text, before emit. Slot into `GuardedNarrationService` between Spark output and the existing kill-switch checks.
3. **Return type?** `ValidationResult` dataclass with `verdict: Literal["PASS", "WARN", "FAIL"]`, `rule_violations: list[RuleViolation]`, each violation carrying `rule_id`, `severity`, `detail`.
4. **Response policy?** FAIL → template fallback (same as ContradictionChecker Class A/B). WARN → emit text + log for post-session review.
5. **Layer B positive rules — dormant or active?** Build the code. Rules that check `presentation_semantics` fields will no-op when those fields are None (GAP-B-001 pipeline is wired but dormant). When content_id emission lands, rules activate automatically.

## Contract Spec

### Change 1: ValidationResult and RuleViolation Data Classes

New file `aidm/narration/narration_validator.py`:

```python
@dataclass(frozen=True)
class RuleViolation:
    rule_id: str       # "RV-001", "RV-002", etc.
    severity: str      # "FAIL" or "WARN"
    detail: str        # Human-readable explanation

@dataclass(frozen=True)
class ValidationResult:
    verdict: str       # "PASS", "WARN", "FAIL"
    violations: tuple  # Tuple of RuleViolation
```

### Change 2: P0 Negative Rules (3 rules — FAIL on violation)

**RV-001: Hit/Miss Consistency**
- If `action_type == "attack_hit"`: narration must NOT contain miss-language (MISS_KEYWORDS from ContradictionChecker)
- If `action_type == "attack_miss"`: narration must NOT contain hit-language (HIT_KEYWORDS)
- Severity: FAIL

**RV-002: Defeat Consistency**
- If `target_defeated == True`: narration must NOT contain language implying target continues fighting (STANDING_KEYWORDS)
- If `target_defeated == False`: narration must NOT contain defeat-language (DEFEAT_KEYWORDS)
- Severity: FAIL

**RV-008: Save Result Consistency**
- If `action_type == "spell_resisted"`: narration must NOT describe full unmitigated effect
- If `action_type == "spell_damage_dealt"`: narration must NOT describe target shrugging off the spell
- Severity: FAIL

These rules reuse the existing keyword lists from `ContradictionChecker`. Import them, don't duplicate them.

### Change 3: P1 Positive/Structural Rules (4 rules — WARN on violation)

**RV-003: Severity-Narration Alignment**
- If `severity == "minor"`: narration must NOT contain severity-inflation keywords
- If `severity == "lethal"` or `severity == "devastating"`: narration must NOT contain severity-deflation keywords
- Severity: WARN

**RV-004: Condition Consistency**
- If `condition_applied` is set: narration should reference the condition (soft match — at least one keyword)
- If `condition_removed` is set: narration should reference removal
- Severity: WARN

**RV-005: Contraindication Enforcement** (Layer B — dormant until content_id lands)
- If `presentation_semantics.contraindications` is non-empty: narration must NOT contain any contraindicated term
- Severity: FAIL
- Guard: if `presentation_semantics is None`, skip this rule

**RV-007: Delivery Mode Consistency** (Layer B — dormant until content_id lands)
- If `presentation_semantics.delivery_mode` is set: narration should contain language consistent with delivery mode (e.g., CONE → directional language)
- Severity: WARN
- Guard: if `presentation_semantics is None`, skip this rule

### Change 4: Integration into GuardedNarrationService

In `aidm/narration/guarded_narration_service.py`:
- After Spark generates text, call `NarrationValidator.validate(narration_text, brief)`
- If verdict == FAIL: treat as Class A/B contradiction (retry, then template fallback)
- If verdict == WARN: log violations, emit text
- If verdict == PASS: emit text

### Change 5: Expose Keyword Lists from ContradictionChecker

The keyword lists (HIT_KEYWORDS, MISS_KEYWORDS, DEFEAT_KEYWORDS, STANDING_KEYWORDS, SEVERITY_INFLATION, SEVERITY_DEFLATION) currently live as module-level constants in `contradiction_checker.py`. They stay there — NarrationValidator imports them. No duplication.

### Constraints

- Do NOT modify ContradictionChecker's existing logic — validator is additive
- Do NOT modify GrammarShield — those checks remain independent
- Do NOT add kill switches — use existing kill-switch infrastructure
- Do NOT implement streaming validation — validate complete text only
- Do NOT build a synonym index for positive validation yet — use direct keyword matching for now
- Layer B rules MUST gracefully no-op when presentation_semantics is None
- All existing narration tests must pass without modification

### Boundary Laws Affected

- BL-021 (TruthChannel contract): NOT AFFECTED — validator reads the truth frame, doesn't modify it
- No mechanical boundary laws affected — narration layer only

## Success Criteria

- [ ] `NarrationValidator` class exists in `aidm/narration/narration_validator.py`
- [ ] `ValidationResult` and `RuleViolation` dataclasses defined
- [ ] RV-001 catches hit/miss contradiction
- [ ] RV-002 catches defeat contradiction
- [ ] RV-008 catches save result contradiction
- [ ] RV-003 catches severity inflation/deflation
- [ ] RV-004 checks condition mention
- [ ] RV-005 enforces contraindications (no-ops when presentation_semantics is None)
- [ ] RV-007 checks delivery mode consistency (no-ops when presentation_semantics is None)
- [ ] GuardedNarrationService calls validator after Spark output
- [ ] FAIL verdict triggers template fallback
- [ ] WARN verdict logs but emits text
- [ ] All existing tests pass without modification
- [ ] New tests: one per rule (RV-001 through RV-008 where implemented), integration test with GuardedNarrationService

## Files Expected to Change

- New: `aidm/narration/narration_validator.py`
- `aidm/narration/guarded_narration_service.py` — integration point
- `aidm/narration/contradiction_checker.py` — export keyword lists (may already be importable)
- Test files for validator rules and integration

## Files NOT to Change

- `aidm/narration/grammar_shield.py` — independent check
- `aidm/spark/` — Spark generation untouched
- `aidm/core/` — no resolver changes
- Gold masters — no mechanical behavior change

## PM Amendment (2026-02-14): Narration-to-Event Persistence

**Bundled scope addition per roadmap audit (MEMO_ROADMAP_AUDIT §3.2).**

### Change 6: Narration Persistence Hook

At the NarrationValidator output point (after verdict is determined, whether PASS, WARN, or FAIL), persist:

```python
{
    "narration_text": str,          # Spark's output (or template fallback)
    "source_event_ids": tuple,      # From NarrativeBrief.source_event_ids
    "validation_verdict": str,      # "PASS", "WARN", or "FAIL"
    "violations": list,             # RuleViolation details (empty if PASS)
    "timestamp": str                # ISO 8601
}
```

Write to a session-scoped JSONL file (e.g., `narration_log.jsonl` alongside the event log). This enables post-session narration quality analysis and is a prerequisite for H3 audit UX (Transparency Gem, Replay Journal).

**Additional success criterion:**
- [ ] Narration text + source_event_ids + validation verdict persisted to session JSONL after every narration pass

---

## Delivery

When all success criteria are met:

1. `git add` all changed and new files
2. `git commit` with a descriptive message referencing WO-NARRATION-VALIDATOR-001
3. Write your debrief to `pm_inbox/DEBRIEF_WO-NARRATION-VALIDATOR-001.md`

Do NOT submit a debrief without a commit. The commit hash goes in the debrief header.

---

*End of WO-NARRATION-VALIDATOR-001*

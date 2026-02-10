# M2 PR Gate Checklist
## Mandatory Verification Before Merge

**Document Type:** Governance / PR Gate
**Status:** ✅ **BINDING** (M2+)
**Date:** 2026-02-10
**Authority:** PM (Aegis)

---

## 1. Purpose

**This checklist defines mandatory verification steps for ALL PRs during M2 development.**

**Gate Condition:** ALL checks MUST pass before PR approval.

**Scope:** Any PR modifying M2-related code (SPARK, campaign prep pipeline, model selection, configuration)

---

## 2. PR Gate Checks

### CHECK-001: Test Suite Passes

**Requirement:** All existing tests MUST pass.

**Verification:**
```bash
pytest tests/ --maxfail=1
```

**Pass Criteria:**
- ✅ 0 test failures
- ✅ Test execution time < 10 seconds (M2 speed requirement)

**Fail Criteria:**
- ❌ Any test failure
- ❌ Test suite regression (new tests slow down suite)

---

### CHECK-002: Code Coverage Maintained

**Requirement:** Code coverage MUST NOT decrease.

**Verification:**
```bash
pytest --cov=aidm --cov-report=term-missing
```

**Pass Criteria:**
- ✅ Coverage ≥ baseline (current coverage from main branch)
- ✅ All new code has tests (no untested lines in diff)

**Fail Criteria:**
- ❌ Coverage decreased from baseline
- ❌ New code added without corresponding tests

---

### CHECK-003: Determinism Preserved

**Requirement:** RNG-dependent code MUST be deterministic (seeded).

**Verification:**
- Manual review: All `random.randint()`, `random.choice()`, etc. use seeded `Random()` instance
- Check for global `random` module usage (should use `world_state.rng` or equivalent)

**Pass Criteria:**
- ✅ All randomness uses seeded RNG
- ✅ No global `random` module usage in deterministic code

**Fail Criteria:**
- ❌ Unseeded randomness detected
- ❌ Global `random.randint()` used in BOX or event log code

---

### CHECK-004: No Hard-Coded Mechanics

**Requirement:** Game rules MUST come from data files, NOT hard-coded constants.

**Verification:**
- Review diff for hard-coded damage values, AC bonuses, skill DCs
- Ensure all mechanics reference data tables or configuration

**Pass Criteria:**
- ✅ No hard-coded game constants (all from data files)
- ✅ Magic numbers documented (if unavoidable, with rationale)

**Fail Criteria:**
- ❌ Hard-coded mechanics detected (e.g., `damage = 1d8 + 3` in code)
- ❌ Undocumented magic numbers

---

### CHECK-005: Spark/Lens/Box Separation

**Requirement:** SPARK, LENS, and BOX layers MUST remain separate.

**Verification:**
- Ensure SPARK never computes mechanics (BOX responsibility)
- Ensure BOX never calls SPARK for decisions (determinism)
- Ensure LENS filters SPARK output (no bypass)

**Pass Criteria:**
- ✅ SPARK generates text only (no mechanical claims)
- ✅ BOX computes mechanics independently
- ✅ LENS gates all SPARK output

**Fail Criteria:**
- ❌ SPARK computes damage, hit/miss, or legality
- ❌ BOX delegates decisions to SPARK
- ❌ SPARK output presented without LENS filtering

---

### CHECK-006: Event Log Completeness

**Requirement:** All game-state-changing events MUST be logged.

**Verification:**
- Ensure all BOX computations emit event log entries
- Verify event log includes all fields (timestamp, type, result, metadata)

**Pass Criteria:**
- ✅ All state changes logged
- ✅ Event log schema valid

**Fail Criteria:**
- ❌ State change without corresponding event log entry
- ❌ Malformed event log entries

---

### CHECK-007: No External Dependencies Without Justification

**Requirement:** New dependencies MUST be justified and approved by PM.

**Verification:**
- Check `pyproject.toml` for new dependencies
- Verify PM approval for any new libraries

**Pass Criteria:**
- ✅ No new dependencies, OR
- ✅ New dependencies approved by PM with justification

**Fail Criteria:**
- ❌ Unapproved dependencies added
- ❌ Dependencies without justification

---

### ✨ CHECK-008: Spark Swappability (NEW — M2 Invariant)

**Requirement:** SPARK MUST be user-swappable via configuration, NOT hard-coded.

**Verification:**
```bash
bash scripts/audit_spark_swappability.sh
```

**Pass Criteria:**
- ✅ Audit script exits with code 0 (all checks passed)
- ✅ No hard-coded model paths or provider names
- ✅ All capability usage validated
- ✅ No SPARK output bypasses LENS/BOX

**Fail Criteria:**
- ❌ Audit script fails (violations detected)
- ❌ Any STOP condition triggered (STOP-001 through STOP-005)

**Detailed Specification:** [PR_GATE_CHECK_008_SPARK_SWAPPABILITY.md](PR_GATE_CHECK_008_SPARK_SWAPPABILITY.md)

**Authority:** [docs/doctrine/SPARK_SWAPPABLE_INVARIANT.md](../doctrine/SPARK_SWAPPABLE_INVARIANT.md)

---

### CHECK-009: Documentation Updated

**Requirement:** User-facing changes MUST include documentation updates.

**Verification:**
- If PR adds features, ensure README or docs updated
- If PR changes configuration, ensure example configs updated

**Pass Criteria:**
- ✅ Documentation reflects new features
- ✅ Configuration examples up-to-date

**Fail Criteria:**
- ❌ Features added without documentation
- ❌ Configuration changed without examples

---

### CHECK-010: No Breaking Changes Without Migration Path

**Requirement:** Breaking changes MUST include migration guide.

**Verification:**
- Check for API changes, schema changes, configuration changes
- Ensure migration path documented if breaking changes detected

**Pass Criteria:**
- ✅ No breaking changes, OR
- ✅ Breaking changes with migration guide

**Fail Criteria:**
- ❌ Breaking changes without migration path
- ❌ Undocumented schema changes

---

## 3. Checklist Workflow

### 3.1 Submitter Responsibilities (Before PR Submission)

**Required Actions:**
1. Run test suite locally: `pytest tests/`
2. Run CHECK-008 audit: `bash scripts/audit_spark_swappability.sh`
3. Review diff against all 10 checks
4. Fix any violations before submitting PR
5. Include checklist completion in PR description:

**PR Description Template:**
```markdown
## Description

[What this PR does]

## PR Gate Checklist

- [x] CHECK-001: Test Suite Passes (pytest passed locally)
- [x] CHECK-002: Code Coverage Maintained (coverage >= baseline)
- [x] CHECK-003: Determinism Preserved (all RNG seeded)
- [x] CHECK-004: No Hard-Coded Mechanics (rules from data files)
- [x] CHECK-005: Spark/Lens/Box Separation (layers isolated)
- [x] CHECK-006: Event Log Completeness (all state changes logged)
- [x] CHECK-007: No External Dependencies (or PM approved)
- [x] CHECK-008: Spark Swappability (audit script passed)
- [x] CHECK-009: Documentation Updated (if applicable)
- [x] CHECK-010: No Breaking Changes (or migration guide included)

## Audit Script Output (CHECK-008)

```
[Paste output of scripts/audit_spark_swappability.sh here]
```

## Test Results

```
[Paste pytest output here]
```
```

---

### 3.2 Reviewer Responsibilities (During PR Review)

**Required Actions:**
1. Re-run test suite on PR branch: `pytest tests/`
2. Re-run CHECK-008 audit: `bash scripts/audit_spark_swappability.sh`
3. Manually review diff against checks 3-7, 9-10
4. Verify PR description includes checklist completion
5. Request changes if any check fails
6. Approve only if ALL checks pass

**Review Approval Template:**
```markdown
## PR Gate Review

**Reviewer:** [Name]
**Date:** YYYY-MM-DD

### Automated Checks

- [x] CHECK-001: Test Suite Passes ✅
- [x] CHECK-002: Code Coverage Maintained ✅
- [x] CHECK-008: Spark Swappability ✅

### Manual Checks

- [x] CHECK-003: Determinism Preserved ✅
- [x] CHECK-004: No Hard-Coded Mechanics ✅
- [x] CHECK-005: Spark/Lens/Box Separation ✅
- [x] CHECK-006: Event Log Completeness ✅
- [x] CHECK-007: No External Dependencies ✅
- [x] CHECK-009: Documentation Updated ✅
- [x] CHECK-010: No Breaking Changes ✅

**Status:** ✅ APPROVED / ❌ CHANGES REQUESTED

**Notes:** [Any observations or recommendations]
```

---

### 3.3 Merge Gate (Before Merge)

**Final Verification:**
1. PR approved by reviewer
2. All checks passed (10/10)
3. No unresolved review comments
4. No merge conflicts with main branch

**Only after all 4 conditions met:** Merge PR

---

## 4. Exemptions and Overrides

**PM (Aegis) may grant exemptions for:**
- CHECK-007 (new dependencies) — if justified and approved
- CHECK-010 (breaking changes) — if migration guide provided

**PM CANNOT grant exemptions for:**
- CHECK-001 (test failures) — NO exemptions, tests MUST pass
- CHECK-003 (determinism) — Determinism is sacred, non-negotiable
- CHECK-005 (Spark/Lens/Box separation) — Architectural principle, non-negotiable
- CHECK-008 (Spark swappability) — M2 invariant, binding

**Exemption Request Process:**
1. Submitter documents justification in PR description
2. Submitter requests exemption from PM (Aegis)
3. PM reviews and approves/denies
4. If approved, PM documents exemption in PR comments
5. Exemption included in merge commit message

---

## 5. Enforcement

**Violations:**
- Any check failure → PR REJECTED (no merge until fixed)
- Bypassing PR gate → Governance violation (escalation to PM)
- Falsifying checklist → Immediate escalation to PM

**Accountability:**
- Submitter responsible for pre-submission verification
- Reviewer responsible for re-verification
- PM responsible for exemption decisions

---

## 6. Integration with M2 Acceptance Tests

**PR gate checks are PREREQUISITES for acceptance testing.**

**Relationship:**
- **PR Gate Checks (this document)** = Per-PR verification (code quality, compliance)
- **Acceptance Tests** ([M2_ACCEPTANCE_SPARK_SWAPPABILITY.md](M2_ACCEPTANCE_SPARK_SWAPPABILITY.md)) = End-to-end validation (runtime behavior)

**M2 Completion Requires BOTH:**
1. ✅ All PRs pass PR gate checks (no violations in codebase)
2. ✅ All 6 acceptance tests pass (runtime swappability verified)

---

## 7. Compliance Statement

**This checklist is BINDING for M2+.**

**All PRs MUST:**
- ✅ Pass all 10 checks before merge
- ✅ Include checklist completion in PR description
- ✅ Re-verified by reviewer before approval

**No PR may be merged without:**
- ✅ Reviewer approval
- ✅ All checks passed (10/10)
- ✅ No unresolved review comments

---

**END OF M2 PR GATE CHECKLIST**

**Date:** 2026-02-10
**Agent:** Agent D (Research Orchestrator)
**Authority:** PM (Aegis)
**Status:** ✅ **BINDING** (M2 gate requirement)
**Signature:** Agent D (Research Orchestrator) — 2026-02-10

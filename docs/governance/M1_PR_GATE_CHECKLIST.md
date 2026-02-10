# M1 PR Gate Checklist
## Strict Pass/Fail Review for M1 Pull Requests

**Document Type:** Governance / Code Review Gate
**Purpose:** Enforceable pass/fail checklist for all M1 PRs
**Agent:** Agent D (Research Orchestrator)
**Date:** 2026-02-10
**Status:** ACTIVE (mandatory for all M1 PRs)
**Authority:** PR MUST pass ALL checks to merge

---

## 1. Purpose Statement

**This checklist is STRICT PASS/FAIL.**

- ✅ **PASS:** ALL checks pass → PR approved for merge
- ❌ **FAIL:** ANY check fails → PR rejected, return to author

**No subjective interpretation allowed.** Each check is binary (yes/no).

**Reviewer authority:** Any reviewer may REJECT on sight if any check fails.

---

## 2. Mandatory Pre-Merge Checks

### CHECK-001: No Schema Diff

**Question:** Does this PR modify any schema files?

**Files to Check:**
- `aidm/schemas/campaign_memory.py`
- `aidm/schemas/canonical_ids.py`
- `aidm/schemas/immersion.py`
- Any file in `aidm/schemas/` directory

**Pass Criteria:**
- ✅ NO modifications to schema files
- ✅ OR: Schema modifications have explicit PM approval comment in PR

**Fail Criteria:**
- ❌ Schema files modified WITHOUT PM approval

**Verification Command:**
```bash
git diff main...HEAD -- aidm/schemas/
# Should return empty (no diff) OR include PM approval comment
```

**Reviewer Action:**
- ✅ PASS: No schema diff OR PM approval present → Continue to CHECK-002
- ❌ FAIL: Schema modified without PM approval → REJECT PR immediately

**Rejection Message Template:**
```
❌ CHECK-001 FAILED: Schema Modification Without PM Approval

This PR modifies schema files without PM approval:
- [list modified files]

Required Action:
1. Obtain PM approval for schema changes, OR
2. Remove schema modifications from this PR

Reference: M1_PR_GATE_CHECKLIST.md CHECK-001
```

---

### CHECK-002: No Narration Write Path

**Question:** Does this PR create any code path where narration can write to indexed memory?

**Code Patterns to Reject:**
- `narration_text` → `SessionLedgerEntry.add_fact()`
- `llm_output` → `memory.update()`
- Any function that extracts facts from narration and writes without validation

**Pass Criteria:**
- ✅ NO narration → memory write paths
- ✅ OR: All narration-derived writes go through `validate_fact_exists_in_memory()` first

**Fail Criteria:**
- ❌ Direct narration → memory write detected
- ❌ Fact extraction without validation gate

**Verification Command:**
```bash
# Search for narration write patterns
grep -r "narration.*add_fact\|narration.*update\|llm_output.*write" --include="*.py" aidm/
# Should return 0 results OR all results include validation
```

**Reviewer Action:**
- ✅ PASS: No direct write paths OR all writes validated → Continue to CHECK-003
- ❌ FAIL: Unvalidated narration write detected → REJECT PR immediately

**Rejection Message Template:**
```
❌ CHECK-002 FAILED: Narration Write Path Without Validation

This PR creates a code path where narration can write to memory without validation:
- [file:line] shows narration_text → add_fact() without validate_fact_exists_in_memory()

Required Action:
1. Add validation gate: validate_fact_exists_in_memory(fact) before write
2. OR: Route write through event-sourced path (require event_id)

Reference: M1_PR_GATE_CHECKLIST.md CHECK-002
Guardrail: INV-DET-002 (Event-Sourced Writes Only)
```

---

### CHECK-003: Temperature Clamps Enforced

**Question:** Do all LLM query functions enforce temperature ≤0.5?

**Code Patterns to Check:**
- `query_memory()` functions MUST have `temperature ≤ 0.5`
- `generate_narration()` functions MUST have `temperature ≥ 0.7`
- NO shared temperature parameter between query and narration

**Pass Criteria:**
- ✅ All query functions use hardcoded `temperature ≤ 0.5`
- ✅ All narration functions use hardcoded `temperature ≥ 0.7`
- ✅ No shared temperature variable

**Fail Criteria:**
- ❌ Query function with `temperature > 0.5`
- ❌ Narration function with `temperature < 0.7`
- ❌ Shared temperature parameter (risk of cross-contamination)

**Verification Command:**
```bash
# Check query functions for low temperature
grep -A5 "def query_memory\|def query_session\|def retrieve" aidm/ -r --include="*.py" | grep "temperature"
# All should show ≤0.5

# Check narration functions for high temperature
grep -A5 "def generate_narration\|def narrate" aidm/ -r --include="*.py" | grep "temperature"
# All should show ≥0.7
```

**Reviewer Action:**
- ✅ PASS: Temperature clamps correct → Continue to CHECK-004
- ❌ FAIL: Temperature violation detected → REJECT PR immediately

**Rejection Message Template:**
```
❌ CHECK-003 FAILED: Temperature Clamp Violation

This PR violates temperature isolation:
- [file:line] query function uses temperature > 0.5
- OR: [file:line] narration function uses temperature < 0.7

Required Action:
1. Query functions MUST use temperature ≤ 0.5
2. Narration functions MUST use temperature ≥ 0.7
3. Do NOT share temperature parameters

Reference: M1_PR_GATE_CHECKLIST.md CHECK-003
Guardrail: INV-DET-003 (Temperature Isolation)
```

---

### CHECK-004: Hash Freeze Enforced

**Question:** Do all narration generation functions log pre/post memory hash and assert stability?

**Required Code Pattern:**
```python
def generate_narration(memory_snapshot):
    hash_before = hash(memory_snapshot.to_dict())
    logger.info(f"PRE_NARRATION_HASH: {hash_before}")

    # ... narration generation ...

    hash_after = hash(memory_snapshot.to_dict())
    logger.info(f"POST_NARRATION_HASH: {hash_after}")
    assert hash_before == hash_after, "KILL-001: Memory mutated during narration"
```

**Pass Criteria:**
- ✅ All narration functions log pre/post hash
- ✅ All narration functions assert hash stability
- ✅ KILL-001 trigger armed (raises exception on mutation)

**Fail Criteria:**
- ❌ Narration function missing hash logging
- ❌ Narration function missing stability assertion
- ❌ KILL-001 not armed

**Verification Command:**
```bash
# Check all narration functions for hash freeze
grep -A20 "def generate_narration\|def narrate" aidm/ -r --include="*.py" | grep "PRE_NARRATION_HASH\|POST_NARRATION_HASH\|assert.*hash"
# All narration functions should show both logs + assertion
```

**Reviewer Action:**
- ✅ PASS: Hash freeze enforced → Continue to CHECK-005
- ❌ FAIL: Hash freeze missing → REJECT PR immediately

**Rejection Message Template:**
```
❌ CHECK-004 FAILED: Hash Freeze Not Enforced

This PR adds narration generation without hash freeze enforcement:
- [file:line] generate_narration() missing PRE_NARRATION_HASH log
- [file:line] generate_narration() missing POST_NARRATION_HASH log
- [file:line] generate_narration() missing hash stability assertion

Required Action:
1. Add hash logging BEFORE narration generation
2. Add hash logging AFTER narration generation
3. Add assertion: hash_before == hash_after

Reference: M1_PR_GATE_CHECKLIST.md CHECK-004
Guardrail: INV-DET-001 (Memory Immutability)
Kill Switch: KILL-001
```

---

### CHECK-005: Kill Switch Demonstrably Testable

**Question:** If this PR adds new narration/query code, does it include tests that verify kill switches fire correctly?

**Required Tests:**
- If adds narration code → MUST include test for KILL-001 (memory mutation triggers exception)
- If adds memory write → MUST include test for KILL-002 (unauthorized write rejected)
- If adds fact extraction → MUST include test for KILL-003 (hallucination detection)

**Pass Criteria:**
- ✅ New narration code includes KILL-001 test
- ✅ New memory write code includes KILL-002 test
- ✅ New fact extraction code includes KILL-003 test
- ✅ OR: PR does NOT add narration/write/extraction code (no tests required)

**Fail Criteria:**
- ❌ New narration code WITHOUT KILL-001 test
- ❌ New memory write WITHOUT KILL-002 test
- ❌ New fact extraction WITHOUT KILL-003 test

**Verification Command:**
```bash
# Check for kill switch tests
grep -r "test.*KILL-001\|test.*memory.*mutation\|test.*hash.*violation" tests/ --include="*.py"
grep -r "test.*KILL-002\|test.*unauthorized.*write\|test.*event_id" tests/ --include="*.py"
grep -r "test.*KILL-003\|test.*hallucination\|test.*validation" tests/ --include="*.py"
# Each added feature should have corresponding test
```

**Reviewer Action:**
- ✅ PASS: Kill switch tests present → Continue to CHECK-006
- ❌ FAIL: Kill switch tests missing → REJECT PR immediately

**Rejection Message Template:**
```
❌ CHECK-005 FAILED: Kill Switch Tests Missing

This PR adds narration/write/extraction code but lacks kill switch tests:
- Added: [file:line] generate_narration() function
- Missing: test_narration_mutation_triggers_KILL_001()

Required Action:
1. Add test that verifies KILL-001 fires when memory mutated
2. Add test that verifies KILL-002 fires on unauthorized write
3. Add test that verifies KILL-003 fires on hallucination

Reference: M1_PR_GATE_CHECKLIST.md CHECK-005
Monitoring: M1_MONITORING_PROTOCOL.md Section 2
```

---

### CHECK-006: New Tests Added

**Question:** Does this PR add tests for all new code paths?

**Coverage Requirements:**
- New function → MUST have unit test
- New code path → MUST have integration test
- Modified function → MUST have regression test

**Pass Criteria:**
- ✅ Test coverage ≥90% for modified files
- ✅ All new functions have tests
- ✅ No reduction in overall test coverage

**Fail Criteria:**
- ❌ Test coverage <90% for modified files
- ❌ New functions without tests
- ❌ Test coverage decreased from main branch

**Verification Command:**
```bash
# Run coverage on modified files
pytest --cov=aidm --cov-report=term-missing tests/
# Check coverage % for files modified in this PR
```

**Reviewer Action:**
- ✅ PASS: Test coverage ≥90% → APPROVE PR
- ❌ FAIL: Test coverage <90% → REJECT PR immediately

**Rejection Message Template:**
```
❌ CHECK-006 FAILED: Insufficient Test Coverage

This PR has insufficient test coverage:
- [file.py]: 72% coverage (required: ≥90%)
- [function_name]: No tests found

Required Action:
1. Add unit tests for all new functions
2. Add integration tests for new code paths
3. Achieve ≥90% coverage for all modified files

Reference: M1_PR_GATE_CHECKLIST.md CHECK-006
```

---

### CHECK-007: Spark/Lens/Box Separation

**Question:** Does this PR preserve the Spark/Lens/Box architectural separation?

**Doctrine Reference:** `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md`

**Pass Criteria:**
- ✅ NO code path allows narration/LLM output to directly mutate canonical state (SPARK→state writes forbidden)
- ✅ ALL "illegal/not permitted" decisions sourced from engine/box, NOT from LLM/narration
- ✅ ALL user-facing mechanical claims include provenance tag (BOX/DERIVED/NARRATIVE/UNCERTAIN)
- ✅ NO refusal originates from SPARK layer (refusal only via LENS gating or BOX illegality)

**Fail Criteria:**
- ❌ LLM output treated as authoritative mechanics without BOX verification
- ❌ Any refusal originates from narration component rather than box/lens policy layer
- ❌ Any path collapses layers (SPARK becomes arbiter, LENS invents authority)
- ❌ Missing provenance labels on user-facing output

**Verification Command:**
```bash
# Check for SPARK→state writes
grep -r "narration.*WorldState\|llm_output.*state\|generate.*mutate" --include="*.py" aidm/
# Should return 0 results

# Check for provenance labeling
grep -r "\\[BOX\\]\\|\\[NARRATIVE\\]\\|\\[DERIVED\\]\\|\\[UNCERTAIN\\]" --include="*.py" aidm/
# Should show provenance tags in output code

# Check for SPARK refusal (anti-pattern)
grep -r "cannot.*generate\\|refuse.*narrat\\|inappropriate" --include="*.py" aidm/narration/
# Should return 0 results (refusal must be LENS/BOX, not SPARK)
```

**Reviewer Action:**
- ✅ PASS: Separation preserved → Continue to next check
- ❌ FAIL: Separation violated → REJECT PR immediately

**Rejection Message Template:**
```
❌ CHECK-007 FAILED: Spark/Lens/Box Separation Violated

This PR violates the Spark/Lens/Box doctrine:
- [specify violation: SPARK→state write / SPARK refusal / missing provenance / LENS authority invention]

Required Action:
1. Review docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md
2. Route all state mutations through BOX event-sourcing
3. Move any refusal logic to LENS (post-generation gating) or BOX (mechanical illegality)
4. Add provenance labels ([BOX]/[NARRATIVE]/[DERIVED]/[UNCERTAIN]) to all user-facing output

Reference: M1_PR_GATE_CHECKLIST.md CHECK-007
Doctrine: SPARK_LENS_BOX_DOCTRINE.md
```

---

## 3. Checklist Summary

**Reviewer MUST verify ALL 7 checks:**

| Check | Requirement | Verification Method |
|-------|-------------|---------------------|
| ✅ **CHECK-001** | No schema diff without PM approval | `git diff main...HEAD -- aidm/schemas/` |
| ✅ **CHECK-002** | No narration write path without validation | `grep narration.*add_fact` |
| ✅ **CHECK-003** | Temperature clamps enforced (query ≤0.5, narration ≥0.7) | `grep temperature` in query/narration functions |
| ✅ **CHECK-004** | Hash freeze enforced (pre/post logs + assertion) | `grep PRE_NARRATION_HASH\|POST_NARRATION_HASH` |
| ✅ **CHECK-005** | Kill switch tests present | `grep test.*KILL` in tests/ |
| ✅ **CHECK-006** | Test coverage ≥90% | `pytest --cov` |
| ✅ **CHECK-007** | Spark/Lens/Box separation preserved | `grep SPARK→state / provenance tags` |

**PR Status:**
- **PASS:** All 7 checks pass → Approved for merge
- **FAIL:** ANY check fails → Rejected, return to author

---

## 4. Reviewer Workflow

### Step 1: Pre-Review (Automated)

**Run CI checks:**
```bash
# Automated CI should verify:
1. All tests pass
2. Test coverage ≥90%
3. No schema diff (or PM approval comment present)
4. No linter errors
```

**If CI fails:** REJECT PR immediately (do not proceed to manual review)

---

### Step 2: Manual Review (Checklist)

**For each check (CHECK-001 through CHECK-007):**

1. **Run verification command** (see above)
2. **Evaluate result** (pass/fail)
3. **Mark checkbox** in PR review comment
4. **If FAIL:** Use rejection message template, REJECT PR

**Review Comment Template:**
```markdown
## M1 PR Gate Checklist Review

- [ ] CHECK-001: No schema diff ✅ PASS / ❌ FAIL
- [ ] CHECK-002: No narration write path ✅ PASS / ❌ FAIL
- [ ] CHECK-003: Temperature clamps enforced ✅ PASS / ❌ FAIL
- [ ] CHECK-004: Hash freeze enforced ✅ PASS / ❌ FAIL
- [ ] CHECK-005: Kill switch tests present ✅ PASS / ❌ FAIL
- [ ] CHECK-006: Test coverage ≥90% ✅ PASS / ❌ FAIL
- [ ] CHECK-007: Spark/Lens/Box separation ✅ PASS / ❌ FAIL

**Result:** ✅ APPROVED / ❌ REJECTED

[If REJECTED: include specific failure details + required actions]

Reference: docs/governance/M1_PR_GATE_CHECKLIST.md
```
```markdown
## M1 PR Gate Checklist Review

- [ ] CHECK-001: No schema diff ✅ PASS / ❌ FAIL
- [ ] CHECK-002: No narration write path ✅ PASS / ❌ FAIL
- [ ] CHECK-003: Temperature clamps enforced ✅ PASS / ❌ FAIL
- [ ] CHECK-004: Hash freeze enforced ✅ PASS / ❌ FAIL
- [ ] CHECK-005: Kill switch tests present ✅ PASS / ❌ FAIL
- [ ] CHECK-006: Test coverage ≥90% ✅ PASS / ❌ FAIL
- [ ] CHECK-007: Spark/Lens/Box separation ✅ PASS / ❌ FAIL

**Result:** ✅ APPROVED / ❌ REJECTED

[If REJECTED: include specific failure details + required actions]

Reference: docs/governance/M1_PR_GATE_CHECKLIST.md
```

---

### Step 3: Approval/Rejection

**If ALL 7 checks PASS:**
- ✅ Mark PR as **Approved**
- ✅ Add comment: "M1 PR Gate: ALL CHECKS PASSED"
- ✅ PR may merge

**If ANY check FAILS:**
- ❌ Mark PR as **Request Changes**
- ❌ Add rejection message (use template from failed check)
- ❌ Tag author + Agent D
- ❌ PR BLOCKED until fixed

---

## 5. Escalation Procedure

### 5.1 Reviewer Uncertain (Edge Case)

**If reviewer unsure whether PR passes a check:**

1. **TAG Agent D** in PR comment
2. **Describe uncertainty** (which check, why uncertain)
3. **WAIT for Agent D guidance** (do not approve/reject yet)

**Agent D Response Time:** <24 hours

---

### 5.2 Repeated Failures (Same Check)

**If same author fails same check 3+ times:**

1. **Reviewer notifies Agent D**
2. **Agent D conducts root cause analysis** (knowledge gap? tooling issue?)
3. **Agent D provides guidance** (training, improved tooling, etc.)

---

### 5.3 Checklist Ambiguity (Process Issue)

**If checklist itself is ambiguous:**

1. **Reviewer files issue:** "M1_PR_GATE_CHECKLIST.md ambiguity in CHECK-XXX"
2. **Agent D updates checklist** (clarify language, add examples)
3. **PM approves update** (if changes verification method)

---

## 6. Exception Process (PM Override)

**PM may override ANY check with explicit justification.**

**Override Comment Format:**
```markdown
## PM OVERRIDE: CHECK-XXX

**Justification:** [why override is necessary]

**Risk Acknowledged:** [what risk is accepted]

**Mitigation:** [what compensating controls exist]

**Approval:** PM (Thunder) — [date]

Reference: M1_PR_GATE_CHECKLIST.md Section 6
```

**Reviewer Action:**
- ✅ Accept PM override as equivalent to CHECK PASS
- ✅ Tag PR with label: `pm-override-check-XXX`
- ✅ Proceed with review (remaining checks still apply)

---

## 7. Compliance Statement

**This checklist is MANDATORY for all M1 PRs.**

**No exceptions without PM override.**

**Reviewer authority:** REJECT on sight if ANY check fails.

**Agent D authority:** Update checklist if ambiguity found, with PM approval.

---

**END OF M1 PR GATE CHECKLIST**

**Date:** 2026-02-10
**Agent:** Agent D (Research Orchestrator)
**Phase:** M1 Monitoring Spine Setup
**Status:** ✅ ACTIVE (mandatory for all M1 PRs)
**Authority:** Strict pass/fail enforcement

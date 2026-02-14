# MEMO: Next-Phase Operational Recommendations

**From:** Builder (Opus 4.6)
**To:** PM (Aegis)
**Date:** 2026-02-14
**Session scope:** Post-fix phase review — builder field assessment of what would make the next dispatch wave run smoother
**Lifecycle:** NEW

---

## Action Items (PM must act on these)

1. **Vault/RELIABILITY.md** — Create gate file. Builders currently have no way to distinguish verified data from garbled OCR. One table, 3 tiers. Blocks: nothing, but prevents wasted builder time on every future Vault reference.
2. **AMBIGUOUS verdict deadlines** — Add DEADLINE column to decision log. 7 of 28 verdicts have sat with blank DECISION fields. Default policy: "operator decides by [date] or PM defaults to KEEP." Blocks: prevents indefinite accumulation.
3. **is_ranged micro-WO** — Prioritize as first WO in next feature wave. Activates 3 already-implemented rules (Prone AC, Helpless AC, soft cover). ~10 lines per resolver. Highest code leverage in the backlog.
4. **Dispatch template updates** — Add "fix-once" consumer check section and "activated by" dependency field. Two template additions that prevent the sunder gap and dormant-fix patterns from recurring.

## Status Updates (Informational only)

5. **Framework repo completed** — `multi-agent-coordination-framework` pushed to GitHub at 100% (was 56%). 4 new patterns, 2 new templates, full case study (4 docs), taxonomy updated 6 to 8 categories.
6. **sys.modules fixture ready** — 10-line defensive fixture for root conftest. Code written, ready to commit on approval. Prevents the entire class of test contamination bugs.

## Deferred (Not blocking, act when convenient)

7. **--check-stale dispatch validation script** — Parses dispatch markdown, validates file/line references against HEAD. Useful but the Tier 2 version (manual checklist item) works until volume justifies tooling.

---

## Detail: The 7 Recommendations

### 1. Vault/RELIABILITY.md gate file

**Problem:** The Vault OCR data looks authoritative but isn't. A builder spent 30 minutes trying to reconcile garbled numbers from `pages/0039.txt` before abandoning it. Every Vault page currently looks equally trustworthy.

**Proposal:** Create `Vault/RELIABILITY_INDEX.md`:

```
| Page | Source | Tier | Verified By | Date |
|------|--------|------|-------------|------|
| 0039.txt | DMG p.38-39 | OCR-RAW | -- | -- |
| 0142.txt | PHB p.141 | VERIFIED | Thunder | 2026-02-10 |
```

Tiers: VERIFIED (human-checked against physical book), OCR-RAW (unverified scan), STUB (placeholder). Start with STUB for everything, promote incrementally as pages are used.

**Priority:** High impact, low effort. No code, no risk.

### 2. "Fix-once" consumer check in dispatch template

**Problem:** WO-FIX-01 (grip multiplier) was applied to attack_resolver and full_attack_resolver but missed the sunder path in maneuver_resolver. The dispatch treated each WO as independent. Cross-cutting rules get missed when consumers span multiple WOs.

**Proposal:** Add to dispatch packet header:

```
## Consumer Matrix -- Cross-WO Dependencies

| Rule | Primary WO | All Consumer Code Paths |
|------|-----------|------------------------|
| STR grip multiplier | WO-FIX-01 | attack_resolver.py:363, full_attack_resolver.py:297, maneuver_resolver.py:1071 |
```

The dispatch author builds this by grepping for the field/function name across the codebase before writing the packet. This is Tier 2 enforcement — process-positioned, not automated.

**Priority:** Template addition. Prevents the category of bug, not just the instance.

### 3. sys.modules snapshot fixture

**Problem:** Module-level `sys.modules['torch']` injection in test_imagereward_critique.py caused permanent contamination, masking 3 broken tests and corrupting GPU detection across the suite.

**Proposal:** Add to `tests/conftest.py`:

```python
@pytest.fixture(autouse=True, scope="session")
def _snapshot_sys_modules():
    snapshot = dict(sys.modules)
    yield
    for key in list(sys.modules):
        if key not in snapshot:
            del sys.modules[key]
    for key, mod in snapshot.items():
        sys.modules[key] = mod
```

**Note on scope:** `scope="session"` restores at session end. The specific torch fix is already committed (`f581d44`). This fixture is defensive infrastructure against the entire class of bugs, not a fix for a specific instance.

**Priority:** 10 lines. Ready to commit.

### 4. --check-stale dispatch validation

**Problem:** WO-FIX-FINALIZE dispatch listed "uncommitted changes in these files" but those changes were already committed. Stale dispatches create false signals for builders.

**Proposal (Tier 2 — now):** Add to dispatch template: "Before sending, verify all file references against HEAD. Run `git diff --name-only` against each listed file."

**Proposal (Tier 1 — later):** Shell script that parses dispatch markdown for file paths and validates against current git state. 50-80 lines of Python. Build this when dispatch volume justifies the tooling investment.

**Priority:** Template checklist item now. Script later.

### 5. AMBIGUOUS verdict deadlines

**Problem:** 7 of 28 AMBIGUOUS verdicts have blank DECISION fields since verification completed. They aren't blocking today but represent unresolved design decisions that will conflict with future feature WOs.

**Proposal:** Add DEADLINE column to `AMBIGUOUS_VERDICTS_DECISION_LOG.md`:

```
| ID | Domain | Issue | DECISION | DEADLINE |
|----|--------|-------|----------|----------|
| A-AMB-05 | Attack | Cover AC tiers | -- | 2026-03-01 |
```

Default policy: "Operator decision required by [date] or PM defaults to KEEP."

**Priority:** Process decision, no code. Prevents indefinite accumulation. Set deadlines relative to next feature wave.

### 6. is_ranged detection micro-WO

**Problem:** The Prone/Helpless AC differentiation (WO-FIX-03), soft cover direction, and future melee/ranged distinctions are all implemented but gated behind `feat_context.get("is_ranged", False)` which always returns False. Three rules are architecturally complete but functionally dormant.

**Proposal:** Micro-WO: read weapon type/category field, set `is_ranged=True` for bow/crossbow/thrown. Does not require the full weapon system — just type detection and flag propagation.

**Impact:** One change activates three already-implemented rules. Highest leverage item in the backlog.

**Priority:** First WO in next feature wave. See also P4-D in `MEMO_POST_FIX_PHASE_ACTION_PLAN.md`.

### 7. Cross-WO consumer matrix (reinforces #2)

**Problem:** Schema changes propagate through layers that aren't visible from the consumer level. WO-FIX-03 was scoped for 3 files, actually required 6. The dispatch author traced direct consumers but missed serialization, aggregation, and test infrastructure.

**Proposal:** When a WO changes a schema or shared field, the dispatch includes a cascade checklist:

```
Schema Cascade Checklist:
- [ ] Definition (schema file)
- [ ] Serialization (to_dict / from_dict)
- [ ] Aggregation (get_condition_modifiers, etc.)
- [ ] Consumers (attack_resolver, full_attack_resolver, etc.)
- [ ] Tests (assertions on old values)
```

Each layer is confirmed as "no change needed" or "change required at [file:line]."

**Priority:** Template addition. Prevents Schema Cascade Underestimation (F-008 in framework failure catalog).

---

## Recommended Priority Order

1. **is_ranged micro-WO** (#6) — activates 3 dormant rules, highest code leverage
2. **Vault/RELIABILITY.md** (#1) — prevents wasted builder time, zero risk
3. **sys.modules fixture** (#3) — 10 lines, defensive infrastructure
4. **AMBIGUOUS deadlines** (#5) — process decision, no code
5. **Dispatch template updates** (#2 + #7) — two template additions, low effort
6. **--check-stale validation** (#4) — tooling can wait, checklist item now
7. **Resolver duplication refactor** (implied by #2) — highest risk, dedicated session

---

## Cross-References

- `MEMO_POST_FIX_PHASE_ACTION_PLAN.md` — Full action plan with P1-P5 priority tiers
- `MEMO_BUILDER_DEBRIEF_FIX_PHASE_COMPLETION.md` — Fix phase debrief with RECs 1-7
- Framework repo: `patterns/COORDINATION_FAILURE_TAXONOMY.md` — Categories 7 (Silent Agent Completion) and 8 (Schema Cascade Underestimation) added from this session's findings

---

*End of memo.*

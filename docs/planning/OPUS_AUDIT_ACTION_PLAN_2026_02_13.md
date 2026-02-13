# Opus Audit Action Plan — 2026-02-13

**Author:** Opus (Full Codebase Audit)
**Purpose:** Detailed corrective action plan derived from complete codebase audit (5,254 tests, 212 source files, all 8 architectural layers reviewed). Merges audit findings with existing roadmap to produce a unified path forward.
**Supersedes:** Nothing — this is additive to REVISED_PROGRAM_SEQUENCING_2026_02_12.md

---

## Strategic Context

This plan addresses two parallel needs:

1. **Hardening** — Fix the bugs, violations, and structural weaknesses found during audit
2. **Forward Motion** — Continue the critical path toward MVP (Phase 0 → 1 → 2 → 3 → 4)

These are not in conflict. Hardening is organized into work orders that slot into the existing wave dispatch system. Each WO is sized for a single agent context window and has clear acceptance criteria.

---

## Part 1: Hardening Work Orders (Audit Remediation)

### Wave H1: Critical Bugs (Do First)

These are correctness defects in the deterministic engine. They affect game outcomes.

#### WO-AUDIT-001: Fix AoO Damage Detection (C-1)

**File:** `aidm/core/aoo.py`
**Bug:** `aoo_dealt_damage()` checks for key `"hp_change"` but `attack_resolver` emits `"delta"`. AoO-triggered disarm/grapple auto-fail conditions silently never fire.

**Acceptance Criteria:**
- [ ] Fix key lookup in `aoo_dealt_damage()` to match actual event payload field name
- [ ] Add explicit test: AoO that deals damage → verify `aoo_dealt_damage()` returns True
- [ ] Add explicit test: AoO that deals 0 damage → verify returns False
- [ ] All existing AoO tests still pass
- [ ] Run full test suite — 0 regressions

**Estimated scope:** ~10 lines changed, ~20 lines of new tests

---

#### WO-AUDIT-002: Fix Spell Save Natural 1/20 (C-2)

**File:** `aidm/core/spell_resolver.py`
**Bug:** Saving throws against spells don't honor natural 1 (always fail) and natural 20 (always succeed) per PHB p.177. `save_resolver.py` handles this correctly — `spell_resolver.py` does its own save logic and misses it.

**Acceptance Criteria:**
- [ ] Spell saving throws honor natural 1 = auto-fail regardless of modifier
- [ ] Spell saving throws honor natural 20 = auto-succeed regardless of modifier
- [ ] Ideally route spell saves through `save_resolver.py` rather than duplicating logic (DRY)
- [ ] If routing isn't feasible, add natural 1/20 checks inline with clear PHB citation
- [ ] Add tests: spell with DC 5 + target rolls natural 1 → fails despite high modifier
- [ ] Add tests: spell with DC 40 + target rolls natural 20 → succeeds despite low modifier
- [ ] All existing spell tests still pass
- [ ] Run full test suite — 0 regressions

**Estimated scope:** ~20-40 lines changed depending on approach, ~30 lines of new tests

---

#### WO-AUDIT-003: Freeze Mutable Containers in Frozen Dataclasses (C-3, H-3, H-5)

**Files (systemic — all instances):**
- `aidm/schemas/engine_result.py` — `events: List[Dict]`, `rolls: List[RollResult]`
- `aidm/schemas/content_pack.py` — `Dict[str, X] = None; type: ignore` defaults
- `aidm/lens/narrative_brief.py` — `List[str]` fields in frozen `NarrativeBrief`
- `aidm/core/fact_acquisition.py` — `List` fields in frozen `ValidationResult`, `AcquisitionResult`

**Bug:** Python `frozen=True` prevents attribute reassignment but not mutation of mutable containers. Code like `result.events.append(...)` silently works, violating the immutability contract that the entire architecture depends on.

**Acceptance Criteria:**
- [ ] All `List` fields in frozen dataclasses converted to `tuple` in `__post_init__`
- [ ] All `Dict` fields in frozen dataclasses converted to `MappingProxyType` in `__post_init__` (or frozen dict equivalent)
- [ ] `content_pack.py` mutable dict defaults replaced with `field(default_factory=dict)` + freeze in `__post_init__`
- [ ] Any code that previously relied on mutating these fields after construction is updated (likely `EngineResultBuilder` — verify it constructs with lists then freezes)
- [ ] Add tests: attempt to `.append()` on a frozen result's events → raises `TypeError`
- [ ] Add tests: attempt to `[key] = value` on a frozen content pack's dict fields → raises `TypeError`
- [ ] Run full test suite — 0 regressions

**Estimated scope:** ~100-150 lines changed across 4+ files, ~40 lines of new tests

**IMPORTANT:** This is the highest-risk hardening WO. The `EngineResultBuilder` pattern constructs results incrementally — verify that the builder accumulates in mutable containers and freezes on `.build()`. Do NOT break the builder pattern.

---

### Wave H2: Architectural Violations

#### WO-AUDIT-004: Fix BL-004 Boundary Violation (H-1)

**Files:**
- `aidm/core/model_selector.py` — imports from `aidm.spark.model_registry`
- `tests/test_boundary_law.py` — BL-004 test incomplete (doesn't check `aidm.spark` imports)

**Violation:** Box layer imports from Spark layer. This is a one-way boundary violation (Box must never depend on Spark).

**Acceptance Criteria:**
- [ ] `model_selector.py` no longer imports from `aidm.spark`
- [ ] Model selection interface lives in Box or schemas (abstract protocol/ABC)
- [ ] Spark layer registers its implementation via dependency injection or the interface is consumed through Lens
- [ ] Update `test_boundary_law.py` BL-004 test to check for `aidm.spark` imports from Box
- [ ] BL-004 test passes with the new check
- [ ] All existing boundary law tests still pass
- [ ] Run full test suite — 0 regressions

**Design decision needed:** Where does the model selection interface live? Options:
- (a) `aidm/schemas/model_selection.py` — protocol/ABC that Spark implements
- (b) `aidm/lens/model_selection.py` — Lens mediates between Box need and Spark capability
- Recommend (a) — schemas is the shared contract layer

---

#### WO-AUDIT-005: Fix WebSocket Race Condition (H-2)

**File:** `aidm/server/ws_bridge.py`
**Bug:** `_get_or_create_session()` is async with no lock. Concurrent WebSocket connections with the same session_id can create duplicate sessions.

**Acceptance Criteria:**
- [ ] Add `asyncio.Lock()` to guard session creation in `_get_or_create_session()`
- [ ] Add test: simulate 10 concurrent connection attempts with same session_id → verify only 1 session created
- [ ] Verify `_sessions` dict access is thread-safe (or document that the server is single-threaded async)
- [ ] All existing WebSocket tests still pass
- [ ] Run full test suite — 0 regressions

**Estimated scope:** ~10 lines changed, ~20 lines of new tests

---

### Wave H3: Schema Hygiene

#### WO-AUDIT-006: Schema Layer Cleanup (M-1, H-4, M-7, M-8)

**Files:**
- `aidm/schemas/__init__.py` — no public exports, stale Pydantic reference
- `aidm/schemas/campaign.py` — `validate()` returns errors instead of raising
- `aidm/schemas/campaign_memory.py` — type annotations use `str` instead of `Literal` aliases
- `aidm/runtime/session.py` — frozen intent mutation inconsistency

**Acceptance Criteria:**
- [ ] `schemas/__init__.py` exports all public schema types and has accurate docstring
- [ ] `campaign.py` adds `__post_init__` validation that raises on construction for critical fields (paths must exist, session_zero_config must be valid); keep `validate()` as soft-check API
- [ ] `campaign_memory.py` type annotations use the declared `Literal` aliases (`EvidenceType`, `AlignmentAxisTag`, `ClueStatus`) instead of bare `str`
- [ ] `session.py` frozen intent mutation either uses `object.__setattr__` consistently or documents the pattern
- [ ] Run full test suite — 0 regressions

**Estimated scope:** ~80-100 lines changed across 4 files

---

### Wave H4: Documentation Corrections

#### WO-AUDIT-007: Update Stale Documentation

**Files:**
- `PROJECT_COHERENCE_DOCTRINE.md` — test runtime invariant (<5s) is stale
- `PROJECT_COHERENCE_DOCTRINE.md` — voice integration scope ambiguity
- `KNOWN_TECH_DEBT.md` — add audit findings as new TD items

**Acceptance Criteria:**
- [ ] Test runtime invariant updated to reflect actual scale (~105s for 5,254 tests). Either update the target or add a per-test budget (e.g., <25ms average)
- [ ] Voice integration scope clarified — either mark as In Scope (since M3 implements it) or document the boundary between "voice pipeline" (in scope) and "voice model training" (out of scope)
- [ ] New TD items added for any audit findings that remain open after Waves H1-H3
- [ ] Test count updated to 5,254 (or current actual)
- [ ] 2026-02-12 addendum in Coherence Doctrine reviewed for accuracy

**Estimated scope:** ~50 lines of documentation changes

---

### Wave H5: Boundary Law Test Hardening

#### WO-AUDIT-008: Strengthen Boundary Law Tests

**File:** `tests/test_boundary_law.py`
**Issue:** BL-004 test doesn't check `aidm.spark` imports, which allowed a violation to persist undetected.

**Acceptance Criteria:**
- [ ] BL-004 test checks ALL upstream layer imports (not just `aidm.lens` but also `aidm.spark`, `aidm.immersion`, `aidm.narration`, `aidm.server`)
- [ ] Audit all other BL tests for similar gaps — each BL-00X test should check all layers above its own
- [ ] Add a meta-test that verifies the BL test matrix is complete (every layer pair that should be blocked IS tested)
- [ ] All BL tests pass (after WO-AUDIT-004 fixes the violation)
- [ ] Run full test suite — 0 regressions

**Estimated scope:** ~100-150 lines of test code

---

## Part 2: Integration Fixes (From PM Session Status)

These were already identified before the audit and should be done before Wave 4.

#### WO-INTEGRATION-001: Unify CompileStage Interface

**Files:**
- `aidm/core/world_compiler.py` — canonical `CompileStage` + `CompileContext`
- `aidm/core/compile_stages/_base.py` — local duplicate

**Acceptance Criteria:**
- [ ] `_base.py` re-exports from `world_compiler.py` (option b from PM status)
- [ ] All three stage implementations (Lexicon, Semantics, NPC) work with the unified interface
- [ ] Remove duplicate `CompileContext` and `StageResult` from `_base.py`
- [ ] All world compiler tests pass
- [ ] Run full test suite — 0 regressions

---

#### WO-INTEGRATION-002: Wire ContentPackLoader into WorldCompiler

**Files:**
- `aidm/core/world_compiler.py` — uses `ContentPackStub`
- `aidm/lens/content_pack_loader.py` — real loader

**Acceptance Criteria:**
- [ ] `WorldCompiler` accepts a `ContentPackLoader` (or protocol-compatible interface) instead of `ContentPackStub`
- [ ] `ContentPackStub` removed or demoted to test-only fixture
- [ ] Stage 0 validation uses real content pack data
- [ ] All world compiler tests pass
- [ ] Run full test suite — 0 regressions

---

#### WO-INTEGRATION-003: Fix compile_stages Exports + Creature Count

**Files:**
- `aidm/core/compile_stages/__init__.py` — missing `LexiconStage` export
- `aidm/data/content_pack/creatures.json` — count discrepancy (273 vs 373)

**Acceptance Criteria:**
- [ ] `__init__.py` exports `LexiconStage`, `SemanticsStage`, `NPCArchetypeStage`
- [ ] Verify actual creature count in `creatures.json` and update documentation to match
- [ ] All imports of compile stages work correctly
- [ ] Run full test suite — 0 regressions

---

## Part 3: Forward Motion (Existing Roadmap)

After hardening and integration fixes, the critical path continues per REVISED_PROGRAM_SEQUENCING_2026_02_12.md. The audit found nothing that changes the roadmap — only strengthens the foundation it builds on.

### Remaining World Compiler Stages (Phase 1 continuation)

| WO | Stage | Description | Depends On | Status |
|----|-------|-------------|------------|--------|
| WO-WORLDCOMPILE-RULEBOOK-001 | 2 | Rulebook generation | Stages 1 + 3 | COMPLETE |
| WO-WORLDCOMPILE-BESTIARY-001 | 5 | Bestiary naming + stat blocks | Stage 1 | COMPLETE |
| WO-WORLDCOMPILE-MAPS-001 | 6 | Map generation | None | NOT STARTED |
| WO-WORLDCOMPILE-ASSETS-001 | 7 | Asset pool manifests | None | NOT STARTED |

### Phase 2: Play Loop Integration

| WO | Description | Depends On | Status |
|----|-------------|------------|--------|
| Wire Spark narration into game loop | AD-007 + existing Spark | NOT STARTED |
| Voice pipeline integration | Spark wiring | NOT STARTED |
| Discovery Log backend wiring | World model | BACKEND COMPLETE |
| Session Zero flow | Voice pipeline | NOT STARTED |

### Phase 3: Table UI Prototype

| WO | Description | Status |
|----|-------------|--------|
| Three.js table surface + camera | NOT STARTED |
| Notebook, Dice, Crystal Ball, Battle Map | NOT STARTED |
| WebSocket bridge (frontend ↔ backend) | BACKEND COMPLETE |
| Character Sheet, Rulebook, Handouts | NOT STARTED |

### Phase 4: MVP Integration

| WO | Description | Status |
|----|-------------|--------|
| End-to-end integration | Blocked by Phases 2+3 |
| Asset pipeline | Blocked by generation infrastructure |
| Acceptance testing (10 MVP criteria) | Blocked by 4.1 |

---

## Part 4: Execution Sequencing

### Recommended Dispatch Order

```
┌─────────────────────────────────────────────────────────┐
│  WAVE H1: Critical Bugs (parallelize all 3)             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │ WO-AUDIT-001 │ │ WO-AUDIT-002 │ │ WO-AUDIT-003     │ │
│  │ AoO key fix  │ │ Spell nat1/20│ │ Freeze mutables  │ │
│  └──────────────┘ └──────────────┘ └──────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  WAVE H2 + INTEGRATION: Architecture (parallelize)      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │ WO-AUDIT-004 │ │ WO-AUDIT-005 │ │ WO-INTEG-001/2/3 │ │
│  │ BL-004 fix   │ │ WS race cond │ │ Compiler unify   │ │
│  └──────────────┘ └──────────────┘ └──────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  WAVE H3-H5: Cleanup (parallelize)                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │ WO-AUDIT-006 │ │ WO-AUDIT-007 │ │ WO-AUDIT-008     │ │
│  │ Schema hygiene│ │ Docs update  │ │ BL test harden   │ │
│  └──────────────┘ └──────────────┘ └──────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  FULL TEST SUITE GATE                                   │
│  All 5,254+ tests must pass before proceeding           │
├─────────────────────────────────────────────────────────┤
│  RESUME ROADMAP: Phase 1 remainder → Phase 2 → 3 → 4   │
│  (per REVISED_PROGRAM_SEQUENCING_2026_02_12.md)         │
└─────────────────────────────────────────────────────────┘
```

### Parallelization Strategy

- **Wave H1:** All 3 WOs are independent — dispatch in parallel
- **Wave H2 + Integration:** WO-AUDIT-004, WO-AUDIT-005, and WO-INTEG-001/002/003 are independent — dispatch in parallel
- **Wave H3-H5:** WO-AUDIT-006, WO-AUDIT-007, WO-AUDIT-008 are independent — dispatch in parallel
- **Gate:** Full test suite run after each wave. No forward progress until gate passes.

### Total Hardening Effort

| Wave | WOs | Files Touched | New Tests (est.) |
|------|-----|---------------|------------------|
| H1 | 3 | ~8-10 | ~90 |
| H2 + Integ | 5 | ~8-10 | ~60 |
| H3-H5 | 3 | ~6-8 | ~40 |
| **Total** | **11** | **~22-28** | **~190** |

After hardening, the test suite should be ~5,444+ tests with all critical/high findings resolved.

---

## Part 5: Maintainability Reinforcement

These are process improvements to prevent the kind of issues found in this audit from recurring. They address the legitimate concern about long-term maintainability of an AI-assisted project.

### 1. Immutability Gate (Automated)

Add a test that scans all frozen dataclasses for mutable container fields (`List`, `Dict`, `Set`) and fails if any are found without a corresponding `__post_init__` freeze.

**File:** `tests/test_immutability_gate.py`
**Trigger:** Any new frozen dataclass with mutable fields
**Prevents:** C-3/H-3/H-5 class of bugs from recurring

### 2. Boundary Law Completeness Gate (Automated)

Add a meta-test that verifies every layer boundary pair has a corresponding BL test. If a new module is added to `aidm/core/`, it automatically gets checked.

**File:** Extend `tests/test_boundary_law.py`
**Trigger:** Any new module in any layer
**Prevents:** BL-004 class of gaps from recurring

### 3. Event Payload Schema Consistency Gate (Automated)

Add a test that verifies all event payload field names referenced by consumers match the field names emitted by producers.

**File:** `tests/test_event_schema_consistency.py`
**Trigger:** Any new event type or consumer
**Prevents:** C-1 class of key mismatch bugs from recurring

### 4. PHB Citation Requirement (Process)

Any combat resolver function that implements a PHB rule should have a comment citing the page number. This makes it possible to audit rule fidelity without re-reading the entire PHB.

**Already partially done:** `attack_resolver.py` cites PHB pages. Extend to `spell_resolver.py`, `maneuver_resolver.py`, `aoo.py`.

### 5. Audit Cadence (Process)

Run a full-depth audit (like this one) at each phase gate. The test suite catches regressions, but systemic issues like frozen-mutability and boundary violations require human-or-AI review of the patterns, not just the behavior.

---

## Appendix: Mapping Audit Findings to WOs

| Finding | Severity | WO Assignment |
|---------|----------|---------------|
| C-1: AoO wrong key | CRITICAL | WO-AUDIT-001 |
| C-2: Spell nat 1/20 | CRITICAL | WO-AUDIT-002 |
| C-3: Mutable in frozen | CRITICAL | WO-AUDIT-003 |
| H-1: BL-004 violation | HIGH | WO-AUDIT-004 |
| H-2: WS race condition | HIGH | WO-AUDIT-005 |
| H-3: content_pack dicts | HIGH | WO-AUDIT-003 (bundled) |
| H-4: campaign validate | HIGH | WO-AUDIT-006 |
| H-5: fact_acquisition lists | HIGH | WO-AUDIT-003 (bundled) |
| M-1: schemas __init__ | MEDIUM | WO-AUDIT-006 |
| M-2: box_events strings | MEDIUM | Deferred (low risk) |
| M-3: maneuver degraded | MEDIUM | Tracked in KNOWN_TECH_DEBT |
| M-4: spell SR/DR missing | MEDIUM | Tracked in KNOWN_TECH_DEBT |
| M-5: Tumble DC hardcoded | MEDIUM | Tracked in KNOWN_TECH_DEBT |
| M-6: world_archive mutation | MEDIUM | WO-AUDIT-006 or deferred |
| M-7: campaign_memory types | MEDIUM | WO-AUDIT-006 |
| M-8: session intent freeze | MEDIUM | WO-AUDIT-006 |
| L-1: Doctrine test runtime | LOW | WO-AUDIT-007 |
| L-2: Doctrine voice scope | LOW | WO-AUDIT-007 |
| L-3: Flanking float precision | LOW | Deferred (edge case) |
| L-4: Sneak attack visibility | LOW | Tracked in KNOWN_TECH_DEBT |
| L-5: play_loop monolith | LOW | Tracked as TD-003 |
| L-6: attack_resolver range | LOW | Tracked as TD-009 |

---

*This plan is additive to the existing roadmap. Hardening waves should execute before resuming Phase 1 remainder. Total hardening scope: 11 WOs, ~190 new tests, ~22-28 files touched.*

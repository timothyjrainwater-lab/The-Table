# WO-058: ContradictionChecker v1 — Post-Hoc Spark Output Validation

**Status:** COMPLETE
**Filed:** 2026-02-12
**Implements:** RQ-LENS-SPARK-001 Deliverable 4 (Phase 1)
**Prerequisite:** WO-057 (PromptPackBuilder), WO-046B (NarrativeBrief)

---

## Problem

`GrammarShield` (KILL-002) catches mechanical assertions leaking into Spark output
(`AC 18`, `2d6 damage`, `PHB 145`). It does NOT catch fictional state mutations:

- "the ogre falls unconscious" when `target_defeated=False`
- "strikes the goblin" when `action_type=attack_miss`
- "devastating blow" when `severity=minor`

Players don't lose trust over `AC 18` leaking. They lose trust over
**false world-state claims** in narration.

## Solution

`ContradictionChecker` — a post-hoc validation layer that checks LLM narration
output against the NarrativeBrief truth frame. Runs AFTER GrammarShield, BEFORE
output delivery.

### Three Contradiction Classes

| Class | Name | Severity | Example |
|-------|------|----------|---------|
| A | Entity State | Critical | Defeat keywords when target NOT defeated |
| B | Outcome | High | Wrong weapon name, wrong damage type |
| C | Continuity | Medium | Indoor narration in outdoor scene |

### Class A Checks (Entity State)

- **Defeat keywords** in non-defeat context: `falls`, `collapses`, `dies`, `slain`, etc.
- **Hit keywords** in miss context: `strikes`, `hits`, `wounds`, `pierces`, etc.
- **Miss keywords** in hit context: `misses`, `dodges`, `parries`, `blocks`, etc.
- **Severity inflation**: `minor` brief + `devastating` narration
- **Severity deflation**: `lethal` brief + `scratches` narration
- **Stance contradiction**: `condition_applied=prone` + `stands tall` narration

### Class B Checks (Outcome)

- **Wrong weapon**: `weapon_name=longsword` + narration mentions `greataxe`
- **Wrong damage type**: `damage_type=slashing` + narration describes `burn`/`flame`

### Class C Checks (Continuity)

- **Scene location mismatch**: indoor scene + outdoor narration (or vice versa)

### Response Policy

| Class | 1st Occurrence | 2nd Consecutive | 3rd+ Consecutive |
|-------|---------------|-----------------|------------------|
| A | retry | template_fallback | template_fallback |
| B | retry | template_fallback | template_fallback |
| C | annotate | retry | template_fallback |

### Retry Mechanism

When response policy says "retry":
1. Build correction text from ContradictionResult
2. Append correction to prompt (e.g., "CORRECTION: The target was NOT defeated.")
3. Regenerate with slightly bumped temperature (+0.1)
4. Re-check retry output for both mechanical assertions and contradictions
5. If retry also fails → fall back to template

## Integration Point

```
LLM Generation
    ↓
KILL-004: Latency check
    ↓
KILL-003: Token overflow check
    ↓
KILL-002: Mechanical assertion check (GrammarShield)
    ↓
[NEW] ContradictionChecker: Fictional state validation
    ├── Class A/B contradiction → retry (1st) / template (2nd+)
    ├── Class C contradiction → annotate (1st) / retry (2nd) / template (3rd)
    └── Clean → proceed
    ↓
Final narration selection
    ↓
KILL-001/KILL-006: Post-generation hash verification
```

## Files

| File | Lines | Description |
|------|-------|-------------|
| `aidm/narration/contradiction_checker.py` | ~430 | ContradictionChecker class, keyword dictionaries, response policy |
| `tests/test_contradiction_checker.py` | ~530 | 67 tests across 10 test classes |
| `aidm/narration/guarded_narration_service.py` | Modified | ContradictionChecker wired into narration pipeline |

## Test Coverage (67 tests)

- **TestDefeatKeywords** (7): defeat keyword detection, non-defeat flagging, defeat context pass
- **TestHitMissKeywords** (9): hit/miss keyword context, concealment/spell variants, false positive avoidance
- **TestSeverity** (6): inflation/deflation for minor/moderate/lethal/devastating
- **TestStance** (3): prone/standing contradiction
- **TestWeaponName** (4): wrong weapon detection, correct weapon pass, partial match handling
- **TestDamageType** (5): wrong damage type, correct type pass, null type skip
- **TestSceneContinuity** (4): indoor/outdoor mismatch
- **TestResponsePolicy** (7): escalation from retry → template_fallback, consecutive counter
- **TestContradictionResult** (5): frozen dataclasses, worst_class property
- **TestRetryCorrection** (6): correction prompt generation for each subtype
- **TestFalsePositiveAvoidance** (5): clean narrations that should NOT trigger
- **TestEdgeCases** (6): empty narration, long text, case insensitivity, multiple classes

## Boundary Law Compliance

- **BL-003**: ContradictionChecker lives in `aidm/narration/`. No `aidm.core` imports.
  NarrativeBrief received as `Any` parameter to avoid circular import.
- **FREEZE-001**: All inputs are immutable (narration text string, frozen NarrativeBrief).
- **Axiom 2**: ContradictionChecker has no mechanical effect — it only validates narration.

## Citations

- RQ-LENS-SPARK-001: Context Orchestration Sprint (Deliverable 4)
- RQ-LENS-002: Contradiction Surface Mapping (keyword dictionaries, scripted brief matrix)
- AD-002: Lens Context Orchestration (five-channel wire protocol)

## What This Does NOT Do

- Semantic contradiction detection via LLM (deferred per RQ-LENS-SPARK-001 scope)
- Actor/target name substitution detection (deferred to v2 — requires NER)
- Class C defeated-entity-acting check (requires SessionSegmentSummary — Deliverable 3)
- Multi-turn coherence tracking (requires Deliverable 2 retrieval policy)
- KILL-007 kill switch for contradiction rate threshold (optional, deferred)

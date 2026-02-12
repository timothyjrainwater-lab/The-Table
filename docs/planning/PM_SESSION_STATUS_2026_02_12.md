# PM Session Status — 2026-02-12

**Author:** Opus (PM)
**Sessions Covered:** 10 context windows (TTS evaluation → GPT findings review → Phase 1 research review + AD-003 → WO-FIX-001/002 + AD-004 → WO-FIX-003 + Evidence Gate enforcement → WO-048 DR system → WO-049 Concealment + WO-034-FIX Power Attack → WO-051B/052B Policy Defaults + Scene Gen → AD-005 + WO-053/054/055 Physical Affordance + WO-045B PromptPack → WO-046B NarrativeBrief + WO-056 Gear Affordance)
**Purpose:** Context continuity document for next PM session pickup

---

## Executive Summary

Phase 1 research is **complete**. All hotfixes are **complete**. **Phase 2 is substantially complete**: 12 Box/Lens-layer WOs done (WO-048/049/034-FIX/036/051B/052B/053/054/055/045B/046B/056). **AD-005 Physical Affordance Policy fully implemented** through all 3 layers: L1 Encumbrance, L2 Container Policies, L3 Gear Affordance Tags. **Box→Lens seam upgraded to GREEN** with NarrativeBrief handling all event types. **Lens→Spark seam YELLOW** with PromptPack v1 + visible_gear wired.

**Test suite:** 4130 passed, 8 pre-existing failures (Chatterbox TTS adapter + import boundary), 0 regressions.

**Next action:** GAP-007 resolution (unify dual prompt assembly paths via PromptPack).

---

## What Was Accomplished

### Architectural Decisions (Binding)

| Decision | Path | Key Rule |
|----------|------|----------|
| AD-001: Authority Resolution Protocol | `docs/decisions/AD-001_AUTHORITY_RESOLUTION_PROTOCOL.md` | Spark MUST NEVER supply mechanical truth. NeedFact/WorldPatch halt-and-resolve protocol. |
| AD-002: Lens Context Orchestration | `docs/decisions/AD-002_LENS_CONTEXT_ORCHESTRATION.md` | Five-channel PromptPack wire protocol. Lens as OS for context assembly. |
| AD-003: Self-Sufficiency Resolution | `docs/decisions/AD-003_SELF_SUFFICIENCY_RESOLUTION_POLICY.md` | System self-sufficiency through Policy Default Library + Seeded Deterministic Generator, not LLM invention. |
| AD-005: Physical Affordance Policy | `docs/decisions/AD-005_PHYSICAL_AFFORDANCE_POLICY.md` | Declared physical facts for RAW-silent properties. Four-layer inventory architecture. HOUSE_POLICY provenance for container/storage rules. |

### AD-004: Mechanical Evidence Gate

| Decision | Path | Key Rule |
|----------|------|----------|
| AD-004: Mechanical Evidence Gate | `docs/decisions/AD-004_MECHANICAL_EVIDENCE_GATE.md` | No mechanical rule enters Box without local corpus evidence. Three enforcement layers. |

### Phase 1 Research Deliverables (All Complete)

| Agent | Output | Grade | Key Finding |
|-------|--------|-------|-------------|
| RWO-001 | `docs/research/RQ_SPARK_001_SYNTHESIS.md` | A | Spark Emission Contract v1 — 31 normative statements, 5 emission schemas, 15-class failure taxonomy |
| RWO-002 | `docs/research/RQ_NARR_001_SYNTHESIS.md` | A | Narrative Balance Contract v1 — 43 event labels, 3-dimension rubric (Fidelity/Containment/Tone), 6 open questions |
| RWO-003 | `docs/CURRENT_CANON.md`, `docs/DOC_DRIFT_LEDGER.md` | A- | Document hierarchy canonicalized. 6 drift entries logged. |
| RWO-004 | `docs/audits/5E_CONTAMINATION_AUDIT.md` | A | **P0 BUG: DurationTracker 5e concentration limiter** (`duration_tracker.py:115`). 9 warnings, 18 clean. |
| RWO-005 | `docs/audits/SEAM_PROTOCOL_ANALYSIS.md` | A | 8 gaps (2 CRITICAL, 3 HIGH, 3 MEDIUM). Seam 2 (Lens→Spark) is RED: no PromptPack schema. |
| RWO-006 | `docs/audits/MECHANICAL_COVERAGE_AUDIT.md` | A+ | 7 Full / 8 Partial / 2 Stub / 15 Missing of 32 D&D 3.5e mechanics. 46.9% Missing. |

### Sprint Spec Created

- `docs/specs/RQ-LENS-SPARK-001_CONTEXT_ORCHESTRATION_SPRINT.md` — 5 deliverables gating Lens→Spark asset integration: PromptPack, Memory Retrieval, Summarization, Contradiction Handling, Evaluation Harness

### Git Commits (This Session)

1. `088bff0` — Phase 1 research deliverables and architectural decisions (12 files, 5122 lines)
2. `8477bcc` — HISTORICAL banners and scope clarifications to governance docs
3. `4a8f507` — GPT rehydration packet, voice research, PM inbox items (58 files)
4. `4d06065` — WO-FIX-001: Remove 5e concentration auto-displacement from DurationTracker
5. `62a1a10` — Harden AD-001 and AD-003 with PO-specified guardrails
6. `52c043a` — Complete Steps 1-5, WO-016/017 of execution plan
7. `4cbe57b` — Complete WO-018 Replay Regression Suite
8. `a8575ad` — WO-FIX-002: Critical hits in attack_resolver + AD-004 Evidence Gate
9. `60b4587` — WO-FIX-003: Unify AC/modifier computation in full_attack_resolver
10. `3ca2454` — AD-004 Layer 1: Evidence pointers in critical attack test docstrings
11. `94f2e4e` — PM session status update with hotfix completions
12. `6c91573` — WO-048: Damage Reduction system with full bypass matching
13. `74ba855` — WO-049: Concealment/Miss Chance system (PHB p.152)
14. `760176d` — WO-034-FIX: Wire Power Attack penalty through intent pipeline (PHB p.98)
15. `4de9cbd` — WO-051B: Policy Default Library with 20 environmental object classes (AD-003)
16. `fb8bc73` — WO-052B: Seeded Deterministic Generator for scene objects (AD-003)
17. `4efadd5` — AD-005 Physical Affordance Policy + WO-053 Equipment Item Catalog (35 items)
18. `0023c4b` — WO-054: Inventory + Encumbrance system (PHB p.162)
19. `5597f3d` — WO-055: Container Policies + Storage Location (AD-005 Layer 2)
20. `3fefa9b` — WO-045B: PromptPack v1 Schema (AD-002 five-channel wire protocol)
21. `530739f` — PM session status update with Phase 2 completions
22. `753673f` — WO-046B: NarrativeBrief completion — wire all event types (82 new tests)
23. `abdcfd6` — WO-056: Gear Affordance Tags for Lens→Spark (AD-005 Layer 3, 16 tests)

---

## Critical Bugs Found

### P0: DurationTracker 5e Concentration Limiter (WO-FIX-001) — FIXED

**File:** `aidm/core/duration_tracker.py:115`
**Bug:** `_concentration: Dict[str, str]` implements 5e one-concentration-per-caster rule. Lines 124-136 auto-remove existing concentration effect when a new one is applied.
**3.5e Rule:** Multiple concentration spells ARE allowed (each requires a Concentration check, but no automatic displacement).
**Fix:** Changed to `Dict[str, List[str]]` (one-to-many mapping), removed auto-end logic.
**Commit:** `4d06065`
**Status:** COMPLETE. Golden tests regenerated, full suite green.

### P1: Critical Hits Missing from Single Attacks (WO-FIX-002) — FIXED

**File:** `aidm/core/attack_resolver.py`
**Bug:** No critical hit logic. Only `full_attack_resolver.py` handled criticals. Standard single attacks could not score critical hits.
**Fix:** Added threat detection, confirmation roll, damage multiplication. Also fixed expanded threat range auto-hit bug in both resolvers.
**Commit:** `a8575ad`
**Status:** COMPLETE. 8 new tests, gold masters regenerated.

### P1: Full Attack Resolver Modifier Bypass (WO-FIX-003) — FIXED

**File:** `aidm/core/full_attack_resolver.py`
**Bug:** Used raw entity AC directly, bypassing condition modifiers (CP-16), cover (CP-19), terrain higher ground (CP-19), mounted bonuses (CP-18A), and feat modifiers (WO-034).
**Fix:** Added targeting legality, total cover blocking, and all modifier layers matching attack_resolver.py. Full audit trail in event payloads.
**Commit:** `60b4587`
**Status:** COMPLETE. 5 new tests, 3794 total passed, 0 regressions.

---

## Seam Protocol Health

| Seam | Health | Critical Gap |
|------|--------|--------------|
| Box → Lens | **GREEN** | NarrativeBrief handles all event types (WO-046B). Dual STP systems not yet unified but functional. |
| Lens → Spark | **YELLOW** | PromptPack v1 schema + visible_gear wired (GAP-002 resolved). Two prompt paths not yet unified (GAP-007). |
| Spark → Immersion | **RED** | No ImmersionPlan schema. Adapters exist in isolation with no orchestrator. |

---

## Mechanical Coverage Status

**Overall: 10 Full / 7 Partial / 2 Stub / 13 Missing out of 32 D&D 3.5e mechanics**

Recent promotions:
- Damage Reduction: Missing → **Full** (WO-048)
- Concealment/Miss Chance: Missing → **Full** (WO-049)
- Power Attack: Partial → **Full** (WO-034-FIX)

**New AD-003 infrastructure:** Policy Default Library (20 env object classes) + Seeded Scene Generator (5 templates, deterministic).

**New work stream (PO-directed):** Physical Affordance / Inventory system (AD-005, WO-053 through WO-056).

**Remaining Tier 1 (Critical Path) gaps:** Sneak Attack (blocked on flanking geometry), 5-foot step completion, Inventory/Encumbrance (new — WO-054).

Full details: `docs/audits/MECHANICAL_COVERAGE_AUDIT.md`

---

## Open Questions Awaiting PO Decision

| ID | Topic | Options |
|----|-------|---------|
| OQ-1 | HP description margin | ±5% (strict) vs ±10% (relaxed) |
| OQ-2 | NPC HP visibility | Never / Bloodied only / DM toggle |
| OQ-3 | KILL-002 strictness | Strict (no numbers) / Contextual |
| OQ-4 | DM override UX | No override / Edit / Full rewrite |
| OQ-5 | Default tone params | Dramatic+terse / Dramatic+verbose / Neutral |
| OQ-6 | NPC voice mutability | Fixed at start / Mutable by DM |
| OQ-7 | Test runtime re-baseline | Per-test avg / New wall-clock / Downgrade |

---

## Execution Plan Updates

The execution plan v2 (`docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md`) has been updated with:

- **3 hotfix WOs** (WO-FIX-001 through WO-FIX-003) — execute before Phase 2
- **8 new WOs** (WO-045B through WO-052B) — scheduled into Phase 2/3
- **4 additions to existing WOs** (WO-034, WO-035) — from mechanical coverage audit
- **7 open questions** (OQ-1 through OQ-7) — awaiting PO decision
- **Expanded cross-references** linking all new deliverables

---

## What to Do Next

### Immediate

1. **GAP-007 resolution**: Unify two prompt assembly paths (GuardedNarrationService._build_llm_prompt + ContextAssembler) via PromptPack
2. **WO-050B**: Sneak Attack (requires flanking detection prerequisite — geometry)
3. **Spark → Immersion seam**: Design ImmersionPlan schema to connect Spark outputs to TTS/Image adapters

### Phase 2 Dispatch (Ready)

| Item | Agent Type | Status |
|------|-----------|--------|
| WO-048: Damage Reduction system | Coding agent | **COMPLETE** (`6c91573`) |
| WO-049: Concealment/miss chance | Coding agent | **COMPLETE** (`74ba855`) |
| WO-034-FIX: Power Attack integration | Coding agent | **COMPLETE** (`760176d`) |
| WO-036: Spell registry expansion | Coding agent | **COMPLETE** (53 spells, prior session) |
| WO-051B: Policy Default Library | Coding agent | **COMPLETE** (`4de9cbd`) |
| WO-052B: Seeded Deterministic Generator | Coding agent | **COMPLETE** (`fb8bc73`) |
| WO-053: Equipment Item Catalog | Coding agent | **COMPLETE** (`4efadd5`) |
| WO-054: Inventory + Encumbrance | Coding agent | **COMPLETE** (`0023c4b`) |
| WO-055: Container Policies | Coding agent | **COMPLETE** (`5597f3d`) |
| WO-045B: PromptPack v1 Schema | Coding agent | **COMPLETE** (`3fefa9b`) |
| WO-046B: NarrativeBrief completion | Coding agent | **COMPLETE** (`753673f`) |
| WO-056: Gear Affordance Tags | Coding agent | **COMPLETE** (`abdcfd6`) |

### Phase 2 Dispatch (Blocked)

| Item | Blocked By |
|------|-----------|
| WO-050B: Sneak Attack | Flanking detection prerequisite (geometry) |

---

## File Inventory (New This Session)

### Decisions
- `docs/decisions/AD-001_AUTHORITY_RESOLUTION_PROTOCOL.md` (190 lines)
- `docs/decisions/AD-002_LENS_CONTEXT_ORCHESTRATION.md` (180 lines)
- `docs/decisions/AD-003_SELF_SUFFICIENCY_RESOLUTION_POLICY.md` (225 lines)
- `docs/decisions/AD-004_MECHANICAL_EVIDENCE_GATE.md` (163 lines)

### Evidence Maps (AD-004)
- `docs/evidence/ATTACK_RESOLUTION.md` — 16 single attack + 10 full attack + 3 weapon mechanics mapped
- `docs/evidence/CONCENTRATION_AND_DURATION.md` — 9 concentration + 4 anti-5e + 8 duration mechanics mapped

### Mechanical Systems (Phase 2)
- `aidm/core/damage_reduction.py` — WO-048: DR resolver with bypass matching (90 lines)
- `aidm/core/concealment.py` — WO-049: Concealment/miss chance resolver (90 lines)
- `tests/test_damage_reduction.py` — 19 DR tests (unit + integration)
- `tests/test_concealment.py` — 19 concealment tests (unit + integration)
- `tests/test_power_attack_integration.py` — 10 Power Attack integration tests

### Data Layer (AD-003)
- `aidm/data/__init__.py` — Package exports for PDL + Scene Generator
- `aidm/data/policy_defaults.json` — 20 environmental object classes (DMG-sourced)
- `aidm/data/policy_defaults_loader.py` — Typed PDL loader (PolicyDefaultLibrary, ObjectDefault, Dimensions)
- `aidm/data/scene_generator.py` — Seeded deterministic generator (5 scene templates)
- `tests/test_policy_defaults.py` — 28 PDL tests
- `tests/test_scene_generator.py` — 19 scene generator tests

### Research
- `docs/research/RQ_SPARK_001_SYNTHESIS.md` (1046 lines)
- `docs/research/RQ_NARR_001_SYNTHESIS.md` (935 lines)

### Audits
- `docs/audits/5E_CONTAMINATION_AUDIT.md` (262 lines)
- `docs/audits/MECHANICAL_COVERAGE_AUDIT.md` (467 lines)
- `docs/audits/SEAM_PROTOCOL_ANALYSIS.md` (491 lines)

### Governance
- `docs/CURRENT_CANON.md` (updated — AD-001/002/003 added to Tier 1)
- `docs/DOC_DRIFT_LEDGER.md` (161 lines, 6 entries)

### Specs
- `docs/specs/RQ-LENS-SPARK-001_CONTEXT_ORCHESTRATION_SPRINT.md` (607 lines)
- `docs/planning/GPT_RESEARCH_SYNTHESIS_ACTION_PLAN.md` (450 lines)

### Lens Layer (WO-046B, WO-056)
- `aidm/lens/narrative_brief.py` — WO-046B/056: NarrativeBrief with all event types + visible_gear (770 lines)
- `tests/test_narrative_brief_046b.py` — 82 WO-046B tests (spell/maneuver/AoO/movement/full attack/condition/concealment)
- `tests/test_gear_affordance_056.py` — 16 WO-056 tests (gear resolution, pipeline, containment boundary)

---

*This document supersedes all prior session summaries. Next PM session should read this first, then the PSD, then proceed with the "What to Do Next" section above.*

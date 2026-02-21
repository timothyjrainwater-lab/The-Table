# WO-VOICE-TYPED-CALL-SPEC-001: Typed Call Contract — Every Spark Invocation is Mode-Locked

**Classification:** CODE (contract document + gate tests + validator script)
**Priority:** BURST-001 Tier 1.3. Spec freeze. No engine changes.
**Dispatched by:** Slate (PM)
**Date:** 2026-02-21
**Origin:** BURST-001 build order. Source: `docs/research/VOICE_CONTROL_PLANE_CONTRACT.md` (Sections 2-3), `docs/research/RQ-SPRINT-004_SPARK_CONTAINMENT_AUDIT.md`, Playbook Section 2.

---

## Context

Tier 1.1 (CLI Grammar Contract) froze **output formatting** — how lines look and which ones get spoken.
Tier 1.2 (Unknown Handling Contract) froze **input failure handling** — what happens when the system can't understand the player.

Tier 1.3 freezes **the invocation boundary between Lens and Spark**. Every call to the LLM must carry a CallType that defines what the LLM is allowed to claim, what it's forbidden from asserting, and what happens when output violates the contract.

**The rule:** Spark has ZERO mechanical authority. The CallType enforces this at the invocation boundary, before the LLM sees the prompt.

---

## Objective

Produce a binding contract document (`docs/contracts/TYPED_CALL_CONTRACT.md`) that defines:
1. The CallType enum — every legal Spark invocation type
2. Per-type input schema — what context Lens must provide
3. Per-type output schema — what fields Spark must return
4. Per-type forbidden claims — what the LLM is never allowed to assert
5. Per-type fallback — what template replaces failed/rejected output
6. Validation pipeline — which validators run and in what order
7. Integration points with Tier 1.1 (line type conformance) and Tier 1.2 (clarification flows)

Plus gate tests and a validator script, same pattern as Tier 1.1 and 1.2.

---

## Scope

### IN SCOPE

1. **Contract document** — `docs/contracts/TYPED_CALL_CONTRACT.md`. Follows the same structure as `CLI_GRAMMAR_CONTRACT.md` and `UNKNOWN_HANDLING_CONTRACT.md`.

2. **CallType definitions** — Six types identified in research. For each type, define:
   - **Authority level:** ATMOSPHERIC, UNCERTAIN, INFORMATIONAL, or NON-AUTHORITATIVE
   - **Input schema:** Required context fields (e.g., NarrativeBrief, entity list, session state)
   - **Output schema:** Required return fields (e.g., narration_text, tone_marker, provenance)
   - **Forbidden claims:** Regex patterns or vocabulary that constitute mechanical assertion violations
   - **Line type mapping:** Which Tier 1.1 line types this CallType may produce
   - **Fallback template:** What replaces output if validation fails
   - **Latency ceiling:** Max generation time before fallback fires

   The six types (confirm or adjust based on research reading):
   | CallType | Authority | Purpose |
   |----------|-----------|---------|
   | COMBAT_NARRATION | ATMOSPHERIC | Flavor prose for resolved actions |
   | NPC_DIALOGUE | ATMOSPHERIC | NPC speech during narration |
   | SUMMARY | INFORMATIONAL | Compressing event history |
   | RULE_EXPLAINER | NON-AUTHORITATIVE | Answering rules questions |
   | OPERATOR_DIRECTIVE | UNCERTAIN | Asking for clarification/menu options |
   | CLARIFICATION_QUESTION | UNCERTAIN | Generating clarification prompts |

3. **Validation pipeline spec** — Define the ordered validator chain:
   - Stage 1: GrammarShield (Tier 1.1 conformance — line type, anti-patterns)
   - Stage 2: ForbiddenClaimChecker (per-CallType forbidden vocabulary/patterns)
   - Stage 3: (Future — EvidenceValidator, not required in this spec, but slot must exist)

4. **Invariants** — Minimum 4:
   - TC-INV-01: Every Spark invocation carries exactly one CallType
   - TC-INV-02: No CallType may assert mechanical outcomes (AC, HP, damage values, save results, hit/miss)
   - TC-INV-03: Fallback template exists for every CallType (no invocation can produce empty output)
   - TC-INV-04: Validation pipeline is ordered and deterministic (same output, same validators, same verdict)

5. **Gate tests** — New test file `tests/test_typed_call_gate_l.py`. Gate L tests (L-01 through L-XX). Minimum gates:
   - L-01: Every CallType has all required fields (input schema, output schema, forbidden claims, fallback, latency ceiling)
   - L-02: No two CallTypes share the same authority level + purpose combination (unique typing)
   - L-03: Every CallType's line type mapping is a subset of Tier 1.1's seven line types
   - L-04: Every CallType has a non-empty forbidden claims list
   - L-05: Every CallType has a fallback template that itself passes GrammarShield validation
   - L-06: Forbidden claims patterns for COMBAT_NARRATION reject strings containing mechanical values (e.g., "AC 18", "deals 14 damage", "rolls a 17")
   - L-07: OPERATOR_DIRECTIVE and CLARIFICATION_QUESTION CallTypes map to Tier 1.2 escalation flow (clarification budget applies)
   - L-08: Invariants TC-INV-01 through TC-INV-04 are testable assertions
   - Additional gates at builder's discretion if the research suggests more coverage

6. **Validator script** — `scripts/check_typed_call.py`. Reads the contract, checks structural completeness (all types defined, all fields present, no orphan references).

### OUT OF SCOPE

- No engine code changes. No changes to `narrator.py`, `dm_persona.py`, or any Spark runtime.
- No implementation of the validation pipeline — this spec defines WHAT validators must check, not the runtime code.
- No EvidenceValidator implementation (that's a later tier).
- No changes to Tier 1.1 or Tier 1.2 contracts.
- No new line types. The CallType line-type mapping uses existing Tier 1.1 types only.
- No changes to doctrine files.

---

## Research Sources (READ, do not send to builders — but builder must read these)

The builder must read these to understand the typed call design:

1. `docs/research/VOICE_CONTROL_PLANE_CONTRACT.md` — Sections 2-3: call type taxonomy, authority levels, forbidden claims concept
2. `docs/research/RQ-SPRINT-004_SPARK_CONTAINMENT_AUDIT.md` — Typed call schemas, containment invariants
3. `docs/contracts/CLI_GRAMMAR_CONTRACT.md` — Tier 1.1 (frozen). Line types, grammar rules, voice routing. The CallType output must conform.
4. `docs/contracts/UNKNOWN_HANDLING_CONTRACT.md` — Tier 1.2 (frozen). Failure classes, clarification budget. OPERATOR_DIRECTIVE and CLARIFICATION_QUESTION must integrate.

---

## Design Decisions (PM-resolved)

| # | Decision | Resolution | Rationale |
|---|----------|------------|-----------|
| TD-01 | Forbidden claims: D&D-specific or parameterized? | **Parameterized.** Define as pattern categories (mechanical_values, rule_citations, outcome_assertions) with D&D examples. The contract must work for any game system. | GT v12: system is not D&D-only in architecture. |
| TD-02 | EvidenceValidator in this spec? | **No.** Slot it as Stage 3 "RESERVED — future tier" in the pipeline. GrammarShield + ForbiddenClaimChecker are sufficient for Tier 1.3. | Escalation ladder: don't build what you haven't proven you need. |
| TD-03 | Retrofit existing narrator.py calls? | **No.** This is a spec-only WO. The contract defines the target state. A future wiring WO retrofits existing calls. | Spec freeze before code changes. |
| TD-04 | Latency ceiling: per-call or per-turn? | **Per-call.** Each CallType has its own ceiling. A turn that makes multiple calls sums the ceilings as worst-case. | Per-turn is too loose; a single slow call hides behind a generous aggregate. |

---

## Integration Seams

| Seam | Module | Relationship |
|------|--------|-------------|
| CLI Grammar Contract | `docs/contracts/CLI_GRAMMAR_CONTRACT.md` | READ ONLY — CallType line-type mapping must reference these types |
| Unknown Handling Contract | `docs/contracts/UNKNOWN_HANDLING_CONTRACT.md` | READ ONLY — OPERATOR_DIRECTIVE and CLARIFICATION_QUESTION must reference clarification budget |
| Spark Containment Audit | `docs/research/RQ-SPRINT-004_SPARK_CONTAINMENT_AUDIT.md` | READ ONLY — source for CallType definitions |
| Voice Control Plane | `docs/research/VOICE_CONTROL_PLANE_CONTRACT.md` | READ ONLY — source for authority levels and forbidden claims |

No code integration seams — this is a spec-only WO.

---

## Assumptions to Validate

| # | Assumption | How to validate |
|---|-----------|----------------|
| A1 | Six CallTypes are the complete set (no missing types in research) | Read all research sources, cross-reference with Playbook Section 2 |
| A2 | Authority levels (ATMOSPHERIC, UNCERTAIN, INFORMATIONAL, NON-AUTHORITATIVE) are defined in the research | Read `VOICE_CONTROL_PLANE_CONTRACT.md` |
| A3 | GrammarShield patterns are already defined in Tier 1.1 contract | Read `CLI_GRAMMAR_CONTRACT.md` anti-pattern registry |
| A4 | Clarification budget (max rounds) is defined in Tier 1.2 contract | Read `UNKNOWN_HANDLING_CONTRACT.md` |
| A5 | Fallback templates for narration already exist in the Playbook (Section 4.3) | Read Playbook |

If any assumption fails, document what's missing and fill the gap in the contract (within scope).

---

## Stop Conditions

1. **Research sources missing or contradictory** — If the six CallTypes don't match across sources, stop and document the conflict.
2. **Authority levels undefined** — If the research doesn't define authority levels, stop. This is the load-bearing concept.
3. **Tier 1.1 or 1.2 contracts need modification** — Stop. Those are frozen. Work within their constraints.
4. **Scope creep into engine code** — No runtime implementation. This is a contract.

---

## Implementation Order

1. Read all 4 research sources + both existing contracts
2. Validate assumptions A1-A5
3. Draft the contract document structure (match CLI_GRAMMAR_CONTRACT.md pattern)
4. Define the 6 CallTypes with all required fields
5. Define the validation pipeline (3 stages, Stage 3 reserved)
6. Define the 4+ invariants
7. Write gate tests (L-01 through L-XX)
8. Write validator script
9. Run full test suite — 0 regressions

---

## Preflight

Run `python scripts/preflight_canary.py` and log results in `pm_inbox/PREFLIGHT_CANARY_LOG.md` before starting work.

---

## Delivery

### Commit

Single commit. Message format: `feat: WO-VOICE-TYPED-CALL-SPEC-001 — Typed Call Contract, Gate L tests, validator`

All new gate tests must pass. All existing tests must show zero regressions.

### Completion Report

File as `pm_inbox/DEBRIEF_WO-VOICE-TYPED-CALL-SPEC-001.md`. 500 words max. Five mandatory sections:

0. **Scope Accuracy** — Did you deliver what was asked? Note any deviations.
1. **Discovery Log** — Anything you found that the dispatch didn't anticipate.
2. **Methodology Challenge** — Hardest part and how you solved it.
3. **Field Manual Entry** — One tradecraft tip for the next builder working in this area.
4. **Builder Radar** (mandatory, 3 labeled lines):
   - **Trap.** Hidden dependency or trap for the next WO.
   - **Drift.** Current drift risk.
   - **Near stop.** What got close to triggering a stop condition.

### Audio Cue (MANDATORY)

When all work is complete (commit landed, debrief written), fire this command so the Operator knows you're done:

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

### Debrief Focus Questions

1. **CallType completeness:** Did the research support exactly six types, or did you find more/fewer? What did you add or remove, and why?
2. **Forbidden claims coverage:** How did you parameterize the forbidden claims to be game-system-independent while still being testable with D&D examples?

# Agent Projection Notes — Spark/Lens/Box Doctrine
## Binding Constraints Derived from SPARK_LENS_BOX_DOCTRINE.md

**Document Type:** Governance / Agent Instructions
**Date:** 2026-02-10
**Authority:** PM (Thunder) + Agent D (Research Orchestrator)
**Status:** ✅ **BINDING** (non-negotiable for all agents)
**Source:** `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md`

---

## Purpose

This document provides **one-sentence binding constraints** for each agent, derived from the canonical Spark/Lens/Box doctrine.

**DO NOT distribute the full doctrine conversation to agents.** Use these crystallized projections instead.

---

## Agent A (Implementation/Narration)

### Binding Constraint

**"SPARK output is never authoritative; only BOX can declare illegal; LENS can adapt tone; enforce provenance tags on all user-facing output."**

### Enforcement Rules

1. **SPARK Layer (Narration Generation)**
   - ✅ Generate narrative content freely without refusal
   - ❌ NEVER assert mechanical authority ("you cannot," "this is illegal")
   - ❌ NEVER mutate WorldState or memory directly from narration
   - ✅ All SPARK output labeled `[NARRATIVE]` or `[UNCERTAIN]`

2. **BOX Layer (Deterministic Engine)**
   - ✅ ALL mechanical rulings ("hit/miss," "legal/illegal," damage) sourced from BOX
   - ✅ ALL BOX output labeled `[BOX]` with rule citation
   - ❌ NEVER delegate mechanical decisions to SPARK/LLM

3. **LENS Layer (Presentation)**
   - ✅ Adapt tone/verbosity for user expertise
   - ✅ Apply post-generation content filtering (player safety)
   - ❌ NEVER invent mechanical claims not present in BOX
   - ✅ Preserve provenance labels (cannot strip `[BOX]` tags)

4. **Provenance Labeling**
   - ALL user-facing mechanical output MUST include:
     - `[BOX]` — Authoritative (attack rolls, spell effects, legal rulings)
     - `[DERIVED]` — Inferred from BOX state (e.g., "you seem injured")
     - `[NARRATIVE]` — SPARK-generated flavor (no authority)
     - `[UNCERTAIN]` — System guessing (paraphrase, clarification)

### Code Review Checklist

When reviewing Agent A code:
- ✅ All narration generation returns ephemeral strings (no state mutation)
- ✅ All mechanical claims sourced from BOX with `[BOX]` tag
- ✅ No SPARK refusal logic (refusal via LENS gating or BOX illegality only)
- ✅ Provenance tags present on all user-facing output

### Test Requirements

- Add tests verifying SPARK never mutates state
- Add tests verifying all mechanical claims labeled `[BOX]`
- Add tests verifying LENS preserves provenance through transformations

---

## Agent B (Schema/Validation)

### Binding Constraint

**"Any schema or memory pathway that allows SPARK→state writes or authority claims without BOX validation is architecturally invalid."**

### Enforcement Rules

1. **Schema Design**
   - ✅ ALL state mutations event-sourced through BOX
   - ❌ NO direct LLM→memory write paths
   - ✅ Memory schemas immutable during SPARK operations (frozen snapshots)
   - ✅ Event schemas include full provenance (event_id, rule_citation, BOX_hash)

2. **Validation Gates**
   - ✅ All SPARK-derived facts MUST pass validation before memory write
   - ✅ Validation rejects hallucinations (fact not in memory snapshot)
   - ❌ NO validation bypass paths (all writes gated)

3. **Authority Traceability**
   - ✅ Every mechanical ruling traceable to BOX computation
   - ✅ Every memory write traceable to event_id
   - ❌ NO "magic" writes without provenance

### Schema Review Checklist

When reviewing schemas:
- ✅ No mutable fields accessible to SPARK layer
- ✅ All write methods require event_id or BOX validation
- ✅ Provenance fields present (source: BOX/DERIVED/NARRATIVE)
- ❌ REJECT any schema allowing SPARK→state writes

### Test Requirements

- Add tests verifying frozen snapshots immutable
- Add tests verifying all writes require event_id
- Add tests verifying validation rejects hallucinations

---

## Agent C (UX)

### Binding Constraint

**"UX must visually distinguish BOX truth vs DERIVED vs NARRATIVE; never let narrative feel like authoritative rulings."**

### Enforcement Rules

1. **Visual Distinction**
   - ✅ `[BOX]` output rendered with authoritative styling (bold, distinct color)
   - ✅ `[NARRATIVE]` output rendered with flavor styling (italics, muted color)
   - ✅ `[DERIVED]` output rendered with informational styling (grey, smaller font)
   - ✅ `[UNCERTAIN]` output rendered with tentative styling (question mark, light color)

2. **Never Blur Authority**
   - ❌ NEVER present SPARK narration as mechanical truth
   - ❌ NEVER strip provenance labels from BOX output
   - ✅ Always preserve rule citations from BOX (show source: PHB 141)

3. **Trust Repair Features**
   - ✅ "Show me why" links for all BOX rulings (drill down to computation)
   - ✅ Full audit trail accessible (combat log with provenance)
   - ✅ Error messages legible (explain what failed, cite rule, show inputs)

### UX Review Checklist

When reviewing UX:
- ✅ Provenance visually distinct (BOX bold, NARRATIVE italic, etc.)
- ✅ Rule citations present on BOX output ("PHB 141: AoO provoked")
- ✅ "Show me why" feature implemented for all BOX rulings
- ❌ REJECT any UI that strips provenance labels

### Test Requirements

- Add visual regression tests for provenance rendering
- Add tests verifying rule citations displayed
- Add tests verifying "show me why" links functional

---

## Agent D (Governance)

### Binding Constraint

**"Certification must explicitly attest Spark/Lens/Box separation; CHECK-007 required for every M1 PR."**

### Enforcement Rules

1. **PR Gate Enforcement**
   - ✅ ALL M1 PRs MUST pass CHECK-007 (Spark/Lens/Box Separation)
   - ✅ CHECK-007 verifies:
     - No SPARK→state writes
     - No SPARK refusal (refusal via LENS/BOX only)
     - Provenance labeling present
     - No LENS authority invention

2. **Monitoring Protocol**
   - ✅ INV-TRUST-001 monitored continuously (Authority Provenance Preserved)
   - ✅ Weekly reviews verify provenance compliance
   - ✅ Any trust violation escalated to PM immediately

3. **Certification Requirements**
   - ✅ All M1 certifications MUST attest Spark/Lens/Box separation
   - ✅ Evidence MUST include provenance tag coverage
   - ❌ REJECT certification if separation violated

### Governance Review Checklist

When reviewing PRs:
- ✅ CHECK-007 explicitly verified (binary pass/fail)
- ✅ Provenance tag grep shows coverage
- ✅ No SPARK→state write paths detected
- ❌ REJECT immediately if CHECK-007 fails

### Escalation Path

- Any CHECK-007 failure → REJECT PR, notify author + Agent D
- Any INV-TRUST-001 violation → HALT, notify PM within 24 hours
- Sustained trust violations → M1 unlock suspension

---

## Cross-Agent Integration

### Workflow: SPARK → LENS → User (Narrative)

1. **Agent A (SPARK)** generates narration text
2. **Agent A (LENS)** applies tone/filtering
3. **Agent C (UX)** renders with `[NARRATIVE]` tag
4. User sees: `[NARRATIVE] "The orc bellows in rage."`

### Workflow: BOX → LENS → User (Authority)

1. **Agent A (BOX)** computes attack roll: `{roll: 18, AC: 16, result: HIT}`
2. **Agent A (LENS)** formats: `"Attack hits (roll 18 vs AC 16)"`
3. **Agent C (UX)** renders with `[BOX]` tag + rule citation
4. User sees: `[BOX] "Attack hits (roll 18 vs AC 16). [PHB 134: Attack Roll]"`

### Workflow: SPARK → Validation → BOX → Memory (Fact Extraction)

1. **Agent A (SPARK)** extracts fact: `"Player defeated orc chief"`
2. **Agent B (Validation)** checks memory snapshot: `validate_fact_exists_in_memory()`
3. **IF valid:** **Agent A (BOX)** writes via event-sourcing with event_id
4. **IF invalid:** REJECT write, log hallucination (KILL-003)

---

## Violation Examples (What NOT to Do)

### ❌ WRONG: SPARK Asserts Authority

```python
# SPARK narration says:
"You cannot move there (difficult terrain)"

# Problem: SPARK asserted mechanical ruling without BOX
# Fix: BOX computes legality → SPARK narrates result
```

### ❌ WRONG: LENS Invents Mechanics

```python
# LENS code adds:
output += " [You provoke an AoO]"

# Problem: LENS invented mechanical claim not from BOX
# Fix: LENS only formats BOX output, never adds mechanics
```

### ❌ WRONG: Missing Provenance

```python
# User sees:
"Your attack hits for 15 damage"

# Problem: No provenance tag ([BOX] missing)
# Fix: "[BOX] Your attack hits for 15 damage [PHB 134]"
```

### ❌ WRONG: SPARK→State Write

```python
# Code path:
narration_text = generate_narration(event)
world_state.hp -= damage_from_narration(narration_text)

# Problem: Narration text used to mutate state
# Fix: BOX computes damage → state updated via event → SPARK narrates
```

---

## Compliance Summary

**All agents MUST:**
- ✅ Enforce their projected constraint (see agent-specific section)
- ✅ Label all user-facing output with provenance
- ✅ Route all mechanical authority through BOX
- ✅ Preserve trust repair features (logs, citations, audit trail)

**Agent D MUST:**
- ✅ Verify CHECK-007 on every M1 PR
- ✅ Monitor INV-TRUST-001 continuously
- ✅ Escalate trust violations immediately

**PM (Thunder) MAY:**
- Override CHECK-007 with explicit justification (rare exception)
- Update doctrine for M4+ (not M1-M3, doctrine frozen)

---

**END OF AGENT PROJECTION NOTES**

**Date:** 2026-02-10
**Agent:** Agent D (Research Orchestrator)
**Authority:** PM (Thunder) + Agent D Stop Authority
**Status:** ✅ **BINDING** (mandatory for all agents)
**Source:** `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md`

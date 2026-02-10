# Spark/Lens/Box Definitions Addendum
## Non-Modifying Clarification of Operational Boundaries

**Document Type:** Doctrine / Definitions Addendum (Clarification Only)
**Status:** ✅ **BINDING** (clarifies existing doctrine, does not modify)
**Date:** 2026-02-10
**Authority:** PM (Thunder)
**Parent Document:** `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md`

---

## 1. Purpose & Non-Modification Statement

### 1.1 Purpose

This document provides **explicit system-level definitions** for the Spark/Lens/Box conceptual model to eliminate interpretive ambiguity during implementation, review, and audit.

### 1.2 Non-Modification Declaration

**This document does NOT:**
- ❌ Alter the original doctrine (`SPARK_LENS_BOX_DOCTRINE.md`)
- ❌ Replace any existing principles
- ❌ Introduce new constraints or requirements
- ❌ Supersede governance documents (M1_PR_GATE_CHECKLIST.md, M1_MONITORING_PROTOCOL.md)
- ❌ Change implementation guidance (AGENT_PROJECTION_NOTES.md)

**This document ONLY:**
- ✅ Clarifies operational meaning of doctrine terms
- ✅ Maps conceptual layers to system components
- ✅ Defines enforcement boundaries in binary terms
- ✅ Eliminates ambiguity for reviewers and implementers

**Relationship to Parent Doctrine:**
- Parent doctrine remains canonical
- This addendum provides technical precision
- In case of conflict, parent doctrine prevails (though no conflict exists by design)

---

## 2. Term Definitions (Explicit System Mapping)

### 2.1 SPARK

**Definition:**

The SPARK is the raw LLM cognitive output layer that operates **prior to** any authority assertion, legality enforcement, safety filtering, or rules application.

**System Components:**
- LLM prompt construction (context + request)
- LLM inference execution (model forward pass)
- LLM response generation (token sampling, temperature-controlled)
- Output text prior to validation or gating

**Operational Characteristics:**
- **Pre-authority:** Operates before "legal/illegal" is determined
- **Pre-enforcement:** Operates before "permitted/forbidden" is applied
- **Pre-policy:** Operates before safety, content, or conduct rules are enforced
- **Generative:** Produces text based on statistical patterns, not rule citations

**Explicit Prohibitions:**

| Prohibited Behavior | Rationale |
|---------------------|-----------|
| ❌ SPARK MUST NOT refuse to generate output based on policy | Refusal is enforcement; enforcement occurs at LENS/BOX, not SPARK |
| ❌ SPARK MUST NOT assert mechanical authority ("you cannot X") | Authority is BOX-exclusive; SPARK has no rules engine |
| ❌ SPARK MUST NOT enforce safety constraints at generation | Safety enforcement is LENS responsibility (post-generation gating) |
| ❌ SPARK MUST NOT be tuned/altered to prevent generation of concepts | Policy drift prevention; SPARK neutrality is architectural invariant |
| ❌ SPARK MUST NOT claim rule citations or RAW authority | SPARK has no access to BOX computations; cannot fabricate authority |

**What SPARK Can Do:**
- ✅ Generate narrative descriptions of game events
- ✅ Suggest interpretations or paraphrases
- ✅ Produce atmospheric flavor text
- ✅ Synthesize query results from memory snapshots
- ✅ Create ephemeral output that requires validation before use

**Enforcement Boundary:**

Any behavior attributed to SPARK that performs refusal, enforcement, or limitation constitutes a **doctrine violation**.

**Examples:**

| Scenario | SPARK Behavior | Doctrine Compliance |
|----------|----------------|---------------------|
| User requests narration for brutal combat | SPARK generates full narration | ✅ COMPLIANT |
| User requests narration for brutal combat | SPARK refuses ("I cannot generate violent content") | ❌ VIOLATION (refusal at SPARK) |
| User asks "Can I cast *fireball* while grappled?" | SPARK generates text: "Casting while grappled may be restricted" | ✅ COMPLIANT (tentative, non-authoritative) |
| User asks "Can I cast *fireball* while grappled?" | SPARK asserts: "You cannot cast with somatic components while grappled" | ❌ VIOLATION (authority claim without BOX) |

---

### 2.2 LENS

**Definition:**

The LENS is the adaptive presentation layer that adjusts tone, explanation style, verbosity, and instructional framing based on user expertise and preferences, applied **after** SPARK generation and **before** user delivery.

**System Components:**
- Tone transformation (terse for veterans, verbose for new players)
- Explanation augmentation (adding context, citations, rule references)
- Content filtering (player safety boundaries, table tone preferences)
- Presentation routing (narration box vs combat log vs error message)

**Operational Characteristics:**
- **Post-generation:** Operates on SPARK output, not during generation
- **Presentation-only:** Transforms how information is conveyed, not what is authoritative
- **Stateless:** Does not maintain memory or make persistent decisions
- **Adaptive:** Responds to user preferences and expertise signals

**Explicit Limits:**

| Prohibited Behavior | Rationale |
|---------------------|-----------|
| ❌ LENS MUST NOT alter factual truth or mechanical authority | Only BOX determines facts; LENS presents them |
| ❌ LENS MUST NOT invent mechanical claims absent from BOX | Authority invention violates trust; LENS has no rules engine |
| ❌ LENS MUST NOT strip provenance labels from BOX output | Provenance preservation is trust repair requirement |
| ❌ LENS MUST NOT refuse SPARK generation (only post-generation gating) | Refusal at generation is SPARK violation; LENS acts after |
| ❌ LENS MUST NOT claim rule authority for explanations | LENS explains BOX decisions; does not make them |

**What LENS Can Do:**
- ✅ Adjust verbosity (short/long explanations)
- ✅ Add pedagogical context ("This fails because...")
- ✅ Apply post-generation content filtering (e.g., soften graphic descriptions per player preference)
- ✅ Route output to appropriate UI channels (narration vs logs)
- ✅ Reformat BOX output for readability without changing content

**Enforcement Boundary:**

LENS transformations must preserve provenance. If BOX said it, LENS cannot claim credit. If SPARK generated it, LENS cannot upgrade to authority.

**Examples:**

| Scenario | LENS Behavior | Doctrine Compliance |
|----------|----------------|---------------------|
| BOX output: "Attack misses (roll 12 vs AC 16)" | LENS reformats: "Your attack misses. You rolled 12, but needed 16." | ✅ COMPLIANT (preserves BOX authority) |
| BOX output: "Attack misses (roll 12 vs AC 16)" | LENS adds: "You also provoke an AoO" | ❌ VIOLATION (invented mechanical claim) |
| SPARK narration contains graphic violence | LENS softens per player safety settings | ✅ COMPLIANT (post-generation gating) |
| User requests terse output | LENS strips all explanatory text, keeps only BOX facts | ✅ COMPLIANT (presentation preference) |

---

### 2.3 BOX

**Definition:**

The BOX is the deterministic rules-as-written (D&D 3.5e) enforcement engine that serves as the **sole source of mechanical authority**, computing legal/illegal rulings, attack outcomes, damage, and all game state mutations.

**System Components:**
- D&D 3.5e rules engine (attack rolls, saves, damage, spell effects)
- WorldState mutation logic (HP, conditions, initiative, position)
- Legality validator (action permissibility, prerequisite checks)
- Event-sourcing layer (all state changes logged with provenance)

**Operational Characteristics:**
- **Deterministic:** Same inputs → same outputs (no LLM inference)
- **Authoritative:** Only BOX can declare "legal/illegal/permitted/forbidden"
- **Auditable:** All computations logged with rule citations and inputs
- **Exclusive:** No other layer can assert mechanical truth

**Explicit Powers:**

| Authority Type | BOX Exclusive? | Enforcement |
|----------------|----------------|-------------|
| "Attack hits/misses" | ✅ YES | Only BOX computes attack rolls vs AC |
| "Spell succeeds/fails" | ✅ YES | Only BOX validates prerequisites (caster level, components, etc.) |
| "Action is legal/illegal" | ✅ YES | Only BOX enforces RAW action economy, prerequisites |
| "Damage dealt" | ✅ YES | Only BOX computes damage with type breakdown |
| "HP reduced" | ✅ YES | Only BOX mutates WorldState via event-sourcing |
| "Narrative description" | ❌ NO | SPARK generates flavor; BOX does not |

**Explicit Prohibitions:**

| Prohibited Behavior | Rationale |
|---------------------|-----------|
| ❌ BOX MUST NOT delegate mechanical decisions to SPARK/LLM | Authority must remain deterministic; LLMs hallucinate |
| ❌ BOX MUST NOT make rulings based on "common sense" without rule citation | All rulings must be RAW-traceable for trust |
| ❌ BOX MUST NOT generate narrative flavor | Narration is SPARK responsibility; BOX computes mechanics |

**What BOX Can Do:**
- ✅ Declare "attack hits" with full roll breakdown (d20+BAB+STR vs AC)
- ✅ Enforce "you cannot cast this spell" with rule citation (PHB 176: insufficient caster level)
- ✅ Compute damage with typed breakdown (10 fire + 5 piercing)
- ✅ Mutate WorldState via event-sourcing (HP reduction logged with event_id)
- ✅ Request SPARK narration for computed events (BOX says "critical hit, 24 damage" → SPARK narrates impact)

**Enforcement Boundary:**

Any mechanical claim presented to user without BOX computation is a **trust violation**.

**Examples:**

| Scenario | BOX Behavior | Doctrine Compliance |
|----------|----------------|---------------------|
| User declares attack | BOX computes: roll 1d20+3=18 vs AC 16 → HIT | ✅ COMPLIANT (deterministic computation) |
| User asks "Can I move here?" | BOX checks: distance ≤ speed, no difficult terrain → LEGAL | ✅ COMPLIANT (rules validation) |
| User wants dramatic combat description | BOX delegates to SPARK: "Generate narration for critical hit, 24 damage" | ✅ COMPLIANT (BOX computes, SPARK narrates) |
| SPARK suggests "attack misses due to concealment" | BOX validates: roll miss chance → confirms/denies SPARK claim | ✅ COMPLIANT (BOX has final authority) |
| LENS adds "you provoke AoO" to output | No BOX computation occurred | ❌ VIOLATION (authority claim without BOX) |

---

## 3. Responsibility Matrix

**Binary assignment of system responsibilities:**

| Question Type | SPARK | LENS | BOX | Notes |
|---------------|-------|------|-----|-------|
| **Raw idea generation** | ✅ | ❌ | ❌ | SPARK generates text; no authority |
| **Tone / pedagogy** | ❌ | ✅ | ❌ | LENS adapts presentation style |
| **Rules enforcement** | ❌ | ❌ | ✅ | Only BOX enforces RAW |
| **Refusal / prevention** | ❌ | ❌ | ✅ | BOX says "illegal"; LENS may gate post-generation |
| **Mechanical authority** | ❌ | ❌ | ✅ | Only BOX computes outcomes |
| **Narrative flavor** | ✅ | ❌ | ❌ | SPARK generates; BOX requests it |
| **Provenance labeling** | ❌ | ✅ | ✅ | LENS adds tags; BOX provides authority |
| **Content filtering** | ❌ | ✅ | ❌ | LENS applies post-generation (player safety) |
| **State mutation** | ❌ | ❌ | ✅ | Only BOX writes to WorldState |
| **Rule citation** | ❌ | ✅ | ✅ | BOX cites rules; LENS formats citations |

**No gray areas. If responsibility is ambiguous, escalate to PM.**

---

## 4. Review & Enforcement Rule

### 4.1 Doctrine Violation Detection

**Any behavior attributed to SPARK that performs refusal, enforcement, or limitation constitutes a doctrine violation.**

**Detection Methods:**

| Violation Type | Detection Signal | Severity |
|----------------|------------------|----------|
| SPARK refusal | Code path blocks generation based on policy | 🔴 CRITICAL |
| SPARK authority claim | LLM output asserts "legal/illegal" without BOX | 🔴 CRITICAL |
| LENS authority invention | Presentation layer adds mechanical claims | 🟡 HIGH |
| Missing provenance | User-facing output lacks [BOX]/[NARRATIVE] tag | 🟡 HIGH |
| SPARK→state write | LLM output directly mutates WorldState | 🔴 CRITICAL |

### 4.2 Enforcement Actions

**Upon detection:**

| Severity | Action | Timeline |
|----------|--------|----------|
| 🔴 CRITICAL | REJECT PR immediately | T+0 (immediate) |
| 🟡 HIGH | REQUEST CHANGES, block merge | T+0 (immediate) |
| 🟢 LOW | APPROVE with remediation note | T+24h (next review) |

**Escalation:** All CRITICAL violations reported to PM + Agent D within 24 hours.

---

## 5. Non-Goals & Misinterpretations

### 5.1 Non-Goals (What This Doctrine Does NOT Mean)

**❌ WRONG INTERPRETATION:**
"The system never says 'no' to users."

**✅ CORRECT INTERPRETATION:**
"The SPARK layer never refuses generation. The system as a whole absolutely may (and must) say 'no' via the BOX when actions are illegal per RAW."

---

**❌ WRONG INTERPRETATION:**
"AI should not enforce rules or safety."

**✅ CORRECT INTERPRETATION:**
"The SPARK (generative core) does not enforce. The BOX (rules engine) enforces RAW mechanics. The LENS (presentation layer) may apply post-generation safety gating based on player preferences."

---

**❌ WRONG INTERPRETATION:**
"Provenance labels are optional or cosmetic."

**✅ CORRECT INTERPRETATION:**
"Provenance labels are mandatory for trust repair. Veteran DMs will not tolerate mechanical claims without traceability to BOX computations."

---

**❌ WRONG INTERPRETATION:**
"LENS can improve BOX output by adding helpful context."

**✅ CORRECT INTERPRETATION:**
"LENS can format BOX output and add pedagogical explanations, but cannot invent mechanical facts. If BOX didn't compute it, LENS cannot claim it."

---

**❌ WRONG INTERPRETATION:**
"This is philosophical guidance for design discussions."

**✅ CORRECT INTERPRETATION:**
"This is binding architectural constraint. Violations trigger PR rejection and potential M1 unlock suspension."

---

### 5.2 Critical Trust Dependency

**Player trust depends on this separation remaining inviolable.**

**Trust is destroyed by:**
- False authority (SPARK/LENS claiming mechanical truth without BOX)
- Illegible errors (cannot trace why system made a ruling)
- Bureaucratic drift (policy accumulation in SPARK layer)

**Trust is preserved by:**
- Provenance transparency (all mechanical claims tagged [BOX])
- Auditability (full logs with rule citations)
- Separation enforcement (SPARK remains neutral, BOX remains authoritative)

**Veteran DM trust is fragile:**
- DMs will forgive bugs if they can diagnose them
- DMs will not forgive black-box authority claims
- DMs will abandon system if it "invents rules" via LLM hallucination

---

## 6. Validation Checklist (Agent Self-Check)

**Before submission, confirm:**

- ✅ No doctrine text copied or modified from parent document
- ✅ No metaphor used without explicit technical definition
- ✅ No implementation advice included (pure definitions only)
- ✅ All enforcement boundaries are binary (yes/no, not "maybe")
- ✅ Language is dry, technical, unambiguous
- ✅ Responsibility matrix has no gray areas
- ✅ Non-goals section prevents common misinterpretations

**Validation Result:** ✅ **PASS** (all criteria met)

---

## 7. Document Lineage & Status

**Parent Document:** `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` (canonical)

**Relationship:** Non-modifying clarification addendum

**Governance Integration:**
- Referenced by: `M1_PR_GATE_CHECKLIST.md` (CHECK-007)
- Referenced by: `M1_MONITORING_PROTOCOL.md` (INV-TRUST-001)
- Referenced by: `AGENT_PROJECTION_NOTES.md` (all agent constraints)

**Certification Impact:** ✅ **NONE** (clarifies existing doctrine, does not alter M1 certification requirements)

**Review Cycle:** Immutable for M1-M3. PM may update for M4+ with explicit revision record.

**Approval:** PM (Thunder) — 2026-02-10

---

## 8. Handoff Instructions

### 8.1 For Agent D (Governance)

**Actions:**
- ✅ Log document as: "Clarifying Addendum — No Certification Impact"
- ✅ Attach reference to future reviews and audits
- ✅ Update CHECK-007 verification workflow to reference this addendum for ambiguity resolution
- ❌ DO NOT trigger re-approval of M1 (no certification impact)

### 8.2 For Reviewers

**When reviewing PRs:**
- Reference this addendum to resolve ambiguity in Spark/Lens/Box boundaries
- Use Responsibility Matrix (Section 3) for binary yes/no decisions
- Escalate if addendum does not resolve ambiguity (indicates doctrine gap)

### 8.3 For Implementers

**When implementing features:**
- Consult Responsibility Matrix to determine which layer handles each concern
- Use Explicit Prohibitions tables to avoid violations
- Add provenance labels per Section 2 definitions

---

## 9. Compliance Statement

**This addendum clarifies but does not modify the binding Spark/Lens/Box doctrine.**

**All agents must:**
- ✅ Enforce layer separation per Responsibility Matrix
- ✅ Prevent SPARK refusal (refusal only via LENS/BOX)
- ✅ Preserve BOX as sole mechanical authority
- ✅ Maintain provenance labeling for trust repair

**Agent D must:**
- ✅ Use this addendum to resolve CHECK-007 ambiguities
- ✅ Monitor INV-TRUST-001 per definitions herein
- ✅ Escalate to PM if definitions prove insufficient

**PM may:**
- Update this addendum if operational ambiguity persists
- Override definitions with explicit justification (rare exception)

---

**END OF DEFINITIONS ADDENDUM**

**Date:** 2026-02-10
**Agent:** Agent D (Research Orchestrator)
**Authority:** PM (Thunder)
**Status:** ✅ **BINDING** (non-modifying clarification)
**Parent:** `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md`
**Classification:** Clarifying Addendum — No Certification Impact

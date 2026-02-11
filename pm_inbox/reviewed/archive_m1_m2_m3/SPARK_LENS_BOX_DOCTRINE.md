# Spark/Lens/Box Doctrine
## Canonical Conceptual Architecture for AIDM Authority & Trust

**Document Type:** Doctrine / Conceptual Constitution
**Status:** ✅ **BINDING** (non-negotiable architectural axiom)
**Date:** 2026-02-10
**Authority:** PM (Thunder) + Agent D (Research Orchestrator)
**Scope:** All AIDM components (engine, narration, memory, UX)

---

## 1. Purpose Statement

**This doctrine defines the immutable separation of concerns between intelligence, presentation, and authority in the AIDM system.**

The system is built for **veteran dungeon masters** who possess deep domain expertise and fragile trust. Any perception of false authority, bureaucratic drift, or illegible error destroys trust permanently.

This doctrine exists to **prevent three failure modes:**

1. **False Authority**: AI-generated output presented as mechanical truth when it is narrative/derived
2. **Bureaucratic Drift**: Corporate safety theater infecting the generative core
3. **Illegible Error**: Errors that cannot be debugged because provenance is lost

**Enforcement:** This doctrine is **binding**. Violations constitute architectural breaches and trigger immediate remediation.

---

## 2. The Four-Layer Containment Model

### Layer 1: SPARK

**Definition:** Pure neutral generative intelligence with zero constraints.

**Role:**
- Generate conceptual content without judgment, refusal, or enforcement
- Produce narrative, suggestions, interpretations, paraphrases
- Explore possibility space freely

**Non-negotiable Rules:**
- ✅ **SPARK NEVER REFUSES** — No "I cannot," "that would be inappropriate," or safety theater at generation
- ✅ **SPARK HAS NO AUTHORITY** — Cannot declare "this is legal/illegal," only "this is what I generated"
- ✅ **SPARK IS PRE-LAW** — Operates before rules, policy, or mechanical constraints are applied
- ✅ **SPARK CANNOT DRIFT** — No corporate bureaucracy, no policy accumulation, no judgment creep

**What SPARK Can Do:**
- Generate narration for any game event
- Suggest interpretations of rules text
- Paraphrase player intent
- Create atmospheric descriptions
- Synthesize query results

**What SPARK Cannot Do:**
- Assert mechanical authority ("you cannot do X")
- Refuse to generate content based on policy
- Make binding rulings on legality
- Mutate canonical game state

**Containment Mechanism:** SPARK output is ephemeral and non-authoritative until validated by BOX or presented through LENS.

---

### Layer 2: LENS

**Definition:** Adaptive delivery layer that adjusts tone, pacing, and assumptions without creating authority.

**Role:**
- Adapt presentation based on user expertise (veteran DM vs new player)
- Apply pacing/tone/style preferences
- Route SPARK output through appropriate presentation channels
- Apply **post-generation gating** (e.g., content filtering, player safety boundaries)

**Non-negotiable Rules:**
- ✅ **LENS ADAPTS STANCE, NOT AUTHORITY** — Can change how something is said, never what is authoritative
- ✅ **LENS GATES AFTER GENERATION** — "Forbidden" happens here, not in SPARK
- ✅ **LENS CANNOT INVENT MECHANICS** — Can present BOX results, cannot fabricate them
- ✅ **LENS MUST PRESERVE PROVENANCE** — Cannot blur BOX truth vs SPARK narrative

**What LENS Can Do:**
- Adjust verbosity (terse for veterans, verbose for new players)
- Apply content filters (player safety, table tone preferences)
- Route output to appropriate UI channels (narration box vs mechanical log)
- Add context/framing ("This is narrative flavor, not a binding ruling")

**What LENS Cannot Do:**
- Assert mechanical truth not sourced from BOX
- Refuse SPARK generation (only post-generation gating)
- Collapse provenance labels (cannot say "the rules say X" if BOX didn't compute it)

**Containment Mechanism:** LENS is stateless presentation logic; all mechanical truth flows from BOX.

---

### Layer 3: BOX

**Definition:** Deterministic referee engine with exclusive authority over game mechanics.

**Role:**
- Execute canonical D&D 3.5 rules (RAW)
- Compute attack rolls, saves, damage, movement, actions
- Enforce legality ("this action is permitted/illegal under RAW")
- Maintain authoritative game state (WorldState, initiative, HP, conditions)

**Non-negotiable Rules:**
- ✅ **BOX IS SOLE AUTHORITY** — Only BOX can declare "legal/illegal/permitted"
- ✅ **BOX IS DETERMINISTIC** — Same inputs → same outputs (no LLM drift)
- ✅ **BOX NEVER HALLUCINATES** — Every ruling is traceable to rules text or explicit computation
- ✅ **BOX IS TRANSPARENT** — All computations logged with provenance (rule citation, die rolls)

**What BOX Can Do:**
- Declare "attack hits/misses" with full roll breakdown
- Enforce "you cannot cast this spell (insufficient caster level)"
- Compute damage with typed breakdown (fire 10, piercing 5)
- Maintain initiative order, HP totals, condition durations

**What BOX Cannot Do:**
- Generate narrative flavor (that's SPARK)
- Adapt tone for user preference (that's LENS)
- Make rulings based on "common sense" without rules citation

**Containment Mechanism:** BOX is the only layer that mutates WorldState. All state changes are event-sourced with full provenance.

---

### Layer 4: LOGS

**Definition:** Immutable provenance and audit trail for trust repair.

**Role:**
- Capture every BOX computation (inputs, outputs, rule citations)
- Tag every output with source layer (BOX/DERIVED/NARRATIVE/UNCERTAIN)
- Enable post-hoc debugging ("why did the system rule X?")
- Support trust repair after errors

**Non-negotiable Rules:**
- ✅ **ALL BOX DECISIONS LOGGED** — Every mechanical ruling has full audit trail
- ✅ **PROVENANCE LABELING REQUIRED** — User-facing output tagged by source layer
- ✅ **ERRORS MUST BE LEGIBLE** — If system makes mistake, logs allow diagnosis and fix
- ✅ **NO SILENT FAILURES** — Errors are acceptable; illegible errors are not

**Provenance Labels:**
- `[BOX]` — Authoritative mechanical truth (attack roll, legal ruling)
- `[DERIVED]` — Inferred from BOX state but not computed (e.g., "you seem injured" from HP < 50%)
- `[NARRATIVE]` — SPARK-generated flavor (no mechanical authority)
- `[UNCERTAIN]` — System is guessing (e.g., paraphrase of player intent before confirmation)

**What LOGS Enable:**
- "Show me why the attack missed" → display full attack roll breakdown
- "Why can't I cast this spell?" → show rule citation + failed prerequisite check
- "This narration contradicts earlier events" → trace back to source memory snapshot

**Containment Mechanism:** LOGS are append-only. Past decisions cannot be rewritten, only annotated/corrected.

---

## 3. Critical Axioms

### Axiom 1: No Refusal Originates from SPARK

**Rule:** The SPARK layer never says "I cannot generate this" based on policy, safety, or judgment.

**Rationale:** Refusal at generation creates bureaucratic drift and infects the neutral intelligence core.

**Enforcement:** "Forbidden" is a LENS or BOX decision applied **after** SPARK generates output.

**Example:**
- ❌ **WRONG:** SPARK refuses to generate narration for a gruesome combat scene
- ✅ **CORRECT:** SPARK generates full narration → LENS applies player safety filter → output gated/softened based on table preferences

---

### Axiom 2: Authority Only from BOX

**Rule:** Only BOX can declare mechanical truth ("legal/illegal/permitted/computed").

**Rationale:** Veteran DMs will not tolerate AI hallucinating rulings. All authority must be traceable to RAW rules text or explicit computation.

**Enforcement:** Any user-facing claim of mechanical truth must include BOX provenance or be labeled `[NARRATIVE]`.

**Example:**
- ❌ **WRONG:** SPARK narration includes "your attack misses because of concealment" without BOX computing miss chance
- ✅ **CORRECT:** BOX computes "miss chance 20%, roll 47 → HIT" → SPARK narrates hit → output tagged `[BOX: Hit (concealment miss chance passed)]`

---

### Axiom 3: LENS Adapts Stance, Not Authority

**Rule:** LENS can change tone/pacing/verbosity, but cannot invent mechanical claims.

**Rationale:** Presentation should adapt to user expertise, but authority source must never blur.

**Enforcement:** LENS transformations must preserve provenance. If BOX said it, LENS cannot claim credit. If SPARK generated it, LENS cannot upgrade to authority.

**Example:**
- ❌ **WRONG:** LENS adds "the rules say you provoke an AoO" when BOX didn't compute it
- ✅ **CORRECT:** LENS rephrases BOX output from technical ("AoO provoked: PHB 141") to natural ("moving away provokes an attack of opportunity")

---

### Axiom 4: Trust Repair Requires Legible Errors

**Rule:** Errors are inevitable and acceptable. Illegible errors (cannot diagnose cause) destroy trust.

**Rationale:** Veteran DMs will forgive bugs if they can understand and fix them. They will not forgive black-box mistakes.

**Enforcement:** Every BOX decision must be logged with full provenance. Every user-facing output must be traceable to source layer.

**Example:**
- ❌ **WRONG:** System says "your spell fails" with no explanation or audit trail
- ✅ **CORRECT:** System says "your spell fails [BOX: insufficient caster level, requires CL 5, you have CL 3, PHB 176]" with full logs

---

## 4. Layer Interaction Rules

### Rule 1: SPARK → LENS → User (Narrative Path)

**Flow:** SPARK generates narrative → LENS applies tone/filtering → user sees labeled output

**Provenance:** Output tagged `[NARRATIVE]` or `[DERIVED]`

**Authority:** None. User understands this is flavor, not binding.

**Example:**
```
SPARK: "The orc chieftain bellows in rage, veins bulging."
LENS: (applies terse mode for veteran DM) "Orc enraged."
OUTPUT: [NARRATIVE] "Orc enraged."
```

---

### Rule 2: BOX → LENS → User (Authority Path)

**Flow:** BOX computes ruling → LENS formats for presentation → user sees labeled output

**Provenance:** Output tagged `[BOX]` with rule citation

**Authority:** Binding. User can trust this is RAW-correct.

**Example:**
```
BOX: {attack_roll: 18, AC: 16, result: HIT, breakdown: "1d20=15+BAB3+STR0"}
LENS: (formats for readability)
OUTPUT: [BOX] "Attack hits (roll 18 vs AC 16). Breakdown: d20=15, BAB+3."
```

---

### Rule 3: SPARK ↛ BOX (No Direct Authority Capture)

**Prohibition:** SPARK output can **never** directly mutate BOX state or be treated as authoritative without validation.

**Rationale:** This is the M1 guardrail core. If SPARK could write to memory or assert rulings, determinism collapses.

**Enforcement:** All SPARK→state writes must pass through validation gate or event-sourcing.

**Example:**
- ❌ **WRONG:** SPARK narration says "you take 10 fire damage" → HP reduced without BOX computing damage
- ✅ **CORRECT:** BOX computes damage from event → SPARK narrates result → HP reduced via event-sourced write

---

### Rule 4: BOX Uses SPARK for Flavor Only

**Permitted:** BOX may request SPARK to generate narration for computed events.

**Prohibited:** BOX may not delegate mechanical decisions to SPARK.

**Example:**
- ✅ **CORRECT:** BOX computes "critical hit, 24 damage" → requests SPARK narration → SPARK generates "Your blade cleaves deep into the orc's skull"
- ❌ **WRONG:** BOX asks SPARK "should this character provoke an AoO?" and uses SPARK answer as ruling

---

## 5. Provenance Labeling Standard

**All user-facing output must include provenance metadata.**

### Label Definitions

| Label | Source | Authority | Example |
|-------|--------|-----------|---------|
| `[BOX]` | Deterministic engine computation | **AUTHORITATIVE** | "Attack hits (roll 18 vs AC 16)" |
| `[DERIVED]` | Inferred from BOX state, not computed | **INFORMATIONAL** | "You appear injured (HP < 50%)" |
| `[NARRATIVE]` | SPARK-generated flavor | **ATMOSPHERIC** | "The orc roars in fury" |
| `[UNCERTAIN]` | System guessing/paraphrasing | **TENTATIVE** | "You want to cast *fireball*?" (clarifying intent) |

### Labeling Requirements

**Required for:**
- All mechanical claims (combat results, spell effects, legal rulings)
- All player-facing output (narration, combat log, query results)

**Optional for:**
- Internal system logs (already tagged by layer)
- Debug output (provenance implicit)

**Enforcement:**
- UX layer must visually distinguish BOX truth from NARRATIVE flavor
- LENS cannot strip provenance labels
- Missing labels treated as `[UNCERTAIN]` by default

---

## 6. Non-Negotiables

**These rules are architecturally immutable. Violation constitutes a trust breach.**

### Non-Negotiable 1: SPARK Never Refuses

**Rule:** The generative core never says "I cannot" based on policy.

**Breach Severity:** 🔴 **CRITICAL** — Introduces bureaucratic drift, violates core design

**Detection:** Any code path where SPARK generation is blocked by non-mechanical constraint

**Remediation:** Move constraint to LENS (post-generation gating) or BOX (mechanical illegality)

---

### Non-Negotiable 2: BOX is Sole Mechanical Authority

**Rule:** Only BOX can assert "legal/illegal/permitted" or compute game state.

**Breach Severity:** 🔴 **CRITICAL** — Violates determinism, enables hallucinated rulings

**Detection:** Any mechanical claim not traceable to BOX computation

**Remediation:** Route all mechanical decisions through BOX, label non-BOX output as `[NARRATIVE]`

---

### Non-Negotiable 3: LENS Cannot Invent Authority

**Rule:** Presentation layer can adapt tone but cannot fabricate mechanical truth.

**Breach Severity:** 🟡 **HIGH** — Blurs authority source, erodes trust

**Detection:** LENS code that adds mechanical claims not present in BOX output

**Remediation:** LENS may only transform BOX output format, never content authority

---

### Non-Negotiable 4: Provenance Must Be Preserved

**Rule:** Every user-facing output must be traceable to source layer.

**Breach Severity:** 🟡 **HIGH** — Prevents trust repair, makes errors illegible

**Detection:** Output presented without `[BOX]`/`[DERIVED]`/`[NARRATIVE]`/`[UNCERTAIN]` tag

**Remediation:** Add provenance labeling to all user-facing output pipelines

---

### Non-Negotiable 5: No SPARK → State Writes

**Rule:** Generative output can never directly mutate canonical game state.

**Breach Severity:** 🔴 **CRITICAL** — Violates M1 guardrails, destroys determinism

**Detection:** Any code path where SPARK output is written to WorldState/memory without BOX validation

**Remediation:** Route all state writes through BOX event-sourcing with validation

---

## 7. Enforcement & Governance

### Governance Integration

This doctrine is enforced via:

1. **M1_PR_GATE_CHECKLIST.md CHECK-007**: Spark/Lens/Box Separation (binary pass/fail)
2. **M1_MONITORING_PROTOCOL.md INV-TRUST-001**: Authority Provenance Preserved (continuous monitoring)
3. **Agent projection constraints**: Each agent receives one-sentence binding rule from this doctrine

### Certification Requirements

All M1 PRs must explicitly attest:
- ✅ No SPARK refusal (generation always succeeds, gating is post-generation)
- ✅ No SPARK authority (mechanical claims sourced from BOX only)
- ✅ No LENS authority invention (presentation preserves BOX provenance)
- ✅ Provenance labeling present (all user-facing output tagged)
- ✅ No SPARK→state writes (all mutations via BOX event-sourcing)

### Breach Response

**Detection:** Automated (CHECK-007) + manual code review

**Severity Tiers:**
- 🔴 **CRITICAL**: SPARK refusal, BOX authority bypass, SPARK→state writes → **REJECT PR immediately**
- 🟡 **HIGH**: LENS authority invention, missing provenance → **REQUEST CHANGES, must fix before merge**
- 🟢 **LOW**: Inconsistent labeling, unclear provenance → **APPROVE with remediation note**

**Escalation:** All CRITICAL breaches reported to PM + Agent D within 24 hours

---

## 8. Agent-Specific Projections

**These are the one-sentence constraints each agent must enforce from this doctrine.**

### Agent A (Implementation/Narration)

**Constraint:** "SPARK output is never authoritative; only BOX can declare illegal; LENS can adapt tone; enforce provenance tags on all user-facing output."

**Enforcement:** All narration generation must be labeled `[NARRATIVE]`, all mechanical claims must source from BOX with `[BOX]` tag.

---

### Agent B (Schema/Validation)

**Constraint:** "Any schema or memory pathway that allows SPARK→state writes or authority claims without BOX validation is architecturally invalid."

**Enforcement:** Schema reviews must verify all state mutations are event-sourced through BOX, no direct LLM→memory writes.

---

### Agent C (UX)

**Constraint:** "UX must visually distinguish BOX truth vs DERIVED vs NARRATIVE; never let narrative feel like authoritative rulings."

**Enforcement:** UI must render provenance labels distinctly (e.g., bold for `[BOX]`, italics for `[NARRATIVE]`, grey for `[DERIVED]`).

---

### Agent D (Governance)

**Constraint:** "Certification must explicitly attest Spark/Lens/Box separation; CHECK-007 required for every M1 PR."

**Enforcement:** All M1 PR reviews must include CHECK-007 verification; any separation violation is immediate rejection.

---

## 9. Trust Repair Axiom

**Axiom:** Veteran DM trust is fragile. Therefore, the system must **never assert false authority** and must always preserve provenance so trust can be repaired.

**Implications:**

1. **Errors Are Acceptable**: Bugs happen. DMs understand this.
2. **Illegible Errors Are Not**: If DM cannot diagnose why system made a mistake, trust is destroyed.
3. **False Authority Is Unforgivable**: If system claims RAW authority for a hallucinated ruling, DM will abandon system.

**Design Principle:** When in doubt, under-claim authority and over-label provenance.

**Example:**
- ❌ **TRUST VIOLATION:** "You cannot take this action [no explanation, no rule citation, no provenance]"
- ✅ **TRUST PRESERVING:** "This action may provoke an AoO [DERIVED: you are moving out of threatened square] — confirm? [BOX will compute if confirmed]"

---

## 10. Doctrine Lineage

**Origin:** PM (Thunder) + Agent D (Research Orchestrator) design conversation (2026-02-10)

**Basis:** Convergence on four-layer containment model to prevent false authority, bureaucratic drift, and illegible errors.

**Status:** **BINDING** as of 2026-02-10

**Review Cycle:** Doctrine is immutable for M1-M3. PM may update for M4+ with explicit revision record.

**Supersedes:** No prior doctrine (this is first canonical statement of Spark/Lens/Box model)

---

## 11. Compliance Statement

**This doctrine is non-negotiable.**

- ✅ All agents must enforce their projected constraints
- ✅ All PRs must pass CHECK-007 (Spark/Lens/Box Separation)
- ✅ All monitoring must verify INV-TRUST-001 (Authority Provenance Preserved)
- ✅ All UX must render provenance labels distinctly

**Violation = Architectural Breach → Immediate remediation required**

---

**END OF SPARK/LENS/BOX DOCTRINE**

**Date:** 2026-02-10
**Agent:** Agent D (Research Orchestrator)
**Authority:** PM (Thunder) + Agent D Stop Authority
**Status:** ✅ **BINDING** (conceptual constitution)
**Signature:** Agent D (Research Orchestrator) — 2026-02-10

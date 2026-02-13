# PO Session: Policy Governance Doctrine + Lens-Spark Research Sprint

**Agent:** Opus
**Source:** PO design session (2026-02-12)
**Date:** 2026-02-12
**Status:** Complete — Requires PM Review

---

## What This Is

Thunder (PO) conducted a multi-hour design session covering two connected topics:

1. **Lens-Spark Context Orchestration Research Sprint** — formalized as RQ-LENS-SPARK-001
2. **House Policy Governance Doctrine** — a new architectural constraint on how Box handles RAW silences

Both are now documented. The PM needs to review, integrate into project governance, and determine sequencing.

---

## Deliverable 1: RQ-LENS-SPARK-001 (Context Orchestration Sprint)

**File:** `docs/specs/RQ-LENS-SPARK-001_CONTEXT_ORCHESTRATION_SPRINT.md`

**Decision:** Feature development is frozen. The Lens-Spark protocol must be hardened before any asset integration (TTS, image, music beyond current Kokoro wiring).

**Core risk identified:** Lens cannot currently guarantee multi-turn coherence. The system will appear to work for 20 turns and silently unravel over 200. Failures will be attributed to assets when the real cause is context orchestration.

**Five deliverables defined:**

| # | Deliverable | Summary |
|---|-------------|---------|
| 1 | **PromptPack v1 Wire Format** | Frozen dataclass replacing distributed prompt assembly (DMPersona + ContextAssembler + GuardedNarrationService) with a single versioned, sectioned, deterministic prompt object. TaskType enum (4 narration types + 2 reserved). Per-task section budgets. Truncation invariants: sections 1-3 never dropped. |
| 2 | **Memory Retrieval Policy** | Deterministic heuristic ranking (recency 0.5, actor-match 0.3, severity 0.2). Hard caps: 3 recent narrations, 5 session summaries. RetrievedItem provenance dataclass. No RAG — not needed for v1. |
| 3 | **Summarization Stability** | Template-based SessionSegmentSummary every 10 turns. Drift detection via entity-state consistency checks. Rebuild-from-sources on drift. No LLM summaries in v1. |
| 4 | **Contradiction Handling** | Three-class taxonomy: Class A (entity state — critical), Class B (outcome — high), Class C (continuity — medium). Keyword dictionaries for defeat/hit/miss/severity detection. Response policy: retry with stricter prompt, then template fallback. Runs post-GrammarShield, pre-output. |
| 5 | **Evaluation Harness** | 4 scenarios (50-turn combat, 20-turn transitions, 30-turn mixed, 100-turn pressure). 8 metrics with targets. Model-swap regression comparison. |

**Exit gate:** All scenarios pass with <1% contradiction rate, 0% mechanics leak, 100% budget stability, 100% determinism.

**Explicit scope exclusions:** No expand-on-demand feedback loop, no campaign authoring, no RAG, no LLM summaries, no semantic contradiction detection, no NPC dialogue generation, no multi-session persistence, no voice/image/music integration.

**Implementation sequence:** Phase 1 (PromptPack + ContradictionChecker) → Phase 2 (Retrieval + Summarization) → Phase 3 (Evaluation Harness).

**Prerequisite WOs:** WO-032, WO-039, WO-040, WO-041, WO-045, WO-046 (all INTEGRATED).

---

## Deliverable 2: House Policy Governance Doctrine

**This is a new architectural constraint.** It governs how Box handles situations where RAW is silent — the "of course a ladder doesn't fit in a backpack" class of problems.

### The Hard Lock (Non-Negotiable)

**There is no opaque DM. The system does not exercise discretion. Ever.**

Every outcome that affects game state traces to exactly two sources:
1. **Rules As Written** — the 3.5e SRD/PHB/DMG/MM corpus, encoded as deterministic resolvers
2. **House Policy** — pre-declared, bounded, template-instantiated, logged to an immutable ledger, player-inspectable

There is no third source.

### What the system is forbidden from doing:

- Creating new categories of judgment at runtime
- Weighing competing interpretations silently
- Applying "common sense" as a computational input
- Inferring that something "should" be disallowed if no rule or policy prohibits it
- Generating house policy outside a pre-declared template family
- Any form of hidden, uninspectable authority over game state

### What the system is allowed to do:

- **Instantiate specific policies within pre-declared template families** at runtime
- This is parameterization, not discretion
- The family defines inputs, outputs, and bounds
- The system picks a value within those bounds, logs it, freezes it
- Replay-stable, deterministic, auditable

### The Two-Loop Model

**Loop 1 — Runtime (sacred, frozen):**
- Only RAW + existing trigger families govern
- Only instance instantiation within families (never family creation)
- If no family covers a situation: RAW applies, or FAIL_CLOSED
- No learning, no invention, no approximation

**Loop 2 — Offline Evolution (between versions):**
- Analyze FAIL_CLOSED logs from sessions
- Identify patterns that justify new trigger families
- Design bounded templates (inputs, outputs, stop conditions)
- Ship in a new versioned release
- Rule of Three: new family only if pattern appears in multiple independent sessions, can't be expressed as existing family instance, and bounded template is definable

### Initial Trigger Family Candidates (90-95% coverage)

These are the RAW silence categories that cause known table friction in 3.5e:

| # | Trigger Family | Description |
|---|----------------|-------------|
| 1 | CONTAINMENT_PLAUSIBILITY | Does this item physically fit in this container |
| 2 | RETRIEVAL_ACCESSIBILITY | What action cost to access a stored item |
| 3 | CONCEALMENT_PLAUSIBILITY | Can this item be hidden on a person |
| 4 | ENVIRONMENTAL_INTERACTION | Can this tool/weapon affect this object (hardness/material) |
| 5 | SPATIAL_CLEARANCE | Can this creature/item fit in this space |
| 6 | STACKING_NESTING_LIMITS | Bags inside bags, containers inside containers |
| 7 | FRAGILITY_BREAKAGE | Does rough handling damage this item |
| 8 | READINESS_STATE | Is this item "at hand" vs "stowed" and what that costs |
| 9 | MOUNT_COMPATIBILITY | Can this creature serve as mount for this rider |

Each requires a template spec with: trigger condition, allowed inputs, allowed outputs, bounds, stop conditions, ledger format.

### FAIL_CLOSED Logging

When Box encounters a situation outside all known trigger families:
- Emit structured `FAIL_CLOSED` record
- Contents: action attempted, trigger class it would need, available data, missing data, RAW-only outcome
- These become the evidence for Loop 2 (offline family creation)
- The session continues — either RAW governs or the action is denied

---

## PM Action Items

1. **Review RQ-LENS-SPARK-001** — Confirm sequencing against current project state. All prerequisites are INTEGRATED. This is the next body of work.

2. **Review House Policy Governance Doctrine** — This is a new foundational constraint. It needs to be codified in project governance (MANIFESTO.md addition or standalone doctrine document). It affects Box architecture and future feature design.

3. **Decide on artifact priority for House Policy:**
   - Template Family Registry (formal spec for the 9 trigger families)
   - FAIL_CLOSED Logging Schema (structured record format for unresolvable situations)
   - Both can be a single governance spec

4. **Sequence relative to RQ-LENS-SPARK-001** — The Lens-Spark sprint and the House Policy work are independent tracks. Lens-Spark is narration infrastructure. House Policy is Box governance. They don't block each other but both represent architectural hardening before feature expansion.

5. **PSD update** — Neither deliverable changes test counts or locked systems yet. They are specs/doctrine, not implementation. PSD update deferred until implementation WOs are dispatched and integrated.

6. **Review three new research briefs** — PO authorized the following research items during the session. All three are drafted and ready for PM review:

   | RQ ID | File | Summary |
   |-------|------|---------|
   | RQ-BOX-002 | `docs/specs/RQ-BOX-002_RAW_SILENCE_CATALOG.md` | Systematic audit of 3.5e RAW silences. Maps each silence to a trigger family. Must complete before Template Family Registry is finalized. |
   | RQ-BOX-003 | `docs/specs/RQ-BOX-003_OBJECT_IDENTITY_MODEL.md` | Minimal object identity model (ObjectState schema, integrity state transitions, spell interaction rules). Prerequisite for mending/sunder/container trigger families. |
   | RQ-LENS-002 | `docs/specs/RQ-LENS-002_CONTRADICTION_SURFACE_MAPPING.md` | Empirical Spark output analysis — run 300+ narrations against scripted NarrativeBriefs to measure actual contradiction rates and validate keyword dictionaries before building ContradictionChecker. |

   **Sequencing recommendation:**
   - RQ-BOX-002 (RAW Silence Catalog) is highest leverage — directly produces Template Family Registry input
   - RQ-BOX-003 (Object Identity) is most architecturally significant — affects Box data model
   - RQ-LENS-002 (Contradiction Surface) sequences after Spark model is available for empirical testing
   - RQ-BOX-002 and RQ-BOX-003 can run in parallel; RQ-LENS-002 is independent of both

7. **MANIFESTO.md updated** — PO added the No-Opaque-DM Doctrine directly to the project manifesto (lines 174-176). This is now canonical project doctrine, not just a session decision.

8. **Review community RAW argument survey** — PO directed a community research sprint mining EN World, Giant in the Playground, and other 3.5e forums for RAW arguments and edge cases. Results are documented in:

   **File:** `docs/research/RQ-BOX-002-A_COMMUNITY_RAW_ARGUMENT_SURVEY.md`

   **Key findings:**
   - **SIL-007:** PHB vs DMG directly contradict on magic item enhancement bonus to hardness/HP (+2/+10 vs +1/+1). No errata. Affects every magic item. System must pick one and log as House Policy.
   - **SIL-008:** Armor is excluded from the DMG enhancement bonus table. +5 full plate has base 10 hardness/20 HP and is trivially destroyed.
   - **SIL-009:** Whether grappled creatures threaten adjacent squares is ambiguous. Box resolver must pick one interpretation.
   - **SIL-010:** "Ruined" (object at 0 HP) has no physical definition. Cross-references RQ-BOX-003 Object Identity.
   - **Polymorph subsystem** is so broken that WotC abandoned it. When polymorph enters scope, it will need its own dedicated research question.
   - **Design principles reinforced:** RAW is not physics, contradictions require a design-time choice (not runtime judgment), "broken" interactions are still RAW (No-Opaque-DM applies), scope discipline protects against complexity explosion.

   The 4 new silence entries (SIL-007 through SIL-010) have been added to the RQ-BOX-002 catalog.

---

## Key Quotes from PO (for doctrine precision)

On opaque DM:
> "There is no room for opaque DM. That is above and beyond anything that we want to happen. I cannot state any harder how that should never, never, never happen."

On house policy scope:
> "Any kind of change that it makes wouldn't necessarily break the whole integrity of the system — it would just be polishing the surface that's already made."

On discovery vs invention:
> "A lot of these house rules that will need to be implemented haven't been discovered yet and the template hasn't been made for that yet because they're still using the rules as written."

Resolution: The system discovers **instances** through play (safe). It never discovers **families** through play (forbidden). Families are created offline by human research, justified by session evidence.

---

## Appendix: Edge Cases Discussed (PO Session Notes)

### A. Structural Load-Bearing (Trigger Family Candidate)

**Scenario:** Player uses a wooden pole to span a 10-foot gap instead of making a Jump check. Can a 400-lb ogre barbarian walk across it? Can a 30-lb halfling?

**RAW provides:** Material hardness (wood=5, iron=10), object HP by material and thickness (1-inch wood = 10 HP), Break DCs, sunder rules. (PHB p.165-166, DMG p.61)

**RAW does NOT provide:** Load-bearing capacity as a function of HP, whether sustained weight constitutes damage, how span length affects integrity.

**Classification:** House Policy trigger family — likely **STRUCTURAL_LOAD_BEARING** (new candidate #10) or folds into ENVIRONMENTAL_INTERACTION (#4). The data exists in RAW (material HP, character weight). The missing piece is a weight-to-stress conversion formula — a bounded template, not a judgment call.

**Template shape:** Inputs = material HP, object dimensions, span distance, applied weight. Outputs = ALLOW / ALLOW_WITH_CHECK(Balance DC) / DENY(object breaks) / PARTIAL(HP reduced). Bounds = cannot invent materials, cannot override RAW hardness/HP.

### B. Mending Spell — Object Identity (RAW Resolution, NOT House Policy)

**Scenario:** Can the *mending* cantrip join two completely severed rope halves back together? PO position: no — mending repairs damage to one object, it does not merge two separate objects into one.

**Analysis:** This is NOT a House Policy case. It resolves under RAW once object identity is properly modeled:

- **Partially cut rope** (still one object with damage) → valid mending target, repaired
- **Fully severed rope** (two separate objects) → invalid target, spell fails
- **Two unrelated rope ends placed adjacent** → invalid target, spell fails

If mending could merge objects, it would replace *make whole*, eliminate crafting, and allow infinite material assembly. RAW clearly does not intend this.

**Architectural implication:** Box needs an **object identity model** — when an item is damaged it remains one object with reduced HP; when it's destroyed/severed completely it becomes two objects. Spell target validation must check object identity, not physical proximity. This is a data model requirement, not a policy template.

**PM note:** Object identity tracking is a prerequisite for correct spell targeting, sunder resolution, and several trigger families (FRAGILITY_BREAKAGE, STRUCTURAL_LOAD_BEARING). Consider scoping as a research item.

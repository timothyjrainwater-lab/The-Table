# AD-006: House Policy Governance Doctrine

**Status:** RATIFIED
**Date:** 2026-02-12
**Authority:** PM (Opus) + PO (Thunder)
**Source:** PO design session — Policy Governance Doctrine
**Depends on:** AD-001 (Authority Resolution), AD-003 (Self-Sufficiency), AD-005 (Physical Affordance)

---

## The Hard Lock (Non-Negotiable)

**There is no opaque DM. The system does not exercise discretion. Ever.**

Every outcome that affects game state traces to exactly two sources:

1. **Rules As Written (RAW)** — the 3.5e SRD/PHB/DMG/MM corpus, encoded as deterministic resolvers
2. **House Policy** — pre-declared, bounded, template-instantiated, logged to an immutable ledger, player-inspectable

There is no third source. No inference, no "common sense," no silent adjudication.

> "There is no room for opaque DM. That is above and beyond anything that we want to happen. I cannot state any harder how that should never, never, never happen." — PO

---

## What the System Is Forbidden From Doing

1. Creating new categories of judgment at runtime
2. Weighing competing interpretations silently
3. Applying "common sense" as a computational input
4. Inferring that something "should" be disallowed if no rule or policy prohibits it
5. Generating house policy outside a pre-declared template family
6. Any form of hidden, uninspectable authority over game state

---

## What the System Is Allowed To Do

**Instantiate specific policies within pre-declared template families** at runtime. This is parameterization, not discretion:

- The family defines inputs, outputs, bounds, and forbidden effects
- The system picks a value within those bounds, logs it, freezes it
- The result is replay-stable, deterministic, auditable

---

## The Family / Instance Distinction

This is the core governance principle:

- A **Template Family** defines a *category* of House Policy judgment (e.g., "does this item fit in this container"). Families are finite and explicitly enumerated in the Template Family Registry.
- An **Instance** is a specific policy decision within a family (e.g., "a 10-foot pole does not fit in a backpack"). Instances are parameterized from family templates and may be created at runtime.

**The system discovers instances through play (safe). It never discovers families through play (forbidden).** Families are created offline by human research, justified by session evidence.

---

## The Two-Loop Model

### Loop 1 — Runtime (Sacred, Frozen)

- Only RAW + existing trigger families govern
- Only instance instantiation within families (never family creation)
- If no family covers a situation: RAW applies, or FAIL_CLOSED
- No learning, no invention, no approximation

### Loop 2 — Offline Evolution (Between Versions)

- Analyze FAIL_CLOSED logs from sessions
- Identify patterns that justify new trigger families
- Design bounded templates (inputs, outputs, stop conditions, forbidden effects)
- Ship in a new versioned release

**The Template Family Registry is closed during runtime, but open across engine versions.** This preserves long-term adaptability without reopening runtime discretion. Future contributors must not interpret "finite families" as "permanently fixed" — adaptation happens between releases, not inside sessions.

### Loop 2 Authority Chain

- **PO approves** new families (sole authority for family creation decisions)
- **PM executes** family formalization (template spec, registry entry, implementation WO)
- **The system never proposes new families.** FAIL_CLOSED logs provide evidence; humans provide judgment.

### Rule of Three (Family Creation Gate)

A new trigger family may only be created if ALL of:

1. The pattern appears in **multiple independent sessions** (not a one-off edge case)
2. It **cannot be expressed** as an instance of an existing family
3. A **bounded template is definable** (finite inputs, finite outputs, explicit stop conditions, explicit forbidden effects)

---

## Template Family Registry

### Registry Rules

1. Each family has a unique `FAMILY_ID` (e.g., `CONTAINMENT_PLAUSIBILITY`)
2. Each family spec must include:
   - **Trigger condition:** When does this family activate?
   - **Allowed inputs:** What data may the template consume?
   - **Allowed outputs:** What decisions may it produce?
   - **Forbidden effects:** What is this family explicitly NOT allowed to do?
   - **Value bounds:** What are the min/max/enum constraints on outputs?
   - **Stop conditions:** When does instantiation halt?
   - **Ledger format:** How is the instantiation logged?
3. The registry is versioned. Adding or removing a family increments the registry version.
4. Runtime code may only instantiate families present in the registry at session start.

### Initial Registry (v1.0)

| # | Family ID | Status | Description | Implementing WO |
|---|-----------|--------|-------------|-----------------|
| 1 | CONTAINMENT_PLAUSIBILITY | **GREEN** (shipped) | Does this item physically fit in this container | WO-055 (AD-005 L2) |
| 2 | RETRIEVAL_ACCESSIBILITY | **GREEN** (shipped) | What action cost to access a stored item | WO-055 (AD-005 L2) |
| 3 | CONCEALMENT_PLAUSIBILITY | **YELLOW** (partial) | Can this item be hidden on a person | — |
| 4 | ENVIRONMENTAL_INTERACTION | **YELLOW** (partial) | Can this tool/weapon affect this object | WO-051B (PDL hardness/HP) |
| 5 | SPATIAL_CLEARANCE | **RED** (deferred) | Can this creature/item fit in this space | — |
| 6 | STACKING_NESTING_LIMITS | **RED** (deferred) | Containers inside containers | — |
| 7 | FRAGILITY_BREAKAGE | **YELLOW** (partial) | Does rough handling damage this item | WO-051B (PDL hardness/HP) |
| 8 | READINESS_STATE | **GREEN** (shipped) | Is this item "at hand" vs "stowed" and what that costs | WO-055 (AD-005 L2) |
| 9 | MOUNT_COMPATIBILITY | **RED** (deferred) | Can this creature serve as mount for this rider | — |

RED families are deferred until FAIL_CLOSED logging provides empirical evidence of need. YELLOW families have partial infrastructure but need complete template specs.

---

## Template Family Spec Format

Every family in the registry must conform to this format:

```
FAMILY_ID: <unique identifier>
VERSION: <semver>
STATUS: GREEN | YELLOW | RED

TRIGGER CONDITION:
  <When does this family activate?>

ALLOWED INPUTS:
  <What data may the template consume? Exhaustive list.>

ALLOWED OUTPUTS:
  <What decisions may it produce? Exhaustive list.>

FORBIDDEN EFFECTS:
  - Cannot alter creature stats (HP, AC, ability scores, saves, BAB)
  - Cannot invent new damage types
  - Cannot modify RAW success/failure states
  - Cannot chain into other families implicitly
  - Cannot derive outputs from real-world physics (all outputs must map to
    existing D&D mechanical constructs: DCs, damage, conditions, allow/deny)
  - <Family-specific prohibitions>

VALUE BOUNDS:
  <Min/max/enum constraints on every output field>

STOP CONDITIONS:
  <When does instantiation halt? What prevents runaway instantiation?>

LEDGER FORMAT:
  <Structured record format for audit trail>

PROVENANCE: HOUSE_POLICY
```

The **Forbidden Effects** section is mandatory for every family. It defines the negative space — what the family is explicitly not allowed to do — and provides auditors an inspection surface independent of positive behavior.

---

## FAIL_CLOSED Protocol

### When It Triggers

Box encounters a situation that:
1. Is not covered by RAW, AND
2. Does not fall within any registered trigger family

### What Happens (System Behavior)

1. Emit a structured `FAIL_CLOSED` record to the session log
2. Apply RAW-only resolution if any RAW rule is applicable
3. If no RAW rule applies: deny the action with an explainable outcome
4. Continue the session — never stall, never crash

### What the Player Experiences

FAIL_CLOSED always produces a **deterministic, explainable outcome**, not a silent stall or cryptic error. The system must communicate:

- That the attempted action falls outside the system's current rule coverage
- That RAW provides no ruling for this specific situation
- What the system did instead (RAW-only fallback or action denial)
- That this gap has been logged for future system improvement

The system must **never degrade into narration-only resolution** during FAIL_CLOSED. If Box cannot resolve the mechanics, the action is denied or resolved conservatively — Spark does not fill the gap.

### FAIL_CLOSED Record Format

```
FailClosedRecord {
    record_id: str              # Deterministic (turn_id + event_cursor)
    session_id: str             # Session identifier
    turn_id: int                # Turn when encountered
    event_cursor: int           # Position in event stream

    # What was attempted
    action_attempted: str       # Natural language description
    actor_id: str               # Entity attempting the action
    target_ref: str             # Target object/entity/location

    # What family would be needed
    nearest_family: str?        # Closest existing family, if any
    hypothetical_family: str    # What kind of family this would need
    missing_template: str       # What template shape would resolve this

    # Available vs missing data
    available_data: Dict        # Data the system had
    missing_data: List[str]     # Data the system would need

    # Resolution applied
    raw_fallback: str?          # RAW rule applied, if any (with citation)
    resolution: "RAW_ONLY" | "ACTION_DENIED"
    player_explanation: str     # What the player was told

    # Loop 2 metadata
    severity: "LOW" | "MEDIUM" | "HIGH"  # How much this affected gameplay
    frequency_hint: str         # "first_occurrence" | "recurring"
}
```

### FAIL_CLOSED Evidence Pipeline (Loop 2)

1. Records accumulate in session logs
2. Between versions, PO reviews aggregated FAIL_CLOSED records
3. Patterns meeting the Rule of Three trigger family design
4. PM formalizes the template spec
5. New family ships in next versioned release

---

## Relationship to Existing Architectural Decisions

### AD-001 (Authority Resolution Protocol)

AD-006 governs the **meta-level** that AD-001 operates within. AD-001 defines how individual facts are resolved (NeedFact → WorldPatch). AD-006 defines what *categories* of facts may be resolved through House Policy.

**Source tier mapping:**
- AD-001 `CANONICAL` → AD-006 **RAW** (rules as written, deterministic resolvers)
- AD-001 `POLICY_DEFAULT` → AD-006 **House Policy** (template-instantiated, logged, inspectable)
- AD-001 `PLAYER` → Legitimate authority input (player/DM choice within bounded options)
- AD-001 `SPARK_DRAFT` → Remains forbidden for mechanical facts (unchanged)

This mapping is additive — AD-006 does not change AD-001's resolution protocol. It constrains what kinds of POLICY_DEFAULT entries may exist.

### AD-003 (Self-Sufficiency Resolution Policy)

AD-003's Policy Default Library is the *implementation* of AD-006's House Policy concept. The PDL's object classes are instances within trigger families. AD-006 adds the governance layer: what categories of defaults are permitted, how new categories are created, and what happens when no category applies.

### AD-005 (Physical Affordance Policy)

AD-005's four-layer architecture maps directly to trigger families:
- Layer 1 (Encumbrance) → RAW, not House Policy
- Layer 2 (Container Policies) → Families #1 CONTAINMENT, #2 RETRIEVAL, #8 READINESS
- Layer 3 (Gear Affordances) → DERIVED provenance (Lens→Spark, not House Policy)
- Layer 4 (Physical Complications) → Future families, deferred

---

## Edge Cases (From PO Design Session)

### A. Structural Load-Bearing

**Scenario:** Wooden pole spanning a 10-foot gap. Can a 400-lb ogre cross it?

**Classification:** Candidate family #10 (STRUCTURAL_LOAD_BEARING) or subsumable under #4 (ENVIRONMENTAL_INTERACTION). RAW provides material HP, hardness, character weight. Missing piece: weight-to-stress conversion formula.

**Template shape:** Inputs = material HP, dimensions, span distance, applied weight. Outputs = ALLOW / ALLOW_WITH_CHECK(Balance DC) / DENY(object breaks) / PARTIAL(HP reduced). Bounds = cannot invent materials, cannot override RAW hardness/HP.

**Status:** Deferred. Requires FAIL_CLOSED evidence before family creation.

### B. Mending Spell — Object Identity

**Scenario:** Can *mending* join two fully severed rope halves?

**Classification:** NOT a House Policy case. Resolves under RAW via object identity:
- Partially cut rope (one object with damage) → valid mending target
- Fully severed rope (two separate objects) → invalid target, spell fails

**Architectural implication:** Box needs an object identity model (damaged object vs. destroyed/severed into two objects). This is a data model prerequisite, not a trigger family. Noted as a research item for spell targeting and sunder resolution.

---

*This decision was prompted by PO design session establishing the No-Opaque-DM doctrine. It formalizes the family/instance distinction, the Two-Loop Model, and the FAIL_CLOSED protocol as binding governance. The Template Family Registry is closed at runtime, open across versions — the system adapts between releases, never during play.*

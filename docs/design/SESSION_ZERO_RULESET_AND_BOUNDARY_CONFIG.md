# Session Zero Ruleset & Boundary Configuration
## Formalizing Table Authority, Variant Rules, and Creative Scope

**Document ID:** SZ-RBC-001
**Version:** 1.0
**Status:** ADOPTED
**Scope:** Campaign Initialization · LLM Behavior · Engine Constraints

**Project:** AIDM — Deterministic D&D 3.5e Engine + Local Open-Source LLM
**Document Type:** Core Design Specification

---

## 1. PURPOSE

This document defines **Session Zero** as a **formal, machine-readable contract**
that governs:

- Which rules are in effect
- Which variants/homebrew are enabled
- How alignment behaves
- How deities, classes, and doctrines function
- What boundaries exist for the campaign
- How the LLM is expected to behave narratively

This replaces informal "table agreements" with **explicit, auditable configuration**
while preserving creative freedom.

---

## 2. WHY SESSION ZERO MUST BE FIRST-CLASS

In human tabletop play:
- Session Zero sets expectations
- Rules arguments are avoided later
- Boundaries are established socially

In an AI-mediated tabletop:
- These expectations **must be explicit**
- The system cannot rely on vibes or assumptions
- Every refusal or allowance must trace back to table-defined rules

Therefore:
> **Nothing about tone, morality, or rules should be implied.
> Everything must be declared.**

---

## 3. SESSION ZERO CONFIG AS A CONTRACT

Session Zero produces a **Ruleset Manifest**, which is:

- Versioned
- Immutable once play begins (unless explicitly amended)
- Referenced by every event log
- Queryable by players at any time

Example:
```yaml
config_schema_version: 1
ruleset_id: frontier_ruin_campaign_v1
base_rules: DND_3.5_RAW
```

---

## 4. CORE CONFIGURATION SECTIONS

### 4.1 Ruleset Foundation

Defines the baseline rules:

```yaml
base_ruleset: DND_3.5_RAW
errata_version: official | none | custom
optional_rules_enabled: [list]
```

This answers: "What rules are we actually using?"

---

### 4.2 Variant & Homebrew Rules

Each variant must be explicitly declared:

```yaml
variant_rules:
  - id: variant_paladin_doctrine
    version: 1.0
    description: Paladins derive power from deity doctrine, not LG alignment
```

Rules must specify:
- What RAW rule they override
- Scope of impact
- Whether they affect mechanics or flavor only

**Undeclared homebrew does not exist.**

---

### 4.3 Alignment System Configuration

Alignment behavior must be chosen, not assumed.

Options include:

```yaml
alignment_tracking: strict | inferred | narrative-only
alignment_visibility: hidden | summary | full-ledger
alignment_enforcement:
  class_codes: on/off
  divine_reactions: on/off
  spell_interactions: on/off
```

This allows:
- Evil campaigns
- Moral ambiguity campaigns
- Alignment-free settings

Without engine confusion.

---

### 4.4 Deities, Doctrine, and Divine Power

Defines how gods function mechanically.

Configurable elements:
- Deity alignment expectations
- Doctrine constraints (codes of behavior)
- Consequences of violation (loss of powers, omens, quests, etc.)
- Whether exceptions are allowed

Example:
```yaml
deity_doctrine:
  allow_alignment_variance: true
  enforcement_model: doctrine_based
```

This is what makes concepts like CE deity champions mechanically coherent.

---

### 4.5 Class Restriction Policy

Defines whether RAW class restrictions apply:
- Alignment locks (on/off/variant)
- Multiclass penalties
- Ex-class behavior

This prevents the system from "refusing" character concepts unexpectedly.

---

### 4.6 Narrative Tone & World Assumptions

This section guides LLM narration, not mechanics.

Examples:
- Grimdark / heroic / mythic
- High magic / low magic
- Lethality expectations
- Moral absolutism vs ambiguity

This is tone, not censorship.

---

### 4.7 Creative Boundaries (Table-Defined)

Important distinction:
> These are table boundaries, not model ethics.

Examples:
- Themes to avoid
- Fade-to-black preferences
- Content intensity

These affect narration style, not mechanical outcomes.

---

### 4.8 Preparation Depth

Defines how thoroughly the DM agent prepares before play begins:

```yaml
preparation_depth: light | standard | deep
```

- **light**: Minimal prep, faster start, lighter immersion assets
- **standard**: Balanced preparation appropriate for most campaigns
- **deep**: Thorough preparation, longer wait, richer asset generation

Depth may also be inferred from campaign type and tone if not specified.

---

## 5. HOW THE LLM MUST USE SESSION ZERO

### 5.1 LLM Obedience Hierarchy

When narrating or interpreting intent, the LLM must defer in this order:

1. Deterministic engine output
2. Session Zero ruleset config
3. Campaign state & history
4. Player intent
5. Narrative style preferences

The LLM must never override Session Zero.

---

### 5.2 No Ideological Refusals

If an action is:
- Allowed by ruleset
- Allowed by session config
- Physically possible

Then the LLM must:
- Accept it
- Clarify intent if needed
- Resolve consequences

Refusal is allowed only if the ruleset forbids it, not because of tone.

---

## 6. AMENDMENTS & EVOLUTION

Session Zero may be amended only if:
- The table explicitly agrees
- A new ruleset version is created
- The change is logged

Past events remain bound to the old ruleset.

Amendment history is preserved in the campaign record.

---

## 7. AUDITABILITY & TRANSPARENCY

Players may ask at any time:
- "What rules are we using?"
- "Why did this work/fail?"
- "Is this because of a variant rule?"

The system must be able to answer by pointing to:
- Session Zero config
- Ruleset manifest
- Event logs

---

## 8. DEFAULT BEHAVIOR (FAIL-SAFE)

If a configuration key is missing:
- The system uses **RAW 3.5e behavior** as the default
- Missing optional features default to **disabled**
- The system logs a warning for missing expected keys

No silent improvisation is permitted.

---

## 9. FAILURE MODES THIS PREVENTS

Without this document:
- The LLM improvises boundaries
- Players feel arbitrarily blocked
- Homebrew causes silent inconsistencies
- Trust erodes

With this document:
- Authority is explicit
- Creativity is protected
- Disputes are minimized

---

## 10. SUMMARY OF NON-NEGOTIABLES

1. Session Zero must be explicit and machine-readable
2. Homebrew must be declared, not inferred
3. Alignment behavior must be chosen, not assumed
4. LLM narration must obey table-defined boundaries
5. No ideological refusals for valid in-fiction play
6. Missing config defaults to RAW, not improvisation

---

## 11. NEXT DEPENDENT DOCUMENTS

This config feeds directly into:
- `LLM_ENGINE_BOUNDARY_CONTRACT.md`
- `CHARACTER_SHEET_UI_CONTRACT.md`
- `ALIGNMENT_LEDGER_SCHEMA.md`

---

## END OF SESSION ZERO RULESET & BOUNDARY CONFIG

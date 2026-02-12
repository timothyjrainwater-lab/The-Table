# AD-001: Authority Resolution Protocol (NeedFact / WorldPatch)

**Status:** APPROVED
**Date:** 2026-02-12
**Authority:** PM (Opus) + PO (Thunder)
**Source:** GPT architectural review during research synthesis phase

---

## Decision

**Spark MUST NEVER supply facts that affect mechanical game state.**

When Box encounters a missing fact required for mechanical resolution (cover calculation, break DC, concealment, distance, lighting level, object properties), the system MUST halt and resolve through an authority chain — not by asking Spark to invent the answer.

This is a binding extension of the existing invariant: "No LLM calls in the runtime combat loop."

---

## The Problem

RQ-SPARK-001 Sub-C proposes a "JIT Fact Acquisition" pattern where Spark can fill in missing scene details (e.g., table dimensions, wall thickness). If those details affect mechanical outcomes (cover AC bonus, concealment miss chance, break DCs), then Spark is effectively **inside the combat loop** — deciding whether attacks hit or miss through indirect fact injection.

Even if Spark's answer is "plausible," it creates:
- Soft nondeterminism (different Spark runs → different facts → different combat outcomes)
- Perceived cheating ("the DM made up that table height to block my shot")
- Impossible-to-debug edge cases (replay produces different facts → different state)
- Loss of trust in Box authority

---

## Two Kinds of Unknown

### 1. Authoritative Unknowns (Mechanics-Relevant)

Examples:
- Table height / dimensions / material (affects cover)
- Wall thickness (affects break DC)
- Lighting level (affects concealment miss chance)
- Whether a door is locked (affects interaction options)
- Exact object positions when needed for geometry
- NPC stat blocks or ability scores

**These CANNOT be invented by Spark.** They must be resolved by an authoritative source.

### 2. Non-Authoritative Unknowns (Narrative-Only)

Examples:
- What the tavern smells like
- NPC tone of voice, mannerisms, dialogue style
- How to describe an arrow hitting a table
- Atmospheric details (weather mood, ambient sounds)
- Flavor text for spell effects

**Spark can fill these freely** within existing containment rules, because they do not affect mechanical state.

---

## The Protocol: NeedFact → Authority Resolution → WorldPatch

### Step 1: Box encounters missing fact

Box halts with a structured request:

```
NeedFact {
    fact_type: "OBJECT_DIMENSIONS" | "LIGHTING_LEVEL" | "MATERIAL" | ...
    object_ref: "table_12"          # Scene-local handle
    why_needed: "cover_calculation"  # What mechanical system needs this
    constraints: {                   # Plausibility bounds from RAW
        height_range: [0.3, 1.5],   # meters
        must_be: "solid"            # for cover to apply
    }
}
```

This is **fail-closed**: Box does NOT proceed with a guess. It halts.

### Step 2: Lens routes to Authority Resolver

Resolution priority (strict ordering, fail-closed):

1. **Scene canonical data** — if the SessionBundle / SceneCard already defines this fact, use it
2. **Policy default** — explicitly declared rule-backed defaults (e.g., "If furniture dimensions unspecified, treat as standard tavern table: 0.9m × 1.2m × 0.6m"). These defaults are part of Box/Lens governance, NOT Spark creativity. They are logged with provenance `source=POLICY_DEFAULT`
3. **User question** — present bounded choices to the player/GM: "Is this a small tavern table or a large banquet table?" (not free-form — constrained to mechanically distinct options)
4. **Spark suggestion** — Spark may propose a candidate answer, but it is a **draft only**. It MUST be confirmed by user or policy before commitment. It is NEVER auto-committed.

If no authority can resolve the fact: the system uses the most conservative mechanical assumption (e.g., no cover if table dimensions unknown) and logs the gap.

### Step 3: WorldPatch committed to authoritative state

Once resolved, the system produces a deterministic, replayable patch:

```
WorldPatch {
    fact_id: "table_12.height"
    value: 0.9
    unit: "meters"
    source: "SCENE_DATA" | "POLICY_DEFAULT" | "USER_CONFIRMED" | "SPARK_DRAFT_USER_CONFIRMED"
    timestamp: <deterministic turn counter>
    provenance: {
        resolver: "authority_resolver_v1"
        priority_used: 1  # which level of the chain resolved it
    }
}
```

This patch becomes part of the authoritative world state. It is logged in the event stream. It is replayable.

### Step 4: Box proceeds with committed fact

Only after the WorldPatch is committed does Box compute the mechanical result (cover, concealment, break DC, etc.).

---

## Spark's Role in This Protocol

Spark may:
- **Phrase the user question** ("The fighter wants to duck behind the table — is it a small tavern table or a large banquet table?")
- **Propose plausible candidates** as drafts (tagged `source=SPARK_DRAFT`, never auto-committed)
- **Narrate the result** after Box resolves ("She ducks behind the heavy oak table, arrows thudding into the wood")

Spark may NOT:
- Supply a fact that is auto-committed to world state
- Bypass the authority chain
- Decide mechanical properties without user/policy confirmation

---

## Campaign Continuity Implications

This same protocol extends to creative/campaign content:

- Spark produces **draft scene cards / hooks / NPCs** (non-authoritative)
- Lens structures drafts into **candidates** with required fields
- User (or policy) accepts/rejects
- Accepted items become part of the world ledger with full provenance

The pattern is universal: **Spark suggests texture, never truth. Lens manages knowledge. Box only runs when truth is committed.**

---

## Impact on Existing Research

### RQ-SPARK-001 Sub-C (Improvisation Protocol)
The "JIT Fact Acquisition" pattern described in Sub-C is valid ONLY for non-authoritative facts. Any mechanics-relevant fact acquisition must go through this Authority Resolution Protocol. The synthesis document (RWO-001) must reflect this constraint.

### WO-008 (JIT Fact Acquisition)
The existing `fact_acquisition.py` module should be reviewed against this protocol. Its fallback to `DEFAULT_ROOM_TEMPLATES` is acceptable as a policy default (priority level 2), but any path where Spark-generated facts enter mechanical calculations must be blocked.

### Future Scene Generation
Any prep-phase scene generation that uses Spark to create room layouts, object placements, or environmental features must commit all mechanics-relevant facts to the SessionBundle BEFORE play begins. During play, missing facts follow this protocol.

---

## Existing Infrastructure (Code Audit Findings, 2026-02-12)

A code audit confirmed that ~80% of the machinery for this protocol already exists:

### Already Built
- **Authority tiers** in `aidm/lens/lens_index.py` — `SourceTier` enum: BOX > CANONICAL > PLAYER > SPARK > DEFAULT. The resolution order already encodes the principle that Spark-sourced facts are low-authority.
- **Fact acquisition** in `aidm/lens/fact_acquisition.py` — `FactRequest`, `FactResponse`, `FactAcquisitionManager`, validation rules, forbidden defaults for critical attributes (size, position, HP, AC). This is essentially the `NeedFact` concept, already designed.
- **Box↔Lens bridge** in `aidm/lens/box_lens_bridge.py` — synchronization layer with query methods like `get_entity_size()`, `get_cell_properties()`.
- **Event sourcing** — all Box state changes flow through typed events (`box_events.py`). Close to the `WorldPatch` concept, though output-side (results of resolution) rather than input-side (committing facts before resolution).
- **Conflict resolution** — `LensIndex.resolve_conflict()` exists but Box doesn't call it during fact reads.

### Missing (The Integration Gap)
- **Box does not halt mid-combat to acquire missing facts.** The `FactAcquisitionManager` (WO-008) was designed and built but never integrated into the combat resolution path. Box either uses pre-loaded data or proceeds without it — there is no mid-turn pause.
- **No `WorldPatch` commit handshake.** Events flow Box→Lens (output), but there's no formal input-side commit of "here is a new authoritative fact, now you may proceed." The closest thing is `LensIndex.set_fact()` with a source tier, but no handshake where Box says "I accept this fact and will now compute."
- **No "never auto-commit from SPARK tier" enforcement.** `resolve_conflict()` exists but the policy that SPARK-tier facts cannot enter mechanical calculations is not enforced at the boundary.

### Integration Path
The `WorldPatch` contract should be: a set of `LensFact` entries at CANONICAL, PLAYER, or POLICY_DEFAULT tier (never raw SPARK), with a commit ID that Box references when it resumes. This makes fact acquisition replayable and auditable.

The concrete integration is: wire `FactAcquisitionManager` into the combat resolution path, add the halt-and-resolve protocol, and enforce the "no auto-commit from SPARK tier" policy at the `LensIndex.set_fact()` boundary.

---

## Concrete Next Steps

1. Define `NeedFact` message type formally — extends existing `FactRequest` with `why_needed` and `constraints` fields
2. Define `WorldPatch` message type formally — set of `LensFact` entries with commit ID, provenance, replay semantics
3. Wire `FactAcquisitionManager` into combat resolution path (the critical missing integration)
4. Add enforcement: `LensIndex.set_fact()` rejects SPARK-tier facts for mechanics-relevant attributes
5. Add boundary law: "No Spark-originated fact may enter Box state without explicit authority confirmation"
6. Update RQ-SPARK-001 synthesis to reflect this constraint

---

*This decision was prompted by external architectural review identifying that Spark-supplied scene facts in mechanical calculations constitute an LLM-in-the-combat-loop violation. Infrastructure audit confirmed 80% of machinery exists; the gap is integration and policy enforcement.*

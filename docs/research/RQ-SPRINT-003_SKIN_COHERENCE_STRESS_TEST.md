# RQ-SPRINT-003: Skin Coherence Under Stress -- Cross-Session Consistency

**Research Sprint:** RQ-SPRINT-003
**Executed by:** Research Agent (Opus 4.6)
**Date:** 2026-02-14
**Status:** COMPLETE

---

## Executive Summary

**Core Question:** What breaks first when a frozen skin meets an unforeseen mechanical interaction?

**Answer:** Not content novelty. The system handles unforeseen abilities adequately via `EventPresentationEntry` category fallbacks. What breaks is **compound events** -- when multiple abilities interact in a single narrative moment (AoO during bull rush, sneak attack on flanked+grappled target, AoE with differential saves). The NarrativeBrief is a single-event, single-target, single-condition pipe. Real play constantly produces multi-event, multi-target, multi-condition moments.

---

## Key Findings

### Finding 1: Layer B is Operationally Disconnected

Layer B (Presentation Semantics) is well-designed as a frozen schema with full compile-time provenance, but it is **operationally disconnected** from the live narration pipeline. Two critical gaps exist:

- **GAP-B-001:** `NarrativeBrief.presentation_semantics` is always `None` at runtime -- the Lens assembler does not populate it from the PresentationSemanticsRegistry
- **GAP-B-002:** `TruthChannel` has no fields to serialize Layer B data to Spark

These gaps mean that even though the schema is correct and the data exists in compiled form, Spark never sees it during narration generation.

### Finding 2: Stress Test Results (20 Edge Cases)

Of 20 edge-case scenarios tested against the current schema:

| Result | Count | Description |
|--------|-------|-------------|
| PASS | 1 | Clean narration with full Layer B support |
| PARTIAL | 10 | Narration functional but loses flavor -- falls back to generic event templates |
| FAIL | 9 | Schema cannot represent the situation; narration would contradict or omit critical detail |

### Finding 3: Failures Cluster Around Three Structural Limitations

1. **Single-target briefs cannot represent AoE or multi-target events** -- A Fireball hitting 5 creatures generates 5 separate NarrativeBriefs, losing the narrative unity of "one explosion, five victims"
2. **Single-condition slots cannot represent condition stacking** -- A target that is prone, grappled, and flanked simultaneously has no way to communicate all three conditions to Spark in one brief
3. **Independent event-to-brief mapping cannot represent causal chains** -- An AoO triggered by a bull rush that causes a trip is three events that form one narrative moment, but produce three disconnected briefs

### Finding 4: Cross-Session Tonal Drift

For mechanically identical situations occurring in different sessions, the narration **would** remain tonally consistent IF Layer B data reached Spark, because:
- Delivery mode, staging, and VFX tags are frozen at compile time
- The same ability always resolves to the same presentation entry
- Template narration uses the same template for the same narration token

However, without Layer B connected (GAP-B-001), Spark currently has no frozen reference point. Narration tone depends entirely on the template selected by `action_type`, which is coarser than Layer B would provide.

---

## Priority Fix Path

| Priority | Fix | Effort | Impact |
|----------|-----|--------|--------|
| **P0** | Connect Layer B to pipeline: populate `NarrativeBrief.presentation_semantics` from registry in `assemble_narrative_brief()` | Low (5-10 lines) | High -- enables all downstream Layer B consumption |
| **P1** | Widen NarrativeBrief from single-target to multi-target with combat context flags | Medium | High -- fixes 6 of 9 FAIL cases |
| **P1** | Add `causal_chain_id` field to NarrativeBrief for grouping related events | Low | Medium -- enables narrative unity for compound events |
| **P2** | Add `active_conditions: tuple[str, ...]` field to NarrativeBrief | Low | Medium -- enables condition-stack narration |
| **P2** | Teach Narrator to consume staging/delivery_mode for narration structure | Medium | High -- delivers the Layer B promise |

---

## Stress Test Edge Cases (Representative Sample)

| # | Scenario | Result | Failure Mode |
|---|----------|--------|-------------|
| 1 | Critical hit with concealment miss | PARTIAL | Two contradictory outcomes in sequence; no brief grouping mechanism |
| 2 | AoO during forced movement into hazard | FAIL | Three-event causal chain produces three disconnected briefs |
| 3 | Sneak attack on flanked+grappled target | FAIL | Multiple conditions and damage bonuses; single-condition slot insufficient |
| 4 | AoE with differential saves | FAIL | Per-target save results require multi-target brief; current schema is single-target |
| 5 | Spell save with cover bonus | PARTIAL | Cover bonus modifies save but is not communicated to Spark |
| 6 | Counter-trip during trip attempt | FAIL | Recursive event: trip triggers counter-trip; no brief nesting |
| 7 | Full attack: some hit, some miss, target dies mid-sequence | PARTIAL | Defeat event mid-sequence is narrated separately from the hits |
| 8 | Grapple → pin → tie up sequence | FAIL | Three-phase maneuver; each phase is independent brief |
| 9 | Readied action interrupts spellcasting | PARTIAL | Interrupt timing not communicated in brief; Spark doesn't know this was a reaction |
| 10 | Environmental + spell damage in same round | PARTIAL | Two damage sources; separate briefs lose "caught between fire and ice" moment |

---

## NarrativeBrief Schema Extension Recommendations

### Current Schema (Relevant Fields)

```python
@dataclass(frozen=True)
class NarrativeBrief:
    action_type: str
    actor_name: str
    target_name: Optional[str]           # Single target
    severity: str
    condition_applied: Optional[str]     # Single condition
    target_defeated: bool
    presentation_semantics: Optional[AbilityPresentationEntry]  # Always None today
    source_event_ids: tuple
```

### Recommended Extensions

```python
@dataclass(frozen=True)
class NarrativeBrief:
    # ... existing fields ...

    # Multi-target support (P1)
    additional_targets: tuple = ()       # ((name, severity, defeated), ...)

    # Causal chain grouping (P1)
    causal_chain_id: Optional[str] = None  # Groups related events
    chain_position: int = 0                # 0=standalone, 1=first, 2=continuation

    # Condition context (P2)
    active_conditions: tuple = ()        # All conditions on target at narration time
    actor_conditions: tuple = ()         # Conditions on actor affecting this action

    # Combat spatial context (P2)
    is_flanking: bool = False
    has_cover: bool = False
    is_aoo: bool = False                 # This action was an attack of opportunity
    is_readied: bool = False             # This action was a readied action
```

---

## Answer: What Breaks First?

What breaks first is not the frozen skin itself -- it is the **pipe width between Box and Spark**. The NarrativeBrief is designed as a single-event summary, but D&D 3.5e combat regularly produces compound narrative moments that span multiple events, multiple targets, and multiple conditions simultaneously.

The frozen Layer B presentation semantics are architecturally sound and would provide cross-session consistency -- but they are not yet connected to the runtime pipeline. Connecting them (GAP-B-001, ~10 lines of code) is the single highest-impact fix for skin coherence.

---

*End of RQ-SPRINT-003 report.*

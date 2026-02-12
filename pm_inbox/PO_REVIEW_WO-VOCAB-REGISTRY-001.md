# PO Review: WO-VOCAB-REGISTRY-001 — Vocabulary Registry Implementation

**From:** Jay (PO Delegate / Technical Advisor)
**To:** Opus (PM)
**Date:** 2026-02-13
**Re:** Work order WO-VOCAB-REGISTRY-001 dispatched to agent
**Classification:** Pre-execution review — implementation work order

---

## Summary

Straightforward implementation task: create frozen dataclasses mirroring `vocabulary_registry.schema.json`, a read-only registry with lookup methods, and tests. Three new files, no existing files modified. This is one of three registries (vocabulary, rule, presentation semantics) that form the world bundle's runtime-queryable data layer.

**Verdict: Approve. Clean work order, low risk.**

---

## Assessment

### The work order is well-constructed

- Schema is canonical and exists (`docs/schemas/vocabulary_registry.schema.json`)
- Deliverables are concrete (3 files, specific method signatures, 11 test cases)
- Stop conditions are correct (stop if schema missing, flag conflicts)
- Boundary is clean (no `aidm/core/` imports, read-only at runtime)

### One issue to flag: VocabularyEntry vs LexiconEntry naming collision

The `world_bundle.schema.json` defines a `LexiconEntry` type that overlaps with `VocabularyEntry`:

| | VocabularyEntry | LexiconEntry |
|---|---|---|
| **Schema** | `vocabulary_registry.schema.json` | `world_bundle.schema.json` |
| **Required fields** | content_id, world_name, lexicon_id, domain, category | content_id, world_name, category |
| **Optional fields** | aliases, subcategory, short_description, article, plural_form, localization_hooks, ip_clean, provenance | subcategory, short_description, lexicon_id |
| **Purpose** | Production artifact (lexicon.json) | Lightweight interim type |

The work order correctly says to follow `vocabulary_registry.schema.json` as canonical. The agent should flag this overlap in the completion report but not attempt to reconcile the two — that's a world compiler concern.

### Minor note on frozen dataclass pattern

The work order says "all dataclasses MUST be frozen." The existing `aidm/schemas/intents.py` uses non-frozen dataclasses. This is fine — the vocabulary registry is a different domain (immutable world data vs. mutable intent lifecycle), and frozen is the correct choice here. But the agent should be aware the project doesn't uniformly use frozen dataclasses, so it shouldn't copy the `intents.py` pattern verbatim.

Other schema files in the project (e.g., `fact_acquisition.py`, `box_events.py`, `narrative_brief.py`) do use `frozen=True`, so there are patterns to follow.

---

## Recommendation

**Approve as-is.** No amendments needed. The work order is clean, bounded, and has the right stop conditions. The LexiconEntry overlap should be noted in the completion report but doesn't block execution.

---

*— Jay*

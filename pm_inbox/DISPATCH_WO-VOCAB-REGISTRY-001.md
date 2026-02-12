# Instruction Packet: Vocabulary Registry Agent

**Work Order:** WO-VOCAB-REGISTRY-001 (Vocabulary Registry Implementation)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 2 (Blocks World Compiler lexicon output)
**Deliverable Type:** Code implementation + tests

---

## READ FIRST

The vocabulary registry is how the World Compiler maps mechanical IDs (content_id) to world-flavored names. The JSON schema exists at `docs/schemas/vocabulary_registry.schema.json`. This is the lexicon layer — it answers "what is ABILITY_003 called in this world?" (Answer: "Void Flare" in Ashenmoor, "Sunburst" in Crystaldeep).

The vocabulary registry is a companion to the presentation semantics registry (WO-AD007-IMPL-001) and the rule registry (WO-RULEBOOK-MODEL-001). Together these three registries form the world bundle's runtime-queryable data layer.

---

## YOUR TASK

### Deliverable 1: Vocabulary Dataclasses

**File:** `aidm/schemas/vocabulary.py` (NEW)

Implement frozen dataclasses mirroring `docs/schemas/vocabulary_registry.schema.json`:

- `VocabularyEntry` — A single name mapping: content_id → world_name + category + subcategory + short_description + lexicon_id
- `VocabularyRegistry` — Top-level container: schema_version, world_id, entries (sorted by content_id)
- Any supporting types defined in the JSON schema (WorldTaxonomy, LocalizationHooks, VocabularyProvenance, etc.)

All dataclasses frozen. All support `to_dict()` / `from_dict()`.

Read the JSON schema first — match its structure exactly.

### Deliverable 2: Vocabulary Registry

**File:** `aidm/lens/vocabulary_registry.py` (NEW)

Implement a registry that:
1. Loads a `VocabularyRegistry` from a JSON file
2. `get_world_name(content_id: str) -> Optional[str]` — look up the world-flavored name for a content ID
3. `get_entry(content_id: str) -> Optional[VocabularyEntry]` — full entry lookup
4. `search_by_name(query: str) -> list[VocabularyEntry]` — find entries by world_name substring (case-insensitive)
5. `list_by_category(category: str) -> list[VocabularyEntry]` — all entries in a category
6. `get_content_id(world_name: str) -> Optional[str]` — reverse lookup: world name → content ID
7. Immutable after loading
8. Validates no duplicate content_ids on load
9. Validates no duplicate lexicon_ids on load

### Deliverable 3: Tests

**File:** `tests/test_vocabulary.py` (NEW)

Tests:
1. Frozen dataclass rejects mutation
2. `to_dict()` / `from_dict()` round-trip
3. Registry rejects duplicate content_ids
4. Registry rejects duplicate lexicon_ids
5. `get_world_name()` returns correct name
6. `get_world_name()` returns None for unknown ID
7. `search_by_name()` finds entries by substring
8. `search_by_name()` is case-insensitive
9. `get_content_id()` reverse lookup works
10. `list_by_category()` returns sorted results
11. Empty registry is valid

Create a fixture with 5-8 vocabulary entries across 2-3 categories.

---

## WHAT EXISTS (DO NOT MODIFY)

| Component | Location | Status |
|-----------|----------|--------|
| JSON schema | `docs/schemas/vocabulary_registry.schema.json` | Canonical — match exactly |
| World compiler contract | `docs/contracts/WORLD_COMPILER.md` | References vocabulary as compile output |
| LexiconEntry in world_bundle schema | `docs/schemas/world_bundle.schema.json` | Related type — check for overlap |

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `docs/schemas/vocabulary_registry.schema.json` | Canonical JSON schema |
| 2 | `docs/contracts/WORLD_COMPILER.md` | How vocabulary entries are produced (Stage 1) |
| 2 | `docs/schemas/world_bundle.schema.json` | LexiconEntry type definition |
| 3 | `aidm/schemas/intents.py` | Frozen dataclass pattern |

## STOP CONDITIONS

- If `vocabulary_registry.schema.json` does not exist, STOP and report.
- If LexiconEntry in world_bundle.schema.json conflicts with the vocabulary registry schema, flag in completion report but follow vocabulary_registry.schema.json as canonical.

## DELIVERY

- New files: `aidm/schemas/vocabulary.py`, `aidm/lens/vocabulary_registry.py`, `tests/test_vocabulary.py`
- Full test suite run at end — report total pass/fail count
- Completion report: `pm_inbox/AGENT_WO-VOCAB-REGISTRY-001_completion.md`

## RULES

- All dataclasses MUST be frozen
- No imports from `aidm/core/`
- The registry is READ-ONLY at runtime
- Follow existing code style and test patterns
- `lexicon_id` generation (sha256(world_seed + content_id)[:16]) is a compiler concern — the registry just stores and validates uniqueness

---

END OF INSTRUCTION PACKET

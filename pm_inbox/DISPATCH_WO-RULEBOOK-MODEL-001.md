# Instruction Packet: Rulebook Agent

**Work Order:** WO-RULEBOOK-MODEL-001 (Rulebook Object Model)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 1 (Blocks World Compiler output + Table UI rulebook object)
**Deliverable Type:** Code implementation + tests

---

## READ FIRST

The Rulebook Object Model is Phase 0.4 in the revised program sequencing. It defines how the world-owned rulebook works at runtime: storage format, indexing, and query API. The World Compiler (Phase 1.2) will *produce* rulebook entries; this WO builds the container that *stores and serves* them.

The JSON schema already exists at `docs/schemas/rule_registry.schema.json`. The MVP scenario requires a player to ask "show me that fire ability" and get a stable, frozen entry back.

---

## YOUR TASK

### Deliverable 1: Rule Entry Dataclasses

**File:** `aidm/schemas/rulebook.py` (NEW)

Implement frozen dataclasses mirroring `docs/schemas/rule_registry.schema.json`:

- `RuleEntry` — A single rulebook entry with fields from the JSON schema. Must include at minimum:
  - `content_id: str` — Stable mechanical ID (e.g., "spell.fire_burst_003")
  - `world_name: str` — World-flavored display name (from lexicon)
  - `category: str` — Taxonomy category in this world
  - `rule_text: str` — Generated prose description of the rule/ability
  - `parameters: RuleParameters` — Mechanical parameter summary
  - `text_slots: RuleTextSlots` — Templated text components
  - `provenance: RuleProvenance` — Where this entry came from

- `RuleParameters` — Structured mechanical summary (range, area, damage, save, duration, etc.)
- `RuleTextSlots` — Named text components (short_description, full_description, flavor_text, mechanical_summary)
- `RuleProvenance` — Source tracking (compiler_version, seed_used, content_pack_id, llm_output_hash)

Read the JSON schema file first — match its structure exactly. All dataclasses frozen, all support `to_dict()` / `from_dict()`.

### Deliverable 2: Rulebook Registry

**File:** `aidm/lens/rulebook_registry.py` (NEW)

Implement a registry that:
1. Loads a `RulebookRegistry` from a JSON file (world bundle output)
2. `get_entry(content_id: str) -> Optional[RuleEntry]` — exact lookup by mechanical ID
3. `search(query: str) -> list[RuleEntry]` — simple substring search on `world_name`, `category`, `rule_text` (case-insensitive)
4. `list_by_category(category: str) -> list[RuleEntry]` — all entries in a category, sorted by world_name
5. `list_all() -> list[RuleEntry]` — all entries, sorted by content_id
6. Is immutable after loading — no add/remove/modify methods
7. Validates no duplicate content_ids on load

The registry lives in Lens because it's a context-providing component — it helps the Crystal Ball / Notebook / Spark answer player questions about abilities.

### Deliverable 3: Tests

**File:** `tests/test_rulebook.py` (NEW)

Tests:
1. Frozen dataclass rejects mutation
2. `to_dict()` / `from_dict()` round-trip preserves all fields
3. Registry rejects duplicate content_ids
4. `get_entry()` returns correct entry
5. `get_entry()` returns None for unknown ID
6. `search()` finds entries by world_name substring
7. `search()` is case-insensitive
8. `list_by_category()` returns sorted results
9. `list_all()` returns all entries sorted by content_id
10. Empty registry is valid (world with no rules yet)

Create a small fixture (3-5 rule entries covering different categories) for test use.

---

## WHAT EXISTS (DO NOT MODIFY)

| Component | Location | Status |
|-----------|----------|--------|
| JSON schema | `docs/schemas/rule_registry.schema.json` | Canonical — match exactly |
| World compiler contract | `docs/contracts/WORLD_COMPILER.md` | References rulebook as compile output |
| Existing schemas pattern | `aidm/schemas/intents.py`, `aidm/schemas/attack.py` | Follow same frozen dataclass pattern |

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `docs/schemas/rule_registry.schema.json` | Canonical JSON schema |
| 2 | `docs/contracts/WORLD_COMPILER.md` | How rulebook entries are produced |
| 2 | `docs/decisions/AD-007_PRESENTATION_SEMANTICS_CONTRACT.md` | Layer B feeds rulebook `ui_description` |
| 3 | `aidm/schemas/intents.py` | Frozen dataclass pattern to follow |

## STOP CONDITIONS

- If `rule_registry.schema.json` does not exist or is empty, STOP and report.
- If the schema structure conflicts with AD-007 presentation semantics (e.g., overlapping fields), flag in completion report but proceed.

## DELIVERY

- New files: `aidm/schemas/rulebook.py`, `aidm/lens/rulebook_registry.py`, `tests/test_rulebook.py`
- Full test suite run at end — report total pass/fail count
- Completion report: `pm_inbox/AGENT_WO-RULEBOOK-MODEL-001_completion.md`

## RULES

- All dataclasses MUST be frozen
- No imports from `aidm/core/` — this is a schemas + lens component
- The registry is READ-ONLY at runtime. The World Compiler writes it; everything else reads it.
- Search does NOT use LLM. Simple substring matching only. Spark handles natural language queries by converting them to search terms first.
- Follow existing code style and test patterns

---

END OF INSTRUCTION PACKET

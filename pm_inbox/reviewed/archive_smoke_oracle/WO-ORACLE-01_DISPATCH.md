# WO-ORACLE-01: Oracle Spine — Stores + Canonical Profile + Gate A

**Priority:** P0 — Next on build order
**Depends on:** WO-ORACLE-SURVEY (ACCEPTED, `7b4268f`), WO-FUZZER-DETERMINISM-GATES (ACCEPTED, `e128342`)
**Authority:** Aegis Direction Memo (2026-02-18), Oracle Memo v5.2 §4, GT v12 A-ORACLE-SPINE
**PM Review:** DISPATCHED
**PM Amendment:** Aegis audit — 3 must-fix + 2 recommended (2026-02-18). See amendment notes inline.

---

## Objective

Build the Oracle v0 data stores as a thin spine: FactsLedger, UnlockState, and minimal StoryState container. Pin the canonical JSON profile and hash algorithm globally. Prove determinism via Gate A (same inputs → same canonical bytes). No higher-layer wiring (Lens/Spark/UI) in this WO.

This is **persistence + determinism infrastructure only.** The stores accept writes and produce deterministic reads. They do not yet feed WorkingSet assembly — that's Phase 2.

---

## Context for Builder

**Read before implementing** (in this order):
1. [SURVEY_ORACLE_OVERLAP.md](pm_inbox/SURVEY_ORACLE_OVERLAP.md) — Sections 1 (FactsLedger), 4 (UnlockState), 2 (StoryState), 7 (Canonical Serialization). This tells you what already exists and what's greenfield.
2. [DOCTRINE_03_ORACLE_MEMO_V52.txt](pm_inbox/DOCTRINE_03_ORACLE_MEMO_V52.txt) — §4 (Minimum Oracle Data Model), §5 (Precision Tokens), §6 (Determinism: Canonical Bytes).
3. [DOCTRINE_01_FINAL_DELIVERABLE.txt](pm_inbox/DOCTRINE_01_FINAL_DELIVERABLE.txt) — Anchor index (A-ORACLE-SPINE, A-NO-BACKFLOW, A-ORACLE-TRUNC) and GAP register (GAP-004, GAP-005, GAP-006).

**Existing code you will build on or alongside:**
- `aidm/core/event_log.py` — Event/EventLog. Append-only, monotonic IDs, JSONL persistence. You are NOT modifying this file. Oracle stores sit alongside EventLog, not inside it.
- `aidm/core/provenance.py` — ProvenanceStore, `compute_value_hash()` (SHA-256, 16-char prefix). You will USE `compute_value_hash()` as the content-addressing function for facts. Do NOT create a second hashing utility.
- `aidm/schemas/knowledge_mask.py` — KnowledgeTier, KnowledgeEntry, MaskedEntityView. This is the existing entity-level unlock system. UnlockState generalizes from entity visibility to arbitrary content visibility.
- `aidm/core/state.py` — WorldState, FrozenWorldStateView. StoryState is a NEW object that sits between CampaignStore (persistence) and WorldState (mechanics).

**Existing serialization pattern:** `json.dumps(sort_keys=True)` → SHA-256 is used across EventLog, ProvenanceStore, WorldState.state_hash(), PromptPack.to_json(). Follow this pattern exactly — the canonical profile formalizes what already exists.

---

## Changes

### Change 1: Canonical JSON Profile (`aidm/oracle/canonical.py`)

Create `aidm/oracle/__init__.py` and `aidm/oracle/canonical.py`.

Define the canonical JSON profile as a single authoritative module:

```
CANONICAL_JSON_PROFILE:
- object keys: sorted lexicographically (sort_keys=True)
- separators: (',', ':') — no insignificant whitespace
- encoding: UTF-8, ensure_ascii=True
- no trailing newline in canonical form
- floats: FORBIDDEN in canonical artifacts (raise TypeError if encountered)
- hash algorithm: SHA-256, full hex digest (64 chars)
- short hash: first 16 chars of full hex digest (for IDs)
```

Provide two public functions:
- `canonical_json(obj: Any) -> bytes` — Returns canonical UTF-8 bytes. Raises `TypeError` on floats.
- `canonical_hash(obj: Any) -> str` — Returns SHA-256 hex digest of `canonical_json(obj)`. Full 64-char digest.
- `canonical_short_hash(obj: Any) -> str` — Returns first 16 chars of `canonical_hash(obj)`.

**Constraint:** `canonical_json` must produce byte-identical output across Python versions for the same input. Test this explicitly.

**Float prohibition:** Oracle Memo v5.2 §6 says "floats: avoid in canonical artifacts; if unavoidable, define normalization explicitly." For v0, we choose FORBIDDEN — raise on floats. This closes GAP-005 for Oracle artifacts.

**Relationship to existing code:** This module does NOT replace existing `json.dumps(sort_keys=True)` calls in EventLog, PromptPack, etc. Those continue unchanged. This module is for NEW Oracle artifacts only. Migration of existing code is a future WO.

### Change 2: FactsLedger (`aidm/oracle/facts_ledger.py`)

Implement the FactsLedger as an append-only store of canon facts with provenance.

**Fact schema (frozen dataclass):**
- `fact_id: str` — `compute_value_hash(payload)` from `provenance.py` (content-addressed, SHA-256, 16-char prefix). **Do NOT use `canonical_short_hash` for fact_id.** The existing `compute_value_hash` is the single content-addressing function. `canonical_hash`/`canonical_short_hash` are for digests and receipts only.
- `kind: str` — One of: `WORLD_RULE`, `NPC_IDENTITY`, `LOCATION`, `FACTION_LAW`, `CLUE`, `ITEM_LORE`, `QUEST_STATE`, `ENTITY_STATE`, `COMBAT_OUTCOME`
- `payload: Dict[str, Any]` — The fact content. Must pass `canonical_json()` without error (no floats).
- `provenance: Dict[str, Any]` — Source references: `{"source": str, "event_ids": List[int], "rule_refs": List[Dict]}`. Must pass `canonical_json()`. **Normalization required:** `event_ids` must be sorted ascending. `rule_refs` must be sorted by a stable key (e.g., `json.dumps(ref, sort_keys=True)`). Normalize on construction, not on serialization.
- `visibility_mask: str` — One of: `PUBLIC`, `DM_ONLY`, `PLAYER_SPECIFIC`, `SYSTEM`. Default: `DM_ONLY` (default-deny per Oracle Memo §4.4).
- `precision_tag: str` — `LOCKED` or `UNLOCKED`. Default: `LOCKED` (default-deny per Oracle Memo §5).
- `stable_key: str` — Ordering tie-break for deterministic enumeration. Format: `"{kind}:{fact_id}"` (full 16-char hash). If two facts have the same `kind` and `fact_id` (impossible given content addressing), use `created_event_id` as final tie-break.
- `created_event_id: int` — The EventLog event_id that caused this fact to be recorded.

**FactsLedger class:**
- `append(fact: Fact) -> None` — Append a fact. **Idempotent for identical content:** if `fact_id` already exists and stored fact canonical bytes are identical, treat as no-op. If `fact_id` exists but canonical bytes differ, raise `ValueError` (inconsistent content for same hash — signals a bug). This is replay-friendly.
- `get(fact_id: str) -> Optional[Fact]` — Retrieve by ID.
- `query(kind: Optional[str], visibility_mask: Optional[str]) -> List[Fact]` — Filter. Return sorted by `stable_key` for deterministic ordering.
- `all_facts() -> List[Fact]` — All facts sorted by `stable_key`.
- `to_jsonl(path: Path) -> None` — Persist to JSONL using `canonical_json()`.
- `from_jsonl(path: Path) -> FactsLedger` — Load from JSONL.
- `digest() -> str` — `canonical_hash` of the full sorted fact list. This is the determinism receipt.

**Constraint:** `digest()` must be deterministic — same facts in any insertion order → same digest. This requires sorting by `stable_key` before hashing.

### Change 3: UnlockState (`aidm/oracle/unlock_state.py`)

Implement UnlockState as the enforcement state for precision tokens and content visibility.

**UnlockEntry (frozen dataclass):**
- `handle: str` — The content handle being unlocked (fact_id, rule_ref, or arbitrary content key).
- `scope: str` — One of: `SCENE`, `SESSION`, `CAMPAIGN`. Default: `SCENE`.
- `source: str` — One of: `NOTEBOOK`, `RULEBOOK`, `RECALL_ROLL`, `SYSTEM`.
- `provenance_event_id: int` — The event that caused the unlock.

**No `created_at` field.** Wall-clock timestamps break determinism (Gate A). The `provenance_event_id` provides ordering and traceability. If wall-clock time is needed later, it must be derived deterministically from the EventLog event's timestamp, not from `datetime.now()`.

**UnlockState class:**
- `unlock(entry: UnlockEntry) -> None` — Record an unlock. Idempotent — re-unlocking with broader scope upgrades; narrower scope is ignored.
- `is_unlocked(handle: str, current_scope: str) -> bool` — Check if a handle is unlocked at the given scope level. Scope ordering: `SCENE < SESSION < CAMPAIGN`. A `CAMPAIGN` unlock satisfies `SESSION` and `SCENE` checks.
- `unlocked_handles(current_scope: str) -> FrozenSet[str]` — All handles unlocked at or above the given scope.
- `to_jsonl(path: Path) -> None` — Persist using `canonical_json()`.
- `from_jsonl(path: Path) -> UnlockState` — Load.
- `digest() -> str` — Determinism receipt.

**Relationship to KnowledgeMask:** KnowledgeMask handles entity-stat progressive revelation (KnowledgeTier enum, per-entity, per-player). UnlockState handles arbitrary content visibility (facts, rule_refs, precision tokens). They are complementary, not competing. Do NOT modify KnowledgeMask. In a future WO, KnowledgeMask may delegate to UnlockState for entity-level unlocks, but that's out of scope here.

### Change 4: Minimal StoryState Container (`aidm/oracle/story_state.py`)

Implement a minimal StoryState as evented pointers. This is Phase 1 — pointers only, no threads or clocks.

**StoryState (frozen dataclass):**
- `world_id: Optional[str]` — Content hash of the WorldState at worldgen commit.
- `campaign_id: str` — From CampaignManifest.
- `scene_id: Optional[str]` — Current scene identifier.
- `mode: str` — One of: `COMBAT`, `EXPLORATION`, `ROLEPLAY`, `REFERENCE`, `NOTEBOOK`. Default: `EXPLORATION`.
- `version: int` — Monotonically increasing. Every mutation creates a new StoryState with `version + 1`.

**StoryStateLog class:**
- `current() -> StoryState` — Return the latest StoryState.
- `apply(event_type: str, payload: Dict) -> StoryState` — Apply an event to produce a new StoryState. Supported event types: `scene_start` (sets scene_id), `scene_end` (clears scene_id), `mode_changed` (sets mode), `world_id_set` (sets world_id). Unknown event types are ignored (no crash).
- `history() -> List[StoryState]` — All versions, ordered by version number.
- `to_jsonl(path: Path) -> None` — Persist.
- `from_jsonl(path: Path) -> StoryStateLog` — Load.
- `digest() -> str` — Determinism receipt of current state.

**Constraint:** StoryState is immutable. Every change creates a new version. The log is append-only. This satisfies "all updates are events; no silent mutation" (Oracle Memo §4.2).

### Change 5: Gate A Tests (`tests/test_oracle_spine.py`)

Write tests proving Gate A: store determinism.

**Required test cases:**

1. **`test_canonical_json_deterministic`** — Same input → byte-identical output, 10 iterations.
2. **`test_canonical_json_rejects_floats`** — `canonical_json({"x": 1.5})` raises `TypeError`.
3. **`test_canonical_hash_stable`** — Same input → same hash, 10 iterations.
4. **`test_facts_ledger_digest_deterministic`** — Insert N facts in random order; digest is identical regardless of insertion order. Run 5 times with shuffled insertion.
5. **`test_facts_ledger_idempotent_append`** — Same fact appended twice = no-op (no error, same digest). Different fact with same fact_id (impossible via content addressing, but test with mock) = ValueError.
6. **`test_facts_ledger_jsonl_roundtrip`** — Write to JSONL, load, digest matches.
7. **`test_facts_ledger_provenance_normalized`** — Facts with unsorted `event_ids` or `rule_refs` are normalized on construction. Digest is stable regardless of input order.
8. **`test_unlock_state_scope_ordering`** — CAMPAIGN unlock satisfies SESSION and SCENE checks.
9. **`test_unlock_state_idempotent_upgrade`** — Re-unlock with broader scope upgrades; narrower ignored.
10. **`test_unlock_state_digest_deterministic`** — Same unlocks in different order → same digest.
11. **`test_unlock_state_jsonl_roundtrip`** — Write, load, digest matches.
12. **`test_story_state_immutable`** — Applying event produces new version, old version unchanged.
13. **`test_story_state_version_monotonic`** — Versions strictly increase.
14. **`test_story_state_digest_deterministic`** — Same events → same digest.
15. **`test_story_state_ignores_unknown_events`** — Unknown event type does not crash.
16. **`test_story_state_jsonl_roundtrip`** — Write, load, history matches.
17. **`test_fact_id_uses_compute_value_hash`** — Verify `fact_id` matches `compute_value_hash(payload)` from `provenance.py`, not `canonical_short_hash`.

**All 17 tests must PASS.** This is Gate A.

### Change 6: No-Backflow Assertion (`tests/test_oracle_no_backflow.py`)

Write a structural test proving Oracle stores have no write path from Spark or Immersion layers.

**Required test:**

1. **`test_oracle_stores_no_spark_import`** — Scan all files in `aidm/oracle/` for imports from `aidm/spark/`, `aidm/immersion/`, or `aidm/voice/`. Assert zero matches. This is a static gate for A-NO-BACKFLOW.

---

## Files Expected to Change

| File | Action |
|---|---|
| `aidm/oracle/__init__.py` | CREATE — Package init |
| `aidm/oracle/canonical.py` | CREATE — Canonical JSON profile + hash functions |
| `aidm/oracle/facts_ledger.py` | CREATE — FactsLedger store |
| `aidm/oracle/unlock_state.py` | CREATE — UnlockState store |
| `aidm/oracle/story_state.py` | CREATE — StoryState container + log |
| `tests/test_oracle_spine.py` | CREATE — Gate A determinism tests (17 cases) |
| `tests/test_oracle_no_backflow.py` | CREATE — A-NO-BACKFLOW structural gate |

**Files NOT to change:** Nothing in `aidm/core/`, `aidm/schemas/`, `aidm/lens/`, or existing tests. This WO creates new files only.

---

## Assumptions to Validate (Before Writing Code)

1. **`aidm/oracle/` does not exist** — Verify. If it does, read existing files before creating new ones.
2. **`provenance.py:compute_value_hash()` uses SHA-256, returns 16-char hex prefix** — Verify the implementation. This function mints `fact_id`. Confirm it takes a JSON-serializable value and returns a string. Do NOT use `canonical_short_hash` for `fact_id`.
3. **No existing `Fact` or `FactsLedger` class** — Grep for these names. If they exist, align with them.
4. **`json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=True)`** — Verify this produces compact JSON. The canonical profile uses compact separators (no spaces after `:` and `,`).
5. **Frozen dataclass immutability** — Verify `@dataclass(frozen=True)` prevents attribute mutation in your Python version.
6. **`compute_value_hash` internal serialization** — Check whether `compute_value_hash` uses `sort_keys=True` and what separators it uses. If it uses different canonical rules than `canonical_json()`, document the difference. The two functions serve different purposes (content addressing vs. canonical serialization) and may diverge — that's acceptable as long as each is internally consistent.

---

## Constraints

- **DO NOT modify production code.** This WO creates new files in `aidm/oracle/` and `tests/` only.
- **DO NOT wire Oracle stores to Lens, Spark, or any consumer.** This is persistence infrastructure. Wiring is Phase 2.
- **Hash utility boundary:** `compute_value_hash()` from `provenance.py` is the ONLY function for minting `fact_id` (content addressing). `canonical_hash()`/`canonical_short_hash()` from `canonical.py` are for store digests and determinism receipts only. Two functions, two purposes, no overlap.
- **DO NOT use floats in any Oracle artifact.** The canonical profile rejects them.
- **DO NOT use wall-clock timestamps** (`datetime.now()`, `time.time()`) in any Oracle dataclass field. All temporal ordering must derive from EventLog event_ids or version counters.
- **All persisted data must use canonical_json() from Change 1.** No raw `json.dumps()` in Oracle code.
- **All stores must have a digest() method.** This is the determinism receipt used by Gate A.
- **Provenance dicts must be normalized on construction.** `event_ids` sorted ascending, `rule_refs` sorted by canonical JSON of each ref.
---

## Success Criteria

1. `aidm/oracle/` package exists with `canonical.py`, `facts_ledger.py`, `unlock_state.py`, `story_state.py`.
2. `canonical_json()` produces byte-identical output for same input across 10 iterations.
3. `canonical_json()` raises `TypeError` on float values.
4. FactsLedger digest is insertion-order-independent (shuffled insert → same digest).
5. FactsLedger JSONL roundtrip preserves digest.
6. FactsLedger `append()` is idempotent for identical content, raises ValueError for conflicting content at same hash.
7. `fact_id` is generated by `compute_value_hash(payload)` from `provenance.py`, not by `canonical_short_hash`.
8. Provenance dicts are normalized on construction (sorted event_ids, sorted rule_refs).
9. UnlockState scope ordering works (CAMPAIGN ⊇ SESSION ⊇ SCENE).
10. UnlockState digest is insertion-order-independent.
11. UnlockEntry has NO `created_at` field. No wall-clock timestamps anywhere in Oracle dataclasses.
12. StoryState is immutable; events produce new versions.
13. StoryState version numbers are monotonically increasing.
14. All 17 Gate A tests PASS.
15. No-backflow structural gate PASSES (zero imports from spark/immersion/voice in oracle/).
16. All existing tests still PASS (zero regressions).
17. No files modified outside `aidm/oracle/` and `tests/`.

---

## Delivery

Commit message format: `feat: WO-ORACLE-01 — Oracle spine stores + canonical profile + Gate A`

**Debrief (4 mandatory sections, 500-word cap):**
1. **Scope Accuracy** — Did the WO scope match what you built?
2. **Discovery Log** — What did you verify/discover before and during implementation?
3. **Methodology Challenge** — Where was the WO wrong, ambiguous, or improvable?
4. **Field Manual Entry** — One reusable tradecraft finding for the Builder Field Manual.

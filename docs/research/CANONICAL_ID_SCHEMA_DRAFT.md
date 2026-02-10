# Canonical ID Schema — R0 Research Draft

**Status:** R0 / DRAFT / NON-BINDING
**Purpose:** Define ID conventions before M0 planning
**Authority:** Advisory — requires validation and approval
**Last Updated:** 2026-02-10

---

## ⚠️ DRAFT NOTICE

This document is a **research draft** created during the R0 preparation phase. It represents **proposed** ID conventions, not finalized requirements.

**Do not use for implementation** until:
1. R0 research phase validates feasibility
2. Cross-agent review confirms no conflicts
3. Formal approval locks the schema

**Contradictions with existing code or audit findings must be surfaced, not resolved.**

---

## Purpose

AIDM requires a canonical ID schema to ensure:
- **Uniqueness** across entities, assets, sessions, and events
- **Determinism** (same inputs → same IDs, no UUIDs)
- **Traceability** (IDs reveal provenance and type)
- **Collision resistance** (different types can't collide)
- **Human readability** (debugging and logging)

**Identified Gap:** Current codebase uses inconsistent ID patterns (string IDs, numeric IDs, hash-based IDs). This blocks indexed memory, asset management, and cross-campaign referencing.

---

## Design Principles

### 1. Deterministic Generation
- IDs derived from **content hash + context**, never from random sources
- Same content + same context = same ID (replay-safe)
- No timestamps, UUIDs, or sequential counters (breaks determinism)

### 2. Type Safety
- ID format encodes type (entity vs asset vs session)
- Collision impossible across types (e.g., `entity_123` ≠ `asset_123`)

### 3. Provenance Transparency
- ID reveals creation context (campaign, prep job, generation source)
- Debugging can trace ID back to origin

### 4. Length Constraints
- Human-readable prefix (2-8 chars)
- Hash suffix (8-16 chars, SHA-256 truncated)
- Total length ≤ 64 characters (database key limits)

---

## Proposed ID Format

### General Pattern

```
<type_prefix>_<context>_<hash>
```

**Components:**
- `type_prefix`: 2-8 char type identifier (e.g., `entity`, `asset`, `session`)
- `context`: Optional context for scoping (e.g., campaign ID, prep job ID)
- `hash`: 8-16 char truncated SHA-256 hash of content

**Example:**
```
entity_camp001_a3f2b8c4
asset_camp001_scene_7d4e9a12
session_camp001_20260210_f1c3d8a6
```

---

## ID Types and Schemas

### 1. Entity IDs

**Format:** `entity_<campaign_id>_<entity_hash>`

**Hash Input:**
```python
hash_input = f"{campaign_id}:{entity_type}:{canonical_name}"
entity_id = f"entity_{campaign_id}_{sha256(hash_input)[:8]}"
```

**Example:**
```
entity_camp001_fighter_a3f2b8c4  # Fighter in campaign 001
entity_camp001_goblin_7d4e9a12   # Goblin in campaign 001
```

**Rationale:**
- Campaign scoping prevents cross-campaign collisions
- Entity type + name ensures uniqueness
- Deterministic: same fighter in same campaign = same ID

**Open Questions:**
- Q1: How are NPCs with duplicate names handled? (e.g., "Goblin 1", "Goblin 2")
- Q2: Do entities persist across sessions or are they session-scoped?
- Q3: What happens when an entity is renamed?

---

### 2. Asset IDs

**Format:** `asset_<campaign_id>_<asset_type>_<content_hash>`

**Hash Input:**
```python
hash_input = f"{campaign_id}:{asset_type}:{semantic_key}"
asset_id = f"asset_{campaign_id}_{asset_type}_{sha256(hash_input)[:8]}"
```

**Example:**
```
asset_camp001_portrait_a3f2b8c4  # NPC portrait
asset_camp001_scene_7d4e9a12     # Background plate
asset_camp001_audio_f1c3d8a6     # Ambient sound
```

**Rationale:**
- Asset type prefix enables filtering (e.g., "show me all portraits")
- Content hash enables deduplication (same semantic_key = same asset)
- Campaign scoping allows cross-campaign shared cache resolution

**Open Questions:**
- Q4: Are assets truly content-addressed, or can same semantic_key have multiple versions?
- Q5: How are asset variants handled? (e.g., "tavern_interior_day" vs "tavern_interior_night")
- Q6: Should shared cache assets use `shared_` prefix instead of campaign ID?

---

### 3. Session IDs

**Format:** `session_<campaign_id>_<session_number>_<timestamp_hash>`

**Hash Input:**
```python
hash_input = f"{campaign_id}:{session_number}:{start_timestamp}"
session_id = f"session_{campaign_id}_{session_number:04d}_{sha256(hash_input)[:8]}"
```

**Example:**
```
session_camp001_0001_a3f2b8c4  # Campaign 001, Session 1
session_camp001_0042_7d4e9a12  # Campaign 001, Session 42
```

**Rationale:**
- Sequential session numbers for human readability
- Timestamp hash prevents collisions if session restarted
- Campaign scoping isolates sessions

**Open Questions:**
- Q7: Are session numbers deterministic or sequential?
- Q8: What happens if a session is replayed from a save point?
- Q9: Do sessions nest (e.g., "session 5, encounter 3")?

---

### 4. Event IDs

**Format:** `event_<session_id>_<event_seq>_<event_hash>`

**Hash Input:**
```python
hash_input = f"{session_id}:{event_seq}:{event_type}:{event_data}"
event_id = f"event_{session_id}_{event_seq:06d}_{sha256(hash_input)[:8]}"
```

**Example:**
```
event_session001_000001_a3f2b8c4  # First event in session
event_session001_000042_7d4e9a12  # 42nd event in session
```

**Rationale:**
- Sequential event IDs for replay ordering
- Event hash enables integrity verification
- Session scoping isolates event logs

**Open Questions:**
- Q10: Are event IDs truly deterministic, or do they include random elements?
- Q11: How are branching timelines handled (save/load)?
- Q12: Do events reference each other (parent/child)?

---

### 5. Prep Job IDs

**Format:** `prepjob_<campaign_id>_<job_type>_<content_hash>`

**Hash Input:**
```python
hash_input = f"{campaign_id}:{job_type}:{job_params}"
job_id = f"prepjob_{campaign_id}_{job_type}_{sha256(hash_input)[:8]}"
```

**Example:**
```
prepjob_camp001_scaffold_a3f2b8c4  # Campaign scaffold job
prepjob_camp001_portrait_7d4e9a12  # Portrait generation job
```

**Rationale:**
- Job type prefix enables filtering and querying
- Content hash enables idempotency (same params = same job ID)
- Campaign scoping isolates prep work

**Open Questions:**
- Q13: Are prep jobs truly idempotent, or can they run multiple times?
- Q14: How are failed prep jobs retried?
- Q15: Do prep jobs reference each other (dependency DAG)?

---

### 6. Campaign IDs

**Format:** `camp_<user_id>_<campaign_hash>`

**Hash Input:**
```python
hash_input = f"{user_id}:{campaign_title}:{creation_timestamp}"
campaign_id = f"camp_{user_id[:8]}_{sha256(hash_input)[:8]}"
```

**Example:**
```
camp_user001_a3f2b8c4  # User 001's campaign
camp_user042_7d4e9a12  # User 042's campaign
```

**Rationale:**
- User scoping prevents cross-user collisions
- Title + timestamp hash ensures uniqueness
- Short enough for human use

**Open Questions:**
- Q16: Are user IDs also deterministic, or are they external (e.g., Steam ID)?
- Q17: Can campaigns be forked/cloned?
- Q18: How are multi-user campaigns handled?

---

## Collision Resistance

### Hash Truncation Analysis

**SHA-256 truncated to 8 characters (32 bits):**
- Collision probability: ~1 in 4.3 billion per ID type
- Expected collisions: negligible for <100k entities per campaign

**SHA-256 truncated to 16 characters (64 bits):**
- Collision probability: ~1 in 18.4 quintillion per ID type
- Expected collisions: effectively zero for any realistic campaign

**Recommendation:** Use **8-char hashes for most IDs**, **16-char for critical IDs** (campaign, session).

**Open Questions:**
- Q19: What is the target max entities per campaign? (10k? 100k? 1M?)
- Q20: Should collision detection be automated?

---

## Reserved Prefixes

To prevent future conflicts, reserve the following prefixes:

| Prefix | Purpose | Status |
|--------|---------|--------|
| `entity_` | Player/NPC/monster entities | REQUIRED |
| `asset_` | Generated assets (images, audio) | REQUIRED |
| `session_` | Game sessions | REQUIRED |
| `event_` | Event log entries | REQUIRED |
| `prepjob_` | Prep phase jobs | REQUIRED |
| `camp_` | Campaign IDs | REQUIRED |
| `user_` | User IDs | RESERVED |
| `shared_` | Shared cache assets | RESERVED |
| `template_` | Asset templates | RESERVED |
| `rule_` | Rule source references | RESERVED |
| `spell_` | Spell definitions | RESERVED |
| `feat_` | Feat definitions | RESERVED |
| `item_` | Item definitions | RESERVED |

**Open Questions:**
- Q21: Are rule/spell/feat/item IDs needed, or do they use external IDs (e.g., SRD references)?

---

## Migration Path from Current Code

### Current State (From Codebase Audit)

**Entity IDs:**
- Used as dict keys in `WorldState.entities`
- Appear to be strings (e.g., `"fighter"`, `"goblin_1"`)
- No enforced format

**Asset IDs:**
- Used in `AssetRecord.asset_id`
- Generated via `compute_asset_id(campaign_id, asset_type, asset_key)`
- Uses SHA-256 hash, truncated to 16 chars

**Campaign IDs:**
- Used in `CampaignManifest.campaign_id`
- No enforced format visible

**Event IDs:**
- Used in `EventLog` (monotonic sequence)
- Integer-based, not hash-based

### Proposed Migration Strategy

**Phase 1: Document existing patterns**
- Audit all current ID generation sites
- Document edge cases and collision risks
- Identify migration blockers

**Phase 2: Implement canonical schema**
- Add `aidm/schemas/canonical_ids.py` with ID generation functions
- Add validation helpers (e.g., `is_valid_entity_id()`)
- Add tests for determinism and collision resistance

**Phase 3: Gradual migration**
- Migrate new code to canonical schema
- Add compatibility layer for legacy IDs
- Deprecate legacy patterns

**Phase 4: Remove legacy IDs**
- Complete migration (CP-002 or later)
- Remove compatibility layer

**Open Questions:**
- Q22: Are there existing campaigns that would break with new ID schema?
- Q23: Can migration happen incrementally, or must it be atomic?

---

## Integration with Indexed Memory

**Requirement:** Indexed memory requires stable, queryable IDs.

**Implications:**
- Entity IDs must be **stable** across sessions (same entity = same ID)
- Asset IDs must be **content-addressed** (same content = same ID)
- Session IDs must be **unique** but **deterministic** (replay-safe)

**Open Questions:**
- Q24: How does indexed memory handle entity renames?
- Q25: How are deleted entities handled in the index?
- Q26: Can IDs be aliased (e.g., "Theron" → `entity_camp001_a3f2b8c4`)?

---

## Integration with Prep Pipeline

**Requirement:** Prep jobs must be **idempotent** (same params = same job ID).

**Implications:**
- Prep job IDs must be **content-addressed** (hash of params)
- Assets must be **deduplicatable** (same semantic_key = same asset)
- Shared cache must use **stable IDs** (cross-campaign references)

**Open Questions:**
- Q27: Can prep jobs be retried with different params (e.g., "regenerate portrait with better quality")?
- Q28: How are versioned assets handled (v1, v2, v3)?

---

## Compatibility with Determinism

**Requirement:** IDs must be deterministic for replay.

**Guarantees:**
- Same campaign + same entity → same entity ID ✓
- Same session + same event sequence → same event IDs ✓
- Same prep params → same prep job ID ✓

**Risks:**
- **Timestamp-based IDs break determinism** (current session IDs use timestamps?)
- **Sequential counters break parallelism** (prep jobs can't run in parallel if IDs are sequential)

**Open Questions:**
- Q29: Are there any non-deterministic ID sources in the current codebase?
- Q30: How are IDs generated in parallel contexts (e.g., multi-threaded prep)?

---

## Next Steps (R0 Research Phase)

### Validation Required

1. **Audit current codebase** for all ID generation sites
2. **Identify collision risks** in existing ID patterns
3. **Prototype canonical ID generators** and benchmark performance
4. **Test determinism** (10× generation = 10× same IDs)
5. **Validate integration** with indexed memory, prep pipeline, asset store

### Open Questions to Resolve

30 open questions identified in this draft. Priority resolution order:

**Critical (blocks M0):**
- Q1, Q4, Q7, Q10, Q19, Q22, Q29

**Important (affects architecture):**
- Q2, Q5, Q8, Q11, Q13, Q16, Q21, Q24, Q27

**Optional (clarifications):**
- Q3, Q6, Q9, Q12, Q14, Q15, Q17, Q18, Q20, Q23, Q25, Q26, Q28, Q30

---

## Appendix: Example ID Generation Code (Illustrative, Not Final)

```python
import hashlib

def generate_entity_id(campaign_id: str, entity_type: str, canonical_name: str) -> str:
    """Generate deterministic entity ID.

    Example:
        generate_entity_id("camp001", "npc", "Theron")
        -> "entity_camp001_a3f2b8c4"
    """
    hash_input = f"{campaign_id}:{entity_type}:{canonical_name}"
    hash_bytes = hashlib.sha256(hash_input.encode('utf-8')).digest()
    hash_hex = hash_bytes.hex()[:8]
    return f"entity_{campaign_id}_{hash_hex}"

def generate_asset_id(campaign_id: str, asset_type: str, semantic_key: str) -> str:
    """Generate deterministic asset ID.

    Example:
        generate_asset_id("camp001", "portrait", "npc:theron:v1")
        -> "asset_camp001_portrait_7d4e9a12"
    """
    hash_input = f"{campaign_id}:{asset_type}:{semantic_key}"
    hash_bytes = hashlib.sha256(hash_input.encode('utf-8')).digest()
    hash_hex = hash_bytes.hex()[:8]
    return f"asset_{campaign_id}_{asset_type}_{hash_hex}"

def generate_session_id(campaign_id: str, session_number: int, start_timestamp: str) -> str:
    """Generate deterministic session ID.

    Example:
        generate_session_id("camp001", 1, "2026-02-10T14:30:00")
        -> "session_camp001_0001_f1c3d8a6"
    """
    hash_input = f"{campaign_id}:{session_number}:{start_timestamp}"
    hash_bytes = hashlib.sha256(hash_input.encode('utf-8')).digest()
    hash_hex = hash_bytes.hex()[:8]
    return f"session_{campaign_id}_{session_number:04d}_{hash_hex}"
```

**Note:** This is illustrative only. Actual implementation requires validation, tests, and integration with existing ID generation in `aidm/schemas/campaign.py`.

---

## References

- Global Plan Audit: `docs/analysis/GLOBAL_AUDIT_GAP_AND_RISK_REGISTER.md` (Blocker #1: Canonical ID schema undefined)
- Current Implementation: `aidm/schemas/campaign.py::compute_asset_id()` (SHA-256, 16-char truncation)
- Design Insight: `docs/analysis/GLOBAL_AUDIT_CONSISTENCY_AUDIT.md` (Orphaned: ID stability for indexed memory)

---

**END OF DRAFT** — R0 validation required before use.

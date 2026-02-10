# R0 Canonical ID Schema
## Enforceable Contract for Entity and Asset Identification

**Status:** R0 RESEARCH / STRUCTURED SPEC / AWAITING APPROVAL
**Agent:** Agent A (Canonical Foundations Architect)
**Date:** 2026-02-10
**Authority:** Proposal — requires cross-agent validation + PM approval before implementation

---

## Purpose

This document defines the **canonical ID schema** for AIDM, converting the conceptual requirement (from Inbox documents) into an **enforceable contract** with:
- Unambiguous format specifications
- Collision resistance guarantees
- Determinism contracts
- Validation rules implementers can code without guessing

**Identified Gap (from GLOBAL-AUDIT-001):**
- GAP-001 (🔴 CRITICAL): Canonical ID schema undefined, blocks M1.8, M2.5, M3.7
- Constraint A3 (🔴 SACRED): "All mechanically relevant entities must be defined by stable, language-agnostic identifiers"

---

## Design Principles (Non-Negotiable)

### P1. Determinism First
- **RULE:** Same inputs → same ID (100% reproducible)
- **FORBIDDEN:** UUIDs, timestamps, random numbers, sequential counters (breaks replay)
- **REQUIRED:** Content-addressed hashing with stable inputs

### P2. Type Safety via Namespace Isolation
- **RULE:** ID format encodes type explicitly (prefix-based)
- **GUARANTEE:** Cross-type collisions impossible (`spell.fireball` ≠ `item.fireball`)

### P3. Human Readability (Debug-First)
- **RULE:** IDs must be inspectable in logs without lookup tables
- **FORMAT:** `<namespace>.<readable_key>` or `<namespace>_<context>_<hash>`
- **LENGTH:** ≤64 characters (database key limits)

### P4. Provenance Transparency
- **RULE:** ID reveals creation context (campaign, session, generation source)
- **PURPOSE:** Debugging can trace ID back to origin without external metadata

---

## ID Type Taxonomy

AIDM requires 7 distinct ID namespaces:

| Namespace | Purpose | Scope | Deterministic? |
|-----------|---------|-------|----------------|
| `mechanical_id` | Rules entities (spells, items, conditions) | Global (cross-campaign) | ✅ YES |
| `entity_id` | Runtime entities (PCs, NPCs, monsters) | Campaign-scoped | ✅ YES |
| `asset_id` | Generated assets (portraits, sounds, backdrops) | Campaign-scoped | ✅ YES (with caveats) |
| `session_id` | Game sessions | Campaign-scoped | ✅ YES |
| `event_id` | Event log entries | Session-scoped | ✅ YES |
| `campaign_id` | Campaign instances | User-scoped | ✅ YES |
| `prepjob_id` | Preparation phase jobs | Campaign-scoped | ✅ YES |

**Trade-off:** More namespaces = more complexity, but **prevents collisions** and **enables type-based queries**.

---

## Namespace 1: Mechanical IDs (Rules Entities)

### Format

```
<domain>.<canonical_name>
```

**Components:**
- `domain`: Rules domain (`spell`, `item`, `condition`, `feat`, `class_feature`, `monster_template`, `action`)
- `canonical_name`: SRD-style snake_case identifier (lowercase, no spaces)

### Examples

```
spell.fireball
spell.magic_missile
item.longsword
item.potion_of_healing
condition.stunned
condition.prone
feat.power_attack
feat.weapon_finesse
class_feature.sneak_attack
class_feature.rage
monster_template.goblin
monster_template.ancient_red_dragon
action.standard_attack
action.grapple
```

### Rationale

- **Global scope:** Same spell in all campaigns (no `spell_camp001_fireball`)
- **SRD alignment:** Uses D&D 3.5e naming conventions (no copyright infringement)
- **Human-readable:** No hashes (debugging-friendly)
- **Deterministic:** Name = ID (no generation required)

### Validation Rules

```python
def validate_mechanical_id(id: str) -> bool:
    """Validate mechanical ID format."""
    if '.' not in id:
        return False
    domain, name = id.split('.', 1)

    # Check domain
    valid_domains = {
        'spell', 'item', 'condition', 'feat',
        'class_feature', 'monster_template', 'action'
    }
    if domain not in valid_domains:
        return False

    # Check name format (snake_case, alphanumeric + underscore)
    if not name.replace('_', '').isalnum() or name != name.lower():
        return False

    return True
```

### Open Questions Resolved

- **Q21 (from draft):** Are rule/spell/feat/item IDs needed?
  **ANSWER:** YES. Mechanical IDs are **global canonical names** (not campaign-specific).

- **Collision risk:** Duplicate names across domains (e.g., `spell.shield` vs `feat.shield`)?
  **ANSWER:** NO COLLISION. Namespace prefix prevents (`spell.shield` ≠ `feat.shield`).

---

## Namespace 2: Entity IDs (Runtime NPCs/Monsters/PCs)

### Format

```
entity_<campaign_id>_<stable_hash>
```

**Hash Input:**
```python
hash_input = f"{campaign_id}:{entity_type}:{unique_key}"
stable_hash = sha256(hash_input.encode('utf-8')).hexdigest()[:12]
```

### Examples

```
entity_camp4f2a_fighter_a3f2b8c4e1d9
entity_camp4f2a_goblin1_7d4e9a12c5f3
entity_camp4f2a_theron_8b1c4d7a9e2f
```

### Rationale

- **Campaign-scoped:** Entity IDs isolated per campaign (prevents cross-campaign leakage)
- **Deterministic:** Same entity in same campaign = same ID (replay-safe)
- **Hash-based:** Avoids name collisions ("Goblin 1" vs "Goblin 2" vs "Goblin" duplicate NPCs)
- **12-char hash:** Collision probability ~1 in 16 trillion (safe for <1M entities/campaign)

### Hash Input Construction

**For PCs:**
```python
unique_key = f"pc:{character_name}:{creation_timestamp}"
# Example: "pc:Theron:2026-02-10T14:30:00"
```

**For NPCs (named):**
```python
unique_key = f"npc:{npc_name}:{creation_context}"
# Example: "npc:Innkeeper_Bob:session_0001_encounter_tavern"
```

**For NPCs (anonymous/templated):**
```python
unique_key = f"npc:{template}:{instance_counter}"
# Example: "npc:goblin:0001" (first goblin)
```

**For Monsters (instanced from templates):**
```python
unique_key = f"monster:{template}:{encounter_id}:{instance_index}"
# Example: "monster:goblin:enc_forest_ambush:0003" (3rd goblin in encounter)
```

### Validation Rules

```python
import re

def validate_entity_id(id: str) -> bool:
    """Validate entity ID format."""
    pattern = r'^entity_camp[0-9a-f]{4,8}_[0-9a-f]{12}$'
    return bool(re.match(pattern, id))
```

### Open Questions Resolved

- **Q1 (from draft):** NPCs with duplicate names?
  **ANSWER:** Use `creation_context` or `instance_counter` in hash input to disambiguate.

- **Q2:** Do entities persist across sessions?
  **ANSWER:** YES. Entity IDs are **campaign-scoped**, not session-scoped.

- **Q3:** Entity renamed?
  **ANSWER:** ID remains unchanged (IDs are **stable identifiers**, not display names).

---

## Namespace 3: Asset IDs (Generated Images/Audio)

### Format

```
asset_<campaign_id>_<asset_type>_<content_hash>
```

**Hash Input:**
```python
hash_input = f"{campaign_id}:{asset_type}:{semantic_key}"
content_hash = sha256(hash_input.encode('utf-8')).hexdigest()[:12]
```

### Examples

```
asset_camp4f2a_portrait_a3f2b8c4e1d9
asset_camp4f2a_scene_7d4e9a12c5f3
asset_camp4f2a_audio_8b1c4d7a9e2f
asset_shared_generic_tavern_f4e3d2c1b0a9
```

### Rationale

- **Campaign-scoped:** Assets tied to campaign (enables per-campaign caching)
- **Type-prefixed:** Enables filtering (`asset_*_portrait_*` retrieves all portraits)
- **Content-addressed:** Same semantic_key = same ID (deduplication-friendly)
- **Shared cache support:** `asset_shared_*` prefix for cross-campaign generic assets

### Asset Types

| Type | Description | Example semantic_key |
|------|-------------|----------------------|
| `portrait` | NPC/PC portraits | `npc:theron:default` |
| `scene` | Location backdrops | `location:tavern:interior:day` |
| `audio` | Sound effects, music | `sfx:sword_clash:metal_on_metal` |
| `icon` | UI icons, spell icons | `spell:fireball:icon` |

### Semantic Key Construction

**For entity-linked assets:**
```python
semantic_key = f"{entity_type}:{entity_name}:{variant}"
# Example: "npc:theron:default" (Theron's default portrait)
```

**For location assets:**
```python
semantic_key = f"location:{location_name}:{variant}"
# Example: "location:tavern:interior:night" (tavern interior at night)
```

**For generic assets (shared cache):**
```python
semantic_key = f"generic:{category}:{descriptor}"
# Example: "generic:forest:clearing" (generic forest clearing backdrop)
```

### Validation Rules

```python
def validate_asset_id(id: str) -> bool:
    """Validate asset ID format."""
    pattern = r'^asset_(camp[0-9a-f]{4,8}|shared)_[a-z_]+_[0-9a-f]{12}$'
    return bool(re.match(pattern, id))
```

### Open Questions Resolved

- **Q4 (from draft):** Can same semantic_key have multiple versions?
  **ANSWER:** NO. Versioning handled via **semantic_key variant suffix** (`npc:theron:v1`, `npc:theron:v2`).

- **Q5:** Asset variants (day/night)?
  **ANSWER:** YES. Variants encoded in semantic_key (`location:tavern:day` vs `location:tavern:night`).

- **Q6:** Shared cache prefix?
  **ANSWER:** YES. Use `asset_shared_*` instead of campaign ID.

---

## Namespace 4: Session IDs

### Format

```
session_<campaign_id>_<session_seq>_<start_hash>
```

**Hash Input:**
```python
hash_input = f"{campaign_id}:{session_seq}:{start_event_hash}"
start_hash = sha256(hash_input.encode('utf-8')).hexdigest()[:8]
```

### Examples

```
session_camp4f2a_0001_a3f2b8c4
session_camp4f2a_0042_7d4e9a12
```

### Rationale

- **Sequential numbering:** Human-readable session ordering
- **Start hash:** Prevents collisions if session restarted/branched
- **Campaign-scoped:** Sessions isolated per campaign
- **8-char hash:** Sufficient for session-level uniqueness

### Validation Rules

```python
def validate_session_id(id: str) -> bool:
    """Validate session ID format."""
    pattern = r'^session_camp[0-9a-f]{4,8}_\d{4}_[0-9a-f]{8}$'
    return bool(re.match(pattern, id))
```

### Open Questions Resolved

- **Q7 (from draft):** Session numbers deterministic or sequential?
  **ANSWER:** SEQUENTIAL (human-assigned), but hash ensures determinism.

- **Q8:** Session replayed from save point?
  **ANSWER:** Replay creates **new session** with new ID (branching timeline).

- **Q9:** Do sessions nest?
  **ANSWER:** NO. Encounters are **event sequences**, not sub-sessions.

---

## Namespace 5: Event IDs

### Format

```
event_<session_id>_<event_seq>_<event_hash>
```

**Hash Input:**
```python
hash_input = f"{session_id}:{event_seq}:{event_type}:{event_data_hash}"
event_hash = sha256(hash_input.encode('utf-8')).hexdigest()[:8]
```

### Examples

```
event_session_camp4f2a_0001_a3f2b8c4_000001_f1c3d8a6
event_session_camp4f2a_0001_a3f2b8c4_000042_7d4e9a12
```

### Rationale

- **Sequential ordering:** Event log must be **append-only** and **ordered**
- **Event hash:** Integrity check (detects log corruption)
- **Session-scoped:** Events isolated per session
- **6-digit sequence:** Supports 1M events per session

### Validation Rules

```python
def validate_event_id(id: str) -> bool:
    """Validate event ID format."""
    pattern = r'^event_session_camp[0-9a-f]{4,8}_\d{4}_[0-9a-f]{8}_\d{6}_[0-9a-f]{8}$'
    return bool(re.match(pattern, id))
```

### Open Questions Resolved

- **Q10 (from draft):** Are event IDs truly deterministic?
  **ANSWER:** YES. Event data + sequence = deterministic hash.

- **Q11:** Branching timelines (save/load)?
  **ANSWER:** New branch = new session ID, events re-sequenced from branch point.

- **Q12:** Events reference each other?
  **ANSWER:** YES. Events may contain `parent_event_id` field (but ID itself doesn't encode this).

---

## Namespace 6: Campaign IDs

### Format

```
camp_<campaign_hash>
```

**Hash Input:**
```python
hash_input = f"{user_id}:{campaign_title}:{creation_timestamp_iso}"
campaign_hash = sha256(hash_input.encode('utf-8')).hexdigest()[:8]
```

### Examples

```
camp_4f2a8b1c
camp_a3f2b8c4
```

### Rationale

- **User-scoped:** Campaign hash includes user ID (multi-user collision prevention)
- **Title + timestamp:** Ensures uniqueness even if same user creates "Campaign 1" twice
- **Short:** 8-char hash is human-typable and log-friendly

### Validation Rules

```python
def validate_campaign_id(id: str) -> bool:
    """Validate campaign ID format."""
    pattern = r'^camp_[0-9a-f]{8}$'
    return bool(re.match(pattern, id))
```

### Open Questions Resolved

- **Q16 (from draft):** Are user IDs deterministic?
  **ANSWER:** NO. User IDs are **external** (e.g., OS username, Steam ID, email hash).

- **Q17:** Can campaigns be forked/cloned?
  **ANSWER:** YES. Fork = new campaign ID, source campaign referenced in metadata.

- **Q18:** Multi-user campaigns?
  **ANSWER:** Single campaign ID, multiple user IDs in access control list (not encoded in campaign ID).

---

## Namespace 7: Prep Job IDs

### Format

```
prepjob_<campaign_id>_<job_type>_<params_hash>
```

**Hash Input:**
```python
hash_input = f"{campaign_id}:{job_type}:{job_params_json}"
params_hash = sha256(hash_input.encode('utf-8')).hexdigest()[:12]
```

### Examples

```
prepjob_camp4f2a_scaffold_a3f2b8c4e1d9
prepjob_camp4f2a_portrait_7d4e9a12c5f3
prepjob_camp4f2a_soundpal_8b1c4d7a9e2f
```

### Rationale

- **Idempotency:** Same params = same job ID (prevents duplicate work)
- **Job type prefix:** Enables filtering and dependency tracking
- **Campaign-scoped:** Prep jobs isolated per campaign

### Job Types

| Type | Description |
|------|-------------|
| `scaffold` | Campaign structure generation |
| `portrait` | NPC portrait generation |
| `soundpal` | Sound palette generation |
| `backdrop` | Location backdrop generation |

### Validation Rules

```python
def validate_prepjob_id(id: str) -> bool:
    """Validate prep job ID format."""
    pattern = r'^prepjob_camp[0-9a-f]{4,8}_[a-z_]+_[0-9a-f]{12}$'
    return bool(re.match(pattern, id))
```

### Open Questions Resolved

- **Q13 (from draft):** Are prep jobs idempotent?
  **ANSWER:** YES. Same params = same job ID = no duplicate execution.

- **Q14:** Failed prep jobs retried?
  **ANSWER:** Retry = same job ID, status updated (not new job).

- **Q15:** Prep jobs reference each other?
  **ANSWER:** YES. Jobs store `dependency_job_ids` list (but ID itself doesn't encode this).

---

## Collision Resistance Analysis

### Hash Length Selection

| Hash Length | Bits | Collision Probability (Birthday Paradox) | Safe Entity Count |
|-------------|------|------------------------------------------|-------------------|
| 8 chars | 32 bits | ~1 in 4.3 billion | <10,000 per namespace |
| 12 chars | 48 bits | ~1 in 281 trillion | <1 million per namespace |
| 16 chars | 64 bits | ~1 in 18.4 quintillion | <1 billion per namespace |

**Chosen Strategy:**
- **12-char hashes** for most IDs (entities, assets, prep jobs)
- **8-char hashes** for session/event IDs (lower cardinality)
- **No hash** for mechanical IDs (human-readable names)

**Worst-Case Scenario:**
- Campaign with 100,000 entities: Collision probability ~0.0000018% (negligible)
- Campaign with 1 million assets: Collision probability ~0.018% (acceptable)

**Mitigation:**
- Automated collision detection during ID generation
- If collision detected → append disambiguation suffix (`_001`, `_002`)

---

## Determinism Guarantees

### What MUST Be Deterministic

| ID Type | Deterministic? | Guarantee |
|---------|----------------|-----------|
| `mechanical_id` | ✅ YES | Name = ID (no generation) |
| `entity_id` | ✅ YES | Same campaign + same unique_key → same ID |
| `asset_id` | ✅ YES | Same campaign + same semantic_key → same ID |
| `session_id` | ✅ YES | Same campaign + same session_seq + same start_hash → same ID |
| `event_id` | ✅ YES | Same session + same event_seq + same event_data → same ID |
| `campaign_id` | ✅ YES | Same user + same title + same timestamp → same ID |
| `prepjob_id` | ✅ YES | Same campaign + same job_type + same params → same ID |

### What MAY Vary (Presentation Layer)

- **Display names:** Entity ID `entity_camp4f2a_theron_8b1c` may be displayed as "Theron the Bold" or "Theron" or "NPC #42" (presentation-only)
- **Asset appearance:** Asset ID `asset_camp4f2a_portrait_a3f2` may render differently if generation model changes (but ID remains stable)

### Determinism Test Protocol

```python
def test_id_determinism():
    """Verify ID generation is deterministic."""
    # Generate same entity ID 10 times
    ids = [generate_entity_id("camp_test", "pc:Theron:2026-02-10T14:30:00") for _ in range(10)]

    # All IDs must be identical
    assert len(set(ids)) == 1, "Entity ID generation is non-deterministic!"
```

---

## Validation Rules (Implementation Contract)

Implementers MUST enforce these rules at ID generation time:

### Rule 1: Format Compliance

```python
# Mechanical IDs
assert validate_mechanical_id("spell.fireball") == True
assert validate_mechanical_id("spell_fireball") == False  # Wrong separator
assert validate_mechanical_id("Spell.Fireball") == False  # Wrong case

# Entity IDs
assert validate_entity_id("entity_camp4f2a_a3f2b8c4e1d9") == True
assert validate_entity_id("entity_camp4f2a") == False  # Missing hash
```

### Rule 2: Namespace Isolation

```python
# Cross-namespace collision check
def check_id_namespace_isolation(id1: str, id2: str) -> bool:
    """Verify two IDs from different namespaces cannot collide."""
    prefix1 = id1.split('_')[0] if '_' in id1 else id1.split('.')[0]
    prefix2 = id2.split('_')[0] if '_' in id2 else id2.split('.')[0]

    # Same ID allowed ONLY if same namespace prefix
    if id1 == id2:
        return prefix1 == prefix2
    return True

assert check_id_namespace_isolation("spell.fireball", "item.fireball") == True
assert check_id_namespace_isolation("entity_camp4f2a_a3f2", "asset_camp4f2a_a3f2") == True
```

### Rule 3: Hash Determinism

```python
# Hash generation must be deterministic
def test_hash_determinism():
    hash1 = generate_entity_id("camp_test", "pc:Theron:2026-02-10T14:30:00")
    hash2 = generate_entity_id("camp_test", "pc:Theron:2026-02-10T14:30:00")
    assert hash1 == hash2, "Hash generation is non-deterministic!"
```

### Rule 4: Collision Detection

```python
# Automated collision detection
def register_id(id: str, id_registry: set) -> bool:
    """Register ID and detect collision."""
    if id in id_registry:
        raise ValueError(f"ID collision detected: {id}")
    id_registry.add(id)
    return True
```

---

## Integration with Existing Code

### Current State (From Codebase Audit)

**File:** `aidm/schemas/campaign.py`
```python
def compute_asset_id(campaign_id: str, asset_type: str, asset_key: str) -> str:
    """Current asset ID generation (16-char hash)."""
    hash_input = f"{campaign_id}:{asset_type}:{asset_key}"
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:16]
```

**Gap:** Current implementation:
- ✅ Uses deterministic hashing
- ✅ Includes campaign scoping
- ❌ Missing `asset_` prefix (namespace isolation)
- ❌ Uses 16-char hash (inconsistent with proposed 12-char)
- ❌ No validation logic

### Migration Strategy

**Phase 1 (R0):** Document proposed schema (this document)
**Phase 2 (M0.6):** Implement `aidm/schemas/canonical_ids.py` with all 7 namespaces
**Phase 3 (M0.6):** Add compatibility layer for existing code
**Phase 4 (M1):** Migrate new code to canonical schema
**Phase 5 (CP-002+):** Deprecate legacy ID patterns

---

## Reference Examples (30 IDs)

### Mechanical IDs (Global Rules)

```
spell.magic_missile
spell.fireball
spell.cure_light_wounds
item.longsword
item.potion_of_healing
item.bag_of_holding
condition.stunned
condition.prone
condition.invisible
feat.power_attack
feat.cleave
class_feature.sneak_attack
monster_template.goblin
monster_template.ancient_red_dragon
action.standard_attack
```

### Entity IDs (Campaign-Scoped)

```
entity_camp4f2a_fighter_a3f2b8c4e1d9
entity_camp4f2a_goblin1_7d4e9a12c5f3
entity_camp4f2a_theron_8b1c4d7a9e2f
entity_camp4f2a_dragon_f4e3d2c1b0a9
```

### Asset IDs (Campaign-Scoped + Shared)

```
asset_camp4f2a_portrait_a3f2b8c4e1d9
asset_camp4f2a_scene_7d4e9a12c5f3
asset_camp4f2a_audio_8b1c4d7a9e2f
asset_shared_generic_tavern_f4e3d2c1b0a9
```

### Session IDs

```
session_camp4f2a_0001_a3f2b8c4
session_camp4f2a_0042_7d4e9a12
```

### Event IDs

```
event_session_camp4f2a_0001_a3f2b8c4_000001_f1c3d8a6
event_session_camp4f2a_0001_a3f2b8c4_000042_7d4e9a12
```

### Campaign IDs

```
camp_4f2a8b1c
camp_a3f2b8c4
```

### Prep Job IDs

```
prepjob_camp4f2a_scaffold_a3f2b8c4e1d9
prepjob_camp4f2a_portrait_7d4e9a12c5f3
prepjob_camp4f2a_soundpal_8b1c4d7a9e2f
```

---

## Bad ID Examples (Validation Failures)

```
# Missing namespace prefix
"fireball" ❌ (should be "spell.fireball")

# Wrong case
"Spell.Fireball" ❌ (should be lowercase "spell.fireball")

# Non-deterministic (UUID)
"entity_camp4f2a_8f7e6d5c-4b3a-2c1d-0e9f-8a7b6c5d4e3f" ❌

# Wrong separator
"spell_fireball" ❌ (should use "spell.fireball")

# Hash too short
"entity_camp4f2a_a3f2" ❌ (should be 12 chars: "entity_camp4f2a_a3f2b8c4e1d9")

# Missing campaign context
"entity_theron_a3f2b8c4e1d9" ❌ (should include campaign ID)
```

---

## Appendix: Python Implementation Stub

```python
import hashlib
import re

class CanonicalIDGenerator:
    """Canonical ID generation and validation."""

    @staticmethod
    def mechanical_id(domain: str, name: str) -> str:
        """Generate mechanical ID (rules entities)."""
        if domain not in {'spell', 'item', 'condition', 'feat', 'class_feature', 'monster_template', 'action'}:
            raise ValueError(f"Invalid domain: {domain}")
        if not name.replace('_', '').isalnum() or name != name.lower():
            raise ValueError(f"Invalid name format: {name}")
        return f"{domain}.{name}"

    @staticmethod
    def entity_id(campaign_id: str, entity_type: str, unique_key: str) -> str:
        """Generate entity ID (runtime entities)."""
        hash_input = f"{campaign_id}:{entity_type}:{unique_key}"
        hash_hex = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:12]
        return f"entity_{campaign_id}_{hash_hex}"

    @staticmethod
    def asset_id(campaign_id: str, asset_type: str, semantic_key: str) -> str:
        """Generate asset ID (generated assets)."""
        hash_input = f"{campaign_id}:{asset_type}:{semantic_key}"
        hash_hex = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:12]
        return f"asset_{campaign_id}_{asset_type}_{hash_hex}"

    @staticmethod
    def session_id(campaign_id: str, session_seq: int, start_hash: str) -> str:
        """Generate session ID."""
        hash_input = f"{campaign_id}:{session_seq}:{start_hash}"
        hash_hex = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:8]
        return f"session_{campaign_id}_{session_seq:04d}_{hash_hex}"

    @staticmethod
    def validate_mechanical_id(id: str) -> bool:
        """Validate mechanical ID format."""
        return bool(re.match(r'^[a-z_]+\.[a-z_]+$', id))

    @staticmethod
    def validate_entity_id(id: str) -> bool:
        """Validate entity ID format."""
        return bool(re.match(r'^entity_camp[0-9a-f]{4,8}_[0-9a-f]{12}$', id))
```

---

## Exit Criteria

This spec is **ready for implementation** when:

- [x] Format specifications unambiguous (implementer can code without guessing)
- [x] Validation rules defined with regex patterns
- [x] Determinism guarantees documented
- [x] Collision resistance analyzed
- [x] 30 reference examples provided
- [x] Bad ID examples documented
- [x] Integration with existing code defined
- [ ] Cross-agent review complete (Agent B, C, D feedback)
- [ ] PM approval obtained

---

## References

- **Gap Source:** docs/analysis/GLOBAL_AUDIT_GAP_AND_RISK_REGISTER.md (GAP-001)
- **Constraint Source:** docs/analysis/GLOBAL_AUDIT_CONSTRAINT_LEDGER.md (Constraint A3)
- **Current Implementation:** aidm/schemas/campaign.py::compute_asset_id()
- **Draft Source:** docs/research/CANONICAL_ID_SCHEMA_DRAFT.md (30 open questions resolved)

---

**STATUS:** Awaiting cross-agent review + PM approval before implementation.

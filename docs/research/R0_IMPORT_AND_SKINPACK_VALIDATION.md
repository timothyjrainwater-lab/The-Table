# R0 Import and Skin Pack Validation
## Safety Rules, Validation Checks, and Rejection Criteria

**Status:** R0 RESEARCH / STRUCTURED SPEC / AWAITING APPROVAL
**Agent:** Agent A (Canonical Foundations Architect)
**Date:** 2026-02-10
**Authority:** Proposal — requires cross-agent validation + PM approval before implementation

---

## Purpose

This document defines **import safety rules** and **Skin Pack validation** to prevent:
- Mechanical smuggling (Skin Packs changing damage, range, or legality)
- Alias conflicts (ambiguous input mappings)
- Malicious payloads (code injection, resource exhaustion)
- Campaign corruption (invalid entity references)

**Sacred Constraint (from GLOBAL-AUDIT-001):**
- Constraint B1 (🟠 CRITICAL): "Skin Packs are declarative, validated, hot-swappable at presentation level. Skin Packs CANNOT alter mechanics, add modifiers, introduce new action legalities."

---

## Core Principle

### Separation: Presentation vs Mechanics

**AIDM Architecture:**
```
┌────────────────────────────────────┐
│ PRESENTATION LAYER                 │
│ (Skin Packs, Localization, Assets) │
│ ✅ CAN change: names, descriptions │
│ ✅ CAN change: tone, visuals       │
│ ❌ CANNOT change: damage, range    │
│ ❌ CANNOT change: action legality  │
└────────────────────────────────────┘
           ↓ decorates ↓
┌────────────────────────────────────┐
│ MECHANICAL LAYER                   │
│ (Canonical IDs, Rules, Engine)     │
│ - spell.fireball = 8d6 fire damage │
│ - item.longsword = 1d8 slashing    │
│ - Action legality rules            │
└────────────────────────────────────┘
```

**Enforcement:** Skin Packs are **decorators**, not **overrides**.

---

## Skin Pack Schema

### Structure

```json
{
    "skin_pack_id": "cyberpunk_reskin_v1",
    "version": "1.0.0",
    "author": "user_12345",
    "description": "Cyberpunk 2077-style reskin for D&D 3.5e",
    "base_ruleset": "dnd35e",
    "display_names": {
        "spell.fireball": "Plasma Grenade",
        "spell.magic_missile": "Auto-Targeting Nanobots",
        "item.longsword": "Monofilament Blade",
        "item.potion_of_healing": "Medkit"
    },
    "aliases": {
        "en": {
            "plasma grenade": "spell.fireball",
            "grenade": "spell.fireball",
            "nanobots": "spell.magic_missile",
            "blade": "item.longsword",
            "medkit": "item.potion_of_healing"
        },
        "es": {
            "granada de plasma": "spell.fireball",
            "nanobots": "spell.magic_missile"
        }
    },
    "descriptions": {
        "spell.fireball": {
            "short": "A plasma grenade detonates, incinerating all in its radius.",
            "long": "You throw a futuristic plasma grenade that explodes on impact..."
        }
    },
    "tone_constraints": {
        "genre": "cyberpunk",
        "tech_level": "high",
        "magic_flavor": "technology"
    },
    "visual_prompts": {
        "spell.fireball": "cyberpunk plasma explosion, neon orange glow, futuristic tech"
    },
    "audio_profiles": {
        "spell.fireball": {
            "sfx": "electronic_explosion_high_tech"
        }
    }
}
```

---

## Validation Rules (Enforceable)

### Rule 1: Canonical ID Integrity

**RULE:** All referenced canonical IDs MUST exist in the canonical ID registry.

**Check:**
```python
def validate_canonical_ids(skin_pack, id_registry):
    """Verify all referenced IDs exist."""
    for canonical_id in skin_pack['display_names'].keys():
        if canonical_id not in id_registry:
            raise ValidationError(f"Unknown canonical ID: {canonical_id}")

    for aliases in skin_pack['aliases'].values():
        for canonical_id in aliases.values():
            if canonical_id not in id_registry:
                raise ValidationError(f"Alias maps to unknown ID: {canonical_id}")
```

**Example Rejection:**
```json
// ❌ REJECTED
{
    "display_names": {
        "spell.ultimate_blast": "Nuclear Bomb"  // ID doesn't exist!
    }
}
```

---

### Rule 2: No Mechanical Changes

**RULE:** Skin Packs CANNOT contain fields that affect mechanics.

**Forbidden Fields:**
- `damage`
- `range`
- `area_of_effect`
- `duration`
- `saving_throw`
- `spell_resistance`
- `attack_bonus`
- `ac_modifier`
- `hp_modifier`
- `action_cost` (standard/move/swift/free)

**Check:**
```python
FORBIDDEN_FIELDS = {
    'damage', 'range', 'area_of_effect', 'duration', 'saving_throw',
    'spell_resistance', 'attack_bonus', 'ac_modifier', 'hp_modifier', 'action_cost'
}

def validate_no_mechanical_changes(skin_pack):
    """Reject Skin Packs with mechanical fields."""
    for entry in skin_pack.get('display_names', {}).values():
        if isinstance(entry, dict):  # If entry has nested data
            for field in entry.keys():
                if field in FORBIDDEN_FIELDS:
                    raise ValidationError(f"Forbidden mechanical field: {field}")
```

**Example Rejection:**
```json
// ❌ REJECTED
{
    "display_names": {
        "spell.fireball": {
            "name": "Plasma Grenade",
            "damage": "10d6"  // Attempting to change damage!
        }
    }
}
```

---

### Rule 3: Alias Conflict Detection

**RULE:** Aliases CANNOT map to multiple canonical IDs within the same language.

**Check:**
```python
def validate_alias_uniqueness(skin_pack):
    """Detect alias conflicts within each language."""
    for lang, aliases in skin_pack['aliases'].items():
        seen_aliases = {}
        for alias, canonical_id in aliases.items():
            if alias in seen_aliases:
                existing_id = seen_aliases[alias]
                if existing_id != canonical_id:
                    raise ValidationError(
                        f"Alias conflict in '{lang}': '{alias}' maps to both "
                        f"'{existing_id}' and '{canonical_id}'"
                    )
            seen_aliases[alias] = canonical_id
```

**Example Rejection:**
```json
// ❌ REJECTED
{
    "aliases": {
        "en": {
            "blade": "item.longsword",
            "blade": "item.dagger"  // Conflict! Same alias, different IDs
        }
    }
}
```

---

### Rule 4: Cross-Language Alias Consistency

**RULE:** The SAME alias in different languages SHOULD map to the SAME canonical ID (warning, not error).

**Check:**
```python
def check_cross_language_alias_consistency(skin_pack):
    """Warn if same alias maps to different IDs across languages."""
    alias_to_ids = {}  # alias_text → set of canonical IDs

    for lang, aliases in skin_pack['aliases'].items():
        for alias, canonical_id in aliases.items():
            if alias not in alias_to_ids:
                alias_to_ids[alias] = set()
            alias_to_ids[alias].add(canonical_id)

    # Warn if alias maps to multiple IDs
    for alias, ids in alias_to_ids.items():
        if len(ids) > 1:
            warnings.warn(
                f"Cross-language inconsistency: '{alias}' maps to {ids} in different languages"
            )
```

**Example Warning:**
```json
// ⚠️ WARNING (not rejected, but flagged)
{
    "aliases": {
        "en": {"blade": "item.longsword"},
        "es": {"blade": "item.dagger"}  // "blade" means different things!
    }
}
```

---

### Rule 5: Schema Version Compatibility

**RULE:** Skin Pack schema version MUST be compatible with engine version.

**Check:**
```python
SUPPORTED_SCHEMA_VERSIONS = ["1.0.0", "1.1.0"]

def validate_schema_version(skin_pack):
    """Verify Skin Pack uses supported schema version."""
    version = skin_pack.get('version', '0.0.0')
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValidationError(
            f"Unsupported schema version: {version}. "
            f"Supported versions: {SUPPORTED_SCHEMA_VERSIONS}"
        )
```

**Example Rejection:**
```json
// ❌ REJECTED
{
    "version": "2.0.0",  // Future schema version not supported
    ...
}
```

---

### Rule 6: Base Ruleset Compatibility

**RULE:** Skin Pack MUST declare compatible base ruleset.

**Check:**
```python
SUPPORTED_RULESETS = ["dnd35e"]

def validate_base_ruleset(skin_pack):
    """Verify Skin Pack is compatible with engine ruleset."""
    ruleset = skin_pack.get('base_ruleset', 'unknown')
    if ruleset not in SUPPORTED_RULESETS:
        raise ValidationError(
            f"Unsupported base ruleset: {ruleset}. "
            f"Supported rulesets: {SUPPORTED_RULESETS}"
        )
```

**Example Rejection:**
```json
// ❌ REJECTED
{
    "base_ruleset": "pathfinder2e",  // Different game system!
    ...
}
```

---

### Rule 7: Resource Limits (Malicious Payload Prevention)

**RULE:** Skin Packs MUST NOT exceed resource limits (prevents DoS).

**Limits:**
| Resource | Limit | Rationale |
|----------|-------|-----------|
| File size | 10 MB | Prevents bloat |
| Display names | 10,000 | Prevents memory exhaustion |
| Aliases per language | 50,000 | Prevents lookup table bloat |
| Description length | 10,000 chars | Prevents text spam |

**Check:**
```python
def validate_resource_limits(skin_pack, max_file_size_mb=10):
    """Enforce resource limits to prevent DoS."""
    # File size check (done at load time)
    # Display names count
    if len(skin_pack.get('display_names', {})) > 10000:
        raise ValidationError("Too many display names (limit: 10,000)")

    # Aliases count per language
    for lang, aliases in skin_pack.get('aliases', {}).items():
        if len(aliases) > 50000:
            raise ValidationError(f"Too many aliases in '{lang}' (limit: 50,000)")

    # Description length
    for desc in skin_pack.get('descriptions', {}).values():
        if isinstance(desc, dict):
            for text in desc.values():
                if len(text) > 10000:
                    raise ValidationError("Description too long (limit: 10,000 chars)")
```

---

### Rule 8: No Code Execution (Security)

**RULE:** Skin Packs MUST be pure data (JSON/YAML), NO executable code.

**Check:**
```python
def validate_no_code_execution(skin_pack):
    """Reject Skin Packs attempting code execution."""
    # Check for eval/exec patterns
    skin_pack_json = json.dumps(skin_pack)

    FORBIDDEN_PATTERNS = [
        'eval', 'exec', '__import__', 'compile',
        '<script>', 'javascript:', 'data:text/html'
    ]

    for pattern in FORBIDDEN_PATTERNS:
        if pattern in skin_pack_json.lower():
            raise SecurityError(f"Forbidden pattern detected: {pattern}")
```

**Example Rejection:**
```json
// ❌ REJECTED
{
    "display_names": {
        "spell.fireball": "<script>alert('XSS')</script>"  // Code injection attempt!
    }
}
```

---

## Campaign Import Validation

### Import Safety Checklist

**Before importing a campaign, validate:**

| Check | Purpose | Rejection Criteria |
|-------|---------|-------------------|
| **Manifest integrity** | Verify campaign manifest is well-formed | Missing required fields, schema errors |
| **Version compatibility** | Verify campaign was created with compatible engine version | Incompatible engine version |
| **Entity ID validity** | Verify all entity IDs follow canonical format | Invalid ID format, unknown namespace |
| **Event log integrity** | Verify event log is append-only, no gaps | Missing events, out-of-order events |
| **Asset references** | Verify all asset IDs exist (if Strategy B) | Missing assets |
| **Skin Pack validation** | Verify attached Skin Packs pass all validation rules | Any Skin Pack validation failure |

---

### Manifest Schema

```json
{
    "campaign_id": "camp_4f2a8b1c",
    "version": "1.0.0",
    "engine_version": "0.3.0-post-audit-m3",
    "created_at": "2026-02-10T14:30:00Z",
    "player_profile": {
        "experience_level": "experienced",
        "pacing": "balanced"
    },
    "skin_pack_id": "cyberpunk_reskin_v1",
    "entities": [
        "entity_camp4f2a_fighter_a3f2b8c4e1d9",
        "entity_camp4f2a_goblin1_7d4e9a12c5f3"
    ],
    "assets": [
        "asset_camp4f2a_portrait_a3f2b8c4e1d9",
        "asset_camp4f2a_scene_7d4e9a12c5f3"
    ],
    "event_log": "event_log.jsonl",
    "determinism_strategy": "asset_export"
}
```

---

### Validation Checks

#### Check 1: Manifest Integrity

```python
REQUIRED_MANIFEST_FIELDS = {
    'campaign_id', 'version', 'engine_version', 'created_at',
    'player_profile', 'entities', 'event_log'
}

def validate_manifest_integrity(manifest):
    """Verify manifest has all required fields."""
    missing_fields = REQUIRED_MANIFEST_FIELDS - set(manifest.keys())
    if missing_fields:
        raise ValidationError(f"Missing required fields: {missing_fields}")
```

---

#### Check 2: Version Compatibility

```python
COMPATIBLE_ENGINE_VERSIONS = ["0.3.0-post-audit-m3", "0.4.0"]

def validate_version_compatibility(manifest):
    """Verify campaign engine version is compatible."""
    engine_version = manifest['engine_version']
    if engine_version not in COMPATIBLE_ENGINE_VERSIONS:
        raise ValidationError(
            f"Incompatible engine version: {engine_version}. "
            f"Compatible versions: {COMPATIBLE_ENGINE_VERSIONS}"
        )
```

---

#### Check 3: Entity ID Validity

```python
from research.R0_CANONICAL_ID_SCHEMA import validate_entity_id

def validate_entity_ids(manifest):
    """Verify all entity IDs follow canonical format."""
    for entity_id in manifest['entities']:
        if not validate_entity_id(entity_id):
            raise ValidationError(f"Invalid entity ID format: {entity_id}")
```

---

#### Check 4: Event Log Integrity

```python
def validate_event_log_integrity(event_log):
    """Verify event log is append-only with no gaps."""
    prev_seq = -1
    for event in event_log:
        # Check sequential ordering
        if event['event_seq'] != prev_seq + 1:
            raise ValidationError(
                f"Event log gap: expected seq {prev_seq + 1}, got {event['event_seq']}"
            )
        prev_seq = event['event_seq']

        # Check event has required fields
        required_fields = {'event_id', 'event_type', 'event_seq', 'timestamp'}
        missing = required_fields - set(event.keys())
        if missing:
            raise ValidationError(f"Event missing required fields: {missing}")
```

---

#### Check 5: Asset References (Strategy B)

```python
def validate_asset_references(manifest, asset_files):
    """Verify all referenced assets exist (for asset export strategy)."""
    if manifest.get('determinism_strategy') == 'asset_export':
        for asset_id in manifest['assets']:
            asset_filename = f"{asset_id}.png"  # or .wav, .json, etc.
            if asset_filename not in asset_files:
                raise ValidationError(f"Missing asset file: {asset_filename}")
```

---

## Rejection Criteria Summary

### Critical Rejections (Import MUST Fail)

| Violation | Severity | Action |
|-----------|----------|--------|
| Mechanical field in Skin Pack | 🔴 CRITICAL | REJECT, log error |
| Unknown canonical ID | 🔴 CRITICAL | REJECT, log error |
| Alias conflict | 🔴 CRITICAL | REJECT, log error |
| Code execution attempt | 🔴 CRITICAL | REJECT, log security alert |
| Incompatible engine version | 🔴 CRITICAL | REJECT, suggest upgrade |
| Invalid entity ID format | 🔴 CRITICAL | REJECT, log error |
| Event log gap/corruption | 🔴 CRITICAL | REJECT, log error |

---

### Warnings (Import Succeeds with Notice)

| Issue | Severity | Action |
|-------|----------|--------|
| Cross-language alias inconsistency | 🟡 MEDIUM | ALLOW, log warning |
| Missing asset (Strategy A) | 🟡 MEDIUM | ALLOW, regenerate on-demand |
| Unsupported audio profile | 🟡 MEDIUM | ALLOW, fallback to default |
| Unknown tone constraint | 🟡 MEDIUM | ALLOW, ignore unknown field |

---

## Skin Pack Hot-Swap Rules

### When Can Skin Packs Be Changed?

**Safe to swap:**
- ✅ Between sessions (no active gameplay)
- ✅ During prep phase (before session start)

**FORBIDDEN to swap:**
- ❌ Mid-combat (causes UI/narration desync)
- ❌ During intent clarification (causes alias confusion)

**Enforcement:**
```python
def can_swap_skin_pack(game_state):
    """Check if Skin Pack swap is safe."""
    if game_state.in_combat:
        return False, "Cannot swap Skin Pack during combat"
    if game_state.intent_pending:
        return False, "Cannot swap Skin Pack during intent clarification"
    return True, "Safe to swap"
```

---

## Validation Test Harness

### Validation Test Suite

```python
def test_skin_pack_validation():
    """Test Skin Pack validation rules."""

    # Valid Skin Pack (should pass)
    valid_pack = {
        "skin_pack_id": "cyberpunk_reskin_v1",
        "version": "1.0.0",
        "base_ruleset": "dnd35e",
        "display_names": {
            "spell.fireball": "Plasma Grenade"
        },
        "aliases": {
            "en": {"plasma grenade": "spell.fireball"}
        }
    }
    assert validate_skin_pack(valid_pack) == True

    # Mechanical change (should reject)
    invalid_pack_mechanical = {
        "skin_pack_id": "cheater_pack",
        "version": "1.0.0",
        "base_ruleset": "dnd35e",
        "display_names": {
            "spell.fireball": {
                "name": "Super Fireball",
                "damage": "20d6"  # Mechanical change!
            }
        }
    }
    with pytest.raises(ValidationError, match="Forbidden mechanical field"):
        validate_skin_pack(invalid_pack_mechanical)

    # Unknown canonical ID (should reject)
    invalid_pack_unknown_id = {
        "skin_pack_id": "bad_pack",
        "version": "1.0.0",
        "base_ruleset": "dnd35e",
        "display_names": {
            "spell.ultimate_blast": "Nuclear Bomb"  # ID doesn't exist
        }
    }
    with pytest.raises(ValidationError, match="Unknown canonical ID"):
        validate_skin_pack(invalid_pack_unknown_id)

    # Alias conflict (should reject)
    invalid_pack_alias_conflict = {
        "skin_pack_id": "conflict_pack",
        "version": "1.0.0",
        "base_ruleset": "dnd35e",
        "aliases": {
            "en": {
                "blade": "item.longsword",
                "blade": "item.dagger"  # Conflict!
            }
        }
    }
    with pytest.raises(ValidationError, match="Alias conflict"):
        validate_skin_pack(invalid_pack_alias_conflict)
```

---

## Import Rejection Examples

### Example 1: Mechanical Smuggling Attempt

**Skin Pack:**
```json
{
    "skin_pack_id": "overpowered_pack",
    "display_names": {
        "spell.fireball": {
            "name": "Mega Fireball",
            "damage": "50d6",  // ❌ Mechanical change!
            "range": "1000 feet"  // ❌ Mechanical change!
        }
    }
}
```

**Rejection:**
```
ValidationError: Forbidden mechanical field: damage
Skin Pack 'overpowered_pack' rejected.
```

---

### Example 2: Alias Conflict

**Skin Pack:**
```json
{
    "skin_pack_id": "confusing_pack",
    "aliases": {
        "en": {
            "fire": "spell.fireball",
            "fire": "spell.burning_hands"  // ❌ Conflict!
        }
    }
}
```

**Rejection:**
```
ValidationError: Alias conflict in 'en': 'fire' maps to both 'spell.fireball' and 'spell.burning_hands'
Skin Pack 'confusing_pack' rejected.
```

---

### Example 3: Unknown Canonical ID

**Skin Pack:**
```json
{
    "skin_pack_id": "fantasy_pack",
    "display_names": {
        "spell.time_stop": "Chronomancy"  // ❌ ID not in registry (Gate T2+)
    }
}
```

**Rejection:**
```
ValidationError: Unknown canonical ID: spell.time_stop
Canonical ID 'spell.time_stop' does not exist in registry.
Hint: Are you referencing a gated spell? Check gate status.
Skin Pack 'fantasy_pack' rejected.
```

---

## Exit Criteria

This spec is **ready for implementation** when:

- [x] Skin Pack schema defined
- [x] Validation rules unambiguous (8 rules documented)
- [x] Rejection criteria specified (critical vs warnings)
- [x] Security checks defined (no code execution)
- [x] Campaign import validation specified
- [x] Hot-swap rules defined
- [x] Test harness examples provided
- [x] Rejection examples documented
- [ ] Cross-agent review complete (Agent B, C, D feedback)
- [ ] PM approval obtained

---

## References

- **Constraint Source:** docs/analysis/GLOBAL_AUDIT_CONSTRAINT_LEDGER.md (Constraint B1)
- **Gap Source:** docs/analysis/GLOBAL_AUDIT_GAP_AND_RISK_REGISTER.md (GAP-002)
- **Canonical ID Schema:** docs/research/R0_CANONICAL_ID_SCHEMA.md
- **Design Intent:** Inbox documents (Generative Presentation Architecture)

---

**STATUS:** Awaiting cross-agent review + PM approval before implementation.

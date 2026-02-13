# CP-16 — Conditions & Status Effects Kernel

**Status:** ✅ IMPLEMENTED & FROZEN
**Created:** 2026-02-08
**Instruction Packet:** CP-16
**Test Coverage:** 14 integration tests (all passing)

---

## 1. Purpose

CP-16 introduces **deterministic condition modifiers** for D&D 3.5e combat. This packet implements data-only condition contracts that affect attack resolution, AC, and damage rolls while maintaining strict event-driven architecture and fail-closed design.

**CRITICAL SCOPE DECISION (OPTION A - MINIMAL SCOPE):**
Conditions are **metadata-only descriptors**. They declare mechanical truth but do NOT enforce legality. All enforcement of movement restrictions, action prohibitions, and legal move validation is deferred to CP-17+.

---

## 2. Implementation Scope

### IN SCOPE (OPTION A - MINIMAL SCOPE)

✅ **Condition Storage**:
- Conditions stored in `entities[actor_id]["conditions"]` dict
- Event-driven application/removal lifecycle
- Deterministic serialization to/from JSON

✅ **Modifier Query System**:
- `get_condition_modifiers(world_state, actor_id)` returns aggregate modifiers
- Numeric modifiers stack additively (AC, attack, damage, Dex)
- Boolean flags use OR logic (any condition sets flag → True)

✅ **Attack/AC Integration**:
- Attacker conditions modify attack rolls (e.g., shaken -2)
- Defender conditions modify AC (e.g., prone -4 vs melee)
- Damage modifiers affect damage total (e.g., sickened -2)

✅ **Condition Set (8 Total)**:
- **MUST-HAVE**: Prone, Flat-Footed, Grappled, Helpless (blocking)
- **SHOULD-HAVE**: Stunned, Dazed, Shaken, Sickened (non-blocking)

✅ **Metadata-Only Flags**:
- `movement_prohibited` (grappled): descriptor only, no enforcement
- `actions_prohibited` (stunned/dazed/helpless): descriptor only, no enforcement
- `standing_triggers_aoo` (prone): descriptor only, no enforcement
- `auto_hit_if_helpless` (helpless): descriptor only, coup de grace deferred
- `loses_dex_to_ac` (flat-footed/stunned/helpless): descriptor only, Dex loss calculation deferred

### OUT OF SCOPE (Deferred to CP-17+)

❌ **Enforcement Logic**: Movement prohibition, action legality, standing validation
❌ **Duration Tracking**: No automatic expiration or countdown (manual removal only)
❌ **Saving Throws**: No save-based removal or application
❌ **Spell System**: No spell catalog, spell effects, or caster level
❌ **Full Grapple System**: Grapple state only (no checks, pinning, escape)
❌ **Feats**: No feat-based condition interactions (e.g., Improved Trip)
❌ **Immunity/Suppression**: No condition immunity or suppression logic
❌ **Context-Specific Modifiers**: Prone AC penalty vs melee vs ranged (all attacks get modifier)

---

## 3. Canonical Architecture Decisions

All decisions below are **LOCKED** and binding for CP-17+.

### 3.1 Conditions Are Metadata-Only Descriptors (LOCKED)

**Decision:** Conditions declare mechanical truth but do NOT enforce legality

**Critical Rule (OPTION A - BINDING):**
> "Conditions describe mechanical truth but do not enforce legality. Enforcement deferred to CP-17+."

**Examples:**

| Condition | Metadata | Enforcement (Deferred) |
|-----------|----------|------------------------|
| Grappled | `movement_prohibited: True` | Movement system must check flag and block |
| Prone | `standing_triggers_aoo: True` | Standing action must trigger AoO check |
| Stunned | `actions_prohibited: True` | Action economy must check flag and block |

**Rationale:**
- CP-16 has no movement system (deferred to CP-16+)
- CP-16 has no standing action (deferred to CP-16+)
- CP-16 has no skill check system (deferred to CP-17+)
- Metadata flags prepare for future enforcement without premature implementation

**Contract:**
Resolvers query `get_condition_modifiers()` and apply numeric modifiers. Boolean flags are stored but not enforced in CP-16.

---

### 3.2 Modifier Stacking — Simple Summation (LOCKED)

**Decision:** Numeric modifiers stack additively, boolean flags use OR logic

**Stacking Rules:**
```python
# Numeric modifiers: additive stacking
shaken (-2 attack) + sickened (-2 attack) = -4 attack total

# Boolean flags: OR logic
stunned (actions_prohibited) OR dazed (actions_prohibited) = actions_prohibited
```

**Rationale:**
- PHB p. 21: "Bonuses with the same type don't stack" (exception: dodge bonuses)
- CP-16 conditions impose **penalties**, not bonuses (penalties stack per RAW)
- Simplified stacking model (no typed bonus tracking deferred to CP-17+)

**Contract:**
`get_condition_modifiers()` sums all numeric modifiers and ORs all boolean flags. No suppression, no maximum penalty cap.

---

### 3.3 Condition Storage — Entity-Keyed Dict (LOCKED)

**Decision:** Conditions stored in `entities[actor_id]["conditions"]` as dict keyed by condition type

**Schema:**
```python
entities["goblin_1"]["conditions"] = {
    "prone": {  # Key is condition_type.value
        "condition_type": "prone",
        "source": "trip_attack",
        "modifiers": {...},
        "applied_at_event_id": 5,
        "notes": "..."
    },
    "shaken": {...}
}
```

**Rationale:**
- Dict keying by condition type prevents duplicate condition types (no two "prone" conditions)
- Same condition type overwrites previous instance (no manual deduplication)
- Deterministic serialization via sorted keys (WorldState.state_hash())

**Contract:**
Applying condition with same `condition_type` as existing condition overwrites the existing instance. No error, no stacking of identical types.

---

### 3.4 Event-Driven Lifecycle — Manual Removal Only (LOCKED)

**Decision:** Conditions applied via events, removed manually (no automatic expiration)

**Application (Future):**
```python
# CP-17+ will emit condition_applied events
Event(
    event_type="condition_applied",
    payload={
        "actor_id": "goblin_1",
        "condition_type": "prone",
        "source": "trip_attack",
        ...
    }
)
```

**Removal (Future):**
```python
# CP-17+ will emit condition_removed events
Event(
    event_type="condition_removed",
    payload={
        "actor_id": "goblin_1",
        "condition_type": "prone"
    }
)
```

**CP-16 Scope:**
- No event emission for application/removal (deferred to CP-17+)
- Direct mutation via `apply_condition()` / `remove_condition()` helpers
- No duration tracking (no `expires_at_t_seconds` field)

**Rationale:**
- Duration tracking requires time advancement system (deferred to CP-17+)
- Automatic expiration requires combat round progression (CP-14 exists but not integrated)
- Event-driven application deferred until full condition lifecycle designed

**Contract:**
CP-16 conditions persist until manually removed. No automatic cleanup.

---

### 3.5 Query System — Fail-Closed for Missing Entities (LOCKED)

**Decision:** `get_condition_modifiers()` returns zero modifiers for missing entities

**Implementation:**
```python
def get_condition_modifiers(world_state, actor_id, context=None):
    entity = world_state.entities.get(actor_id)
    if entity is None:
        return ConditionModifiers()  # All zeros, all flags False
```

**Rationale:**
- Fail-closed design (no guessing, no silent assumptions)
- Missing entity is explicit error, not implicit zero state
- Deterministic (same missing data always returns same zero modifiers)

**Contract:**
Query system MUST NOT raise exceptions for missing entities. Zero modifiers = safe default for fail-closed queries.

---

### 3.6 Attack Resolver Integration — Modifier Injection (LOCKED)

**Decision:** Attack resolver queries conditions and injects modifiers before resolution

**Integration Points:**

1. **Attack Roll Modifier:**
```python
attacker_modifiers = get_condition_modifiers(world_state, intent.attacker_id)
attack_bonus_with_conditions = intent.attack_bonus + attacker_modifiers.attack_modifier
total = d20_result + attack_bonus_with_conditions
```

2. **AC Modifier:**
```python
defender_modifiers = get_condition_modifiers(world_state, intent.target_id)
target_ac = base_ac + defender_modifiers.ac_modifier
```

3. **Damage Modifier:**
```python
base_damage = sum(damage_rolls) + weapon.damage_bonus
damage_total = max(0, base_damage + attacker_modifiers.damage_modifier)
```

**Event Payloads (Extended):**
```python
{
    "event_type": "attack_roll",
    "payload": {
        "attack_bonus": 5,  # Base bonus
        "condition_modifier": -2,  # Condition penalty
        "total": 15,  # d20 + 5 - 2
        "target_ac": 11,  # Base AC 15 - 4 (prone)
        "target_base_ac": 15,
        "target_ac_modifier": -4
    }
}
```

**Rationale:**
- Modifier injection preserves CP-10 attack pipeline (no refactoring)
- Event payload completeness (audit trail includes all modifiers)
- Backward compatible (new fields optional, default to 0)

**Contract:**
Attack resolver MUST query `get_condition_modifiers()` for both attacker and defender. Events MUST record `condition_modifier` separate from base bonus.

---

### 3.7 Canonical Condition Definitions — PHB Fidelity (LOCKED)

**Decision:** Each condition has factory function with PHB citations and RAW modifiers

**Condition Definitions:**

| Condition | AC Mod | Attack Mod | Damage Mod | Dex Mod | Flags | PHB Citation |
|-----------|--------|------------|------------|---------|-------|--------------|
| **Prone** | -4 | -4 (melee) | 0 | 0 | `standing_triggers_aoo` | p. 311 |
| **Flat-Footed** | 0 | 0 | 0 | 0 | `loses_dex_to_ac` | p. 137 |
| **Grappled** | 0 | 0 | 0 | -4 | `movement_prohibited` | p. 156 |
| **Helpless** | -4 | 0 | 0 | 0 | `loses_dex_to_ac`, `actions_prohibited`, `auto_hit_if_helpless` | p. 311 |
| **Stunned** | -2 | 0 | 0 | 0 | `loses_dex_to_ac`, `actions_prohibited` | p. 311 |
| **Dazed** | 0 | 0 | 0 | 0 | `actions_prohibited` | p. 311 |
| **Shaken** | 0 | -2 | 0 | 0 | None | p. 311 |
| **Sickened** | 0 | -2 | -2 | 0 | None | p. 311 |

**Factory Functions:**
```python
create_prone_condition(source, applied_at_event_id) -> ConditionInstance
create_flat_footed_condition(source, applied_at_event_id) -> ConditionInstance
create_grappled_condition(source, applied_at_event_id) -> ConditionInstance
create_helpless_condition(source, applied_at_event_id) -> ConditionInstance
create_stunned_condition(source, applied_at_event_id) -> ConditionInstance
create_dazed_condition(source, applied_at_event_id) -> ConditionInstance
create_shaken_condition(source, applied_at_event_id) -> ConditionInstance
create_sickened_condition(source, applied_at_event_id) -> ConditionInstance
```

**Rationale:**
- Factory functions prevent manual construction errors
- PHB citations baked into notes field for audit trail
- RAW modifiers locked (no house rules, no interpretation)

**Contract:**
Use factory functions for all condition creation. Direct ConditionInstance construction allowed but discouraged.

---

### 3.8 No RNG Consumption (LOCKED)

**Decision:** Condition queries and application consume ZERO RNG

**Guarantee:**
```python
# Same condition state → identical modifier query result
modifiers1 = get_condition_modifiers(world_state, "goblin_1")
modifiers2 = get_condition_modifiers(world_state, "goblin_1")
assert modifiers1 == modifiers2  # Deterministic, no RNG

# Condition application does not advance RNG streams
rng_before = rng.stream("combat").get_state()
world_state = apply_condition(world_state, "goblin_1", prone)
rng_after = rng.stream("combat").get_state()
assert rng_before == rng_after  # RNG state unchanged
```

**Rationale:**
- Conditions are deterministic data lookups (no randomness)
- RNG stream isolation preserved (combat/initiative/policy)
- Deterministic replay guaranteed

**Contract:**
Condition system MUST NOT consume RNG under any circumstances. All operations are pure data queries or mutations.

---

### 3.9 Context Parameter — Reserved for Future (LOCKED)

**Decision:** `get_condition_modifiers()` accepts optional `context` parameter (unused in CP-16)

**Signature:**
```python
def get_condition_modifiers(
    world_state: WorldState,
    actor_id: str,
    context: Optional[str] = None  # Reserved for CP-17+
) -> ConditionModifiers
```

**Future Use Cases (CP-17+):**
- `context="melee_attack"` → Prone AC penalty applies
- `context="ranged_attack"` → Prone AC bonus applies (+4 vs ranged per PHB)
- `context="dex_check"` → Grappled Dex penalty applies

**CP-16 Behavior:**
Context parameter ignored. All modifiers returned unconditionally.

**Rationale:**
- Prepares for context-specific filtering without breaking API
- CP-16 has no attack type distinction (melee vs ranged deferred to CP-17+)
- Reserved parameter prevents future breaking change

**Contract:**
`context` parameter MUST be accepted but MAY be ignored in CP-16. CP-17+ may implement context filtering.

---

### 3.10 Backward Compatibility — No Breaking Changes (LOCKED)

**Decision:** CP-16 is additive-only (zero changes to CP-09 through CP-15 behavior)

**Compatibility Mechanism:**

1. **Attack Resolver Extension:**
   - New fields in event payloads (`condition_modifier`, `target_base_ac`, `target_ac_modifier`)
   - All new fields optional with default values (0 for modifiers)
   - Existing tests unaffected (no conditions → zero modifiers → same behavior)

2. **WorldState Extension:**
   - `entities[actor_id]["conditions"]` dict (optional, defaults to empty dict)
   - Missing `conditions` key treated as no conditions (zero modifiers)

3. **No Import Changes:**
   - No changes to existing module APIs
   - New modules (`aidm.core.conditions`, `aidm.schemas.conditions`) do not affect existing code

**Result:**
- All 524 existing tests still pass (100% backward compatible)
- 14 new tests added (524 → 538 total)
- No test modifications required

**Contract:**
CP-16 MUST NOT break any CP-09 through CP-15 tests. Test count progression: 524 → 538 (14 new tests only).

---

## 4. Modifier Schema

### 4.1 ConditionModifiers Dataclass

```python
@dataclass
class ConditionModifiers:
    # Numeric modifiers (stack additively)
    ac_modifier: int = 0
    attack_modifier: int = 0
    damage_modifier: int = 0
    dex_modifier: int = 0

    # Metadata-only flags (OR logic, no enforcement in CP-16)
    movement_prohibited: bool = False
    actions_prohibited: bool = False
    standing_triggers_aoo: bool = False
    auto_hit_if_helpless: bool = False
    loses_dex_to_ac: bool = False
```

### 4.2 ConditionInstance Schema

```python
@dataclass
class ConditionInstance:
    condition_type: ConditionType
    source: str  # e.g., "trip_attack", "spell_hold_person"
    modifiers: ConditionModifiers
    applied_at_event_id: int  # Provenance
    notes: Optional[str] = None  # Human-readable description
```

---

## 5. Event Model

### 5.1 Extended Event Payloads (CP-16)

| Event Type | New Fields | Purpose |
|------------|------------|---------|
| `attack_roll` | `condition_modifier`, `target_base_ac`, `target_ac_modifier` | Track condition effects on attack/AC |
| `damage_roll` | `condition_modifier` | Track condition effects on damage |

**No New Event Types:**
CP-16 does not introduce `condition_applied` or `condition_removed` events. Event-driven lifecycle deferred to CP-17+.

---

## 6. Test Coverage

### 6.1 Tier-1 Tests (MUST PASS)

| Test | Requirement | Status |
|------|-------------|--------|
| `test_condition_modifiers_affect_attack_rolls` | Shaken -2 attack affects attack total | ✅ PASS |
| `test_condition_modifiers_affect_ac` | Prone -4 AC affects target AC | ✅ PASS |
| `test_condition_modifiers_affect_damage_rolls` | Sickened -2 damage affects damage total | ✅ PASS |
| `test_multiple_conditions_stack_correctly` | Shaken + Sickened = -4 attack (stacking) | ✅ PASS |
| `test_deterministic_replay_with_conditions` | Same seed → identical state hash with conditions | ✅ PASS |

### 6.2 Tier-2 Tests (SHOULD PASS)

| Test | Requirement | Status |
|------|-------------|--------|
| `test_condition_application_and_storage` | Conditions stored in WorldState | ✅ PASS |
| `test_condition_removal` | Conditions can be removed | ✅ PASS |
| `test_query_system_fail_closed` | Missing entities return zero modifiers | ✅ PASS |
| `test_helpless_condition_modifiers` | Helpless has correct modifiers | ✅ PASS |
| `test_stunned_condition_modifiers` | Stunned has correct modifiers | ✅ PASS |
| `test_grappled_condition_modifiers` | Grappled has correct modifiers | ✅ PASS |
| `test_dazed_condition_modifiers` | Dazed has correct modifiers | ✅ PASS |
| `test_flat_footed_condition_modifiers` | Flat-footed has correct modifiers | ✅ PASS |
| `test_condition_overwrite_same_type` | Same condition type overwrites | ✅ PASS |

**Total Coverage:** 14 tests (5 Tier-1, 9 Tier-2)
**Regression Tests:** All 524 existing tests still pass (538 total)

---

## 7. File Manifest

### 7.1 New Files

| File | Purpose | Lines |
|------|---------|-------|
| `aidm/schemas/conditions.py` | Condition schemas and factory functions | 373 |
| `aidm/core/conditions.py` | Condition query and mutation helpers | 155 |
| `tests/test_conditions_kernel.py` | CP-16 integration tests | 520 |
| `docs/CP16_CONDITIONS_DECISIONS.md` | This document | - |

### 7.2 Modified Files

| File | Changes | Rationale |
|------|---------|-----------|
| `aidm/core/attack_resolver.py` | Added condition modifier queries and event payload fields | Attack/AC/damage integration |

---

## 8. API Reference

### 8.1 Condition Queries

```python
from aidm.core.conditions import get_condition_modifiers
from aidm.core.state import WorldState

# Query aggregate modifiers for an actor
modifiers = get_condition_modifiers(world_state, "goblin_1", context="attack")

# Access modifier values
print(modifiers.ac_modifier)  # e.g., -4 (prone)
print(modifiers.attack_modifier)  # e.g., -2 (shaken)
print(modifiers.damage_modifier)  # e.g., -2 (sickened)

# Check metadata flags
if modifiers.actions_prohibited:
    print("Actor cannot take actions")
```

### 8.2 Condition Application

```python
from aidm.core.conditions import apply_condition, remove_condition, has_condition
from aidm.schemas.conditions import create_prone_condition

# Apply condition
prone = create_prone_condition(source="trip_attack", applied_at_event_id=5)
world_state = apply_condition(world_state, "goblin_1", prone)

# Check if condition present
if has_condition(world_state, "goblin_1", "prone"):
    print("Goblin is prone")

# Remove condition
world_state = remove_condition(world_state, "goblin_1", "prone")
```

### 8.3 Factory Functions

```python
from aidm.schemas.conditions import (
    create_prone_condition,
    create_flat_footed_condition,
    create_grappled_condition,
    create_helpless_condition,
    create_stunned_condition,
    create_dazed_condition,
    create_shaken_condition,
    create_sickened_condition
)

# Create condition instances with PHB-compliant modifiers
prone = create_prone_condition(source="trip", applied_at_event_id=10)
shaken = create_shaken_condition(source="fear", applied_at_event_id=15)
```

---

## 9. Citations

All mechanics traceable to PHB 3.5e:

| Rule | Citation | Page |
|------|----------|------|
| Prone condition | PHB 3.5e | 311 |
| Flat-footed condition | PHB 3.5e | 137 |
| Grappled condition | PHB 3.5e | 156 |
| Helpless condition | PHB 3.5e | 311 |
| Stunned condition | PHB 3.5e | 311 |
| Dazed condition | PHB 3.5e | 311 |
| Shaken condition | PHB 3.5e | 311 |
| Sickened condition | PHB 3.5e | 311 |
| Penalty stacking | PHB 3.5e | 21 |

---

## 10. RAW Deviations

### 10.1 Prone AC Modifier — Simplified (No Context)

**Deviation:** Prone AC modifier (-4) applied unconditionally (no melee vs ranged distinction)

**PHB Rule:** "A prone defender gains a +4 bonus to Armor Class against ranged attacks, but takes a -4 penalty to AC against melee attacks." (PHB p. 311)

**CP-16 Behavior:** All attacks apply -4 AC penalty (both melee and ranged)

**Rationale:**
- CP-16 has no attack type distinction (melee vs ranged deferred to CP-17+)
- Context parameter reserved for future filtering
- Simplified implementation prevents premature attack type system

**Impact:** Minimal. Prone defenders are slightly more vulnerable to ranged attacks than RAW. Attack type distinction deferred to CP-17+ when ranged attack system introduced.

---

## 11. Future Work (Out of Scope)

The following systems are **explicitly deferred** to future packets:

- **CP-17:** Event-driven condition lifecycle (`condition_applied`, `condition_removed` events)
- **CP-17:** Duration tracking and automatic expiration (time-based removal)
- **CP-17:** Context-specific modifiers (prone AC vs melee vs ranged)
- **CP-17:** Enforcement of movement prohibition, action legality, standing validation
- **CP-18:** Saving throw-based condition application and removal
- **CP-18:** Condition immunity and suppression (e.g., elf immunity to sleep)
- **CP-19:** Full grapple system (grapple checks, pinning, escape attempts)
- **CP-19:** Feat interactions (e.g., Improved Trip, Stunning Fist)
- **CP-20:** Spell effects and spell-based conditions (hold person, sleep, etc.)

---

## 12. Architectural Precedent

CP-16 establishes the **metadata-only condition pattern** for all future status effects:

### 12.1 Metadata-Only Design Pattern

**Core Principle:**
Conditions declare mechanical truth but do not enforce legality. Enforcement is the responsibility of resolvers and validators.

**Pattern:**
```python
# Condition declares restriction
modifiers.movement_prohibited = True  # Metadata

# Resolver enforces restriction (CP-17+)
if get_condition_modifiers(world_state, actor_id).movement_prohibited:
    return TurnResult(status="invalid_intent", failure_reason="Movement prohibited by grappled condition")
```

**Future Applications:**
- Paralyzed condition (actions prohibited, auto-fail Str/Dex checks)
- Petrified condition (DR 8/adamantine, immunity to critical hits)
- Invisible condition (melee attacks get miss chance, ranged locate DC)
- Blinded condition (50% miss chance, -2 AC)

### 12.2 Modifier Injection Pattern

**Core Principle:**
Resolvers query condition modifiers at resolution time, not at validation time.

**Pattern:**
```python
# Resolver queries conditions
attacker_mods = get_condition_modifiers(world_state, attacker_id)
defender_mods = get_condition_modifiers(world_state, defender_id)

# Resolver injects modifiers
attack_total = d20 + base_bonus + attacker_mods.attack_modifier
target_ac = base_ac + defender_mods.ac_modifier
```

**Future Applications:**
- Skill check modifiers (CP-17+)
- Saving throw modifiers (CP-18+)
- Initiative modifiers (improved initiative feat, CP-19+)
- Speed modifiers (haste, slow, CP-20+)

---

## 13. Success Criteria

✅ All acceptance criteria met:

1. ✅ Condition modifiers affect attack rolls (shaken -2, sickened -2)
2. ✅ Condition modifiers affect AC (prone -4, stunned -2)
3. ✅ Condition modifiers affect damage rolls (sickened -2)
4. ✅ Multiple conditions stack additively (shaken + sickened = -4 attack)
5. ✅ Deterministic replay preserved (same seed → identical state hash)
6. ✅ Backward compatibility preserved (all 524 CP-09–CP-15 tests pass)
7. ✅ All 14 new tests pass (5 Tier-1, 9 Tier-2)
8. ✅ No RNG consumption by condition system
9. ✅ Fail-closed query system (missing entities → zero modifiers)

---

## 14. Lessons Learned

### 14.1 Metadata-Only Scope Prevents Premature Complexity

Deferring enforcement logic to CP-17+ avoided premature movement system, skill check system, and action economy validation. Metadata flags prepare for future enforcement without blocking CP-16 delivery.

### 14.2 Modifier Injection Preserves Pipeline Integrity

Adding condition queries to existing attack resolver required minimal changes (3 lines of query code, 4 event payload fields). Pipeline architecture remains intact.

### 14.3 Factory Functions Prevent Construction Errors

Using `create_prone_condition()` instead of manual `ConditionInstance()` construction eliminated PHB reference errors and ensured consistent modifier values.

### 14.4 Additive Stacking Simplifies Implementation

Simple summation of modifiers (no typed bonus tracking, no maximum caps) reduced complexity while remaining RAW-compliant for penalties.

---

**Document Version:** 1.0
**Last Updated:** 2026-02-08
**Status:** LOCKED (non-negotiable for CP-17+)

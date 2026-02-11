# WO-038: Intent Bridge - Implementation Summary

**Status**: ✅ Complete
**Priority**: Phase 3 Batch 1
**Tests**: 27 new tests, all passing
**Regressions**: 0 (3628 total tests passing)

## Delivered Components

### 1. IntentBridge Class (`aidm/interaction/intent_bridge.py`)

**Core Methods:**
- `resolve_attack()` - Translates DeclaredAttackIntent → AttackIntent
- `resolve_spell()` - Translates CastSpellIntent → SpellCastIntent
- `resolve_move()` - Validates MoveIntent

**Resolution Features:**
- **Entity Name Resolution**: Exact match, partial match with single candidate, ambiguity detection
- **Weapon Resolution**: Named weapons, default weapon fallback, unarmed strike
- **Spell Resolution**: SPELL_REGISTRY lookup, case-insensitive matching
- **Attack Bonus**: Entity ATTACK_BONUS field with BAB+STR fallback

### 2. ClarificationRequest Dataclass

**Ambiguity Types:**
- `TARGET_AMBIGUOUS` - Multiple entities match name
- `TARGET_NOT_FOUND` - No entity matches name
- `WEAPON_AMBIGUOUS` - Multiple weapons match (future)
- `WEAPON_NOT_FOUND` - Weapon not in entity's equipment
- `SPELL_NOT_FOUND` - Spell not in SPELL_REGISTRY
- `DESTINATION_OUT_OF_BOUNDS` - Invalid move destination

**Fields:**
- `intent_type` - Which intent failed (attack/spell/move)
- `ambiguity_type` - Specific problem
- `candidates` - Possible matches for user to choose
- `message` - Human-readable clarification prompt

### 3. Test Suite (`tests/test_intent_bridge.py`)

**27 Tests Covering:**

**Entity Resolution (7 tests):**
- Exact name match
- Partial name match (single candidate)
- Ambiguous partial match
- Unknown target with available roster
- Defeated entity exclusion
- Case-insensitive matching
- Empty target_ref handling

**Weapon Resolution (5 tests):**
- Named weapon resolution
- Default weapon fallback
- Unknown weapon error
- Unarmed strike fallback
- Damage type inference (slashing/piercing/bludgeoning)

**Attack Bonus (2 tests):**
- ATTACK_BONUS field
- BAB + STR_MOD fallback

**Spell Resolution (6 tests):**
- Spell name → spell_id
- Target entity resolution
- Target position handling
- Unknown spell error
- Empty spell name
- Case-insensitive matching

**Move Intent (2 tests):**
- Valid destination
- Missing destination error

**ClarificationRequest (3 tests):**
- Intent type field
- Human-readable message
- Immutability (frozen=True)

**Boundary Law Compliance (2 tests):**
- FrozenWorldStateView usage (BL-020)
- No state mutation

## Architecture Decisions

### 1. Read-Only State Access
- Uses `FrozenWorldStateView` for all lookups (BL-020)
- No mutations to world state
- Entity lookups via `view.entities.get()`

### 2. Entity Resolution Strategy
```python
# Priority order:
1. Exact match (case-insensitive) → entity_id
2. Partial match with single candidate → entity_id
3. Multiple matches → ClarificationRequest
4. No matches → ClarificationRequest with roster
```

### 3. Weapon Resolution
- Checks `EF.WEAPON` field for default
- Matches against entity's equipment (simplified in Phase 3 Batch 1)
- Infers damage type from weapon name (sword→slashing, spear→piercing, mace→bludgeoning)
- Falls back to unarmed strike (1d3 bludgeoning) if no weapon

### 4. Attack Bonus Calculation
```python
# Priority:
1. entity[EF.ATTACK_BONUS] if set
2. entity[EF.BAB] + entity[EF.STR_MOD] otherwise
```

### 5. Spell Resolution
- Case-insensitive lookup in `SPELL_REGISTRY`
- Matches both `spell_id` and `spell_def.name`
- Returns first 10 spells on error for usability

## PHB Citations

**Entity Targeting:**
- PHB p.138: Declaring actions in combat
- PHB p.139: Choosing a target

**Weapons:**
- PHB p.113: Weapon damage types
- PHB p.114: Unarmed strikes (1d3 for Medium creatures)

**Spells:**
- PHB p.174: Spell targeting and ranges
- PHB Chapter 10: Spell descriptions

**Attack Bonus:**
- PHB p.139: Base Attack Bonus
- PHB p.139: Strength modifier to melee attacks

## Usage Example

```python
from aidm.interaction.intent_bridge import IntentBridge
from aidm.schemas.intents import DeclaredAttackIntent
from aidm.core.state import FrozenWorldStateView

# Create bridge
bridge = IntentBridge()
view = FrozenWorldStateView(world_state)

# Resolve attack
declared = DeclaredAttackIntent(target_ref="Goblin", weapon="longsword")
result = bridge.resolve_attack("pc_fighter", declared, view)

if isinstance(result, AttackIntent):
    # Success - pass to combat resolver
    combat_controller.execute_attack(result, world_state)
else:
    # ClarificationRequest - present to user
    voice_layer.request_clarification(result.message, result.candidates)
```

## Design Principles

1. **Single Responsibility**: Bridge translates intents, does not resolve combat
2. **Fail Loudly**: Returns explicit ClarificationRequest instead of guessing
3. **User Friendly**: Provides helpful error messages with available options
4. **Type Safe**: Uses dataclasses with frozen=True for immutability
5. **BL-020 Compliant**: Read-only state access via FrozenWorldStateView

## Next Steps (Future Work Orders)

- **WO-039**: Full equipment inventory system (proper weapon registry)
- **WO-040**: Weapon proficiency checks
- **WO-041**: Spell slot tracking and validation
- **WO-042**: Range and LOS validation for spell targeting
- **WO-043**: Mounted combat intent translation
- **WO-044**: Grapple/disarm/sunder intent translation

## Acceptance Criteria ✅

- [x] Exact name match resolves correctly
- [x] Partial name match with single candidate resolves correctly
- [x] Ambiguous match returns ClarificationRequest with candidates list
- [x] Unknown target returns error with helpful message listing available targets
- [x] Weapon resolution works for named, default, and unknown weapons
- [x] Spell name resolution against SPELL_REGISTRY
- [x] FrozenWorldStateView used for all lookups
- [x] No modifications to existing files (new files only)
- [x] All existing tests pass (3628 total)
- [x] 27 new tests with PHB citations where applicable

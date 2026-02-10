# CP-17 — Saving Throws & Defensive Resolution Kernel

**Status:** ✅ IMPLEMENTED & READY FOR PBHA-17
**Created:** 2026-02-08
**Instruction Packet:** CP-17
**Test Coverage:** 26 tests (20 unit + 6 integration, all passing)
**Preconditions:** CP-14 ✅, CP-15 ✅, CP-16 ✅ (all frozen)

---

## 1. Purpose

CP-17 introduces **deterministic saving throws** and **defensive resolution** as a fully event-sourced kernel, integrated with existing combat, conditions, and event ordering guarantees.

**IN SCOPE (CP-17):**
- Fortitude, Reflex, Will saving throws
- Save DC computation
- Save resolution outcomes (SUCCESS / FAILURE / PARTIAL)
- Condition + damage gating via save result
- Spell Resistance (SR) checks (minimal, generic)
- Deterministic RNG consumption for saves

**OUT OF SCOPE (deferred to CP-18+):**
- Full spellcasting system (spell lists, preparation, targeting rules)
- Concentration checks
- Counterspelling
- Complex multi-save effects (phased spells)
- Environmental saves (hazards) beyond generic hooks

---

## 2. Core Decisions (Locked)

### 2.1 Save Trigger Mechanism (Decision 1)

**Decision:** **C-lite (Effect rider hook)** - Internal `save_triggered` event

**Implementation:**
- `SaveContext` emitted by resolvers (attack, spell, hazard)
- **Not a player-facing intent** (no `SaveIntent` type)
- Turn executor resolves save immediately in same turn phase

**Rationale:**
- Keeps CP-17 decoupled from attack intents
- Avoids premature API surface (SaveIntent) that would complicate spell/hazard integration
- Generic `SaveContext` can be attached by any resolver

**Contract:**
```python
# After damage application, resolver may emit save_triggered (event)
# Turn executor immediately resolves save in same turn phase
```

**Confidence:** 0.86

---

### 2.2 EffectSpec Definition (Decision 2)

**Decision:** **Minimal-but-correct** - Damage multiplier + condition list

**Implementation:**
```python
@dataclass
class EffectSpec:
    damage_multiplier: float = 1.0  # Allowed: 0.0, 0.5, 1.0
    conditions_to_apply: List[str] = field(default_factory=list)
```

**Rationale:**
- Flat damage-only is too weak for half-damage-on-save (canonical use case)
- Avoids re-implementing dice in CP-17 (leverages CP-10 damage computation)
- Damage multiplier scales pre-computed `base_damage` deterministically

**Contract:**
- `damage_multiplier` applied to `SaveContext.base_damage` (integer)
- Conditions use CP-16 factory functions (`create_stunned_condition`, etc.)

**Confidence:** 0.90

---

### 2.3 Spell Resistance Caster Level (Decision 3)

**Decision:** **Explicit data** - `sr_check: Optional[SRCheck]` in `SaveContext`

**Implementation:**
```python
@dataclass
class SRCheck:
    caster_level: int
    source_id: str  # Entity ID of caster/effect source
```

**Rationale:**
- SR is meaningless without caster level
- CP-17 must remain agnostic to spellcasting (no spell system assumptions)
- Caller supplies CL when SR enforcement is needed

**Contract:**
```python
# SR check formula: d20 + caster_level >= target.SR
# SR check occurs BEFORE save (PHB p. 177)
# Failed SR negates effect (no save needed)
```

**Confidence:** 0.95

---

### 2.4 Save Modifier Source (Decision 4)

**Decision:** **Extend CP-16** - Add save modifiers to `ConditionModifiers`

**Implementation:**
```python
@dataclass
class ConditionModifiers:
    # CP-16 original fields
    ac_modifier: int = 0
    attack_modifier: int = 0
    damage_modifier: int = 0
    dex_modifier: int = 0

    # CP-17 extension
    fort_save_modifier: int = 0
    ref_save_modifier: int = 0
    will_save_modifier: int = 0
```

**Rationale:**
- RAW conditions like shaken affect saving throws (PHB p. 311: "-2 to saves")
- Same pattern as attack/AC/damage modifiers already flowing through CP-16
- Backward compatible (defaults to 0)

**Governance interpretation:**
- "Frozen" = no behavioral changes to existing features
- Additive extensions for new packets are permitted if backward-compatible
- CP-16 extension marked with `# CP-17 extension` comments

**Confidence:** 0.82

---

### 2.5 Partial Save Outcomes (Decision 5)

**Decision:** **Used but explicit** - `PARTIAL` = success with reduced effect

**Rule:**
```python
if save succeeds:
    if on_partial exists → PARTIAL
    else → SUCCESS
if save fails:
    → FAILURE
```

**Rationale:**
- No extra die rolls (violates determinism)
- No arbitrary thresholds (e.g., "exactly DC")
- Explicit definition via `SaveContext.on_partial`

**Typical use case:**
```python
# Half damage on successful save
SaveContext(
    save_type=SaveType.REF,
    dc=15,
    base_damage=20,
    on_failure=EffectSpec(damage_multiplier=1.0),  # Full damage
    on_partial=EffectSpec(damage_multiplier=0.5)   # Half damage
)
```

**Confidence:** 0.92

---

### 2.6 Event Ordering with AoO (Decision 6)

**Decision:** **Confirmed** - AoO → Attack → Damage → Save → Outcome

**Authoritative ordering:**
```
1. Action declared
2. AoO trigger emission
3. AoO resolution(s) (may defeat attacker)
4. If actor still valid → attack resolution
5. Damage application
6. If rider conditions met → save_triggered
7. SR check (if any)
8. Save roll
9. Apply save outcome effects
```

**Guarantee:** Save resolution completes within same turn phase (no mid-turn interrupts).

**Confidence:** 0.93

---

## 3. RNG Stream Isolation (Strict)

**New RNG stream:** `"saves"`

**Existing streams:**
- `"combat"` - Attack rolls, damage rolls (CP-10)
- `"initiative"` - Initiative rolls (CP-14)
- `"saves"` - **NEW:** Save rolls, SR checks (CP-17)

**Consumption order (deterministic):**
1. SR check (if present): `rng.stream("saves").randint(1, 20)`
2. Save roll: `rng.stream("saves").randint(1, 20)`

**Guarantee:** Save resolution consumes exactly **1-2 RNG calls** (1 if no SR, 2 if SR check).

**Isolation verification:**
```python
# Test: save_stream_isolated_from_combat_stream (PASSED)
# Combat stream state unchanged by save rolls
```

---

## 4. Save Resolution Algorithm (Authoritative)

### 4.1 Save Bonus Calculation

```python
save_bonus =
    base_save[target][save_type]
  + ability_modifier[target][mapped_ability]
  + condition_modifiers.save_modifier[save_type]
```

**Ability mapping (PHB p. 177):**
- Fort → CON modifier
- Ref → DEX modifier
- Will → WIS modifier

**Condition modifiers:**
- Sourced from `get_condition_modifiers(world_state, actor_id)`
- Aggregated additively (shaken -2 + sickened -2 = -4 total)

### 4.2 Roll & Compare

```python
roll = d20()
total = roll + save_bonus

if roll == 20:
    outcome = SUCCESS  # Natural 20 auto-succeeds
elif roll == 1:
    outcome = FAILURE  # Natural 1 auto-fails
else:
    outcome = SUCCESS if total >= DC else FAILURE
```

### 4.3 Outcome Mapping

```python
if outcome == SUCCESS:
    if on_partial exists → PARTIAL
    else → SUCCESS

if outcome == FAILURE:
    → FAILURE
```

---

## 5. Event Model (Required)

### 5.1 Save Events

**save_rolled:**
```python
Event(
    event_type="save_rolled",
    payload={
        "target_id": str,
        "save_type": "fortitude" | "reflex" | "will",
        "d20_result": int,
        "save_bonus": int,
        "total": int,
        "dc": int,
        "outcome": "success" | "failure" | "partial",
        "is_natural_20": bool,
        "is_natural_1": bool
    },
    citations=[{"source_id": "681f92bc94ff", "page": 177}]
)
```

**spell_resistance_checked:**
```python
Event(
    event_type="spell_resistance_checked",
    payload={
        "source_id": str,
        "target_id": str,
        "d20_result": int,
        "caster_level": int,
        "total": int,
        "target_sr": int,
        "sr_passed": bool
    },
    citations=[{"source_id": "681f92bc94ff", "page": 177}]
)
```

**save_negated:**
```python
Event(
    event_type="save_negated",
    payload={
        "target_id": str,
        "save_type": str,
        "reason": "spell_resistance"
    }
)
```

**condition_applied** (from save effects):
```python
Event(
    event_type="condition_applied",
    payload={
        "target_id": str,
        "condition_type": str,
        "source": "save_effect:{source_id}"
    }
)
```

### 5.2 Event Guarantees

- All save-related state changes originate from these events
- Events are append-only and replay-authoritative
- Event IDs strictly increasing
- Timestamps monotonic

---

## 6. Integration Points

### 6.1 Conditions (CP-16)

**Conditions → Saves:**
- Conditions modify save bonuses via `fort/ref/will_save_modifier`
- Shaken: -2 to all saves
- Sickened: -2 to all saves

**Saves → Conditions:**
- Save outcomes apply conditions via `EffectSpec.conditions_to_apply`
- Failed Will save → stunned condition
- Failed Fort save → sickened condition

**Contract:**
```python
# Query save modifiers
mods = get_condition_modifiers(world_state, actor_id)
save_bonus += mods.fort_save_modifier  # (Fort example)

# Apply condition from save outcome
condition = create_stunned_condition(source="save_effect:spell", applied_at_event_id=10)
world_state = apply_condition(world_state, target_id, condition)
```

### 6.2 Attack & AoO (CP-15)

**Attack riders:**
- Attacks may trigger saves (e.g., poison on hit)
- Save resolution occurs after damage application
- Event ordering: attack → damage → save

**Future integration:**
- Attack resolver will emit `save_triggered` event with `SaveContext`
- Turn executor will call `resolve_save()` immediately

### 6.3 Future CP-18+

**Spell system:**
- Spells will emit `SaveContext` with SR check
- Spell effects gate on save outcomes

**Hazards:**
- Environmental hazards emit `SaveContext` for trap resolution

**Grapple:**
- Grapple checks may trigger Fort saves (suffocation, crushing)

---

## 7. Test Acceptance Criteria (All Met ✅)

### 7.1 Determinism (✅ PASS)
- 10× identical save sequences → identical hashes ✅
- Test: `test_deterministic_replay_10x` (PASSED)

### 7.2 Correctness (✅ PASS)
- Fort/Ref/Will bonuses calculated correctly ✅
- Natural 1 / Natural 20 enforced ✅
- Condition modifiers applied exactly once ✅

### 7.3 Integration (✅ PASS)
- Save triggered from attack rider (simulated) ✅
- Save applies condition via CP-16 pipeline ✅
- SR negates effect cleanly ✅

### 7.4 Coverage (✅ PASS)
- **20 unit tests** ✅ (test_save_resolution.py)
- **6 integration tests** ✅ (test_save_integration.py)
- Zero flaky or order-dependent tests ✅

---

## 8. File Structure

```
aidm/schemas/saves.py              # SaveType, SaveOutcome, SaveContext, EffectSpec, SRCheck
aidm/core/save_resolver.py         # resolve_save(), check_spell_resistance(), apply_save_effects()
aidm/schemas/conditions.py         # EXTENDED: save modifier fields (CP-17 extension)
aidm/core/conditions.py            # EXTENDED: save modifier aggregation (CP-17 extension)
tests/test_save_resolution.py      # 20 unit tests
tests/test_save_integration.py     # 6 integration tests
docs/CP17_SAVES_DECISIONS.md       # This document
```

---

## 9. Backward Compatibility Verification

**CP-16 extension impact:**
- Extended `ConditionModifiers` with 3 new fields (all default 0)
- Updated `create_shaken_condition()` and `create_sickened_condition()`
- Updated `get_condition_modifiers()` aggregation logic

**Backward compatibility tests:**
- All 14 CP-16 tests passing ✅
- All 16 CP-10 attack tests passing ✅
- All 9 state hashing tests passing ✅

**Total test suite:** 49 tests passing (20 save + 6 integration + 14 condition + 9 state)

---

## 10. PBHA-17 Readiness

CP-17 is **READY FOR PBHA-17** with the following guarantees:

### 10.1 RNG Isolation ✅
- Save stream (`"saves"`) isolated from combat/initiative streams
- Test: `test_save_stream_isolated_from_combat_stream` (PASSED)

### 10.2 No Mid-Turn Interrupts ✅
- Save resolution completes within same turn phase
- Event ordering preserves execute-turn boundary

### 10.3 CP-18 Unblocked ✅
- SaveContext extensible for spell system
- EffectSpec minimal but sufficient for CP-18 spell effects
- No premature spell typing or catalog dependencies

### 10.4 Determinism Guaranteed ✅
- 10× replay test passed
- State hash stability verified across save sequences
- Zero RNG consumption outside resolution functions

---

## 11. Known Limitations (Deferred to CP-18+)

### 11.1 No Event Emission for Attack Riders
- Attack resolver does not yet emit `save_triggered` events
- Integration tests simulate attack rider (manual `SaveContext` creation)
- **Unblocked by:** CP-18 attack rider integration

### 11.2 No Automatic Condition Duration
- Conditions from saves persist until manually removed
- No duration tracking (e.g., "stunned for 1 round")
- **Unblocked by:** CP-18 duration system

### 11.3 No Evasion/Improved Evasion
- `PARTIAL` outcome defined but not auto-triggered by feats
- Evasion (Reflex save → zero damage) deferred
- **Unblocked by:** CP-19 feat system

---

## 12. Architectural Precedent

CP-17 establishes the **generic defensive resolution pattern** for all future save-based effects:

### 12.1 SaveContext as Universal Hook

**Pattern:**
```python
# Any resolver (attack, spell, hazard) can emit SaveContext
save_context = SaveContext(
    save_type=SaveType.FORT,
    dc=15,
    source_id="poison_trap",
    target_id="rogue",
    base_damage=10,
    on_failure=EffectSpec(damage_multiplier=1.0, conditions_to_apply=["sickened"])
)

# Turn executor resolves immediately
outcome, events = resolve_save(save_context, world_state, rng, next_event_id, timestamp)
updated_state, effect_events = apply_save_effects(save_context, outcome, world_state, ...)
```

**Future applications:**
- Spell save resolution (CP-18)
- Trap/hazard saves (CP-18)
- Poison/disease tracking (CP-19+)
- Death saves (CP-20+)

### 12.2 EffectSpec as Declarative Contract

**Pattern:**
```python
# Declare effects without implementing logic
on_failure=EffectSpec(
    damage_multiplier=1.0,
    conditions_to_apply=["stunned", "prone"]
)

# Resolver applies effects deterministically
apply_save_effects(context, outcome, state, ...)
```

**Future applications:**
- Spell effects (damage + condition + resource drain)
- Item effects (potion of healing, poison, etc.)
- Environmental effects (lava damage + burning condition)

---

## 13. Summary

**CP-17 Status:** ✅ **READY TO FREEZE**

**Implementation stats:**
- **2 new files** (saves.py, save_resolver.py)
- **2 extended files** (conditions.py schema + core)
- **2 new test files** (26 tests total, all passing)
- **396 LOC** (schemas + resolver)
- **0 breaking changes** to CP-09–CP-16

**Acceptance criteria:**
- ✅ 20 unit tests (≥20 required)
- ✅ 6 integration tests (≥6 required)
- ✅ Determinism verified (10× replay)
- ✅ RNG isolation confirmed
- ✅ Backward compatibility maintained

**PBHA-17 trigger:** YES (new interaction class + defensive resolution)

**Freeze criteria met:**
- All acceptance tests pass ✅
- No deferred systems partially implemented ✅
- CP-18 unblocked ✅

---

**Document Version:** 1.0
**Last Updated:** 2026-02-08
**Status:** LOCKED (non-negotiable for CP-18+)
**Confidence:** 0.94

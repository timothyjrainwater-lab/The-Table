# WO-015 Completion Report: Play Loop Spellcasting Integration

**Assigned To:** Sonnet-C (Claude 4.5 Sonnet)
**Issued By:** Opus (PM)
**Date:** 2026-02-11
**Status:** COMPLETE

---

## Summary

Integrated the spellcasting resolution system (WO-014) into the play loop so that `SpellCastIntent` can be executed during combat turns. This completes the Box→Lens→Spark pipeline for spellcasting.

Key accomplishments:
- Extended `execute_turn()` to handle `SpellCastIntent` routing
- Added concentration break checks when entities take damage
- Implemented duration tracking at round end via `_tick_duration_tracker()`
- Generated appropriate events and narration tokens for all spell types

---

## Files Modified/Created

| File | Lines | Change Type |
|------|-------|-------------|
| `aidm/core/play_loop.py` | 1366 | Modified |
| `aidm/core/combat_controller.py` | 364 | Modified |
| `tests/test_play_loop_spellcasting.py` | 915 | Created |

### Changes to `aidm/core/play_loop.py`

1. **New imports** (lines 29-37):
   - `SpellCastIntent`, `SpellResolver`, `CasterStats`, `TargetStats`, `SpellDefinition`, `SpellEffect`
   - `SPELL_REGISTRY`
   - `DurationTracker`, `ActiveSpellEffect`, `create_effect`
   - `Position`, `BattleGrid`

2. **New helper functions** (lines 145-410):
   - `_create_caster_stats()`: Extract CasterStats from WorldState entity
   - `_create_target_stats()`: Extract TargetStats from WorldState entity
   - `_get_or_create_duration_tracker()`: Get/create DurationTracker from active_combat
   - `_resolve_spell_cast()`: Main spell resolution orchestrator
   - `_check_concentration_break()`: Check if damage breaks concentration

3. **Intent routing** (lines 733-735):
   - Added `SpellCastIntent` to intent actor detection (via `caster_id`)

4. **Spell resolution routing** (lines 1163-1196):
   - Route `SpellCastIntent` to `_resolve_spell_cast()`
   - Check concentration break if caster took AoO damage

5. **Concentration break checks** (lines 1015-1028, 1047-1060):
   - Added after `apply_attack_events()` for single attacks
   - Added after `apply_full_attack_events()` for full attacks

### Changes to `aidm/core/combat_controller.py`

1. **New import** (line 25):
   - `DurationTracker`

2. **New helper function** (lines 32-126):
   - `_tick_duration_tracker()`: Tick duration at round end, expire effects, emit events

3. **Round end integration** (lines 336-353):
   - Apply updated active_combat BEFORE ticking duration
   - Call `_tick_duration_tracker()` at round end
   - Return world_state from duration tick

---

## Test Results

```
python -m pytest --tb=short

===================== 2743 passed, 43 warnings in 10.50s ======================
```

### New Tests (17 tests in `tests/test_play_loop_spellcasting.py`)

| Test Class | Test Name | Description |
|------------|-----------|-------------|
| TestAreaDamageSpells | test_cast_fireball_hits_multiple_targets | Area damage affects all targets |
| TestAreaDamageSpells | test_cast_cone_spell_direction | Cone spells use direction parameter |
| TestSingleTargetSpells | test_cast_magic_missile_auto_hit | Auto-hit spells work |
| TestHealingSpells | test_cast_cure_wounds_heals_target | Healing spells restore HP |
| TestBuffSpells | test_cast_mage_armor_applies_buff | Buff conditions applied |
| TestBuffSpells | test_cast_self_spell_no_target_needed | Self-target spells work |
| TestDebuffSpells | test_cast_hold_person_applies_condition | Debuff on failed save |
| TestSpellValidation | test_cast_spell_wrong_actor | Actor mismatch fails |
| TestSpellValidation | test_cast_unknown_spell | Unknown spell fails |
| TestSpellValidation | test_cast_spell_range_validation | Out of range fails |
| TestDurationTracking | test_spell_duration_expires_at_round_end | Duration expires correctly |
| TestConcentration | test_concentration_breaks_on_damage | Concentration breaks on damage |
| TestDeterminismAndSTPs | test_deterministic_spell_resolution | Same seed = same result |
| TestDeterminismAndSTPs | test_cast_spell_generates_stps | spell_cast event generated |
| TestDeterminismAndSTPs | test_save_reduces_damage_by_half | Reflex half works |
| TestAdditionalCases | test_spell_cast_on_defeated_target | Can target defeated entity |
| TestAdditionalCases | test_multiple_spells_same_combat | Multiple casts work |

---

## Event Types Generated

| Event Type | When Generated |
|------------|----------------|
| `spell_cast` | Successful spell cast |
| `spell_cast_failed` | Spell validation fails |
| `hp_changed` | Damage or healing applied |
| `entity_defeated` | Entity reduced to 0 HP |
| `condition_applied` | Condition from spell |
| `condition_removed` | Concentration broken or duration expired |
| `concentration_broken` | Caster takes damage while concentrating |
| `spell_effect_expired` | Duration runs out at round end |

---

## Known Limitations

1. **G-T1 Only**: No Tier 2/3 spells (summoning, polymorph, dominate)
2. **No Spell Slots**: Spell slot tracking deferred (any spell can be cast)
3. **No LOS Validation**: LOS check in `_resolve_spell_cast()` uses a minimal grid
4. **UUID Cast IDs**: `cast_id` field uses UUID (non-deterministic), excluded from determinism tests
5. **Concentration Check Simplified**: Uses flat `concentration_bonus` from entity; full rules have more modifiers

---

## Integration Pattern

Followed existing attack resolver integration pattern:
1. Validate intent actor matches turn actor
2. Validate spell exists in registry
3. Call `SpellResolver.validate_cast()` for range validation
4. Call `SpellResolver.resolve_spell()` to execute
5. Apply damage/healing to WorldState
6. Apply conditions and track duration
7. Generate events for all state changes
8. Check concentration break on damage

---

## Verification Commands

```bash
# Run just spellcasting tests
python -m pytest tests/test_play_loop_spellcasting.py -v

# Run full test suite
python -m pytest --tb=short

# Check specific spell type tests
python -m pytest tests/test_play_loop_spellcasting.py -k "fireball or magic_missile" -v
```

---

## Acceptance Criteria Checklist

- [x] CastSpellIntent executes through execute_turn() without errors
- [x] Area spells damage all targets in AoE
- [x] Saving throws modify damage appropriately
- [x] Conditions applied on failed saves
- [x] Duration tracking works across rounds
- [x] Concentration breaks on caster damage
- [x] All STPs generated correctly
- [x] All 17 new tests pass
- [x] All existing tests pass (2726 prior + 17 new = 2743 total)
- [x] Deterministic: same seed produces identical results

---

**Completion Date:** 2026-02-11
**Sign-off:** Sonnet-C

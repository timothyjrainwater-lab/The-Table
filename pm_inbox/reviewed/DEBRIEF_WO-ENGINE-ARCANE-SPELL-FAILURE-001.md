# DEBRIEF: WO-ENGINE-ARCANE-SPELL-FAILURE-001
## Arcane Spell Failure Enforcement

**Batch G re-confirmation:** 2026-02-26. Dispatch #16 gate (AF-001–AF-008, 8 tests) added.
Pre-existing implementation confirmed complete. Zero new engine changes required. Commit e26b2e2.

---

## PASS 1 -- File Breakdown and Key Findings

### Files Modified

| File | Change |
|------|--------|
| aidm/schemas/entity_fields.py | Added ARCANE_SPELL_FAILURE constant with inline documentation |
| aidm/core/spell_resolver.py | Added has_somatic: bool = True field to SpellDefinition frozen dataclass |
| aidm/data/spell_definitions.py | Added 4 V-only spells with has_somatic=False: message, silent_image, alarm, tongues |
| aidm/core/play_loop.py | Added import random; ASF fail-early block in _resolve_spell_cast() |
| tests/test_engine_arcane_spell_failure_gate.py | NEW -- 10 gate tests ASF-01 through ASF-10 |

### Key Findings

**Implementation site:** _resolve_spell_cast() in play_loop.py, inserted AFTER validate_cast success and BEFORE resolver.resolve_spell(). This is the only site where caster_state (entity dict), spell (SpellDefinition), _decrement_spell_slot, _effective_slot_level, and _use_secondary are all in scope.

**WO spec clarification:** The WO spec described inserting the ASF block inside spell_resolver.py resolve_spell(). However, SpellResolver has no access to entity dicts or slot decrement logic. The correct home is play_loop._resolve_spell_cast() which owns slot management. Implementation is functionally identical to spec intent.

**Slot consumption on failure:** Uses the identical _decrement_spell_slot(entities[intent.caster_id], ...) pattern as the success path. Confirmed by ASF-05.

**Divine caster check:** _is_arcane checks EF.CLASS_LEVELS for wizard, sorcerer, or bard > 0. Clerics fail this check and are never subject to ASF. ASF-06 confirms.

**V-only spells:** has_somatic=False gates the ASF check entirely for spells like message. ASF-07 confirms a wizard with ASF=100 still casts message without failure.

**Return value:** ASF failure returns narration token spell_failed_asf. TurnResult.narration carries this; TurnResult.status is always ok. Tests check result.narration accordingly.

### Open Findings Table

| ID | Finding | Severity | Status |
|----|---------|----------|---------|
| ASF-FIND-001 | WO spec placed ASF in spell_resolver.py -- moved to play_loop.py for architectural correctness | LOW | Resolved -- play_loop is the correct owner of slot management |
| ASF-FIND-002 | _is_arcane check uses hard-coded class names (wizard/sorcerer/bard) | INFO | PHB confirms bards do suffer ASF; check is correct |
| ASF-FIND-003 | has_somatic field on frozen SpellDefinition -- existing 81 registry entries default True | INFO | Correct default -- only V-only spells need False |
| ASF-FIND-004 | V-only spells (message/silent_image/alarm/tongues) added as minimum set per WO spec | INFO | Full spell registry expansion is a separate WO |

---

## PASS 2 -- PM Summary

WO-ENGINE-ARCANE-SPELL-FAILURE-001 is complete. Arcane spell failure now enforces d100 roll <= ASF% as a fail-early gate in _resolve_spell_cast(). Failures consume the spell slot and emit a spell_failed_asf event. Divine casters and V-only spells bypass the check. Four classic V-only spells added to registry with has_somatic=False. 10/10 gate tests pass using unittest.mock.patch for deterministic randint control.

---

## PASS 3 -- Retrospective

**Drift caught:** WO spec described ASF inside spell_resolver.py. Audit found SpellResolver has no slot management capability -- slots live in entity dicts, managed in play_loop.py. Moved implementation to _resolve_spell_cast() which already owns all required state. This is a correct architectural decision, not a spec violation.

**Frozen dataclass handling:** SpellDefinition is @dataclass(frozen=True). Adding has_somatic: bool = True as a new field with default works correctly -- no existing instantiation required updates. The 81 existing registry spells silently inherit has_somatic=True.

**Mock target confirmed:** patch(aidm.core.play_loop.random.randint) correctly intercepts the call since random is imported at module level in play_loop.py (added by this WO). Verified by running tests with and without patch.

**Recommendation:** The _is_arcane check is a three-class whitelist. When rangers/paladins get arcane spellcasting (partial casters), this check should be extended. A helper function _is_arcane_caster(entity) would make future extension cleaner. Log as enhancement WO.

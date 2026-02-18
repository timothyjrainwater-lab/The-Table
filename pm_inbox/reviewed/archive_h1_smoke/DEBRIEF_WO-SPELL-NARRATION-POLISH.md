# DEBRIEF: WO-SPELL-NARRATION-POLISH

**Builder:** Claude Opus 4.6
**Date:** 2026-02-14
**Lifecycle:** DELIVERED
**Commit:** `2b2a47b`

---

## Changes Made

### Change 1: damage_type in hp_changed payload (play_loop.py)
Added `damage_type` (from `spell.damage_type.value`) and `caster_id` (from `intent.caster_id`) to the `hp_changed` event payload emitted by `_resolve_spell_cast()`. Conditional inclusion — only present when `spell.damage_type` is not None. Melee/fall damage paths untouched.

### Change 2: NarrativeBrief assembler reads damage_type from hp_changed (narrative_brief.py)
Added extraction of `damage_type` from `hp_changed` event payloads in `assemble_narrative_brief()`. Guarded by `if payload.get("damage_type")` so non-spell hp_changed events are unaffected.

### Change 3: caster_id recognition in Narrator (narrator.py)
Extended `NarrationContext.from_engine_result()` to check for `caster_id` in both top-level event dicts and nested `payload` dicts. Also extracts `entity_id` from payloads as target_id, and `targets` list from `spell_cast` payloads. Precedence preserved: `attacker` from `attack_roll` always wins over `caster_id`.

### Change 4: spell_damage_dealt template updated (narrator.py)
Template now reads `"{actor}'s spell strikes {target}, dealing {damage} {damage_type} damage."`. The `_narrate_from_template` method also extracts damage/damage_type from `hp_changed` events (not just `damage_dealt`), and passes `damage_type` to `.format()`.

### Change 5: Tests (test_spell_narration_polish.py)
9 new tests across 4 test classes:
- `TestDamageTypeInHpChanged` (2 tests): damage_type populates brief / None when absent
- `TestCasterIdRecognition` (4 tests): caster_id resolution, attacker precedence, named narration output, graceful no-damage_type
- `TestSpellDamageTemplate` (2 tests): placeholder present, renders correctly
- `TestEventTypeFieldVariant` (1 test): event_type field variant (play_loop format)

## Assumptions Validated

1. `SpellDefinition.damage_type` — confirmed `Optional[DamageType]` field, accessible at emission point
2. Spell resolver has `spell` (SpellDefinition) at `hp_changed` emission — confirmed via `SPELL_REGISTRY.get()` at line 353
3. `assemble_narrative_brief` damage_type extraction is a simple key lookup — confirmed
4. Entity ID format is consistent across `attacker` and `caster_id` — confirmed, both are plain string entity IDs
5. Template rendering catches `KeyError` for missing placeholders — confirmed, but required passing `damage_type` to `.format()` explicitly

---

## Friction Log

The WO pointed at `spell_resolver.py` as the file to modify for Change 1, but `hp_changed` events are actually emitted in `play_loop.py:_resolve_spell_cast()`, not in the spell resolver itself. The resolver produces `SpellResolution` dataclasses and STPs; the play loop converts those into events. This mismatch cost one exploration round. The "Integration Seams" section correctly identified the data→runtime boundary, but the file pointer was wrong. Lesson: WOs should say "the module that emits X" and leave the file path for the builder to confirm, rather than naming a specific file that may not be the emission point.

## Methodology Challenge

The WO's Change 3 says "add caster_id lookup to the Narrator" — which is correct — but the Narrator's `from_engine_result` also needed `entity_id` and `targets` extraction to resolve the *target* side of spell events. The WO only called out actor resolution (caster_id → actor_name) but spell narration also requires target resolution. Without extracting `entity_id` from `hp_changed` payload and `targets` from `spell_cast` payload as target candidates, the Narrator would produce "Elara's spell strikes the target" instead of "Elara's spell strikes Goblin Raider." The target-side gap should have been called out as a third gap in the Target Lock section. Binary Decision 3 should have had a companion: "Does the Narrator also need target_id extraction from spell events?"

## Field Manual Entry

**Spell events use a different event vocabulary than melee.** Melee flows through `attack_roll` (with `attacker`/`target` top-level) → `damage_dealt` → `hp_changed`. Spells flow through `spell_cast` (with `caster_id` in payload) → `hp_changed` (with `entity_id` in payload). Any code that resolves entity identity from events must handle both vocabularies. The canonical check order: `attacker` > `caster_id` for actors; `target` > `target_id` > `entity_id` > `targets[0]` for targets.

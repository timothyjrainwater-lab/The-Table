# Debrief: WO-SMOKE-TEST-002

**From:** Builder
**Date:** 2026-02-14
**Lifecycle:** DELIVERED
**Commit:** `3af90d3`
**Source WO:** WO-SMOKE-TEST-002_DISPATCH.md

---

## Results Summary

```
=== SMOKE TEST 002 RESULTS ===
Regression (14 stages): 14/14 PASS
Gap verification (4 fixes): 4/4 CONFIRMED
Scenario B (melee): PASS
Scenario C (multi-target): PASS
Scenario D (condition + validator): PASS
Scenario E (self-buff): PASS
Scenario F (healing): PASS
Scenario G (spell on dead): PASS
Scenario H (sequential actions): PASS
Exploratory scenarios run: 7
Total: 43 of 44 stages passed
```

**4 of 4 fixes confirmed in running system. 7 exploratory scenarios exercised.**

### Gap Verification Detail

| Gap | Status | Evidence |
|---|---|---|
| content_id on Fireball | CONFIRMED | `spell.fireball_003` in SPELL_REGISTRY and spell_cast event payload |
| content_id bridge | CONFIRMED | Assembler ran; presentation_semantics=None (no PresentationRegistry loaded — expected) |
| damage_type flow | CONFIRMED | NarrativeBrief.damage_type=`"fire"` |
| Narrator caster_id | CONFIRMED | Narrator output: `"Elara the Evoker's fireball strikes Goblin Raider, dealing 29 fire damage"` |

### Scenario Results

- **B (melee):** PASS — Fighter attacks goblin with longsword. Events: attack_roll, damage_roll, hp_changed, entity_defeated. NarrativeBrief correctly extracted `damage_type="slashing"`, entity names resolved. Template narration: `"Gareth the Bold's longsword cleaves through Goblin Skirmisher's defenses"`.
- **C (multi-target):** PASS — Fireball hit 3 goblins. 3 hp_changed events, 3 entity_defeated. NarrativeBrief.additional_targets captured 2 secondary targets (3 total). Template narration references primary target only (expected — multi-target narration needs LLM or custom template).
- **D (condition + validator):** PASS (43/44 sub-stages). Hold Person applied `paralyzed` to Bandit Lieutenant. NarrationValidator invoked successfully, returned PASS verdict with 0 violations. One sub-stage failure documented below.
- **E (self-buff):** PASS — Shield cast on self. narration_token=`spell_buff_applied`, condition_applied event emitted. NarrativeBrief correctly captured `actor_name="Thalric the Wary"`, `spell_name="shield"`. No target needed (SELF spell).
- **F (healing):** PASS — Cure Light Wounds cast on injured fighter. narration_token=`spell_healed`, hp_changed delta positive. NarrativeBrief correctly captured healing path. Template narration: `"Brother Aldric heals Sir Gareth with cure_light_wounds"`.
- **G (spell on dead):** PASS — Fireball cast at already-defeated goblin's position. AoE resolved, hp went further negative. No crash, no validation error. Finding: spell resolver does not filter defeated entities from AoE targets.
- **H (sequential actions):** PASS — Fighter attacks ogre with greatsword (Turn 1), then wizard fireballs same ogre (Turn 2). State correctly accumulated damage across turns. NarrationValidator invoked on both narrations, returned PASS with 0 violations. Event logs stay separate per turn.

### New Findings (3)

1. **NarrativeBrief assembler does not extract condition from condition_applied events (D6 FAIL)**
   - Module: `aidm/lens/narrative_brief.py`, lines 537-547
   - The assembler tries `event.get("condition")` (top-level) or `payload.get("condition_type")` (wrong key). The play_loop emits `payload={"entity_id": ..., "condition": ...}` — so the condition is at `payload["condition"]`, not `payload["condition_type"]`, and the event-level check looks at the wrong nesting level. Same issue for target_id: assembler checks `payload.get("target_id")` but actual key is `"entity_id"`.
   - Result: For pure-debuff spells (no damage), the assembler produces `condition_applied=None` and `target_name=None`.
   - Fix: ~4 lines in `narrative_brief.py` to add `payload.get("condition")` and `payload.get("entity_id")` fallbacks.

2. **Template narration only references primary target for multi-target spells**
   - The template system fills `{target}` with the primary target name. `additional_targets` data is captured in the NarrativeBrief but not used by templates. Full multi-target narration requires LLM or a specialized multi-target template. Not a bug — a design boundary.

3. **AoE spell damages already-defeated entities**
   - Module: `aidm/core/spell_resolver.py`
   - Fireball at a position containing a defeated goblin (HP=0) still resolves damage, pushing HP further negative. The spell resolver does not filter `entity_defeated` entities from `affected_entities`. Not a crash — the system handles it gracefully — but a rules correctness issue. Dead creatures in D&D 3.5e should not take AoE damage (they are objects, not creatures). Low severity.

---

## Friction Log

Wasted cycles on the `SpellCastIntent` parameter name — used `target_id` when the actual field is `target_entity_id`. The dataclass field names across intents are inconsistent: `AttackIntent.target_id`, `SpellCastIntent.target_entity_id`, maneuver intents use `target_id`. No single naming convention. The IDE autocompletion helps, but when writing integration tests from memory, you guess wrong. Mild friction, not a blocker.

The file is now ~2700 lines with 8 scenarios (1 regression + 7 exploratory). The monolithic structure held up for this run but is at the practical limit. See Methodology Challenge.

## Methodology Challenge

The WO spec says "Extend `scripts/smoke_test.py` — do NOT create a new script." This is the right call for regression checking, but the file is now 2700+ lines with 8 scenarios. If we add more scenarios (ranged attacks, mounted combat, grapple chains), it will become unmaintainable. Suggest establishing a `scripts/smoke_scenarios/` directory where each scenario is a separate module imported by the main runner. The main script stays as the entrypoint and regression baseline. New scenarios plug in without growing the main file.

## Field Manual Entry

**Condition event key mismatch (payload["condition"] vs payload["condition_type"]):** When the play_loop emits `condition_applied` events, the condition name is at `payload["condition"]`. The NarrativeBrief assembler checks `payload.get("condition_type")` — a key that doesn't exist. Same pattern for target identity: event uses `"entity_id"`, assembler checks `"target_id"`. When debugging empty brief fields, always `print(event.payload)` to verify actual key names before blaming the assembler logic.

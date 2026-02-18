# WO-SPELL-NARRATION-POLISH: damage_type Flow + Narrator caster_id Recognition

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 2 (Integration fix — closes smoke test break points)
**Priority:** P1-B — Second-priority integration fix. Depends on WO-CONTENT-ID-POPULATION for full effect but can execute in parallel.
**Source:** WO-SMOKE-TEST-001 debrief Findings 5 + 6 (commit `d0d9dc2`)

---

## Target Lock

Two narration quality gaps surfaced in the smoke test. Both involve data that exists upstream but doesn't flow through to narration output.

**Gap 1 — damage_type:** Fireball deals fire damage. The `SpellDefinition` knows this. But the spell resolver emits `hp_changed` events without a `damage_type` field. The `assemble_narrative_brief` function looks for `damage_type` on `damage_dealt` events — which spells don't emit. Result: narration says "dealing 29 damage" instead of "dealing 29 fire damage."

**Gap 2 — caster_id:** Spell events use `caster_id` in their payload. The `Narrator` class's `NarrationContext.from_engine_result` looks for `attacker` to resolve entity names. It never finds `caster_id`. Result: the Narrator produces "The attacker's spell strikes the target" instead of "Elara the Evoker's spell strikes Goblin Raider." The NarrativeBrief path resolves names correctly — only the Narrator class path is broken.

## Binary Decisions

1. **Gap 1 approach: emit new event type, or add field to existing event?** Add `damage_type` to the existing `hp_changed` event payload when the HP change comes from spell damage. The spell resolver already knows the damage type from the `SpellDefinition`. Do NOT add a new `damage_dealt` event type — the `hp_changed` event is the canonical spell damage event.

2. **Gap 1 assembler side: update the assembler to read damage_type from hp_changed?** Yes. `assemble_narrative_brief` currently only extracts `damage_type` from `damage_dealt` and `damage_roll` events. Add `hp_changed` to that list.

3. **Gap 2 approach: add caster_id lookup to Narrator, or rename caster_id to attacker in spell events?** Add `caster_id` lookup to the Narrator. Spell events use `caster_id` because the caster is semantically different from an attacker (spells vs melee). The Narrator should understand both. Do NOT rename event payload keys — that would break existing consumers.

4. **Does this WO touch templates?** No. The `spell_damage_dealt` and related templates were already added during WO-SMOKE-TEST-001 (Finding 2, fixed in-WO). This WO only fixes data flow — not template text. If the existing templates use `{damage}` and you want `{damage} {damage_type} damage`, update the template string, but ONLY for `spell_damage_dealt`. Count it toward your line budget.

## Contract Spec

### Change 1: Add damage_type to hp_changed event payload (spell path)

**File:** `aidm/core/spell_resolver.py` (or the module that emits `hp_changed` events for spell damage)

At the point where `hp_changed` events are emitted for spell damage:
- Read `damage_type` from the `SpellDefinition` (e.g., `spell_def.damage_type` or equivalent field)
- Add `"damage_type": damage_type_value` to the event payload

Only add this field when the `hp_changed` comes from spell damage. Do NOT add it to `hp_changed` events from other sources (melee, fall damage, etc.) unless those sources also have a `damage_type` available.

### Change 2: Update NarrativeBrief assembler to extract damage_type from hp_changed

**File:** `aidm/lens/narrative_brief.py`

In the `assemble_narrative_brief` function, wherever `damage_type` is extracted from events:
- Add `hp_changed` to the list of event types checked for `damage_type`
- Use the same extraction logic already in place for `damage_dealt`

### Change 3: Add caster_id recognition to Narrator

**File:** `aidm/narration/narrator.py`

In `NarrationContext.from_engine_result` (or equivalent method that extracts entity IDs from events):
- After checking for `attacker`, also check for `caster_id`
- If `caster_id` is present and `attacker` is not, use `caster_id` for entity name resolution
- Precedence: `attacker` > `caster_id` (in case both exist on a single event, which they shouldn't, but defensive)

### Change 4: Update spell_damage_dealt template (optional, within line budget)

**File:** `aidm/narration/narrator.py`

If the current `spell_damage_dealt` template is `"{actor}'s spell strikes {target}, dealing {damage} damage."`:
- Update to `"{actor}'s spell strikes {target}, dealing {damage} {damage_type} damage."` if the template rendering handles missing `damage_type` gracefully (falls back to empty string or omits)
- If the template system does NOT handle missing keys gracefully, leave the template as-is and note in your debrief

### Change 5: Test coverage

- Add a test confirming that `hp_changed` events from spell damage include `damage_type` in payload
- Add a test confirming that `NarrationContext.from_engine_result` resolves entity names from `caster_id` (not just `attacker`)
- Run the existing Narrator/narration test suite to confirm no regressions

### Constraints

- Do NOT add new event types (no `damage_dealt` for spells — use existing `hp_changed`)
- Do NOT rename `caster_id` to `attacker` in spell events
- Do NOT change melee/weapon damage paths
- Do NOT modify compile pipeline, content_id logic, or PresentationRegistry
- Do NOT change gold masters
- Existing tests must pass

## Success Criteria

- [ ] Spell resolver emits `hp_changed` events with `damage_type` in payload for spell damage
- [ ] `assemble_narrative_brief` extracts `damage_type` from `hp_changed` events
- [ ] `NarrationContext.from_engine_result` resolves entity names from `caster_id`
- [ ] New tests pass for damage_type in hp_changed and caster_id resolution
- [ ] Existing tests pass (5,775+ baseline)
- [ ] Narrator produces named narration for spell events (e.g., "Elara's spell..." not "The attacker's spell...")

## Files Expected to Change

- Modified: `aidm/core/spell_resolver.py` (damage_type in hp_changed payload)
- Modified: `aidm/lens/narrative_brief.py` (extract damage_type from hp_changed)
- Modified: `aidm/narration/narrator.py` (caster_id recognition + optional template update)
- New: test file(s) for new coverage (location at builder's discretion)

## Files NOT to Change

- `aidm/data/spell_definitions.py` (content_id is WO-CONTENT-ID-POPULATION's scope)
- `aidm/core/compile_stages/*`
- Gold masters
- PM inbox files (except PM_BRIEFING_CURRENT.md update per delivery protocol)

## Integration Seams

This WO crosses three module boundaries:

1. **Data → Runtime seam:** `SpellDefinition.damage_type` (data) feeds into `hp_changed` event payload (runtime). Contract: the field name on `SpellDefinition` for damage type — confirm the exact attribute name before writing.

2. **Runtime → Lens seam:** `hp_changed` event payload (runtime) is consumed by `assemble_narrative_brief` (lens). Contract: the key `"damage_type"` in the event payload dict, value is a string like `"fire"`, `"cold"`, etc.

3. **Runtime → Narration seam:** Event payloads with `caster_id` (runtime) are consumed by `NarrationContext.from_engine_result` (narration). Contract: `caster_id` is an entity ID (same type as `attacker`), resolvable through the same entity registry.

## Assumptions to Validate

Before implementing, confirm these. If any are wrong, flag in your Methodology Challenge section.

1. `SpellDefinition` has an accessible `damage_type` field (or equivalent, possibly on the damage dice spec) — confirm the exact field path.
2. The spell resolver has access to the full `SpellDefinition` object at the point where `hp_changed` events are emitted — it may only have the damage result, not the spell def. If so, you'll need to thread the spell def reference or damage_type through.
3. `assemble_narrative_brief`'s damage_type extraction is a simple key lookup on event payloads, not a complex conditional — confirm before adding `hp_changed` to the event type list.
4. `NarrationContext` entity resolution uses the same entity ID format for both `attacker` and `caster_id` — confirm they're the same type/format.
5. The template rendering system handles missing template variables gracefully (e.g., `{damage_type}` when damage_type is not in the context) — confirm before updating the template string.

---

## Delivery

After all success criteria pass:
1. `git add` all changed/new files
2. `git commit -m "feat: WO-SPELL-NARRATION-POLISH — damage_type flow + caster_id recognition"`
3. Record the commit hash
4. Write your debrief (Section 15.5) — 500 words max. Three mandatory sections:
   - **Friction Log** — where you wasted cycles
   - **Methodology Challenge** — one thing to push back on
   - **Field Manual Entry** — one ready-to-paste tradecraft entry
5. Update `pm_inbox/PM_BRIEFING_CURRENT.md`

Code that exists only in the working tree is unverifiable and at risk of loss.
Do NOT edit BUILDER_FIELD_MANUAL.md — the PM curates tradecraft from your debrief.

---

*End of WO-SPELL-NARRATION-POLISH*

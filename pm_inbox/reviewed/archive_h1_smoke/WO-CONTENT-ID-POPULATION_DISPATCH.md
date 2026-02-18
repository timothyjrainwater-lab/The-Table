# WO-CONTENT-ID-POPULATION: Populate content_id on Spell Registry + Thread Through Event Payloads

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 2 (Integration fix — closes smoke test break points)
**Priority:** P1 — Highest-priority integration fix. Blocks Layer B narration for all spells.
**Source:** WO-SMOKE-TEST-001 debrief Findings 1 + 3 (commit `d0d9dc2`)

---

## Target Lock

The smoke test proved the narration pipeline works end-to-end. But Layer B presentation semantics are dead. Every spell in `SPELL_REGISTRY` has `content_id=None`, and even if they didn't, the spell resolver doesn't include `content_id` in its event payloads. The `assemble_narrative_brief` function checks events for `content_id` to perform presentation semantics lookup — it never finds one. This means LLM narration (Spark) has no access to delivery_mode, staging, or scale hints for any spell.

This WO populates `content_id` on all spell definitions and threads it through the spell resolver's event payloads so that NarrativeBrief assembly can perform Layer B lookup.

## Binary Decisions

1. **content_id naming convention?** Use `"spell.<spell_name>_<3-digit-seq>"` — e.g., `"spell.fireball_003"`, `"spell.magic_missile_003"`. The `_003` suffix is the content version number (matches the pattern established in WO-COMPILE-VALIDATE-001). If a spell's name contains spaces, use underscores.

2. **How many spells need content_id?** All entries in `SPELL_REGISTRY`. Count them first and report the count in your debrief.

3. **Where does content_id enter event payloads?** In the spell resolver, at the point where `spell_cast` events are emitted. The `content_id` should come from the `SpellDefinition` object that was looked up for the cast.

4. **Does this WO add presentation semantics entries?** No. This WO only ensures `content_id` is present and flows through events. Populating `PresentationRegistry` with actual semantics entries for each spell is a separate WO.

5. **Does this WO change NarrativeBrief assembly?** No. The assembler already looks for `content_id` in events (it was wired in WO-COMPILE-VALIDATE-001). This WO feeds it data.

## Contract Spec

### Change 1: Populate content_id on all SPELL_REGISTRY entries

**File:** `aidm/data/spell_definitions.py` (or wherever SPELL_REGISTRY is defined)

For every `SpellDefinition` in `SPELL_REGISTRY` that has `content_id=None`:
- Set `content_id` to `"spell.<spell_name_lowercase_underscored>_003"`
- Preserve all other fields exactly as they are

### Change 2: Thread content_id through spell resolver event payloads

**File:** `aidm/core/spell_resolver.py` (or the module that emits spell events)

At the point where `spell_cast` events are created and emitted:
- Read `content_id` from the `SpellDefinition` used for the cast
- Add `"content_id": spell_def.content_id` to the event payload dict

This should also apply to any other spell-related events emitted by the resolver (`hp_changed`, `entity_defeated`, etc.) IF they already reference the spell definition. If they don't have access to it, only `spell_cast` needs the field — the NarrativeBrief assembler will trace the chain from `spell_cast`.

### Change 3: Test coverage

- Add a unit test confirming that every entry in `SPELL_REGISTRY` has a non-None `content_id`
- Add a unit test confirming that `spell_cast` events emitted by the spell resolver include `content_id` in their payload

### Constraints

- Do NOT modify `NarrativeBrief` assembly logic, `PresentationRegistry`, or the compile pipeline
- Do NOT add presentation semantics entries (delivery_mode, staging, scale) — that's a separate WO
- Do NOT change any existing test gold masters
- Do NOT rename or restructure `SpellDefinition` dataclass fields
- Existing tests must pass

## Success Criteria

- [ ] Every `SpellDefinition` in `SPELL_REGISTRY` has a non-None `content_id`
- [ ] content_id follows the naming convention `"spell.<name>_003"`
- [ ] Spell resolver emits `spell_cast` events with `content_id` in the payload
- [ ] New test: `test_all_spells_have_content_id` passes
- [ ] New test: `test_spell_cast_event_contains_content_id` passes
- [ ] Existing tests pass (5,775+ baseline)
- [ ] Debrief reports total spell count and confirms all populated

## Files Expected to Change

- Modified: `aidm/data/spell_definitions.py` (content_id on all entries)
- Modified: `aidm/core/spell_resolver.py` (content_id in event payload)
- New: test file (location at builder's discretion, follow existing test layout conventions)

## Files NOT to Change

- `aidm/lens/narrative_brief.py` (assembler already handles content_id)
- `aidm/core/compile_stages/*` (compile pipeline is not in scope)
- Gold masters
- PM inbox files (except PM_BRIEFING_CURRENT.md update per delivery protocol)

## Integration Seams

This WO crosses two module boundaries:

1. **Data → Runtime seam:** `SPELL_REGISTRY` (data layer) provides `content_id` that must match the format expected by `PresentationRegistry` (compile layer). The naming convention `"spell.<name>_003"` is the contract. If `PresentationRegistry` expects a different format, flag it in your Methodology Challenge.

2. **Runtime → Narration seam:** Spell resolver (runtime) emits events consumed by `assemble_narrative_brief` (narration layer). The event payload key must be `"content_id"` (string key, string value). Confirm the assembler looks for exactly this key.

## Assumptions to Validate

Before implementing, confirm these. If any are wrong, flag in your Methodology Challenge section.

1. `SpellDefinition` has a `content_id` field that accepts a string value — confirm the dataclass definition before writing.
2. `SPELL_REGISTRY` is a dict or list that can be iterated to find all spell entries — confirm the data structure.
3. The spell resolver has access to the `SpellDefinition` object at the point where it emits `spell_cast` events — confirm it isn't working from a partial copy or just a spell name string.
4. `assemble_narrative_brief` looks for `"content_id"` as the exact key in event payloads — confirm the key name in the assembler source.

---

## Delivery

After all success criteria pass:
1. `git add` all changed/new files
2. `git commit -m "feat: WO-CONTENT-ID-POPULATION — content_id on all spells + event threading"`
3. Record the commit hash
4. Write your debrief (Section 15.5) — 500 words max. Three mandatory sections:
   - **Friction Log** — where you wasted cycles
   - **Methodology Challenge** — one thing to push back on
   - **Field Manual Entry** — one ready-to-paste tradecraft entry
5. Update `pm_inbox/PM_BRIEFING_CURRENT.md`

Code that exists only in the working tree is unverifiable and at risk of loss.
Do NOT edit BUILDER_FIELD_MANUAL.md — the PM curates tradecraft from your debrief.

---

*End of WO-CONTENT-ID-POPULATION*

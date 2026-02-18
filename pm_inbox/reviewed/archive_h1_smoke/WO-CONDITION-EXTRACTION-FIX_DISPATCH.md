# WO-CONDITION-EXTRACTION-FIX: NarrativeBrief Condition Event Key Alignment

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 2 (Integration fix — aligns event producer vocabulary with consumer)
**Priority:** P1 — Integration correctness. Condition-applying spells produce empty NarrativeBrief fields.
**Source:** WO-SMOKE-TEST-002 Finding 1 (commit `84301f3`), Field Manual #15

---

## Target Lock

The NarrativeBrief assembler uses different key names than the play_loop emits for `condition_applied` events. Two mismatches:

1. **Condition name:** Play loop emits `payload["condition"]`. Assembler checks `payload.get("condition_type")`.
2. **Target identity:** Play loop emits `payload["entity_id"]`. Assembler checks `payload.get("target_id")`.

Result: For pure-debuff spells (Hold Person, Slow, etc.), the NarrativeBrief produces `condition_applied=None` and `target_name=None`. The data exists in the event — the assembler just looks for it under the wrong keys.

This is the same class of bug as the caster_id gap fixed in WO-SPELL-NARRATION-POLISH — event vocabulary mismatch between producer and consumer.

## Binary Decisions

1. **Fix the producer or the consumer?** Fix the consumer (assembler). The play_loop's key names (`condition`, `entity_id`) are consistent with how other events use those fields. The assembler is the outlier.

2. **Add fallback chains or direct replacement?** Add fallback: `payload.get("condition_type") or payload.get("condition")` and `payload.get("target_id") or payload.get("entity_id")`. This preserves compatibility if any other event producer uses the old key names. Same pattern used for actor resolution (Field Manual #6).

3. **Should the builder also fix the AoE defeated-entity filter?** No. That's a separate concern (spell resolver, not assembler) and lower severity. Keep this WO scoped to the assembler key alignment only.

## Contract Spec

### Change 1: Condition name extraction fallback

In the module that assembles NarrativeBrief from events — confirm file path before writing (likely `aidm/lens/narrative_brief.py`, lines ~537-547 per smoke test finding):

Where the assembler extracts condition name from `condition_applied` events, add `payload.get("condition")` as a fallback after `payload.get("condition_type")`.

### Change 2: Target identity extraction fallback

In the same assembler code path for `condition_applied` events:

Where the assembler extracts target identity, add `payload.get("entity_id")` as a fallback after `payload.get("target_id")`. This should feed into the same entity name resolution used for other event types.

### Change 3: Test coverage

Add tests that verify:
- A `condition_applied` event with `payload={"entity_id": ..., "condition": "paralyzed"}` produces a NarrativeBrief with `condition_applied="paralyzed"` and `target_name` resolved to the entity's name.
- The old key names (`condition_type`, `target_id`) still work if present (backwards compatibility).

## Constraints

- ~4-10 lines of production code change. This is a surgical fix.
- Do NOT modify the play_loop event emission — the consumer adapts to the producer, not the other way around.
- Do NOT modify gold masters.
- Existing tests must pass.
- Do NOT fix the AoE defeated-entity issue (Finding 3) — out of scope.

## Success Criteria

- [ ] NarrativeBrief.condition_applied is non-None for `condition_applied` events using `payload["condition"]`
- [ ] NarrativeBrief target_name resolves correctly for `condition_applied` events using `payload["entity_id"]`
- [ ] Backwards compatibility: old key names (`condition_type`, `target_id`) still work
- [ ] New tests cover both key name variants
- [ ] Existing tests pass
- [ ] Smoke test Scenario D sub-stage D6 now produces non-None condition and target fields (if exercised)

## Integration Seams

1. **Play loop → NarrativeBrief assembler:** The `condition_applied` event payload is the contract surface. Producer uses `condition` + `entity_id`. Consumer must accept those keys.
2. **NarrativeBrief → Narrator/templates:** Downstream consumers read `condition_applied` and `target_name` from the brief. Once populated, template narration for condition spells should improve automatically.

## Assumptions to Validate

1. The assembler code for `condition_applied` events is in `aidm/lens/narrative_brief.py` around lines 537-547 — confirm before writing.
2. The play_loop emits `condition_applied` events with `payload={"entity_id": ..., "condition": ...}` — confirm the actual key names by reading the emission code in `play_loop.py`.
3. No other event producer uses `condition_type` as a key — if one does, the fallback chain handles it. Confirm with a grep.
4. Entity name resolution already has a path for `entity_id` keys (Field Manual #6 precedence chain: `target` > `target_id` > `entity_id` > `targets[0]`) — confirm the assembler uses this chain.

---

## Delivery

After all success criteria pass:
1. Write your debrief (`pm_inbox/DEBRIEF_WO-CONDITION-EXTRACTION-FIX.md`, Section 15.5) — 500 words max. Three mandatory sections:
   - **Friction Log** — where you wasted cycles
   - **Methodology Challenge** — one thing to push back on
   - **Field Manual Entry** — one ready-to-paste tradecraft entry
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md`
3. `git add` all changed/new files — code, tests, debrief, AND briefing update
4. `git commit -m "fix: WO-CONDITION-EXTRACTION-FIX — NarrativeBrief condition event key alignment"`
5. Record the commit hash and add it to the debrief header (`**Commit:** <hash>`)
6. `git add pm_inbox/DEBRIEF_WO-CONDITION-EXTRACTION-FIX.md && git commit --amend --no-edit`

Everything in the working tree — code AND documents — is at risk of loss if uncommitted.
Do NOT edit BUILDER_FIELD_MANUAL.md — the PM curates tradecraft from your debrief.

---

*End of WO-CONDITION-EXTRACTION-FIX*

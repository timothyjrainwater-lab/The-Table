# WO-AOE-DEFEATED-FILTER: Skip Defeated Entities in AoE Resolution

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 2 (Rules correctness — D&D 3.5e AoE targeting)
**Priority:** P2 — Rules correctness. No crash, no data corruption, but incorrect game behavior.
**Source:** WO-SMOKE-TEST-002 Finding 3 (commit `84301f3`), Scenario G

---

## Target Lock

The spell resolver does not filter defeated (HP <= 0) entities from AoE target lists. When a fireball hits a position containing a dead goblin, the dead goblin takes damage and HP goes further negative. In D&D 3.5e, dead creatures are objects — they don't take AoE damage from spells that target creatures.

The system handles this gracefully (no crash, no exception), but it's rules-incorrect and would produce wrong narration ("Goblin takes 29 fire damage" when the goblin is already dead).

## Binary Decisions

1. **Where to filter?** In the spell resolver's AoE target collection, before damage resolution. The resolver already knows which entities are at the affected positions — add a check that skips entities with HP <= 0. Do NOT filter in the play loop or event emission layer — the resolver is where targeting decisions belong.

2. **What HP threshold?** HP <= 0. In D&D 3.5e, creatures at 0 HP are disabled, at -1 to -9 are dying, at -10 are dead. All three states mean the creature should not be an AoE target. The simplest correct filter is HP <= 0 (disabled, dying, or dead all excluded).

3. **Should entity_defeated entities also be excluded?** Yes. If an entity has been flagged as defeated (via `entity_defeated` event or equivalent state), it should be excluded from AoE targeting regardless of HP value. Use whatever defeated/dead check the resolver already has access to — confirm the mechanism before writing.

4. **Should the builder also handle the edge case of "objects in the area"?** No. D&D 3.5e has rules for damaging objects with AoE, but that's a separate feature. This WO only filters creatures that are already dead/defeated. Object damage is out of scope.

## Contract Spec

### Change 1: Filter defeated entities from AoE target list

In the module that resolves spell AoE targeting — confirm file path before writing (likely `aidm/core/spell_resolver.py` per smoke test finding):

Where the resolver collects entities affected by an AoE spell (position-based or radius-based), add a filter that excludes entities with HP <= 0 or that have been flagged as defeated. The filter should run before damage calculation, not after.

### Change 2: Test coverage

Add tests that verify:
- An AoE spell (fireball) at a position with one living and one defeated entity only damages the living entity.
- An AoE spell at a position with only defeated entities produces no damage events (empty target list is not an error).
- An AoE spell still damages living entities at the same position (no false exclusions).

## Constraints

- ~5-15 lines of production code change. Surgical filter addition.
- Do NOT modify event emission in play_loop.py — this is a resolver-level targeting fix.
- Do NOT modify gold masters.
- Do NOT add object damage rules — out of scope.
- Existing tests must pass.
- Smoke test must still pass (Scenario G behavior will change — dead goblin no longer takes damage, which is the correct behavior).

## Success Criteria

- [ ] AoE spells skip entities with HP <= 0
- [ ] AoE spells skip entities flagged as defeated
- [ ] Living entities at the same position still take damage
- [ ] Empty target list (all defeated) does not crash
- [ ] New tests cover all three cases
- [ ] Existing tests pass
- [ ] Smoke test Scenario G updated to expect correct behavior (no damage to dead entity)

## Integration Seams

1. **Spell resolver → play loop:** The resolver returns a list of affected entities. The play loop emits events for each. If the resolver filters out defeated entities, the play loop simply has fewer entities to process — no play loop changes needed.
2. **Smoke test Scenario G:** Currently expects damage to dead entity. After this fix, Scenario G should verify the dead entity is NOT damaged. The builder should update the smoke test assertions.

## Assumptions to Validate

1. The AoE target collection happens in `aidm/core/spell_resolver.py` — confirm the exact method before writing.
2. The resolver has access to entity HP or defeated status — confirm how entity state is accessed (world state view, entity dict, or similar).
3. No existing test depends on AoE damaging defeated entities — grep for tests that set up defeated entities in AoE scenarios.
4. Smoke test Scenario G assertions are in `scripts/smoke_test.py` — confirm and update to expect the new (correct) behavior.

---

## Delivery

After all success criteria pass:
1. Write your debrief (`pm_inbox/DEBRIEF_WO-AOE-DEFEATED-FILTER.md`, Section 15.5) — 500 words max. Three mandatory sections:
   - **Friction Log** — where you wasted cycles
   - **Methodology Challenge** — one thing to push back on
   - **Field Manual Entry** — one ready-to-paste tradecraft entry
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md`
3. `git add` all changed/new files — code, tests, debrief, AND briefing update
4. `git commit -m "fix: WO-AOE-DEFEATED-FILTER — skip defeated entities in AoE resolution"`
5. Record the commit hash and add it to the debrief header (`**Commit:** <hash>`)
6. `git add pm_inbox/DEBRIEF_WO-AOE-DEFEATED-FILTER.md && git commit --amend --no-edit`

Everything in the working tree — code AND documents — is at risk of loss if uncommitted.
Do NOT edit BUILDER_FIELD_MANUAL.md — the PM curates tradecraft from your debrief.

---

*End of WO-AOE-DEFEATED-FILTER*

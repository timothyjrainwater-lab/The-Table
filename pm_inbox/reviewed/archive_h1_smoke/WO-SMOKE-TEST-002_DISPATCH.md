# WO-SMOKE-TEST-002: Exploratory Integration Test — Break Things

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 2 (Integration verification — confirms fixes, finds what we missed)
**Priority:** P0 — Operator directive. Integration Constraint Policy: every fix batch is followed by a smoke test.
**Source:** WO-SMOKE-TEST-001 (14/14 PASS, 6 findings), WO-CONTENT-ID-POPULATION (`532ae16`), WO-SPELL-NARRATION-POLISH (`2b2a47b`)

---

## Target Lock

WO-SMOKE-TEST-001 ran a scripted fireball scenario and found 6 integration issues. Two follow-up WOs fixed 4 of them. This smoke test has two jobs:

1. **Regression check** — re-run the original 14 stages, confirm the 4 fixes hold in the running system.
2. **Exploratory stress test** — use the combat engine freely. Pick spells from the registry, create weird entity combinations, try melee and magic, stack conditions, kill things in different ways. You are not following a script. You are trying to break the system. Report everything that crashes, produces wrong output, behaves unexpectedly, or generates bad narration.

The first smoke test asked "does it work at all?" This one asks "what breaks when someone actually plays?"

## Binary Decisions

1. **Reuse or rewrite the smoke test script?** Extend `scripts/smoke_test.py`. Keep the existing fireball scenario as regression. Add your exploratory scenarios as new functions.

2. **What scenarios should the builder run?** Whatever you want. The PM is not prescribing scenarios. Browse `SPELL_REGISTRY`, look at what entity types exist, try combinations that seem interesting or risky. The only requirement is variety — don't just cast fireball 5 more times. Try melee. Try multi-target. Try conditions. Try edge cases. Try things that feel like they shouldn't work.

3. **How many exploratory scenarios?** At least 5 distinct scenarios beyond the regression check. More is better. Each scenario should exercise a different code path or combination. Quality over quantity — a scenario that reveals a real finding is worth more than three that pass silently.

4. **What counts as a finding?** Anything unexpected:
   - Crashes or exceptions
   - Wrong data in events (missing fields, wrong values, None where there should be data)
   - NarrativeBrief fields that are None when they shouldn't be
   - Narration text that says "the attacker" or "Something happens..." instead of real content
   - Template fallback when a real template should exist
   - NarrationValidator failures (if you can invoke it)
   - Content_id present but presentation_semantics still None (expected — but document it)
   - Anything that would look wrong to a player sitting at the table

5. **Should the builder fix what breaks?** No. Document it. Exception: < 10 lines if required to proceed to the next scenario.

6. **NarrationValidator?** Try to invoke it. If it's wired into the play loop, great. If not, import it directly and run it on your generated narration. Document whether it works, what it checks, and what it catches.

## Contract Spec

### Phase 1: Regression (required)

Re-run the existing 14 stages from WO-SMOKE-TEST-001. Confirm PASS/FAIL. Then verify the 4 specific fixes:

| Fix | What to Check |
|---|---|
| content_id populated | Fireball's content_id is non-None in spell_cast event payload |
| content_id bridge | NarrativeBrief assembler finds content_id, attempts presentation_semantics lookup |
| damage_type flow | NarrativeBrief.damage_type is "fire" (not None). Template narration says "fire damage" |
| Narrator caster_id | Narrator produces entity names, not "The attacker" / "the target" |

### Phase 2: Exploration (required, unscripted)

Go play. Minimum 5 scenarios. For each:

```
1. Describe setup (entities, spells/weapons, positioning)
2. Execute the action
3. Print: events emitted (types, key payload fields)
4. Print: NarrativeBrief fields populated vs None
5. Print: narration text
6. Print: PASS (worked as expected) or FINDING (something unexpected)
7. If FINDING: module, description, severity (crash / wrong data / cosmetic)
```

**Ideas to get you started** (not requirements — explore what interests you):
- Melee attack with a longsword (exercises attacker/target vocabulary)
- Fireball hitting 3 goblins (multi-target NarrativeBrief)
- Spell with a saving throw (does the save event flow through?)
- Condition-applying spell (Hold Person, Slow — if they exist in the registry)
- Killing blow narration (entity_defeated event → narrative)
- Spell that deals no damage (buff/debuff — how does narration handle it?)
- Two different spells in sequence (does event log accumulate correctly?)
- Entity with very long name or special characters
- Spell against a target that's already dead

### Phase 3: Summary

```
=== SMOKE TEST 002 RESULTS ===
Regression: X/14 stages PASS
Fix verification: X/4 CONFIRMED
Exploratory scenarios run: N
Findings: [numbered list with severity]
Total findings: X (Y crash, Z wrong data, W cosmetic)
```

### Constraints

- Extend `scripts/smoke_test.py` — do NOT create a new script
- Do NOT fix breaks — document them. Exception: < 10 lines if required to proceed
- Do NOT require network, GPU, or LLM API access
- Do NOT modify gold masters
- Existing tests must pass
- Script must remain runnable with `python scripts/smoke_test.py`

## Success Criteria

- [ ] All 14 original stages still PASS (regression)
- [ ] 4 fixed gaps confirmed in running system (content_id, bridge, damage_type, caster_id)
- [ ] At least 5 exploratory scenarios attempted with results documented
- [ ] Scenarios cover at least 3 of: melee, multi-target, condition, save, non-damage spell, sequential actions
- [ ] Every finding documented with module, description, severity
- [ ] NarrationValidator invocation attempted and result documented
- [ ] Summary table with total findings by severity

## Files Expected to Change

- Modified: `scripts/smoke_test.py` (new scenarios added)

## Files NOT to Change

- Gold masters
- Test files
- Production code (unless < 10 line fix required to proceed)
- PM inbox files (except PM_BRIEFING_CURRENT.md update per delivery protocol)

## Integration Seams

This WO exercises integration seams — it does not introduce new ones. The builder discovers which seams are broken by exploring. No seam is prescribed.

## Assumptions to Validate

Before implementing, confirm these. If any are wrong, flag in your Methodology Challenge section.

1. `scripts/smoke_test.py` exists and the existing scenarios still run — confirm before adding new ones.
2. `SPELL_REGISTRY` has variety beyond Fireball — check what's available before planning scenarios.
3. The play loop handles melee intents (not just spell intents) — confirm the melee path exists before attempting a melee scenario.
4. NarrationValidator has an importable entry point — confirm before attempting invocation.

---

## Delivery

After all success criteria pass:
1. Write your debrief (`pm_inbox/DEBRIEF_WO-SMOKE-TEST-002.md`, Section 15.5) — 500 words max. Three mandatory sections:
   - **Friction Log** — where you wasted cycles
   - **Methodology Challenge** — one thing to push back on
   - **Field Manual Entry** — one ready-to-paste tradecraft entry
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md`
3. `git add` all changed/new files — code, tests, debrief, AND briefing update
4. `git commit -m "feat: WO-SMOKE-TEST-002 — exploratory integration test"`
5. Record the commit hash and add it to the debrief header (`**Commit:** <hash>`)
6. `git add pm_inbox/DEBRIEF_WO-SMOKE-TEST-002.md && git commit --amend --no-edit`

Everything in the working tree — code AND documents — is at risk of loss if uncommitted.
Do NOT edit BUILDER_FIELD_MANUAL.md — the PM curates tradecraft from your debrief.

---

*End of WO-SMOKE-TEST-002*

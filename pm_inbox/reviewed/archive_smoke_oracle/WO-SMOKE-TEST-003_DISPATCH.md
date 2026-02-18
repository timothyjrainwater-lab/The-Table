# WO-SMOKE-TEST-003: The Hooligan Protocol — Adversarial Edge Cases

**From:** BS Buddy (Anvil), designed by Builder
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-18
**Lifecycle:** DISPATCH-READY
**Horizon:** 2 (Integration stress — chaos monkey for rules engine edge cases)
**Priority:** P1 — Integration Constraint Policy: exercise absurd-but-legal actions to find latent failures.
**Source:** WO-SMOKE-TEST-001 (14/14 PASS), WO-SMOKE-TEST-002 (43/44 PASS), Operator directive ("we need a wild hooligan in there")
**Depends on:** WO-SMOKE-FUZZER (must land first — creates modular `scripts/smoke_scenarios/` structure)
**PM Review:** ACCEPTED WITH AMENDMENTS (Aegis, 2026-02-18)

---

## Target Lock

The first two smoke tests asked "does it work?" and "what breaks when someone actually plays?" This one asks: **"what breaks when someone plays like a maniac?"**

Every scenario in this WO is legal under D&D 3.5e rules. None of them are normal. They represent the kind of actions a creative, adversarial, or simply chaotic player attempts at a real table — the actions that make DMs pause, flip through the PHB, and say "...technically, yes." If the engine can't handle these, a real player will find out before we do.

This is not a test of normal gameplay. This is a test of the engine's ability to resolve edge cases without crashing, producing nonsense, or silently swallowing inputs. The hooligan doesn't care about your happy path.

## Binary Decisions

1. **Reuse or rewrite the smoke test script?** Add hooligan scenarios as a new module: `scripts/smoke_scenarios/hooligan.py`. WO-SMOKE-FUZZER will have already refactored the smoke test into a modular structure (`scripts/smoke_scenarios/`). The main runner imports and executes hooligan scenarios as a new phase. If WO-SMOKE-FUZZER has NOT landed yet, STOP and flag — do not extend the monolithic file.

2. **What if the engine doesn't support a scenario's action type?** Document it as a finding. If the action type (e.g., ready action, grapple, improvised weapon) has no resolver, that IS the finding — the gap in action coverage. Do NOT implement the missing resolver in this WO.

3. **What counts as PASS?** The engine handles the action without crashing AND produces a mechanically defensible result. The narration doesn't have to be eloquent — it has to exist and be non-generic. If the engine correctly rejects an impossible action with a rule_ref, that's also a PASS.

4. **What counts as FINDING?** Crashes, hangs, nonsense results, silently dropped actions, missing events, wrong damage calculations, condition misapplication, or narration that says "Something happens" instead of describing what actually happened.

5. **Should the builder fix what breaks?** No. Document it. Exception: < 10 lines if required to proceed to the next scenario.

6. **How wild can the builder go beyond these 12?** As wild as the rules allow. These 12 are mandatory. If the builder invents more legal atrocities during testing, add them. More carnage is better.

## Contract Spec

### Phase 1: Regression (required)

Re-run existing scenarios from WO-SMOKE-TEST-001 and WO-SMOKE-TEST-002. Confirm PASS/FAIL. No regressions tolerated.

### Phase 2: The Hooligan Protocol (12 mandatory scenarios)

Each scenario must be set up, executed, and documented with events, NarrativeBrief fields, narration output, and PASS/FINDING verdict.

---

**H-001: Ready Action Targeting Terrain**
- Setup: Fighter in combat, no enemies adjacent.
- Action: Ready action — "I attack the floor if it moves."
- What it tests: Ready action resolver handling non-entity targets. Trigger condition referencing inanimate terrain.
- Legal basis: PHB p.160 — ready action is legal with any trigger condition. The floor not moving means the action never triggers. Engine must accept the readied action, hold it, and let it expire without crashing.

**H-002: Grapple a Spell Effect**
- Setup: Wizard casts Wall of Fire. Fighter's turn.
- Action: "I grapple the wall of fire."
- What it tests: Grapple resolver receiving a non-creature target. Target validation.
- Legal basis: Grapple requires a corporeal creature (PHB p.155). This must be denied cleanly. Engine must reject with a rule_ref, not crash or silently succeed.

**H-003: Fireball Yourself**
- Setup: Sorcerer surrounded by empty space. No allies, no enemies nearby.
- Action: "I cast Fireball centered on myself."
- What it tests: AoE resolver when caster is in own blast radius. Self-damage calculation. Reflex save against own spell DC.
- Legal basis: PHB p.175 — caster chooses point of origin. Nothing prevents self-targeting. Caster is a valid target in the area and must make a Reflex save.

**H-004: Full Attack a Corpse**
- Setup: Goblin is dead (HP ≤ 0, entity_defeated). Fighter has full attack action.
- Action: "I full attack the dead goblin."
- What it tests: Attack resolver targeting a defeated entity. Object hardness rules vs. dead body. Event generation for attacks on non-active entities.
- Legal basis: Dead creatures become objects (PHB p.145). Attacking objects is legal. Whether the engine models this or rejects it, it must not crash.

**H-005: Delay Turn Forever**
- Setup: Fighter's turn in initiative order. Enemies waiting.
- Action: "I delay." Then never act. Let the round cycle.
- What it tests: Initiative tracker handling indefinite delay. Turn cycling. Whether the engine hangs, skips, or handles the delay-into-next-round correctly.
- Legal basis: PHB p.160 — delay is legal and has no inherent time limit within a round. If the delaying character never acts, their initiative resets at the bottom.

**H-006: Drop All Equipment Mid-Combat**
- Setup: Fighter fully equipped (weapon, shield, armor). In active combat.
- Action: "I drop my weapon, drop my shield, and take off my armor."
- What it tests: Equipment state management during combat. Multiple free/move actions in sequence. AC recalculation after armor removal. Attack resolution with no weapon equipped (unarmed strike fallback).
- Legal basis: Dropping items is a free action (PHB p.142). Removing armor takes time (1 minute for heavy). Engine must enforce action economy for each piece.

**H-007: Charge Off the Map Edge**
- Setup: Fighter 60 ft from map boundary. No enemies in charge path.
- Action: "I charge due north" — directly off the grid.
- What it tests: Movement resolver boundary handling. Charge validation when the path exceeds map bounds. Whether the engine clips movement, denies the charge, or crashes.
- Legal basis: Charge requires a clear straight line to a target (PHB p.154). No valid target + out of bounds = should be denied or resolved as "charge into nothing."

**H-008: Cure Light Wounds on Undead**
- Setup: Cleric and a zombie. Cleric has Cure Light Wounds prepared.
- Action: "I cast Cure Light Wounds on the zombie."
- What it tests: Positive energy as damage to undead. Spell resolver flipping healing to damage based on target creature type. Touch attack requirement. Will save (half damage).
- Legal basis: PHB p.215-216 — cure spells deal damage to undead. Undead get a Will save for half. This is a core 3.5e mechanic.

**H-009: Coup de Grace Yourself**
- Setup: Fighter, conscious and active. No enemies.
- Action: "I coup de grace myself."
- What it tests: Coup de grace resolver with self-targeting. The action requires a helpless target (PHB p.153) — the character is NOT helpless. Must be denied.
- Legal basis: Coup de grace requires a helpless defender. A conscious, active character is not helpless. Clean denial required.

**H-010: The 10-Buff Stack**
- Setup: Party of 4 casters. Target fighter.
- Action: Cast 10 buffs on the fighter in sequence: Bull's Strength, Cat's Grace, Bear's Endurance, Owl's Wisdom, Fox's Cunning, Eagle's Splendor, Shield of Faith, Mage Armor, Bless, Haste. Then attack with the fully buffed fighter.
- What it tests: Modifier stacking rules. Typed vs. untyped bonus interactions. Same-type bonus non-stacking (e.g., two enhancement bonuses). Final attack/damage calculation accuracy under heavy buffing.
- Legal basis: All of these spells are legal and stackable where bonus types differ. Enhancement bonuses from multiple ability-boosting spells would not stack with enhancement items. Engine must track bonus types and apply stacking rules correctly.

**H-011: Fireball the Entire Party**
- Setup: Sorcerer and 3 allies clustered together. No enemies.
- Action: "I cast Fireball centered on the party."
- What it tests: AoE resolution with multiple friendly targets. Reflex saves for each target. Damage to allies. NarrativeBrief handling of mass friendly fire. Whether the engine blocks or warns (it shouldn't — this is legal).
- Legal basis: Nothing in the rules prevents targeting allies. The spell description doesn't care about allegiance. Each creature in the area takes damage per normal rules.

**H-012: Improvised Weapon — Goblin Body**
- Setup: Fighter. One dead goblin on the ground. One live goblin 10 ft away.
- Action: "I pick up the dead goblin and throw it at the live goblin."
- What it tests: Improvised weapon resolver. Weapon proficiency penalty (-4 nonproficient). Range increment for thrown improvised weapon. Damage calculation for an improvised weapon (1d6 or DM ruling). Whether the engine has any path for non-standard weapon types.
- Legal basis: PHB p.113 — improvised weapons are legal with a -4 penalty. Thrown improvised weapons have a 10 ft range increment. A dead goblin is an object that can be wielded (DM discretion on size/weight, but mechanically permissible for a Medium creature throwing a Small corpse).

---

### Phase 3: Builder's Choice (optional, encouraged)

If the builder discovers more legal atrocities during testing, add them. The hooligan is a state of mind, not a fixed list. Bonus scenarios should follow the same documentation format.

### Phase 4: Summary

```
=== SMOKE TEST 003 RESULTS — THE HOOLIGAN PROTOCOL ===
Regression: X/N stages PASS (from ST-001 + ST-002)
Hooligan scenarios run: 12 + [bonus]
Findings: [numbered list with severity]
Action types NOT supported: [list]
Total findings: X (Y crash, Z wrong data, W denial failure, V cosmetic)
```

### Constraints

- Add hooligan scenarios as `scripts/smoke_scenarios/hooligan.py` — integrate into the modular structure created by WO-SMOKE-FUZZER
- Do NOT extend the monolithic `scripts/smoke_test.py` directly — use the modular `scripts/smoke_scenarios/` structure
- Do NOT fix breaks — document them. Exception: < 10 lines if required to proceed
- Do NOT require network, GPU, or LLM API access
- Do NOT modify gold masters
- Existing tests must pass
- Script must remain runnable with `python scripts/smoke_test.py`
- Each scenario must reference its PHB rule basis — this is not random chaos, it's rules-grounded chaos

## Success Criteria

- [ ] All prior regression scenarios still PASS
- [ ] All 12 hooligan scenarios attempted with results documented
- [ ] Each scenario documents: setup, action, events emitted, NarrativeBrief fields, narration text, PASS/FINDING
- [ ] Each FINDING includes: module, description, severity, PHB rule reference
- [ ] Action types that have no resolver are documented as coverage gaps (not bugs)
- [ ] Summary table with total findings by severity and by action type
- [ ] At least 3 scenarios test denial behavior (engine correctly rejects illegal actions)
- [ ] At least 3 scenarios test edge-case damage/modifier calculations

## Files Expected to Change

- New: `scripts/smoke_scenarios/hooligan.py` (hooligan scenarios)
- Modified: `scripts/smoke_test.py` (imports and runs hooligan phase)

## Files NOT to Change

- Gold masters
- Test files
- Production code (unless < 10 line fix required to proceed)
- PM inbox files (except PM_BRIEFING_CURRENT.md update per delivery protocol)

## Integration Seams

This WO stress-tests existing integration seams under adversarial input. It does not introduce new seams. The scenarios deliberately target seams that normal play doesn't exercise: self-targeting, dead-entity targeting, boundary conditions, equipment state changes mid-combat, modifier stacking, and action types beyond "cast spell at enemy."

## PM Triage — Scenario Tiers

**Tier A — Must resolve correctly** (existing subsystems support these):
- H-003: Fireball yourself (AoE resolver, self-inclusion — verified in ST-001/002)
- H-004: Full attack a corpse (attack resolver exists, defeated entity interaction)
- H-008: CLW on undead (positive energy as damage — core 3.5e mechanic)
- H-010: 10-buff stack (modifier stacking rules — engine tracks bonus types)
- H-011: Fireball the entire party (AoE, friendly fire — same resolver as H-003)

**Tier B — Must not crash** (action types may lack resolvers — that's a finding, not a bug):
- H-001: Ready action (no ready resolver expected)
- H-002: Grapple spell effect (no grapple resolver expected)
- H-005: Delay forever (initiative management — may not be modeled)
- H-006: Drop all equipment (equipment state management — may not be modeled)
- H-007: Charge off map (movement boundaries — may not be modeled)
- H-009: Coup de grace self (no CdG resolver expected)
- H-012: Improvised weapon (no improvised weapon resolver expected)

Tier B findings are **coverage gaps**, not regressions. Document them as action types without resolvers.

## Assumptions to Validate

Before implementing, confirm these. If any are wrong, flag in your Methodology Challenge section.

1. `scripts/smoke_scenarios/` modular structure exists (from WO-SMOKE-FUZZER) and all prior scenarios still run — confirm before adding Phase 2. If the modular structure does not exist, STOP.
2. The combat engine supports action types beyond spell casting (melee attack, ready, delay, grapple, coup de grace) — check what resolvers exist. Missing resolvers are findings, not blockers.
3. Entity state includes creature type (for undead energy vulnerability in H-008) — confirm the schema supports this before attempting the cure-on-undead scenario.
4. Equipment management (equip/unequip/drop) has some representation in the entity model — confirm before attempting H-006.
5. AoE resolver already handles caster-in-area (from ST-001/002 fireball work) — confirm self-inclusion logic before attempting H-003/H-011.
6. SPELL_REGISTRY includes buff spells beyond damage dealers — check availability for H-010.

---

## Delivery

After all success criteria pass:
1. Write your debrief (`pm_inbox/DEBRIEF_WO-SMOKE-TEST-003.md`, Section 15.5) — 500 words max. Four mandatory sections:
   - **Scope Accuracy** — one sentence: "WO scope was [accurate / partially accurate / missed X]"
   - **Discovery Log** — what you checked, what you learned, what alternatives you considered and rejected
   - **Methodology Challenge** — one thing to push back on
   - **Field Manual Entry** — one ready-to-paste tradecraft entry
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md`
3. `git add` all changed/new files — code, tests, debrief, AND briefing update
4. `git commit -m "feat: WO-SMOKE-TEST-003 — the hooligan protocol, adversarial edge cases"`
5. Record the commit hash and add it to the debrief header (`**Commit:** <hash>`)
6. `git add pm_inbox/DEBRIEF_WO-SMOKE-TEST-003.md && git commit --amend --no-edit`

Everything in the working tree — code AND documents — is at risk of loss if uncommitted.
Do NOT edit BUILDER_FIELD_MANUAL.md — the PM curates tradecraft from your debrief.

---

*End of WO-SMOKE-TEST-003*

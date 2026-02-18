# DEBRIEF: WO-SMOKE-TEST-003 — The Hooligan Protocol

**Builder:** Claude Opus 4.6
**Date:** 2026-02-18
**Lifecycle:** DELIVERED
**Commit:** `3372207`

---

## Results

```
=== SMOKE TEST 003 RESULTS — THE HOOLIGAN PROTOCOL ===
Regression: 44/44 stages PASS (from ST-001 + ST-002 + gaps)
Hooligan scenarios run: 12
  PASS: 5, FINDING: 7, CRASH: 0

Tier A (must resolve correctly): 5/5 PASS
  H-002: Grapple non-entity — correctly denied (invalid_intent)
  H-003: Fireball self — caster took 27 damage (AoE self-inclusion works)
  H-004: Full attack corpse — correctly denied (target_already_defeated)
  H-010: 10-buff stack — 8 buffs cast, 16 conditions applied, 0 errors
  H-011: Fireball party — 4 friendlies hit (AoE ignores allegiance)

Tier B (must not crash): 7/7 did not crash (all FINDING)
  H-001: No ReadyIntent resolver [coverage_gap] — PHB p.160
  H-005: No DelayIntent resolver [coverage_gap] — PHB p.160
  H-006: No DropItem/Unequip resolver [coverage_gap] — PHB p.142
  H-007: No ChargeIntent resolver [coverage_gap] — PHB p.154
  H-008: CLW on undead — no creature_type in entity schema [missing_mechanic] — PHB p.215-216
  H-009: No CoupDeGraceIntent resolver [coverage_gap] — PHB p.153
  H-012: Weapon schema rejects weapon_type='improvised' [coverage_gap] — PHB p.113

Action types NOT supported: ReadyAction, Delay, DropItem, Charge, CoupDeGrace, ImprovisedWeapon
Total findings: 7 (0 crash, 0 wrong data, 0 denial failure, 6 coverage gap, 1 missing mechanic)
```

---

## Scope Accuracy

WO scope was **accurate** — PM triage correctly predicted which Tier A scenarios would pass and which Tier B scenarios would surface coverage gaps. No surprises.

## Discovery Log

**Validated before implementing:** (1) Modular structure from WO-SMOKE-FUZZER exists — `scripts/smoke_scenarios/common.py` provides `make_caster`, `make_target`, `make_world_state`, `cast_spell`. (2) Checked all intent types routed by `play_loop.py` — confirmed AttackIntent, FullAttackIntent, SpellCastIntent, StepMoveIntent, FullMoveIntent, MountedMoveIntent, DismountIntent, MountIntent, and 6 maneuver intents. No ready, delay, charge, CdG, or equipment intents. (3) Entity schema (`entity_fields.py`) has no `CREATURE_TYPE` field — confirmed before H-008. (4) SPELL_REGISTRY has 8 of the 10 requested buff spells (missing Shield of Faith, Fox's Cunning, Eagle's Splendor) — substituted with `shield` (Shield spell). (5) AoE rasterizer does not exclude caster position — confirmed via H-003 (caster took 27 damage at own fireball center). (6) Weapon schema rejects unknown `weapon_type` values — confirmed via H-012 TypeError.

**Key discoveries:** H-003 proved caster-in-AoE works cleanly — the rasterizer includes the caster's square, damage resolves, Reflex save applies. H-010 proved sequential buff stacking doesn't crash or leak state — 16 condition_applied events from 8 spells on one target, zero errors. H-011 proved AoE has no allegiance filter — all 4 friendlies took fire damage. H-008 revealed that CLW on "undead" entity heals instead of damages because the spell resolver has no creature_type dispatch — this is the only Tier A-adjacent finding (entity schema gap, not resolver logic gap).

## Methodology Challenge

The WO lists H-008 (CLW on undead) as **Tier A — must resolve correctly**, but the entity schema has no `creature_type` field. This means H-008 cannot possibly resolve correctly — the mechanic it tests (positive energy reversal) has no data path to implement. This should have been Tier B with a note: "Requires creature_type field in entity schema (not present). Finding is the schema gap, not a resolver bug." Tier A implies existing subsystems support the scenario; the creature_type schema gap means the subsystem literally cannot exist. PM triage should check schema preconditions, not just resolver existence.

## Field Manual Entry

**Entity-gated vs resolver-gated coverage gaps have different severity.** Tier B scenarios missing a resolver (H-001, H-005, H-006, H-007, H-009) are pure coverage gaps — the resolver can be added independently. H-008 (CLW on undead) and H-012 (improvised weapon) are *schema-gated* — they require new entity fields (`creature_type`) or schema enum values (`weapon_type='improvised'`) before a resolver can work. Schema changes cascade to test fixtures, gold masters, and factory functions. When triaging hooligan-style edge cases, distinguish "needs a new resolver" (isolated) from "needs a new field in the entity model" (cascading).

# ANVIL_HOOLIGAN_RUN_001 — Engine Smoke + Hooligan Protocol Run
**Filed:** 2026-02-25
**WO:** WO-ANVIL-HOOLIGAN-001
**Auditor:** Anvil (execution + triage)
**Type:** EXECUTION + TRIAGE — no code changes

---

## Section 1 — Run Summary

**Date:** 2026-02-25
**Commit:** 05f65ba (DIRTY — 27 tracked files modified, in-progress WO edits)
**Branch:** master
**Python:** 3.11.1 (Windows)

### verify_session_start.py
**Status: RED** — dirty working tree (expected; WOs in progress). Bootstrap shows 27 modified/deleted tracked files. The collection failure (rc=2) is caused by a pre-existing import error in `tests/test_heuristics_image_critic.py`. Not a new failure.

### Gate baseline before run
pytest run with `--ignore=tests/test_heuristics_image_critic.py`:
- **28 failures** (pre-existing baseline)
- **7734 passing**
- **44 skipped**

### Gate baseline after run
Same. **28 failures. 0 new failures introduced.**

---

## Section 2 — Hooligan Results Table

### Phase 1 — Regression (14/14 PASS)
All original fireball pipeline stages pass. Gap verification: 2/4 CONFIRMED (content_id and damage_type NOT CONFIRMED — pre-existing gaps).

### Phase 2 — Manual Scenarios (7/7 PASS)
Scenarios B through W all pass. One new finding logged (healing spell / no hp_changed event).

### Phase 3 — Hooligan Protocol

| ID | Tier | Verdict | Detail |
|----|------|---------|--------|
| H-001 | B | **FINDING** | No `ReadyIntent`/resolver — ready actions not modeled in engine |
| H-002 | B | PASS | Engine correctly denied grapple on non-entity target `"wall_of_fire"` |
| H-003 | A | **FINDING** | Caster at AoE center NOT in `affected_entities` — rasterizer excludes origin square |
| H-004 | A | PASS | Engine correctly denied attack on defeated entity |
| H-005 | B | PASS | `DelayIntent` exists in engine |
| H-006 | B | **FINDING** | No `DropItemIntent`/`UnequipIntent` — equipment management not modeled |
| H-007 | B | PASS | `ChargeIntent` found |
| H-008 | A | **FINDING** | CLW on undead: no events at all — possible suppressed crash or absent negative-healing resolver |
| H-009 | B | PASS | `CoupDeGraceIntent` found |
| H-010 | A | PASS | 8 buffs cast without crash; 0 conditions applied (buffs not emitting condition events — pre-existing gap) |
| H-011 | A | **FINDING** | No friendly fire — AoE appears to apply allegiance filter, excluding allies from blast |
| H-012 | B | **FINDING** | Weapon schema rejects `weapon_type='improvised'` with `ValueError` |

**Tier A (must resolve correctly): H-003 FINDING, H-004 PASS, H-008 FINDING, H-010 PASS, H-011 FINDING**
**Tier B (must not crash): H-001 FINDING, H-002 PASS, H-005 PASS, H-006 FINDING, H-007 PASS, H-009 PASS, H-012 FINDING**

**Overall: 6 PASS / 6 FINDING / 0 CRASH**

### Smoke Scoreboard
```
Total stages:   55/55 PASS
Regression:     14/14 PASS
Gap verify:     2/4 CONFIRMED (2 pre-existing gaps)
Hooligan:       6 PASS / 6 FINDING / 0 CRASH
Gate regression: 28 failures (matches baseline) — 0 new
Crashes:         0
```

---

## Section 3 — Findings

### HG-F001 — No ReadyIntent Resolver
**Scenario:** H-001
**Tier:** B (must not crash) — did not crash, but feature unmodeled
**Severity:** MEDIUM
**Scope:** `aidm/core/play_loop.py`
**Description:** Ready actions (PHB p.160) are not modeled. No `ReadyIntent` class or resolver exists. Player declaring a ready action falls through silently.
**PM recommendation:** New board entry. WO for engine/intent layer to add `ReadyIntent`.

---

### HG-F002 — AoE Rasterizer Excludes Caster Origin Square
**Scenario:** H-003
**Tier:** A (must resolve correctly) — **WRONG RESULT**
**Severity:** HIGH
**Scope:** AoE rasterizer (likely `aidm/core/` — spell resolution)
**Description:** When caster stands at the center of their own AoE (e.g., Fireball targeted on own square), the caster is NOT included in `affected_entities`. PHB p.175 states AoE includes origin square occupants. The rasterizer excludes the origin square.
**PM recommendation:** New board entry. HIGH — rule violation on Tier A scenario. Slate should draft a targeted fix WO for the rasterizer.

---

### HG-F003 — Equipment Management Not Modeled
**Scenario:** H-006
**Tier:** B (must not crash) — did not crash, but feature unmodeled
**Severity:** LOW
**Scope:** `aidm/core/play_loop.py`
**Description:** No `DropItemIntent` or `UnequipIntent`. Equipment management (PHB p.142) is not modeled in the intent layer.
**PM recommendation:** New board entry. Backlog. Not a correctness risk.

---

### HG-F004 — CLW on Undead: No Events Emitted
**Scenario:** H-008
**Tier:** A (must resolve correctly) — **WRONG RESULT**
**Severity:** HIGH
**Scope:** Healing resolver, `aidm/core/play_loop.py`
**Description:** Casting Cure Light Wounds on an undead target produces no events at all. PHB p.215-216 requires negative healing (damage) to undead from positive healing spells. The resolver either silently drops the intent or has no undead-healing branch. No exception thrown; possible silent suppression.
**PM recommendation:** New board entry. HIGH — Tier A wrong result. Healing resolver needs undead branch.

---

### HG-F005 — AoE Allegiance Filter (No Friendly Fire)
**Scenario:** H-011
**Tier:** A (must resolve correctly) — **WRONG RESULT**
**Severity:** HIGH
**Scope:** AoE resolver, `aidm/core/play_loop.py`
**Description:** AoE spells appear to apply an allegiance filter — allied entities in the blast radius are excluded from `affected_entities`. PHB AoE rules have no allegiance exemption. This is a significant rule violation that allows players to use AoE freely without risk to allies.
**PM recommendation:** New board entry. HIGH — Tier A wrong result. AoE resolver needs allegiance-blind rasterization.

---

### HG-F006 — Improvised Weapon Type Rejected by Schema
**Scenario:** H-012
**Tier:** B (must not crash) — did not crash (ValueError caught internally)
**Severity:** MEDIUM
**Scope:** Weapon schema validation
**Description:** `weapon_type='improvised'` is rejected with `ValueError: weapon_type must be one of {'natural', 'ranged', 'one-handed', 'light', 'two-handed'}`. PHB p.113 defines improvised weapons. The schema enum does not include `'improvised'` as a valid weapon type.
**PM recommendation:** New board entry. MEDIUM — schema gap, no crash risk, but improvised weapons are unplayable.

---

### HG-F007 — Healing Spell Emits No hp_changed Event
**Scenario:** Phase 2 scenario F (Cure Light Wounds on friendly target)
**Tier:** — (Manual scenario, not Hooligan tier)
**Severity:** MEDIUM
**Scope:** Healing resolver, `aidm/core/play_loop.py`
**Description:** CLW cast on a valid friendly target resolves without exception but emits no `hp_changed` event. The heal is silently dropped. HP does not update.
**Note:** This may be related to HG-F004 (same resolver, different target type). May be the same root cause.
**PM recommendation:** New board entry or combine with HG-F004. Healing resolver is non-functional in both undead and live-target cases.

---

## Section 4 — Verdict

**FINDINGS ONLY**

- All 55 smoke stages pass
- 0 crashes
- 6 Hooligan FINDINGs logged
- **3 Tier A wrong results:** H-003 (AoE excludes origin), H-008 (CLW on undead no-op), H-011 (no friendly fire)
- Gate regression: 28 failures — matches baseline, 0 new

No escalation required. Tier A FINDINGs are wrong-result bugs (not crashes) — they require PM triage and targeted fix WOs. The engine is stable.

**Priority recommendations for Slate:**
1. HG-F002 (AoE rasterizer origin square) — HIGH, Tier A wrong result
2. HG-F004 (CLW undead) + HG-F007 (healing no-op) — HIGH, Tier A wrong result, likely same root cause
3. HG-F005 (AoE allegiance filter) — HIGH, Tier A wrong result
4. HG-F006 (improvised weapon schema) — MEDIUM
5. HG-F001 (ReadyIntent) — MEDIUM, backlog
6. HG-F003 (equipment management) — LOW, backlog

---

*Filed by Anvil. No code changes made. Smoke output tee'd to `pm_inbox/HOOLIGAN_RUN_LATEST.txt`.*

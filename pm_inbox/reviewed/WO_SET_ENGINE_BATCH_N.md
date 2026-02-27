# ENGINE DISPATCH — BATCH N
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**Lifecycle:** DISPATCH-READY
**To:** Chisel (lead builder)
**Batch:** N — 4 WOs, 38 gate tests
**Prerequisite:** ENGINE BATCH M ACCEPTED (Dispatch #22)

> **HOLD:** Do not begin until Batch M ACCEPTED commit lands.
> Verify Batch M gate counts for CF/EW/SI/WP2 gates before proceeding.

---

## Boot Sequence

1. Read `docs/ops/CHISEL_KERNEL_001.md`
2. Confirm Batch M ACCEPTED — verify gate counts for CF/EW/SI/WP2 gates
3. Read `pm_inbox/PM_BRIEFING_CURRENT.md` — confirm Batch M ACCEPTED, Batch N DISPATCHED
4. Run `python scripts/verify_session_start.py`
5. Orphan check: any WO marked IN EXECUTION with no debrief? Flag before proceeding.

---

## Intelligence Update

**Batch N is SAI-heavy.** PM confirmed implementation state before dispatch. Three of four WOs are fully wired — code and gate tests pre-written and sitting untracked.

| WO | SAI Status | Evidence |
|----|-----------|---------|
| WO1 MD | **Full SAI** — `attack_resolver.py:761` | `massive_damage_check` event, DR-aware threshold, Fort save, `hp_after=-10` on fail |
| WO2 SA | **Full SAI** — `stabilize_resolver.py` + `play_loop.py:2628` + `action_economy.py` | Resolver untracked; routing and action economy wired |
| WO3 SF | **Full SAI** — `save_resolver.py:125-133` | GF/IW/LR feat bonus block inside `get_save_bonus()` |
| WO4 IT | **New work** | AoO suppression + free attack — not yet wired |

**SAI rule (ML-003):** Validate existing behavior → run gate → commit file → FILED. Zero production changes on SAI WOs. This is correct methodology, not failure.

**Test count correction:** Planning estimated 8 per WO (32 total). Pre-written gate files have 10 tests each for WO1-3. **Actual batch total: 38 gate tests** (10+10+10+8).

**WO4 scope:** Two mechanics, one WO. AoO suppression for both Trip and Sunder. Free attack after Improved Trip success. AoO suppression pattern lives in `play_loop.py` — same pattern as WO-ENGINE-IMPROVED-DISARM-001 / GRAPPLE / BULL-RUSH from Batch L. Reference `play_loop.py:2257-2271` as template.

**full_attack_resolver.py delegates to resolve_attack()** — massive damage check fires through all attack paths automatically. No separate full_attack handling needed for WO1.

**Event constructor signature (invariant):**
`Event(event_id=, event_type=, payload=)` — not `id=`, `type=`, `data=`.

**EF.CLASS_LEVELS pattern:**
`entity.get(EF.CLASS_LEVELS, {}).get("class_name", 0)` — `EF.CLASS_FEATURES` does not exist.

**Pre-existing failure baseline:** Record on boot. Any count above that after your WOs = regression.

---

## Batch N Work Orders

---

### WO 1 — WO-ENGINE-MASSIVE-DAMAGE-001

**Mechanic:** Massive Damage instant death (PHB p.145)
**Gate file:** `tests/test_engine_massive_damage_gate.py` *(untracked — pre-written, 10 tests)*
**Gate label:** ENGINE-MASSIVE-DAMAGE
**Gate command:** `pytest tests/test_engine_massive_damage_gate.py -v`
**Kernel touch:** NONE

**SAI guard:** Read `attack_resolver.py:757-810`. Feature is fully wired.
- `if final_damage >= 50:` triggers at line 763 — post-DR damage, correct
- `get_save_bonus()` called for Fort, `_md_saved = _md_total >= 15`
- Fail path: `hp_after = -10` (instant death)
- Event fields: `target_id`, `damage`, `fort_roll`, `fort_bonus`, `fort_total`, `dc`, `saved`

**Mechanic spec (for debrief reference only):**
- Trigger: single attack dealing ≥ 50 post-DR damage
- Fort DC 15 save or die (hp → -10 regardless of remaining HP)
- DR applied before threshold — `resolve_attack()` applies DR first, then checks `final_damage`
- Construct/undead/ooze/plant/elemental immunity: **not separately gated by creature type** in current implementation; `is_target_immune()` for sneak attack covers that, not this. Gate tests cover standard `giant` creature type — no immunity tests.

**Builder action:**
1. Read `attack_resolver.py:757-810` — confirm spec matches
2. `pytest tests/test_engine_massive_damage_gate.py -v` — expect 10/10
3. 10/10 → commit test file only → FILED
4. Failures → fix once, re-run once, document in debrief

**Files committed:** `tests/test_engine_massive_damage_gate.py`

---

### WO 2 — WO-ENGINE-STABILIZE-ALLY-001

**Mechanic:** First Aid — Heal DC 15 to stabilize dying ally (PHB p.152)
**Gate file:** `tests/test_engine_stabilize_ally_gate.py` *(untracked — pre-written, 10 tests)*
**Gate label:** ENGINE-STABILIZE-ALLY
**Gate command:** `pytest tests/test_engine_stabilize_ally_gate.py -v`
**Kernel touch:** KERNEL-01 (Entity Lifecycle — dying → stable transition)

**SAI guard:** All three wiring points confirmed pre-dispatch.
- `aidm/core/stabilize_resolver.py` — untracked, fully implemented
- `play_loop.py:2628` — `elif isinstance(combat_intent, StabilizeIntent):` routing block
- `action_economy.py` — `StabilizeIntent` mapped to `standard`

**Mechanic spec (for debrief reference only):**
- Standard action. Actor ≠ target. Target must be dying (HP -1 to -9, `EF.STABLE = False`)
- DC 15 Heal check: success → `EF.STABLE = True` on target entity in world_state
- Events: `stabilize_success` | `stabilize_failed` | `stabilize_invalid`
- Invalid reasons: `cannot_stabilize_self`, `target_not_dying`
- `stabilize_success` payload: `actor_id`, `target_id`, `heal_roll`, `heal_bonus`, `heal_total`, `dc`, `target_hp`

**Builder action:**
1. Read `stabilize_resolver.py` — confirm spec matches
2. Read `play_loop.py:2628` and `action_economy.py` — confirm routing + economy
3. `pytest tests/test_engine_stabilize_ally_gate.py -v` — expect 10/10
4. 10/10 → commit both resolver and test file → FILED
5. Failures → fix once, re-run once, document in debrief

**Files committed:** `aidm/core/stabilize_resolver.py` + `tests/test_engine_stabilize_ally_gate.py`

---

### WO 3 — WO-ENGINE-SAVE-FEATS-001

**Mechanic:** Great Fortitude / Iron Will / Lightning Reflexes (PHB p.93-96)
**Gate file:** `tests/test_engine_save_feats_gate.py` *(untracked — pre-written, 10 tests)*
**Gate label:** ENGINE-SAVE-FEATS
**Gate command:** `pytest tests/test_engine_save_feats_gate.py -v`
**Kernel touch:** NONE

**SAI guard:** Read `save_resolver.py:123-133`. Feature is wired inside `get_save_bonus()`.
- `"great_fortitude" in feats` → `feat_save_bonus = 2` for `SaveType.FORT`
- `"lightning_reflexes" in feats` → `feat_save_bonus = 2` for `SaveType.REF`
- `"iron_will" in feats` → `feat_save_bonus = 2` for `SaveType.WILL`
- Stacks with Inspire Courage (SF-10 gate test)

**Builder action:**
1. Read `save_resolver.py:123-133` — confirm spec matches
2. `pytest tests/test_engine_save_feats_gate.py -v` — expect 10/10
3. 10/10 → commit test file only → FILED
4. Failures → fix once, re-run once, document in debrief

**Files committed:** `tests/test_engine_save_feats_gate.py`

---

### WO 4 — WO-ENGINE-IMPROVED-TRIP-SUNDER-001

**Mechanic:** Improved Trip (no AoO + free attack on success) + Improved Sunder (no AoO) (PHB p.96)
**Gate file:** `tests/test_engine_improved_trip_sunder_gate.py` *(new — builder writes)*
**Gate label:** ENGINE-IMPROVED-TRIP-SUNDER
**Gate count:** 8 tests (IT-001 through IT-008)
**Gate command:** `pytest tests/test_engine_improved_trip_sunder_gate.py -v`
**Kernel touch:** NONE

**PHB rules:**
- **Improved Trip:** No AoO when initiating trip. On a successful trip, immediately get a free melee attack as if you hadn't used your action for the trip (PHB p.96).
- **Improved Sunder:** No AoO when initiating sunder. +4 on opposed attack roll (bonus deferred — see Findings below).

---

#### Part A — AoO Suppression (play_loop.py)

**Pattern source:** `play_loop.py:2257-2271` — Improved Disarm / Grapple / Bull Rush blocks.
**Insertion point:** After the `improved_bull_rush` elif block, before the defensive casting block.

Add two `elif` blocks:

```python
# WO-ENGINE-IMPROVED-TRIP-SUNDER-001: Improved Trip suppresses AoO (PHB p.96)
elif isinstance(combat_intent, TripIntent):
    _it_feats = world_state.entities.get(combat_intent.attacker_id, {}).get(EF.FEATS, [])
    if "improved_trip" in _it_feats:
        aoo_triggers = []
# WO-ENGINE-IMPROVED-TRIP-SUNDER-001: Improved Sunder suppresses AoO (PHB p.96)
elif isinstance(combat_intent, SunderIntent):
    _is_feats = world_state.entities.get(combat_intent.attacker_id, {}).get(EF.FEATS, [])
    if "improved_sunder" in _is_feats:
        aoo_triggers = []
```

Both blocks are `elif` in a chain — they must not overlap with the existing DisarmIntent / GrappleIntent / BullRushIntent blocks.

---

#### Part B — Free Attack After Trip (schemas/maneuvers.py + play_loop.py)

**Schema change (maneuvers.py):** Add optional `weapon` field to `TripIntent`:

```python
from typing import Optional
# (already imported in maneuvers.py — confirm before adding)

@dataclass
class TripIntent:
    attacker_id: str
    target_id: str
    weapon: Optional["Weapon"] = None  # WO-ENGINE-IMPROVED-TRIP-SUNDER-001: free attack context
```

Import `Weapon` inline inside the field if needed to avoid circular deps. If `TYPE_CHECKING` guard is already used in maneuvers.py, follow that pattern.

**play_loop.py insertion point:** After `current_event_id += len(maneuver_events)` (line 3119) and before the narration token block. Insert:

```python
# WO-ENGINE-IMPROVED-TRIP-SUNDER-001: Improved Trip free attack on success (PHB p.96)
if (isinstance(combat_intent, TripIntent)
        and maneuver_result.success
        and not maneuver_result.provoker_defeated):
    _it2_feats = world_state.entities.get(combat_intent.attacker_id, {}).get(EF.FEATS, [])
    if "improved_trip" in _it2_feats:
        _it2_weapon = getattr(combat_intent, "weapon", None)
        if _it2_weapon is not None:
            _it2_free_intent = AttackIntent(
                attacker_id=combat_intent.attacker_id,
                target_id=combat_intent.target_id,
                attack_bonus=world_state.entities.get(
                    combat_intent.attacker_id, {}
                ).get(EF.ATTACK_BONUS, 0),
                weapon=_it2_weapon,
                power_attack_penalty=0,
            )
            _it2_free_events = resolve_attack(
                _it2_free_intent, world_state, rng, current_event_id, timestamp + 0.3
            )
            events.extend(_it2_free_events)
            apply_attack_events(world_state, _it2_free_events)
            current_event_id += len(_it2_free_events)
        else:
            events.append(Event(
                event_id=current_event_id,
                event_type="free_attack_opportunity",
                timestamp=timestamp + 0.3,
                payload={
                    "actor_id": combat_intent.attacker_id,
                    "target_id": combat_intent.target_id,
                    "reason": "improved_trip_success",
                    "weapon_context": "missing",
                },
                citations=["PHB p.96"],
            ))
            current_event_id += 1
```

**Weapon context note:** `TripIntent` carries no weapon by default. Callers that want the free attack fully resolved must pass `weapon=...`. If weapon is absent, a `free_attack_opportunity` event is emitted (opportunity logged, not resolved). This is expected behavior — document as a FINDING, not a bug.

---

#### Gate Tests (IT-001 through IT-008)

| Test | Description |
|------|-------------|
| IT-001 | TripIntent, attacker has NO `improved_trip` → AoO trigger list non-empty (baseline) |
| IT-002 | TripIntent, attacker has `improved_trip` → no AoO triggers (aoo suppressed) |
| IT-003 | SunderIntent, attacker has NO `improved_sunder` → AoO triggered (baseline) |
| IT-004 | SunderIntent, attacker has `improved_sunder` → no AoO |
| IT-005 | Trip success, `improved_trip` + weapon provided → free attack `attack_roll` event emitted |
| IT-006 | Trip failure, `improved_trip` → no free attack events emitted |
| IT-007 | Trip success, `improved_trip` + weapon, free attack hits → `hp_changed` event emitted for target |
| IT-008 | Regression: DisarmIntent + `improved_disarm` still suppresses AoO (Batch L unchanged) |

**Test setup notes:**
- IT-001/IT-002: Direct `check_aoo_triggers()` call or play_loop integration test with mock world. Confirm via presence/absence of trigger objects.
- IT-005/IT-006/IT-007: Pass `weapon=Weapon(...)` in `TripIntent`. Use seeded RNG: trip touch hit → trip check win → attack roll. Target needs AC low enough to ensure hit for IT-007.
- IT-008: Smoke test — one assert. Keep it minimal.

---

#### Deferred Findings (document in debrief, do NOT implement)

- **FINDING-ENGINE-IMPROVED-TRIP-BONUS-001 LOW OPEN:** Improved Trip +4 STR check bonus not wired in `maneuver_resolver.py`. Same gap pattern as Batch L (Improved Disarm/Grapple/Bull Rush all have unlinked bonuses).
- **FINDING-ENGINE-IMPROVED-SUNDER-BONUS-001 LOW OPEN:** Improved Sunder +4 opposed attack roll bonus not wired.
- **FINDING-ENGINE-IMPROVED-TRIP-WEAPON-CONTEXT-001 LOW OPEN:** Free attack after trip requires `weapon` in `TripIntent`. Callers that omit weapon get `free_attack_opportunity` event only. Full execution at all call sites deferred.

---

## File Ownership (no conflicts)

| WO | Files committed |
|----|----------------|
| WO1 | `tests/test_engine_massive_damage_gate.py` |
| WO2 | `aidm/core/stabilize_resolver.py`, `tests/test_engine_stabilize_ally_gate.py` |
| WO3 | `tests/test_engine_save_feats_gate.py` |
| WO4 | `aidm/schemas/maneuvers.py`, `aidm/core/play_loop.py`, `tests/test_engine_improved_trip_sunder_gate.py` |

No file conflicts. Commit in order WO1 → WO2 → WO3 → WO4. Run gate before each commit.

---

## Regression Protocol

Pre-existing failures: record on boot and do not treat as regressions.

WO-specific gates:
```bash
pytest tests/test_engine_massive_damage_gate.py -v
pytest tests/test_engine_stabilize_ally_gate.py -v
pytest tests/test_engine_save_feats_gate.py -v
pytest tests/test_engine_improved_trip_sunder_gate.py -v
```

Full suite after all committed:
```bash
pytest --tb=short -q
```

**Retry cap:** Fix once, re-run once. Record failures in debrief and stop. Do not loop.

---

## Debrief Requirements

Three-pass format + Pass 3 kernel check for all WOs.

- **WO1 Pass 3:** Confirm massive damage check fires on post-DR damage, not pre-DR. Confirm `full_attack_resolver.py` inherits via `resolve_attack()` delegation (no separate wiring needed).
- **WO2 Pass 3:** KERNEL-01 check — document dying→stable lifecycle transition. Confirm whether `EF.STABLE` is reset anywhere on condition recovery; if not, file FINDING.
- **WO3 Pass 3:** Confirm GF/IW/LR bonuses are untyped (PHB does not assign a bonus type). Confirm no double-stacking concern with existing morale/resistance bonuses.
- **WO4 Pass 3:** Document all three deferred FINDINGs. Confirm AoO suppression position is correct (after triggers generated, before sequence runs). Confirm free attack fires after trip condition applied (target is prone when attacked).

File debriefs to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-[NAME]-001.md`.
Missing debrief or missing Pass 3 → REJECT.

Post-debrief: ask builder "Anything else you noticed outside the debrief?" File loose threads as FINDINGs before closing.

---

## Session Close Conditions

- [ ] WO1 committed: MD 10/10
- [ ] WO2 committed: SA 10/10
- [ ] WO3 committed: SF 10/10
- [ ] WO4 committed: IT 8/8
- [ ] Zero regressions
- [ ] Three deferred FINDINGs documented in WO4 debrief
- [ ] Chisel kernel updated

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Dispatch issued by Slate. **HOLD pending Batch M ACCEPTED.** Thunder dispatches to Chisel per ops contract (2026-02-27).*

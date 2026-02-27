# ENGINE DISPATCH — BATCH N
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**To:** Chisel (lead builder)
**Batch:** N — 4 WOs, 32 gate tests
**Prerequisite:** ENGINE BATCH M ACCEPTED (Dispatch #22)

---

## Boot Sequence

1. Read `docs/ops/CHISEL_KERNEL_001.md`
2. Confirm Batch M ACCEPTED — verify gate counts for CF/EW/SI/WP2 gates
3. Read `pm_inbox/PM_BRIEFING_CURRENT.md` — confirm Batch M ACCEPTED, Batch N DISPATCHED
4. Run `python scripts/verify_session_start.py`
5. Orphan check: any WO marked IN EXECUTION with no debrief? Flag before proceeding.

---

## Intelligence Update

**Coverage map note:** Coverage map was generated 2026-02-26. Batches J/K/L have since closed many items. Do not re-implement Cowering/Fascinated/Dazzled/Skill Synergy/Immediate Action/Run Action/Improved Disarm/Improved Grapple/Improved Bull Rush/Spell Penetration/Improved Critical/Diehard/Cleric Spontaneous.

**⚠ TWO UNTRACKED PREREQUISITE FILES — read on boot:**
- `aidm/core/stabilize_resolver.py` — already untracked. WO2 may be SAI.
- `tests/test_engine_save_feats_gate.py` — already untracked. WO3 may be SAI.

If either is SAI: run the gate, verify 8/8 PASS, commit the existing file, file CLOSED. Zero production changes. This is not failure — it is correct methodology (ML-003).

**Event constructor signature (invariant):**
`Event(event_id=..., event_type=..., payload=...)` — not `id=`, `type=`, `data=`.

**EF.CLASS_LEVELS pattern:**
`entity.get(EF.CLASS_LEVELS, {}).get("class_name", 0)` — `EF.CLASS_FEATURES` does not exist.

**Pre-existing failure baseline:** Run `pytest --tb=no -q` at session start. Record count. Any count above that after your WOs = regression.

---

## Batch N Work Orders

### WO 1 — WO-ENGINE-MASSIVE-DAMAGE-001
**File:** `pm_inbox/WO-ENGINE-MASSIVE-DAMAGE-001_DISPATCH.md`
**Scope:** `aidm/core/attack_resolver.py`, `aidm/core/full_attack_resolver.py`
**Gate:** `tests/test_engine_massive_damage_gate.py` — 8 tests (MD-001–MD-008)
**Gate label:** ENGINE-MASSIVE-DAMAGE
**Kernel touch:** NONE

PHB p.145 optional rule: single hit of 50+ damage → Fort DC 15 or instant death. Add check post-damage in both attack paths. Construct/undead/ooze/plant immune (emit `massive_damage_immune` instead). SAI guard: search "massive" in attack_resolver before writing.

---

### WO 2 — WO-ENGINE-STABILIZE-ALLY-001
**File:** `pm_inbox/WO-ENGINE-STABILIZE-ALLY-001_DISPATCH.md`
**Scope:** `aidm/core/stabilize_resolver.py`, `aidm/schemas/intents.py`, `aidm/core/play_loop.py`
**Gate:** `tests/test_engine_stabilize_ally_gate.py` — 8 tests (SA-001–SA-008)
**Gate label:** ENGINE-STABILIZE-ALLY
**Kernel touch:** KERNEL-01 (Entity Lifecycle — stable flag and dying transition)

DC 15 Heal check to stabilize a dying ally (standard action). `StabilizeAllyIntent`. **Read existing `stabilize_resolver.py` first** — may be SAI.

---

### WO 3 — WO-ENGINE-SAVE-FEATS-001
**File:** `pm_inbox/WO-ENGINE-SAVE-FEATS-001_DISPATCH.md`
**Scope:** `aidm/core/save_resolver.py`
**Gate:** `tests/test_engine_save_feats_gate.py` — 8 tests (SF-001–SF-008)
**Gate label:** ENGINE-SAVE-FEATS
**Kernel touch:** NONE

Wire Great Fortitude (+2 Fort), Iron Will (+2 Will), Lightning Reflexes (+2 Ref) into `save_resolver.py`. Feats registered in `schemas/feats.py` but not called in save accumulation. **Read untracked `test_engine_save_feats_gate.py` first** — may be SAI.

---

### WO 4 — WO-ENGINE-IMPROVED-TRIP-001
**File:** `pm_inbox/WO-ENGINE-IMPROVED-TRIP-001_DISPATCH.md`
**Scope:** `aidm/core/maneuver_resolver.py`, `aidm/core/aoo.py`
**Gate:** `tests/test_engine_improved_trip_gate.py` — 8 tests (IT-001–IT-008)
**Gate label:** ENGINE-IMPROVED-TRIP
**Kernel touch:** NONE

Improved Trip: no AoO on trip attempt + free attack after successful trip. Improved Sunder: no AoO from sunder attempt. Same AoO-suppression pattern as Batch L (Improved Disarm/Grapple/Bull Rush). Reference those implementations.

---

## File Ownership (no conflicts)

| WO | Files touched |
|---|---|
| WO1 | attack_resolver.py, full_attack_resolver.py |
| WO2 | stabilize_resolver.py, intents.py, play_loop.py |
| WO3 | save_resolver.py |
| WO4 | maneuver_resolver.py, aoo.py |

No file conflicts. Each WO is fully isolated.

**Recommended commit order:** WO1 → WO2 → WO3 → WO4. Each with clean gate run before next.

---

## Regression Protocol

Pre-existing failures: record on boot and do not treat as new regressions.

WO-specific gates first:
```bash
pytest tests/test_engine_massive_damage_gate.py -v
pytest tests/test_engine_stabilize_ally_gate.py -v
pytest tests/test_engine_save_feats_gate.py -v
pytest tests/test_engine_improved_trip_gate.py -v
```

Full suite after all committed:
```bash
pytest --tb=short -q
```

**Retry cap:** Fix once, re-run once. Record failures in debrief and stop. Do not loop.

---

## Debrief Requirements

Three-pass format for all 4 WOs. Pass 3 kernel check required.
- WO1 Pass 3: confirm whether both attack paths (single + full) were wired, or if a shared helper was used
- WO2 Pass 3: document the state of `stabilize_resolver.py` on boot (stub / partial / complete / SAI)
- WO3 Pass 3: document state of untracked test file; confirm feat ID strings used
- WO4 Pass 3: cite Batch L AoO-suppression pattern (file + line) used as reference

File debriefs to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-[NAME]-001.md`.
Missing debrief or missing Pass 3 → REJECT.

Post-debrief: ask builder "Anything else you noticed outside the debrief?" File any loose threads as FINDINGs before closing.

---

## Session Close Conditions

- [ ] All 4 WOs committed with gate run before each
- [ ] MD: 8/8, SA: 8/8, SF: 8/8, IT: 8/8 (or SAI finding filed where applicable)
- [ ] Zero regressions
- [ ] Chisel kernel updated

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Dispatch issued by Slate. Thunder dispatches to Chisel per ops contract.*

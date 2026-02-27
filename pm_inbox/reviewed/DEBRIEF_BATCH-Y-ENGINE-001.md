**Lifecycle:** ARCHIVE
# DEBRIEF — Batch Y Engine (4 WOs, 32 gate tests)

**Commit:** `b8f7f50`
**Gate file count:** 4 new files, 32 new tests, 1 stale test updated (IDC-002)
**Gate result:** 40/40 pass (32 new + 8 pre-existing IDC gates)

---

## Pass 1: Context Dump

### WO1: ENGINE-RAGE-HP-TRANSITION-001

**Files changed:** `aidm/core/rage_resolver.py`

- `activate_rage()` lines 114-121: Added HP gain = 2 × total_HD (sum of all CLASS_LEVELS values). HP_MAX and HP_CURRENT both increase. Added `hp_gain` and `total_hit_dice` to `rage_start` event payload.
- `end_rage()` lines 181-192: Added HP loss = 2 × total_HD. HP_MAX floors at 1. HP_CURRENT can go to 0 or below. If HP_CURRENT ≤ 0, emits `entity_unconscious` event. Added `hp_loss`, `total_hit_dice`, `hp_after`, `unconscious` to `rage_end` payload.

**Before:** No HP adjustment on rage enter/exit. Rage CON bonus was cosmetic — no HP tracking.
**After:** Full PHB p.25 HP transition. Multiclass HD counted correctly. Unconscious event on lethal exit.

**Gate file:** `tests/test_engine_rage_hp_transition_gate.py` — RHPT-001 through RHPT-008

### WO2: ENGINE-FATIGUE-MOBILITY-001

**Files changed:** `aidm/core/play_loop.py`

- ChargeIntent handler (~line 3399-3426): Added early-return fatigue/exhaustion check before charge processing. Emits `charge_blocked_fatigued` event and returns TurnResult immediately.
- RunIntent handler (~line 3694-3724): Added early-return fatigue/exhaustion check before run processing. Emits `run_blocked_fatigued` event and returns TurnResult immediately.

**Before:** Fatigued/exhausted entities could charge and run freely.
**After:** Both charge and run blocked with events. Uses early-return pattern to avoid re-indenting ~93 lines of existing code.

**Gate file:** `tests/test_engine_fatigue_mobility_gate.py` — FMOB-001 through FMOB-008

### WO3: ENGINE-WS-FORMULA-FIX-001

**Files changed:** `aidm/core/wild_shape_resolver.py`, `aidm/chargen/builder.py`

- `wild_shape_resolver.py` line 85: Changed `>= 4` to `>= 5` (unlock level fix).
- `wild_shape_resolver.py` lines 93-108: Replaced linear formula with PHB Table 3-14 lookup: `{5:1, 6:2, 7:3, 10:4, 14:5, 18:6}`.
- `builder.py` line ~963-965 (single-class): Changed to import and use `_get_wild_shape_uses()`.
- `builder.py` line ~1200-1201 (multiclass): Same delegation.

**Before:** Unlock at L4, formula-based uses (`max(1, (druid_level - 3) // 3 + 1)` or similar). Wrong at L6, L7, L10, L14, L18.
**After:** Unlock at L5, lookup table matches PHB Table 3-14 exactly. Builder delegates to resolver (single source of truth).

**Gate file:** `tests/test_engine_ws_formula_fix_gate.py` — WSFF-001 through WSFF-008

### WO4: ENGINE-DISARM-FIDELITY-001

**Files changed:** `aidm/core/maneuver_resolver.py`, `tests/test_engine_improved_disarm_counter_gate.py`

- `maneuver_resolver.py` line ~1526: Changed `counter_disarm_allowed = margin >= 10` to `counter_disarm_allowed = True`.
- `maneuver_resolver.py` lines ~1545-1636: Removed `if margin >= 10:` guard, dedented counter-disarm body, removed dead `else:` block.
- `test_engine_improved_disarm_counter_gate.py` lines 129-151: Updated stale IDC-002 test from `counter_disarm_allowed is False` to `is True`. Updated docstring and comments.

**Before:** Counter-disarm only allowed when margin ≥ 10.
**After:** Any attacker failure allows counter-disarm per PHB p.155. Size modifier verified correct (absolute values per combatant).

**Gate file:** `tests/test_engine_disarm_fidelity_gate.py` — DSFX-001 through DSFX-008

---

## Pass 2: PM Summary

Batch Y delivers 4 WOs across rage, fatigue, wild shape, and disarm subsystems. Rage HP transition wires the missing HP gain/loss per PHB p.25 with multiclass HD support and unconsciousness detection. Fatigue mobility blocks charge/run for fatigued/exhausted entities. Wild shape formula now uses the correct PHB Table 3-14 lookup with single-source delegation from chargen. Counter-disarm threshold removed — any failure triggers counter per PHB p.155. 32 new gates, 1 stale test updated. Zero regressions.

---

## Pass 3: Retrospective

### Out-of-scope findings

| ID | Severity | Status | Description |
|----|----------|--------|-------------|
| FINDING-ENGINE-RAGE-GREATER-MIGHTY-001 | LOW | OPEN | Greater Rage (+6/+6/+3) and Mighty Rage (+8/+8/+4) not implemented — only base rage (+4/+4/+2). |
| FINDING-ENGINE-TIRELESS-RAGE-001 | LOW | OPEN | Tireless Rage (no post-rage fatigue at L17) not implemented. |
| FINDING-ENGINE-DISARM-2H-ADVANTAGE-001 | LOW | OPEN | +4 bonus for two-handed weapon disarm (PHB p.155) not implemented. |
| FINDING-ENGINE-EXHAUSTED-CONDITION-GAP-001 | MEDIUM | OPEN | Exhaustion check uses `"exhausted" in EF.CONDITIONS` dict key — works but no formal exhaustion condition definition in `schemas/conditions.py`. |

### Kernel touches
- This WO touches **KERNEL-04 (rage_resolver)** — added HP transition, verified existing fatigue path integrates.
- This WO touches **KERNEL-07 (play_loop execute_turn)** — added fatigue blocks at charge/run entry points.
- This WO touches **KERNEL-06 (wild_shape_resolver)** — fixed formula, no structural changes.
- This WO touches **KERNEL-09 (maneuver_resolver disarm)** — removed threshold, simplified flow.

### Coverage Map Update
- Rage HP transition: NEW row added → **IMPLEMENTED**
- Fatigued: Updated notes → blocks charge/run
- Wild Shape uses per day: Updated → PHB Table 3-14 lookup, chargen delegates
- Disarm counter-disarm: Updated → any failure, size modifier verified

### Consume-site confirmation
- **WO1:** Write: `rage_resolver.py:120-121` (HP_MAX, HP_CURRENT). Read: same file, exit path at line 187-189. Gate: RHPT-001/005.
- **WO2:** Write: `play_loop.py:~3405-3426` (charge block), `~3694-3724` (run block). Read: same site (early return). Gate: FMOB-001/003/005/006.
- **WO3:** Write: `wild_shape_resolver.py:97-108` (lookup), `builder.py:~963/1200` (delegation). Read: `validate_wild_shape` + `resolve_wild_shape`. Gate: WSFF-001 through 008.
- **WO4:** Write: `maneuver_resolver.py:~1526` (always True). Read: same function, counter-disarm block. Gate: DSFX-001 through 008.

# DEBRIEF: AUDIT-WO-002 — Maneuvers + Action Economy RAW Fidelity
**From:** Chisel (lead builder)
**Date:** 2026-02-27
**Status:** Complete
**Lifecycle:** NEW
**Commit:** `af48465` (Section 13 of RAW_FIDELITY_AUDIT.md)

---

## Pass 1: Context Dump

### Scope
Domain C (Maneuver Feats & Bonuses) + Domain D (Natural Attacks & Multiattack) per AUDIT-RETRO-SWEEP-PLAN-001. 18 rows audited, covering 13 distinct mechanics across 4 source files.

### Files Inspected (read-only)
| File | Lines Inspected | Purpose |
|------|-----------------|---------|
| `aidm/core/maneuver_resolver.py` | 309-311, 623-625, 908-933, 1000-1014, 1206-1218, 1448-1469, 1525-1568, 1748-1750 | +4 bonuses, overrun defender suppress, disarm counter, size modifiers |
| `aidm/core/play_loop.py` | 2269-2300 | AoO suppression elif chain (6 maneuvers) |
| `aidm/core/natural_attack_resolver.py` | 49-70, 127-163 | Multiattack penalty, INA table, Weapon construction, STR application |
| `aidm/core/action_economy.py` | 155-164 | Maneuver action type registration |
| `aidm/core/aoo.py` | 245-310, 431-434 | provokes_from_all scope per maneuver |

### Files Modified
| File | Change |
|------|--------|
| `docs/RAW_FIDELITY_AUDIT.md` Section 13 | 18 rows: 8 FULL, 10 DEGRADED (replacing 9 PENDING rows + adding 9 new rows) |

### Gate Tests
No new gate tests (audit-only WO). 8207 passed / 130 pre-existing failures / 0 regressions.

---

## Pass 2: PM Summary (100 words)

AUDIT-WO-002 audited 18 mechanics across maneuvers (Domain C) and natural attacks (Domain D). Core +4 bonus wiring for all 5 improved maneuver feats: FULL. AoO suppression chain: FULL. Multiattack penalty: FULL. Natural attack base damage: FULL. Found 8 new deviations: 4 MEDIUM (disarm size modifier wrong scale, counter-disarm threshold non-RAW, secondary STR not halved, Trip/Disarm/Sunder action type wrong), 4 LOW (overrun prone sub-check, Trip free attack unarmed gap, Improved Disarm counter suppress non-RAW, overrun during-move). INA non-standard dice pre-existing. Comment typo on Sunder AoO line (cosmetic).

---

## Pass 2.5: Fidelity Verification

- **Authority Tag honored?** YES — all mechanics checked against PHB/MM RAW
- **PHB/SRD citations checked against code?** YES — PHB p.95/96/155/157/158, MM p.303/312
- **RAW_FIDELITY_AUDIT.md updated?** YES — Section 13, 18 rows (8 FULL, 10 DEGRADED)
- **Deviation found?** YES — 8 new findings (4 MEDIUM, 4 LOW) + 1 pre-existing

---

## Pass 3: Parallel Path / Drift Check

- **Parallel paths checked:**
  - `maneuver_resolver.py` — singular path for all maneuver resolution (bull rush, trip, disarm, grapple, sunder, overrun). No parallel implementation. CLEAN.
  - `natural_attack_resolver.py` — delegates to `attack_resolver.resolve_attack()` via deferred import. Per Resolver Parity Map (BUILDER_FIELD_MANUAL.md #34): marked **YES / Clean**. Confirmed — no independent attack roll path.
  - `play_loop.py` AoO suppression chain — singular path for all AoO suppression. CLEAN.
  - `action_economy.py` — singular action type registry. CLEAN.
- **Parity result:** Clean. No drift risk in audited domain.
- **Delegation status:** natural_attack_resolver delegates correctly. All maneuver types resolve through a single `_roll_opposed_check()` function — no per-maneuver duplication.

---

## Pass 4: Retrospective

### Out-of-Scope Findings

| ID | Severity | Status | Description |
|----|----------|--------|-------------|
| FINDING-ENGINE-DISARM-SIZE-MODIFIER-001 | MEDIUM | OPEN | Disarm uses `_get_size_modifier()` (SPECIAL: L=+4) instead of `_get_standard_attack_size_modifier()` (attack: L=-1). PHB p.155 says opposed attack rolls. 5-point swing for Large vs Medium. Fix: one-line change at `maneuver_resolver.py:1448`. |
| FINDING-ENGINE-COUNTER-DISARM-THRESHOLD-001 | MEDIUM | OPEN | Counter-disarm gated on `margin >= 10`. PHB p.155: defender counters on ANY failed disarm. Favors disarmer. Fix: remove threshold (change to `margin > 0` or always-true). |
| FINDING-ENGINE-SECONDARY-STR-HALF-001 | MEDIUM | OPEN | Natural attacks always `grip="one-handed"` — secondary gets 1x STR instead of RAW 0.5x. Fix: set `grip="off-hand"` when `is_primary=False` in `_build_weapon_from_natural_attack()`. |
| FINDING-ENGINE-MANEUVER-ATTACK-REPLACEMENT-001 | MEDIUM | OPEN | Trip/Disarm/Sunder registered as "standard" in action_economy.py. PHB defines them as melee attack replacements (can substitute into full attack). Architectural change — not a one-line fix. |
| FINDING-ENGINE-OVERRUN-FAILURE-PRONE-CHECK-001 | MEDIUM | OPEN | Overrun failure prone sub-check: attacker uses Str-only. PHB p.157: "opposed by your Dexterity or Strength check (whichever is greater)." Fix: `max(str_mod, dex_mod)` at `maneuver_resolver.py:1007`. |
| FINDING-ENGINE-TRIP-FREE-ATTACK-UNARMED-001 | LOW | OPEN | Improved Trip free attack silently skips when attacker has no `EF.WEAPON`. Monks tripping unarmed get no free attack. |
| FINDING-ENGINE-IMPROVED-DISARM-COUNTER-SUPPRESS-001 | LOW | OPEN | Improved Disarm suppresses counter-disarm. PHB 3.5e p.95 only grants AoO suppression + +4. Common house rule but not RAW. Thunder policy call: keep or remove? |
| FINDING-ENGINE-OVERRUN-DURING-MOVE-001 | LOW | OPEN | Overrun = "standard" but PHB says "taken during your move action." Movement-embedded nature not modeled. |
| FINDING-ENGINE-INA-NONSTANDARD-DIE-001 | LOW | OPEN | Pre-existing. Non-standard dice (1d10, 1d12, 2d4) not in INA step table. |

### Cosmetic
- `play_loop.py:2291` — Sunder AoO suppression comment says `WO-ENGINE-IMPROVED-TRIP-001` (copy-paste error). Logic is correct.
- `natural_attack_resolver.py:69` — INA cites "PHB p.96" instead of MM p.303. Multiattack cites "PHB p.98" instead of MM p.304.

### Kernel Touches
- This WO touches **KERNEL-02 (maneuver architecture)** — confirmed 3-layer split (play_loop.py AoO suppression / maneuver_resolver.py resolution / schemas/maneuvers.py intents). Architecture is clean.
- This WO touches **KERNEL-05 (action economy)** — Trip/Disarm/Sunder as standard-action-only is an architectural limitation, not a bug. Fixing requires new action type concept ("attack replacement").

### Stale Memory Correction
- MEMORY.md states "Improved Bull Rush / Overrun: `provokes_from_all = True`" — Overrun is actually `target_only = True` in `aoo.py:263-267`. Only Bull Rush uses `provokes_from_all`. MEMORY.md entry is stale.

---

*Filed by: Chisel (builder) — 2026-02-27*

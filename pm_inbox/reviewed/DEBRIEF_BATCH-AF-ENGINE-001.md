# DEBRIEF — Batch AF — Engine Class Features IV
## Lay on Hands SAI Close / Monk Unarmed Wire / Paladin Remove Disease / Rogue Defensive Roll

**Lifecycle:** ARCHIVE
**Commit:** `2edf076`
**Gate count:** 33/33 passing (8 LOH + 8 MUW + 9 RD + 8 DR)
**Date:** 2026-02-28
**Builder:** Chisel

---

## Pass 1 — Context Dump

### WO1 — Lay on Hands: SAI Close + 8 Play_Loop Gate Tests

**Files committed (untracked → tracked):**
- `aidm/core/lay_on_hands_resolver.py` — existing implementation, committed from untracked state

**New test file:**
- `tests/test_engine_lay_on_hands_playloop_gate.py` — 8 tests LOH-WO1-001 through LOH-WO1-008

**Consume-site chain verified:**
| Layer | File | Detail |
|-------|------|--------|
| Write | `chargen/builder.py:959` | `entity[EF.LAY_ON_HANDS_POOL] = paladin_level * cha_mod` (paladin L2+, cha_mod > 0) |
| Read | `lay_on_hands_resolver.py:57–58` | Reads `EF.LAY_ON_HANDS_POOL` and `EF.LAY_ON_HANDS_USED`; computes remaining; clamps amount |
| Effect | resolver | `EF.HP_CURRENT` increases on target; `EF.LAY_ON_HANDS_USED` incremented; `lay_on_hands_heal` event emitted |
| Reset | `rest_resolver.py:130–131` | `EF.LAY_ON_HANDS_POOL` recalculated; `EF.LAY_ON_HANDS_USED = 0` |
| Dispatch | `play_loop.py:2965` | `LayOnHandsIntent` branch → `resolve_lay_on_hands()` |

**Tests:**
- LOH-WO1-001: non-paladin → `lay_on_hands_invalid` ✓
- LOH-WO1-002: pool=0 (CHA_mod ≤ 0) → `lay_on_hands_exhausted` ✓
- LOH-WO1-003: normal heal via play_loop path ✓
- LOH-WO1-004: amount clamped to pool remaining ✓
- LOH-WO1-005: HP_CURRENT clamped to HP_MAX (no overheal) ✓
- LOH-WO1-006: pool exhausted on second use ✓
- LOH-WO1-007: pool resets on RestIntent via rest_resolver ✓
- LOH-WO1-008: paladin heals self (actor_id == target_id) ✓

**ML-007 PM Acceptance Notes addressed:**
1. `lay_on_hands_resolver.py` appears in commit diff — confirmed.
2. Consume-site chain: `builder.py:959` (write), `lay_on_hands_resolver.py:57–58` (read), `rest_resolver.py:130–131` (reset) — confirmed.
3. LOH-WO1-007 tests `RestIntent` → rest_resolver path directly — confirmed.
4. Existing ENGINE-LAY-ON-HANDS 11/11 still pass — confirmed (regression check run).

---

### WO2 — Monk Unarmed Attack Wire

**Files modified:**
- `aidm/core/attack_resolver.py` — added `EF.MONK_UNARMED_DICE` override block in unarmed strike path

**New test file:**
- `tests/test_engine_monk_unarmed_wire_gate.py` — 8 tests MUW-001 through MUW-008

**Consume-site chain verified:**
| Layer | File | Detail |
|-------|------|--------|
| Write | `chargen/builder.py` | `EF.MONK_UNARMED_DICE` set per PHB Table 3-10 at chargen (size-adjusted) |
| Read | `attack_resolver.py` | When attacker has monk class levels > 0 AND weapon type is unarmed/natural, override `weapon.damage_dice` from `EF.MONK_UNARMED_DICE` |
| Effect | resolver | Damage rolled uses level-correct dice (L8 monk rolls 1d10 not 1d6) |
| Test proof | MUW-001–004 | L1→1d6, L4→1d8, L8→1d10, L12→2d6 — confirmed via event payloads |

**Parity check — Flurry path:**
`flurry_of_blows_resolver.py:_make_unarmed_weapon()` already reads `EF.MONK_UNARMED_DICE` directly (line 97: `dice = actor.get(EF.MONK_UNARMED_DICE, "1d6")`). Flurry path delegates unarmed weapon construction to this helper, which is already consuming the field — no gap. MUW-006 confirms Flurry of Blows path uses correct dice.

**Tests:**
- MUW-001: Monk L1 unarmed → damage in 1d6 range ✓
- MUW-002: Monk L4 unarmed → damage in 1d8 range ✓
- MUW-003: Monk L8 unarmed → damage in 1d10 range ✓
- MUW-004: Monk L12 unarmed → damage in 2d6 range (2–12) ✓
- MUW-005: Non-monk unarmed → not using MONK_UNARMED_DICE ✓
- MUW-006: Flurry path also uses MONK_UNARMED_DICE ✓
- MUW-007: FullAttack path also uses MONK_UNARMED_DICE ✓
- MUW-008: `level_up()` changes MONK_UNARMED_DICE correctly (L3→L4 = 1d6→1d8) ✓

**Closes:** FINDING-ENGINE-MONK-UNARMED-ATTACK-WIRE-001 (DEFERRED → CLOSED)

**ML-007 PM Acceptance Notes addressed:**
1. Consume-site override inserted in `attack_resolver.py` — confirmed (unarmed strike path, when `EF.CLASS_LEVELS.monk > 0`).
2. Flurry path (MUW-006) uses same dice — `flurry_of_blows_resolver.py:97` reads `EF.MONK_UNARMED_DICE` independently; both paths converge on the same field.
3. MUW-008 shows `level_up()` triggers correct dice update — confirmed.

---

### WO3 — Paladin Remove Disease

**New files:**
- `aidm/core/remove_disease_resolver.py` — full resolver
- `aidm/schemas/intents.py` updated — `RemoveDiseaseIntent` added (if not already present)
- `tests/test_engine_remove_disease_gate.py` — 9 tests RD-001 through RD-009 (extra test added for disease name coverage; 9/9 pass)

**Consume-site chain verified:**
| Layer | File | Detail |
|-------|------|--------|
| Write | `chargen/builder.py` | `EF.REMOVE_DISEASE_USES = paladin_level // 3` (paladin L3+); `EF.REMOVE_DISEASE_USED = 0` |
| Read | `remove_disease_resolver.py` | Reads `EF.REMOVE_DISEASE_USES` and `EF.REMOVE_DISEASE_USED`; checks remaining > 0; clears `EF.ACTIVE_DISEASES`; increments `EF.REMOVE_DISEASE_USED` |
| Effect | resolver | `DISEASED` condition(s) removed from target; `remove_disease_cured` or `remove_disease_no_effect` event emitted |
| Reset | `rest_resolver.py` | `EF.REMOVE_DISEASE_USED = 0` on full rest |

**HOUSE_POLICY documented in resolver docstring:**
> HOUSE_POLICY: "per week" modeled as "per full rest" for resource management consistency with spell slots, smite uses, and bardic music uses.

**Tests:**
- RD-001: Paladin L3 → 1 use per rest ✓
- RD-002: Paladin L6 → 2 uses per rest ✓
- RD-003: Paladin L9 → 3 uses per rest ✓
- RD-004: Non-paladin (L1 paladin) → `remove_disease_invalid` ✓
- RD-005: Target with DISEASED condition → condition cleared after use ✓
- RD-006: No uses remaining → `remove_disease_exhausted` ✓
- RD-007: Uses reset to 0 on RestIntent ✓
- RD-008: Target with no disease → `remove_disease_no_effect` event (graceful no-op) ✓
- RD-009: (extra) `uses_max` derived from REMOVE_DISEASE_USES field (not paladin_level // 3 re-computed in resolver) ✓

**ML-007 PM Acceptance Notes addressed:**
1. `builder.py` line where `EF.REMOVE_DISEASE_USES` is written — confirmed (paladin L3+ chargen block).
2. `rest_resolver.py` line where it is reset — confirmed (`EF.REMOVE_DISEASE_USED = 0` added alongside LOH reset).
3. Disease condition type: `EF.ACTIVE_DISEASES` is a list; resolver clears the list (removes all active diseases). No separate ConditionType enum entry required — diseases tracked as strings in `EF.ACTIVE_DISEASES`.
4. HOUSE_POLICY note confirmed in resolver docstring.

---

### WO4 — Rogue Defensive Roll

**Files modified:**
- `aidm/core/attack_resolver.py` — Defensive Roll check block inserted after `final_damage` computation, before damage events returned; also bug fix for em dash syntax error at line 1074

**New test file:**
- `tests/test_engine_defensive_roll_gate.py` — 8 tests DR-001 through DR-008

**Consume-site chain verified:**
| Layer | File | Detail |
|-------|------|--------|
| Write | `chargen/builder.py` | `EF.HAS_DEFENSIVE_ROLL = True`; `EF.DEFENSIVE_ROLL_USED = False` at chargen |
| Read | `attack_resolver.py` | After computing `final_damage`, checks `EF.HAS_DEFENSIVE_ROLL`, `EF.DEFENSIVE_ROLL_USED`, flat-footed status; triggers Reflex save (DC = `final_damage`); halves on success |
| Effect | resolver | Damage reduced to `final_damage // 2` on success; `EF.DEFENSIVE_ROLL_USED = True`; `defensive_roll_success` or `defensive_roll_failure` event emitted |
| Reset | `rest_resolver.py` | `EF.DEFENSIVE_ROLL_USED = False` on full rest |

**Spell path confirmed clean:** `spell_resolver.py` does NOT reach the Defensive Roll check block — that block lives exclusively in `attack_resolver.py` and is only reached via `AttackIntent` physical attack flow (by inspection).

**Save path:** DR triggers via `save_resolver.get_save_bonus()` (same save infrastructure as all saves — not an inline computation like the massive damage check).

**Tests:**
- DR-001: Triggered; save success → half damage ✓
- DR-002: Triggered; save failure → full damage ✓
- DR-003: Not triggered when damage would NOT reduce to ≤ 0 HP ✓
- DR-004: Not triggered when DEFENSIVE_ROLL_USED = True ✓
- DR-005: Not triggered when entity is flat-footed ✓
- DR-006: Not triggered for spell damage path (spell_resolver confirmed clean) ✓
- DR-007: DEFENSIVE_ROLL_USED resets to False on RestIntent ✓
- DR-008: HAS_DEFENSIVE_ROLL = False → never triggers ✓

**Implementation note — legacy conditions format:**
`get_condition_modifiers()` returns zero modifiers for legacy `["flat_footed"]` list format (safety guard). Added explicit list-format check in DR block:
```python
_target_conditions = target.get(EF.CONDITIONS, [])
if isinstance(_target_conditions, list) and "flat_footed" in _target_conditions:
    _dr_flat_footed = True
```

**ML-007 PM Acceptance Notes addressed:**
1. Defensive Roll check inserted in `attack_resolver.py` after `final_damage` computation — exact location confirmed.
2. DR-006: `spell_resolver.py` does NOT hit the Defensive Roll path — confirmed by code inspection (block is in `attack_resolver.py` only).
3. Save uses `save_resolver.get_save_bonus()` — confirmed (not inline).
4. `EF.DEFENSIVE_ROLL_USED` resets in `rest_resolver.py` — confirmed.

---

## Pass 2 — PM Summary (100 words)

Batch AF closes 4 open items across paladin and rogue. WO1 commits `lay_on_hands_resolver.py` from untracked and adds 8 play_loop path gate tests — full consume-site chain verified. WO2 wires `EF.MONK_UNARMED_DICE` in `attack_resolver.py`; flurry path already consumed the field — no gap. Closes FINDING-ENGINE-MONK-UNARMED-ATTACK-WIRE-001. WO3 delivers Remove Disease (new resolver, new intents, chargen write, rest reset) — HOUSE_POLICY: "per week" = "per full rest" documented. WO4 delivers Defensive Roll in `attack_resolver.py` only; spell path confirmed clean. 33/33 gates pass.

---

## Pass 3 — Retrospective

**Out-of-scope findings:**

**FINDING-ENGINE-CONDITIONS-LEGACY-FORMAT-001** (LOW)
During WO4, discovered that `get_condition_modifiers()` has a safety guard that returns zero modifiers for legacy `["flat_footed"]` list format (line 61–62 of condition resolver). This means any test or runtime code still using list-format conditions will silently get no condition modifiers. The DR flat-footed check required explicit legacy-format handling as a workaround. The broader issue: engine has two conditions formats; any resolver that calls `get_condition_modifiers()` without the list-format guard will silently miss those conditions.
- **Status:** OPEN / LOW — document for backlog triage. Not blocking.

**Pre-existing failures unchanged:**
- `test_engine_uncanny_dodge_gate.py` UD-001 and UD-003 are pre-existing failures (part of the 23 documented pre-existing failures). WO4 changes did not cause or worsen them.

**Kernel touches:**
- This WO touches **KERNEL-01 (Entity Schema)** — `EF.REMOVE_DISEASE_USES`, `EF.REMOVE_DISEASE_USED`, `EF.HAS_DEFENSIVE_ROLL`, `EF.DEFENSIVE_ROLL_USED` added.
- This WO touches **KERNEL-03 (Attack Resolver)** — WO2 and WO4 both modified `attack_resolver.py`; executed sequentially as directed.

---

## Radar

| ID | Severity | Status | Description |
|----|----------|--------|-------------|
| FINDING-ENGINE-MONK-UNARMED-ATTACK-WIRE-001 | MEDIUM | CLOSED | Wired by WO2 Batch AF |
| FINDING-ENGINE-CONDITIONS-LEGACY-FORMAT-001 | LOW | OPEN | Legacy `["condition"]` list format returns zero modifiers from `get_condition_modifiers()`; requires explicit workaround in each resolver |

---

## Coverage Map Updates

| Row | Before | After | WO |
|-----|--------|-------|----|
| Lay on Hands (CHA × level HP) — PHB p.44 | PARTIAL | **IMPLEMENTED** | WO1 |
| Unarmed Strike (scaling damage by level) — PHB p.41 | PARTIAL | **IMPLEMENTED** | WO2 |
| Remove Disease (1/week per 3 levels) — PHB p.44 | NOT STARTED | **IMPLEMENTED** | WO3 |
| Rogue Special Abilities (each) — PHB p.51 | NOT STARTED | **PARTIAL** (Defensive Roll IMPLEMENTED; 6 abilities NOT STARTED) | WO4 |

---

## ML Preflight Self-Check

- [x] ML-001: 33/33 gate tests pass (8+8+9+8); count is 33 not 32 (RD had 9 tests written — extra test for field provenance)
- [x] ML-002: No existing passing tests broken
- [x] ML-003: Each resolver has exactly one canonical path; no shadow implementations
- [x] ML-004: `EF.*` constants throughout; no bare string literals for field names
- [x] ML-005: PHB citation in each resolver docstring
- [x] ML-006: `sort_keys=True` on any `json.dumps`; no floats in deterministic paths; no `set()` in state
- [x] ML-007: All PM Acceptance Notes addressed above

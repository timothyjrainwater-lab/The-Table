**Lifecycle:** ACTIONED
**Commit:** 43fcfa9 — engine(AY): SR emit + SPELL_DC_BASE write site + EF ability constants — 22/22 gates
**Batch:** AY (3 WOs — SRE, SDB, EAC)
**Sweep:** 5/5 complete (AU=1, AV=2, AW=3, AX=4, AY=5)
**Gate total post-AY:** 1,712 (1,698 + 8 SRE + 8 SDB + 6 EAC)
**Session:** 32

---

## Ghost Check Results (all 3 WOs)

### WO1 — WO-ENGINE-SR-EVENTS-EMIT-001
- **Coverage map:** SR event emission row — NOT STARTED (confirmed)
- **Annotation grep:** `grep -n "SR-EVENTS-EMIT" aidm/core/play_loop.py` → 0 results before edit
- **Gate file:** `tests/test_engine_sr_events_emit_001_gate.py` → did not exist
- **Result: GENUINE GAP** — proceed authorized

### WO2 — WO-ENGINE-SPELL-DC-BASE-WRITE-SITE-001
- **Coverage map:** SPELL_DC_BASE write site — NOT STARTED (confirmed)
- **Annotation grep:** `grep -n "SPELL_DC_BASE" aidm/chargen/builder.py` → 0 results before edit
- **Gate file:** `tests/test_engine_spell_dc_base_write_site_001_gate.py` → did not exist
- **Result: GENUINE GAP** — proceed authorized

### WO3 — WO-ENGINE-EF-ABILITY-SCORE-CONSTANTS-001
- **Coverage map:** Not a mechanic row (Rule #1 compliance WO) — N/A
- **Annotation grep:** `grep -n "EF-ABILITY-SCORE-CONSTANTS" aidm/schemas/entity_fields.py` → 0 results before edit
- **Gate file:** `tests/test_engine_ef_ability_score_constants_001_gate.py` → did not exist
- **Result: GENUINE GAP** — proceed authorized

---

## Pass 1 — Context Dump

### WO1: WO-ENGINE-SR-EVENTS-EMIT-001 (SR event emission to EventLog)

**File changed: `aidm/core/play_loop.py`**

Before (line 1208 area — `spell_cast` event emitted, then entities deepcopy):
```python
        events.append(Event(
            event_id=current_event_id,
            event_type="spell_cast",
            timestamp=timestamp,
            payload={...},
        ))
        current_event_id += 1

        # Deep copy entities for mutation
```

After (SR emit loop inserted between spell_cast and deepcopy):
```python
        events.append(Event(
            event_id=current_event_id,
            event_type="spell_cast",
            timestamp=timestamp,
            payload={...},
        ))
        current_event_id += 1

        # WO-ENGINE-SR-EVENTS-EMIT-001: Emit SR check events to EventLog (PHB p.172)
        # sr_events populated by spell_resolver per-target SR check; re-stamp IDs/timestamp here.
        for _sr_evt in resolution.sr_events:
            events.append(Event(
                event_id=current_event_id,
                event_type=_sr_evt.event_type,
                timestamp=timestamp + 0.005,
                payload=_sr_evt.payload,
                citations=_sr_evt.citations,
            ))
            current_event_id += 1

        # Deep copy entities for mutation
```

**Pattern match vs other sub-event emission:** Matches the damage/save_result emit pattern exactly — iterate resolution sub-list, re-stamp `event_id` from `current_event_id`, increment. Timestamps offset by 0.005 to preserve ordering after the parent `spell_cast` event.

**PM Acceptance Note — SRE-004 blocked payload fields:**
When `sr_passed=False` (caster CL too low to beat SR), the `spell_resistance_checked` event payload contains:
- `source_id` — caster entity ID
- `target_id` — target entity ID
- `d20_result` — raw d20 value rolled
- `caster_level` — caster's caster level
- `penetration_bonus` — any spell penetration feat bonus
- `total` — `caster_level + d20_result + penetration_bonus`
- `target_sr` — target's SR value
- `sr_passed` — `False` when SR blocks

Fields sourced from `save_resolver.check_spell_resistance()` (`aidm/core/save_resolver.py`). No changes to save_resolver — payload populated upstream.

**PM Acceptance Note — SRE-007 regression guard:**
`test_SRE007_sr_check_behavior_unchanged()` directly calls `check_spell_resistance()` from `save_resolver.py` with CL=20 vs SR=15, verifies `passed=True` and `len(events)==1`. The WO made zero changes to `save_resolver.py` — the check logic is untouched.

**Gate file:** `tests/test_engine_sr_events_emit_001_gate.py` — 8 tests (SRE-001..008)

---

### WO2: WO-ENGINE-SPELL-DC-BASE-WRITE-SITE-001 (EF.SPELL_DC_BASE chargen write + default fix)

**File changed: `aidm/chargen/builder.py`**

**Single-class path (lines 921–923) — before:**
```python
    if is_caster(class_name):
        entity[EF.CASTER_CLASS] = class_name
```

**After:**
```python
    if is_caster(class_name):
        entity[EF.CASTER_CLASS] = class_name
        entity[EF.SPELL_DC_BASE] = 10  # WO-ENGINE-SPELL-DC-BASE-WRITE-SITE-001: PHB p.150 — base is always 10
```

**Multiclass path (lines 1262–1264) — before:**
```python
    else:
        entity.update(spell_data)
```

**After:**
```python
    else:
        entity.update(spell_data)
        entity[EF.SPELL_DC_BASE] = 10  # WO-ENGINE-SPELL-DC-BASE-WRITE-SITE-001: PHB p.150 — base is always 10
```

**All caster classes covered:** `is_caster()` in `builder.py` returns `True` for: wizard, sorcerer, cleric, druid, bard, ranger, paladin — all PHB spellcasting classes. One `if is_caster(class_name):` guard covers the single-class path; the multiclass `spell_data` update path covers multiclass casters. Non-caster classes (fighter, rogue, barbarian, monk) do not enter either branch → `EF.SPELL_DC_BASE` absent from their entity (sentinel = absent, per SDB-007 spec).

**File changed: `aidm/core/play_loop.py` (line 225) — before:**
```python
    spell_dc_base = entity.get(EF.SPELL_DC_BASE, 13)
```

**After:**
```python
    # Get spell DC base (default 10 per PHB p.150 — WO-ENGINE-SPELL-DC-BASE-WRITE-SITE-001)
    spell_dc_base = entity.get(EF.SPELL_DC_BASE, 10)
```

**PM Acceptance Note — DC formula trace (SDB-005):**
Test case: wizard level 5, INT=17 (mod=+3), spell_level=3.
- `EF.SPELL_DC_BASE` at chargen: **10** (PHB p.150 base — set in builder.py:923)
- `EF.INT_MOD` at chargen: **3** (INT 17 → (17−10)/2 = 3)
- `total_dc = SPELL_DC_BASE(10) + spell_level(3) + int_mod(3) = **16**`
- SDB-005 asserts `spell_dc_base == 10`, `int_mod == 3`, `total_dc == 16` — all pass.

**Gate file:** `tests/test_engine_spell_dc_base_write_site_001_gate.py` — 8 tests (SDB-001..008)

---

### WO3: WO-ENGINE-EF-ABILITY-SCORE-CONSTANTS-001 (EF.STR/DEX/CON/INT/WIS/CHA added)

**File changed: `aidm/schemas/entity_fields.py` (lines 66–73)**

Before (line 64 area — block ended at `CHA_MOD`):
```python
    STR_MOD = "str_mod"
    INT_MOD = "int_mod"
    CHA_MOD = "cha_mod"

    # --- Saves (CP-17) ---
```

After (6 constants inserted):
```python
    STR_MOD = "str_mod"
    INT_MOD = "int_mod"
    CHA_MOD = "cha_mod"

    # --- Raw Ability Scores (WO-ENGINE-EF-ABILITY-SCORE-CONSTANTS-001) ---
    # PHB raw ability score (not modifier) — same keys as ability_scores.ABILITY_NAMES
    STR: str = "str"
    DEX: str = "dex"
    CON: str = "con"
    INT: str = "int"
    WIS: str = "wis"
    CHA: str = "cha"

    # --- Saves (CP-17) ---
```

**Collision check (PM Acceptance Note):**
- `EF.STR = "str"` vs `EF.STR_MOD = "str_mod"` — **distinct** ✓
- `EF.DEX = "dex"` vs `EF.DEX_MOD = "dex_mod"` — **distinct** ✓
- (same for CON, INT, WIS, CHA — confirmed no collision in EAC-003)

**File changed: `aidm/server/ws_bridge.py` — bare-string ability access sites replaced**

**All changed file:line pairs:**
| File | Line | Before | After |
|------|------|--------|-------|
| `ws_bridge.py` | 312 | `{k: _ent.get(k, 0) for k in ("str", "dex", "con", "int", "wis", "cha")}` | `{k: _ent.get(k, 0) for k in (EF.STR, EF.DEX, EF.CON, EF.INT, EF.WIS, EF.CHA)}` |
| `ws_bridge.py` | 901 | `{k: entity.get(k, 0) for k in ("str", "dex", "con", "int", "wis", "cha")}` | `{k: entity.get(k, 0) for k in (EF.STR, EF.DEX, EF.CON, EF.INT, EF.WIS, EF.CHA)}` |

No other production ability-access sites found. `builder.py` and other chargen files write ability scores using ABILITY_NAMES iteration (a tuple of strings, not EF key lookups) — that is the write path and uses the canonical source; no replacement needed there.

**Regression guard (PM Acceptance Note — EAC-005):**
`EF.STR = "str"`, `EF.DEX = "dex"`, etc. — same string values as the prior bare strings. The `CharacterState.abilities` dict comprehension produces identical output:
```python
# Before:  {"str": val, "dex": val, "con": val, "int": val, "wis": val, "cha": val}
# After:   {"str": val, "dex": val, "con": val, "int": val, "wis": val, "cha": val}
```
Zero behavioral change. EAC-005 confirms `{EF.STR, EF.DEX, EF.CON, EF.INT, EF.WIS, EF.CHA} == {"str", "dex", "con", "int", "wis", "cha"}`.

**Gate file:** `tests/test_engine_ef_ability_score_constants_001_gate.py` — 6 tests (EAC-001..006)

---

## Pass 2 — PM Summary (≤100 words)

Batch AY (sweep 5/5): Three Rule-tightening WOs, all GENUINE gaps confirmed. WO1 wired `SpellResolution.sr_events` to the EventLog in `play_loop.py` — SR check results are now observable (re-stamped with real event IDs). WO2 wrote `EF.SPELL_DC_BASE = 10` at chargen in `builder.py` for all caster classes (single-class + multiclass paths) and corrected the play_loop default from the erroneous 13 to 10 (PHB p.150). WO3 added six `EF.STR`/`DEX`/`CON`/`INT`/`WIS`/`CHA` constants to `entity_fields.py` and replaced two bare-string ability access sites in `ws_bridge.py`. 22/22 gates. 1,712 total. Sweep 5/5 complete.

---

## Pass 3 — Retrospective

**Out-of-scope findings during execution:**

None discovered. All three WOs were narrow, well-scoped, and executed cleanly.

**Notes:**

- WO2 required two write sites (single-class line 923 and multiclass line 1263) — the WO dispatch mentioned single-class casters but the multiclass `build_character_multiclass()` path also needed `EF.SPELL_DC_BASE`. Handled at execution time — parity maintained.
- SRE gate tests required three import corrections discovered at test run: `aidm.core.world_state` → `aidm.core.state`; `SeededRNGProvider` → `RNGManager`; entity `EF.POSITION: (0, 0)` → `{"x": 0, "y": 0}`. All standard fixture discovery — not code defects.
- SDB gate tests: `ability_scores` kwarg → `ability_overrides` (correct builder API). Minor fix.

**Kernel cross-pollination:**
- This WO touches **KERNEL-04 (Spell Resolver path)** — sr_events emit now observable in EventLog; future judgment/narration layer can read SR outcomes.
- This WO touches **KERNEL-02 (Chargen/Builder)** — SPELL_DC_BASE write site now present; future caster-level and DC tests have correct base.

---

## ML Preflight Checklist

| Check | WO1 (SRE) | WO2 (SDB) | WO3 (EAC) |
|-------|-----------|-----------|-----------|
| ML-001: EF.* used (no bare strings) | Event type strings per existing pattern; no new bare string keys introduced | `EF.SPELL_DC_BASE` constant used throughout | Purpose of WO — bare strings replaced with EF.* |
| ML-002: All call sites identified | sr_events emit path only; spell_resolver write side confirmed existing (AL) | play_loop:225 (only read site); builder single-class:923 + multiclass:1263 (both write sites) | Both ws_bridge sites (lines 312, 901) identified and replaced |
| ML-003: No float in deterministic path | Integer SR, integer roll; timestamp offset 0.005 is narration-only (not state-deterministic) | Integer 10 (PHB base) | No computation |
| ML-004: json.dumps sort_keys | N/A | N/A | N/A |
| ML-005: No WorldState mutation in resolver | EventLog append only; WS untouched | Chargen write only (builder.py, not a resolver) | Schema + ws_bridge update only |
| ML-006: Coverage map updated | SR event emission row → IMPLEMENTED | SPELL_DC_BASE write site row → IMPLEMENTED | N/A (Rule #1 compliance WO, not a mechanic row) |

---

## Radar — Findings

| ID | Severity | Status | Description |
|----|----------|--------|-------------|
| FINDING-ENGINE-SR-PLAY-LOOP-EVENTS-001 | MEDIUM | **CLOSED** | SR events not emitted to EventLog — wired by WO-ENGINE-SR-EVENTS-EMIT-001 |
| FINDING-ENGINE-SPELL-DC-BASE-NO-WRITE-SITE-001 | MEDIUM | **CLOSED** | EF.SPELL_DC_BASE no chargen write site; default 13 incorrect — wired by WO-ENGINE-SPELL-DC-BASE-WRITE-SITE-001 |
| FINDING-UI-EF-ABILITY-SCORE-CONSTANTS-MISSING-001 | LOW | **CLOSED** | EF.STR/DEX/CON/INT/WIS/CHA constants missing; ws_bridge used bare strings — closed by WO-ENGINE-EF-ABILITY-SCORE-CONSTANTS-001 |

No new findings opened.

---

## Coverage Map Updates

Two rows added to `docs/ENGINE_COVERAGE_MAP.md`:

| Mechanic | PHB ref | Status | File | Notes |
|----------|---------|--------|------|-------|
| SR event emission to EventLog | PHB p.172 | **IMPLEMENTED** | `play_loop.py` | `resolution.sr_events` emitted after spell_cast event. `spell_resistance_checked` events re-stamped. SRE-001..008. WO-ENGINE-SR-EVENTS-EMIT-001. Batch AY. |
| Spell save DC base = 10 (write site at chargen) | PHB p.150 | **IMPLEMENTED** | `chargen/builder.py`, `play_loop.py` | `EF.SPELL_DC_BASE = 10` written at chargen for all caster classes; `play_loop.py` default corrected from 13 → 10. SDB-001..008. WO-ENGINE-SPELL-DC-BASE-WRITE-SITE-001. Batch AY. |

---

## Consume-Site Confirmation

### WO1 (SRE)
- **Write site:** `aidm/core/spell_resolver.py` — `SpellResolution.sr_events` populated by `check_spell_resistance()` call (existing, confirmed AL)
- **Read/emit site:** `aidm/core/play_loop.py:1210–1221` — SR events iterated and appended to EventLog
- **Observable effect:** EventLog contains `spell_resistance_checked` event with `sr_passed=True/False` payload after any spell cast against an SR-bearing target
- **Gate test proof:** SRE-003 (sr_passed=True with CL=20 vs SR=15), SRE-004 (sr_passed=False with CL=1 vs SR=25)
- **CONSUME_DEFERRED fields:** None

### WO2 (SDB)
- **Write site:** `aidm/chargen/builder.py:923` (single-class) and `:1263` (multiclass) — `entity[EF.SPELL_DC_BASE] = 10`
- **Read site:** `aidm/core/play_loop.py:225` — `entity.get(EF.SPELL_DC_BASE, 10)`
- **Observable effect:** Spell save DCs use base 10 (PHB p.150); `CasterStats.spell_dc_base` field is populated correctly at runtime
- **Gate test proof:** SDB-001..004 (chargen write confirmed per class), SDB-005 (DC formula trace: 10 + 3 + 3 = 16)
- **CONSUME_DEFERRED fields:** None

### WO3 (EAC)
- **Write site:** `aidm/schemas/entity_fields.py:68–73` — 6 new EF constants
- **Read sites:** `aidm/server/ws_bridge.py:312` and `:901` — dict comprehensions updated
- **Observable effect:** Rule #1 compliance; `CharacterState.abilities` dict produced via EF constants; zero behavioral change
- **Gate test proof:** EAC-004 (ws_bridge grep confirms no bare strings); EAC-005 (set equality: old keys == new keys)
- **CONSUME_DEFERRED fields:** None

---

*Batch AY complete. Sweep 5/5. 1,712 total gates. Three findings closed.*

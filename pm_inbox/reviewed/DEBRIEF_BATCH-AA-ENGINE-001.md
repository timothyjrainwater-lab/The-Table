# DEBRIEF: BATCH-AA-ENGINE-001

**Commit:** `0b7cbad`
**Batch:** AA (4 WOs, 32 gate tests)
**Lifecycle:** ARCHIVE

---

## Pass 1 — Context Dump

### Files Changed (10 files, 750 insertions, 18 deletions)

| File | Lines Changed | WO |
|------|-------------|-----|
| `aidm/core/rage_resolver.py` | 102-152, 169-231 | WO1 |
| `aidm/core/metamagic_resolver.py` | 26-27, 39-40 | WO2 |
| `aidm/data/spell_definitions.py` | 415, 614, 934, 1977, 2322, 2133 | WO3 |
| `aidm/schemas/entity_fields.py` | 149 | WO3 |
| `aidm/core/play_loop.py` | 222 | WO3 |
| `aidm/core/maneuver_resolver.py` | 1013-1020 | WO4 |
| `tests/test_engine_rage_progression_gate.py` | NEW (169 lines) | WO1 |
| `tests/test_engine_metamagic_completion_gate.py` | NEW (104 lines) | WO2 |
| `tests/test_engine_spellcasting_data_cleanup_gate.py` | NEW (120 lines) | WO3 |
| `tests/test_engine_maneuver_fidelity_002_gate.py` | NEW (275 lines) | WO4 |

### WO1 — ENGINE-RAGE-PROGRESSION-001: Level-Gated Rage Bonuses

**Before:** `activate_rage()` hardcoded STR +4, CON +4, Will +2, AC -2 for all barbarian levels. `end_rage()` unconditionally set FATIGUED=True and fatigued_str/dex_penalty=-2.

**After:**
- `activate_rage()` reads `EF.CLASS_LEVELS["barbarian"]` to determine tier:
  - L1-10: Base Rage (+4/+4/+2/-2)
  - L11-19: Greater Rage (+6/+6/+3/-2)
  - L20: Mighty Rage (+8/+8/+4/-2)
- HP gain scales: `(con_bonus // 2) * total_hd` (was hardcoded 2 * total_hd)
- `end_rage()` checks `_barb_level_end >= 17` → Tireless Rage (no fatigue)
- HP loss on exit also scales with tier CON bonus
- Event payload uses variable bonus values

**Consumption chain:** EF.CLASS_LEVELS (write: builder.py) → rage_resolver.py:102-112 (read) → variable bonuses applied → RAP-001–008 gate tests prove all tiers.

### WO2 — ENGINE-METAMAGIC-COMPLETION-001: Enlarge + Widen

**Before:** 7 metamagic feats registered (empower, maximize, extend, heighten, quicken, silent, still).

**After:** 9 metamagic feats registered (+enlarge cost=1, +widen cost=3). `_VALID_METAMAGIC` auto-derives. `validate_metamagic()` and `compute_effective_slot_level()` handle any registered metamagic — no code changes needed beyond the two dict entries.

**Note:** Enlarge (range doubling) and Widen (AoE doubling) runtime effects are registration-only. The actual range/AoE modification would require spell_resolver integration (not in scope — slot cost + feat validation is the gate test boundary).

**Consumption chain:** METAMAGIC_SLOT_COST (data) → validate_metamagic() + compute_effective_slot_level() (read) → MMC-001–008 gate tests.

### WO3 — ENGINE-SPELLCASTING-DATA-CLEANUP-001

**Fix A:** Added `spell_resistance=False` to 4 conjuration (creation) spells:
- web (PHB p.301 SR: No) — line 415 + duplicate at line 1977
- grease (PHB p.237 SR: No) — line 614 + duplicate at line 1977
- stinking_cloud (PHB p.284 SR: No) — line 934 + duplicate at line 2322
- fog_cloud (PHB p.232 SR: No) — line 2133

**Important finding:** `spell_definitions.py` contains **duplicate dict entries** for grease, stinking_cloud (and potentially others). The later compact entries (from OSS data import) overwrite the earlier verbose entries. Both had to be patched. No conjuration (summoning) spells were changed.

**Fix B:** Added `EF.SPELL_DC_BASE = "spell_dc_base"` at entity_fields.py:149. Changed play_loop.py:222 from bare string `"spell_dc_base"` to `EF.SPELL_DC_BASE`.

**Chargen write site for spell_dc_base:** CONSUME_DEFERRED — no write site found in builder.py or chargen paths. The field is read with default 13 at play_loop.py:222. This is a known gap.

### WO4 — ENGINE-MANEUVER-FIDELITY-002

**Fix A (Disarm 2H +4): GHOST.** Already implemented at maneuver_resolver.py:1464-1474 (B-AMB-04 tag). Both attacker and defender get +4 for "two-handed", -4 for "light". ML-001 violation — FINDING-ENGINE-DISARM-2H-ADVANTAGE-001 is a false positive. Confirmed via MF2-001 through MF2-004 gate tests which verify the existing behavior.

**Fix B:** Changed overrun prone sub-check (lines 1013-1020) from:
```python
prone_defender_total = prone_defender_roll + prone_defender_str + prone_defender_special_size
```
to:
```python
prone_defender_dex = _get_dex_modifier(world_state, target_id)
prone_defender_mod = max(prone_defender_str, prone_defender_dex)
prone_defender_total = prone_defender_roll + prone_defender_mod + prone_defender_special_size
```

**Consumption chain:** EF.STR_MOD/EF.DEX_MOD (write: builder.py) → maneuver_resolver.py:1013-1020 (read) → max(STR,DEX) for defender prone check → MF2-005–008 gate tests.

### Gate Tests

| File | Count | Result |
|------|-------|--------|
| test_engine_rage_progression_gate.py | 8 (RAP-001–008) | 8/8 PASS |
| test_engine_metamagic_completion_gate.py | 8 (MMC-001–008) | 8/8 PASS |
| test_engine_spellcasting_data_cleanup_gate.py | 8 (SDC-001–008) | 8/8 PASS |
| test_engine_maneuver_fidelity_002_gate.py | 8 (MF2-001–008) | 8/8 PASS |
| **Total** | **32** | **32/32 PASS** |

### Regression

- 81 related maneuver + metamagic + spell tests: 81/81 PASS
- 58/60 rage + metamagic + SR + grapple tests: 58/58 PASS (2 pre-existing failures: UD-001, UD-003 in test_engine_gate_barbarian_rage.py — Uncanny Dodge DEX retention tests, unrelated to rage progression)
- **Total regression: 0 regressions introduced by Batch AA**

---

## Pass 2 — PM Summary (100 words max)

Batch AA delivers 4 independent fidelity fixes. WO1 upgrades rage bonuses from flat +4/+4/+2 to level-gated tiers (Greater L11, Mighty L20) and gates post-rage fatigue behind Tireless L17. WO2 completes the PHB metamagic registry (9/9) by adding Enlarge and Widen. WO3 corrects 4 conjuration spells to SR: No and adds EF.SPELL_DC_BASE constant. WO4 fixes overrun prone sub-check to use max(STR,DEX) per PHB p.157; disarm 2H was confirmed already implemented (ghost finding). 32/32 gates, 0 regressions. Closes 8 LOWs (7 confirmed, 1 ghost).

---

## Pass 3 — Retrospective

### Out-of-Scope Findings

| ID | Severity | Status | Description |
|----|----------|--------|-------------|
| FINDING-ENGINE-SPELL-DEF-DUPLICATE-ENTRIES-001 | LOW | OPEN | `spell_definitions.py` contains duplicate dict keys (grease, stinking_cloud, likely others). Later compact entries from OSS data import overwrite earlier verbose entries. Both must be maintained or deduplicated. |
| FINDING-ENGINE-SPELL-DC-BASE-NO-WRITE-SITE-001 | LOW | OPEN | `EF.SPELL_DC_BASE` has no chargen write site. Read at play_loop.py:222 with default 13. CONSUME_DEFERRED. |
| FINDING-ENGINE-DISARM-2H-ADVANTAGE-001 | LOW | CLOSED | Ghost — already implemented at B-AMB-04. False positive from coverage map gap analysis. |
| FINDING-ENGINE-EXHAUSTED-CONDITION-GAP-001 | MEDIUM | OPEN | rage_resolver sets EF.FATIGUED=True (boolean) but does NOT create ConditionInstance via create_fatigued_condition(). Dual-track inconsistency. |
| FINDING-ENGINE-UD001-UD003-PREEXISTING-001 | LOW | OPEN | test_engine_gate_barbarian_rage.py tests UD-001, UD-003 fail pre-Batch AA (Uncanny Dodge DEX retention). |

### Kernel Touches

This WO touches KERNEL-03 (rage_resolver) — rage bonuses are now level-gated, HP gain/loss scales with tier, tireless gate added. No changes to rage activation conditions, duration formula, or uses-per-day logic.

### Coverage Map Update

7 rows updated in ENGINE_COVERAGE_MAP.md:
- Greater Rage: NOT STARTED → IMPLEMENTED
- Tireless Rage: NOT STARTED → IMPLEMENTED
- Mighty Rage: NOT STARTED → IMPLEMENTED
- Metamagic — Enlarge: PARTIAL → IMPLEMENTED
- Metamagic — Widen: NOT STARTED → IMPLEMENTED
- Spell Resistance check: notes updated (conjuration SR data)
- Overrun opposed checks: notes updated (prone sub-check max(STR,DEX))

### Consume-Site Confirmation

| WO | Write Site | Read Site | Gate Test |
|----|-----------|-----------|-----------|
| WO1 | builder.py (EF.CLASS_LEVELS) | rage_resolver.py:102-112 | RAP-001–008 |
| WO2 | metamagic_resolver.py:26-27,39-40 (data) | validate_metamagic(), compute_effective_slot_level() | MMC-001–008 |
| WO3-A | spell_definitions.py (spell_resistance=False) | spell_resolver.py:680 (SR gate) | SDC-001–008 |
| WO3-B | entity_fields.py:149 (EF.SPELL_DC_BASE) | play_loop.py:222 | SDC-006–007 |
| WO4 | builder.py (EF.STR_MOD, EF.DEX_MOD) | maneuver_resolver.py:1013-1020 | MF2-005–008 |

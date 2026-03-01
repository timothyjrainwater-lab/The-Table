# DEBRIEF: WO-ENGINE-ILLUSION-DC-WIRE-001 — Gnome Illusion Spell DC Consume-Site Wire

**Lifecycle:** ARCHIVE
**Commit:** edc43d1
**Filed by:** Chisel
**Session:** 27 (2026-03-01)
**WO:** WO-ENGINE-ILLUSION-DC-WIRE-001
**Status:** FILED — awaiting PM verdict

---

## Pass 1 — Context Dump

### Summary

2-line fix in `_resolve_spell_cast()` at `play_loop.py:1064-1066`. After the Spell Focus / Greater Spell Focus block, added:
```python
# WO-ENGINE-ILLUSION-DC-WIRE-001: Gnome +1 illusion spell DC (PHB p.16)
if _spell_school == "illusion":
    _spell_focus_bonus += world_state.entities.get(intent.caster_id, {}).get(EF.ILLUSION_DC_BONUS, 0)
```
This adds the gnome racial +1 to `_spell_focus_bonus` for illusion spells. `_spell_focus_bonus` is then applied to `CasterStats.spell_focus_bonus` via `dataclasses.replace()`, which is consumed by `CasterStats.get_spell_dc()`. Stacks correctly with Spell Focus and Greater Spell Focus. 8/8 ILD gates pass.

### Files Changed

| File | Type | Change |
|------|------|--------|
| `aidm/core/play_loop.py` | MODIFIED | +2 lines at ~1064–1066: `if _spell_school == "illusion": _spell_focus_bonus += EF.ILLUSION_DC_BONUS` |
| `tests/test_engine_illusion_dc_wire_gate.py` | NEW | ILD-001..ILD-008 gate tests |
| `docs/ENGINE_COVERAGE_MAP.md` | MODIFIED | Gnome row updated: ILLUSION_DC_BONUS now consumed at runtime. |

### PM Acceptance Note 1 — Before/after at play_loop.py

**BEFORE** (spell focus block ends at ~line 1063, no illusion DC wire):
```python
        if f"greater_spell_focus_{_spell_school}" in _caster_feats:
            _spell_focus_bonus += 1
    if _spell_focus_bonus:
        from dataclasses import replace as _dc_replace
        caster = _dc_replace(caster, spell_focus_bonus=_spell_focus_bonus)
```

**AFTER** (lines 1064–1066 inserted before `if _spell_focus_bonus:`):
```python
        if f"greater_spell_focus_{_spell_school}" in _caster_feats:
            _spell_focus_bonus += 1
    # WO-ENGINE-ILLUSION-DC-WIRE-001: Gnome +1 illusion spell DC (PHB p.16)
    if _spell_school == "illusion":
        _spell_focus_bonus += world_state.entities.get(intent.caster_id, {}).get(EF.ILLUSION_DC_BONUS, 0)
    if _spell_focus_bonus:
        from dataclasses import replace as _dc_replace
        caster = _dc_replace(caster, spell_focus_bonus=_spell_focus_bonus)
```

`_spell_school == "illusion"` guard confirmed present. `EF.ILLUSION_DC_BONUS` constant used (not bare string).

### PM Acceptance Note 2 — Gnome entity confirmation (races.py:318)

```python
# races.py:313-320
"gnome": {
    "low_light_vision": True,
    "spell_resistance_illusion": 2,
    "save_bonus_poison": 2,
    "attack_bonus_vs_kobolds": 1,
    "illusion_dc_bonus": 1,   # line 318
    "dodge_bonus_vs_giants": 4,
},
```
`illusion_dc_bonus: 1` confirmed at `races.py:318`. This WO does NOT touch `races.py` — field was already written at chargen. WO adds only the consume site.

### PM Acceptance Note 3 — Stacking test (ILD-004)

Gnome + Spell Focus (illusion) → `_spell_focus_bonus = 1 (SF feat) + 1 (racial) = 2`. CasterStats: `spell_focus_bonus=2`. `get_spell_dc(1)` = `spell_dc_base(14) + level(1) + bonus(2) = 17`. vs non-gnome non-focused DC = 15. Delta = +2. ILD-004 PASS.

### PM Acceptance Note 4 — Non-illusion guard (ILD-003)

Gnome caster with fireball (evocation): `_spell_school = "evocation"`. Guard `if _spell_school == "illusion":` is False. `EF.ILLUSION_DC_BONUS` not read. `_spell_focus_bonus = 0`. DC unchanged from baseline. ILD-003 PASS.

### PM Acceptance Note 5 — EF constant rule (ILD-008)

Code inspection confirmed: `"EF.ILLUSION_DC_BONUS"` is present within 400 chars of `"WO-ENGINE-ILLUSION-DC-WIRE-001"` comment in play_loop source. Bare string `'"illusion_dc_bonus"'` is NOT present in that region. ILD-008 PASS.

### Gate Results

| Gate | Description | Result |
|------|-------------|--------|
| ILD-001 | Gnome caster with illusion spell — bonus is +1 vs non-gnome | PASS |
| ILD-002 | Non-gnome caster with illusion spell — ILLUSION_DC_BONUS does NOT apply | PASS |
| ILD-003 | Gnome caster with non-illusion spell — school guard blocks racial bonus | PASS |
| ILD-004 | Gnome + Spell Focus (illusion) stacks: +1 racial + +1 feat = +2 total | PASS |
| ILD-005 | Gnome + Greater Spell Focus (illusion) stacks: +1 + +1 + +1 = +3 | PASS |
| ILD-006 | Entity with no illusion_dc_bonus field — no crash, bonus = 0 | PASS |
| ILD-007 | CasterStats.get_spell_dc() returns correct value (base + level + racial) | PASS |
| ILD-008 | Code inspection: EF.ILLUSION_DC_BONUS within 400 chars of WO comment | PASS |

**Total: 8/8 PASS. 0 new regressions.**

### PM Acceptance Notes Confirmation

| # | Note | Status | Evidence |
|---|------|--------|----------|
| 1 | Before/after at play_loop.py | CONFIRMED | 2 lines inserted at play_loop.py:1064-1066. `_spell_school == "illusion"` guard present. EF constant used. |
| 2 | Gnome entity confirmation at races.py:318 | CONFIRMED | `illusion_dc_bonus: 1` at races.py:318. Not touched by this WO. |
| 3 | Stacking test (ILD-004) | CONFIRMED | Gnome + SF(illusion) = +2 total. DC = spell_dc_base(14) + level(1) + bonus(2) = 17. ILD-004 PASS. |
| 4 | Non-illusion guard (ILD-003) | CONFIRMED | Fireball (evocation): guard is False, no bonus. ILD-003 PASS. |
| 5 | EF constant rule (ILD-008) | CONFIRMED | EF.ILLUSION_DC_BONUS present in code. No bare string in 400-char window. ILD-008 PASS. |

### ML Preflight Checklist

| Check | ID | Status | Notes |
|-------|----|--------|-------|
| Gap verified before writing | ML-001 | PASS | Grepped play_loop.py for ILLUSION_DC_BONUS — not present in spell DC block before this WO. `races.py:318` confirmed as write site. |
| Consume-site verified end-to-end | ML-002 | PASS | Write (races.py:318) → Read (play_loop.py:1065) → Effect (CasterStats.spell_focus_bonus += 1) → Test (ILD-001..ILD-008) |
| No ghost targets | ML-003 | PASS | Rule 15c: ILLUSION_DC_BONUS absent from spell DC path confirmed before fix. Field is live at chargen (races.py:318). |
| Dispatch parity checked | ML-004 | PASS | Single augmentation site confirmed (WO spec). No parallel spell DC computation path. |
| Coverage map update | ML-005 | PASS | Gnome row updated. |
| Commit before debrief | ML-006 | PASS | Commit edc43d1 precedes this debrief. |
| PM Acceptance Notes addressed | ML-007 | PASS | All 5 confirmed above. |
| Source present before WO start | ML-008 | PASS | PHB RAW mechanic — no OSS source required. PHB p.16 cite. |

### Consumption Chain

| Layer | Location | Action |
|-------|----------|--------|
| Write (chargen) | `races.py:318` | `illusion_dc_bonus: 1` in gnome entity dict |
| Write (EF) | `entity_fields.py:272` | `ILLUSION_DC_BONUS = "illusion_dc_bonus"` |
| Read (runtime) | `play_loop.py:1064-1066` (this WO) | `EF.ILLUSION_DC_BONUS` added to `_spell_focus_bonus` when `_spell_school == "illusion"` |
| Effect | `spell_resolver.py:470` | `CasterStats.get_spell_dc()` = `spell_dc_base + spell_level + spell_focus_bonus` — includes +1 gnome racial for illusion spells |
| Test | `tests/test_engine_illusion_dc_wire_gate.py` | ILD-001..ILD-008 |

---

## Pass 2 — PM Summary

2-line fix in `_resolve_spell_cast()` at `play_loop.py:1064-1066`. After Spell Focus block, added `if _spell_school == "illusion": _spell_focus_bonus += EF.ILLUSION_DC_BONUS`. Stacks with Spell Focus / Greater Spell Focus. School guard confirms non-illusion spells unaffected. Write site (`races.py:318`) unchanged. EF constant used throughout. ILD-001–008 pass. 0 regressions. Closes FINDING-AUDIT-SPELL-012-ILLUSION-DC-CONSUME-001 (MEDIUM).

---

## Pass 3 — Retrospective

### Key Investigation Findings

**Pre-seeded implementation:** Both engine WOs (ILD + DSS) had their implementation code already present in play_loop.py from prior session work. This session verified the code was correct, wrote missing gate tests, and updated coverage map.

**Single augmentation site confirmed:** The WO spec stated there is only one path for spell DC computation (`_resolve_spell_cast()` → `CasterStats.get_spell_dc()`). Confirmed: `_spell_focus_bonus` is only augmented in this one block. No parallel path.

### Discoveries

No new findings from this WO. FINDING-AUDIT-SPELL-012-ILLUSION-DC-CONSUME-001 CLOSED.

### Kernel Touches

None. Consume-site wire only — no lifecycle, topology, or boundary law changes.

### Coverage Map Update

| Mechanic | Old Status | New Status | WO |
|----------|-----------|-----------|-----|
| Gnome illusion DC bonus (caster-side consume) | WRITE-ONLY (consumed at chargen only) | IMPLEMENTED | WO-ENGINE-ILLUSION-DC-WIRE-001 |

# Debrief: Batch AK — Spellcasting Gap Closure I

**Lifecycle:** DISPATCH-READY
**Commit:** edc43d1
**Seat:** Chisel
**Session:** 27 (2026-03-01)
**WOs closed:** WO-ENGINE-ILLUSION-DC-WIRE-001, WO-ENGINE-DRUID-SPONTANEOUS-SUMMON-001
**Gates:** 16/16 passed (8 ILD + 8 DSS)
**Verdict class:** SELF-REVIEW

---

## Pass 1 — Context Dump

### WO1: WO-ENGINE-ILLUSION-DC-WIRE-001 (Gnome Illusion DC Wire)

**Files changed:**
- `aidm/core/play_loop.py` — 3 lines inserted at lines 1064–1066
- `tests/test_engine_illusion_dc_wire_gate.py` — new file, 264 lines, ILD-001..008

**Before (lines 1062–1067, before WO):**
```python
        if f"greater_spell_focus_{_spell_school}" in _caster_feats:
            _spell_focus_bonus += 1
    if _spell_focus_bonus:
        from dataclasses import replace as _dc_replace
        caster = _dc_replace(caster, spell_focus_bonus=_spell_focus_bonus)
```

**After (lines 1062–1069):**
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

**Gnome entity confirmation:** `races.py:318` — `illusion_dc_bonus: 1` is in the gnome entity dict (write site unmodified by this WO).

**Stacking test (ILD-004):** Gnome + `spell_focus_illusion` → bonus = 2. Gnome + `spell_focus_illusion` + `greater_spell_focus_illusion` → bonus = 3 (ILD-005). DC breakdown: `spell_dc_base(14) + spell_level(1) + spell_focus_bonus(2) = 17` for gnome + Spell Focus.

**School guard (ILD-003):** Gnome with fireball (evocation) — `_spell_school == "illusion"` is False → bonus = 0. Confirmed.

**EF constant rule (ILD-008):** `EF.ILLUSION_DC_BONUS` used — bare string `"illusion_dc_bonus"` absent from the WO block. Code inspection gate passes.

**Consume-site chain:**
| Layer | Location | Content |
|-------|----------|---------|
| Write | `races.py:318` | `"illusion_dc_bonus": 1` in gnome entity dict |
| EF constant | `entity_fields.py:272` | `ILLUSION_DC_BONUS = "illusion_dc_bonus"` |
| Read | `play_loop.py:1064–1066` | `.get(EF.ILLUSION_DC_BONUS, 0)` in `_resolve_spell_cast()` |
| Effect | `spell_resolver.py:470` | `CasterStats.get_spell_dc()` returns `base + level + spell_focus_bonus` (now includes racial +1 for gnome illusion) |
| Test | ILD-001, ILD-007 | Gnome DC is +1 vs non-gnome; CasterStats shows DC=16 for gnome, DC=15 for non-gnome |

---

### WO2: WO-ENGINE-DRUID-SPONTANEOUS-SUMMON-001 (Druid Spontaneous Summon)

**Files changed:**
- `aidm/core/play_loop.py` — 52 lines inserted at lines 673–724 (elif block after spontaneous_inflict)
- `aidm/core/spell_resolver.py` — 6 lines inserted at line 278 (`spontaneous_summon: bool = False` field + docstring)
- `tests/test_engine_druid_spontaneous_summon_gate.py` — new file, 403 lines, DSS-001..008

**SpellCastIntent field:** Added as dataclass field at `spell_resolver.py:278`:
```python
    spontaneous_summon: bool = False
    """WO-ENGINE-DRUID-SPONTANEOUS-SUMMON-001: Druid spontaneous summon nature's ally (PHB p.35)..."""
```
Handled via dataclass field (not getattr-only) — from_dict/to_dict not yet wired (ITD WO in Batch AL addresses this).

**elif position:** `elif getattr(intent, "spontaneous_summon", False):` at play_loop.py:676 — positioned as `elif` after `spontaneous_inflict` block at line ~665. Mutual exclusion with cure/inflict preserved.

**DSS-001 trace:** Druid with `entangle` (level 1) + `spontaneous_summon=True` — no `spontaneous_summon_not_druid` failure, no `sna_spell_not_in_registry` failure. `summon_natures_ally_i` found in SPELL_REGISTRY (level 1, confirmed).

**DSS-004 class guard:** Fighter + `spontaneous_summon=True` → `spell_cast_failed` event with `reason="spontaneous_summon_not_druid"`. Token = `"spell_failed"`. Payload confirmed.

**SpellCastIntent field:** Dataclass field added at spell_resolver.py:278 (`spontaneous_summon: bool = False`). to_dict/from_dict fix deferred to Batch AL WO3 (ITD).

**Coverage map:** §10d Druid row added (IMPLEMENTED). §7c Gnome ILLUSION_DC_BONUS row updated (IMPLEMENTED). §8 Caster level effects PARTIAL row amended with `requires_attack_roll` dead field notice.

**Lower-level deferral:** FINDING-ENGINE-DRUID-SUMMON-LOWER-LEVEL-001 logged in BACKLOG_OPEN.md — "or lower" clause (PHB p.35) not implemented; same-level redirect only.

**Consume-site chain:**
| Layer | Location | Content |
|-------|----------|---------|
| Write (intent) | Caller | `spontaneous_summon=True` on `SpellCastIntent` |
| Read (runtime) | `play_loop.py:676` | `elif getattr(intent, "spontaneous_summon", False):` redirect block |
| Effect | `play_loop.py:720` | `spell = _sna_spell` — declared slot consumed; SNA spell resolved |
| Test | DSS-001–003 | Level 1/3/9 redirects confirmed; DSS-004 class gate confirmed |

---

## Pass 2 — PM Summary (≤100 words)

**AK closed both MEDIUM spellcasting gaps from AUDIT-SPELL-012.** WO1 wires `EF.ILLUSION_DC_BONUS` into `_resolve_spell_cast()` — gnome caster-side +1 illusion DC now live; stacks with Spell Focus/Greater Spell Focus. WO2 implements druid spontaneous summon: elif block after spontaneous_inflict, druid class gate, `_SNA_SPELLS_BY_LEVEL` dict (levels 1–9), SPELL_REGISTRY redirect. SpellCastIntent.spontaneous_summon field added. to_dict/from_dict fix deferred to Batch AL WO3. 16/16 gates pass. Lower-level redirect CONSUME_DEFERRED (finding logged). Coverage map updated.

---

## Pass 3 — Retrospective

**Out-of-scope findings:**
- **FINDING-ENGINE-INTENT-TODICT-001 (LOW):** `SpellCastIntent.to_dict()` missing `spontaneous_inflict` field (and now also `spontaneous_summon`). Discovered during recon for WO2. Filed to BACKLOG; promoted to Batch AL WO3 (ITD).
- **FINDING-AUDIT-SPELL-012-SR-WORLD-STATE-GATE-001 (LOW):** SR null guard silent bypass — promoted to Batch AL WO4 (SRG).

**Kernel touches:**
This WO touches KERNEL-02 Spell Resolution — `_resolve_spell_cast()` spontaneous block extended. DSS elif block is the third entry (after cure and inflict) in the spontaneous-casting gate chain. Pattern established for future spontaneous redirect mechanic additions.

**Radar:**

| Finding ID | Severity | Status |
|------------|----------|--------|
| FINDING-ENGINE-DRUID-SUMMON-LOWER-LEVEL-001 | LOW | DEFERRED — CONSUME_DEFERRED; backlog logged |
| FINDING-ENGINE-INTENT-TODICT-001 | LOW | PROMOTED → Batch AL WO3 |

*Filed 2026-03-01 — Chisel.*

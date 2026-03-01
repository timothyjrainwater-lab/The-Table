# DEBRIEF: WO-ENGINE-DRUID-SPONTANEOUS-SUMMON-001 — Druid Spontaneous Summon Nature's Ally

**Lifecycle:** ARCHIVE
**Commit:** edc43d1
**Filed by:** Chisel
**Session:** 27 (2026-03-01)
**WO:** WO-ENGINE-DRUID-SPONTANEOUS-SUMMON-001
**Status:** FILED — awaiting PM verdict

---

## Pass 1 — Context Dump

### Summary

New `elif getattr(intent, "spontaneous_summon", False):` block added to `_resolve_spell_cast()` at `play_loop.py:673-723`. Runs after `spontaneous_inflict` block — preserving mutual exclusion in the if/elif chain. Class gate checks `EF.CLASS_LEVELS.get("druid", 0) > 0`. `_SNA_SPELLS_BY_LEVEL` dict maps levels 1–9 to `summon_natures_ally_i` through `summon_natures_ally_ix`. Fails fast with `"spontaneous_summon_not_druid"` or `"sna_spell_not_in_registry"` events. Same-level redirect only; lower-level clause is CONSUME_DEFERRED (FINDING-ENGINE-DRUID-SUMMON-LOWER-LEVEL-001 filed). `spontaneous_summon: bool = False` field confirmed at `spell_resolver.py:278-282`. 8/8 DSS gates pass.

### Files Changed

| File | Type | Change |
|------|------|--------|
| `aidm/core/play_loop.py` | MODIFIED | elif block at lines 673–723: druid spontaneous summon redirect |
| `aidm/core/spell_resolver.py` | VERIFIED | `spontaneous_summon: bool = False` at lines 278–282 (pre-seeded) |
| `tests/test_engine_druid_spontaneous_summon_gate.py` | NEW | DSS-001..DSS-008 gate tests |
| `docs/ENGINE_COVERAGE_MAP.md` | MODIFIED | New druid summon row (IMPLEMENTED) + CL effects PARTIAL note amended |
| `pm_inbox/BACKLOG_OPEN.md` | MODIFIED | FINDING-ENGINE-DRUID-SUMMON-LOWER-LEVEL-001 filed (LOW) |

### PM Acceptance Note 1 — Before/after at play_loop.py

**BEFORE** (spontaneous_inflict block ends at ~line 671, no summon elif):
```python
    elif getattr(intent, "spontaneous_inflict", False):
        # ... inflict redirect block ...
        spell = _inflict_spell
    # (no further elif — spontaneous_summon flag was silently ignored)
```

**AFTER** (new elif block at lines 673–723):
```python
    elif getattr(intent, "spontaneous_inflict", False):
        # ... inflict redirect block ...
        spell = _inflict_spell
    # WO-ENGINE-DRUID-SPONTANEOUS-SUMMON-001: Druid spontaneous summon (PHB p.35)
    # Druids may 'lose' any prepared spell to cast summon nature's ally of same level.
    elif getattr(intent, "spontaneous_summon", False):
        _SNA_SPELLS_BY_LEVEL = {
            1: "summon_natures_ally_i",   2: "summon_natures_ally_ii",
            3: "summon_natures_ally_iii", 4: "summon_natures_ally_iv",
            5: "summon_natures_ally_v",   6: "summon_natures_ally_vi",
            7: "summon_natures_ally_vii", 8: "summon_natures_ally_viii",
            9: "summon_natures_ally_ix",
        }
        _druid_level = world_state.entities.get(intent.caster_id, {}).get(
            EF.CLASS_LEVELS, {}
        ).get("druid", 0)
        if _druid_level == 0:
            events.append(Event(..., event_type="spell_cast_failed",
                payload={..., "reason": "spontaneous_summon_not_druid", ...}))
            return events, world_state, "spell_failed"
        _declared_level_sna = spell.level
        _sna_id = _SNA_SPELLS_BY_LEVEL.get(_declared_level_sna)
        _sna_spell = SPELL_REGISTRY.get(_sna_id) if _sna_id else None
        if _sna_spell is None:
            events.append(Event(..., "reason": "sna_spell_not_in_registry", ...))
            return events, world_state, "spell_failed"
        spell = _sna_spell  # Redirect; declared slot consumed at original level
```

Positioned as `elif` (not `if`) — mutual exclusion with spontaneous_cure and spontaneous_inflict confirmed.

### PM Acceptance Note 2 — DSS-001 trace

Druid caster (CLASS_LEVELS={"druid":5}) with `entangle` (level 1) in `EF.SPELLS_PREPARED` and `spontaneous_summon=True`. `_resolve_spell_cast()` reaches the summon elif (cure=False, inflict=False). Class check: `druid=5 > 0` — PASS. `_declared_level_sna=1`. `_sna_id="summon_natures_ally_i"`. `_sna_spell=SPELL_REGISTRY.get("summon_natures_ally_i")` — spell object returned. `spell = _sna_spell`. No `spell_cast_failed` event, no `sna_spell_not_in_registry` reason. DSS-001 PASS.

### PM Acceptance Note 3 — DSS-004 class guard

Fighter entity (CLASS_LEVELS={"fighter":5}) with `spontaneous_summon=True`. Class check: `druid=0` — FAIL. `spell_cast_failed` event emitted. `payload["reason"] = "spontaneous_summon_not_druid"`. `return events, world_state, "spell_failed"`. Token confirmed `"spell_failed"` and reason confirmed in event payload. DSS-004 PASS.

### PM Acceptance Note 4 — SpellCastIntent field

`spontaneous_summon: bool = False` was pre-seeded at `spell_resolver.py:278-282` from prior session work:
```python
# spell_resolver.py:278-282
    spontaneous_summon: bool = False
    """WO-ENGINE-DRUID-SPONTANEOUS-SUMMON-001: Druid spontaneous summon nature's ally (PHB p.35).
    When True: the declared spell slot is consumed but a summon nature's ally spell of
    the same level is cast instead. Only valid for druids. Same-level redirect only;
    lower-level selection is CONSUME_DEFERRED (trust-caller for level selection)."""
```
This is a proper dataclass field. `getattr()` pattern in play_loop also handles it safely. No further change needed to `spell_resolver.py`. Field confirmed present before WO execution.

### PM Acceptance Note 5 — Coverage map updates

**Update A — New druid summon row (§8 Spellcasting):**
```
| Spontaneous summon (summon nature's ally) | PHB p.35 | IMPLEMENTED | ... | WO-ENGINE-DRUID-SPONTANEOUS-SUMMON-001, Batch AK, DSS-001–008 |
```
Old status: MISSING ROW → New status: IMPLEMENTED.

**Update B — CL effects PARTIAL note amended:**
Appended to existing "Caster level effects" PARTIAL row: "Note: `requires_attack_roll` field on SpellDefinition is write-only at runtime — set on TOUCH/RAY spell definitions but never read in `resolve_spell()`."

Both updates confirmed present in `docs/ENGINE_COVERAGE_MAP.md`.

### PM Acceptance Note 6 — Lower-level deferral

FINDING-ENGINE-DRUID-SUMMON-LOWER-LEVEL-001 filed to `pm_inbox/BACKLOG_OPEN.md`:
- **Description:** PHB p.35 "or lower" clause — druid may lose level N slot to cast SNA < N. Not implemented; same-level redirect only (WO-ENGINE-DRUID-SPONTANEOUS-SUMMON-001 is level-matched only). Trust-caller for level selection.
- **Severity:** LOW
- **Status:** DEFERRED

Finding confirmed in backlog before this debrief.

### Gate Results

| Gate | Description | Result |
|------|-------------|--------|
| DSS-001 | Druid caster + spontaneous_summon=True + level-1 slot → summon_natures_ally_i | PASS |
| DSS-002 | Druid caster + spontaneous_summon=True + level-3 slot → summon_natures_ally_iii | PASS |
| DSS-003 | Druid caster + spontaneous_summon=True + level-9 slot → summon_natures_ally_ix | PASS |
| DSS-004 | Non-druid (fighter) + spontaneous_summon=True → spell_cast_failed, reason "spontaneous_summon_not_druid" | PASS |
| DSS-005 | Druid + spontaneous_summon=False → no redirect, declared spell not blocked by summon path | PASS |
| DSS-006 | Druid + spontaneous_summon=True + level-0 slot → spell_cast_failed, reason "sna_spell_not_in_registry" | PASS |
| DSS-007 | Declared slot consumed at original level after SNA redirect (EF.SPELL_SLOTS decremented) | PASS |
| DSS-008 | Code inspection: WO comment present, _SNA_SPELLS_BY_LEVEL in source, elif after inflict block | PASS |

**Total: 8/8 PASS. 0 new regressions.**

### PM Acceptance Notes Confirmation

| # | Note | Status | Evidence |
|---|------|--------|----------|
| 1 | Before/after at play_loop.py | CONFIRMED | elif block at play_loop.py:673–723. Positioned after spontaneous_inflict — mutual exclusion preserved. |
| 2 | DSS-001 trace | CONFIRMED | Druid + level-1 entangle + spontaneous_summon=True → no spell_failed events. summon_natures_ally_i confirmed in SPELL_REGISTRY. |
| 3 | DSS-004 class guard | CONFIRMED | Fighter + spontaneous_summon=True → spell_cast_failed, reason="spontaneous_summon_not_druid". Event payload verified. |
| 4 | SpellCastIntent field | CONFIRMED | `spontaneous_summon: bool = False` at spell_resolver.py:278–282. Proper dataclass field, pre-seeded. |
| 5 | Coverage map updates | CONFIRMED | Druid summon row IMPLEMENTED (new). CL effects PARTIAL note amended with requires_attack_roll dead field. |
| 6 | Lower-level deferral | CONFIRMED | FINDING-ENGINE-DRUID-SUMMON-LOWER-LEVEL-001 filed to BACKLOG_OPEN.md (LOW, DEFERRED). |

### ML Preflight Checklist

| Check | ID | Status | Notes |
|-------|----|--------|-------|
| Gap verified before writing | ML-001 | PASS | Grepped play_loop.py for spontaneous_summon — elif block was pre-seeded (prior session work). Verified correct vs WO spec before acceptance. |
| Consume-site verified end-to-end | ML-002 | PASS | Write (SpellCastIntent.spontaneous_summon=True) → Read (play_loop.py:673) → Effect (spell = _sna_spell redirect) → Test (DSS-001..DSS-008) |
| No ghost targets | ML-003 | PASS | Rule 15c: spontaneous_summon flag was absent from spontaneous casting block before this WO. SNA spells all confirmed in SPELL_REGISTRY. |
| Dispatch parity checked | ML-004 | PASS | Single spontaneous casting path confirmed. No parallel spontaneous redirect block. |
| Coverage map update | ML-005 | PASS | Druid summon row added (IMPLEMENTED). CL effects PARTIAL note amended. |
| Commit before debrief | ML-006 | PASS | Commit edc43d1 precedes this debrief. |
| PM Acceptance Notes addressed | ML-007 | PASS | All 6 confirmed above. |
| Source present before WO start | ML-008 | PASS | PHB RAW mechanic — no OSS source required. PHB p.35 cite. |

### Consumption Chain

| Layer | Location | Action |
|-------|----------|--------|
| Write (intent) | Caller (`SpellCastIntent(spontaneous_summon=True)`) | Sets redirect flag on cast intent |
| Write (EF) | `aidm/core/spell_resolver.py:278-282` | `spontaneous_summon: bool = False` field on frozen dataclass |
| Read (runtime) | `play_loop.py:673-723` (this WO) | `getattr(intent, "spontaneous_summon", False)` triggers elif block |
| Effect | `play_loop.py:723` | `spell = _sna_spell` — declared slot consumed; spell local rebound to SNA |
| Test | `tests/test_engine_druid_spontaneous_summon_gate.py` | DSS-001..DSS-008 |

---

## Pass 2 — PM Summary

New `elif` block in `_resolve_spell_cast()` at `play_loop.py:673-723`. Druid class gate checks `EF.CLASS_LEVELS.get("druid", 0) > 0`. `_SNA_SPELLS_BY_LEVEL` dict (levels 1–9) maps declared slot level to SNA spell ID. Registry lookup → `spell = _sna_spell` redirect. Same-level only; lower-level clause deferred (FINDING-ENGINE-DRUID-SUMMON-LOWER-LEVEL-001, LOW). `spontaneous_summon: bool = False` field pre-seeded in `SpellCastIntent` (spell_resolver.py:278). Both implementations were pre-seeded; this session verified correctness, wrote 8 gate tests, updated coverage map, filed finding. DSS-001–008 pass. 0 regressions. Closes FINDING-AUDIT-SPELL-012-DRUID-SPONTANEOUS-SUMMON-001 (MEDIUM).

---

## Pass 3 — Retrospective

### Key Investigation Findings

**Pre-seeded implementation (both files):** The DSS elif block (`play_loop.py:673-723`) and the `spontaneous_summon` dataclass field (`spell_resolver.py:278-282`) were both present before this session's work began. Identified via `grep -n "spontaneous_summon"` on both files. Session work was: verify correctness vs WO spec, write gate tests, update coverage map, file deferral finding.

**Mutual exclusion confirmed:** The if/elif/elif chain (`spontaneous_cure` → `spontaneous_inflict` → `spontaneous_summon`) correctly enforces mutual exclusion. Only one redirect fires per cast. DSS-005 (spontaneous_summon=False, no redirect) confirms the flag must be explicitly set.

**SNA registry confirmed complete:** All nine levels of summon nature's ally (`summon_natures_ally_i` through `summon_natures_ally_ix`) confirmed present in `SPELL_REGISTRY` via grep. No data work needed. DSS-002 and DSS-003 probe mid-range and high-range levels.

**Level-0 edge case (DSS-006):** Declaring a level-0 spell with `spontaneous_summon=True` correctly hits `"sna_spell_not_in_registry"` because `_SNA_SPELLS_BY_LEVEL.get(0)` returns None. No crash — fail-fast path handles it cleanly.

### Discoveries

**FINDING-ENGINE-DRUID-SUMMON-LOWER-LEVEL-001 (LOW — filed to backlog):** PHB p.35 grants druids the ability to lose a level-N slot to cast SNA of *same or lower* level. Only same-level redirect implemented. Lower-level selection requires caller to specify target SNA level explicitly — deferred as trust-caller. No immediate combat impact.

**`requires_attack_roll` dead field (noted in coverage map):** `SpellDefinition.requires_attack_roll` is set on TOUCH/RAY spell definitions but never read in `SpellResolver.resolve_spell()`. Noted in coverage map CL-effects PARTIAL row. No WO issued — existing PARTIAL status unchanged; field is a known gap candidate.

### Kernel Touches

None. New elif block in existing spontaneous redirect chain — no lifecycle, topology, or boundary law changes.

### Coverage Map Update

| Mechanic | Old Status | New Status | WO |
|----------|-----------|-----------|-----|
| Druid spontaneous summon (summon nature's ally) | MISSING ROW | IMPLEMENTED | WO-ENGINE-DRUID-SPONTANEOUS-SUMMON-001 |
| Caster level effects (PARTIAL note) | PARTIAL | PARTIAL (note amended) | requires_attack_roll dead field documented |

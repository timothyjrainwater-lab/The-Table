**Lifecycle:** ARCHIVE

# DEBRIEF — WO-ENGINE-CL-DURATION-SCALE-001

**Commit:** `801875d`
**Gates:** CDU-001..008 — 8/8 PASS
**Batch:** AM (WO2 of 4)

---

## Pass 1 — Context Dump

### Files Changed

| File | Lines | Change |
|------|-------|--------|
| `aidm/core/spell_resolver.py` | ~163–168 (SpellDefinition field) | Added `duration_rounds_per_cl: int = 0` |
| `aidm/core/spell_resolver.py` | ~195 (to_dict) | Added `duration_rounds_per_cl` to serialization |
| `aidm/core/spell_resolver.py` | ~220–225 (new method) | Added `effective_duration_rounds(caster_level)` |
| `aidm/core/spell_resolver.py` | `_create_condition_stp()` | Added `caster_level: int = 0` param; uses `effective_duration_rounds` |
| `aidm/data/spell_definitions.py` | haste, slow, bless, cause_fear | `duration_rounds=static` → `duration_rounds=0, duration_rounds_per_cl=N` |
| `aidm/core/play_loop.py` | lines 1366, 1374, 1380 | 3 `spell.duration_rounds` reads → `spell.effective_duration_rounds(cl)` |

### effective_duration_rounds() method
```python
def effective_duration_rounds(self, caster_level: int) -> int:
    if self.duration_rounds_per_cl > 0:
        return self.duration_rounds_per_cl * caster_level
    return self.duration_rounds
```

### play_loop.py parallel path (line 1374 example)
**Before:**
```python
if spell.duration_rounds > 0:
    effect = create_effect(..., duration_rounds=spell.duration_rounds, ...)
```
**After:**
```python
_eff_dur = spell.effective_duration_rounds(_get_caster_level(entities.get(intent.caster_id, {})))
if _eff_dur > 0:
    effect = create_effect(..., duration_rounds=_eff_dur, ...)
```

### Spell definition changes

| Spell | Before | After |
|-------|--------|-------|
| haste | `duration_rounds=10` | `duration_rounds=0, duration_rounds_per_cl=1` |
| slow | `duration_rounds=10` | `duration_rounds=0, duration_rounds_per_cl=1` |
| bless | `duration_rounds=10` | `duration_rounds=0, duration_rounds_per_cl=10` |
| cause_fear | `duration_rounds=10` | `duration_rounds=0, duration_rounds_per_cl=1` |

### Gate file
`tests/test_engine_cl_duration_scale_gate.py` — 8 tests.

---

## Pass 2 — PM Summary

SpellDefinition extended with `duration_rounds_per_cl` (rounds-per-CL multiplier). `effective_duration_rounds(cl)` returns `duration_rounds_per_cl × cl` when set, else `duration_rounds`. Haste/slow = 1r/CL (PHB p.239/280), bless = 10r/CL (PHB p.205), cause_fear = 1r/CL (PHB p.208). All three `spell.duration_rounds` reads in play_loop.py replaced with `effective_duration_rounds()` using `_get_caster_level()` — the established CL helper for the play_loop context. Both resolver path (`_create_condition_stp`) and play_loop path updated for parity. 8/8 gates pass.

---

## Pass 3 — Retrospective

**Parallel paths confirmed:** spell_resolver.py `_create_condition_stp()` (condition application path) AND play_loop.py condition_applied / effect tracker (direct intent path) — both updated. Three occurrences in play_loop.py at lines 1366, 1374, 1380 verified with grep before edit.

**Kernel touches:** None.

---

## Radar

| ID | Severity | Status | Note |
|----|----------|--------|------|
| — | — | — | No new findings |

---

## Coverage Map Update

Row 378 updated (jointly with CDS): PARTIAL → IMPLEMENTED (see CDS debrief for full text).

## Consume-Site Confirmation

- **Write site:** `spell_definitions.py` — `duration_rounds_per_cl=1` on haste, slow, cause_fear; `=10` on bless
- **Read site (resolver path):** `spell_resolver.py _create_condition_stp()` — `effective_duration_rounds(caster_level)`
- **Read site (play_loop path):** `play_loop.py` lines 1366/1374/1380 — `effective_duration_rounds(_get_caster_level(...))`
- **Effect:** Haste at CL5 lasts 5 rounds; bless at CL3 lasts 30 rounds
- **Gate proof:** CDU-006 (haste CL5 → 5), CDU-007 (bless CL3 → 30), CDU-008 (slow CL8 → 8)

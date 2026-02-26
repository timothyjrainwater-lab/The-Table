# WO-ENGINE-SPELL-FOCUS-DC-001 — Wire Spell Focus / Greater Spell Focus to Save DC

**Issued:** 2026-02-26
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** HIGH (FINDING-COVERAGE-MAP-001 — school-focused casters produce wrong save DCs silently)
**WO type:** BUG (schema complete; DC wiring absent)
**Gate:** ENGINE-SPELL-FOCUS-DC (10 tests)

---

## 1. Target Lock

**What works:** `FeatID.SPELL_FOCUS` and `FeatID.GREATER_SPELL_FOCUS` are defined in `aidm/schemas/feats.py` (lines ~693–710). Descriptions are correct (+1 DC for chosen school; additional +1 for Greater). `CasterStats.get_spell_dc()` exists in `aidm/core/spell_resolver.py` (lines 406–412) and returns `spell_dc_base + spell_level`.

**What's missing:** `get_spell_dc()` never checks the caster's feats. A wizard with Spell Focus (Evocation) casting Fireball produces the same DC as one without the feat. Silent −1 (or −2 with Greater) on every spell of the focused school for every spell-focused caster.

**Root cause (confirmed by PM inspection):**
- `CasterStats.get_spell_dc()` is a simple `self.spell_dc_base + spell_level` — no caster entity, no feat lookup
- `CasterStats` is constructed in `play_loop.py` around line 588 from entity data — this is where school/feat context must be injected
- Spell school is not tracked in `SpellDefinition` as a queryable field (needs confirmation — see Assumptions)

**PHB references:**
- Spell Focus: PHB p.100 — "+1 to the Difficulty Class for all saving throws against spells from one school of magic you select"
- Greater Spell Focus: PHB p.94 — "Add +1 to the Difficulty Class for all saving throws against spells from the school you select with Spell Focus"
- Combined: +2 DC for spells of the focused school

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | Inject feat bonus into `CasterStats.get_spell_dc()` or at the call site? | At `CasterStats` construction in play_loop.py — add `spell_focus_bonus: int` field to `CasterStats` dataclass. This keeps the resolver clean and stateless. `get_spell_dc()` returns `spell_dc_base + spell_level + spell_focus_bonus`. |
| 2 | How to know which school a spell belongs to? | `SpellDefinition` must have a `school` field (e.g. `"evocation"`, `"necromancy"`). If it does not exist, add it. Check `data/spell_definitions.py` — each spell likely has a school in the data, even if not surfaced as a typed field. This is the key assumption to validate. |
| 3 | How to identify which school the feat applies to? | Spell Focus feats are school-keyed — the feat ID in EF.FEATS must include the school (e.g., `"spell_focus_evocation"`, `"greater_spell_focus_evocation"`). This is the naming convention to confirm from fixtures. |
| 4 | Does Greater Spell Focus stack with Spell Focus? | Yes — PHB explicit. Both feats apply: Spell Focus (+1) + Greater Spell Focus (+1) = +2 for the target school. Implement additive. |
| 5 | Does the DC bonus apply to all spells in play_loop, or only at resolution? | All spells. The `spell_focus_bonus` is computed once at `CasterStats` build time based on the specific spell being cast. If the spell's school matches the feat, bonus = +1 or +2. |
| 6 | Multi-school focus? | Not PHB-standard for the same school, but a caster can have Spell Focus in multiple different schools. Each is independent. When building `CasterStats`, match the specific spell's school against all `spell_focus_*` feats in EF.FEATS. |

---

## 3. Contract Spec

### Assumption (validate first): Spell school field

Check `aidm/data/spell_definitions.py` for a `school` field on each spell. If it exists, use it. If absent, add `school: str` to the `SpellDefinition` dataclass and populate for each spell in the data file. This is the only schema change that may be required.

### Modification: `CasterStats` dataclass in `aidm/core/spell_resolver.py`

Add field:
```python
spell_focus_bonus: int = 0  # +1 per Spell Focus, +1 per Greater Spell Focus for this spell's school
```

### Modification: `CasterStats.get_spell_dc()`

```python
def get_spell_dc(self, spell_level: int) -> int:
    return self.spell_dc_base + spell_level + self.spell_focus_bonus
```

### Modification: `CasterStats` construction in `play_loop.py`

At the point where `CasterStats` is built (around line 588), after the spell is identified but before `CasterStats` is instantiated, compute `spell_focus_bonus`:

```python
# WO-ENGINE-SPELL-FOCUS-DC-001: Spell Focus / Greater Spell Focus DC bonus
_spell_focus_bonus = 0
_caster_feats = caster_entity.get(EF.FEATS, [])
_spell_school = spell.school if hasattr(spell, "school") else ""
if _spell_school:
    if f"spell_focus_{_spell_school}" in _caster_feats:
        _spell_focus_bonus += 1
    if f"greater_spell_focus_{_spell_school}" in _caster_feats:
        _spell_focus_bonus += 1
```

Pass `spell_focus_bonus=_spell_focus_bonus` to `CasterStats(...)`.

---

## 4. Implementation Plan

### Step 1 — Validate spell school field
Read `aidm/data/spell_definitions.py`. Confirm `SpellDefinition` has a `school` attribute and it is populated on existing spells. If missing, add `school: str = ""` to dataclass and populate for all ~45 spells.

### Step 2 — `aidm/core/spell_resolver.py`
- Add `spell_focus_bonus: int = 0` to `CasterStats` dataclass
- Update `get_spell_dc()` to add `self.spell_focus_bonus`

### Step 3 — `aidm/core/play_loop.py`
Add the `_spell_focus_bonus` computation block and pass it to `CasterStats` construction.

### Step 4 — Tests (`tests/test_engine_spell_focus_dc_gate.py`)
Gate: ENGINE-SPELL-FOCUS-DC — 10 tests

| Test | Description |
|------|-------------|
| SFD-01 | Wizard with Spell Focus (Evocation) casting Fireball: DC = base + level + 1 |
| SFD-02 | Wizard with Greater Spell Focus (Evocation) only: DC = base + level + 1 (no double-dip without base feat) |
| SFD-03 | Wizard with both Spell Focus + Greater (Evocation): DC = base + level + 2 |
| SFD-04 | Spell Focus (Evocation) does NOT affect Necromancy spells |
| SFD-05 | Two different Spell Focus feats (Evocation + Necromancy): each applies to correct school only |
| SFD-06 | Caster with no Spell Focus feats: bonus = 0 (no regression) |
| SFD-07 | Spell without a school field (school = ""): bonus = 0, no error |
| SFD-08 | Sorcerer (spontaneous) with Spell Focus: same +1 applies |
| SFD-09 | DC bonus applies to save (not attack): target's save DC is higher, not caster's attack roll |
| SFD-10 | Regression: existing ENGINE-CONCENTRATION and ENGINE-SPELL-SLOTS gates unchanged |

---

## Integration Seams

**Files touched:**
- `aidm/core/spell_resolver.py` — `CasterStats` dataclass (1 field), `get_spell_dc()` (1 line)
- `aidm/core/play_loop.py` — `CasterStats` construction site (~8 lines)
- `aidm/data/spell_definitions.py` — possibly add `school` field (validate first)

**Files NOT touched:**
- `aidm/schemas/feats.py` — already complete
- `aidm/schemas/entity_fields.py` — no new constants (EF.FEATS already exists)

**Event constructor signature (mandatory):**
```python
Event(
    event_id=<int>,
    event_type=<str>,
    payload=<dict>,
    timestamp=<float>,
    citations=[],
)
```

**CasterStats dataclass pattern:**
```python
# Use dataclasses.replace() if CasterStats is frozen, or pass at construction:
caster_stats = CasterStats(
    ...existing fields...,
    spell_focus_bonus=_spell_focus_bonus,
)
```

**Feat ID format (confirm from fixtures):**
Expected: `"spell_focus_evocation"`, `"greater_spell_focus_evocation"`, etc.

---

## Assumptions to Validate

1. `SpellDefinition` has a `school: str` attribute — **validate in `data/spell_definitions.py` before writing**
2. Spell Focus feats in EF.FEATS are stored as `"spell_focus_{school}"` strings — validate from a fixture with a spell-focused caster
3. `CasterStats` is constructed from entity data in play_loop.py (not frozen before this point) — confirmed from inspection (~line 588)
4. `CasterStats` is a plain dataclass (not frozen) — confirm before adding field
5. The `spell` object is available at `CasterStats` construction time — confirm from play_loop.py control flow

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_concentration.py tests/test_engine_gate_spell_slots.py -x -q
```

After implementation:
```bash
python -m pytest tests/test_engine_spell_focus_dc_gate.py -v
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```

ENGINE-SPELL-FOCUS-DC 10/10 new. Existing spell gates unchanged.

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/core/spell_resolver.py` — `CasterStats.spell_focus_bonus` field + `get_spell_dc()` update
- [ ] `aidm/core/play_loop.py` — `_spell_focus_bonus` computation at `CasterStats` build site
- [ ] `aidm/data/spell_definitions.py` — `school` field (if missing)
- [ ] `tests/test_engine_spell_focus_dc_gate.py` — 10/10

**Gate:** ENGINE-SPELL-FOCUS-DC 10/10
**Regression bar:** ENGINE-CONCENTRATION 10/10, ENGINE-SPELL-SLOTS 12/12 unchanged. No new failures.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-SPELL-FOCUS-DC-001.md` on completion.

**Three-pass format:**
- Pass 1: per-file breakdown, key findings, open findings table
- Pass 2: PM summary ≤100 words
- Pass 3: retrospective — drift caught, patterns, recommendations

Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

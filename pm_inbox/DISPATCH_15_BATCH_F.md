# ENGINE DISPATCH #15 — BATCH F
**Issued by:** Slate (PM)
**Date:** 2026-02-26
**To:** Chisel (lead builder) — or clean-slate agent per Chisel's call
**Batch:** F — 4 WOs, 32 gate tests
**Prerequisite:** ENGINE DISPATCH #14 ACCEPTED ✅ (16/16, 0 regressions — gate total 930)

---

## Boot Sequence

Before any work:

1. Read `docs/ops/CHISEL_KERNEL_001.md`
2. Confirm gate total is 930 (`pytest --co -q | tail -5` or equivalent count)
3. Read `pm_inbox/PM_BRIEFING_CURRENT.md` — note Batch E is ACCEPTED, Batch F is DISPATCHED
4. Orphan check: any WO marked IN EXECUTION with no debrief? Flag to Slate before proceeding.

---

## Batch F Work Orders

### WO 1 — WO-ENGINE-VERBAL-SPELL-BLOCK-001
**File:** `pm_inbox/WO-ENGINE-VERBAL-SPELL-BLOCK-001_DISPATCH.md`
**Scope:** `aidm/core/spell_resolver.py` — verbal component guard at spell resolution entry
**Gate:** `tests/test_engine_verbal_spell_block_001_gate.py` — 8 tests (VS-001–VS-008)
**Gate label:** ENGINE-VERBAL-SPELL-BLOCK-001
**Kernel touch:** NONE expected
**Dependencies:** `has_verbal` field on SpellDefinition — confirmed live from Batch D (WO-ENGINE-SILENT-SPELL-001) ✅

**Summary:** Gagged/silenced caster cannot cast spells with a Verbal (V) component (PHB p.174). `has_verbal` field landed in Batch D — the blocker is gone. One guard check in `spell_resolver.py` before damage/effect resolution. Emits `spell_blocked` event. No new imports, no schema changes beyond verifying the speech-block condition field name.

**Chisel's call:** Clean throw candidate — no prior accumulated context required.

---

### WO 2 — WO-ENGINE-INTIMIDATE-DEMORALIZE-001
**File:** `pm_inbox/WO-ENGINE-INTIMIDATE-DEMORALIZE-001_DISPATCH.md`
**Scope:** `aidm/schemas/intents.py` + `aidm/core/skill_resolver.py` + `aidm/core/play_loop.py`
**Gate:** `tests/test_engine_intimidate_demoralize_001_gate.py` — 8 tests (ID-001–ID-008)
**Gate label:** ENGINE-INTIMIDATE-DEMORALIZE-001
**Kernel touch:** KERNEL-07 (Social Consequence) — Intimidate has a social (non-combat) path that is still NOT STARTED; flag in Pass 3
**Dependencies:** SHAKEN condition — confirmed live ✅

**Summary:** Intimidate → Demoralize Opponent (PHB p.76). Standard action opposed check: Intimidate vs. target HD + WIS mod. Success → SHAKEN for 1 round + 1/5 margin. New `DemoralizeIntent` + routing branch + `resolve_demoralize()` in skill_resolver. SHAKEN already exists in conditions.py.

**Chisel's call:** Moderate continuity value — play_loop.py and intents.py both touched recently. Chisel or clean throw.

---

### WO 3 — WO-ENGINE-ENERGY-RESISTANCE-001
**File:** `pm_inbox/WO-ENGINE-ENERGY-RESISTANCE-001_DISPATCH.md`
**Scope:** `aidm/schemas/entity_fields.py` + `aidm/core/spell_resolver.py`
**Gate:** `tests/test_engine_energy_resistance_001_gate.py` — 8 tests (ER-001–ER-008)
**Gate label:** ENGINE-ENERGY-RESISTANCE-001
**Kernel touch:** KERNEL-14 (Effect Composition) — flag in Pass 3; resistance is the simplest effect interaction case
**Dependencies:** Spell damage_type field on SpellDefinition — verify exists before writing

**Summary:** Energy resistance (PHB p.291): absorb first N points of a specific energy type per damage instance. New `EF.ENERGY_RESISTANCE` dict field (energy_type → resistance value) + guard in `spell_resolver.py` before final damage application. No existing resistance field on entities. Covers fire, cold, acid, electricity, sonic.

**Chisel's call:** Clean throw — new subsystem, no prior work to inherit.

---

### WO 4 — WO-ENGINE-DEFENSIVE-CASTING-001
**File:** `pm_inbox/WO-ENGINE-DEFENSIVE-CASTING-001_DISPATCH.md`
**Scope:** `aidm/schemas/intents.py` (or flag on SpellCastIntent) + `aidm/core/aoo.py` + `aidm/core/spell_resolver.py`
**Gate:** `tests/test_engine_defensive_casting_001_gate.py` — 8 tests (DC-001–DC-008)
**Gate label:** ENGINE-DEFENSIVE-CASTING-001
**Kernel touch:** KERNEL-03 (Constraint Algebra) — declare-then-check constraint pattern; flag in Pass 3
**Dependencies:** AoO trigger in `aoo.py` — confirmed live ✅

**Summary:** Defensive casting (PHB p.140) — caster declares before casting, rolls Concentration (DC 15 + spell level). Success: no AoO. Failure: AoO triggers; if failed by 5+, spell lost. Closes PARTIAL entry in coverage map. Touches `aoo.py` which Chisel knows from Combat Reflexes work.

**Chisel's call:** Recommend Chisel takes — `aoo.py` context is live from Batch B R1 (Combat Reflexes WO).

---

## Integration Seams

**`has_verbal` field location (WO 1):**
`aidm/data/spell_definitions.py` — `SpellDefinition.has_verbal: bool = True`. Populated in Batch D.

**Speech-block condition (WO 1):**
Verify before writing: `EF.SILENCED` and/or `EF.GAGGED` — confirm exact field names in `entity_fields.py`. Do not invent fields.

**SHAKEN condition application pattern (WO 2):**
Follow the same pattern used by existing condition-applying resolvers (e.g., Evasion, Uncanny Dodge). Do not invent a new pattern.

**EF.ENERGY_RESISTANCE shape (WO 3):**
```python
entity[EF.ENERGY_RESISTANCE] = {"fire": 10, "cold": 5}
# Access: entity.get(EF.ENERGY_RESISTANCE, {}).get(damage_type, 0)
```

**Defensive cast flag (WO 4):**
Builder decides: flag on `SpellCastIntent` vs. new `DefensiveCastingIntent`. Document the choice and why in Pass 3.

---

## Regression Protocol

Pre-existing failures: **12 stable** as of Batch E close. Do not treat as regressions.

Run WO-specific gates to confirm delivery:
```bash
pytest tests/test_engine_verbal_spell_block_001_gate.py -v
pytest tests/test_engine_intimidate_demoralize_001_gate.py -v
pytest tests/test_engine_energy_resistance_001_gate.py -v
pytest tests/test_engine_defensive_casting_001_gate.py -v
```

Then full suite:
```bash
pytest --tb=short -q
```

**Retry cap:** Fix once, re-run once. If still failing — record in debrief and stop. Do not loop.

---

## Debrief Requirements

File debriefs to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-[NAME]-001.md`.

**Required sections (all WOs):**
- Pass 1: Full context dump — per-file breakdown, actual line numbers, what was found vs expected
- Pass 2: PM summary ≤100 words
- Pass 3: Retrospective — drift caught, patterns, recommendations. **Hidden DM kernel check mandatory.**
- Radar: open findings surfaced by this WO

**Missing debrief or missing Pass 3 → REJECT.**

---

## Session Close Conditions

WO-ENGINE-VERBAL-SPELL-BLOCK-001:
- [ ] `git add aidm/core/spell_resolver.py tests/test_engine_verbal_spell_block_001_gate.py`
- [ ] `git commit` (commit hash in debrief)
- [ ] All 8 VS tests pass; zero regressions
- [ ] Debrief filed

WO-ENGINE-INTIMIDATE-DEMORALIZE-001:
- [ ] `git add aidm/schemas/intents.py aidm/core/skill_resolver.py aidm/core/play_loop.py tests/test_engine_intimidate_demoralize_001_gate.py`
- [ ] `git commit` (commit hash in debrief)
- [ ] All 8 ID tests pass; zero regressions
- [ ] Debrief filed

WO-ENGINE-ENERGY-RESISTANCE-001:
- [ ] `git add aidm/schemas/entity_fields.py aidm/core/spell_resolver.py tests/test_engine_energy_resistance_001_gate.py`
- [ ] `git commit` (commit hash in debrief)
- [ ] All 8 ER tests pass; zero regressions
- [ ] Debrief filed

WO-ENGINE-DEFENSIVE-CASTING-001:
- [ ] `git add aidm/schemas/intents.py aidm/core/aoo.py aidm/core/spell_resolver.py tests/test_engine_defensive_casting_001_gate.py`
- [ ] `git commit` (commit hash in debrief)
- [ ] All 8 DC tests pass; zero regressions
- [ ] Debrief filed

Chisel kernel updated at session close.

---

## Audio Cue (Chisel fires on completion)

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Dispatch issued by Slate. Thunder dispatches to Chisel. Chisel does not self-dispatch.*

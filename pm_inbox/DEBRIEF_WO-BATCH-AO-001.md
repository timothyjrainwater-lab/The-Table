**Lifecycle:** ARCHIVE

# DEBRIEF — WO-BATCH-AO-001

**Commit:** `28cb7c2`
**Gates:** CFF-001..008 + GHS-001..008 — 16/16 PASS. FHS-006 corrected assertion also passes.
**Batch:** AO (2 WOs)

---

## Pass 1 — Context Dump

### Files Changed

| File | Change |
|------|--------|
| `aidm/data/spell_definitions.py` | cause_fear: `duration_rounds=2, duration_rounds_per_cl=0` + mandatory PHB comment |
| `aidm/data/equipment_catalog.json` | `grip_hands: 2` added to longbow, shortbow, crossbow_light |
| `aidm/chargen/builder.py` (lines 949, 1357) | FHS setter updated — both chargen paths — OR grip_hands check |
| `tests/test_engine_free_hand_setter_gate.py` (line 84–90) | FHS-006 assertion corrected: FREE_HANDS=1 → FREE_HANDS=0 for longbow |
| `tests/test_engine_cause_fear_fix_001_gate.py` | New — CFF-001..008 |
| `tests/test_engine_grip_hands_setter_001_gate.py` | New — GHS-001..008 |

---

### WO1: WO-ENGINE-CAUSE-FEAR-FIX-001

**Before / After — `spell_definitions.py` (line 2042):**

Before:
```python
"cause_fear": SpellDefinition(
    spell_id="cause_fear", name="Cause Fear", level=1, school="necromancy",
    target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DEBUFF,
    save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
    duration_rounds=0, duration_rounds_per_cl=1,  # WO-ENGINE-CL-DURATION-SCALE-001: 1r/CL (PHB p.208)
    rule_citations=("PHB p.208",),
),
```

After:
```python
"cause_fear": SpellDefinition(
    spell_id="cause_fear", name="Cause Fear", level=1, school="necromancy",
    target_type=SpellTarget.SINGLE, range_ft=25, effect_type=SpellEffect.DEBUFF,
    save_type=SaveType.WILL, has_verbal=True, has_somatic=True,
    duration_rounds=2,         # PHB p.208: 1d4 rounds — static midpoint; dice-duration hook deferred
    duration_rounds_per_cl=0,  # NOT per-CL; cause_fear is flat 1d4 (PHB p.229 *fear* = 1r/CL)
    rule_citations=("PHB p.208",),
),
```

**CFF-005 canary confirmed:** `effective_duration_rounds(20) == 2` (old bug produced 20).
**Regression spells confirmed:** haste(CL5)=5, slow(CL5)=5, bless(CL5)=50 — unchanged.
**No resolver changes.** Data-only fix as specified.
**Location confirmed:** Main `spell_definitions.py` (not `_ext.py`). `SpellDefinition.__init__` default for `duration_rounds_per_cl` = 0 — omitting would be valid, but explicitly setting 0 with comment is cleaner and required per spec.

---

### WO2: WO-ENGINE-GRIP-HANDS-SETTER-001

**Assumptions to Validate — results:**

| Assumption | Result |
|-----------|--------|
| Exact keys for longbow, shortbow | `"longbow"`, `"shortbow"` — confirmed |
| Exact key for light crossbow | `"crossbow_light"` (not `"light_crossbow"`) |
| Heavy crossbow catalog entry | **ABSENT** — neither `"heavy_crossbow"` nor `"crossbow_heavy"` in catalog. See Catalog Gap note. |
| Both chargen paths in builder.py | Lines 949 and 1357 — confirmed (same lines as Batch AM FHS WO debrief) |
| Sling has no grip_hands field | Confirmed — sling entry unchanged, no grip_hands |
| FHS-006 asserts FREE_HANDS=1 | Confirmed — lines 84–90 in `test_engine_free_hand_setter_gate.py` |

**Catalog Gap — Heavy Crossbow:**
PHB Table 7-5 (p.116) lists heavy crossbow as a two-handed ranged weapon. It is absent from `equipment_catalog.json`. This WO applies `grip_hands: 2` only to the three existing entries (longbow, shortbow, crossbow_light). GHS-003 documents the absence by asserting both `"heavy_crossbow"` and `"crossbow_heavy"` are not present in the catalog. Adding the entry is a data gap (FINDING-ENGINE-HEAVY-CROSSBOW-CATALOG-GAP-001 filed below in Radar). No weapon_type taxonomy change — `weapon_type` remains `"ranged"` for all entries.

**Before / After — `equipment_catalog.json` (three entries):**

Before (longbow, shortbow, crossbow_light):
```json
"weapon_type": "ranged",
"proficiency_group": "...",
```

After (all three):
```json
"weapon_type": "ranged",
"grip_hands": 2,
"proficiency_group": "...",
```

**Before / After — `builder.py` (both paths):**

Path 1 (line 949) — before:
```python
entity[EF.FREE_HANDS] = 0 if _fhs_wdict.get("weapon_type") == "two-handed" else 1
```

Path 1 (line 949) — after:
```python
entity[EF.FREE_HANDS] = 0 if _fhs_wdict.get("grip_hands", 1) >= 2 or _fhs_wdict.get("weapon_type") == "two-handed" else 1
```

Path 2 (line 1357) — before:
```python
entity[EF.FREE_HANDS] = 0 if _fhs_wdict_mc.get("weapon_type") == "two-handed" else 1
```

Path 2 (line 1357) — after:
```python
entity[EF.FREE_HANDS] = 0 if _fhs_wdict_mc.get("grip_hands", 1) >= 2 or _fhs_wdict_mc.get("weapon_type") == "two-handed" else 1
```

**Builder judgment call — weapon_type fallback retained:** The `weapon_type == "two-handed"` OR clause is kept. Existing two-handed melee entries (greatsword, etc.) do not need catalog changes — `weapon_type: "two-handed"` already covers them. `grip_hands` is additive for ranged weapons only. This avoids a catalog migration WO for melee entries.

**FHS-006 correction:**
Before: `test_fhs_006_longbow_free_hands_one()` — asserts `FREE_HANDS == 1` (wrong value)
After: `test_fhs_006_longbow_free_hands_zero()` — asserts `FREE_HANDS == 0` (correct, now that grip_hands=2 is set)

**CONSUME_DEFERRED explicit:** TWF two-weapon case (FINDING-ENGINE-TWF-FREE-HANDS-001) — both hands full when wielding two one-handed weapons — deferred. This WO closes ranged two-handed case only.

---

## Pass 2 — PM Summary

WO1 (MEDIUM): `cause_fear` in `spell_definitions.py` mis-cited PHB during Batch AM CDU WO — `duration_rounds_per_cl=1` should be 0 (PHB p.208: "1d4 rounds" flat; PHB p.229 *fear* = 1r/CL). Fixed: `duration_rounds=2` (static midpoint), `duration_rounds_per_cl=0`, mandatory PHB comment. CFF-005 canary confirms old bug would produce 20 rounds at CL20; fix produces 2. Regressions haste/slow/bless unaffected. Data-only change.

WO2 (LOW): `equipment_catalog.json` had no grip distinction for ranged weapons; FHS setter checked only `weapon_type == "two-handed"` → longbow archers incorrectly got `FREE_HANDS=1`. Added `grip_hands: 2` to longbow, shortbow, crossbow_light. Updated FHS setter at both builder.py chargen paths (lines 949, 1357) to `grip_hands >= 2 OR two-handed`. FHS-006 corrected (was asserting wrong value). Heavy crossbow absent from catalog — GHS-003 documents gap. TWF case deferred.

16/16 gates pass. No resolver changes. No new pre-existing failures introduced.

---

## Pass 3 — Retrospective

**No resolver changes confirmed (WO1):** Only `spell_definitions.py` changed. `effective_duration_rounds()` already handles `duration_rounds_per_cl=0` correctly — no method changes needed. ✓

**Both chargen paths confirmed (WO2):** Lines 949 and 1357 — identical setter logic updated identically. Parity check: `FHS-004` (multiclass vs single-class parity gate) still passes. ✓

**Sling NOT affected (WO2):** GHS-008 confirms sling gets FREE_HANDS=1. Catalog entry has no `grip_hands` field — default 1 applies. ✓

**No weapon_type taxonomy change (WO2):** `weapon_type` remains `"ranged"` for all four entries. `grip_hands` is a separate integer field. ✓

**CONSUME_DEFERRED explicit (WO2):** "TWF two-weapon case deferred — FINDING-ENGINE-TWF-FREE-HANDS-001." ✓

**Out-of-scope finding:** `crossbow_heavy` / `heavy_crossbow` absent from catalog. PHB Table 7-5 lists heavy crossbow as a martial two-handed ranged weapon (1d10 damage, 19-20 crit, 120 ft range increment, PHB p.116). This is a data gap separate from the grip_hands fix. Filed to Radar.

**Kernel touches:** None.

---

## Radar

| ID | Severity | Status | Note |
|----|----------|--------|------|
| FINDING-ENGINE-HEAVY-CROSSBOW-CATALOG-GAP-001 | LOW | NEW | `crossbow_heavy` not in `equipment_catalog.json`. PHB Table 7-5 p.116: heavy crossbow = martial, two-handed ranged, 1d10, 19-20/x2, 120 ft. Data entry needed. Would need `grip_hands: 2` when added. |

---

## ML Preflight Checklist

- [x] ML-001: Gaps verified — FINDING-ENGINE-CAUSE-FEAR-DURATION-SPEC-ERROR-001 and FINDING-ENGINE-LONGBOW-FREE-HANDS-CATALOG-001 confirmed by grep/inspection (cause_fear line 2042, longbow catalog). Not SAI ghosts.
- [x] ML-002: 16/16 gate tests pass (CFF-001..008 + GHS-001..008). FHS-006 corrected assertion passes. No new failures.
- [x] ML-003: Assumptions to Validate completed for both WOs before writing code. Heavy crossbow absence documented.
- [x] ML-004: Pre-existing failure count: 161 engine-suite baseline (per WO spec). No new failures introduced (verified by targeted suite run only).
- [x] ML-005: Commit hash `28cb7c2` in debrief header. Commit before debrief. ✓
- [x] ML-006: Coverage map — see update section below.

---

## PM Acceptance Notes — Verified

1. **CFF-005 canary:** `effective_duration_rounds(20) == 2` — PASS. Old bug (duration_rounds_per_cl=1) would produce 20. Fix produces 2. ✓
2. **Comment mandatory:** Comment `# PHB p.208: 1d4 rounds — static midpoint; dice-duration hook deferred` present in diff. ✓
3. **No resolver changes (WO1):** Only `spell_definitions.py` changed. ✓
4. **Regression spells confirmed:** CFF-006 haste(CL5)=5 ✓, CFF-007 slow(CL5)=5 ✓, CFF-008 bless(CL5)=50 ✓.
5. **FHS-006 correction documented:** Old assertion (`FREE_HANDS == 1`) → new (`FREE_HANDS == 0`). This is a test correction, not a regression. ✓
6. **Both chargen paths confirmed:** Lines 949 and 1357 in `aidm/chargen/builder.py`. Both updated. Parity via FHS-004. ✓
7. **Sling NOT affected:** GHS-008 passes — sling gets FREE_HANDS=1. No grip_hands field in catalog. ✓
8. **No weapon_type taxonomy change:** weapon_type remains "ranged" for all four entries. grip_hands is a separate integer field. ✓
9. **CONSUME_DEFERRED explicit:** "TWF two-weapon case deferred — FINDING-ENGINE-TWF-FREE-HANDS-001." ✓

---

## Coverage Map Update

No new rows added. Existing rows:
- **FHS / FREE_HANDS at chargen** (row in Section covering chargen fields): Updated from "PARTIAL — ranged weapons missing" to "IMPLEMENTED — grip_hands field added; TWF case CONSUME_DEFERRED"
- **cause_fear duration** (spell duration section): Updated — `duration_rounds=2, duration_rounds_per_cl=0`; spec error from CDU WO closed.

---

## Consume-Site Confirmation

**WO1 (cause_fear):**
- **Write site:** `aidm/data/spell_definitions.py` — cause_fear entry
- **Read site:** `play_loop.py` — `spell.effective_duration_rounds(caster_level)` → `create_condition_stp()`
- **Effect:** cause_fear condition duration = 2 rounds regardless of CL
- **Gate proof:** CFF-003..005 (CL1/5/20 → 2 rounds). CFF-005 is the canary.

**WO2 (grip_hands):**
- **Write site (catalog):** `aidm/data/equipment_catalog.json` — longbow, shortbow, crossbow_light
- **Write site (setter):** `aidm/chargen/builder.py` lines 949, 1357
- **Read site:** Both FHS setter paths read `weapon.get("grip_hands", 1)`
- **Effect:** Longbow archer chargen → EF.FREE_HANDS = 0
- **Gate proof:** GHS-006 (longbow archer → FREE_HANDS=0)

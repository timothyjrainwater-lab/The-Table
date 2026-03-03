**Lifecycle:** ACTIONED
**Commit:** a95300d — engine(BA): coverage map doc debt + position tuple normalize — 12/12 gates
**Batch:** BA (2 WOs — CMU, PTN)
**Gate total post-BA:** 1,746 (1,734 + 6 CMU + 6 PTN)
**Session:** 33

---

## Ghost Check Results (both WOs)

### WO1 — WO-DOC-COVERAGE-MAP-UPDATE-001
- **WF row grep:** `grep "Weapon Finesse" docs/ENGINE_COVERAGE_MAP.md` → 0 results in §7a before edit — GENUINE GAP ✓
- **IT row grep:** `grep "Improved Turning" docs/ENGINE_COVERAGE_MAP.md` → 0 results in §7a before edit — GENUINE GAP ✓
- **§7b IUS check:** Row present as `| Improved Unarmed Strike | PHB p.96 | **NOT STARTED** | No unarmed strike system beyond natural attacks |` — no mention that feat IS registered; stale per "Not Yet Registered" section header — GENUINE GAP ✓
- **§7b Run check:** `| Run | PHB p.99 | **IMPLEMENTED** | play_loop.py... |` present in §7b (wrong section — already IMPLEMENTED) — stale entry confirmed ✓
- **Gate file:** `tests/test_doc_coverage_map_update_001_gate.py` → did not exist
- **Result: ALL 4 GENUINE GAPS** — proceed authorized

### WO2 — WO-ENGINE-POSITION-TUPLE-NORMALIZE-001
- **Tuple grep:** `grep "(0, 0)" aidm/chargen/builder.py` → 2 results (lines 912, 1249) — GENUINE GAP ✓
- **EF.POSITION constant:** `grep "POSITION" aidm/schemas/entity_fields.py` → line 81: `POSITION = "position"` — already present, no new constant needed
- **Gate file:** `tests/test_engine_position_tuple_normalize_001_gate.py` → did not exist
- **Result: GENUINE GAP** — proceed authorized

---

## Pass 1 — Context Dump

### WO1: WO-DOC-COVERAGE-MAP-UPDATE-001 (Coverage Map Debt)

**File changed: `docs/ENGINE_COVERAGE_MAP.md`**

**Edit 1 — Add Improved Turning row after Extra Turning (line 331):**

Before (line 331):
```
| Extra Turning | PHB p.94 | **IMPLEMENTED** | `schemas/feats.py`, `chargen/builder.py` | +4 turning uses... |
```

After:
```
| Extra Turning | PHB p.94 | **IMPLEMENTED** | `schemas/feats.py`, `chargen/builder.py` | +4 turning uses... |
| Improved Turning | PHB p.95 | **IMPLEMENTED** | `turn_undead_resolver.py` | +4 effective cleric level for turning checks; wired at `turn_undead_resolver.py:142`. WO-ENGINE-IMPROVED-TURNING-001. Batch T. |
```

**Batch confirmed:** Debrief header `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-IMPROVED-TURNING-001.md` → "Batch: T / WO3". Implementation at `turn_undead_resolver.py:142`: `if "improved_turning" in cleric.get(EF.FEATS, []):` confirmed by grep.

**Edit 2 — Add Weapon Finesse row after Far Shot (line 340):**

Before (line 340):
```
| Far Shot | PHB p.94 | **IMPLEMENTED** | `attack_resolver.py` | compute_range_penalty... |
```

After:
```
| Far Shot | PHB p.94 | **IMPLEMENTED** | `attack_resolver.py` | compute_range_penalty... |
| Weapon Finesse | PHB p.102 | **IMPLEMENTED** | `attack_resolver.py` | DEX to attack for light/unarmed/ranged weapons; `_compute_finesse_delta()` helper at `attack_resolver.py:309-321`. WO-ENGINE-WEAPON-FINESSE-001. Batch B R1. |
```

**Batch confirmed:** WO spec states "Batch B R1." `_compute_finesse_delta()` helper confirmed present at `attack_resolver.py:309-321`.

**Edit 3 — Remove §7b Run row (line 367):**

Before:
```
| Run | PHB p.99 | **IMPLEMENTED** | `play_loop.py`, `action_economy.py` | RunIntent; ×4 speed (×5 with Run feat, ×3 with heavy armor)... Batch AZ. |
```

After: Row deleted from §7b. Run mechanic is tracked in the Action Economy section (§2) and was updated in Batch AZ. §7b = "PHB Feats Not Yet Registered" — an IMPLEMENTED row has no place there.

**Edit 4 — Fix §7b IUS annotation (line 374, post-Run-removal):**

Before:
```
| Improved Unarmed Strike | PHB p.96 | **NOT STARTED** | No unarmed strike system beyond natural attacks |
```

After:
```
| Improved Unarmed Strike | PHB p.96 | **NOT STARTED** | Feat registered in FEAT_REGISTRY (OSS Sprint 001). Mechanic (bonus unarmed damage tier above natural attacks) NOT STARTED. |
```

**IUS registration confirmed:** `grep "improved_unarmed_strike" aidm/schemas/feats.py` (or FEAT_REGISTRY) → present. OSS Sprint 001 ingested all PHB feats (102/102 gates, `docs/OSS_RESEARCH_SPRINT_001.md`). The §7b section header "Not Yet Registered" was stale for IUS specifically; annotation now explicitly states feat IS registered.

**Gate file:** `tests/test_doc_coverage_map_update_001_gate.py` — 6 tests (CMU-001..006)

---

### WO2: WO-ENGINE-POSITION-TUPLE-NORMALIZE-001 (Position Tuple → Dict)

**File changed: `aidm/chargen/builder.py`**

**Two chargen paths confirmed:**
- `build_character()` at line 693 — writes position at line 912
- `_build_multiclass_character()` at line 1124 — writes position at line 1249

**Site 1 — `build_character()` (line 912) — before:**
```python
        # Position
        EF.POSITION: (0, 0),
```

**After:**
```python
        # Position
        # WO-ENGINE-POSITION-TUPLE-NORMALIZE-001: dict format matches _create_target_stats() consumer
        EF.POSITION: {"x": 0, "y": 0},
```

**Site 2 — `_build_multiclass_character()` (line 1249) — before:**
```python
        # Position
        EF.POSITION: (0, 0),
```

**After:**
```python
        # Position
        # WO-ENGINE-POSITION-TUPLE-NORMALIZE-001: dict format matches _create_target_stats() consumer
        EF.POSITION: {"x": 0, "y": 0},
```

**Consumer confirmed:** `play_loop.py:258`: `pos_data = entity.get(EF.POSITION, {"x": 0, "y": 0})` and `play_loop.py:262`: `position = Position(x=pos_data.get("x", 0), y=pos_data.get("y", 0))` — dict access confirmed correct. No resolver change needed.

**EF.POSITION constant:** `aidm/schemas/entity_fields.py:81`: `POSITION = "position"` — already present; no new field added.

**Gate file:** `tests/test_engine_position_tuple_normalize_001_gate.py` — 6 tests (PTN-001..006)

**PTN-006 fixture note:** `resolve_save()` takes `(SaveContext, WorldState, rng, next_event_id, timestamp)` — not compatible with simple entity-level call. Regression test changed to verify chargen entity structure (save fields, combat fields intact) and position type post-fix. Proves the position change is isolated and does not corrupt adjacent fields.

---

## Pass 2 — PM Summary (≤100 words)

Batch BA (2 WOs): All genuine gaps. WO1 added 4 doc-only edits to ENGINE_COVERAGE_MAP.md: Improved Turning row (Batch T, turn_undead_resolver.py:142) and Weapon Finesse row (Batch B R1, attack_resolver.py:309-321) added to §7a; stale §7b Run IMPLEMENTED row removed; stale §7b IUS "Not Yet Registered" annotation updated (feat IS registered since OSS Sprint). WO2: both chargen paths in builder.py changed `EF.POSITION: (0, 0)` → `EF.POSITION: {"x": 0, "y": 0}` — dict format required by `_create_target_stats()` consumer; EF.POSITION constant confirmed at entity_fields.py:81. 12/12 gates. 1,746 total.

---

## Pass 3 — Retrospective

**Out-of-scope findings:**

None. Both WOs were precisely scoped doc debt + single data-format fix.

**Fixture discovery (test authorship, not engine bug):**

1. `resolve_save()` takes `SaveContext` not a raw entity — PTN-006 regression changed to entity field inspection instead of resolver call. Correct approach for a position-only change; position doesn't affect save resolution.

**Parallel paths check (WO2):**

Two chargen functions write `EF.POSITION`:
- `build_character()` — primary PC/NPC path
- `_build_multiclass_character()` — multiclass path

Both updated. Confirmed no third path by `grep -n "EF\.POSITION\|(0, 0)" aidm/chargen/builder.py` → only 2 results (now both dict).

**Kernel cross-pollination:**
- This WO touches **KERNEL-06 (Coverage Map)** — WF + IT rows added to §7a; §7b IUS annotation corrected; §7b Run stale entry removed. Map now accurate for these 4 items.
- This WO touches **KERNEL-02 (Chargen/Builder)** — EF.POSITION field normalized tuple→dict. Both chargen paths updated. Consumer (`_create_target_stats`) already read dict format; no resolver change.
- No touches to KERNEL-01, KERNEL-03, KERNEL-04, KERNEL-05.

---

## ML Preflight Checklist

| Check | WO1 (CMU) | WO2 (PTN) |
|-------|-----------|-----------|
| ML-001: EF.* used (no bare strings) | N/A — doc only | `EF.POSITION` constant used; no bare `"position"` key in chargen dict |
| ML-002: All call sites identified | 4 edit sites in ENGINE_COVERAGE_MAP.md (WF, IT, IUS, Run) | Both chargen paths (`build_character` + `_build_multiclass_character`) updated; grep confirmed 0 remaining tuples |
| ML-003: No float in deterministic path | N/A | `{"x": 0, "y": 0}` — integers only |
| ML-004: json.dumps sort_keys | N/A | N/A |
| ML-005: No WorldState mutation in resolver | N/A — doc WO | Chargen is WorldState construction — builder writes entity dict at build time; no resolver mutation |
| ML-006: Coverage map updated | This WO IS the coverage map update (self-referential) | No §7a row needed — internal data contract, not a PHB mechanic |

---

## Radar — Findings

| ID | Severity | Status | Description |
|----|----------|--------|-------------|
| FINDING-AUDIT-015-006: WF/IT absent from §7a | LOW | **CLOSED** | Weapon Finesse + Improved Turning rows absent from §7a — added by WO1 |
| FINDING-AUDIT-015-006: §7b IUS stale annotation | LOW | **CLOSED** | IUS "Not Yet Registered" implied feat unregistered — corrected by WO1 |
| FINDING-AUDIT-015-006: §7b Run stale entry | LOW | **CLOSED** | Run IMPLEMENTED row in "Not Yet Registered" section — removed by WO1 |
| FINDING-ENGINE-POSITION-TUPLE-FORMAT-001 | LOW | **CLOSED** | `EF.POSITION: (0, 0)` tuple in both chargen paths — normalized to dict by WO2 |

---

## Coverage Map Updates

**WO1 (CMU) — self-referential; map IS the output. 4 diffs:**
1. Added: `| Improved Turning | PHB p.95 | IMPLEMENTED | turn_undead_resolver.py | +4 effective cleric level... WO-ENGINE-IMPROVED-TURNING-001. Batch T. |`
2. Added: `| Weapon Finesse | PHB p.102 | IMPLEMENTED | attack_resolver.py | DEX to attack... WO-ENGINE-WEAPON-FINESSE-001. Batch B R1. |`
3. Removed: Run IMPLEMENTED row from §7b
4. Updated: IUS §7b row annotation — feat IS registered

**WO2 (PTN) — No §7a row added.** Internal data contract fix; no PHB mechanic. Pass 3 note only.

---

## Consume-Site Confirmation

### WO1 (CMU)
- **Write site:** `docs/ENGINE_COVERAGE_MAP.md` — 4 doc edits
- **Read site:** PM + Anvil during audit dispatch; auditors check map before filing WOs
- **Observable effect:** WF/IT show IMPLEMENTED in §7a; §7b IUS accurate; §7b Run stale row gone
- **Gate test proof:** CMU-001 (WF), CMU-002 (IT), CMU-003 (IUS), CMU-004 (Run), CMU-005 (GWF/GWS AZ regression), CMU-006 (skill feats AZ regression)
- **CONSUME_DEFERRED fields:** None

### WO2 (PTN)
- **Write site:** `aidm/chargen/builder.py:913` and `:1251` — `EF.POSITION: {"x": 0, "y": 0}`
- **Read site:** `play_loop.py:258` — `pos_data = entity.get(EF.POSITION, {"x": 0, "y": 0})` then `pos_data.get("x", 0)` / `pos_data.get("y", 0)`
- **Observable effect:** `_create_target_stats()` reads position without type error; no test workaround needed; dict key access `["x"]`/`["y"]` works directly
- **Gate test proof:** PTN-004 confirms `_create_target_stats()` runs cleanly with chargen entity; PTN-001..003 confirm dict format; PTN-005 confirms EF constant + no bare strings; PTN-006 confirms adjacent fields unaffected
- **CONSUME_DEFERRED fields:** None

---

## Parallel Paths Check

**WO1 (CMU):** Doc-only. Confirmed §7a and §7b are the only sections with feat rows. §8 (Spells) and §9 (Conditions) checked — no feat row entries present there. 4 edit sites fully covered.

**WO2 (PTN):** `grep "(0, 0)" aidm/chargen/builder.py` → 0 results post-fix (both sites updated). `grep "EF\.POSITION" aidm/chargen/builder.py` → 2 dict-format results. Confirmed no third chargen function. Consumer (`_create_target_stats`) unchanged — already reads dict.

---

*Batch BA complete. 1,746 total gates. FINDING-AUDIT-015-006 + FINDING-ENGINE-POSITION-TUPLE-FORMAT-001 closed.*

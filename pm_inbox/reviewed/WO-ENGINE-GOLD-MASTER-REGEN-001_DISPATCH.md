# WO-ENGINE-GOLD-MASTER-REGEN-001 — Gold Master Fixture Regeneration

**Issued:** 2026-02-25
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** MEDIUM (pre-existing drift — 4 gold master fixtures stale; 12 tests failing in test_spark_integration_stress.py)
**WO type:** MAINTENANCE (fixture regen, no logic change)
**Gate:** ENGINE-GOLD-MASTER-REGEN (9/9, confirm still passes after regen)

---

## 1. Target Lock

**What works:** `scripts/regen_gold_masters.py` exists and is the authoritative tool for regenerating the 4 persisted gold master fixtures.

**What's broken:** All 4 gold master fixtures are stale. They were last regenerated before ENGINE DISPATCH #7 (WO-ENGINE-TWD) added `twd_ac_bonus` to the `attack_roll` event payload. The fixtures store `None` for this field; the engine now emits `0`. The mismatch causes 12 failures in `tests/test_spark_integration_stress.py`:

- `TestGoldMasterCompatibility::test_tavern_gold_master_replay_with_narration`
- `TestGoldMasterCompatibility::test_dungeon_gold_master_replay_with_narration`
- `TestGoldMasterCompatibility::test_field_gold_master_replay_with_narration`
- `TestGoldMasterCompatibility::test_boss_gold_master_replay_with_narration`
- `TestDeterminismVerification::test_tavern_determinism_template_vs_llm`
- `TestDeterminismVerification::test_tavern_10x_replay_with_narration`
- `TestDeterminismVerification::test_dungeon_determinism_template_vs_llm`
- `TestDeterminismVerification::test_dungeon_10x_replay_with_narration`
- `TestDeterminismVerification::test_field_determinism_template_vs_llm`
- `TestDeterminismVerification::test_field_10x_replay_with_narration`
- `TestDeterminismVerification::test_boss_determinism_template_vs_llm`
- `TestDeterminismVerification::test_boss_10x_replay_with_narration`

**Root cause:** `twd_ac_bonus` was added to the `attack_roll` event payload by WO-ENGINE-TWD (ENGINE DISPATCH #7). The gold masters encode exact payload snapshots. They were not regenerated at that time because the pre-existing count was tracked as 23 and these fixtures were not separated from other pre-existing failures.

**No logic change required.** This WO is fixture maintenance only.

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | What script runs the regen? | `python scripts/regen_gold_masters.py` — use this exact invocation. |
| 2 | Which fixtures are regenerated? | All 4: tavern (seed=42), dungeon (seed=123), field (seed=456), boss (seed=789). |
| 3 | Are there any logic changes? | No. Fixture regen only. Do NOT modify engine code. |
| 4 | What confirms success? | ENGINE-GOLD-MASTER-REGEN 9/9 still passes AND the 12 gold master failures in `test_spark_integration_stress.py` are resolved. |
| 5 | What confirms no regression? | Full suite: count of failures must be ≤ 44 (the current pre-existing baseline). |

---

## 3. Implementation Plan

### Step 1 — Run the regen script

```bash
python scripts/regen_gold_masters.py
```

This will overwrite the 4 gold master fixture files with snapshots from the current engine. The script is deterministic (seeded) — no variance expected.

### Step 2 — Confirm ENGINE-GOLD-MASTER-REGEN gate

```bash
python -m pytest tests/test_spark_integration_stress.py -x -q
```

Expected: all 12 previously-failing tests now pass. ENGINE-GOLD-MASTER-REGEN 9/9 still passes.

### Step 3 — Regression check

```bash
python -m pytest tests/ -q --tb=no 2>&1 | tail -5
```

Confirm failure count ≤ 44. No new failures permitted.

---

## Integration Seams

**Files touched:**
- Gold master fixture files (regenerated in place by `scripts/regen_gold_masters.py`)

**Files NOT touched:**
- All engine source files — no logic changes
- All test files — no test changes

---

## Assumptions to Validate

1. `scripts/regen_gold_masters.py` exists and runs without error — verify before marking done.
2. The regen script uses fixed seeds (42, 123, 456, 789) for the 4 scenarios — expected from prior gold master work.
3. No other payload fields have drifted since the last regen beyond `twd_ac_bonus` — if additional drift is found, report in debrief findings table.

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_cp24.py -x -q
```

---

## Delivery Footer

**Deliverables:**
- [ ] 4 gold master fixture files regenerated via `scripts/regen_gold_masters.py`
- [ ] ENGINE-GOLD-MASTER-REGEN 9/9 confirmed
- [ ] `test_spark_integration_stress.py` — 12 previously-failing tests now pass
- [ ] Suite regression check: ≤ 44 failures

**Gate:** ENGINE-GOLD-MASTER-REGEN 9/9 (confirm pass)
**Regression bar:** No new failures. Total failure count ≤ 44.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-GOLD-MASTER-REGEN-001.md` on completion.

**Three-pass format:**
- Pass 1: per-file breakdown (which fixtures were updated), script output, any drift beyond `twd_ac_bonus`
- Pass 2: PM summary ≤100 words
- Pass 3: retrospective — drift caught, any additional field gaps found, recommendations

Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

# WO-ENGINE-PA-2H-FIX-001 — Power Attack Two-Handed Multiplier Fix

**Batch:** PA-FIX (standalone, urgent)
**Priority:** HIGH — Thunder directive 2026-02-27
**WO ID:** WO-ENGINE-PA-2H-FIX-001
**Gate:** ENGINE-POWER-ATTACK (PA) — 8/8 must pass with updated 2× expectations
**Pre-existing failures:** 141 (do not treat as regressions)

---

## Target Lock

**Finding closed:** FINDING-ENGINE-PA-2H-PHB-DEVIATION-001
**Authority:** PHB p.98 (RAW) — "if you use a two-handed weapon... add twice the number subtracted"
**Change:** feat_resolver.py — 2H Power Attack multiplier from 1.5× to 2×
**Gate update:** test_engine_power_attack_gate.py — 2H test cases expected values corrected

The Batch P debrief (DEBRIEF_WO-ENGINE-POWER-ATTACK-001.md) implemented `int(power_attack_penalty * 1.5)` per dispatch spec. That spec was wrong — a silent assumption slipped through without PHB citation. Thunder ruling 2026-02-27: fix to 2×, close the finding.

---

## Binary Decisions

| # | Decision | Ruling |
|---|---------|--------|
| 1 | 1H vs 2H PA multiplier: same or different? | **Different.** 2H=2×, 1H=1×, off-hand=0.5×. Unchanged. |
| 2 | Change STR 1.5× path in attack_resolver.py? | **No.** That is the STR bonus multiplier for two-handed weapons — a separate, correct mechanic. Do NOT touch it. |
| 3 | Update integration test (test_power_attack_integration.py)? | **Yes, if it contains hardcoded 2H PA expectations.** Validate and update. |

**Critical distinction — debrief Pass 3 mandatory:**
> 2H STR bonus = 1.5× STR modifier (attack_resolver.py) — correct, do not change
> 2H PA multiplier = 2× penalty (feat_resolver.py) — this is the fix
> These are two distinct mechanics on two distinct code paths. Do not conflate.

---

## Contract Spec

### A. feat_resolver.py — `get_damage_modifier()`

**File:** `aidm/core/feat_resolver.py`
**Function:** `get_damage_modifier()` → Power Attack block → `is_two_handed` branch

**Change (from Batch P debrief, line known):**
```python
# BEFORE (Batch P — incorrect):
if is_two_handed:
    modifier += int(power_attack_penalty * 1.5)   # dispatch spec: 1.5:1

# AFTER (this WO — PHB p.98 compliant):
if is_two_handed:
    modifier += int(power_attack_penalty * 2)     # PHB p.98: 2:1 for two-handed weapons
```

No other lines in the Power Attack block change. Off-hand (`penalty // 2`) and 1H (`penalty`) paths are correct and untouched.

### B. tests/test_engine_power_attack_gate.py — 2H test case expectations

**File:** `tests/test_engine_power_attack_gate.py`
**Action:** Locate all PA gate tests that set `is_two_handed=True` (or pass a `grip="two-handed"` fixture). Update the expected damage bonus from the old 1.5× value to the new 2× value.

**Example arithmetic:** PA penalty 4 with 2H weapon
- Old expectation: `int(4 * 1.5) = 6`
- New expectation: `int(4 * 2) = 8`

Do NOT change 1H or off-hand test cases.

### C. tests/test_power_attack_integration.py — validate

**File:** `tests/test_power_attack_integration.py`
**Action:** Read the file. If any tests assert 2H PA damage using hardcoded 1.5× expectations, update them. If tests compute expectations from a multiplier variable, no change needed.

---

## Implementation Plan

1. Read `aidm/core/feat_resolver.py` — confirm `int(power_attack_penalty * 1.5)` at `is_two_handed` branch
2. Make the one-line change: `* 1.5` → `* 2`, update inline comment to cite PHB p.98
3. Read `tests/test_engine_power_attack_gate.py` — identify 2H test cases, update expected values
4. Read `tests/test_power_attack_integration.py` — check for 2H hardcoded expectations, update if needed
5. Update `docs/RAW_FIDELITY_AUDIT.md` — add Power Attack to the Combat Feats section (or COMBAT MODIFIERS section if no feats section exists). Row format:
   `| Power Attack | PHB p.97–98 | FULL | 2H=2×, 1H=1×, off-hand=0.5×; BAB cap on penalty |`
6. Run `pytest tests/test_engine_power_attack_gate.py` — all 8/8 must pass
7. Run full regression (cap: 1 fix attempt if new failures). Pre-existing: 141. Do not loop.
8. File debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-PA-2H-FIX-001.md`

**Retry cap:** If regression produces new failures, fix once, re-run once. If still failing: record in debrief and stop. Do not loop.

---

## Integration Seams

- **Primary touch:** `aidm/core/feat_resolver.py` — `get_damage_modifier()` — `is_two_handed` branch — one-line change
- **Secondary touch:** `tests/test_engine_power_attack_gate.py` — 2H expectation updates only
- **Validate only:** `tests/test_power_attack_integration.py` — update if hardcoded, skip if computed
- **No touch:** `aidm/core/attack_resolver.py` — STR 1.5× path is correct and separate
- **Audit update:** `docs/RAW_FIDELITY_AUDIT.md` — add Power Attack row (missing entirely — predates Batch P)

Event constructor signature (for any events emitted):
```python
Event(event_id=..., event_type="...", payload={...})
```
NOT `id=`, `type=`, `data=`.

---

## Assumptions to Validate

1. `int(power_attack_penalty * 1.5)` is the exact expression at the `is_two_handed` branch in `feat_resolver.py:get_damage_modifier()` — confirm before editing (from Batch P debrief, this is expected)
2. `tests/test_engine_power_attack_gate.py` contains PA gate tests PA-001 through PA-008 with hardcoded 2H expected bonus values — confirm at least one 2H case exists
3. No other resolver applies a second PA multiplier to the 2H path (attack_resolver.py delegates to feat_resolver for PA bonus — confirmed in Batch P debrief, no double-application)
4. STR 1.5× path in attack_resolver.py is in a separate code path from PA multiplier — confirm they are independent, do not interact

If assumption 1 is wrong (expression differs), pause, document actual expression, adjust accordingly before editing.

---

## Preflight

- [ ] `python scripts/verify_session_start.py` passes
- [ ] Read feat_resolver.py and confirm assumption 1 before any edit
- [ ] `git status` clean before first edit

---

## Debrief Required

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-PA-2H-FIX-001.md`

**Pass 1:** File breakdown — feat_resolver.py (exact line changed, before/after), gate test file (which tests updated, old vs. new expected values), integration test (changed or not changed with reason), RAW_FIDELITY_AUDIT.md (confirm Power Attack row added with FULL status)

**Pass 2:** PM summary ≤100 words

**Pass 3 — MANDATORY FINDING:**
> "2H STR bonus (1.5× in attack_resolver.py) and 2H PA multiplier (2× in feat_resolver.py) are confirmed as two separate mechanics on separate code paths. STR path unchanged and correct. PA path corrected to PHB p.98. These must not be conflated in future WOs."

**Radar:** Any new findings (especially if a third 2H multiplier site exists anywhere in the codebase).

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

## Delivery Footer

**Authority:** PHB p.98 (RAW) — "add twice the number subtracted from your attack roll"
**Finding closed on ACCEPTED:** FINDING-ENGINE-PA-2H-PHB-DEVIATION-001
**Provenance:** RAW — not a house policy deviation
**Dispatched by:** Slate (PM) — 2026-02-27
**Dispatch authorized by:** Thunder (PO) — ruling 2026-02-27

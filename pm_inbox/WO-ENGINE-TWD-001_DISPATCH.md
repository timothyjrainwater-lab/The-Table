# WO-ENGINE-TWD-001 — Two-Weapon Defense

**Type:** Builder WO
**Gate:** ENGINE-TWD
**Tests:** 8 (TWD-01 through TWD-08)
**Depends on:** WO-ENGINE-TWF-WIRE (ACCEPTED — `full_attack_resolver.py` TWF patterns in place)
**Blocks:** nothing
**Priority:** Low — closes a PHB feat gap

---

## 1. Target Lock

Two-Weapon Defense (PHB p.102) grants a shield-equivalent AC bonus when wielding two weapons. The feat is recognized in chargen (`EF.FEATS`) but has no runtime effect. Wire the AC bonus into the defender AC calculation in `attack_resolver.py`.

**PHB p.102 spec:**
- Wielding two weapons (main + off-hand): +1 shield bonus to AC
- Improved Two-Weapon Defense: +2 shield bonus to AC
- Greater Two-Weapon Defense: +3 shield bonus to AC
- Bonus applies only when not flat-footed (shield bonus lost when denied Dex)
- Bonus applies to melee and ranged AC equally (it is a shield bonus, not dodge)

---

## 2. Binary Decisions

| # | Question | Answer |
|---|---|---|
| BD-01 | Where is the bonus applied? | Defender AC in `attack_resolver.py` — same location as fight_defensively_ac extraction. Read from `EF.FEATS` on the defender entity at attack time. |
| BD-02 | Flat-footed suppression? | Yes. Shield bonus is lost when flat-footed (denied Dex). Check `is_flat_footed()` or equivalent condition flag before applying. |
| BD-03 | Stored as TEMPORARY_MODIFIERS? | No. TWD is a passive feat bonus, not a declared action. Computed on-the-fly from feat list at attack resolution time — no storage needed. |
| BD-04 | Off-hand weapon required? | Yes. Bonus only applies when `FullAttackIntent.off_hand_weapon` is set OR entity has `EF.WEAPON` with `is_off_hand=True`. Single-weapon wielder gets nothing even with the feat. |
| BD-05 | Event emitted? | Yes — include `twd_ac_bonus` field in existing `attack_roll` event payload (value 0 if not applicable, 1/2/3 if active). No new event type needed. |

---

## 3. Contract Spec

### New helper function — `full_attack_resolver.py`

```python
def _compute_twd_ac_bonus(defender: dict) -> int:
    """Compute Two-Weapon Defense AC bonus for defender.

    PHB p.102: Shield bonus when wielding two weapons.
    Returns 0 if feat not present or defender is flat-footed.

    Progression:
      Two-Weapon Defense          → +1
      Improved Two-Weapon Defense → +2
      Greater Two-Weapon Defense  → +3
    """
```

### Wiring in `attack_resolver.py`

At the point where defender AC is assembled (before hit determination):

```python
twd_bonus = _compute_twd_ac_bonus(target)
effective_ac = base_ac + ... + twd_bonus
```

### Flat-footed check

Defender loses shield bonus when flat-footed. Check for:
- `ConditionType.HELPLESS` in conditions
- `ConditionType.STUNNED` in conditions
- `ConditionType.PINNED` in conditions
- OR any condition with `loses_dex=True`

If any apply, `twd_bonus = 0`.

### Off-hand weapon detection

```python
def _has_off_hand_weapon(defender: dict) -> bool:
    """True if defender is wielding an off-hand weapon."""
    # Check EF.WEAPON for is_off_hand flag or secondary weapon slot
    ...
```

### Feat strings (match existing `EF.FEATS` conventions)

```python
TWD_FEATS = {
    "Two-Weapon Defense": 1,
    "Improved Two-Weapon Defense": 2,
    "Greater Two-Weapon Defense": 3,
}
```

### Event payload addition

Add to existing `attack_roll` event `details` dict:
```python
"twd_ac_bonus": twd_bonus  # int, 0 if not active
```

---

## 4. Implementation Plan

1. Add `_compute_twd_ac_bonus()` helper to `full_attack_resolver.py` (imports already present)
2. Add `_has_off_hand_weapon()` helper — reads `EF.WEAPON` for off-hand indicator
3. Wire both into defender AC assembly in `attack_resolver.py`
4. Add `twd_ac_bonus` field to `attack_roll` event payload
5. Add gate tests `tests/test_engine_twd_gate.py` (TWD-01 through TWD-08)
6. Zero existing test regressions — passive bonus, no new intents, no new events

---

## 5. Gate Tests (ENGINE-TWD 8/8)

| ID | Description |
|----|-------------|
| TWD-01 | Defender with TWD feat + off-hand weapon: effective AC is +1 higher than base |
| TWD-02 | Defender with Improved TWD: effective AC is +2 higher |
| TWD-03 | Defender with Greater TWD: effective AC is +3 higher |
| TWD-04 | Defender with TWD but no off-hand weapon: bonus is 0 |
| TWD-05 | Defender with TWD + off-hand but flat-footed (HELPLESS condition): bonus is 0 |
| TWD-06 | Defender with TWD + off-hand but PINNED: bonus is 0 |
| TWD-07 | `attack_roll` event payload contains `twd_ac_bonus` field (0 when not active) |
| TWD-08 | `attack_roll` event payload contains `twd_ac_bonus` field (correct value when active) |

---

## 6. Delivery Footer

**Files to create:**
- `tests/test_engine_twd_gate.py`

**Files to modify:**
- `aidm/core/full_attack_resolver.py` — add `_compute_twd_ac_bonus()`, `_has_off_hand_weapon()`
- `aidm/core/attack_resolver.py` — wire twd bonus into defender AC assembly + event payload

**No new EF constants required** — feat check reads from existing `EF.FEATS`.
**No new intent classes required** — passive feat, no action.
**No new event types required** — payload field added to existing `attack_roll`.

**Commit requirement:** Builder commits all changes. Message: `feat: WO-ENGINE-TWD-001 — Two-Weapon Defense AC bonus — Gate ENGINE-TWD 8/8`

**Preflight:** Run `pytest tests/test_engine_twd_gate.py -v` — 8/8 must pass. Run full suite — 0 new failures.

---

## 7. Integration Seams

- `attack_resolver.py` AC assembly: add `twd_bonus` alongside existing `fight_defensively_ac` and `total_defense_ac` extraction from TEMPORARY_MODIFIERS
- `full_attack_resolver.py`: helper lives here (near `_compute_twf_penalties`) — imported into `attack_resolver.py`
- Flat-footed check reuses existing condition introspection already in `attack_resolver.py`

---

## 8. Assumptions to Validate

- `EF.FEATS` is a list of strings on defender entity — confirmed (WO-034, test pattern `"Two-Weapon Fighting" in feats`)
- Off-hand weapon detection: confirm `EF.WEAPON` dict has an `is_off_hand` key, OR that `FullAttackIntent.off_hand_weapon` is the canonical source — builder must check before implementing `_has_off_hand_weapon()`
- Flat-footed condition detection: builder verifies which conditions set `loses_dex=True` in `conditions.py`

---

## 9. Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

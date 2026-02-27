# ENGINE DISPATCH — BATCH R
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**Lifecycle:** DISPATCH-READY
**To:** Chisel (lead builder)
**Batch:** R — 4 WOs, 32 gate tests
**Prerequisite:** NONE — runs in parallel with ENGINE BATCH P

**Parallel track:** Batch R intentionally avoids `attack_resolver.py`, `maneuver_resolver.py`, and `play_loop.py` — the three files locked by Batch P. Start immediately after dirty-tree baseline is committed; do not wait for Batch P to close.

**Batch Q coupling note:** Batch R WO4 (GTWF) and Batch Q WO3 (WFC) both touch `full_attack_resolver.py`. Ensure Batch R WO4 is committed and clean before Batch Q WO3 begins.

---

## Boot Sequence

1. Read `docs/ops/CHISEL_KERNEL_001.md`
2. Confirm dirty-tree baseline is committed — `git status` must show clean tracked files before any WO begins. If dirty tree is still present from the Batch P baseline commit, stop and flag to Thunder.
3. Read `pm_inbox/PM_BRIEFING_CURRENT.md`
4. Run `python scripts/verify_session_start.py`
5. Orphan check: any WO IN EXECUTION with no debrief? Flag before proceeding.
6. Record pre-existing failure count: `pytest --tb=no -q`

---

## Intelligence Update

**File ownership — zero overlap with Batch P:**

| WO | File(s) | Batch P conflict? |
|---|---|---|
| WO1 (IE) | `spell_resolver.py` | None |
| WO2 (MB) | `aoo.py` | None |
| WO3 (SP) | `aoo.py` | None |
| WO4 (GTWF) | `full_attack_resolver.py` | None |

**WO2 and WO3 both touch `aoo.py`.** Commit WO2 before WO3.

**Recommended commit order:** WO1 → WO2 → WO3 → WO4.

**Evasion insertion site:** Batch B R1 debrief confirmed Evasion lives in `_resolve_damage()` in `spell_resolver.py`, threaded with `world_state` and `target_entity_id`. Improved Evasion inserts at the same site, in the FAILED Reflex save branch immediately below the existing Evasion check.

**Improved Evasion is a class feature, not a feat.** Check: `rogue_level >= 10 OR monk_level >= 9`. Use `entity.get(EF.CLASS_LEVELS, {}).get("rogue", 0)`. Do NOT look for `"improved_evasion"` in `EF.FEATS`.

**Mobility TEMPORARY_MODIFIERS assumption:** Mobility grants +4 dodge AC against movement-provoked AoOs specifically. The cleanest implementation sets `EF.TEMPORARY_MODIFIERS["mobility_dodge_ac"] = 4` on the moving entity in `aoo.py` before the AoO resolves, then clears it after. This requires `attack_resolver.py` to already read `TEMPORARY_MODIFIERS` AC keys generically (or include `mobility_dodge_ac` in its lookup). **On boot, confirm that `attack_resolver.py` reads TEMPORARY_MODIFIERS AC values generically or by known-key enumeration.** If a new key requires a change to `attack_resolver.py`: WO2 is BLOCKED — defer Mobility, note in debrief, skip to WO3. Do not touch `attack_resolver.py`.

**AoO standing from prone:** FINDING-CE-STANDING-AOO-001 deferred "pending grapple movement WO." Grapple is now fully wired (ENGINE-GRAPPLE-PIN 10/10). Blocker is cleared. Implementation is purely in `aoo.py` — add the prone stand-up case inside `check_aoo_triggers()` (or equivalent) without modifying `play_loop.py`.

**Greater TWF chain:** TWF (−2/−2 penalty, one off-hand attack) and Improved TWF (second off-hand at −5) confirmed wired in `full_attack_resolver.py` (Gate CP-21 12/12). Greater TWF adds a third off-hand attack at highest BAB −10. Pattern: extend the off-hand attack list after ITWF check, same half-STR damage as all off-hand attacks.

**EF.CLASS_LEVELS pattern:** `entity.get(EF.CLASS_LEVELS, {}).get("rogue", 0)` — confirmed.

**EF.ARMOR_TYPE pattern:** `entity.get(EF.ARMOR_TYPE, "none")` — added in Batch D (WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001). Values: `"none"`, `"light"`, `"medium"`, `"heavy"`.

**Event constructor:** `Event(event_id=..., event_type=..., payload=...)`.

---

## WO 1 — WO-ENGINE-IMPROVED-EVASION-001

**Scope:** `aidm/core/spell_resolver.py`
**Gate file:** `tests/test_engine_improved_evasion_gate.py`
**Gate label:** ENGINE-IMPROVED-EVASION
**Gate count:** 8 tests (IE-001 – IE-008)
**Kernel touch:** NONE
**Source:** PHB p.50 (Rogue), p.41 (Monk)

### Gap Verification

Deferred explicitly from Batch B R1 WO1 debrief: "Improved Evasion: still takes half on failed save. Deferred: Improved Evasion with Reflex fail-half (separate WO candidate)."

PHB p.50: "If a rogue with improved evasion is exposed to any effect that normally allows her to attempt a Reflex saving throw for half damage, she takes no damage if she makes a saving throw and only half damage on a failed save." Armor restriction: cannot use Improved Evasion in medium or heavy armor (same as Evasion).

**Assumptions to Validate on boot:**
- Locate `_resolve_damage()` in `spell_resolver.py`. Confirm existing Evasion check (on successful Reflex save → 0 damage). Improved Evasion inserts in the FAILED branch immediately below.
- Confirm armor check: `EF.ARMOR_TYPE` in `("none", "light")` required for IE to trigger. Medium/heavy suppress.
- SAI check: search for `improved_evasion` or `rogue_level >= 10` in `spell_resolver.py`. If already wired, document as SAI and run gate tests only.
- Confirm class level thresholds: rogue ≥ 10, monk ≥ 9 (PHB p.50/41).

### Implementation

In `spell_resolver.py`, in `_resolve_damage()`, after the Reflex save result:

```python
# Existing Evasion (success branch):
if reflex_save_succeeded and has_evasion:
    final_damage = 0  # already wired

# Add Improved Evasion (failure branch):
if reflex_save_failed:
    _rogue_lvl = target.get(EF.CLASS_LEVELS, {}).get("rogue", 0)
    _monk_lvl = target.get(EF.CLASS_LEVELS, {}).get("monk", 0)
    _armor = target.get(EF.ARMOR_TYPE, "none")
    _has_ie = (_rogue_lvl >= 10 or _monk_lvl >= 9) and _armor in ("none", "light")
    if _has_ie:
        final_damage = final_damage // 2
        events.append(Event(event_id=..., event_type="improved_evasion_active",
                            payload={"target_id": target_id, "damage_halved": final_damage}))
```

### Gate Tests (IE-001 – IE-008)

```python
# IE-001: Rogue 10, fails Reflex save vs AoE → half damage (not full)
# IE-002: Monk 9, fails Reflex save → half damage
# IE-003: Rogue 10, succeeds Reflex save → no damage (Evasion success case unaffected)
# IE-004: Rogue 9 (below threshold), fails Reflex → full damage (no IE)
# IE-005: No Evasion class, fails Reflex → full damage (regression guard)
# IE-006: Rogue 10 in medium armor, fails → full damage (armor suppresses IE)
# IE-007: improved_evasion_active event emitted with damage_halved payload when IE triggers
# IE-008: Rogue 10 in light armor, fails → half damage (light armor does NOT suppress)
```

### Session Close Conditions
- [ ] `git add aidm/core/spell_resolver.py tests/test_engine_improved_evasion_gate.py`
- [ ] `git commit`
- [ ] IE-001–IE-008: 8/8 PASS; zero regressions

---

## WO 2 — WO-ENGINE-MOBILITY-001

**Scope:** `aidm/core/aoo.py`
**Gate file:** `tests/test_engine_mobility_gate.py`
**Gate label:** ENGINE-MOBILITY
**Gate count:** 8 tests (MB-001 – MB-008)
**Kernel touch:** NONE
**Source:** PHB p.97

**Blocked condition:** If on-boot audit confirms `attack_resolver.py` must be modified to read `mobility_dodge_ac` from TEMPORARY_MODIFIERS — this WO is BLOCKED. Skip to WO3. Document in debrief. Do not touch `attack_resolver.py`.

### Gap Verification

Coverage map: MISSING. PHB p.97: "+4 dodge bonus to AC against attacks of opportunity caused when you move out of or within a threatened area." Prerequisite: Dodge feat. The bonus applies only to movement-provoked AoOs, not to all AoOs.

**Assumptions to Validate on boot:**
- Search `attack_resolver.py` for TEMPORARY_MODIFIERS AC key enumeration. If it sums all keys matching a pattern (e.g., keys ending in `_ac`) or reads a general AC bonus dict → implementation is safe in `aoo.py` alone.
- Search `aoo.py` for `check_aoo_triggers()` or equivalent. Confirm this is where movement-provoked AoOs are determined. Mobility sets the marker HERE, before the AoO attack resolves.
- Confirm feat key: `"mobility"` (lowercase).
- Confirm TEMPORARY_MODIFIERS is the correct pattern (not a separate EF field).

### Implementation

In `aoo.py`, when a movement-provoked AoO is about to be resolved for a creature with Mobility:

```python
# In movement AoO resolution path:
_mover_feats = mover_entity.get(EF.FEATS, [])
if "mobility" in _mover_feats:
    # Set temporary dodge AC bonus for this AoO only
    _tmp = mover_entity.setdefault(EF.TEMPORARY_MODIFIERS, {})
    _tmp["mobility_dodge_ac"] = 4
    events.append(Event(event_id=..., event_type="mobility_active",
                        payload={"actor_id": mover_id}))

# ... resolve AoO attack (attack_resolver.py reads mobility_dodge_ac) ...

# Clear immediately after AoO resolves (before next trigger):
if "mobility_dodge_ac" in mover_entity.get(EF.TEMPORARY_MODIFIERS, {}):
    del mover_entity[EF.TEMPORARY_MODIFIERS]["mobility_dodge_ac"]
```

### Gate Tests (MB-001 – MB-008)

```python
# MB-001: Mobility feat, movement provokes AoO → AoO attack roll is vs AC+4
# MB-002: No Mobility feat, movement provokes AoO → normal AC (no bonus)
# MB-003: Mobility feat, non-movement AoO (e.g., spell cast) → no +4 bonus (movement-only)
# MB-004: Mobility bonus is dodge type → stacks with other bonuses (does not interfere with CEX/total-defense)
# MB-005: mobility_active event emitted when Mobility triggers
# MB-006: mobility_dodge_ac cleared after AoO resolves (no carryover to next action)
# MB-007: Multiple movement AoOs in same round → Mobility applies to each
# MB-008: Regression — non-Mobility entity movement-AoO path unaffected
```

### Session Close Conditions
- [ ] `git add aidm/core/aoo.py tests/test_engine_mobility_gate.py`
- [ ] `git commit`
- [ ] MB-001–MB-008: 8/8 PASS; zero regressions

---

## WO 3 — WO-ENGINE-AOO-STANDING-PRONE-001

**Scope:** `aidm/core/aoo.py`
**Gate file:** `tests/test_engine_aoo_standing_prone_gate.py`
**Gate label:** ENGINE-AOO-STANDING-PRONE
**Gate count:** 8 tests (SP-001 – SP-008)
**Kernel touch:** NONE
**Source:** PHB p.137, p.154

**Closes:** FINDING-CE-STANDING-AOO-001

**Commit WO2 first** — both WO2 and WO3 touch `aoo.py`.

### Gap Verification

FINDING-CE-STANDING-AOO-001: OPEN — "`standing_triggers_aoo` (prone stand-up provokes AoO) not wired in aoo.py. Deferred pending grapple movement WO." Grapple WO is now fully wired and accepted (ENGINE-GRAPPLE-PIN 10/10). Blocker is cleared.

PHB p.154: Standing up from prone is a move action and provokes AoO from all threatening opponents.

**Assumptions to Validate on boot:**
- Search `aoo.py` for `check_aoo_triggers()` or the equivalent function that determines whether an intent provokes AoO. The prone stand-up case inserts here.
- Determine how "standing from prone" is represented: is there a distinct `StandFromProneIntent`? Or does it come through as a `FullMoveIntent` with the actor having `PRONE` condition? Confirm the intent type on boot; gate tests may need to match the actual intent used.
- Confirm `PRONE` condition key in `EF.CONDITIONS` (dict, per Batch O confirmation).
- The `check_aoo_triggers()` function must NOT require changes to `play_loop.py` — the AoO trigger check should be fully self-contained in `aoo.py`.

### Implementation

In `aoo.py`, in `check_aoo_triggers()`, add the prone stand-up case:

```python
# Standing from prone provokes AoO (PHB p.154):
_is_standing_from_prone = (
    isinstance(combat_intent, StandFromProneIntent)  # if distinct intent exists
    # OR: isinstance(combat_intent, FullMoveIntent) and "prone" in actor.get(EF.CONDITIONS, {})
)
if _is_standing_from_prone:
    # AoO from all threatening opponents (standard AoO logic applies)
    aoo_triggers.extend(_get_threatening_opponents(actor_id, world_state))
```

Use whichever intent form is confirmed on boot. If there is no distinct stand-up intent, use the FullMoveIntent + PRONE condition pattern.

### Gate Tests (SP-001 – SP-008)

```python
# SP-001: Prone entity stands up (move action), adjacent enemy → AoO triggered
# SP-002: Prone entity stands up, no adjacent enemy → no AoO (nothing to trigger from)
# SP-003: Non-prone entity uses move action → no prone-stand AoO triggered
# SP-004: Prone entity stands up, enemy AoO hits → damage applied normally
# SP-005: Prone entity stands up, enemy AoO misses → entity stands, no damage
# SP-006: Multiple adjacent enemies, entity stands → each threatening enemy gets AoO
# SP-007: Entity with Improved Uncanny Dodge stands from prone → IUD does not apply (not a flanking case; AoO is not SA-based)
# SP-008: Regression — FullMoveIntent without PRONE condition does not spuriously trigger prone-stand AoO
```

### Session Close Conditions
- [ ] `git add aidm/core/aoo.py tests/test_engine_aoo_standing_prone_gate.py`
- [ ] `git commit`
- [ ] SP-001–SP-008: 8/8 PASS; zero regressions
- [ ] FINDING-CE-STANDING-AOO-001: CLOSED in debrief

---

## WO 4 — WO-ENGINE-GREATER-TWF-001

**Scope:** `aidm/core/full_attack_resolver.py`
**Gate file:** `tests/test_engine_greater_twf_gate.py`
**Gate label:** ENGINE-GREATER-TWF
**Gate count:** 8 tests (GTWF-001 – GTWF-008)
**Kernel touch:** NONE
**Source:** PHB p.96

### Gap Verification

TWF chain status: TWF (−2/−2, one off-hand) + Improved TWF (second off-hand at −5 from highest BAB) ACCEPTED via WO-ENGINE-TWF-WIRE (Gate CP-21 12/12). Greater TWF: third off-hand attack at highest BAB −10. Not yet wired — no ENGINE-GREATER-TWF in gate table.

**Assumptions to Validate on boot:**
- In `full_attack_resolver.py`, locate where the second off-hand attack (ITWF) is appended. GTWF inserts after this, gated on `"greater_two_weapon_fighting" in attacker_feats`.
- Confirm the off-hand penalty scheme: PHB says each off-hand attack uses the same TWF penalty structure. The third off-hand attack follows the iterative progression (highest BAB −10) just like the second (highest BAB −5). Confirm the ITWF attack is at `highest_bab - 5` on boot — GTWF appends at `highest_bab - 10`.
- Confirm half-STR damage applies to the third off-hand attack (same as first and second off-hand).
- Feat key: `"greater_two_weapon_fighting"` (lowercase, underscore).
- SAI check: search `full_attack_resolver.py` for `greater_two_weapon_fighting`. If already wired, document as SAI.

### Implementation

In `full_attack_resolver.py`, immediately after the ITWF off-hand attack is appended:

```python
# Greater Two-Weapon Fighting: third off-hand attack at highest_bab - 10
if "greater_two_weapon_fighting" in attacker_feats:
    gtwf_bonus = highest_bab - 10
    offhand_attacks.append(
        _build_offhand_attack(attacker_id, offhand_weapon, gtwf_bonus,
                              str_mod_half, twf_penalty, world_state)
    )
```

Where `_build_offhand_attack()` (or equivalent inline logic) is the same helper used for the first and second off-hand attacks. Half-STR damage, TWF penalty, same event type as other off-hand attacks.

### Gate Tests (GTWF-001 – GTWF-008)

```python
# GTWF-001: Greater TWF feat, full attack → third off-hand attack appears in event sequence
# GTWF-002: ITWF only (no GTWF) → exactly two off-hand attacks; third not triggered (regression guard)
# GTWF-003: TWF only (no ITWF, no GTWF) → exactly one off-hand attack (regression guard)
# GTWF-004: GTWF third off-hand attack uses highest_bab - 10 as attack bonus
# GTWF-005: GTWF third off-hand: half-STR damage applied (same as first and second off-hand)
# GTWF-006: Main-hand iterative attacks unaffected by GTWF — count and bonuses unchanged
# GTWF-007: Three off-hand attack events emitted in sequence (event ordering: main then off-hand interleaved per existing pattern)
# GTWF-008: Regression — full suite of TWF events unaffected (CP-21 pattern preserved)
```

### Session Close Conditions
- [ ] `git add aidm/core/full_attack_resolver.py tests/test_engine_greater_twf_gate.py`
- [ ] `git commit`
- [ ] GTWF-001–GTWF-008: 8/8 PASS; zero regressions

---

## File Ownership

| WO | Files touched |
|---|---|
| WO1 | `spell_resolver.py` |
| WO2 | `aoo.py` |
| WO3 | `aoo.py` |
| WO4 | `full_attack_resolver.py` |

**WO2 and WO3 both touch `aoo.py`.** Commit WO2 before WO3. All other WOs are independent of each other.

**No overlap with Batch P** (`attack_resolver.py` / `maneuver_resolver.py` / `play_loop.py`).

---

## Regression Protocol

WO-specific gates first:
```bash
pytest tests/test_engine_improved_evasion_gate.py -v
pytest tests/test_engine_mobility_gate.py -v
pytest tests/test_engine_aoo_standing_prone_gate.py -v
pytest tests/test_engine_greater_twf_gate.py -v
```

Full suite after all committed:
```bash
pytest --tb=short -q
```

**Retry cap:** Fix once, re-run once. Record in debrief and stop. Do not loop.

**If WO2 (Mobility) is BLOCKED** on boot (attack_resolver.py touch required): skip WO2, run WO3 and WO4 as normal. File debrief for WO2 with BLOCKED status and root cause. Batch R closes with 24/32 gates (WO1+WO3+WO4 = 24). PM will re-queue Mobility for a later batch when Batch P/Q are settled.

---

## Debrief Requirements

Three-pass format for all WOs executed.
- WO1 Pass 3: confirm insertion site (file:line in spell_resolver.py); confirm armor types tested; note whether class level check uses EF.CLASS_LEVELS or a cached feature flag
- WO2 Pass 3: document TEMPORARY_MODIFIERS read pattern in attack_resolver.py (generic vs enumerated keys); confirm mobility_dodge_ac cleared after each AoO; if BLOCKED — document root cause and the attack_resolver.py line that would need to change
- WO3 Pass 3: document which intent type represents stand-from-prone (StandFromProneIntent vs FullMoveIntent+PRONE); file CLOSED on FINDING-CE-STANDING-AOO-001; note whether grapple-movement deferred note in finding is now fully resolved
- WO4 Pass 3: document ITWF attack bonus (highest_bab - 5 confirmed?); confirm third off-hand at highest_bab - 10; note Batch Q coupling (full_attack_resolver.py now touched — Batch Q WO3/WFC must commit after this)

Post-debrief: ask builder "Anything else you noticed outside the debrief?" File loose threads before closing.

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-[NAME]-001.md`
Missing debrief or missing Pass 3 → REJECT.

---

## Session Close Conditions

- [ ] All executed WOs committed with gate run before each
- [ ] IE: 8/8, MB: 8/8 (or BLOCKED — documented), SP: 8/8, GTWF: 8/8
- [ ] Zero regressions
- [ ] Chisel kernel updated
- [ ] FINDING-CE-STANDING-AOO-001: CLOSED

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Dispatch issued by Slate. Thunder dispatches to Chisel per ops contract.*

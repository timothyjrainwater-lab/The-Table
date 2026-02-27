# ENGINE DISPATCH — BATCH Q
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**Lifecycle:** DISPATCH-READY
**To:** Chisel (lead builder)
**Batch:** Q — 4 WOs, 32 gate tests
**Prerequisite:** ENGINE BATCH P ACCEPTED

**Note:** WO detail is inline in this file. Combined format (inbox at cap).

---

## Boot Sequence

1. Read `docs/ops/CHISEL_KERNEL_001.md`
2. Confirm Batch P ACCEPTED — verify PA/IMB/PS/IDC gate counts (8+8+8+8 = 32)
3. Read `pm_inbox/PM_BRIEFING_CURRENT.md`
4. Run `python scripts/verify_session_start.py`
5. Orphan check: any WO IN EXECUTION with no debrief? Flag before proceeding.
6. Record pre-existing failure count: `pytest --tb=no -q`

---

## Intelligence Update

**File conflicts:**
- All 4 WOs touch `attack_resolver.py`. Commit each WO before starting the next.
- WO3 (WFC) also touches `full_attack_resolver.py`. WO4 (WSP) does not.

**Recommended commit order:** WO1 → WO2 → WO3 → WO4.

**Cleave architecture:** Cleave bonus attack logic lives in `attack_resolver.py`. The ENGINE-CLEAVE gate (10/10) confirmed basic Cleave is wired. ENGINE-CLEAVE-ADJACENCY (6/6, Batch C) confirmed adjacency guard via `_find_cleave_target()`. Great Cleave (WO1) extends this: check whether a per-round limit flag exists (`cleave_used_this_round` or similar) and bypass it for Great Cleave holders. If no limit flag exists, confirm on boot (may be SAI-adjacent — document in debrief either way).

**Sneak attack flanking path (IUD):** Improved Uncanny Dodge (WO2) suppresses flanking-based sneak attack. Uncanny Dodge (UD, Batch B R1) handled flat-footed DEX bypass at TWO sites (attack_resolver.py:388 + :924). IUD is a separate guard at the flanking eligibility check (not the DEX site). Locate the flanking check that enables sneak attack — this is where IUD suppression goes.

**Weapon type key pattern (WFC/WSP):** Engine `Weapon.weapon_type` is categorical: `light`, `one-handed`, `two-handed`, `ranged`, `natural`. Feat keys follow the pattern `weapon_focus_{weapon_type}` and `weapon_specialization_{weapon_type}`. This is a simplification from PHB (which is per specific weapon), chosen for engine compatibility. Document in debrief.

**All 3 attack bonus sites must be covered for WFC:** Per WO-ENGINE-FAVORED-ENEMY-001 pattern (Batch N): attack bonus applies in both `attack_resolver.py` (single attack) AND `full_attack_resolver.py` (full attack sequence). Weapon Focus +1 must appear in both files. Check whether natural attack resolver (`natural_attack_resolver.py`) also needs coverage — document on boot.

**EF.CLASS_LEVELS pattern:** `entity.get(EF.CLASS_LEVELS, {}).get("rogue", 0)` — confirmed pattern.

**Event constructor:** `Event(event_id=..., event_type=..., payload=...)` — not `id=`, `type=`, `data=`.

---

## WO 1 — WO-ENGINE-GREAT-CLEAVE-001

**Scope:** `aidm/core/attack_resolver.py`
**Gate file:** `tests/test_engine_great_cleave_gate.py`
**Gate label:** ENGINE-GREAT-CLEAVE
**Gate count:** 8 tests (GC-001 – GC-008)
**Kernel touch:** NONE
**Source:** PHB p.93

### Gap Verification

Coverage map: MISSING. Cleave (already wired) grants one free attack when you drop a foe in melee. PHB p.93: "As Cleave, except that there is no limit to the number of times you can use it per round." Great Cleave removes the per-round limit: each killing blow in the round can trigger an additional Cleave attack against an adjacent foe.

**Assumptions to Validate on boot:**
- Search `attack_resolver.py` for `cleave_used_this_round`, `cleave_count`, or any per-round Cleave limiter. If a flag exists: Great Cleave bypasses it. If no per-round limit is enforced in code: Cleave is already functionally unlimited → SAI risk. Verify against gate GC-002 (basic Cleave without Great Cleave feat should produce exactly one bonus attack per round — if the test fails because Cleave is already unlimited, this is an existing bug, not SAI). Document finding in debrief.
- Confirm `_find_cleave_target()` from ENGINE-CLEAVE-ADJACENCY (Batch C) is still the adjacency helper. Great Cleave's additional bonus attacks use the same adjacency check.
- Confirm Cleave event type string — probably `cleave_attack`. Great Cleave bonus attacks emit the same event type (no new event type needed unless preferred).

### Implementation

In `attack_resolver.py`, in the Cleave trigger block, locate where the per-round Cleave limit is enforced. Add Great Cleave bypass:

```python
# Where Cleave per-round limit is checked:
if _attacker_has_cleave and foe_dropped and adjacent_target_exists:
    if cleave_used_this_round and "great_cleave" not in attacker_feats:
        pass  # Cleave exhausted for this round
    else:
        # Fire bonus attack (sets cleave_used_this_round for non-Great-Cleave holders)
        _resolve_cleave_attack(attacker_id, adjacent_target_id, world_state, events)
        if "great_cleave" not in attacker_feats:
            cleave_used_this_round = True
        # (Great Cleave holders: flag not set; next kill can trigger again)
```

Feat guard: `"great_cleave" not in attacker_feats` — no Great Cleave effect without the feat.

Prerequisite assumed enforced at chargen (Cleave + STR 13 + Power Attack). Gate tests check feat presence only.

### Gate Tests (GC-001 – GC-008)

```python
# GC-001: Great Cleave feat + 2nd kill in same round → second Cleave bonus attack triggers
# GC-002: Cleave feat only (no Great Cleave) + 2nd kill → only first Cleave fires; second kill gets no bonus attack (regression guard)
# GC-003: Great Cleave + 3rd kill → third Cleave bonus attack also triggers (chain confirmed)
# GC-004: Great Cleave + kill + no adjacent target → no phantom Cleave (adjacency check still applies)
# GC-005: No Cleave feat, no Great Cleave → no bonus attack on kill (regression guard)
# GC-006: Great Cleave adjacency guard — second Cleave target must be adjacent to first kill (not arbitrary)
# GC-007: cleave_attack event emitted for each Great Cleave bonus attack in sequence
# GC-008: Full attack with Great Cleave — multiple iterative attacks, multiple kills → each kill triggers Cleave
```

### Session Close Conditions
- [ ] `git add aidm/core/attack_resolver.py tests/test_engine_great_cleave_gate.py`
- [ ] `git commit`
- [ ] GC-001–GC-008: 8/8 PASS; zero regressions

---

## WO 2 — WO-ENGINE-IMPROVED-UNCANNY-DODGE-001

**Scope:** `aidm/core/attack_resolver.py`
**Gate file:** `tests/test_engine_improved_uncanny_dodge_gate.py`
**Gate label:** ENGINE-IMPROVED-UNCANNY-DODGE
**Gate count:** 8 tests (IUD-001 – IUD-008)
**Kernel touch:** NONE
**Source:** PHB p.26 (Barbarian), p.50 (Rogue)

**Closes:** FINDING-ENGINE-IMPROVED-UNCANNY-DODGE-001 (deferred Batch C WO4)

**Commit WO1 first** — both WO1 and WO2 touch `attack_resolver.py`.

### Gap Verification

Coverage map: DEFERRED from Batch C. WO-ENGINE-UNCANNY-DODGE-001 was accepted 8/8 (Batch B R1, flat-footed DEX bypass at lines 388+924). Improved Uncanny Dodge was explicitly deferred: "Improved Uncanny Dodge (flanking immunity) deferred."

PHB: "You can no longer be flanked. This defense denies a rogue the ability to sneak attack you by flanking you, unless the attacker has at least four more rogue levels than you have."

**Assumptions to Validate on boot:**
- Locate the flanking check in `attack_resolver.py` that enables sneak attack eligibility. This is the insertion site — it is distinct from the flat-footed DEX bypass sites (lines 388+924 from Batch B R1).
- Confirm feat key: `"improved_uncanny_dodge"` (lowercase, underscore).
- For the rogue-level exception: use `attacker.get(EF.CLASS_LEVELS, {}).get("rogue", 0)` vs `target.get(EF.CLASS_LEVELS, {}).get("rogue", 0) + target.get(EF.CLASS_LEVELS, {}).get("barbarian", 0)` as the IUD-level base. Document this simplification in debrief.
- Confirm that regular Uncanny Dodge (flat-footed DEX bypass) is unaffected at its existing sites.

### Implementation

In `attack_resolver.py`, at the flanking eligibility check for sneak attack:

```python
# Before: if is_flanking: sneak_attack_eligible = True
if is_flanking:
    _target_feats = target_entity.get(EF.FEATS, [])
    if "improved_uncanny_dodge" in _target_feats:
        # Check rogue-level exception: attacker rogue lvl must be ≥ IUD-base + 4
        _attacker_rogue = attacker.get(EF.CLASS_LEVELS, {}).get("rogue", 0)
        _target_iud_base = (
            target_entity.get(EF.CLASS_LEVELS, {}).get("rogue", 0)
            + target_entity.get(EF.CLASS_LEVELS, {}).get("barbarian", 0)
        )
        if _attacker_rogue < _target_iud_base + 4:
            events.append(Event(event_id=..., event_type="improved_uncanny_dodge_active",
                                payload={"target_id": target_id}))
            is_flanking = False  # Suppress flanking for sneak attack
    if is_flanking:
        sneak_attack_eligible = True
```

### Gate Tests (IUD-001 – IUD-008)

```python
# IUD-001: Target with IUD (rogue 8), attacker flanking → flanking suppressed, no sneak attack
# IUD-002: Target with IUD (barbarian 5), attacker flanking → flanking suppressed, no sneak attack
# IUD-003: Target IUD-base=8, attacker rogue_level=12 (≥8+4) → exception applies; flanking valid, sneak attack allowed
# IUD-004: Target IUD-base=8, attacker rogue_level=11 (< 8+4) → suppressed; no sneak attack
# IUD-005: Target WITHOUT IUD, flanked → sneak attack eligible (regression guard)
# IUD-006: IUD active → improved_uncanny_dodge_active event emitted in sequence
# IUD-007: IUD does NOT suppress flat-footed sneak attack — UD regression (lines 388+924 unaffected)
# IUD-008: Regular Uncanny Dodge (flat-footed DEX bypass) still works after IUD commit — regression guard
```

### Session Close Conditions
- [ ] `git add aidm/core/attack_resolver.py tests/test_engine_improved_uncanny_dodge_gate.py`
- [ ] `git commit`
- [ ] IUD-001–IUD-008: 8/8 PASS; zero regressions
- [ ] FINDING-ENGINE-IMPROVED-UNCANNY-DODGE-001: CLOSED in debrief

---

## WO 3 — WO-ENGINE-WEAPON-FOCUS-001

**Scope:** `aidm/core/attack_resolver.py`, `aidm/core/full_attack_resolver.py`
**Gate file:** `tests/test_engine_weapon_focus_gate.py`
**Gate label:** ENGINE-WEAPON-FOCUS
**Gate count:** 8 tests (WFC-001 – WFC-008)
**Kernel touch:** NONE
**Source:** PHB p.102

**Abbreviation note:** Use WFC (Weapon FoCus) internally. "WF" is ENGINE-WEAPON-FINESSE (Batch B R1, 8/8 ACCEPTED) — do NOT conflate.

**Commit WO2 first** — both WO2 and WO3 touch `attack_resolver.py`.

### Gap Verification

Coverage map: MISSING. PHB p.102: "+1 bonus on all attack rolls made with the selected weapon." Prerequisite: proficiency with weapon, BAB +1. Feat key is per-weapon-type in the engine (see Intelligence Update above for simplification rationale).

**Assumptions to Validate on boot:**
- SAI check: search `attack_resolver.py` and `full_attack_resolver.py` for `weapon_focus`. If found and already applying +1 bonus, document as SAI. Otherwise proceed with production changes.
- Confirm `Weapon.weapon_type` values in use: `light`, `one-handed`, `two-handed`, `ranged`, `natural`. Feat key: `f"weapon_focus_{weapon.weapon_type}"`.
- Check `natural_attack_resolver.py` — confirm whether natural attacks should also receive WF bonus. If the natural attack path calls into `attack_resolver.py`, it may inherit the bonus automatically. Document the call chain in debrief.
- Reference pattern: WO-ENGINE-FAVORED-ENEMY-001 touched both `attack_resolver.py:397-398` and `full_attack_resolver.py:706-709`. Weapon Focus must cover both same sites.

### Implementation

In `attack_resolver.py` and `full_attack_resolver.py`, at the attack bonus computation:

```python
# Weapon Focus +1 bonus (PHB p.102)
wf_key = f"weapon_focus_{weapon.weapon_type}"
if wf_key in attacker_feats:
    attack_bonus += 1
    events.append(Event(event_id=..., event_type="weapon_focus_active",
                        payload={"actor_id": attacker_id, "weapon_type": weapon.weapon_type}))
```

Apply at the same site as Favored Enemy attack bonus. No interaction with Power Attack, Combat Expertise, or other attack modifiers — plain additive.

### Gate Tests (WFC-001 – WFC-008)

```python
# WFC-001: weapon_focus_one-handed feat, attack with one-handed weapon → +1 to attack roll
# WFC-002: weapon_focus_one-handed, attack with two-handed weapon → no bonus (type mismatch)
# WFC-003: Full attack (FullAttackIntent) — all iterative attacks get +1 (both resolvers covered)
# WFC-004: weapon_focus_two-handed → +1 with two-handed weapon
# WFC-005: weapon_focus_ranged → +1 with ranged weapon
# WFC-006: No Weapon Focus feat → no attack bonus (regression guard)
# WFC-007: weapon_focus_natural → +1 with natural attacks
# WFC-008: weapon_focus_active event emitted in attack sequence when feat active
```

### Session Close Conditions
- [ ] `git add aidm/core/attack_resolver.py aidm/core/full_attack_resolver.py tests/test_engine_weapon_focus_gate.py`
- [ ] `git commit`
- [ ] WFC-001–WFC-008: 8/8 PASS; zero regressions

---

## WO 4 — WO-ENGINE-WEAPON-SPECIALIZATION-001

**Scope:** `aidm/core/attack_resolver.py`
**Gate file:** `tests/test_engine_weapon_specialization_gate.py`
**Gate label:** ENGINE-WEAPON-SPECIALIZATION
**Gate count:** 8 tests (WSP-001 – WSP-008)
**Kernel touch:** NONE
**Source:** PHB p.102

**Commit WO3 first** — both WO3 and WO4 touch `attack_resolver.py`. WO4 also requires WO3 committed first for design parity (WSP pairs with WFC).

### Gap Verification

Coverage map: MISSING. PHB p.102: "+2 bonus on all damage rolls you make using the selected weapon." Prerequisite: Weapon Focus (same weapon), fighter level 4. Chargen enforces prerequisites. Gate tests check feat presence only.

Feat key follows the same pattern as Weapon Focus: `f"weapon_specialization_{weapon.weapon_type}"`.

**Damage bonus stacking note:** Weapon Specialization +2 is a flat damage bonus. It applies pre-crit and is multiplied by the crit multiplier (same as enhancement bonus and STR mod — PHB p.224: "Roll the damage with all your usual bonuses one extra time"). Apply at the same site as enhancement_bonus in `attack_resolver.py`.

**Assumptions to Validate on boot:**
- SAI check: search `attack_resolver.py` for `weapon_specialization`. If found and already applying +2 damage, document as SAI.
- Confirm the damage bonus site in `attack_resolver.py` is the correct insertion point (before crit multiplier application, so it multiplies on crits).
- Does `full_attack_resolver.py` need a separate WSP wiring? Per the Weapon Enhancement debrief (Batch N): `enhancement_bonus` is applied in BOTH resolvers. Check whether the damage path for full attacks goes through the same damage resolution as single attacks (if `full_attack_resolver.py` calls `resolve_single_attack_with_critical`, the bonus may inherit automatically). Document in debrief.
- Confirm `weapon_focus_{weapon_type}` is already present (WO3 committed) before writing WO4 gate tests.

### Implementation

In `attack_resolver.py`, at the damage bonus computation (after enhancement_bonus, before crit multiplication):

```python
# Weapon Specialization +2 damage bonus (PHB p.102)
ws_key = f"weapon_specialization_{weapon.weapon_type}"
if ws_key in attacker_feats:
    damage_bonus += 2
```

No event emission required (damage bonuses are covered by the `hp_changed` payload). Optional: emit `weapon_specialization_active` for parity with WFC if desired — include in WSP-008 gate test.

### Gate Tests (WSP-001 – WSP-008)

```python
# WSP-001: weapon_specialization_one-handed + matching weapon → +2 to damage roll
# WSP-002: weapon_specialization_one-handed + two-handed weapon → no bonus (type mismatch)
# WSP-003: Full attack — all iterative hits get +2 damage
# WSP-004: Crit confirms: +2 damage bonus is included in crit multiplier (net damage = (base_dice + str_mod + enh + 2) × crit_mult)
# WSP-005: Weapon Focus + Weapon Specialization on same weapon_type → +1 attack AND +2 damage (both active, no interference)
# WSP-006: No Weapon Specialization feat → no damage bonus (regression guard)
# WSP-007: weapon_specialization_two-handed → +2 damage with two-handed weapon
# WSP-008: After WSP commit — WFC regression guard: Weapon Focus +1 attack bonus still applies (WO3 unaffected)
```

### Session Close Conditions
- [ ] `git add aidm/core/attack_resolver.py tests/test_engine_weapon_specialization_gate.py`
- [ ] `git commit`
- [ ] WSP-001–WSP-008: 8/8 PASS; zero regressions

---

## File Ownership

| WO | Files touched |
|---|---|
| WO1 | `attack_resolver.py` |
| WO2 | `attack_resolver.py` |
| WO3 | `attack_resolver.py`, `full_attack_resolver.py` |
| WO4 | `attack_resolver.py` |

**All 4 WOs touch attack_resolver.py.** Commit each before starting the next. Recommended order: WO1 → WO2 → WO3 → WO4.

---

## Regression Protocol

WO-specific gates first:
```bash
pytest tests/test_engine_great_cleave_gate.py -v
pytest tests/test_engine_improved_uncanny_dodge_gate.py -v
pytest tests/test_engine_weapon_focus_gate.py -v
pytest tests/test_engine_weapon_specialization_gate.py -v
```

Full suite after all committed:
```bash
pytest --tb=short -q
```

**Retry cap:** Fix once, re-run once. Record in debrief and stop. Do not loop.

---

## Debrief Requirements

Three-pass format for all 4 WOs.
- WO1 Pass 3: document whether a per-round Cleave limit existed in code; if not found, explain what GC added vs existing behavior; confirm Great Cleave does not bypass the adjacency guard from ENGINE-CLEAVE-ADJACENCY
- WO2 Pass 3: document the flanking check site (file:line); confirm Uncanny Dodge flat-footed sites (388+924) are untouched; note rogue-level comparison formula used; file CLOSED on deferred IUD finding
- WO3 Pass 3: document both attack bonus insertion sites (attack_resolver.py + full_attack_resolver.py line numbers); note whether natural_attack_resolver.py required a separate touch; confirm WF abbreviation collision avoidance (WF = Weapon Finesse, WFC = Weapon Focus in all docs)
- WO4 Pass 3: confirm damage bonus multiplication behavior on crits (pre-crit site confirmed); document whether full_attack_resolver.py required separate wiring or inherited from single-attack path; note WSP+WFC stacking behavior verified by WSP-005

Post-debrief: ask builder "Anything else you noticed outside the debrief?" File loose threads before closing.

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-[NAME]-001.md`
Missing debrief or missing Pass 3 → REJECT.

---

## Session Close Conditions

- [ ] All 4 WOs committed with gate run before each
- [ ] GC: 8/8, IUD: 8/8, WFC: 8/8, WSP: 8/8
- [ ] Zero regressions
- [ ] Chisel kernel updated

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Dispatch issued by Slate. Thunder dispatches to Chisel per ops contract.*

# WO-ENGINE-TWF-WIRE — Two-Weapon Fighting Detection and Penalty Application

**Issued:** 2026-02-23
**Authority:** Audit finding — confirmed stub. `is_twf = False` is hardcoded in both `attack_resolver.py:233` and `full_attack_resolver.py:480`. The `feat_resolver.py` TWF context key `is_twf` is documented (line 145) but never set to True. Result: dual-wielding fighters receive no off-hand attack penalty (should be −5 main / −5 off-hand, or −2/−2 with TWF feat). This is a correctness gap that makes dual-wielders overpowered.
**Gate:** CP-21 (new gate). Target: 12 tests.
**Blocked by:** Nothing. Parallel-safe with XP-01 and CP-17/18/19. Does not touch experience_resolver.py, duration_tracker.py, or condition logic.
**Track:** Engine mechanics.

---

## 1. PHB Contract (p.160)

**Two-Weapon Fighting:**
- Default penalties: −6 main hand, −10 off hand
- If off-hand weapon is light: −4 main hand, −8 off hand
- With Two-Weapon Fighting feat: −4 main hand, −4 off hand
- With TWF feat + light off-hand: −2 main hand, −2 off hand
- Off-hand damage: only STR bonus × 0.5 (already partially implemented at `full_attack_resolver.py:381`)

**When TWF applies:** Player declares a full attack with two weapons. The off-hand weapon is a secondary attack. Single `AttackIntent` never involves TWF — only `FullAttackIntent` with an off-hand weapon.

---

## 2. Binary Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Schema change | Add `off_hand_weapon: Optional[Weapon] = None` to `FullAttackIntent` | Cleanest signal. If present, TWF attack sequence applies. `AttackIntent` unchanged — single attack is never TWF. |
| 2 | TWF penalty computation | New helper `_compute_twf_penalties(attacker, off_hand_weapon) → (main_penalty, off_penalty)` in `full_attack_resolver.py` | Pure function, testable in isolation. |
| 3 | Off-hand attack sequence | After all iterative main-hand attacks, add one off-hand attack at `BAB + off_penalty` with the off-hand weapon | PHB: off-hand gets one attack at full BAB minus penalty. No iterative off-hand attacks unless Improved TWF feat. |
| 4 | `is_twf` flag | Set `is_twf=True` in feat context when `intent.off_hand_weapon is not None` | Lets `feat_resolver.py` TWF bonus apply correctly. |
| 5 | Improved TWF | Detect `EF.FEATS` contains `"Improved Two-Weapon Fighting"` — grants second off-hand attack at BAB−5 | Stay PHB-accurate. |
| 6 | `attack_resolver.py` `is_twf` | Leave `False` — single `AttackIntent` is never TWF by definition | No change to single-attack resolver needed. |
| 7 | Intent bridge | Add `off_hand_weapon` parsing to `intent_bridge.py` — if player says "attack with both swords", route to `FullAttackIntent` with off_hand_weapon set | Wire at parse layer, not just resolver. |
| 8 | Existing off-hand damage | `full_attack_resolver.py:381` already handles `str_modifier * 0.5` for off-hand grip — keep it, add the attack bonus penalty on top | Don't break existing partial implementation. |

---

## 3. Contract Spec

### 3.1 `aidm/core/full_attack_resolver.py` — Schema addition

Add to `FullAttackIntent` dataclass:

```python
off_hand_weapon: Optional["Weapon"] = None  # noqa: F821
"""Off-hand weapon for two-weapon fighting. If set, TWF penalty sequence applies.
PHB p.160: off-hand gets one attack at BAB with penalty applied."""
```

### 3.2 `aidm/core/full_attack_resolver.py` — TWF penalty helper

```python
def _compute_twf_penalties(
    attacker: dict,
    off_hand_weapon: "Weapon",  # noqa: F821
) -> tuple[int, int]:
    """Compute main-hand and off-hand attack penalties for TWF.

    PHB p.160 table:
    - Base: -6 main / -10 off
    - Light off-hand: -4 main / -8 off
    - TWF feat: -4 main / -4 off
    - TWF feat + light off-hand: -2 main / -2 off

    Returns:
        (main_penalty, off_hand_penalty) — both negative integers
    """
    feats = attacker.get(EF.FEATS, [])
    has_twf = "Two-Weapon Fighting" in feats
    light_off_hand = off_hand_weapon.is_light  # Weapon.is_light property

    if has_twf and light_off_hand:
        return (-2, -2)
    elif has_twf:
        return (-4, -4)
    elif light_off_hand:
        return (-4, -8)
    else:
        return (-6, -10)
```

### 3.3 `aidm/core/full_attack_resolver.py` — resolve_full_attack() changes

In `resolve_full_attack()`, before building attack sequence:

```python
# Detect TWF
is_twf = intent.off_hand_weapon is not None
main_penalty = 0
off_penalty = 0
if is_twf:
    attacker = world_state.entities.get(intent.attacker_id, {})
    main_penalty, off_penalty = _compute_twf_penalties(attacker, intent.off_hand_weapon)
```

Apply `main_penalty` to all main-hand iterative attacks:
```python
attack_bonuses = [bab + main_penalty for bab in calculate_iterative_attacks(intent.base_attack_bonus)]
```

After main-hand attacks, add off-hand attack:
```python
if is_twf:
    off_hand_bonus = intent.base_attack_bonus + off_penalty
    # Resolve off-hand attack with off_hand_weapon
    off_hand_events = resolve_single_attack_with_critical(
        attacker_id=intent.attacker_id,
        target_id=intent.target_id,
        attack_bonus=off_hand_bonus,
        weapon=intent.off_hand_weapon,
        is_off_hand=True,  # signals half-STR damage
        ...
    )
    # Add Improved TWF second off-hand attack if feat present
    feats = world_state.entities.get(intent.attacker_id, {}).get(EF.FEATS, [])
    if "Improved Two-Weapon Fighting" in feats:
        off_hand_2_bonus = intent.base_attack_bonus - 5 + off_penalty
        # resolve second off-hand attack ...
```

Update feat context `is_twf` flag:
```python
feat_context = {
    ...
    "is_twf": is_twf,  # Was hardcoded False — now derived from intent
    ...
}
```

### 3.4 `aidm/schemas/attack.py` or `full_attack_resolver.py` — Weapon.is_light property

Confirm `Weapon` dataclass has `is_light` property. If not, add:
```python
@property
def is_light(self) -> bool:
    """PHB p.155: light weapons for TWF penalty reduction."""
    return self.weapon_type == "light"
```

---

## 4. Test Spec (Gate CP-21 — 12 tests)

Write `tests/test_engine_twf_gate.py`:

| ID | Test | Assertion |
|----|------|-----------|
| CP21-01 | No off_hand_weapon → is_twf False, no penalty | Main-hand attack bonus unchanged; no off-hand attack in events |
| CP21-02 | off_hand_weapon set → is_twf True, penalties apply | main_penalty = −6, off_penalty = −10 (no feat, heavy off-hand) |
| CP21-03 | Light off-hand weapon → −4/−8 penalties | `off_hand_weapon.is_light = True`, no TWF feat |
| CP21-04 | TWF feat + heavy off-hand → −4/−4 penalties | Attacker has "Two-Weapon Fighting" in feats |
| CP21-05 | TWF feat + light off-hand → −2/−2 penalties | Best case — daggers both hands with feat |
| CP21-06 | Off-hand attack in events | `full_attack` with off_hand_weapon → events contain off-hand attack_roll |
| CP21-07 | Off-hand damage uses half STR | Off-hand attack_roll event payload has `str_bonus = floor(str_mod / 2)` |
| CP21-08 | Improved TWF grants second off-hand attack | Attacker with "Improved Two-Weapon Fighting" → 2 off-hand attack events |
| CP21-09 | No Improved TWF → one off-hand attack only | Standard TWF → exactly 1 off-hand attack event |
| CP21-10 | `is_twf` flag in feat context when TWF active | `feat_resolver` receives `is_twf=True` in context dict |
| CP21-11 | `is_twf` flag False in feat context when no off-hand | `feat_resolver` receives `is_twf=False` in context dict |
| CP21-12 | Zero regressions — non-TWF full attack unaffected | Existing full attack without off_hand_weapon produces same events as before |

---

## 5. Implementation Plan

1. **Read** `aidm/core/full_attack_resolver.py` (full file) and `aidm/schemas/attack.py` — confirm `Weapon.is_light` presence
2. **Edit** `FullAttackIntent` — add `off_hand_weapon: Optional[Weapon] = None` field
3. **Write** `_compute_twf_penalties()` helper in `full_attack_resolver.py`
4. **Edit** `resolve_full_attack()`:
   - Add TWF detection (`is_twf = intent.off_hand_weapon is not None`)
   - Compute penalties via `_compute_twf_penalties()`
   - Apply `main_penalty` to iterative attack bonuses
   - Add off-hand attack after main-hand sequence
   - Check for Improved TWF second off-hand
   - Set `is_twf` in feat context
5. **Edit** `aidm/interaction/intent_bridge.py` — parse off-hand weapon from "attack with both" style declarations, construct `FullAttackIntent` with `off_hand_weapon` set
6. **Write** `tests/test_engine_twf_gate.py` — 12 tests (CP21-01 through CP21-12)
7. **Run** `pytest tests/test_engine_twf_gate.py -v` — 12/12 PASS
8. **Run** full suite — zero regressions

---

## 6. Deliverables Checklist

- [ ] `FullAttackIntent.off_hand_weapon: Optional[Weapon] = None` added
- [ ] `_compute_twf_penalties(attacker, off_hand_weapon) → (int, int)` implemented
- [ ] `resolve_full_attack()` applies TWF penalty to main-hand attacks
- [ ] `resolve_full_attack()` adds off-hand attack event(s) when `off_hand_weapon` set
- [ ] `feat_context["is_twf"]` set from intent, not hardcoded `False`
- [ ] Improved TWF second off-hand attack wired
- [ ] `intent_bridge.py` parses off-hand weapon into `FullAttackIntent`
- [ ] `tests/test_engine_twf_gate.py` — Gate CP-21: 12/12 PASS
- [ ] Zero regressions on all existing gates

## 7. Integration Seams

- **Files modified:** `aidm/core/full_attack_resolver.py`, `aidm/interaction/intent_bridge.py`
- **Files added:** `tests/test_engine_twf_gate.py`
- **Do not modify:** `attack_resolver.py` (single attack, never TWF), `experience_resolver.py`, `duration_tracker.py`, `play_loop.py` (no changes needed — `is_twf` lives entirely within `full_attack_resolver.py`)
- **Verify:** `Weapon.is_light` property exists in `aidm/schemas/attack.py` — add if missing

## 8. Preflight

```bash
pytest tests/test_engine_twf_gate.py -v
pytest tests/ -x -q --ignore=tests/test_engine_twf_gate.py  # regression check
```

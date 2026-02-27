# ENGINE DISPATCH — BATCH T
**Issued by:** Slate (PM)
**Date:** 2026-02-27
**Lifecycle:** DISPATCH-READY
**To:** Chisel (lead builder)
**Batch:** T — 4 WOs, 32 gate tests
**Prerequisite:** NONE — fourth parallel track

**Parallel track:** Batch T locks only `natural_attack_resolver.py` and `turn_undead_resolver.py`. No overlap with Batch P (`attack_resolver.py` / `maneuver_resolver.py` / `play_loop.py`), Batch R (`spell_resolver.py` / `aoo.py` / `full_attack_resolver.py`), or Batch S (`builder.py` / `save_resolver.py`). Start immediately after dirty-tree baseline is committed.

**Batch Q coupling note:** Batch Q WO3 (WFC) notes that `natural_attack_resolver.py` may or may not inherit Weapon Focus through the call chain. Batch T WO1 boot audit should document whether `natural_attack_resolver.py` delegates to `attack_resolver.py` or maintains its own attack path — file this in WO1 debrief to inform Batch Q WO3.

**Builder.py lock:** Batch S locks `builder.py`. WOs 3 and 4 (turn_undead_resolver.py) must NOT write to `builder.py`. Implement resolver-side only, reading `EF.FEATS` and `EF.DOMAINS` directly. If a chargen write to `builder.py` is unavoidable for WO4, defer WO4 until Batch S closes.

**Difficult Terrain (deferred):** `movement_resolver.py` is not in this batch. Reason: (1) `movement_resolver.py` carries unstaged changes in the working tree (dirty-tree risk), and (2) Difficult Terrain implementation may route through `play_loop.py` (locked by Batch P). Revisit post-Batch-P close.

---

## Boot Sequence

1. Read `docs/ops/CHISEL_KERNEL_001.md`
2. Confirm dirty-tree baseline is committed — `git status` must show clean tracked files before any WO begins.
3. Read `pm_inbox/PM_BRIEFING_CURRENT.md`
4. Run `python scripts/verify_session_start.py`
5. Orphan check: any WO IN EXECUTION with no debrief? Flag before proceeding.
6. Record pre-existing failure count: `pytest --tb=no -q`

---

## Intelligence Update

**File conflicts — none with Batch P, R, or S:**

| WO | File(s) | Batch P conflict? | Batch R conflict? | Batch S conflict? |
|---|---|---|---|---|
| WO1 (MA) | `natural_attack_resolver.py` | None | None | None |
| WO2 (INA) | `natural_attack_resolver.py` | None | None | None |
| WO3 (ITN) | `turn_undead_resolver.py` | None | None | None |
| WO4 (SD) | `turn_undead_resolver.py` | None | None | None¹ |

¹ Conditional: if WO4 requires `builder.py` for domain-based chargen fields, WO4 is blocked until Batch S closes.

**WO1 and WO2 both touch `natural_attack_resolver.py`.** Commit WO1 before WO2.
**WO3 and WO4 both touch `turn_undead_resolver.py`.** Commit WO3 before WO4.
**WO1 and WO3 are file-independent.** Builder executes in order WO1 → WO2 → WO3 → WO4 (single-stream).

**Recommended commit order:** WO1 → WO2 → WO3 → WO4.

**Natural attack system:** Natural attacks are stored on entity as a list of attack definitions (likely `EF.NATURAL_ATTACKS`). Each entry has `attack_type` (string: `"bite"`, `"claw"`, `"gore"`, `"slam"`, `"sting"`, `"tentacle"`, `"wing"`), `damage_dice`, and a primary/secondary flag. Confirm on boot: read `natural_attack_resolver.py` to understand the secondary attack penalty implementation site.

**Secondary attack penalty pattern:** PHB p.134: Primary natural attacks use full BAB; secondary natural attacks suffer −5 penalty. With Multiattack: −2. Likely a constant in `natural_attack_resolver.py`. WO1 SAI risk — search for `−5`, `secondary_penalty`, or `multiattack` on boot.

**Improved Natural Attack die step table (PHB p.96):**
`1d2 → 1d3 → 1d4 → 1d6 → 1d8 → 2d6 → 3d6 → 4d6 → 6d6 → 8d6 → 12d6`

**Feat key for INA:** `f"improved_natural_attack_{attack_type}"` — per attack type. Confirm the exact `attack_type` strings stored in entity natural attacks on boot (from WO1 audit).

**Turning effective level pattern:** `turn_undead_resolver.py` likely computes `_effective_level = entity.get(EF.CLASS_LEVELS, {}).get("cleric", 0)` with adjustments. Improved Turning adds +1. Search for `effective_level` or `turning_level` variable on boot.

**Domain storage:** Cleric domains may be stored in `EF.DOMAINS` (list of strings, e.g., `["sun", "fire"]`) or as feat-like strings in `EF.FEATS`. Confirm on boot before writing WO4. If domain system is absent: WO4 is BLOCKED — file FINDING-ENGINE-DOMAIN-SYSTEM-MISSING-001 and skip WO4.

**Abbreviation conflict guard:** IT = Improved Trip+Sunder (Batch N, WO-ENGINE-IMPROVED-TRIP-SUNDER-001). Improved Turning uses abbreviation ITN throughout this batch. Do NOT use "IT" for Improved Turning in any filename, gate label, or comment.

**Batch S coupling (turn resolvers):**
- Batch S WO3 (ETN) sets `EF.TURN_UNDEAD_USES_MAX` in `builder.py`.
- Batch T WO3 (ITN) and WO4 (SD) operate in `turn_undead_resolver.py` only — zero conflict on `builder.py`.
- `EF.GREATER_TURNING_USES_REMAINING` (if needed for SD) is a different field from `EF.TURN_UNDEAD_USES_MAX` — no conflict.

---

## WO 1 — WO-ENGINE-MULTIATTACK-001

**Scope:** `aidm/core/natural_attack_resolver.py`
**Gate file:** `tests/test_engine_multiattack_gate.py`
**Gate label:** ENGINE-MULTIATTACK
**Gate count:** 8 tests (MA-001 – MA-008)
**Kernel touch:** NONE
**Source:** PHB p.98

### Gap Verification

Coverage map: MISSING. PHB p.98: "The creature's secondary natural attacks only suffer a −2 penalty." Without Multiattack, secondary natural attacks carry a −5 attack penalty (PHB p.134). Prerequisite: 3 or more natural attacks. Gate tests check feat presence only.

**Assumptions to Validate on boot:**
- SAI check: search `natural_attack_resolver.py` for `−5`, `secondary_penalty`, or `multiattack`. If secondary penalty is already conditionally −2 when Multiattack feat is present, document as SAI.
- Confirm the data structure for natural attacks on entity. `EF.NATURAL_ATTACKS` or similar — a list of dicts or objects with `attack_type`, `damage_dice`, and primary/secondary distinction.
- Confirm feat key: `"multiattack"` — confirm this matches how the feat is stored in `EF.FEATS`.
- Confirm where the secondary attack penalty is applied in `natural_attack_resolver.py`. Likely a constant subtracted from the computed attack bonus for secondary attacks.
- Document whether `natural_attack_resolver.py` calls into `attack_resolver.py` or maintains its own attack roll path — file this in debrief for Batch Q WO3 (WFC).

### Implementation

In `natural_attack_resolver.py`, at the secondary attack penalty computation:

```python
# Multiattack feat: secondary natural attacks at −2 instead of −5 (PHB p.98)
_secondary_penalty = -2 if "multiattack" in entity.get(EF.FEATS, []) else -5
```

Apply `_secondary_penalty` to all secondary natural attacks. Primary attacks unaffected.

### Gate Tests (MA-001 – MA-008)

```python
# MA-001: Creature without Multiattack → secondary natural attacks have −5 attack penalty
# MA-002: Creature with Multiattack feat → secondary natural attacks have −2 penalty (not −5)
# MA-003: Primary natural attack unaffected by Multiattack (full BAB, no secondary penalty)
# MA-004: Multiattack with 3 secondary attacks — all three get −2
# MA-005: Penalty delta verifiable from attack roll: same creature, same target, without vs with Multiattack → 3-point delta
# MA-006: Creature with only 1 natural attack type (no secondary) → Multiattack has no effect on primary
# MA-007: Regression — non-Multiattack creature's primary attack bonus unchanged
# MA-008: Multiattack + INA on same secondary attack → both apply independently (WO2 regression guard)
```

### Session Close Conditions
- [ ] `git add aidm/core/natural_attack_resolver.py tests/test_engine_multiattack_gate.py`
- [ ] `git commit`
- [ ] MA-001–MA-008: 8/8 PASS; zero regressions

---

## WO 2 — WO-ENGINE-IMPROVED-NATURAL-ATTACK-001

**Scope:** `aidm/core/natural_attack_resolver.py`
**Gate file:** `tests/test_engine_improved_natural_attack_gate.py`
**Gate label:** ENGINE-IMPROVED-NATURAL-ATTACK
**Gate count:** 8 tests (INA-001 – INA-008)
**Kernel touch:** NONE
**Source:** PHB p.96

**Commit WO1 first** — both WO1 and WO2 touch `natural_attack_resolver.py`.

### Gap Verification

Coverage map: MISSING. PHB p.96: "Choose one of the creature's natural attack forms. The damage for this natural attack increases by one step on the following list: 1d2, 1d3, 1d4, 1d6, 1d8, 2d6, 3d6, 4d6, 6d6, 8d6, 12d6." Prerequisite: natural weapon, base attack bonus +4. Feat key is per-attack-type.

**Assumptions to Validate on boot:**
- SAI check: search `natural_attack_resolver.py` for `improved_natural_attack`. If die step logic already present, document as SAI.
- Confirm `attack_type` string values from WO1 boot audit. Feat key: `f"improved_natural_attack_{attack_type}"`.
- Confirm where `damage_dice` is stored per natural attack — INA upgrades this at **resolve time** (local variable), NOT permanently in entity. Do NOT mutate `entity[EF.NATURAL_ATTACKS]` — read it, compute upgraded die, use in resolve. Builder.py is locked (Batch S); chargen write is unavailable.
- Confirm die format: `"1d6"`, `"2d6"` etc. (string). Die step table must use exact same format.

### Implementation

In `natural_attack_resolver.py`, when computing damage for a natural attack:

```python
# Improved Natural Attack: damage die size increase by one step (PHB p.96)
_INA_STEP_TABLE = ["1d2", "1d3", "1d4", "1d6", "1d8", "2d6", "3d6", "4d6", "6d6", "8d6", "12d6"]
ina_key = f"improved_natural_attack_{attack.attack_type}"
if ina_key in entity.get(EF.FEATS, []):
    _current_idx = _INA_STEP_TABLE.index(attack.damage_dice) if attack.damage_dice in _INA_STEP_TABLE else -1
    if 0 <= _current_idx < len(_INA_STEP_TABLE) - 1:
        attack_damage_dice = _INA_STEP_TABLE[_current_idx + 1]
    else:
        attack_damage_dice = attack.damage_dice  # already at max or unknown die
else:
    attack_damage_dice = attack.damage_dice
```

Use `attack_damage_dice` (local variable) for damage resolution. Do NOT mutate `attack.damage_dice` on the entity.

### Gate Tests (INA-001 – INA-008)

```python
# INA-001: improved_natural_attack_bite feat + bite attack with 1d6 damage → resolves as 1d8
# INA-002: improved_natural_attack_claw feat + claw attack with 1d4 damage → resolves as 1d6
# INA-003: No INA feat → damage dice unchanged (regression guard)
# INA-004: improved_natural_attack_bite feat, attack is claw (type mismatch) → no upgrade for claw
# INA-005: improved_natural_attack_bite, bite = 1d8 → resolves as 2d6 (step crosses 1d8→2d6 boundary)
# INA-006: improved_natural_attack_bite, bite = 2d6 → resolves as 3d6
# INA-007: Entity damage_dice field unchanged after resolve — no permanent mutation of entity dict
# INA-008: MA-008 regression guard — Multiattack penalty unaffected by INA commit (both apply independently)
```

### Session Close Conditions
- [ ] `git add aidm/core/natural_attack_resolver.py tests/test_engine_improved_natural_attack_gate.py`
- [ ] `git commit`
- [ ] INA-001–INA-008: 8/8 PASS; zero regressions

---

## WO 3 — WO-ENGINE-IMPROVED-TURNING-001

**Scope:** `aidm/core/turn_undead_resolver.py`
**Gate file:** `tests/test_engine_improved_turning_gate.py`
**Gate label:** ENGINE-IMPROVED-TURNING
**Gate count:** 8 tests (ITN-001 – ITN-008)
**Kernel touch:** NONE
**Source:** PHB p.96

**Abbreviation:** ITN (Improved TurNing) — avoids collision with IT (Improved Trip+Sunder, Batch N WO-ENGINE-IMPROVED-TRIP-SUNDER-001).

### Gap Verification

Coverage map: MISSING. PHB p.96: "You turn or rebuke undead as if you were one level higher in the class that grants you the ability." Adds +1 to effective turning level. Prerequisite: ability to turn or rebuke undead.

**Assumptions to Validate on boot:**
- SAI check: search `turn_undead_resolver.py` for `improved_turning` or `+1` near effective level computation. If wired, document as SAI.
- Confirm effective level variable name in `turn_undead_resolver.py`. Likely `_effective_cleric_level`, `_turning_level`, or similar.
- Confirm feat key: `"improved_turning"`.
- Do NOT touch `builder.py` (locked by Batch S). Implement by reading `EF.FEATS` directly in the resolver.
- Paladin turning path: paladin turns undead at cleric_level ÷ 2 (PHB p.44). Confirm whether paladin effective_level also picks up the +1 — document in debrief.

### Implementation

In `turn_undead_resolver.py`, at the effective turning level computation:

```python
# Improved Turning feat: +1 to effective turning level (PHB p.96)
# Adjust _effective_level (or equivalent local variable) before turn check table lookup
if "improved_turning" in entity.get(EF.FEATS, []):
    _effective_level += 1
    events.append(Event(event_id=..., event_type="improved_turning_active",
                        payload={"actor_id": actor_id, "effective_level": _effective_level}))
```

Apply before the turn result table lookup (not after). Paladin turning level: if paladin turns at a derived level, apply +1 to the same derived value.

### Gate Tests (ITN-001 – ITN-008)

```python
# ITN-001: Cleric level 5 + Improved Turning → turns as effective cleric 6 (HD threshold shifts)
# ITN-002: Effective +1 allows turning a higher-HD undead that base level cannot turn
# ITN-003: Cleric without Improved Turning → turns at base level (regression guard)
# ITN-004: improved_turning_active event emitted with correct effective_level payload
# ITN-005: Paladin with Improved Turning → paladin turning level also increases by 1
# ITN-006: Rebuke attempt with Improved Turning → effective level +1 applies to rebuke as well
# ITN-007: Improved Turning + Extra Turning (ETN, Batch S WO3) — TURN_UNDEAD_USES_MAX unaffected
# ITN-008: Regression — Extra Turning uses count unchanged by ITN commit (ETN regression guard)
```

### Session Close Conditions
- [ ] `git add aidm/core/turn_undead_resolver.py tests/test_engine_improved_turning_gate.py`
- [ ] `git commit`
- [ ] ITN-001–ITN-008: 8/8 PASS; zero regressions

---

## WO 4 — WO-ENGINE-SUN-DOMAIN-001

**Scope:** `aidm/core/turn_undead_resolver.py`
**Gate file:** `tests/test_engine_sun_domain_gate.py`
**Gate label:** ENGINE-SUN-DOMAIN
**Gate count:** 8 tests (SD-001 – SD-008)
**Kernel touch:** NONE
**Source:** PHB p.186 (Domains)

**Commit WO3 first** — both WO3 and WO4 touch `turn_undead_resolver.py`.

**BLOCKED RISK (HIGH — two vectors):**
1. If domain storage is not implemented (no `EF.DOMAINS` or equivalent field), WO4 cannot be implemented without infrastructure outside `turn_undead_resolver.py`. File FINDING-ENGINE-DOMAIN-SYSTEM-MISSING-001 and skip WO4.
2. If flagging a turn attempt as "greater turning" requires modifying `play_loop.py` (locked by Batch P), defer WO4 until Batch P closes.
Do NOT attempt to build domain infrastructure or touch `play_loop.py` within this WO.

### Gap Verification

PHB p.186 Sun Domain Granted Power: "Once per day, you can perform a greater turning against undead in place of a regular turning. The greater turning is like a normal turning except that the undead creatures that would be turned are destroyed instead."

Mechanics:
- Uses 1 regular turn attempt slot (`EF.TURN_UNDEAD_USES_REMAINING` decremented)
- Affected undead are destroyed (not just turned) — removed from play
- Available once per day (`EF.GREATER_TURNING_USES_REMAINING`, separate field from `EF.TURN_UNDEAD_USES_MAX`)
- Restored on full rest

**Assumptions to Validate on boot:**
- Domain check: search `turn_undead_resolver.py` and `builder.py` (read-only) for `"sun"`, `"sun_domain"`, `EF.DOMAINS`, or `"greater_turning"`. Document the storage field name.
- If `EF.DOMAINS` stores domain strings as a list: `"sun" in entity.get(EF.DOMAINS, [])` is the check.
- If domain system is absent: BLOCK WO4 immediately (see above).
- `TurnUndeadIntent` schema: confirm whether `is_greater_turning: bool = False` field exists. If it does not, adding it to the schema (not `play_loop.py`) may be sufficient — confirm the call path from `play_loop.py` to `turn_undead_resolver.py`. If `play_loop.py` must be touched to pass the flag, BLOCK WO4 until Batch P closes.
- `EF.GREATER_TURNING_USES_REMAINING`: if this field must be initialized at chargen in `builder.py` (locked), use `entity.get(EF.GREATER_TURNING_USES_REMAINING, 1)` defaulting to 1 for Sun domain clerics — avoids builder.py touch. Confirm this is safe.
- SAI check: search `turn_undead_resolver.py` for `sun_domain` or `greater_turning`.

### Implementation

In `turn_undead_resolver.py`, when processing a turning attempt with `is_greater_turning=True`:

```python
# Sun Domain greater turning: destroy undead that would be turned (PHB p.186)
_is_sun_cleric = "sun" in entity.get(EF.DOMAINS, [])
_greater_uses = entity.get(EF.GREATER_TURNING_USES_REMAINING, 0)
if is_greater_turning and _is_sun_cleric and _greater_uses > 0:
    # Decrement greater turning use
    entity[EF.GREATER_TURNING_USES_REMAINING] = _greater_uses - 1
    # Emit destruction event for each would-be-turned undead
    for _target_id in would_be_turned_ids:
        events.append(Event(event_id=..., event_type="sun_domain_greater_turning_active",
                            payload={"target_id": _target_id, "result": "destroyed"}))
# EF.TURN_UNDEAD_USES_REMAINING is still decremented by the normal turn path
```

Adjust field and variable names to match confirmed boot findings.

### Gate Tests (SD-001 – SD-008)

```python
# SD-001: Sun domain cleric, greater turning attempt → undead that would be turned are destroyed
# SD-002: Sun domain cleric starts day with 1 greater turning use available
# SD-003: After using greater turning → EF.GREATER_TURNING_USES_REMAINING decremented to 0
# SD-004: Greater turning also depletes EF.TURN_UNDEAD_USES_REMAINING by 1 (regular slot consumed)
# SD-005: Cleric WITHOUT Sun domain → no greater turning; regular turn resolves normally
# SD-006: Full rest → EF.GREATER_TURNING_USES_REMAINING restored to 1 for Sun domain cleric
# SD-007: sun_domain_greater_turning_active event emitted for each destroyed undead
# SD-008: Regression — normal turn attempt (is_greater_turning=False) unaffected by this commit
```

### Session Close Conditions
- [ ] `git add aidm/core/turn_undead_resolver.py tests/test_engine_sun_domain_gate.py`
- [ ] `git commit`
- [ ] SD-001–SD-008: 8/8 PASS; zero regressions (OR: WO4 BLOCKED — finding filed, batch closes 3/4 WOs)

---

## File Ownership

| WO | Files touched |
|---|---|
| WO1 | `natural_attack_resolver.py` |
| WO2 | `natural_attack_resolver.py` |
| WO3 | `turn_undead_resolver.py` |
| WO4 | `turn_undead_resolver.py` |

**WO1+WO2 both touch `natural_attack_resolver.py`.** Commit WO1 before WO2.
**WO3+WO4 both touch `turn_undead_resolver.py`.** Commit WO3 before WO4.

**No overlap with Batch P, R, or S.**

---

## Regression Protocol

WO-specific gates first:
```bash
pytest tests/test_engine_multiattack_gate.py -v
pytest tests/test_engine_improved_natural_attack_gate.py -v
pytest tests/test_engine_improved_turning_gate.py -v
pytest tests/test_engine_sun_domain_gate.py -v
```

Full suite after all committed:
```bash
pytest --tb=short -q
```

**Retry cap:** Fix once, re-run once. Record in debrief and stop. Do not loop.

**If WO4 (Sun Domain) is BLOCKED on boot:** file FINDING-ENGINE-DOMAIN-SYSTEM-MISSING-001 (or FINDING-ENGINE-SUN-DOMAIN-PLAYLOOP-001 if blocked by play_loop.py dependency), skip WO4, close batch at 3/4 WOs. Do NOT attempt to build domain infrastructure within this batch.

---

## Debrief Requirements

Three-pass format for all executed WOs.
- WO1 Pass 3: document the existing secondary penalty value found on boot; confirm Multiattack feat key string; note whether `natural_attack_resolver.py` calls into `attack_resolver.py` (document for Batch Q WO3/WFC). State SAI or new work.
- WO2 Pass 3: document the `attack_type` strings confirmed on boot; confirm die step table index boundaries; state whether entity `damage_dice` field was mutated or not (local variable approach verified).
- WO3 Pass 3: document effective level variable name and location (file:line); confirm paladin turning path picks up +1; note ETN regression (TURN_UNDEAD_USES_MAX unchanged).
- WO4 Pass 3: document domain storage field name confirmed on boot; state BLOCKED or ACCEPTED with reason; if BLOCKED, state the FINDING number filed and which block vector triggered (domain absent vs play_loop.py dependency).

Post-debrief: ask builder "Anything else you noticed outside the debrief?" File loose threads before closing.

File to: `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-[NAME]-001.md`
Missing debrief or missing Pass 3 → REJECT.

---

## Session Close Conditions

- [ ] All executed WOs committed with gate run before each
- [ ] MA: 8/8, INA: 8/8, ITN: 8/8, SD: 8/8 (or SD BLOCKED — debrief + finding filed)
- [ ] Zero regressions
- [ ] Chisel kernel updated

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Dispatch issued by Slate. Thunder dispatches to Chisel per ops contract.*

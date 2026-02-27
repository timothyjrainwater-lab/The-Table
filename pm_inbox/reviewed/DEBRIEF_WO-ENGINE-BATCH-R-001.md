# DEBRIEF — ENGINE BATCH R (Dispatch: WO-ENGINE-IMPROVED-EVASION-001 / WO-ENGINE-MOBILITY-001 / WO-ENGINE-AOO-STANDING-PRONE-001 / WO-ENGINE-GREATER-TWF-001)

**Batch:** R
**Commits:** 38f12e0 (WO1 IE) / 0452427 (WO2 MB) / 4083663 (WO4 GTWF)
**Gate result:** IE 8/8, MB 8/8, SP 8/8 (existing), GTWF 8/8 — 32/32 total
**Regressions:** 0 (141 pre-existing failures unchanged; all UI tests)
**Lifecycle:** DISPATCH-READY

---

## Pass 1 — Context Dump

### WO1 — WO-ENGINE-IMPROVED-EVASION-001 (SAI)
**SAI confirmed.** Both Improved Evasion branches already wired in `aidm/core/spell_resolver.py`:

- **Success branch (lines 909-916):** `if _evasion_active and (EF.EVASION or EF.IMPROVED_EVASION): total = 0`
- **Failed save branch (lines 920-927):** `if _armor in ("none","light") and EF.IMPROVED_EVASION: total //= 2`
- **Armor gate:** Both branches gated on `_armor in ("none", "light")`. Medium/heavy suppress IE.

`EF.IMPROVED_EVASION` set at chargen in `aidm/chargen/builder.py`:
- Single-class path: lines 960-967 — `_rogue_level >= 10 or _monk_level >= 9`
- Multiclass path: lines 1193-1200 — same condition

**No production changes to `spell_resolver.py` or `builder.py` required.**

**Gate file:** `tests/test_engine_improved_evasion_gate.py` (new, 159 lines)
**Gate count:** IE-001–IE-008, 8 tests
- IE-001: fail + IE=True, armor unset → 24 (half of 48) ✓
- IE-002: fail + IE=True, cone_of_cold 10d6 → 30 ✓
- IE-003: succeed + IE=True → 0 ✓
- IE-004: fail + Evasion only (no IE) → 48 (full) ✓
- IE-005: fail + no flags → 48 ✓
- IE-006: fail + IE=True + medium armor → 48 (armor suppresses) ✓
- IE-007: chargen boundary — rogue 9: no IE; rogue 10: IE=True ✓
- IE-008: fail + IE=True + light armor → 24 (light OK) ✓

---

### WO2 — WO-ENGINE-MOBILITY-001 (SAI + minor cleanup)
**SAI confirmed.** Wiring already live in two files:

- `aidm/core/feat_resolver.py` lines 264-268: `FeatID.MOBILITY = "mobility"` → +4 for `movement_out`/`mounted_movement_out` triggers
- `aidm/core/aoo.py` lines 615-624: deepcopy path applies modifier to provoker's AC in a temporary WorldState before `resolve_attack()` is called

**Production change (cleanup only):** Removed stale WO-034 TODO comment at `aoo.py` former lines 609-613. Replaced with `# WO-ENGINE-MOBILITY-001: Modify provoker's AC in world_state copy for this AoO only`. Deepcopy block (former 615-624) unchanged.

Before:
```python
        # TODO WO-034: Apply feat_ac_modifier to AoO attack
        # Current limitation: attack_resolver doesn't accept context-specific AC modifiers.
        # For now, Mobility +4 AC is computed but not applied to the attack.
        # This requires refactoring attack_resolver to accept an optional AC modifier parameter.
        # Tracked in WO-034 acceptance criteria.
        # WORKAROUND: Temporarily modify provoker's AC in world_state copy
        if feat_ac_modifier != 0:
```
After:
```python
        # WO-ENGINE-MOBILITY-001: Modify provoker's AC in world_state copy for this AoO only
        if feat_ac_modifier != 0:
```

**Gate file:** `tests/test_engine_mobility_gate.py` (new, 231 lines)
**Gate count:** MB-001–MB-008, 8 tests
- MB-001: `get_ac_modifier(mobility feat, movement_out context)` → 4 ✓
- MB-002: `get_ac_modifier(no feat, movement_out)` → 0 ✓
- MB-003: `get_ac_modifier(mobility feat, spellcasting)` → 0 (non-movement) ✓
- MB-004: e2e — AC=10, attack_bonus=8, roll=3, Mobility present → MISS (11 < 14) ✓
- MB-005: e2e — same setup, no Mobility → HIT (11 >= 10) ✓
- MB-006: `get_ac_modifier(mobility feat, stand_from_prone)` → 0 ✓
- MB-007: two triggers in sequence, both MISS with Mobility (deepcopy per-AoO) ✓
- MB-008: `get_ac_modifier(mobility feat, mounted_movement_out)` → 4 ✓

---

### WO3 — WO-ENGINE-AOO-STANDING-PRONE-001 (Full SAI)
**Full SAI. Zero production changes.**

`check_stand_from_prone_aoo()` fully implemented at `aoo.py:709-817`:
- Checks `"prone" in EF.CONDITIONS`
- Finds adjacent enemies
- Flat-footed reactor guard at **`aoo.py:779`**: `if "flat_footed" in _reactor_conditions: continue`

Existing gate file: `tests/test_engine_aoo_stand_from_prone_001_gate.py` (Batch I)
SP-001–SP-008: 8/8 PASS (confirmed this session)

**FINDING-CE-STANDING-AOO-001: CLOSED.** Flat-footed reactor guard confirmed at `aoo.py:779`.

---

### WO4 — WO-ENGINE-GREATER-TWF-001 (New work)
**New work.** GTWF was absent from `full_attack_resolver.py`. Confirmed by searching for `"Greater Two-Weapon"` — no match.

**Feat string confirmed:** `"Greater Two-Weapon Fighting"` (Title Case). Verified by reading line 902: `if "Improved Two-Weapon Fighting" in feats`. GTWF follows same convention.

**Insertion point:** `aidm/core/full_attack_resolver.py`, after ITWF block (former line 952, after `attacks_executed += 1`). New block inserts before `# Apply accumulated damage to HP` comment.

Before (line 952 → 954):
```python
            current_hp -= itwf_damage
            attacks_executed += 1

    # Apply accumulated damage to HP
```

After (GTWF block inserted):
```python
            current_hp -= itwf_damage
            attacks_executed += 1

        # Greater Two-Weapon Fighting: third off-hand attack at BAB-10+off_penalty
        # PHB p.96: GTWF grants a third off-hand attack (same chain as ITWF at -5, GTWF at -10)
        # Feat string: "Greater Two-Weapon Fighting" (Title Case — matches TWF/ITWF convention)
        if "Greater Two-Weapon Fighting" in feats and current_hp > 0:
            gtwf_bab = intent.base_attack_bonus - 10 + off_penalty
            gtwf_adjusted = (gtwf_bab + attacker_modifiers.attack_modifier + ...)
            gtwf_events, current_event_id, gtwf_damage = resolve_single_attack_with_critical(...)
            ...
            attacks_executed += 1

    # Apply accumulated damage to HP
```

Variables confirmed available at insertion point:
- `feats`: defined at line 901 (inside `if is_twf` block, unconditional)
- `off_penalty`: defined at line 669-671 (outside TWF block)
- `off_str_mod`: defined at line 857 (inside `if is_twf` block)
- `current_hp`: running counter from all previous attacks

**Gate file:** `tests/test_engine_greater_twf_gate.py` (new, 312 lines)
**Gate count:** GTWF-001–GTWF-008, 8 tests
- GTWF-001: [TWF+ITWF+GTWF], BAB=11 → 6 attack_rolls ✓
- GTWF-002: [TWF+ITWF only] → 5 attack_rolls (regression guard) ✓
- GTWF-003: [TWF only] → 4 attack_rolls (regression guard) ✓
- GTWF-004: GTWF fires even when target HP=9999 (target survives all hits) → 6 attacks ✓
- GTWF-005: STR_MOD=4, 3rd off-hand uses off_str_mod=2 (half-STR) → 6 attacks + damage_roll events ✓
- GTWF-006: GTWF vs ITWF delta = exactly 1 extra attack ✓
- GTWF-007: 6 attack_roll events in non-decreasing timestamp order ✓
- GTWF-008: regression — ITWF (no GTWF) still gives 5 attacks ✓

---

## Pass 2 — PM Summary (≤100 words)

Batch R: 4 WOs, 32 gate tests, 0 regressions. WO1 (IE) and WO3 (SP) full SAI — both
already wired; gate tests confirm behaviour. WO2 (MB) SAI + cleanup: removed stale
WO-034 TODO comment from aoo.py, gate tests validate deepcopy AC path end-to-end.
WO4 (GTWF) new work: inserted third off-hand attack block in full_attack_resolver.py after
ITWF block; feat string "Greater Two-Weapon Fighting" (Title Case); BAB-10+off_penalty;
half-STR via off_str_mod. FINDING-CE-STANDING-AOO-001 CLOSED. Commits 38f12e0 / 0452427 / 4083663.

---

## Pass 3 — Retrospective

**WO1 (IE) — SAI confirmation details:**
- `spell_resolver.py:909-916`: success branch — `EF.EVASION or EF.IMPROVED_EVASION` both trigger 0 damage
- `spell_resolver.py:920-927`: fail branch — `EF.IMPROVED_EVASION` + armor gate → `total //= 2`
- `EF.IMPROVED_EVASION` set at chargen: single path line 966, multiclass path line 1199
- No event emission for IE (spell_resolver just modifies `total`). IE-007 tests chargen boundary rather than event payload — consistent with existing EV gate test pattern.

**WO2 (MB) — deepcopy path documentation:**
- `FeatID.MOBILITY = "mobility"` (lowercase) — stored as string in `EF.FEATS`
- Mobility +4 applies ONLY to `movement_out` and `mounted_movement_out` triggers (NOT `stand_from_prone`, `spellcasting`, `ranged_attack`)
- MB-006 confirms no +4 for stand_from_prone; MB-008 confirms mounted_movement_out
- Deepcopy correctly creates a fresh WorldState per-AoO (MB-007 confirms two sequential AoOs both get +4)

**WO3 (SP) — SAI + finding close:**
- `check_stand_from_prone_aoo()` at `aoo.py:709-817` — fully implemented, called from `play_loop.py:3530`
- Flat-footed guard at `aoo.py:779` — `if "flat_footed" in _reactor_conditions: continue`
- **FINDING-CE-STANDING-AOO-001: CLOSED.** Flat-footed guard present and confirmed.

**WO4 (GTWF) — feat string and BAB confirmation:**
- Feat string: `"Greater Two-Weapon Fighting"` (Title Case confirmed from line 902 boot read)
- BAB offset: `-10` vs ITWF `-5` — correct per PHB p.96
- `current_hp > 0` guard: present (GTWF-004 confirms with HP=9999 target)
- GTWF-005 confirms half-STR path fires for 3rd off-hand (5 damage_roll events with str_mod=4)

**Out-of-scope findings noticed:**

| ID | Severity | Status | Description |
|----|----------|--------|-------------|
| FINDING-ENGINE-GTWF-PREREQ-CHAIN-001 | LOW | OPEN | PHB requires GTWF prerequisites (Int 15, Dex 17, TWF, ITWF, BAB+11). Engine does not enforce feat prerequisites at resolution time — only at chargen. Consistent with all other feat prereq handling. |
| FINDING-ENGINE-MOBILITY-DODGE-CHAIN-001 | LOW | OPEN | PHB p.97: Mobility requires Dodge as a prerequisite. `FeatID.DODGE` check exists in `get_ac_modifier()` (lines 255-260) but is separate from Mobility. No validation that Dodge is present when Mobility fires. Consistent with no-prereq-enforcement policy. |

**Kernel touches:**
- This WO touches **KERNEL-04 (Intent Semantics)** — GTWF expands the full-attack intent's off-hand semantics to include a 3rd attack. The `FullAttackIntent` dataclass is unchanged; the resolver now derives three off-hand attacks from the same intent when the feat chain warrants it.
- No KERNEL-01/02/03/06 touches from this batch.

---

## Radar

| Finding ID | Severity | Status |
|-----------|----------|--------|
| FINDING-CE-STANDING-AOO-001 | — | **CLOSED** (flat-footed guard at aoo.py:779) |
| FINDING-ENGINE-GTWF-PREREQ-CHAIN-001 | LOW | OPEN |
| FINDING-ENGINE-MOBILITY-DODGE-CHAIN-001 | LOW | OPEN |

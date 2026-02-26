# DEBRIEF -- WO-ENGINE-COMBAT-EXPERTISE-001
**Verdict:** PASS [8/8]
**Gate:** ENGINE-COMBAT-EXPERTISE
**Date:** 2026-02-26

## Pass 1 -- Per-File Breakdown

### aidm/schemas/attack.py
- Added  to  after .
- Added validation: .

### aidm/schemas/entity_fields.py
- Added  in new labeled block before Evasion block.
- Docstring: int, penalty==1 -> +1 AC; penalty 2-5 -> +2 AC. Cleared per-turn.

### aidm/core/attack_resolver.py
- Insertion 1 (attack penalty):  appended to .
- Insertion 2 (write attacker AC bonus): After computing total, CE bonus written to attacker entity.
  
- Insertion 3 (read target AC bonus):  added to target_ac formula.

### aidm/core/play_loop.py
- Added per-turn reset after WO-ENGINE-DEFEND-001 clear block.
- Clears COMBAT_EXPERTISE_BONUS to 0 via deepcopy+WorldState rebuild if non-zero.

### tests/test_engine_combat_expertise_gate.py (new)
- 8 tests: CEX-001 through CEX-008.
- Uses _FixedRNG (d20=15), _make_ws, _attacker, _target, _weapon helpers.

## Pass 2 -- PM Summary

Combat Expertise (PHB p.92) mirrors Power Attack: declare 1-5 penalty on 
in . The penalty subtracts from  in attack_resolver.py
and writes  (+1 for penalty==1, +2 for penalty 2-5) to the attacker entity.
When any entity is targeted, its  raises . Cleared per-turn in
play_loop.py. 4 files modified, 1 new test file, 8/8 gate pass, 0 regressions introduced.

## Pass 3 -- Retrospective

- AC formula is non-linear (1:1 only for penalty==1; capped at +2 for penalty 2-5): matches PHB p.92.
- CE bonus written to attacker entity, read from target entity on incoming attacks: consistent with
  fight-defensively and inspire-courage patterns already in the codebase.
- No INT 13 prereq check at resolution time (chargen-only, per spec).
- NonlethalAttackIntent has no combat_expertise_penalty field; CE not applied to nonlethal path.
- Pre-existing failures confirmed pre-existing (aoo_kernel, boundary, parser_audit, pm_inbox_hygiene).

## Radar

| Gate | Result |
|------|--------|
| CEX-001: penalty=3 reduces total by 3 | PASS |
| CEX-002: penalty=3 writes COMBAT_EXPERTISE_BONUS=2 | PASS |
| CEX-003: penalty=1 writes COMBAT_EXPERTISE_BONUS=1 | PASS |
| CEX-004: penalty=0 no change, no bonus | PASS |
| CEX-005: penalty=5 reduces total by 5, bonus=2 cap | PASS |
| CEX-006: no CE declared, total unchanged | PASS |
| CEX-007: target with CE bonus=2 raises target_ac by 2 | PASS |
| CEX-008: power_attack regression clean | PASS |

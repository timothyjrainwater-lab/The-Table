# DEBRIEF — WO-ENGINE-WEAPON-FINESSE-001

**Verdict:** PASS [8/8]
**Gate:** ENGINE-WEAPON-FINESSE
**Date:** 2026-02-26

## Pass 1 — Per-File Breakdown

**`aidm/core/attack_resolver.py`**
`resolve_attack()` and `resolve_nonlethal_attack()` both received the `_finesse_delta` block after `_favored_enemy_bonus`. Preflight confirmed: `intent.attack_bonus` is constructed as **BAB + STR_MOD** (confirmed from `intent_bridge.py` line ~490). Delta approach `dex_mod - str_mod` is therefore correct — when finesse applies, the STR component is replaced by DEX by adding the difference. Applied identically in both attack paths.

**Latent bug fixed (prerequisite):** `Weapon.enhancement_bonus` field was referenced in existing attack_resolver.py code but was missing from the `Weapon` dataclass definition in `aidm/schemas/attack.py`. Added `enhancement_bonus: int = 0` as a prerequisite to avoid AttributeError. This was a latent bug caught during preflight inspection — not introduced by this WO.

**`tests/test_engine_weapon_finesse_gate.py`** — NEW
WF-001 through WF-008 all pass. Coverage: DEX > STR positive delta (WF-001); mandatory substitution even when DEX < STR / negative delta (WF-002); one-handed weapon no finesse (WF-003); no feat no bonus (WF-004); damage still STR (WF-005); equal stats zero delta (WF-006); iterative attacks all finessed (WF-007); regression unaffected (WF-008).

## Pass 2 — PM Summary (≤100 words)

Weapon Finesse fully wired. Attackers with `weapon_finesse` feat and a light weapon now substitute DEX for STR on attack rolls via `_finesse_delta = dex_mod - str_mod` added to `attack_bonus_with_conditions` in both `resolve_attack()` and `resolve_nonlethal_attack()`. Mandatory substitution (PHB p.102) — delta is applied unconditionally when conditions met, even if negative. Damage unaffected. Critical preflight finding: intent.attack_bonus includes STR already (BAB+STR), making the delta formula correct. Latent bug fixed: Weapon.enhancement_bonus missing from dataclass. 8/8 gate.

## Pass 3 — Retrospective

**Drift caught:**
- Latent bug: `Weapon.enhancement_bonus` field referenced in attack resolver but absent from dataclass. Fixed as prerequisite. This is a good example of preflight inspection catching pre-existing issues before they surface as test failures.

**Patterns:** The spec's preflight step ("verify whether `intent.attack_bonus` is BAB-only or BAB+STR") was essential — getting this wrong would have double-applied or missed the STR correction. The conditional check in the spec was correct.

**Open findings:**
| ID | Severity | Description |
|----|----------|-------------|
| FINDING-ENGINE-FINESSE-TOUCH-001 | LOW | Touch attack finesse deferred per spec — melee touch attacks via spell_resolver not covered |
| FINDING-ENGINE-FINESSE-RAPIER-001 | LOW | Rapier/whip/spiked chain eligible weapons deferred — requires weapon-name lookup WO |

## Radar

- ENGINE-WEAPON-FINESSE: 8/8 PASS
- intent.attack_bonus confirmed: BAB + STR_MOD (intent_bridge.py ~490)
- Weapon.is_light confirmed as derived property: attack.py:107
- Latent bug fixed: Weapon.enhancement_bonus added to dataclass
- Zero new failures in full regression

# CP-18 Gate-Violation Sentinels (STOP Conditions)
**Date:** 2026-02-08
**Purpose:** Quick rejection/stop list to prevent accidental capability gate crossing during CP-18.

---

## 1) Gates relevant to CP-18

### G-T3C — Relational Conditions (CLOSED)
**Forbidden:** Any bidirectional grapple representation (attacker <-> defender relationship).

**Sentinel checks:**
- If you feel compelled to add `grappling`, `grapple_target`, `grappled_by`, or any attacker-side grapple state → **STOP**.
- If a condition payload contains `attacker_id` or references another entity → **STOP**.

**Allowed:** Grapple-lite = defender-only Grappled condition (no references).

---

### G-T2A — Permanent Stat Mutation (CLOSED)
**Forbidden:** any base ability score modifications, permanent bonuses/penalties.

**Sentinel checks:**
- Any attempt to modify STR/DEX/CON/INT/WIS/CHA base values → **STOP**.
- Any attempt to encode "fatigue" or "injury" as permanent stat changes → **STOP**.

---

### G-T3A — Entity Forking (CLOSED)
**Forbidden:** creating new entities (items, dropped weapons, "object entities") to represent disarm/sunder.

**Sentinel checks:**
- "Weapon on ground" must be represented as a *narrative/event* only, not as an entity.
- If you want to `add_entity` for dropped gear → **STOP**.

---

## 2) CP-18-specific gate pressure points

### Item-state kernel absent
**Forbidden:** persistent item HP, hardness, broken states, ownership transfer.

**Sentinel checks:**
- Sunder must not decrement item HP because item HP does not exist.
- Disarm must not change inventory/ownership (unless such state already exists and is explicitly used in design — default is event-only).

---

### Feat system absent
**Forbidden:** Improved Trip/Bull Rush/Overrun/etc. removing AoOs or adding free attacks.

**Sentinel checks:**
- If you're adding exceptions like "does not provoke AoO" → **STOP**.

---

## 3) Allowed new entity fields (ONLY THESE)

Per packet:
- `EF.SIZE_CATEGORY`
- `EF.STABILITY_BONUS`
- `EF.GRAPPLE_SIZE_MODIFIER`

**Sentinel checks:**
- If you need another field → **STOP** and escalate.

# AD-004: Mechanical Evidence Gate

**Status:** APPROVED
**Date:** 2026-02-12
**Authority:** PM (Opus) + PO (Thunder) + External Systems Auditor
**Source:** External Auditor advisory on source-of-truth hardening and 5e drift containment

---

## Decision

**No mechanical rule may enter Box unless it is traceable to a local corpus reference.**

This is a binding extension of AD-001 (Authority Resolution Protocol). AD-001 governs where *facts* come from. AD-004 governs where *rules* come from. Both must be locally grounded.

---

## The Problem

The current mechanical correctness enforcement model is **reactive**:

1. Contamination audits find edition bleed after code is written
2. Golden tests catch regressions after they exist
3. Citation discipline depends on individual agents remembering

Evidence:
- **WO-FIX-001:** 5e concentration auto-displacement was in the codebase for multiple development cycles before the audit found it
- **WO-FIX-002:** Critical hits were missing from `attack_resolver.py` — no structural check prevented shipping a resolver without complete PHB coverage

As Phase 2 expands the surface area (feats, spells, skills, conditions), the combinatorial space becomes too large for manual auditing. This is the last low-cost moment to enforce a hard evidence discipline.

---

## The Local Corpus

The PO's local Vault (`F:\DnD-3.5\Vault`) provides:

| Asset | Location | Status |
|---|---|---|
| PHB OCR'd pages (322 pages) | `Vault/00-System/Staging/681f92bc94ff/pages/` | Available |
| DMG staged | `Vault/00-System/Staging/fed77f68501d/` | Available |
| MM staged | `Vault/00-System/Staging/e390dfd9143f/` | Available |
| 18 source books total | `Vault/00-System/Staging/*/pages/` | Available |
| Library index (650 items) | `Vault/00-System/library.json` | Available |
| Obsidian rules notes | `Vault/00-System/` + root-level `Rule — *.md` | Available |
| Citation policy | `Vault/00-System/citation_policy.md` | Available |
| Metadata indices | `Vault/00-System/Indexes/` | Available |

This corpus is sufficient to implement the Evidence Gate without additional ingestion.

---

## Three Enforcement Layers

### Layer 1: Evidence-Gated Test Docstrings (Immediate, Binding)

Every mechanical test must include a local corpus pointer in its docstring:

```python
def test_critical_hit_confirmation():
    """Confirmed critical multiplies damage (PHB p.140).

    Evidence: Vault/00-System/Staging/681f92bc94ff/pages/0140.txt
    Rule: "If the confirmation roll also results in a hit against the
    target's AC, your original attack is a critical hit."
    """
```

**Format:**
- `Evidence:` line with staging path or Obsidian note path
- `Rule:` line with the specific quoted text from the source
- PHB page citation in docstring first line (existing convention)

**Enforcement:** A test without an `Evidence:` pointer is incomplete and blocks merge for any mechanics-affecting PR.

### Layer 2: Subsystem Evidence Maps (Immediate, Binding)

For each implemented resolver, a structured evidence table in `docs/evidence/`:

```markdown
# Evidence Map: Attack Resolution

| Mechanic | PHB Page | Vault Path | Tests | Gaps |
|---|---|---|---|---|
| Attack roll = d20 + bonus vs AC | p.140 | 681f92bc94ff/pages/0140.txt | test_attack_hits_when_roll_meets_or_exceeds_ac | None |
| Natural 20 auto-hit + threat | p.140 | 681f92bc94ff/pages/0140.txt | test_natural_20_always_hits | None |
| Natural 1 auto-miss | p.140 | 681f92bc94ff/pages/0140.txt | test_natural_1_always_misses | None |
| Critical confirmation | p.140 | 681f92bc94ff/pages/0140.txt | test_single_attack_critical_confirmation | None |
| Critical damage multiplication | p.140 | 681f92bc94ff/pages/0140.txt | test_single_attack_critical_damage_multiplied | None |
| Expanded threat range | p.140 | 681f92bc94ff/pages/0140.txt | test_single_attack_expanded_threat_range_19_20 | None |
| Threat doesn't auto-hit | p.140 | 681f92bc94ff/pages/0140.txt | test_single_attack_threat_in_expanded_range_must_still_meet_ac | None |
```

Every row must have:
- A specific page reference
- A Vault staging path
- At least one test covering the mechanic
- An explicit `None` or description in the Gaps column

### Layer 3: Fail-Closed Rule Resolution (Future, Optional)

If a rule lookup fails local evidence resolution, the system returns `NEEDS_EVIDENCE` — not "best guess," not model recall. This transforms the system from recall-based to corpus-based.

This layer is deferred to Phase 2 integration. It is documented here for completeness but is NOT required for current execution.

---

## Scope Boundaries (Binding)

### The Evidence Gate covers:
- Attack resolution mechanics (hit, miss, critical, damage)
- AC computation (base, condition modifiers, cover, touch, flat-footed)
- Spell resolution mechanics (saving throws, spell resistance, concentration)
- Condition application and effects
- Movement and positioning rules
- Feat mechanical effects
- Skill check mechanics
- Duration and expiration rules
- Damage reduction, energy resistance
- Combat maneuvers (grapple, trip, bull rush, etc.)

### The Evidence Gate does NOT cover:
- Narrative text, flavor descriptions, or atmospheric content
- NPC personality or dialogue
- Scene generation templates (covered by AD-003's Policy Default Library)
- Spark's language/framing output
- UI/UX decisions

---

## Vault Source ID Reference

| Source ID | Book | Priority |
|---|---|---|
| `681f92bc94ff` | Player's Handbook | 1 (Primary) |
| `fed77f68501d` | Dungeon Master's Guide | 2 |
| `e390dfd9143f` | Monster Manual | 3 |

All other source IDs are supplementary. Core rulebook source IDs are the primary evidence authority.

---

## Relationship to AD-001, AD-002, AD-003

### AD-001 (Authority Resolution Protocol)
AD-001 governs where *facts* come from (scene data, policy defaults, player choice — never Spark). AD-004 extends this principle to *rules*: mechanical rules must come from local corpus, not model recall.

### AD-003 (Self-Sufficiency Resolution Policy)
AD-003 specifies that the Policy Default Library must be RAW-grounded. AD-004 provides the enforcement mechanism: every policy default must trace to a Vault evidence path.

---

## Concrete Next Steps

1. **WO-HARDEN-001:** Build subsystem evidence maps for all currently implemented mechanics
2. Add `Evidence:` pointers to existing critical test docstrings (attack, spell, duration, concentration)
3. Add CI check: mechanical test files must contain `Evidence:` lines (can start as a warning, graduate to blocking)
4. Continue WO-FIX-003 and Phase 2 dispatch with evidence-gated golden tests

---

*This decision was prompted by the External Systems Auditor identifying that reactive contamination detection is insufficient as surface area grows. The local Vault corpus (322 OCR'd PHB pages, 18 source books, Obsidian rules notes) provides the enforcement authority. No new architecture required — only governance enforcement using existing assets.*

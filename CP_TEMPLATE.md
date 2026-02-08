<!--
CP TEMPLATE — Standard format for Completion Packet decision documents.

Copy this file to docs/CP{XX}_{NAME}_DECISIONS.md and fill in the sections.
Do not skip sections — write "N/A" if a section doesn't apply.

LAST UPDATED: Post-Audit Corrections (594 tests)
-->

# CP-{XX}: {Feature Name} — Design Decisions

**Status:** {IN PROGRESS | COMPLETE}
**Date:** {YYYY-MM-DD}
**Depends on:** {List of prerequisite CPs, or "None"}
**Blocked by gates:** {List of capability gates, or "None — G-T1 OPEN"}

---

## 1. Scope

### In Scope
- {Bullet list of what this CP implements}
- {Be specific — "add X function to Y module" not "handle X"}

### Out of Scope
- {What this CP explicitly does NOT do}
- {Deferred items go here with the CP/SKR that will handle them}

### Acceptance Criteria
- [ ] All new tests pass
- [ ] All 594+ existing tests still pass
- [ ] Full suite runs in under 2 seconds
- [ ] {Feature-specific acceptance criteria}

---

## 2. Schema Design

### New Data Contracts
```python
# File: aidm/schemas/{concept}.py

@dataclass
class {NewType}:
    """Description. Reference: PHB p.XXX"""
    field_name: type  # Description
```

### New Entity Fields (if any)
```python
# Added to aidm/schemas/entity_fields.py

class _EntityFields:
    # --- {Category} (CP-{XX}) ---
    NEW_FIELD = "new_field"
```

### Event Types
| Event Type | Payload Fields | Emitted By |
|------------|---------------|------------|
| `{event_name}` | `{field}: {type}` | `{module}.py` |

---

## 3. Implementation Plan

### Files to Create
| File | Purpose |
|------|---------|
| `aidm/schemas/{concept}.py` | Data contracts |
| `aidm/core/{concept}_resolver.py` | Core logic |
| `tests/test_{concept}.py` | Test coverage |

### Files to Modify
| File | Change |
|------|--------|
| `aidm/core/{existing}.py` | {What changes and why} |

### RNG Stream
- **Stream used:** `"{stream_name}"` (or "None — deterministic only")
- **Consumption order:** {Document if using RNG}

---

## 4. D&D 3.5e Rules Reference

### Primary Sources
- PHB p.{XXX}: {Rule description}
- DMG p.{XXX}: {Rule description}

### Rules Implemented
- {Specific rule with PHB/DMG citation}

### Rules Deferred
- {Rule that exists in 3.5e but is out of scope for this CP}

### 5e Contamination Check
- [ ] No advantage/disadvantage mechanics used
- [ ] No short rest/long rest terminology
- [ ] No proficiency bonus (uses BAB + feat bonuses)
- [ ] Damage types use 3.5e names (electricity, not electric)
- [ ] Spell slots used for 0-level spells (not at-will cantrips)

---

## 5. Test Strategy

### Tier-1 Tests (Blocking)
| Test Name | Validates |
|-----------|-----------|
| `test_{basic_functionality}` | Core correctness |
| `test_{edge_case}` | Boundary condition |

### Tier-2 Tests (Integration)
| Test Name | Validates |
|-----------|-----------|
| `test_{integration_scenario}` | End-to-end workflow |

### PBHA Tests (Determinism — if applicable)
| Test Name | Validates |
|-----------|-----------|
| `test_pbha_{feature}_10x_replay` | 10 runs produce identical results |

---

## 6. Pitfalls & Decisions

### Decision 1: {Decision Title}
- **Options considered:** {A, B, C}
- **Chosen:** {X}
- **Rationale:** {Why}
- **Trade-offs:** {What we lose}

### Pitfalls Discovered
- {Any new coding pitfall discovered during implementation}
- {Add to AGENT_DEVELOPMENT_GUIDELINES.md if broadly applicable}

---

## 7. Completion Checklist

Before marking this CP as COMPLETE:

- [ ] All new tests pass
- [ ] All 594+ existing tests still pass (zero regressions)
- [ ] Full test suite runs in under 2 seconds
- [ ] New entity fields added to `entity_fields.py` (if any)
- [ ] `PROJECT_STATE_DIGEST.md` updated:
  - [ ] Test count updated (old → new)
  - [ ] Module inventory updated
  - [ ] Test file inventory updated
  - [ ] CP history entry added
  - [ ] Locked systems updated (if applicable)
- [ ] `AGENT_DEVELOPMENT_GUIDELINES.md` updated (if new patterns/pitfalls found)
- [ ] `KNOWN_TECH_DEBT.md` updated (if new deferred items identified)
- [ ] No bare string literals for entity fields (used `EF.*` constants)
- [ ] No `set()` objects in state
- [ ] No floating point in deterministic paths
- [ ] All `json.dumps()` calls use `sort_keys=True`
- [ ] RNG streams not cross-contaminated
- [ ] Resolver functions return events only (no state mutation)

---

## 8. Post-Completion Notes

### What Went Well
- {Lessons for future CPs}

### What Was Harder Than Expected
- {Challenges encountered}

### Follow-Up Items
- {Items that should be addressed in future CPs}
- {Add to KNOWN_TECH_DEBT.md if deferred}

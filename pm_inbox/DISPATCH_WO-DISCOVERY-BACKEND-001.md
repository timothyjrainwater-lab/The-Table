# Instruction Packet: Discovery Log Agent

**Work Order:** WO-DISCOVERY-BACKEND-001 (Discovery Log Backend)
**Dispatched By:** PM (Opus)
**Date:** 2026-02-13
**Priority:** 2 (Enriches MVP — bestiary progressive revelation)
**Deliverable Type:** Code implementation + tests

---

## READ FIRST

The Discovery Log contract is complete (764 lines at `docs/contracts/DISCOVERY_LOG.md`). The knowledge mask schema exists with 35 enforcement tests. Four-tier progression (HEARD_OF → SEEN → FOUGHT → STUDIED) is already defined and tested.

What's missing: the backend state machine that:
1. Receives knowledge events (encounter, skill check, NPC conversation)
2. Applies them to the per-player discovery mask
3. Persists discovery state
4. Provides queries for the notebook bestiary section

---

## YOUR TASK

### Deliverable 1: Discovery State Machine

**File:** `aidm/lens/discovery_log.py` (NEW)

Implement a DiscoveryLog that manages per-player creature knowledge:

1. `DiscoveryLog` class:
   - `record_encounter(player_id: str, creature_type: str, knowledge_level: KnowledgeLevel)` — record that a player gained knowledge
   - `get_knowledge(player_id: str, creature_type: str) -> KnowledgeLevel` — query current knowledge level
   - `get_all_known(player_id: str) -> dict[str, KnowledgeLevel]` — all creatures this player knows about
   - `get_visible_fields(player_id: str, creature_type: str) -> set[str]` — which fields are visible at current knowledge level

2. Knowledge level transitions:
   - UNKNOWN → HEARD_OF: NPC mentions creature, rumor, lore book
   - HEARD_OF → SEEN: Player sees creature (enter combat, spot check)
   - SEEN → FOUGHT: Player engages in combat with creature
   - FOUGHT → STUDIED: Successful knowledge check, multiple encounters, or special ability
   - Transitions are ONE-WAY — knowledge never decreases
   - Skip levels allowed (first encounter can go UNKNOWN → FOUGHT if combat starts without prior knowledge)

3. Field gating by knowledge level (read the contract for exact mappings, but approximately):
   - HEARD_OF: name, general type (humanoid, beast, etc.)
   - SEEN: name, type, size, general appearance
   - FOUGHT: name, type, size, appearance, observed AC range, observed damage range, observed abilities
   - STUDIED: full stat block, resistances, vulnerabilities, special abilities, lore text

4. Serialization: `to_dict()` / `from_dict()` for persistence (JSONL format, append-only)

### Deliverable 2: Knowledge Event Integration

**File:** `aidm/lens/discovery_log.py` (same file)

Define knowledge event types that trigger discovery updates:

```python
class KnowledgeEvent:
    """An event that reveals creature information to a player."""
    player_id: str
    creature_type: str
    source: KnowledgeSource  # ENCOUNTER, SKILL_CHECK, NPC_CONVERSATION, SPECIAL_ABILITY
    resulting_level: KnowledgeLevel
    timestamp: str  # injected, not generated
```

The DiscoveryLog processes KnowledgeEvents to update its state.

### Deliverable 3: Tests

**File:** `tests/test_discovery_log.py` (NEW)

Tests:
1. New player has no knowledge (UNKNOWN for all creatures)
2. Recording HEARD_OF → query returns HEARD_OF
3. Recording FOUGHT after HEARD_OF → level upgrades to FOUGHT
4. Recording HEARD_OF after FOUGHT → level stays at FOUGHT (no downgrade)
5. Skip level: UNKNOWN → FOUGHT is valid
6. Field gating: HEARD_OF shows only name + type
7. Field gating: STUDIED shows full stat block
8. Multiple players have independent knowledge states
9. Serialization round-trip preserves all state
10. get_all_known returns all creatures for a player
11. Knowledge events correctly trigger level transitions

---

## WHAT EXISTS (DO NOT MODIFY)

| Component | Location | Status |
|-----------|----------|--------|
| Discovery Log contract | `docs/contracts/DISCOVERY_LOG.md` | Canonical spec |
| Knowledge mask schema | `docs/schemas/knowledge_mask.schema.json` | JSON schema |
| Knowledge mask tests | 35 existing tests | Do not break |
| Existing KnowledgeLevel enum | Check `aidm/schemas/` for existing definition | Use if exists, create if not |

## REFERENCES

| Priority | File | What It Contains |
|----------|------|-----------------|
| 1 | `docs/contracts/DISCOVERY_LOG.md` | Full contract — field gating tables, event types, transition rules |
| 1 | `docs/schemas/knowledge_mask.schema.json` | JSON schema for knowledge masks |
| 2 | `aidm/schemas/immersion.py` | May contain related schemas |
| 3 | `docs/specs/UX_VISION_PHYSICAL_TABLE.md` | How bestiary displays in notebook |

## STOP CONDITIONS

- If KnowledgeLevel enum already exists in a different module, use it (do not create a duplicate).
- If the Discovery Log contract specifies behavior that conflicts with existing knowledge mask tests, follow the contract and flag the conflict in your completion report.
- If the contract is missing critical field-gating tables, implement a reasonable default and flag as "needs PO clarification."

## DELIVERY

- New files: `aidm/lens/discovery_log.py`, `tests/test_discovery_log.py`
- Full test suite run at end — report total pass/fail count
- Completion report: `pm_inbox/AGENT_WO-DISCOVERY-BACKEND-001_completion.md`

## RULES

- This is a Lens component — no imports from `aidm/core/` internal resolvers
- May import from `aidm/schemas/` for data types
- Knowledge state is append-only (new events only add knowledge, never remove)
- All dataclasses frozen
- Timestamp fields are injected (BL-018), not generated with `datetime.now()`
- Follow existing code style and test patterns

---

END OF INSTRUCTION PACKET

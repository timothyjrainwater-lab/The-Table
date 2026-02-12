# Template Family Specs — GREEN Families (Shipped)

**Version:** 1.0
**Date:** 2026-02-12
**Authority:** PM (Opus) + PO (Thunder)
**Governing AD:** AD-006 (House Policy Governance Doctrine)
**Implementing WO:** WO-055 (AD-005 Layer 2)
**Code:** `aidm/core/container_resolver.py`, `aidm/data/equipment_catalog_loader.py`

---

## Family 1: CONTAINMENT_PLAUSIBILITY

```
FAMILY_ID: CONTAINMENT_PLAUSIBILITY
VERSION: 1.0.0
STATUS: GREEN (shipped)

TRIGGER CONDITION:
  An entity attempts to store an item inside a container.
  Evaluates on every store_item action before the item is placed.
  Does NOT trigger for items already in containers at session start
  (those are assumed valid from character creation or prior sessions).

ALLOWED INPUTS:
  - item.size_category: str  (Fine | Diminutive | Tiny | Small | Medium | Large)
  - item.weight_lb: float    (item weight from equipment catalog)
  - item.name: str           (for rejection message only)
  - container.container_max_size: str  (maximum size category accepted)
  - container.container_capacity_lb: float  (maximum weight capacity in pounds)
  - container.storage_slots: int  (maximum discrete item count)
  - container_state.current_weight_lb: float  (weight already in container)
  - container_state.current_slots_used: int   (slots already occupied)
  - container.is_container: bool  (whether the target is a container at all)

ALLOWED OUTPUTS:
  - can_store: bool           (True = item fits; False = rejected)
  - rejection_reason: str     (human-readable explanation when can_store=False)
    Possible rejection reasons:
    - "item too large for container" (size category exceeds max)
    - "weight exceeds remaining capacity"
    - "container is full (slots)"
    - "target is not a container"
    - "unknown item/container ID"

FORBIDDEN EFFECTS:
  - Cannot alter creature stats (HP, AC, ability scores, saves, BAB)
  - Cannot invent new damage types
  - Cannot modify RAW success/failure states
  - Cannot chain into other families implicitly
  - Cannot derive outputs from real-world physics (all outputs must map to
    existing D&D mechanical constructs: DCs, damage, conditions, allow/deny)
  - Cannot modify the item being stored (no weight adjustment, no size change)
  - Cannot modify the container (no capacity expansion, no slot creation)
  - Cannot charge an action cost (that is RETRIEVAL_ACCESSIBILITY's domain)
  - Cannot consider item fragility (that is FRAGILITY_BREAKAGE's domain)

VALUE BOUNDS:
  - can_store: {True, False}  (binary, no partial fit)
  - rejection_reason: str, max 200 chars, no mechanical data exposed
  - Size comparison is ordinal: Fine < Diminutive < Tiny < Small < Medium < Large
  - Weight comparison: item.weight_lb <= container_state.remaining_capacity_lb
  - Slot comparison: container_state.current_slots_used < container.storage_slots

STOP CONDITIONS:
  - Instantiation is per-action: one trigger per store_item attempt.
  - No recursive evaluation (an item being a container does not trigger
    CONTAINMENT_PLAUSIBILITY on itself).
  - If either item_id or container_id is unknown, immediately return False
    with identification failure — no retry, no fallback.

LEDGER FORMAT:
  {
    "family": "CONTAINMENT_PLAUSIBILITY",
    "provenance": "HOUSE_POLICY",
    "item_id": "<item attempting to be stored>",
    "container_id": "<target container>",
    "result": "ALLOWED" | "REJECTED",
    "rejection_reason": "<reason string or empty>",
    "checks": {
      "size_ok": bool,
      "weight_ok": bool,
      "slots_ok": bool
    },
    "container_state_snapshot": {
      "current_weight_lb": float,
      "current_slots_used": int,
      "remaining_capacity_lb": float,
      "remaining_slots": int
    }
  }

PROVENANCE: HOUSE_POLICY
  RAW provides weight-only capacity (PHB p.130). Size-category gating and
  slot limits are House Policy additions per AD-005 Layer 2, addressing
  SIL-001 (Container Capacity — Volume/Shape).
```

**Implementation:** `ContainerResolver.can_store_item()` at [container_resolver.py:127-177](aidm/core/container_resolver.py#L127-L177)
**Test coverage:** ~40 test cases in [test_container_resolver.py](tests/test_container_resolver.py) and [test_equipment_catalog.py](tests/test_equipment_catalog.py)

---

## Family 2: RETRIEVAL_ACCESSIBILITY

```
FAMILY_ID: RETRIEVAL_ACCESSIBILITY
VERSION: 1.0.0
STATUS: GREEN (shipped)

TRIGGER CONDITION:
  An entity attempts to draw, retrieve, or access an item from storage.
  Evaluates on every draw_item / retrieve_item action to determine the
  action economy cost.

ALLOWED INPUTS:
  - item_id: str              (the item being retrieved)
  - stow_location: str        (in_hand | belt | external | in_pack)
  - item.draw_action: str     (catalog override, e.g., "free" for quiver)

ALLOWED OUTPUTS:
  - draw_action: str          (the action cost to retrieve the item)
    Possible values:
    - "free"       — item is already in hand, or item type has free draw
    - "move"       — standard draw from belt or external position
    - "full_round" — must open and search through a pack
    - "standard"   — fallback for unknown locations

FORBIDDEN EFFECTS:
  - Cannot alter creature stats (HP, AC, ability scores, saves, BAB)
  - Cannot invent new damage types
  - Cannot modify RAW success/failure states
  - Cannot chain into other families implicitly
  - Cannot derive outputs from real-world physics (all outputs must map to
    existing D&D mechanical constructs: DCs, damage, conditions, allow/deny)
  - Cannot move the item (retrieval cost evaluation only, not the move itself)
  - Cannot modify the container the item is in
  - Cannot grant bonus actions or action economy benefits beyond RAW
  - Cannot evaluate whether BAB +1 grants free weapon draw (that is a RAW
    rule implemented in the combat resolver, not this family)

VALUE BOUNDS:
  - draw_action: enum {"free", "move", "full_round", "standard"}
  - Location-to-action mapping is fixed:
    in_hand  -> "free"
    belt     -> "move"
    external -> "move"
    in_pack  -> "full_round"
  - Item override: only "free" may override a slower location default
    (items cannot make retrieval slower than location default)
  - Unknown locations default to "move" (conservative)

STOP CONDITIONS:
  - One evaluation per draw/retrieve action. No iteration.
  - If item_id is unknown to catalog, location-based default applies.
    No error, no retry.

LEDGER FORMAT:
  {
    "family": "RETRIEVAL_ACCESSIBILITY",
    "provenance": "HOUSE_POLICY",
    "item_id": "<item being drawn>",
    "stow_location": "<current storage location>",
    "draw_action": "free" | "move" | "full_round" | "standard",
    "override_applied": bool,
    "override_source": "<item catalog draw_action or null>"
  }

PROVENANCE: HOUSE_POLICY
  RAW specifies "retrieve a stored item" as a move action (PHB p.142,
  Table 8-2). The gradient by storage depth (belt vs. external vs. in_pack)
  is House Policy per AD-005 Layer 2, addressing SIL-003 (Item Retrieval
  Action Cost).
```

**Implementation:** `ContainerResolver.get_draw_action()` at [container_resolver.py:228-261](aidm/core/container_resolver.py#L228-L261)
**Test coverage:** 6 test cases in [test_container_resolver.py:307-338](tests/test_container_resolver.py#L307-L338)

---

## Family 3: READINESS_STATE

```
FAMILY_ID: READINESS_STATE
VERSION: 1.0.0
STATUS: GREEN (shipped)

TRIGGER CONDITION:
  1. Lens builds a NarrativeBrief and needs to determine which gear is
     visible to other characters (feeds visible_gear field for Spark).
  2. Any system queries whether an item is "at hand" vs "stowed" for
     action legality checks (e.g., can this item be used without drawing it?).

ALLOWED INPUTS:
  - inventory: List[Dict]     (entity's full inventory with stow_locations)
  - entry.stow_location: str  (in_hand | belt | external | in_pack)
  - entry.item_id: str        (item identifier)
  - item.stow_location: str   (catalog default stow location, fallback)

ALLOWED OUTPUTS:
  - visible_gear: List[str]   (item_ids of externally visible gear)
  - is_visible: bool          (for single-item queries)
    Visibility rules:
    - in_hand  -> visible
    - belt     -> visible
    - external -> visible
    - in_pack  -> NOT visible

FORBIDDEN EFFECTS:
  - Cannot alter creature stats (HP, AC, ability scores, saves, BAB)
  - Cannot invent new damage types
  - Cannot modify RAW success/failure states
  - Cannot chain into other families implicitly
  - Cannot derive outputs from real-world physics (all outputs must map to
    existing D&D mechanical constructs: DCs, damage, conditions, allow/deny)
  - Cannot modify any item's stow_location (read-only query)
  - Cannot determine action cost (that is RETRIEVAL_ACCESSIBILITY's domain)
  - Cannot evaluate Sleight of Hand concealment (that is CONCEALMENT_PLAUSIBILITY)
  - Cannot grant or deny actions — only reports readiness state

VALUE BOUNDS:
  - visible_gear: List[str], may be empty, no duplicates
  - Visibility is binary per item: visible or not visible
  - Location classification is exhaustive:
    {"in_hand", "belt", "external"} -> visible
    {"in_pack"} -> not visible
    Unknown locations -> not visible (conservative default)

STOP CONDITIONS:
  - Single pass through inventory. O(n) where n = inventory size.
  - No recursion into containers (items inside containers inherit
    the container's visibility, not their own stow_location).
  - Maximum inventory size bounded by entity inventory limits
    (typically < 100 items).

LEDGER FORMAT:
  {
    "family": "READINESS_STATE",
    "provenance": "HOUSE_POLICY",
    "entity_id": "<entity whose inventory was queried>",
    "visible_count": int,
    "hidden_count": int,
    "visible_items": ["<item_id>", ...],
    "query_type": "full_inventory" | "single_item"
  }

PROVENANCE: HOUSE_POLICY
  RAW distinguishes "drawn weapon" from "stored item" (PHB p.142) but
  does not define a gradient of readiness states. The four-tier model
  (in_hand / belt / external / in_pack) is House Policy per AD-005
  Layer 2, providing deterministic visibility and accessibility without
  requiring DM judgment.
```

**Implementation:** `ContainerResolver.get_visible_gear()` at [container_resolver.py:263-288](aidm/core/container_resolver.py#L263-L288)
**Data model:** `InventoryEntry` at [container_resolver.py:33-64](aidm/core/container_resolver.py#L33-L64)
**Test coverage:** ~13 test cases in [test_container_resolver.py:341-400](tests/test_container_resolver.py#L341-L400) and [test_gear_affordance_056.py](tests/test_gear_affordance_056.py)

---

## Cross-Family Interaction Rules

These three families are designed to be independent but complementary:

| Action | Primary Family | May Also Trigger |
|--------|---------------|-----------------|
| Store item in container | CONTAINMENT_PLAUSIBILITY | — |
| Draw/retrieve item | RETRIEVAL_ACCESSIBILITY | — |
| Query visible gear | READINESS_STATE | — |
| Store item, then query visibility | CONTAINMENT_PLAUSIBILITY | READINESS_STATE (after store completes) |
| Draw item from pack | RETRIEVAL_ACCESSIBILITY | READINESS_STATE (stow_location changes from in_pack to in_hand) |

**Chaining rule:** Families never invoke each other directly. If storing an item changes visibility, the READINESS_STATE query is a separate downstream evaluation triggered by the state change, not by CONTAINMENT_PLAUSIBILITY calling READINESS_STATE.

---

## Silence Coverage

| Silence ID | Description | Family | Coverage |
|-----------|-------------|--------|----------|
| SIL-001 | Container capacity (volume/shape) | CONTAINMENT_PLAUSIBILITY | Size-category gating addresses shape/volume gap |
| SIL-003 | Item retrieval action cost | RETRIEVAL_ACCESSIBILITY | Four-tier gradient addresses storage depth gap |
| — | Item readiness/visibility | READINESS_STATE | Four-tier model addresses "at hand" ambiguity |

These three families together close the Equipment & Inventory domain's most common silences for v1 scope.

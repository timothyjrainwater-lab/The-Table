# WO-COMEDY-STINGERS-P1 — Comedy Stinger Content Subsystem (Phase 1)

**Status:** READY FOR DISPATCH
**Scope:** Standalone content system — schema, data bank, validator, deterministic selector, tests. **No pipeline wiring.**

---

## Target Lock

Build the NPC comedy stinger subsystem as a standalone, testable content module. Phase 1 is content + logic + validation only. No Director, no Lens PromptPack, no Oracle usage state, no WebSocket protocol touches.

---

## Binary Decisions

1. **Schema location:** `aidm/schemas/npc_stinger.py` — YES (new module)
2. **Data location:** `aidm/data/content_pack/npc_stingers.json` — YES (alongside existing spells.json, creatures.json, feats.json)
3. **Logic location:** `aidm/lens/comedy_stingers.py` — YES (new module, 3 functions)
4. **NPCComedyState in Phase 1?** — NO. `NPCComedyState` is Oracle usage state and belongs in Phase 2. Phase 1 builds the selector with a `used_ids: List[str]` parameter for recency filtering — the caller provides it, the module doesn't persist it.
5. **Fragment count fixed at 4?** — YES. Exactly 4 fragments: 3 credentials + 1 punchline. Validator rejects anything else.
6. **Stinger count:** Minimum 3 per archetype × 7 archetypes = 21 stingers minimum in the bank. Builder may write more if the rhythm is flowing, but 21 is the floor.
7. **Gate suite:** New gate letter **I** — comedy stinger gates. Register in `test_boundary_completeness_gate.py`.

---

## Contract Spec

### 1. Schema — `aidm/schemas/npc_stinger.py`

```python
@dataclass(frozen=True)
class Stinger:
    stinger_id: str                    # stable ID, format: "{archetype}_{nnn}"
    archetype: str                     # tavern_keeper, town_guard, merchant, quest_giver, petty_villain, old_sage, bard
    delivery_contexts: List[str]       # first_meeting, post_combat_lull, tavern_downtime, quest_refusal, callback
    fragments: List[str]              # exactly 4: [cred, cred, cred, punchline]
    tags: Dict[str, Any]              # pace, pause_ms_before_punchline, emphasis_target, mood_hint
```

- `frozen=True` — stingers are immutable content.
- No `constraints_override` field. That was a design-time placeholder from the memo. Phase 1 validator applies uniform rules.
- No `NPCComedyState` dataclass in Phase 1.

### 2. Data Bank — `aidm/data/content_pack/npc_stingers.json`

JSON array of stinger objects matching the schema. Minimum 21 entries (3 per archetype × 7 archetypes). Each stinger must pass the validator at load time.

**Archetypes (7):** `tavern_keeper`, `town_guard`, `merchant`, `quest_giver`, `petty_villain`, `old_sage`, `bard`

**Delivery contexts (5):** `first_meeting`, `post_combat_lull`, `tavern_downtime`, `quest_refusal`, `callback`

Builder writes the actual comedy content. See the loadout memo examples for the staccato rhythm: credential-credential-credential-punchline. The comedy IS the deliverable — phone it in and it'll get rejected.

### 3. Logic — `aidm/lens/comedy_stingers.py`

Three public functions:

**`validate_stinger_bank(stingers: List[Stinger]) -> List[str]`**
- Returns list of error strings (empty = valid).
- Rules (ALL fail-closed — any violation is a hard error):
  1. `len(fragments) == 4`
  2. Credentials (fragments[0:3]): 2–6 words each
  3. Punchline (fragments[3]): word count strictly greater than every credential's word count
  4. No conjunctions ("and", "but", "or", "yet", "so") as standalone words in credentials (fragments[0:3])
  5. Total rendered text (all fragments joined with ". ") produces ≤ 3 sentences
  6. Estimated spoken duration ≤ 6.0 seconds: `(total_words / 2.75) + (tags.get("pause_ms_before_punchline", 0) / 1000)`
  7. `stinger_id` is unique across the entire bank
  8. `archetype` is one of the 7 canonical values
  9. `delivery_contexts` are all from the 5 canonical values

**`select_stinger_deterministic(stingers: List[Stinger], archetype: str, delivery_context: str, seed_material: str, used_ids: Optional[List[str]] = None) -> Optional[Stinger]`**
- Filters by archetype + delivery_context.
- Excludes `used_ids` (recency ring — caller manages state, not this module).
- If pool exhausted after exclusion, relax (ignore used_ids) and select from full filtered pool.
- Deterministic: `hashlib.sha256(seed_material.encode()).digest()` → int mod pool size → index.
- Returns `None` only if no stingers match archetype + delivery_context at all.

**`render_stinger_fragments(stinger: Stinger) -> str`**
- Joins fragments into a single deliverable string.
- Format: `"{frag[0]}. {frag[1]}. {frag[2]}. {frag[3]}."`
- No creativity. No interpolation. Literal join with period-space separators.

### 4. Tests — `tests/lens/test_comedy_stinger_gates.py`

Gate I tests (minimum 8):

| Test ID | Test | Purpose |
|---------|------|---------|
| I-01 | `test_stinger_bank_loads_and_validates` | Load npc_stingers.json, parse into Stinger objects, validate entire bank. 0 errors. |
| I-02 | `test_stinger_rejects_wrong_fragment_count` | fragments with 3 or 5 items → error |
| I-03 | `test_stinger_rejects_long_credential` | credential with 7+ words → error |
| I-04 | `test_stinger_rejects_short_punchline` | punchline shorter than any credential → error |
| I-05 | `test_stinger_rejects_conjunction_in_credential` | "Three wars and two plagues" → error |
| I-06 | `test_stinger_rejects_over_duration` | Stinger exceeding 6.0s estimate → error |
| I-07 | `test_deterministic_selection_seeded` | Same seed_material → same stinger_id across 100 calls |
| I-08 | `test_selection_excludes_used_ids_then_relaxes` | used_ids covers all but one → returns the one. used_ids covers ALL → relaxes and returns from full pool. |

Additional tests welcome if the builder spots edge cases, but the 8 above are the gate floor.

### 5. Boundary Gate Registration

Add `"lens/comedy_stingers"` (or equivalent path token) to the boundary completeness gate in the module that does boundary checking — confirm path before writing. The existing gate test lives at `tests/test_boundary_completeness_gate.py`.

---

## Implementation Plan

1. Create `aidm/schemas/npc_stinger.py` with frozen `Stinger` dataclass.
2. Create `aidm/lens/comedy_stingers.py` with the 3 public functions.
3. Write `aidm/data/content_pack/npc_stingers.json` with ≥21 stingers (3 per archetype × 7).
4. Write `tests/lens/test_comedy_stinger_gates.py` with Gate I tests (≥8 tests).
5. Register the new module in boundary completeness gate.
6. Run full test suite. 0 regressions. All Gate I tests pass.

---

## Integration Seams

**No integration seams.** This is a standalone content module. Phase 1 has no consumers — it produces testable content and logic that Phase 2 will wire into Director/Lens/Oracle.

The only dependency is on Python stdlib (`hashlib`, `json`, `dataclasses`). No imports from `aidm/core/`, `aidm/oracle/`, `aidm/director/`, or `aidm/immersion/`.

---

## Assumptions to Validate

1. **`aidm/data/content_pack/` is the correct data plane** for content pack JSON. Existing files (spells.json, creatures.json, feats.json) live there — confirm the pattern before adding npc_stingers.json.
2. **`tests/lens/` exists and is the correct test home** for lens module tests. Confirm directory exists; create if not.
3. **Boundary completeness gate format** — check how existing modules are registered in `test_boundary_completeness_gate.py` before adding the new entry. Match the existing pattern exactly.
4. **`frozen=True` on the dataclass** is compatible with how other schemas in `aidm/schemas/` are structured. Some may use regular dataclasses. Match the local convention — if other schemas aren't frozen, use regular dataclass and note why.
5. **The conjunction rule** counts standalone words only — "android" contains "and" but is not a conjunction. Split on whitespace, check each token against the banned list. Case-insensitive.

---

## Debrief Focus

1. **Underspecified anchor:** Was anything in this WO ambiguous enough that you had to make a judgment call? What did you decide and why?
2. **Saving gate:** Did the validator catch any of your own stingers during development? Which rule tripped, and did the rule feel right or too strict?

---

## Stop Conditions

- **STOP if** you need to import from `aidm/oracle/`, `aidm/director/`, `aidm/core/event_log.py`, or `aidm/immersion/`. That's Phase 2 wiring. Report what you needed and why.
- **STOP if** the boundary completeness gate pattern is unclear or would require modifying the gate test's structure (not just adding an entry).
- **STOP if** you can't write 21 stingers that pass validation. Report which rules are too tight and suggest specific relaxations.

---

## Delivery

Commit message format: `feat: WO-COMEDY-STINGERS-P1 — <one-line summary>`

**Debrief required.** File as `pm_inbox/DEBRIEF_WO-COMEDY-STINGERS-P1.md`. Five mandatory sections: (0) Scope Accuracy; (1) Discovery Log; (2) Methodology Challenge; (3) Field Manual Entry; (4) Builder Radar.

**Radar format (mandatory, 3 labeled lines):**
- Line 1: **Trap.** Hidden dependency or trap.
- Line 2: **Drift.** Current drift risk.
- Line 3: **Near stop.** What got close to triggering a stop condition.

Missing or unlabeled Radar → REJECT.

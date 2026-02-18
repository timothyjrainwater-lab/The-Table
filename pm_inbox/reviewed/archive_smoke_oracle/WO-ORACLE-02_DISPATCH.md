# WO-ORACLE-02: WorkingSet Compiler (Oracle Phase 2)

**Status:** DISPATCH-READY
**Phase:** Oracle Phase 2 of 3
**Gate:** Gate B — Cold Boot Byte-Equality
**Depends on:** WO-ORACLE-01 (committed at `4c5526a`), DOCTRINE_06_LENS_SPEC_V0.txt
**Blocked by:** Nothing (Lens spec memo now exists)

---

## Target Lock

Build the WorkingSet compiler: a deterministic function that reads Oracle Phase 1 stores (FactsLedger, UnlockState, StoryState) and produces WorkingSet bytes + a PromptPack compiler entry point that converts WorkingSet bytes into PromptPack bytes with an "allowed-to-say" envelope.

**One-line success:** `compile_working_set(stores, policy) -> WorkingSet` produces byte-identical output on repeated calls. `compile_promptpack(working_set) -> (PromptPack, AllowedToSayEnvelope)` produces byte-identical output. Gate B green.

---

## Binary Decisions

1. **WorkingSet lives in Oracle layer, PromptPack compiler lives in Lens layer.** WorkingSet is Oracle's output artifact. PromptPack is Lens's output artifact. The boundary is at the WorkingSet bytes.
2. **No Spark changes.** PromptPack format is unchanged. Only the compilation path changes (WorkingSet → PromptPack instead of ad-hoc assembly).
3. **No Director integration.** Phase 1 Lens operates without Director input. Default pacing.
4. **No PVIB.** ImageGen pipeline does not exist yet. PVIB is Phase 3.
5. **Truncation is Oracle-only.** WorkingSet compiler enforces token budget and truncation policy. Lens/PromptPack compiler does NOT truncate — it routes what it receives.
6. **Use canonical_short_hash for all new content-addressed IDs.** Per PIN-1/PIN-2 in Lens spec. Do NOT use compute_value_hash for Oracle artifact IDs.

---

## Contract Spec

### Change 1: WorkingSet dataclass (new file in `aidm/oracle/`)

Create a WorkingSet frozen dataclass matching Oracle v5.2 §4.5:

```
WorkingSet:
  working_set_id: str          # canonical_short_hash(canonical_bytes)
  world_id: str
  campaign_id: str
  scene_id: str
  mode: str                    # from EV-030 ModeChanged
  policy_ids: dict             # mask_matrix_id, ordering_policy_id, truncation_policy_id, budget_policy_id
  pins_snapshot: dict           # asserted, not derived
  allowmention_handles: tuple   # fact_ids permitted in output (frozen)
  locked_precision_handles: tuple  # fact_ids explicitly locked (frozen)
  facts_slice: tuple            # ordered fact payloads from FactsLedger (frozen)
  state_slice: dict             # StoryState pointer snapshot
  compactions_slice: tuple      # optional compaction payloads (frozen), empty for Phase 2
  directives: dict              # output_class constraints, channel rules
  canonical_bytes: bytes        # canonical JSON UTF-8 (computed, not stored)
  bytes_hash: str               # SHA-256 of canonical_bytes
```

All mutable containers replaced with frozen equivalents (tuple, frozenset). Follows existing Oracle pattern from WO-ORACLE-01.

### Change 2: WorkingSet compiler function (new, in `aidm/oracle/`)

`compile_working_set(facts_ledger, unlock_state, story_state, policy, scope_cursor) -> WorkingSet`

Steps:
1. Read facts from FactsLedger filtered by scope_cursor (scene_id, campaign_id)
2. Apply mask rules: separate allowmention_handles vs locked_precision_handles using UnlockState
3. Apply ordering policy: sort facts by stable_key using ordering_policy_id
4. Apply truncation policy: trim to budget using truncation_policy_id (stable ordering, no stochastic selection)
5. Snapshot StoryState pointers (world_id, campaign_id, scene_id, mode)
6. Assemble WorkingSet dataclass
7. Serialize to canonical JSON (sort_keys=True, separators=(',',':'), ensure_ascii=True, floats FORBIDDEN)
8. Compute bytes_hash = SHA-256 of canonical_bytes
9. Compute working_set_id = canonical_short_hash(canonical_bytes)

**Determinism requirement:** Steps 1-9 introduce no entropy. No randomness, no timestamps, no UUIDs.

### Change 3: AllowedToSayEnvelope dataclass (new, in the module that handles Lens compilation — confirm file path before writing)

```
AllowedToSayEnvelope:
  allowed_handles: tuple        # Oracle handles included in PromptPack
  locked_handles: tuple         # Oracle handles excluded due to precision lock
  mask_matrix_id: str
  promptpack_hash: str          # SHA-256 of PromptPack canonical bytes
  working_set_id: str           # traceability to input WorkingSet
```

### Change 4: PromptPack compiler entry point (new function, in the module that handles PromptPack building — confirm file path before writing)

`compile_promptpack(working_set: WorkingSet) -> tuple[PromptPack, AllowedToSayEnvelope]`

Steps:
1. Extract facts_slice → TruthChannel (mask-safe subset only — filter against allowmention_handles)
2. Extract compactions_slice → MemoryChannel (if present)
3. Extract directives → TaskChannel + OutputContract
4. Apply default StyleChannel (no Director input in Phase 2)
5. Assemble PromptPack using existing five-channel structure
6. Serialize PromptPack to canonical bytes
7. Compute promptpack_hash = SHA-256 of canonical bytes
8. Build AllowedToSayEnvelope from allowmention_handles, locked_precision_handles, mask_matrix_id, promptpack_hash, working_set_id
9. Return (PromptPack, AllowedToSayEnvelope)

**No truncation in this function.** WorkingSet slices are already budget-constrained. Lens routes, never clips (A-ORACLE-TRUNC).

### Change 5: Gate B tests (new test file)

Minimum 20 tests across these categories:

**Determinism (Gate B core):**
1. `test_compile_working_set_deterministic` — same inputs twice, assert bytes_hash identical
2. `test_compile_working_set_deterministic_10x` — 10 compilations, all bytes_hash identical
3. `test_compile_promptpack_deterministic` — same WorkingSet twice, assert promptpack_hash identical
4. `test_compile_promptpack_deterministic_10x` — 10 compilations, all promptpack_hash identical
5. `test_cold_boot_byte_equality` — compile from stores, clear, recompile from same stores, assert WorkingSet bytes identical
6. `test_cold_boot_promptpack_equality` — full pipeline stores → WorkingSet → PromptPack, repeat, assert identical

**Mask enforcement (LENS-G2):**
7. `test_locked_handles_absent_from_promptpack` — inject locked facts, compile, assert absent from PromptPack bytes
8. `test_only_allowmention_handles_in_output` — verify no handle outside allowmention set appears in output
9. `test_locked_tokens_absent_from_truth_channel` — precision content excluded from TruthChannel
10. `test_locked_tokens_absent_from_memory_channel` — precision content excluded from MemoryChannel
11. `test_envelope_manifest_complete` — AllowedToSayEnvelope.allowed_handles matches actual PromptPack content

**Attribution (LENS-G3):**
12. `test_every_promptpack_fact_has_oracle_source` — each content block traces to a FactsLedger entry
13. `test_envelope_working_set_id_matches_input` — traceability chain intact

**No-truncation (LENS-G4):**
14. `test_promptpack_contains_all_slice_content` — no data loss between WorkingSet slices and PromptPack channels
15. `test_lens_no_token_counting` — assert compile_promptpack contains no token budget logic

**No-backflow (LENS-G5):**
16. `test_lens_no_oracle_writes` — static: compile_promptpack does not call any Oracle store write method
17. `test_oracle_layer_boundary` — boundary completeness gate registers WorkingSet in Oracle layer

**WorkingSet integrity:**
18. `test_working_set_canonical_json_no_floats` — float injection raises TypeError
19. `test_working_set_id_is_canonical_short_hash` — verify working_set_id = canonical_short_hash(canonical_bytes)
20. `test_working_set_frozen` — all container fields are frozen (tuple/frozenset, no list/set/dict mutation)

---

## Integration Seams

1. **Oracle stores → WorkingSet compiler:** The compiler reads from FactsLedger, UnlockState, and StoryState created by WO-ORACLE-01. Confirm the read APIs exist and match (e.g., `facts_ledger.get_facts()`, `unlock_state.get_unlocked_handles()`, `story_state.get_pointers()`). The WO-ORACLE-01 builder may have used different method names — validate before coding.

2. **WorkingSet → PromptPack compiler:** The PromptPack compiler takes a WorkingSet dataclass (Oracle layer) and produces a PromptPack (Lens layer). This is a cross-layer boundary. The boundary completeness gate (`test_boundary_completeness_gate.py`) must permit Oracle → Lens reads but not Lens → Oracle writes.

3. **PromptPack format stability:** The existing PromptPack five-channel format (aidm/schemas/prompt_pack.py) must not change. The compiler produces PromptPacks using the existing dataclass. If the existing PromptPack constructor or serialization doesn't support the WorkingSet-derived inputs, adapt the compiler, not the PromptPack.

4. **Canonical JSON profile:** The WorkingSet compiler must use the same canonical JSON profile as WO-ORACLE-01 (canonical.py: sort_keys=True, separators=(',',':'), ensure_ascii=True, floats FORBIDDEN via recursive pre-walk). Import from `aidm/oracle/canonical.py`.

---

## Assumptions to Validate

1. **WO-ORACLE-01 store APIs:** Confirm method names and signatures on FactsLedger, UnlockState, StoryState. The dispatch spec used descriptive names; the builder may have chosen different ones. Check the actual code at `aidm/oracle/`.

2. **canonical.py location and exports:** Confirm `canonical_json()`, `canonical_hash()`, `canonical_short_hash()` exist in `aidm/oracle/canonical.py` and are importable.

3. **Boundary completeness gate:** WO-ORACLE-01 registered `oracle` in the boundary gate. Confirm the gate permits oracle → lens reads. If not, update the gate's `PROHIBITED_IMPORTS` to allow this specific direction.

4. **PromptPack constructor:** Confirm the existing PromptPack dataclass can be constructed from WorkingSet-derived data without format changes. Check required fields and types.

5. **Existing PromptPackBuilder:** The new `compile_promptpack` function may overlap with existing `PromptPackBuilder.build()`. Decide whether to wrap the existing builder or write a parallel path. The existing builder takes NarrativeBrief + session_facts; the new function takes WorkingSet. These are different input shapes, so a parallel path is likely correct. Do not break the existing builder — it remains valid for non-Oracle compilation paths.

6. **Test file location:** Gate B tests should go in a new test file (e.g., `tests/test_oracle_gate_b.py` or `tests/test_working_set_compiler.py`). Follow existing test file naming conventions in the repo.

---

## Success Criteria (20 minimum)

Gate B is GREEN when all of:
1. `compile_working_set()` exists and is callable
2. `compile_promptpack()` exists and is callable
3. AllowedToSayEnvelope is emitted with every PromptPack compilation
4. Tests 1-6 pass (determinism — byte-identical on rebuild)
5. Tests 7-11 pass (mask enforcement — locked content absent)
6. Tests 12-13 pass (attribution — traceability intact)
7. Tests 14-15 pass (no-truncation — Lens routes, doesn't clip)
8. Tests 16-17 pass (no-backflow — static boundary enforcement)
9. Tests 18-20 pass (WorkingSet integrity — frozen, canonical, no floats)
10. All existing tests still pass (0 regressions)
11. WorkingSet uses canonical_short_hash for working_set_id (not compute_value_hash)
12. No wall-clock timestamps in any new dataclass
13. No UUIDs or random values in any compilation output
14. Canonical JSON profile matches WO-ORACLE-01 (same separators, same float prohibition)
15. Boundary completeness gate updated if new layer registered
16. PromptPack format unchanged (existing consumers unaffected)
17. WorkingSet dataclass is fully frozen (immutability gate passes)
18. At least 20 tests in Gate B test file
19. AllowedToSayEnvelope.allowed_handles matches actual PromptPack content handles
20. Gate A (22/22) still GREEN after changes

---

## Constraints

- **No Spark changes.** PromptPack is the interface. Spark doesn't know or care that the compilation path changed.
- **No Director integration.** Phase 2 only. Default pacing in StyleChannel.
- **No PVIB.** Phase 3 only.
- **No wall-clock timestamps.** Anywhere. In any dataclass field.
- **No compute_value_hash for Oracle artifact IDs.** Use canonical_short_hash only (PIN-2 in Lens spec).
- **Floats FORBIDDEN in canonical artifacts.** Use the recursive pre-walk pattern from WO-ORACLE-01 (Field Manual #22).
- **New aidm/ packages must register in boundary completeness gate** (Field Manual #23).
- **Oracle is the sole truncator** (A-ORACLE-TRUNC). The PromptPack compiler must not contain token-counting or budget logic.
- **Oracle stores are read-only to Lens.** compile_promptpack must not call write methods on any Oracle store.

---

## Delivery

1. Write debrief to `pm_inbox/DEBRIEF_WO-ORACLE-02.md` with 4 mandatory sections (Scope Accuracy, Discovery Log, Methodology Challenge, Field Manual Entry). 500-word cap.
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md` — add WO-ORACLE-02 verdict row (leave verdict blank for PM to fill).
3. `git add` ALL files: code + tests + debrief + briefing.
4. Commit with message: `feat: WO-ORACLE-02 — WorkingSet compiler + PromptPack compiler + Gate B`
5. Add commit hash to debrief header.
6. Amend commit to include hash in debrief.
7. Run `git status` to confirm clean tree.

---

*Drafted by PM (Aegis). Dispatch-ready for Operator.*

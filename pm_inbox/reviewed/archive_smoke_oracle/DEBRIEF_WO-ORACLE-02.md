# DEBRIEF: WO-ORACLE-02 — WorkingSet Compiler + PromptPack Compiler + Gate B

**WO:** WO-ORACLE-02
**Status:** COMPLETE
**Commit:** `09ad53d` (hash changes on amend — verify with `git log --oneline -1`)

---

## 1. Scope Accuracy

The WO specified 5 changes and 20 success criteria. All 5 changes implemented, all 20 criteria met. 23 Gate B tests written (exceeding the 20 minimum). One file modified outside the primary scope: `aidm/oracle/canonical.py` required a fix to handle `MappingProxyType` objects in the float-rejection pre-walk and JSON encoder — frozen dataclass containers from `__post_init__` are `MappingProxyType`, not `dict`, so `isinstance(o, dict)` returned False and the encoder's `default()` raised TypeError.

**Files created (3):** `aidm/oracle/working_set.py` (WorkingSet dataclass + `compile_working_set()` + ScopeCursor + CompilationPolicy), `aidm/lens/promptpack_compiler.py` (AllowedToSayEnvelope + `compile_promptpack()`), `tests/test_oracle_gate_b.py` (23 Gate B tests across 6 categories).

**Files modified (1):** `aidm/oracle/canonical.py` — changed `isinstance(o, dict)` to `isinstance(o, Mapping)` (from `collections.abc`) in `_reject_floats()`, and added MappingProxyType→dict conversion in `default()`. This makes canonical_json handle frozen containers transparently.

## 2. Discovery Log

**Before implementation:**
- Confirmed Phase 1 store APIs: `FactsLedger.all_facts()`, `UnlockState.unlocked_handles(scope)`, `StoryStateLog.current()`. Method names matched expectations from WO-ORACLE-01.
- Confirmed `canonical_json`, `canonical_hash`, `canonical_short_hash` all importable from `aidm.oracle.canonical`.
- Confirmed PromptPack constructor accepts TruthChannel, MemoryChannel, TaskChannel, StyleChannel, OutputContract. TruthChannel requires `action_type` and `actor_name` at minimum.
- Confirmed boundary gate: `("oracle", "lens")` is PROHIBITED but `("lens", "oracle")` is NOT — correct direction for Lens reading WorkingSet from Oracle.
- Confirmed existing `PromptPackBuilder` takes NarrativeBrief (different input shape). Parallel path is correct — existing builder untouched.

**During implementation:**
- The immutability gate (`test_no_unprotected_mutable_fields_in_frozen_dataclasses`) caught WorkingSet's Dict fields immediately. Added `__post_init__` with `MappingProxyType` freezing following the existing pattern from `fact_acquisition.py`.
- Two Gate B tests required refinement: `test_lens_no_token_counting` produced a false positive on the word "budget" in a docstring, and `test_lens_no_oracle_writes` matched `.append(` used for list-building, not Oracle store writes. Both fixed by making assertions more precise — strip comments/docstrings before checking, and match specific Oracle store method patterns.
- The MappingProxyType bug was the final fix: frozen containers serialized fine within `compile_working_set` (canonical_json runs on plain dicts before `__post_init__` freezes them), but downstream code calling `canonical_short_hash()` on already-frozen `facts_slice` entries hit the TypeError.

## 3. Methodology Challenge

**The `canonical.py` modification is a Phase 1 file touched by Phase 2.** The WO doesn't explicitly scope modifications to `canonical.py`, but the fix is a direct consequence of the frozen container pattern mandated by the WO's immutability requirements. The alternative — converting MappingProxyType back to dict at every call site — would be error-prone and violate the principle that frozen containers should be transparent to consumers. The fix is minimal (import `Mapping`, change one isinstance check, add one default handler) and strengthens the canonical profile for all future frozen dataclass consumers.

**Static analysis tests are fragile.** The no-token-counting and no-oracle-writes tests use source code inspection (regex on `inspect.getsource`). These are inherently brittle — a comment mentioning "budget" or a variable named `append_result` would trigger false positives. The current implementation strips docstrings/comments and checks for specific Oracle store method signatures, but future maintainers should be aware these tests need updating if method names change.

## 4. Field Manual Entry

**`canonical_json` must handle `Mapping` types, not just `dict`.** Frozen dataclasses use `MappingProxyType` (a `Mapping` but not a `dict`) in `__post_init__` for immutability. The canonical JSON encoder's float-rejection pre-walk and `default()` handler must use `isinstance(o, Mapping)` from `collections.abc`, not `isinstance(o, dict)`. This applies to any code that processes frozen Oracle artifacts through canonical serialization. The fix from WO-ORACLE-02 makes this transparent — no call-site changes needed.

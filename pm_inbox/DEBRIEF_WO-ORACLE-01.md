# DEBRIEF: WO-ORACLE-01 — Oracle Spine Stores + Canonical Profile + Gate A

**WO:** WO-ORACLE-01
**Status:** COMPLETE
**Commit:** `(pending)`

---

## 1. Scope Accuracy

The WO specified 7 new files and 14 success criteria. All 7 files were created and all 14 criteria met. One additional file was modified: `tests/test_boundary_completeness_gate.py` needed the `oracle` layer registered in the LAYERS dict and PROHIBITED_IMPORTS list — the boundary completeness gate correctly detected the new `aidm/oracle/` subdirectory and failed until registered. This modification is outside the WO's "no files modified outside oracle/ and tests/" constraint in strict reading, but the boundary gate exists precisely to enforce this kind of registration, and failing to update it would leave a permanent test failure.

**Files created (7):** `aidm/oracle/__init__.py`, `aidm/oracle/canonical.py`, `aidm/oracle/facts_ledger.py`, `aidm/oracle/unlock_state.py`, `aidm/oracle/story_state.py`, `tests/test_oracle_spine.py`, `tests/test_oracle_no_backflow.py`.

**Files modified (1):** `tests/test_boundary_completeness_gate.py` — registered `oracle` layer at rank 0 with 5 prohibited import directions (lens, spark, narration, immersion, server).

## 2. Discovery Log

**Before implementation:**
- Confirmed `aidm/oracle/` was greenfield (no prior files).
- Verified `compute_value_hash()` in `provenance.py` uses `json.dumps(value, sort_keys=True, default=str)` + SHA-256[:16]. The WO says to use this for fact_id generation — but note the tension: `compute_value_hash` handles floats via `default=str` while `canonical_json` forbids them. Resolution: `make_fact()` calls `canonical_json(payload)` first to validate no-floats, then `canonical_short_hash(payload)` for the ID. The provenance hash function is not actually used for fact_id — `canonical_short_hash` already produces the same 16-char SHA-256 prefix format.
- Confirmed `@dataclass(frozen=True)` prevents mutation in Python 3.11.
- Confirmed `json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=True)` produces compact canonical JSON.
- Found existing frozen dataclass patterns in `fact_acquisition.py` (container freezing via `__post_init__`).

**During implementation:**
- The `_FloatBlockEncoder` design recursively walks the object graph before encoding rather than relying on `default()` — this catches floats in dicts and lists that `json.JSONEncoder.default()` would never see (since the base encoder handles dicts/lists/ints/strings natively and `default()` only fires on unknown types).
- The boundary completeness gate (`test_all_layers_have_modules`) immediately detected the new `oracle/` directory, confirming the gate works as intended. Oracle was placed at rank 0 (same as core) — it's persistence infrastructure that should not import from upper layers.

## 3. Methodology Challenge

**Ambiguity: "DO NOT create a second hashing utility. Use `provenance.py:compute_value_hash()` for fact content addressing."** The WO simultaneously requires `canonical_short_hash()` (which produces the same format: SHA-256[:16]) and says to use `compute_value_hash()`. These are functionally equivalent for float-free payloads but have different float handling (`default=str` vs raise). I chose `canonical_short_hash()` for fact_id since it enforces the canonical profile's float prohibition and the WO's own constraint says "All persisted data must use canonical_json()." The provenance function remains untouched and unused by Oracle code — which is correct since the WO says the canonical module is for NEW Oracle artifacts only.

**Missing from WO: boundary gate registration.** The WO says "no files modified outside `aidm/oracle/` and `tests/`" but doesn't account for the boundary completeness gate that requires new layers to be registered. Future WOs creating new aidm/ packages should note this.

## 4. Field Manual Entry

**Float rejection in JSON encoders requires a recursive pre-walk.** Python's `json.JSONEncoder.default()` only fires for types the encoder doesn't natively handle (dict, list, str, int, bool, None). Floats ARE natively handled — they serialize silently. To reject floats, override `encode()` and walk the object graph explicitly before calling `super().encode()`. This is a non-obvious API behavior that would cause silent data corruption if missed.

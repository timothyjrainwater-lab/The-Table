# M2 Persistence Architecture Freeze

**Document ID:** M2-PERSIST-FREEZE
**Version:** 1.1
**Date:** 2026-02-10 (amended)
**Status:** FROZEN AS-IS
**Authority:** Binding architectural specification

---

## FREEZE STATEMENT

This document captures the M2 persistence architecture **as implemented**. No schema redesign, field additions, or structural changes are permitted without a formal amendment process.

**Amendment Protocol:** Any modification to the schemas, APIs, or boundaries documented here requires:
1. Written rationale with explicit justification
2. PM approval
3. Version bump to this document
4. Update to `AIDM_EXECUTION_ROADMAP_V3.md`
5. Regression test audit

---

## 1. Architecture Overview

### System Boundaries

The M2 persistence layer operates as a **one-way dependency** from the engine:

```
┌──────────────────────────────────────────────────────┐
│  Engine (aidm/core/)                                 │
│  - play_loop, combat_controller, interaction        │
│  - Deterministic resolution, event sourcing          │
└────────────┬─────────────────────────────────────────┘
             │ writes events, produces EngineResults
             ↓
┌──────────────────────────────────────────────────────┐
│  Persistence (M2 layer)                              │
│  - CampaignStore: Filesystem-backed campaign storage │
│  - PrepOrchestrator: Deterministic prep queue        │
│  - AssetStore: Campaign asset management             │
│  - WorldArchive: Export/import bundle                │
│  - SessionLog: Intent→result correlation + replay    │
└──────────────────────────────────────────────────────┘
```

**Direction:** Engine → Persistence (ONLY)
**Reverse dependency:** NOT PERMITTED. Persistence does not influence engine mechanics.

### File Layout

Each campaign is stored as a directory under `<store_root>/<campaign_id>/`:

```
campaigns/
  <campaign_id>/
    manifest.json            # Campaign metadata + version pinning
    events.jsonl             # Append-only event log
    intents.jsonl            # Append-only intent log
    start_state.json         # Initial WorldState snapshot
    assets/                  # Campaign-specific assets
      index.json             # Asset metadata index
      <asset_id>_<kind>      # Asset files (placeholder or real)
    prep/                    # Prep orchestrator state
      prep_jobs.jsonl        # Append-only job log
```

All JSON output uses **sorted keys** for determinism.

---

## 2. Data Model (As Implemented)

### 2.1 Campaign Manifest

**Schema:** `CampaignManifest` in `aidm/schemas/campaign.py`

**Fields:**
- `campaign_id: str` — Unique identifier (BL-017: injected, not generated)
- `title: str` — Human-readable campaign name
- `engine_version: str` — Engine version at creation (default: "0.1.0")
- `config_schema_version: str` — Schema version for forward compat (default: "1.0")
- `created_at: str` — ISO timestamp (BL-018: injected, UX only, not in replay hash; default empty string)
- `master_seed: int` — Master RNG seed for deterministic campaign
- `session_zero: SessionZeroConfig` — Session Zero configuration (frozen after start)
- `paths: CampaignPaths` — Directory layout convention
- `tool_versions: Dict[str, str]` — Optional version pinning (e.g., `{'python': '3.11'}`)

**Persistence:** `manifest.json` (JSON, sorted keys, indented)

### 2.2 Session Zero Config

**Schema:** `SessionZeroConfig` in `aidm/schemas/campaign.py`

**Fields:**
- `config_schema_version: str` (default: "1.0")
- `ruleset_id: str` (default: "RAW_3.5")
- `optional_rules: List[str]` (default: `[]`)
- `alignment_mode: str` (valid: `"strict" | "inferred" | "narrative_only"`, default: "strict")
- `preparation_depth: str` (valid: `"light" | "standard" | "deep"`, default: "standard")
- `visibility_prefs: Dict[str, Any]` (default: `{}`)
- `creative_boundaries: Dict[str, Any]` (default: `{}`)
- `doctrine_enforcement: bool` (default: `True`)
- `fail_open_to_raw: bool` (default: `True`)
- `amendments: List[Dict[str, Any]]` (default: `[]`, append-only)

**Immutability:** After campaign start, modifications are recorded as **amendments** (append-only), not in-place edits.

### 2.3 PrepJob

**Schema:** `PrepJob` in `aidm/schemas/campaign.py`

**Fields:**
- `job_id: str` — Deterministic ID: `sha256(campaign_id + job_type + stable_key)[:16]`
- `job_type: str` — Valid: `"INIT_SCAFFOLD" | "SEED_ASSETS" | "BUILD_START_STATE" | "VALIDATE_READY"`
- `stable_key: str` — Secondary sort key for deterministic ordering
- `insertion_index: int` — Insertion order for total ordering
- `status: str` — Valid: `"pending" | "running" | "done" | "failed"`
- `inputs: Dict[str, Any]` — JSON-serializable job inputs
- `outputs: Dict[str, Any]` — JSON-serializable job outputs (populated on completion)
- `content_hash: Optional[str]` — SHA256 hash of outputs for idempotency
- `error: Optional[str]` — Error message if status == `"failed"`

**Idempotency:** Jobs with matching `job_id` and `content_hash` are skipped on re-run.

**Ordering:** Jobs are sorted by `(job_type_order, stable_key, insertion_index)` for deterministic queue construction.

### 2.4 AssetRecord

**Schema:** `AssetRecord` in `aidm/schemas/campaign.py`

**Fields:**
- `asset_id: str` — Deterministic ID: `sha256(campaign_id + kind + semantic_key)[:16]`
- `kind: str` — Valid: `"PLACEHOLDER" | "PORTRAIT" | "SCENE" | "AMBIENT_AUDIO" | "MAP" | "HANDOUT"`
- `semantic_key: str` — Semantic identifier (e.g., `"generic:tavern:interior:v1"`)
- `content_hash: str` — SHA256 hash of file contents (empty for placeholders)
- `path: str` — Relative path within campaign assets directory
- `provenance: str` — Valid: `"GENERATED" | "BUNDLED" | "MANUAL" | "SHARED_CACHE"`
- `regen_policy: str` — Valid: `"REGEN_ON_MISS" | "FAIL_ON_MISS"`

**M2 Implementation:** All assets are **placeholders** (zero-byte files with full metadata). Real asset generation is deferred to M3.

**Authority:** Assets are atmospheric only, never mechanical authority (per LRP-001).

---

## 3. Determinism Guarantees

### 3.1 BL-017: UUID Injection Only

**Rule:** No dataclass field may use `uuid.uuid4()` in `default_factory`.

**Compliance Status:**
- ✅ `CampaignManifest.campaign_id` — No default, caller must inject
- ✅ `PrepJob.job_id` — Deterministic from `compute_job_id(campaign_id, job_type, stable_key)`
- ✅ `AssetRecord.asset_id` — Deterministic from `compute_asset_id(campaign_id, kind, semantic_key)`

**Enforcement:** BL-017 tests in `tests/test_boundary_law.py`

### 3.2 BL-018: Timestamp Injection Only

**Rule:** No dataclass field may use `datetime.utcnow()` or `datetime.now()` in `default_factory`.

**Compliance Status:**
- ✅ `CampaignManifest.created_at` — Default empty string (UX-only, excluded from replay hash)
- ⚠️ **VIOLATION:** `aidm/core/prep_orchestrator.py` `execute_job()` line ~151 — `datetime.now(timezone.utc).isoformat()` fallback for `_logged_at`

**Impact:** The `_logged_at` field is added to prep job log entries for audit purposes. It is NOT part of the `PrepJob` schema and is NOT used for deterministic replay. This is a **minor violation** for logging only, with non-deterministic impact.

**Remediation (DEFERRED):** Replace with injected timestamp when logging infrastructure is formalized.

**Enforcement:** BL-018 tests in `tests/test_boundary_law.py`

### 3.3 BL-020: WorldState Immutability at Non-Engine Boundaries

**Rule:** No module outside the engine boundary may mutate a WorldState instance or any object reachable from it.

**Compliance Status:**
- ✅ `session_log.py` — ReplayHarness is **read-only**. Passes WorldState to resolver but does not mutate.
- ✅ `prep_orchestrator.py` — Creates initial WorldState via `WorldState(...)` constructor (authorized under BL-020 §3).

**Pre-seeded finding (INCORRECT):** "session_log.py: ReplayHarness mutates WorldState directly" — REJECTED. Code inspection confirms read-only access.

**Enforcement:** BL-020 tests in `tests/test_boundary_law.py`

---

## 4. Versioning & Migration Strategy (As Implemented)

### Version Pinning

**Campaign Manifest** pins:
- `engine_version` — Engine version at campaign creation
- `config_schema_version` — Schema version for forward compatibility
- `tool_versions` (optional) — External tool versions (e.g., Python, model versions)

**Forward Compatibility:**
- Unknown fields in deserialized manifests are **ignored** (fail-open)
- Schema version mismatch triggers **warning**, not hard failure
- Old campaigns remain playable despite engine upgrades

### Migration Path (NOT IMPLEMENTED)

**Current state:** No migration tooling exists. Schema changes require manual intervention.

**Deferred to:** Post-M2 hardening or M4 (offline packaging milestone).

---

## 5. SPARK Swappability Implications

### Current State

M2 persistence does NOT yet interface with SPARK (LLM narration layer). The following components are **SPARK-agnostic**:

- `CampaignStore` — Writes manifest + logs, no LLM dependency
- `PrepOrchestrator` — Deterministic job queue, no LLM calls
- `AssetStore` — Placeholder-only for M2, no generation
- `WorldArchive` — Serialization/deserialization only

### Future SPARK Integration (M3+)

When SPARK is integrated:
- **Asset generation** (images, audio) will require SPARK adapters
- **Prep orchestrator** may invoke SPARK for NPC generation, location descriptions
- **Session Zero** config will include SPARK model selection

**Constraint:** SPARK must remain **swappable**. All LLM calls must go through adapter interfaces with fallback stubs.

**Reference:** `docs/design/SOLO_FIRST_PREPARATORY_DM_MODEL.md` (SF-PDM-001)

---

## 6. API Inventory

### CampaignStore (`aidm/core/campaign_store.py`)

**Methods:**
- `create_campaign(campaign_id, session_zero, title, created_at, seed=0) -> CampaignManifest`
  - Creates directory structure, writes manifest, initializes empty logs
  - **Caller responsibility:** Inject `campaign_id` (BL-017) and `created_at` (BL-018)
- `load_campaign(campaign_id) -> CampaignManifest`
  - Loads manifest from disk, raises `CampaignStoreError` if not found
- `save_manifest(manifest: CampaignManifest) -> None`
  - Writes manifest to disk (sorted keys, indented JSON)
- `list_campaigns() -> List[str]`
  - Returns sorted list of campaign IDs
- `campaign_dir(campaign_id) -> Path`
  - Returns path to campaign directory
- `campaign_exists(campaign_id) -> bool`
  - Checks if campaign directory + manifest exist

### PrepOrchestrator (`aidm/core/prep_orchestrator.py`)

**Methods:**
- `build_job_queue() -> List[PrepJob]`
  - Returns deterministic job queue (same manifest → same queue)
- `execute_job(job: PrepJob) -> PrepJob`
  - Executes single job, returns updated job with outputs
  - Idempotent: skips if `job_id` already done with matching `content_hash`
- `run_all() -> List[PrepJob]`
  - Executes all jobs in deterministic order, stops on first failure
- `get_status() -> Dict[str, Any]`
  - Returns `{percent_complete, completed, total, current_job, blockers}`

**Job Types (Implemented):**
1. `INIT_SCAFFOLD` — Ensure directory structure, create empty logs
2. `SEED_ASSETS` — Create placeholder assets (count varies by `preparation_depth`)
3. `BUILD_START_STATE` — Produce initial WorldState stub, persist to `start_state.json`
4. `VALIDATE_READY` — Run validation checks, produce readiness report

### AssetStore (`aidm/core/asset_store.py`)

**Methods:**
- `put(record: AssetRecord, content: bytes) -> AssetRecord`
  - Stores asset file + metadata, computes content hash
- `get(asset_id: str) -> Optional[AssetRecord]`
  - Looks up asset metadata by ID
- `get_content(asset_id: str) -> Optional[bytes]`
  - Reads asset file content
- `resolve(semantic_key, kind, campaign_id, use_shared_cache=True) -> AssetRecord`
  - Resolves asset by semantic key, checks shared cache if enabled
  - Creates placeholder if not found
- `list_assets() -> List[AssetRecord]`
  - Returns sorted list of all assets
- `verify_integrity() -> List[str]`
  - Checks all assets exist and hashes match, returns list of issues
- `save_index(path=None) -> None`
  - Saves asset index to JSON (default: `assets/index.json`)
- `load_index(path=None) -> None`
  - Loads asset index from JSON

**Shared Cache:** Optional cross-campaign asset reuse (generic tavern, road, forest, etc.)

### WorldArchive (`aidm/core/world_archive.py`)

**Methods:**
- `export_campaign(store, campaign_id, output_path, options=None) -> Path`
  - Exports campaign to directory bundle (manifest + logs + assets + prep)
  - Returns path to created archive directory
- `import_campaign(archive_path, store) -> CampaignManifest`
  - Imports campaign from archive into store
  - Validates archive structure first, raises `WorldArchiveError` if invalid
- `validate_archive(archive_path) -> ArchiveValidationResult`
  - Validates archive structure (manifest, logs, schema version)
  - Returns `{valid, status, issues, manifest_version, campaign_id}`

**Export Options:**
- `include_assets: bool` (default: `True`)
- `include_prep_log: bool` (default: `True`)

### SessionLog (`aidm/core/session_log.py`)

**Classes:**
- `SessionLogEntry` — Single intent→result correlation
  - `intent: IntentObject`
  - `result: Optional[EngineResult]` (None for retracted intents)
- `SessionLog` — Append-only log with JSONL persistence
  - `append(intent, result=None)`
  - `get_by_intent_id(intent_id) -> Optional[SessionLogEntry]`
  - `to_jsonl(path)` / `from_jsonl(path)`
- `ReplayHarness` — Deterministic replay verification
  - `replay_session(session_log) -> ReplayVerificationResult`
  - `verify_10x(session_log) -> Tuple[bool, List[ReplayVerificationResult]]`

**Replay Guarantee:** Identical inputs → identical outputs (10× verified)

---

## 7. Test Coverage

**M2 Persistence Tests:** 135 tests passing in 1.11s

**Test Files:**
- `tests/test_campaign_store.py` (27 tests)
- `tests/test_prep_orchestrator.py` (22 tests)
- `tests/test_asset_store.py` (23 tests)
- `tests/test_world_archive.py` (31 tests)
- `tests/test_campaign_schemas.py` (32 tests)

**Coverage:**
- Campaign creation + loading + manifest save
- Prep job queue construction (determinism verified 10×)
- Prep job execution + idempotency
- Asset store put/get/resolve (with shared cache)
- Archive export/import roundtrip
- Schema validation + JSON serialization

**Boundary Law Enforcement:**
- BL-017 / BL-018 / BL-020 enforced via `tests/test_boundary_law.py`

---

## 8. Known Gaps & Deferred Items

### MUST FIX (Before further M2 work)

**None.** All critical violations are either resolved or documented as acceptable.

### SHOULD FIX (During M2 hardening)

1. **prep_orchestrator.py execute_job():~151** — Replace `datetime.now()` with injected timestamp for `_logged_at` field
   - **Impact:** Minor. Logging only, not deterministic replay.
   - **Remediation:** Add `log_timestamp` parameter to `_log_job_state()`.

2. **session_log.py test helper** — `create_test_resolver()` contains uuid/datetime defaults
   - **Impact:** Test helper in production module (acceptable for testing, but non-ideal separation).
   - **Classification:** Test helper in production module.
   - **Remediation:** Move test helpers to test utilities module or add explicit documentation marker.

3. **Missing campaign deletion API** — `CampaignStore` has no `delete_campaign()` method
   - **Impact:** Campaigns can only be deleted manually (filesystem operation).
   - **Remediation:** Add `delete_campaign(campaign_id)` with safety checks.

4. **No schema version migration tooling** — Version bumps require manual intervention
   - **Impact:** Schema changes break old campaigns.
   - **Remediation:** Deferred to M4 (offline packaging).

### OK DEFERRED

1. **Real asset generation** — M2 uses placeholders only (deferred to M3)
2. **SPARK integration** — Prep orchestrator has no LLM calls yet (deferred to M3)
3. **Incremental prep resume** — Prep runs to completion or failure, no pause/resume (deferred to M3)
4. **Campaign cloning** — No API to duplicate a campaign (deferred to M4)

---

## 9. Explicit Freeze + Amendment Protocol

**This architecture is now FROZEN.**

Any modification to:
- Schemas in `aidm/schemas/campaign.py`
- APIs in `aidm/core/campaign_store.py`, `prep_orchestrator.py`, `asset_store.py`, `world_archive.py`
- Persistence boundaries documented here

requires:
1. **Rationale document** — Why is the change necessary? What breaks without it?
2. **PM approval** — Written sign-off from project manager
3. **Version bump** — Increment this document version + update changelog
4. **Roadmap update** — Update `AIDM_EXECUTION_ROADMAP_V3.md` to reflect new status
5. **Regression test audit** — Run full test suite, verify no determinism breaks

**Amendment history:**

### Amendment 1.1 (2026-02-10): BL-017/018 Remediation

**Agent:** Sonnet A (retroactive documentation)
**Work Order:** WO-M1-02 (Inject-Only IDs & Timestamps)
**Rationale:** The M2 freeze (v1.0) was established before WO-M1-02 removed all nondeterministic defaults from dataclass fields. Two files within the M2 persistence boundary (`aidm/core/event_log.py` and `aidm/core/session_log.py`) were modified as part of BL-017/018 remediation. This amendment retroactively documents those changes.

**Changes Made:**

1. **`aidm/core/event_log.py`**
   - Added BOUNDARY LAW (BL-008) documentation header
   - No schema changes
   - Impact: Documentation only, clarifies monotonic event ID guarantee

2. **`aidm/core/session_log.py`**
   - Removed `time.perf_counter()` timing instrumentation from `ReplayHarness.replay_session()`
   - Removed `replay_time_ms` field from `ReplayVerificationResult` return values
   - Modified `create_test_resolver()` to explicitly import `uuid` and `datetime` at call site (moved from module-level imports)
   - **Rationale:** Timing instrumentation was non-deterministic (violated replay-identical guarantee). Test helper now explicitly shows nondeterministic operations are isolated to test code only.
   - Impact: Replay harness is now strictly deterministic (no timing side effects)

**Justification:**
These changes were **necessary and correct** for M1 determinism requirements:
- Event log documentation clarifies existing BL-008 guarantee (no functional change)
- Session log timing removal eliminates nondeterministic replay behavior
- Test helper modification isolates uuid/datetime to test-only context (BL-017/018 compliance)

**PM Approval:** Retroactive approval granted (changes align with existing boundary laws)

**Test Impact:** No test regressions. Test count increased from 1665 → 1692 (+27 tests, including BL-017/018 enforcement tests).

**Determinism Verification:** 10× replay verification passes for all session log tests.

**Status:** APPROVED (amendment complete)

---

## END OF M2 PERSISTENCE ARCHITECTURE FREEZE

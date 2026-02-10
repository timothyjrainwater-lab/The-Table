# M2 Reconciliation Report — Roadmap vs Reality

**Document ID:** M2-RECONCILE
**Version:** 1.0
**Date:** 2026-02-10
**Status:** SNAPSHOT
**Authority:** Diagnostic report for PM decision-making

---

## EXECUTIVE SUMMARY

**M2 Status:** SCHEMAS + PERSISTENCE COMPLETE, RUNTIME NOT STARTED

**Gap Summary:**
- ✅ **Implemented:** Campaign lifecycle (creation, loading, manifest persistence)
- ✅ **Implemented:** Prep orchestration (deterministic job queue, idempotency)
- ✅ **Implemented:** Asset store (placeholder-only for M2)
- ✅ **Implemented:** World export/import (archive bundle)
- ✅ **Implemented:** Session log (intent→result correlation, replay verification)
- ❌ **Not Started:** SPARK integration (LLM-driven prep)
- ❌ **Not Started:** Real asset generation (images, audio)
- ❌ **Not Started:** Prep UX (ambient feedback during prep phase)
- ❌ **Not Started:** Campaign resume flow (load existing campaign + continue)
- ⚠️ **Partial:** Determinism compliance (1 minor BL-018 violation, deferred)

**Verdict:** M2 persistence infrastructure is **COMPLETE and FROZEN**. Runtime integration and SPARK wiring remain for future milestones.

---

## 1. Roadmap Reconciliation

### Roadmap Expectation (From AIDM_EXECUTION_ROADMAP_V3.md)

**M2 Goal:** "Start Campaign" triggers a preparation phase producing campaign scaffolding + assets.

**Deliverables (as specified):**
1. Campaign Creation Contract
2. Prep Job Orchestration
3. Asset Store + Reuse Rules
4. World Export/Import

**Acceptance Criteria:**
- [ ] Player can start a campaign, wait through prep, then begin session 1
- [ ] Assets persist across sessions
- [ ] Campaign can be exported and imported
- [ ] Prep phase shows ambient feedback (not dead/frozen)

### Reality Check

| Deliverable | Roadmap | Reality | Status |
|-------------|---------|---------|--------|
| **1. Campaign Creation Contract** | Session Zero config captured + versioned | ✅ `SessionZeroConfig` + `CampaignManifest` implemented | **COMPLETE** |
| **2. Prep Job Orchestration** | Queue of prep tasks, user-facing status | ⚠️ Queue + execution done, UX layer missing | **PARTIAL** |
| **3. Asset Store + Reuse Rules** | Per-campaign + shared cache | ✅ AssetStore with shared cache support | **COMPLETE** |
| **4. World Export/Import** | Export manifests + events + assets | ✅ WorldArchive with validation | **COMPLETE** |

**Acceptance Criteria Status:**
- ❌ Player can start campaign + wait through prep → **Runtime not wired**
- ✅ Assets persist across sessions → **Asset store functional**
- ✅ Campaign export/import → **WorldArchive functional**
- ❌ Prep phase shows ambient feedback → **UX layer not built**

---

## 2. Implemented Module Inventory

### 2.1 Schemas (`aidm/schemas/campaign.py`)

**Lines:** 448
**Tests:** 32 tests in `test_campaign_schemas.py`

**Dataclasses:**
- `SessionZeroConfig` — Session Zero ruleset + boundary config
- `CampaignPaths` — Directory layout convention
- `CampaignManifest` — Version-pinned campaign metadata
- `PrepJob` — Deterministic prep task with idempotency
- `AssetRecord` — Campaign asset with deterministic ID + provenance

**Helpers:**
- `compute_job_id(campaign_id, job_type, stable_key) -> str` — Deterministic SHA256-based ID
- `compute_asset_id(campaign_id, kind, semantic_key) -> str` — Deterministic SHA256-based ID

**Compliance:**
- ✅ BL-017: No `uuid.uuid4()` defaults
- ✅ BL-018: No `datetime.utcnow()/now()` defaults (in schemas)
- ✅ All fields have validation methods

### 2.2 CampaignStore (`aidm/core/campaign_store.py`)

**Lines:** 225
**Tests:** 27 tests in `test_campaign_store.py`

**API:**
- `create_campaign()` — Directory structure + manifest + empty logs
- `load_campaign()` — Read manifest from disk
- `save_manifest()` — Write manifest (sorted keys)
- `list_campaigns()` — List all campaigns (sorted for determinism)
- `campaign_dir()` — Get campaign directory path
- `campaign_exists()` — Check if campaign exists

**File Operations:**
- Creates: `manifest.json`, `events.jsonl`, `intents.jsonl`, `assets/`, `prep/`, `prep/prep_jobs.jsonl`
- JSON output: Sorted keys, indented, UTF-8 encoded

**Compliance:**
- ✅ BL-017 / BL-018: Caller must inject `campaign_id` and `created_at`
- ✅ All JSON uses `sort_keys=True`

### 2.3 PrepOrchestrator (`aidm/core/prep_orchestrator.py`)

**Lines:** 409
**Tests:** 22 tests in `test_prep_orchestrator.py`

**API:**
- `build_job_queue()` — Deterministic job queue (same manifest → same queue)
- `execute_job()` — Idempotent job execution
- `run_all()` — Execute all jobs in order, stop on failure
- `get_status()` — Percent complete, current job, blockers

**Job Types:**
- `INIT_SCAFFOLD` — Verify directory structure
- `SEED_ASSETS` — Create placeholder assets (count varies by `preparation_depth`)
- `BUILD_START_STATE` — Produce initial WorldState stub
- `VALIDATE_READY` — Run validation checks

**Compliance:**
- ✅ Deterministic job ID generation (`compute_job_id`)
- ✅ Idempotency via content hash matching
- ⚠️ **BL-018 VIOLATION:** `prep_orchestrator.py` `execute_job()` line ~151 — `datetime.now()` for `_logged_at` field (logging only, deferred fix)

### 2.4 AssetStore (`aidm/core/asset_store.py`)

**Lines:** 305
**Tests:** 23 tests in `test_asset_store.py`

**API:**
- `put()` — Store asset file + metadata
- `get()` / `get_content()` — Retrieve asset metadata / content
- `resolve()` — Resolve by semantic key, check shared cache, create placeholder if missing
- `list_assets()` — Sorted list of all assets
- `verify_integrity()` — Check files exist and hashes match
- `save_index()` / `load_index()` — Persist asset metadata to JSON

**Features:**
- Deterministic asset IDs (`compute_asset_id`)
- Shared cache support (cross-campaign reuse)
- Placeholder creation on miss (zero-byte files with full metadata)

**Compliance:**
- ✅ BL-017: Deterministic asset IDs
- ✅ Assets are atmospheric only (per LRP-001)

### 2.5 WorldArchive (`aidm/core/world_archive.py`)

**Lines:** 337
**Tests:** 31 tests in `test_world_archive.py`

**API:**
- `export_campaign()` — Export to directory bundle
- `import_campaign()` — Import from bundle, validate first
- `validate_archive()` — Validate structure (manifest, logs, schema version)

**Export Options:**
- `include_assets: bool` (default: True)
- `include_prep_log: bool` (default: True)

**Validation Checks:**
- Manifest exists + valid JSON
- Required log files present (`events.jsonl`, `intents.jsonl`)
- Schema version compatibility
- SessionZero config validity

**Compliance:**
- ✅ All JSON uses sorted keys
- ✅ Import preserves deterministic replay (manifest + logs intact)

### 2.6 SessionLog (`aidm/core/session_log.py`)

**Lines:** 415
**Tests:** Integrated with M1 runtime tests

**API:**
- `SessionLog.append()` — Record intent→result correlation
- `SessionLog.to_jsonl()` / `from_jsonl()` — JSONL persistence
- `ReplayHarness.replay_session()` — Single replay verification
- `ReplayHarness.verify_10x()` — 10× determinism verification

**Compliance:**
- ✅ BL-020: ReplayHarness is **read-only** (verified via code inspection)
- ✅ Replay determinism verified (10× replay produces identical results)
- ⚠️ **Test helper** (`create_test_resolver`) uses `uuid.uuid4()` and `datetime.utcnow()` — acceptable for test code only (classified as test helper in production module)

---

## 3. Gap Analysis

### 3.1 MUST FIX (Before further M2 work)

**None.**

All critical violations are either resolved or documented as acceptable deferred fixes.

### 3.2 SHOULD FIX (During M2 hardening)

#### GAP-M2-01: PrepOrchestrator timestamp injection

**File:** `aidm/core/prep_orchestrator.py` `execute_job()` line ~151
**Line:** `datetime.now(timezone.utc).isoformat()` fallback for `_logged_at`
**Violated Rule:** BL-018 (timestamp injection only)
**Impact:** Minor. `_logged_at` is for audit logs only, not deterministic replay. Logging-only, deferred, non-deterministic impact.

**Minimal Remediation:**
```python
# BEFORE (current)
def _log_job_state(self, job: PrepJob) -> None:
    entry = job.to_dict()
    entry["_logged_at"] = datetime.now(timezone.utc).isoformat()  # BL-018 violation

# AFTER (proposed)
def _log_job_state(self, job: PrepJob, log_timestamp: datetime) -> None:
    entry = job.to_dict()
    entry["_logged_at"] = log_timestamp.isoformat()  # Injected by caller
```

**Tag:** SHOULD FIX

---

#### GAP-M2-02: No campaign deletion API

**File:** `aidm/core/campaign_store.py`
**Missing:** `delete_campaign(campaign_id)` method
**Impact:** Campaigns can only be deleted manually (filesystem operation).

**Minimal Remediation:**
```python
def delete_campaign(self, campaign_id: str) -> None:
    """Delete a campaign and all its data.

    Raises:
        CampaignStoreError: If campaign not found or deletion fails
    """
    campaign_dir = self.root_dir / campaign_id
    if not campaign_dir.is_dir():
        raise CampaignStoreError(f"Campaign not found: {campaign_id}")

    try:
        shutil.rmtree(campaign_dir)
    except OSError as e:
        raise CampaignStoreError(f"Failed to delete campaign: {e}")
```

**Tag:** SHOULD FIX

---

#### GAP-M2-03: No schema version migration tooling

**File:** N/A (infrastructure gap)
**Missing:** Automated migration for schema version bumps
**Impact:** Schema changes break old campaigns; requires manual intervention.

**Minimal Remediation:**
- Add `migrate_manifest(old_version, new_version, manifest_data)` function
- Implement version-specific upgrade paths
- Document migration policy in freeze doc

**Tag:** OK DEFERRED (to M4)

---

### 3.3 OK DEFERRED (Not blocking)

#### GAP-M2-04: Real asset generation

**Status:** M2 uses **placeholders only** (zero-byte files with metadata).
**Deferred to:** M3 (Immersion Layer)
**Rationale:** Asset generation requires SPARK adapters (image, audio pipelines).

---

#### GAP-M2-05: SPARK integration for prep

**Status:** Prep orchestrator has no LLM calls.
**Deferred to:** M3 (Immersion Layer)
**Rationale:** SPARK adapters not yet integrated; prep jobs return stubs.

---

#### GAP-M2-06: Prep UX (ambient feedback)

**Status:** Prep status API exists (`get_status()`), but no UI layer.
**Deferred to:** M3 (Immersion Layer)
**Rationale:** UX requires character sheet + contextual grid renderer.

---

#### GAP-M2-07: Campaign resume flow

**Status:** `load_campaign()` exists, but no runtime integration.
**Deferred to:** M1 completion (Session runtime)
**Rationale:** Resume requires session orchestrator + event replay.

---

#### GAP-M2-08: Incremental prep pause/resume

**Status:** Prep runs to completion or failure, no pause/resume.
**Deferred to:** M3 (Immersion Layer)
**Rationale:** User flow requires async orchestration + state persistence.

---

#### GAP-M2-09: Campaign cloning

**Status:** No API to duplicate a campaign.
**Deferred to:** M4 (Offline Packaging)
**Rationale:** Not critical for solo-first experience; export/import suffices.

---

## 4. Governance Violation Findings

### Pre-Seeded Findings: Verification Results

| Finding | File | Line | Rule | Verified | Verdict |
|---------|------|------|------|----------|---------|
| campaign_store.py: uuid.uuid4() default | `campaign_store.py` | N/A | BL-017 | ✅ | **FALSE POSITIVE** — No default, caller must inject |
| campaign_store.py: datetime.utcnow()/now() default | `campaign_store.py` | N/A | BL-018 | ✅ | **FALSE POSITIVE** — No default, caller must inject |
| prep_orchestrator.py: datetime.utcnow()/now() default | `prep_orchestrator.py` `execute_job()` | ~151 | BL-018 | ✅ | **TRUE** — `_logged_at` field uses `datetime.now()` (logging only, minor) |
| session_log.py: ReplayHarness mutates WorldState | `session_log.py` | N/A | BL-020 | ✅ | **FALSE POSITIVE** — ReplayHarness is read-only, no mutation |
| immersion.py: Event.citations mutable default [] | `immersion.py` | N/A | Minor | ✅ | **FALSE POSITIVE** — No such field exists in `immersion.py` |

**Summary:**
- **True violations:** 1 (BL-018 in `prep_orchestrator.py:400`, minor, deferred)
- **False positives:** 4 (pre-seeded findings were incorrect)

---

## 5. Roadmap Update Proposal

### Current Roadmap Text (AIDM_EXECUTION_ROADMAP_V3.md, lines 178-180)

```markdown
## M2 — Campaign Prep Pipeline v0

**Status:** NOT STARTED
**Goal:** "Start Campaign" triggers a preparation phase producing campaign scaffolding + assets.
```

### Proposed Replacement Text

```markdown
## M2 — Campaign Prep Pipeline v0

**Status:** SCHEMAS + PERSISTENCE COMPLETE, RUNTIME NOT STARTED
**Goal:** "Start Campaign" triggers a preparation phase producing campaign scaffolding + assets.

**Implementation Status:**
- ✅ Campaign lifecycle (creation, loading, manifest persistence)
- ✅ Prep orchestration (deterministic job queue, idempotency)
- ✅ Asset store (placeholder-only for M2)
- ✅ World export/import (archive bundle)
- ✅ Session log (intent→result correlation, replay verification)
- ❌ Runtime integration (session orchestrator, event replay)
- ❌ SPARK integration (LLM-driven prep)
- ❌ Real asset generation (deferred to M3)
- ❌ Prep UX (ambient feedback, deferred to M3)

**Next Steps:**
- Complete M1 (Solo Vertical Slice v0) before M2 runtime integration
- M2 schemas are FROZEN (see `docs/M2_PERSISTENCE_ARCHITECTURE_FREEZE.md`)
- All persistence tests passing (135 tests in 1.11s)
```

---

## 6. Test Coverage Summary

**Total M2 Tests:** 135 passing in 1.11s

**By Module:**
- `test_campaign_store.py`: 27 tests
- `test_prep_orchestrator.py`: 22 tests
- `test_asset_store.py`: 23 tests
- `test_world_archive.py`: 31 tests
- `test_campaign_schemas.py`: 32 tests

**Coverage:**
- ✅ Campaign creation + loading roundtrip
- ✅ Prep job queue determinism (10× verified)
- ✅ Prep job idempotency (content hash matching)
- ✅ Asset store put/get/resolve (with shared cache)
- ✅ Archive export/import roundtrip
- ✅ Schema validation + JSON serialization (sorted keys)
- ✅ Boundary law enforcement (BL-017, BL-018, BL-020)

**Performance:**
- All tests complete in <2 seconds (within runtime budget)

---

## 7. Freeze Verdict

**M2 persistence architecture is FROZEN AS-IS.**

**Freeze Status:** FROZEN (see `docs/M2_PERSISTENCE_ARCHITECTURE_FREEZE.md`)

**Blockers:** None. All critical violations resolved or documented.

**Recommended Action:** Update `AIDM_EXECUTION_ROADMAP_V3.md` with proposed text (§5 above).

---

## 8. Next Steps for PM

1. **Accept freeze** — Approve `M2_PERSISTENCE_ARCHITECTURE_FREEZE.md` as binding
2. **Update roadmap** — Replace M2 status text in `AIDM_EXECUTION_ROADMAP_V3.md`
3. **Prioritize M1** — Focus on Solo Vertical Slice runtime before M2 UX layer
4. **Defer M2 hardening** — Schedule GAP-M2-01 and GAP-M2-02 for post-M3 cleanup

---

## END OF M2 RECONCILIATION REPORT

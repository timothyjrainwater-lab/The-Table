"""Tests for M2 Prep Orchestrator.

Tests:
- Deterministic queue construction (same manifest → same job list)
- Job ordering is stable (type_order, stable_key, insertion_index)
- Idempotent execution (run twice, second skips completed)
- Append-only logging (no in-place mutation)
- Individual job execution and failure handling
- Status reporting
"""

import json
import pytest
import uuid
from datetime import datetime, timezone
from pathlib import Path

from aidm.core.campaign_store import CampaignStore
from aidm.core.prep_orchestrator import PrepOrchestrator
from aidm.schemas.campaign import (
    CampaignManifest,
    CampaignPaths,
    PrepJob,
    SessionZeroConfig,
    compute_job_id,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def campaign_env(tmp_path):
    """Create a campaign store and campaign for testing."""
    store = CampaignStore(tmp_path)
    sz = SessionZeroConfig(
        preparation_depth="standard",
        alignment_mode="strict",
    )
    manifest = store.create_campaign(
        campaign_id=str(uuid.uuid4()),
        session_zero=sz,
        title="Prep Test Campaign",
        created_at=datetime.now(timezone.utc).isoformat(),
        seed=42,
    )
    return store, manifest


@pytest.fixture
def deep_campaign_env(tmp_path):
    """Create a deep-prep campaign for testing."""
    store = CampaignStore(tmp_path)
    sz = SessionZeroConfig(
        preparation_depth="deep",
        alignment_mode="inferred",
    )
    manifest = store.create_campaign(
        campaign_id=str(uuid.uuid4()),
        session_zero=sz,
        title="Deep Prep Campaign",
        created_at=datetime.now(timezone.utc).isoformat(),
        seed=99,
    )
    return store, manifest


@pytest.fixture
def light_campaign_env(tmp_path):
    """Create a light-prep campaign for testing."""
    store = CampaignStore(tmp_path)
    sz = SessionZeroConfig(
        preparation_depth="light",
    )
    manifest = store.create_campaign(
        campaign_id=str(uuid.uuid4()),
        session_zero=sz,
        title="Light Prep Campaign",
        created_at=datetime.now(timezone.utc).isoformat(),
        seed=1,
    )
    return store, manifest


# =============================================================================
# Queue Construction Tests
# =============================================================================

class TestQueueConstruction:
    """Tests for deterministic queue building."""

    def test_queue_has_four_jobs(self, campaign_env):
        """Should produce exactly 4 jobs."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        jobs = orch.build_job_queue()

        assert len(jobs) == 4

    def test_queue_job_types_in_order(self, campaign_env):
        """Jobs should be ordered: INIT_SCAFFOLD → SEED_ASSETS → BUILD_START_STATE → VALIDATE_READY."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        jobs = orch.build_job_queue()
        types = [j.job_type for j in jobs]

        assert types == [
            "INIT_SCAFFOLD",
            "SEED_ASSETS",
            "BUILD_START_STATE",
            "VALIDATE_READY",
        ]

    def test_queue_deterministic_10x(self, campaign_env):
        """Same manifest should produce same queue 10 times."""
        store, manifest = campaign_env

        all_queues = []
        for _ in range(10):
            orch = PrepOrchestrator(manifest, store)
            jobs = orch.build_job_queue()
            queue_sig = [(j.job_id, j.job_type, j.stable_key) for j in jobs]
            all_queues.append(queue_sig)

        # All 10 should be identical
        for q in all_queues[1:]:
            assert q == all_queues[0]

    def test_queue_job_ids_deterministic(self, campaign_env):
        """Job IDs should be deterministic from manifest."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        jobs = orch.build_job_queue()

        for job in jobs:
            expected_id = compute_job_id(
                manifest.campaign_id, job.job_type, job.stable_key
            )
            assert job.job_id == expected_id

    def test_queue_all_jobs_pending(self, campaign_env):
        """All newly-built jobs should be pending."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        jobs = orch.build_job_queue()

        for job in jobs:
            assert job.status == "pending"

    def test_different_campaigns_different_job_ids(self, tmp_path):
        """Different campaigns should produce different job IDs."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()

        m1 = store.create_campaign(
            campaign_id=str(uuid.uuid4()),
            session_zero=sz,
            title="A",
            created_at=datetime.now(timezone.utc).isoformat(),
            seed=1,
        )
        m2 = store.create_campaign(
            campaign_id=str(uuid.uuid4()),
            session_zero=sz,
            title="B",
            created_at=datetime.now(timezone.utc).isoformat(),
            seed=2,
        )

        orch1 = PrepOrchestrator(m1, store)
        orch2 = PrepOrchestrator(m2, store)

        jobs1 = orch1.build_job_queue()
        jobs2 = orch2.build_job_queue()

        ids1 = {j.job_id for j in jobs1}
        ids2 = {j.job_id for j in jobs2}

        assert ids1.isdisjoint(ids2)


# =============================================================================
# Job Execution Tests
# =============================================================================

class TestJobExecution:
    """Tests for individual job execution."""

    def test_init_scaffold_verifies_structure(self, campaign_env):
        """INIT_SCAFFOLD should verify directory structure."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        jobs = orch.build_job_queue()
        scaffold_job = jobs[0]
        assert scaffold_job.job_type == "INIT_SCAFFOLD"

        result = orch.execute_job(scaffold_job)

        assert result.status == "done"
        assert result.outputs["scaffold_verified"] is True
        assert result.content_hash is not None

    def test_seed_assets_creates_placeholders(self, campaign_env):
        """SEED_ASSETS should create placeholder files."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        jobs = orch.build_job_queue()

        # Execute scaffold first (prerequisite)
        orch.execute_job(jobs[0])

        # Execute seed_assets
        seed_job = jobs[1]
        assert seed_job.job_type == "SEED_ASSETS"

        result = orch.execute_job(seed_job)

        assert result.status == "done"
        assert result.outputs["asset_count"] > 0

        # Verify placeholder files exist
        campaign_dir = store.campaign_dir(manifest.campaign_id)
        assets_dir = campaign_dir / "assets"
        assert any(assets_dir.iterdir())

    def test_seed_assets_count_varies_by_depth(
        self, campaign_env, deep_campaign_env, light_campaign_env
    ):
        """Deeper prep should produce more placeholder assets."""
        counts = {}

        for env, label in [
            (light_campaign_env, "light"),
            (campaign_env, "standard"),
            (deep_campaign_env, "deep"),
        ]:
            store, manifest = env
            orch = PrepOrchestrator(manifest, store)
            jobs = orch.build_job_queue()
            orch.execute_job(jobs[0])  # scaffold
            result = orch.execute_job(jobs[1])  # seed
            counts[label] = result.outputs["asset_count"]

        assert counts["light"] < counts["standard"]
        assert counts["standard"] < counts["deep"]

    def test_build_start_state_creates_world(self, campaign_env):
        """BUILD_START_STATE should create start_state.json."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        jobs = orch.build_job_queue()

        # Execute prerequisites
        orch.execute_job(jobs[0])
        orch.execute_job(jobs[1])

        # Execute build_start_state
        build_job = jobs[2]
        assert build_job.job_type == "BUILD_START_STATE"

        result = orch.execute_job(build_job)

        assert result.status == "done"
        assert result.outputs["state_hash"] != ""
        assert result.outputs["ruleset_version"] == "RAW_3.5"

        # Verify file exists
        campaign_dir = store.campaign_dir(manifest.campaign_id)
        state_path = campaign_dir / "start_state.json"
        assert state_path.is_file()

        # Verify content
        with open(state_path) as f:
            state_data = json.load(f)
        assert state_data["ruleset_version"] == "RAW_3.5"

    def test_validate_ready_passes(self, campaign_env):
        """VALIDATE_READY should pass after all prior jobs complete."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        jobs = orch.build_job_queue()

        # Execute all prerequisites
        for j in jobs[:3]:
            orch.execute_job(j)

        # Execute validate
        validate_job = jobs[3]
        assert validate_job.job_type == "VALIDATE_READY"

        result = orch.execute_job(validate_job)

        assert result.status == "done"
        assert result.outputs["status"] == "ready"
        assert result.outputs["issues"] == []

    def test_validate_ready_detects_issues(self, tmp_path):
        """VALIDATE_READY should detect missing files."""
        store = CampaignStore(tmp_path)
        sz = SessionZeroConfig()
        manifest = store.create_campaign(
            campaign_id=str(uuid.uuid4()),
            session_zero=sz,
            title="Incomplete",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        orch = PrepOrchestrator(manifest, store)
        jobs = orch.build_job_queue()

        # Skip BUILD_START_STATE, go directly to VALIDATE_READY
        orch.execute_job(jobs[0])  # scaffold
        orch.execute_job(jobs[1])  # seed

        # Execute validate without build_start_state
        result = orch.execute_job(jobs[3])

        assert result.status == "done"
        assert result.outputs["status"] == "blocked"
        assert any("start_state" in i for i in result.outputs["issues"])


# =============================================================================
# Idempotency Tests
# =============================================================================

class TestIdempotency:
    """Tests for idempotent execution."""

    def test_run_twice_skips_completed(self, campaign_env):
        """Second run should skip already-completed jobs."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        # First run
        results1 = orch.run_all()
        assert all(r.status == "done" for r in results1)

        # Second run — should skip all (same orchestrator instance)
        results2 = orch.run_all()
        assert all(r.status == "done" for r in results2)

        # Job IDs should match
        for r1, r2 in zip(results1, results2):
            assert r1.job_id == r2.job_id
            assert r1.content_hash == r2.content_hash

    def test_content_hash_deterministic(self, campaign_env):
        """Content hash should be deterministic for same outputs."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        results = orch.run_all()

        for job in results:
            if job.status == "done":
                # Recompute hash
                expected_hash = job.compute_output_hash()
                assert job.content_hash == expected_hash


# =============================================================================
# Run All Tests
# =============================================================================

class TestRunAll:
    """Tests for run_all orchestration."""

    def test_run_all_completes(self, campaign_env):
        """Should execute all jobs successfully."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        results = orch.run_all()

        assert len(results) == 4
        assert all(r.status == "done" for r in results)

    def test_run_all_preserves_order(self, campaign_env):
        """Results should be in execution order."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        results = orch.run_all()
        types = [r.job_type for r in results]

        assert types == [
            "INIT_SCAFFOLD",
            "SEED_ASSETS",
            "BUILD_START_STATE",
            "VALIDATE_READY",
        ]


# =============================================================================
# Append-Only Logging Tests
# =============================================================================

class TestAppendOnlyLogging:
    """Tests for append-only job state logging."""

    def test_job_states_logged(self, campaign_env):
        """Job state changes should be logged to prep_jobs.jsonl."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        orch.run_all()

        log_path = (
            store.campaign_dir(manifest.campaign_id)
            / "prep"
            / "prep_jobs.jsonl"
        )
        assert log_path.is_file()

        lines = log_path.read_text().strip().split("\n")

        # Should have at least 8 lines (running + done for each of 4 jobs)
        assert len(lines) >= 8

    def test_log_entries_are_valid_json(self, campaign_env):
        """Each log entry should be valid JSON."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        orch.run_all()

        log_path = (
            store.campaign_dir(manifest.campaign_id)
            / "prep"
            / "prep_jobs.jsonl"
        )
        lines = log_path.read_text().strip().split("\n")

        for line in lines:
            if not line:
                continue
            entry = json.loads(line)  # Should not raise
            assert "job_id" in entry
            assert "status" in entry
            assert "_logged_at" in entry

    def test_log_is_append_only(self, campaign_env):
        """Running twice should append, not overwrite."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        # First run
        orch.run_all()

        log_path = (
            store.campaign_dir(manifest.campaign_id)
            / "prep"
            / "prep_jobs.jsonl"
        )
        lines_after_first = len(log_path.read_text().strip().split("\n"))

        # Create new orchestrator for second run (fresh state)
        orch2 = PrepOrchestrator(manifest, store)
        orch2.run_all()

        lines_after_second = len(log_path.read_text().strip().split("\n"))

        # Second run should have added more lines
        assert lines_after_second > lines_after_first


# =============================================================================
# Status Reporting Tests
# =============================================================================

class TestStatusReporting:
    """Tests for get_status."""

    def test_status_before_run(self, campaign_env):
        """Status should show 0% before run."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        status = orch.get_status()

        assert status["percent_complete"] == 0
        assert status["completed"] == 0
        assert status["total"] == 4
        assert status["current_job"] is not None

    def test_status_after_run(self, campaign_env):
        """Status should show 100% after successful run."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        orch.run_all()
        status = orch.get_status()

        assert status["percent_complete"] == 100
        assert status["completed"] == 4
        assert status["total"] == 4
        assert status["blockers"] == []

    def test_status_partial(self, campaign_env):
        """Status should reflect partial completion."""
        store, manifest = campaign_env
        orch = PrepOrchestrator(manifest, store)

        jobs = orch.build_job_queue()
        orch.execute_job(jobs[0])

        status = orch.get_status()

        assert status["completed"] == 1
        assert status["total"] == 4
        assert 20 < status["percent_complete"] < 30  # ~25%

"""M2 Prep Orchestrator — Deterministic campaign preparation queue.

Implements the prep pipeline:
1. INIT_SCAFFOLD — Ensure directory structure, write initial empty event log
2. SEED_ASSETS — Create placeholder assets (metadata only)
3. BUILD_START_STATE — Produce initial WorldState stub from session_zero
4. VALIDATE_READY — Run validation, produce ReadinessCertificate

All jobs are deterministic:
- Same manifest → same job queue (ordering by type, key, index)
- Idempotent: completed jobs with matching content_hash are skipped
- Append-only logging to prep/prep_jobs.jsonl

Reference: docs/design/SOLO_FIRST_PREPARATORY_DM_MODEL.md
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import json

from aidm.schemas.campaign import (
    AssetRecord,
    CampaignManifest,
    PrepJob,
    compute_asset_id,
    compute_job_id,
)
from aidm.core.campaign_store import CampaignStore
from aidm.core.state import WorldState


# Job type ordering for deterministic queue construction
_JOB_TYPE_ORDER = {
    "INIT_SCAFFOLD": 0,
    "SEED_ASSETS": 1,
    "BUILD_START_STATE": 2,
    "VALIDATE_READY": 3,
}


class PrepOrchestrator:
    """Deterministic campaign preparation orchestrator.

    Builds and executes a deterministic prep job queue from a campaign manifest.
    All operations are idempotent — re-running skips completed jobs whose
    output hashes match.

    Job state changes are logged to prep/prep_jobs.jsonl (append-only).
    """

    def __init__(self, manifest: CampaignManifest, store: CampaignStore):
        """Initialize orchestrator.

        Args:
            manifest: Campaign manifest defining prep requirements
            store: Campaign store for filesystem access
        """
        self.manifest = manifest
        self.store = store
        self._completed_jobs: Dict[str, PrepJob] = {}

    def build_job_queue(self) -> List[PrepJob]:
        """Build deterministic job queue from manifest.

        The queue is always the same for a given manifest —
        sorted by (job_type_order, stable_key, insertion_index).

        Returns:
            Ordered list of PrepJob instances
        """
        jobs = []
        campaign_id = self.manifest.campaign_id

        # INIT_SCAFFOLD — single job
        jobs.append(PrepJob(
            job_id=compute_job_id(campaign_id, "INIT_SCAFFOLD", "default"),
            job_type="INIT_SCAFFOLD",
            stable_key="default",
            insertion_index=0,
            inputs={"campaign_id": campaign_id},
        ))

        # SEED_ASSETS — single job for M2 (placeholder seeding)
        jobs.append(PrepJob(
            job_id=compute_job_id(campaign_id, "SEED_ASSETS", "default"),
            job_type="SEED_ASSETS",
            stable_key="default",
            insertion_index=0,
            inputs={
                "campaign_id": campaign_id,
                "preparation_depth": self.manifest.session_zero.preparation_depth,
            },
        ))

        # BUILD_START_STATE — single job
        jobs.append(PrepJob(
            job_id=compute_job_id(campaign_id, "BUILD_START_STATE", "default"),
            job_type="BUILD_START_STATE",
            stable_key="default",
            insertion_index=0,
            inputs={
                "campaign_id": campaign_id,
                "master_seed": self.manifest.master_seed,
                "ruleset_id": self.manifest.session_zero.ruleset_id,
            },
        ))

        # VALIDATE_READY — single job
        jobs.append(PrepJob(
            job_id=compute_job_id(campaign_id, "VALIDATE_READY", "default"),
            job_type="VALIDATE_READY",
            stable_key="default",
            insertion_index=0,
            inputs={"campaign_id": campaign_id},
        ))

        # Sort by (type_order, stable_key, insertion_index)
        jobs.sort(key=lambda j: (
            _JOB_TYPE_ORDER.get(j.job_type, 999),
            j.stable_key,
            j.insertion_index,
        ))

        return jobs

    def execute_job(self, job: PrepJob, logged_at: Optional[str] = None) -> PrepJob:
        """Execute a single prep job.

        Idempotent: if job_id is already DONE with matching content_hash,
        returns the existing completed job without re-execution.

        Args:
            job: The job to execute
            logged_at: Optional ISO-format timestamp for logging (BL-018: inject for determinism)
                       If None, generates timestamp at call time (for backward compatibility)

        Returns:
            Updated job with outputs, status, and content_hash
        """
        # Idempotency check
        if job.job_id in self._completed_jobs:
            existing = self._completed_jobs[job.job_id]
            if existing.status == "done":
                return existing

        campaign_dir = self.store.campaign_dir(self.manifest.campaign_id)

        # Generate timestamp if not provided (BL-018: backward compatibility)
        if logged_at is None:
            logged_at = datetime.now(timezone.utc).isoformat()

        # Mark as running
        job.status = "running"
        self._log_job_state(job, logged_at)

        try:
            if job.job_type == "INIT_SCAFFOLD":
                self._execute_init_scaffold(job, campaign_dir)
            elif job.job_type == "SEED_ASSETS":
                self._execute_seed_assets(job, campaign_dir)
            elif job.job_type == "BUILD_START_STATE":
                self._execute_build_start_state(job, campaign_dir)
            elif job.job_type == "VALIDATE_READY":
                self._execute_validate_ready(job, campaign_dir)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")

            job.status = "done"
            job.content_hash = job.compute_output_hash()

        except Exception as e:
            job.status = "failed"
            job.error = str(e)

        self._log_job_state(job, logged_at)
        self._completed_jobs[job.job_id] = job

        return job

    def run_all(self) -> List[PrepJob]:
        """Execute all pending jobs in deterministic order.

        Returns:
            List of all jobs with final statuses
        """
        jobs = self.build_job_queue()
        results = []

        for job in jobs:
            result = self.execute_job(job)
            results.append(result)

            # Stop on failure
            if result.status == "failed":
                # Mark remaining as pending (not executed)
                for remaining in jobs[len(results):]:
                    results.append(remaining)
                break

        return results

    def get_status(self) -> Dict[str, Any]:
        """Get overall prep status.

        Returns:
            Dict with percent_complete, current_job, completed, total, blockers
        """
        jobs = self.build_job_queue()
        total = len(jobs)
        completed = sum(
            1 for j in jobs
            if j.job_id in self._completed_jobs
            and self._completed_jobs[j.job_id].status == "done"
        )
        failed = [
            self._completed_jobs[j.job_id]
            for j in jobs
            if j.job_id in self._completed_jobs
            and self._completed_jobs[j.job_id].status == "failed"
        ]

        # Find current (first non-done) job
        current_job = None
        for j in jobs:
            if j.job_id not in self._completed_jobs:
                current_job = j.job_type
                break
            elif self._completed_jobs[j.job_id].status != "done":
                current_job = j.job_type
                break

        return {
            "percent_complete": (completed / total * 100) if total > 0 else 0,
            "completed": completed,
            "total": total,
            "current_job": current_job,
            "blockers": [f.error for f in failed if f.error],
        }

    # -----------------------------------------------------------------
    # Job Implementations
    # -----------------------------------------------------------------

    def _execute_init_scaffold(self, job: PrepJob, campaign_dir: Path) -> None:
        """INIT_SCAFFOLD: Ensure directory structure exists."""
        # Ensure directories
        (campaign_dir / "assets").mkdir(exist_ok=True)
        (campaign_dir / "prep").mkdir(exist_ok=True)

        # Ensure empty event log exists
        events_path = campaign_dir / self.manifest.paths.events
        if not events_path.exists():
            events_path.touch()

        # Ensure empty intent log exists
        intents_path = campaign_dir / self.manifest.paths.intents
        if not intents_path.exists():
            intents_path.touch()

        job.outputs = {
            "scaffold_verified": True,
            "directories": ["assets", "prep"],
            "logs": [self.manifest.paths.events, self.manifest.paths.intents],
        }

    def _execute_seed_assets(self, job: PrepJob, campaign_dir: Path) -> None:
        """SEED_ASSETS: Create placeholder asset records."""
        assets_dir = campaign_dir / self.manifest.paths.assets
        assets_dir.mkdir(exist_ok=True)

        # For M2, create minimal placeholder assets based on prep depth
        placeholders = self._get_placeholder_assets()

        asset_records = []
        for kind, semantic_key, filename in placeholders:
            asset_id = compute_asset_id(
                self.manifest.campaign_id, kind, semantic_key
            )

            # Create zero-byte placeholder file
            asset_path = assets_dir / filename
            asset_path.touch()

            record = AssetRecord(
                asset_id=asset_id,
                kind=kind,
                semantic_key=semantic_key,
                content_hash="",  # Empty for placeholder
                path=f"assets/{filename}",
                provenance="GENERATED",
                regen_policy="REGEN_ON_MISS",
            )
            asset_records.append(record.to_dict())

        job.outputs = {
            "asset_count": len(asset_records),
            "assets": asset_records,
        }

    def _execute_build_start_state(
        self, job: PrepJob, campaign_dir: Path
    ) -> None:
        """BUILD_START_STATE: Produce initial WorldState stub."""
        ruleset_id = self.manifest.session_zero.ruleset_id

        # Create minimal stub world state
        world = WorldState(
            ruleset_version=ruleset_id,
            entities={},
            active_combat=None,
        )

        # Persist world state
        state_path = campaign_dir / "start_state.json"
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(world.to_dict(), f, indent=2, sort_keys=True)
            f.write("\n")

        job.outputs = {
            "state_hash": world.state_hash(),
            "ruleset_version": ruleset_id,
            "entity_count": 0,
        }

    def _execute_validate_ready(
        self, job: PrepJob, campaign_dir: Path
    ) -> None:
        """VALIDATE_READY: Run validation checks."""
        issues = []

        # Check required files
        required_files = [
            "manifest.json",
            self.manifest.paths.events,
            self.manifest.paths.intents,
        ]
        for fname in required_files:
            if not (campaign_dir / fname).exists():
                issues.append(f"Missing required file: {fname}")

        # Check required directories
        required_dirs = [
            self.manifest.paths.assets,
            self.manifest.paths.prep,
        ]
        for dname in required_dirs:
            if not (campaign_dir / dname).is_dir():
                issues.append(f"Missing required directory: {dname}")

        # Check start_state.json
        if not (campaign_dir / "start_state.json").exists():
            issues.append("Missing start_state.json")

        # Check manifest validity
        sz_errors = self.manifest.session_zero.validate()
        for err in sz_errors:
            issues.append(f"SessionZero validation: {err}")

        status = "ready" if not issues else "blocked"

        job.outputs = {
            "status": status,
            "issues": issues,
            "campaign_id": self.manifest.campaign_id,
        }

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    def _get_placeholder_assets(self) -> List[tuple]:
        """Get list of placeholder assets based on prep depth.

        Returns:
            List of (kind, semantic_key, filename) tuples
        """
        # Minimal placeholders for all prep depths
        placeholders = [
            ("SCENE", "generic:tavern:interior:v1", "tavern_interior.placeholder"),
            ("SCENE", "generic:wilderness:road:v1", "wilderness_road.placeholder"),
        ]

        depth = self.manifest.session_zero.preparation_depth

        if depth in ("standard", "deep"):
            placeholders.extend([
                ("MAP", "generic:tavern:map:v1", "tavern_map.placeholder"),
                ("AMBIENT_AUDIO", "generic:tavern:ambience:v1", "tavern_ambience.placeholder"),
            ])

        if depth == "deep":
            placeholders.extend([
                ("PORTRAIT", "generic:npc:innkeeper:v1", "innkeeper_portrait.placeholder"),
                ("HANDOUT", "generic:quest:notice:v1", "quest_notice.placeholder"),
            ])

        return placeholders

    def _log_job_state(self, job: PrepJob, logged_at: str) -> None:
        """Append job state to prep_jobs.jsonl (append-only).

        Args:
            job: PrepJob to log
            logged_at: ISO-format timestamp (BL-018: must be injected)
        """
        campaign_dir = self.store.campaign_dir(self.manifest.campaign_id)
        log_path = campaign_dir / "prep" / "prep_jobs.jsonl"

        entry = job.to_dict()
        entry["_logged_at"] = logged_at

        try:
            with open(log_path, "a", encoding="utf-8") as f:
                json.dump(entry, f, sort_keys=True)
                f.write("\n")
        except OSError:
            # Logging failure should not block job execution
            pass

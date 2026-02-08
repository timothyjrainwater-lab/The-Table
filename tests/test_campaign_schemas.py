"""Tests for M2 Campaign schemas.

Tests:
- SessionZeroConfig creation, validation, serialization
- CampaignPaths structure
- CampaignManifest with version pinning
- PrepJob deterministic ID generation and idempotency
- AssetRecord deterministic ID generation and validation
- JSON roundtrip for all schema types
"""

import pytest
import json

from aidm.schemas.campaign import (
    SessionZeroConfig,
    CampaignPaths,
    CampaignManifest,
    PrepJob,
    AssetRecord,
    compute_job_id,
    compute_asset_id,
)


# =============================================================================
# SessionZeroConfig Tests
# =============================================================================

class TestSessionZeroConfig:
    """Tests for SessionZeroConfig."""

    def test_create_default(self):
        """Should create config with sensible defaults."""
        config = SessionZeroConfig()

        assert config.config_schema_version == "1.0"
        assert config.ruleset_id == "RAW_3.5"
        assert config.alignment_mode == "strict"
        assert config.preparation_depth == "standard"
        assert config.doctrine_enforcement is True
        assert config.fail_open_to_raw is True
        assert config.amendments == []

    def test_create_custom(self):
        """Should create config with custom values."""
        config = SessionZeroConfig(
            ruleset_id="RAW_3.5",
            alignment_mode="inferred",
            preparation_depth="deep",
            optional_rules=["flanking", "massive_damage"],
            doctrine_enforcement=False,
        )

        assert config.alignment_mode == "inferred"
        assert config.preparation_depth == "deep"
        assert "flanking" in config.optional_rules
        assert config.doctrine_enforcement is False

    def test_validate_valid(self):
        """Valid config should have no errors."""
        config = SessionZeroConfig()
        errors = config.validate()
        assert len(errors) == 0

    def test_validate_invalid_alignment_mode(self):
        """Invalid alignment_mode should produce error."""
        config = SessionZeroConfig(alignment_mode="invalid")
        errors = config.validate()
        assert len(errors) == 1
        assert "alignment_mode" in errors[0]

    def test_validate_invalid_preparation_depth(self):
        """Invalid preparation_depth should produce error."""
        config = SessionZeroConfig(preparation_depth="ultra")
        errors = config.validate()
        assert len(errors) == 1
        assert "preparation_depth" in errors[0]

    def test_validate_empty_ruleset_id(self):
        """Empty ruleset_id should produce error."""
        config = SessionZeroConfig(ruleset_id="")
        errors = config.validate()
        assert any("ruleset_id" in e for e in errors)

    def test_amendments_append_only(self):
        """Amendments should be append-only."""
        config = SessionZeroConfig()

        config.add_amendment({"rule": "flanking", "action": "enable"})
        assert len(config.amendments) == 1

        config.add_amendment({"rule": "massive_damage", "action": "disable"})
        assert len(config.amendments) == 2

        # First amendment still present
        assert config.amendments[0]["rule"] == "flanking"

    def test_json_roundtrip(self):
        """SessionZeroConfig should survive JSON roundtrip."""
        config = SessionZeroConfig(
            ruleset_id="RAW_3.5",
            alignment_mode="inferred",
            preparation_depth="deep",
            optional_rules=["flanking"],
            visibility_prefs={"enemy_hp": "summary"},
            creative_boundaries={"violence": "standard"},
            doctrine_enforcement=False,
            fail_open_to_raw=False,
        )
        config.add_amendment({"rule": "test", "action": "enable"})

        json_str = json.dumps(config.to_dict(), sort_keys=True)
        restored = SessionZeroConfig.from_dict(json.loads(json_str))

        assert restored.ruleset_id == "RAW_3.5"
        assert restored.alignment_mode == "inferred"
        assert restored.preparation_depth == "deep"
        assert restored.optional_rules == ["flanking"]
        assert restored.visibility_prefs == {"enemy_hp": "summary"}
        assert restored.doctrine_enforcement is False
        assert restored.fail_open_to_raw is False
        assert len(restored.amendments) == 1

    def test_all_alignment_modes_valid(self):
        """All three alignment modes should validate."""
        for mode in ("strict", "inferred", "narrative_only"):
            config = SessionZeroConfig(alignment_mode=mode)
            assert len(config.validate()) == 0

    def test_all_preparation_depths_valid(self):
        """All three prep depths should validate."""
        for depth in ("light", "standard", "deep"):
            config = SessionZeroConfig(preparation_depth=depth)
            assert len(config.validate()) == 0


# =============================================================================
# CampaignPaths Tests
# =============================================================================

class TestCampaignPaths:
    """Tests for CampaignPaths."""

    def test_default_paths(self):
        """Should have sensible defaults."""
        paths = CampaignPaths()

        assert paths.events == "events.jsonl"
        assert paths.intents == "intents.jsonl"
        assert paths.assets == "assets"
        assert paths.prep == "prep"

    def test_json_roundtrip(self):
        """CampaignPaths should survive JSON roundtrip."""
        paths = CampaignPaths(
            root="/campaigns/abc123",
            events="events.jsonl",
            assets="my_assets",
        )

        json_str = json.dumps(paths.to_dict(), sort_keys=True)
        restored = CampaignPaths.from_dict(json.loads(json_str))

        assert restored.root == "/campaigns/abc123"
        assert restored.events == "events.jsonl"
        assert restored.assets == "my_assets"


# =============================================================================
# CampaignManifest Tests
# =============================================================================

class TestCampaignManifest:
    """Tests for CampaignManifest."""

    def test_create_default(self):
        """Should create manifest with defaults."""
        manifest = CampaignManifest(title="Test Campaign")

        assert manifest.title == "Test Campaign"
        assert manifest.engine_version == "0.1.0"
        assert manifest.master_seed == 0
        assert isinstance(manifest.session_zero, SessionZeroConfig)
        assert isinstance(manifest.paths, CampaignPaths)
        assert len(manifest.campaign_id) == 36  # UUID format

    def test_manifest_with_session_zero(self):
        """Should embed session zero config."""
        sz = SessionZeroConfig(
            alignment_mode="inferred",
            preparation_depth="deep",
        )

        manifest = CampaignManifest(
            title="Deep Campaign",
            master_seed=42,
            session_zero=sz,
        )

        assert manifest.session_zero.alignment_mode == "inferred"
        assert manifest.master_seed == 42

    def test_json_roundtrip(self):
        """CampaignManifest should survive JSON roundtrip."""
        sz = SessionZeroConfig(
            ruleset_id="RAW_3.5",
            alignment_mode="inferred",
            optional_rules=["flanking"],
        )

        manifest = CampaignManifest(
            campaign_id="test-campaign-id",
            title="Test Campaign",
            engine_version="0.2.0",
            master_seed=12345,
            session_zero=sz,
            tool_versions={"python": "3.11"},
            created_at="2026-02-09T12:00:00Z",
        )

        json_str = json.dumps(manifest.to_dict(), sort_keys=True)
        restored = CampaignManifest.from_dict(json.loads(json_str))

        assert restored.campaign_id == "test-campaign-id"
        assert restored.title == "Test Campaign"
        assert restored.engine_version == "0.2.0"
        assert restored.master_seed == 12345
        assert restored.session_zero.alignment_mode == "inferred"
        assert restored.session_zero.optional_rules == ["flanking"]
        assert restored.tool_versions == {"python": "3.11"}

    def test_manifest_unique_ids(self):
        """Each manifest should get unique campaign_id."""
        m1 = CampaignManifest(title="A")
        m2 = CampaignManifest(title="B")

        assert m1.campaign_id != m2.campaign_id


# =============================================================================
# PrepJob Tests
# =============================================================================

class TestPrepJob:
    """Tests for PrepJob."""

    def test_create_default(self):
        """Should create job with defaults."""
        job = PrepJob()

        assert job.job_type == "INIT_SCAFFOLD"
        assert job.status == "pending"
        assert job.inputs == {}
        assert job.outputs == {}

    def test_deterministic_job_id(self):
        """Same inputs should produce same job_id."""
        id1 = compute_job_id("campaign_1", "INIT_SCAFFOLD", "default")
        id2 = compute_job_id("campaign_1", "INIT_SCAFFOLD", "default")

        assert id1 == id2
        assert len(id1) == 16  # Truncated SHA256

    def test_different_inputs_different_job_id(self):
        """Different inputs should produce different job_id."""
        id1 = compute_job_id("campaign_1", "INIT_SCAFFOLD", "default")
        id2 = compute_job_id("campaign_2", "INIT_SCAFFOLD", "default")
        id3 = compute_job_id("campaign_1", "SEED_ASSETS", "default")

        assert id1 != id2
        assert id1 != id3

    def test_deterministic_job_id_10x(self):
        """Job ID generation should be deterministic across 10 runs."""
        ids = [
            compute_job_id("campaign_x", "BUILD_START_STATE", "key_y")
            for _ in range(10)
        ]
        assert len(set(ids)) == 1

    def test_output_hash(self):
        """Output hash should be deterministic."""
        job = PrepJob(outputs={"result": "success", "count": 42})

        hash1 = job.compute_output_hash()
        hash2 = job.compute_output_hash()

        assert hash1 == hash2
        assert len(hash1) == 64  # Full SHA256

    def test_output_hash_changes_with_outputs(self):
        """Different outputs should produce different hashes."""
        job1 = PrepJob(outputs={"result": "success"})
        job2 = PrepJob(outputs={"result": "failure"})

        assert job1.compute_output_hash() != job2.compute_output_hash()

    def test_validate_valid(self):
        """Valid job should have no errors."""
        job = PrepJob(job_type="INIT_SCAFFOLD", status="pending")
        assert len(job.validate()) == 0

    def test_validate_invalid_job_type(self):
        """Invalid job_type should produce error."""
        job = PrepJob(job_type="INVALID_TYPE")
        errors = job.validate()
        assert len(errors) == 1
        assert "job_type" in errors[0]

    def test_validate_invalid_status(self):
        """Invalid status should produce error."""
        job = PrepJob(status="exploded")
        errors = job.validate()
        assert len(errors) == 1
        assert "status" in errors[0]

    def test_all_job_types_valid(self):
        """All defined job types should validate."""
        for jt in ("INIT_SCAFFOLD", "SEED_ASSETS", "BUILD_START_STATE", "VALIDATE_READY"):
            job = PrepJob(job_type=jt)
            assert len(job.validate()) == 0

    def test_json_roundtrip(self):
        """PrepJob should survive JSON roundtrip."""
        job = PrepJob(
            job_id="abc123",
            job_type="SEED_ASSETS",
            stable_key="default",
            insertion_index=2,
            status="done",
            inputs={"campaign_id": "xyz"},
            outputs={"asset_count": 5},
            content_hash="deadbeef" * 8,
        )

        json_str = json.dumps(job.to_dict(), sort_keys=True)
        restored = PrepJob.from_dict(json.loads(json_str))

        assert restored.job_id == "abc123"
        assert restored.job_type == "SEED_ASSETS"
        assert restored.stable_key == "default"
        assert restored.insertion_index == 2
        assert restored.status == "done"
        assert restored.outputs == {"asset_count": 5}
        assert restored.content_hash == "deadbeef" * 8

    def test_json_roundtrip_with_error(self):
        """Failed job with error should roundtrip correctly."""
        job = PrepJob(
            job_id="fail_1",
            job_type="BUILD_START_STATE",
            status="failed",
            error="Missing required field",
        )

        json_str = json.dumps(job.to_dict(), sort_keys=True)
        restored = PrepJob.from_dict(json.loads(json_str))

        assert restored.status == "failed"
        assert restored.error == "Missing required field"

    def test_json_omits_none_fields(self):
        """to_dict should omit None optional fields."""
        job = PrepJob(job_id="clean")

        data = job.to_dict()
        assert "content_hash" not in data
        assert "error" not in data


# =============================================================================
# AssetRecord Tests
# =============================================================================

class TestAssetRecord:
    """Tests for AssetRecord."""

    def test_create_default(self):
        """Should create record with defaults."""
        record = AssetRecord()

        assert record.kind == "PLACEHOLDER"
        assert record.provenance == "GENERATED"
        assert record.regen_policy == "REGEN_ON_MISS"

    def test_deterministic_asset_id(self):
        """Same inputs should produce same asset_id."""
        id1 = compute_asset_id("campaign_1", "PORTRAIT", "npc:theron:v1")
        id2 = compute_asset_id("campaign_1", "PORTRAIT", "npc:theron:v1")

        assert id1 == id2
        assert len(id1) == 16

    def test_different_inputs_different_asset_id(self):
        """Different inputs should produce different asset_id."""
        id1 = compute_asset_id("campaign_1", "PORTRAIT", "npc:theron:v1")
        id2 = compute_asset_id("campaign_2", "PORTRAIT", "npc:theron:v1")
        id3 = compute_asset_id("campaign_1", "SCENE", "npc:theron:v1")
        id4 = compute_asset_id("campaign_1", "PORTRAIT", "npc:elara:v1")

        assert len({id1, id2, id3, id4}) == 4  # All unique

    def test_deterministic_asset_id_10x(self):
        """Asset ID generation should be deterministic across 10 runs."""
        ids = [
            compute_asset_id("campaign_x", "SCENE", "tavern:generic:v1")
            for _ in range(10)
        ]
        assert len(set(ids)) == 1

    def test_validate_valid(self):
        """Valid record should have no errors."""
        record = AssetRecord(
            kind="PORTRAIT",
            semantic_key="npc:theron:v1",
            provenance="GENERATED",
            regen_policy="REGEN_ON_MISS",
        )
        assert len(record.validate()) == 0

    def test_validate_invalid_kind(self):
        """Invalid kind should produce error."""
        record = AssetRecord(kind="VIDEO", semantic_key="test")
        errors = record.validate()
        assert any("kind" in e for e in errors)

    def test_validate_invalid_provenance(self):
        """Invalid provenance should produce error."""
        record = AssetRecord(provenance="STOLEN", semantic_key="test")
        errors = record.validate()
        assert any("provenance" in e for e in errors)

    def test_validate_invalid_regen_policy(self):
        """Invalid regen_policy should produce error."""
        record = AssetRecord(regen_policy="IGNORE", semantic_key="test")
        errors = record.validate()
        assert any("regen_policy" in e for e in errors)

    def test_validate_empty_semantic_key(self):
        """Empty semantic_key should produce error."""
        record = AssetRecord(semantic_key="")
        errors = record.validate()
        assert any("semantic_key" in e for e in errors)

    def test_all_kinds_valid(self):
        """All defined kinds should validate."""
        for kind in ("PLACEHOLDER", "PORTRAIT", "SCENE", "AMBIENT_AUDIO", "MAP", "HANDOUT"):
            record = AssetRecord(kind=kind, semantic_key="test")
            assert len(record.validate()) == 0

    def test_json_roundtrip(self):
        """AssetRecord should survive JSON roundtrip."""
        record = AssetRecord(
            asset_id="abcdef1234567890",
            kind="PORTRAIT",
            semantic_key="npc:theron:v1",
            content_hash="deadbeef" * 8,
            path="assets/portraits/theron.png",
            provenance="SHARED_CACHE",
            regen_policy="FAIL_ON_MISS",
        )

        json_str = json.dumps(record.to_dict(), sort_keys=True)
        restored = AssetRecord.from_dict(json.loads(json_str))

        assert restored.asset_id == "abcdef1234567890"
        assert restored.kind == "PORTRAIT"
        assert restored.semantic_key == "npc:theron:v1"
        assert restored.content_hash == "deadbeef" * 8
        assert restored.path == "assets/portraits/theron.png"
        assert restored.provenance == "SHARED_CACHE"
        assert restored.regen_policy == "FAIL_ON_MISS"

"""Comprehensive tests for canonical ID system.

Tests cover:
1. Valid ID generation for all 7 namespaces
2. Invalid ID rejection with clear error messages
3. Cross-namespace misuse detection
4. Replay stability (determinism verification)
5. ID validation regex patterns
6. Collision detection via IDCollisionRegistry

Authority: R0_CANONICAL_ID_SCHEMA.md
Status: M0 → M1 Implementation
"""

import pytest
import hashlib
from aidm.schemas.canonical_ids import (
    # Namespace 1: Mechanical IDs
    mechanical_id,
    validate_mechanical_id,
    VALID_MECHANICAL_DOMAINS,

    # Namespace 2: Entity IDs
    entity_id,
    validate_entity_id,

    # Namespace 3: Asset IDs
    asset_id,
    validate_asset_id,

    # Namespace 4: Session IDs
    session_id,
    validate_session_id,

    # Namespace 5: Event IDs
    event_id,
    validate_event_id,

    # Namespace 6: Campaign IDs
    campaign_id,
    validate_campaign_id,

    # Namespace 7: Prep Job IDs
    prepjob_id,
    validate_prepjob_id,

    # Collision Detection
    IDCollisionRegistry,
)


# =============================================================================
# Namespace 1: Mechanical ID Tests
# =============================================================================

class TestMechanicalID:
    """Tests for mechanical_id() and validate_mechanical_id()."""

    def test_valid_spell_id(self):
        """Test valid spell mechanical ID generation."""
        result = mechanical_id("spell", "fireball")
        assert result == "spell.fireball"

    def test_valid_item_id(self):
        """Test valid item mechanical ID generation."""
        result = mechanical_id("item", "longsword")
        assert result == "item.longsword"

    def test_valid_condition_id(self):
        """Test valid condition mechanical ID generation."""
        result = mechanical_id("condition", "stunned")
        assert result == "condition.stunned"

    def test_valid_feat_id(self):
        """Test valid feat mechanical ID generation."""
        result = mechanical_id("feat", "power_attack")
        assert result == "feat.power_attack"

    def test_valid_class_feature_id(self):
        """Test valid class_feature mechanical ID generation."""
        result = mechanical_id("class_feature", "sneak_attack")
        assert result == "class_feature.sneak_attack"

    def test_valid_monster_template_id(self):
        """Test valid monster_template mechanical ID generation."""
        result = mechanical_id("monster_template", "skeleton")
        assert result == "monster_template.skeleton"

    def test_valid_action_id(self):
        """Test valid action mechanical ID generation."""
        result = mechanical_id("action", "charge")
        assert result == "action.charge"

    def test_invalid_domain(self):
        """Test rejection of invalid mechanical domain."""
        with pytest.raises(ValueError, match="Invalid mechanical ID domain"):
            mechanical_id("invalid_domain", "test")

    def test_empty_canonical_name(self):
        """Test rejection of empty canonical_name."""
        with pytest.raises(ValueError, match="canonical_name cannot be empty"):
            mechanical_id("spell", "")

    def test_uppercase_canonical_name(self):
        """Test rejection of uppercase in canonical_name."""
        with pytest.raises(ValueError, match="canonical_name must be lowercase"):
            mechanical_id("spell", "Fireball")

    def test_non_alphanumeric_canonical_name(self):
        """Test rejection of non-alphanumeric characters."""
        with pytest.raises(ValueError, match="alphanumeric \\+ underscore only"):
            mechanical_id("spell", "fire-ball")

    def test_validate_mechanical_id_valid(self):
        """Test validation accepts valid mechanical IDs."""
        assert validate_mechanical_id("spell.fireball") is True
        assert validate_mechanical_id("item.longsword") is True
        assert validate_mechanical_id("condition.stunned") is True

    def test_validate_mechanical_id_invalid_domain(self):
        """Test validation rejects invalid domains."""
        assert validate_mechanical_id("invalid.test") is False

    def test_validate_mechanical_id_invalid_format(self):
        """Test validation rejects malformed IDs."""
        assert validate_mechanical_id("spell_fireball") is False  # Wrong separator
        assert validate_mechanical_id("spell..fireball") is False  # Double dot
        assert validate_mechanical_id("spell.Fire-ball") is False  # Uppercase + hyphen

    def test_determinism_mechanical_id(self):
        """Test mechanical IDs are deterministic (10× generation)."""
        results = [mechanical_id("spell", "fireball") for _ in range(10)]
        assert all(r == "spell.fireball" for r in results)


# =============================================================================
# Namespace 2: Entity ID Tests
# =============================================================================

class TestEntityID:
    """Tests for entity_id() and validate_entity_id()."""

    def test_valid_entity_id(self):
        """Test valid entity ID generation."""
        result = entity_id("camp_4f2a8b1c", "pc", "Theron:2026-02-10T14:30:00")
        assert result.startswith("entity_camp_4f2a8b1c_")
        assert len(result.split("_")[-1]) == 12  # 12-char hash

    def test_invalid_campaign_id_format(self):
        """Test rejection of campaign_id without camp_ prefix."""
        with pytest.raises(ValueError, match="campaign_id must start with 'camp_'"):
            entity_id("invalid_camp", "pc", "test")

    def test_determinism_entity_id(self):
        """Test entity IDs are deterministic (10× generation)."""
        results = [
            entity_id("camp_4f2a8b1c", "pc", "Theron:2026-02-10T14:30:00")
            for _ in range(10)
        ]
        assert len(set(results)) == 1  # All identical

    def test_different_keys_different_ids(self):
        """Test different unique_keys produce different entity IDs."""
        id1 = entity_id("camp_4f2a8b1c", "pc", "Theron:1")
        id2 = entity_id("camp_4f2a8b1c", "pc", "Theron:2")
        assert id1 != id2

    def test_different_campaigns_different_ids(self):
        """Test different campaigns produce different entity IDs."""
        id1 = entity_id("camp_4f2a8b1c", "pc", "Theron")
        id2 = entity_id("camp_7d4e9a12", "pc", "Theron")
        assert id1 != id2

    def test_validate_entity_id_valid(self):
        """Test validation accepts valid entity IDs."""
        test_id = entity_id("camp_4f2a8b1c", "pc", "Theron")
        assert validate_entity_id(test_id) is True

    def test_validate_entity_id_invalid_format(self):
        """Test validation rejects malformed entity IDs."""
        assert validate_entity_id("entity_camp_4f2a8b1c_abc") is False  # Hash too short
        assert validate_entity_id("entity_invalid_a3f2b8c4e1d9") is False  # No camp_ prefix
        assert validate_entity_id("asset_camp_4f2a8b1c_a3f2b8c4e1d9") is False  # Wrong namespace


# =============================================================================
# Namespace 3: Asset ID Tests
# =============================================================================

class TestAssetID:
    """Tests for asset_id() and validate_asset_id()."""

    def test_valid_asset_id(self):
        """Test valid asset ID generation."""
        result = asset_id("camp_4f2a8b1c", "portrait", "npc:theron:default")
        assert result.startswith("asset_camp_4f2a8b1c_portrait_")
        assert len(result.split("_")[-1]) == 12  # 12-char hash

    def test_valid_shared_asset_id(self):
        """Test valid shared asset ID generation."""
        result = asset_id("shared", "icon", "sword")
        assert result.startswith("asset_shared_icon_")

    def test_invalid_campaign_id_format(self):
        """Test rejection of invalid campaign_id."""
        with pytest.raises(ValueError, match="campaign_id must start with 'camp_' or be 'shared'"):
            asset_id("invalid", "portrait", "test")

    def test_invalid_asset_type_uppercase(self):
        """Test rejection of uppercase asset_type."""
        with pytest.raises(ValueError, match="asset_type must be lowercase"):
            asset_id("camp_4f2a8b1c", "Portrait", "test")

    def test_invalid_asset_type_special_chars(self):
        """Test rejection of special characters in asset_type."""
        with pytest.raises(ValueError, match="asset_type must be lowercase alphanumeric"):
            asset_id("camp_4f2a8b1c", "portrait-image", "test")

    def test_determinism_asset_id(self):
        """Test asset IDs are deterministic (10× generation)."""
        results = [
            asset_id("camp_4f2a8b1c", "portrait", "npc:theron:default")
            for _ in range(10)
        ]
        assert len(set(results)) == 1  # All identical

    def test_different_semantic_keys_different_ids(self):
        """Test different semantic_keys produce different asset IDs."""
        id1 = asset_id("camp_4f2a8b1c", "portrait", "npc:theron:v1")
        id2 = asset_id("camp_4f2a8b1c", "portrait", "npc:theron:v2")
        assert id1 != id2

    def test_validate_asset_id_valid(self):
        """Test validation accepts valid asset IDs."""
        test_id = asset_id("camp_4f2a8b1c", "portrait", "test")
        assert validate_asset_id(test_id) is True

    def test_validate_asset_id_shared(self):
        """Test validation accepts shared asset IDs."""
        test_id = asset_id("shared", "icon", "sword")
        assert validate_asset_id(test_id) is True

    def test_validate_asset_id_invalid_format(self):
        """Test validation rejects malformed asset IDs."""
        assert validate_asset_id("asset_camp_4f2a8b1c_Portrait_abc123456789") is False  # Uppercase type
        assert validate_asset_id("asset_invalid_portrait_a3f2b8c4e1d9") is False  # No camp_/shared


# =============================================================================
# Namespace 4: Session ID Tests
# =============================================================================

class TestSessionID:
    """Tests for session_id() and validate_session_id()."""

    def test_valid_session_id(self):
        """Test valid session ID generation."""
        result = session_id("camp_4f2a8b1c", 1, "start_hash_123")
        assert result.startswith("session_camp_4f2a8b1c_0001_")
        assert len(result.split("_")[-1]) == 8  # 8-char hash

    def test_invalid_campaign_id_format(self):
        """Test rejection of invalid campaign_id."""
        with pytest.raises(ValueError, match="campaign_id must start with 'camp_'"):
            session_id("invalid", 1, "test")

    def test_invalid_session_seq_zero(self):
        """Test rejection of zero session_seq."""
        with pytest.raises(ValueError, match="session_seq must be positive integer"):
            session_id("camp_4f2a8b1c", 0, "test")

    def test_invalid_session_seq_negative(self):
        """Test rejection of negative session_seq."""
        with pytest.raises(ValueError, match="session_seq must be positive integer"):
            session_id("camp_4f2a8b1c", -1, "test")

    def test_determinism_session_id(self):
        """Test session IDs are deterministic (10× generation)."""
        results = [
            session_id("camp_4f2a8b1c", 1, "start_hash_123")
            for _ in range(10)
        ]
        assert len(set(results)) == 1  # All identical

    def test_different_seq_different_ids(self):
        """Test different session_seq produce different session IDs."""
        id1 = session_id("camp_4f2a8b1c", 1, "start_hash")
        id2 = session_id("camp_4f2a8b1c", 2, "start_hash")
        assert id1 != id2

    def test_validate_session_id_valid(self):
        """Test validation accepts valid session IDs."""
        test_id = session_id("camp_4f2a8b1c", 1, "test")
        assert validate_session_id(test_id) is True

    def test_validate_session_id_invalid_format(self):
        """Test validation rejects malformed session IDs."""
        assert validate_session_id("session_camp_4f2a8b1c_1_a3f2b8c4") is False  # Seq not padded
        assert validate_session_id("session_invalid_0001_a3f2b8c4") is False  # No camp_ prefix


# =============================================================================
# Namespace 5: Event ID Tests
# =============================================================================

class TestEventID:
    """Tests for event_id() and validate_event_id()."""

    def test_valid_event_id(self):
        """Test valid event ID generation."""
        sess_id = session_id("camp_4f2a8b1c", 1, "start")
        result = event_id(sess_id, 42, "attack_resolved", "data_hash_123")
        assert result.startswith(f"event_{sess_id}_000042_")
        assert len(result.split("_")[-1]) == 8  # 8-char hash

    def test_invalid_session_id_format(self):
        """Test rejection of invalid session_id."""
        with pytest.raises(ValueError, match="session_id_str must be valid session ID"):
            event_id("invalid_session", 1, "test", "data")

    def test_invalid_event_seq_negative(self):
        """Test rejection of negative event_seq."""
        sess_id = session_id("camp_4f2a8b1c", 1, "start")
        with pytest.raises(ValueError, match="event_seq must be non-negative integer"):
            event_id(sess_id, -1, "test", "data")

    def test_determinism_event_id(self):
        """Test event IDs are deterministic (10× generation)."""
        sess_id = session_id("camp_4f2a8b1c", 1, "start")
        results = [
            event_id(sess_id, 42, "attack_resolved", "data_hash_123")
            for _ in range(10)
        ]
        assert len(set(results)) == 1  # All identical

    def test_different_seq_different_ids(self):
        """Test different event_seq produce different event IDs."""
        sess_id = session_id("camp_4f2a8b1c", 1, "start")
        id1 = event_id(sess_id, 1, "attack", "data")
        id2 = event_id(sess_id, 2, "attack", "data")
        assert id1 != id2

    def test_validate_event_id_valid(self):
        """Test validation accepts valid event IDs."""
        sess_id = session_id("camp_4f2a8b1c", 1, "start")
        test_id = event_id(sess_id, 42, "attack", "data")
        assert validate_event_id(test_id) is True

    def test_validate_event_id_invalid_format(self):
        """Test validation rejects malformed event IDs."""
        assert validate_event_id("event_session_camp_4f2a8b1c_0001_a3f2b8c4_42_f1c3d8a6") is False  # Seq not padded


# =============================================================================
# Namespace 6: Campaign ID Tests
# =============================================================================

class TestCampaignID:
    """Tests for campaign_id() and validate_campaign_id()."""

    def test_valid_campaign_id(self):
        """Test valid campaign ID generation."""
        result = campaign_id("user_12345", "My Campaign", "2026-02-10T14:30:00")
        assert result.startswith("camp_")
        assert len(result.split("_")[1]) == 8  # 8-char hash

    def test_empty_user_id(self):
        """Test rejection of empty user_id."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            campaign_id("", "My Campaign", "2026-02-10T14:30:00")

    def test_empty_campaign_title(self):
        """Test rejection of empty campaign_title."""
        with pytest.raises(ValueError, match="campaign_title cannot be empty"):
            campaign_id("user_12345", "", "2026-02-10T14:30:00")

    def test_empty_creation_timestamp(self):
        """Test rejection of empty creation_timestamp."""
        with pytest.raises(ValueError, match="creation_timestamp cannot be empty"):
            campaign_id("user_12345", "My Campaign", "")

    def test_determinism_campaign_id(self):
        """Test campaign IDs are deterministic (10× generation)."""
        results = [
            campaign_id("user_12345", "My Campaign", "2026-02-10T14:30:00")
            for _ in range(10)
        ]
        assert len(set(results)) == 1  # All identical

    def test_different_users_different_ids(self):
        """Test different users produce different campaign IDs."""
        id1 = campaign_id("user_1", "Campaign", "2026-02-10T14:30:00")
        id2 = campaign_id("user_2", "Campaign", "2026-02-10T14:30:00")
        assert id1 != id2

    def test_different_titles_different_ids(self):
        """Test different titles produce different campaign IDs."""
        id1 = campaign_id("user_1", "Campaign A", "2026-02-10T14:30:00")
        id2 = campaign_id("user_1", "Campaign B", "2026-02-10T14:30:00")
        assert id1 != id2

    def test_validate_campaign_id_valid(self):
        """Test validation accepts valid campaign IDs."""
        test_id = campaign_id("user_1", "Campaign", "2026-02-10T14:30:00")
        assert validate_campaign_id(test_id) is True

    def test_validate_campaign_id_invalid_format(self):
        """Test validation rejects malformed campaign IDs."""
        assert validate_campaign_id("camp_") is False  # No hash
        assert validate_campaign_id("camp_abc") is False  # Hash too short
        assert validate_campaign_id("campaign_4f2a8b1c") is False  # Wrong prefix


# =============================================================================
# Namespace 7: Prep Job ID Tests
# =============================================================================

class TestPrepJobID:
    """Tests for prepjob_id() and validate_prepjob_id()."""

    def test_valid_prepjob_id(self):
        """Test valid prep job ID generation."""
        camp_id = campaign_id("user_1", "Campaign", "2026-02-10T14:30:00")
        result = prepjob_id(camp_id, "scaffold", '{"setting": "fantasy"}')
        assert result.startswith(f"prepjob_{camp_id}_scaffold_")
        assert len(result.split("_")[-1]) == 12  # 12-char hash

    def test_invalid_campaign_id_format(self):
        """Test rejection of invalid campaign_id."""
        with pytest.raises(ValueError, match="campaign_id_str must be valid campaign ID"):
            prepjob_id("invalid", "scaffold", "{}")

    def test_invalid_job_type_uppercase(self):
        """Test rejection of uppercase job_type."""
        camp_id = campaign_id("user_1", "Campaign", "2026-02-10T14:30:00")
        with pytest.raises(ValueError, match="job_type must be lowercase alphanumeric"):
            prepjob_id(camp_id, "Scaffold", "{}")

    def test_invalid_job_type_special_chars(self):
        """Test rejection of special characters in job_type."""
        camp_id = campaign_id("user_1", "Campaign", "2026-02-10T14:30:00")
        with pytest.raises(ValueError, match="job_type must be lowercase alphanumeric"):
            prepjob_id(camp_id, "scaffold-job", "{}")

    def test_determinism_prepjob_id(self):
        """Test prep job IDs are deterministic (10× generation)."""
        camp_id = campaign_id("user_1", "Campaign", "2026-02-10T14:30:00")
        results = [
            prepjob_id(camp_id, "scaffold", '{"setting": "fantasy"}')
            for _ in range(10)
        ]
        assert len(set(results)) == 1  # All identical

    def test_different_params_different_ids(self):
        """Test different job_params produce different prep job IDs."""
        camp_id = campaign_id("user_1", "Campaign", "2026-02-10T14:30:00")
        id1 = prepjob_id(camp_id, "scaffold", '{"setting": "fantasy"}')
        id2 = prepjob_id(camp_id, "scaffold", '{"setting": "scifi"}')
        assert id1 != id2

    def test_validate_prepjob_id_valid(self):
        """Test validation accepts valid prep job IDs."""
        camp_id = campaign_id("user_1", "Campaign", "2026-02-10T14:30:00")
        test_id = prepjob_id(camp_id, "scaffold", "{}")
        assert validate_prepjob_id(test_id) is True

    def test_validate_prepjob_id_invalid_format(self):
        """Test validation rejects malformed prep job IDs."""
        assert validate_prepjob_id("prepjob_camp_4f2a8b1c_Scaffold_abc123456789") is False  # Uppercase type
        assert validate_prepjob_id("prepjob_invalid_scaffold_a3f2b8c4e1d9") is False  # Invalid camp ID


# =============================================================================
# Collision Detection Tests
# =============================================================================

class TestIDCollisionRegistry:
    """Tests for IDCollisionRegistry collision detection."""

    def test_register_id_first_time(self):
        """Test registering ID for first time succeeds."""
        registry = IDCollisionRegistry()
        registry.register("entity_camp_4f2a8b1c_a3f2b8c4e1d9", "entity_id")
        # Should not raise

    def test_register_same_id_same_namespace_collision(self):
        """Test registering same ID in same namespace raises collision error."""
        registry = IDCollisionRegistry()
        test_id = "entity_camp_4f2a8b1c_a3f2b8c4e1d9"
        registry.register(test_id, "entity_id")

        with pytest.raises(ValueError, match="ID collision detected in namespace 'entity_id'"):
            registry.register(test_id, "entity_id")

    def test_register_same_id_different_namespace_allowed(self):
        """Test registering same ID in different namespace is allowed (namespace isolation)."""
        registry = IDCollisionRegistry()
        test_id = "test_123"
        registry.register(test_id, "entity_id")
        registry.register(test_id, "asset_id")  # Should not raise

    def test_contains_registered_id(self):
        """Test contains() returns True for registered ID."""
        registry = IDCollisionRegistry()
        test_id = "entity_camp_4f2a8b1c_a3f2b8c4e1d9"
        registry.register(test_id, "entity_id")
        assert registry.contains(test_id) is True

    def test_contains_unregistered_id(self):
        """Test contains() returns False for unregistered ID."""
        registry = IDCollisionRegistry()
        assert registry.contains("nonexistent_id") is False

    def test_get_namespace_registered(self):
        """Test get_namespace() returns namespace for registered ID."""
        registry = IDCollisionRegistry()
        test_id = "entity_camp_4f2a8b1c_a3f2b8c4e1d9"
        registry.register(test_id, "entity_id")
        assert registry.get_namespace(test_id) == "entity_id"

    def test_get_namespace_unregistered(self):
        """Test get_namespace() returns None for unregistered ID."""
        registry = IDCollisionRegistry()
        assert registry.get_namespace("nonexistent_id") is None

    def test_clear_registry(self):
        """Test clear() removes all registered IDs."""
        registry = IDCollisionRegistry()
        registry.register("id1", "entity_id")
        registry.register("id2", "asset_id")
        registry.clear()
        assert registry.contains("id1") is False
        assert registry.contains("id2") is False


# =============================================================================
# Cross-Namespace Tests
# =============================================================================

class TestCrossNamespace:
    """Tests for cross-namespace ID isolation and misuse detection."""

    def test_mechanical_id_format_different_from_hash_based(self):
        """Test mechanical IDs have different format than hash-based IDs."""
        mech_id = mechanical_id("spell", "fireball")
        ent_id = entity_id("camp_4f2a8b1c", "pc", "test")

        # Mechanical IDs use dot separator, others use underscore
        assert "." in mech_id
        assert "." not in ent_id

    def test_namespace_prefixes_unique(self):
        """Test all namespace prefixes are unique."""
        camp_id = campaign_id("user_1", "Campaign", "2026-02-10T14:30:00")
        sess_id = session_id(camp_id, 1, "start")

        ent_id = entity_id(camp_id, "pc", "test")
        asset_id_str = asset_id(camp_id, "portrait", "test")
        event_id_str = event_id(sess_id, 1, "attack", "data")
        prep_id = prepjob_id(camp_id, "scaffold", "{}")

        prefixes = [
            ent_id.split("_")[0],
            asset_id_str.split("_")[0],
            sess_id.split("_")[0],
            event_id_str.split("_")[0],
            camp_id.split("_")[0],
            prep_id.split("_")[0],
        ]

        assert len(set(prefixes)) == 6  # All unique

    def test_validation_rejects_wrong_namespace(self):
        """Test validation functions reject IDs from wrong namespace."""
        ent_id = entity_id("camp_4f2a8b1c", "pc", "test")

        # Entity ID should not validate as other types
        assert validate_asset_id(ent_id) is False
        assert validate_session_id(ent_id) is False
        assert validate_campaign_id(ent_id) is False


# =============================================================================
# Determinism Verification Tests (10× Replay)
# =============================================================================

class TestDeterminismVerification:
    """Tests verifying deterministic ID generation (replay stability)."""

    def test_10x_replay_entity_ids(self):
        """Test 10× replay produces identical entity IDs."""
        results = [
            entity_id("camp_4f2a8b1c", "pc", "Theron:2026-02-10T14:30:00")
            for _ in range(10)
        ]
        assert len(set(results)) == 1, "Entity IDs must be replay-identical"

    def test_10x_replay_asset_ids(self):
        """Test 10× replay produces identical asset IDs."""
        results = [
            asset_id("camp_4f2a8b1c", "portrait", "npc:theron:default")
            for _ in range(10)
        ]
        assert len(set(results)) == 1, "Asset IDs must be replay-identical"

    def test_10x_replay_session_ids(self):
        """Test 10× replay produces identical session IDs."""
        results = [
            session_id("camp_4f2a8b1c", 1, "start_hash_123")
            for _ in range(10)
        ]
        assert len(set(results)) == 1, "Session IDs must be replay-identical"

    def test_10x_replay_event_ids(self):
        """Test 10× replay produces identical event IDs."""
        sess_id = session_id("camp_4f2a8b1c", 1, "start")
        results = [
            event_id(sess_id, 42, "attack_resolved", "data_hash_123")
            for _ in range(10)
        ]
        assert len(set(results)) == 1, "Event IDs must be replay-identical"

    def test_10x_replay_campaign_ids(self):
        """Test 10× replay produces identical campaign IDs."""
        results = [
            campaign_id("user_12345", "My Campaign", "2026-02-10T14:30:00")
            for _ in range(10)
        ]
        assert len(set(results)) == 1, "Campaign IDs must be replay-identical"

    def test_10x_replay_prepjob_ids(self):
        """Test 10× replay produces identical prep job IDs."""
        camp_id = campaign_id("user_1", "Campaign", "2026-02-10T14:30:00")
        results = [
            prepjob_id(camp_id, "scaffold", '{"setting": "fantasy"}')
            for _ in range(10)
        ]
        assert len(set(results)) == 1, "Prep job IDs must be replay-identical"

    def test_hash_stability_sha256(self):
        """Test SHA-256 hashing is stable across runs."""
        hash_input = "test_input_123"
        results = [
            hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:12]
            for _ in range(10)
        ]
        assert len(set(results)) == 1, "SHA-256 hashing must be stable"


# =============================================================================
# Error Message Clarity Tests
# =============================================================================

class TestErrorMessageClarity:
    """Tests verifying error messages are unambiguous."""

    def test_mechanical_id_invalid_domain_message(self):
        """Test invalid domain error message is clear."""
        with pytest.raises(ValueError) as exc_info:
            mechanical_id("invalid", "test")

        error_msg = str(exc_info.value)
        assert "Invalid mechanical ID domain" in error_msg
        assert "invalid" in error_msg
        assert "Valid domains" in error_msg

    def test_mechanical_id_uppercase_message(self):
        """Test uppercase error message is clear."""
        with pytest.raises(ValueError) as exc_info:
            mechanical_id("spell", "Fireball")

        error_msg = str(exc_info.value)
        assert "lowercase" in error_msg
        assert "Fireball" in error_msg

    def test_entity_id_invalid_campaign_message(self):
        """Test invalid campaign_id error message is clear."""
        with pytest.raises(ValueError) as exc_info:
            entity_id("invalid", "pc", "test")

        error_msg = str(exc_info.value)
        assert "campaign_id must start with 'camp_'" in error_msg
        assert "invalid" in error_msg

    def test_session_id_invalid_seq_message(self):
        """Test invalid session_seq error message is clear."""
        with pytest.raises(ValueError) as exc_info:
            session_id("camp_4f2a8b1c", 0, "test")

        error_msg = str(exc_info.value)
        assert "session_seq must be positive integer" in error_msg
        assert "1-indexed" in error_msg

    def test_campaign_id_empty_field_messages(self):
        """Test empty field error messages are clear."""
        with pytest.raises(ValueError) as exc_info:
            campaign_id("", "title", "timestamp")
        assert "user_id cannot be empty" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            campaign_id("user", "", "timestamp")
        assert "campaign_title cannot be empty" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            campaign_id("user", "title", "")
        assert "creation_timestamp cannot be empty" in str(exc_info.value)


# =============================================================================
# Integration Tests
# =============================================================================

class TestIDIntegration:
    """Integration tests for complete ID workflows."""

    def test_campaign_to_event_id_chain(self):
        """Test complete ID chain from campaign → session → event."""
        # Create campaign
        camp_id = campaign_id("user_123", "Test Campaign", "2026-02-10T14:30:00")
        assert validate_campaign_id(camp_id)

        # Create session
        sess_id = session_id(camp_id, 1, "start_hash")
        assert validate_session_id(sess_id)

        # Create event
        evt_id = event_id(sess_id, 1, "attack", "data")
        assert validate_event_id(evt_id)

    def test_campaign_entity_asset_chain(self):
        """Test ID chain for campaign → entity → asset."""
        # Create campaign
        camp_id = campaign_id("user_123", "Test Campaign", "2026-02-10T14:30:00")

        # Create entity
        ent_id = entity_id(camp_id, "pc", "Theron")
        assert validate_entity_id(ent_id)

        # Create asset
        asset_id_str = asset_id(camp_id, "portrait", f"entity:{ent_id}")
        assert validate_asset_id(asset_id_str)

    def test_campaign_prepjob_chain(self):
        """Test ID chain for campaign → prep job."""
        # Create campaign
        camp_id = campaign_id("user_123", "Test Campaign", "2026-02-10T14:30:00")

        # Create prep job
        prep_id = prepjob_id(camp_id, "scaffold", '{"setting": "fantasy"}')
        assert validate_prepjob_id(prep_id)

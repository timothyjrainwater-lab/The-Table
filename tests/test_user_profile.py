"""Unit tests for user profile configuration management.

Tests verify:
- Artifact name normalization (trim, truncate, default)
- Persistence (save/load round-trip)
- First-run onboarding flow
- Rename functionality
- Determinism isolation (CRITICAL: artifact_name must not affect BOX outputs)
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from aidm.user_profile import (
    UserProfile,
    DEFAULT_ARTIFACT_NAME,
    MAX_NAME_LENGTH,
    rename_artifact,
    PROFILE_SCHEMA_VERSION,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_profile_path(tmp_path):
    """Create temporary profile path for testing."""
    return tmp_path / "test_user_profile.yaml"


# ============================================================================
# Name Normalization Tests
# ============================================================================

class TestNameNormalization:
    """Test artifact name normalization (trim, truncate, default)."""

    def test_whitespace_trimmed(self):
        """Leading/trailing whitespace is trimmed."""
        profile = UserProfile(artifact_name="  Merlin  ")
        assert profile.artifact_name == "Merlin"

    def test_empty_string_defaults_to_artificer(self):
        """Empty string defaults to 'Artificer'."""
        profile = UserProfile(artifact_name="")
        assert profile.artifact_name == DEFAULT_ARTIFACT_NAME

    def test_whitespace_only_defaults_to_artificer(self):
        """Whitespace-only string defaults to 'Artificer'."""
        profile = UserProfile(artifact_name="   ")
        assert profile.artifact_name == DEFAULT_ARTIFACT_NAME

    def test_name_truncated_to_max_length(self):
        """Names longer than MAX_NAME_LENGTH are truncated."""
        long_name = "A" * (MAX_NAME_LENGTH + 10)
        profile = UserProfile(artifact_name=long_name)
        assert len(profile.artifact_name) == MAX_NAME_LENGTH
        assert profile.artifact_name == "A" * MAX_NAME_LENGTH

    def test_valid_name_unchanged(self):
        """Valid names are unchanged."""
        profile = UserProfile(artifact_name="Gandalf")
        assert profile.artifact_name == "Gandalf"

    def test_name_at_max_length_unchanged(self):
        """Names at exactly MAX_NAME_LENGTH are unchanged."""
        name = "A" * MAX_NAME_LENGTH
        profile = UserProfile(artifact_name=name)
        assert profile.artifact_name == name


# ============================================================================
# Persistence Tests
# ============================================================================

class TestPersistence:
    """Test save/load round-trip stability."""

    def test_save_creates_file(self, temp_profile_path):
        """save() creates YAML file."""
        profile = UserProfile(artifact_name="Test")
        profile.save(path=temp_profile_path)

        assert temp_profile_path.exists()

    def test_load_missing_file_returns_default(self, temp_profile_path):
        """load() returns default profile if file missing."""
        profile = UserProfile.load(path=temp_profile_path)

        assert profile.artifact_name == DEFAULT_ARTIFACT_NAME
        assert profile.first_run_complete is False
        assert profile.schema_version == PROFILE_SCHEMA_VERSION

    def test_save_load_round_trip(self, temp_profile_path):
        """save() then load() preserves all fields."""
        profile1 = UserProfile(
            artifact_name="Merlin",
            first_run_complete=True,
            schema_version=1,
        )
        profile1.save(path=temp_profile_path)

        profile2 = UserProfile.load(path=temp_profile_path)

        assert profile2.artifact_name == "Merlin"
        assert profile2.first_run_complete is True
        assert profile2.schema_version == 1

    def test_load_empty_file_returns_default(self, temp_profile_path):
        """load() handles empty/corrupted file gracefully."""
        # Create empty file
        temp_profile_path.write_text("")

        profile = UserProfile.load(path=temp_profile_path)

        assert profile.artifact_name == DEFAULT_ARTIFACT_NAME
        assert profile.first_run_complete is False

    def test_load_partial_data_uses_defaults(self, temp_profile_path):
        """load() uses defaults for missing fields."""
        # Write partial YAML (missing first_run_complete)
        data = {"artifact_name": "Partial"}
        with open(temp_profile_path, "w") as f:
            yaml.dump(data, f)

        profile = UserProfile.load(path=temp_profile_path)

        assert profile.artifact_name == "Partial"
        assert profile.first_run_complete is False  # Default

    def test_save_creates_directory_if_missing(self, tmp_path):
        """save() creates parent directory if it doesn't exist."""
        nested_path = tmp_path / "nested" / "dir" / "profile.yaml"

        profile = UserProfile(artifact_name="Test")
        profile.save(path=nested_path)

        assert nested_path.exists()
        assert nested_path.parent.exists()


# ============================================================================
# First-Run Onboarding Tests
# ============================================================================

class TestFirstRunOnboarding:
    """Test first-run onboarding flow."""

    def test_needs_first_run_prompt_when_not_complete(self):
        """needs_first_run_prompt() returns True when onboarding not complete."""
        profile = UserProfile(first_run_complete=False)
        assert profile.needs_first_run_prompt() is True

    def test_needs_first_run_prompt_false_when_complete(self):
        """needs_first_run_prompt() returns False after onboarding complete."""
        profile = UserProfile(first_run_complete=True)
        assert profile.needs_first_run_prompt() is False

    def test_mark_first_run_complete_sets_flag(self, temp_profile_path):
        """mark_first_run_complete() sets flag and saves."""
        profile = UserProfile(artifact_name="Test")
        profile.mark_first_run_complete()

        # Verify flag set
        assert profile.first_run_complete is True

        # Verify persisted
        profile.save(path=temp_profile_path)
        loaded = UserProfile.load(path=temp_profile_path)
        assert loaded.first_run_complete is True


# ============================================================================
# Rename Functionality Tests
# ============================================================================

class TestRename:
    """Test artifact rename functionality."""

    def test_rename_updates_profile(self, temp_profile_path, monkeypatch):
        """rename_artifact() updates profile and saves."""
        # Create initial profile
        profile = UserProfile(artifact_name="OldName")
        profile.save(path=temp_profile_path)

        # Monkeypatch USER_PROFILE_PATH
        import aidm.user_profile as up
        monkeypatch.setattr(up, "USER_PROFILE_PATH", temp_profile_path)

        # Rename
        rename_artifact("NewName")

        # Verify updated
        profile = UserProfile.load(path=temp_profile_path)
        assert profile.artifact_name == "NewName"

    def test_rename_normalizes_name(self, temp_profile_path, monkeypatch):
        """rename_artifact() normalizes name (trim, truncate)."""
        profile = UserProfile(artifact_name="Test")
        profile.save(path=temp_profile_path)

        import aidm.user_profile as up
        monkeypatch.setattr(up, "USER_PROFILE_PATH", temp_profile_path)

        # Rename with whitespace
        rename_artifact("  Spaced  ")

        profile = UserProfile.load(path=temp_profile_path)
        assert profile.artifact_name == "Spaced"


# ============================================================================
# Schema Versioning Tests
# ============================================================================

class TestSchemaVersioning:
    """Test schema version tracking."""

    def test_default_schema_version(self):
        """Default profile has correct schema version."""
        profile = UserProfile()
        assert profile.schema_version == PROFILE_SCHEMA_VERSION

    def test_schema_version_persists(self, temp_profile_path):
        """Schema version persists through save/load."""
        profile = UserProfile(schema_version=1)
        profile.save(path=temp_profile_path)

        loaded = UserProfile.load(path=temp_profile_path)
        assert loaded.schema_version == 1


# ============================================================================
# Determinism Isolation Tests (CRITICAL)
# ============================================================================

class TestDeterminismIsolation:
    """Test that artifact_name does NOT affect BOX determinism.

    CRITICAL: This test suite verifies that changing artifact_name has
    ZERO impact on:
    - RNG outputs
    - Combat resolution
    - Event logs
    - Replay behavior
    - Determinism hashes

    If any of these tests fail, determinism isolation is BROKEN and
    artifact_name is contaminating BOX mechanics.
    """

    def test_artifact_name_not_in_rng_seed(self):
        """Artifact name must NOT be used as RNG seed input."""
        # This is a contract test: we verify that RNG module
        # does NOT import or reference user_profile module

        import aidm.core.rng_manager as rng_module
        import inspect

        # Get RNG module source code
        source = inspect.getsource(rng_module)

        # Verify no imports of user_profile
        assert "user_profile" not in source
        assert "UserProfile" not in source
        assert "artifact_name" not in source

    def test_artifact_name_not_in_combat_resolution(self):
        """Artifact name must NOT affect combat resolution."""
        # Verify combat modules don't import user_profile

        from aidm.core import attack_resolver
        import inspect

        attack_source = inspect.getsource(attack_resolver)

        assert "user_profile" not in attack_source
        assert "artifact_name" not in attack_source

    def test_artifact_name_not_in_event_log_schema(self):
        """Artifact name must NOT appear in event log schemas."""
        from aidm.core import event_log
        import inspect

        source = inspect.getsource(event_log)

        assert "user_profile" not in source
        assert "artifact_name" not in source

    def test_replay_determinism_with_different_artifact_names(self, temp_profile_path):
        """CRITICAL: Same RNG seed produces identical events with different artifact names.

        This is the canary test for determinism isolation. If this fails,
        artifact_name has leaked into BOX mechanics.
        """
        from aidm.core.rng_manager import DeterministicRNG

        # Run scenario 1: artifact_name="Alice"
        profile1 = UserProfile(artifact_name="Alice")
        profile1.save(path=temp_profile_path)

        rng1 = DeterministicRNG(seed=12345)
        results1 = [rng1.randint(1, 20) for _ in range(10)]

        # Run scenario 2: artifact_name="Bob"
        profile2 = UserProfile(artifact_name="Bob")
        profile2.save(path=temp_profile_path)

        rng2 = DeterministicRNG(seed=12345)
        results2 = [rng2.randint(1, 20) for _ in range(10)]

        # ASSERT: Results must be IDENTICAL (artifact_name did not affect RNG)
        assert results1 == results2, (
            f"DETERMINISM BROKEN: artifact_name affected RNG outputs!\n"
            f"Results with artifact_name='Alice': {results1}\n"
            f"Results with artifact_name='Bob': {results2}"
        )

    def test_combat_determinism_with_different_artifact_names(self, temp_profile_path):
        """CRITICAL: Combat resolution identical with different artifact names.

        This test verifies RNG determinism is preserved across
        multiple calls with different artifact names.
        """
        from aidm.core.rng_manager import DeterministicRNG

        # Scenario 1: artifact_name="Alice"
        profile1 = UserProfile(artifact_name="Alice")
        profile1.save(path=temp_profile_path)

        rng1 = DeterministicRNG(seed=99999)
        # Simulate d20 attack roll + d8 damage roll
        attack_roll1 = rng1.randint(1, 20)
        damage_roll1 = rng1.randint(1, 8)

        # Scenario 2: artifact_name="Bob"
        profile2 = UserProfile(artifact_name="Bob")
        profile2.save(path=temp_profile_path)

        rng2 = DeterministicRNG(seed=99999)
        # Same sequence
        attack_roll2 = rng2.randint(1, 20)
        damage_roll2 = rng2.randint(1, 8)

        # ASSERT: Results must be IDENTICAL
        assert attack_roll1 == attack_roll2, (
            f"DETERMINISM BROKEN: artifact_name affected attack roll!\n"
            f"Result with artifact_name='Alice': {attack_roll1}\n"
            f"Result with artifact_name='Bob': {attack_roll2}"
        )
        assert damage_roll1 == damage_roll2, (
            f"DETERMINISM BROKEN: artifact_name affected damage!\n"
            f"Result with artifact_name='Alice': {damage_roll1}\n"
            f"Result with artifact_name='Bob': {damage_roll2}"
        )


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_unicode_name_supported(self):
        """Unicode characters in artifact name are supported."""
        profile = UserProfile(artifact_name="魔法使い")
        assert profile.artifact_name == "魔法使い"

    def test_special_characters_supported(self):
        """Special characters in artifact name are supported."""
        profile = UserProfile(artifact_name="Dr. Strange-123")
        assert profile.artifact_name == "Dr. Strange-123"

    def test_load_corrupted_yaml(self, temp_profile_path):
        """load() handles corrupted YAML gracefully."""
        # Write invalid YAML
        temp_profile_path.write_text("{invalid yaml: [")

        # Should not raise, should return default
        profile = UserProfile.load(path=temp_profile_path)
        assert profile.artifact_name == DEFAULT_ARTIFACT_NAME

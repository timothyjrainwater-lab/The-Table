"""Tests for version compatibility checking.

WO-VERSION-MVP: Minimum Viable Version Safety

Tests:
- check_version: equal, patch diff, minor diff, major diff
- validate_campaign_version: warning passthrough, error raising
- VersionMismatchError on minor/major
"""

import logging
import pytest

from aidm.core.version_check import (
    VersionVerdict,
    VersionMismatchError,
    check_version,
    validate_campaign_version,
)


class TestCheckVersion:
    """Tests for check_version function."""

    def test_equal_versions_compatible(self):
        """Identical versions should return COMPATIBLE."""
        verdict = check_version("0.1.0", "0.1.0")
        assert verdict == VersionVerdict.COMPATIBLE

    def test_patch_difference_warns(self):
        """Patch-only difference should return WARN_PATCH."""
        verdict = check_version("0.1.0", "0.1.1")
        assert verdict == VersionVerdict.WARN_PATCH

    def test_patch_difference_reverse(self):
        """Campaign newer patch than engine also warns."""
        verdict = check_version("0.1.3", "0.1.0")
        assert verdict == VersionVerdict.WARN_PATCH

    def test_minor_difference_hard_stops(self):
        """Minor version difference should return HARD_STOP_MINOR."""
        verdict = check_version("0.1.0", "0.2.0")
        assert verdict == VersionVerdict.HARD_STOP_MINOR

    def test_minor_difference_reverse(self):
        """Campaign newer minor than engine also hard stops."""
        verdict = check_version("0.2.0", "0.1.0")
        assert verdict == VersionVerdict.HARD_STOP_MINOR

    def test_major_difference_hard_stops(self):
        """Major version difference should return HARD_STOP_MAJOR."""
        verdict = check_version("0.1.0", "1.0.0")
        assert verdict == VersionVerdict.HARD_STOP_MAJOR

    def test_major_difference_reverse(self):
        """Campaign newer major than engine also hard stops."""
        verdict = check_version("2.0.0", "1.0.0")
        assert verdict == VersionVerdict.HARD_STOP_MAJOR

    def test_major_takes_precedence_over_minor(self):
        """Major diff should dominate even if minor also differs."""
        verdict = check_version("0.1.0", "1.2.0")
        assert verdict == VersionVerdict.HARD_STOP_MAJOR

    def test_defaults_to_aidm_version(self):
        """When engine_version is None, should use aidm.__version__."""
        import aidm
        verdict = check_version(aidm.__version__)
        assert verdict == VersionVerdict.COMPATIBLE

    def test_patch_logs_warning(self, caplog):
        """Patch mismatch should emit WARNING log."""
        with caplog.at_level(logging.WARNING, logger="aidm.core.version_check"):
            check_version("0.1.0", "0.1.5")
        assert "PATCH version mismatch" in caplog.text
        assert "bug fixes only" in caplog.text

    def test_minor_logs_error(self, caplog):
        """Minor mismatch should emit ERROR log."""
        with caplog.at_level(logging.ERROR, logger="aidm.core.version_check"):
            check_version("0.1.0", "0.3.0")
        assert "MINOR version mismatch" in caplog.text

    def test_major_logs_error(self, caplog):
        """Major mismatch should emit ERROR log."""
        with caplog.at_level(logging.ERROR, logger="aidm.core.version_check"):
            check_version("0.1.0", "2.0.0")
        assert "MAJOR version mismatch" in caplog.text

    def test_compatible_no_log(self, caplog):
        """Equal versions should not log anything."""
        with caplog.at_level(logging.DEBUG, logger="aidm.core.version_check"):
            check_version("0.1.0", "0.1.0")
        assert caplog.text == ""


class TestValidateCampaignVersion:
    """Tests for validate_campaign_version convenience wrapper."""

    def test_compatible_no_error(self):
        """Compatible version should not raise."""
        validate_campaign_version("0.1.0", "0.1.0")

    def test_patch_no_error(self):
        """Patch difference should warn but not raise."""
        validate_campaign_version("0.1.0", "0.1.1")

    def test_minor_raises(self):
        """Minor difference should raise VersionMismatchError."""
        with pytest.raises(VersionMismatchError, match="Minor version mismatch"):
            validate_campaign_version("0.1.0", "0.2.0")

    def test_major_raises(self):
        """Major difference should raise VersionMismatchError."""
        with pytest.raises(VersionMismatchError, match="Major version mismatch"):
            validate_campaign_version("0.1.0", "1.0.0")

    def test_error_message_includes_versions(self):
        """Error message should name both versions."""
        with pytest.raises(VersionMismatchError) as exc_info:
            validate_campaign_version("0.1.0", "0.3.0")
        msg = str(exc_info.value)
        assert "0.1.0" in msg
        assert "0.3.0" in msg


class TestEventSchemaVersion:
    """Tests for event_schema_version field on Event."""

    def test_default_value(self):
        """Event should default event_schema_version to '1'."""
        from aidm.core.event_log import Event

        event = Event(
            event_id=0,
            event_type="test",
            timestamp=1.0,
            payload={},
        )
        assert event.event_schema_version == "1"

    def test_to_dict_includes_field(self):
        """to_dict() should include event_schema_version."""
        from aidm.core.event_log import Event

        event = Event(
            event_id=0,
            event_type="test",
            timestamp=1.0,
            payload={},
        )
        data = event.to_dict()
        assert "event_schema_version" in data
        assert data["event_schema_version"] == "1"

    def test_from_dict_with_field(self):
        """from_dict() should read event_schema_version when present."""
        from aidm.core.event_log import Event

        data = {
            "event_id": 0,
            "event_type": "test",
            "timestamp": 1.0,
            "payload": {},
            "rng_offset": 0,
            "citations": [],
            "event_schema_version": "2",
        }
        event = Event.from_dict(data)
        assert event.event_schema_version == "2"

    def test_from_dict_without_field(self):
        """from_dict() should default to '1' when field is absent (backward compat)."""
        from aidm.core.event_log import Event

        data = {
            "event_id": 0,
            "event_type": "test",
            "timestamp": 1.0,
            "payload": {},
            "rng_offset": 0,
            "citations": [],
        }
        event = Event.from_dict(data)
        assert event.event_schema_version == "1"

    def test_roundtrip_preserves_field(self):
        """Event roundtrip should preserve event_schema_version."""
        from aidm.core.event_log import Event

        original = Event(
            event_id=5,
            event_type="attack",
            timestamp=99.0,
            payload={"target": "goblin"},
            event_schema_version="1",
        )
        data = original.to_dict()
        restored = Event.from_dict(data)
        assert restored.event_schema_version == original.event_schema_version

    def test_old_jsonl_without_field(self):
        """JSONL without event_schema_version should deserialize with default '1'."""
        import json
        import tempfile
        from pathlib import Path
        from aidm.core.event_log import EventLog

        # Simulate old JSONL without event_schema_version
        old_event = {
            "event_id": 0,
            "event_type": "start",
            "timestamp": 1.0,
            "payload": {},
            "rng_offset": 0,
            "citations": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "old_events.jsonl"
            with open(path, "w") as f:
                json.dump(old_event, f, sort_keys=True)
                f.write("\n")

            log = EventLog.from_jsonl(path)
            assert len(log) == 1
            assert log[0].event_schema_version == "1"

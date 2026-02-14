"""Campaign version compatibility checking.

Compares the engine version that created a campaign against the currently
running engine version and returns a compatibility verdict.

Version mismatch policy (from WO-VERSION-MVP):
- PATCH difference (Type A): WARNING, proceed normally
- MINOR difference (Type B): HARD STOP, require user choice
- MAJOR difference (Type C): HARD STOP, require migration

SINGLE SOURCE OF TRUTH for: version compatibility decisions.
CANONICAL OWNER: aidm.core.version_check (this file).
"""

import logging
from enum import Enum
from typing import Tuple

from packaging.version import Version

import aidm

logger = logging.getLogger(__name__)


class VersionVerdict(Enum):
    """Result of comparing campaign engine_version to running engine version."""

    COMPATIBLE = "compatible"
    WARN_PATCH = "warn_patch"
    HARD_STOP_MINOR = "hard_stop_minor"
    HARD_STOP_MAJOR = "hard_stop_major"


class VersionMismatchError(Exception):
    """Raised when a campaign requires a different engine version."""


def check_version(campaign_version: str, engine_version: str | None = None) -> VersionVerdict:
    """Compare campaign version against the running engine version.

    Args:
        campaign_version: The engine_version string from CampaignManifest.
        engine_version: Override for the running version (defaults to aidm.__version__).

    Returns:
        VersionVerdict indicating compatibility level.
    """
    if engine_version is None:
        engine_version = aidm.__version__

    cv = Version(campaign_version)
    ev = Version(engine_version)

    if cv == ev:
        return VersionVerdict.COMPATIBLE

    if cv.major != ev.major:
        logger.error(
            "MAJOR version mismatch: campaign=%s engine=%s — "
            "schema migration required, cannot load.",
            campaign_version,
            engine_version,
        )
        return VersionVerdict.HARD_STOP_MAJOR

    if cv.minor != ev.minor:
        logger.error(
            "MINOR version mismatch: campaign=%s engine=%s — "
            "behavior changes detected, cannot load without user confirmation.",
            campaign_version,
            engine_version,
        )
        return VersionVerdict.HARD_STOP_MINOR

    # Only patch differs
    logger.warning(
        "PATCH version mismatch: campaign=%s engine=%s — "
        "bug fixes only, loading normally.",
        campaign_version,
        engine_version,
    )
    return VersionVerdict.WARN_PATCH


def validate_campaign_version(campaign_version: str, engine_version: str | None = None) -> None:
    """Check version and raise on hard-stop mismatches.

    Convenience wrapper that logs warnings for patch differences and raises
    VersionMismatchError for minor/major differences.

    Args:
        campaign_version: The engine_version string from CampaignManifest.
        engine_version: Override for the running version (defaults to aidm.__version__).

    Raises:
        VersionMismatchError: On MINOR or MAJOR version mismatch.
    """
    verdict = check_version(campaign_version, engine_version)

    if verdict == VersionVerdict.HARD_STOP_MINOR:
        raise VersionMismatchError(
            f"Minor version mismatch: campaign={campaign_version} "
            f"engine={engine_version or aidm.__version__}. "
            f"Behavior changes detected — cannot load without user confirmation."
        )
    if verdict == VersionVerdict.HARD_STOP_MAJOR:
        raise VersionMismatchError(
            f"Major version mismatch: campaign={campaign_version} "
            f"engine={engine_version or aidm.__version__}. "
            f"Schema migration required — cannot load."
        )

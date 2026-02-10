"""User profile configuration management.

This module manages user-specific presentation preferences including artifact naming.

DETERMINISM ISOLATION:
- This module handles PRESENTATION-ONLY configuration
- NO fields in user profile affect determinism-critical systems:
  - RNG state
  - Combat resolution
  - Event-sourced logs
  - Replay behavior
  - Determinism hashes

Usage:
    profile = UserProfile.load()
    print(f"Welcome back! Your {profile.artifact_name} is ready.")

    # Rename
    profile.artifact_name = "Merlin"
    profile.save()

Location Rationale:
- Placed outside aidm/core/ (app-level, not mechanics)
- Safe for UI/narration wrapper usage only
- Never imported by BOX mechanics modules

Schema:
    artifact_name: str (max 32 chars, trimmed, default "Artificer")
    first_run_complete: bool (triggers onboarding prompt)
    schema_version: int (for future migration support)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml


# ============================================================================
# Constants
# ============================================================================

DEFAULT_ARTIFACT_NAME = "Artificer"
MAX_NAME_LENGTH = 32
PROFILE_SCHEMA_VERSION = 1

# Path to user profile (relative to project root)
USER_PROFILE_PATH = Path(__file__).parent.parent / "config" / "user_profile.yaml"


# ============================================================================
# User Profile Data Model
# ============================================================================

@dataclass
class UserProfile:
    """User profile configuration (presentation layer only).

    Attributes:
        artifact_name: User-chosen name for AIDM instance (UI/narration only)
        first_run_complete: Whether first-run onboarding has been shown
        schema_version: Profile schema version (for migration support)
    """

    artifact_name: str = DEFAULT_ARTIFACT_NAME
    first_run_complete: bool = False
    schema_version: int = PROFILE_SCHEMA_VERSION

    def __post_init__(self):
        """Validate and normalize artifact_name."""
        self.artifact_name = self._normalize_name(self.artifact_name)

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize artifact name (trim, truncate, default if empty).

        Args:
            name: Raw name input

        Returns:
            Normalized name (max 32 chars, trimmed, default if empty)
        """
        # Trim whitespace
        name = name.strip()

        # Default if empty
        if not name:
            return DEFAULT_ARTIFACT_NAME

        # Truncate if too long
        if len(name) > MAX_NAME_LENGTH:
            name = name[:MAX_NAME_LENGTH]

        return name

    def save(self, path: Optional[Path] = None) -> None:
        """Save user profile to YAML file.

        Args:
            path: Optional custom path (defaults to USER_PROFILE_PATH)
        """
        if path is None:
            path = USER_PROFILE_PATH

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize to YAML
        data = {
            "artifact_name": self.artifact_name,
            "first_run_complete": self.first_run_complete,
            "schema_version": self.schema_version,
        }

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "UserProfile":
        """Load user profile from YAML file.

        Args:
            path: Optional custom path (defaults to USER_PROFILE_PATH)

        Returns:
            UserProfile instance (creates default if file missing)
        """
        if path is None:
            path = USER_PROFILE_PATH

        # If file doesn't exist, return default profile
        if not path.exists():
            return cls()

        # Load from YAML
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except (yaml.YAMLError, ValueError):
            # Handle corrupted YAML
            return cls()

        # Handle empty/corrupted file
        if not data:
            return cls()

        # Extract fields with defaults
        artifact_name = data.get("artifact_name", DEFAULT_ARTIFACT_NAME)
        first_run_complete = data.get("first_run_complete", False)
        schema_version = data.get("schema_version", PROFILE_SCHEMA_VERSION)

        return cls(
            artifact_name=artifact_name,
            first_run_complete=first_run_complete,
            schema_version=schema_version,
        )

    def mark_first_run_complete(self) -> None:
        """Mark first-run onboarding as complete and save."""
        self.first_run_complete = True
        self.save()

    def needs_first_run_prompt(self) -> bool:
        """Check if first-run onboarding prompt should be shown.

        Returns:
            True if onboarding not yet completed
        """
        return not self.first_run_complete


# ============================================================================
# First-Run Onboarding
# ============================================================================

def prompt_artifact_name(default: str = DEFAULT_ARTIFACT_NAME) -> str:
    """Prompt user for artifact name (first-run onboarding).

    Args:
        default: Default name if user accepts without input

    Returns:
        User-chosen name (normalized, max 32 chars)
    """
    print("\n" + "=" * 60)
    print("FIRST-RUN SETUP")
    print("=" * 60)
    print(f"\nWhat would you like to call me?")
    print(f"(Press Enter to use default: '{default}')")
    print()

    try:
        name = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        # Handle non-interactive environments or Ctrl+C
        name = ""

    # Use default if empty
    if not name:
        name = default

    # Normalize
    name = UserProfile._normalize_name(name)

    print(f"\nGreat! You can call me '{name}'.")
    print("(You can change this later via Settings or CLI: 'aidm set-name \"NewName\"')")
    print()

    return name


def run_first_run_onboarding() -> UserProfile:
    """Run first-run onboarding flow (prompt for artifact name).

    Returns:
        UserProfile with user-chosen name and first_run_complete=True
    """
    # Load existing profile (or create default)
    profile = UserProfile.load()

    # Check if onboarding already completed
    if profile.first_run_complete:
        return profile

    # Prompt for artifact name
    name = prompt_artifact_name(default=profile.artifact_name)

    # Update profile
    profile.artifact_name = name
    profile.mark_first_run_complete()

    return profile


# ============================================================================
# Rename Utility
# ============================================================================

def rename_artifact(new_name: str) -> None:
    """Rename artifact (update user profile).

    Args:
        new_name: New artifact name
    """
    profile = UserProfile.load()
    profile.artifact_name = new_name
    profile.save()
    print(f"Artifact renamed to: '{profile.artifact_name}'")


# ============================================================================
# CLI Entry Point (for testing/manual invocation)
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "set-name" and len(sys.argv) > 2:
            # CLI: python -m aidm.user_profile set-name "NewName"
            new_name = sys.argv[2]
            rename_artifact(new_name)

        elif command == "show":
            # CLI: python -m aidm.user_profile show
            profile = UserProfile.load()
            print(f"Artifact Name: {profile.artifact_name}")
            print(f"First Run Complete: {profile.first_run_complete}")
            print(f"Schema Version: {profile.schema_version}")

        elif command == "first-run":
            # CLI: python -m aidm.user_profile first-run
            profile = run_first_run_onboarding()
            print(f"\nProfile saved: {profile.artifact_name}")

        else:
            print("Usage:")
            print("  python -m aidm.user_profile set-name \"NewName\"")
            print("  python -m aidm.user_profile show")
            print("  python -m aidm.user_profile first-run")

    else:
        # No args: show current profile
        profile = UserProfile.load()
        print(f"Artifact Name: {profile.artifact_name}")
        print(f"First Run Complete: {profile.first_run_complete}")

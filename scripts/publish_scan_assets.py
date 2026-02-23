#!/usr/bin/env python3
"""P3 Asset Scan — No Shipped Artifacts Gate (PRS-01 §3).

Validates that the repository contains only source code and documentation,
not model weights, audio files, databases, or other binary artifacts.

Usage:
    python scripts/publish_scan_assets.py

Exit code 0 if clean, 1 if violations found.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from _publish_scan_utils import (
    Finding,
    exit_with_findings,
    get_tracked_files,
    matches_any_directory,
    matches_any_pattern,
)


# ---------------------------------------------------------------------------
# PRS-01 §3 Allowlist and Blocklist
# ---------------------------------------------------------------------------

# Extensions explicitly allowed
ALLOWLIST_EXTENSIONS = [
    "*.py", "*.ts", "*.tsx", "*.js", "*.json", "*.yaml", "*.yml", "*.toml",
    "*.md", "*.txt", "*.html", "*.css",
    "*.cfg", "*.ini", "*.sh", "*.bat", "*.ps1",
    "*.ahk",  # AutoHotkey operator tooling
    "*.jsonl",  # Test fixtures and playtest logs
]

# Exact filenames allowed (no extension)
ALLOWLIST_EXACT = [
    "Makefile",
    "Dockerfile",
    ".gitignore",
    ".gitattributes",
    "LICENSE",
    "NOTICE",
]

# Extensions explicitly blocked (§3 blocklist)
BLOCKLIST_EXTENSIONS = [
    # Model weights
    "*.gguf", "*.safetensors", "*.bin",
    # Audio files
    "*.wav", "*.mp3", "*.ogg", "*.flac",
    # Image files (allowed in docs/ only)
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.webp",
    # Databases
    "*.sqlite", "*.db", "*.sqlite3",
    # Serialized objects
    "*.pkl", "*.pickle",
    # Cache files
    "*.cache",
]

# Directory patterns to block
BLOCKLIST_DIRECTORIES = [
    "__pycache__/",
    ".cache/",
    "node_modules/",
    "weights/",
    "models/",
    "cache/",
    "outputs/",
    "recordings/",
    "oracle_db/",
    "image_cache/",
    "audio_cache/",
]

# Image extensions for docs/ exception
IMAGE_EXTENSIONS = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.webp"]


# ---------------------------------------------------------------------------
# Scan logic
# ---------------------------------------------------------------------------

def is_allowed_file(file_path: str) -> tuple[bool, str | None]:
    """Check if a file is explicitly allowed by PRS-01 §3.

    Args:
        file_path: Relative path from repo root.

    Returns:
        Tuple of (is_allowed, reason). Reason is None if allowed.
    """
    path_obj = Path(file_path)
    filename = path_obj.name

    # Check exact filename matches
    if filename in ALLOWLIST_EXACT:
        return True, None

    # Check allowlist extensions
    matched, pattern = matches_any_pattern(file_path, ALLOWLIST_EXTENSIONS)
    if matched:
        return True, None

    # Check for .dockerfile extension (e.g., foo.dockerfile)
    if file_path.endswith(".dockerfile"):
        return True, None

    # Check for images in docs/ (special exception per PRS-01 §3)
    if file_path.startswith("docs/"):
        matched, _ = matches_any_pattern(file_path, IMAGE_EXTENSIONS)
        if matched:
            return True, None

    return False, "not on allowlist"


def is_blocked_file(file_path: str) -> tuple[bool, str | None]:
    """Check if a file matches the PRS-01 §3 blocklist.

    Args:
        file_path: Relative path from repo root.

    Returns:
        Tuple of (is_blocked, reason). Reason is the matching pattern if blocked.
    """
    # Check directory blocklist
    matched, pattern = matches_any_directory(file_path, BLOCKLIST_DIRECTORIES)
    if matched:
        return True, f"in blocked directory: {pattern}"

    # Check blocklist extensions
    matched, pattern = matches_any_pattern(file_path, BLOCKLIST_EXTENSIONS)
    if matched:
        # Exception: images in docs/ are allowed
        if pattern in IMAGE_EXTENSIONS and file_path.startswith("docs/"):
            return False, None
        return True, f"blocked extension: {pattern}"

    return False, None


def scan_assets() -> list[Finding]:
    """Scan all tracked files for asset violations.

    Returns:
        List of Finding objects for violations.
    """
    findings: list[Finding] = []
    tracked_files = get_tracked_files()

    for file_path in tracked_files:
        # Check if blocked
        is_blocked, block_reason = is_blocked_file(file_path)
        if is_blocked:
            findings.append(
                Finding(
                    file_path=file_path,
                    line_number=None,
                    rule="P3-BLOCK",
                    message=f"Blocklist violation: {block_reason}",
                )
            )
            continue

        # Check if on allowlist
        is_allowed, allow_reason = is_allowed_file(file_path)
        if not is_allowed:
            findings.append(
                Finding(
                    file_path=file_path,
                    line_number=None,
                    rule="P3-UNKNOWN",
                    message="File type not on allowlist (requires manual review)",
                )
            )

    return findings


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Run P3 asset scan."""
    try:
        tracked_files = get_tracked_files()
        findings = scan_assets()
        return exit_with_findings(findings, len(tracked_files), "P3 Asset Scan")
    except Exception as e:
        print(f"ERROR: P3 Asset Scan failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

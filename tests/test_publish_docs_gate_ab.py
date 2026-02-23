#!/usr/bin/env python3
"""
Gate AB: Documentation Compliance Tests (PRS-01 §P9)

Tests for the documentation validation system.
Validates that publish_check_docs.py correctly enforces doc compliance.

Gate letter: AB
Minimum tests: 6
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_PRIVACY_SECTIONS = [
    "Data Locality",
    "Microphone",
    "Retention Defaults",
    "Delete Everything",
]


# --------------------------------------------------------------------------
# AB-01: Current repo passes validation
# --------------------------------------------------------------------------

def test_ab01_current_repo_passes():
    """AB-01: publish_check_docs.py exits 0 on current repo."""
    result = subprocess.run(
        [sys.executable, "scripts/publish_check_docs.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Doc check failed on current repo.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
    assert "[PASS]" in result.stdout


# --------------------------------------------------------------------------
# AB-02: Validator detects missing privacy section (planted)
# --------------------------------------------------------------------------

def test_ab02_detect_missing_privacy_section():
    """AB-02: Validator detects when a required section is removed from PRIVACY.md."""
    privacy_path = PROJECT_ROOT / "docs" / "PRIVACY.md"
    backup_path = PROJECT_ROOT / "docs" / "PRIVACY.md.bak"
    shutil.copy(privacy_path, backup_path)

    try:
        content = privacy_path.read_text(encoding="utf-8")
        # Remove the "Retention Defaults" section heading
        modified = content.replace("## Retention Defaults", "## Data Tables")
        privacy_path.write_text(modified, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, "scripts/publish_check_docs.py"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, "Validator should fail with missing section"
        assert "[FAIL]" in result.stdout
        assert "Retention Defaults" in result.stdout
    finally:
        shutil.move(backup_path, privacy_path)


# --------------------------------------------------------------------------
# AB-03: Validator detects invalid path reference (planted)
# --------------------------------------------------------------------------

def test_ab03_detect_invalid_path_reference():
    """AB-03: Validator detects a referenced path that does not exist."""
    privacy_path = PROJECT_ROOT / "docs" / "PRIVACY.md"
    backup_path = PROJECT_ROOT / "docs" / "PRIVACY.md.bak"
    shutil.copy(privacy_path, backup_path)

    try:
        content = privacy_path.read_text(encoding="utf-8")
        # Inject a fake path reference
        modified = content + "\n| Fake data | `nonexistent_dir/` | N/A | N/A |\n"
        privacy_path.write_text(modified, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, "scripts/publish_check_docs.py"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, "Validator should fail with invalid path"
        assert "[FAIL]" in result.stdout
        assert "nonexistent_dir/" in result.stdout
    finally:
        shutil.move(backup_path, privacy_path)


# --------------------------------------------------------------------------
# AB-04: PRIVACY.md exists and has all 4 required sections
# --------------------------------------------------------------------------

def test_ab04_privacy_has_required_sections():
    """AB-04: docs/PRIVACY.md exists and has all 4 required sections (direct parse)."""
    privacy_path = PROJECT_ROOT / "docs" / "PRIVACY.md"
    assert privacy_path.exists(), "docs/PRIVACY.md does not exist"

    content = privacy_path.read_text(encoding="utf-8")

    for section in REQUIRED_PRIVACY_SECTIONS:
        pattern = r"^#{1,4}\s+" + re.escape(section)
        assert re.search(pattern, content, re.MULTILINE), (
            f"Missing required section: '{section}'"
        )


# --------------------------------------------------------------------------
# AB-05: OGL_NOTICE.md exists
# --------------------------------------------------------------------------

def test_ab05_ogl_notice_exists():
    """AB-05: docs/OGL_NOTICE.md exists."""
    ogl_path = PROJECT_ROOT / "docs" / "OGL_NOTICE.md"
    assert ogl_path.exists(), "docs/OGL_NOTICE.md does not exist"


# --------------------------------------------------------------------------
# AB-06: All paths referenced in PRIVACY.md exist
# --------------------------------------------------------------------------

def test_ab06_privacy_referenced_paths_exist():
    """AB-06: All directory paths referenced in PRIVACY.md exist on disk."""
    privacy_path = PROJECT_ROOT / "docs" / "PRIVACY.md"
    content = privacy_path.read_text(encoding="utf-8")

    # Extract backtick-quoted directory paths (e.g., `logs/`)
    referenced_paths = re.findall(r"`([a-zA-Z_][a-zA-Z0-9_]*/)`", content)
    assert len(referenced_paths) > 0, "No directory paths found in PRIVACY.md"

    missing = []
    for ref_path in referenced_paths:
        full_path = PROJECT_ROOT / ref_path
        if not full_path.exists():
            missing.append(ref_path)

    assert not missing, f"Referenced paths do not exist: {missing}"

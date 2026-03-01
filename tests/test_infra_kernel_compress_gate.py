"""
Gate tests: WO-INFRA-KERNEL-COMPRESS-001 — Chisel Kernel Compression
KC-001..KC-008
"""

import os
import pytest

KERNEL_PATH = "docs/ops/CHISEL_KERNEL_001.md"
ARCHIVE_PATH = "docs/ops/CHISEL_SESSION_ARCHIVE.md"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _lines(path):
    return _read(path).splitlines()


# KC-001: Kernel line count <= 200
def test_kc_001_kernel_line_count():
    count = len(_lines(KERNEL_PATH))
    assert count <= 200, (
        f"KC-001 FAIL: CHISEL_KERNEL_001.md is {count} lines — must be <= 200"
    )


# KC-002: Kernel contains Active Capsule section
def test_kc_002_kernel_has_active_capsule():
    content = _read(KERNEL_PATH)
    assert "## Active Capsule" in content, (
        "KC-002 FAIL: CHISEL_KERNEL_001.md missing '## Active Capsule' section"
    )


# KC-003: Kernel contains Critical Behavioral Rules section
def test_kc_003_kernel_has_behavioral_rules():
    content = _read(KERNEL_PATH)
    assert "## Critical Behavioral Rules" in content, (
        "KC-003 FAIL: CHISEL_KERNEL_001.md missing '## Critical Behavioral Rules' section"
    )


# KC-004: Kernel contains Hidden DM Kernel Quick Reference section
def test_kc_004_kernel_has_dm_kernel_ref():
    content = _read(KERNEL_PATH)
    assert "## Hidden DM Kernel Quick Reference" in content, (
        "KC-004 FAIL: CHISEL_KERNEL_001.md missing '## Hidden DM Kernel Quick Reference' section"
    )


# KC-005: Kernel contains Communication Paths section
def test_kc_005_kernel_has_communication_paths():
    content = _read(KERNEL_PATH)
    assert "## Communication Paths" in content, (
        "KC-005 FAIL: CHISEL_KERNEL_001.md missing '## Communication Paths' section"
    )


# KC-006: Archive file exists
def test_kc_006_archive_exists():
    assert os.path.exists(ARCHIVE_PATH), (
        f"KC-006 FAIL: {ARCHIVE_PATH} does not exist — delta content was not graduated"
    )


# KC-007: Archive line count > 100 (confirms deltas were graduated, not discarded)
def test_kc_007_archive_has_delta_content():
    count = len(_lines(ARCHIVE_PATH))
    assert count > 100, (
        f"KC-007 FAIL: {ARCHIVE_PATH} is only {count} lines — delta content appears missing"
    )


# KC-008: Kernel does NOT contain '## Project State' (stale section removed)
def test_kc_008_kernel_no_project_state():
    content = _read(KERNEL_PATH)
    assert "## Project State" not in content, (
        "KC-008 FAIL: CHISEL_KERNEL_001.md still contains '## Project State' — stale section not removed"
    )

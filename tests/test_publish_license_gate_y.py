#!/usr/bin/env python3
"""
Gate Y: License Compliance Tests (P4)

Tests for the license ledger validation system per PRS-01 §P4.
Validates that publish_check_licenses.py correctly enforces license compliance.

Gate letter: Y
Minimum tests: 6
"""

import subprocess
import sys
from pathlib import Path
import shutil
import pytest


# Test Y-01: Current repo passes validation
def test_y01_current_repo_passes():
    """
    Y-01: publish_check_licenses.py exits 0 on current repo.

    Validates that the current repository's LICENSE_LEDGER.md is complete
    and all dependencies are documented with valid licenses.
    """
    result = subprocess.run(
        [sys.executable, "scripts/publish_check_licenses.py"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, (
        f"License check failed on current repo.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
    assert "[PASS]" in result.stdout


# Test Y-02: Lint detects missing dependency
def test_y02_detect_missing_dependency(tmp_path):
    """
    Y-02: Lint detects missing dependency (planted).

    Creates a temporary ledger missing a known dependency and verifies
    the lint script catches it.
    """
    # Backup original ledger
    original_ledger = Path("docs/LICENSE_LEDGER.md")
    backup_ledger = Path("docs/LICENSE_LEDGER.md.bak")
    shutil.copy(original_ledger, backup_ledger)

    try:
        # Modify ledger to remove pytest entry
        content = original_ledger.read_text()
        lines = content.splitlines()
        modified_lines = [line for line in lines if "pytest" not in line.lower()]
        original_ledger.write_text("\n".join(modified_lines))

        # Run validation
        result = subprocess.run(
            [sys.executable, "scripts/publish_check_licenses.py"],
            capture_output=True,
            text=True
        )

        # Should fail with missing dependency error
        assert result.returncode == 1, "Lint should fail when dependency is missing"
        assert "[FAIL]" in result.stdout
        assert "pytest" in result.stdout.lower() or "missing" in result.stdout.lower()

    finally:
        # Restore original ledger
        shutil.move(backup_ledger, original_ledger)


# Test Y-03: Lint detects UNKNOWN license
def test_y03_detect_unknown_license(tmp_path):
    """
    Y-03: Lint detects UNKNOWN license (planted).

    Creates a ledger with an UNKNOWN license field and verifies
    the lint script rejects it.
    """
    # Backup original ledger
    original_ledger = Path("docs/LICENSE_LEDGER.md")
    backup_ledger = Path("docs/LICENSE_LEDGER.md.bak")
    shutil.copy(original_ledger, backup_ledger)

    try:
        # Create a ledger with UNKNOWN license for pytest
        content = original_ledger.read_text()
        # Replace MIT license for pytest with UNKNOWN
        modified_content = content.replace("| pytest | 7.0.0 | MIT |", "| pytest | 7.0.0 | UNKNOWN |")
        original_ledger.write_text(modified_content)

        result = subprocess.run(
            [sys.executable, "scripts/publish_check_licenses.py"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1, "Lint should fail when UNKNOWN license exists"
        assert "[FAIL]" in result.stdout
        assert "UNKNOWN" in result.stdout

    finally:
        # Restore original ledger
        shutil.move(backup_ledger, original_ledger)


# Test Y-04: Lint detects missing required field
def test_y04_detect_missing_field(tmp_path):
    """
    Y-04: Lint detects missing required field (planted).

    Creates a ledger with a missing 'where_used' field and verifies
    the lint script catches the schema violation.
    """
    # Backup original ledger
    original_ledger = Path("docs/LICENSE_LEDGER.md")
    backup_ledger = Path("docs/LICENSE_LEDGER.md.bak")
    shutil.copy(original_ledger, backup_ledger)

    try:
        # Create ledger with missing where_used field (remove last column from pytest row)
        content = original_ledger.read_text()
        lines = content.splitlines()
        modified_lines = []
        for line in lines:
            if "| pytest |" in line:
                # Remove the last column
                parts = line.rsplit("|", 2)
                modified_lines.append(parts[0] + "|")
            else:
                modified_lines.append(line)
        original_ledger.write_text("\n".join(modified_lines))

        result = subprocess.run(
            [sys.executable, "scripts/publish_check_licenses.py"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 1, "Lint should fail when required field is missing"
        assert "[FAIL]" in result.stdout
        # Should report invalid table structure
        assert "Invalid table row" in result.stdout or "columns" in result.stdout

    finally:
        # Restore original ledger
        shutil.move(backup_ledger, original_ledger)


# Test Y-05: Ledger schema validates (all 6 fields present)
def test_y05_schema_validation():
    """
    Y-05: Ledger schema validates (all 6 fields present on every row).

    Verifies that LICENSE_LEDGER.md has all 6 required fields for each dependency:
    dependency, version, license, source_url, redistribution, where_used
    """
    ledger_path = Path("docs/LICENSE_LEDGER.md")
    assert ledger_path.exists(), "LICENSE_LEDGER.md must exist"

    content = ledger_path.read_text()
    lines = content.splitlines()

    in_table = False
    row_count = 0

    for line in lines:
        line = line.strip()

        # Find table header
        if "| dependency | version | license |" in line:
            in_table = True
            # Verify all 6 columns in header
            assert line.count("|") >= 7, "Table header must have 6 columns (7 separators)"
            continue

        # Skip separator
        if in_table and line.startswith("|--"):
            continue

        # End of table
        if in_table and (not line.startswith("|") or line == ""):
            break

        # Validate data rows
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            assert len(parts) == 6, (
                f"Each row must have exactly 6 fields, found {len(parts)} in: {line}"
            )
            row_count += 1

    assert row_count > 0, "Ledger must contain at least one dependency"
    assert row_count >= 10, f"Expected at least 10 dependencies, found {row_count}"


# Test Y-06: Every dep in lockfiles appears in ledger
def test_y06_all_deps_in_ledger():
    """
    Y-06: Every dependency in lockfiles appears in ledger.

    Validates that there are no undocumented dependencies by checking
    that all packages in requirements.txt, pyproject.toml, and package.json
    are present in the LICENSE_LEDGER.md.
    """
    import re
    import json

    # Read ledger
    ledger_path = Path("docs/LICENSE_LEDGER.md")
    ledger_content = ledger_path.read_text()

    # Extract dependency names from ledger (case-insensitive)
    ledger_deps = set()
    for line in ledger_content.splitlines():
        if line.startswith("|") and not line.startswith("|--") and "dependency" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 1:
                ledger_deps.add(parts[0].lower())

    # Collect all lockfile dependencies
    lockfile_deps = set()

    # Python deps from pyproject.toml
    if Path("pyproject.toml").exists():
        content = Path("pyproject.toml").read_text()
        matches = re.findall(r'"([a-zA-Z0-9_-]+)(?:[><=]+[0-9.]+)"', content)
        lockfile_deps.update(m.lower() for m in matches)

    # Python deps from requirements.txt
    if Path("requirements.txt").exists():
        for line in Path("requirements.txt").read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'([a-zA-Z0-9_-]+)', line)
                if match:
                    lockfile_deps.add(match.group(1).lower())

    # Node deps from package.json
    if Path("client/package.json").exists():
        data = json.loads(Path("client/package.json").read_text())
        lockfile_deps.update(dep.lower() for dep in data.get("dependencies", {}).keys())
        lockfile_deps.update(dep.lower() for dep in data.get("devDependencies", {}).keys())

    # Check that all lockfile deps are in ledger
    missing = lockfile_deps - ledger_deps

    assert len(missing) == 0, (
        f"Found {len(missing)} dependencies in lockfiles but not in ledger: "
        f"{', '.join(sorted(missing))}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

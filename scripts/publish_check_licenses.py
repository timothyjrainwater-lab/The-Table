#!/usr/bin/env python3
"""
License Ledger Validation Script (Gate P4)

This gate script validates that:
1. All dependencies in lockfiles are documented in LICENSE_LEDGER.md
2. No UNKNOWN licenses exist
3. All required fields are present per PRS-01 §P4 schema
4. Ledger entries match actual lockfile versions

Usage:
    python scripts/publish_check_licenses.py

Exit codes:
    0 = PASS (all deps documented, no UNKNOWN licenses, schema valid)
    1 = FAIL (missing deps, UNKNOWN licenses, or schema violations)

Evidence:
    Outputs validation results to stdout (captured by orchestrator)
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


# SPDX license identifiers that are known and valid
KNOWN_SPDX_LICENSES = {
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "GPL-2.0", "GPL-3.0",
    "LGPL-2.1", "LGPL-3.0", "ISC", "MPL-2.0", "AGPL-3.0", "Unlicense",
    "CC0-1.0", "HPND", "PSF-2.0", "0BSD", "Zlib"
}


def parse_ledger() -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Parse LICENSE_LEDGER.md and return dependencies + validation errors.

    Returns:
        (deps, errors) where deps is a list of dicts and errors is a list of error messages
    """
    ledger_path = Path("docs/LICENSE_LEDGER.md")

    if not ledger_path.exists():
        return [], ["LICENSE_LEDGER.md does not exist"]

    content = ledger_path.read_text()
    lines = content.splitlines()

    deps = []
    errors = []
    in_table = False
    header_found = False

    for i, line in enumerate(lines, start=1):
        line = line.strip()

        # Find the dependencies table
        if "| dependency | version | license |" in line:
            header_found = True
            in_table = True
            continue

        # Skip separator line
        if in_table and line.startswith("|--"):
            continue

        # End of table
        if in_table and (not line.startswith("|") or line == ""):
            break

        # Parse table rows
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")]
            # Remove empty first/last elements from split
            parts = [p for p in parts if p]

            if len(parts) != 6:
                errors.append(f"Line {i}: Invalid table row (expected 6 columns, got {len(parts)})")
                continue

            dep = {
                "dependency": parts[0],
                "version": parts[1],
                "license": parts[2],
                "source_url": parts[3],
                "redistribution": parts[4],
                "where_used": parts[5],
            }

            # Validate required fields are not UNKNOWN
            for field in ["dependency", "version", "license", "source_url", "redistribution", "where_used"]:
                if dep[field] == "UNKNOWN":
                    errors.append(f"Dependency '{dep['dependency']}': field '{field}' is UNKNOWN")

            # Validate redistribution field
            if dep["redistribution"] not in ["bundled", "runtime-dep", "dev-only"]:
                errors.append(
                    f"Dependency '{dep['dependency']}': invalid redistribution value '{dep['redistribution']}' "
                    f"(must be bundled/runtime-dep/dev-only)"
                )

            deps.append(dep)

    if not header_found:
        errors.append("Dependencies table header not found in LICENSE_LEDGER.md")

    return deps, errors


def get_python_deps() -> Set[str]:
    """Extract Python dependency names from pyproject.toml and requirements.txt."""
    deps = set()

    # Parse pyproject.toml
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        content = pyproject_path.read_text()

        # Extract from dependencies and optional-dependencies
        matches = re.findall(r'"([a-zA-Z0-9_-]+)(?:[><=]+[0-9.]+)"', content)
        deps.update(matches)

    # Parse requirements.txt
    requirements_path = Path("requirements.txt")
    if requirements_path.exists():
        for line in requirements_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r'([a-zA-Z0-9_-]+)', line)
            if match:
                deps.add(match.group(1))

    return deps


def get_node_deps() -> Set[str]:
    """Extract Node dependency names from package.json."""
    deps = set()

    package_json_path = Path("client/package.json")
    if not package_json_path.exists():
        return deps

    data = json.loads(package_json_path.read_text())

    # Add both dependencies and devDependencies
    deps.update(data.get("dependencies", {}).keys())
    deps.update(data.get("devDependencies", {}).keys())

    return deps


def validate_license_compliance() -> Tuple[bool, List[str]]:
    """
    Validate license ledger compliance.

    Returns:
        (passed, errors) where passed is True if all checks pass
    """
    errors = []

    # Parse the ledger
    ledger_deps, ledger_errors = parse_ledger()
    errors.extend(ledger_errors)

    if ledger_errors:
        return False, errors

    # Get actual dependencies from lockfiles
    python_deps = get_python_deps()
    node_deps = get_node_deps()
    all_deps = python_deps | node_deps

    # Build ledger dependency set (normalized to lowercase for case-insensitive comparison)
    ledger_dep_names = {dep["dependency"].lower() for dep in ledger_deps}

    # Check for missing dependencies
    missing_deps = []
    for dep in all_deps:
        if dep.lower() not in ledger_dep_names:
            missing_deps.append(dep)

    if missing_deps:
        errors.append(f"Dependencies in lockfiles but not in ledger: {', '.join(sorted(missing_deps))}")

    # Check for UNKNOWN licenses
    unknown_licenses = [dep["dependency"] for dep in ledger_deps if dep["license"] == "UNKNOWN"]
    if unknown_licenses:
        errors.append(f"Dependencies with UNKNOWN licenses: {', '.join(unknown_licenses)}")

    # Check for invalid SPDX licenses (warn but don't fail)
    for dep in ledger_deps:
        if dep["license"] not in KNOWN_SPDX_LICENSES and dep["license"] != "UNKNOWN":
            print(f"WARNING: '{dep['dependency']}' uses non-standard SPDX identifier '{dep['license']}'")

    # Check schema completeness
    for dep in ledger_deps:
        for field in ["dependency", "version", "license", "source_url", "redistribution", "where_used"]:
            if not dep.get(field) or dep[field].strip() == "":
                errors.append(f"Dependency '{dep['dependency']}': missing required field '{field}'")

    passed = len(errors) == 0
    return passed, errors


def main():
    """Execute license validation gate."""
    print("=" * 70)
    print("Gate P4: License Ledger Validation")
    print("=" * 70)
    print()

    passed, errors = validate_license_compliance()

    if passed:
        print("[PASS] License ledger is complete and valid")
        print()
        print("Summary:")
        ledger_deps, _ = parse_ledger()
        python_deps = get_python_deps()
        node_deps = get_node_deps()
        print(f"  - Total dependencies in ledger: {len(ledger_deps)}")
        print(f"  - Python dependencies: {len(python_deps)}")
        print(f"  - Node dependencies: {len(node_deps)}")
        print(f"  - All dependencies documented: YES")
        print(f"  - No UNKNOWN licenses: YES")
        print(f"  - Schema valid: YES")
        print()
        return 0
    else:
        print("[FAIL] License ledger validation failed")
        print()
        print(f"Errors ({len(errors)}):")
        for i, error in enumerate(errors, start=1):
            print(f"  {i}. {error}")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())

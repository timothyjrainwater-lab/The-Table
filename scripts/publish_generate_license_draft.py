#!/usr/bin/env python3
"""
Draft License Ledger Generator

This is a helper script (not a gate script) that generates a draft LICENSE_LEDGER.md
by scanning lockfiles for dependencies. The builder must manually complete the ledger
with license information, source URLs, redistribution status, and usage notes.

Usage:
    python scripts/publish_generate_license_draft.py

Output:
    docs/LICENSE_LEDGER.md (draft with UNKNOWN fields to be filled manually)
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set


def parse_python_deps() -> List[Dict[str, str]]:
    """Extract Python dependencies from pyproject.toml and requirements.txt."""
    deps = []

    # Parse pyproject.toml
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        content = pyproject_path.read_text()

        # Extract dependencies from [project] dependencies array
        in_deps = False
        for line in content.splitlines():
            if line.strip().startswith("dependencies = ["):
                in_deps = True
                continue
            if in_deps:
                if "]" in line:
                    break
                # Match pattern: "package>=version" or "package==version"
                match = re.search(r'"([a-zA-Z0-9_-]+)([><=]+)([0-9.]+)"', line)
                if match:
                    pkg_name = match.group(1)
                    version_constraint = match.group(3)
                    deps.append({
                        "dependency": pkg_name,
                        "version": version_constraint,
                        "source": "pyproject.toml (runtime)",
                    })

        # Extract optional dependencies (dev/server extras)
        in_optional = False
        current_extra = None
        for line in content.splitlines():
            if "[project.optional-dependencies]" in line:
                in_optional = True
                continue
            if in_optional:
                if line.startswith("["):
                    break
                # Detect extra name (e.g., "server = [")
                extra_match = re.match(r'(\w+)\s*=\s*\[', line)
                if extra_match:
                    current_extra = extra_match.group(1)
                    continue
                # Extract dependency
                match = re.search(r'"([a-zA-Z0-9_-]+)([><=]+)([0-9.]+)"', line)
                if match and current_extra:
                    pkg_name = match.group(1)
                    version_constraint = match.group(3)
                    deps.append({
                        "dependency": pkg_name,
                        "version": version_constraint,
                        "source": f"pyproject.toml ({current_extra} extra)",
                    })

    # Parse requirements.txt
    requirements_path = Path("requirements.txt")
    if requirements_path.exists():
        for line in requirements_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r'([a-zA-Z0-9_-]+)([><=]+)([0-9.]+)', line)
            if match:
                pkg_name = match.group(1)
                version_constraint = match.group(3)
                deps.append({
                    "dependency": pkg_name,
                    "version": version_constraint,
                    "source": "requirements.txt",
                })

    return deps


def parse_node_deps() -> List[Dict[str, str]]:
    """Extract Node dependencies from package.json."""
    deps = []

    package_json_path = Path("client/package.json")
    if not package_json_path.exists():
        return deps

    data = json.loads(package_json_path.read_text())

    # Runtime dependencies
    for pkg_name, version in data.get("dependencies", {}).items():
        # Clean version (remove ^ or ~)
        clean_version = version.lstrip("^~")
        deps.append({
            "dependency": pkg_name,
            "version": clean_version,
            "source": "package.json (runtime)",
        })

    # Dev dependencies
    for pkg_name, version in data.get("devDependencies", {}).items():
        clean_version = version.lstrip("^~")
        deps.append({
            "dependency": pkg_name,
            "version": clean_version,
            "source": "package.json (dev)",
        })

    return deps


def deduplicate_deps(deps: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Remove duplicate dependencies, keeping the first occurrence."""
    seen: Set[str] = set()
    unique = []
    for dep in deps:
        key = dep["dependency"]
        if key not in seen:
            seen.add(key)
            unique.append(dep)
    return unique


def generate_ledger_markdown(deps: List[Dict[str, str]]) -> str:
    """Generate the LICENSE_LEDGER.md markdown content."""
    lines = [
        "# License Ledger",
        "",
        "**Document ID:** LICENSE_LEDGER",
        "**Version:** DRAFT",
        "**Status:** INCOMPLETE — Builder must manually fill UNKNOWN fields",
        "",
        "This ledger documents all dependencies (Python + Node) with their license information.",
        "All fields are required per PRS-01 §P4.",
        "",
        "## Schema",
        "",
        "| Field | Description |",
        "|-------|-------------|",
        "| `dependency` | Package name |",
        "| `version` | Pinned version |",
        "| `license` | SPDX identifier (e.g., MIT, Apache-2.0) |",
        "| `source_url` | PyPI/npm/GitHub URL |",
        "| `redistribution` | `bundled` / `runtime-dep` / `dev-only` |",
        "| `where_used` | Module or subsystem that imports it |",
        "",
        "## Dependencies",
        "",
        "| dependency | version | license | source_url | redistribution | where_used |",
        "|------------|---------|---------|------------|----------------|------------|",
    ]

    for dep in deps:
        dep_name = dep["dependency"]
        version = dep["version"]

        # Infer redistribution from source
        if "dev" in dep["source"].lower():
            redistribution = "dev-only"
        else:
            redistribution = "runtime-dep"

        lines.append(
            f"| {dep_name} | {version} | UNKNOWN | UNKNOWN | {redistribution} | UNKNOWN |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**Builder Notes:**")
    lines.append("- Fill all UNKNOWN fields with accurate information")
    lines.append("- License: Use SPDX identifiers (MIT, Apache-2.0, BSD-3-Clause, etc.)")
    lines.append("- source_url: Link to PyPI, npm, or GitHub repository")
    lines.append("- where_used: Module/subsystem that imports this dependency")
    lines.append("")

    return "\n".join(lines)


def main():
    """Generate draft LICENSE_LEDGER.md."""
    print("Scanning dependencies...")

    python_deps = parse_python_deps()
    node_deps = parse_node_deps()

    all_deps = python_deps + node_deps
    all_deps = deduplicate_deps(all_deps)

    print(f"Found {len(all_deps)} dependencies:")
    print(f"  - Python: {len(python_deps)}")
    print(f"  - Node: {len(node_deps)}")

    ledger_content = generate_ledger_markdown(all_deps)

    output_path = Path("docs/LICENSE_LEDGER.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(ledger_content)

    print(f"\nDraft ledger written to: {output_path}")
    print("\nNext steps:")
    print("1. Manually fill all UNKNOWN fields in the ledger")
    print("2. Verify license information from PyPI/npm/GitHub")
    print("3. Run: python scripts/publish_check_licenses.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())

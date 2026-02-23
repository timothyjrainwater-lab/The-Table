#!/usr/bin/env python3
"""
Gate AB: Documentation Compliance Validator (PRS-01 §P9)

Validates that required project documentation exists and is complete:
1. docs/PRIVACY.md — has all 4 required sections per PRS-01 §7
2. docs/OGL_NOTICE.md — exists
3. All directory paths referenced in PRIVACY.md exist on disk

Usage:
    python scripts/publish_check_docs.py

Exit codes:
    0 = PASS (all checks pass)
    1 = FAIL (violations found)

Evidence:
    Outputs validation results to stdout
"""

import re
import sys
from pathlib import Path


# Required section headings in PRIVACY.md (per PRS-01 §P9)
REQUIRED_PRIVACY_SECTIONS = [
    "Data Locality",
    "Microphone",
    "Retention Defaults",
    "Delete Everything",
]


def find_project_root() -> Path:
    """Find the project root (directory containing docs/)."""
    # When run from project root or scripts/
    cwd = Path.cwd()
    if (cwd / "docs").is_dir():
        return cwd
    if (cwd.parent / "docs").is_dir():
        return cwd.parent
    # Fallback: relative to this script
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent


def check_privacy(root: Path) -> list:
    """Validate docs/PRIVACY.md exists and has required sections.

    Returns list of error strings (empty = pass).
    """
    errors = []
    privacy_path = root / "docs" / "PRIVACY.md"

    if not privacy_path.exists():
        errors.append("docs/PRIVACY.md does not exist")
        return errors

    content = privacy_path.read_text(encoding="utf-8")

    # Check required sections
    for section in REQUIRED_PRIVACY_SECTIONS:
        # Match markdown heading with section name (## or ### etc.)
        pattern = r"^#{1,4}\s+" + re.escape(section)
        if not re.search(pattern, content, re.MULTILINE):
            errors.append(f"Missing required section: '{section}'")

    # Extract referenced directory paths (backtick-quoted, ending with /)
    # Pattern matches `logs/`, `oracle_db/`, etc.
    referenced_paths = re.findall(r"`([a-zA-Z_][a-zA-Z0-9_]*/)`", content)

    for ref_path in referenced_paths:
        full_path = root / ref_path
        if not full_path.exists():
            errors.append(f"Referenced path does not exist: {ref_path}")

    return errors


def check_ogl(root: Path) -> list:
    """Validate docs/OGL_NOTICE.md exists.

    Returns list of error strings (empty = pass).
    """
    errors = []
    ogl_path = root / "docs" / "OGL_NOTICE.md"

    if not ogl_path.exists():
        errors.append("docs/OGL_NOTICE.md does not exist")

    return errors


def main() -> int:
    """Execute Gate AB documentation validation."""
    print("=" * 70)
    print("Gate AB: Documentation Compliance (PRS-01 P9)")
    print("=" * 70)
    print()

    root = find_project_root()
    all_errors = []

    # Check PRIVACY.md
    privacy_errors = check_privacy(root)
    all_errors.extend(privacy_errors)

    # Check OGL_NOTICE.md
    ogl_errors = check_ogl(root)
    all_errors.extend(ogl_errors)

    if not all_errors:
        print("[PASS] Documentation validation successful")
        print()
        print("Summary:")
        print("  - docs/PRIVACY.md: present, all 4 sections found")
        print("  - docs/OGL_NOTICE.md: present")
        print("  - All referenced paths exist")
        return 0
    else:
        print("[FAIL] Documentation validation failed")
        print()
        print(f"Errors ({len(all_errors)}):")
        for i, error in enumerate(all_errors, start=1):
            print(f"  {i}. {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

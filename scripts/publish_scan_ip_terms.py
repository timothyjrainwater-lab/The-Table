#!/usr/bin/env python3
"""P8 IP String Hygiene — Trademarked/Copyrighted Term Detection (PRS-01 §3).

Scans source files for non-OGL proper nouns and product identity terms.

Usage:
    python scripts/publish_scan_ip_terms.py

Exit code 0 if clean (or all matches are in exceptions), 1 if violations found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from _publish_scan_utils import (
    Finding,
    exit_with_findings,
    filter_by_extension,
    get_tracked_files,
    is_binary_file,
    load_exceptions,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DENYLIST_FILE = Path("scripts/ip_denylist.txt")  # Relative to CWD (repo root)
EXCEPTIONS_FILE = Path("scripts/ip_exceptions.txt")  # Relative to CWD (repo root)

# File extensions to scan
SCAN_EXTENSIONS = [".py", ".md", ".txt", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml"]


# ---------------------------------------------------------------------------
# Denylist loading
# ---------------------------------------------------------------------------

def load_denylist() -> list[tuple[str, re.Pattern[str]]]:
    """Load IP denylist from file.

    Format: One term per line. Case-insensitive matching. Lines starting with # are comments.

    Returns:
        List of (term, compiled_pattern) tuples.
    """
    if not DENYLIST_FILE.exists():
        return []

    patterns: list[tuple[str, re.Pattern[str]]] = []
    with open(DENYLIST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Build case-insensitive word boundary pattern
            # Use \b for word boundaries to avoid partial matches
            pattern = re.compile(r"\b" + re.escape(stripped) + r"\b", re.IGNORECASE)
            patterns.append((stripped, pattern))

    return patterns


# ---------------------------------------------------------------------------
# Scan logic
# ---------------------------------------------------------------------------

def scan_ip_terms() -> list[Finding]:
    """Scan tracked files for IP denylist terms.

    Returns:
        List of Finding objects for violations (excluding exceptions).
    """
    findings: list[Finding] = []
    denylist = load_denylist()
    exceptions = load_exceptions(EXCEPTIONS_FILE)
    tracked_files = get_tracked_files()

    # Filter to scannable file types
    scannable_files = filter_by_extension(tracked_files, SCAN_EXTENSIONS)

    for file_path in scannable_files:
        # Skip binary files
        if is_binary_file(file_path):
            continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, start=1):
                    for term, pattern in denylist:
                        if pattern.search(line):
                            # Normalize path for exception matching (forward slashes)
                            normalized_path = file_path.replace("\\", "/")

                            # Check if this match is in exceptions
                            if term in exceptions and normalized_path in exceptions[term]:
                                continue  # Exception granted

                            findings.append(
                                Finding(
                                    file_path=file_path,
                                    line_number=line_num,
                                    rule="P8-IP",
                                    message=f"IP denylist term detected: {term!r}",
                                )
                            )
        except (OSError, IOError):
            pass  # Skip unreadable files

    return findings


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Run P8 IP term scan."""
    try:
        tracked_files = get_tracked_files()
        scannable_files = filter_by_extension(tracked_files, SCAN_EXTENSIONS)
        findings = scan_ip_terms()
        return exit_with_findings(findings, len(scannable_files), "P8 IP Term Scan")
    except Exception as e:
        print(f"ERROR: P8 IP Term Scan failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

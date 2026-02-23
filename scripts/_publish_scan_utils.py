#!/usr/bin/env python3
"""Shared utilities for PRS-01 publish gate scan scripts.

Provides common functionality:
- Git tracked file enumeration (git ls-files wrapper)
- Pattern matching (glob, regex)
- Evidence logging in machine-readable format
- Exit code management
"""
from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Finding:
    """A single scan finding (violation)."""
    file_path: str
    line_number: int | None
    rule: str
    message: str

    def __str__(self) -> str:
        """Machine-readable format: file:line [rule] message"""
        loc = f"{self.file_path}:{self.line_number}" if self.line_number else self.file_path
        return f"{loc} [{self.rule}] {self.message}"


# ---------------------------------------------------------------------------
# Git utilities
# ---------------------------------------------------------------------------

def get_tracked_files() -> list[str]:
    """Return all git tracked files in the repository.

    Returns:
        List of relative file paths from repo root.

    Raises:
        RuntimeError: If git ls-files fails.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"git ls-files failed: {e.stderr}") from e


def is_binary_file(file_path: str | Path) -> bool:
    """Check if a file is binary (heuristic: contains null bytes in first 8KB).

    Args:
        file_path: Path to file to check.

    Returns:
        True if file appears to be binary, False otherwise.
    """
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(8192)
            return b"\x00" in chunk
    except (OSError, IOError):
        return True  # Treat unreadable files as binary


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------

def matches_any_pattern(path: str, patterns: list[str]) -> tuple[bool, str | None]:
    """Check if a path matches any glob pattern.

    Args:
        path: File path to check.
        patterns: List of glob patterns (e.g., "*.py", "*.txt").

    Returns:
        Tuple of (matched, matching_pattern). If no match, pattern is None.
    """
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True, pattern
    return False, None


def matches_any_directory(path: str, dir_patterns: list[str]) -> tuple[bool, str | None]:
    """Check if a path contains any of the specified directory patterns.

    Args:
        path: File path to check.
        dir_patterns: List of directory patterns (e.g., "__pycache__/", "node_modules/").

    Returns:
        Tuple of (matched, matching_pattern). If no match, pattern is None.
    """
    parts = Path(path).parts
    for pattern in dir_patterns:
        pattern_clean = pattern.rstrip("/")
        if pattern_clean in parts:
            return True, pattern
    return False, None


def scan_file_content(
    file_path: str | Path,
    pattern: re.Pattern[str],
    skip_binary: bool = True,
) -> list[tuple[int, str]]:
    """Scan file content for regex matches.

    Args:
        file_path: Path to file to scan.
        pattern: Compiled regex pattern to search for.
        skip_binary: If True, skip binary files.

    Returns:
        List of (line_number, line_text) tuples for matches.
    """
    if skip_binary and is_binary_file(file_path):
        return []

    matches: list[tuple[int, str]] = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, start=1):
                if pattern.search(line):
                    matches.append((line_num, line.rstrip("\n")))
    except (OSError, IOError):
        pass  # Skip unreadable files

    return matches


# ---------------------------------------------------------------------------
# Evidence logging
# ---------------------------------------------------------------------------

def log_findings(findings: list[Finding], summary: str) -> None:
    """Log findings to stdout in machine-readable format.

    Args:
        findings: List of Finding objects.
        summary: Summary message (e.g., "PASS: 0 violations" or "FAIL: 5 violations").
    """
    print(summary)
    if findings:
        print()
        for finding in findings:
            print(finding)


def exit_with_findings(findings: list[Finding], total_files: int, scan_name: str) -> int:
    """Log findings and exit with appropriate code.

    Args:
        findings: List of Finding objects.
        total_files: Total number of files scanned.
        scan_name: Name of the scan (for summary message).

    Returns:
        Exit code: 0 if no findings, 1 if findings exist.
    """
    if not findings:
        log_findings([], f"PASS: {scan_name} — {total_files} files scanned, 0 violations.")
        return 0
    else:
        log_findings(
            findings,
            f"FAIL: {scan_name} — {len(findings)} violation(s) in {total_files} files scanned.",
        )
        return 1


# ---------------------------------------------------------------------------
# File filtering
# ---------------------------------------------------------------------------

def filter_by_extension(files: list[str], extensions: list[str]) -> list[str]:
    """Filter files by extension.

    Args:
        files: List of file paths.
        extensions: List of extensions (with leading dot, e.g., [".py", ".md"]).

    Returns:
        Filtered list of files matching any extension.
    """
    return [f for f in files if any(f.endswith(ext) for ext in extensions)]


def load_baseline(baseline_path: str | Path) -> set[str]:
    """Load baseline exclusions from a file.

    Format: One pattern per line. Lines starting with # are comments. Blank lines ignored.

    Args:
        baseline_path: Path to baseline file.

    Returns:
        Set of baseline patterns (stripped, non-empty, non-comment).
    """
    path = Path(baseline_path)
    if not path.exists():
        return set()

    baseline = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                baseline.add(stripped)
    return baseline


def load_exceptions(exceptions_path: str | Path) -> dict[str, dict[str, str]]:
    """Load exception list from file.

    Format: term|file_path|justification (one per line, pipe-separated).

    Args:
        exceptions_path: Path to exceptions file.

    Returns:
        Dict mapping term -> {file_path -> justification}.
    """
    path = Path(exceptions_path)
    if not path.exists():
        return {}

    exceptions: dict[str, dict[str, str]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            parts = stripped.split("|", 2)
            if len(parts) != 3:
                print(
                    f"Warning: Invalid exception line {line_num}: {line!r}",
                    file=sys.stderr,
                )
                continue

            term, file_path, justification = parts
            term = term.strip()
            file_path = file_path.strip()
            justification = justification.strip()

            if term not in exceptions:
                exceptions[term] = {}
            exceptions[term][file_path] = justification

    return exceptions

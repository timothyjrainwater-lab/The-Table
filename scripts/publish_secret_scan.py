#!/usr/bin/env python3
"""P5 Secret Scan — High-Confidence Secret Detection (PRS-01 §3).

Scans all tracked files for API keys, tokens, passwords, and private keys.

Usage:
    python scripts/publish_secret_scan.py

Exit code 0 if clean (or all matches are in baseline), 1 if violations found.
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
    get_tracked_files,
    is_binary_file,
    load_baseline,
    scan_file_content,
)


# ---------------------------------------------------------------------------
# Secret patterns (high-confidence regex)
# ---------------------------------------------------------------------------

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # API keys (common prefixes)
    ("API-KEY-SK", re.compile(r"\bsk-[A-Za-z0-9]{20,}")),  # OpenAI, Anthropic style
    ("API-KEY-PK", re.compile(r"\bpk_(?:live|test)_[A-Za-z0-9]{20,}")),  # Stripe
    ("API-KEY-AKIA", re.compile(r"\bAKIA[A-Z0-9]{16}")),  # AWS access key
    ("API-KEY-GENERIC", re.compile(r'\b(?:api[_-]?key|apikey)\s*[=:]\s*["\'][A-Za-z0-9+/]{20,}["\']', re.IGNORECASE)),

    # Private key headers (PEM format)
    ("PRIVATE-KEY-PEM", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),

    # Password/secret/token assignments with literal values
    ("PASSWORD-LITERAL", re.compile(r'\b(?:password|passwd|pwd)\s*[=:]\s*["\'][^"\']{8,}["\']', re.IGNORECASE)),
    ("SECRET-LITERAL", re.compile(r'\b(?:secret|api_secret)\s*[=:]\s*["\'][A-Za-z0-9+/]{16,}["\']', re.IGNORECASE)),
    ("TOKEN-LITERAL", re.compile(r'\b(?:token|auth_token|access_token)\s*[=:]\s*["\'][A-Za-z0-9+/._-]{20,}["\']', re.IGNORECASE)),

    # Base64 blobs in config files (>40 chars, likely credentials)
    ("BASE64-BLOB", re.compile(r'\b[A-Za-z0-9+/]{40,}={0,2}\b')),

    # GitHub tokens
    ("GITHUB-TOKEN", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}")),

    # JWT tokens (3 base64 segments separated by dots)
    ("JWT-TOKEN", re.compile(r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
]

# File extensions to scan for BASE64-BLOB pattern (config files)
BASE64_SCAN_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env"}

# Files to skip for BASE64-BLOB pattern only (contain legitimate base64 data)
# npm integrity hashes (SHA-512) and image thumbnails are not secrets
SECRET_SCAN_SKIP_FILES = {
    "client/package-lock.json",
    "config/REUSE_DECISION.json",
}

# Directories to exclude from scan
EXCLUDE_DIRECTORIES = [".git/", "node_modules/", "__pycache__/"]


# ---------------------------------------------------------------------------
# Baseline management
# ---------------------------------------------------------------------------

BASELINE_FILE = Path("scripts/secret_scan_baseline.txt")  # Relative to CWD (repo root)


def normalize_match(file_path: str, line_num: int, pattern_id: str, line_text: str) -> str:
    """Normalize a match for baseline comparison.

    Format: file_path:line_num:pattern_id:line_text_stripped

    Args:
        file_path: File path where match was found.
        line_num: Line number of match.
        pattern_id: Secret pattern ID.
        line_text: Full line text.

    Returns:
        Normalized string for baseline comparison.
    """
    # Normalize path separators to forward slashes for cross-platform compatibility
    normalized_path = file_path.replace("\\", "/")
    return f"{normalized_path}:{line_num}:{pattern_id}:{line_text.strip()}"


# ---------------------------------------------------------------------------
# Scan logic
# ---------------------------------------------------------------------------

def should_scan_for_base64(file_path: str) -> bool:
    """Check if file should be scanned for base64 blobs.

    Args:
        file_path: File path to check.

    Returns:
        True if file is a config file type.
    """
    return Path(file_path).suffix in BASE64_SCAN_EXTENSIONS


def scan_secrets() -> list[Finding]:
    """Scan all tracked files for secrets.

    Returns:
        List of Finding objects for violations (excluding baseline matches).
    """
    findings: list[Finding] = []
    baseline = load_baseline(BASELINE_FILE)
    tracked_files = get_tracked_files()

    for file_path in tracked_files:
        # Skip excluded directories
        if any(excl in file_path for excl in EXCLUDE_DIRECTORIES):
            continue

        # Skip binary files
        if is_binary_file(file_path):
            continue

        # Scan for each pattern
        for pattern_id, pattern in SECRET_PATTERNS:
            # BASE64-BLOB only scanned in config files
            if pattern_id == "BASE64-BLOB" and not should_scan_for_base64(file_path):
                continue

            # Skip BASE64-BLOB for files with legitimate base64 data (npm hashes, image thumbnails)
            if pattern_id == "BASE64-BLOB" and file_path.replace("\\", "/") in SECRET_SCAN_SKIP_FILES:
                continue

            matches = scan_file_content(file_path, pattern, skip_binary=True)
            for line_num, line_text in matches:
                # Check if in baseline
                normalized = normalize_match(file_path, line_num, pattern_id, line_text)
                if normalized in baseline:
                    continue  # Baseline exclusion

                findings.append(
                    Finding(
                        file_path=file_path,
                        line_number=line_num,
                        rule=f"P5-{pattern_id}",
                        message=f"High-confidence secret detected: {pattern_id}",
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Run P5 secret scan."""
    try:
        tracked_files = get_tracked_files()
        findings = scan_secrets()
        return exit_with_findings(findings, len(tracked_files), "P5 Secret Scan")
    except Exception as e:
        print(f"ERROR: P5 Secret Scan failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

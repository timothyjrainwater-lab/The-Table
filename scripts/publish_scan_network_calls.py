#!/usr/bin/env python3
"""P6 Offline Guarantee — Static Network Call Scanner

WO-PRS-OFFLINE-001 Gate Z

Scans Python and TypeScript source files for network client imports and verifies
they are either:
1. Behind an explicit opt-in config gate (defaults to off), or
2. Listed in the exceptions file with justification

Network patterns detected (per PRS-01 §P6):
- Python: socket, requests, urllib, http.client
- TypeScript: fetch, axios, XMLHttpRequest, WebSocket

Exit codes:
    0 — All network imports are gated or excepted (PASS)
    1 — Found ungated network imports (FAIL)

Usage:
    python scripts/publish_scan_network_calls.py
    python scripts/publish_scan_network_calls.py --exceptions scripts/offline_exceptions.txt
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Set


class NetworkImport(NamedTuple):
    """Detected network import."""
    file_path: str
    line_number: int
    pattern: str
    line_content: str


class ExceptionEntry(NamedTuple):
    """Exception entry from exceptions file."""
    file_path: str
    import_name: str
    justification: str


# Network patterns per PRS-01 §P6
PYTHON_PATTERNS = [
    r'\bimport\s+socket\b',
    r'\bfrom\s+socket\s+import\b',
    r'\bimport\s+requests\b',
    r'\bfrom\s+requests\s+import\b',
    r'\bimport\s+urllib\b',
    r'\bfrom\s+urllib\b',
    r'\bimport\s+http\.client\b',
    r'\bfrom\s+http\.client\s+import\b',
    r'\bimport\s+http\b',
    r'\bfrom\s+http\s+import\b',
]

TYPESCRIPT_PATTERNS = [
    r'\bfetch\s*\(',
    r'\baxios\b',
    r'\bXMLHttpRequest\b',
    r'\bnew\s+WebSocket\s*\(',
    r'\bWebSocket\s*\(',
]

# Opt-in guard patterns — code must be inside conditional checking a config flag
# Examples:
#   if config.get("network_enabled"):
#   if settings.ALLOW_NETWORK:
#   if self.network_mode:
OPT_IN_GUARD_PATTERNS = [
    r'if\s+.*\b(network|remote|api|online|web).*:',
    r'if\s+config\.get\s*\(\s*["\'].*network.*["\']\s*\)',
    r'if\s+settings\.\w*NETWORK\w*',
]


def load_exceptions(exceptions_path: Path) -> List[ExceptionEntry]:
    """Load exceptions from file.

    Format: file_path|import_name|justification
    """
    if not exceptions_path.exists():
        return []

    exceptions = []
    for line in exceptions_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split('|', maxsplit=2)
        if len(parts) != 3:
            print(f"[WARN] Malformed exception line: {line}", file=sys.stderr)
            continue
        exceptions.append(ExceptionEntry(
            file_path=parts[0].strip(),
            import_name=parts[1].strip(),
            justification=parts[2].strip(),
        ))
    return exceptions


def is_excepted(import_: NetworkImport, exceptions: List[ExceptionEntry], root: Path) -> bool:
    """Check if import matches an exception."""
    for exc in exceptions:
        # Normalize paths for comparison (handle both Unix and Windows separators)
        # Convert absolute path to relative path from root
        import_path = Path(import_.file_path)
        try:
            import_path_rel = import_path.relative_to(root).as_posix()
        except ValueError:
            # If not relative to root, use as-is
            import_path_rel = import_path.as_posix()

        exc_path_normalized = Path(exc.file_path).as_posix()

        if import_path_rel == exc_path_normalized:
            # Check if the pattern name matches the exception import name
            if exc.import_name in import_.pattern or exc.import_name in import_.line_content:
                return True
    return False


def is_behind_guard(file_content: str, line_number: int) -> bool:
    """Check if the import at line_number is inside an opt-in guard block.

    Simplified heuristic: scan backwards from line_number for an if statement
    matching opt-in guard patterns. If found within reasonable distance (say 10 lines),
    and indentation suggests we're inside that block, consider it gated.
    """
    lines = file_content.splitlines()
    if line_number >= len(lines):
        return False

    current_indent = len(lines[line_number]) - len(lines[line_number].lstrip())

    # Scan backwards up to 20 lines for a guard pattern
    for i in range(max(0, line_number - 20), line_number):
        line = lines[i]
        line_indent = len(line) - len(line.lstrip())

        # Only consider lines with less indentation (potential parent scope)
        if line_indent >= current_indent:
            continue

        for guard_pattern in OPT_IN_GUARD_PATTERNS:
            if re.search(guard_pattern, line, re.IGNORECASE):
                return True

    return False


def scan_file_python(file_path: Path) -> List[NetworkImport]:
    """Scan a Python file for network imports."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"[WARN] Could not read {file_path}: {e}", file=sys.stderr)
        return []

    imports = []
    lines = content.splitlines()

    for line_num, line in enumerate(lines):
        for pattern in PYTHON_PATTERNS:
            if re.search(pattern, line):
                imports.append(NetworkImport(
                    file_path=str(file_path),
                    line_number=line_num + 1,
                    pattern=pattern,
                    line_content=line.strip(),
                ))

    return imports


def scan_file_typescript(file_path: Path) -> List[NetworkImport]:
    """Scan a TypeScript file for network calls."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"[WARN] Could not read {file_path}: {e}", file=sys.stderr)
        return []

    imports = []
    lines = content.splitlines()

    for line_num, line in enumerate(lines):
        # Skip comments
        if line.strip().startswith('//') or line.strip().startswith('*'):
            continue

        for pattern in TYPESCRIPT_PATTERNS:
            if re.search(pattern, line):
                imports.append(NetworkImport(
                    file_path=str(file_path),
                    line_number=line_num + 1,
                    pattern=pattern,
                    line_content=line.strip(),
                ))

    return imports


def scan_codebase(root: Path, exceptions: List[ExceptionEntry]) -> Dict[str, List[NetworkImport]]:
    """Scan all Python and TypeScript source files.

    Returns:
        Dict with keys 'gated', 'excepted', 'ungated' mapping to lists of NetworkImport
    """
    all_imports: List[NetworkImport] = []

    # Scan Python files
    for py_file in root.rglob('*.py'):
        # Skip node_modules, venv, build artifacts
        if any(part in py_file.parts for part in ['node_modules', 'venv', '__pycache__', '.venv', '.venvs', 'build', 'dist', 'site-packages']):
            continue
        all_imports.extend(scan_file_python(py_file))

    # Scan TypeScript files (skip node_modules)
    for ts_file in root.rglob('*.ts'):
        if 'node_modules' in ts_file.parts:
            continue
        all_imports.extend(scan_file_typescript(ts_file))

    for tsx_file in root.rglob('*.tsx'):
        if 'node_modules' in tsx_file.parts:
            continue
        all_imports.extend(scan_file_typescript(tsx_file))

    # Categorize imports
    gated = []
    excepted = []
    ungated = []

    for import_ in all_imports:
        if is_excepted(import_, exceptions, root):
            excepted.append(import_)
        else:
            # Check if behind guard
            try:
                file_content = Path(import_.file_path).read_text(encoding='utf-8')
                if is_behind_guard(file_content, import_.line_number - 1):
                    gated.append(import_)
                else:
                    ungated.append(import_)
            except Exception:
                # If can't read file, assume ungated
                ungated.append(import_)

    return {
        'gated': gated,
        'excepted': excepted,
        'ungated': ungated,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='P6 Offline Guarantee — Static Network Call Scanner')
    parser.add_argument('--exceptions', type=Path, default=Path('scripts/offline_exceptions.txt'),
                        help='Path to exceptions file (default: scripts/offline_exceptions.txt)')
    parser.add_argument('--root', type=Path, default=Path('.'),
                        help='Root directory to scan (default: current directory)')
    args = parser.parse_args()

    root = args.root.resolve()
    exceptions_path = args.exceptions

    print(f"P6 OFFLINE GUARANTEE — Static Network Call Scanner")
    print(f"Root: {root}")
    print(f"Exceptions file: {exceptions_path}")
    print()

    exceptions = load_exceptions(exceptions_path)
    print(f"Loaded {len(exceptions)} exception(s)")
    print()

    results = scan_codebase(root, exceptions)

    # Report findings
    print(f"=== SCAN RESULTS ===")
    print(f"Gated imports (behind opt-in config): {len(results['gated'])}")
    print(f"Excepted imports (in exceptions file): {len(results['excepted'])}")
    print(f"Ungated imports (VIOLATIONS): {len(results['ungated'])}")
    print()

    if results['gated']:
        print("--- Gated Imports ---")
        for imp in results['gated']:
            print(f"  {imp.file_path}:{imp.line_number} — {imp.line_content}")
        print()

    if results['excepted']:
        print("--- Excepted Imports ---")
        for imp in results['excepted']:
            print(f"  {imp.file_path}:{imp.line_number} — {imp.line_content}")
        print()

    if results['ungated']:
        print("--- UNGATED IMPORTS (VIOLATIONS) ---")
        for imp in results['ungated']:
            print(f"  {imp.file_path}:{imp.line_number} — {imp.line_content}")
        print()
        print("FAIL: Found ungated network imports. Either:")
        print("  1. Add opt-in config guards around these imports, or")
        print("  2. Add them to the exceptions file with justification")
        return 1

    print("PASS: All network imports are either gated or excepted.")
    return 0


if __name__ == '__main__':
    sys.exit(main())

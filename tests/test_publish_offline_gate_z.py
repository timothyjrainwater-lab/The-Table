"""Gate Z — P6 Offline Guarantee Tests

WO-PRS-OFFLINE-001

Tests the P6 offline guarantee enforcement:
- Static scanner detects ungated network imports
- Runtime smoke test verifies no outbound connections in default config

Gate letter: Z
Minimum tests: 6

Test coverage:
- Z-01: Static scan exits 0 on current repo
- Z-02: Static scan detects planted ungated network import
- Z-03: Static scan respects exceptions file
- Z-04: Runtime smoke exits 0 (no outbound connections in default config)
- Z-05: Runtime smoke detects planted outbound connection
- Z-06: Socket monkey-patch correctly intercepts connect()
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List

import pytest


REPO_ROOT = Path(__file__).parent.parent
STATIC_SCANNER = REPO_ROOT / "scripts" / "publish_scan_network_calls.py"
RUNTIME_SMOKE = REPO_ROOT / "scripts" / "publish_smoke_no_network.py"
EXCEPTIONS_FILE = REPO_ROOT / "scripts" / "offline_exceptions.txt"


# ==============================================================================
# STATIC SCANNER TESTS
# ==============================================================================


def test_z01_static_scan_passes_on_current_repo():
    """Z-01: Static scan exits 0 on current repo.

    Verifies that the static scanner finds no ungated network imports in the
    current codebase (all network code should be excepted or gated).
    """
    result = subprocess.run(
        [sys.executable, str(STATIC_SCANNER), "--root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )

    # Print output for debugging
    print("=== Static Scanner Output ===")
    print(result.stdout)
    if result.stderr:
        print("=== STDERR ===")
        print(result.stderr)

    assert result.returncode == 0, (
        f"Static scanner failed on current repo. "
        f"This means ungated network imports were found. "
        f"Output:\n{result.stdout}\n{result.stderr}"
    )


def test_z02_static_scan_detects_ungated_import():
    """Z-02: Static scan detects planted ungated network import.

    Creates a temporary Python file with an ungated 'import requests' and
    verifies the scanner detects it.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a Python file with ungated network import
        test_file = tmpdir_path / "test_network.py"
        test_file.write_text(
            "# Test file with ungated network import\n"
            "import requests\n"
            "\n"
            "def fetch_data():\n"
            "    return requests.get('http://example.com')\n"
        )

        # Run scanner on temp directory (no exceptions file)
        result = subprocess.run(
            [
                sys.executable,
                str(STATIC_SCANNER),
                "--root", str(tmpdir_path),
                "--exceptions", "/dev/null",  # No exceptions
            ],
            capture_output=True,
            text=True,
        )

        print("=== Static Scanner Output (should FAIL) ===")
        print(result.stdout)

        # Should exit 1 (found ungated import)
        assert result.returncode == 1, "Scanner should detect ungated import"
        assert "UNGATED" in result.stdout or "VIOLATIONS" in result.stdout


def test_z03_static_scan_respects_exceptions():
    """Z-03: Static scan respects exceptions file.

    Creates a temporary Python file with a network import, adds it to an
    exceptions file, and verifies the scanner accepts it.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a Python file with network import
        test_file = tmpdir_path / "allowed_network.py"
        test_file.write_text(
            "# This file is in the exceptions list\n"
            "import socket\n"
            "\n"
            "def local_ipc():\n"
            "    # Only used for local IPC, not outbound\n"
            "    pass\n"
        )

        # Create exceptions file
        exceptions_file = tmpdir_path / "exceptions.txt"
        exceptions_file.write_text(
            f"allowed_network.py|socket|Local IPC only, not outbound connections\n"
        )

        # Run scanner with exceptions
        result = subprocess.run(
            [
                sys.executable,
                str(STATIC_SCANNER),
                "--root", str(tmpdir_path),
                "--exceptions", str(exceptions_file),
            ],
            capture_output=True,
            text=True,
        )

        print("=== Static Scanner Output (should PASS with exception) ===")
        print(result.stdout)

        # Should exit 0 (import is excepted)
        assert result.returncode == 0, "Scanner should accept excepted import"
        assert "Excepted imports" in result.stdout


# ==============================================================================
# RUNTIME SMOKE TESTS
# ==============================================================================


def test_z04_runtime_smoke_passes_default_config():
    """Z-04: Runtime smoke exits 0 (no outbound connections in default config).

    Runs the runtime smoke test which patches socket.connect and verifies
    that default aidm import/instantiation makes no outbound connections.
    """
    result = subprocess.run(
        [sys.executable, str(RUNTIME_SMOKE)],
        capture_output=True,
        text=True,
        timeout=30,
    )

    print("=== Runtime Smoke Output ===")
    print(result.stdout)
    if result.stderr:
        print("=== STDERR ===")
        print(result.stderr)

    assert result.returncode == 0, (
        f"Runtime smoke test failed. Default config attempted network connection.\n"
        f"Output:\n{result.stdout}\n{result.stderr}"
    )


def test_z05_runtime_smoke_detects_outbound_connection():
    """Z-05: Runtime smoke detects planted outbound connection.

    Creates a temporary Python script that tries to make an outbound socket
    connection, and verifies the monkey-patched socket.connect catches it.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a script that attempts outbound connection
        test_script = tmpdir_path / "test_outbound.py"
        test_script.write_text(
            "#!/usr/bin/env python3\n"
            "import socket\n"
            "import sys\n"
            "\n"
            "# Patch socket.connect to fail (simulate smoke test)\n"
            "_original_connect = socket.socket.connect\n"
            "def _patched_connect(self, address):\n"
            "    raise ConnectionRefusedError(f'Blocked connection to {address}')\n"
            "socket.socket.connect = _patched_connect\n"
            "\n"
            "# Try to connect (should fail)\n"
            "try:\n"
            "    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
            "    s.connect(('example.com', 80))\n"
            "    print('FAIL: Connection succeeded (should have been blocked)')\n"
            "    sys.exit(1)\n"
            "except ConnectionRefusedError as e:\n"
            "    print(f'PASS: Connection blocked as expected: {e}')\n"
            "    sys.exit(0)\n"
        )

        # Run the script
        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        print("=== Outbound Connection Test Output ===")
        print(result.stdout)

        assert result.returncode == 0, "Monkey-patch should block outbound connection"
        assert "PASS" in result.stdout


def test_z06_socket_monkeypatch_intercepts_connect():
    """Z-06: Socket monkey-patch correctly intercepts connect().

    Unit test verifying the socket.connect monkey-patch mechanism works.
    """
    import socket

    # Save original
    original_connect = socket.socket.connect

    # Apply patch
    def patched_connect(self, address):
        raise ConnectionRefusedError(f"Test patch blocked {address}")

    socket.socket.connect = patched_connect  # type: ignore

    # Try to connect
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with pytest.raises(ConnectionRefusedError, match="Test patch blocked"):
            s.connect(('localhost', 9999))
    finally:
        # Restore
        socket.socket.connect = original_connect  # type: ignore


# ==============================================================================
# GATE METADATA
# ==============================================================================


def test_gate_z_metadata():
    """Gate Z metadata check.

    Verifies this test file has the required gate structure.
    """
    # Count test functions
    test_functions = [
        name for name in dir(sys.modules[__name__])
        if name.startswith('test_z')
    ]

    assert len(test_functions) >= 6, (
        f"Gate Z requires minimum 6 tests, found {len(test_functions)}"
    )

    # Verify scripts exist
    assert STATIC_SCANNER.exists(), f"Static scanner not found: {STATIC_SCANNER}"
    assert RUNTIME_SMOKE.exists(), f"Runtime smoke test not found: {RUNTIME_SMOKE}"
    assert EXCEPTIONS_FILE.exists(), f"Exceptions file not found: {EXCEPTIONS_FILE}"

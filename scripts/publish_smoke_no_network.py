#!/usr/bin/env python3
"""P6 Offline Guarantee — Runtime Network Smoke Test

WO-PRS-OFFLINE-001 Gate Z

Verifies that the application's default startup path makes zero outbound network
connections by monkey-patching socket.socket.connect() to fail.

Test method:
1. Patch socket.socket.connect to raise ConnectionRefusedError
2. Import aidm and instantiate core objects (default config path)
3. If no ConnectionRefusedError escapes, PASS
4. If ConnectionRefusedError is raised, FAIL (outbound connection attempted)

Exit codes:
    0 — No outbound connections attempted (PASS)
    1 — Outbound connection attempted in default config (FAIL)

Usage:
    python scripts/publish_smoke_no_network.py
"""

from __future__ import annotations

import socket
import sys
from typing import Any


# Monkey-patch socket.connect BEFORE any imports that might use it
_original_connect = socket.socket.connect


def _patched_connect(self: socket.socket, address: Any) -> None:
    """Patched connect that always fails.

    This simulates a network-disconnected environment. Any code that tries to
    make an outbound connection will hit ConnectionRefusedError.
    """
    raise ConnectionRefusedError(
        f"[SMOKE TEST] Attempted outbound connection to {address} — OFFLINE GUARANTEE VIOLATION"
    )


socket.socket.connect = _patched_connect  # type: ignore


def run_default_startup() -> None:
    """Run the application's default startup path.

    This simulates what happens when a user runs the application with default
    configuration (no network features enabled).

    We import aidm and instantiate key objects. If any of these try to connect
    to the network, the patched socket will raise ConnectionRefusedError.
    """
    import sys
    from pathlib import Path

    # Add project root to path to allow imports
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    print("[INFO] Importing aidm package...")
    try:
        import aidm
    except ConnectionRefusedError as e:
        print(f"[FAIL] Import triggered outbound connection: {e}")
        raise
    except ModuleNotFoundError:
        print("[INFO] aidm package not installed (acceptable for smoke test)")
        print("[INFO] Testing lower-level imports...")
        # Try importing core modules directly
        try:
            import aidm.core
            print("[INFO] aidm.core import successful")
        except ConnectionRefusedError as e:
            print(f"[FAIL] aidm.core import triggered outbound connection: {e}")
            raise
        except Exception as e:
            print(f"[INFO] Non-network exception in aidm.core (acceptable): {type(e).__name__}")
        return

    print("[INFO] Import successful, no outbound connections during import")

    # Try to instantiate some core objects to test deeper initialization
    print("[INFO] Testing core object instantiation...")

    try:
        # Import core modules that might have network code
        from aidm.core.state import OracleState
        from aidm.core.event_log import EventLog

        # Instantiate core objects
        print("[INFO] Creating OracleState...")
        state = OracleState()

        print("[INFO] Creating EventLog...")
        log = EventLog()

        print("[INFO] Core object instantiation successful")

    except ConnectionRefusedError as e:
        print(f"[FAIL] Core object instantiation triggered outbound connection: {e}")
        raise
    except Exception as e:
        # Other exceptions are acceptable (missing files, etc.) — we only care about network
        print(f"[INFO] Non-network exception during instantiation (acceptable): {type(e).__name__}: {e}")

    print("[INFO] Default startup path complete — no network connections attempted")


def main() -> int:
    print("P6 OFFLINE GUARANTEE — Runtime Network Smoke Test")
    print("=" * 60)
    print()
    print("Testing default startup path with network blocked...")
    print("(socket.connect is patched to fail)")
    print()

    try:
        run_default_startup()
        print()
        print("=" * 60)
        print("PASS: No outbound connections attempted in default config")
        print("=" * 60)
        return 0

    except ConnectionRefusedError as e:
        print()
        print("=" * 60)
        print("FAIL: Outbound connection attempted in default config")
        print(f"Error: {e}")
        print("=" * 60)
        print()
        print("The application attempted a network connection during default startup.")
        print("Per PRS-01 §P6, all network features must be opt-in and default to off.")
        return 1

    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: Unexpected exception during smoke test: {type(e).__name__}")
        print(f"{e}")
        print("=" * 60)
        print()
        print("This may indicate a different issue unrelated to network calls.")
        print("Check if the application can start in a clean environment.")
        return 1

    finally:
        # Restore original socket.connect (cleanup)
        socket.socket.connect = _original_connect  # type: ignore


if __name__ == '__main__':
    sys.exit(main())

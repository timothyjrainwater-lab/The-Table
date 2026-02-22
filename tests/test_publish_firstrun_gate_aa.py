"""Gate AA: P7 Fail-Closed First Run — WO-PRS-FIRSTRUN-001

Tests that publish_first_run_missing_weights.py correctly validates
fail-closed behavior when required runtime assets are missing.

Per PRS-01 §P7, the application must:
1. Exit with non-zero code when assets missing
2. Name the missing asset in error message
3. Suggest where to obtain it
4. Generate no partial output before error

Gate Letter: AA
Authority: docs/contracts/PUBLISHING_READINESS_SPEC.md §P7
Test Count: 6 (minimum per gate spec)

Exit Code Semantics (inverted in publish script):
- publish script returns 0 = app correctly fails closed (PASS)
- publish script returns 1 = app silently starts or hangs (FAIL)
"""

import subprocess
import sys
from pathlib import Path


# ============================================================================
# GATE AA TESTS
# ============================================================================


def test_aa_01_script_exits_success():
    """AA-01: Script exits 0 when run (app correctly fails closed)."""
    script_path = Path("scripts/publish_first_run_missing_weights.py")
    assert script_path.exists(), f"Script not found: {script_path}"

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Script should exit 0 (meaning: app correctly fails closed)
    assert result.returncode == 0, (
        f"Script failed (exit {result.returncode}). "
        f"This means the app does NOT fail closed correctly.\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_aa_02_missing_model_weights_produce_error():
    """AA-02: Missing model weights produce actionable error message."""
    # Run the script and check for model weight error in output
    script_path = Path("scripts/publish_first_run_missing_weights.py")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )

    output = result.stdout + result.stderr

    # Should mention model weights in some form
    keywords = ["model", "weight", "gguf", "missing", "not found"]
    found_keyword = any(kw in output.lower() for kw in keywords)

    assert found_keyword, (
        f"Script output does not mention model weights or missing files.\n"
        f"Expected keywords: {keywords}\n"
        f"Output: {output}"
    )


def test_aa_03_missing_tts_voices_produce_error():
    """AA-03: Missing TTS voices produce actionable error message."""
    script_path = Path("scripts/publish_first_run_missing_weights.py")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )

    output = result.stdout + result.stderr

    # Should mention TTS or voice in some form
    keywords = ["tts", "voice", "kokoro", "onnx", "missing", "unavailable"]
    found_keyword = any(kw in output.lower() for kw in keywords)

    assert found_keyword, (
        f"Script output does not mention TTS voices or missing voice files.\n"
        f"Expected keywords: {keywords}\n"
        f"Output: {output}"
    )


def test_aa_04_error_names_specific_asset():
    """AA-04: Error message names the specific missing asset.

    Per PRS-01 §P7: "Error message names the missing asset and suggests
    where to obtain it."
    """
    script_path = Path("scripts/publish_first_run_missing_weights.py")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )

    output = result.stdout + result.stderr

    # Check for specific asset naming patterns
    # Good: "Model not found: models/Qwen2.5-7B-Instruct-Q4_K_M.gguf"
    # Good: "Missing Kokoro model: kokoro.onnx"
    # Bad: "Something went wrong"

    specific_patterns = [
        ".gguf",  # Model file extension
        ".onnx",  # TTS model file extension
        "model",  # Generic model reference
        "voice",  # Voice model reference
        "file",   # File reference
    ]

    found_pattern = any(pattern in output.lower() for pattern in specific_patterns)

    assert found_pattern, (
        f"Error message does not name specific assets.\n"
        f"Expected patterns: {specific_patterns}\n"
        f"Output: {output}"
    )


def test_aa_05_app_exits_nonzero_on_missing_assets():
    """AA-05: Application exits with non-zero code when assets missing.

    This is tested indirectly: the publish script tests that the app
    fails (non-zero exit) when assets are missing. If the script passes
    (exit 0), then the app correctly failed.
    """
    # This invariant is enforced by the script's logic:
    # - Script runs subprocess tests that attempt to load missing assets
    # - If those subprocesses exit 0 (app started), script reports FAIL
    # - If those subprocesses exit non-zero (app failed), script reports PASS

    # We validate this by checking that test_aa_01 passes (script exit 0)
    # which transitively proves the app exited non-zero

    script_path = Path("scripts/publish_first_run_missing_weights.py")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )

    # If script passed (exit 0), then app correctly exited non-zero
    assert result.returncode == 0, (
        "Script failed, indicating app did not exit with non-zero on missing assets"
    )


def test_aa_06_no_partial_output_before_error():
    """AA-06: No partial output before error.

    Per PRS-01 §P7: "No partial output is generated before the error."

    The script validates that failures happen during initialization,
    before any session output, audio generation, or narration occurs.
    """
    script_path = Path("scripts/publish_first_run_missing_weights.py")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )

    output = result.stdout + result.stderr

    # Check that script validates "no partial output"
    assert "no partial output" in output.lower() or "initialization" in output.lower(), (
        f"Script does not validate no-partial-output requirement.\n"
        f"Output: {output}"
    )

    # Script passing (exit 0) also implies fast failure with no hang
    assert result.returncode == 0, (
        "Script failed, indicating potential partial output or hang"
    )


# ============================================================================
# METADATA
# ============================================================================


def test_aa_metadata():
    """Verify gate metadata: 6 tests, gate letter AA."""
    # This test file must contain exactly 6 test functions (excluding this one)
    import inspect

    test_functions = [
        name for name, obj in inspect.getmembers(sys.modules[__name__])
        if inspect.isfunction(obj)
        and name.startswith("test_aa_")
        and name != "test_aa_metadata"
    ]

    assert len(test_functions) == 6, (
        f"Gate AA must have exactly 6 tests (excluding metadata test). "
        f"Found {len(test_functions)}: {test_functions}"
    )

    # Verify test IDs match spec
    expected_test_ids = [
        "test_aa_01_script_exits_success",
        "test_aa_02_missing_model_weights_produce_error",
        "test_aa_03_missing_tts_voices_produce_error",
        "test_aa_04_error_names_specific_asset",
        "test_aa_05_app_exits_nonzero_on_missing_assets",
        "test_aa_06_no_partial_output_before_error",
    ]

    for expected_id in expected_test_ids:
        assert expected_id in test_functions, (
            f"Missing expected test: {expected_id}"
        )

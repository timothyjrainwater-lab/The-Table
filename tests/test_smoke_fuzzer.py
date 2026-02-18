"""Meta-tests for the generative fuzzer.

WO-SMOKE-FUZZER: Verifies the fuzzer infrastructure itself works — completes
without crash, produces structured results, and is reproducible.
"""

import sys
from pathlib import Path

import pytest

# Ensure project root and scripts/ are on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


class TestSmokeFuzzer:
    """Meta-tests for the generative spell fuzzer."""

    def test_fuzzer_completes_without_crash(self):
        """Fuzzer runs 3 iterations with fixed seed and produces results."""
        from smoke_scenarios.common import reset_state
        from smoke_scenarios.fuzzer import run_fuzz

        reset_state()
        results = run_fuzz(fuzz_count=3, seed=42)

        assert len(results) == 3
        for r in results:
            assert r["status"] in ("PASS", "FINDING"), (
                f"Iteration {r['iteration']} crashed: {r.get('error')}"
            )
            assert "spell_id" in r
            assert "spell_name" in r

    def test_fuzzer_reproducible_with_same_seed(self):
        """Same seed produces identical spell selection and results."""
        from smoke_scenarios.common import reset_state
        from smoke_scenarios.fuzzer import run_fuzz

        reset_state()
        run1 = run_fuzz(fuzz_count=5, seed=99)
        reset_state()
        run2 = run_fuzz(fuzz_count=5, seed=99)

        for r1, r2 in zip(run1, run2):
            assert r1["spell_id"] == r2["spell_id"], (
                f"Iteration {r1['iteration']}: "
                f"{r1['spell_id']} != {r2['spell_id']}"
            )
            assert r1["status"] == r2["status"]

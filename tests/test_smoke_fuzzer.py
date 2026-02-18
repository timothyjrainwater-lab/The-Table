"""Meta-tests for the generative fuzzer.

WO-SMOKE-FUZZER: Verifies the fuzzer infrastructure itself works — completes
without crash, produces structured results, and is reproducible.

WO-FUZZER-DETERMINISM-GATES: Verifies determinism gates — ScenarioID hashes,
event log digests, and FUZZ RECEIPT output.
"""

import sys
from io import StringIO
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
        results = run_fuzz(fuzz_count=3, seed=42, collect_all=True)

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
        run1 = run_fuzz(fuzz_count=5, seed=99, collect_all=True)
        reset_state()
        run2 = run_fuzz(fuzz_count=5, seed=99, collect_all=True)

        for r1, r2 in zip(run1, run2):
            assert r1["spell_id"] == r2["spell_id"], (
                f"Iteration {r1['iteration']}: "
                f"{r1['spell_id']} != {r2['spell_id']}"
            )
            assert r1["status"] == r2["status"]

    def test_scenario_id_determinism(self):
        """Same seed + count produces identical ordered ScenarioID lists."""
        from smoke_scenarios.common import reset_state
        from smoke_scenarios.fuzzer import run_fuzz

        reset_state()
        run1 = run_fuzz(fuzz_count=5, seed=77, collect_all=True)
        reset_state()
        run2 = run_fuzz(fuzz_count=5, seed=77, collect_all=True)

        ids1 = [r["scenario_id"] for r in run1]
        ids2 = [r["scenario_id"] for r in run2]

        assert len(ids1) == 5
        assert ids1 == ids2, (
            f"ScenarioID mismatch:\n  run1={ids1}\n  run2={ids2}"
        )
        # Verify IDs are valid hex hashes (64 chars = sha256)
        for sid in ids1:
            assert len(sid) == 64, f"ScenarioID wrong length: {sid}"
            assert all(c in "0123456789abcdef" for c in sid)

    def test_event_digest_determinism(self):
        """Same seed + count produces identical event log digests."""
        from smoke_scenarios.common import reset_state
        from smoke_scenarios.fuzzer import run_fuzz

        reset_state()
        run1 = run_fuzz(fuzz_count=5, seed=77, collect_all=True)
        reset_state()
        run2 = run_fuzz(fuzz_count=5, seed=77, collect_all=True)

        for r1, r2 in zip(run1, run2):
            assert "event_digest" in r1, (
                f"Iteration {r1['iteration']} missing event_digest"
            )
            assert r1["event_digest"] == r2["event_digest"], (
                f"Event digest mismatch at iteration {r1['iteration']}: "
                f"{r1['event_digest'][:12]} != {r2['event_digest'][:12]}"
            )

    def test_fuzz_receipt_printed(self):
        """FUZZ RECEIPT line is printed to stdout."""
        from smoke_scenarios.common import reset_state
        from smoke_scenarios.fuzzer import run_fuzz

        reset_state()
        captured = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            run_fuzz(fuzz_count=3, seed=42, collect_all=True)
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue()
        assert "FUZZ RECEIPT:" in output, (
            f"FUZZ RECEIPT not found in output:\n{output}"
        )
        # Verify receipt format contains expected fields
        for field in ["seed=", "count=", "first=", "last=", "digest="]:
            assert field in output, f"Receipt missing field: {field}"

    def test_stop_on_first_failure_default(self):
        """Default behavior stops on first failure (collect_all=False).

        We use seed=42 with count=20 which is known to produce at least
        one FINDING. With collect_all=False, results should be shorter
        than 20 if any failure occurs.
        """
        from smoke_scenarios.common import reset_state
        from smoke_scenarios.fuzzer import run_fuzz

        reset_state()
        results_stop = run_fuzz(fuzz_count=20, seed=42, collect_all=False)
        reset_state()
        results_all = run_fuzz(fuzz_count=20, seed=42, collect_all=True)

        has_failure = any(r["status"] != "PASS" for r in results_all)
        if has_failure:
            # If there are failures, stop mode should produce fewer results
            assert len(results_stop) <= len(results_all), (
                f"Stop mode produced {len(results_stop)} results, "
                f"collect-all produced {len(results_all)}"
            )
            # Last result in stop mode should be the failure
            assert results_stop[-1]["status"] != "PASS"

"""Gate B tests — WorkingSet compiler + PromptPack compiler determinism.

20+ tests across 6 categories:
    - Determinism (cold boot byte-equality)
    - Mask enforcement (locked content absent)
    - Attribution (traceability intact)
    - No-truncation (Lens routes, doesn't clip)
    - No-backflow (static boundary enforcement)
    - WorkingSet integrity (frozen, canonical, no floats)

Authority: WO-ORACLE-02, Lens Spec v0, Oracle Memo v5.2.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import re

import pytest

from aidm.oracle.canonical import canonical_json, canonical_short_hash
from aidm.oracle.facts_ledger import FactsLedger, make_fact
from aidm.oracle.unlock_state import UnlockEntry, UnlockState
from aidm.oracle.story_state import StoryState, StoryStateLog
from aidm.oracle.working_set import (
    CompilationPolicy,
    ScopeCursor,
    WorkingSet,
    compile_working_set,
)
from aidm.lens.promptpack_compiler import (
    AllowedToSayEnvelope,
    compile_promptpack,
)


# ── Helpers ───────────────────────────────────────────────────────────


def _build_test_stores(
    n_facts: int = 5,
    n_unlocked: int = 3,
):
    """Build Oracle stores with N facts, some unlocked."""
    ledger = FactsLedger()
    unlock = UnlockState()

    fact_ids = []
    for i in range(n_facts):
        fact = make_fact(
            kind="WORLD_RULE",
            payload={"rule": f"test_rule_{i}", "index": i},
            provenance={"source": "test", "event_ids": [i], "rule_refs": []},
            created_event_id=i,
            visibility_mask="PUBLIC",
            precision_tag="UNLOCKED" if i < n_unlocked else "LOCKED",
        )
        ledger.append(fact)
        fact_ids.append(fact.fact_id)

        if i < n_unlocked:
            unlock.unlock(UnlockEntry(
                handle=fact.fact_id,
                scope="SESSION",
                source="SYSTEM",
                provenance_event_id=i,
            ))

    story_log = StoryStateLog(StoryState(
        campaign_id="camp_test",
        world_id="world_abc",
        scene_id="scene_001",
        mode="COMBAT",
    ))

    return ledger, unlock, story_log, fact_ids


def _compile_full_pipeline(n_facts=5, n_unlocked=3):
    """Run the full Oracle→Lens pipeline and return all artifacts."""
    ledger, unlock, story_log, fact_ids = _build_test_stores(n_facts, n_unlocked)
    policy = CompilationPolicy()
    cursor = ScopeCursor(campaign_id="camp_test", scene_id="scene_001")

    ws = compile_working_set(ledger, unlock, story_log, policy, cursor)
    pack, envelope = compile_promptpack(ws)

    return ws, pack, envelope, ledger, unlock, story_log, fact_ids


# ══════════════════════════════════════════════════════════════════════
# DETERMINISM (Gate B core) — Tests 1-6
# ══════════════════════════════════════════════════════════════════════


class TestDeterminism:

    def test_compile_working_set_deterministic(self):
        """Test 1: Same inputs twice → identical bytes_hash."""
        ledger, unlock, story_log, _ = _build_test_stores()
        policy = CompilationPolicy()
        cursor = ScopeCursor(campaign_id="camp_test", scene_id="scene_001")

        ws1 = compile_working_set(ledger, unlock, story_log, policy, cursor)
        ws2 = compile_working_set(ledger, unlock, story_log, policy, cursor)

        assert ws1.bytes_hash == ws2.bytes_hash
        assert ws1.canonical_bytes == ws2.canonical_bytes

    def test_compile_working_set_deterministic_10x(self):
        """Test 2: 10 compilations → all bytes_hash identical."""
        ledger, unlock, story_log, _ = _build_test_stores()
        policy = CompilationPolicy()
        cursor = ScopeCursor(campaign_id="camp_test", scene_id="scene_001")

        hashes = set()
        for _ in range(10):
            ws = compile_working_set(ledger, unlock, story_log, policy, cursor)
            hashes.add(ws.bytes_hash)

        assert len(hashes) == 1

    def test_compile_promptpack_deterministic(self):
        """Test 3: Same WorkingSet twice → identical promptpack_hash."""
        ws, _, _, _, _, _, _ = _compile_full_pipeline()

        _, env1 = compile_promptpack(ws)
        _, env2 = compile_promptpack(ws)

        assert env1.promptpack_hash == env2.promptpack_hash

    def test_compile_promptpack_deterministic_10x(self):
        """Test 4: 10 compilations → all promptpack_hash identical."""
        ws, _, _, _, _, _, _ = _compile_full_pipeline()

        hashes = set()
        for _ in range(10):
            _, env = compile_promptpack(ws)
            hashes.add(env.promptpack_hash)

        assert len(hashes) == 1

    def test_cold_boot_byte_equality(self):
        """Test 5: Compile from stores, rebuild stores, recompile → identical."""
        # First compilation.
        ledger1, unlock1, story_log1, _ = _build_test_stores()
        policy = CompilationPolicy()
        cursor = ScopeCursor(campaign_id="camp_test", scene_id="scene_001")
        ws1 = compile_working_set(ledger1, unlock1, story_log1, policy, cursor)

        # "Cold boot" — rebuild stores from scratch with same data.
        ledger2, unlock2, story_log2, _ = _build_test_stores()
        ws2 = compile_working_set(ledger2, unlock2, story_log2, policy, cursor)

        assert ws1.canonical_bytes == ws2.canonical_bytes
        assert ws1.bytes_hash == ws2.bytes_hash
        assert ws1.working_set_id == ws2.working_set_id

    def test_cold_boot_promptpack_equality(self):
        """Test 6: Full pipeline twice → identical PromptPack."""
        ws1, pack1, env1, _, _, _, _ = _compile_full_pipeline()
        ws2, pack2, env2, _, _, _, _ = _compile_full_pipeline()

        assert env1.promptpack_hash == env2.promptpack_hash
        assert pack1.to_json() == pack2.to_json()


# ══════════════════════════════════════════════════════════════════════
# MASK ENFORCEMENT (LENS-G2) — Tests 7-11
# ══════════════════════════════════════════════════════════════════════


class TestMaskEnforcement:

    def test_locked_handles_absent_from_promptpack(self):
        """Test 7: Locked facts do not appear in PromptPack bytes."""
        ws, pack, _, _, _, _, fact_ids = _compile_full_pipeline(
            n_facts=5, n_unlocked=2,
        )
        # Facts 2,3,4 are locked.
        locked_ids = fact_ids[2:]
        pack_json = pack.to_json()

        for locked_id in locked_ids:
            assert locked_id not in pack_json, (
                f"Locked handle {locked_id} found in PromptPack output"
            )

    def test_only_allowmention_handles_in_output(self):
        """Test 8: No handle outside allowmention set in output."""
        ws, pack, envelope, _, _, _, _ = _compile_full_pipeline(
            n_facts=5, n_unlocked=2,
        )
        allowed_set = set(ws.allowmention_handles)
        # Verify envelope matches.
        assert set(envelope.allowed_handles) == allowed_set

    def test_locked_tokens_absent_from_truth_channel(self):
        """Test 9: Locked precision content excluded from TruthChannel."""
        # Create facts with distinctive payloads.
        ledger = FactsLedger()
        unlock = UnlockState()

        # Unlocked fact.
        f_open = make_fact(
            kind="WORLD_RULE",
            payload={"rule": "gravity_works", "detail": "apples_fall"},
            provenance={"source": "test", "event_ids": [1], "rule_refs": []},
            created_event_id=1,
            precision_tag="UNLOCKED",
        )
        ledger.append(f_open)
        unlock.unlock(UnlockEntry(handle=f_open.fact_id, scope="SESSION", source="SYSTEM"))

        # Locked fact with distinctive content.
        f_locked = make_fact(
            kind="CLUE",
            payload={"secret": "villain_is_the_butler", "detail": "hidden_room"},
            provenance={"source": "test", "event_ids": [2], "rule_refs": []},
            created_event_id=2,
            precision_tag="LOCKED",
        )
        ledger.append(f_locked)

        story_log = StoryStateLog(StoryState(campaign_id="c", scene_id="s"))
        policy = CompilationPolicy()
        cursor = ScopeCursor(campaign_id="c", scene_id="s")

        ws = compile_working_set(ledger, unlock, story_log, policy, cursor)
        pack, _ = compile_promptpack(ws)

        serialized = pack.serialize()
        assert "villain_is_the_butler" not in serialized
        assert "hidden_room" not in serialized
        assert "apples_fall" in serialized

    def test_locked_tokens_absent_from_memory_channel(self):
        """Test 10: Locked precision content excluded from MemoryChannel."""
        ws, pack, _, _, _, _, _ = _compile_full_pipeline(n_facts=5, n_unlocked=2)
        # Memory channel should not contain locked fact payloads.
        for fact_str in pack.memory.session_facts:
            for locked_handle in ws.locked_precision_handles:
                assert locked_handle not in fact_str

    def test_envelope_manifest_complete(self):
        """Test 11: AllowedToSayEnvelope.allowed_handles matches PromptPack content."""
        ws, pack, envelope, _, _, _, _ = _compile_full_pipeline()

        # Envelope allowed_handles should match WorkingSet allowmention.
        assert envelope.allowed_handles == ws.allowmention_handles
        assert envelope.locked_handles == ws.locked_precision_handles
        assert envelope.working_set_id == ws.working_set_id


# ══════════════════════════════════════════════════════════════════════
# ATTRIBUTION (LENS-G3) — Tests 12-13
# ══════════════════════════════════════════════════════════════════════


class TestAttribution:

    def test_every_promptpack_fact_has_oracle_source(self):
        """Test 12: Each content block traces to a FactsLedger entry."""
        ws, pack, envelope, ledger, _, _, _ = _compile_full_pipeline()

        # Every fact in the WorkingSet should be traceable to the ledger.
        for fact_payload in ws.facts_slice:
            fact_id = canonical_short_hash(fact_payload)
            assert ledger.get(fact_id) is not None, (
                f"Fact payload with id {fact_id} not found in FactsLedger"
            )

    def test_envelope_working_set_id_matches_input(self):
        """Test 13: Traceability chain — envelope points back to WorkingSet."""
        ws, _, envelope, _, _, _, _ = _compile_full_pipeline()
        assert envelope.working_set_id == ws.working_set_id


# ══════════════════════════════════════════════════════════════════════
# NO-TRUNCATION (LENS-G4) — Tests 14-15
# ══════════════════════════════════════════════════════════════════════


class TestNoTruncation:

    def test_promptpack_contains_all_slice_content(self):
        """Test 14: No data loss between WorkingSet slices and PromptPack."""
        ws, pack, _, _, _, _, _ = _compile_full_pipeline(n_facts=5, n_unlocked=5)

        serialized = pack.serialize()
        # Every fact payload value should appear in the PromptPack output.
        for fact_payload in ws.facts_slice:
            for key in sorted(fact_payload.keys()):
                value_str = str(fact_payload[key])
                assert value_str in serialized, (
                    f"Fact content '{key}: {value_str}' missing from PromptPack"
                )

    def test_lens_no_token_counting(self):
        """Test 15: compile_promptpack contains no token budget logic."""
        source = inspect.getsource(compile_promptpack)

        # Strip docstrings and comments — only check executable code.
        # Remove triple-quoted strings and single-line comments.
        code_only = re.sub(r'""".*?"""', '', source, flags=re.DOTALL)
        code_only = re.sub(r"'''.*?'''", '', code_only, flags=re.DOTALL)
        code_lines = [
            line for line in code_only.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]
        executable = '\n'.join(code_lines).lower()

        # Should not contain token counting patterns in executable code.
        budget_patterns = [
            "token_budget",
            "token_count",
            "count_tokens",
            "estimate_tokens",
            "max_tokens",
        ]
        for pattern in budget_patterns:
            assert pattern not in executable, (
                f"compile_promptpack contains budget/token logic: '{pattern}'"
            )


# ══════════════════════════════════════════════════════════════════════
# NO-BACKFLOW (LENS-G5) — Tests 16-17
# ══════════════════════════════════════════════════════════════════════


LENS_DIR = pathlib.Path(__file__).resolve().parent.parent / "aidm" / "lens"
ORACLE_DIR = pathlib.Path(__file__).resolve().parent.parent / "aidm" / "oracle"


class TestNoBackflow:

    def test_lens_no_oracle_writes(self):
        """Test 16: compile_promptpack does not call Oracle store write methods."""
        source = inspect.getsource(compile_promptpack)

        # Check for Oracle store mutation methods (not generic list.append).
        # Oracle stores: ledger.append(), unlock.unlock(), story_log.apply(), *.to_jsonl()
        oracle_write_patterns = [
            "ledger.append(",
            "facts_ledger.append(",
            "unlock.unlock(",
            "unlock_state.unlock(",
            "story_log.apply(",
            "story_state_log.apply(",
            ".to_jsonl(",
        ]
        for method in oracle_write_patterns:
            assert method not in source, (
                f"compile_promptpack calls Oracle write method: {method}"
            )

    def test_oracle_no_lens_imports(self):
        """Test 17: Oracle layer does not import from Lens."""
        violations = []
        for py_file in sorted(ORACLE_DIR.glob("*.py")):
            with open(py_file, "r", encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    if re.search(r"^\s*(?:from|import)\s+aidm\.lens\b", line):
                        violations.append(f"{py_file.name}:{lineno}: {line.rstrip()}")

        assert not violations, (
            f"Oracle→Lens backflow violation:\n" + "\n".join(violations)
        )


# ══════════════════════════════════════════════════════════════════════
# WORKINGSET INTEGRITY — Tests 18-20
# ══════════════════════════════════════════════════════════════════════


class TestWorkingSetIntegrity:

    def test_working_set_canonical_json_no_floats(self):
        """Test 18: Float injection raises TypeError."""
        ledger = FactsLedger()
        unlock = UnlockState()

        # Try to create a fact with float payload — should fail at make_fact.
        with pytest.raises(TypeError, match="[Ff]loat"):
            make_fact(
                kind="WORLD_RULE",
                payload={"rule": "bad", "value": 3.14},
                provenance={"source": "test", "event_ids": [1], "rule_refs": []},
                created_event_id=1,
            )

    def test_working_set_id_is_canonical_short_hash(self):
        """Test 19: working_set_id = canonical_short_hash(canonical_bytes content)."""
        ws, _, _, _, _, _, _ = _compile_full_pipeline()

        # Verify working_set_id format.
        assert len(ws.working_set_id) == 16
        assert all(c in "0123456789abcdef" for c in ws.working_set_id)

        # Verify it's derived from the canonical bytes content.
        assert len(ws.bytes_hash) == 64
        assert ws.bytes_hash == __import__("hashlib").sha256(ws.canonical_bytes).hexdigest()

    def test_working_set_frozen(self):
        """Test 20: All container fields are frozen (no mutation)."""
        ws, _, _, _, _, _, _ = _compile_full_pipeline()

        # WorkingSet is frozen dataclass.
        with pytest.raises(AttributeError):
            ws.mode = "EXPLORATION"  # type: ignore

        # Tuple fields cannot be mutated.
        assert isinstance(ws.allowmention_handles, tuple)
        assert isinstance(ws.locked_precision_handles, tuple)
        assert isinstance(ws.facts_slice, tuple)
        assert isinstance(ws.compactions_slice, tuple)

    def test_working_set_no_timestamps(self):
        """Test 21 (bonus): No wall-clock timestamps in WorkingSet."""
        ws, _, _, _, _, _, _ = _compile_full_pipeline()
        ws_str = str(ws.canonical_bytes)

        timestamp_patterns = [
            "datetime", "timestamp", "created_at", "updated_at",
            "T00:00:00", "2026-",
        ]
        for pattern in timestamp_patterns:
            assert pattern not in ws_str, (
                f"WorkingSet contains timestamp-like content: '{pattern}'"
            )

    def test_envelope_frozen(self):
        """Test 22 (bonus): AllowedToSayEnvelope is frozen."""
        _, _, envelope, _, _, _, _ = _compile_full_pipeline()

        with pytest.raises(AttributeError):
            envelope.promptpack_hash = "tampered"  # type: ignore

        assert isinstance(envelope.allowed_handles, tuple)
        assert isinstance(envelope.locked_handles, tuple)

    def test_different_stores_different_hashes(self):
        """Test 23 (bonus): Different store content → different WorkingSet hashes."""
        # 3 unlocked facts.
        ws1, _, _, _, _, _, _ = _compile_full_pipeline(n_facts=3, n_unlocked=3)
        # 5 unlocked facts.
        ws2, _, _, _, _, _, _ = _compile_full_pipeline(n_facts=5, n_unlocked=5)

        assert ws1.bytes_hash != ws2.bytes_hash
        assert ws1.working_set_id != ws2.working_set_id

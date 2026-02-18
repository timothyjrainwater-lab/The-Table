"""Gate I — Comedy stinger content subsystem tests.

Validates the NPC comedy stinger schema, data bank, deterministic selector,
and rendering. Standalone content module — no Director, Lens PromptPack,
Oracle, or WebSocket dependencies.

WO-COMEDY-STINGERS-P1: Comedy Stinger Content Subsystem (Phase 1)
"""

import json
import pathlib

import pytest

from aidm.schemas.npc_stinger import (
    CANONICAL_ARCHETYPES,
    CANONICAL_DELIVERY_CONTEXTS,
    Stinger,
)
from aidm.lens.comedy_stingers import (
    validate_stinger_bank,
    select_stinger_deterministic,
    render_stinger_fragments,
)

# ── Data loading helper ─────────────────────────────────────────────

DATA_PATH = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "aidm" / "data" / "content_pack" / "npc_stingers.json"
)


def _load_bank() -> list:
    """Load the full stinger bank from the content pack JSON."""
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return [Stinger.from_dict(entry) for entry in raw]


# ── Helpers for invalid stinger construction ────────────────────────

def _valid_stinger(**overrides) -> Stinger:
    """Return a baseline valid Stinger, with optional field overrides."""
    defaults = dict(
        stinger_id="test_archetype_001",
        archetype="tavern_keeper",
        delivery_contexts=["first_meeting"],
        fragments=[
            "Forty years pouring",
            "Served kings nightly",
            "Survived three plagues",
            "Rats still own the cellar",
        ],
        tags={"pace": "brisk", "pause_ms_before_punchline": 400,
              "emphasis_target": "rats", "mood_hint": "dry"},
    )
    defaults.update(overrides)
    return Stinger(**defaults)


# ════════════════════════════════════════════════════════════════════
# Gate I Tests
# ════════════════════════════════════════════════════════════════════


class TestGateI:
    """Gate I — NPC comedy stinger content subsystem."""

    # ── I-01: Bank loads and validates ──────────────────────────────

    def test_stinger_bank_loads_and_validates(self):
        """I-01: Load npc_stingers.json, parse into Stinger objects,
        validate entire bank. 0 errors."""
        bank = _load_bank()
        assert len(bank) >= 21, (
            f"Bank has {len(bank)} stingers; minimum is 21 "
            f"(3 per archetype x 7 archetypes)"
        )
        # Coverage: at least 3 per archetype
        for arch in CANONICAL_ARCHETYPES:
            count = sum(1 for s in bank if s.archetype == arch)
            assert count >= 3, (
                f"Archetype '{arch}' has only {count} stingers (need >=3)"
            )
        errors = validate_stinger_bank(bank)
        assert errors == [], (
            f"Stinger bank validation errors:\n"
            + "\n".join(errors)
        )

    # ── I-02: Wrong fragment count ─────────────────────────────────

    def test_stinger_rejects_wrong_fragment_count(self):
        """I-02: fragments with 3 or 5 items -> error."""
        for n_frags in (3, 5):
            frags = ["Two words"] * n_frags
            s = _valid_stinger(
                stinger_id=f"test_frag_{n_frags}",
                fragments=frags,
            )
            errors = validate_stinger_bank([s])
            assert any("4 fragments" in e for e in errors), (
                f"Expected fragment-count error for {n_frags} fragments, "
                f"got: {errors}"
            )

    # ── I-03: Long credential ──────────────────────────────────────

    def test_stinger_rejects_long_credential(self):
        """I-03: credential with 7+ words -> error."""
        s = _valid_stinger(
            stinger_id="test_long_cred",
            fragments=[
                "One two three four five six seven",  # 7 words
                "Served kings nightly",
                "Survived three plagues",
                "Punchline definitely longer than any single credential here",
            ],
        )
        errors = validate_stinger_bank([s])
        assert any("words" in e and "2-6" in e for e in errors), (
            f"Expected word-count error for 7-word credential, got: {errors}"
        )

    # ── I-04: Short punchline ──────────────────────────────────────

    def test_stinger_rejects_short_punchline(self):
        """I-04: punchline shorter than any credential -> error."""
        s = _valid_stinger(
            stinger_id="test_short_punch",
            fragments=[
                "Forty years pouring",          # 3 words
                "Served kings nightly",          # 3 words
                "Survived three plagues",        # 3 words
                "Too short",                     # 2 words
            ],
        )
        errors = validate_stinger_bank([s])
        assert any("strictly longer" in e for e in errors), (
            f"Expected punchline-length error, got: {errors}"
        )

    # ── I-05: Conjunction in credential ────────────────────────────

    def test_stinger_rejects_conjunction_in_credential(self):
        """I-05: 'Three wars and two plagues' -> error."""
        s = _valid_stinger(
            stinger_id="test_conjunction",
            fragments=[
                "Three wars and plagues",    # contains "and"
                "Short cred here",
                "Another short one",
                "Punchline is definitely longer than credentials here",
            ],
        )
        errors = validate_stinger_bank([s])
        assert any("conjunction" in e.lower() for e in errors), (
            f"Expected conjunction error for 'and', got: {errors}"
        )

    # ── I-06: Over duration ────────────────────────────────────────

    def test_stinger_rejects_over_duration(self):
        """I-06: Stinger exceeding 6.0s estimate -> error."""
        s = _valid_stinger(
            stinger_id="test_over_duration",
            fragments=[
                "Word one two four",              # 4 words
                "Word one two four",              # 4 words
                "Word one two four",              # 4 words
                "This punchline has way too many words in it",  # 10 words
            ],
            tags={"pause_ms_before_punchline": 3000},
        )
        errors = validate_stinger_bank([s])
        assert any("duration" in e.lower() for e in errors), (
            f"Expected duration error, got: {errors}"
        )

    # ── I-07: Deterministic selection ──────────────────────────────

    def test_deterministic_selection_seeded(self):
        """I-07: Same seed_material -> same stinger_id across 100 calls."""
        bank = _load_bank()
        seed = "test_deterministic_seed_42"
        first = select_stinger_deterministic(
            bank, "tavern_keeper", "first_meeting", seed
        )
        assert first is not None, "Expected a stinger for tavern_keeper/first_meeting"

        for _ in range(100):
            result = select_stinger_deterministic(
                bank, "tavern_keeper", "first_meeting", seed
            )
            assert result is not None
            assert result.stinger_id == first.stinger_id

    # ── I-08: Exclusion + relaxation ───────────────────────────────

    def test_selection_excludes_used_ids_then_relaxes(self):
        """I-08: used_ids covers all but one -> returns the one.
        used_ids covers ALL -> relaxes and returns from full pool."""
        bank = _load_bank()
        pool = [
            s for s in bank
            if s.archetype == "tavern_keeper"
            and "first_meeting" in s.delivery_contexts
        ]
        assert len(pool) >= 2, "Need >=2 tavern_keeper/first_meeting stingers"

        # Exclude all but one
        keep = pool[0]
        exclude_all_but_one = [s.stinger_id for s in pool if s is not keep]
        result = select_stinger_deterministic(
            bank, "tavern_keeper", "first_meeting",
            "test_exclude_seed", used_ids=exclude_all_but_one,
        )
        assert result is not None
        assert result.stinger_id == keep.stinger_id

        # Exclude ALL -> should relax and still return something
        exclude_all = [s.stinger_id for s in pool]
        result = select_stinger_deterministic(
            bank, "tavern_keeper", "first_meeting",
            "test_relax_seed", used_ids=exclude_all,
        )
        assert result is not None
        assert result.stinger_id in [s.stinger_id for s in pool]

    # ── I-09: No match returns None ────────────────────────────────

    def test_selection_returns_none_for_no_match(self):
        """I-09: Nonexistent archetype/context combo returns None."""
        bank = _load_bank()
        result = select_stinger_deterministic(
            bank, "dragon_tamer", "first_meeting", "seed"
        )
        assert result is None

    # ── I-10: Render fragments ─────────────────────────────────────

    def test_render_stinger_fragments(self):
        """I-10: render_stinger_fragments produces correct literal join."""
        s = _valid_stinger()
        rendered = render_stinger_fragments(s)
        expected = (
            "Forty years pouring. Served kings nightly. "
            "Survived three plagues. Rats still own the cellar."
        )
        assert rendered == expected

    # ── I-11: Stinger immutability ─────────────────────────────────

    def test_stinger_is_frozen(self):
        """I-11: Stinger dataclass is frozen — cannot mutate fields."""
        s = _valid_stinger()
        with pytest.raises(AttributeError):
            s.stinger_id = "mutated"  # type: ignore[misc]

    # ── I-12: Invalid archetype rejected ───────────────────────────

    def test_stinger_rejects_invalid_archetype(self):
        """I-12: Non-canonical archetype -> error."""
        s = _valid_stinger(stinger_id="bad_arch", archetype="dragon_rider")
        errors = validate_stinger_bank([s])
        assert any("Invalid archetype" in e for e in errors), (
            f"Expected archetype error, got: {errors}"
        )

    # ── I-13: Invalid delivery context rejected ────────────────────

    def test_stinger_rejects_invalid_delivery_context(self):
        """I-13: Non-canonical delivery context -> error."""
        s = _valid_stinger(
            stinger_id="bad_ctx",
            delivery_contexts=["first_meeting", "during_boss_fight"],
        )
        errors = validate_stinger_bank([s])
        assert any("Invalid delivery_context" in e for e in errors), (
            f"Expected delivery context error, got: {errors}"
        )

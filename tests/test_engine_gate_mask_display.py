"""
Gate ENGINE-MASK-DISPLAY-001 — Precision-safe player-visible label strings.

All server-provided strings that reach UI canvas fillText() must be free of
locked precision tokens (exact HP, AC, DC, CR, SR, numeric parentheticals)
except at STUDIED tier in bestiary context (where exact values are permitted).

Tests (6):
  MD-01: knowledge_mask.py HEARD_OF tier: display_name, rumor_text — no numeric patterns
  MD-02: knowledge_mask.py SEEN tier: appearance — no locked precision patterns
  MD-03: knowledge_mask.py FOUGHT tier: hp_estimate, ac_estimate — qualitative only (no bare integers)
  MD-04: Forbidden token pattern list defined (canonical list in this file)
  MD-05: Python sim — label_is_safe() rejects known violation strings
  MD-06: Python sim — label_is_safe() passes known safe strings
"""

import re, pathlib, sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from aidm.schemas.knowledge_mask import (
    _HEARD_OF_FIELDS,
    _SEEN_FIELDS,
    _FOUGHT_FIELDS,
    _STUDIED_FIELDS,
)

# ---------------------------------------------------------------------------
# Canonical forbidden pattern list
# ---------------------------------------------------------------------------

# These are the patterns that must NOT appear in player-visible label strings
# at or below FOUGHT tier. At STUDIED tier, exact numeric values are permitted
# in description/body fields but still not in display_name or title.

FORBIDDEN_PATTERNS = [
    r'\(\s*\d+\s*[Hh][Pp]\s*\)',          # "(12 HP)", "( 7 hp )"
    r'\(\s*[Hh][Pp]\s*\d+\s*\)',           # "(hp 12)", "(HP 7)"
    r'\(\s*\d+\s*/\s*\d+\s*[Hh][Pp]\)',   # "(8/11 HP)"
    r'\b[Aa][Cc]\s*\d+\b',                # "AC 14", "ac14"
    r'\b[Dd][Cc]\s*\d+\b',                # "DC 18"
    r'\b[Cc][Rr]\s*[\d/]+\b',             # "CR 4", "CR 1/2"
    r'\b[Ss][Rr]\s*\d+\b',                # "SR 15"
    r'\+\d+\s*to\s*hit',                  # "+5 to hit"
    r'\d+d\d+\+\d+',                      # "2d6+4" damage expressions
]


def label_is_safe(label: str) -> bool:
    """
    Fail-closed check: returns False if label contains any forbidden pattern.
    UI render guard uses this; returns True only when all checks pass.
    This is an injection guard, not a sanitizer — caller replaces with 'Unknown',
    does not edit the string.
    """
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, label):
            return False
    return True


# ---------------------------------------------------------------------------
# MD-01: HEARD_OF tier — display_name and rumor_text are text-only fields
# ---------------------------------------------------------------------------

def test_md01_heard_of_tier_fields_are_qualitative():
    """MD-01: HEARD_OF tier contains only text/qualitative fields — no bare stat fields."""
    # Precision-locked field names that must NOT appear at HEARD_OF
    precision_fields = {'ac', 'hp_max', 'hit_dice', 'challenge_rating', 'spell_resistance',
                        'base_attack_bonus', 'saves_exact', 'damage_reduction'}
    violations = _HEARD_OF_FIELDS & precision_fields
    assert not violations, (
        f"HEARD_OF tier must not expose precision fields: {violations}"
    )
    # display_name and rumor_text must be present (they are the label-bearing fields)
    assert 'display_name' in _HEARD_OF_FIELDS, (
        "HEARD_OF must expose display_name — it is the primary player-visible label"
    )
    assert 'rumor_text' in _HEARD_OF_FIELDS, (
        "HEARD_OF must expose rumor_text — it is the flavor text label"
    )


# ---------------------------------------------------------------------------
# MD-02: SEEN tier — appearance is a text field, no stat exposure
# ---------------------------------------------------------------------------

def test_md02_seen_tier_appearance_is_qualitative():
    """MD-02: SEEN tier exposes appearance (qualitative text), no exact stat fields."""
    precision_fields = {'ac', 'hp_max', 'hit_dice', 'challenge_rating', 'spell_resistance',
                        'base_attack_bonus', 'saves_exact', 'damage_reduction'}
    # SEEN adds fields on top of HEARD_OF — check SEEN-exclusive fields only
    seen_exclusive = _SEEN_FIELDS - _HEARD_OF_FIELDS
    violations = seen_exclusive & precision_fields
    assert not violations, (
        f"SEEN tier must not expose precision fields in its exclusive additions: {violations}"
    )
    assert 'appearance' in _SEEN_FIELDS, (
        "SEEN must expose appearance — physical description field"
    )


# ---------------------------------------------------------------------------
# MD-03: FOUGHT tier — hp_estimate and ac_estimate are qualitative fields
# ---------------------------------------------------------------------------

def test_md03_fought_tier_estimates_are_qualitative():
    """MD-03: FOUGHT tier uses *_estimate fields (qualitative), not exact stat fields."""
    # Qualitative estimate fields must be present
    assert 'hp_estimate' in _FOUGHT_FIELDS, (
        "FOUGHT must expose hp_estimate (qualitative: 'sturdy', 'fragile') — not hp_max"
    )
    assert 'ac_estimate' in _FOUGHT_FIELDS, (
        "FOUGHT must expose ac_estimate (qualitative: 'lightly armored') — not ac"
    )
    # Exact precision fields must NOT be present at FOUGHT tier
    assert 'ac' not in _FOUGHT_FIELDS, (
        "Exact 'ac' must not be exposed at FOUGHT tier — only ac_estimate"
    )
    assert 'hp_max' not in _FOUGHT_FIELDS, (
        "Exact 'hp_max' must not be exposed at FOUGHT tier — only hp_estimate"
    )
    assert 'challenge_rating' not in _FOUGHT_FIELDS, (
        "challenge_rating must not be exposed at FOUGHT tier — only at STUDIED"
    )
    assert 'spell_resistance' not in _FOUGHT_FIELDS, (
        "spell_resistance must not be exposed at FOUGHT tier — only at STUDIED"
    )


# ---------------------------------------------------------------------------
# MD-04: Forbidden pattern list is defined and valid
# ---------------------------------------------------------------------------

def test_md04_forbidden_pattern_list_defined():
    """MD-04: Canonical forbidden token pattern list is defined and non-empty."""
    assert len(FORBIDDEN_PATTERNS) >= 6, (
        "Forbidden pattern list must cover at minimum: HP parentheticals, "
        "AC, DC, CR, SR, attack bonus, damage expressions"
    )
    # All entries must be valid regex
    for p in FORBIDDEN_PATTERNS:
        re.compile(p)  # raises if invalid


# ---------------------------------------------------------------------------
# MD-05: label_is_safe() rejects known violations
# ---------------------------------------------------------------------------

def test_md05_label_is_safe_rejects_violations():
    """MD-05: label_is_safe() rejects known precision-leak strings."""
    violations = [
        "Goblin (12 HP)",
        "Orc (8/11 HP)",
        "Guard AC 14",
        "Trap DC 18",
        "Vampire CR 13",
        "Golem SR 25",
        "+5 to hit",
        "2d6+4 damage",
        "Skeleton (hp 12)",
    ]
    for v in violations:
        assert not label_is_safe(v), (
            f"label_is_safe() must reject '{v}' — contains precision token"
        )


# ---------------------------------------------------------------------------
# MD-06: label_is_safe() passes known-safe strings
# ---------------------------------------------------------------------------

def test_md06_label_is_safe_passes_safe_strings():
    """MD-06: label_is_safe() passes known-safe display strings."""
    safe = [
        "Goblin",
        "Ancient Red Dragon",
        "Guard",
        "City Watch",
        "Heard of: a large beast",
        "Seems heavily armored",
        "Very tough",
        "Fights to the death",
        "Skeleton",
        "Zombie",
    ]
    for s in safe:
        assert label_is_safe(s), (
            f"label_is_safe() must pass '{s}' — no precision tokens present"
        )

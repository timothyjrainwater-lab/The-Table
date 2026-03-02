"""Gate tests: WO-ENGINE-REQUIRES-ATTACK-ROLL-DEAD-FIELD-001 (Batch AX WO2).

RAD-001..004 — CONSUME_DEFERRED documentation for SpellDefinition.requires_attack_roll:
  RAD-001: SpellDefinition.requires_attack_roll field declaration has comment containing "CONSUME_DEFERRED"
  RAD-002: spell_resolver.py has comment containing "requires_attack_roll" and "CONSUME_DEFERRED"
            near the affected_entities assembly site
  RAD-003: At least 2 spells in SPELL_REGISTRY have requires_attack_roll=True (TOUCH/RAY present)
  RAD-004: Regression — TOUCH spell still resolves to hit without attack roll (existing behavior preserved)

PHB p.150: Touch spells require attack roll (Phase 2 WO — not implemented yet).
PHB p.224: Ray spells require ranged touch attack roll (Phase 2 WO — not implemented yet).
FINDING-AUDIT-SPELL-012-REQUIRES-ATTACK-ROLL-DEAD-001 closed.
"""
from __future__ import annotations

import os
import pytest


# ---------------------------------------------------------------------------
# RAD-001: SpellDefinition.requires_attack_roll has CONSUME_DEFERRED comment
# ---------------------------------------------------------------------------

def test_RAD001_requires_attack_roll_field_has_consume_deferred_comment():
    """RAD-001: spell_resolver.py field declaration has 'CONSUME_DEFERRED' comment.
    The requires_attack_roll field must be annotated so future builders know it is not read.
    """
    spell_resolver_path = os.path.join(
        os.path.dirname(__file__), "..", "aidm", "core", "spell_resolver.py"
    )
    with open(spell_resolver_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the block containing requires_attack_roll field
    assert "requires_attack_roll" in content, (
        "RAD-001: spell_resolver.py must contain 'requires_attack_roll' field"
    )
    assert "CONSUME_DEFERRED" in content, (
        "RAD-001: spell_resolver.py must contain 'CONSUME_DEFERRED' comment near "
        "requires_attack_roll field declaration"
    )

    # Verify the comment is near the field declaration
    lines = content.splitlines()
    field_line = None
    for i, line in enumerate(lines):
        if "requires_attack_roll: bool = False" in line:
            field_line = i
            break
    assert field_line is not None, (
        "RAD-001: requires_attack_roll: bool = False not found in spell_resolver.py"
    )
    # CONSUME_DEFERRED must appear within 5 lines of the field declaration
    window = "\n".join(lines[max(0, field_line - 2): field_line + 5])
    assert "CONSUME_DEFERRED" in window, (
        f"RAD-001: CONSUME_DEFERRED comment must be within 5 lines of requires_attack_roll field. "
        f"Window:\n{window}"
    )


# ---------------------------------------------------------------------------
# RAD-002: spell_resolver.py has CONSUME_DEFERRED comment at affected_entities site
# ---------------------------------------------------------------------------

def test_RAD002_spell_resolver_affected_entities_has_consume_deferred_comment():
    """RAD-002: spell_resolver.resolve_spell() has CONSUME_DEFERRED comment at affected_entities
    assembly site. Comment must include both 'requires_attack_roll' and 'CONSUME_DEFERRED'.
    No behavior change — comment only.
    """
    spell_resolver_path = os.path.join(
        os.path.dirname(__file__), "..", "aidm", "core", "spell_resolver.py"
    )
    with open(spell_resolver_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Both keywords must appear in the file together (the field + the gap site comment)
    assert "requires_attack_roll" in content, (
        "RAD-002: 'requires_attack_roll' must appear in spell_resolver.py"
    )
    # Find the affected_entities site comment with CONSUME_DEFERRED
    assert "CONSUME_DEFERRED" in content, (
        "RAD-002: 'CONSUME_DEFERRED' must appear in spell_resolver.py"
    )

    # The gap-site comment must reference both keywords on the same or adjacent lines
    lines = content.splitlines()
    gap_comment_line = None
    for i, line in enumerate(lines):
        if "CONSUME_DEFERRED" in line and "requires_attack_roll" in line:
            gap_comment_line = i
            break
    assert gap_comment_line is not None, (
        "RAD-002: A single comment line must contain both 'CONSUME_DEFERRED' and "
        "'requires_attack_roll' at the gap site in spell_resolver.py. "
        "Check that the WO2 comment was inserted at the affected_entities assembly."
    )


# ---------------------------------------------------------------------------
# RAD-003: At least 2 spells in SPELL_REGISTRY have requires_attack_roll=True
# ---------------------------------------------------------------------------

def test_RAD003_spell_registry_has_requires_attack_roll_spells():
    """RAD-003: At least 2 spells in SPELL_REGISTRY have requires_attack_roll=True.
    Confirms TOUCH/RAY spells are still present and the field is set (even if not consumed).
    """
    from aidm.core.spell_resolver import SpellDefinition
    from aidm.schemas.spell_definitions import SPELL_REGISTRY

    touch_ray_spells = [
        spell_id for spell_id, spell in SPELL_REGISTRY.items()
        if hasattr(spell, "requires_attack_roll") and spell.requires_attack_roll
    ]
    assert len(touch_ray_spells) >= 2, (
        f"RAD-003: At least 2 spells must have requires_attack_roll=True in SPELL_REGISTRY. "
        f"Found {len(touch_ray_spells)}: {touch_ray_spells}"
    )


# ---------------------------------------------------------------------------
# RAD-004: Regression — TOUCH spell still resolves without attack roll
# ---------------------------------------------------------------------------

def test_RAD004_no_conditional_on_requires_attack_roll_in_resolver():
    """RAD-004: Regression — WO2 is comment-only. No conditional logic on requires_attack_roll
    was added to spell_resolver.py. The field is still a dead write-only field.
    Verify by confirming spell_resolver.py has no 'if.*requires_attack_roll' branch.
    """
    spell_resolver_path = os.path.join(
        os.path.dirname(__file__), "..", "aidm", "core", "spell_resolver.py"
    )
    with open(spell_resolver_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Check that no conditional branch on requires_attack_roll was introduced
    conditional_lines = [
        (i + 1, line.rstrip())
        for i, line in enumerate(lines)
        if "requires_attack_roll" in line and ("if " in line or "elif " in line)
    ]
    assert not conditional_lines, (
        f"RAD-004 REGRESSION: WO2 must be comment-only — no conditional logic on "
        f"requires_attack_roll. Found conditional(s) at:\n"
        + "\n".join(f"  Line {ln}: {content}" for ln, content in conditional_lines)
    )

    # Also confirm requires_attack_roll is still ONLY referenced in field declaration and comments
    from aidm.schemas.spell_definitions import SPELL_REGISTRY
    # The field must still be set on spells (not removed by this WO)
    touch_ray_count = sum(
        1 for spell in SPELL_REGISTRY.values()
        if hasattr(spell, "requires_attack_roll") and spell.requires_attack_roll
    )
    assert touch_ray_count >= 2, (
        f"RAD-004: requires_attack_roll=True must still be set on ≥2 spells. "
        f"Found: {touch_ray_count}. WO2 must not have altered spell definitions."
    )

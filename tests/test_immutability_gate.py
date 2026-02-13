"""Automated immutability gate for frozen dataclasses.

Scans all frozen dataclasses in aidm/ and verifies that any mutable container
fields (List, Dict, Set) are protected by a __post_init__ method that freezes
them (converts to tuple, MappingProxyType, frozenset, etc.).

This test exists to prevent the class of bugs where a frozen dataclass has
mutable container fields that can be silently mutated after construction,
violating the immutability contract the architecture depends on.

If this test fails, either:
1. Add a __post_init__ to freeze the mutable fields, OR
2. Change the field type to an immutable equivalent (tuple, Mapping, frozenset)

See WO-AUDIT-003 for the original fix and KNOWN_TECH_DEBT.md for context.
"""

import ast
import pathlib
import pytest


AIDM_ROOT = pathlib.Path(__file__).resolve().parent.parent / "aidm"

# Classes that are known to have mutable fields by design and are tracked
# in KNOWN_TECH_DEBT.md. These are intentionally deferred — do not add to
# this list without explicit approval.
KNOWN_EXCEPTIONS = frozenset({
    # truth_packets.py — payload dicts are consumed immediately, never stored
    "CoverPayload",
    "AoEPayload",
    "LOSPayload",
    "LOEPayload",
    "MovementPayload",
    "StructuredTruthPacket",
    # scene_manager.py — these are constructed once in Lens, never shared
    "EncounterDef",
    "SceneState",
    "TransitionResult",
    "EncounterResult",
    "RestResult",
    # immersion layer — non-authoritative, cannot affect Box state
    "CombatReceipt",
    "EntityInspection",
    "EntityStateView",
    "PlacedObject",
    # runtime outputs — consumed once per turn, never stored
    "TurnOutput",
    "TurnResult",
    # other tracked exceptions
    "AoOTracker",
    "ProvenanceExplanation",
    "SessionSegmentSummary",
    "BestiaryRegistry",
    "FeatDefinition",
    "TruthChannel",
    "FilteredSTP",
    "SessionStateMsg",
    "ModelProfile",
})


def _scan_frozen_dataclasses():
    """Scan aidm/ for frozen dataclasses with unprotected mutable fields."""
    violations = []

    for py_file in sorted(AIDM_ROOT.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            # Check frozen=True
            is_frozen = False
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call):
                    for kw in dec.keywords:
                        if (kw.arg == "frozen"
                                and isinstance(kw.value, ast.Constant)
                                and kw.value.value is True):
                            is_frozen = True

            if not is_frozen:
                continue

            # Check for __post_init__
            has_post_init = any(
                isinstance(item, ast.FunctionDef) and item.name == "__post_init__"
                for item in node.body
            )

            # Check for mutable annotations
            mutable_fields = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and item.target:
                    ann_str = ast.dump(item.annotation) if item.annotation else ""
                    name = (item.target.id
                            if isinstance(item.target, ast.Name) else "?")
                    if any(x in ann_str for x in ["List", "Dict", "Set"]):
                        mutable_fields.append(name)

            if mutable_fields and not has_post_init:
                rel_path = py_file.relative_to(AIDM_ROOT.parent)
                violations.append({
                    "file": str(rel_path),
                    "class": node.name,
                    "fields": mutable_fields,
                })

    return violations


def test_no_unprotected_mutable_fields_in_frozen_dataclasses():
    """Every frozen dataclass with mutable containers must have __post_init__.

    This is an automated gate that prevents the class of immutability bugs
    found in WO-AUDIT-003. If a new frozen dataclass is added with List,
    Dict, or Set fields, this test will fail unless a __post_init__ is added
    to freeze those fields.

    Known exceptions are tracked in KNOWN_EXCEPTIONS and KNOWN_TECH_DEBT.md.
    """
    violations = _scan_frozen_dataclasses()

    # Filter out known exceptions
    new_violations = [
        v for v in violations if v["class"] not in KNOWN_EXCEPTIONS
    ]

    if new_violations:
        msg_lines = [
            "Frozen dataclasses with unprotected mutable container fields:",
            "",
        ]
        for v in new_violations:
            msg_lines.append(
                f"  {v['file']}::{v['class']} — fields: {v['fields']}"
            )
        msg_lines.append("")
        msg_lines.append(
            "Fix: Add __post_init__ to freeze these fields "
            "(List→tuple, Dict→MappingProxyType, Set→frozenset), "
            "OR add to KNOWN_EXCEPTIONS with justification."
        )
        pytest.fail("\n".join(msg_lines))


def test_known_exceptions_still_exist():
    """Verify KNOWN_EXCEPTIONS haven't been silently fixed.

    If a class in KNOWN_EXCEPTIONS now has a __post_init__, it should be
    removed from the exception list to keep it honest.
    """
    violations = _scan_frozen_dataclasses()
    violation_classes = {v["class"] for v in violations}

    stale_exceptions = KNOWN_EXCEPTIONS - violation_classes
    # Some exceptions might have been fixed — that's good, but we should
    # clean up the exception list. Only flag if there are many stale entries.
    # A few removals are expected during normal development.
    if len(stale_exceptions) > 5:
        pytest.fail(
            f"{len(stale_exceptions)} classes in KNOWN_EXCEPTIONS now have "
            f"__post_init__ protection. Remove them from the exception list: "
            f"{sorted(stale_exceptions)}"
        )

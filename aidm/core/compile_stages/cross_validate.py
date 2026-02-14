"""WO-COMPILE-VALIDATE-001: Compile-time Layer A vs Layer B cross-validation.

Compares RuleEntry (Layer A mechanics) against AbilityPresentationEntry
(Layer B presentation) for each content_id. Catches mismatches at compile
time instead of at runtime when a player sees broken narration.

7 checks total:
  P0 (FAIL — block compilation): CT-001, CT-002, CT-003
  P3 (WARN — log to world metadata): CT-004, CT-005, CT-006, CT-007

Runs after the semantics stage produces the PresentationSemanticsRegistry.
Read-only: compares data, does not modify it.

BOUNDARY LAW: No imports from aidm/lens/ or aidm/immersion/.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from aidm.core.compile_stages._base import CompileContext, CompileStage, StageResult
from aidm.schemas.presentation_semantics import (
    AbilityPresentationEntry,
    DeliveryMode,
    OriginRule,
    Scale,
    Staging,
)
from aidm.schemas.rulebook import RuleEntry, RuleParameters


# ═══════════════════════════════════════════════════════════════════════
# CompileViolation
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CompileViolation:
    """A single cross-validation violation found at compile time."""

    check_id: str
    """Check identifier: 'CT-001', 'CT-002', etc."""

    content_id: str
    """Which ability has the violation."""

    severity: str
    """'FAIL' (P0 — blocks compilation) or 'WARN' (P3 — logged only)."""

    detail: str
    """Human-readable description of the mismatch."""


# ═══════════════════════════════════════════════════════════════════════
# Error type for P0 failures
# ═══════════════════════════════════════════════════════════════════════


class CompileValidationError(Exception):
    """Raised when P0 cross-validation checks fail.

    Carries the list of FAIL violations so the caller can report them.
    """

    def __init__(self, violations: List[CompileViolation]) -> None:
        self.violations = violations
        details = "; ".join(
            f"[{v.check_id}] {v.content_id}: {v.detail}" for v in violations
        )
        super().__init__(f"Compile validation failed: {details}")


# ═══════════════════════════════════════════════════════════════════════
# Dice parsing helper
# ═══════════════════════════════════════════════════════════════════════

_DICE_RE = re.compile(r"^(\d+)d(\d+)(?:[+-]\d+)?$", re.IGNORECASE)


def _parse_max_damage(damage_dice: Optional[str]) -> Optional[int]:
    """Parse a damage dice string and return its maximum possible damage.

    Supports expressions like '8d6', '2d8+5', '1d12-1'.
    Returns None if the string is unparseable.
    """
    if not damage_dice:
        return None

    expr = damage_dice.strip().lower()

    # Handle bonus/penalty
    bonus = 0
    if "+" in expr:
        parts = expr.split("+", 1)
        expr = parts[0]
        try:
            bonus = int(parts[1])
        except ValueError:
            return None
    elif "-" in expr:
        # Only split on the last '-' to avoid issues with negative numbers
        idx = expr.rfind("-")
        if idx > 0:
            try:
                bonus = -int(expr[idx + 1:])
            except ValueError:
                return None
            expr = expr[:idx]

    m = _DICE_RE.match(expr + "+0")  # Append dummy to satisfy regex if stripped
    # Simpler: just re-parse
    m = re.match(r"^(\d+)d(\d+)$", expr, re.IGNORECASE)
    if not m:
        return None

    num_dice = int(m.group(1))
    die_size = int(m.group(2))
    return num_dice * die_size + bonus


def _estimate_damage_band(damage_dice: Optional[str]) -> Optional[Scale]:
    """Map damage dice to expected Scale band.

    Thresholds (max damage of dice expression, ignoring bonuses):
      SUBTLE:      max ≤ 12  (up to 2d6)
      MODERATE:    max ≤ 36  (up to 6d6)
      DRAMATIC:    max ≤ 72  (up to 12d6)
      CATASTROPHIC: max > 72  (over 12d6)
    """
    if not damage_dice:
        return None

    expr = damage_dice.strip().lower()

    # Strip bonus for band calculation — we only care about dice magnitude
    for sep in ("+", "-"):
        if sep in expr:
            expr = expr[:expr.index(sep)]
            break

    m = re.match(r"^(\d+)d(\d+)$", expr, re.IGNORECASE)
    if not m:
        return None

    num_dice = int(m.group(1))
    die_size = int(m.group(2))
    max_damage = num_dice * die_size

    if max_damage <= 12:
        return Scale.SUBTLE
    elif max_damage <= 36:
        return Scale.MODERATE
    elif max_damage <= 72:
        return Scale.DRAMATIC
    else:
        return Scale.CATASTROPHIC


# ═══════════════════════════════════════════════════════════════════════
# Individual CT Checks
# ═══════════════════════════════════════════════════════════════════════

# AoE delivery modes that conflict with single-target targeting
_AOE_DELIVERY_MODES = frozenset({
    DeliveryMode.BURST_FROM_POINT,
    DeliveryMode.CONE,
    DeliveryMode.LINE,
    DeliveryMode.EMANATION,
})


def _check_ct_001(
    content_id: str,
    params: RuleParameters,
    entry: AbilityPresentationEntry,
) -> Optional[CompileViolation]:
    """CT-001: Delivery Mode vs Target Type.

    If target_type == 'single' and delivery_mode is an AoE mode: FAIL.
    """
    if params.target_type == "single" and entry.delivery_mode in _AOE_DELIVERY_MODES:
        return CompileViolation(
            check_id="CT-001",
            content_id=content_id,
            severity="FAIL",
            detail=(
                f"target_type='single' but delivery_mode="
                f"'{entry.delivery_mode.value}' (AoE mode)"
            ),
        )
    return None


def _check_ct_002(
    content_id: str,
    params: RuleParameters,
    entry: AbilityPresentationEntry,
) -> Optional[CompileViolation]:
    """CT-002: Delivery Mode vs Area Shape.

    area_shape must align with delivery_mode:
      burst → BURST_FROM_POINT
      cone  → CONE
      line  → LINE
    """
    shape_to_mode = {
        "burst": DeliveryMode.BURST_FROM_POINT,
        "cone": DeliveryMode.CONE,
        "line": DeliveryMode.LINE,
    }

    if params.area_shape in shape_to_mode:
        expected = shape_to_mode[params.area_shape]
        if entry.delivery_mode != expected:
            return CompileViolation(
                check_id="CT-002",
                content_id=content_id,
                severity="FAIL",
                detail=(
                    f"area_shape='{params.area_shape}' requires "
                    f"delivery_mode='{expected.value}', "
                    f"got '{entry.delivery_mode.value}'"
                ),
            )
    return None


def _check_ct_003(
    content_id: str,
    params: RuleParameters,
    entry: AbilityPresentationEntry,
) -> Optional[CompileViolation]:
    """CT-003: Origin Rule vs Delivery Mode.

    If range_ft == 0 then origin_rule must be FROM_CASTER
    and delivery_mode must be TOUCH (or SELF).
    """
    if params.range_ft == 0:
        # Allow SELF delivery for self-targeting spells
        valid_modes = {DeliveryMode.TOUCH, DeliveryMode.SELF}
        if entry.origin_rule != OriginRule.FROM_CASTER or entry.delivery_mode not in valid_modes:
            return CompileViolation(
                check_id="CT-003",
                content_id=content_id,
                severity="FAIL",
                detail=(
                    f"range_ft=0 requires origin_rule='from_caster' and "
                    f"delivery_mode in (touch, self), got origin_rule="
                    f"'{entry.origin_rule.value}', delivery_mode="
                    f"'{entry.delivery_mode.value}'"
                ),
            )
    return None


def _check_ct_004(
    content_id: str,
    params: RuleParameters,
    entry: AbilityPresentationEntry,
) -> Optional[CompileViolation]:
    """CT-004: Scale vs Damage Magnitude.

    Parse damage dice and check if scale matches expected band.
    """
    expected_scale = _estimate_damage_band(params.damage_dice)
    if expected_scale is not None and entry.scale != expected_scale:
        return CompileViolation(
            check_id="CT-004",
            content_id=content_id,
            severity="WARN",
            detail=(
                f"damage_dice='{params.damage_dice}' suggests scale="
                f"'{expected_scale.value}', got '{entry.scale.value}'"
            ),
        )
    return None


def _check_ct_005(
    content_id: str,
    params: RuleParameters,
    entry: AbilityPresentationEntry,
) -> Optional[CompileViolation]:
    """CT-005: Save Type vs Staging.

    If save_type is None and staging is DELAYED: WARN.
    A delayed effect with no save is suspicious.
    """
    if params.save_type is None and entry.staging == Staging.DELAYED:
        return CompileViolation(
            check_id="CT-005",
            content_id=content_id,
            severity="WARN",
            detail="save_type is None but staging='delayed' (delayed effects typically have saves)",
        )
    return None


def _check_ct_006(
    content_id: str,
    _params: RuleParameters,
    entry: AbilityPresentationEntry,
) -> Optional[CompileViolation]:
    """CT-006: Contraindication Self-Conflict.

    If any tag in contraindications appears in vfx_tags or sfx_tags: WARN.
    """
    contra_set = set(entry.contraindications)
    if not contra_set:
        return None

    vfx_conflict = contra_set & set(entry.vfx_tags)
    sfx_conflict = contra_set & set(entry.sfx_tags)
    conflicts = vfx_conflict | sfx_conflict

    if conflicts:
        return CompileViolation(
            check_id="CT-006",
            content_id=content_id,
            severity="WARN",
            detail=(
                f"contraindication tags {sorted(conflicts)} "
                f"also appear in vfx_tags or sfx_tags"
            ),
        )
    return None


def _check_ct_007(
    content_id: str,
    params: RuleParameters,
    entry: AbilityPresentationEntry,
) -> Optional[CompileViolation]:
    """CT-007: Residue vs Staging.

    - If duration_unit == 'instantaneous' and residue is non-empty: WARN
    - If staging == LINGER and residue is empty: WARN
    """
    if params.duration_unit == "instantaneous" and entry.residue:
        return CompileViolation(
            check_id="CT-007",
            content_id=content_id,
            severity="WARN",
            detail=(
                f"duration_unit='instantaneous' but residue is non-empty: "
                f"{list(entry.residue)}"
            ),
        )

    if entry.staging == Staging.LINGER and not entry.residue:
        return CompileViolation(
            check_id="CT-007",
            content_id=content_id,
            severity="WARN",
            detail="staging='linger' but residue is empty (lingering effects should leave residue)",
        )

    return None


# ═══════════════════════════════════════════════════════════════════════
# Main cross_validate function
# ═══════════════════════════════════════════════════════════════════════

# All checks in execution order
_ALL_CHECKS = [
    _check_ct_001,
    _check_ct_002,
    _check_ct_003,
    _check_ct_004,
    _check_ct_005,
    _check_ct_006,
    _check_ct_007,
]


def cross_validate(
    rule_entries: Dict[str, RuleEntry],
    ability_entries: Dict[str, AbilityPresentationEntry],
) -> List[CompileViolation]:
    """Compare Layer A RuleParameters against Layer B AbilityPresentationEntry.

    Runs all 7 CT checks for each content_id present in both registries.
    Content IDs present in only one registry are silently skipped (those
    are different types of inconsistency handled elsewhere).

    Args:
        rule_entries: {content_id: RuleEntry} from the rulebook stage.
        ability_entries: {content_id: AbilityPresentationEntry} from semantics stage.

    Returns:
        List of CompileViolation (may be empty). FAIL violations indicate
        compilation should be blocked; WARN violations are informational.
    """
    violations: List[CompileViolation] = []

    # Only validate content_ids that appear in both registries
    common_ids = sorted(set(rule_entries.keys()) & set(ability_entries.keys()))

    for content_id in common_ids:
        rule = rule_entries[content_id]
        ability = ability_entries[content_id]

        for check_fn in _ALL_CHECKS:
            violation = check_fn(content_id, rule.parameters, ability)
            if violation is not None:
                violations.append(violation)

    return violations


# ═══════════════════════════════════════════════════════════════════════
# CrossValidateStage — integrates into World Compiler pipeline
# ═══════════════════════════════════════════════════════════════════════


class CrossValidateStage(CompileStage):
    """Stage 4: Cross-validate Layer A vs Layer B after semantics + rulebook."""

    @property
    def stage_id(self) -> str:
        return "cross_validate"

    @property
    def stage_number(self) -> int:
        return 4

    @property
    def depends_on(self) -> Tuple[str, ...]:
        return ("semantics", "rulebook")

    def execute(self, context: CompileContext) -> StageResult:
        """Run cross-validation checks on compiled data.

        1. Load rule_registry.json (Layer A)
        2. Load presentation_semantics.json (Layer B)
        3. Run all CT checks
        4. FAIL violations → return failed status (blocks compilation)
        5. WARN violations → return in stage warnings
        """
        log = logging.getLogger(__name__)
        log.info("Stage 4 (cross_validate): starting")
        start_ms = time.monotonic_ns() // 1_000_000

        try:
            # Load Layer A: rule_registry.json → {content_id: RuleEntry}
            rule_registry_path = context.workspace_dir / "rule_registry.json"
            if not rule_registry_path.exists():
                elapsed = (time.monotonic_ns() // 1_000_000) - start_ms
                return StageResult(
                    stage_id=self.stage_id,
                    status="success",
                    output_files=(),
                    warnings=("rule_registry.json not found; skipping cross-validation",),
                    elapsed_ms=elapsed,
                )

            with open(rule_registry_path, "r", encoding="utf-8") as f:
                rule_data = json.load(f)

            rule_entries: Dict[str, RuleEntry] = {}
            for entry_dict in rule_data.get("entries", []):
                entry = RuleEntry.from_dict(entry_dict)
                rule_entries[entry.content_id] = entry

            # Load Layer B: presentation_semantics.json → {content_id: AbilityPresentationEntry}
            semantics_path = context.workspace_dir / "presentation_semantics.json"
            if not semantics_path.exists():
                elapsed = (time.monotonic_ns() // 1_000_000) - start_ms
                return StageResult(
                    stage_id=self.stage_id,
                    status="success",
                    output_files=(),
                    warnings=("presentation_semantics.json not found; skipping cross-validation",),
                    elapsed_ms=elapsed,
                )

            with open(semantics_path, "r", encoding="utf-8") as f:
                semantics_data = json.load(f)

            ability_entries: Dict[str, AbilityPresentationEntry] = {}
            for entry_dict in semantics_data.get("ability_entries", []):
                entry = AbilityPresentationEntry.from_dict(entry_dict)
                ability_entries[entry.content_id] = entry

            # Run cross-validation
            violations = cross_validate(rule_entries, ability_entries)

            # Separate FAIL vs WARN
            fails = [v for v in violations if v.severity == "FAIL"]
            warns = [v for v in violations if v.severity == "WARN"]

            elapsed = (time.monotonic_ns() // 1_000_000) - start_ms

            log.info(
                "Stage 4 (cross_validate): %d violations (%d FAIL, %d WARN)",
                len(violations), len(fails), len(warns),
            )

            # WARN violations become stage warnings
            warning_strs = tuple(
                f"[{v.check_id}] {v.content_id}: {v.detail}" for v in warns
            )

            if fails:
                # P0 violations block compilation
                fail_detail = "; ".join(
                    f"[{v.check_id}] {v.content_id}: {v.detail}" for v in fails
                )
                return StageResult(
                    stage_id=self.stage_id,
                    status="failed",
                    output_files=(),
                    warnings=warning_strs,
                    error=f"Cross-validation FAIL: {fail_detail}",
                    elapsed_ms=elapsed,
                )

            return StageResult(
                stage_id=self.stage_id,
                status="success",
                output_files=(),
                warnings=warning_strs,
                elapsed_ms=elapsed,
            )

        except Exception as exc:
            elapsed = (time.monotonic_ns() // 1_000_000) - start_ms
            log.error("Stage 4 (cross_validate) failed: %s", exc)
            return StageResult(
                stage_id=self.stage_id,
                status="failed",
                output_files=(),
                error=str(exc),
                elapsed_ms=elapsed,
            )
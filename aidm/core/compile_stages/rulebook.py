"""Stage 2: Rulebook Generation — produce rule_registry.json from content pack.

Joins lexicon + semantics output to produce a rule registry binding every
spell and active feat to an engine procedure with world-flavored text,
parameters, and provenance.

BOUNDARY LAW: This is a core-layer component. Imports from aidm.schemas
are allowed. No imports from aidm.lens or aidm.immersion.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from aidm.core.compile_stages._base import CompileContext, CompileStage, StageResult
from aidm.schemas.rulebook import (
    RuleEntry,
    RuleParameters,
    RuleProvenance,
    RuleTextSlots,
)

COMPILER_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0"


# ═══════════════════════════════════════════════════════════════════════
# Parameter extraction helpers
# ═══════════════════════════════════════════════════════════════════════


def _parse_range_ft(range_formula: str) -> int | None:
    """Convert a range_formula string to an integer feet value, or None."""
    if not range_formula:
        return None
    # Named ranges from 3.5e SRD
    named = {
        "close": 25,
        "medium": 100,
        "long": 400,
        "touch": 0,
        "personal": 0,
    }
    lower = range_formula.lower().strip()
    if lower in named:
        return named[lower]
    # Try to parse as raw integer (e.g. "120")
    try:
        return int(lower)
    except (ValueError, TypeError):
        return None


def _parse_duration(duration_formula: str) -> Tuple[str | None, int | None]:
    """Extract duration_unit and duration_value from a duration_formula string.

    Returns:
        (duration_unit, duration_value) — either or both may be None.
    """
    if not duration_formula:
        return None, None
    lower = duration_formula.lower().strip()
    if lower == "instantaneous":
        return "instantaneous", None
    if lower == "permanent":
        return "permanent", None
    if "round" in lower:
        return "rounds", _extract_leading_int(lower)
    if "min" in lower:
        return "minutes", _extract_leading_int(lower)
    if "hour" in lower:
        return "hours", _extract_leading_int(lower)
    if "day" in lower:
        return "days", _extract_leading_int(lower)
    # Fallback — keep the raw string as unit
    return lower, None


def _extract_leading_int(s: str) -> int | None:
    """Extract the first integer from a string, or return None."""
    digits = []
    for ch in s:
        if ch.isdigit():
            digits.append(ch)
        elif digits:
            break
    return int("".join(digits)) if digits else None


def _extract_spell_parameters(spell: Dict[str, Any]) -> RuleParameters:
    """Build RuleParameters from a content-pack spell dict."""
    range_ft = _parse_range_ft(spell.get("range_formula", "") or "")
    dur_unit, dur_value = _parse_duration(spell.get("duration_formula", "") or "")

    return RuleParameters(
        range_ft=range_ft,
        area_shape=spell.get("aoe_shape"),
        area_radius_ft=spell.get("aoe_radius_ft"),
        damage_dice=spell.get("damage_formula"),
        damage_type=spell.get("damage_type"),
        save_type=spell.get("save_type"),
        save_effect=spell.get("save_effect"),
        duration_unit=dur_unit,
        duration_value=dur_value,
        action_cost=spell.get("casting_time"),
        target_type=spell.get("target_type"),
    )


def _extract_feat_parameters(feat: Dict[str, Any]) -> RuleParameters:
    """Build RuleParameters from a content-pack feat dict."""
    custom: Dict[str, Any] = {}
    if feat.get("bonus_value") is not None:
        custom["bonus_value"] = feat["bonus_value"]
    if feat.get("bonus_type"):
        custom["bonus_type"] = feat["bonus_type"]
    if feat.get("bonus_applies_to"):
        custom["bonus_applies_to"] = feat["bonus_applies_to"]

    action_cost = None
    grants_action = feat.get("grants_action") or ""
    if grants_action:
        action_cost = "free" if "free" in grants_action.lower() else "special"

    return RuleParameters(
        action_cost=action_cost,
        target_type="self",
        custom=custom,
    )


# ═══════════════════════════════════════════════════════════════════════
# Text-slot generation (stub mode)
# ═══════════════════════════════════════════════════════════════════════


def _spell_short_description(spell: Dict[str, Any]) -> str:
    """Generate a short_description for a spell (max 120 chars)."""
    tier = spell.get("tier", 0)
    school = spell.get("school_category", "unknown")
    effect = spell.get("effect_type", "effect")
    desc = f"Tier {tier} {school} {effect}"
    return desc[:120]


def _spell_mechanical_summary(spell: Dict[str, Any]) -> str:
    """Generate a mechanical_summary from spell parameters."""
    parts: List[str] = []
    if spell.get("damage_formula"):
        parts.append(f"Damage: {spell['damage_formula']}")
    if spell.get("damage_type"):
        parts.append(f"Type: {spell['damage_type']}")
    if spell.get("range_formula"):
        parts.append(f"Range: {spell['range_formula']}")
    if spell.get("aoe_shape"):
        radius = spell.get("aoe_radius_ft")
        if radius:
            parts.append(f"Area: {spell['aoe_shape']} {radius}ft")
        else:
            parts.append(f"Area: {spell['aoe_shape']}")
    if spell.get("save_type"):
        parts.append(f"Save: {spell['save_type']}")
    if spell.get("duration_formula"):
        parts.append(f"Duration: {spell['duration_formula']}")
    return "; ".join(parts) if parts else "No parameters"


def _feat_short_description(feat: Dict[str, Any]) -> str:
    """Generate a short_description for a feat (max 120 chars)."""
    effect = feat.get("effect_type", "general")
    feat_type = feat.get("feat_type", "general")
    desc = f"Active {feat_type} feat ({effect})"
    return desc[:120]


def _feat_mechanical_summary(feat: Dict[str, Any]) -> str:
    """Generate a mechanical_summary from feat parameters."""
    parts: List[str] = []
    if feat.get("trigger"):
        parts.append(f"Trigger: {feat['trigger']}")
    if feat.get("grants_action"):
        parts.append(f"Grants: {feat['grants_action']}")
    if feat.get("bonus_value") is not None:
        parts.append(f"Bonus: +{feat['bonus_value']}")
    if feat.get("bonus_applies_to"):
        parts.append(f"Applies to: {feat['bonus_applies_to']}")
    return "; ".join(parts) if parts else "No parameters"


# ═══════════════════════════════════════════════════════════════════════
# Active-feat check (duplicated from semantics.py to avoid cross-import)
# ═══════════════════════════════════════════════════════════════════════


def is_active_feat(feat: Dict[str, Any]) -> bool:
    """Return True if the feat has active mechanics.

    Only feats with a trigger or grants_action get rule entries.
    Passive feats (proficiency, skill modifiers) are excluded.
    """
    trigger = feat.get("trigger")
    grants_action = feat.get("grants_action")
    return bool(trigger) or bool(grants_action)


# ═══════════════════════════════════════════════════════════════════════
# Tag extraction
# ═══════════════════════════════════════════════════════════════════════


def _spell_tags(spell: Dict[str, Any]) -> Tuple[str, ...]:
    """Extract tags from a spell dict."""
    tags: List[str] = []
    # combat_role_tags from content pack
    for tag in spell.get("combat_role_tags", []):
        if tag and tag not in tags:
            tags.append(tag)
    # school as tag
    school = spell.get("school_category", "")
    if school and school not in tags:
        tags.append(school)
    return tuple(tags)


def _feat_tags(feat: Dict[str, Any]) -> Tuple[str, ...]:
    """Extract tags from a feat dict."""
    tags: List[str] = []
    feat_type = feat.get("feat_type", "")
    if feat_type and feat_type not in tags:
        tags.append(feat_type)
    effect_type = feat.get("effect_type", "")
    if effect_type and effect_type not in tags:
        tags.append(effect_type)
    return tuple(tags)


# ═══════════════════════════════════════════════════════════════════════
# RulebookStage
# ═══════════════════════════════════════════════════════════════════════


class RulebookStage(CompileStage):
    """Stage 2: Generate rule_registry.json binding content to engine procedures."""

    @property
    def stage_id(self) -> str:
        return "rulebook"

    @property
    def stage_number(self) -> int:
        return 2

    @property
    def depends_on(self) -> Tuple[str, ...]:
        return ("lexicon", "semantics")

    def execute(self, context: CompileContext) -> StageResult:
        """Execute the rulebook stage.

        1. Load spells and feats from content pack
        2. Map each to a RuleEntry with parameters, text_slots, provenance
        3. Sort by content_id (deterministic)
        4. Write rule_registry.json to workspace
        """
        log = logging.getLogger(__name__)
        log.info("Stage 2 (rulebook): starting")

        try:
            return self._execute_inner(context, log)
        except Exception as exc:
            log.error("Stage 2 (rulebook) failed: %s", exc)
            return StageResult(
                stage_id=self.stage_id,
                status="failed",
                output_files=(),
                error=str(exc),
            )

    def _execute_inner(
        self, context: CompileContext, log: logging.Logger
    ) -> StageResult:
        provenance = RuleProvenance(
            source="world_compiler",
            compiler_version=COMPILER_VERSION,
            seed_used=context.world_seed,
            content_pack_id=context.content_pack_id,
        )

        # ── Load content ───────────────────────────────────────────
        spells = self._load_spells(context.content_pack_dir)
        log.info("Loaded %d spells", len(spells))

        feats = self._load_feats(context.content_pack_dir)
        active_feats = [f for f in feats if is_active_feat(f)]
        log.info("Loaded %d feats (%d active)", len(feats), len(active_feats))

        # ── Build rule entries ─────────────────────────────────────
        entries: List[RuleEntry] = []
        seen_ids: set = set()

        for spell in spells:
            template_id = spell.get("template_id", "")
            content_id = f"spell.{template_id.lower()}"
            if content_id in seen_ids:
                continue
            seen_ids.add(content_id)

            entry = RuleEntry(
                content_id=content_id,
                procedure_id=f"proc.spell.{template_id.lower()}",
                rule_type="spell",
                world_name=content_id,  # stub mode: use content_id
                parameters=_extract_spell_parameters(spell),
                provenance=RuleProvenance(
                    source=provenance.source,
                    compiler_version=provenance.compiler_version,
                    seed_used=provenance.seed_used,
                    content_pack_id=provenance.content_pack_id,
                    template_ids=(template_id,),
                ),
                text_slots=RuleTextSlots(
                    short_description=_spell_short_description(spell),
                    mechanical_summary=_spell_mechanical_summary(spell),
                ),
                tags=_spell_tags(spell),
            )
            entries.append(entry)

        for feat in active_feats:
            template_id = feat.get("template_id", "")
            content_id = f"feat.{template_id.lower()}"
            if content_id in seen_ids:
                continue
            seen_ids.add(content_id)

            entry = RuleEntry(
                content_id=content_id,
                procedure_id=f"proc.feat.{template_id.lower()}",
                rule_type="feat",
                world_name=content_id,  # stub mode: use content_id
                parameters=_extract_feat_parameters(feat),
                provenance=RuleProvenance(
                    source=provenance.source,
                    compiler_version=provenance.compiler_version,
                    seed_used=provenance.seed_used,
                    content_pack_id=provenance.content_pack_id,
                    template_ids=(template_id,),
                ),
                text_slots=RuleTextSlots(
                    short_description=_feat_short_description(feat),
                    mechanical_summary=_feat_mechanical_summary(feat),
                ),
                tags=_feat_tags(feat),
            )
            entries.append(entry)

        # ── Sort by content_id for determinism ─────────────────────
        entries.sort(key=lambda e: e.content_id)

        # ── Build registry dict ────────────────────────────────────
        world_id = context.world_id or "unknown"
        registry_dict: Dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "world_id": world_id,
            "compiler_version": COMPILER_VERSION,
            "entry_count": len(entries),
            "entries": [e.to_dict() for e in entries],
        }

        # ── Write output ───────────────────────────────────────────
        output_file = "rule_registry.json"
        output_path = context.workspace_dir / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(registry_dict, f, indent=2)

        log.info(
            "Stage 2 (rulebook): wrote %d entries (%d spells + %d feats)",
            len(entries),
            len([e for e in entries if e.rule_type == "spell"]),
            len([e for e in entries if e.rule_type == "feat"]),
        )

        return StageResult(
            stage_id=self.stage_id,
            status="success",
            output_files=(output_file,),
        )

    # ── Content loading (same pattern as semantics.py) ─────────────

    @staticmethod
    def _load_spells(content_pack_dir: Path) -> List[Dict[str, Any]]:
        """Load spell data from content pack JSON."""
        spells_path = content_pack_dir / "spells.json"
        if not spells_path.exists():
            return []
        with open(spells_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "spells" in data:
            return data["spells"]
        return []

    @staticmethod
    def _load_feats(content_pack_dir: Path) -> List[Dict[str, Any]]:
        """Load feat data from content pack JSON."""
        feats_path = content_pack_dir / "feats.json"
        if not feats_path.exists():
            return []
        with open(feats_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "feats" in data:
            return data["feats"]
        if isinstance(data, list):
            return data
        return []

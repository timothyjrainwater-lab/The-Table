"""Content Pack Loader — read-only registry for content pack data.

Loads extracted content pack JSON files (spells, creatures, feats) from
aidm/data/content_pack/ and provides lookup, filtering, and validation.

Immutable after loading. Consumed by the World Compiler pipeline.

BOUNDARY LAW (BL-003): No imports from aidm/core/.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from aidm.schemas.content_pack import (
    ContentPack,
    MechanicalCreatureTemplate,
    MechanicalFeatTemplate,
    MechanicalSpellTemplate,
    compute_pack_id,
)


class DuplicateTemplateIdError(ValueError):
    """Raised when duplicate template_ids are found within a category."""
    pass


class ContentPackLoader:
    """Loads and validates the content pack from aidm/data/content_pack/*.json.

    Read-only after construction. All templates are frozen dataclasses.
    """

    def __init__(
        self,
        spells: List[MechanicalSpellTemplate],
        creatures: List[MechanicalCreatureTemplate],
        feats: List[MechanicalFeatTemplate],
        pack_id: str = "",
        extraction_versions: Optional[Dict[str, str]] = None,
        source_ids: Optional[List[str]] = None,
    ):
        self._spells = tuple(spells)
        self._creatures = tuple(creatures)
        self._feats = tuple(feats)
        self._pack_id = pack_id
        self._extraction_versions = extraction_versions or {}
        self._source_ids = tuple(source_ids or [])

        # Build indices
        self._spell_index: Dict[str, MechanicalSpellTemplate] = {
            s.template_id: s for s in self._spells
        }
        self._creature_index: Dict[str, MechanicalCreatureTemplate] = {
            c.template_id: c for c in self._creatures
        }
        self._feat_index: Dict[str, MechanicalFeatTemplate] = {
            f.template_id: f for f in self._feats
        }

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @classmethod
    def from_directory(cls, path: Path) -> "ContentPackLoader":
        """Load all content pack JSON files from a directory.

        Expected files:
            spells.json — bare array or {spells: [...]} envelope
            creatures.json — {creatures: [...]} envelope
            feats.json — {feats: [...]} envelope

        Missing files are silently skipped (empty collections).
        """
        spells: List[MechanicalSpellTemplate] = []
        creatures: List[MechanicalCreatureTemplate] = []
        feats: List[MechanicalFeatTemplate] = []
        extraction_versions: Dict[str, str] = {}
        source_ids_set: set = set()
        file_paths: List[str] = []

        # Spells
        spells_path = path / "spells.json"
        if spells_path.exists():
            file_paths.append(str(spells_path))
            with open(spells_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # spells.json is a bare array
            if isinstance(data, list):
                spells = [MechanicalSpellTemplate.from_dict(s) for s in data]
            else:
                # Envelope format
                spell_list = data.get("spells", [])
                spells = [MechanicalSpellTemplate.from_dict(s) for s in spell_list]
                if "extraction_version" in data:
                    extraction_versions["spells"] = data["extraction_version"]
                if "source_id" in data:
                    source_ids_set.add(data["source_id"])

        # Creatures
        creatures_path = path / "creatures.json"
        if creatures_path.exists():
            file_paths.append(str(creatures_path))
            with open(creatures_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            creature_list = data.get("creatures", []) if isinstance(data, dict) else data
            creatures = [MechanicalCreatureTemplate.from_dict(c) for c in creature_list]
            if isinstance(data, dict):
                if "extraction_version" in data:
                    extraction_versions["creatures"] = data["extraction_version"]
                if "source_id" in data:
                    source_ids_set.add(data["source_id"])

        # Feats
        feats_path = path / "feats.json"
        if feats_path.exists():
            file_paths.append(str(feats_path))
            with open(feats_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            feat_list = data.get("feats", []) if isinstance(data, dict) else data
            feats = [MechanicalFeatTemplate.from_dict(ft) for ft in feat_list]
            if isinstance(data, dict):
                if "extraction_version" in data:
                    extraction_versions["feats"] = data["extraction_version"]
                if "source_id" in data:
                    source_ids_set.add(data["source_id"])

        pack_id = compute_pack_id(*file_paths) if file_paths else ""

        return cls(
            spells=spells,
            creatures=creatures,
            feats=feats,
            pack_id=pack_id,
            extraction_versions=extraction_versions,
            source_ids=sorted(source_ids_set),
        )

    @classmethod
    def from_content_pack(cls, pack: ContentPack) -> "ContentPackLoader":
        """Load from a ContentPack dataclass."""
        return cls(
            spells=list(pack.spells),
            creatures=list(pack.creatures),
            feats=list(pack.feats),
            pack_id=pack.pack_id,
            extraction_versions=dict(pack.extraction_versions),
            source_ids=list(pack.source_ids),
        )

    @classmethod
    def empty(cls) -> "ContentPackLoader":
        """Create an empty loader (valid — no content yet)."""
        return cls(spells=[], creatures=[], feats=[])

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def get_spell(self, template_id: str) -> Optional[MechanicalSpellTemplate]:
        """Look up a spell by template_id."""
        return self._spell_index.get(template_id)

    def get_creature(self, template_id: str) -> Optional[MechanicalCreatureTemplate]:
        """Look up a creature by template_id."""
        return self._creature_index.get(template_id)

    def get_feat(self, template_id: str) -> Optional[MechanicalFeatTemplate]:
        """Look up a feat by template_id."""
        return self._feat_index.get(template_id)

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def list_spells_by_tier(self, tier: int) -> List[MechanicalSpellTemplate]:
        """List all spells of a given tier (spell level 0-9)."""
        return [s for s in self._spells if s.tier == tier]

    def list_spells_by_school(self, school: str) -> List[MechanicalSpellTemplate]:
        """List all spells of a given school category."""
        school_lower = school.lower()
        return [s for s in self._spells if s.school_category == school_lower]

    def list_creatures_by_type(self, creature_type: str) -> List[MechanicalCreatureTemplate]:
        """List all creatures of a given type."""
        type_lower = creature_type.lower()
        return [c for c in self._creatures if c.creature_type == type_lower]

    def list_creatures_by_cr(self, cr: float) -> List[MechanicalCreatureTemplate]:
        """List all creatures with a given challenge rating."""
        return [c for c in self._creatures if c.cr == cr]

    def list_feats_by_type(self, feat_type: str) -> List[MechanicalFeatTemplate]:
        """List all feats of a given type."""
        type_lower = feat_type.lower()
        return [f for f in self._feats if f.feat_type == type_lower]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> List[str]:
        """Run validation checks. Returns list of error strings (empty = valid).

        Checks:
        1. No duplicate template_ids within a category
        2. All feat prereq_feat_refs resolve to existing feat template_ids
        3. No string field value longer than 100 chars (prose leakage check)
        4. All required fields present (template_id non-empty)
        """
        errors: List[str] = []

        # 1. No duplicate template_ids
        errors.extend(self._check_duplicates("spell", self._spells))
        errors.extend(self._check_duplicates("creature", self._creatures))
        errors.extend(self._check_duplicates("feat", self._feats))

        # 2. Feat prereq chains resolve
        feat_ids = set(self._feat_index.keys())
        for feat in self._feats:
            for ref in feat.prereq_feat_refs:
                if ref not in feat_ids:
                    errors.append(
                        f"feat {feat.template_id}: prereq_feat_ref "
                        f"'{ref}' not found in feat index"
                    )

        # 3. No string field > 100 chars (prose leakage)
        errors.extend(self._check_field_lengths("spell", self._spells))
        errors.extend(self._check_field_lengths("creature", self._creatures))
        errors.extend(self._check_field_lengths("feat", self._feats))

        # 4. All template_ids non-empty
        for s in self._spells:
            if not s.template_id:
                errors.append("spell: empty template_id")
        for c in self._creatures:
            if not c.template_id:
                errors.append("creature: empty template_id")
        for f in self._feats:
            if not f.template_id:
                errors.append("feat: empty template_id")

        return errors

    def _check_duplicates(self, category: str, templates: tuple) -> List[str]:
        """Check for duplicate template_ids within a category."""
        seen: Dict[str, int] = {}
        errors: List[str] = []
        for i, t in enumerate(templates):
            tid = t.template_id
            if tid in seen:
                errors.append(
                    f"{category}: duplicate template_id '{tid}' "
                    f"at indices {seen[tid]} and {i}"
                )
            seen[tid] = i
        return errors

    def _check_field_lengths(self, category: str, templates: tuple) -> List[str]:
        """Check that no string field exceeds 100 chars."""
        errors: List[str] = []
        # Fields to skip length check on (these can legitimately be long)
        skip_fields = {
            "replaces_normal",  # contains truncated normal text
            "organization_patterns",  # organization descriptions
        }
        for t in templates:
            d = t.to_dict()
            for key, val in d.items():
                if key in skip_fields:
                    continue
                if isinstance(val, str) and len(val) > 100:
                    errors.append(
                        f"{category} {t.template_id}: field '{key}' "
                        f"is {len(val)} chars (max 100)"
                    )
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, str) and len(item) > 100:
                            errors.append(
                                f"{category} {t.template_id}: "
                                f"item in '{key}' is {len(item)} chars (max 100)"
                            )
        return errors

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def spell_count(self) -> int:
        return len(self._spells)

    @property
    def creature_count(self) -> int:
        return len(self._creatures)

    @property
    def feat_count(self) -> int:
        return len(self._feats)

    @property
    def pack_id(self) -> str:
        return self._pack_id

    @property
    def source_ids(self) -> tuple:
        return self._source_ids

    @property
    def extraction_versions(self) -> dict:
        return dict(self._extraction_versions)

    def to_content_pack(self) -> ContentPack:
        """Convert to a ContentPack dataclass."""
        return ContentPack(
            schema_version="1.0.0",
            pack_id=self._pack_id,
            spells=self._spells,
            creatures=self._creatures,
            feats=self._feats,
            source_ids=self._source_ids,
            extraction_versions=dict(self._extraction_versions),
        )

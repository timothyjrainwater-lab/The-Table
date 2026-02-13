"""Stage 1: Lexicon Generation — assign world-flavored names to all content IDs.

Reads template IDs from the content pack, generates world-flavored names
(via LLM or deterministic stub), and writes lexicon.json conforming to
VocabularyRegistry schema.

BOUNDARY LAW: May import from aidm/schemas/ (data models). Must NOT import
from aidm/lens/ (Lens reads our output, not the other way around).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from aidm.core.compile_stages._base import CompileContext, CompileStage, StageResult
from aidm.schemas.vocabulary import (
    LocalizationHooks,
    TaxonomyCategory,
    VocabularyEntry,
    VocabularyProvenance,
    VocabularyRegistry,
    WorldTaxonomy,
)

COMPILER_VERSION = "0.1.0"

# Domain mapping from content pack file names to vocabulary domains.
_FILE_DOMAIN_MAP = {
    "spells.json": "spell",
    "creatures.json": "creature",
    "feats.json": "feat",
}

# Stub-mode category assignments per domain.
_STUB_CATEGORIES = {
    "spell": "arcane_arts",
    "creature": "bestiary",
    "feat": "martial_techniques",
}

# Stub-mode tone register per domain.
_STUB_TONE = {
    "spell": "archaic",
    "creature": "mythic",
    "feat": "technical",
}

# Stub-mode semantic root prefix per domain.
_STUB_SEMANTIC_PREFIX = {
    "spell": "spell_effect",
    "creature": "creature_type",
    "feat": "combat_technique",
}


def _make_lexicon_id(world_seed: int, content_id: str) -> str:
    """Deterministic lexicon_id: sha256(world_seed:content_id)[:16]."""
    raw = f"{world_seed}:{content_id}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def _content_id_from_template(domain: str, template_id: str) -> str:
    """Build a content_id from domain + template_id.

    E.g. domain='spell', template_id='SPELL_001' -> 'spell.SPELL_001'
    """
    return f"{domain}.{template_id}"


def _stub_world_name(template_id: str, world_seed: int) -> str:
    """Generate a deterministic stub name from template_id + seed.

    Produces names like 'Lexis_SPELL_001_42' — clearly synthetic but
    unique and deterministic.
    """
    seed_suffix = world_seed % 1000
    return f"Lexis_{template_id}_{seed_suffix}"


def _stub_short_description(domain: str, template_id: str) -> str:
    """Generate a deterministic stub description (≤120 chars)."""
    return f"A {domain} entry for {template_id}."


def _load_template_ids(content_pack_dir: Path) -> Dict[str, List[str]]:
    """Load all template IDs from the content pack, grouped by domain.

    Returns:
        Dict mapping domain ('spell', 'creature', 'feat') to list of
        template_id strings (e.g. ['SPELL_001', 'SPELL_002', ...]).
    """
    result: Dict[str, List[str]] = {}

    for filename, domain in _FILE_DOMAIN_MAP.items():
        filepath = content_pack_dir / filename
        if not filepath.exists():
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Content pack files have two formats:
        #   - Array of objects (spells.json): [{"template_id": "SPELL_001", ...}, ...]
        #   - Object with a list key (creatures.json, feats.json):
        #     {"creatures": [...], "creature_count": N, ...}
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Find the list key — it's the plural of the domain or the
            # domain + 's'.
            list_key = f"{domain}s" if not domain.endswith("s") else domain
            items = data.get(list_key, [])
        else:
            continue

        ids = [item["template_id"] for item in items if "template_id" in item]
        if ids:
            result[domain] = ids

    return result


def _build_stub_entries(
    template_ids_by_domain: Dict[str, List[str]],
    world_seed: int,
    content_pack_id: str,
) -> List[VocabularyEntry]:
    """Build VocabularyEntry list using deterministic stub names."""
    entries: List[VocabularyEntry] = []

    for domain, template_ids in sorted(template_ids_by_domain.items()):
        for template_id in template_ids:
            content_id = _content_id_from_template(domain, template_id)
            lexicon_id = _make_lexicon_id(world_seed, content_id)
            world_name = _stub_world_name(template_id, world_seed)
            short_desc = _stub_short_description(domain, template_id)
            category = _STUB_CATEGORIES.get(domain, "uncategorized")

            entry = VocabularyEntry(
                content_id=content_id,
                lexicon_id=lexicon_id,
                domain=domain,
                world_name=world_name,
                category=category,
                aliases=(),
                subcategory=None,
                short_description=short_desc,
                article=None,
                plural_form=None,
                localization_hooks=LocalizationHooks(
                    semantic_root=f"{_STUB_SEMANTIC_PREFIX.get(domain, 'entry')}_{template_id.lower()}",
                    tone_register=_STUB_TONE.get(domain, "formal"),
                ),
                ip_clean=True,
                provenance=VocabularyProvenance(
                    source="world_compiler",
                    compiler_version=COMPILER_VERSION,
                    seed_used=world_seed,
                    content_pack_id=content_pack_id,
                    template_ids=(template_id,),
                    llm_output_hash=None,
                ),
            )
            entries.append(entry)

    return entries


def _build_stub_taxonomy(
    domains: List[str],
) -> WorldTaxonomy:
    """Build a minimal taxonomy for the stub mode."""
    categories: List[TaxonomyCategory] = []
    for domain in sorted(domains):
        cat_id = _STUB_CATEGORIES.get(domain, "uncategorized")
        display = cat_id.replace("_", " ").title()
        categories.append(
            TaxonomyCategory(
                category_id=cat_id,
                display_name=display,
                domain=domain,
            )
        )
    return WorldTaxonomy(categories=tuple(categories))


class LexiconStage(CompileStage):
    """Stage 1: Generate world-flavored names for all content pack IDs."""

    @property
    def stage_id(self) -> str:
        return "lexicon"

    @property
    def stage_number(self) -> int:
        return 1

    @property
    def depends_on(self) -> Tuple[str, ...]:
        return ()

    def execute(self, context: CompileContext) -> StageResult:
        """Run lexicon generation.

        1. Load template IDs from content pack
        2. Generate names (stub or LLM)
        3. Build VocabularyRegistry
        4. Write lexicon.json to workspace
        """
        try:
            return self._execute_inner(context)
        except Exception as exc:
            return StageResult(
                stage_id=self.stage_id,
                status="failed",
                output_files=(),
                error=str(exc),
            )

    def _execute_inner(self, context: CompileContext) -> StageResult:
        # 1. Load template IDs
        template_ids_by_domain = _load_template_ids(context.content_pack_dir)

        if not template_ids_by_domain:
            return StageResult(
                stage_id=self.stage_id,
                status="failed",
                output_files=(),
                error="No template IDs found in content pack.",
            )

        # 2. Determine mode: stub vs LLM
        llm_model_id = context.toolchain_pins.get("llm_model_id", "stub")
        use_stub = llm_model_id == "stub"

        if use_stub:
            entries = _build_stub_entries(
                template_ids_by_domain,
                context.world_seed,
                context.content_pack_id,
            )
        else:
            # LLM mode — not implemented in this WO.
            # When wired in, this branch would call the LLM adapter.
            entries = _build_stub_entries(
                template_ids_by_domain,
                context.world_seed,
                context.content_pack_id,
            )

        # 3. Build taxonomy
        domains = sorted(template_ids_by_domain.keys())
        taxonomy = _build_stub_taxonomy(domains)

        # 4. Compute world_id if not provided
        world_id = context.world_id
        if not world_id:
            world_id = hashlib.sha256(
                f"{context.world_seed}:{context.content_pack_id}".encode()
            ).hexdigest()[:32]

        # 5. Build VocabularyRegistry
        naming_style = context.world_theme_brief.get("naming_style", "")
        sorted_entries = tuple(sorted(entries, key=lambda e: e.content_id))

        registry = VocabularyRegistry(
            schema_version="1.0",
            world_id=world_id,
            locale=context.locale,
            entries=sorted_entries,
            naming_style=naming_style,
            entry_count=len(sorted_entries),
            taxonomy=taxonomy,
        )

        # 6. Serialize and write
        registry_dict = registry.to_dict()
        context.workspace_dir.mkdir(parents=True, exist_ok=True)
        output_path = context.workspace_dir / "lexicon.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(registry_dict, f, indent=2, sort_keys=False)

        return StageResult(
            stage_id=self.stage_id,
            status="success",
            output_files=("lexicon.json",),
        )

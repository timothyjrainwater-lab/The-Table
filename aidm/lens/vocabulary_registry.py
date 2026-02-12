"""Vocabulary Registry — read-only registry for world vocabulary entries.

Loads a vocabulary registry JSON file (produced by the World Compiler) and
provides lookup, search, and listing operations. Immutable after loading.

Lives in Lens because it's a context-providing component: it helps the
narration layer, discovery log, and search resolve world-flavored names.

BOUNDARY LAW (BL-003): No imports from aidm/core/.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from aidm.schemas.vocabulary import VocabularyEntry, VocabularyRegistry


class DuplicateContentIdError(ValueError):
    """Raised when a registry contains duplicate content_ids."""
    pass


class DuplicateLexiconIdError(ValueError):
    """Raised when a registry contains duplicate lexicon_ids."""
    pass


class VocabularyRegistryLoader:
    """Read-only registry of world vocabulary entries.

    Loads from a JSON file conforming to vocabulary_registry.schema.json.
    All entries are frozen VocabularyEntry dataclasses. The registry itself
    provides no mutation methods — it is read-only after construction.
    """

    def __init__(
        self,
        entries: List[VocabularyEntry],
        schema_version: str = "1.0",
        world_id: str = "",
        locale: str = "en",
    ):
        """Initialize registry from a list of VocabularyEntry objects.

        Args:
            entries: Vocabulary entries to register (will be sorted by content_id).
            schema_version: Schema version of the source registry file.
            world_id: World identity hash.
            locale: BCP-47 locale tag.

        Raises:
            DuplicateContentIdError: If any two entries share a content_id.
            DuplicateLexiconIdError: If any two entries share a lexicon_id.
        """
        # Validate no duplicate content_ids
        seen_content: Dict[str, int] = {}
        for i, entry in enumerate(entries):
            if entry.content_id in seen_content:
                raise DuplicateContentIdError(
                    f"Duplicate content_id '{entry.content_id}' "
                    f"at indices {seen_content[entry.content_id]} and {i}"
                )
            seen_content[entry.content_id] = i

        # Validate no duplicate lexicon_ids
        seen_lexicon: Dict[str, int] = {}
        for i, entry in enumerate(entries):
            if entry.lexicon_id in seen_lexicon:
                raise DuplicateLexiconIdError(
                    f"Duplicate lexicon_id '{entry.lexicon_id}' "
                    f"at indices {seen_lexicon[entry.lexicon_id]} and {i}"
                )
            seen_lexicon[entry.lexicon_id] = i

        # Store sorted by content_id (deterministic ordering)
        self._entries = tuple(sorted(entries, key=lambda e: e.content_id))
        self._content_index: Dict[str, VocabularyEntry] = {
            e.content_id: e for e in self._entries
        }
        self._name_index: Dict[str, str] = {
            e.world_name: e.content_id for e in self._entries
        }
        self._schema_version = schema_version
        self._world_id = world_id
        self._locale = locale

    @property
    def schema_version(self) -> str:
        """Schema version of the source registry file."""
        return self._schema_version

    @property
    def world_id(self) -> str:
        """World identity hash."""
        return self._world_id

    @property
    def locale(self) -> str:
        """BCP-47 locale tag."""
        return self._locale

    @property
    def entry_count(self) -> int:
        """Total number of entries."""
        return len(self._entries)

    def get_world_name(self, content_id: str) -> Optional[str]:
        """Look up the world-flavored name for a content ID.

        Args:
            content_id: Stable mechanical ID (e.g., 'spell.fireball').

        Returns:
            The world-flavored name, or None if not found.
        """
        entry = self._content_index.get(content_id)
        if entry is not None:
            return entry.world_name
        return None

    def get_entry(self, content_id: str) -> Optional[VocabularyEntry]:
        """Look up a full vocabulary entry by content_id.

        Args:
            content_id: Stable mechanical ID (e.g., 'spell.fireball').

        Returns:
            The matching VocabularyEntry, or None if not found.
        """
        return self._content_index.get(content_id)

    def search_by_name(self, query: str) -> List[VocabularyEntry]:
        """Find entries by world_name substring (case-insensitive).

        Args:
            query: Search string to match against world_name.

        Returns:
            List of matching entries, sorted by content_id.
        """
        q = query.lower()
        return [
            e for e in self._entries
            if q in e.world_name.lower()
        ]

    def list_by_category(self, category: str) -> List[VocabularyEntry]:
        """List all entries in a given category, sorted by world_name.

        Args:
            category: Category to filter by.

        Returns:
            List of entries in the category, sorted by world_name.
        """
        return sorted(
            [e for e in self._entries if e.category == category],
            key=lambda e: e.world_name,
        )

    def get_content_id(self, world_name: str) -> Optional[str]:
        """Reverse lookup: world name -> content ID.

        Args:
            world_name: Exact world-flavored display name.

        Returns:
            The content_id, or None if not found.
        """
        return self._name_index.get(world_name)

    def list_all(self) -> List[VocabularyEntry]:
        """List all entries, sorted by content_id.

        Returns:
            All entries in deterministic order.
        """
        return list(self._entries)

    @classmethod
    def from_registry(cls, registry: VocabularyRegistry) -> "VocabularyRegistryLoader":
        """Build from a parsed VocabularyRegistry dataclass.

        Args:
            registry: Parsed VocabularyRegistry instance.

        Returns:
            VocabularyRegistryLoader with indexed lookups.

        Raises:
            DuplicateContentIdError: If duplicate content_ids found.
            DuplicateLexiconIdError: If duplicate lexicon_ids found.
        """
        return cls(
            entries=list(registry.entries),
            schema_version=registry.schema_version,
            world_id=registry.world_id,
            locale=registry.locale,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VocabularyRegistryLoader":
        """Load registry from a parsed JSON dictionary.

        Args:
            data: Dictionary matching the VocabularyRegistry schema.

        Returns:
            Loaded VocabularyRegistryLoader instance.
        """
        registry = VocabularyRegistry.from_dict(data)
        return cls.from_registry(registry)

    @classmethod
    def from_json_file(cls, path: Path) -> "VocabularyRegistryLoader":
        """Load registry from a JSON file.

        Args:
            path: Path to the vocabulary_registry.json file.

        Returns:
            Loaded VocabularyRegistryLoader instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
            DuplicateContentIdError: If duplicate content_ids found.
            DuplicateLexiconIdError: If duplicate lexicon_ids found.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def empty(cls) -> "VocabularyRegistryLoader":
        """Create an empty registry (valid — world with no vocabulary yet)."""
        return cls(entries=[])

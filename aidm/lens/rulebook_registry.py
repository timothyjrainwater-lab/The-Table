"""Rulebook Registry — read-only registry for world-authored rule entries.

Loads a rule registry JSON file (produced by the World Compiler) and provides
lookup, search, and listing operations. Immutable after loading.

Lives in Lens because it's a context-providing component: it helps the
Crystal Ball, Notebook, and Spark answer player questions about abilities.

BOUNDARY LAW (BL-003): No imports from aidm/core/.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from aidm.schemas.rulebook import RuleEntry


class DuplicateContentIdError(ValueError):
    """Raised when a registry contains duplicate content_ids."""
    pass


class RulebookRegistry:
    """Read-only registry of world-authored rule entries.

    Loads from a JSON file conforming to rule_registry.schema.json.
    All entries are frozen RuleEntry dataclasses. The registry itself
    provides no mutation methods — it is read-only after construction.
    """

    def __init__(
        self,
        entries: List[RuleEntry],
        schema_version: str = "1.0",
        world_id: str = "",
        compiler_version: str = "",
    ):
        """Initialize registry from a list of RuleEntry objects.

        Args:
            entries: Rule entries to register (will be sorted by content_id).
            schema_version: Schema version of the source registry file.
            world_id: World identity hash.
            compiler_version: Compiler version that produced the registry.

        Raises:
            DuplicateContentIdError: If any two entries share a content_id.
        """
        # Validate no duplicates
        seen: Dict[str, int] = {}
        for i, entry in enumerate(entries):
            if entry.content_id in seen:
                raise DuplicateContentIdError(
                    f"Duplicate content_id '{entry.content_id}' "
                    f"at indices {seen[entry.content_id]} and {i}"
                )
            seen[entry.content_id] = i

        # Store sorted by content_id (deterministic ordering)
        self._entries = tuple(sorted(entries, key=lambda e: e.content_id))
        self._index: Dict[str, RuleEntry] = {e.content_id: e for e in self._entries}
        self._schema_version = schema_version
        self._world_id = world_id
        self._compiler_version = compiler_version

    @property
    def schema_version(self) -> str:
        """Schema version of the source registry file."""
        return self._schema_version

    @property
    def world_id(self) -> str:
        """World identity hash."""
        return self._world_id

    @property
    def compiler_version(self) -> str:
        """Compiler version that produced the registry."""
        return self._compiler_version

    @property
    def entry_count(self) -> int:
        """Total number of entries."""
        return len(self._entries)

    def get_entry(self, content_id: str) -> Optional[RuleEntry]:
        """Look up a rule entry by exact content_id.

        Args:
            content_id: Stable mechanical ID (e.g., 'spell.fire_burst_003').

        Returns:
            The matching RuleEntry, or None if not found.
        """
        return self._index.get(content_id)

    def search(self, query: str) -> List[RuleEntry]:
        """Simple substring search across world_name, category, and rule_text.

        Case-insensitive. No LLM involvement — Spark handles natural language
        queries by converting them to search terms first.

        Args:
            query: Search string to match against entry fields.

        Returns:
            List of matching entries, sorted by content_id.
        """
        q = query.lower()
        results = []
        for entry in self._entries:
            if (
                q in entry.world_name.lower()
                or q in entry.category.lower()
                or q in entry.rule_text.lower()
            ):
                results.append(entry)
        return results

    def list_by_category(self, category: str) -> List[RuleEntry]:
        """List all entries in a given category, sorted by world_name.

        Args:
            category: Category to filter by (matches rule_type).

        Returns:
            List of entries in the category, sorted by world_name.
        """
        return sorted(
            [e for e in self._entries if e.category == category],
            key=lambda e: e.world_name,
        )

    def list_all(self) -> List[RuleEntry]:
        """List all entries, sorted by content_id.

        Returns:
            All entries in deterministic order.
        """
        return list(self._entries)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RulebookRegistry":
        """Load registry from a parsed JSON dictionary.

        Args:
            data: Dictionary matching the RuleRegistry schema.

        Returns:
            Loaded RulebookRegistry instance.
        """
        entries = [RuleEntry.from_dict(e) for e in data.get("entries", [])]
        return cls(
            entries=entries,
            schema_version=data.get("schema_version", "1.0"),
            world_id=data.get("world_id", ""),
            compiler_version=data.get("compiler_version", ""),
        )

    @classmethod
    def from_json_file(cls, path: Path) -> "RulebookRegistry":
        """Load registry from a JSON file.

        Args:
            path: Path to the rule_registry.json file.

        Returns:
            Loaded RulebookRegistry instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
            DuplicateContentIdError: If duplicate content_ids are found.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def empty(cls) -> "RulebookRegistry":
        """Create an empty registry (valid — world with no rules yet)."""
        return cls(entries=[])

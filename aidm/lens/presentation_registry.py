"""AD-007: Presentation Semantics Registry Loader.

Loads a PresentationSemanticsRegistry from a JSON file (world bundle
output) and provides immutable lookups by content_id or event_category.

BOUNDARY LAW: Lens layer component. Receives frozen schemas from
aidm.schemas.presentation_semantics. Does not import from aidm.core.
"""

import json
from pathlib import Path
from typing import Dict, Optional

from aidm.schemas.presentation_semantics import (
    AbilityPresentationEntry,
    EventCategory,
    EventPresentationEntry,
    PresentationSemanticsRegistry,
)


class RegistryValidationError(Exception):
    """Raised when a registry file fails validation."""


class PresentationRegistryLoader:
    """Immutable registry for AD-007 presentation semantics lookups.

    After construction, provides O(1) lookup by content_id or
    event_category. No mutation methods. Validates integrity on load.
    """

    def __init__(self, registry: PresentationSemanticsRegistry) -> None:
        """Build lookup indices from a loaded registry.

        Args:
            registry: Parsed PresentationSemanticsRegistry instance.

        Raises:
            RegistryValidationError: If entry counts don't match or
                duplicate content_id / event_category detected.
        """
        # Validate ability_entry_count if provided
        if (
            registry.ability_entry_count is not None
            and registry.ability_entry_count != len(registry.ability_entries)
        ):
            raise RegistryValidationError(
                f"ability_entry_count mismatch: declared "
                f"{registry.ability_entry_count}, actual "
                f"{len(registry.ability_entries)}"
            )

        # Validate event_entry_count if provided
        if (
            registry.event_entry_count is not None
            and registry.event_entry_count != len(registry.event_entries)
        ):
            raise RegistryValidationError(
                f"event_entry_count mismatch: declared "
                f"{registry.event_entry_count}, actual "
                f"{len(registry.event_entries)}"
            )

        # Build ability lookup index — reject duplicates
        ability_index: Dict[str, AbilityPresentationEntry] = {}
        for entry in registry.ability_entries:
            if entry.content_id in ability_index:
                raise RegistryValidationError(
                    f"duplicate content_id: '{entry.content_id}'"
                )
            ability_index[entry.content_id] = entry

        # Build event lookup index — reject duplicates
        event_index: Dict[EventCategory, EventPresentationEntry] = {}
        for entry in registry.event_entries:
            if entry.event_category in event_index:
                raise RegistryValidationError(
                    f"duplicate event_category: "
                    f"'{entry.event_category.value}'"
                )
            event_index[entry.event_category] = entry

        # Store as private (no mutation methods exposed)
        self._registry = registry
        self._ability_index = ability_index
        self._event_index = event_index

    @property
    def registry(self) -> PresentationSemanticsRegistry:
        """The underlying registry (frozen dataclass)."""
        return self._registry

    def get_ability_semantics(
        self, content_id: str,
    ) -> Optional[AbilityPresentationEntry]:
        """Look up presentation semantics by ability content_id.

        Args:
            content_id: Content pack identifier (e.g., 'spell.fireball').

        Returns:
            AbilityPresentationEntry if found, None otherwise.
        """
        return self._ability_index.get(content_id)

    def get_event_semantics(
        self, event_category: EventCategory,
    ) -> Optional[EventPresentationEntry]:
        """Look up default presentation semantics by event category.

        Args:
            event_category: EventCategory enum value.

        Returns:
            EventPresentationEntry if found, None otherwise.
        """
        return self._event_index.get(event_category)

    @classmethod
    def from_json_file(cls, path: Path) -> "PresentationRegistryLoader":
        """Load a registry from a JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            PresentationRegistryLoader with indexed lookups.

        Raises:
            FileNotFoundError: If path doesn't exist.
            json.JSONDecodeError: If file is not valid JSON.
            RegistryValidationError: If validation fails.
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        registry = PresentationSemanticsRegistry.from_dict(data)
        return cls(registry)

    @classmethod
    def from_dict(cls, data: Dict) -> "PresentationRegistryLoader":
        """Load a registry from a dictionary.

        Args:
            data: Dictionary conforming to the JSON schema.

        Returns:
            PresentationRegistryLoader with indexed lookups.

        Raises:
            RegistryValidationError: If validation fails.
        """
        registry = PresentationSemanticsRegistry.from_dict(data)
        return cls(registry)

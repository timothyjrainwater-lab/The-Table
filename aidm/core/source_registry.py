"""Source registry for accessing D&D 3.5e source material.

Provides centralized access to provenance metadata and extracted text.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class SourceNotFoundError(Exception):
    """Raised when a sourceId is not found in the registry."""
    pass


class TextNotAvailableError(Exception):
    """Raised when extracted text is not available for a source."""
    pass


class PageNotFoundError(Exception):
    """Raised when a specific page is not found."""
    pass


class SourceRegistry:
    """Registry for D&D 3.5e source materials with provenance tracking."""

    def __init__(self, provenance_path: str = "sources/provenance.json"):
        """
        Initialize source registry from provenance file.

        Args:
            provenance_path: Path to provenance.json file

        Raises:
            FileNotFoundError: If provenance file doesn't exist
            ValueError: If provenance file is malformed
        """
        self.provenance_path = Path(provenance_path)

        if not self.provenance_path.exists():
            raise FileNotFoundError(f"Provenance file not found: {provenance_path}")

        with open(self.provenance_path, 'r', encoding='utf-8') as f:
            self.provenance = json.load(f)

        self.sources = self.provenance.get("sources", {})

        if not self.sources:
            raise ValueError("Provenance file contains no sources")

    def get_source(self, source_id: str) -> Dict[str, Any]:
        """
        Get source metadata by sourceId.

        Args:
            source_id: 12-character hex sourceId

        Returns:
            Source metadata dict

        Raises:
            SourceNotFoundError: If sourceId not found
        """
        if source_id not in self.sources:
            raise SourceNotFoundError(f"Source not found: {source_id}")

        return self.sources[source_id]

    def get_text_page(self, source_id: str, page_number: int) -> str:
        """
        Get extracted text for a specific page.

        Args:
            source_id: 12-character hex sourceId
            page_number: Page number (1-indexed)

        Returns:
            Page text content

        Raises:
            SourceNotFoundError: If sourceId not found
            TextNotAvailableError: If extracted text not available for this source
            PageNotFoundError: If specific page not found
            ValueError: If page_number is invalid
        """
        if page_number < 1:
            raise ValueError(f"Page number must be >= 1, got {page_number}")

        source = self.get_source(source_id)

        if not source.get("text_extracted"):
            raise TextNotAvailableError(
                f"No extracted text for source: {source['title']} ({source_id})"
            )

        text_path = source.get("text_path")
        if not text_path:
            raise TextNotAvailableError(
                f"Text path not set for source: {source['title']} ({source_id})"
            )

        # Page files are zero-padded 4-digit, 1-indexed (0001.txt, 0002.txt, ...)
        page_file = Path(text_path) / f"{page_number:04d}.txt"

        if not page_file.exists():
            raise PageNotFoundError(
                f"Page {page_number} not found for {source['title']} ({source_id}): {page_file}"
            )

        return page_file.read_text(encoding='utf-8')

    def list_sources_with_text(self) -> list[Dict[str, Any]]:
        """
        Get list of all sources with extracted text available.

        Returns:
            List of source metadata dicts
        """
        return [
            source for source in self.sources.values()
            if source.get("text_extracted")
        ]

    def list_core_sources(self) -> list[Dict[str, Any]]:
        """
        Get list of core rulebook sources (PHB, DMG, MM).

        Returns:
            List of source metadata dicts
        """
        return [
            source for source in self.sources.values()
            if "core" in source.get("tags", [])
        ]

    def get_source_by_short_name(self, short_name: str) -> Optional[Dict[str, Any]]:
        """
        Get source by short name (e.g., 'PHB', 'DMG', 'MM').

        Args:
            short_name: Short name identifier

        Returns:
            Source metadata dict or None if not found
        """
        for source in self.sources.values():
            if source.get("short_name") == short_name:
                return source
        return None

    def get_page_count(self, source_id: str) -> int:
        """
        Get total page count for a source.

        Args:
            source_id: 12-character hex sourceId

        Returns:
            Number of pages

        Raises:
            SourceNotFoundError: If sourceId not found
        """
        source = self.get_source(source_id)
        return source["pages"]

    def __len__(self) -> int:
        """Total number of sources in registry."""
        return len(self.sources)

    def __contains__(self, source_id: str) -> bool:
        """Check if sourceId exists in registry."""
        return source_id in self.sources

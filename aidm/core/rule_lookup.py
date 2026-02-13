"""Rule lookup with page-level retrieval from extracted source text.

Provides simple keyword-based search over D&D 3.5e rulebook pages.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from aidm.core.source_registry import SourceRegistry


@dataclass
class SearchHit:
    """A single search result from rule lookup."""

    source_id: str
    """12-character hex sourceId"""

    short_name: str
    """Human-readable short name (e.g., 'PHB', 'DMG', 'MM')"""

    page: int
    """Page number (1-indexed)"""

    snippet: str
    """Text snippet (≤ 300 chars)"""

    score: float
    """Relevance score (higher is better)"""


def search(
    query: str,
    source_ids: Optional[List[str]] = None,
    k: int = 5,
    registry: Optional[SourceRegistry] = None
) -> List[SearchHit]:
    """
    Search for rules across extracted rulebook pages.

    Args:
        query: Search query (case-insensitive)
        source_ids: List of sourceIds to search (None = core rulebooks)
        k: Maximum number of results to return
        registry: SourceRegistry instance (None = default)

    Returns:
        List of SearchHit results, sorted by relevance (descending)
    """
    if registry is None:
        registry = SourceRegistry("sources/provenance.json")

    # Default to core rulebooks if no sources specified
    if source_ids is None:
        core_sources = registry.list_core_sources()
        source_ids = [s["sourceId"] for s in core_sources]

    query_lower = query.lower()
    query_tokens = set(query_lower.split())

    hits = []

    for source_id in source_ids:
        source = registry.get_source(source_id)

        # Skip sources without extracted text
        if not source.get("text_extracted"):
            continue

        short_name = source.get("short_name", source_id[:8])
        page_count = source["pages"]

        # Search each page
        for page_num in range(1, page_count + 1):
            try:
                page_text = registry.get_text_page(source_id, page_num)
            except Exception:
                # Skip pages that can't be read
                continue

            page_lower = page_text.lower()

            # Simple scoring: count matching tokens
            score = 0
            for token in query_tokens:
                score += page_lower.count(token)

            # Skip pages with no matches
            if score == 0:
                continue

            # Extract snippet around first match
            snippet = _extract_snippet(page_text, query_lower, max_len=300)

            hits.append(SearchHit(
                source_id=source_id,
                short_name=short_name,
                page=page_num,
                snippet=snippet,
                score=float(score)
            ))

    # Sort by score (descending), then by source_id, page for determinism
    hits.sort(key=lambda h: (-h.score, h.source_id, h.page))

    return hits[:k]


def _extract_snippet(text: str, query: str, max_len: int = 300) -> str:
    """
    Extract snippet around first occurrence of query.

    Args:
        text: Full page text
        query: Search query (lowercase)
        max_len: Maximum snippet length

    Returns:
        Snippet trimmed to max_len characters
    """
    text_lower = text.lower()

    # Find first occurrence of any query token
    query_tokens = query.split()
    first_pos = len(text)

    for token in query_tokens:
        pos = text_lower.find(token)
        if pos != -1 and pos < first_pos:
            first_pos = pos

    # No match found (shouldn't happen if score > 0)
    if first_pos == len(text):
        return text[:max_len].strip()

    # Extract context around match
    start = max(0, first_pos - 100)
    end = min(len(text), first_pos + 200)

    snippet = text[start:end].strip()

    # Trim to max_len
    if len(snippet) > max_len:
        snippet = snippet[:max_len].strip()

    return snippet

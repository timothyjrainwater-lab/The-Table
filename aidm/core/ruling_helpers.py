"""Helper functions for creating ruling events with citations.

Demonstrates non-AI integration between rule lookup and event log.
"""

from typing import List, Dict, Any
from aidm.core.event_log import Event
from aidm.core.rule_lookup import SearchHit
from aidm.schemas.citation import build_citation


def make_rule_lookup_event(
    query: str,
    hits: List[SearchHit],
    event_id: int,
    timestamp: float,
    max_citations: int = 3
) -> Event:
    """
    Create an event from rule lookup results with citations.

    Args:
        query: Original search query
        hits: SearchHit results from rule_lookup.search()
        event_id: Monotonic event ID
        timestamp: Event timestamp
        max_citations: Maximum citations to attach (default 3)

    Returns:
        Event with type "rule_lookup" and citations populated
    """
    # Build payload with query and result summary
    payload = {
        "query": query,
        "results_count": len(hits),
        "top_sources": _summarize_sources(hits[:max_citations])
    }

    # Convert top hits to citations
    citations = [
        build_citation(hit).to_dict()
        for hit in hits[:max_citations]
    ]

    return Event(
        event_id=event_id,
        event_type="rule_lookup",
        timestamp=timestamp,
        payload=payload,
        citations=citations
    )


def _summarize_sources(hits: List[SearchHit]) -> List[Dict[str, Any]]:
    """
    Summarize search hits for event payload.

    Args:
        hits: SearchHit results

    Returns:
        List of dicts with source_id, short_name, page, score
    """
    return [
        {
            "source_id": hit.source_id,
            "short_name": hit.short_name,
            "page": hit.page,
            "score": hit.score
        }
        for hit in hits
    ]

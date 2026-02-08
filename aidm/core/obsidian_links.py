"""Obsidian URI helpers for optional UI integration.

Provides URI construction for Obsidian deep-linking WITHOUT requiring Obsidian
to be installed or present. These are purely string formatting utilities.
"""

from urllib.parse import quote


def build_obsidian_uri(vault_name: str, note_path: str) -> str:
    """
    Build an Obsidian URI for deep-linking to a note.

    Args:
        vault_name: Name of the Obsidian vault
        note_path: Path to note within vault (e.g., "Rulebooks/PHB/PHB_p0010.md")

    Returns:
        Obsidian URI string (obsidian://open?vault=...&file=...)

    Example:
        >>> build_obsidian_uri("DnD", "Rulebooks/PHB/PHB_p0010.md")
        'obsidian://open?vault=DnD&file=Rulebooks%2FPHB%2FPHB_p0010.md'
    """
    # URL-encode vault and file path
    vault_encoded = quote(vault_name)
    file_encoded = quote(note_path)

    return f"obsidian://open?vault={vault_encoded}&file={file_encoded}"


def build_rulebook_page_note_path(short_name: str, page: int) -> str:
    """
    Build conventional note path for a rulebook page.

    Uses convention: Rulebooks/{SHORT_NAME}/{SHORT_NAME}_p{PAGE:04d}.md

    Args:
        short_name: Short name like "PHB", "DMG", "MM"
        page: Page number (1-indexed)

    Returns:
        Note path string

    Example:
        >>> build_rulebook_page_note_path("PHB", 10)
        'Rulebooks/PHB/PHB_p0010.md'
    """
    page_padded = f"{page:04d}"
    return f"Rulebooks/{short_name}/{short_name}_p{page_padded}.md"

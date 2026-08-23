"""Helpers for robust Anthropic response extraction (handles thinking-enabled responses)."""

from __future__ import annotations


def text_content(resp) -> str:
    """Extract the text from an Anthropic messages response, skipping ThinkingBlock(s).

    With thinking enabled, resp.content = [ThinkingBlock, TextBlock]; with disabled, [TextBlock].
    Older code did resp.content[0].text which breaks on thinking. This grabs the text-type block.
    """
    for b in getattr(resp, "content", []):
        if getattr(b, "type", None) == "text" and hasattr(b, "text"):
            return b.text
    # fallback: first block with a .text attr
    for b in getattr(resp, "content", []):
        if hasattr(b, "text"):
            return b.text
    return ""

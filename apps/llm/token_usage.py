"""Token/cost placeholders for Milestone 1.

Gemini SDK response usage metadata can be wired here in Milestone 2 when agent_steps are persisted.
"""


def estimate_text_tokens(text: str | None) -> int:
    """Rough fallback estimate. Replace with provider usage metadata when available."""
    if not text:
        return 0
    return max(1, len(text) // 4)

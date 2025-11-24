"""Context windowing for token efficiency."""

from agentic_builder.core.constants import (
    MAX_CHARS_PER_DEPENDENCY,
    MAX_TOTAL_CONTEXT_CHARS,
    SUMMARY_TARGET_CHARS,
)


def estimate_tokens(text: str) -> int:
    """Estimate token count from text (roughly 4 chars per token).

    Args:
        text: Text to estimate

    Returns:
        Estimated token count
    """
    return len(text) // 4


def truncate_to_summary(text: str, target_chars: int = SUMMARY_TARGET_CHARS) -> str:
    """Truncate text to summary length.

    Attempts to cut at sentence boundaries for cleaner truncation.

    Args:
        text: Text to truncate
        target_chars: Target character count

    Returns:
        Truncated text
    """
    if len(text) <= target_chars:
        return text
    # Try to cut at sentence boundary
    truncated = text[:target_chars]
    last_period = truncated.rfind(".")
    if last_period > target_chars // 2:
        return truncated[: last_period + 1]
    return truncated + "..."


def apply_windowing(dependencies: list[dict]) -> list[dict]:
    """Apply windowing to dependency outputs for token efficiency.

    Truncates individual dependencies and ensures total context
    stays within budget.

    Args:
        dependencies: List of dependency dictionaries with 'output' field

    Returns:
        Windowed dependencies with truncated outputs
    """
    total_chars = 0
    windowed = []

    for dep in dependencies:
        output = dep.get("output", "")

        # Window individual dependency
        if len(output) > MAX_CHARS_PER_DEPENDENCY:
            output = truncate_to_summary(output, MAX_CHARS_PER_DEPENDENCY)

        # Check total budget
        if total_chars + len(output) > MAX_TOTAL_CONTEXT_CHARS:
            # Further truncate to fit
            remaining = MAX_TOTAL_CONTEXT_CHARS - total_chars
            if remaining > SUMMARY_TARGET_CHARS:
                output = truncate_to_summary(output, remaining)
            else:
                # Skip this dependency, budget exhausted
                continue

        windowed.append({**dep, "output": output})
        total_chars += len(output)

    return windowed

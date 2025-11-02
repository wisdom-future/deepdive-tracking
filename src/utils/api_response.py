"""Utilities for parsing and processing API responses."""


def strip_markdown_code_blocks(text: str) -> str:
    """Strip markdown code blocks from text.

    Handles formats like:
    - ```json\n{...}\n```
    - ```\n{...}\n```
    - ```python\n{...}\n```

    Args:
        text: Text potentially containing markdown code blocks

    Returns:
        Text with code blocks stripped
    """
    text = text.strip()
    if text.startswith("```"):
        # Remove opening ``` and optional language identifier (e.g., ```json)
        text = text[3:]
        if text.startswith("json"):
            text = text[4:]
        elif text.startswith("python"):
            text = text[6:]
        # Remove newline after opening marker
        text = text.lstrip()
        # Remove closing ```
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return text

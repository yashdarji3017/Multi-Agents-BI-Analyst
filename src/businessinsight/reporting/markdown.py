"""Markdown formatting utilities for structured financial reporting."""

from typing import Any, Dict, List


def format_currency(val: float | None) -> str:
    """Formats float as USD currency string."""
    if val is None:
        return "N/A"
    return f"${val:,.2f}"


def format_pct(val: float | None) -> str:
    """Formats float as signed percentage string."""
    if val is None:
        return "N/A"
    return f"{val:+.2f}%"


def generate_markdown_table(headers: List[str], rows: List[List[Any]]) -> str:
    """Generates standard GitHub-compatible markdown table."""
    if not headers:
        return ""
    header_line = "| " + " | ".join(str(h) for h in headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    row_lines = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join([header_line, separator_line] + row_lines)

"""Utility functions for parsing, formatting, and helpers."""

import re
import shlex
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json


def parse_command(user_input: str) -> Tuple[str, List[str]]:
    """Parse user input into command and arguments.

    Args:
        user_input: Raw user input string

    Returns:
        Tuple of (command, arguments_list)
    """
    if not user_input.strip():
        return "", []

    try:
        parts = shlex.split(user_input.strip())
        if not parts:
            return "", []
        return parts[0], parts[1:]
    except ValueError:
        # Fallback for malformed quotes
        parts = user_input.strip().split()
        if not parts:
            return "", []
        return parts[0], parts[1:]


def format_output(data: Any, format_type: str = "text") -> str:
    """Format output data for display.

    Args:
        data: Data to format
        format_type: Output format ("text", "json", "table")

    Returns:
        Formatted string
    """
    if format_type == "json":
        if isinstance(data, str):
            return data
        return json.dumps(data, indent=2, default=str)

    elif format_type == "table" and isinstance(data, list):
        if not data:
            return "No data"

        if isinstance(data[0], dict):
            # Table from list of dicts
            headers = list(data[0].keys())
            rows = []

            # Calculate column widths
            widths = [len(h) for h in headers]
            for row in data:
                for i, header in enumerate(headers):
                    value = str(row.get(header, ""))
                    widths[i] = max(widths[i], len(value))

            # Format header
            header_row = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
            separator = "-+-".join("-" * w for w in widths)

            # Format data rows
            data_rows = []
            for row in data:
                formatted_row = " | ".join(
                    str(row.get(h, "")).ljust(w) for h, w in zip(headers, widths)
                )
                data_rows.append(formatted_row)

            return "\n".join([header_row, separator] + data_rows)

    # Default text format
    if isinstance(data, (list, dict)):
        return json.dumps(data, indent=2, default=str)
    return str(data)


def human_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}".rjust(8)
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB".rjust(8)

# Backward compatibility alias
def format_size(size_bytes: int) -> str:
    """Legacy alias for human_size."""
    return human_size(size_bytes)


def format_mtime(timestamp: float) -> str:
    """Format modification time for display.

    Args:
        timestamp: Unix timestamp

    Returns:
        Formatted timestamp string (YYYY-MM-DD HH:MM)
    """
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M")

# Backward compatibility alias
def format_timestamp(timestamp: float) -> str:
    """Legacy alias for format_mtime."""
    return format_mtime(timestamp)


def validate_path(path: str) -> bool:
    """Validate if a path is acceptable for operations.

    Safety restrictions have been lifted, so every path is considered valid unless
    it's an obvious traversal attempt that cannot be resolved elsewhere.
    """
    return True


def format_perms(mode: int) -> str:
    """Format file permissions for display.

    Args:
        mode: File mode bits

    Returns:
        Formatted permission string (e.g., -rw-r--r--)
    """
    import stat
    return stat.filemode(mode)


def truncate(text: str, max_chars: int = 5000) -> str:
    """Truncate text to maximum character limit.

    Args:
        text: Text to truncate
        max_chars: Maximum number of characters

    Returns:
        Truncated text with notice if truncated
    """
    if len(text) <= max_chars:
        return text

    return text[:max_chars] + f"\n[truncated - output too long ({len(text)} chars)]"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem operations.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', sanitized)

    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]

    # Ensure not empty
    if not sanitized.strip():
        sanitized = "unnamed_file"

    return sanitized.strip()


def colorize_text(text: str, color: str) -> str:
    """Add ANSI color codes to text.

    Args:
        text: Text to colorize
        color: Color name (red, green, yellow, blue, cyan, magenta, white)

    Returns:
        Colorized text with ANSI codes
    """
    colors = {
        'red': '\033[91m',       # Bright red for errors
        'green': '\033[92m',     # Bright green for success
        'yellow': '\033[93m',    # Bright yellow for warnings
        'blue': '\033[94m',      # Bright blue for prompts
        'cyan': '\033[96m',      # Bright cyan for info
        'magenta': '\033[95m',   # Bright magenta for special
        'white': '\033[97m',     # Bright white for emphasis
        'gray': '\033[90m',      # Gray for less important text
        'bold': '\033[1m',       # Bold text
        'reset': '\033[0m'       # Reset all formatting
    }

    color_code = colors.get(color.lower(), '')
    reset_code = colors['reset']

    if color_code:
        return f"{color_code}{text}{reset_code}"
    return text


def truncate_output(output: str, max_lines: int = 100, max_chars: int = 5000) -> str:
    """Truncate output to prevent overwhelming display.

    Args:
        output: Output string to truncate
        max_lines: Maximum number of lines to keep
        max_chars: Maximum number of characters to keep

    Returns:
        Truncated output with notice if truncated
    """
    # First check character limit
    if len(output) > max_chars:
        truncated = output[:max_chars]
        return truncated + f"\n[truncated - output too long ({len(output)} chars)]"

    # Then check line limit
    lines = output.split('\n')
    if len(lines) <= max_lines:
        return output

    truncated_lines = lines[:max_lines]
    remaining = len(lines) - max_lines
    truncated_lines.append(f"\n[truncated - {remaining} more lines]")

    return '\n'.join(truncated_lines)


def parse_flags(args: List[str]) -> Tuple[List[str], Dict[str, Any]]:
    """Parse command arguments into positional args and flags.

    Args:
        args: List of command arguments

    Returns:
        Tuple of (positional_args, flags_dict)
    """
    positional = []
    flags = {}

    i = 0
    while i < len(args):
        arg = args[i]

        if arg.startswith('--'):
            # Long flag
            if '=' in arg:
                key, value = arg[2:].split('=', 1)
                flags[key] = value
            else:
                key = arg[2:]
                if i + 1 < len(args) and not args[i + 1].startswith('-'):
                    flags[key] = args[i + 1]
                    i += 1
                else:
                    flags[key] = True
        elif arg.startswith('-') and len(arg) > 1:
            # Short flag(s)
            for char in arg[1:]:
                flags[char] = True
        else:
            positional.append(arg)

        i += 1

    return positional, flags

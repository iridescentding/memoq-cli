# -*- coding: utf-8 -*-
"""
memoQ CLI - Output Helpers

Provides consistent formatting for CLI output.
"""

import json
import sys
from typing import Any, List, Dict, Optional, Callable

import click


def output_json(data: Any, indent: int = 2) -> None:
    """
    Output data as formatted JSON.

    Args:
        data: Data to output
        indent: JSON indentation level
    """
    click.echo(json.dumps(data, indent=indent, ensure_ascii=False, default=str))


def output_error(message: str, details: str = None) -> None:
    """
    Output error message to stderr.

    Args:
        message: Error message
        details: Optional details
    """
    click.echo(f"Error: {message}", err=True)
    if details:
        click.echo(f"  {details}", err=True)


def output_success(message: str) -> None:
    """Output success message."""
    click.echo(f"Done: {message}")


def output_info(message: str) -> None:
    """Output informational message."""
    click.echo(message)


def output_warning(message: str) -> None:
    """Output warning message."""
    click.echo(f"Warning: {message}", err=True)


def output_list(
    items: List[Dict],
    title: str = None,
    fields: List[tuple] = None,
    empty_message: str = "No items found"
) -> None:
    """
    Output a formatted list of items.

    Args:
        items: List of dictionaries to display
        title: Optional title
        fields: List of (key, label) tuples to display
        empty_message: Message when list is empty
    """
    if not items:
        click.echo(empty_message)
        return

    if title:
        click.echo(f"\n{title} ({len(items)}):\n")
        click.echo("=" * 70)

    for i, item in enumerate(items, 1):
        if fields:
            # Use specified fields
            first = True
            for key, label in fields:
                value = item.get(key, "N/A")
                if first:
                    click.echo(f"  {i}. {label}: {value}")
                    first = False
                else:
                    click.echo(f"     {label}: {value}")
        else:
            # Default: show all fields
            click.echo(f"  {i}. {item}")

        click.echo("-" * 70)


def output_detail(
    data: Dict,
    title: str = None,
    fields: List[tuple] = None
) -> None:
    """
    Output detailed information for a single item.

    Args:
        data: Dictionary with item data
        title: Optional title
        fields: List of (key, label) tuples to display
    """
    if title:
        click.echo(f"\n{title}:\n")

    if fields:
        for key, label in fields:
            value = data.get(key, "N/A")
            click.echo(f"  {label}: {value}")
    else:
        for key, value in data.items():
            click.echo(f"  {key}: {value}")


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Ask user for confirmation.

    Args:
        message: Confirmation message
        default: Default value if user just presses enter

    Returns:
        True if confirmed, False otherwise
    """
    return click.confirm(message, default=default)


def handle_api_error(error: Exception, verbose: bool = False) -> None:
    """
    Handle and display API errors consistently.

    Args:
        error: The exception that occurred
        verbose: Whether to show full traceback
    """
    output_error(str(error))

    if verbose:
        import traceback
        click.echo(traceback.format_exc(), err=True)

    sys.exit(1)


class OutputFormat:
    """Context manager for handling JSON vs pretty output."""

    def __init__(self, as_json: bool = False):
        self.as_json = as_json

    def output(
        self,
        data: Any,
        title: str = None,
        fields: List[tuple] = None,
        empty_message: str = "No items found"
    ) -> None:
        """
        Output data in the configured format.

        Args:
            data: Data to output
            title: Title for pretty output
            fields: Fields for pretty output
            empty_message: Message when data is empty
        """
        if self.as_json:
            output_json(data)
        elif isinstance(data, list):
            output_list(data, title=title, fields=fields, empty_message=empty_message)
        elif isinstance(data, dict):
            output_detail(data, title=title, fields=fields)
        else:
            click.echo(data)

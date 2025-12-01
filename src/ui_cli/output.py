"""Output formatters for table, JSON, and CSV formats."""

import csv
import io
import json
from enum import Enum
from typing import Any

from rich.console import Console
from rich.json import JSON
from rich.table import Table

console = Console()


class OutputFormat(str, Enum):
    """Available output formats."""

    TABLE = "table"
    JSON = "json"
    CSV = "csv"
    YAML = "yaml"


def flatten_dict(data: dict[str, Any], parent_key: str = "", sep: str = ".") -> dict[str, Any]:
    """Flatten nested dictionary for CSV output."""
    items: list[tuple[str, Any]] = []
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            items.append((new_key, json.dumps(value)))
        else:
            items.append((new_key, value))
    return dict(items)


def output_json(data: Any, verbose: bool = False) -> None:
    """Output data as formatted JSON."""
    if verbose:
        console.print(JSON(json.dumps(data, indent=2, default=str)))
    else:
        print(json.dumps(data, indent=2, default=str))


def get_nested_value(data: dict[str, Any], key: str) -> Any:
    """Get value from nested dict using dot notation key."""
    value = data
    for part in key.split("."):
        if isinstance(value, dict):
            value = value.get(part, "")
        else:
            return ""
    return value


def output_csv(
    data: list[dict[str, Any]],
    columns: list[tuple[str, str]] | None = None,
) -> None:
    """Output data as CSV.

    Args:
        data: List of dictionaries to output
        columns: Optional list of (key, header) tuples. If None, flattens all fields.
    """
    if not data:
        return

    output = io.StringIO()

    if columns:
        # Use specified columns with headers
        headers = [header for _, header in columns]
        writer = csv.writer(output)
        writer.writerow(headers)

        for item in data:
            row = []
            for key, _ in columns:
                value = get_nested_value(item, key)
                if value is None:
                    value = ""
                elif isinstance(value, bool):
                    value = "Yes" if value else "No"
                elif isinstance(value, (list, dict)):
                    value = json.dumps(value)
                else:
                    value = str(value)
                row.append(value)
            writer.writerow(row)
    else:
        # Flatten and output all fields
        flattened = [flatten_dict(item) for item in data]
        all_keys: set[str] = set()
        for item in flattened:
            all_keys.update(item.keys())
        fieldnames = sorted(all_keys)

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for item in flattened:
            writer.writerow(item)

    print(output.getvalue(), end="")


def output_table(
    data: list[dict[str, Any]],
    columns: list[tuple[str, str]],
    title: str | None = None,
) -> None:
    """Output data as a Rich table.

    Args:
        data: List of dictionaries to display
        columns: List of (key, header) tuples defining columns
        title: Optional table title
    """
    table = Table(title=title, show_header=True, header_style="bold cyan")

    # Add columns
    for _, header in columns:
        table.add_column(header)

    # Add rows
    for item in data:
        row = []
        for key, _ in columns:
            value = item
            # Handle nested keys like "meta.name"
            for part in key.split("."):
                if isinstance(value, dict):
                    value = value.get(part, "")
                else:
                    value = ""
                    break
            # Format value
            if value is None:
                value = ""
            elif isinstance(value, bool):
                value = "Yes" if value else "No"
            elif isinstance(value, (list, dict)):
                value = json.dumps(value)
            else:
                value = str(value)
            row.append(value)
        table.add_row(*row)

    console.print(table)


def output_single_table(
    data: dict[str, Any],
    title: str | None = None,
) -> None:
    """Output a single item as a key-value table."""
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    flat = flatten_dict(data)
    for key, value in flat.items():
        if value is None:
            value = ""
        elif isinstance(value, bool):
            value = "Yes" if value else "No"
        else:
            value = str(value)
        table.add_row(key, value)

    console.print(table)


def output_count_table(
    counts: dict[str, int],
    group_header: str = "Group",
    count_header: str = "Count",
    title: str | None = None,
) -> None:
    """Output count data as a table with totals."""
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column(group_header)
    table.add_column(count_header, justify="right")

    total = 0
    for group, count in sorted(counts.items()):
        table.add_row(group, str(count))
        total += count

    # Add separator and total
    table.add_row("─" * 20, "─" * 10, style="dim")
    table.add_row("Total", str(total), style="bold")

    console.print(table)


def render_output(
    data: Any,
    output_format: OutputFormat,
    columns: list[tuple[str, str]] | None = None,
    title: str | None = None,
    verbose: bool = False,
    is_single: bool = False,
) -> None:
    """Render data in the specified format.

    Args:
        data: Data to render (list or dict)
        output_format: Output format (table, json, csv)
        columns: Column definitions for table format [(key, header), ...]
        title: Title for table output
        verbose: Enable verbose output
        is_single: If True, render as single item detail view
    """
    if output_format == OutputFormat.JSON:
        output_json(data, verbose=verbose)
    elif output_format == OutputFormat.CSV:
        if isinstance(data, dict):
            data = [data]
        output_csv(data, columns=columns)
    else:  # TABLE
        if is_single and isinstance(data, dict):
            output_single_table(data, title=title)
        elif isinstance(data, list) and columns:
            output_table(data, columns=columns, title=title)
        elif isinstance(data, dict):
            output_single_table(data, title=title)
        else:
            console.print(data)


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]Error:[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]Warning:[/yellow] {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]{message}[/green]")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[cyan]{message}[/cyan]")

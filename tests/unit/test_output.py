"""Unit tests for output formatting utilities."""

import pytest

from ui_cli.output import OutputFormat


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_output_format_values(self):
        """Test that all expected output formats exist."""
        assert OutputFormat.TABLE.value == "table"
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.CSV.value == "csv"

    def test_output_format_from_string(self):
        """Test creating OutputFormat from string."""
        assert OutputFormat("table") == OutputFormat.TABLE
        assert OutputFormat("json") == OutputFormat.JSON
        assert OutputFormat("csv") == OutputFormat.CSV

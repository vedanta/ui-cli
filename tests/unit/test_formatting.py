"""Unit tests for formatting helper functions."""

import pytest

from ui_cli.commands.local.dpi import format_bytes as dpi_format_bytes, get_category_name, get_app_name
from ui_cli.commands.local.vouchers import format_duration, format_quota, format_code, is_voucher_expired
from ui_cli.commands.local.devices import get_device_type, get_device_status, get_uptime
from ui_cli.commands.local.stats import format_bytes as stats_format_bytes, format_timestamp


class TestBytesFormatting:
    """Tests for bytes formatting functions."""

    def test_format_bytes_zero(self):
        """Test formatting zero bytes."""
        assert dpi_format_bytes(0) == "0 B"
        assert stats_format_bytes(0) == "0 B"

    def test_format_bytes_none(self):
        """Test formatting None bytes."""
        assert dpi_format_bytes(None) == "0 B"
        assert stats_format_bytes(None) == "0 B"

    def test_format_bytes_small(self):
        """Test formatting small byte values."""
        assert dpi_format_bytes(500) == "500 B"

    def test_format_bytes_kilobytes(self):
        """Test formatting kilobytes."""
        result = dpi_format_bytes(1024)
        assert "KB" in result
        assert "1" in result

    def test_format_bytes_megabytes(self):
        """Test formatting megabytes."""
        result = dpi_format_bytes(1024 * 1024 * 5)
        assert "MB" in result

    def test_format_bytes_gigabytes(self):
        """Test formatting gigabytes."""
        result = dpi_format_bytes(1024 * 1024 * 1024 * 2.5)
        assert "GB" in result

    def test_format_bytes_terabytes(self):
        """Test formatting terabytes."""
        result = dpi_format_bytes(1024 * 1024 * 1024 * 1024 * 1.5)
        assert "TB" in result


class TestDPIFormatting:
    """Tests for DPI formatting functions."""

    def test_get_category_name_known(self):
        """Test getting known category names."""
        assert get_category_name(3) == "Streaming Media"
        assert get_category_name(15) == "Social Network"
        assert get_category_name(12) == "Web"

    def test_get_category_name_unknown(self):
        """Test getting unknown category names."""
        result = get_category_name(999)
        assert "Category 999" in result

    def test_get_app_name_known(self):
        """Test getting known app names."""
        assert get_app_name("youtube") == "YouTube"
        assert get_app_name("netflix") == "Netflix"
        assert get_app_name("SPOTIFY") == "Spotify"  # Case insensitive

    def test_get_app_name_partial_match(self):
        """Test getting app names with partial matches."""
        result = get_app_name("youtube_video")
        assert result == "YouTube"

    def test_get_app_name_unknown(self):
        """Test getting unknown app names."""
        result = get_app_name("some_random_app")
        assert result == "Some Random App"  # Title case


class TestVoucherFormatting:
    """Tests for voucher formatting functions."""

    def test_format_duration_minutes(self):
        """Test formatting duration in minutes."""
        assert format_duration(30) == "30m"
        assert format_duration(59) == "59m"

    def test_format_duration_hours(self):
        """Test formatting duration in hours."""
        assert format_duration(60) == "1h"
        assert format_duration(120) == "2h"
        assert format_duration(1439) == "23h"

    def test_format_duration_days(self):
        """Test formatting duration in days."""
        assert format_duration(1440) == "1d"
        assert format_duration(2880) == "2d"
        assert format_duration(10080) == "7d"

    def test_format_duration_none(self):
        """Test formatting None duration."""
        assert format_duration(None) == "-"

    def test_format_quota_unlimited(self):
        """Test formatting unlimited quota."""
        assert format_quota(0) == "No limit"
        assert format_quota(None) == "No limit"

    def test_format_quota_megabytes(self):
        """Test formatting quota in megabytes."""
        assert format_quota(500) == "500 MB"
        assert format_quota(1000) == "1000 MB"

    def test_format_quota_gigabytes(self):
        """Test formatting quota in gigabytes."""
        result = format_quota(1024)
        assert "GB" in result
        assert "1.0" in result

    def test_format_code_with_dash(self):
        """Test formatting code that already has dash."""
        assert format_code("12345-67890") == "12345-67890"

    def test_format_code_without_dash(self):
        """Test formatting code without dash."""
        assert format_code("1234567890") == "12345-67890"

    def test_format_code_none(self):
        """Test formatting None code."""
        assert format_code(None) == "-"

    def test_is_voucher_expired_not_expired(self):
        """Test voucher that is not expired."""
        import time
        voucher = {
            "create_time": int(time.time()),
            "duration": 1440,  # 24 hours
        }
        assert is_voucher_expired(voucher) is False

    def test_is_voucher_expired_expired(self):
        """Test voucher that is expired."""
        voucher = {
            "create_time": 1600000000,  # Old timestamp
            "duration": 60,  # 1 hour
        }
        assert is_voucher_expired(voucher) is True


class TestDeviceFormatting:
    """Tests for device formatting functions."""

    def test_get_device_type_known(self):
        """Test getting known device types."""
        assert get_device_type({"type": "uap"}) == "Access Point"
        assert get_device_type({"type": "usw"}) == "Switch"
        assert get_device_type({"type": "udm"}) == "Dream Machine"
        assert get_device_type({"type": "ugw"}) == "Gateway"

    def test_get_device_type_unknown(self):
        """Test getting unknown device type."""
        result = get_device_type({"type": "xyz"})
        assert result == "XYZ"

    def test_get_device_status_online(self):
        """Test device status for online devices."""
        status, style = get_device_status({"state": 1})
        assert status == "online"
        assert style == "green"

    def test_get_device_status_offline(self):
        """Test device status for offline devices."""
        status, style = get_device_status({"state": 0})
        assert status == "offline"
        assert style == "red"

    def test_get_device_status_pending(self):
        """Test device status for pending devices."""
        status, style = get_device_status({"state": 2})
        assert status == "pending"
        assert style == "yellow"

    def test_get_device_status_upgrading(self):
        """Test device status for upgrading devices."""
        status, style = get_device_status({"state": 4})
        assert status == "upgrading"
        assert style == "cyan"

    def test_get_uptime_none(self):
        """Test uptime formatting for no uptime."""
        assert get_uptime({"uptime": 0}) == "-"
        assert get_uptime({}) == "-"

    def test_get_uptime_minutes(self):
        """Test uptime formatting for minutes."""
        result = get_uptime({"uptime": 1800})  # 30 minutes
        assert "30m" in result

    def test_get_uptime_hours(self):
        """Test uptime formatting for hours."""
        result = get_uptime({"uptime": 7200})  # 2 hours
        assert "2h" in result

    def test_get_uptime_days(self):
        """Test uptime formatting for days."""
        result = get_uptime({"uptime": 172800})  # 2 days
        assert "2d" in result


class TestStatsFormatting:
    """Tests for stats formatting functions."""

    def test_format_timestamp_date_only(self):
        """Test formatting timestamp as date only."""
        # 1700000000 = 2023-11-14
        result = format_timestamp(1700000000000, include_time=False)
        assert "2023-11-14" in result

    def test_format_timestamp_with_time(self):
        """Test formatting timestamp with time."""
        result = format_timestamp(1700000000000, include_time=True)
        assert "2023-11-14" in result
        assert ":" in result  # Has time component

    def test_format_timestamp_none(self):
        """Test formatting None timestamp."""
        assert format_timestamp(None) == "-"

    def test_format_timestamp_milliseconds(self):
        """Test formatting timestamp in milliseconds."""
        # Should auto-convert from milliseconds
        result = format_timestamp(1700000000000)
        assert result != "-"

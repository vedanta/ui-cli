# Release Notes - v0.2.0

**Release Date:** December 1, 2024

## What's New

This release introduces **Local Controller API** support, allowing direct connection to your UniFi Controller (UDM, Cloud Key, or self-hosted) for real-time network management.

## Highlights

- **Direct Controller Access** - Connect directly to your UDM, Cloud Key, or self-hosted controller
- **Client Management** - List, block, unblock, and monitor network clients with detailed status
- **Device Control** - Restart, upgrade, locate, and adopt UniFi devices
- **Traffic Analytics** - DPI statistics and daily/hourly bandwidth reports
- **Guest Vouchers** - Create and manage hotspot vouchers
- **Config Export** - Backup your running configuration to YAML/JSON

## New Commands

### Local Controller (`./ui lo`)

| Command | Description |
|---------|-------------|
| `lo health` | Site health summary |
| `lo clients list/get/status/block/unblock/kick` | Client management |
| `lo devices list/get/restart/upgrade/locate/adopt` | Device control |
| `lo networks list` | View networks and VLANs |
| `lo firewall list/groups` | Inspect firewall rules |
| `lo portfwd list` | View port forwarding |
| `lo vouchers list/create/delete` | Guest voucher management |
| `lo dpi stats/client` | DPI traffic analysis |
| `lo stats daily/hourly` | Traffic statistics |
| `lo events list` | View recent events |
| `lo config show` | Export running config |

### Other

| Command | Description |
|---------|-------------|
| `speedtest` | Run speedtest via controller |
| `status` | Enhanced with local controller info |

## Configuration

Add these to your `.env` file for local controller access:

```bash
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword
UNIFI_CONTROLLER_SITE=default
UNIFI_CONTROLLER_VERIFY_SSL=false
```

## Breaking Changes

None. This release is fully backward compatible with v0.1.0.

## Upgrade Instructions

```bash
cd ui-cli
git pull origin main
pip install -e .
```

## Quality

- 87 tests (71 unit, 16 integration)
- All tests passing
- Supports UDM, UDM Pro, UDM SE, Cloud Key, and self-hosted controllers

## Full Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete details.

---

**Full Changelog**: https://github.com/vedanta/ui-cli/compare/v0.1.0...v0.2.0

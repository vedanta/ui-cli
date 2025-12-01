# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-12-01

### Added

#### Local Controller API (Milestone 2)
- **Health & Monitoring**
  - `./ui lo health` - Site health summary (WAN, LAN, WLAN, VPN status)
  - `./ui lo events list` - View recent events with filtering

- **Client Management**
  - `./ui lo clients list` - List connected clients with filters (wired/wireless/network)
  - `./ui lo clients all` - List all clients including offline
  - `./ui lo clients get` - Get client details by name or MAC
  - `./ui lo clients status` - Comprehensive client status (signal, experience, data usage)
  - `./ui lo clients block/unblock` - Block or unblock clients
  - `./ui lo clients kick` - Disconnect (reconnect) clients
  - `./ui lo clients count` - Count clients by type/network/vendor/AP
  - `./ui lo clients duplicates` - Find duplicate client names

- **Device Management**
  - `./ui lo devices list` - List network devices
  - `./ui lo devices get` - Get device details by ID/MAC/name
  - `./ui lo devices restart` - Restart a device
  - `./ui lo devices upgrade` - Upgrade device firmware
  - `./ui lo devices locate` - Toggle locate LED
  - `./ui lo devices adopt` - Adopt a new device

- **Network Configuration**
  - `./ui lo networks list` - List all networks/VLANs
  - `./ui lo config show` - Export running configuration (table/JSON/YAML)

- **Security & Firewall**
  - `./ui lo firewall list` - List firewall rules with ruleset filter
  - `./ui lo firewall groups` - List firewall groups (address/port)
  - `./ui lo portfwd list` - List port forwarding rules

- **Guest Management**
  - `./ui lo vouchers list` - List guest vouchers
  - `./ui lo vouchers create` - Create vouchers with duration/quota/limits
  - `./ui lo vouchers delete` - Delete vouchers

- **DPI & Statistics**
  - `./ui lo dpi stats` - Site-level DPI statistics
  - `./ui lo dpi client` - Per-client DPI breakdown
  - `./ui lo stats daily` - Daily traffic statistics
  - `./ui lo stats hourly` - Hourly traffic statistics

- **Other**
  - `./ui speedtest` - Run speedtest via controller
  - `./ui status` - Enhanced status with local controller info

### Added (Testing)
- Comprehensive pytest test suite (87 tests)
  - 71 unit tests
  - 16 integration tests
- Test fixtures for mock API responses
- pytest-asyncio for async test support

### Changed
- Updated documentation (README, USERGUIDE, ROADMAP)
- Added CONTRIBUTING.md and LICENSE

---

## [0.1.0] - 2024-11-29

### Added

#### Site Manager API (Milestone 1)
- **Authentication**
  - API key authentication via `UNIFI_API_KEY`
  - Connection status check (`./ui status`)

- **Hosts**
  - `./ui hosts list` - List all controllers
  - `./ui hosts get` - Get controller details

- **Sites**
  - `./ui sites list` - List all sites

- **Devices**
  - `./ui devices list` - List all devices with host filter
  - `./ui devices count` - Count devices by model/status/host/product-line

- **ISP Metrics**
  - `./ui isp metrics` - ISP performance metrics with interval options

- **SD-WAN**
  - `./ui sdwan list` - List SD-WAN configurations
  - `./ui sdwan get` - Get configuration details
  - `./ui sdwan status` - Get deployment status

- **Output Formats**
  - Table (default), JSON, CSV output for all commands
  - Verbose mode for additional details

### Infrastructure
- Typer CLI framework
- Rich terminal formatting
- httpx async HTTP client
- pydantic-settings configuration

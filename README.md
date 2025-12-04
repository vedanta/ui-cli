# UniFi CLI

<p align="center">
  <img src="art/uicli_new.png" alt="UI-CLI" width="400">
</p>

<p align="center">
  <strong>Manage your UniFi infrastructure from the command line</strong>
</p>

<p align="center">
  <a href="https://vedanta.github.io/ui-cli">Documentation</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="CHANGELOG.md">Changelog</a>
</p>

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Cloud API Commands](#cloud-api-commands)
- [Local Controller Commands](#local-controller-commands)
- [Client Groups](#client-groups)
- [Claude Desktop Integration](#claude-desktop-integration)
- [Output Formats](#output-formats)
- [Command Reference](#command-reference)
- [Data Storage](#data-storage)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

---

## Overview

UI-CLI is a comprehensive command-line tool for managing UniFi network infrastructure. It provides two connection modes to cover all management scenarios:

| Mode | Connection | Use Cases |
|------|------------|-----------|
| **Cloud API** | Via `api.ui.com` | Multi-site management, ISP metrics, SD-WAN, remote access |
| **Local API** | Direct to controller | Real-time client control, device management, bulk actions |

### Features

**Cloud API (Site Manager)**
- View and manage multiple sites and controllers from anywhere
- List all devices across your infrastructure with filtering
- Monitor ISP performance metrics (latency, speeds, uptime, packet loss)
- Manage SD-WAN configurations and deployment status
- Count and group devices by model, status, or controller

**Local Controller API**
- **Client Management** - List connected clients, filter by wired/wireless/network, view detailed status including signal strength and WiFi experience, block/unblock/reconnect clients
- **Client Groups** - Create named groups of devices for bulk actions (e.g., "Kids Devices", "Smart Bulbs"), supports static groups with manual membership and auto groups with pattern-based rules (vendor, hostname, network, IP range)
- **Device Control** - List all network devices, restart or upgrade firmware, toggle locate LED for physical identification, adopt new devices
- **Network Visibility** - View all networks and VLANs with DHCP configuration, monitor site health (WAN/LAN/WLAN/VPN status), browse recent events and alerts
- **Security & Firewall** - Inspect firewall rules by ruleset, view address and port groups, list port forwarding rules
- **Traffic Analytics** - Deep packet inspection (DPI) statistics by application, per-client traffic breakdown, daily and hourly bandwidth reports
- **Guest Management** - Create hotspot vouchers with custom duration, data limits, and speed caps, list and delete existing vouchers
- **Configuration Export** - Export running config to YAML/JSON for backup, filter by section (networks, wireless, firewall, devices)

**Claude Desktop Integration (MCP)**
- Natural language control of your network via Claude Desktop
- 21 tools covering status, health, client management, device control, groups, and vouchers
- Ask questions like "How many devices are connected?" or "Block the kids iPad"
- Group actions like "Block all kids devices" or "Show status of smart bulbs"

**General**
- Multiple output formats: table (human-readable), JSON (scripting), CSV (spreadsheets), YAML (config)
- Works with UDM, UDM Pro, UDM SE, Cloud Key, and self-hosted controllers
- Automatic controller type detection (UDM vs Cloud Key API paths)
- Session management with automatic re-authentication
- SSL verification bypass for self-signed certificates
- CI/CD friendly with automatic spinner disable

---

## Installation

### Prerequisites

- Python 3.10+
- Conda (recommended) or pip
- Network access to your UniFi controller

### Using Conda (Recommended)

```bash
# Clone the repository
git clone https://github.com/vedanta/ui-cli.git
cd ui-cli

# Create and activate conda environment
conda env create -f environment.yml
conda activate ui-cli

# Install the package
pip install -e .
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/vedanta/ui-cli.git
cd ui-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

### Using Docker

```bash
# Build the image
docker build -t ui-cli .

# Run with environment variables
docker run --rm -e UNIFI_API_KEY=your-key ui-cli status

# Run with .env file
docker run --rm --env-file .env ui-cli hosts list

# Run local controller commands
docker run --rm --env-file .env ui-cli lo clients list

# Interactive mode
docker run -it --rm --env-file .env ui-cli --help
```

**Docker Compose:**

```bash
# Run commands via docker-compose
docker-compose run --rm ui-cli status
docker-compose run --rm ui-cli lo clients list
```

### Verify Installation

```bash
./ui --help          # Using wrapper script
ui --help            # After pip install (if in PATH)
```

---

## Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

### Cloud API Configuration

For commands that use the UniFi Site Manager API (`api.ui.com`):

```bash
# Required: Your API key
UNIFI_API_KEY=your-api-key-here

# Optional: API base URL (default: https://api.ui.com/v1)
UNIFI_API_URL=https://api.ui.com/v1

# Optional: Request timeout in seconds (default: 30)
UNIFI_TIMEOUT=30
```

**Getting Your API Key:**
1. Go to [unifi.ui.com](https://unifi.ui.com)
2. Navigate to **Settings** → **API**
3. Click **Create API Key**
4. Copy the key immediately (it's only shown once!)

### Local Controller Configuration

For commands that connect directly to your UniFi Controller:

```bash
# Required: Controller URL (include https://)
UNIFI_CONTROLLER_URL=https://192.168.1.1

# Required: Credentials
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword

# Optional: Site name (default: "default")
UNIFI_CONTROLLER_SITE=default

# Optional: SSL verification (default: false for self-signed certs)
UNIFI_CONTROLLER_VERIFY_SSL=false
```

### Full Configuration Example

```bash
# ===========================================
# Cloud API (api.ui.com)
# ===========================================
UNIFI_API_KEY=your-api-key-here
UNIFI_API_URL=https://api.ui.com/v1
UNIFI_TIMEOUT=30

# ===========================================
# Local Controller
# ===========================================
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword
UNIFI_CONTROLLER_SITE=default
UNIFI_CONTROLLER_VERIFY_SSL=false
```

### Controller Types

UI-CLI automatically detects your controller type and uses the correct API paths:

| Controller | API Path |
|------------|----------|
| UDM / UDM Pro / UDM SE | `/proxy/network/api/s/{site}/` |
| Cloud Key / Self-hosted | `/api/s/{site}/` |

### Multiple Sites

To work with different sites on the same controller:

```bash
# Option 1: Edit .env
UNIFI_CONTROLLER_SITE=office

# Option 2: Use different .env files
cp .env .env.home
cp .env .env.office
# Edit each file with different site names
```

---

## Quick Start

### 1. Configure Credentials

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 2. Verify Connections

```bash
# Check Cloud API connection
./ui status

# Check Local Controller connection
./ui lo health
```

### 3. Explore Commands

```bash
# List all commands
./ui --help

# List connected clients
./ui lo clients list

# List network devices
./ui lo devices list

# Get client count by type
./ui lo clients count
```

---

## Cloud API Commands

Commands that use the UniFi Site Manager API (`api.ui.com`). Requires `UNIFI_API_KEY`.

### Status & Version

```bash
./ui status                     # Check API connection status
./ui version                    # Show CLI version
```

### Hosts (Controllers)

```bash
./ui hosts list                 # List all controllers
./ui hosts list -o json         # JSON output
./ui hosts get HOST_ID          # Get controller details
```

### Sites

```bash
./ui sites list                 # List all sites across controllers
./ui sites list -o json         # JSON output
./ui sites list -v              # Verbose with device counts
```

### Devices (Cloud)

```bash
# List devices
./ui devices list               # List all devices across sites
./ui devices list --host ID     # Filter by controller
./ui devices list -v            # Verbose with details
./ui devices list -o json       # JSON output

# Count devices
./ui devices count              # Total count
./ui devices count --by model   # Group by device model
./ui devices count --by status  # Find online/offline counts
./ui devices count --by host    # Group by controller
```

### ISP Metrics

Monitor ISP performance over time:

```bash
# Default: Last 7 days with hourly data
./ui isp metrics

# Custom time range
./ui isp metrics --hours 24     # Last 24 hours
./ui isp metrics --hours 48     # Last 48 hours

# Higher resolution (5-minute intervals, max 24h)
./ui isp metrics -i 5m
./ui isp metrics -i 5m --hours 12

# Output formats
./ui isp metrics -o json        # JSON for scripting
./ui isp metrics -o csv         # CSV for spreadsheets
```

Metrics include:
- Download/upload speeds
- Latency (min, max, average)
- Packet loss
- Uptime percentage

### SD-WAN

```bash
./ui sdwan list                 # List SD-WAN configurations
./ui sdwan get CONFIG_ID        # Get configuration details
./ui sdwan status CONFIG_ID     # Check deployment status
```

### Speed Test

```bash
./ui speedtest                  # Get last speed test result
./ui speedtest -r               # Run new speed test (takes 30-60s)
./ui speedtest -o json          # JSON output
```

---

## Local Controller Commands

Commands that connect directly to your UniFi Controller. Use `./ui local` or the shorthand `./ui lo`.

Requires `UNIFI_CONTROLLER_URL`, `UNIFI_CONTROLLER_USERNAME`, and `UNIFI_CONTROLLER_PASSWORD`.

### Timeout Options

```bash
./ui lo health                  # Default timeout (15s)
./ui lo -q health               # Quick mode (5s timeout)
./ui lo --timeout 60 health     # Custom timeout (60s)
```

### Health & Monitoring

```bash
# Site health summary
./ui lo health                  # Shows WAN, LAN, WLAN, VPN status
./ui lo health -v               # Verbose with details
./ui lo health -o json          # JSON output

# Events
./ui lo events list             # Recent events (default: 25)
./ui lo events list -l 50       # Last 50 events
./ui lo events list -l 100      # Last 100 events
./ui lo events list -v          # Verbose with full details
./ui lo events list -o json     # JSON output
```

### Clients

```bash
# List clients
./ui lo clients list            # Connected clients only
./ui lo clients list -w         # Wired clients only
./ui lo clients list -W         # Wireless clients only
./ui lo clients list -n Guest   # Filter by network/SSID
./ui lo clients list -g kids    # Filter by group
./ui lo clients list -v         # Verbose (signal, experience)
./ui lo clients list -o json    # JSON output

# All clients (including offline/historical)
./ui lo clients all
./ui lo clients all -o json

# Get specific client
./ui lo clients get my-iPhone          # By display name
./ui lo clients get AA:BB:CC:DD:EE:FF  # By MAC address
./ui lo clients get 192.168.1.100      # By IP address
./ui lo clients get iPhone             # Partial name match

# Detailed client status
./ui lo clients status my-iPhone       # Full status with signal, experience
./ui lo clients status -o json

# Client actions
./ui lo clients block my-iPhone        # Block (with confirmation)
./ui lo clients block my-iPhone -y     # Block (skip confirmation)
./ui lo clients unblock my-iPhone      # Unblock client
./ui lo clients kick my-iPhone         # Disconnect (can reconnect)

# Bulk actions with groups
./ui lo clients block -g kids-devices -y    # Block all in group
./ui lo clients unblock -g kids-devices -y  # Unblock all in group
./ui lo clients kick -g kids-devices -y     # Kick all in group

# Statistics
./ui lo clients count                  # Count by connection type
./ui lo clients count --by network     # Count by network/SSID
./ui lo clients count --by vendor      # Count by manufacturer
./ui lo clients count --by ap          # Count by access point
./ui lo clients count --by experience  # Count by WiFi quality
./ui lo clients count -a               # Include offline clients
./ui lo clients count -o json          # JSON output

# Find duplicates
./ui lo clients duplicates             # Find duplicate hostnames/names
```

### Devices

```bash
# List devices
./ui lo devices list            # All network devices (APs, switches, gateway)
./ui lo devices list -v         # Verbose (channels, load, temperatures)
./ui lo devices list -o json    # JSON output

# Get specific device
./ui lo devices get UDM-Pro            # By name
./ui lo devices get 70:a7:41:xx:xx:xx  # By MAC address
./ui lo devices get 192.168.1.1        # By IP address

# Device actions
./ui lo devices restart UDM-Pro        # Restart (with confirmation)
./ui lo devices restart UDM-Pro -y     # Restart (skip confirmation)
./ui lo devices upgrade Office-AP      # Upgrade firmware
./ui lo devices upgrade Office-AP -y   # Upgrade (skip confirmation)

# Locate LED
./ui lo devices locate Office-AP       # Turn on locate LED
./ui lo devices locate Office-AP --off # Turn off locate LED

# Adopt new device
./ui lo devices adopt 70:a7:41:xx:xx:xx
```

### Networks

```bash
./ui lo networks list           # List all networks/VLANs
./ui lo networks list -v        # Verbose (DHCP ranges, settings)
./ui lo networks list -o json   # JSON output
./ui lo networks get NETWORK_ID # Get specific network details
```

### Firewall

```bash
# Firewall rules
./ui lo firewall list                  # All firewall rules
./ui lo firewall list --ruleset WAN_IN # Filter by ruleset
./ui lo firewall list --ruleset LAN_IN
./ui lo firewall list --ruleset WAN_OUT
./ui lo firewall list -v               # Verbose with full details
./ui lo firewall list -o json          # JSON output

# Address and port groups
./ui lo firewall groups                # List all groups
./ui lo firewall groups -v             # Show group members
./ui lo firewall groups -o json        # JSON output
```

### Port Forwarding

```bash
./ui lo portfwd list            # List port forwarding rules
./ui lo portfwd list -v         # Verbose with full details
./ui lo portfwd list -o json    # JSON output
```

### Guest Vouchers

```bash
# List vouchers
./ui lo vouchers list           # All vouchers
./ui lo vouchers list -v        # Verbose with usage details
./ui lo vouchers list -o json   # JSON output

# Create vouchers
./ui lo vouchers create                # Single voucher, 24h duration
./ui lo vouchers create -c 10          # Create 10 vouchers
./ui lo vouchers create -d 60          # 60 minute duration
./ui lo vouchers create -d 1440        # 24 hour duration (in minutes)
./ui lo vouchers create -q 1024        # 1GB data quota (in MB)
./ui lo vouchers create --up 5000      # 5 Mbps upload limit (in kbps)
./ui lo vouchers create --down 10000   # 10 Mbps download limit (in kbps)
./ui lo vouchers create -n "Event"     # Add note

# Full example: 10 vouchers, 2 hours, 500MB quota, speed limits
./ui lo vouchers create -c 10 -d 120 -q 500 --up 5000 --down 10000 -n "Conference"

# Delete voucher
./ui lo vouchers delete 12345-67890
./ui lo vouchers delete 12345-67890 -y  # Skip confirmation
```

### DPI (Deep Packet Inspection)

Requires DPI to be enabled in controller settings.

```bash
# Site-wide DPI statistics
./ui lo dpi stats               # Top applications by traffic
./ui lo dpi stats -l 20         # Top 20 applications
./ui lo dpi stats -v            # Verbose with categories
./ui lo dpi stats -o json       # JSON output

# Per-client DPI
./ui lo dpi client my-MacBook          # By name
./ui lo dpi client AA:BB:CC:DD:EE:FF   # By MAC
./ui lo dpi client -o json
```

### Traffic Statistics

```bash
# Daily statistics
./ui lo stats daily             # Last 30 days
./ui lo stats daily --days 7    # Last 7 days
./ui lo stats daily --days 90   # Last 90 days
./ui lo stats daily -o json     # JSON output
./ui lo stats daily -o csv      # CSV for spreadsheets

# Hourly statistics
./ui lo stats hourly            # Last 24 hours
./ui lo stats hourly --hours 48 # Last 48 hours
./ui lo stats hourly -o json    # JSON output
```

### Configuration Export

Export your running configuration for backup or documentation:

```bash
# Full configuration
./ui lo config show             # All sections (table format)
./ui lo config show -o yaml     # YAML export
./ui lo config show -o json     # JSON export
./ui lo config show -v          # Include internal IDs
./ui lo config show --show-secrets  # Include passwords (careful!)

# Specific sections
./ui lo config show -s networks     # Networks and VLANs
./ui lo config show -s wireless     # SSIDs and WiFi settings
./ui lo config show -s firewall     # Firewall rules
./ui lo config show -s devices      # Device inventory
./ui lo config show -s portfwd      # Port forwarding rules
./ui lo config show -s dhcp         # DHCP reservations
./ui lo config show -s routing      # Static routes

# Save to file
./ui lo config show -o yaml > backup-$(date +%Y%m%d).yaml
./ui lo config show -o json > backup-$(date +%Y%m%d).json
```

---

## Client Groups

Create named groups of client devices for bulk actions. Groups are stored locally and work without network access.

### Use Cases

- **Parental Controls** - Block kids' devices at bedtime
- **IoT Management** - Group smart home devices by type
- **Guest Monitoring** - Track devices on guest network
- **Network Segmentation** - Manage servers, workstations, etc.

### Static Groups

Static groups have manually managed membership using MAC addresses.

```bash
# Create a group
./ui groups create "Kids Devices"
./ui groups create "Kids Devices" -d "Tablets and phones for the kids"

# Add members (with optional alias)
./ui groups add kids-devices AA:BB:CC:DD:EE:FF
./ui groups add kids-devices AA:BB:CC:DD:EE:FF -a "Timmy iPad"
./ui groups add kids-devices 11:22:33:44:55:66 -a "Sarah Phone"
./ui groups add kids-devices 22:33:44:55:66:77 -a "Gaming Console"

# Add multiple at once
./ui groups add kids-devices MAC1 MAC2 MAC3

# View group
./ui groups show kids-devices
./ui groups show kids-devices -o json

# List members
./ui groups members kids-devices
./ui groups members kids-devices -o json

# Update member alias
./ui groups alias kids-devices AA:BB:CC:DD:EE:FF "New Alias"
./ui groups alias kids-devices AA:BB:CC:DD:EE:FF --clear

# Remove members
./ui groups remove kids-devices AA:BB:CC:DD:EE:FF
./ui groups remove kids-devices "Timmy iPad"  # By alias

# Clear all members
./ui groups clear kids-devices
./ui groups clear kids-devices -y  # Skip confirmation
```

### Auto Groups

Auto groups dynamically match clients based on rules. Members are evaluated at query time.

```bash
# Basic syntax
./ui groups auto "Group Name" --rule-type "pattern"

# Match by vendor/manufacturer (OUI)
./ui groups auto "Apple Devices" --vendor "Apple"
./ui groups auto "IoT Devices" --vendor "Philips,LIFX,Ring,Nest"
./ui groups auto "Smart TVs" --vendor "Samsung,LG,Sony"

# Match by client name pattern
./ui groups auto "Cameras" --name "*camera*"
./ui groups auto "Phones" --name "*phone*,*Phone*"
./ui groups auto "Laptops" --name "*MacBook*,*laptop*"

# Match by hostname
./ui groups auto "iPhones" --hostname "iPhone*"
./ui groups auto "Android" --hostname "*android*"

# Match by network/SSID
./ui groups auto "Guest Devices" --network "Guest"
./ui groups auto "IoT Network" --network "IoT,Smart Home"

# Match by IP address or range
./ui groups auto "Servers" --ip "192.168.1.100-200"
./ui groups auto "VLAN10" --ip "10.0.10.0/24"
./ui groups auto "Printers" --ip "192.168.1.50,192.168.1.51"

# Match by MAC prefix
./ui groups auto "Ubiquiti" --mac "70:A7:41:*"

# Match by connection type
./ui groups auto "Wireless" --type "wireless"
./ui groups auto "Wired" --type "wired"

# Combine rules (AND logic between different types)
./ui groups auto "Kids iPhones" --vendor "Apple" --name "*kid*"
./ui groups auto "Wireless IoT" --vendor "Philips,LIFX" --type "wireless"

# Preview without creating
./ui groups auto "Test" --vendor "Apple" --dry-run

# With description
./ui groups auto "Apple Devices" --vendor "Apple" -d "All Apple products"
```

#### Pattern Syntax

| Format | Example | Matches |
|--------|---------|---------|
| Exact | `Apple` | "Apple" only |
| Wildcard | `*phone*` | "iPhone", "Android Phone" |
| Prefix | `iPhone*` | "iPhone", "iPhone-12" |
| Suffix | `*-TV` | "Living-TV", "Bedroom-TV" |
| Regex | `~^iPhone-[0-9]+$` | "iPhone-1", "iPhone-12" |
| Multiple (OR) | `Apple,Samsung` | "Apple" or "Samsung" |

### Managing Groups

```bash
# List all groups
./ui groups list
./ui groups ls                  # Alias
./ui groups list -o json

# Edit group
./ui groups edit kids-devices -n "Children Devices"  # Rename
./ui groups edit kids-devices -d "New description"   # Update description

# Delete group
./ui groups delete kids-devices
./ui groups delete kids-devices -y  # Skip confirmation
./ui groups rm kids-devices         # Alias
```

### Bulk Actions with Groups

```bash
# List clients in a group
./ui lo clients list -g kids-devices
./ui lo clients list -g apple-devices -o json

# Block all clients in a group
./ui lo clients block -g kids-devices      # With confirmation
./ui lo clients block -g kids-devices -y   # Skip confirmation
# Output: Blocked 3 clients (already blocked: 1, failed: 0)

# Unblock all clients in a group
./ui lo clients unblock -g kids-devices
./ui lo clients unblock -g kids-devices -y
# Output: Unblocked 3 clients (not blocked: 1, failed: 0)

# Kick all clients in a group
./ui lo clients kick -g kids-devices
./ui lo clients kick -g kids-devices -y
# Output: Kicked 3 clients (offline: 1, failed: 0)
```

### Import/Export

```bash
# Export all groups to JSON
./ui groups export
./ui groups export -o groups-backup.json

# Import groups from file
./ui groups import groups-backup.json
./ui groups import groups-backup.json --replace  # Replace all existing
./ui groups import groups-backup.json -y         # Skip confirmation
```

### Example: Parental Controls

```bash
# Initial setup (one time)
./ui groups create "Kids Devices" -d "Tablets and phones for the kids"
./ui groups add kids-devices AA:BB:CC:DD:EE:FF -a "Timmy iPad"
./ui groups add kids-devices 11:22:33:44:55:66 -a "Sarah Phone"
./ui groups add kids-devices 22:33:44:55:66:77 -a "Gaming Console"

# Bedtime - block all kids devices
./ui lo clients block -g kids-devices -y

# Morning - unblock all
./ui lo clients unblock -g kids-devices -y

# Check status
./ui lo clients list -g kids-devices
```

---

## Claude Desktop Integration

Control your UniFi network using natural language through [Claude Desktop](https://claude.ai/download).

### Setup

```bash
# Install MCP server to Claude Desktop
./ui mcp install

# Verify installation
./ui mcp check

# View current configuration
./ui mcp show

# Restart Claude Desktop to activate
```

### MCP Commands

```bash
./ui mcp install    # Add to Claude Desktop config
./ui mcp check      # Verify setup and connectivity
./ui mcp show       # View current configuration
./ui mcp remove     # Remove from Claude Desktop
```

### Example Prompts

| You say... | Claude does... |
|------------|----------------|
| "How many devices are on my network?" | Counts clients by type |
| "What's my network health?" | Shows WAN/LAN/WLAN/VPN status |
| "What's my internet speed?" | Shows last speed test result |
| "Run a speed test" | Initiates new speed test |
| "Find my iPhone" | Searches for client by name |
| "Is the TV online?" | Checks client status |
| "Block the kids iPad" | Blocks specific client |
| "Unblock the kids iPad" | Unblocks client |
| "Block all kids devices" | Blocks entire group |
| "Restart the garage AP" | Restarts device |
| "Create a guest WiFi voucher" | Creates voucher |
| "What groups do I have?" | Lists all groups |
| "Show the kids devices group" | Shows group details |

### Available Tools (21)

| Category | Tools | Description |
|----------|-------|-------------|
| **Status & Health** | `network_status` | Check API connectivity |
| | `network_health` | Site health summary |
| | `internet_speed` | Last speed test result |
| | `run_speedtest` | Run new speed test |
| | `isp_performance` | ISP metrics over time |
| **Counts & Lists** | `client_count` | Count clients by category |
| | `device_list` | List UniFi devices |
| | `network_list` | List networks/VLANs |
| **Lookups** | `find_client` | Find client by name/MAC |
| | `find_device` | Find device by name/MAC/IP |
| | `client_status` | Check if client is online/blocked |
| **Actions** | `block_client` | Block from network |
| | `unblock_client` | Restore access |
| | `kick_client` | Force disconnect |
| | `restart_device` | Reboot device |
| | `create_voucher` | Create guest WiFi code |
| **Groups** | `list_groups` | List all client groups |
| | `get_group` | Get group details |
| | `block_group` | Block all in group |
| | `unblock_group` | Unblock all in group |
| | `group_status` | Live status of group members |

### Architecture

```
┌─────────────────┐
│  Claude Desktop │
└────────┬────────┘
         │ MCP Protocol (stdio)
         ▼
┌─────────────────┐
│   MCP Server    │  ← 21 AI-optimized tools
│   (ui_mcp)      │
└────────┬────────┘
         │ subprocess
         ▼
┌─────────────────┐
│    UI CLI       │  ← All business logic
│   (ui_cli)      │
└─────────────────┘
```

See [MCP Documentation](src/ui_mcp/README.md) for full technical details.

---

## Output Formats

All commands support multiple output formats:

```bash
./ui devices list               # Table (default, human-readable)
./ui devices list -o json       # JSON (for scripting)
./ui devices list -o csv        # CSV (for spreadsheets)
./ui lo config show -o yaml     # YAML (for config files)
```

### JSON for Scripting

```bash
# Count devices
./ui devices list -o json | jq 'length'

# Find offline devices
./ui devices list -o json | jq '[.[] | select(.status == "offline")]'

# Get all client IPs
./ui lo clients list -o json | jq -r '.[].ip'

# Get client MACs on Guest network
./ui lo clients list -n Guest -o json | jq -r '.[].mac'

# Find high-traffic clients
./ui lo clients list -o json | jq '[.[] | select(.tx_bytes > 1000000000)]'
```

### CSV for Spreadsheets

```bash
# Export to CSV file
./ui devices list -o csv > devices.csv
./ui lo clients list -o csv > clients.csv
./ui isp metrics -o csv > isp-metrics.csv
```

### CI/CD Usage

Spinners are automatically disabled when running in CI environments:

```bash
# Automatically disabled when CI=true (GitHub Actions, etc.)
./ui lo clients count -o json

# Explicitly disable spinner
UNIFI_NO_SPINNER=1 ./ui lo health -o json

# Also disabled when NO_COLOR is set
NO_COLOR=1 ./ui lo health
```

---

## Command Reference

### Top-Level Commands

```
./ui
├── status              # Check Cloud API connection
├── version             # Show CLI version
├── speedtest           # Run/view speed test
├── hosts               # Manage controllers (cloud)
├── sites               # Manage sites (cloud)
├── devices             # Manage devices (cloud)
├── isp                 # ISP metrics (cloud)
├── sdwan               # SD-WAN configuration (cloud)
├── groups              # Client groups (local storage)
├── local / lo          # Local controller commands
└── mcp                 # Claude Desktop integration
```

### Cloud API Commands

<details>
<summary><strong>Click to expand</strong></summary>

```
./ui hosts
├── list                # List all controllers
└── get <ID>            # Get controller details

./ui sites
└── list                # List all sites

./ui devices
├── list                # List all devices
│   ├── --host <ID>     # Filter by controller
│   └── --verbose       # Show details
└── count               # Count devices
    └── --by <field>    # Group by model/status/host

./ui isp
└── metrics             # ISP performance metrics
    ├── --interval      # 5m or 1h (default: 1h)
    └── --hours         # Time range (default: 168)

./ui sdwan
├── list                # List SD-WAN configs
├── get <ID>            # Get config details
└── status <ID>         # Deployment status

./ui speedtest
├── (no args)           # Get last result
└── -r, --run           # Run new test
```

</details>

### Local Controller Commands

<details>
<summary><strong>Click to expand</strong></summary>

```
./ui lo [--timeout N] [-q/--quick]

./ui lo health          # Site health summary

./ui lo clients
├── list                # Connected clients
│   ├── -w              # Wired only
│   ├── -W              # Wireless only
│   ├── -n <network>    # Filter by network
│   ├── -g <group>      # Filter by group
│   └── -v              # Verbose
├── all                 # All clients (inc. offline)
├── get <name|MAC>      # Client details
├── status <name|MAC>   # Full client status
├── block <name|MAC>    # Block client
│   ├── -g <group>      # Block all in group
│   └── -y              # Skip confirmation
├── unblock <name|MAC>  # Unblock client
│   ├── -g <group>      # Unblock all in group
│   └── -y              # Skip confirmation
├── kick <name|MAC>     # Disconnect client
│   ├── -g <group>      # Kick all in group
│   └── -y              # Skip confirmation
├── count               # Count by category
│   ├── --by <field>    # type/network/vendor/ap/experience
│   └── -a              # Include offline
└── duplicates          # Find duplicate names

./ui lo devices
├── list                # List network devices
│   └── -v              # Verbose
├── get <ID|MAC|name>   # Device details
├── restart <device>    # Restart device
│   └── -y              # Skip confirmation
├── upgrade <device>    # Upgrade firmware
│   └── -y              # Skip confirmation
├── locate <device>     # Toggle locate LED
│   └── --off           # Turn off LED
└── adopt <MAC>         # Adopt new device

./ui lo networks
├── list                # List networks/VLANs
│   └── -v              # Verbose
└── get <ID>            # Network details

./ui lo firewall
├── list                # List firewall rules
│   ├── --ruleset       # Filter by ruleset
│   └── -v              # Verbose
└── groups              # List address/port groups
    └── -v              # Show members

./ui lo portfwd
└── list                # List port forwards
    └── -v              # Verbose

./ui lo vouchers
├── list                # List guest vouchers
│   └── -v              # Verbose
├── create              # Create voucher(s)
│   ├── -c <count>      # Number to create
│   ├── -d <minutes>    # Duration
│   ├── -q <MB>         # Data quota
│   ├── --up <kbps>     # Upload limit
│   ├── --down <kbps>   # Download limit
│   └── -n <note>       # Add note
└── delete <code>       # Delete voucher
    └── -y              # Skip confirmation

./ui lo dpi
├── stats               # Site DPI statistics
│   ├── -l <limit>      # Number of apps
│   └── -v              # Verbose
└── client <name|MAC>   # Per-client DPI

./ui lo stats
├── daily               # Daily traffic stats
│   └── --days <n>      # Number of days
└── hourly              # Hourly traffic stats
    └── --hours <n>     # Number of hours

./ui lo events
└── list                # Recent events
    ├── -l <limit>      # Number of events
    └── -v              # Verbose

./ui lo config
└── show                # Export running config
    ├── -o <format>     # table/json/yaml
    ├── -s <section>    # networks/wireless/firewall/devices/portfwd/dhcp/routing
    ├── -v              # Include IDs
    └── --show-secrets  # Include passwords
```

</details>

### Client Groups Commands

<details>
<summary><strong>Click to expand</strong></summary>

```
./ui groups
├── list                # List all groups
├── ls                  # Alias for list
├── create <name>       # Create static group
│   └── -d <desc>       # Description
├── show <name>         # Show group details
├── delete <name>       # Delete group
│   └── -y              # Skip confirmation
├── rm <name>           # Alias for delete
├── edit <name>         # Edit group
│   ├── -n <name>       # New name
│   └── -d <desc>       # New description
├── add <group> <MAC>   # Add member(s)
│   └── -a <alias>      # Set alias (single MAC only)
├── remove <group> <id> # Remove member (by MAC or alias)
├── alias <grp> <id>    # Set/clear member alias
│   └── --clear         # Clear alias
├── members <group>     # List members
├── clear <group>       # Remove all members
│   └── -y              # Skip confirmation
├── auto <name>         # Create auto group
│   ├── --vendor        # Match by vendor/OUI
│   ├── --name          # Match by client name
│   ├── --hostname      # Match by hostname
│   ├── --network       # Match by network/SSID
│   ├── --ip            # Match by IP/range/CIDR
│   ├── --mac           # Match by MAC prefix
│   ├── --type          # Match by wired/wireless
│   ├── -d <desc>       # Description
│   └── --dry-run       # Preview without creating
├── export              # Export to JSON
│   └── -o <file>       # Output file
└── import <file>       # Import from JSON
    ├── --replace       # Replace all existing
    └── -y              # Skip confirmation
```

</details>

### MCP Commands

```
./ui mcp
├── install             # Add to Claude Desktop config
├── check               # Verify setup
├── show                # View current config
└── remove              # Remove from Claude Desktop
```

---

## Data Storage

UI-CLI stores local data in `~/.config/ui-cli/`:

| File | Purpose |
|------|---------|
| `session.json` | Cached controller login session |
| `groups.json` | Client groups definitions |

### Session Management

Sessions are cached to avoid repeated logins:

```bash
# Force new session (if having auth issues)
rm ~/.config/ui-cli/session.json
./ui lo health
```

### Groups Storage

Groups are stored locally and don't require network access to manage:

```bash
# View storage location
cat ~/.config/ui-cli/groups.json

# Backup groups
./ui groups export -o ~/groups-backup.json

# Restore groups
./ui groups import ~/groups-backup.json
```

---

## Troubleshooting

### Common Errors

| Error | Solution |
|-------|----------|
| "API key not configured" | Add `UNIFI_API_KEY` to `.env` |
| "Invalid API key" | Regenerate key at [unifi.ui.com](https://unifi.ui.com) → Settings → API |
| "Connection timeout" (cloud) | Check internet access to `api.ui.com` |
| "Controller URL not configured" | Add `UNIFI_CONTROLLER_URL` to `.env` |
| "Invalid username or password" | Verify credentials work in UniFi web UI |
| "SSL certificate verify failed" | Set `UNIFI_CONTROLLER_VERIFY_SSL=false` |
| "Connection timeout" (local) | Use `./ui lo --timeout 60 health` |
| "Session expired" | Delete `~/.config/ui-cli/session.json` |
| "Client not found" | Try partial name match or use MAC address |
| "DPI unavailable" | Enable DPI in controller settings |

### Debug Tips

```bash
# Verbose output for more details
./ui lo clients list -v
./ui lo devices list -v

# JSON output for debugging
./ui lo health -o json

# Check configuration
cat .env

# Check session state
cat ~/.config/ui-cli/session.json

# Force fresh session
rm ~/.config/ui-cli/session.json
```

### Getting Help

```bash
# General help
./ui --help

# Command-specific help
./ui lo --help
./ui lo clients --help
./ui groups --help
./ui mcp --help
```

---

## Documentation

| Resource | Description |
|----------|-------------|
| [Online Documentation](https://vedanta.github.io/ui-cli) | Full documentation site |
| [User Guide](USERGUIDE.md) | Detailed usage examples |
| [Client Groups](docs/groups.md) | Groups feature guide |
| [MCP Server](src/ui_mcp/README.md) | Claude Desktop integration |
| [MCP Architecture](src/ui_mcp/ARCHITECTURE.md) | Technical design |
| [Roadmap](ROADMAP.md) | Planned features |
| [Changelog](CHANGELOG.md) | Version history |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

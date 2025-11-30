# UniFi CLI User Guide

A complete guide to using the UniFi CLI tool for managing your UniFi infrastructure.

---

## Table of Contents

1. [Getting Started](#getting-started)
   - [Installation](#installation)
   - [Configuration](#configuration)
   - [Verify Setup](#verify-setup)
2. [Cloud API Commands](#cloud-api-commands)
   - [Status](#status)
   - [Hosts](#hosts)
   - [Sites](#sites)
   - [Devices](#devices)
   - [ISP Metrics](#isp-metrics)
   - [SD-WAN](#sd-wan)
3. [Local Controller Commands](#local-controller-commands)
   - [Setup](#local-controller-setup)
   - [Listing Clients](#listing-clients)
   - [Client Details](#client-details)
   - [Client Actions](#client-actions)
   - [Client Statistics](#client-statistics)
4. [Output Formats](#output-formats)
5. [Command Reference](#command-reference)
6. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Installation

**Prerequisites:**
- Python 3.10 or higher
- Conda (recommended) or pip

**Step 1: Clone the repository**

```bash
git clone <repo-url> ui-cmd
cd ui-cmd
```

**Step 2: Create environment**

Using Conda (recommended):
```bash
conda env create -f environment.yml
conda activate ui-cli
pip install -e .
```

Using pip:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
```

**Step 3: Run the CLI**

```bash
# Using the wrapper script (auto-activates conda)
./ui --help

# Or after activating environment
ui --help
```

### Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Cloud API (for ./ui commands)
UNIFI_API_KEY=your-api-key-here

# Local Controller (for ./ui local commands)
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword
UNIFI_CONTROLLER_SITE=default
UNIFI_CONTROLLER_VERIFY_SSL=false
```

**Getting a Cloud API Key:**

1. Go to [unifi.ui.com](https://unifi.ui.com)
2. Navigate to **Settings** → **API**
3. Click **Create API Key**
4. Copy the key (shown only once!)

### Verify Setup

Check cloud API connection:

```bash
./ui status
```

Expected output:
```
UniFi CLI v0.1.0
────────────────────────────────────────

Site Manager API (api.ui.com)
  URL:               https://api.ui.com/v1
  API Key:           ****...abc123 (configured)
  Connection:        OK (205.3ms)
  Authentication:    Valid

Account Summary:
  Hosts:      2
  Sites:      1
  Devices:    23
```

Check local controller connection:

```bash
./ui lo clients list
```

---

## Cloud API Commands

These commands use the UniFi Site Manager API at `api.ui.com`.

### Status

Check API connectivity and authentication.

```bash
# Basic status check
./ui status

# JSON output for scripting
./ui status -o json

# Show full API key (verbose)
./ui status -v
```

### Hosts

Hosts are UniFi consoles/controllers (UDM, Cloud Key, etc.).

```bash
# List all hosts
./ui hosts list

# Get details for a specific host
./ui hosts get HOST_ID

# Export to CSV
./ui hosts list -o csv > hosts.csv

# JSON output
./ui hosts get HOST_ID -o json
```

### Sites

Sites are logical groupings within a host.

```bash
# List all sites
./ui sites list

# JSON output
./ui sites list -o json
```

### Devices

Devices include APs, switches, gateways, and cameras.

```bash
# List all devices
./ui devices list

# Filter by host
./ui devices list --host HOST_ID

# Show verbose details
./ui devices list -v

# Export to CSV
./ui devices list -o csv > devices.csv
```

**Counting devices:**

```bash
# Total count
./ui devices count

# Group by model
./ui devices count --by model

# Group by status (find offline devices)
./ui devices count --by status

# Group by product line
./ui devices count --by product-line

# Group by host
./ui devices count --by host

# JSON output
./ui devices count -b model -o json
```

### ISP Metrics

View internet service provider performance metrics.

```bash
# Hourly metrics (last 7 days)
./ui isp metrics

# 5-minute intervals (last 24 hours)
./ui isp metrics -i 5m

# Hourly intervals
./ui isp metrics -i 1h

# Custom time range (last 48 hours)
./ui isp metrics --hours 48

# Export to CSV
./ui isp metrics -o csv > isp.csv
```

**Available metrics:**
- Latency (average and maximum)
- Download/upload speeds
- Uptime percentage
- Packet loss
- ISP name

### SD-WAN

Manage SD-WAN (Site Magic) configurations.

```bash
# List all SD-WAN configs
./ui sdwan list

# Get config details
./ui sdwan get CONFIG_ID

# Get deployment status
./ui sdwan status CONFIG_ID
```

---

## Local Controller Commands

These commands connect directly to your UniFi Controller (UDM, Cloud Key, or self-hosted).

Use `./ui local` or the shorthand `./ui lo`.

### Local Controller Setup

Add these to your `.env` file:

```bash
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword
UNIFI_CONTROLLER_SITE=default
UNIFI_CONTROLLER_VERIFY_SSL=false
```

**Notes:**
- Use `https://` for the controller URL
- Set `VERIFY_SSL=false` for self-signed certificates (common on UDM)
- The default site is usually `default`

### Listing Clients

**List connected (online) clients:**

```bash
./ui lo clients list
```

Output:
```
                            Connected Clients
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ Name           ┃ MAC               ┃ IP          ┃ Network  ┃ Type     ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ my-MacBook     │ AA:BB:CC:DD:EE:FF │ 10.0.1.50   │ Home     │ Wireless │
│ Living-Room-TV │ 11:22:33:44:55:66 │ 10.0.1.100  │ Home     │ Wired    │
└────────────────┴───────────────────┴─────────────┴──────────┴──────────┘
```

**Filter options:**

```bash
# Wired clients only
./ui lo clients list --wired
./ui lo clients list -w

# Wireless clients only
./ui lo clients list --wireless
./ui lo clients list -W

# Filter by network/SSID
./ui lo clients list --network "Guest"
./ui lo clients list -n "Home"

# Show more details
./ui lo clients list --verbose
./ui lo clients list -v
```

**List all known clients (including offline):**

```bash
./ui lo clients all
```

### Client Details

**Get client information:**

You can use either the client name or MAC address:

```bash
# By name
./ui lo clients get my-MacBook

# By MAC address
./ui lo clients get AA:BB:CC:DD:EE:FF

# Partial name matching works too
./ui lo clients get MacBook
```

**Get comprehensive client status:**

```bash
./ui lo clients status my-MacBook
```

Output:
```
Client Status: my-MacBook
────────────────────────────────────────
  MAC:       AA:BB:CC:DD:EE:FF
  Vendor:    Apple, Inc.
  IP:        10.0.1.50
  Type:      Wireless
  Network:   Home
  AP:        Living Room AP

  WiFi Info
  Signal:    -52 dBm
  Channel:   Ch 36 (AC)
  Experience: 98%

  Connection
  Uptime:    2d 5h
  Speed:     ↑866 / ↓866 Mbps
  Data:      ↑1.2 GB / ↓15.8 GB

  Status
  Online:    Yes
  Blocked:   No
```

**Understanding the status output:**

| Field | Description |
|-------|-------------|
| Signal | WiFi signal strength in dBm (green: > -50, yellow: -50 to -70, red: < -70) |
| Channel | WiFi channel and protocol (AC = WiFi 5, AX = WiFi 6) |
| Experience | UniFi's satisfaction score (green: > 80%, yellow: 50-80%, red: < 50%) |
| Uptime | How long the client has been connected |
| Speed | Current TX/RX link speed in Mbps |
| Data | Total data transferred this session |

### Client Actions

**Block a client:**

Prevents the client from connecting to the network.

```bash
# With confirmation prompt
./ui lo clients block my-MacBook

# Skip confirmation
./ui lo clients block my-MacBook -y
./ui lo clients block my-MacBook --yes
```

**Unblock a client:**

```bash
./ui lo clients unblock my-MacBook
./ui lo clients unblock my-MacBook -y
```

**Kick (disconnect) a client:**

Forces the client to disconnect and reconnect.

```bash
./ui lo clients kick my-MacBook
./ui lo clients kick my-MacBook -y
```

### Client Statistics

**Count clients by category:**

```bash
# By connection type (default)
./ui lo clients count
```

Output:
```
        Client Count by Type
┏━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Type       ┃      Count ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Wired      │         12 │
│ Wireless   │         35 │
│ ────────── │ ────────── │
│ Total      │         47 │
└────────────┴────────────┘
```

**Other grouping options:**

```bash
# By network/SSID
./ui lo clients count --by network

# By device vendor/manufacturer
./ui lo clients count --by vendor

# By access point
./ui lo clients count --by ap

# By WiFi experience quality
./ui lo clients count --by experience

# Include offline clients
./ui lo clients count --include-offline
./ui lo clients count -a
```

**Find duplicate client names:**

Useful for finding devices with multiple NICs (WiFi + Ethernet) or different devices with the same name.

```bash
./ui lo clients duplicates
```

Output:
```
Found 3 duplicate name(s):

my-MacBook (2 NICs) ← likely same device
  • AA:BB:CC:DD:EE:FF (10.0.1.50) wifi - Apple, Inc.
  • 11:22:33:44:55:66 (10.0.1.51) wired - Apple, Inc.

iPad (4 clients)
  • 22:33:44:55:66:77 (10.0.1.60) wifi - Apple, Inc.
  • 33:44:55:66:77:88 (10.0.1.61) wifi - Apple, Inc.
  • 44:55:66:77:88:99 (10.0.1.62) wifi - Apple, Inc.
  • 55:66:77:88:99:AA (10.0.1.63) wifi - Apple, Inc.
```

The command identifies:
- **Multi-NIC devices**: Same device with both wired and wireless connections (marked "← likely same device")
- **Name conflicts**: Different devices sharing the same name

---

## Output Formats

All commands support three output formats via the `--output` or `-o` option.

### Table (Default)

Human-readable formatted tables:

```bash
./ui devices list
./ui lo clients list
```

### JSON

Machine-readable JSON for scripting:

```bash
./ui devices list -o json
./ui lo clients status my-MacBook -o json
```

**Example: Using with jq**

```bash
# Count devices
./ui devices list -o json | jq 'length'

# Get offline devices
./ui devices list -o json | jq '[.[] | select(.status == "offline")]'

# List device names
./ui devices list -o json | jq -r '.[].name'

# Get client IPs
./ui lo clients list -o json | jq -r '.[].ip'
```

### CSV

Spreadsheet-compatible CSV:

```bash
./ui devices list -o csv > devices.csv
./ui lo clients list -o csv > clients.csv
```

---

## Command Reference

### Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output format: `table`, `json`, `csv` |
| `--verbose` | `-v` | Show additional details |
| `--help` | | Show help message |
| `--version` | `-V` | Show version |

### Cloud API Commands

| Command | Description |
|---------|-------------|
| `./ui status` | Check API connection and authentication |
| `./ui version` | Show CLI version |
| `./ui hosts list` | List all hosts (controllers) |
| `./ui hosts get <ID>` | Get host details |
| `./ui sites list` | List all sites |
| `./ui devices list` | List all devices |
| `./ui devices count` | Count devices by category |
| `./ui isp metrics` | Show ISP performance metrics |
| `./ui sdwan list` | List SD-WAN configurations |
| `./ui sdwan get <ID>` | Get SD-WAN config details |
| `./ui sdwan status <ID>` | Get SD-WAN deployment status |

### Local Controller Commands

| Command | Description |
|---------|-------------|
| `./ui lo clients list` | List connected clients |
| `./ui lo clients all` | List all known clients (including offline) |
| `./ui lo clients get <name\|MAC>` | Get client details |
| `./ui lo clients status <name\|MAC>` | Show comprehensive client status |
| `./ui lo clients block <name\|MAC>` | Block a client |
| `./ui lo clients unblock <name\|MAC>` | Unblock a client |
| `./ui lo clients kick <name\|MAC>` | Disconnect a client |
| `./ui lo clients count` | Count clients by category |
| `./ui lo clients duplicates` | Find duplicate client names |

### Command Options

**`./ui devices list`**

| Option | Short | Description |
|--------|-------|-------------|
| `--host` | `-h` | Filter by host ID |
| `--output` | `-o` | Output format |
| `--verbose` | `-v` | Show additional details |

**`./ui devices count`**

| Option | Short | Description |
|--------|-------|-------------|
| `--by` | `-b` | Group by: `model`, `status`, `product-line`, `host` |
| `--output` | `-o` | Output format |

**`./ui isp metrics`**

| Option | Short | Description |
|--------|-------|-------------|
| `--interval` | `-i` | Interval: `5m` or `1h` |
| `--hours` | | Number of hours to fetch |
| `--output` | `-o` | Output format |

**`./ui lo clients list`**

| Option | Short | Description |
|--------|-------|-------------|
| `--network` | `-n` | Filter by network/SSID |
| `--wired` | `-w` | Show only wired clients |
| `--wireless` | `-W` | Show only wireless clients |
| `--verbose` | `-v` | Show additional details |
| `--output` | `-o` | Output format |

**`./ui lo clients count`**

| Option | Short | Description |
|--------|-------|-------------|
| `--by` | `-b` | Group by: `type`, `network`, `vendor`, `ap`, `experience` |
| `--include-offline` | `-a` | Include offline clients |
| `--output` | `-o` | Output format |

**`./ui lo clients block/unblock/kick`**

| Option | Short | Description |
|--------|-------|-------------|
| `--yes` | `-y` | Skip confirmation prompt |

---

## Troubleshooting

### "API key not configured"

Make sure your `.env` file exists and contains your API key:

```bash
cp .env.example .env
# Edit .env and add UNIFI_API_KEY=your-key
```

### "Invalid API key"

1. Check your API key at [unifi.ui.com](https://unifi.ui.com) → Settings → API
2. Ensure no extra spaces or quotes in `.env`
3. API keys may expire - create a new one if needed

### "Connection timeout"

- Check your internet connection
- The cloud API requires access to `api.ui.com`
- For local controller, verify the URL is correct and reachable

### "Controller URL not configured"

Add local controller settings to `.env`:

```bash
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword
```

### "Invalid username or password" (Local Controller)

1. Verify credentials work in the UniFi web interface
2. Create a local admin account (not a UI.com account)
3. Some controllers require a specific user for API access

### "SSL certificate verify failed"

For self-signed certificates (common on UDM), add to `.env`:

```bash
UNIFI_CONTROLLER_VERIFY_SSL=false
```

### "Client not found"

When using client names:
- Names are case-insensitive
- Partial matching is supported
- If multiple clients match, you'll see a list to choose from
- Use the MAC address for exact matching

### Empty Tables

Some commands may return empty results if:
- No SD-WAN configurations exist
- No clients are connected
- Filters exclude all results

Use `./ui status` to verify your account has resources.

### Session Expired

The CLI automatically handles session expiry for local controller commands. If you see repeated authentication errors, try:

```bash
# Clear the session file
rm ~/.config/ui-cli/session.json
```

---

## Tips & Tricks

### Aliases

Add to your shell profile (`.bashrc`, `.zshrc`):

```bash
alias ui='./ui'
alias uilo='./ui lo'
alias clients='./ui lo clients'
```

### Quick Client Lookup

```bash
# Find a device quickly
./ui lo clients list | grep -i iphone

# Get status by partial name
./ui lo clients status iphone
```

### Export for Reporting

```bash
# Weekly device inventory
./ui devices list -o csv > "devices-$(date +%Y%m%d).csv"

# Client snapshot
./ui lo clients list -o csv > "clients-$(date +%Y%m%d).csv"
```

### Scripting

```bash
# Check if API is working
if ./ui status -o json | jq -e '.authentication == "Valid"' > /dev/null; then
    echo "API OK"
fi

# Alert on offline devices
OFFLINE=$(./ui devices count -b status -o json | jq '.counts.offline // 0')
if [ "$OFFLINE" -gt 0 ]; then
    echo "Warning: $OFFLINE devices offline"
fi

# Block device by name in script
./ui lo clients block "Guest-Device" -y
```

---

## Getting Help

```bash
# General help
./ui --help

# Command-specific help
./ui devices --help
./ui devices count --help
./ui lo clients --help
./ui lo clients status --help
```

For issues and feature requests, visit the GitHub repository.

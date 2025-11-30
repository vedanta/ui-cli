# UniFi CLI

<p align="center">
  <img src="art/uicli.png" alt="UI-CLI" width="400">
</p>

A command-line interface for the [UniFi Site Manager API](https://developer.ui.com/site-manager-api/gettingstarted). Manage your UniFi infrastructure from the terminal.

> **New to UI-CLI?** Check out the [User Guide](USERGUIDE.md) for detailed instructions and examples.

## Features

**Site Manager API (Cloud)**
- List and inspect hosts, sites, and devices
- View ISP performance metrics
- Manage SD-WAN configurations
- Check API connectivity and authentication status

**Local Controller API (Direct)**
- Manage connected clients (list, block, kick)
- View detailed client status (signal, speed, data usage)
- Count clients by network, vendor, AP, or experience
- Find duplicate client names and multi-NIC devices

**General**
- Multiple output formats (table, JSON, CSV)
- Works with UDM, Cloud Key, and self-hosted controllers

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Command Reference](#command-reference)
- [Output Formats](#output-formats)
- [Examples](#examples)
- [Local Controller Commands](#local-controller-commands)
- [User Guide](USERGUIDE.md) - Comprehensive documentation
- [Roadmap](#roadmap)
- [License](#license)

---

## Quick Start

```bash
# 1. Clone and setup
git clone <repo-url> ui-cmd
cd ui-cmd
conda env create -f environment.yml
conda activate ui-cli
pip install -e .

# 2. Configure API key
cp .env.example .env
# Edit .env and add your UNIFI_API_KEY

# 3. Verify connection
./ui status

# 4. Start using
./ui devices list
./ui devices count --by model
```

---

## Installation

### Prerequisites

- Python 3.10+
- Conda (recommended) or pip

### Using Conda (Recommended)

```bash
# Create environment from file
conda env create -f environment.yml

# Activate environment
conda activate ui-cli

# Install package in development mode
pip install -e .
```

### Using pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Running the CLI

```bash
# Option 1: Use the bash wrapper (auto-activates conda)
./ui --help

# Option 2: After pip install (requires active environment)
ui --help
```

---

## Configuration

### Getting an API Key

1. Sign in to [unifi.ui.com](https://unifi.ui.com)
2. Navigate to **Settings** → **API**
3. Click **Create API Key**
4. Copy the key (it's only shown once!)

### Setting Up

Create a `.env` file in the project directory:

```bash
cp .env.example .env
```

Edit `.env` with your API key:

```bash
# Required: Your UniFi API key
UNIFI_API_KEY=your-api-key-here

# Optional: API base URL (defaults to stable v1 API)
# UNIFI_API_URL=https://api.ui.com/v1

# Optional: Request timeout in seconds (default: 30)
# UNIFI_TIMEOUT=30
```

### Verify Configuration

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

---

## Command Reference

### Global Options

All commands support these options:

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output format: `table`, `json`, or `csv` |
| `--verbose` | `-v` | Show detailed information |
| `--help` | | Show help message |

### Version

Display the CLI version.

```bash
ui version             # Show version
```

### Status

Check API connectivity and authentication.

```bash
ui status              # Check connection and auth
ui status -o json      # Output as JSON
ui status -v           # Show full API key
```

### Hosts

Manage UniFi hosts (consoles/controllers like UDM, Cloud Key).

```bash
ui hosts list                    # List all hosts
ui hosts list -o csv > hosts.csv # Export to CSV
ui hosts get <HOST_ID>           # Get host details
ui hosts get <HOST_ID> -o json   # Get as JSON
```

### Sites

Manage UniFi sites.

```bash
ui sites list                    # List all sites
ui sites list -o json            # Output as JSON
```

### Devices

Manage UniFi devices (APs, switches, gateways, cameras).

```bash
ui devices list                       # List all devices
ui devices list --host <HOST_ID>      # Filter by host
ui devices list -o csv > devices.csv  # Export to CSV

ui devices count                      # Total device count
ui devices count --by model           # Count by model
ui devices count --by status          # Count by status
ui devices count --by product-line    # Count by product line
ui devices count --by host            # Count by host
ui devices count -b model -o json     # Output as JSON
```

### ISP Metrics

View ISP performance metrics.

```bash
ui isp metrics                   # Hourly metrics (last 7 days)
ui isp metrics -i 5m             # 5-minute metrics (last 24h)
ui isp metrics -i 1h             # Hourly metrics
ui isp metrics --hours 48        # Last 48 hours
ui isp metrics -o csv > isp.csv  # Export to CSV
```

**Metrics include:** latency (avg/max), download/upload speeds, uptime, packet loss, ISP name.

### SD-WAN

Manage SD-WAN (Site Magic) configurations.

```bash
ui sdwan list                    # List all SD-WAN configs
ui sdwan get <CONFIG_ID>         # Get config details
ui sdwan status <CONFIG_ID>      # Get deployment status
```

---

## Output Formats

### Table (Default)

Human-readable formatted tables:

```bash
./ui devices list
```
```
                              UniFi Devices
┏━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┓
┃ ID       ┃ Name       ┃ Model   ┃ IP Address ┃ Status ┃ Host    ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━┩
│ abc12... │ Gateway    │ UDM SE  │ 192.168... │ online │ Main    │
│ def34... │ Living AP  │ U6 Pro  │ 10.0.1.5   │ online │ Main    │
└──────────┴────────────┴─────────┴────────────┴────────┴─────────┘
```

### JSON

Machine-readable JSON for scripting:

```bash
./ui devices list -o json
```
```json
[
  {
    "id": "abc123...",
    "name": "Gateway",
    "model": "UDM SE",
    "ip": "192.168.1.1",
    "status": "online"
  }
]
```

### CSV

Spreadsheet-compatible CSV:

```bash
./ui devices list -o csv > devices.csv
```
```csv
ID,Name,Model,IP Address,MAC,Product Line,Status,Version,Host
abc123def456,Gateway,UDM SE,192.168.1.1,AA:BB:CC:DD:EE:FF,network,online,4.0.6,Main
```

---

## Examples

### Export All Devices to CSV

```bash
./ui devices list -o csv > devices.csv
```

### Get Device Inventory by Model

```bash
./ui devices count --by model
```
```
        Device Count by Model
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Model                ┃      Count ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ U6 LR                │          1 │
│ U6 Pro               │          2 │
│ UDM SE               │          1 │
│ USW 24 PoE           │          1 │
│ ──────────────────── │ ────────── │
│ Total                │          5 │
└──────────────────────┴────────────┘
```

### Check for Offline Devices

```bash
./ui devices count --by status
```

### Monitor ISP Performance

```bash
# Get last 24 hours of 5-minute interval metrics
./ui isp metrics -i 5m -o csv > isp-metrics.csv
```

### Scripting with JSON

```bash
# Get device count using jq
./ui devices list -o json | jq 'length'

# Get all offline devices
./ui devices list -o json | jq '[.[] | select(.status == "offline")]'

# List device names only
./ui devices list -o json | jq -r '.[].name'
```

### Verify API Status in Scripts

```bash
if ./ui status -o json | jq -e '.authentication == "Valid"' > /dev/null; then
    echo "API is working"
else
    echo "API authentication failed"
    exit 1
fi
```

---

## Local Controller Commands

Direct connection to your UniFi Controller (UDM, Cloud Key, self-hosted) for local network management.

### Configuration

Add to your `.env` file:

```bash
# Local Controller
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword
UNIFI_CONTROLLER_SITE=default
UNIFI_CONTROLLER_VERIFY_SSL=false
```

### Local Clients

Manage connected clients on your local network. Use `./ui local` or `./ui lo` (shorthand).

```bash
# List active (connected) clients
./ui lo clients list
./ui lo clients list --wired          # Wired only
./ui lo clients list --wireless       # Wireless only
./ui lo clients list -n "Guest"       # Filter by network

# List all known clients (including offline)
./ui lo clients all

# Get client details (by name or MAC)
./ui lo clients get my-iPhone
./ui lo clients get AA:BB:CC:DD:EE:FF

# Get detailed client status
./ui lo clients status my-iPhone

# Client actions (with confirmation)
./ui lo clients block my-iPhone       # Block client
./ui lo clients unblock my-iPhone     # Unblock client
./ui lo clients kick my-iPhone        # Disconnect client
./ui lo clients block my-iPhone -y    # Skip confirmation

# Count clients by category
./ui lo clients count                 # By type (wired/wireless)
./ui lo clients count --by network    # By network/SSID
./ui lo clients count --by vendor     # By manufacturer
./ui lo clients count --by ap         # By access point
./ui lo clients count --by experience # By WiFi experience
./ui lo clients count -a              # Include offline clients

# Find duplicate client names
./ui lo clients duplicates            # Shows multi-NIC devices
```

### Client Status Output

The `status` command shows comprehensive client information:

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

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features.

### Milestone 1: Site Manager API (Complete)

- Hosts, Sites, Devices management
- ISP Metrics
- SD-WAN configuration
- Status command

### Milestone 2: Local Controller API (In Progress)

- [x] Phase 2.1: Client management (list, status, block, kick, count, duplicates)
- [ ] Phase 2.2: Monitoring (events, alarms, health)
- [ ] Phase 2.3: Guest management (vouchers)
- [ ] Phase 2.4: Network info (networks, DPI)
- [ ] Phase 2.5: Security (firewall, port forwarding)
- [ ] Phase 2.6: Device commands (restart, upgrade, locate)
- [ ] Phase 2.7: Statistics

---

## API Reference

This CLI uses the [UniFi Site Manager API](https://developer.ui.com/site-manager-api/gettingstarted).

| Endpoint | CLI Command |
|----------|-------------|
| `GET /hosts` | `ui hosts list` |
| `GET /hosts/{id}` | `ui hosts get <id>` |
| `GET /sites` | `ui sites list` |
| `GET /devices` | `ui devices list` |
| `GET /ea/isp-metrics/{type}` | `ui isp metrics` |
| `GET /ea/sd-wan-configs` | `ui sdwan list` |
| `GET /ea/sd-wan-configs/{id}` | `ui sdwan get <id>` |
| `GET /ea/sd-wan-configs/{id}/status` | `ui sdwan status <id>` |

---

## Troubleshooting

### "API key not configured"

Make sure you have a `.env` file with your API key:

```bash
cp .env.example .env
# Edit .env and add UNIFI_API_KEY=your-key
```

### "Invalid API key"

1. Verify your API key at [unifi.ui.com](https://unifi.ui.com) → Settings → API
2. Make sure there are no extra spaces or quotes in your `.env` file
3. API keys may expire - create a new one if needed

### "Connection timeout"

Check your internet connection. The API requires access to `api.ui.com`.

### Empty tables

Some commands may return empty results if:
- You have no SD-WAN configurations (`ui sdwan list`)
- You have no sites/devices (new account)

Use `./ui status` to verify your account has resources.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

MIT License - see [LICENSE](LICENSE) for details.

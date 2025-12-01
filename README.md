# UniFi CLI

<p align="center">
  <img src="art/uicli_new.png" alt="UI-CLI" width="400">
</p>

<p align="center">
  <strong>Manage your UniFi infrastructure from the command line</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#cloud-commands">Cloud API</a> •
  <a href="#local-commands">Local API</a> •
  <a href="USERGUIDE.md">User Guide</a>
</p>

---

## What is UI-CLI?

UI-CLI is a command-line tool for managing UniFi networks. It supports two modes:

| Mode | Connection | Use Case |
|------|------------|----------|
| **Cloud API** | Via `api.ui.com` | Manage multiple sites, view ISP metrics, SD-WAN |
| **Local API** | Direct to controller | Client management, running config, real-time data |

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/vedanta/ui-cli.git
cd ui-cli
conda env create -f environment.yml
conda activate ui-cli
pip install -e .

# Configure
cp .env.example .env
# Edit .env with your credentials

# Verify
./ui status                    # Cloud API status
./ui lo clients list           # Local controller clients
```

---

## Configuration

Create a `.env` file:

```bash
# Cloud API (api.ui.com)
UNIFI_API_KEY=your-api-key-here

# Local Controller (direct connection)
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword
UNIFI_CONTROLLER_SITE=default
UNIFI_CONTROLLER_VERIFY_SSL=false
```

**Get your Cloud API key:** [unifi.ui.com](https://unifi.ui.com) → Settings → API → Create API Key

---

## Cloud Commands

Commands that use the UniFi Site Manager API (`api.ui.com`).

### Status & Info

```bash
./ui status                     # Check API connection
./ui version                    # Show CLI version
```

### Hosts & Sites

```bash
./ui hosts list                 # List all controllers
./ui hosts get <ID>             # Get controller details
./ui sites list                 # List all sites
```

### Devices

```bash
./ui devices list               # List all devices
./ui devices list --host <ID>   # Filter by controller
./ui devices count              # Count devices
./ui devices count --by model   # Group by model
./ui devices count --by status  # Find offline devices
```

### ISP Metrics

```bash
./ui isp metrics                # Last 7 days (hourly)
./ui isp metrics -i 5m          # Last 24h (5-min intervals)
./ui isp metrics --hours 48     # Custom time range
```

### SD-WAN

```bash
./ui sdwan list                 # List configurations
./ui sdwan get <ID>             # Get config details
./ui sdwan status <ID>          # Deployment status
```

---

## Local Commands

Commands that connect directly to your UniFi Controller. Use `./ui local` or `./ui lo`.

### Clients

```bash
# List clients
./ui lo clients list            # Connected clients
./ui lo clients list -w         # Wired only
./ui lo clients list -W         # Wireless only
./ui lo clients list -n Guest   # Filter by network
./ui lo clients all             # All clients (inc. offline)

# Client details
./ui lo clients get my-iPhone   # By name
./ui lo clients get AA:BB:CC:DD:EE:FF  # By MAC
./ui lo clients status my-iPhone       # Full status

# Client actions
./ui lo clients block my-iPhone     # Block client
./ui lo clients unblock my-iPhone   # Unblock client
./ui lo clients kick my-iPhone      # Disconnect client

# Statistics
./ui lo clients count               # By connection type
./ui lo clients count --by network  # By network/SSID
./ui lo clients count --by vendor   # By manufacturer
./ui lo clients count --by ap       # By access point
./ui lo clients duplicates          # Find duplicate names
```

### Running Config

Export your network configuration for backup or documentation.

```bash
# Full configuration
./ui lo config show             # All sections
./ui lo config show -o yaml     # YAML export
./ui lo config show -o json     # JSON export

# Specific sections
./ui lo config show -s networks     # VLANs, subnets, DHCP
./ui lo config show -s wireless     # SSIDs, security
./ui lo config show -s firewall     # Firewall rules
./ui lo config show -s devices      # Device inventory
./ui lo config show -s portfwd      # Port forwarding
./ui lo config show -s dhcp         # DHCP reservations
./ui lo config show -s routing      # Static routes

# Options
./ui lo config show --show-secrets  # Include passwords
./ui lo config show -v              # Verbose (show IDs)
```

**Example output:**

```
UniFi Running Configuration
══════════════════════════════════════════════════════════════════════
Controller: https://192.168.1.1
Site: default

┌─ NETWORKS ──────────────────────────────────────────────────────────┐

  Default
    Purpose:       corporate
    Subnet:        10.0.1.0/24
    Gateway:       10.0.1.1
    DHCP:          Enabled (10.0.1.100 - 10.0.1.254)

  IoT (VLAN 20)
    Purpose:       iot
    Subnet:        10.0.20.0/24
    Isolation:     Yes

└──────────────────────────────────────────────────────────────────────┘

┌─ WIRELESS ──────────────────────────────────────────────────────────┐

  HomeWiFi
    Network:       Default
    Security:      WPA2/WPA3 Personal
    Band:          2.4 GHz + 5 GHz

└──────────────────────────────────────────────────────────────────────┘

Summary: 2 networks, 1 SSIDs, 0 firewall rules, 4 devices
```

---

## Output Formats

All commands support multiple output formats:

```bash
./ui devices list               # Table (default)
./ui devices list -o json       # JSON
./ui devices list -o csv        # CSV
./ui lo config show -o yaml     # YAML (config only)
```

### JSON for Scripting

```bash
# Count devices
./ui devices list -o json | jq 'length'

# Find offline devices
./ui devices list -o json | jq '[.[] | select(.status == "offline")]'

# Get client IPs
./ui lo clients list -o json | jq -r '.[].ip'
```

### CSV for Export

```bash
./ui devices list -o csv > devices.csv
./ui lo clients list -o csv > clients.csv
```

---

## Client Status

The `./ui lo clients status` command shows comprehensive information:

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
  Signal:    -52 dBm          ← Color-coded (green/yellow/red)
  Channel:   Ch 36 (AC)
  Experience: 98%             ← Color-coded

  Connection
  Uptime:    2d 5h
  Speed:     ↑866 / ↓866 Mbps
  Data:      ↑1.2 GB / ↓15.8 GB

  Status
  Online:    Yes
  Blocked:   No
```

---

## Installation

### Prerequisites

- Python 3.10+
- Conda (recommended) or pip

### Using Conda

```bash
conda env create -f environment.yml
conda activate ui-cli
pip install -e .
```

### Using pip

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

### Running

```bash
./ui --help          # Using wrapper script
ui --help            # After pip install
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [User Guide](USERGUIDE.md) | Complete documentation with examples |
| [Roadmap](ROADMAP.md) | Planned features and progress |

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| "API key not configured" | Add `UNIFI_API_KEY` to `.env` |
| "Invalid API key" | Check key at [unifi.ui.com](https://unifi.ui.com) → Settings → API |
| "Connection timeout" | Verify internet access to `api.ui.com` |
| "Controller URL not configured" | Add `UNIFI_CONTROLLER_URL` to `.env` |
| "Invalid username or password" | Verify credentials work in UniFi web UI |
| "SSL certificate verify failed" | Set `UNIFI_CONTROLLER_VERIFY_SSL=false` |

---

## License

MIT License - see [LICENSE](LICENSE) for details.

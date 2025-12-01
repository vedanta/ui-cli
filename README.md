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
| **Local API** | Direct to controller | Client management, device control, real-time data |

### Features

**Cloud API (Site Manager)**
- View and manage multiple sites and controllers from anywhere
- List all devices across your infrastructure with filtering
- Monitor ISP performance metrics (latency, speeds, uptime, packet loss)
- Manage SD-WAN configurations and deployment status
- Count and group devices by model, status, or controller

**Local Controller API**
- **Client Management** - List connected clients, filter by wired/wireless/network, view detailed status including signal strength and WiFi experience, block/unblock/reconnect clients
- **Device Control** - List all network devices, restart or upgrade firmware, toggle locate LED for physical identification, adopt new devices
- **Network Visibility** - View all networks and VLANs with DHCP configuration, monitor site health (WAN/LAN/WLAN/VPN status), browse recent events and alerts
- **Security & Firewall** - Inspect firewall rules by ruleset, view address and port groups, list port forwarding rules
- **Traffic Analytics** - Deep packet inspection (DPI) statistics by application, per-client traffic breakdown, daily and hourly bandwidth reports
- **Guest Management** - Create hotspot vouchers with custom duration, data limits, and speed caps, list and delete existing vouchers
- **Configuration Export** - Export running config to YAML/JSON for backup, filter by section (networks, wireless, firewall, devices)

**General**
- Multiple output formats: table (human-readable), JSON (scripting), CSV (spreadsheets)
- Works with UDM, UDM Pro, UDM SE, Cloud Key, and self-hosted controllers
- Automatic controller type detection (UDM vs Cloud Key API paths)
- Session management with automatic re-authentication
- SSL verification bypass for self-signed certificates

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

### Health & Monitoring

```bash
./ui lo health                  # Site health summary
./ui lo events list             # Recent events
./ui lo events list -l 50       # Last 50 events
```

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
```

### Devices (Local)

```bash
# List and get
./ui lo devices list            # All network devices
./ui lo devices list -v         # Verbose (channels, load)
./ui lo devices get UDM-Pro     # Device details

# Actions
./ui lo devices restart UDM-Pro       # Restart device
./ui lo devices upgrade Office-AP     # Upgrade firmware
./ui lo devices locate Office-AP      # Toggle locate LED
./ui lo devices adopt 70:a7:41:xx:xx  # Adopt device
```

### Networks

```bash
./ui lo networks list           # All networks/VLANs
./ui lo networks list -v        # With DHCP details
```

### Firewall & Security

```bash
./ui lo firewall list           # Firewall rules
./ui lo firewall list --ruleset WAN_IN
./ui lo firewall groups         # Address/port groups
./ui lo portfwd list            # Port forwarding rules
```

### Guest Vouchers

```bash
./ui lo vouchers list           # All vouchers
./ui lo vouchers create         # Create voucher
./ui lo vouchers create -c 10 -d 60   # 10 vouchers, 60 min
./ui lo vouchers delete CODE    # Delete voucher
```

### DPI & Statistics

```bash
./ui lo dpi stats               # Site DPI stats
./ui lo dpi client my-MacBook   # Client DPI stats
./ui lo stats daily             # Daily traffic stats
./ui lo stats hourly            # Hourly traffic stats
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

## Command Reference

```
./ui
├── status              # Check API connection
├── version             # Show CLI version
├── speedtest           # Run speedtest on gateway
├── hosts               # Cloud: manage controllers
├── sites               # Cloud: manage sites
├── devices             # Cloud: manage devices
├── isp                 # Cloud: ISP metrics
├── sdwan               # Cloud: SD-WAN configs
└── local (lo)          # Local controller commands
```

<details>
<summary><strong>Cloud API Commands</strong> (click to expand)</summary>

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
    ├── --interval      # 5m, 1h (default: 1h)
    └── --hours         # Time range (default: 168)

./ui sdwan
├── list                # List SD-WAN configs
├── get <ID>            # Get config details
└── status <ID>         # Deployment status
```

</details>

<details>
<summary><strong>Local Controller Commands</strong> (click to expand)</summary>

```
./ui lo clients
├── list                # Connected clients
│   ├── -w              # Wired only
│   ├── -W              # Wireless only
│   └── -n <network>    # Filter by network
├── all                 # All clients (inc. offline)
├── get <name|MAC>      # Client details
├── status <name|MAC>   # Full client status
├── block <name|MAC>    # Block client
├── unblock <name|MAC>  # Unblock client
├── kick <name|MAC>     # Disconnect client
├── count               # Count by category
│   └── --by <field>    # type/network/vendor/ap
└── duplicates          # Find duplicate names

./ui lo devices
├── list                # List network devices
├── get <ID|MAC|name>   # Device details
├── restart <device>    # Restart device
├── upgrade <device>    # Upgrade firmware
├── locate <device>     # Toggle locate LED
│   └── --off           # Turn off LED
└── adopt <MAC>         # Adopt new device

./ui lo networks
├── list                # List networks/VLANs
└── get <ID>            # Network details

./ui lo firewall
├── list                # List firewall rules
│   └── --ruleset       # Filter by ruleset
└── groups              # List address/port groups

./ui lo portfwd
└── list                # List port forwards

./ui lo vouchers
├── list                # List guest vouchers
├── create              # Create voucher(s)
│   ├── -c <count>      # Number to create
│   ├── -d <minutes>    # Duration
│   ├── -q <MB>         # Data quota
│   ├── --up <kbps>     # Upload limit
│   └── --down <kbps>   # Download limit
└── delete <code>       # Delete voucher

./ui lo dpi
├── stats               # Site DPI statistics
└── client <name|MAC>   # Per-client DPI

./ui lo stats
├── daily               # Daily traffic stats
│   └── --days <n>      # Number of days
└── hourly              # Hourly traffic stats
    └── --hours <n>     # Number of hours

./ui lo events
└── list                # Recent events
    └── -l <limit>      # Number of events

./ui lo health          # Site health summary

./ui lo config
└── show                # Export running config
    ├── -o <format>     # table/json/yaml
    ├── -s <section>    # networks/wireless/firewall/devices
    └── --show-secrets  # Include passwords
```

</details>

---

## Documentation

| Document | Description |
|----------|-------------|
| [User Guide](USERGUIDE.md) | Complete documentation with examples |
| [Roadmap](ROADMAP.md) | Planned features and progress |
| [Changelog](CHANGELOG.md) | Version history |

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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

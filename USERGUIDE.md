# UniFi CLI User Guide

Complete reference for managing UniFi networks from the command line.

---

## Table of Contents

- [Setup](#setup)
- [Cloud API](#cloud-api)
- [Local Controller](#local-controller)
- [Running Config](#running-config)
- [Output Formats](#output-formats)
- [Quick Reference](#quick-reference)
- [Troubleshooting](#troubleshooting)

---

## Setup

### Install

```bash
git clone https://github.com/vedanta/ui-cli.git
cd ui-cli
conda env create -f environment.yml
conda activate ui-cli
pip install -e .
```

### Configure

Create `.env` file:

```bash
cp .env.example .env
```

Add your credentials:

```bash
# Cloud API
UNIFI_API_KEY=your-api-key-here

# Local Controller
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword
UNIFI_CONTROLLER_SITE=default
UNIFI_CONTROLLER_VERIFY_SSL=false
```

### Get API Key

1. Go to [unifi.ui.com](https://unifi.ui.com)
2. Settings → API → Create API Key
3. Copy immediately (shown once)

### Verify

```bash
./ui status              # Cloud API
./ui lo clients list     # Local controller
```

---

## Cloud API

Commands using `api.ui.com` - manage multiple sites from anywhere.

### Status

```bash
./ui status              # Connection check
./ui status -o json      # For scripting
./ui version             # CLI version
```

### Hosts

UniFi controllers (UDM, Cloud Key, etc.)

```bash
./ui hosts list                      # All hosts
./ui hosts get HOST_ID               # Host details
./ui hosts list -o csv > hosts.csv   # Export
```

### Sites

```bash
./ui sites list          # All sites
./ui sites list -o json  # JSON output
```

### Devices

APs, switches, gateways, cameras.

```bash
./ui devices list                    # All devices
./ui devices list --host HOST_ID     # Filter by host
./ui devices list -v                 # Verbose
./ui devices list -o csv             # Export

# Counting
./ui devices count                   # Total
./ui devices count --by model        # By model
./ui devices count --by status       # Find offline
./ui devices count --by product-line # By type
./ui devices count --by host         # By controller
```

### ISP Metrics

```bash
./ui isp metrics                # 7 days, hourly
./ui isp metrics -i 5m          # 24h, 5-min intervals
./ui isp metrics --hours 48     # Custom range
./ui isp metrics -o csv         # Export
```

**Fields:** latency (avg/max), speeds, uptime, packet loss, ISP name

### SD-WAN

```bash
./ui sdwan list              # All configs
./ui sdwan get ID            # Config details
./ui sdwan status ID         # Deployment status
```

---

## Local Controller

Direct connection to your controller. Use `./ui local` or `./ui lo`.

### List Clients

```bash
./ui lo clients list             # Connected clients
./ui lo clients list -w          # Wired only
./ui lo clients list -W          # Wireless only
./ui lo clients list -n "Guest"  # By network
./ui lo clients list -v          # Verbose
./ui lo clients all              # Include offline
```

**Output:**
```
                         Connected Clients
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃ Name         ┃ MAC               ┃ IP         ┃ Network ┃ Type     ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ my-MacBook   │ AA:BB:CC:DD:EE:FF │ 10.0.1.50  │ Home    │ Wireless │
│ Smart-TV     │ 11:22:33:44:55:66 │ 10.0.1.100 │ Home    │ Wired    │
└──────────────┴───────────────────┴────────────┴─────────┴──────────┘
```

### Client Details

```bash
./ui lo clients get my-MacBook         # By name
./ui lo clients get AA:BB:CC:DD:EE:FF  # By MAC
./ui lo clients get MacBook            # Partial match
./ui lo clients status my-MacBook      # Full status
```

**Status output:**
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

| Field | Meaning |
|-------|---------|
| Signal | dBm (green >-50, yellow -50 to -70, red <-70) |
| Channel | WiFi channel + protocol (AC=WiFi 5, AX=WiFi 6) |
| Experience | UniFi satisfaction (green >80%, yellow 50-80%, red <50%) |

### Client Actions

```bash
./ui lo clients block my-MacBook      # Block (with confirmation)
./ui lo clients unblock my-MacBook    # Unblock
./ui lo clients kick my-MacBook       # Disconnect
./ui lo clients block my-MacBook -y   # Skip confirmation
```

### Client Statistics

```bash
./ui lo clients count                 # By type
./ui lo clients count --by network    # By SSID
./ui lo clients count --by vendor     # By manufacturer
./ui lo clients count --by ap         # By access point
./ui lo clients count --by experience # By WiFi quality
./ui lo clients count -a              # Include offline
```

### Find Duplicates

Identifies devices with multiple NICs or naming conflicts.

```bash
./ui lo clients duplicates
```

```
Found 2 duplicate name(s):

my-MacBook (2 NICs) ← likely same device
  • AA:BB:CC:DD:EE:FF (10.0.1.50) wifi - Apple, Inc.
  • 11:22:33:44:55:66 (10.0.1.51) wired - Apple, Inc.

iPad (3 clients)
  • 22:33:44:55:66:77 (10.0.1.60) wifi - Apple, Inc.
  • 33:44:55:66:77:88 (10.0.1.61) wifi - Apple, Inc.
  • 44:55:66:77:88:99 (10.0.1.62) wifi - Apple, Inc.
```

---

## Running Config

Export your network configuration for backup, documentation, or version control.

### Full Config

```bash
./ui lo config show              # All sections, table format
./ui lo config show -o yaml      # YAML export
./ui lo config show -o json      # JSON export
./ui lo config show -v           # Include IDs
./ui lo config show --show-secrets  # Include passwords
```

### Specific Sections

```bash
./ui lo config show -s networks      # VLANs, subnets, DHCP
./ui lo config show -s wireless      # SSIDs, security, bands
./ui lo config show -s firewall      # Rules and groups
./ui lo config show -s devices       # Device inventory
./ui lo config show -s portfwd       # Port forwarding
./ui lo config show -s dhcp          # DHCP reservations
./ui lo config show -s routing       # Static routes
```

### Example Output

```
UniFi Running Configuration
══════════════════════════════════════════════════════════════════════
Controller: https://192.168.1.1
Site: default
Exported: 2024-11-30 10:45:23
══════════════════════════════════════════════════════════════════════

┌─ NETWORKS ──────────────────────────────────────────────────────────┐

  Default
    Purpose:       corporate
    Subnet:        10.0.1.0/24
    Gateway:       10.0.1.1
    DHCP:          Enabled (10.0.1.100 - 10.0.1.254)
    DNS:           10.0.1.1, 1.1.1.1

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
    PMF:           optional

  IoT-Network
    Network:       IoT
    Security:      WPA2 Personal
    Band:          2.4 GHz only
    Hidden:        Yes

└──────────────────────────────────────────────────────────────────────┘

┌─ DEVICES ───────────────────────────────────────────────────────────┐

  UDM-SE (Gateway) online
    IP:            192.168.1.1
    MAC:           AA:BB:CC:DD:EE:01
    Firmware:      4.0.6
    Uptime:        45d 12h

  Living-Room-AP (U6-Pro) online
    IP:            10.0.1.10
    Firmware:      6.6.55
    Channel 2.4G:  6 (HT40)
    Channel 5G:    36 (VHT80)

└──────────────────────────────────────────────────────────────────────┘

Summary: 2 networks, 2 SSIDs, 0 firewall rules, 2 devices
```

### Backup to YAML

```bash
./ui lo config show -o yaml > backup-$(date +%Y%m%d).yaml
```

---

## Output Formats

All commands support multiple formats via `-o`:

| Format | Flag | Use Case |
|--------|------|----------|
| Table | (default) | Human reading |
| JSON | `-o json` | Scripting, APIs |
| CSV | `-o csv` | Spreadsheets |
| YAML | `-o yaml` | Config backup (config command only) |

### JSON with jq

```bash
# Count items
./ui devices list -o json | jq 'length'

# Filter offline
./ui devices list -o json | jq '[.[] | select(.status == "offline")]'

# Extract field
./ui lo clients list -o json | jq -r '.[].ip'

# Pretty names
./ui devices list -o json | jq -r '.[].name'
```

### CSV Export

```bash
./ui devices list -o csv > devices.csv
./ui lo clients list -o csv > clients.csv
./ui isp metrics -o csv > isp-metrics.csv
```

---

## Quick Reference

### Cloud Commands

| Command | Description |
|---------|-------------|
| `./ui status` | API connection status |
| `./ui hosts list` | List controllers |
| `./ui sites list` | List sites |
| `./ui devices list` | List devices |
| `./ui devices count --by X` | Count by model/status/host |
| `./ui isp metrics` | ISP performance |
| `./ui sdwan list` | SD-WAN configs |

### Local Commands

| Command | Description |
|---------|-------------|
| `./ui lo clients list` | Connected clients |
| `./ui lo clients all` | All clients (inc. offline) |
| `./ui lo clients get NAME` | Client details |
| `./ui lo clients status NAME` | Full client status |
| `./ui lo clients block NAME` | Block client |
| `./ui lo clients kick NAME` | Disconnect client |
| `./ui lo clients count --by X` | Count by type/network/vendor/ap |
| `./ui lo clients duplicates` | Find duplicate names |
| `./ui lo config show` | Running configuration |
| `./ui lo config show -s X` | Specific section |

### Common Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Format: table/json/csv/yaml |
| `--verbose` | `-v` | More details |
| `--yes` | `-y` | Skip confirmation |
| `--help` | | Show help |

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| API key not configured | Add `UNIFI_API_KEY` to `.env` |
| Invalid API key | Check at unifi.ui.com → Settings → API |
| Connection timeout | Check internet / `api.ui.com` access |
| Controller URL not configured | Add `UNIFI_CONTROLLER_URL` to `.env` |
| Invalid username or password | Test creds in UniFi web UI; use local admin account |
| SSL certificate verify failed | Set `UNIFI_CONTROLLER_VERIFY_SSL=false` |
| Client not found | Try partial name or use MAC address |
| Session expired | Delete `~/.config/ui-cli/session.json` |

### Get Help

```bash
./ui --help                    # All commands
./ui devices --help            # Device commands
./ui lo clients --help         # Client commands
./ui lo config show --help     # Config options
```

---

## Tips

### Shell Aliases

```bash
# Add to .bashrc or .zshrc
alias ui='./ui'
alias clients='./ui lo clients'
alias config='./ui lo config show'
```

### Scripting Examples

```bash
# Check API health
./ui status -o json | jq -e '.authentication == "Valid"'

# Alert on offline devices
OFFLINE=$(./ui devices count -b status -o json | jq '.counts.offline // 0')
[ "$OFFLINE" -gt 0 ] && echo "Warning: $OFFLINE offline"

# Daily backup
./ui lo config show -o yaml > "config-$(date +%Y%m%d).yaml"

# Find device by partial name
./ui lo clients list -o json | jq '.[] | select(.name | test("iPhone"; "i"))'
```

### Quick Lookups

```bash
# Find any iPhone
./ui lo clients list | grep -i iphone

# Status by partial name
./ui lo clients status iphone

# Who's on Guest network
./ui lo clients list -n Guest
```

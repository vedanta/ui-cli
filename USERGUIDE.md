# UniFi CLI User Guide

Complete reference for managing UniFi networks from the command line.

---

## Table of Contents

- [Setup](#setup)
- [Cloud API](#cloud-api)
- [Local Controller](#local-controller)
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

### Clients

#### List Clients

```bash
./ui lo clients list             # Connected clients
./ui lo clients list -w          # Wired only
./ui lo clients list -W          # Wireless only
./ui lo clients list -n "Guest"  # By network
./ui lo clients list -v          # Verbose
./ui lo clients all              # Include offline
```

#### Client Details

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

#### Client Actions

```bash
./ui lo clients block my-MacBook      # Block (with confirmation)
./ui lo clients unblock my-MacBook    # Unblock
./ui lo clients kick my-MacBook       # Disconnect
./ui lo clients block my-MacBook -y   # Skip confirmation
```

#### Client Statistics

```bash
./ui lo clients count                 # By type
./ui lo clients count --by network    # By SSID
./ui lo clients count --by vendor     # By manufacturer
./ui lo clients count --by ap         # By access point
./ui lo clients count --by experience # By WiFi quality
./ui lo clients count -a              # Include offline
```

#### Find Duplicates

```bash
./ui lo clients duplicates
```

---

### Health & Monitoring

#### Site Health

```bash
./ui lo health                   # Health summary
./ui lo health -v                # Verbose details
```

Shows status of WAN, LAN, WLAN, and VPN subsystems.

#### Events

```bash
./ui lo events list              # Recent events
./ui lo events list -l 50        # Last 50 events
./ui lo events list -v           # Verbose
```

---

### Networks

```bash
./ui lo networks list            # All networks
./ui lo networks list -v         # With details (DHCP, VLAN)
```

---

### Devices (Local)

#### List & Get

```bash
./ui lo devices list                      # All devices
./ui lo devices list -v                   # Verbose (channels, load)
./ui lo devices get UDM-Pro               # By name
./ui lo devices get 70:a7:41:xx:xx:xx     # By MAC
./ui lo devices get device-001            # By ID
```

#### Device Actions

```bash
./ui lo devices restart UDM-Pro           # Restart device
./ui lo devices restart UDM-Pro -y        # Skip confirmation
./ui lo devices upgrade Living-Room-AP    # Upgrade firmware
./ui lo devices locate Office-AP          # Enable locate LED
./ui lo devices locate Office-AP --off    # Disable locate LED
./ui lo devices adopt 70:a7:41:xx:xx:xx   # Adopt new device
```

---

### Firewall & Security

#### Firewall Rules

```bash
./ui lo firewall list                     # All rules
./ui lo firewall list --ruleset WAN_IN    # Filter by ruleset
./ui lo firewall list -v                  # Verbose
```

#### Firewall Groups

```bash
./ui lo firewall groups                   # Address/port groups
./ui lo firewall groups -v                # Show group members
```

#### Port Forwarding

```bash
./ui lo portfwd list                      # All port forwards
./ui lo portfwd list -v                   # Verbose
```

---

### Guest Vouchers

#### List Vouchers

```bash
./ui lo vouchers list                     # All vouchers
./ui lo vouchers list -v                  # With details
```

#### Create Vouchers

```bash
./ui lo vouchers create                   # Single voucher, 24h
./ui lo vouchers create -c 10             # Create 10 vouchers
./ui lo vouchers create -d 60             # 60 minute duration
./ui lo vouchers create -q 1024           # 1GB data limit
./ui lo vouchers create --up 5000         # 5Mbps upload limit
./ui lo vouchers create --down 10000      # 10Mbps download limit
./ui lo vouchers create -n "Event"        # Add note
```

#### Delete Vouchers

```bash
./ui lo vouchers delete 12345-67890       # Delete by code
./ui lo vouchers delete 12345-67890 -y    # Skip confirmation
```

---

### DPI (Deep Packet Inspection)

#### Site DPI Stats

```bash
./ui lo dpi stats                         # Top applications
./ui lo dpi stats -l 20                   # Top 20
./ui lo dpi stats -v                      # Verbose
```

#### Client DPI

```bash
./ui lo dpi client my-MacBook             # By name
./ui lo dpi client AA:BB:CC:DD:EE:FF      # By MAC
```

**Note:** DPI must be enabled in your controller settings. If disabled, the command will show an unavailable message.

---

### Statistics

#### Daily Stats

```bash
./ui lo stats daily                       # Last 30 days
./ui lo stats daily --days 7              # Last 7 days
./ui lo stats daily -o csv                # Export to CSV
```

#### Hourly Stats

```bash
./ui lo stats hourly                      # Last 24 hours
./ui lo stats hourly --hours 48           # Last 48 hours
```

**Fields:** Date, WAN RX/TX, client count

---

### Running Config

Export your network configuration for backup or documentation.

#### Full Config

```bash
./ui lo config show              # All sections, table format
./ui lo config show -o yaml      # YAML export
./ui lo config show -o json      # JSON export
./ui lo config show -v           # Include IDs
./ui lo config show --show-secrets  # Include passwords
```

#### Specific Sections

```bash
./ui lo config show -s networks      # VLANs, subnets, DHCP
./ui lo config show -s wireless      # SSIDs, security, bands
./ui lo config show -s firewall      # Rules and groups
./ui lo config show -s devices       # Device inventory
./ui lo config show -s portfwd       # Port forwarding
./ui lo config show -s dhcp          # DHCP reservations
./ui lo config show -s routing       # Static routes
```

#### Backup to YAML

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
| `./ui lo health` | Site health status |
| `./ui lo clients list` | Connected clients |
| `./ui lo clients get NAME` | Client details |
| `./ui lo clients status NAME` | Full client status |
| `./ui lo clients block NAME` | Block client |
| `./ui lo clients count --by X` | Count by type/network/vendor |
| `./ui lo devices list` | Network devices |
| `./ui lo devices restart NAME` | Restart device |
| `./ui lo devices locate NAME` | Toggle locate LED |
| `./ui lo networks list` | Networks/VLANs |
| `./ui lo events list` | Recent events |
| `./ui lo firewall list` | Firewall rules |
| `./ui lo portfwd list` | Port forwards |
| `./ui lo vouchers list` | Guest vouchers |
| `./ui lo vouchers create` | Create voucher |
| `./ui lo dpi stats` | DPI statistics |
| `./ui lo stats daily` | Daily traffic stats |
| `./ui lo stats hourly` | Hourly traffic stats |
| `./ui lo config show` | Running configuration |

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
| DPI unavailable | Enable DPI in controller settings |

### Get Help

```bash
./ui --help                    # All commands
./ui devices --help            # Device commands
./ui lo --help                 # Local commands
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

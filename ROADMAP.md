# UniFi CLI Roadmap

## Milestone 1: Site Manager API (COMPLETE)

Cloud-based API via `api.ui.com` using API key authentication.

### Commands
- `./ui hosts list` - List all hosts
- `./ui hosts get <ID>` - Get host details
- `./ui sites list` - List all sites
- `./ui devices list` - List all devices
- `./ui devices count` - Count devices with grouping
- `./ui isp metrics` - ISP performance metrics
- `./ui sdwan list` - List SD-WAN configs
- `./ui sdwan get <ID>` - Get SD-WAN config
- `./ui sdwan status <ID>` - Get SD-WAN status

### Output Formats
All commands support: `--output table|json|csv`

---

## Milestone 2: Local Controller API (IN PROGRESS)

Direct connection to UniFi Controller (UDM, Cloud Key, self-hosted) using username/password authentication.

All commands prefixed with `./ui local` (or `./ui lo` shorthand) to distinguish from cloud API.

### Configuration

**.env additions:**
```bash
# Local Controller (for ./ui local commands)
UNIFI_CONTROLLER_URL=https://192.168.0.1
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword
UNIFI_CONTROLLER_SITE=default
UNIFI_CONTROLLER_VERIFY_SSL=false
```

### Phase 2.1 - Clients ✅ COMPLETE

| Command | Description |
|---------|-------------|
| `./ui lo clients list` | List active connected clients |
| `./ui lo clients all` | List all known clients (including offline) |
| `./ui lo clients get <name\|MAC>` | Get details for specific client |
| `./ui lo clients status <name\|MAC>` | Show comprehensive client status |
| `./ui lo clients block <name\|MAC>` | Block a client (with confirmation) |
| `./ui lo clients unblock <name\|MAC>` | Unblock a client (with confirmation) |
| `./ui lo clients kick <name\|MAC>` | Disconnect client (with confirmation) |
| `./ui lo clients count` | Count clients by category |
| `./ui lo clients duplicates` | Find clients with duplicate names |

**Switches for `clients list`:**
| Switch | Short | Description |
|--------|-------|-------------|
| `--network` | `-n` | Filter by network/SSID |
| `--wired` | `-w` | Show only wired clients |
| `--wireless` | `-W` | Show only wireless clients |
| `--verbose` | `-v` | Show additional details |
| `--output` | `-o` | Output format (table/json/csv) |

**Switches for `clients count`:**
| Switch | Short | Description |
|--------|-------|-------------|
| `--by` | `-b` | Group by: type, network, vendor, ap, experience |
| `--include-offline` | `-a` | Include offline clients in count |

**Switches for `block/unblock/kick`:**
| Switch | Short | Description |
|--------|-------|-------------|
| `--yes` | `-y` | Skip confirmation prompt |

**Features:**
- Name or MAC address lookup for all client commands
- Partial name matching with disambiguation
- Comprehensive status display (signal, experience, speed, data usage, uptime)
- Multi-NIC device detection in duplicates command
- Color-coded signal strength and experience scores

### Phase 2.2 - Monitoring

| Command | Description |
|---------|-------------|
| `./ui local events list` | List recent events |
| `./ui local alarms list` | List alarms |
| `./ui local alarms archive <ID>` | Archive an alarm |
| `./ui local health` | Show site health summary |

### Phase 2.3 - Guest Management

| Command | Description |
|---------|-------------|
| `./ui local vouchers list` | List all vouchers |
| `./ui local vouchers create` | Create new voucher(s) |
| `./ui local vouchers revoke <ID>` | Revoke a voucher |

**Switches for `vouchers create`:**
| Switch | Short | Description |
|--------|-------|-------------|
| `--count` | `-c` | Number of vouchers to create |
| `--duration` | `-d` | Duration in minutes |
| `--quota` | `-q` | Data quota in MB (0=unlimited) |
| `--up` | | Upload limit kbps |
| `--down` | | Download limit kbps |
| `--note` | `-n` | Note/description |

### Phase 2.4 - Network Info

| Command | Description |
|---------|-------------|
| `./ui local networks list` | List all networks (VLANs, WiFi) |
| `./ui local networks get <ID>` | Get network details |
| `./ui local dpi site` | Site-level DPI stats |
| `./ui local dpi client <MAC>` | Client-specific DPI stats |

### Phase 2.5 - Security & Firewall

| Command | Description |
|---------|-------------|
| `./ui local firewall list` | List firewall rules |
| `./ui local firewall groups` | List firewall groups |
| `./ui local portfwd list` | List port forwarding rules |

### Phase 2.6 - Device Commands

| Command | Description |
|---------|-------------|
| `./ui local devices list` | List devices (local API version) |
| `./ui local devices restart <MAC>` | Restart a device |
| `./ui local devices upgrade <MAC>` | Upgrade device firmware |
| `./ui local devices locate <MAC>` | Enable locate LED |

### Phase 2.7 - Statistics

| Command | Description |
|---------|-------------|
| `./ui local stats daily` | Daily site statistics |
| `./ui local stats hourly` | Hourly site statistics |

---

## Implementation Notes

### Controller Type Detection
- **UDM/UCG**: Uses `/proxy/network/api/s/{site}/` prefix
- **Cloud Key / Self-hosted**: Uses `/api/s/{site}/` prefix
- Auto-detect or configure via `UNIFI_CONTROLLER_TYPE`

### Session Management
- Login returns session cookie
- Store session in `~/.config/ui-cli/session.json`
- Auto re-login on session expiry

### SSL Handling
- Most controllers use self-signed certs
- `UNIFI_CONTROLLER_VERIFY_SSL=false` to disable verification

---

## Files (Milestone 2)

| File | Purpose | Status |
|------|---------|--------|
| `src/ui_cli/local_client.py` | Local controller API client | ✅ |
| `src/ui_cli/commands/local/__init__.py` | Local command group | ✅ |
| `src/ui_cli/commands/local/clients.py` | Client commands | ✅ |
| `src/ui_cli/commands/local/events.py` | Events/alarms commands | Planned |
| `src/ui_cli/commands/local/vouchers.py` | Voucher commands | Planned |
| `src/ui_cli/commands/local/networks.py` | Network commands | Planned |
| `src/ui_cli/commands/local/firewall.py` | Firewall commands | Planned |
| `src/ui_cli/commands/local/dpi.py` | DPI stats commands | Planned |
| `src/ui_cli/commands/local/devices.py` | Local device commands | Planned |
| `src/ui_cli/commands/local/stats.py` | Statistics commands | Planned |

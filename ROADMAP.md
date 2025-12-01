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

## Milestone 2: Local Controller API (COMPLETE)

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

### Phase 2.1 - Clients (COMPLETE)

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

### Phase 2.2 - Monitoring (COMPLETE)

| Command | Description |
|---------|-------------|
| `./ui lo events list` | List recent events |
| `./ui lo health` | Show site health summary |

### Phase 2.3 - Guest Management (COMPLETE)

| Command | Description |
|---------|-------------|
| `./ui lo vouchers list` | List all vouchers |
| `./ui lo vouchers create` | Create new voucher(s) |
| `./ui lo vouchers delete <CODE>` | Delete a voucher |

### Phase 2.4 - Network Info & DPI (COMPLETE)

| Command | Description |
|---------|-------------|
| `./ui lo networks list` | List all networks (VLANs, WiFi) |
| `./ui lo dpi stats` | Site-level DPI stats |
| `./ui lo dpi client <MAC>` | Client-specific DPI stats |

### Phase 2.5 - Security & Firewall (COMPLETE)

| Command | Description |
|---------|-------------|
| `./ui lo firewall list` | List firewall rules |
| `./ui lo firewall groups` | List firewall groups |
| `./ui lo portfwd list` | List port forwarding rules |

### Phase 2.6 - Device Commands (COMPLETE)

| Command | Description |
|---------|-------------|
| `./ui lo devices list` | List devices (local API) |
| `./ui lo devices get <ID\|MAC\|name>` | Get device details |
| `./ui lo devices restart <ID\|MAC\|name>` | Restart a device |
| `./ui lo devices upgrade <ID\|MAC\|name>` | Upgrade device firmware |
| `./ui lo devices locate <ID\|MAC\|name>` | Toggle locate LED |
| `./ui lo devices adopt <MAC>` | Adopt a device |

### Phase 2.7 - Statistics (COMPLETE)

| Command | Description |
|---------|-------------|
| `./ui lo stats daily` | Daily site statistics |
| `./ui lo stats hourly` | Hourly site statistics |

---

## Milestone 3: Advanced Features (PLANNED)

### Phase 3.1 - Backup & Restore
| Command | Description |
|---------|-------------|
| `./ui lo backup create` | Create site backup |
| `./ui lo backup list` | List available backups |
| `./ui lo backup download <ID>` | Download backup file |

### Phase 3.2 - Notifications & Alerts
| Command | Description |
|---------|-------------|
| `./ui lo alarms list` | List active alarms |
| `./ui lo alarms archive <ID>` | Archive an alarm |
| `./ui lo alarms archive-all` | Archive all alarms |

### Phase 3.3 - Advanced Configuration
| Command | Description |
|---------|-------------|
| `./ui lo wlan list` | List wireless networks |
| `./ui lo wlan create` | Create wireless network |
| `./ui lo wlan delete <ID>` | Delete wireless network |
| `./ui lo network create` | Create network/VLAN |

### Phase 3.4 - Multi-Site Management
| Command | Description |
|---------|-------------|
| `./ui lo sites list` | List sites on controller |
| `./ui lo sites switch <name>` | Switch active site |

---

## Implementation Notes

### Controller Type Detection
- **UDM/UCG**: Uses `/proxy/network/api/s/{site}/` prefix
- **Cloud Key / Self-hosted**: Uses `/api/s/{site}/` prefix
- Auto-detected on first connection

### Session Management
- Login returns session cookie
- Session stored in `~/.config/ui-cli/session.json`
- Auto re-login on session expiry

### SSL Handling
- Most controllers use self-signed certs
- `UNIFI_CONTROLLER_VERIFY_SSL=false` to disable verification

---

## Files

| File | Purpose | Status |
|------|---------|--------|
| `src/ui_cli/client.py` | Site Manager API client | Complete |
| `src/ui_cli/local_client.py` | Local Controller API client | Complete |
| `src/ui_cli/commands/local/__init__.py` | Local command group | Complete |
| `src/ui_cli/commands/local/clients.py` | Client commands | Complete |
| `src/ui_cli/commands/local/config.py` | Running config export | Complete |
| `src/ui_cli/commands/local/events.py` | Events commands | Complete |
| `src/ui_cli/commands/local/vouchers.py` | Voucher commands | Complete |
| `src/ui_cli/commands/local/networks.py` | Network commands | Complete |
| `src/ui_cli/commands/local/firewall.py` | Firewall commands | Complete |
| `src/ui_cli/commands/local/portfwd.py` | Port forward commands | Complete |
| `src/ui_cli/commands/local/dpi.py` | DPI stats commands | Complete |
| `src/ui_cli/commands/local/devices.py` | Local device commands | Complete |
| `src/ui_cli/commands/local/stats.py` | Statistics commands | Complete |
| `src/ui_cli/commands/local/health.py` | Health commands | Complete |
| `tests/` | Test suite (87 tests) | Complete |

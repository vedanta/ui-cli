# MCP Server v2 - Tools Layer Architecture

## Overview

Rewrite the MCP server as a thin tools layer that calls the UI CLI via subprocess. This ensures consistent behavior, single source of truth, and easier debugging.

## Architecture

```
┌─────────────────┐
│  Claude Desktop │
└────────┬────────┘
         │ MCP Protocol (stdio)
         ▼
┌─────────────────┐
│   Tools Layer   │  ← 15 well-defined tools
│   (ui_mcp/v2/)  │  ← Friendly names, chat-optimized
└────────┬────────┘
         │ subprocess.run("./ui ...")
         ▼
┌─────────────────┐
│    UI CLI       │  ← All logic, formatting, error handling
│   (ui_cli/)     │
└─────────────────┘
```

## Design Principles

1. **CLI is the source of truth** - MCP tools just call CLI commands
2. **Friendly tool names** - `network_health` not `unifi_lo_health`
3. **Chat-optimized output** - Use `--json` and format for readability
4. **Lightweight responses** - Prefer counts/summaries over full lists
5. **Safe by default** - Read-only tools, actions clearly named

## Tools Specification

### Category 1: Status & Health (Read-only)

| Tool | CLI Command | Description |
|------|-------------|-------------|
| `network_status` | `./ui status` | Check API connectivity |
| `network_health` | `./ui lo health -o json` | Site health summary |
| `internet_speed` | `./ui speedtest -o json` | Last speed test result |
| `run_speedtest` | `./ui speedtest -r -o json` | Run new speed test |
| `isp_performance` | `./ui isp metrics -o json` | ISP metrics (7 days) |

### Category 2: Counts & Summaries (Read-only)

| Tool | CLI Command | Description |
|------|-------------|-------------|
| `client_count` | `./ui lo clients count -o json` | Device counts by type |
| `device_list` | `./ui lo devices list -o json` | UniFi infrastructure |
| `network_list` | `./ui lo networks -o json` | Networks and VLANs |

### Category 3: Lookups (Read-only)

| Tool | CLI Command | Description |
|------|-------------|-------------|
| `find_client` | `./ui lo clients get <name> -o json` | Find device by name |
| `find_device` | `./ui lo devices get <name> -o json` | Find UniFi device |
| `client_status` | `./ui lo clients status <name> -o json` | Check if blocked |

### Category 4: Actions (Mutating)

| Tool | CLI Command | Description |
|------|-------------|-------------|
| `block_client` | `./ui lo clients block <name>` | Block from network |
| `unblock_client` | `./ui lo clients unblock <name>` | Restore access |
| `kick_client` | `./ui lo clients kick <name>` | Force disconnect |
| `restart_device` | `./ui lo devices restart <name>` | Reboot device |
| `create_voucher` | `./ui lo vouchers create` | Guest WiFi code |

## Implementation Plan

### Phase 1: Foundation
- [ ] Create `src/ui_mcp/v2/` directory structure
- [ ] Implement `cli_runner.py` - subprocess wrapper with timeout, error handling
- [ ] Implement `server.py` - FastMCP server with tool registration
- [ ] Add `--json` output to CLI commands that don't have it

### Phase 2: Read-only Tools (8 tools)
- [ ] `network_status`
- [ ] `network_health`
- [ ] `internet_speed`
- [ ] `isp_performance`
- [ ] `client_count`
- [ ] `device_list`
- [ ] `network_list`
- [ ] `find_client`

### Phase 3: Lookup & Action Tools (7 tools)
- [ ] `find_device`
- [ ] `client_status`
- [ ] `block_client`
- [ ] `unblock_client`
- [ ] `kick_client`
- [ ] `restart_device`
- [ ] `create_voucher`

### Phase 4: Polish
- [ ] Update `./ui mcp install` to use v2
- [ ] Remove old MCP server code
- [ ] Update documentation
- [ ] Test all tools in Claude Desktop

## File Structure

```
src/ui_mcp/
├── __init__.py
├── __main__.py          # Entry point (updated for v2)
├── v2/
│   ├── __init__.py
│   ├── server.py        # FastMCP server + tool definitions
│   ├── cli_runner.py    # Subprocess wrapper
│   └── tools/
│       ├── __init__.py
│       ├── status.py    # network_status, network_health, internet_speed
│       ├── clients.py   # client_count, find_client, block/unblock/kick
│       ├── devices.py   # device_list, find_device, restart_device
│       └── network.py   # network_list, isp_performance, create_voucher
```

## CLI Runner Design

```python
# cli_runner.py
import subprocess
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

def run_cli(args: list[str], timeout: int = 30) -> dict:
    """Run UI CLI command and return parsed JSON output.

    Args:
        args: Command arguments (e.g., ["lo", "health", "-o", "json"])
        timeout: Command timeout in seconds

    Returns:
        Parsed JSON output or error dict
    """
    cmd = ["./ui"] + args

    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            return {
                "error": True,
                "message": result.stderr.strip() or "Command failed",
                "exit_code": result.returncode,
            }

        # Try to parse as JSON
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            # Return raw output if not JSON
            return {"output": result.stdout.strip()}

    except subprocess.TimeoutExpired:
        return {"error": True, "message": f"Command timed out after {timeout}s"}
    except Exception as e:
        return {"error": True, "message": str(e)}
```

## Tool Definition Pattern

```python
# tools/status.py
from ..cli_runner import run_cli

async def network_health() -> str:
    """Get network health status.

    Returns health status for WAN, LAN, WLAN subsystems.
    """
    result = run_cli(["lo", "health", "-o", "json"])

    if result.get("error"):
        return json.dumps(result)

    # Format for chat
    summary = format_health_summary(result)
    return json.dumps({
        "summary": summary,
        "details": result,
    })
```

## Migration Strategy

1. Build v2 in parallel (`ui_mcp/v2/`)
2. Test thoroughly before switching
3. Update `__main__.py` to use v2
4. Keep v1 code until v2 is stable
5. Remove v1 after confirmation

## Success Criteria

- [ ] All 15 tools work in Claude Desktop
- [ ] Response times < 5 seconds
- [ ] Output displays correctly (no "no output" issues)
- [ ] Error messages are helpful
- [ ] Actions (block, restart) work reliably

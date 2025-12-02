# MCP Server Architecture

## Design Principles

### 1. CLI as Source of Truth

The MCP server is a **thin wrapper** around the UI CLI. All business logic, API calls, and formatting live in the CLI. This ensures:

- Consistent behavior between terminal and Claude Desktop
- Single place to fix bugs
- Easy to test (just run the CLI)

### 2. Friendly Tool Names

Tools use natural names that map to user intent:

| User Intent | Tool Name | CLI Command |
|-------------|-----------|-------------|
| "How many clients?" | `client_count` | `./ui lo clients count` |
| "Block a device" | `block_client` | `./ui lo clients block` |
| "Network health" | `network_health` | `./ui lo health` |

### 3. Structured Responses

All tools return JSON with a consistent structure:

```json
{
  "summary": "Human-readable one-liner for Claude",
  "data": { ... },
  "count": 10
}
```

This helps Claude generate natural responses without dumping raw JSON.

## Component Details

### FastMCP Server (`server.py`)

```python
from mcp.server.fastmcp import FastMCP

server = FastMCP(
    "ui-cli",
    instructions="Manage UniFi network infrastructure"
)

@server.tool()
async def network_health() -> str:
    """Tool docstring becomes the description Claude sees."""
    result = run_cli(["lo", "health"])
    return format_result(result, "Health summary")
```

Key points:
- Uses official Anthropic MCP SDK (`mcp.server.fastmcp`)
- Tools are async but call sync subprocess
- Returns JSON strings (FastMCP requirement)
- Docstrings are shown to Claude as tool descriptions

### CLI Runner (`cli_runner.py`)

```python
def run_cli(args: list[str], timeout: int = 30) -> dict:
    """Execute UI CLI and return parsed JSON."""

    # Use same Python as MCP server (conda env)
    python_path = sys.executable
    cmd = [python_path, "-m", "ui_cli.main"] + args

    # Auto-add JSON output flag
    if "-o" not in args:
        cmd.extend(["-o", "json"])

    # Auto-add -y for actions (skip confirmation)
    if any(action in args for action in ["block", "restart"]):
        cmd.append("-y")

    result = subprocess.run(cmd, capture_output=True, ...)
    return json.loads(result.stdout)
```

Key points:
- Uses `sys.executable` to ensure correct conda Python
- Auto-adds `--output json` flag
- Auto-adds `-y` flag for action commands
- Handles timeouts and errors gracefully

### Entry Point (`__main__.py`)

```python
from ui_mcp.server import main

if __name__ == "__main__":
    main()
```

Allows running as: `python -m ui_mcp`

### Wrapper Script (`scripts/mcp-server.sh`)

```bash
#!/bin/bash
# Load .env for credentials
source .env

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT/src"

# Run with specified Python
exec "$PYTHON" -m ui_mcp "$@"
```

Claude Desktop calls this script, which:
1. Changes to project directory
2. Loads `.env` file (API credentials)
3. Sets `PYTHONPATH` for imports
4. Runs the MCP server

## Data Flow

### Read Operation (e.g., `client_count`)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Claude    │     │  FastMCP    │     │ CLI Runner  │     │   UI CLI    │
│   Desktop   │     │  Server     │     │             │     │             │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │ MCP: client_count │                   │                   │
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │                   │ run_cli(["lo",    │                   │
       │                   │  "clients","count"])                  │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │                   │ subprocess:       │
       │                   │                   │ python -m ui_cli  │
       │                   │                   │ lo clients count  │
       │                   │                   │ -o json           │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │                   │   {"counts":      │
       │                   │                   │    {"Wired":17,   │
       │                   │                   │     "Wireless":70}│
       │                   │                   │<──────────────────│
       │                   │                   │                   │
       │                   │ {"summary": "...",│                   │
       │                   │  "counts": {...}} │                   │
       │                   │<──────────────────│                   │
       │                   │                   │                   │
       │ {"summary":       │                   │                   │
       │  "Total: 87..."}  │                   │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
```

### Write Operation (e.g., `block_client`)

Same flow, but:
1. CLI Runner adds `-y` flag to skip confirmation
2. CLI returns `{"success": true, "action": "blocked", ...}`
3. Summary becomes "Blocked client: iPhone"

## Error Handling

### CLI Errors

```python
# CLI returns non-zero exit code
{
    "error": True,
    "message": "Client not found: xyz",
    "exit_code": 1
}
```

### Timeout Errors

```python
# Command exceeds timeout
{
    "error": True,
    "message": "Command timed out after 30s"
}
```

### API Errors

```python
# UniFi API returns error
{
    "error": True,
    "message": "Authentication failed: Invalid API key"
}
```

All errors include `"error": True` so Claude can respond appropriately.

## Security Considerations

### Credentials

- Stored in `.env` file (not in repo)
- Loaded by wrapper script before MCP server starts
- Never exposed in tool responses

### Action Confirmation

- CLI normally prompts for confirmation on destructive actions
- MCP server adds `-y` flag to skip prompts
- Claude should confirm with user before calling action tools

### Network Access

- Local controller access via HTTPS (self-signed cert OK)
- Cloud API access via `api.ui.com`
- No inbound connections required

## Performance

### Typical Response Times

| Operation | Time |
|-----------|------|
| `network_health` | ~500ms |
| `client_count` | ~800ms |
| `device_list` | ~1s |
| `run_speedtest` | 30-60s |

### Optimization

- CLI caches controller connection
- JSON output avoids table rendering overhead
- Subprocess overhead is minimal (~50ms)

## Future Improvements

1. **Caching** - Cache expensive queries like device list
2. **Streaming** - Stream progress for long operations
3. **Batch operations** - Block/unblock multiple clients
4. **Webhooks** - React to network events

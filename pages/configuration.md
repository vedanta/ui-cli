# Configuration

UI-CLI uses environment variables for configuration. Create a `.env` file in the project root.

## Quick Setup

```bash
cp .env.example .env
# Edit .env with your credentials
```

## Cloud API Configuration

For commands that use the UniFi Site Manager API (`api.ui.com`).

```bash
# Required: Your API key
UNIFI_API_KEY=your-api-key-here

# Optional: API base URL (default: https://api.ui.com/v1)
UNIFI_API_URL=https://api.ui.com/v1

# Optional: Request timeout in seconds (default: 30)
UNIFI_TIMEOUT=30
```

### Getting Your API Key

1. Go to [unifi.ui.com](https://unifi.ui.com)
2. Navigate to **Settings** → **API**
3. Click **Create API Key**
4. Copy the key immediately (it's only shown once!)

!!! warning "API Key Security"
    Never commit your `.env` file to version control. It's already in `.gitignore`.

## Local Controller Configuration

For commands that connect directly to your UniFi Controller.

```bash
# Required: Controller URL
UNIFI_CONTROLLER_URL=https://192.168.1.1

# Required: Credentials
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword

# Optional: TOTP code for MFA-enabled accounts (UDM-style controllers only)
# Codes expire in ~30s; only needed for the initial login since the
# session is cached for ~24 hours afterwards.
UNIFI_CONTROLLER_TOTP=123456

# Optional: Site name (default: "default")
UNIFI_CONTROLLER_SITE=default

# Optional: SSL verification (default: false)
UNIFI_CONTROLLER_VERIFY_SSL=false
```

### Controller Types

UI-CLI automatically detects your controller type:

| Controller | API Path |
|------------|----------|
| UDM / UDM Pro / UDM SE | `/proxy/network/api/s/{site}/` |
| Cloud Key / Self-hosted | `/api/s/{site}/` |

### SSL Certificates

Most UniFi controllers use self-signed certificates. Set `UNIFI_CONTROLLER_VERIFY_SSL=false` to skip verification.

!!! tip "Self-signed Certificates"
    If you've installed a valid SSL certificate on your controller, you can set `UNIFI_CONTROLLER_VERIFY_SSL=true`.

## Full Example

```bash
# ===========================================
# Cloud API (api.ui.com)
# ===========================================
UNIFI_API_KEY=your-api-key-here
UNIFI_API_URL=https://api.ui.com/v1
UNIFI_TIMEOUT=30

# ===========================================
# Local Controller
# ===========================================
UNIFI_CONTROLLER_URL=https://192.168.1.1
UNIFI_CONTROLLER_USERNAME=admin
UNIFI_CONTROLLER_PASSWORD=yourpassword
UNIFI_CONTROLLER_SITE=default
UNIFI_CONTROLLER_VERIFY_SSL=false
```

## Data Storage

UI-CLI stores local data in `~/.config/ui-cli/`:

| File | Purpose |
|------|---------|
| `session.json` | Cached controller login session |
| `groups.json` | Client groups definitions |

### Session Management

Local controller sessions are cached to avoid repeated logins:

- Auto-refreshes on expiry
- Delete to force re-login

```bash
# Force new session
rm ~/.config/ui-cli/session.json
./ui lo health
```

### Groups Storage

Client groups are stored locally and don't require a network connection to manage:

```bash
# View groups file location
ls ~/.config/ui-cli/groups.json

# Backup groups
cp ~/.config/ui-cli/groups.json ~/groups-backup.json

# Or use the export command
./ui groups export -o ~/groups-backup.json
```

## Multiple Sites

To switch between sites on the same controller:

```bash
# Edit .env
UNIFI_CONTROLLER_SITE=office

# Or use a different .env file
cp .env .env.office
# Edit .env.office with different site
```

## Verify Configuration

```bash
# Check Cloud API
./ui status

# Check Local Controller
./ui lo health
```

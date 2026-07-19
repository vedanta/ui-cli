"""Configuration management using pydantic-settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="UNIFI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Site Manager API (cloud)
    api_key: str = Field(
        default="",
        description="UniFi API key for authentication",
    )
    api_url: str = Field(
        default="https://api.ui.com/v1",
        description="UniFi API base URL",
    )
    timeout: int = Field(
        default=15,
        description="Request timeout in seconds",
    )

    # Local Controller API
    controller_url: str = Field(
        default="",
        description="Local controller URL (e.g., https://192.168.1.1)",
    )
    controller_username: str = Field(
        default="",
        description="Local controller username",
    )
    controller_password: str = Field(
        default="",
        description="Local controller password",
    )
    controller_site: str = Field(
        default="default",
        description="Site name for local controller",
    )
    controller_verify_ssl: bool = Field(
        default=False,
        description="Verify SSL certificates (disable for self-signed)",
    )
    controller_totp: str = Field(
        default="",
        description="TOTP code for MFA-enabled accounts (UDM-style controllers only)",
    )

    @property
    def is_configured(self) -> bool:
        """Check if Site Manager API key is configured."""
        return bool(self.api_key)

    @property
    def is_local_configured(self) -> bool:
        """Check if local controller is configured."""
        return bool(
            self.controller_url
            and self.controller_username
            and self.controller_password
        )

    @property
    def session_file(self) -> Path:
        """Path to session storage file."""
        config_dir = Path.home() / ".config" / "ui-cli"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "session.json"


# Global settings instance
settings = Settings()

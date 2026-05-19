from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from .env file.

    All values are validated at import time. If a required variable is missing,
    pydantic raises a clear error before any business logic runs.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Angel One SmartAPI ────────────────────────────────────────────────

    ANGEL_API_KEY: str = Field(default="", description="Angel One SmartAPI key")
    ANGEL_CLIENT_CODE: str = Field(default="", description="Angel One client/user ID")
    ANGEL_PASSWORD: str = Field(default="", description="Angel One trading password")
    ANGEL_TOTP_SECRET: str = Field(default="", description="TOTP secret for 2FA login")

    @field_validator("ANGEL_API_KEY", "ANGEL_CLIENT_CODE")
    @classmethod
    def check_not_empty(cls, v: str, info) -> str:
        if not v:
            raise ValueError(
                f"{info.field_name} is required. Set it in .env or export it as an environment variable."
            )
        return v

    # ── NSE Watchlist ─────────────────────────────────────────────────────

    NSE_TOKENS: list[int] = Field(
        default=[2885, 3045, 1333, 11536],
        description="Comma-separated list of Angel One token IDs",
    )

    @field_validator("NSE_TOKENS", mode="before")
    @classmethod
    def parse_token_list(cls, v: str | list[int]) -> list[int]:
        """Accept both a comma-separated string from .env and a list from code."""
        if isinstance(v, str):
            tokens = [int(t.strip()) for t in v.split(",") if t.strip()]
            if not tokens:
                raise ValueError("NSE_TOKENS must contain at least one token ID")
            return tokens
        return v

    # ── Storage ───────────────────────────────────────────────────────────

    DATA_DIR: Path = Field(default=Path("data"), description="Root directory for all data files")

    @field_validator("DATA_DIR", mode="before")
    @classmethod
    def resolve_path(cls, v: str | Path) -> Path:
        return Path(v).resolve()

    # ── Cleaning ──────────────────────────────────────────────────────────

    OUTLIER_Z_THRESHOLD: float = Field(default=4.0, ge=0.0, description="Z-score threshold for outlier detection")
    GAP_FILL_MAX_BARS: int = Field(default=2, ge=0, description="Max consecutive missing bars to auto-fill")

    # ── Behaviour ─────────────────────────────────────────────────────────

    LOG_LEVEL: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    TIMEZONE: str = Field(default="Asia/Kolkata", description="Default timezone for the application")

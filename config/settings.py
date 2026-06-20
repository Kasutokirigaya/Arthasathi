"""Centralized configuration using Pydantic Settings."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass(frozen=True, slots=True)
class ConfiguredAPIReference:
    """A unique configured API reference."""

    name: str
    description: str
    sources: tuple[str, ...]


def _env_files() -> tuple[Path, ...]:
    """Return env file paths in priority order (later overrides earlier)."""
    files: list[Path] = [
        Path(".env"),
    ]
    if explicit := os.environ.get("FCC_ENV_FILE"):
        files.append(Path(explicit))
    return tuple(files)


def _configured_env_files(model_config: Mapping[str, Any]) -> tuple[Path, ...]:
    """Return the currently configured env files for Settings."""
    configured = model_config.get("env_file")
    if configured is None:
        return ()
    if isinstance(configured, (str, Path)):
        return (Path(configured),)
    return tuple(Path(item) for item in configured)


def _env_file_value(path: Path, key: str) -> str | None:
    """Return a dotenv value when the file explicitly defines the key."""
    if not path.is_file():
        return None

    try:
        values = dotenv_values(path)
    except OSError:
        return None

    if key not in values:
        return None
    value = values[key]
    return "" if value is None else value


def _env_file_override(model_config: Mapping[str, Any], key: str) -> str | None:
    """Return the last configured dotenv value that explicitly defines a key."""
    configured_value: str | None = None
    for env_file in _configured_env_files(model_config):
        value = _env_file_value(env_file, key)
        if value is not None:
            configured_value = value
    return configured_value


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ==================== API Keys ====================
    groq_api_key: str = Field(default="", validation_alias="GROQ_API_KEY")

    # ==================== Server ====================
    host: str = "0.0.0.0"
    port: int = 8000

    # ==================== Security ====================
    # API key pepper for hashing API keys (used by auth.py)
    api_key_pepper: str = Field(default="", validation_alias="API_KEY_PEPPER")

    # ==================== Agent Configuration ====================
    # Default agent to use
    default_education_agent: str = Field(
        default="phi-3", validation_alias="DEFAULT_EDUCATION_AGENT"
    )

    # Handle empty strings for optional string fields
    @field_validator(
        "groq_api_key",
        "api_key_pepper",
        "default_education_agent",
        mode="before",
    )
    @classmethod
    def parse_optional_str(cls, v: Any) -> Any:
        if v == "":
            return None
        return v

    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
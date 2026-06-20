"""API key authentication and authorization utilities."""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Set

from fastapi import Depends, HTTPException, Request, status

from config.settings import get_settings, Settings


# Scope constants
SCOPE_EDUCATION_AGENT = "education_agent:invoke"
SCOPE_BUDGET_CALCULATION = "budget_calculation:invoke"
SCOPE_INCOME_CLASSIFICATION = "income_classification:invoke"
SCOPE_READINESS_SCORING = "readiness_scoring:invoke"
SCOPE_GUARDRAILS_FILTER = "guardrails_filter:invoke"
SCOPE_ORCHESTRATOR_FULL = "orchestrator:full"
SCOPE_STATUS_READ = "status:read"


ALL_SCOPES = {
    SCOPE_EDUCATION_AGENT,
    SCOPE_BUDGET_CALCULATION,
    SCOPE_INCOME_CLASSIFICATION,
    SCOPE_READINESS_SCORING,
    SCOPE_GUARDRAILS_FILTER,
    SCOPE_ORCHESTRATOR_FULL,
    SCOPE_STATUS_READ,
}


@dataclass(frozen=True)
class APIKey:
    """Represents a stored API key."""
    key_id: str
    hashed_key: str
    scopes: Set[str]
    disabled: bool = False
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_valid(self) -> bool:
        if self.disabled:
            return False
        if self.expires_at and self.expires_at < datetime.now(timezone.utc):
            return False
        return True


# In-memory stores (for demo / single-process usage)
# In production, replace with a persistent store (Redis, PostgreSQL, etc.)
_api_key_store: dict[str, APIKey] = {}  # key_id -> APIKey
_hash_to_key_id: dict[str, str] = {}   # hashed_key -> key_id


def _hash_key(key: str, pepper: str) -> str:
    """Hash an API key with SHA-256 and a pepper."""
    # Using SHA-256 for demo; consider using bcrypt/argon2 in production.
    to_hash = f"{key}{pepper}".encode("utf-8")
    return hashlib.sha256(to_hash).hexdigest()


def create_api_key(
    scopes: Set[str],
    expires_in_seconds: Optional[int] = None,
    pepper: str = "",
) -> tuple[str, str]:
    """
    Create a new API key.
    Returns (key_id, plain_key). The plain key is only shown once.
    """
    key_id = secrets.token_urlsafe(16)
    plain_key = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = (
        now + timedelta(seconds=expires_in_seconds)
        if expires_in_seconds is not None
        else None
    )
    hashed = _hash_key(plain_key, pepper)
    api_key = APIKey(
        key_id=key_id,
        hashed_key=hashed,
        scopes=set(scopes),
        created_at=now,
        expires_at=expires_at,
    )
    _api_key_store[key_id] = api_key
    _hash_to_key_id[hashed] = key_id
    return key_id, plain_key


def get_api_key_store() -> dict[str, APIKey]:
    """Return a copy of the API key store (for testing/admin)."""
    return dict(_api_key_store)


def _get_pepper() -> str:
    """Retrieve the API key pepper from settings."""
    return get_settings().api_key_pepper


def validate_api_key(key: str) -> Optional[APIKey]:
    """
    Validate a provided API key.
    Returns the APIKey object if valid, else None.
    """
    pepper = _get_pepper()
    hashed = _hash_key(key, pepper)
    key_id = _hash_to_key_id.get(hashed)
    if not key_id:
        return None
    api_key = _api_key_store.get(key_id)
    if not api_key or not api_key.is_valid():
        # Clean up if invalid/disabled/expired
        _hash_to_key_id.pop(hashed, None)
        _api_key_store.pop(key_id, None)
        return None
    return api_key


# --- FastAPI dependencies ---

async def get_api_key_from_header(request: Request) -> str:
    """
    Extract the API key from request headers.
    Looks for `X-Api-Key` or `Authorization: Bearer <key>`.
    """
    header = (
        request.headers.get("x-api-key")
        or request.headers.get("authorization")
        or request.headers.get("anthropic-auth-token")
    )
    if not header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    token = header.strip()
    if header.lower().startswith("bearer "):
        token = header.split(" ", 1)[1].strip()
    # Strip anything after the first colon to handle tokens with appended model names
    if token and ":" in token:
        token = token.split(":", 1)[0].strip()
    return token


async def get_current_user(
    api_key: str = Depends(get_api_key_from_header),
    settings: Settings = Depends(get_settings),
) -> APIKey:
    """
    Validate the API key and return the associated user/scopes.
    Raises HTTPException 401 if invalid or missing.
    """
    user = validate_api_key(api_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return user


# Legacy dependency for backward compatibility (keeps the old single-token check)
async def require_api_key_legacy(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    """
    Legacy dependency that checks the global GROQ_API_KEY.
    Kept for backward compatibility; prefer get_current_user + require_scopes.
    """
    groq_api_key = settings.groq_api_key.strip()
    if not groq_api_key:
        # No API key configured -> allow (as before)
        return
    header = (
        request.headers.get("x-api-key")
        or request.headers.get("authorization")
        or request.headers.get("anthropic-auth-token")
    )
    if not header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    token = header.strip()
    if header.lower().startswith("bearer "):
        token = header.split(" ", 1)[1].strip()
    if token and ":" in token:
        token = token.split(":", 1)[0].strip()
    if not secrets.compare_digest(token.encode("utf-8"), groq_api_key.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
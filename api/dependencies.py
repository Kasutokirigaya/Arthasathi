"""Dependency injection for FastAPI."""

import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Request
from loguru import logger

from config.settings import Settings
from config.settings import get_settings as _get_settings
from api import auth  # new auth module


def get_settings() -> Settings:
    """Return cached :class:`~config.settings.Settings` (FastAPI-friendly alias)."""
    return _get_settings()


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
            status_code=401, detail="Missing API key"
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
) -> auth.APIKey:
    """
    Validate the API key and return the associated user/scopes.
    Raises HTTPException 401 if invalid or missing.
    Supports fallback to legacy GROQ_API_KEY if no API key store configured.
    """
    # Try new API key validation first
    user = auth.validate_api_key(api_key)
    if user is not None:
        return user
    # Fallback to legacy single token if configured
    groq_api_key = settings.groq_api_key.strip()
    if groq_api_key:
        if secrets.compare_digest(
            api_key.encode("utf-8"), groq_api_key.encode("utf-8")
        ):
            # Return a pseudo APIKey with all scopes for backward compatibility
            return auth.APIKey(
                key_id="legacy",
                hashed_key="",
                scopes=set(auth.ALL_SCOPES),
                disabled=False,
            )
    raise HTTPException(
        status_code=401, detail="Invalid API key"
    )


def require_scopes(*required_scopes: str):
    """
    Dependency factory that ensures the current user has all required scopes.
    Usage: Depends(require_scopes("education_agent:invoke", "budget_calculation:invoke"))
    """
    async def _checker(
        request: Request,
        user: auth.APIKey = Depends(get_current_user),
        settings: Settings = Depends(get_settings),
    ) -> auth.APIKey:
        user_scopes: set[str] = set(user.scopes)
        missing = [s for s in required_scopes if s not in user_scopes]
        if missing:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient scope. Missing: {', '.join(missing)}",
            )
        return user

    return _checker


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
            status_code=401, detail="Missing API key"
        )
    token = header.strip()
    if header.lower().startswith("bearer "):
        token = header.split(" ", 1)[1].strip()
    if token and ":" in token:
        token = token.split(":", 1)[0].strip()
    if not secrets.compare_digest(token.encode("utf-8"), groq_api_key.encode("utf-8")):
        raise HTTPException(
            status_code=401, detail="Invalid API key"
        )
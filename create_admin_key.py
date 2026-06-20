#!/usr/bin/env python3
"""
Create an initial admin API key for the AarthSaathi Financial Orchestrator API.

Run this after setting API_KEY_PEPPER in your .env file.
The script will output a key_id and the plain API key (shown only once).
Store the key securely; you can use it to authenticate requests.
"""

import os
import sys
from pathlib import Path

# Ensure we can import from the project root
sys.path.append(str(Path(__file__).parent))

from config.settings import get_settings
from api import auth


def main():
    settings = get_settings()
    pepper = settings.api_key_pepper
    if not pepper:
        print("Error: API_KEY_PEPPER is not set in your .env or environment.")
        print("Please set a random string, e.g.:")
        print('  API_KEY_PEPPER=$(openssl rand -hex 32)')
        sys.exit(1)

    # Create an admin key with all scopes, no expiration
    scopes = set(auth.ALL_SCOPES)
    key_id, plain_key = auth.create_api_key(
        scopes=scopes,
        expires_in_seconds=None,  # no expiry
        pepper=pepper,
    )
    print("=== Admin API Key Created ===")
    print(f"Key ID: {key_id}")
    print(f"API Key: {plain_key}")
    print("\nStore this key securely. It will not be shown again.")
    print("You can use it as the X-Api-Key or Authorization Bearer token.")
    print("\nTo disable the legacy GROQ_API_KEY check, set it to empty in .env")
    print("and restart the server (though keeping both enabled is recommended for backward compatibility).")


if __name__ == "__main__":
    main()
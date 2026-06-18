"""Shared Google OAuth credential loading for Gmail and Calendar tools.

Credentials are obtained once via scripts/google_oauth_setup.py (an
interactive, local-browser consent flow) and cached to GOOGLE_TOKEN_PATH.
This module only refreshes the cached token — it never runs the interactive
flow itself, since a FastAPI request has no browser to redirect to.
"""
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from app.config import GOOGLE_TOKEN_PATH

# Keep scopes minimal and additive. gmail.compose covers draft creation;
# calendar.events covers event create/update (not full calendar settings).
SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/calendar.events",
]


class GoogleCredentialsNotConfigured(Exception):
    """Raised when no cached OAuth token is available yet."""


def load_google_credentials() -> Credentials:
    if not os.path.exists(GOOGLE_TOKEN_PATH):
        raise GoogleCredentialsNotConfigured(
            f"No cached Google OAuth token at {GOOGLE_TOKEN_PATH}. "
            "Run `python scripts/google_oauth_setup.py` once to authorize."
        )

    creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_PATH, SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(GOOGLE_TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return creds

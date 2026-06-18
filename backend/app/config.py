import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/meetops",
)

# Chat/reasoning model used by the agents. Override in .env.
# gpt-5.4-nano (cheapest) or gpt-5.4-mini are good defaults in 2026.
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5.4-mini")

# Speech-to-text model. gpt-4o-mini-transcribe was retired ~June 2026,
# so default to gpt-4o-transcribe. Confirm it is still current when you
# wire up audio.
TRANSCRIBE_MODEL = os.getenv("TRANSCRIBE_MODEL", "gpt-4o-transcribe")

# Google OAuth client secret (downloaded from Cloud Console) and the cached
# token produced by the one-time consent flow (scripts/google_oauth_setup.py).
# Both paths are relative to backend/ unless absolute.
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials/google_credentials.json")
GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "credentials/google_token.json")

# IANA timezone used when creating calendar events from the LLM's free-text
# date/time strings (e.g. "Thursday morning"). Override in .env if you're
# not in this timezone.
CALENDAR_TIMEZONE = os.getenv("CALENDAR_TIMEZONE", "Asia/Calcutta")
CALENDAR_DEFAULT_DURATION_MINUTES = int(os.getenv("CALENDAR_DEFAULT_DURATION_MINUTES", "60"))

# Fine-grained GitHub PAT (Issues: read/write) scoped to one test repo, and
# that repo as "owner/name".
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

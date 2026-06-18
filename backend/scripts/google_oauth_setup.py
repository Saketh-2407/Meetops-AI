"""One-time interactive Google OAuth consent flow.

Run this once from backend/ after placing your downloaded OAuth client
secret at the path in GOOGLE_CREDENTIALS_PATH (default
credentials/google_credentials.json):

    python scripts/google_oauth_setup.py

It opens a browser for you to sign in and approve the requested scopes,
then writes the resulting refreshable token to GOOGLE_TOKEN_PATH (default
credentials/google_token.json). The backend only ever reads/refreshes that
cached token afterward — it never runs this interactive flow itself.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_auth_oauthlib.flow import InstalledAppFlow

from app.config import GOOGLE_CREDENTIALS_PATH, GOOGLE_TOKEN_PATH
from app.services.google_auth import SCOPES


def main():
    if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
        print(f"Missing client secret file at {GOOGLE_CREDENTIALS_PATH}.")
        print("Download it from Google Cloud Console (OAuth client ID, Desktop app type)")
        print("and save it at that path, then re-run this script.")
        return

    flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    os.makedirs(os.path.dirname(GOOGLE_TOKEN_PATH) or ".", exist_ok=True)
    with open(GOOGLE_TOKEN_PATH, "w") as f:
        f.write(creds.to_json())

    print(f"Saved token to {GOOGLE_TOKEN_PATH}. The backend can now create Gmail drafts / calendar events.")


if __name__ == "__main__":
    main()

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Read inbox + send yourself the daily report
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


def main():
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE),
                SCOPES,
            )
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        print(f"Saved token to: {TOKEN_FILE}")

    print("Gmail authorization OK (read + send).")
    if creds.refresh_token:
        print("\n--- For GitHub Actions later (keep secret) ---")
        print("REFRESH_TOKEN:")
        print(creds.refresh_token)
    else:
        print(
            "\nNo refresh token in token.json. "
            "Delete token.json and run again after revoking app access in Google Account."
        )


if __name__ == "__main__":
    main()
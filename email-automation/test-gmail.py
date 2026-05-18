from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_FILE = Path(__file__).resolve().parent / "token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
service = build("gmail", "v1", credentials=creds)

results = service.users().messages().list(
    userId="me",
    maxResults=3,
    q="in:inbox category:primary",
).execute()

messages = results.get("messages", [])

print(f"Found {len(messages)} recent message(s).")
for msg in messages:
    detail = service.users().messages().get(userId="me", id=msg["id"]).execute()
    headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
    print("-", headers.get("Subject", "(no subject)"))
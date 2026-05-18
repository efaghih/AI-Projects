from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent
TOKEN_FILE = BASE_DIR / "token.json"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]
MAX_BODY_CHARS = 1000

DEFAULT_QUERY = "in:inbox category:primary newer_than:1d"


@dataclass
class EmailMessage:
    id: str
    thread_id: str
    from_addr: str
    to_addr: str
    subject: str
    date: str
    snippet: str


def _credentials_from_env() -> Credentials | None:
    """GitHub Actions: build credentials from repository secrets."""
    refresh_token = os.getenv("GMAIL_REFRESH_TOKEN", "").strip()
    client_id = os.getenv("GMAIL_CLIENT_ID", "").strip()
    client_secret = os.getenv("GMAIL_CLIENT_SECRET", "").strip()

    if not (refresh_token and client_id and client_secret):
        return None

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds


def get_credentials() -> Credentials:
    """
    Local: use token.json
    GitHub Actions: use GMAIL_* environment secrets
    """
    env_creds = _credentials_from_env()
    if env_creds is not None:
        return env_creds

    if not TOKEN_FILE.exists():
        raise FileNotFoundError(
            "No token.json and no GMAIL_* env vars. "
            "Run auto-once.py locally or set GitHub Secrets."
        )

    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def get_gmail_service():
    """Build an authenticated Gmail API client."""
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def _header_map(payload: dict) -> dict[str, str]:
    headers = payload.get("headers", [])
    return {h["name"].lower(): h["value"] for h in headers}


def _decode_body_data(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def _extract_plain_text(payload: dict) -> str:
    if not payload:
        return ""

    if payload.get("body", {}).get("data"):
        return _decode_body_data(payload["body"]["data"])

    parts = payload.get("parts", [])
    plain = ""
    html = ""
    for part in parts:
        mime = part.get("mimeType", "")
        if mime == "text/plain" and part.get("body", {}).get("data"):
            plain = _decode_body_data(part["body"]["data"])
        elif mime == "text/html" and part.get("body", {}).get("data"):
            html = _decode_body_data(part["body"]["data"])
        elif mime.startswith("multipart/"):
            nested = _extract_plain_text(part)
            if nested:
                return nested
    return plain or html or ""


def fetch_primary_emails(
    *,
    max_results: int = 25,
    query: str = DEFAULT_QUERY,
) -> list[EmailMessage]:
    service = get_gmail_service()
    list_response = (
        service.users()
        .messages()
        .list(userId="me", maxResults=max_results, q=query)
        .execute()
    )
    stubs = list_response.get("messages", [])
    emails: list[EmailMessage] = []

    for stub in stubs:
        detail = (
            service.users()
            .messages()
            .get(userId="me", id=stub["id"], format="full")
            .execute()
        )
        headers = _header_map(detail.get("payload", {}))
        body_text = _extract_plain_text(detail.get("payload", {}))
        snippet = (body_text or detail.get("snippet", "")).strip()
        if len(snippet) > MAX_BODY_CHARS:
            snippet = snippet[:MAX_BODY_CHARS] + "…"

        emails.append(
            EmailMessage(
                id=detail["id"],
                thread_id=detail.get("threadId", ""),
                from_addr=headers.get("from", ""),
                to_addr=headers.get("to", ""),
                subject=headers.get("subject", "(no subject)"),
                date=headers.get("date", ""),
                snippet=snippet,
            )
        )

    return emails
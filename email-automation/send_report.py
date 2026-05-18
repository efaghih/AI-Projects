import base64
import os
from email.mime.text import MIMEText

from gmail_client import get_gmail_service


def send_report_email(*, subject: str, body_text: str, to_email: str | None = None) -> None:
    """
    Send a plain-text email to yourself using Gmail API.
    """
    to_email = (to_email or os.getenv("MY_EMAIL", "")).strip()
    if not to_email:
        raise ValueError("Missing MY_EMAIL in .env")

    message = MIMEText(body_text, "plain", "utf-8")
    message["to"] = to_email
    message["from"] = to_email
    message["subject"] = subject

    raw_bytes = message.as_bytes()
    raw_b64 = base64.urlsafe_b64encode(raw_bytes).decode("utf-8")

    service = get_gmail_service()
    service.users().messages().send(
        userId="me",
        body={"raw": raw_b64},
    ).execute()
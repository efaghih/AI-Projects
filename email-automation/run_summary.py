import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from gmail_client import fetch_primary_emails
from send_report import send_report_email
from summarizer import RunMode, summarize_emails

load_dotenv()

MODE_ALIASES = {
    "morning": "morning",
    "midday": "midday",
    "afternoon": "midday",
    "evening": "evening",
    "night": "evening",
}

MODE_LABELS = {
    "morning": "Morning",
    "midday": "Midday",
    "evening": "Evening",
}


def query_for_mode(mode: RunMode) -> str:
    base = "in:inbox category:primary"
    if mode == "morning":
        return f"{base} newer_than:12h"
    if mode == "midday":
        return f"{base} newer_than:4h"
    if mode == "evening":
        return f"{base} newer_than:13h"
    return f"{base} newer_than:1d"


def build_email_subject(mode: RunMode) -> str:
    label = MODE_LABELS.get(mode, mode.title())
    today = datetime.now().strftime("%Y-%m-%d")
    return f"Email Assistant – {label} ({today})"


def main():
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "morning"
    mode: RunMode = MODE_ALIASES.get(arg, "morning")  # type: ignore[assignment]

    # Optional: python run_summary.py morning --no-email
    send_email = "--no-email" not in sys.argv

    query = query_for_mode(mode)

    print(f"Run mode: {mode}")
    print(f"Gmail query: {query}")
    print(f"Send email: {send_email}")
    print(f"Time: {datetime.now().isoformat(timespec='seconds')}\n")

    emails = fetch_primary_emails(max_results=15, query=query)
    print(f"Fetched {len(emails)} email(s) from Gmail.\n")

    if not emails:
        print("No Primary emails in this time window. Nothing to summarize.")
        return

    print("=" * 60)
    print(f"EMAIL ASSISTANT REPORT ({mode.upper()})")
    print("=" * 60 + "\n")

    summary = summarize_emails(emails, mode=mode)
    print(summary)
    print("\n" + "=" * 60)
    print("End of report")

    if send_email:
        subject = build_email_subject(mode)
        try:
            send_report_email(subject=subject, body_text=summary)
            print(f"\nReport emailed to {os.getenv('MY_EMAIL', 'you')}.")
        except Exception as e:
            print(f"\nCould not send email: {e}")
            print("Summary was still printed above.")


if __name__ == "__main__":
    main()
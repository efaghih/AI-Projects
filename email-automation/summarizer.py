import os
import re
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI

from gmail_client import EmailMessage

load_dotenv()

MY_EMAIL = os.getenv("MY_EMAIL", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

RunMode = Literal["morning", "midday", "evening"]

# Automatic hints — helps catch PayPal and similar (not only PayPal)
FINANCIAL_SENDERS = re.compile(
    r"paypal|venmo|stripe|square|zelle|cashapp|intuit|quickbooks|adp|gusto|"
    r"chase|bankofamerica|wellsfargo|citi|amex|american express|capital one|"
    r"apple\.com/bill|google pay|payment@|billing@|receipt@|noreply@paypal",
    re.I,
)
FINANCIAL_PHRASES = re.compile(
    r"you paid|you sent|payment received|payment confirmation|receipt for|"
    r"amount paid|has been charged|your payment|order confirmation|invoice paid|"
    r"paycheck|pay roll|payroll|direct deposit|salary|wage|refund issued|"
    r"transaction id|paid \$\d|payment of \$\d",
    re.I,
)


def _financial_hint(em: EmailMessage) -> tuple[str, str]:
    """Returns (yes/no, short reason) for the prompt."""
    text = f"{em.from_addr} {em.subject} {em.snippet}"
    if FINANCIAL_SENDERS.search(text):
        return "yes", "payment provider / bank sender"
    if FINANCIAL_PHRASES.search(text):
        return "yes", "payment or paycheck wording"
    return "no", ""


def _max_tokens_for_mode(mode: RunMode) -> int:
    if mode == "evening":
        return 400
    return 950


def _format_emails_for_prompt(emails: list[EmailMessage]) -> str:
    if not emails:
        return "(No emails in this batch.)"

    blocks = []
    for i, em in enumerate(emails, start=1):
        hint, hint_reason = _financial_hint(em)
        hint_line = f"Payment hint (automatic): {hint}"
        if hint_reason:
            hint_line += f" — {hint_reason}"

        blocks.append(
            f"""Email {i}
{hint_line}
From: {em.from_addr}
To: {em.to_addr}
Date: {em.date}
Subject: {em.subject}
Body/snippet:
{em.snippet}
---"""
        )
    return "\n".join(blocks)


def _system_prompt(mode: RunMode) -> str:
    base = f"""You are a personal email assistant for Ehsan.
The user's Gmail address is: {MY_EMAIL or "(unknown)"}.

Read each email's Subject and Body/snippet carefully.
Each email must appear in EXACTLY ONE section.

## CLASSIFICATION ORDER (important)
1. Financial first
2. Reply needed second
3. Other emails last

## Financial — real money (NOT ads)
Use Financial when the email is about the USER's actual payment, charge, refund, or pay.
Financial does NOT require "Hi Ehsan" or a personal greeting.

INCLUDE in Financial (examples):
- PayPal: "You paid", "You sent", payment receipt, merchant charge (e.g. $1 to a service)
- Stripe, Venmo, Square, Zelle, Apple/Google billing receipts
- Bank/card: charge, deposit, payment posted, statement ready (about their account)
- Paycheck, payroll, direct deposit, ADP/Gusto, tax refund
- Invoice paid, subscription renewed, utility bill paid

If "Payment hint (automatic): yes" → put in Financial unless it is clearly marketing
(e.g. "Apply for a credit card", "Pre-approved loan", "Earn cash back" with no real transaction).

EXCLUDE from Financial (→ Other emails):
- Credit card offers, loan ads, investment promos, coupons, shopping ads
- "You could save" / "Limited offer" with no actual charge or payment by the user

For each Financial bullet: From, Subject, one line (e.g. "You paid $1.00 to … via PayPal").

## Reply needed
ONLY if a real person expects a reply AND personal addressing (Hi Ehsan, Seyyedehsan, faghih, etc.).
Do NOT put PayPal/payment receipts here — those are Financial.

## Other emails
Everything else (FYI, promos, newsletters, alerts with no real transaction).

## Output rules
- Use ONLY the emails provided. Do not invent amounts or senders.
- Be concise.
- Do NOT draft or send replies.
"""

    if mode == "evening":
        return (
            base
            + "\n## Evening mode\n"
            "Short recap (max 10 bullets). Include any payments/paychecks as bullets. "
            "No section headings."
        )

    return (
        base
        + "\n## Morning/Midday mode\n"
        "Use exactly these headings in order:\n"
        "## Reply needed\n"
        "## Financial\n"
        "## Other emails\n"
        "If empty: (none)\n"
    )


def _user_prompt(mode: RunMode, email_block: str) -> str:
    if mode == "evening":
        return (
            "Evening recap. Include PayPal/payments/paychecks if present:\n\n"
            + email_block
        )
    return (
        "Classify each email. Check Financial FIRST (PayPal, you paid, receipts, payroll). "
        "Respect Payment hint (automatic): yes. Not ads:\n\n"
        + email_block
    )


def summarize_emails(
    emails: list[EmailMessage],
    *,
    mode: RunMode = "morning",
    model: str | None = None,
) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("Missing OPENAI_API_KEY in .env")

    model = model or OPENAI_MODEL
    client = OpenAI(api_key=OPENAI_API_KEY)
    email_block = _format_emails_for_prompt(emails)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _system_prompt(mode)},
            {"role": "user", "content": _user_prompt(mode, email_block)},
        ],
        temperature=0.2,
        max_tokens=_max_tokens_for_mode(mode),
    )

    return response.choices[0].message.content.strip()
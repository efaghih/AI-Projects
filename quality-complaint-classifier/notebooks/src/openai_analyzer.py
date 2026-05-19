# notebooks/src/openai_analyzer.py
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from paths import PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

URGENCY_LEVELS = {"Low", "Medium", "High", "Critical"}

SYSTEM_PROMPT = """You are a quality complaint analyst assistant.
Given a consumer complaint and a predicted complaint category, return a JSON object with:
- predicted_category (use the provided category string exactly)
- urgency: one of Low, Medium, High, Critical
- likely_root_cause: 1-3 sentences
- containment_action: immediate steps to limit impact
- corrective_action: longer-term fix to prevent recurrence
- customer_response: professional draft reply (4-6 sentences)

Rules:
- Output ONLY valid JSON, no markdown fences.
- Base reasoning on the complaint text; do not invent specific names, account numbers, or dates.
- If the complaint suggests safety, legal threats, or fraud, urgency should be High or Critical.
- Keep language suitable for a quality/compliance team."""

def build_user_prompt(complaint_text: str, quality_category: str, cfpb_issue_label: str | None = None) -> str:
    parts = [
        f"Predicted category: {quality_category}",
        f"Complaint text:\n{complaint_text.strip()}",
    ]
    if cfpb_issue_label:
        parts.insert(1, f"Source issue label (context only): {cfpb_issue_label}")
    return "\n\n".join(parts)

def analyze_complaint(
    complaint_text: str,
    quality_category: str,
    cfpb_issue_label: str | None = None,
    model: str = "gpt-4o-mini",
) -> dict:
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not set in .env")

    response = client.chat.completions.create(
        model=model,
        temperature=0.3,
        response_format={"type": "json_object"},  # structured JSON mode
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_user_prompt(complaint_text, quality_category, cfpb_issue_label),
            },
        ],
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    # Light validation
    if data.get("predicted_category") != quality_category:
        data["predicted_category"] = quality_category  # enforce taxonomy label
    if data.get("urgency") not in URGENCY_LEVELS:
        data["urgency"] = "Medium"

    return data
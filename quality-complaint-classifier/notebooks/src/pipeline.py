import joblib
from taxonomy import map_issue_to_general, map_issue_to_manufacturing
from openai_analyzer import analyze_complaint
from paths import PROJECT_ROOT
_model = None

def get_model():
    global _model
    if _model is None:
        _model = joblib.load(PROJECT_ROOT / "models/tfidf_logreg_issue_classifier.pkl")
    return _model

def full_analysis(complaint_text: str) -> dict:
    text = complaint_text.lower().strip()
    issue = get_model().predict([text])[0]
    quality = map_issue_to_general(issue)
    mfg = map_issue_to_manufacturing(issue)

    ai = analyze_complaint(
        complaint_text=text,
        quality_category=quality,
        cfpb_issue_label=issue,
    )

    return {
        "cfpb_issue_label": issue,
        "quality_category": quality,
        "manufacturing_demo_category": mfg,
        **ai,
    }
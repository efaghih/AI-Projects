from pathlib import Path
import sys

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Project root = parent of app/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "notebooks" / "src"
sys.path.insert(0, str(SRC_DIR))

load_dotenv(PROJECT_ROOT / ".env")

from pipeline import full_analysis  # noqa: E402

DATA_PATH = PROJECT_ROOT / "data/processed/complaints_clean.csv"
ENRICHED_PATH = PROJECT_ROOT / "data/processed/complaints_with_quality_category.csv"
OUT_DIR = PROJECT_ROOT / "outputs"
MODEL_PATH = PROJECT_ROOT / "models/tfidf_logreg_issue_classifier.pkl"

st.set_page_config(
    page_title="Quality Complaint Classifier",
    page_icon="📋",
    layout="wide",
)


@st.cache_data
def load_data():
    path = ENRICHED_PATH if ENRICHED_PATH.exists() else DATA_PATH
    return pd.read_csv(path, parse_dates=["date_received"])


def run_analysis(text: str) -> dict:
    return full_analysis(text)


# --- Sidebar ---
page = st.sidebar.radio("Navigation", ["Analyze Complaint", "Dataset Insights"])
st.sidebar.markdown("---")
st.sidebar.caption("CFPB complaint intelligence demo (v1)")

# =============================================================================
# Page 1 — Analyze Complaint
# =============================================================================
if page == "Analyze Complaint":
    st.title("Analyze Complaint")
    st.markdown(
        "Paste a complaint narrative. Runs **ML classifier → quality taxonomy → OpenAI**."
    )

    complaint_text = st.text_area(
        "Complaint text",
        value="They charged my account twice and will not fix my statement.",
        height=180,
    )

    if st.button("Analyze Complaint", type="primary"):
        if not complaint_text.strip():
            st.warning("Please enter complaint text.")
        elif not MODEL_PATH.exists():
            st.error(f"Model not found. Train Step 5 first:\n`{MODEL_PATH}`")
        else:
            with st.spinner("Analyzing..."):
                try:
                    result = run_analysis(complaint_text)
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    st.stop()

            st.success("Done")

            c1, c2, c3 = st.columns(3)
            c1.metric("Quality category", result.get("quality_category", "—"))
            c2.metric("Urgency", result.get("urgency", "—"))
            c3.metric("Manufacturing (demo)", result.get("manufacturing_demo_category", "—"))

            with st.expander("ML & taxonomy"):
                st.write("**CFPB issue (ML):**", result.get("cfpb_issue_label"))
                st.write("**Predicted category:**", result.get("predicted_category"))

            st.subheader("Likely root cause")
            st.write(result.get("likely_root_cause", ""))

            a, b = st.columns(2)
            with a:
                st.subheader("Containment action")
                st.info(result.get("containment_action", ""))
            with b:
                st.subheader("Corrective action")
                st.info(result.get("corrective_action", ""))

            st.subheader("Draft customer response")
            st.write(result.get("customer_response", ""))

            with st.expander("Raw JSON"):
                st.json(result)

# =============================================================================
# Page 2 — Dataset Insights
# =============================================================================
else:
    st.title("Dataset Insights")

    if not DATA_PATH.exists():
        st.error(f"Data not found: {DATA_PATH}")
        st.stop()

    df = load_data()

    st.subheader("Overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Complaints", f"{len(df):,}")
    c2.metric("Issue categories", df["issue_label"].nunique())
    c3.metric("Products", df["product"].nunique())
    c4.metric(
        "Date range",
        f"{df['date_received'].min().date()} → {df['date_received'].max().date()}",
    )

    st.subheader("Complaints by issue")
    st.bar_chart(df["issue_label"].value_counts())

    st.subheader("Complaints by product (top 10)")
    st.bar_chart(df["product"].value_counts().head(10))

    if "quality_category" in df.columns:
        st.subheader("General quality categories")
        st.bar_chart(df["quality_category"].value_counts())

    st.subheader("EDA charts")
    charts = [
        ("Issue distribution", "issue_distribution.png"),
        ("Product distribution", "product_distribution.png"),
        ("Monthly trend", "monthly_complaint_trend.png"),
        ("Avg length by issue", "avg_length_by_issue.png"),
    ]
    cols = st.columns(2)
    for i, (title, fname) in enumerate(charts):
        p = OUT_DIR / fname
        with cols[i % 2]:
            st.caption(title)
            if p.exists():
                st.image(str(p), use_container_width=True)
            else:
                st.warning(f"Missing: outputs/{fname}")

    st.subheader("Baseline model — confusion matrix")
    cm = OUT_DIR / "confusion_matrix_baseline.png"
    if cm.exists():
        st.image(str(cm), use_container_width=True)
    else:
        st.info("Generate with notebook `04_train_baseline.ipynb`.")

    st.markdown(
        """
**Test metrics (TF-IDF + Logistic Regression)**  
Accuracy **0.706** · Macro F1 **0.678** · Weighted F1 **0.716**
        """
    )
from pathlib import Path
import pandas as pd

# Repo root = parent of scripts/ (run: python scripts/filter_v1.py from project root)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW = PROJECT_ROOT / "data/raw/cfpb_complaints.csv"  # place CFPB export here
OUT = PROJECT_ROOT / "data/processed/cfpb_v1.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

DATE_MIN = "2021-01-01"
DATE_MAX = "2026-05-19"
TARGET_MIN, TARGET_MAX = 50_000, 500_000

usecols = [
    "Date received",
    "Consumer complaint narrative",
    "Issue",
    "Product",
]


chunks = []
for chunk in pd.read_csv(RAW, usecols=usecols, chunksize=100_000, low_memory=False):
    chunk["Date received"] = pd.to_datetime(chunk["Date received"], errors="coerce")
    chunk = chunk[
        chunk["Date received"].between(DATE_MIN, DATE_MAX)
        & chunk["Consumer complaint narrative"].notna()
        & chunk["Consumer complaint narrative"].astype(str).str.strip().ne("")
    ]
    if len(chunk):
        chunks.append(chunk)

df = pd.concat(chunks, ignore_index=True)
print(f"After filters: {len(df):,} rows")

# If too many rows, keep newest until ~500k (or sample randomly)
if len(df) > TARGET_MAX:
    df = df.sort_values("Date received", ascending=False).head(TARGET_MAX)
elif len(df) < TARGET_MIN:
    print(f"Warning: only {len(df):,} rows (aim was {TARGET_MIN:,}–{TARGET_MAX:,})")

df.to_csv(OUT, index=False)
print(f"Wrote {OUT} ({len(df):,} rows)")
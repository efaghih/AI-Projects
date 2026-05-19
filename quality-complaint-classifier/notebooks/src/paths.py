"""Resolve project root for notebooks, scripts, and the Streamlit app."""
from pathlib import Path


def find_project_root() -> Path:
    """
    Locate the repo root (folder containing data/, notebooks/, app/).

    Works when imported from notebooks/src/*.py. If you run code from
    another working directory, start Jupyter from the repo root or set
    PROJECT_ROOT manually in the notebook.
    """
    candidates = [
        Path(__file__).resolve().parents[2],  # .../quality-complaint-classifier
        Path.cwd(),
        Path.cwd().parent,
    ]
    for root in candidates:
        if (root / "data").is_dir() and (root / "notebooks").is_dir():
            return root
    raise FileNotFoundError(
        "Could not find project root (expected data/ and notebooks/). "
        "Run from the repo root or set PROJECT_ROOT to your clone path."
    )


PROJECT_ROOT = find_project_root()

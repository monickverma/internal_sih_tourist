import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "internship-recommender"
sys.path.insert(0, str(BACKEND))

"""Vercel serverless entrypoint.

Mounts the FastAPI app from internship-recommender/ under /api so the
frontend (served from the same Vercel project) can call relative paths
like /api/recommend.

Run locally from the repo root:  uvicorn api.index:app --port 8000
"""
import sys
from pathlib import Path

from fastapi import FastAPI

BACKEND_DIR = Path(__file__).resolve().parent.parent / "internship-recommender"
sys.path.insert(0, str(BACKEND_DIR))

from main import app as recommender_app  # noqa: E402

app = FastAPI(title="Internship Recommender (Vercel)")
app.mount("/api", recommender_app)

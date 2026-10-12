# main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from api import schemas, utils

app = FastAPI(title="Internship Recommender API")

# CORS so frontend (React) can talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # in prod, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["status"])
def root():
    return {"status": "ok", "message": "Internship recommender API running."}


@app.get("/status", tags=["status"])
def status():
    """Check that the dataset loaded and report the scoring setup."""
    try:
        st = utils.load_data()
        return {
            "scoring": "weighted input-dependent components",
            "weights": utils.WEIGHTS,
            "num_internships_raw": st["n_raw"],
            "num_internships": len(st["df"]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend", response_model=schemas.RecommendOut, tags=["recs"])
def recommend(candidate: schemas.CandidateIn, top_k: int = Query(5, ge=1, le=50)):
    """Main recommendation endpoint, called by the frontend."""
    try:
        r = utils.recommend(candidate.model_dump(), top_k=top_k)
        return {
            "candidate": candidate,
            "match_probability": r["probability"],
            "weights": r["used_components"],
            "recommendations": r["recommendations"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

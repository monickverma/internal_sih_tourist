# InternAI — Internship Recommender

**Live demo:** https://internship-recommender-zeta.vercel.app

A web app that recommends internships from the AICTE internship dataset. A student enters
a preferred job title, work mode (Full Time / Part Time / Virtual Internship) and location,
and gets the top 5 matching internships with a match score.

Built for Smart India Hackathon (SIH).

## How it works

- **Data:** `data/Aicte_Internship_With_Feedback.csv` — 2,237 AICTE internship listings
  (job title, company, type, state, stipend, duration) plus a binary `Label` column
  (299 positive / 1,938 negative).
- **Model (`internship-recommender/train.py`, `preprocess.py`):** job title, job type and
  state are label-encoded; together with stipend and duration they form 5 features for a
  scikit-learn `RandomForestClassifier` (200 trees, `class_weight="balanced"`), trained on an
  80/20 stratified split and saved with joblib to `internship_model.pkl`.
- **Ranking (`internship-recommender/api/utils.py`):** for a request, every internship gets
  `match_score = 0.7 × ML score + 0.2 × title similarity + 0.1 × location similarity`, where
  - *ML score* is the RandomForest's positive-class probability for that internship,
    min-max normalised across the dataset;
  - *title / location similarity* is a `difflib.SequenceMatcher` fuzzy-string ratio between
    the user's input and the internship's title / state.

  The top-k rows by `match_score` are returned. The endpoint also returns a
  `match_probability` for the candidate, obtained by fuzzy-matching their inputs to the
  encoder vocabularies and running the classifier on that vector.
- **API (`internship-recommender/main.py`):** FastAPI with `GET /`, `GET /status` and
  `POST /recommend?top_k=5` (body: `{"JobTitle", "Mode", "Location", "Stipend"?, "Duration"?}`).
- **Frontend (`Final-Sih-Night/`):** React 19 + Vite + Tailwind; a step-by-step form posts to
  the API and the results page shows the recommendations. The form also asks for skillset,
  stipend and experience, but currently only job title, mode and location are sent.
- **Deployment:** one Vercel project. The Vite build is served as static files and
  `api/index.py` runs the FastAPI app as a Python serverless function mounted at `/api`
  (`vercel.json` rewrites `/api/*` to it). The frontend calls `${VITE_API_BASE}` which
  defaults to the relative path `/api`.

Example:

```bash
curl -X POST "https://internship-recommender-zeta.vercel.app/api/recommend?top_k=5" \
  -H "Content-Type: application/json" \
  -d '{"JobTitle": "Finance Intern", "Mode": "Full Time", "Location": "Kerala"}'
```

## Run locally

Requirements: Python 3.11+ and Node 20+.

```bash
# 1. Backend (from the repo root)
pip install -r internship-recommender/requirements.txt uvicorn
uvicorn api.index:app --port 8000          # API at http://127.0.0.1:8000/api

# 2. Frontend (new terminal)
cd Final-Sih-Night
npm install
npm run dev                                 # Vite proxies /api to 127.0.0.1:8000
```

To point the frontend at a different backend, set `VITE_API_BASE`
(e.g. `VITE_API_BASE=https://example.com/api npm run build`).

Retrain the model (requires the same scikit-learn version, 1.7.2):

```bash
cd internship-recommender
python train.py                             # writes internship_model.pkl
```

## Repo layout

```
api/index.py                 Vercel serverless entrypoint (mounts the FastAPI app at /api)
internship-recommender/      FastAPI backend, training scripts, trained model
Final-Sih-Night/             React + Vite frontend
data/                        AICTE internship datasets (CSV)
vercel.json                  Vercel build + routing config
```

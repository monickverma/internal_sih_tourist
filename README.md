# InternAI — Internship Recommender

**Live demo:** https://internship-recommender-zeta.vercel.app

A web app that recommends internships from the AICTE internship dataset. A student fills in a
6-step form (skillset, desired stipend, experience, job title, work mode, location) and gets the
top 5 matching internships, each with a match score and a list of reasons ("why this match").

Built for Smart India Hackathon (SIH).

## How it works

In one sentence: listings are deduplicated, then ranked by a weighted, explainable score that
combines skill-keyword overlap (with fuzzy token matching), TF-IDF text and title similarity,
location/remote match, work-mode match and a soft stipend penalty, all computed from the
student's own input.

- **Data:** `data/Aicte_Internship_With_Feedback.csv`, 2,237 AICTE listings with job title,
  job type (Full Time / Part Time / Virtual Internship), company, city, state, stipend and
  duration. There is no skills, description or experience-requirement column.
- **Cleaning and deduplication (`internship-recommender/api/utils.py`, `load_data`):** rows
  without a title are dropped; durations like "8 Weeks", "45days", "1 Years" are parsed into
  months. Listings whose title, company, city, state, job type, stipend and duration are equal
  after normalisation (case, punctuation, spacing and plurals ignored, so "SELF HELP GROUPS" ==
  "Self Help Group" and "DAY-NULM" == "DAYNULM") are collapsed to one: the 2,236 titled rows become 2,034
  unique listings. When results are picked, a listing is also skipped if a higher-ranked card
  has the same employer and city and a near-identical title (char-n-gram cosine >= 0.9), e.g.
  the same posting listed as both Full Time and Part Time.
- **Scoring (`score_listings`):** each listing gets these components, each in [0, 1]:

  | Component | Weight | How it is computed |
  |---|---|---|
  | `skills` | 0.30 | Skills are split on `, ; / & and`; for each skill, the fraction of its tokens found in the listing's title + company (exact, plural-stemmed, or fuzzy ratio >= 0.85 for tokens of 5+ chars), averaged over skills |
  | `text` | 0.10 | TF-IDF (word) cosine between *skills + job title* and the listing's title + company |
  | `title` | 0.20 | TF-IDF (character 3-5-gram) cosine between the job title typed and the listing title |
  | `location` | 0.20 | 1 if the location matches the listing's city or state (equal, contained, or fuzzy >= 0.85); **Virtual Internship listings match any location** |
  | `mode` | 0.08 | 1 if the job type equals the requested mode; "remote", "online", "WFH", "virtual" map to Virtual Internship |
  | `stipend` | 0.08 | 1 if stipend >= desired, otherwise stipend / desired (soft penalty; unpaid = 0) |
  | `duration` | 0.04 | `exp(-abs(months - desired) / 3)`; only via the API's optional `Duration` field |

  Components whose input is empty are left out and the remaining weights are renormalised, so
  `match_score` is the weighted mean of the active components, in [0, 1]. If the location is
  "remote" (or the mode is remote and no location is given), virtual listings get full location
  credit. Ties are broken deterministically (higher stipend, then dataset row order).
- **Explanations:** every result carries `reasons` (e.g. "Matched skills: computer, data
  entry", "Title similar to “Computer Operator” (97%)", "In your preferred state (Kerala)",
  "Virtual internship: works from any location", "Stipend ₹5,000/month is below your
  ₹10,000/month target"), `matched_skills` and a per-component `score_breakdown`. The results
  page shows the reasons under each card.
- **No ML classifier.** Earlier versions blended in a RandomForest "match probability" (70% of
  the score). It was trained on listing-only features against a per-listing `Label` column that
  is essentially "stipend >= ₹8,000" (294 of 299 positives) and did not depend on the student,
  so every query got roughly the same listings. There are no candidate-listing labels
  (applications, clicks, selections) to train a pairwise model honestly, so the classifier,
  `train.py`, `preprocess.py` and `internship_model.pkl` were removed (they remain in git
  history). scikit-learn is still used for TF-IDF.
- **API (`internship-recommender/main.py`):** FastAPI with `GET /`, `GET /status` and
  `POST /recommend?top_k=5`. Body (all fields optional):
  `{"Skillset", "Stipend", "Experience", "JobTitle", "Mode", "Location"}`. `Skillset` also
  accepts the alias `Skills` and a list; `Stipend`/`Duration` accept numbers or text such as
  "₹10,000/month", "12k", "8 weeks". The old payload `{JobTitle, Mode, Location, Stipend?,
  Duration?}` still works. The response keeps `match_probability` for compatibility; it now
  equals the top result's `match_score`.
- **Frontend (`Final-Sih-Night/`):** React 19 + Vite + Tailwind; the step-by-step form sends
  all six fields to the API and the results page shows each card's location, stipend, score
  and reasons.
- **Deployment:** one Vercel project. The Vite build is served as static files and
  `api/index.py` runs the FastAPI app as a Python serverless function mounted at `/api`
  (`vercel.json` rewrites `/api/*` to it). The frontend calls `${VITE_API_BASE}` which
  defaults to the relative path `/api`.

Example:

```bash
curl -X POST "https://internship-recommender-zeta.vercel.app/api/recommend?top_k=5" \
  -H "Content-Type: application/json" \
  -d '{"Skillset": "computer, data entry", "Stipend": "5000", "Experience": "none",
       "JobTitle": "Computer Operator", "Mode": "Part Time", "Location": "Uttar Pradesh"}'
```

## Limitations

- **Hand-set weights, no learned relevance.** The weights above are chosen by hand, not fitted,
  because the dataset has no record of which students applied to or were selected for which
  internships. Scores are a transparent heuristic, not a probability of selection.
- **Skills are matched against titles only.** Listings have no skills or description text, so
  a skill counts only if its words appear in the title or company name. Most listings are urban
  local-body schemes (Swachh Bharat Mission, DAY-NULM, PM SVANidhi, solid waste management,
  social media / IEC, computer operator, finance); skills like "Python" or "React" match
  nothing.
- **Experience is collected but not used for ranking**: the data has no experience
  requirement. It is accepted and echoed back by the API.
- **Location matching is string-based**, not geographic: "Bengaluru" does not match "Bangalore
  Urban", and a nearby city in another state gets no credit. Only 12 listings are virtual.
- **Stale data**: the dataset is a 2023 snapshot; application deadlines have passed.
- Text matching is English-only with simple plural stemming; no full stemmer or synonyms.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q          # from the repo root
```

`tests/test_recommender.py` checks that different inputs give different top-5s, that each form
field changes the ranking, that duplicates never appear (in the cleaned data or in results),
that remote/virtual matching works, that scoring is deterministic, the stipend soft penalty,
the reasons, input parsing, and the API with both the new and the old payloads.

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

## Repo layout

```
api/index.py                 Vercel serverless entrypoint (mounts the FastAPI app at /api)
internship-recommender/      FastAPI backend (ranking logic in api/utils.py)
tests/                       pytest suite for the ranking
Final-Sih-Night/             React + Vite frontend
data/                        AICTE internship datasets (CSV)
vercel.json                  Vercel build + routing config
```

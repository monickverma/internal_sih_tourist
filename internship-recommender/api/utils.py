"""Input-dependent, explainable internship ranking.

Every score component below is computed from what the student typed, so
different inputs produce different rankings, and each component that fires
also produces a human-readable "why" reason for the result card.

The AICTE dataset has these usable columns: Job Title, Job Type, Company Name,
Cities, States, Stipend / StipendValue, Duration. There is no skills,
description or experience-requirement column, so "skill" matching is done
against the listing's title + company text.
"""
from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

DATA_FILE = Path(__file__).parent.parent.parent / "data" / "Aicte_Internship_With_Feedback.csv"

# Weight of each component. Components whose input the student left empty are
# dropped and the remaining weights are renormalised, so match_score is in [0, 1].
WEIGHTS = {
    "skills": 0.30,    # fraction of the student's skill keywords found in the listing
    "text": 0.10,      # TF-IDF word cosine: (skills + job title) vs listing title + company
    "title": 0.20,     # TF-IDF char-n-gram cosine: job title vs listing title
    "location": 0.20,  # city/state match; virtual listings match any location
    "mode": 0.08,      # Full Time / Part Time / Virtual Internship
    "stipend": 0.08,   # 1 if stipend >= desired, else stipend / desired
    "duration": 0.04,  # closeness to desired duration (months), legacy field
}

STOPWORDS = {
    "and", "or", "the", "of", "for", "in", "on", "to", "an", "a", "at", "with", "by",
    "under", "viz", "intern", "interns", "internship", "intership", "inter", "trainee",
}

MODES = {
    "full time": "Full Time",
    "part time": "Part Time",
    "virtual internship": "Virtual Internship",
}
NEAR_DUP_TITLE_SIM = 0.9
REMOTE_WORDS = {"remote", "virtual", "online", "wfh", "work from home", "anywhere", "home"}

_state: Optional[dict] = None


# ----------------- text helpers -----------------
def _norm_text(s) -> str:
    s = "" if s is None or (isinstance(s, float) and np.isnan(s)) else str(s)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s.lower())).strip()


def _stem(tok: str) -> str:
    if len(tok) > 4 and tok.endswith("ies"):
        return tok[:-3] + "y"
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def tokenize(s) -> list[str]:
    """Lowercase alphanumeric tokens, stopwords removed, light plural stemming."""
    return [_stem(t) for t in _norm_text(s).split() if t not in STOPWORDS and len(t) > 1]


def split_skills(skills) -> list[str]:
    """'Python, Data Analysis; SQL' or ['Python', ...] -> ['python', 'data analysis', 'sql']."""
    if skills is None:
        return []
    if isinstance(skills, (list, tuple)):
        parts = [str(x) for x in skills]
    else:
        parts = re.split(r"[,;/|\n]+|\band\b|&", str(skills), flags=re.I)
    out, seen = [], set()
    for p in parts:
        p = _norm_text(p)
        if p and tokenize(p) and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def parse_amount(v) -> Optional[float]:
    """'₹10,000/month' -> 10000, '12k' -> 12000, 8000 -> 8000, '' -> None."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v) if v >= 0 else None
    s = str(v).lower().replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(k|thousand|lakh|lac)?", s)
    if not m:
        return None
    n = float(m.group(1))
    mult = {"k": 1e3, "thousand": 1e3, "lakh": 1e5, "lac": 1e5}.get(m.group(2) or "", 1)
    return n * mult


def parse_duration_months(v) -> Optional[float]:
    """'8 Weeks' -> 2.0, '45days' -> 1.5, '1 Years' -> 12, '6Months' -> 6, 'Months' -> None."""
    if v is None or v == "" or (isinstance(v, float) and np.isnan(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v) if v > 0 else None
    s = str(v).lower()
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if not m:
        return None
    n = float(m.group(1))
    if "week" in s:
        n = n / 4.0
    elif "day" in s:
        n = n / 30.0
    elif "year" in s:
        n = n * 12
    return round(n, 2) if n > 0 else None


def normalize_mode(mode) -> Optional[str]:
    """Map free-text mode to one of the dataset's job types (remote -> Virtual Internship)."""
    m = _norm_text(mode)
    if not m:
        return None
    if any(w in m for w in REMOTE_WORDS):
        return "Virtual Internship"
    if m in MODES:
        return MODES[m]
    if "part" in m:
        return "Part Time"
    if "full" in m:
        return "Full Time"
    best = difflib.get_close_matches(m, list(MODES), n=1, cutoff=0.6)
    return MODES[best[0]] if best else None


def _fmt_money(x: float) -> str:
    return f"₹{int(round(x)):,}/month"


# ----------------- data loading + dedup -----------------
def _key(s) -> str:
    """Normalisation used for duplicate detection: case, punctuation, spacing and
    plurals are ignored ('SELF HELP GROUPS' == 'Self-Help Group', 'DAY-NULM' == 'DAYNULM')."""
    return "".join(_stem(t) for t in _norm_text(s).split())


def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    """Drop listings that are identical after normalising the fields shown to students."""
    key = pd.DataFrame({
        "title": df["Job Title"].map(_key),
        "company": df["Company Name"].map(_key),
        "city": df["Cities"].map(_key),
        "state": df["States"].map(_key),
        "type": df["Job Type"].map(_norm_text),
        "stipend": df["StipendValue"].fillna(0).astype(int),
        "duration": df["DurationMonths"].fillna(-1),
    })
    keep = ~key.duplicated(keep="first")
    return df[keep].reset_index(drop=True)


def load_data(path: Path = DATA_FILE) -> dict:
    """Load, clean and dedupe the dataset and build the text indexes once per process."""
    global _state
    if _state is not None and _state["path"] == path:
        return _state
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path}")
    raw = pd.read_csv(path)
    df = raw.rename(columns={"Unnamed: 0": "row_id"})
    if "row_id" not in df.columns:
        df["row_id"] = np.arange(len(df))
    df = df.dropna(subset=["Job Title"]).copy()
    for c in ["Job Title", "Job Type", "Company Name", "Cities", "States", "Stipend", "Duration"]:
        df[c] = df[c].fillna("").astype(str).str.strip()
    df["Job Title"] = df["Job Title"].str.replace(r"\s+", " ", regex=True)
    df["StipendValue"] = pd.to_numeric(df["StipendValue"], errors="coerce").fillna(0).clip(lower=0)
    df["DurationMonths"] = df["Duration"].map(parse_duration_months)
    n_raw = len(df)
    df = dedupe(df)

    text = (df["Job Title"] + " " + df["Company Name"]).tolist()
    # Binary token matrix over title + company, for exact/fuzzy skill keyword overlap.
    token_vec = CountVectorizer(tokenizer=tokenize, lowercase=False, binary=True, token_pattern=None)
    token_mat = token_vec.fit_transform(text).tocsc()
    # Word TF-IDF over title + company, for (skills + title) cosine.
    word_vec = TfidfVectorizer(tokenizer=tokenize, lowercase=False, sublinear_tf=True, token_pattern=None)
    word_mat = word_vec.fit_transform(text)
    # Character n-gram TF-IDF over the title only (robust to SWACHH/SWACCH, DAY-NULM/DAYNULM).
    char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True, sublinear_tf=True)
    char_mat = char_vec.fit_transform(df["Job Title"].map(_norm_text))

    _state = {
        "path": path,
        "df": df,
        "n_raw": n_raw,
        "token_vec": token_vec,
        "token_mat": token_mat,
        "vocab": token_vec.vocabulary_,
        "word_vec": word_vec,
        "word_mat": word_mat,
        "char_vec": char_vec,
        "char_mat": char_mat,
        "cities": df["Cities"].map(_norm_text).to_numpy(),
        "company_key": df["Company Name"].map(_key).to_numpy(),
        "city_key": df["Cities"].map(_key).to_numpy(),
        "states": df["States"].map(_norm_text).to_numpy(),
    }
    return _state


# ----------------- scoring components -----------------
def _token_columns(tok: str, vocab: dict) -> list[int]:
    """Vocabulary columns matching a token exactly or fuzzily (ratio >= 0.85, len >= 5)."""
    cols = [vocab[tok]] if tok in vocab else []
    if len(tok) >= 5:
        for v in difflib.get_close_matches(tok, [w for w in vocab if len(w) >= 5], n=5, cutoff=0.85):
            if v != tok:
                cols.append(vocab[v])
    return cols


def skill_overlap(skills: list[str], st: dict):
    """Per listing: mean over skills of the fraction of that skill's tokens present.
    Returns (scores, matched) where matched[i] lists skills fully present in listing i."""
    n = st["df"].shape[0]
    mat, vocab = st["token_mat"], st["vocab"]
    total = np.zeros(n)
    full = []
    for sk in skills:
        toks = list(dict.fromkeys(tokenize(sk)))
        hits = np.zeros(n)
        for t in toks:
            cols = _token_columns(t, vocab)
            if cols:
                hits += (np.asarray(mat[:, cols].sum(axis=1)).ravel() > 0)
        frac = hits / len(toks)
        total += frac
        full.append(frac >= 0.999)
    scores = total / max(len(skills), 1)
    matched = [[sk for sk, f in zip(skills, full) if f[i]] for i in range(n)] if skills else [[] for _ in range(n)]
    return scores, matched


def _place_match(query: str, places: Iterable[str]) -> np.ndarray:
    """1 where query and place are equal, contain each other, or fuzzy ratio >= 0.85."""
    q = _norm_text(query)
    cache: dict[str, float] = {}
    out = []
    for p in places:
        if p not in cache:
            ok = bool(p) and (p == q or (len(p) >= 4 and p in q) or (len(q) >= 4 and q in p)
                              or difflib.SequenceMatcher(None, q, p).ratio() >= 0.85)
            cache[p] = 1.0 if ok else 0.0
        out.append(cache[p])
    return np.array(out)


def score_listings(candidate: dict, st: dict) -> tuple[np.ndarray, dict, dict]:
    """Return (match_score, component_scores, extras) for every listing."""
    df = st["df"]
    n = len(df)
    title = (candidate.get("JobTitle") or "").strip()
    skills = split_skills(candidate.get("Skillset"))
    loc = (candidate.get("Location") or "").strip()
    mode = normalize_mode(candidate.get("Mode"))
    remote_pref = mode == "Virtual Internship"
    stipend = parse_amount(candidate.get("Stipend"))
    duration = parse_duration_months(candidate.get("Duration"))

    comp: dict[str, np.ndarray] = {}
    extras: dict = {"matched_skills": [[] for _ in range(n)], "loc_kind": None}

    if skills:
        comp["skills"], extras["matched_skills"] = skill_overlap(skills, st)
    query_text = " ".join(skills + [title]).strip()
    if query_text and tokenize(query_text):
        q = st["word_vec"].transform([query_text])
        comp["text"] = linear_kernel(q, st["word_mat"]).ravel()
    if title and _norm_text(title):
        q = st["char_vec"].transform([_norm_text(title)])
        comp["title"] = linear_kernel(q, st["char_mat"]).ravel()

    is_virtual = (df["Job Type"] == "Virtual Internship").to_numpy()
    loc_is_remote = _norm_text(loc) in REMOTE_WORDS
    if loc and _norm_text(loc) and not loc_is_remote:
        city = _place_match(loc, st["cities"])
        state = _place_match(loc, st["states"])
        comp["location"] = np.maximum.reduce([city, state, is_virtual.astype(float)])
        extras["loc_kind"] = np.where(is_virtual, "virtual", np.where(city > 0, "city", np.where(state > 0, "state", "")))
    elif remote_pref or loc_is_remote:
        # Remote student with no physical location: any listing is reachable; virtual ones fit best.
        comp["location"] = np.where(is_virtual, 1.0, 0.0)
        extras["loc_kind"] = np.where(is_virtual, "virtual", "")

    if mode:
        comp["mode"] = (df["Job Type"] == mode).to_numpy().astype(float)
    if stipend:
        sv = df["StipendValue"].to_numpy(dtype=float)
        comp["stipend"] = np.clip(sv / stipend, 0.0, 1.0)
    if duration:
        dm = df["DurationMonths"].to_numpy(dtype=float)
        comp["duration"] = np.where(np.isnan(dm), 0.0, np.exp(-np.abs(dm - duration) / 3.0))

    if comp:
        wsum = sum(WEIGHTS[k] for k in comp)
        score = sum(WEIGHTS[k] * v for k, v in comp.items()) / wsum
    else:
        score = np.zeros(n)
    extras.update(skills=skills, title=title, loc=loc, mode=mode, stipend=stipend, duration=duration)
    return score, comp, extras


def _reasons(i: int, row: pd.Series, comp: dict, ex: dict) -> list[str]:
    r = []
    if ex["matched_skills"][i]:
        r.append("Matched skills: " + ", ".join(ex["matched_skills"][i]))
    elif "skills" in comp and comp["skills"][i] > 0:
        r.append(f"Partially matches your skills ({comp['skills'][i]:.0%} of keywords)")
    if "title" in comp and comp["title"][i] >= 0.3:
        r.append(f"Title similar to “{ex['title']}” ({comp['title'][i]:.0%})")
    kind = ex["loc_kind"][i] if ex["loc_kind"] is not None else ""
    if kind == "virtual":
        r.append("Virtual internship: works from any location")
    elif kind == "city":
        r.append(f"In your preferred location ({row['Cities']}, {row['States']})")
    elif kind == "state":
        r.append(f"In your preferred state ({row['States']})")
    if "mode" in comp and comp["mode"][i] == 1:
        r.append(f"Mode matches: {row['Job Type']}")
    if ex["stipend"]:
        sv = float(row["StipendValue"])
        if sv >= ex["stipend"]:
            r.append(f"Stipend {_fmt_money(sv)} meets your {_fmt_money(ex['stipend'])} target")
        elif sv > 0:
            r.append(f"Stipend {_fmt_money(sv)} is below your {_fmt_money(ex['stipend'])} target")
        else:
            r.append("Unpaid (below your stipend target)")
    if "duration" in comp and comp["duration"][i] >= 0.7:
        r.append(f"Duration {row['Duration']} is close to your preference")
    return r


# ----------------- public API -----------------
def recommend(candidate: dict, top_k: int = 5, path: Path = DATA_FILE) -> dict:
    st = load_data(path)
    df = st["df"]
    score, comp, ex = score_listings(candidate, st)
    score = np.round(score, 6)
    # Deterministic order: score desc, then stipend desc, then original row id asc.
    order = np.lexsort((df["row_id"].to_numpy(), -df["StipendValue"].to_numpy(), -score))
    # Skip near-duplicates of an already selected card: same employer and city with a
    # near-identical title (e.g. the same posting listed as both Full Time and Part Time).
    top: list[int] = []
    k = max(1, int(top_k))
    for i in order:
        if any(st["company_key"][i] == st["company_key"][j] and st["city_key"][i] == st["city_key"][j]
               and (st["char_mat"][i] @ st["char_mat"][j].T).toarray()[0, 0] >= NEAR_DUP_TITLE_SIM
               for j in top):
            continue
        top.append(int(i))
        if len(top) == k:
            break

    recs = []
    for i in top:
        row = df.iloc[i]
        recs.append({
            "id": int(row["row_id"]),
            "JobTitle": row["Job Title"],
            "CompanyName": row["Company Name"],
            "Cities": row["Cities"],
            "States": row["States"],
            "JobType": row["Job Type"],
            "Stipend": row["Stipend"],
            "StipendValue": int(row["StipendValue"]),
            "Duration": row["Duration"],
            "match_score": float(score[i]),
            "matched_skills": ex["matched_skills"][i],
            "reasons": _reasons(i, row, comp, ex),
            "score_breakdown": {k: round(float(v[i]), 4) for k, v in comp.items()},
        })
    return {
        "probability": float(score[top[0]]) if len(top) else 0.0,
        "used_components": {k: WEIGHTS[k] for k in comp},
        "recommendations": recs,
    }

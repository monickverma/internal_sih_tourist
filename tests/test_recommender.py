"""Run from the repo root:  pip install -r requirements-dev.txt && pytest -q"""
import itertools

import pytest

from api import utils

PROFILES = [
    {"Skillset": "social media, communication", "Stipend": "₹8,000/month", "Experience": "1 year",
     "JobTitle": "Communications Intern", "Mode": "Full Time", "Location": "Kerala"},
    {"Skillset": "computer, data entry", "Stipend": "5000", "JobTitle": "Computer Operator",
     "Mode": "Part Time", "Location": "Uttar Pradesh"},
    {"Skillset": "solid waste management, sanitation", "JobTitle": "SWM trainee",
     "Mode": "Full Time", "Location": "Karnataka"},
    {"JobTitle": "Finance Intern", "Mode": "Full Time", "Location": "Kerala"},
    {"Skillset": "urban planning", "JobTitle": "Town Planning Intern", "Mode": "Full Time",
     "Location": "Bangalore", "Stipend": "10k"},
    {"Skillset": "street vendors, livelihood", "JobTitle": "PM SVANidhi intern", "Mode": "remote",
     "Location": "Madhya Pradesh"},
]


def ids(candidate, k=5):
    return [r["id"] for r in utils.recommend(candidate, top_k=k)["recommendations"]]


def test_different_inputs_give_different_top5():
    tops = [tuple(ids(p)) for p in PROFILES]
    for a, b in itertools.combinations(range(len(tops)), 2):
        assert tops[a] != tops[b], (PROFILES[a], PROFILES[b])
    # and they are not just reorderings of one fixed set
    assert len(set().union(*map(set, tops))) >= 4 * 5


@pytest.mark.parametrize("field,values", [
    ("Skillset", ["social media", "solid waste management"]),
    ("Location", ["Kerala", "Uttar Pradesh"]),
    ("Stipend", ["0", "12000"]),
])
def test_each_field_changes_ranking(field, values):
    base = {"JobTitle": "Intern", "Mode": "Full Time", "Location": "Karnataka"}
    a, b = ({**base, field: v} for v in values)
    assert ids(a, 10) != ids(b, 10)


def test_dataset_is_deduplicated():
    st = utils.load_data()
    df = st["df"]
    assert st["n_raw"] > len(df)  # the raw CSV does contain duplicates
    key = df[["Job Title", "Company Name", "Cities", "States", "Job Type"]].apply(
        lambda c: c.map(utils._key)
    )
    key["stipend"] = df["StipendValue"]
    key["duration"] = df["DurationMonths"].fillna(-1)
    assert not key.duplicated().any()


@pytest.mark.parametrize("candidate", PROFILES)
def test_no_duplicate_cards_in_results(candidate):
    recs = utils.recommend(candidate, top_k=30)["recommendations"]
    assert len({r["id"] for r in recs}) == len(recs)
    shown = [(utils._key(r["JobTitle"]), utils._key(r["CompanyName"]), utils._key(r["Cities"]),
              r["JobType"], r["StipendValue"], r["Duration"]) for r in recs]
    assert len(set(shown)) == len(shown)
    # no near-duplicates either: same employer + city + same normalised title
    loose = [(utils._key(r["JobTitle"]), utils._key(r["CompanyName"]), utils._key(r["Cities"])) for r in recs]
    assert len(set(loose)) == len(loose)


def test_remote_mode_matches_any_location():
    assert utils.normalize_mode("Remote") == "Virtual Internship"
    assert utils.normalize_mode("work from home") == "Virtual Internship"
    out = utils.recommend({"JobTitle": "SBM internship", "Mode": "remote", "Location": "Kerala"}, top_k=5)
    recs = out["recommendations"]
    # No Kerala listing is virtual, yet virtual listings elsewhere rank on top with full location credit.
    assert all(r["JobType"] == "Virtual Internship" for r in recs)
    assert all(r["States"] != "Kerala" for r in recs)
    for r in recs:
        assert r["score_breakdown"]["location"] == 1.0
        assert any("any location" in x for x in r["reasons"])


def test_remote_location_word_without_mode():
    recs = utils.recommend({"JobTitle": "SBM internship", "Location": "remote"}, top_k=3)["recommendations"]
    assert all(r["JobType"] == "Virtual Internship" for r in recs)


def test_scoring_is_deterministic():
    for p in PROFILES:
        a = utils.recommend(p, top_k=10)
        utils._state = None  # force a cold reload
        b = utils.recommend(p, top_k=10)
        assert a == b


def test_stipend_is_soft_penalty():
    out = utils.recommend({"JobTitle": "Finance Intern", "Location": "Kerala", "Stipend": "20000"}, top_k=5)
    recs = out["recommendations"]
    assert recs, "below-target listings must still be returned"
    assert all(0 < r["score_breakdown"]["stipend"] < 1 for r in recs if 0 < r["StipendValue"] < 20000)
    assert any("below your" in x for r in recs for x in r["reasons"])


def test_reasons_and_matched_skills():
    recs = utils.recommend(PROFILES[1], top_k=5)["recommendations"]
    for r in recs:
        assert r["reasons"]
        assert 0.0 <= r["match_score"] <= 1.0
    assert any("computer" in r["matched_skills"] for r in recs)
    assert any(x.startswith("Matched skills:") for x in recs[0]["reasons"])


def test_parsers():
    assert utils.parse_amount("₹10,000/month") == 10000
    assert utils.parse_amount("12k") == 12000
    assert utils.parse_amount("") is None
    assert utils.parse_duration_months("8 Weeks") == 2
    assert utils.parse_duration_months("1 Years") == 12
    assert utils.parse_duration_months("Months") is None
    assert utils.split_skills("Python, Data Analysis; SQL") == ["python", "data analysis", "sql"]


def test_api_accepts_all_form_fields_and_old_payload():
    from fastapi.testclient import TestClient
    from main import app

    c = TestClient(app)
    new = c.post("/recommend?top_k=5", json=PROFILES[0])
    assert new.status_code == 200, new.text
    body = new.json()
    assert body["candidate"]["Skillset"] == PROFILES[0]["Skillset"]
    assert len(body["recommendations"]) == 5
    assert all(r["reasons"] for r in body["recommendations"])
    assert "skills" in body["weights"] and "stipend" in body["weights"]

    old = c.post("/recommend", json={"JobTitle": "Finance Intern", "Mode": "Full Time", "Location": "Kerala",
                                     "Stipend": 5000, "Duration": 2})
    assert old.status_code == 200, old.text
    assert old.json()["recommendations"][0]["JobTitle"]

    alias = c.post("/recommend", json={"Skills": ["computer"], "JobTitle": "", "Mode": "", "Location": ""})
    assert alias.status_code == 200
    assert alias.json()["recommendations"][0]["matched_skills"] == ["computer"]

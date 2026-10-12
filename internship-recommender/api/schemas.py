# api/schemas.py
from typing import Any, Dict, List, Optional, Union

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


# --- Input schema (what frontend sends) ---
# Old clients sent {JobTitle, Mode, Location, Stipend?, Duration?}; those still work.
# New fields: Skillset (alias "Skills"), Experience. Stipend/Duration may be numbers or
# free text such as "₹10,000/month" or "8 weeks" (parsed server-side).
class CandidateIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    JobTitle: str = ""
    Mode: str = ""
    Location: str = ""
    Skillset: Optional[Union[str, List[str]]] = Field(
        default=None, validation_alias=AliasChoices("Skillset", "Skills", "skills")
    )
    Stipend: Optional[Union[int, float, str]] = None
    Duration: Optional[Union[int, float, str]] = None
    Experience: Optional[Union[int, float, str]] = None
    candidate_id: Optional[str] = None


# --- Output schema for one internship ---
class InternshipOut(BaseModel):
    id: Optional[Any] = None
    JobTitle: str
    CompanyName: str
    Cities: str = ""
    States: str
    JobType: str
    Stipend: str = ""
    StipendValue: int = 0
    Duration: str = ""
    match_score: float
    matched_skills: List[str] = []
    reasons: List[str] = []
    score_breakdown: Dict[str, float] = {}


# --- Output schema for recommendation API ---
class RecommendOut(BaseModel):
    candidate: CandidateIn
    # Kept for backward compatibility: equals the top recommendation's match_score.
    match_probability: float
    weights: Dict[str, float] = {}
    recommendations: List[InternshipOut]

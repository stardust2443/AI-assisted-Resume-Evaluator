"""
data_models.py — All Pydantic schemas for the AI Resume Evaluator.

Design principles:
- Rubric weights: skill_match=25, experience_depth=35, role_alignment=30, additional_strengths=10
- Explainability constraint: every EvidenceScore MUST carry verbatim quotes.
  The application layer enforces score=0 if evidence_quotes is empty.
- LLM-computed total_score is NEVER trusted — always recomputed downstream.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional


# ---------------------------------------------------------------------------
# Resume Structure
# ---------------------------------------------------------------------------

class WorkExperience(BaseModel):
    company: str
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None        # "Present" or date string
    duration_months: Optional[int] = None
    responsibilities: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[float] = None


class Project(BaseModel):
    name: str
    description: str
    technologies: List[str] = Field(default_factory=list)
    url: Optional[str] = None


class ParsedResume(BaseModel):
    candidate_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    work_experience: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    awards_and_achievements: List[str] = Field(default_factory=list)
    raw_text: str = Field(description="Original unmodified resume text")


# ---------------------------------------------------------------------------
# Job Description Structure
# ---------------------------------------------------------------------------

class JDRequirements(BaseModel):
    role_title: str
    seniority_level: Optional[str] = None          # e.g., "Senior", "IC4", "L5"
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    min_years_experience: Optional[float] = None
    key_responsibilities: List[str] = Field(default_factory=list)
    industry_domain: Optional[str] = None
    raw_text: str = Field(description="Original unmodified JD text")


# ---------------------------------------------------------------------------
# Scoring — Core Building Block
# ---------------------------------------------------------------------------

class EvidenceScore(BaseModel):
    """
    A single rubric section score with mandatory evidence.

    Explainability constraint: if evidence_quotes is empty, the application
    layer MUST zero out the score. Never award points without a source quote.
    """
    score: int = Field(ge=0, description="Points awarded for this rubric section")
    reasoning: str = Field(description="Semantic explanation of why this score was given")
    evidence_quotes: List[str] = Field(
        description=(
            "Exact verbatim quotes extracted from the resume that justify each point awarded. "
            "Must be non-empty if score > 0. Quotes must appear verbatim in the original resume text."
        )
    )
    flagged_unverified: bool = Field(
        default=False,
        description="Set to True by the validator if any quote could not be verified in the source text"
    )


# ---------------------------------------------------------------------------
# Rubric Evaluation
# ---------------------------------------------------------------------------

class RubricEvaluation(BaseModel):
    """
    Rubric weights: skill_match=25, experience_depth=35, role_alignment=30, additional_strengths=10
    total_score is ALWAYS recomputed by the validator — never trust the LLM-provided value.
    """
    skill_match: EvidenceScore = Field(
        description="Max 25 points. Semantic match between candidate's skills and JD requirements."
    )
    experience_depth: EvidenceScore = Field(
        description=(
            "Max 35 points. Years of relevant experience, scale of impact, "
            "complexity and seniority of past roles."
        )
    )
    role_alignment: EvidenceScore = Field(
        description=(
            "Max 30 points. Has the candidate performed this specific job function before? "
            "Look for direct role title/responsibility overlap."
        )
    )
    additional_strengths: EvidenceScore = Field(
        description=(
            "Max 10 points. Open-source contributions, notable projects, publications, "
            "awards, or exceptional extracurriculars."
        )
    )
    total_score: int = Field(
        description="Sum of all section scores. Recomputed deterministically by the validator."
    )

    @model_validator(mode="after")
    def total_must_be_100_or_less(self) -> "RubricEvaluation":
        if self.total_score > 100:
            raise ValueError(f"total_score {self.total_score} exceeds 100")
        return self


# ---------------------------------------------------------------------------
# SWOT + Report
# ---------------------------------------------------------------------------

class SWOTAnalysis(BaseModel):
    strengths: List[str] = Field(description="Candidate's key strengths relative to the JD")
    weaknesses: List[str] = Field(description="Gaps or shortcomings versus the JD requirements")
    opportunities: List[str] = Field(description="Potential growth areas if hired")
    threats: List[str] = Field(description="Risks: overqualification, culture fit, intent concerns")


class CandidateReport(BaseModel):
    candidate_name: str
    evaluation: RubricEvaluation
    swot: SWOTAnalysis
    suggestions_for_improvement: List[str] = Field(
        description="Specific, actionable suggestions for the candidate to strengthen their profile"
    )


# ---------------------------------------------------------------------------
# API Schemas
# ---------------------------------------------------------------------------

class EvaluationRequest(BaseModel):
    """For programmatic (non-file-upload) API calls."""
    resume_text: str
    jd_text: str


class RankedCandidate(BaseModel):
    rank: int
    percentile: float = Field(description="Relative percentile among this batch (0–100)")
    report: CandidateReport


class CompareResponse(BaseModel):
    total_candidates: int
    ranked: List[RankedCandidate]
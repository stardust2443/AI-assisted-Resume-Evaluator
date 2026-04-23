"""
config.py — Centralized configuration for the AI Resume Evaluator.
LLM provider: Google Gemini (free tier via google-generativeai).
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Rubric Weights (must sum to 100)
# ---------------------------------------------------------------------------
RUBRIC_WEIGHTS: dict[str, int] = {
    "skill_match": 25,
    "experience_depth": 35,
    "role_alignment": 30,
    "additional_strengths": 10,
}

assert sum(RUBRIC_WEIGHTS.values()) == 100, "Rubric weights must sum to 100"


# ---------------------------------------------------------------------------
# LLM Settings
# ---------------------------------------------------------------------------
@dataclass
class LLMConfig:
    # gemini-2.5-flash: available on this free-tier project with JSON mode support
    model: str = "models/gemini-2.5-flash"
    temperature: float = 0.0          # Deterministic scoring
    max_tokens_parse: int = 8192      # Parse tokens raised — large resumes can have 100+ fields
    max_tokens_score: int = 8192      # Scoring: 4 sections × reasoning + quotes
    max_tokens_report: int = 3000     # SWOT + suggestions
    timeout_seconds: int = 60


# ---------------------------------------------------------------------------
# Application Settings
# ---------------------------------------------------------------------------
@dataclass
class AppConfig:
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    llm: LLMConfig = field(default_factory=LLMConfig)

    # Supported file types for resume and JD upload
    allowed_extensions: tuple[str, ...] = (".pdf", ".docx", ".txt")

    # Evaluation framework settings
    eval_consistency_runs: int = 5
    eval_consistency_threshold: float = 5.0

    # Evidence validation: min similarity ratio for fuzzy quote matching
    quote_match_threshold: float = 0.85

    def validate(self) -> None:
        if not self.gemini_api_key:
            raise EnvironmentError("GEMINI_API_KEY is not set in environment.")


# Singleton — import this everywhere
settings = AppConfig()

"""
parser/jd_parser.py — LLM-based structured extraction from a Job Description.
Uses llm.client — provider-agnostic.
"""

import logging
from pathlib import Path

from llm.client import complete_json
from config import settings
from data_models import JDRequirements

logger = logging.getLogger(__name__)


_JD_PARSE_SYSTEM = """\
You are a precise job description parser. Extract structured hiring requirements from the JD text.
Return ONLY valid JSON matching the schema below. Do not hallucinate.
If a field is truly absent, use null or an empty list.

Schema:
{
  "role_title": "string",
  "seniority_level": "string or null",
  "required_skills": ["string"],
  "preferred_skills": ["string"],
  "min_years_experience": "float or null",
  "key_responsibilities": ["string"],
  "industry_domain": "string or null"
}

Guidelines:
- required_skills: skills explicitly listed as must-have or required
- preferred_skills: skills listed as nice-to-have or preferred
- min_years_experience: extract the number only (e.g. "5+ years" -> 5.0)
- seniority_level: infer from title or requirements (Junior / Mid / Senior / Staff / Principal)
"""


def parse_jd(raw_text: str) -> JDRequirements:
    """Extract structured requirements from a Job Description text."""
    logger.info("Parsing JD with LLM (%d chars)", len(raw_text))

    data = complete_json(
        system=_JD_PARSE_SYSTEM,
        user=f"JOB DESCRIPTION:\n\n{raw_text}",
        max_tokens=settings.llm.max_tokens_parse,
    )

    return JDRequirements(
        role_title=data.get("role_title", "Unknown Role"),
        seniority_level=data.get("seniority_level"),
        required_skills=[s.lower().strip() for s in data.get("required_skills", [])],
        preferred_skills=[s.lower().strip() for s in data.get("preferred_skills", [])],
        min_years_experience=data.get("min_years_experience"),
        key_responsibilities=data.get("key_responsibilities", []),
        industry_domain=data.get("industry_domain"),
        raw_text=raw_text,
    )


def parse_jd_from_file(file_bytes: bytes, filename: str) -> JDRequirements:
    """Convenience wrapper: extract text from file, then parse."""
    from parser.resume_parser import extract_text
    raw_text = extract_text(file_bytes, filename)
    return parse_jd(raw_text)

"""
parser/resume_parser.py — Document text extraction + LLM-based structured parsing.

Design:
- Text extraction is deterministic (pdfplumber / python-docx / plain text)
- Structured extraction (name, skills, experience, etc.) is LLM-driven via llm.client
- If any section is missing, falls back to empty defaults — never crashes
"""

import io
import logging
from pathlib import Path

import pdfplumber
from docx import Document

from llm.client import complete_json
from config import settings
from data_models import ParsedResume, WorkExperience, Education, Project

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Step 1: Deterministic Text Extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    result = "\n".join(text_parts).strip()
    if not result:
        raise ValueError("PDF parsing returned empty text. File may be image-based or corrupted.")
    return result


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    result = "\n".join(paragraphs).strip()
    if not result:
        raise ValueError("DOCX parsing returned empty text.")
    return result


def extract_text_from_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8").strip()
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1").strip()


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Dispatch to the correct extractor based on file extension."""
    ext = Path(filename).suffix.lower()
    dispatch = {
        ".pdf": extract_text_from_pdf,
        ".docx": extract_text_from_docx,
        ".txt": extract_text_from_txt,
    }
    if ext not in dispatch:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: {list(dispatch.keys())}")
    return dispatch[ext](file_bytes)


# ---------------------------------------------------------------------------
# Step 2: LLM Structured Extraction
# ---------------------------------------------------------------------------

# Max chars of raw resume text fed to the parser
# 6000 chars ≈ 1500 tokens input — leaves plenty of room for JSON output
_MAX_PARSE_INPUT_CHARS = 6000

_RESUME_PARSE_SYSTEM = """\
You are a precise, concise resume parser. Extract structured information from the resume text.
Return ONLY valid JSON matching the schema below. Do not hallucinate fields.
If a field is truly absent, use null or an empty list.

CRITICAL output-size limits (strictly enforce to avoid truncation):
- skills: maximum 25 items. Pick the most relevant/technical ones.
- responsibilities: maximum 4 short bullet points per role (each under 100 chars).
- achievements: maximum 3 per role (each under 100 chars).
- project description: maximum 1 sentence (under 120 chars).
- technologies per project: maximum 5 items.
- certifications: maximum 8 items.
- awards_and_achievements: maximum 5 items.

Schema:
{
  "candidate_name": "string",
  "email": "string or null",
  "phone": "string or null",
  "location": "string or null",
  "skills": ["string"],
  "work_experience": [
    {
      "company": "string",
      "title": "string",
      "start_date": "string or null",
      "end_date": "string or null",
      "duration_months": "int or null",
      "responsibilities": ["string"],
      "achievements": ["string"]
    }
  ],
  "education": [
    {
      "institution": "string",
      "degree": "string",
      "field_of_study": "string or null",
      "graduation_year": "string or null",
      "gpa": "float or null"
    }
  ],
  "projects": [
    {
      "name": "string",
      "description": "string",
      "technologies": ["string"],
      "url": "string or null"
    }
  ],
  "certifications": ["string"],
  "awards_and_achievements": ["string"]
}
"""


def parse_resume(raw_text: str) -> ParsedResume:
    """
    Use the LLM to extract structured fields from raw resume text.
    Attaches raw_text to the output for downstream evidence validation.
    """
    logger.info("Parsing resume with LLM (%d chars)", len(raw_text))

    # Truncate input to prevent extremely long prompts;
    # raw_text is always stored in full on ParsedResume for evidence validation
    parse_input = raw_text[:_MAX_PARSE_INPUT_CHARS]

    data = complete_json(
        system=_RESUME_PARSE_SYSTEM,
        user=f"RESUME TEXT:\n\n{parse_input}",
        max_tokens=settings.llm.max_tokens_parse,
    )

    # Normalize skills: lowercase + deduplicate
    skills = list({s.lower().strip() for s in data.get("skills", []) if s})

    return ParsedResume(
        candidate_name=data.get("candidate_name", "Unknown"),
        email=data.get("email"),
        phone=data.get("phone"),
        location=data.get("location"),
        skills=skills,
        work_experience=[WorkExperience(**e) for e in data.get("work_experience", [])],
        education=[Education(**e) for e in data.get("education", [])],
        projects=[Project(**p) for p in data.get("projects", [])],
        certifications=data.get("certifications", []),
        awards_and_achievements=data.get("awards_and_achievements", []),
        raw_text=raw_text,
    )

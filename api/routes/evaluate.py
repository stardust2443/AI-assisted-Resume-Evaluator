"""
api/routes/evaluate.py — Single candidate evaluation endpoint.

POST /evaluate
- Accepts: resume file (PDF/DOCX/TXT) + JD file or raw JD text
- Orchestrates: extract → parse → score → validate → report
- Returns: CandidateReport as JSON
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from data_models import CandidateReport, EvaluationRequest
from parser.resume_parser import extract_text, parse_resume
from parser.jd_parser import parse_jd
from scoring.rubric import score_candidate
from scoring.validator import validate_evaluation
from reporting.report_generator import generate_report

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_pipeline(resume_text: str, jd_text: str) -> CandidateReport:
    """Core evaluation pipeline. Shared by file-upload and text-input paths."""
    # Layer 2: Parse
    resume = parse_resume(resume_text)
    jd = parse_jd(jd_text)

    # Layer 3: Score + Validate
    raw_evaluation = score_candidate(resume, jd)
    validated_evaluation = validate_evaluation(raw_evaluation, resume_text)

    # Layer 4: Report
    report = generate_report(resume, jd, validated_evaluation)
    return report


@router.post(
    "/evaluate",
    response_model=CandidateReport,
    summary="Evaluate a single candidate against a job description",
    status_code=status.HTTP_200_OK,
)
async def evaluate_file(
    resume: UploadFile = File(..., description="Resume file (.pdf, .docx, or .txt)"),
    job_description: Optional[UploadFile] = File(
        None, description="JD file (.pdf, .docx, or .txt)"
    ),
    jd_text: Optional[str] = Form(
        None, description="Raw JD text (use this OR job_description file, not both)"
    ),
):
    """
    Evaluate a candidate's resume against a job description.

    Accepts:
    - resume: file upload (PDF / DOCX / TXT)
    - job_description: file upload OR jd_text form field

    Returns a fully validated CandidateReport with scores, SWOT, and suggestions.
    """
    # --- Input validation ---
    if job_description is None and not jd_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide either a job_description file or jd_text field.",
        )

    try:
        resume_bytes = await resume.read()
        resume_text = extract_text(resume_bytes, resume.filename or "resume.txt")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    if job_description is not None:
        try:
            jd_bytes = await job_description.read()
            jd_text = extract_text(jd_bytes, job_description.filename or "jd.txt")
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # --- Pipeline ---
    try:
        report = await _run_pipeline(resume_text, jd_text)
    except Exception as e:
        logger.exception("Evaluation pipeline failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )

    return report


@router.post(
    "/evaluate/text",
    response_model=CandidateReport,
    summary="Evaluate using raw text input (no file upload)",
    status_code=status.HTTP_200_OK,
)
async def evaluate_text(body: EvaluationRequest):
    """
    Evaluate using pre-extracted text. Useful for testing or non-file frontends.
    """
    try:
        report = await _run_pipeline(body.resume_text, body.jd_text)
    except Exception as e:
        logger.exception("Evaluation pipeline failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )
    return report

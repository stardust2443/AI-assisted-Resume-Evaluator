"""
api/routes/compare.py — Multi-candidate ranking endpoint.

POST /compare
- Accepts: multiple resume files + one JD file or raw JD text
- Evaluates each resume through the full pipeline (parse → score → validate → report)
- Returns: candidates ranked by total_score (desc) with relative percentile
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from data_models import CandidateReport, CompareResponse, RankedCandidate
from parser.resume_parser import extract_text, parse_resume
from parser.jd_parser import parse_jd
from scoring.rubric import score_candidate
from scoring.validator import validate_evaluation
from reporting.report_generator import generate_report

logger = logging.getLogger(__name__)
router = APIRouter()


def _compute_percentiles(reports: list[CandidateReport]) -> list[float]:
    """
    Compute relative percentile rank for each candidate in the batch.

    Percentile = percentage of other candidates this candidate scored higher than.
    Tied scores get the same percentile.
    Returns percentiles in the same order as input reports.
    """
    scores = [r.evaluation.total_score for r in reports]
    n = len(scores)
    percentiles = []
    for score in scores:
        rank = sum(1 for s in scores if s < score)
        # 100 * (candidates beaten) / (total - 1), floored at 0 for n=1
        pct = round((rank / (n - 1)) * 100, 1) if n > 1 else 100.0
        percentiles.append(pct)
    return percentiles


@router.post(
    "/compare",
    response_model=CompareResponse,
    summary="Evaluate and rank multiple candidates against one job description",
    status_code=status.HTTP_200_OK,
)
async def compare_candidates(
    resumes: List[UploadFile] = File(..., description="Resume files (.pdf, .docx, or .txt)"),
    job_description: Optional[UploadFile] = File(None, description="JD file"),
    jd_text: Optional[str] = Form(None, description="Raw JD text"),
):
    """
    Evaluate multiple candidates against a single JD.
    Returns a ranked list with raw scores and relative percentiles.

    - rank=1 is the best candidate
    - percentile=100 means this candidate outscored everyone else in this batch
    """
    if not resumes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one resume file is required.",
        )
    if job_description is None and not jd_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide either a job_description file or jd_text field.",
        )

    # --- Extract JD text ---
    if job_description is not None:
        try:
            jd_bytes = await job_description.read()
            jd_text = extract_text(jd_bytes, job_description.filename or "jd.txt")
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    jd = parse_jd(jd_text)

    # --- Evaluate each candidate ---
    reports: list[CandidateReport] = []
    failed: list[str] = []

    for resume_file in resumes:
        filename = resume_file.filename or "resume.txt"
        try:
            resume_bytes = await resume_file.read()
            resume_text = extract_text(resume_bytes, filename)
            resume = parse_resume(resume_text)
            raw_eval = score_candidate(resume, jd)
            validated_eval = validate_evaluation(raw_eval, resume_text)
            report = generate_report(resume, jd, validated_eval)
            reports.append(report)
        except Exception as e:
            logger.exception("Failed to evaluate resume: %s", filename)
            failed.append(f"{filename}: {str(e)}")

    if not reports:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"All candidates failed evaluation. Errors: {failed}",
        )

    # --- Rank by total_score descending ---
    reports_sorted = sorted(reports, key=lambda r: r.evaluation.total_score, reverse=True)
    percentiles_sorted = _compute_percentiles(reports_sorted)

    ranked = [
        RankedCandidate(
            rank=i + 1,
            percentile=percentiles_sorted[i],
            report=report,
        )
        for i, report in enumerate(reports_sorted)
    ]

    return CompareResponse(
        total_candidates=len(ranked),
        ranked=ranked,
    )

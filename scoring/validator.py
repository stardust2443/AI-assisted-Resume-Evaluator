"""
scoring/validator.py — Post-LLM validation and score integrity enforcement.

Chain of responsibility applied after every LLM scoring call:
1. verify_quotes      — check each quote exists verbatim in raw resume text
2. zero_unquoted      — zero out scores where no valid quote exists
3. enforce_bounds     — clip scores to their rubric max
4. recompute_total    — deterministically sum sections (never trust LLM total)
"""

import logging
from difflib import SequenceMatcher

from config import RUBRIC_WEIGHTS, settings
from data_models import EvidenceScore, RubricEvaluation

logger = logging.getLogger(__name__)

# Max points per section — single source of truth
_MAX_SCORES: dict[str, int] = {
    "skill_match": RUBRIC_WEIGHTS["skill_match"],
    "experience_depth": RUBRIC_WEIGHTS["experience_depth"],
    "role_alignment": RUBRIC_WEIGHTS["role_alignment"],
    "additional_strengths": RUBRIC_WEIGHTS["additional_strengths"],
}


# ---------------------------------------------------------------------------
# Quote Verification
# ---------------------------------------------------------------------------

def _quote_exists_in_text(quote: str, raw_text: str, threshold: float) -> bool:
    """
    Check if a quote exists in the resume text.
    Uses exact substring match first; falls back to similarity ratio
    for minor whitespace/formatting differences.
    """
    quote_clean = " ".join(quote.lower().split())
    text_clean = " ".join(raw_text.lower().split())

    # Exact substring match (primary)
    if quote_clean in text_clean:
        return True

    # Fuzzy fallback: check if any sliding window of similar length is close enough
    q_len = len(quote_clean)
    if q_len == 0:
        return False

    step = max(1, q_len // 2)
    for start in range(0, max(1, len(text_clean) - q_len + 1), step):
        window = text_clean[start : start + q_len]
        ratio = SequenceMatcher(None, quote_clean, window).ratio()
        if ratio >= threshold:
            return True

    return False


def verify_quotes(
    section: EvidenceScore,
    raw_resume_text: str,
    section_name: str,
) -> EvidenceScore:
    """
    Verify each evidence quote in a section against the raw resume text.
    Returns an updated EvidenceScore with valid_quotes only.
    Flags the section if any quote was rejected.
    """
    threshold = settings.quote_match_threshold
    valid_quotes = []
    flagged = False

    for quote in section.evidence_quotes:
        if _quote_exists_in_text(quote, raw_resume_text, threshold):
            valid_quotes.append(quote)
        else:
            logger.warning(
                "[%s] Quote NOT found in resume text (will be rejected): '%s'",
                section_name,
                quote[:120],
            )
            flagged = True

    return EvidenceScore(
        score=section.score,
        reasoning=section.reasoning,
        evidence_quotes=valid_quotes,
        flagged_unverified=flagged,
    )


# ---------------------------------------------------------------------------
# Zero-Out Unquoted Scores
# ---------------------------------------------------------------------------

def zero_unquoted(section: EvidenceScore, section_name: str) -> EvidenceScore:
    """
    If no valid evidence quotes remain after verification, score must be 0.
    Explainability constraint: no quote = no points.
    """
    if section.score > 0 and not section.evidence_quotes:
        logger.warning(
            "[%s] Score %d zeroed out: no verified evidence quotes.",
            section_name,
            section.score,
        )
        return EvidenceScore(
            score=0,
            reasoning=section.reasoning + " [ZEROED: no verified evidence quotes found]",
            evidence_quotes=[],
            flagged_unverified=True,
        )
    return section


# ---------------------------------------------------------------------------
# Bound Enforcement
# ---------------------------------------------------------------------------

def enforce_bounds(section: EvidenceScore, section_name: str) -> EvidenceScore:
    """Clip section score to its rubric maximum. Catches LLM over-scoring."""
    max_score = _MAX_SCORES[section_name]
    if section.score > max_score:
        logger.warning(
            "[%s] Score %d exceeds max %d — clipping.", section_name, section.score, max_score
        )
        return section.model_copy(update={"score": max_score})
    if section.score < 0:
        logger.warning("[%s] Negative score %d — clamping to 0.", section_name, section.score)
        return section.model_copy(update={"score": 0})
    return section


# ---------------------------------------------------------------------------
# Deterministic Total
# ---------------------------------------------------------------------------

def recompute_total(evaluation: RubricEvaluation) -> int:
    """Sum section scores. This is the ONLY correct total_score — LLM value is discarded."""
    return (
        evaluation.skill_match.score
        + evaluation.experience_depth.score
        + evaluation.role_alignment.score
        + evaluation.additional_strengths.score
    )


# ---------------------------------------------------------------------------
# Full Validation Pipeline
# ---------------------------------------------------------------------------

def validate_evaluation(
    evaluation: RubricEvaluation, raw_resume_text: str
) -> RubricEvaluation:
    """
    Run the complete validation pipeline on a raw LLM-produced RubricEvaluation.
    Order: verify quotes → zero unquoted → enforce bounds → recompute total
    """
    sections = ["skill_match", "experience_depth", "role_alignment", "additional_strengths"]
    validated: dict[str, EvidenceScore] = {}

    for name in sections:
        section: EvidenceScore = getattr(evaluation, name)
        section = verify_quotes(section, raw_resume_text, name)
        section = zero_unquoted(section, name)
        section = enforce_bounds(section, name)
        validated[name] = section

    updated = evaluation.model_copy(update=validated)
    total = recompute_total(updated)
    return updated.model_copy(update={"total_score": total})
